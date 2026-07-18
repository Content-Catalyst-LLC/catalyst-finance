"""Migration helpers for evidence and governance definitions."""

from __future__ import annotations

from typing import Any

from .governance_models import GOVERNANCE_CONTRACT_VERSION, GovernanceDefinition


def normalize_governance(payload: dict[str, Any]) -> GovernanceDefinition:
    migrated = _upgrade(payload)
    return GovernanceDefinition.model_validate(migrated)


def _upgrade(value: Any) -> Any:
    if isinstance(value, dict):
        output = {key: _upgrade(item) for key, item in value.items()}
        if output.get("contract_version") in {"1.8.0", "1.9.0"}:
            output["contract_version"] = GOVERNANCE_CONTRACT_VERSION
        return output
    if isinstance(value, list):
        return [_upgrade(item) for item in value]
    return value
