# Export Specification

Catalyst Finance scenario exports conform to `schemas/finance_scenario.schema.json`.

The top-level records are:

- `project`
- `inputs`
- `results`
- `interpretation`
- `metadata`

The v1.0.1 metadata record includes a generation timestamp, tool name, release version, and educational-use disclaimer. The Python CLI accepts `--generated-at` only to reproduce fixtures and tests; ordinary exports use the current UTC time.

v1.0.1 validates repository examples and package integrity. A fully versioned cross-runtime contract, units policy, migration layer, and browser parity suite are scheduled for v1.1.0.
