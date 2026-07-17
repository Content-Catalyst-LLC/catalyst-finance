# Contributing

Catalyst Finance welcomes improvements that make financial reasoning more transparent, reproducible, reviewable, and responsible.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Required checks

```bash
python -m pytest -q
python scripts/check_release.py
```

The release contract runs formatting, linting, type, schema, fixture, packaging, API smoke, JavaScript, and PHP checks. It also confirms that no transient build state remains in the repository.

## Style

Use clear variable names, explicit units, plain-language interpretation notes, and deterministic fixtures. New finance calculations belong in the canonical `catalyst_finance` package. Do not add new logic to the compatibility wrapper under `python/`.

## Boundaries

Do not add features that imply autonomous investment, pricing, lending, procurement, funding, accounting, tax, legal, fiduciary, or assurance decisions. Outputs must remain explainable and subject to qualified human review.
