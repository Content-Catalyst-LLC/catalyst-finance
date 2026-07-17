"""Upgrade v1.4 through v1.7 workspace payloads into the v1.8 contract."""

from __future__ import annotations

from typing import Any

CURRENT_VERSION = "1.8.0"


def migrate_workspace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    migrated = _upgrade(payload)
    workspace = (
        migrated.get("workspace")
        if isinstance(migrated.get("workspace"), dict)
        else migrated
    )
    if isinstance(workspace, dict):
        workspace.setdefault("uncertainty_analyses", [])
        workspace.setdefault("pricing_analyses", [])
        workspace.setdefault("operating_analyses", [])
        workspace.setdefault("sustainable_analyses", [])
    return migrated


def _upgrade(value: Any) -> Any:
    if isinstance(value, dict):
        output = {key: _upgrade(item) for key, item in value.items()}
        for key in (
            "contract_version",
            "workspace_contract_version",
            "export_contract_version",
            "model_version",
            "methodology_version",
            "version",
        ):
            if output.get(key) in {"1.4.0", "1.5.0", "1.6.0", "1.7.0"}:
                output[key] = CURRENT_VERSION
        return output
    if isinstance(value, list):
        return [_upgrade(item) for item in value]
    return value
