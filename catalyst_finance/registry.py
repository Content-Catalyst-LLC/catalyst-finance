"""Stable model registry for Catalyst Finance."""

from __future__ import annotations

from typing import Any

from .models import CONTRACT_VERSION, METHODOLOGY_VERSION, MODEL_ID

MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    MODEL_ID: {
        "model_id": MODEL_ID,
        "name": "Catalyst Finance annual screening model",
        "model_version": METHODOLOGY_VERSION,
        "contract_version": CONTRACT_VERSION,
        "status": "stable",
        "period_frequency": "annual",
        "capabilities": [
            "net capital cost",
            "annual benefit",
            "present value",
            "NPV",
            "simple payback",
            "screening ROI",
            "benefit-cost ratio",
            "carbon cost per ton",
            "transparent review score",
        ],
    }
}


def list_models() -> list[dict[str, Any]]:
    return [dict(MODEL_REGISTRY[key]) for key in sorted(MODEL_REGISTRY)]


def get_model(model_id: str) -> dict[str, Any] | None:
    model = MODEL_REGISTRY.get(model_id)
    return None if model is None else dict(model)
