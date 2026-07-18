# Connected Financial Decision Intelligence Platform

Catalyst Finance v2.0.0 adds a connected platform contract above the individual finance engines. The platform does not replace the underlying screening, cash-flow, comparison, uncertainty, pricing, operating, sustainable-finance, or governance publications. It links versioned artifacts from those models—and from other Sustainable Catalyst products—into reviewable decision cases.

## What the platform connects

A platform definition contains:

- a registry of connected products, versions, roles, supported contracts, operating status, and accepted data classifications;
- immutable artifact and revision references with source-product ownership, model identity, SHA-256 checksums, governance state, and classification;
- decision cases that group the artifacts needed for one institutional choice;
- an acyclic dependency graph showing which evidence, computation, intelligence, and finance outputs inform later artifacts;
- cross-product handoff envelopes with source, target, contract, revision, classification, status, payload hash, and destination identifiers;
- portfolio and publication policies.

## Portfolio aggregation

Only artifacts with `include_in_portfolio: true` contribute to portfolio value. Derived comparison, evidence, and governance artifacts can remain in the dependency graph without counting the same economics a second time.

For every included artifact, the platform carries:

- base NPV;
- adjusted NPV;
- capital required;
- annual value;
- confidence percentage;
- downside probability.

Risk-adjusted value is disclosed as:

```text
adjusted NPV × confidence × (1 − downside probability)
```

The platform does not convert or net multiple currencies. A mixed-currency portfolio is flagged instead of being presented as a comparable total.

## Decision-case readiness

Each case is evaluated against four visible dimensions:

1. artifact approval or publication;
2. governance approval or publication;
3. required product handoff completion;
4. artifact confidence relative to the platform policy.

The resulting status is `blocked`, `ready_for_review`, `decision_ready`, or `decided`. Blocking reasons remain machine-readable.

## Handoff governance

Accepted and completed handoffs must use a classification allowed by the target product. Completed handoffs can also be configured to require an approved artifact and approved governance state. Rejected or failed handoffs remain in the publication so institutional operators can see why a connection did not complete.

Examples include:

- Site Intelligence signal to Catalyst Finance;
- Workbench calculation run to Catalyst Finance;
- Catalyst Finance governed artifact to Decision Studio;
- public finance brief to Knowledge Library.

## Dependency graph

The platform rejects circular dependencies. A deterministic topological order is included in every publication, allowing downstream systems to process upstream evidence and calculations before dependent finance and governance artifacts.

## Reproducibility

Every publication includes:

- canonical input SHA-256;
- output SHA-256;
- dependency-order hash;
- deterministic run identifier;
- integration manifest containing products, artifacts, cases, API routes, and handoff contracts.

Use a fixed `generated_at` value when reproducing a checked-in example.

## CLI

```bash
catalyst-finance-platform data/sample_platform.json \
  --output outputs/sample_platform.output.json \
  --generated-at 2026-07-17T18:30:00+00:00
```

## API

```text
POST /api/v1/platform/evaluate
```

The persistent workspace also supports create, revise, and delete operations under:

```text
/api/v1/workspaces/{workspace_id}/platform-analyses
```

## WordPress

The `[catalyst_finance_workspace]` shortcode includes the Financial Decision Intelligence Platform studio. The browser engine uses the same aggregation, readiness, dependency, product-health, handoff, and run-record contract as Python.

## Boundary

The connected platform is an orchestration and decision-support layer. It does not authorize access to another product, transmit secrets, replace source-system security, certify accounting treatment, provide assurance, or make the institutional decision.
