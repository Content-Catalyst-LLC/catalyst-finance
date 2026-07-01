# Catalyst Finance

Catalyst Finance is an open-source financial scenario and decision-support workspace for Sustainable Catalyst. It helps frame investments, costs, benefits, risks, emissions impacts, and review notes in a way that remains transparent, reproducible, and auditable.

> Educational software only. This repository does not provide investment, legal, tax, accounting, assurance, or financial advice.

## What this repository contains

- A browser-based WordPress demo plugin: `[catalyst_finance_demo]`
- A lightweight Python finance-scenario engine
- JSON schema for scenario exports
- Sample input and example outputs
- Methodology, export, and review documentation
- Tests and GitHub Actions workflow

## Core workflow

```text
initiative -> cost -> benefits -> assumptions -> risk adjustment -> interpretation -> review note -> export
```

Catalyst Finance is designed for practical questions such as:

- What are the upfront and recurring costs?
- What recurring savings or benefits are expected?
- What assumptions drive the result?
- How sensitive is the case to risk, confidence, and discounting?
- What should be reviewed before communicating the result?

## Quickstart: Python scenario brief

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python python/catalyst_finance_core.py \
  --input data/sample_finance_scenario.json \
  --json-out outputs/sample_finance_scenario.output.json \
  --markdown-out outputs/sample_finance_scenario.output.md
```

## Run tests

```bash
python3 -m pytest -q
```

## WordPress demo

The plugin source is in:

```text
wordpress/catalyst-finance-demo/
```

Upload the generated zip from `dist/catalyst-finance-demo.zip`, activate it, and add this shortcode to the Catalyst Finance page:

```text
[catalyst_finance_demo]
```

The demo runs in the browser. It does not submit visitor inputs to Sustainable Catalyst.

## Repository layout

```text
.github/workflows/          CI workflow
app.py                      Legacy CLI utility retained for continuity
data/                       Sample scenario input
schemas/                    JSON schema for exported finance scenarios
python/                     Scenario engine and CLI
examples/                   Example JSON and Markdown outputs
docs/                       Methodology and implementation notes
tests/                      Lightweight validation tests
wordpress/                  WordPress shortcode demo plugin
outputs/                    Generated local outputs, ignored by git
dist/                       Built plugin zip, ignored by git
```

## Boundaries

Catalyst Finance supports structured financial reasoning. It does not provide investment advice, accounting advice, tax advice, lending decisions, valuation opinions, assurance, or fiduciary recommendations. Any real decision requires qualified review, better data, and context-specific judgment.

## License

MIT. See `LICENSE` if present.
