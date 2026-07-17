"""Migration helpers for operating-economics definitions."""

from __future__ import annotations

from typing import Any

from .operating_models import OPERATING_CONTRACT_VERSION, OperatingDefinition


def normalize_operating(payload: dict[str, Any]) -> OperatingDefinition:
    migrated = (
        _upgrade(payload)
        if payload.get("contract_version") in {"1.6.0", "1.7.0", "1.8.0"}
        else payload
    )
    return OperatingDefinition.model_validate(migrated)


def _upgrade(value: Any) -> Any:
    if isinstance(value, dict):
        output = {key: _upgrade(item) for key, item in value.items()}
        if output.get("contract_version") in {"1.6.0", "1.7.0", "1.8.0"}:
            output["contract_version"] = OPERATING_CONTRACT_VERSION
        return output
    if isinstance(value, list):
        return [_upgrade(item) for item in value]
    return value
