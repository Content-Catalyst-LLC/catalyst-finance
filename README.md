# Catalyst Finance

Catalyst Finance is an open-source financial scenario and decision-support workspace for Sustainable Catalyst. It keeps costs, benefits, assumptions, methodology, risk, interpretation, narrative, and review boundaries visible and reproducible.

> Educational software only. This repository does not provide investment, legal, tax, accounting, fiduciary, assurance, lending, procurement, funding, or financial advice.

## v1.1.0 — Canonical Finance Contract and Shared Calculation Engine

This release establishes one authoritative annual screening model shared by Python, FastAPI, the command line, WordPress, fixtures, and exports.

- Strict v1.1.0 input and publication contracts with explicit currency, price basis, discount-rate basis, frequency, timing, and rounding policy.
- Validated Pydantic records with structured validation issues.
- Stable model identifier `catalyst-finance.screening` and methodology version `1.1.0`.
- Separate calculation, interpretation, and narrative modules.
- A transparent four-component review score with disclosed weights and contributions.
- Explicit policies for fractional horizons, overfunding, zero-cost ratios, negative rates, missing emissions, and non-positive benefits.
- Automatic migration of the original v1.0.0 `{project, inputs}` scenario shape.
- Exact Python/JavaScript parity tests for canonical and migrated fixtures.
- API model registry and evaluation routes.

## Install for development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

The plotting dependency for the compatibility elasticity utility is optional:

```bash
python -m pip install -e '.[plots]'
```

## Canonical scenario input

```json
{
  "contract_version": "1.1.0",
  "model_id": "catalyst-finance.screening",
  "project": {"name": "Building efficiency retrofit", "category": "Energy efficiency"},
  "context": {
    "currency": "USD",
    "price_basis": "nominal",
    "discount_rate_basis": "nominal",
    "period_frequency": "annual",
    "time_basis": "end_of_period",
    "rounding_policy": "half_up",
    "monetary_decimals": 2,
    "ratio_decimals": 2,
    "score_decimals": 1
  },
  "assumptions": {}
}
```

See `data/sample_finance_scenario.json` for a complete fixture. Legacy v1.0.0 input remains accepted and is migrated with a preservation record.

## Scenario CLI

```bash
catalyst-finance \
  --input data/sample_finance_scenario.json \
  --json-out outputs/sample_finance_scenario.output.json \
  --markdown-out outputs/sample_finance_scenario.output.md
```

The pre-v1.0.1 wrapper remains available:

```bash
python python/catalyst_finance_core.py --input data/legacy_v1.0.0_scenario.json
```

## API

```bash
catalyst-finance-api --host 127.0.0.1 --port 8000
```

Routes:

```text
GET  /healthz
GET  /api/v1/version
GET  /api/v1/models
GET  /api/v1/models/catalyst-finance.screening
POST /api/v1/evaluate
```

## WordPress

```bash
python scripts/build_plugin.py --versioned-copy
```

Packages:

```text
dist/catalyst-finance.zip
dist/catalyst-finance-demo-v1.1.0.zip
```

Activate the plugin and use:

```text
[catalyst_finance_demo]
```

The browser UI uses the same contract, calculation rules, score weights, methodology metadata, and migration behavior as Python.

## Validation

```bash
python scripts/check_release.py
```

The release contract checks versions, schemas, generated fixtures, Python/JavaScript parity, migration preservation, API smoke behavior, Ruff, formatting, Mypy, PHP, JavaScript, and deterministic ZIP integrity.

## Product boundary

Catalyst Finance supports structured financial reasoning and screening. It does not make autonomous investment, lending, pricing, procurement, funding, tax, accounting, or fiduciary decisions. Real decisions require qualified human review, context-specific evidence, and appropriate professional advice.

## License

MIT. See `LICENSE`.
