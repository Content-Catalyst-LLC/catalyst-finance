"""Core Catalyst Finance scenario model.

Educational decision-support software. It is not financial, investment, tax,
accounting, legal, fiduciary, or assurance advice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .version import __version__

DISCLAIMER = (
    "Educational software only; not financial, investment, legal, accounting, "
    "tax, fiduciary, or assurance advice."
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True, slots=True)
class FinanceInputs:
    capital_cost: float
    external_funding: float
    annual_savings: float
    annual_operating_cost: float
    time_horizon_years: float
    discount_rate_percent: float
    annual_emissions_reduced_tons: float
    carbon_price_per_ton: float
    confidence_percent: float
    implementation_risk_percent: float


@dataclass(frozen=True, slots=True)
class FinanceProject:
    name: str
    category: str = "Sustainability finance"


@dataclass(frozen=True, slots=True)
class FinanceResult:
    net_capital_cost: float
    net_annual_benefit: float
    present_value_benefits: float
    npv: float
    payback_years: float | None
    roi_percent: float
    benefit_cost_ratio: float | None
    carbon_cost_per_ton: float | None
    risk_adjusted_score: float
    risk_level: str
    flags: list[str]
    decision_note: str


def present_value_annuity(
    annual_value: float,
    years: float,
    discount_rate_percent: float,
) -> float:
    """Return the present value of an end-of-period annual amount."""
    years_i = max(0, int(round(years)))
    rate = discount_rate_percent / 100.0
    if years_i == 0:
        return 0.0
    if abs(rate) < 1e-12:
        return annual_value * years_i
    return sum(annual_value / ((1.0 + rate) ** year) for year in range(1, years_i + 1))


def evaluate(
    project: FinanceProject,
    inputs: FinanceInputs,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Evaluate one transparent screening scenario."""
    net_capital_cost = max(0.0, inputs.capital_cost - inputs.external_funding)
    carbon_value = inputs.annual_emissions_reduced_tons * inputs.carbon_price_per_ton
    net_annual_benefit = (
        inputs.annual_savings + carbon_value - inputs.annual_operating_cost
    )
    pv_benefits = present_value_annuity(
        net_annual_benefit,
        inputs.time_horizon_years,
        inputs.discount_rate_percent,
    )
    npv = pv_benefits - net_capital_cost
    payback = None if net_annual_benefit <= 0 else net_capital_cost / net_annual_benefit
    total_undiscounted_benefit = net_annual_benefit * max(
        0.0, inputs.time_horizon_years
    )
    roi = (
        0.0
        if net_capital_cost == 0
        else ((total_undiscounted_benefit - net_capital_cost) / net_capital_cost)
        * 100.0
    )
    bcr = None if net_capital_cost == 0 else pv_benefits / net_capital_cost
    lifetime_tons = inputs.annual_emissions_reduced_tons * max(
        0.0, inputs.time_horizon_years
    )
    carbon_cost = None if lifetime_tons <= 0 else net_capital_cost / lifetime_tons

    confidence = _clamp(inputs.confidence_percent, 0.0, 100.0)
    risk = _clamp(inputs.implementation_risk_percent, 0.0, 100.0)
    npv_signal = 60.0 if npv > 0 else 30.0
    payback_signal = 50.0
    if payback is not None:
        if payback <= 3:
            payback_signal = 75.0
        elif payback <= inputs.time_horizon_years:
            payback_signal = 60.0
        else:
            payback_signal = 35.0
    risk_adjusted_score = _clamp(
        (npv_signal * 0.35)
        + (payback_signal * 0.25)
        + (confidence * 0.25)
        - (risk * 0.25)
        + 20.0,
        0.0,
        100.0,
    )

    flags: list[str] = []
    if npv < 0:
        flags.append("Negative NPV under current assumptions")
    if payback is None:
        flags.append("No payback because net annual benefit is non-positive")
    elif payback > inputs.time_horizon_years:
        flags.append("Payback exceeds selected time horizon")
    if confidence < 60:
        flags.append("Evidence confidence is below review threshold")
    if risk > 60:
        flags.append("Implementation risk is high")
    if inputs.discount_rate_percent < 0 or inputs.discount_rate_percent > 20:
        flags.append("Discount rate needs review")
    if not flags:
        flags.append("No major screening flags under current assumptions")

    if risk_adjusted_score >= 70:
        risk_level = "Lower concern"
    elif risk_adjusted_score >= 45:
        risk_level = "Moderate concern"
    else:
        risk_level = "High concern"

    if npv > 0 and risk_adjusted_score >= 60:
        decision_note = (
            "Current assumptions support further review; validate inputs "
            "before making a decision."
        )
    elif npv > 0:
        decision_note = (
            "Financial signal is positive, but risk or confidence concerns "
            "require deeper review."
        )
    else:
        decision_note = (
            "Current assumptions do not support a strong financial case; "
            "revisit costs, benefits, risks, or alternatives."
        )

    result = FinanceResult(
        net_capital_cost=round(net_capital_cost, 2),
        net_annual_benefit=round(net_annual_benefit, 2),
        present_value_benefits=round(pv_benefits, 2),
        npv=round(npv, 2),
        payback_years=None if payback is None else round(payback, 2),
        roi_percent=round(roi, 2),
        benefit_cost_ratio=None if bcr is None else round(bcr, 2),
        carbon_cost_per_ton=(None if carbon_cost is None else round(carbon_cost, 2)),
        risk_adjusted_score=round(risk_adjusted_score, 1),
        risk_level=risk_level,
        flags=flags,
        decision_note=decision_note,
    )

    timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    return {
        "project": asdict(project),
        "inputs": asdict(inputs),
        "results": {
            key: value
            for key, value in asdict(result).items()
            if key not in {"risk_level", "flags", "decision_note"}
        },
        "interpretation": {
            "risk_level": result.risk_level,
            "flags": result.flags,
            "decision_note": result.decision_note,
        },
        "metadata": {
            "generated_at": timestamp,
            "tool": "Catalyst Finance scenario engine",
            "version": __version__,
            "disclaimer": DISCLAIMER,
        },
    }
