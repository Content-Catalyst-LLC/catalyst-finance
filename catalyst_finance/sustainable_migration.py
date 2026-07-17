"""Migration helpers for sustainable-finance definitions."""

from __future__ import annotations

from typing import Any

from .sustainable_models import SUSTAINABLE_CONTRACT_VERSION, SustainableDefinition


def normalize_sustainable(payload: dict[str, Any]) -> SustainableDefinition:
    migrated = (
        _upgrade(payload) if payload.get("contract_version") == "1.7.0" else payload
    )
    return SustainableDefinition.model_validate(migrated)


def _upgrade(value: Any) -> Any:
    if isinstance(value, dict):
        output = {key: _upgrade(item) for key, item in value.items()}
        if output.get("contract_version") == "1.7.0":
            output["contract_version"] = SUSTAINABLE_CONTRACT_VERSION
        return output
    if isinstance(value, list):
        return [_upgrade(item) for item in value]
    return value
