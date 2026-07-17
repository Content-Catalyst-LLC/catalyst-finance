# Catalyst Finance v1.1.0 Export Specification

Canonical input validates against `schemas/finance_input.schema.json`. Complete publications validate against `schemas/finance_publication.schema.json` and the compatibility alias `schemas/finance_scenario.schema.json`.

The publication contains:

- `contract_version` and `model_id`
- `project`
- `context`
- `assumptions`
- `results`, including a complete score trace
- `interpretation`
- `narrative`
- `methodology`
- `metadata`, including optional migration provenance

Component schemas are also published for results, interpretation, and metadata. All contracts reject undeclared properties.

The CLI's `--generated-at` option exists only for reproducible fixtures and tests. Ordinary exports use the current UTC time.
