"""Check the output against fixed, hand-calculated example expectations.

This script deliberately does not import the application engine.
"""

import json
import sys
from pathlib import Path


def check(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "MATCHED": 3,
        "AMOUNT_MISMATCH": 1,
        "SOURCE_ONLY": 1,
        "LEDGER_ONLY": 1,
        "AMBIGUOUS": 1,
    }
    if data["status_counts"] != expected:
        raise ValueError("Example status counts differ from the worked reference")
    for currency, side, rows, amount in (
        ("USD", "source", 6, "400.00"),
        ("USD", "ledger", 5, "369.99"),
        ("GBP", "source", 1, "75.00"),
        ("GBP", "ledger", 1, "75.00"),
    ):
        values = data["controls"][currency][side]
        if (
            values["input_rows"] != rows
            or values["assigned_rows"] != rows
            or values["input_amount"] != amount
            or values["assigned_amount"] != amount
            or values["population_reconciled"] is not True
            or values["amount_reconciled"] is not True
        ):
            raise ValueError(f"Example control differs: {currency}/{side}")
    if data["controls"]["USD"]["source_less_ledger"] != "30.01":
        raise ValueError("USD difference must equal hand-calculated 30.01")
    duplicate = next(
        g
        for g in data["groups"]
        if g["supplier_id"] == "SYN003" and g["invoice_number"] == "INV-004"
    )
    if duplicate["status"] != "AMBIGUOUS" or duplicate["difference"] != "0.00":
        raise ValueError("Equal duplicate totals must remain ambiguous")
    print("Worked reference PASS: populations, currency totals and duplicate handling")


if __name__ == "__main__":
    check(Path(sys.argv[1]))
