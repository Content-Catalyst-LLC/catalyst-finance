#!/usr/bin/env python3
"""Backward-compatible wrapper for the canonical Catalyst Finance CLI."""

from catalyst_finance.cli import main
from catalyst_finance.domain import (
    FinanceInputs,
    FinanceProject,
    FinanceResult,
    evaluate,
    present_value_annuity,
)
from catalyst_finance.io import load_scenario, render_markdown

__all__ = [
    "FinanceInputs",
    "FinanceProject",
    "FinanceResult",
    "evaluate",
    "present_value_annuity",
    "load_scenario",
    "render_markdown",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
