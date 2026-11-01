import csv
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from finance_control_lab.__main__ import csv_bytes, main, run
from finance_control_lab.engine import Record, Rules, reconcile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples/source.csv"
LEDGER = ROOT / "examples/ledger.csv"
RULES = ROOT / "rules/demo.json"


def test_cli_real_process_and_hashes(tmp_path):
    out = tmp_path / "output"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "finance_control_lab",
            "--source",
            str(SOURCE),
            "--ledger",
            str(LEDGER),
            "--rules",
            str(RULES),
            "--output-dir",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "COMPLETED_WITH_EXCEPTIONS" in result.stdout
    manifest = json.loads((out / "manifest.json").read_bytes())
    for name, digest in manifest["output_sha256"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
    for name, path in (("source", SOURCE), ("ledger", LEDGER), ("rules", RULES)):
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == manifest["input_sha256"][name]
        )
    with (out / "reconciliation.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 7
    assert sum(row["status"] == "AMBIGUOUS" for row in rows) == 1


def test_deterministic_outputs_and_fingerprint(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    a = run(SOURCE, LEDGER, RULES, one)
    b = run(SOURCE, LEDGER, RULES, two)
    assert a["run_fingerprint"] == b["run_fingerprint"]
    assert (one / "report.json").read_bytes() == (two / "report.json").read_bytes()
    assert (one / "reconciliation.csv").read_bytes() == (
        two / "reconciliation.csv"
    ).read_bytes()


def test_existing_output_is_not_overwritten(tmp_path):
    marker = tmp_path / "existing.txt"
    marker.write_text("keep")
    with pytest.raises(FileExistsError):
        run(SOURCE, LEDGER, RULES, tmp_path)
    assert marker.read_text() == "keep"


def test_invalid_input_creates_no_outputs(tmp_path, capsys):
    invalid = tmp_path / "bad.csv"
    invalid.write_text("bad header\n")
    out = tmp_path / "no-output"
    code = main(
        [
            "--source",
            str(invalid),
            "--ledger",
            str(LEDGER),
            "--rules",
            str(RULES),
            "--output-dir",
            str(out),
        ]
    )
    assert code == 2
    assert "EXCEPTION_PENDING_REVIEW" in capsys.readouterr().err
    assert not out.exists()


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@"])
def test_textual_csv_formula_starters_are_escaped(prefix):
    rules = Rules.from_bytes(RULES.read_bytes())
    result = reconcile(
        (Record("S", prefix + "formula", "INV", "USD", -100),), (), rules
    )
    row = next(csv.DictReader(io.StringIO(csv_bytes(result["groups"]).decode())))
    assert row["supplier_id"] == "'" + prefix + "formula"
    assert row["source_amount"] == "-1.00"
    assert result["groups"][0]["supplier_id"] == prefix + "formula"


def test_missing_input_blocks_without_output(tmp_path, capsys):
    out = tmp_path / "no-output"
    code = main(
        [
            "--source",
            str(tmp_path / "absent.csv"),
            "--ledger",
            str(LEDGER),
            "--rules",
            str(RULES),
            "--output-dir",
            str(out),
        ]
    )
    assert code == 2
    assert "EXCEPTION_PENDING_REVIEW" in capsys.readouterr().err
    assert not out.exists()
