# Contributor instructions

Keep this an understandable synthetic teaching lab. Separate deterministic rules from file I/O. Never introduce employer/customer data, credentials or runtime LLM decisions. Preserve case/leading zeros and currency separation; never auto-pair duplicate keys. Externalize material rules with versioned validation; ordinary constants may remain in code.

Before changing behavior, update requirements and independently derived expectations. Run `python -m pytest -q`, `ruff check .`, `ruff format --check .`, the CLI example and `python scripts/check_example.py <output>/report.json`. Keep failing checks visible; do not weaken expected results to pass. Record actual checks and limitations. Do not infer CI success from configuration.

Do not invent development history, testimonials, production use, metrics, test counts, model IDs or review/approval evidence. Do not add a service/UI/database framework without a concrete user requirement.
