# Catalyst Finance v1.2.0 Export Specification

Catalyst Finance produces two related JSON artifact families.

## Scenario publication

A scenario publication contains the validated input, calculated results, interpretation, narrative, methodology, timestamp, disclaimer, and optional migration record. It validates against `finance_publication.schema.json`.

## Workspace export

A workspace export contains:

```json
{
  "export_contract_version": "1.2.0",
  "exported_at": "ISO-8601 timestamp",
  "workspace": {}
}
```

The nested workspace includes defaults, projects, scenarios, all revisions, statuses, tags, notes, immutable identifiers, timestamps, and model-version references. It validates against `finance_workspace_export.schema.json`.

Import must preserve every workspace, project, scenario, and revision identifier. Replacing an existing workspace requires an explicit `replace` instruction.
