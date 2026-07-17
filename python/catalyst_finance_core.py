#!/usr/bin/env python3
"""Backward-compatible wrapper for the canonical Catalyst Finance CLI."""

from catalyst_finance.cli import main
from catalyst_finance.domain import (
    FinanceInputs,
    FinanceProject,
    FinanceResult,
    FinanceScenarioInput,
    evaluate,
    present_value_annuity,
    round_half_up,
)
from catalyst_finance.engine import evaluate_payload, evaluate_scenario
from catalyst_finance.io import load_scenario, render_markdown

__all__ = [
    "FinanceInputs",
    "FinanceProject",
    "FinanceResult",
    "FinanceScenarioInput",
    "evaluate",
    "evaluate_payload",
    "evaluate_scenario",
    "present_value_annuity",
    "round_half_up",
    "load_scenario",
    "render_markdown",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
