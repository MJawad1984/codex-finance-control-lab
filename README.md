# Codex Finance Control Lab

## Invoice Reconciliation & Exception Engine

[![tests](https://github.com/MJawad1984/codex-finance-control-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/MJawad1984/codex-finance-control-lab/actions/workflows/tests.yml)

**A finance professional becoming a builder with Codex.** This small teaching lab turns an invoice-reconciliation requirement into runnable Python, explicit rules, automated checks and a traceable review output.

**Status: synthetic educational prototype, v0.1.0.** Not production software, a tax calculator, or an accounting-policy decision system. No real PSO, customer or supplier data is included. The initial build was created on 1 November 2026 with Codex assistance; see [build provenance](docs/CODEX_BUILD.md).

### Try it (Python 3.11–3.13)

The application itself has **no third-party runtime dependencies** and needs no API key.

```bash
git clone https://github.com/MJawad1984/codex-finance-control-lab.git
cd codex-finance-control-lab
python -m finance_control_lab --source examples/source.csv --ledger examples/ledger.csv --rules rules/demo.json --output-dir demo-output
```

Use a new output directory on each run. Its parent must already exist. The command writes `report.json`, `reconciliation.csv`, and `manifest.json` (the completion marker). Missing/invalid inputs return exit code 2 with `EXCEPTION_PENDING_REVIEW`; no business result is published. Exceptions in otherwise valid populations produce `COMPLETED_WITH_EXCEPTIONS`, not an accounting approval.

### What the example proves

Seven source rows and six ledger rows produce seven key groups:

| Classification | Groups | Meaning |
|---|---:|---|
| MATCHED | 3 | Unique key on each side; amount within configured tolerance |
| AMOUNT_MISMATCH | 1 | Unique key; amount outside tolerance |
| SOURCE_ONLY | 1 | Source record with no ledger key |
| LEDGER_ONLY | 1 | Ledger record with no source key |
| AMBIGUOUS | 1 | Duplicate key on either side; no guessed pairing |

USD source total **400.00**, ledger **369.99**, source less ledger **30.01**. GBP totals are **75.00** on each side and remain separate. The duplicate group totals 60.00 on each side but is still ambiguous: equal money does not establish invoice identity. Credit notes retain their negative sign.

### Controls you can inspect

- Exact integer minor-unit arithmetic; no floating-point money or silent rounding.
- Versioned currency precision/tolerance configuration; exact zero tolerance in the demo.
- Composite key: supplier ID + invoice number + currency. Case and leading zeros preserved.
- Duplicate record IDs block the run. Duplicate business keys route the complete group to review.
- Every input row is assigned exactly once, checked per side and currency; monetary totals also reconcile.
- Exceptions carry `EXCEPTION_PENDING_REVIEW` and a named demo reviewer role.
- SHA-256 of the exact input/rule/output bytes, software version and UTC run timestamp.
- CSV text fields escape spreadsheet formula starters; JSON retains original identifiers.
- No external providers, AI calls, credentials, database writes, postings or automatic policy conclusions at runtime.

### Verify it yourself

```bash
python -m venv .venv
# Activate the virtual environment for your operating system.
python -m pip install -r requirements-dev.txt
python -m pytest -q
ruff check .
ruff format --check .
python scripts/check_example.py demo-output/report.json
```

CI runs these checks on Python 3.11, 3.12 and 3.13. The badge links to actual run results; configuration alone does not prove a passing run. See [validation evidence and limits](docs/VALIDATION.md). Tool pins are in `requirements-dev.txt`; application rules are in `rules/demo.json`.

### Learn the build, not just the output

1. Read the [requirements and acceptance criteria](docs/REQUIREMENTS.md).
2. Inspect the [data contract](docs/DATA_CONTRACT.md) and [control design](docs/CONTROL_DESIGN.md).
3. Follow the [reproducible tutorial](docs/TUTORIAL.md).
4. Compare Codex's role with [human review and build provenance](docs/CODEX_BUILD.md).
5. Review [limitations and production gates](docs/LIMITATIONS.md) before extending it.

Maintainer: **Muhammad Jawad, ACA/FCCA**, Karachi, Pakistan. Finance/tax domain practitioner developing software-building capability with Codex; no claim of conventional software-engineering tenure. The example reflects general reconciliation concepts, not confidential employer methods.
