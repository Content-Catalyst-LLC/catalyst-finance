# Changelog

## 1.6.0 — 2026-07-17

- Added a canonical demand, elasticity, pricing, and revenue model with linear, constant-elasticity, and observed demand curves.
- Added multi-segment aggregation, proportional capacity allocation, cost-to-serve, break-even quantity, and contribution-margin analysis.
- Added revenue, contribution, and operating-profit optima plus current-price recommendations and price-change constraints.
- Added pricing schemas, examples, CLI, FastAPI routes, workspace revisions, exact browser parity, and a WordPress pricing studio.
- Added v1.5.0 migration support and expanded the full release contract.

## 1.5.0 — 2026-07-17

- Added seeded Monte Carlo simulation with uniform, triangular, normal, lognormal, and discrete distributions.
- Added Gaussian-copula correlation with Cholesky validation, deterministic Python/JavaScript parity, and reproducibility keys.
- Added percentiles, downside probabilities, lower-tail value-at-risk, expected shortfall, histograms, retained samples, and variable influence rankings.
- Added named multi-factor stress cases, uncertainty API/CLI surfaces, schemas, examples, workspace revisions, and a WordPress uncertainty studio.
- Added v1.4.0 scenario, comparison, and workspace migration support.

## 1.4.0 — 2026-07-17

- Added revision-linked alternative comparison with aligned metrics, deltas, weighted rankings, and financial Pareto dominance.
- Added one-way and two-way sensitivity, bounded break-even search, tornado data, crossover detection, and assumption-driver explanations.
- Added versioned workspace comparison artifacts, comparison API/CLI surfaces, four export formats, browser parity, and a WordPress comparison studio.
- Added v1.3.0 screening and cash-flow migration support.

## 1.3.0 — 2026-07-17

- Added monthly, quarterly, and annual period cash-flow contracts and calculation services.
- Added phased and irregular capital, operating, benefit, grant, rebate, working-capital, residual, and decommissioning schedules.
- Added nominal/real basis validation, escalation, effective rate conversion, and period reconciliation.
- Added NPV, simple and discounted payback, IRR root detection and ambiguity flags, MIRR, profitability index, benefit-cost ratio, equivalent annual value, and terminal value.
- Added machine-readable metric traces with included categories, excluded categories, source flow IDs, formulas, and review notes.
- Added conventional, irregular, negative, zero-cost, and multiple-sign-change benchmark fixtures.
- Added cash-flow CLI exports, FastAPI evaluation, workspace revision support, exact JavaScript parity, and a WordPress capital-budgeting studio.
- Added v1.2.0 screening migration and expanded release validation.

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
