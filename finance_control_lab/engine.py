"""Deterministic reconciliation with exact minor-unit arithmetic."""

from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

COLUMNS = ("record_id", "supplier_id", "invoice_number", "currency", "gross_amount")
STATUSES = ("MATCHED", "AMOUNT_MISMATCH", "SOURCE_ONLY", "LEDGER_ONLY", "AMBIGUOUS")


class ValidationError(ValueError):
    """Required inputs or invariants are unresolved; do not publish a result."""


def clean_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValidationError(
            f"{field}: required text; surrounding whitespace forbidden"
        )
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValidationError(f"{field}: control characters forbidden")
    return value


def parse_amount(value: object, precision: int) -> int:
    """Return integer minor units; never round an input or accept exponent notation."""
    text = clean_text(value, "amount")
    pattern = rf"-?[0-9]+(?:\.[0-9]{{1,{precision}}})?" if precision else r"-?[0-9]+"
    if not re.fullmatch(pattern, text) or len(text) > 24:
        raise ValidationError("amount: invalid format, magnitude or currency precision")
    sign = -1 if text.startswith("-") else 1
    major, _, fraction = text.removeprefix("-").partition(".")
    return sign * (
        int(major) * 10**precision + int(fraction.ljust(precision, "0") or "0")
    )


def money(units: int, precision: int) -> str:
    sign = "-" if units < 0 else ""
    major, minor = divmod(abs(units), 10**precision)
    return f"{sign}{major}.{minor:0{precision}d}" if precision else f"{sign}{major}"


@dataclass(frozen=True)
class Rules:
    version: str
    currency_precision: dict[str, int]
    tolerance_units: dict[str, int]
    exception_owner: str

    @classmethod
    def from_bytes(cls, data: bytes) -> Rules:
        def reject_duplicates(pairs: list[tuple[str, object]]) -> dict:
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValidationError("rules: duplicate JSON key")
                result[key] = value
            return result

        try:
            raw = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValidationError("rules: invalid UTF-8 JSON") from exc
        required = {"version", "currencies", "exception_owner"}
        if not isinstance(raw, dict) or set(raw) != required:
            raise ValidationError(
                "rules: exact version, currencies, exception_owner required"
            )
        version = clean_text(raw["version"], "rule version")
        owner = clean_text(raw["exception_owner"], "exception owner")
        currencies = raw["currencies"]
        if not isinstance(currencies, dict) or not currencies:
            raise ValidationError("rules: nonempty currency configuration required")
        precisions, tolerances = {}, {}
        for currency, spec in currencies.items():
            if not re.fullmatch(r"[A-Z]{3}", currency):
                raise ValidationError(
                    "rules: currency must have three uppercase ASCII letters"
                )
            if not isinstance(spec, dict) or set(spec) != {"precision", "tolerance"}:
                raise ValidationError("rules: exact precision and tolerance required")
            precision = spec["precision"]
            if type(precision) is not int or not 0 <= precision <= 4:
                raise ValidationError(
                    "rules: precision must be integer from zero to four"
                )
            tolerance = parse_amount(spec["tolerance"], precision)
            if tolerance < 0:
                raise ValidationError("rules: negative tolerance forbidden")
            precisions[currency], tolerances[currency] = precision, tolerance
        return cls(version, precisions, tolerances, owner)


@dataclass(frozen=True)
class Record:
    record_id: str
    supplier_id: str
    invoice_number: str
    currency: str
    units: int

    @property
    def key(self) -> tuple[str, str, str]:
        return self.supplier_id, self.invoice_number, self.currency


