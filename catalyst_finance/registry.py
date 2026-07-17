"""Stable model registry for Catalyst Finance."""

from __future__ import annotations

from typing import Any

from .cashflow_models import CASHFLOW_CONTRACT_VERSION, CASHFLOW_MODEL_ID
from .comparison_models import COMPARISON_CONTRACT_VERSION, COMPARISON_MODEL_ID
from .models import CONTRACT_VERSION, METHODOLOGY_VERSION, MODEL_ID
from .operating_models import OPERATING_CONTRACT_VERSION, OPERATING_MODEL_ID
from .pricing_models import PRICING_CONTRACT_VERSION, PRICING_MODEL_ID
from .sustainable_models import SUSTAINABLE_CONTRACT_VERSION, SUSTAINABLE_MODEL_ID
from .uncertainty_models import UNCERTAINTY_CONTRACT_VERSION, UNCERTAINTY_MODEL_ID

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
    COMPARISON_MODEL_ID: {
        "model_id": COMPARISON_MODEL_ID,
        "name": "Catalyst Finance scenario comparison and sensitivity model",
        "model_version": COMPARISON_CONTRACT_VERSION,
        "contract_version": COMPARISON_CONTRACT_VERSION,
        "status": "stable",
        "period_frequency": ["monthly", "quarterly", "annual"],
        "capabilities": [
            "three-or-more alternative comparison",
            "aligned metrics, deltas, and rankings",
            "Pareto dominance checks",
            "one-way and two-way sensitivity",
            "break-even and threshold search",
            "tornado and crossover data",
            "assumption-driver explanations",
            "revision traceability",
        ],
    },
    UNCERTAINTY_MODEL_ID: {
        "model_id": UNCERTAINTY_MODEL_ID,
        "name": "Catalyst Finance uncertainty, Monte Carlo, and stress model",
        "model_version": UNCERTAINTY_CONTRACT_VERSION,
        "contract_version": UNCERTAINTY_CONTRACT_VERSION,
        "status": "stable",
        "period_frequency": ["monthly", "quarterly", "annual"],
        "capabilities": [
            "seeded Monte Carlo simulation",
            "uniform, triangular, normal, lognormal, and discrete distributions",
            "Gaussian-copula correlation",
            "percentiles, downside probabilities, VaR, and expected shortfall",
            "histograms and variable influence",
            "deterministic multi-factor stress testing",
            "reproducibility keys and retained samples",
        ],
    },
    PRICING_MODEL_ID: {
        "model_id": PRICING_MODEL_ID,
        "name": "Catalyst Finance demand, elasticity, pricing, and revenue model",
        "model_version": PRICING_CONTRACT_VERSION,
        "contract_version": PRICING_CONTRACT_VERSION,
        "status": "stable",
        "period_frequency": "price grid",
        "capabilities": [
            "linear, constant-elasticity, and observed demand",
            "multi-segment demand aggregation",
            "capacity and minimum-volume constraints",
            "revenue, contribution, and profit optimization",
            "point and local elasticity classification",
            "break-even quantity and margin analysis",
            "current-price recommendation deltas",
        ],
    },
    OPERATING_MODEL_ID: {
        "model_id": OPERATING_MODEL_ID,
        "name": "Catalyst Finance cost, budget, and operating-economics model",
        "model_version": OPERATING_CONTRACT_VERSION,
        "contract_version": OPERATING_CONTRACT_VERSION,
        "status": "stable",
        "period_frequency": ["monthly", "quarterly", "annual"],
        "capabilities": [
            "static, flexible, and actual operating statements",
            "sales volume and sales price variances",
            "variable and fixed cost spending variances",
            "unit economics and contribution margins",
            "break-even and margin-of-safety analysis",
            "degree of operating leverage",
            "target-profit volume",
            "cost-center and unit rollups",
            "variance reconciliation",
        ],
    },
    SUSTAINABLE_MODEL_ID: {
        "model_id": SUSTAINABLE_MODEL_ID,
        "name": "Catalyst Finance sustainable finance, carbon, and natural-capital model",
        "model_version": SUSTAINABLE_CONTRACT_VERSION,
        "contract_version": SUSTAINABLE_CONTRACT_VERSION,
        "status": "stable",
        "period_frequency": "reporting horizon",
        "capabilities": [
            "non-double-counted carbon valuation",
            "avoided emissions and carbon-credit accounting",
            "natural-capital stock and ecosystem-service valuation",
            "probability-adjusted transition benefits and costs",
            "green-financing interest savings",
            "adjusted project value and review flags",
            "revision traceability",
        ],
    },
}


def list_models() -> list[dict[str, Any]]:
    return [dict(model) for model in MODEL_REGISTRY.values()]


def get_model(model_id: str) -> dict[str, Any] | None:
    model = MODEL_REGISTRY.get(model_id)
    return None if model is None else dict(model)
