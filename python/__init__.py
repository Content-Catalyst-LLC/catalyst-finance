"""Backward-compatible imports for pre-v1.0.1 callers."""

from catalyst_finance.domain import (
    FinanceInputs,
    FinanceProject,
    FinanceResult,
    evaluate,
    present_value_annuity,
)

__all__ = [
    "FinanceInputs",
    "FinanceProject",
    "FinanceResult",
    "evaluate",
    "present_value_annuity",
]
