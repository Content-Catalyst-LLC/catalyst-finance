"""Review interpretation rules, separate from financial calculations."""

from __future__ import annotations

from math import floor

from .models import FinanceInputs, FinanceInterpretation, FinanceResults


def interpret(inputs: FinanceInputs, results: FinanceResults) -> FinanceInterpretation:
    flags: list[str] = []
    if results.npv < 0:
        flags.append("Negative NPV under current assumptions")
    if results.net_annual_benefit <= 0:
        flags.append("No payback because net annual benefit is non-positive")
    elif (
        results.payback_years is not None
        and results.payback_years > inputs.time_horizon_years
    ):
        flags.append("Payback exceeds selected time horizon")
    if inputs.confidence_percent < 60:
        flags.append("Evidence confidence is below review threshold")
    if inputs.implementation_risk_percent > 60:
        flags.append("Implementation risk is high")
    if inputs.discount_rate_percent < 0:
        flags.append("Negative discount rate requires explicit review")
    elif inputs.discount_rate_percent > 20:
        flags.append("Discount rate exceeds the screening review range")
    if inputs.external_funding > inputs.capital_cost:
        flags.append(
            "External funding exceeds capital cost; net capital cost is floored at zero"
        )
    if inputs.annual_emissions_reduced_tons is None:
        flags.append("Emissions data not provided; carbon value is excluded")
    if inputs.time_horizon_years != floor(inputs.time_horizon_years):
        flags.append("Fractional horizon uses a prorated final period")
    if not flags:
        flags.append("No major screening flags under current assumptions")

    score = results.risk_adjusted_score
    if score >= 70:
        risk_level = "Lower concern"
    elif score >= 45:
        risk_level = "Moderate concern"
    else:
        risk_level = "High concern"
    return FinanceInterpretation(risk_level=risk_level, flags=flags)
