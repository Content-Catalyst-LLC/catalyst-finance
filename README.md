# Catalyst Finance

Catalyst Finance is an open-source financial scenario, cash-flow, and decision-support workspace for Sustainable Catalyst. It keeps assumptions, period schedules, methodology, metric traces, workspace history, and review boundaries visible and reproducible.

> Educational software only. This repository does not provide investment, legal, tax, accounting, fiduciary, assurance, lending, procurement, funding, or financial advice.

## v1.3.0 — Cash-Flow Modeling and Capital Budgeting

This release adds a defensible period-by-period model while retaining the annual screening model and persistent v1.2.0 workspace.

- Monthly, quarterly, and annual cash-flow schedules.
- Initial and phased capital costs; recurring and irregular operating costs; revenue, savings, avoided costs, grants, rebates, residual value, decommissioning, working capital, and recovery.
- Nominal/real basis matching and effective annual-to-period discount conversion.
- Recurrence intervals and annual escalation.
- NPV, simple and discounted payback, IRR roots and ambiguity status, MIRR, profitability index, benefit-cost ratio, equivalent annual value, cumulative cash flow, and terminal value.
- Metric traces listing included and excluded categories, source flow IDs, formulas, and notes.
- Conventional, irregular, negative, zero-cost, and multiple-sign-change benchmark fixtures.
- Cash-flow CLI, FastAPI endpoint, workspace revision persistence, exact Python/JavaScript parity, and a WordPress capital-budgeting studio with tables and charts.
- Screening migrations from v1.0.0, v1.1.0, and v1.2.0.

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
dist/catalyst-finance-demo-v1.3.0.zip
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
- `examples/sample_cash_flow_scenario.output.json`
- `examples/sample_cash_flow_scenario.periods.csv`
- `examples/sample_finance_workspace.export.json`

## Validation

```bash
python scripts/check_release.py
```

The release gate checks synchronized versions, generated schemas, reproducible screening and cash-flow fixtures, all three screening migration paths, JSON/SQLite workspace behavior, API lifecycle operations, exact Python/JavaScript parity for both models, Ruff, formatting, strict Mypy, PHP, JavaScript, and deterministic ZIP integrity.

## Product boundary

Catalyst Finance supports structured financial reasoning and scenario review. It does not make autonomous investment, lending, pricing, procurement, funding, tax, accounting, or fiduciary decisions. Real decisions require qualified human review, context-specific evidence, and appropriate professional advice.

## License

MIT. See `LICENSE`.
