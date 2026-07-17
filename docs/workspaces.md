# Persistent Workspace Contract

Catalyst Finance v1.9.0 stores a complete decision workspace as a versioned document.

## Hierarchy

- Workspace: defaults, projects, scenarios, status, timestamps.
- Project: optional organizational container for related scenarios.
- Scenario: named alternative, notes, tags, status, and revision chain.
- Revision: immutable ID, ordered revision number, model reference, timestamp, change note, and canonical scenario input.

A scenario revision is appended. Existing revision IDs and payloads are never mutated by the workspace service.

## Repositories

`JsonWorkspaceRepository` writes one canonical JSON file per workspace using a temporary file, `fsync`, and atomic replacement. Autosaves use a separate `.autosave.json` recovery file.

`SQLiteWorkspaceRepository` stores the same contract-valid JSON payload in SQLite. The adapter does not change the workspace document shape.

Both implement `WorkspaceRepository`, so the application service and tests are storage-independent.

## Save behavior

- Explicit save appends a revision, writes the canonical workspace, and clears recovery state.
- Autosave appends a recovery revision only in the autosave store.
- Recovery is offered only when the recovery workspace is at least as recent as the explicit save.
- Committing recovery promotes the recovered document to the canonical store.

## Import and export

`WorkspaceExport` wraps the complete workspace with an export version and timestamp. Import validates the entire document and preserves all identifiers. Existing IDs require an explicit replace operation.
