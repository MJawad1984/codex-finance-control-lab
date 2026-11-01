import json
from dataclasses import replace
from itertools import permutations
from pathlib import Path

import pytest

from finance_control_lab.engine import (
    COLUMNS,
    Record,
    Rules,
    ValidationError,
    money,
    parse_amount,
    read_records,
    reconcile,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def rules():
    return Rules.from_bytes((ROOT / "rules/demo.json").read_bytes())


def test_worked_example_independent_totals(rules):
    # Hand calculation: source USD 100+200+50+30+30-10=400;
    # ledger USD 100+199.99+60-10+20=369.99. Difference=30.01.
    result = reconcile(
        read_records((ROOT / "examples/source.csv").read_bytes(), rules),
        read_records((ROOT / "examples/ledger.csv").read_bytes(), rules),
        rules,
    )
    assert result["status_counts"] == {
        "MATCHED": 3,
        "AMOUNT_MISMATCH": 1,
        "SOURCE_ONLY": 1,
        "LEDGER_ONLY": 1,
        "AMBIGUOUS": 1,
    }
    usd = result["controls"]["USD"]
    assert usd["source"]["input_rows"] == 6
    assert usd["ledger"]["input_rows"] == 5
    assert usd["source"]["input_amount"] == "400.00"
    assert usd["ledger"]["input_amount"] == "369.99"
    assert usd["source_less_ledger"] == "30.01"
    assert result["controls"]["GBP"]["source"]["input_amount"] == "75.00"
    assert all(
        usd[s][k]
        for s in ("source", "ledger")
        for k in ("population_reconciled", "amount_reconciled")
    )
    ambiguous = next(g for g in result["groups"] if g["status"] == "AMBIGUOUS")
    assert ambiguous["source_ids"] == ["S004", "S005"]
    assert ambiguous["difference"] == "0.00"  # Equal sums do not authorize a pair.
    assert ambiguous["review_state"] == "EXCEPTION_PENDING_REVIEW"


@pytest.mark.parametrize(
    "source_count,ledger_count", [(2, 1), (1, 2), (2, 2), (2, 0), (0, 2)]
)
def test_duplicate_keys_never_auto_match(rules, source_count, ledger_count):
    source = tuple(Record(f"S{i}", "A", "01", "USD", 100) for i in range(source_count))
    ledger = tuple(Record(f"L{i}", "A", "01", "USD", 100) for i in range(ledger_count))
    group = reconcile(source, ledger, rules)["groups"][0]
    assert group["status"] == "AMBIGUOUS"
    assert group["owner"] == "Demo finance reviewer"


@pytest.mark.parametrize(
    "difference,status",
    [
        (0, "MATCHED"),
        (1, "MATCHED"),
        (-1, "MATCHED"),
        (2, "AMOUNT_MISMATCH"),
        (-2, "AMOUNT_MISMATCH"),
    ],
)
def test_tolerance_boundary_is_inclusive_and_symmetric(rules, difference, status):
    rules = replace(rules, tolerance_units={"USD": 1, "GBP": 0})
    source = (Record("S", "A", "1", "USD", 100),)
    ledger = (Record("L", "A", "1", "USD", 100 - difference),)
    assert reconcile(source, ledger, rules)["groups"][0]["status"] == status


@pytest.mark.parametrize(
    "supplier,invoice,currency",
    [("B", "001", "USD"), ("A", "1", "USD"), ("A", "001", "GBP"), ("a", "001", "USD")],
)
def test_composite_key_preserves_identity(rules, supplier, invoice, currency):
    result = reconcile(
        (Record("S", "A", "001", "USD", 100),),
        (Record("L", supplier, invoice, currency, 100),),
        rules,
    )
    assert result["status_counts"]["MATCHED"] == 0
    assert result["status_counts"]["SOURCE_ONLY"] == 1
    assert result["status_counts"]["LEDGER_ONLY"] == 1


def test_order_does_not_change_results(rules):
    source = (
        Record("S2", "A", "2", "USD", 200),
        Record("S1", "A", "1", "USD", 100),
        Record("S3", "A", "1", "USD", 100),
    )
    ledger = (Record("L", "A", "1", "USD", 200),)
    baseline = reconcile(source, ledger, rules)
    for ordered in permutations(source):
        assert reconcile(ordered, ledger, rules) == baseline


@pytest.mark.parametrize(
    "text,precision,expected",
    [
        ("0", 2, 0),
        ("-0.00", 2, 0),
        ("12.3", 2, 1230),
        ("-1.01", 2, -101),
        ("123", 0, 123),
        ("0.001", 3, 1),
        ("99999999999999999999.99", 2, 9999999999999999999999),
    ],
)
def test_amount_exact_minor_units(text, precision, expected):
    assert parse_amount(text, precision) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "1.001",
        "NaN",
        "Infinity",
        "1e2",
        "1,000.00",
        "+1.00",
        "1.",
        ".50",
        " 1",
        "1 ",
        "--1",
        "１２",
        "1\n",
        "1" * 25,
    ],
)
def test_invalid_amounts_block(text):
    with pytest.raises(ValidationError):
        parse_amount(text, 2)


