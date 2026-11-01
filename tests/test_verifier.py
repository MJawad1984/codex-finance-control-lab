import importlib.util
import json
from pathlib import Path

import pytest

from finance_control_lab.__main__ import run

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "check_example", ROOT / "scripts/check_example.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize("fault", ["status", "amount", "population", "duplicate"])
def test_worked_reference_detects_corrupted_outputs(tmp_path, fault):
    out = tmp_path / "run"
    run(
        ROOT / "examples/source.csv",
        ROOT / "examples/ledger.csv",
        ROOT / "rules/demo.json",
        out,
    )
    path = out / "report.json"
    data = json.loads(path.read_bytes())
    if fault == "status":
        data["status_counts"]["MATCHED"] = 4
    elif fault == "amount":
        data["controls"]["USD"]["source"]["input_amount"] = "399.99"
    elif fault == "population":
        data["controls"]["GBP"]["source"]["assigned_rows"] = 0
    else:
        next(g for g in data["groups"] if g["status"] == "AMBIGUOUS")["status"] = (
            "MATCHED"
        )
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        module.check(path)
