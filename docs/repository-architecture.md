# Repository Architecture

Catalyst Finance v1.3.0 separates five boundaries:

1. Scenario contracts and migration.
2. Pure calculation, interpretation, and narrative.
3. Workspace lifecycle and revision history.
4. Repository adapters for JSON and SQLite.
5. API, CLI, and WordPress delivery surfaces.

`WorkspaceService` depends on the `WorkspaceRepository` protocol, not on a concrete storage system. The browser workspace implements the same document and revision concepts using local browser storage while the calculation engine remains parity-tested against Python.

The annual screening engine is unchanged in scope. Period-level cash flows belong to v1.3.0.
