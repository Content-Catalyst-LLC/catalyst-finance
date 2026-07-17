# Changelog

## 1.2.0 — 2026-07-17

- Added versioned persistent workspaces, projects, scenarios, alternatives, notes, tags, status, and append-only revisions.
- Added atomic JSON and SQLite repositories behind one protocol.
- Added autosave recovery, explicit save, identifier-preserving import/export, templates, workspace CLI, and API routes.
- Upgraded the WordPress module to a multi-scenario local workspace with public read-only mode.
- Added v1.1.0 migration and expanded release validation to workspace contracts.

## 1.1.0 — 2026-07-17

- Added strict versioned input, result, interpretation, metadata, and publication contracts.
- Added explicit currency, price basis, discount-rate basis, annual frequency, end-of-period timing, and half-up rounding policy.
- Replaced the prototype dataclasses with validated Pydantic contract records and structured validation issues.
- Added the stable `catalyst-finance.screening` model registry and methodology version.
- Separated financial calculations, interpretation rules, and user-facing narrative.
- Replaced the opaque score formula with four disclosed weighted components and contribution trace.
- Defined fractional-horizon, overfunding, zero-cost, negative-rate, missing-emissions, and non-positive-benefit behavior.
- Added canonical and legacy fixtures, v1.0.0 migration, and field-preservation metadata.
- Added a shared browser calculation engine and exact Python/JavaScript parity tests.
- Added API model-registry and evaluation routes.

## 1.0.1 — 2026-07-17

- Created one installable `catalyst_finance` package and release version contract.
- Added the FastAPI application boundary, health route, and version route.
- Isolated the legacy elasticity utility and preserved compatibility commands.
- Added `pyproject.toml`, console scripts, one CI matrix, static checks, and release validation.
- Added deterministic example reproduction and WordPress plugin packaging.
- Strengthened the scenario export schema and release metadata.
- Moved generated elasticity outputs into explicit example fixtures.
- Repaired the release gate for Ruff 0.15 by resolving two `SIM910` findings in the elasticity utility.

## 1.0.0 — 2026-07-01

- Added the Catalyst Finance WordPress online demo plugin.
- Added the browser scenario calculator and JSON export.
- Added the Python finance-scenario engine.
- Added sample input data, example outputs, schema, methodology, review notes, and tests.
