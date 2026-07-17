"""Migration helpers for pricing definitions."""

from __future__ import annotations

from typing import Any

from .pricing_models import PRICING_CONTRACT_VERSION, PricingDefinition


def normalize_pricing(payload: dict[str, Any]) -> PricingDefinition:
    migrated = (
        _upgrade(payload)
        if payload.get("contract_version") in {"1.5.0", "1.6.0", "1.7.0"}
        else payload
    )
    return PricingDefinition.model_validate(migrated)


def _upgrade(value: Any) -> Any:
    if isinstance(value, dict):
        output = {key: _upgrade(item) for key, item in value.items()}
        if output.get("contract_version") in {"1.5.0", "1.6.0", "1.7.0"}:
            output["contract_version"] = PRICING_CONTRACT_VERSION
        return output
    if isinstance(value, list):
        return [_upgrade(item) for item in value]
    return value
