# Requirements and acceptance criteria

Decision: which source-versus-ledger invoice groups can be cleared mechanically, and which require review? The prototype never posts to a ledger, approves a payment or determines a tax/accounting conclusion.

Audience: accountants, tax professionals, controllers, auditors and finance leaders learning to build narrow tools with Codex. Starting scale: one person, local files, one process, small synthetic populations. No web framework, service, database, LLM runtime or agent framework is needed.

| Requirement | Acceptance evidence |
|---|---|
| Exact money and explicit rounding policy | Integer minor units; overprecision rejected; signed credit notes tested |
| Strict source contract | Required header/order; missing/extra fields, blank IDs, invalid currency/amount, duplicate record IDs and malformed CSV rejected |
| Stable invoice identity | Exact supplier/invoice/currency key; leading zeros, case and currencies not merged |
| No duplicate guessing | Any key multiplicity on either side classifies the entire group as AMBIGUOUS, even with equal sums |
| Explicit tolerances | Versioned config; nonnegative exact-currency tolerance; inclusive symmetric boundary tests |
| Complete populations | Each record ID assigned once; counts and money reconcile independently for each side/currency |
| Traceable output | Input/config/output SHA-256; software/rule versions, timestamp and interpreter recorded |
| Safe failure | Invalid input returns code 2 without output; existing output directories not overwritten |
| Reproducible learning | Synthetic worked example with separately hand-calculated totals, tutorial and check script |
| Quality checks | pytest, Ruff lint/format, and a three-version CI matrix |

Adopt/extend/build decision: Python's CSV/JSON/integer standard library is adequate; there is no reason to adopt a production reconciliation platform for this educational scope. Excel/Power Query and Power BI remain sensible options for business analysis/reporting; this lab isolates programmable controls and reproducible tests rather than replacing them.
