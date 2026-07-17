"""Persistence adapters for Catalyst Finance workspaces."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Protocol, cast

from .workspace_migration import migrate_workspace_payload
from .workspace_models import FinanceWorkspace


class WorkspaceNotFoundError(KeyError):
    """Raised when a requested workspace does not exist."""


class WorkspaceRepository(Protocol):
    """Storage boundary shared by local JSON and SQLite adapters."""

    def list(self) -> list[FinanceWorkspace]: ...

    def get(self, workspace_id: str) -> FinanceWorkspace: ...

    def save(self, workspace: FinanceWorkspace) -> FinanceWorkspace: ...

    def delete(self, workspace_id: str) -> None: ...

    def save_autosave(self, workspace: FinanceWorkspace) -> FinanceWorkspace: ...

    def recover_autosave(self, workspace_id: str) -> FinanceWorkspace | None: ...

    def clear_autosave(self, workspace_id: str) -> None: ...


def _payload(workspace: FinanceWorkspace) -> str:
    return json.dumps(workspace.model_dump(mode="json"), indent=2) + "\n"


class JsonWorkspaceRepository:
    """Directory-backed repository with atomic writes and recovery snapshots."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, workspace_id: str) -> Path:
        return self.directory / f"{workspace_id}.json"

    def _autosave_path(self, workspace_id: str) -> Path:
        return self.directory / f"{workspace_id}.autosave.json"

    @staticmethod
    def _read(path: Path) -> FinanceWorkspace:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("workspace payload must be a JSON object")
        return cast(
            FinanceWorkspace,
            FinanceWorkspace.model_validate(migrate_workspace_payload(payload)),
        )

    @staticmethod
    def _write_atomic(path: Path, workspace: FinanceWorkspace) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(_payload(workspace))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def list(self) -> list[FinanceWorkspace]:
        records = [
            self._read(path)
            for path in sorted(self.directory.glob("workspace_*.json"))
            if not path.name.endswith(".autosave.json")
        ]
        return sorted(
            records, key=lambda item: (item.name.casefold(), item.workspace_id)
        )

    def get(self, workspace_id: str) -> FinanceWorkspace:
        path = self._path(workspace_id)
        if not path.exists():
            raise WorkspaceNotFoundError(workspace_id)
        return self._read(path)

    def save(self, workspace: FinanceWorkspace) -> FinanceWorkspace:
        validated = cast(
            FinanceWorkspace, FinanceWorkspace.model_validate(workspace.model_dump())
        )
        self._write_atomic(self._path(validated.workspace_id), validated)
        self.clear_autosave(validated.workspace_id)
        return validated

    def delete(self, workspace_id: str) -> None:
        path = self._path(workspace_id)
        if not path.exists():
            raise WorkspaceNotFoundError(workspace_id)
        path.unlink()
        self.clear_autosave(workspace_id)

    def save_autosave(self, workspace: FinanceWorkspace) -> FinanceWorkspace:
        validated = cast(
            FinanceWorkspace, FinanceWorkspace.model_validate(workspace.model_dump())
        )
        self._write_atomic(self._autosave_path(validated.workspace_id), validated)
        return validated

    def recover_autosave(self, workspace_id: str) -> FinanceWorkspace | None:
        autosave_path = self._autosave_path(workspace_id)
        if not autosave_path.exists():
            return None
        autosave = self._read(autosave_path)
        canonical_path = self._path(workspace_id)
        if not canonical_path.exists():
            return autosave
        canonical = self._read(canonical_path)
        return autosave if autosave.updated_at >= canonical.updated_at else None

    def clear_autosave(self, workspace_id: str) -> None:
        self._autosave_path(workspace_id).unlink(missing_ok=True)


class SQLiteWorkspaceRepository:
    """SQLite adapter implementing the same repository contract."""

    def __init__(self, database: Path) -> None:
        self.database = database
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workspaces (
                    workspace_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workspace_autosaves (
                    workspace_id TEXT PRIMARY KEY,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> FinanceWorkspace:
        value = row["payload_json"]
        if not isinstance(value, str):
            raise ValueError("workspace payload_json must be text")
        payload = json.loads(value)
        if not isinstance(payload, dict):
            raise ValueError("workspace payload_json must contain an object")
        return cast(
            FinanceWorkspace,
            FinanceWorkspace.model_validate(migrate_workspace_payload(payload)),
        )

    def list(self) -> list[FinanceWorkspace]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM workspaces ORDER BY lower(name), workspace_id"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, workspace_id: str) -> FinanceWorkspace:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM workspaces WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
        if row is None:
            raise WorkspaceNotFoundError(workspace_id)
        return self._from_row(row)

    def save(self, workspace: FinanceWorkspace) -> FinanceWorkspace:
        validated = cast(
            FinanceWorkspace, FinanceWorkspace.model_validate(workspace.model_dump())
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workspaces(workspace_id, name, updated_at, payload_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(workspace_id) DO UPDATE SET
                    name = excluded.name,
                    updated_at = excluded.updated_at,
                    payload_json = excluded.payload_json
                """,
                (
                    validated.workspace_id,
                    validated.name,
                    validated.updated_at.isoformat(),
                    _payload(validated),
                ),
            )
            connection.execute(
                "DELETE FROM workspace_autosaves WHERE workspace_id = ?",
                (validated.workspace_id,),
            )
        return validated

    def delete(self, workspace_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM workspaces WHERE workspace_id = ?", (workspace_id,)
            )
            connection.execute(
                "DELETE FROM workspace_autosaves WHERE workspace_id = ?",
                (workspace_id,),
            )
        if cursor.rowcount == 0:
            raise WorkspaceNotFoundError(workspace_id)

    def save_autosave(self, workspace: FinanceWorkspace) -> FinanceWorkspace:
        validated = cast(
            FinanceWorkspace, FinanceWorkspace.model_validate(workspace.model_dump())
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workspace_autosaves(workspace_id, updated_at, payload_json)
                VALUES (?, ?, ?)
                ON CONFLICT(workspace_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    payload_json = excluded.payload_json
                """,
                (
                    validated.workspace_id,
                    validated.updated_at.isoformat(),
                    _payload(validated),
                ),
            )
        return validated

    def recover_autosave(self, workspace_id: str) -> FinanceWorkspace | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM workspace_autosaves WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
        if row is None:
            return None
        autosave = self._from_row(row)
        try:
            canonical = self.get(workspace_id)
        except WorkspaceNotFoundError:
            return autosave
        return autosave if autosave.updated_at >= canonical.updated_at else None

    def clear_autosave(self, workspace_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM workspace_autosaves WHERE workspace_id = ?",
                (workspace_id,),
            )
