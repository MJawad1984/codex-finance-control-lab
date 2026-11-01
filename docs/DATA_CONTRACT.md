# Data contract v1

Source and ledger use the same exact CSV header, in this order:

```csv
record_id,supplier_id,invoice_number,currency,gross_amount
```

- Grain: one imported invoice/credit-note record per row, not invoice line items or payments.
- `record_id`: nonempty and unique within each side. The same ID may occur on opposite sides; side is part of lineage.
- `supplier_id` and `invoice_number`: nonempty exact text. Case and leading zeros retained. No fuzzy matching, trimming or punctuation removal. Supplier IDs must already use an agreed common master-data namespace.
- `currency`: three uppercase ASCII letters explicitly configured. Demo currencies USD and GBP; no exchange-rate conversion or cross-currency total.
- `gross_amount`: signed decimal text in major currency units. ASCII digits; optional leading minus and decimal fraction up to configured precision. No commas, plus sign, exponent notation, NaN or infinity. Maximum input amount string length 24. Inputs are never rounded. Negative amounts are credit notes; zero amounts are accepted and visible.
- Input format: UTF-8, with optional BOM; comma delimiter; standard CSV quoting; header-only files are valid explicit empty populations. Completely blank CSV lines follow the standard CSV parser's skip behavior; malformed records do not become zero/missing values.
- All fields: surrounding whitespace and ASCII control characters are rejected. Missing/extra columns, repeated headers, unknown columns and duplicate record IDs block the run.
- Missing counterpart: explicit SOURCE_ONLY or LEDGER_ONLY group, never an invented zero invoice.
- Dates/freshness: no invoice date or accounting-period cutoff is present in v1. The user must supply comparable, complete extracts. The manifest timestamp records execution, not source freshness. Never infer period reconciliation from these outputs.

Output grain: one exact composite-key group. `source_ids` and `ledger_ids` are arrays in JSON and JSON-encoded arrays within CSV cells; no delimiter-based loss of record identity. CSV-only text escaping may prepend an apostrophe to a formula-leading identifier. JSON is the canonical unmodified identifier representation.

All bundled rows are invented SYN-series suppliers and invoice IDs. No live integrations or imported employer datasets are used.
