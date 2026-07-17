"""User-facing narrative rules kept separate from calculations and flags."""

from __future__ import annotations

from .models import FinanceNarrative, FinanceResults

REVIEW_BOUNDARY = (
    "Educational scenario output only. Validate assumptions and obtain qualified "
    "human review before financial, investment, tax, accounting, legal, fiduciary, "
    "procurement, funding, or assurance decisions."
)


def narrate(results: FinanceResults) -> FinanceNarrative:
    if results.npv > 0 and results.risk_adjusted_score >= 60:
        note = (
            "Current assumptions support further review; validate inputs and "
            "alternatives before making a decision."
        )
    elif results.npv > 0:
        note = (
            "The financial signal is positive, but disclosed risk or evidence "
            "concerns require deeper review."
        )
    else:
        note = (
            "Current assumptions do not support a strong financial case; revisit "
            "costs, benefits, risks, timing, or alternatives."
        )
    return FinanceNarrative(decision_note=note, review_boundary=REVIEW_BOUNDARY)
