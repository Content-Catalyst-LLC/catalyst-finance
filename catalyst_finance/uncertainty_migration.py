"""Migration helpers for versioned uncertainty contracts."""

from __future__ import annotations

from typing import Any

from .uncertainty_models import UNCERTAINTY_CONTRACT_VERSION, UncertaintyDefinition


def normalize_uncertainty(payload: dict[str, Any]) -> UncertaintyDefinition:
    migrated = (
        _upgrade(payload) if payload.get("contract_version") == "1.5.0" else payload
    )
    return UncertaintyDefinition.model_validate(migrated)


def _upgrade(value: Any) -> Any:
    if isinstance(value, dict):
        output = {key: _upgrade(item) for key, item in value.items()}
        for key in ("contract_version", "model_version", "methodology_version"):
            if output.get(key) == "1.5.0":
                output[key] = UNCERTAINTY_CONTRACT_VERSION
        return output
    if isinstance(value, list):
        return [_upgrade(item) for item in value]
    return value