@pytest.mark.parametrize(
    "units,precision,expected",
    [
        (0, 2, "0.00"),
        (-1, 2, "-0.01"),
        (-100, 2, "-1.00"),
        (5, 0, "5"),
        (1, 4, "0.0001"),
    ],
)
def test_money_display(units, precision, expected):
    assert money(units, precision) == expected


def test_empty_populations_are_visible_not_missing(rules):
    result = reconcile((), (), rules)
    assert result["groups"] == []
    assert result["controls"]["USD"]["source"]["input_rows"] == 0
    assert result["controls"]["USD"]["source"]["input_amount"] == "0.00"


@pytest.mark.parametrize("side", ["source", "ledger"])
def test_direct_api_duplicate_ids_block(rules, side):
    records = (
        Record("same", "A", "1", "USD", 100),
        Record("same", "A", "2", "USD", 200),
    )
    with pytest.raises(ValidationError):
        reconcile(
            records if side == "source" else (),
            records if side == "ledger" else (),
            rules,
        )


@pytest.mark.parametrize(
    "row",
    [
        "S,A,1,USD,1.001",
        "S,A,1,EUR,1.00",
        "S,,1,USD,1.00",
        "S,A,1,USD",
        "S,A,1,USD,1.00,extra",
        "S,A,1,USD,NaN",
        "S,A,1,USD,1.00\nS,A,2,USD,2.00",
    ],
)
def test_csv_contract_failures(rules, row):
    data = (",".join(COLUMNS) + "\n" + row + "\n").encode()
    with pytest.raises(ValidationError):
        read_records(data, rules)


def test_csv_preserves_identifiers_and_utf8_bom(rules):
    data = (",".join(COLUMNS) + '\nS,Å,"0001",USD,-1.00\n').encode("utf-8-sig")
    row = read_records(data, rules)[0]
    assert row.invoice_number == "0001"
    assert row.supplier_id == "Å"
    assert row.units == -100


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"record_id,record_id\n",
        b"\xff",
        b'record_id,supplier_id,invoice_number,currency,gross_amount\n"S,A,1,USD,1.00\n',
    ],
)
def test_invalid_csv_encoding_header_and_quoting(rules, data):
    with pytest.raises(ValidationError):
        read_records(data, rules)


@pytest.mark.parametrize(
    "patch",
    [
        {"extra": 1},
        {"version": ""},
        {"exception_owner": ""},
        {"currencies": {}},
        {"currencies": {"usd": {"precision": 2, "tolerance": "0.00"}}},
        {"currencies": {"USD": {"precision": True, "tolerance": "0.00"}}},
        {"currencies": {"USD": {"precision": 5, "tolerance": "0.00"}}},
        {"currencies": {"USD": {"precision": 2, "tolerance": "-0.01"}}},
        {"currencies": {"USD": {"precision": 2, "tolerance": 0.01}}},
        {"currencies": {"USD": {"precision": 2, "tolerance": "0.001"}}},
    ],
)
def test_invalid_rules_block(patch):
    raw = json.loads((ROOT / "rules/demo.json").read_bytes())
    raw.update(patch)
    with pytest.raises(ValidationError):
        Rules.from_bytes(json.dumps(raw).encode())


@pytest.mark.parametrize(
    "raw", [b"{", b"[]", b'{"version":"a","version":"b"}', b"\xff"]
)
def test_bad_json_and_duplicate_config_keys_block(raw):
    with pytest.raises(ValidationError):
        Rules.from_bytes(raw)
