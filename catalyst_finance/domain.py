"""Compatibility surface for the canonical Catalyst Finance model.

Educational decision-support software. It is not financial, investment, tax,
accounting, legal, fiduciary, procurement, funding, lending, or assurance advice.
"""

from __future__ import annotations

from typing import Any, cast

from .calculation import present_value_annuity, round_half_up
from .engine import DISCLAIMER, evaluate_scenario
from .models import (
    FinanceInputs,
    FinanceProject,
    FinancePublication,
    FinanceScenarioInput,
)

FinanceResult = FinancePublication


def evaluate(
    project: FinanceProject,
    inputs: FinanceInputs,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Backward-compatible evaluator using canonical v1.4.0 defaults."""
    scenario = FinanceScenarioInput(project=project, assumptions=inputs)
    return cast(
        dict[str, Any],
        evaluate_scenario(scenario, generated_at=generated_at).model_dump(mode="json"),
    )


__all__ = [
    "DISCLAIMER",
    "FinanceInputs",
    "FinanceProject",
    "FinanceResult",
    "FinanceScenarioInput",
    "evaluate",
    "present_value_annuity",
    "round_half_up",
]
