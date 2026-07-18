"""Migration helpers for connected platform definitions."""

from __future__ import annotations

from typing import Any, cast

from .platform_models import PLATFORM_CONTRACT_VERSION, PlatformDefinition


def normalize_platform(payload: dict[str, Any]) -> PlatformDefinition:
    migrated = cast(dict[str, Any], _upgrade(payload))
    return cast(PlatformDefinition, PlatformDefinition.model_validate(migrated))


def _upgrade(value: Any) -> Any:
    if isinstance(value, dict):
        output = {key: _upgrade(item) for key, item in value.items()}
        if output.get("contract_version") == "1.9.0":
            output["contract_version"] = PLATFORM_CONTRACT_VERSION
        if output.get("model_version") == "1.9.0":
            output["model_version"] = PLATFORM_CONTRACT_VERSION
        return output
    if isinstance(value, list):
        return [_upgrade(item) for item in value]
    return value
