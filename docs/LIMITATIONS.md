# Limitations and next gates

This is a small, local, synthetic teaching prototype. It does not establish production readiness or professional assurance.

- No approval workflow, maker/checker roles, authentication, access controls, protected storage, signed audit records, retention policy or monitoring.
- No source-system reconciliation, extraction cutoff, invoice dates, freshness assurance, supplier-master resolution, FX, tax-law determination or payment/posting integration.
- Entire files are read into memory. No tested data-volume, concurrency, availability or recovery SLA. Run one process against a new output directory. A completion manifest is written last; a crash or power failure may leave partial files that must not be treated as completed output.
- Matching is exact and case-sensitive. AMBIGUOUS is a group-level exception, not a claim of fraud or an instruction to delete duplicates. Tolerance does not authorize a write-off.
- Rules permit precision zero through four; use policy-approved currency specifications. The demo values are educational configuration, not an ISO currency catalogue or organization policy.
- The direct Python API is intended for records/configuration validated by the supplied readers. CSV/JSON are the supported user input boundary.
- Identifiers and amounts in generated outputs may be sensitive if users supply real data. Do not commit those outputs. Hashes can expose integrity differences and do not encrypt data.
- The run fingerprint identifies bytes plus declared software version, not a signed commit or installed environment. Dev tools are pinned directly; transitive tool dependencies and hosted CI runner images can still change.
- Tests are predominantly written by the same coding assistant. Independent manual sample arithmetic is limited to the small published example; it is not a second-party audit.

Before any real use: business-owner-approved rules and extract contract; independent reconciliation to authoritative source totals; security/privacy review; maker/checker ownership; controlled dependency/environment versions; exception recovery, backup, rollback and monitoring; volume/concurrency tests and user acceptance. Block affected decisions while required evidence remains unresolved. No fallback provider or runtime AI is present.
