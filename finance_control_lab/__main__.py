"""Run locally with Python; publish outputs only after validation and controls."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from . import __version__
from .engine import Rules, ValidationError, read_records, reconcile


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: dict) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode()


def safe_csv_text(value: str) -> str:
    """Escape spreadsheet formula starters in textual export fields only."""
    return "'" + value if value.startswith(("=", "+", "-", "@")) else value


def csv_bytes(groups: list[dict]) -> bytes:
    fields = [
        "supplier_id",
        "invoice_number",
        "currency",
        "status",
        "review_state",
        "owner",
        "source_ids",
        "ledger_ids",
        "source_amount",
        "ledger_amount",
        "difference",
    ]
    text_fields = set(fields) - {"source_amount", "ledger_amount", "difference"}
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for group in groups:
        row = {
            k: json.dumps(v, ensure_ascii=True) if isinstance(v, list) else v
            for k, v in group.items()
        }
        writer.writerow(
            {k: safe_csv_text(v) if k in text_fields else v for k, v in row.items()}
        )
    return output.getvalue().encode("utf-8")


def run(source: Path, ledger: Path, rules_path: Path, output: Path) -> dict:
    inputs = {
        "source": source.read_bytes(),
        "ledger": ledger.read_bytes(),
        "rules": rules_path.read_bytes(),
    }
    rules = Rules.from_bytes(inputs["rules"])
    result = reconcile(
        read_records(inputs["source"], rules),
        read_records(inputs["ledger"], rules),
        rules,
    )
    artifacts = {
        "report.json": json_bytes(result),
        "reconciliation.csv": csv_bytes(result["groups"]),
    }
    input_hashes = {k: sha256(v) for k, v in inputs.items()}
    manifest = {
        "schema_version": 1,
        "software_version": __version__,
        "rule_version": rules.version,
        "run_fingerprint": sha256(
            json_bytes({"input_sha256": input_hashes, "software_version": __version__})
        ),
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "python": sys.version.split()[0],
        "input_sha256": input_hashes,
        "output_sha256": {k: sha256(v) for k, v in artifacts.items()},
        "run_status": "COMPLETED_WITH_EXCEPTIONS"
        if any(g["status"] != "MATCHED" for g in result["groups"])
        else "COMPLETED",
        "data_classification": (
            "Synthetic examples only; user inputs are not independently authenticated"
        ),
    }
    # Never overwrite an existing run; manifest is the final completion marker.
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    try:
        for name, data in artifacts.items():
            with (output / name).open("xb") as stream:
                stream.write(data)
        with (output / "manifest.json").open("xb") as stream:
            stream.write(json_bytes(manifest))
    except OSError:
        shutil.rmtree(output)
        raise
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synthetic invoice reconciliation control lab"
    )
    for name in ("source", "ledger", "rules", "output-dir"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = run(args.source, args.ledger, args.rules, args.output_dir)
    except (ValidationError, OSError) as exc:
        print(f"EXCEPTION_PENDING_REVIEW: {exc}", file=sys.stderr)
        return 2
    print(f"{manifest['run_status']}: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