def read_records(data: bytes, rules: Rules) -> tuple[Record, ...]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValidationError("CSV: UTF-8 required") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    try:
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValidationError(f"CSV: header must be {','.join(COLUMNS)}")
        records, seen = [], set()
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValidationError(f"CSV line {reader.line_num}: wrong column count")
            values = {k: clean_text(v, k) for k, v in row.items()}
            identity = values["record_id"]
            if identity in seen:
                raise ValidationError("CSV: duplicate record_id")
            seen.add(identity)
            currency = values["currency"]
            if currency not in rules.currency_precision:
                raise ValidationError("CSV: currency not explicitly configured")
            records.append(
                Record(
                    identity,
                    values["supplier_id"],
                    values["invoice_number"],
                    currency,
                    parse_amount(
                        values["gross_amount"], rules.currency_precision[currency]
                    ),
                )
            )
        return tuple(records)
    except csv.Error as exc:
        raise ValidationError("CSV: malformed quoting") from exc


def reconcile(
    source: tuple[Record, ...], ledger: tuple[Record, ...], rules: Rules
) -> dict:
    """Every row belongs to one group; duplicate keys never become guessed pairs."""
    grouped = defaultdict(lambda: {"source": [], "ledger": []})
    for side, records in (("source", source), ("ledger", ledger)):
        ids = [r.record_id for r in records]
        if len(ids) != len(set(ids)):
            raise ValidationError(f"{side}: duplicate record_id")
        for record in records:
            for field in ("record_id", "supplier_id", "invoice_number", "currency"):
                clean_text(getattr(record, field), field)
            if (
                record.currency not in rules.currency_precision
                or type(record.units) is not int
            ):
                raise ValidationError(
                    "record: unknown currency or non-integer minor units"
                )
            grouped[record.key][side].append(record)
    groups = []
    for key, sides in sorted(grouped.items()):
        left, right = sides["source"], sides["ledger"]
        source_units, ledger_units = (
            sum(r.units for r in left),
            sum(r.units for r in right),
        )
        difference = source_units - ledger_units
        if len(left) > 1 or len(right) > 1:
            status = "AMBIGUOUS"
        elif not left:
            status = "LEDGER_ONLY"
        elif not right:
            status = "SOURCE_ONLY"
        elif abs(difference) <= rules.tolerance_units[key[2]]:
            status = "MATCHED"
        else:
            status = "AMOUNT_MISMATCH"
        precision = rules.currency_precision[key[2]]
        groups.append(
            {
                "supplier_id": key[0],
                "invoice_number": key[1],
                "currency": key[2],
                "status": status,
                "review_state": "CLEARED"
                if status == "MATCHED"
                else "EXCEPTION_PENDING_REVIEW",
                "owner": "" if status == "MATCHED" else rules.exception_owner,
                "source_ids": sorted(r.record_id for r in left),
                "ledger_ids": sorted(r.record_id for r in right),
                "source_amount": money(source_units, precision),
                "ledger_amount": money(ledger_units, precision),
                "difference": money(difference, precision),
            }
        )
    controls = {}
    for currency in sorted(rules.currency_precision):
        precision = rules.currency_precision[currency]
        currency_groups = [g for g in groups if g["currency"] == currency]
        by_side = {}
        for side, records in (("source", source), ("ledger", ledger)):
            inputs = [r for r in records if r.currency == currency]
            assigned = [
                identity for g in currency_groups for identity in g[f"{side}_ids"]
            ]
            input_total = sum(r.units for r in inputs)
            assigned_total = sum(
                parse_amount(g[f"{side}_amount"], precision) for g in currency_groups
            )
            count_ok = Counter(assigned) == Counter(r.record_id for r in inputs)
            amount_ok = input_total == assigned_total
            if not count_ok or not amount_ok:
                raise ValidationError(
                    "control: population or monetary reconciliation failed"
                )
            by_side[side] = {
                "input_rows": len(inputs),
                "assigned_rows": len(assigned),
                "input_amount": money(input_total, precision),
                "assigned_amount": money(assigned_total, precision),
                "population_reconciled": count_ok,
                "amount_reconciled": amount_ok,
            }
        by_side["source_less_ledger"] = money(
            sum(r.units for r in source if r.currency == currency)
            - sum(r.units for r in ledger if r.currency == currency),
            precision,
        )
        controls[currency] = by_side
    return {
        "rule_version": rules.version,
        "status_counts": {s: sum(g["status"] == s for g in groups) for s in STATUSES},
        "controls": controls,
        "groups": groups,
    }
