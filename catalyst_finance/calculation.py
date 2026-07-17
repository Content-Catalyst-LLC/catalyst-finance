"""Pure calculations for the canonical Catalyst Finance screening model."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from math import floor

from .models import FinanceContext, FinanceInputs, FinanceResults, ScoreComponent


def round_half_up(value: float, decimals: int) -> float:
    quantum = Decimal("1").scaleb(-decimals)
    return float(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP))


def present_value_annuity(
    annual_value: float,
    years: float,
    discount_rate_percent: float,
) -> float:
    """Present value with a prorated final period for fractional horizons."""
    if years <= 0:
        return 0.0
    rate = discount_rate_percent / 100.0
    full_periods = floor(years)
    fraction = years - full_periods
    total = 0.0
    for period in range(1, full_periods + 1):
        total += annual_value / ((1.0 + rate) ** period)
    if fraction > 1e-12:
        total += (annual_value * fraction) / ((1.0 + rate) ** years)
    return total


def _score_components(
    *,
    npv: float,
    payback_years: float | None,
    net_capital_cost: float,
    net_annual_benefit: float,
    horizon: float,
    confidence: float,
    implementation_risk: float,
    decimals: int,
) -> list[ScoreComponent]:
    if npv > 0:
        financial_score = 80.0
        financial_reason = "NPV is positive under the current assumptions."
    elif abs(npv) < 1e-12:
        financial_score = 50.0
        financial_reason = "NPV is approximately zero under the current assumptions."
    else:
        financial_score = 20.0
        financial_reason = "NPV is negative under the current assumptions."

    if net_capital_cost == 0 and net_annual_benefit > 0:
        payback_score = 100.0
        payback_reason = (
            "No net upfront capital remains and annual benefit is positive."
        )
    elif payback_years is None:
        payback_score = 10.0
        payback_reason = (
            "No simple payback exists because annual benefit is non-positive."
        )
    elif payback_years <= 3:
        payback_score = 90.0
        payback_reason = "Simple payback is three years or less."
    elif payback_years <= horizon:
        payback_score = 70.0
        payback_reason = "Simple payback occurs within the selected horizon."
    else:
        payback_score = 30.0
        payback_reason = "Simple payback exceeds the selected horizon."

    raw = [
        (
            "financial_signal",
            "Financial signal",
            financial_score,
            0.35,
            financial_reason,
        ),
        (
            "payback_signal",
            "Payback signal",
            payback_score,
            0.25,
            payback_reason,
        ),
        (
            "evidence_confidence",
            "Evidence confidence",
            confidence,
            0.20,
            "Uses the disclosed evidence-confidence assumption directly.",
        ),
        (
            "implementation_resilience",
            "Implementation resilience",
            100.0 - implementation_risk,
            0.20,
            "Equals 100 minus the disclosed implementation-risk assumption.",
        ),
    ]
    return [
        ScoreComponent(
            component_id=component_id,
            label=label,
            raw_score=round_half_up(score, decimals),
            weight=weight,
            weighted_contribution=round_half_up(score * weight, decimals),
            rationale=rationale,
        )
        for component_id, label, score, weight, rationale in raw
    ]


def calculate(inputs: FinanceInputs, context: FinanceContext) -> FinanceResults:
    money_decimals = context.monetary_decimals
    ratio_decimals = context.ratio_decimals
    score_decimals = context.score_decimals

    net_capital_cost = max(0.0, inputs.capital_cost - inputs.external_funding)
    emissions = inputs.annual_emissions_reduced_tons
    carbon_value = 0.0 if emissions is None else emissions * inputs.carbon_price_per_ton
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
    undiscounted_benefit = net_annual_benefit * inputs.time_horizon_years
    roi = (
        None
        if net_capital_cost == 0
        else ((undiscounted_benefit - net_capital_cost) / net_capital_cost) * 100.0
    )
    bcr = None if net_capital_cost == 0 else pv_benefits / net_capital_cost
    lifetime_tons = None if emissions is None else emissions * inputs.time_horizon_years
    carbon_cost = (
        None
        if lifetime_tons is None or lifetime_tons <= 0
        else net_capital_cost / lifetime_tons
    )

    components = _score_components(
        npv=npv,
        payback_years=payback,
        net_capital_cost=net_capital_cost,
        net_annual_benefit=net_annual_benefit,
        horizon=inputs.time_horizon_years,
        confidence=inputs.confidence_percent,
        implementation_risk=inputs.implementation_risk_percent,
        decimals=score_decimals,
    )
    total_score = sum(
        component.raw_score * component.weight for component in components
    )

    return FinanceResults(
        net_capital_cost=round_half_up(net_capital_cost, money_decimals),
        carbon_value_per_year=round_half_up(carbon_value, money_decimals),
        net_annual_benefit=round_half_up(net_annual_benefit, money_decimals),
        present_value_benefits=round_half_up(pv_benefits, money_decimals),
        npv=round_half_up(npv, money_decimals),
        payback_years=(
            None if payback is None else round_half_up(payback, ratio_decimals)
        ),
        roi_percent=None if roi is None else round_half_up(roi, ratio_decimals),
        benefit_cost_ratio=(
            None if bcr is None else round_half_up(bcr, ratio_decimals)
        ),
        carbon_cost_per_ton=(
            None if carbon_cost is None else round_half_up(carbon_cost, money_decimals)
        ),
        risk_adjusted_score=round_half_up(total_score, score_decimals),
        score_components=components,
    )
