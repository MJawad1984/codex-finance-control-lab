# From spreadsheet control to tested application with Codex

## 1. Define the control before prompting

Ask: "Which invoice keys occur once on each side, and are their signed gross amounts equal? What must happen when keys repeat or inputs are invalid?" Decide the grain, key, currency precision, tolerance and missing-data policy first. Do not ask an LLM to decide whether an invoice is legally recoverable or payable.

## 2. Give Codex a narrow acceptance contract

Example prompt:

> Build a local Python invoice-reconciliation lab using only synthetic CSV data. Use exact minor units, reject excess decimal precision, and keep currencies separate. Preserve supplier/invoice identity. Route duplicate keys to review rather than guessing. Prove every input row is assigned once and money reconciles by side/currency. Externalize material rule configuration. Add boundary/failure tests, a hand-calculated example, clear limitations and a three-version CI workflow. Never post accounting entries or invent production use.

Review the resulting requirements and data contract. The prompt is a reproducible teaching prompt for this lab, not claimed as a verbatim log of an earlier session.

## 3. Run the supplied synthetic population

Use the README command. Open `report.json` first: inspect status counts, USD/GBP controls and the ambiguous key SYN003/INV-004. Then open the CSV for convenient review. Read its owner and exception state rather than treating all balanced groups as approved.

## 4. Check money independently

Add the example USD amounts by hand: 400.00 source, 369.99 ledger, 30.01 difference. Run `python scripts/check_example.py demo-output/report.json`. Neither a green test badge nor a plausible looking report replaces this check.

## 5. Explore one rule change

Copy `rules/demo.json` to a new local config, change the version, and set USD tolerance to the string `0.01`. Run into a new output directory. The one-cent mismatch should become MATCHED, while the duplicate group remains AMBIGUOUS and the 30.01 total difference remains visible. Do not silently apply this tolerance in a real organization; it needs policy approval.

## 6. Make a failure useful

Copy a sample file, replace an amount with `NaN` or repeat a record ID, and run it locally. Expect exit code 2, `EXCEPTION_PENDING_REVIEW`, and no new business-output directory. Record the error, fix the source with an authorized owner, and rerun; do not substitute a guessed amount.

## 7. Extend with evidence

Before adding dates, fuzzy matching, tax rates, dashboards or live systems, define new acceptance criteria and independently calculated expectations. An invoice-line/payment settlement model needs a different grain and matching policy. For reporting, consider Power BI on validated output while preserving source totals, currency filters and exception visibility.
