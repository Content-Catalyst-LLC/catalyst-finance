# Catalyst Finance

Catalyst Finance is an open-source financial scenario, cash-flow, and decision-support workspace for Sustainable Catalyst. It keeps assumptions, period schedules, methodology, metric traces, workspace history, and review boundaries visible and reproducible.

> Educational software only. This repository does not provide investment, legal, tax, accounting, fiduciary, assurance, lending, procurement, funding, or financial advice.

## v2.0.0 — Connected Financial Decision Intelligence Platform

The v2.0.0 release adds a ninth canonical engine that connects governed finance artifacts to decision cases, product capabilities, dependency graphs, and classification-controlled handoffs. It aggregates designated value-bearing artifacts without counting comparison, evidence, governance, or publication derivatives twice.

The platform contract preserves product ownership, model and contract versions, workspace and revision identifiers, artifact checksums, information classifications, governance states, and transfer outcomes. Portfolio totals, case readiness, product health, dependency order, and integration warnings are calculated from explicit records rather than hidden orchestration.

```bash
catalyst-finance-platform data/sample_platform.json \
  --output outputs/sample_platform.output.json \
  --manifest outputs/sample_platform.integration-manifest.json
```

The API endpoint is `POST /api/v1/platform/evaluate`. The WordPress shortcode remains `[catalyst_finance_workspace]` and now includes the Connected Platform Studio alongside the eight established finance studios. Governed handoffs support Decision Studio, Knowledge Library, Site Intelligence, Research Lab, Workbench, Catalyst Canvas, and other registered Sustainable Catalyst products while enforcing classification and approval rules.

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
POST /api/v1/pricing/evaluate
POST /api/v1/operating/evaluate
POST /api/v1/sustainable/evaluate
POST /api/v1/governance/evaluate
POST /api/v1/platform/evaluate
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
dist/catalyst-finance-demo-v2.0.0.zip
```

Shortcodes:

```text
[catalyst_finance_workspace]
[catalyst_finance_demo]
[catalyst_finance_demo mode="public"]
```

The module includes persistent screening, capital budgeting, comparison, uncertainty, pricing, operating-economics, sustainable-finance, governance/publication, and connected-platform studios with contract-valid local exports.

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
- `schemas/pricing_definition.schema.json`
- `schemas/pricing_publication.schema.json`
- `schemas/operating_definition.schema.json`
- `schemas/operating_publication.schema.json`
- `schemas/sustainable_definition.schema.json`
- `schemas/sustainable_publication.schema.json`
- `schemas/governance_definition.schema.json`
- `schemas/governance_publication.schema.json`
- `schemas/platform_definition.schema.json`
- `schemas/platform_publication.schema.json`
- `examples/sample_cash_flow_scenario.output.json`
- `examples/sample_cash_flow_scenario.periods.csv`
- `examples/sample_finance_workspace.export.json`
- `examples/sample_comparison.output.json`
- `examples/sample_uncertainty.output.json`
- `examples/sample_uncertainty.summary.csv`
- `examples/sample_pricing.output.json`
- `examples/sample_pricing.curve.csv`
- `examples/sample_operating.output.json`
- `examples/sample_operating.summary.csv`
- `examples/sample_governance.output.json`
- `examples/sample_governance.public.json`
- `examples/sample_platform.output.json`
- `examples/sample_platform.integration-manifest.json`

## Validation

```bash
python scripts/check_release.py
```

The release gate checks synchronized versions, generated schemas, reproducible publications for all nine engines, complete v1.9.0 migration coverage, JSON/SQLite workspace behavior, API lifecycle operations, classification-gated handoffs, portfolio aggregation without derivative double counting, exact Python/JavaScript parity across all nine engines, Ruff, formatting, strict Mypy, PHP, JavaScript, and deterministic ZIP integrity.

## Product boundary

Catalyst Finance supports structured financial reasoning and scenario review. It does not make autonomous investment, lending, pricing, procurement, funding, tax, accounting, or fiduciary decisions. Real decisions require qualified human review, context-specific evidence, and appropriate professional advice.

## License

MIT. See `LICENSE`.
