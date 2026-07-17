"""Migration helpers for versioned comparison contracts."""

from __future__ import annotations

from typing import Any

from .comparison_models import COMPARISON_CONTRACT_VERSION, ComparisonDefinition


def normalize_comparison(payload: dict[str, Any]) -> ComparisonDefinition:
    migrated = (
        _upgrade_versions(payload)
        if payload.get("contract_version") == "1.4.0"
        else payload
    )
    return ComparisonDefinition.model_validate(migrated)


def _upgrade_versions(value: Any) -> Any:
    if isinstance(value, dict):
        output = {key: _upgrade_versions(item) for key, item in value.items()}
        for key in ("contract_version", "model_version", "methodology_version"):
            if output.get(key) == "1.4.0":
                output[key] = COMPARISON_CONTRACT_VERSION
        return output
    if isinstance(value, list):
        return [_upgrade_versions(item) for item in value]
    return value
