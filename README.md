# Catalyst Finance

Catalyst Finance is an open-source financial scenario and decision-support workspace for Sustainable Catalyst. It keeps costs, benefits, assumptions, methodology, risk, interpretation, narrative, workspace history, and review boundaries visible and reproducible.

> Educational software only. This repository does not provide investment, legal, tax, accounting, fiduciary, assurance, lending, procurement, funding, or financial advice.

## v1.2.0 — Persistent Scenarios and Workspace Management

This release turns the canonical finance model into a reusable workspace rather than a disposable calculator.

- Versioned workspace, project, scenario, alternative, note, tag, status, and revision contracts.
- Immutable workspace, project, scenario, and revision identifiers.
- Explicit save and append-only scenario revision history.
- Atomic JSON persistence and SQLite persistence behind one repository interface.
- Autosave recovery that does not overwrite the last explicit save.
- Complete workspace import/export without identifier loss.
- Create, duplicate, rename, archive, restore, import, export, and delete operations.
- Five templates: capital project, operating change, pricing decision, sustainability investment, and public-value initiative.
- Workspace defaults for currency, locale, time basis, price basis, discount-rate basis, model ID, and model version.
- FastAPI workspace endpoints and a `catalyst-finance-workspace` command.
- A multi-scenario WordPress browser workspace with `localStorage` persistence and a public read-only mode.
- Migration of v1.0.0 and v1.1.0 scenario inputs into the v1.2.0 contract.

The annual screening calculation model remains intentionally stable in this release. Period-by-period cash-flow modeling begins in v1.3.0.

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

## Evaluate one scenario

```bash
catalyst-finance \
  --input data/sample_finance_scenario.json \
  --json-out outputs/sample_finance_scenario.output.json \
  --markdown-out outputs/sample_finance_scenario.output.md
```

Legacy v1.0.0 and v1.1.0 inputs are migrated with a preservation record.

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

Typical lifecycle:

```bash
catalyst-finance-workspace --directory ./workspaces create "Portfolio review"
catalyst-finance-workspace --directory ./workspaces add-scenario WORKSPACE_ID "Retrofit" --template sustainability-investment
catalyst-finance-workspace --directory ./workspaces export WORKSPACE_ID workspace-export.json
catalyst-finance-workspace --directory ./restored import workspace-export.json
```

The Python service also supports projects, revision saves, autosave recovery, duplication, rename, archive, restore, metadata updates, and deletion.

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
dist/catalyst-finance-demo-v1.2.0.zip
```

Persistent browser workspace:

```text
[catalyst_finance_workspace]
```

Equivalent primary shortcode:

```text
[catalyst_finance_demo]
```

Public read-only demonstration:

```text
[catalyst_finance_demo mode="public"]
```

Browser workspace data is stored only in that browser until the user exports or deletes it. The browser engine retains exact Python calculation parity.

## Contracts and examples

- `schemas/finance_input.schema.json`
- `schemas/finance_publication.schema.json`
- `schemas/finance_workspace.schema.json`
- `schemas/finance_workspace_export.schema.json`
- `schemas/finance_workspace_scenario.schema.json`
- `schemas/finance_scenario_template.schema.json`
- `examples/sample_finance_workspace.export.json`

## Validation

```bash
python scripts/check_release.py
```

The release gate checks versions, generated schemas, reproducible scenario and workspace fixtures, both migration paths, JSON/SQLite behavior, autosave recovery, API lifecycle operations, Python/JavaScript parity, Ruff, formatting, Mypy, PHP, JavaScript, and deterministic ZIP integrity.

## Product boundary

Catalyst Finance supports structured financial reasoning and screening. It does not make autonomous investment, lending, pricing, procurement, funding, tax, accounting, or fiduciary decisions. Real decisions require qualified human review, context-specific evidence, and appropriate professional advice.

## License

MIT. See `LICENSE`.
