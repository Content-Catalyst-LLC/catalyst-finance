"""Stable model registry for Catalyst Finance."""

from __future__ import annotations

from typing import Any

from .cashflow_models import CASHFLOW_CONTRACT_VERSION, CASHFLOW_MODEL_ID
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
    },
    CASHFLOW_MODEL_ID: {
        "model_id": CASHFLOW_MODEL_ID,
        "name": "Catalyst Finance cash-flow and capital-budgeting model",
        "model_version": CASHFLOW_CONTRACT_VERSION,
        "contract_version": CASHFLOW_CONTRACT_VERSION,
        "status": "stable",
        "period_frequency": ["monthly", "quarterly", "annual"],
        "capabilities": [
            "period cash-flow schedules",
            "nominal and real basis validation",
            "NPV",
            "simple and discounted payback",
            "IRR root detection and ambiguity flags",
            "MIRR",
            "profitability index",
            "benefit-cost ratio",
            "equivalent annual value",
            "working-capital recovery",
            "terminal value",
            "metric-to-cash-flow traceability",
        ],
    },
}


def list_models() -> list[dict[str, Any]]:
    return [dict(model) for model in MODEL_REGISTRY.values()]


def get_model(model_id: str) -> dict[str, Any] | None:
    model = MODEL_REGISTRY.get(model_id)
    return None if model is None else dict(model)
