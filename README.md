# Catalyst Finance

Catalyst Finance is an open-source financial scenario, cash-flow, and decision-support workspace for Sustainable Catalyst. It keeps assumptions, period schedules, methodology, metric traces, workspace history, and review boundaries visible and reproducible.

> Educational software only. This repository does not provide investment, legal, tax, accounting, fiduciary, assurance, lending, procurement, funding, or financial advice.

## v1.5.0 — Uncertainty, Monte Carlo, and Stress Testing

Catalyst Finance now adds a transparent probability and adverse-case layer to the canonical cash-flow engine. The uncertainty model supports seeded Monte Carlo simulation, five distribution types, explicit correlation, percentiles, downside probabilities, lower-tail value-at-risk, expected shortfall, histograms, variable influence, named multi-factor stress cases, reproducibility keys, workspace revisions, API/CLI execution, and exact Python/JavaScript parity.

```bash
catalyst-finance-uncertainty data/sample_uncertainty.json \
  --output outputs/sample_uncertainty.output.json \
  --summary-csv outputs/sample_uncertainty.summary.csv
```

The API endpoint is `POST /api/v1/uncertainty/evaluate`. The WordPress shortcode remains `[catalyst_finance_workspace]` and now includes the uncertainty and stress-testing studio.

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

## Annual screening model

```bash
catalyst-finance \
  --input data/sample_finance_scenario.json \
  --json-out outputs/sample_finance_scenario.output.json \
  --markdown-out outputs/sample_finance_scenario.output.md
```

## Cash-flow and capital-budgeting model

```bash
catalyst-finance-cashflow \
  data/sample_cash_flow_scenario.json \
  --json-output outputs/sample_cash_flow_scenario.output.json \
  --markdown-output outputs/sample_cash_flow_scenario.output.md \
  --csv-output outputs/sample_cash_flow_scenario.periods.csv
```

The cash-flow input contract uses non-negative amounts plus explicit categories. The engine applies the sign convention, expands recurring schedules, validates basis consistency, and records exactly which flows feed every metric.

## Persistent workspace CLI

JSON directory adapter:

```bash
catalyst-finance-workspace \
  --directory ~/.catalyst-finance/workspaces \
  create "Facilities investment review"
```

SQLite adapter:

```bash
catalyst-finance-workspace \
  --sqlite ~/.catalyst-finance/finance.sqlite3 \
  list
```

Screening and cash-flow scenarios can both be preserved in append-only workspace revisions. Workspace import/export retains identifiers and revision history.

## API

```bash
catalyst-finance-api --host 127.0.0.1 --port 8000
```

Core routes:

```text
GET  /healthz
GET  /api/v1/version
GET  /api/v1/models
POST /api/v1/evaluate
POST /api/v1/cash-flow/evaluate
POST /api/v1/compare
POST /api/v1/uncertainty/evaluate
GET  /api/v1/templates
GET  /api/v1/workspaces
POST /api/v1/workspaces
POST /api/v1/workspaces/import
GET  /api/v1/workspaces/{workspace_id}
DELETE /api/v1/workspaces/{workspace_id}
POST /api/v1/workspaces/{workspace_id}/projects
POST /api/v1/workspaces/{workspace_id}/scenarios
POST /api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/revisions
POST /api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/duplicate
POST /api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/archive
POST /api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/restore
```

Set `CATALYST_FINANCE_WORKSPACE_DIR` to change the API JSON repository location.

## WordPress

Build the plugin:

```bash
python scripts/build_plugin.py --versioned-copy
```

Packages:

```text
dist/catalyst-finance.zip
dist/catalyst-finance-demo-v1.5.0.zip
```

Shortcodes:

```text
[catalyst_finance_workspace]
[catalyst_finance_demo]
[catalyst_finance_demo mode="public"]
```

The module includes the persistent screening workspace and a capital-budgeting studio with cash-flow tables, cumulative curves, period waterfalls, metric explanations, and contract-valid JSON exports.

## Contracts and examples

- `schemas/finance_input.schema.json`
- `schemas/finance_publication.schema.json`
- `schemas/cash_flow_input.schema.json`
- `schemas/cash_flow_publication.schema.json`
- `schemas/finance_workspace.schema.json`
- `schemas/finance_workspace_export.schema.json`
- `schemas/comparison_definition.schema.json`
- `schemas/comparison_publication.schema.json`
- `schemas/uncertainty_definition.schema.json`
- `schemas/uncertainty_publication.schema.json`
- `examples/sample_cash_flow_scenario.output.json`
- `examples/sample_cash_flow_scenario.periods.csv`
- `examples/sample_finance_workspace.export.json`
- `examples/sample_comparison.output.json`
- `examples/sample_uncertainty.output.json`
- `examples/sample_uncertainty.summary.csv`

## Validation

```bash
python scripts/check_release.py
```

The release gate checks synchronized versions, generated schemas, reproducible screening and cash-flow fixtures, all three screening migration paths, JSON/SQLite workspace behavior, API lifecycle operations, exact Python/JavaScript parity for screening, cash-flow, comparison, and uncertainty models, Ruff, formatting, strict Mypy, PHP, JavaScript, and deterministic ZIP integrity.

## Product boundary

Catalyst Finance supports structured financial reasoning and scenario review. It does not make autonomous investment, lending, pricing, procurement, funding, tax, accounting, or fiduciary decisions. Real decisions require qualified human review, context-specific evidence, and appropriate professional advice.

## License

MIT. See `LICENSE`.
