# Catalyst Finance

Catalyst Finance is an open-source financial scenario and decision-support workspace for Sustainable Catalyst. It keeps costs, benefits, assumptions, risk, emissions value, interpretation, and review boundaries visible and reproducible.

> Educational software only. This repository does not provide investment, legal, tax, accounting, fiduciary, assurance, lending, or financial advice.

## v1.0.1 release foundation

Catalyst Finance v1.0.1 repairs the prototype repository before new finance models are added. The release provides:

- one installable Python package and version contract;
- a canonical scenario CLI;
- a named demand and elasticity compatibility CLI;
- a FastAPI application boundary with `/healthz` and `/api/v1/version`;
- one Python 3.10–3.13 CI workflow;
- deterministic scenario examples and WordPress packaging;
- JSON, Python, PHP, JavaScript, package, and release-contract checks;
- a clean separation between source files and generated elasticity artifacts.

## Install for development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

The plotting dependency is optional:

```bash
python -m pip install -e '.[plots]'
```

## Scenario CLI

```bash
catalyst-finance \
  --input data/sample_finance_scenario.json \
  --json-out outputs/sample_finance_scenario.output.json \
  --markdown-out outputs/sample_finance_scenario.output.md
```

The pre-v1.0.1 command remains available:

```bash
python python/catalyst_finance_core.py --input data/sample_finance_scenario.json
```

## API boundary

```bash
catalyst-finance-api --host 127.0.0.1 --port 8000
```

Or:

```bash
uvicorn app:app --reload
```

System routes:

```text
GET /healthz
GET /api/v1/version
```

## Demand and elasticity compatibility utility

```bash
catalyst-finance-elasticity observed \
  --input examples/elasticity/input/observed_sample.csv \
  --output outputs/observed_results.csv

catalyst-finance-elasticity linear \
  --a 100 --b 2 \
  --p-start 5 --p-end 45 --p-step 5 \
  --output outputs/linear_results.csv
```

Add `--plots --plot-dir outputs/plots` after installing the `plots` extra.

## Validation and packaging

```bash
python scripts/check_release.py
python scripts/build_plugin.py --versioned-copy
```

The canonical WordPress package is:

```text
dist/catalyst-finance.zip
```

The versioned package is:

```text
dist/catalyst-finance-demo-v1.0.1.zip
```

Activate the plugin and use:

```text
[catalyst_finance_demo]
```

## Repository layout

```text
catalyst_finance/           Installable package, API, CLIs, and domain core
python/                     Backward-compatible pre-v1.0.1 wrapper
schemas/                    Scenario export schema
data/                       Canonical sample scenario input
examples/                   Reproducible outputs and legacy elasticity fixtures
docs/                       Methodology and implementation notes
scripts/                    Validation, smoke, reproduction, and package builders
tests/                      Domain, API, CLI, and elasticity tests
wordpress/                  WordPress shortcode plugin source
release/                    Versioned release notes
outputs/                    Ignored local outputs
dist/                       Ignored generated packages
```

## Product boundary

Catalyst Finance supports structured financial reasoning and screening. It does not provide autonomous investment, lending, pricing, procurement, funding, tax, accounting, or fiduciary decisions. Real decisions require qualified human review, context-specific evidence, and appropriate professional advice.

## License

MIT. See `LICENSE`.
