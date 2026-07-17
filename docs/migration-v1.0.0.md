# v1.0.0 Scenario Migration

Inputs with top-level `project` and `inputs` records and no `contract_version` are treated as v1.0.0 scenarios.

Migration:

1. Preserves every project and input value.
2. Renames `inputs` to `assumptions`.
3. Adds the v1.1.0 contract and model identifiers.
4. Adds the default USD nominal annual end-of-period context.
5. Adds a metadata migration record listing all preserved legacy fields.

Invalid legacy values are rejected by the same v1.1.0 validation rules; migration does not silently repair financially material assumptions.
