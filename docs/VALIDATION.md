# Validation evidence — 1 November 2026

Version: v0.1.0 initial implementation. This page records observed checks, not a claim of production assurance.

| Check | Observed local result |
|---|---|
| Python interpreter | 3.12.14 |
| `python -m pytest -q` | 86 passed |
| `ruff check .` | All checks passed |
| `ruff format --check .` | Passed before publication |
| CLI with committed synthetic fixtures | COMPLETED_WITH_EXCEPTIONS |
| `python scripts/check_example.py <run>/report.json` | Worked reference PASS |

The reference checker is a separate standard-library script with fixed expectations derived from the worked arithmetic in CONTROL_DESIGN.md; it does not import the application engine. Tests also corrupt outputs deliberately to check that this verifier rejects incorrect counts, amounts and duplicate classification. This is a limited numerical cross-check, not independent third-party assurance.

Coverage includes exact/negative money, tolerance boundaries, duplicate-key multiplicities, identity preservation, order invariance, empty populations, invalid amounts/currencies/IDs/headers/quoting/configuration, no-overwrite/fail-closed behavior, formula escaping, actual subprocess execution, hashes and repeatability. **86 is the number of passing pytest cases, including parameterized cases; no coverage percentage is asserted.**

## GitHub Actions

The committed workflow runs on push/pull request/manual dispatch across Python 3.11, 3.12 and 3.13. Consult [actual runs](https://github.com/MJawad1984/codex-finance-control-lab/actions/workflows/tests.yml) for each commit. Local execution alone does not establish that those hosted jobs passed. A later validation update may record their observed result.

## Reproduction limits

Direct and transitive development-tool versions observed in this run are pinned in requirements-dev.txt. Hosted runner images and pip are not fixed, and the manifest timestamp/interpreter version vary. The application has no third-party runtime dependencies. Exact code comes from the Git commit; input/config/output integrity comes from the manifest hashes. Neither establishes source authenticity or a protected audit trail.

No independent human code audit, full production security evaluation, load/concurrency qualification or real-data acceptance has been completed.
