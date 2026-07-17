"""Canonical sustainable-finance, carbon, and natural-capital engine."""

from __future__ import annotations

from datetime import datetime, timezone

from .calculation import present_value_annuity, round_half_up
from .sustainable_models import (
    CarbonResult,
    NaturalCapitalAssetResult,
    SustainableDefinition,
    SustainableMetadata,
    SustainableMethodology,
    SustainablePublication,
    SustainableSummary,
    TransitionItemResult,
)

DISCLAIMER = (
    "Decision-support output only. Validate emissions boundaries, additionality, "
    "credit eligibility, natural-capital valuation, discount rates, accounting "
    "treatment, legal rights, and assurance evidence before reporting or investment use."
)


def _pv(value: float, years: float, rate_percent: float) -> float:
    return float(value / ((1 + rate_percent / 100) ** years))


def evaluate_sustainable(
    definition: SustainableDefinition, *, generated_at: str | None = None
) -> SustainablePublication:
    rate = definition.discount_rate_percent
    avoided = max(
        0.0, definition.baseline_emissions_tco2e - definition.project_emissions_tco2e
    )
    reduction_percent = (
        None
        if definition.baseline_emissions_tco2e <= 0
        else avoided / definition.baseline_emissions_tco2e * 100
    )
    shadow_value = avoided * definition.carbon_price_per_tco2e
    eligible_credits = min(definition.carbon_credit_quantity_tco2e, avoided)
    gross_credit = eligible_credits * definition.carbon_credit_price_per_tco2e
    discounted_credit = gross_credit * (
        1 - definition.carbon_credit_discount_percent / 100
    )
    net_credit = discounted_credit - definition.verification_cost
    method = definition.carbon_valuation_method
    if method == "shadow_price":
        selected_carbon = shadow_value
    elif method == "market_credit":
        selected_carbon = net_credit
    elif method == "higher_of":
        selected_carbon = max(shadow_value, net_credit)
    else:
        selected_carbon = min(shadow_value, net_credit)

    asset_results: list[NaturalCapitalAssetResult] = []
    natural_total = 0.0
    for item in definition.natural_capital_assets:
        baseline = item.quantity * item.baseline_unit_value
        projected = item.quantity * item.projected_unit_value
        uplift = projected - baseline
        adjusted_uplift = uplift * item.confidence_percent / 100
        service_pv = present_value_annuity(
            item.annual_service_value,
            definition.horizon_years,
            rate,
        )
        net_value = adjusted_uplift + service_pv - item.restoration_cost
        natural_total += net_value
        asset_results.append(
            NaturalCapitalAssetResult(
                asset_id=item.asset_id,
                label=item.label,
                category=item.category,
                quantity=round_half_up(item.quantity, 6),
                unit=item.unit,
                baseline_stock_value=round_half_up(baseline, 2),
                projected_stock_value=round_half_up(projected, 2),
                gross_stock_uplift=round_half_up(uplift, 2),
                confidence_adjusted_stock_uplift=round_half_up(adjusted_uplift, 2),
                annual_service_value=round_half_up(item.annual_service_value, 2),
                service_value_present_value=round_half_up(service_pv, 2),
                restoration_cost=round_half_up(item.restoration_cost, 2),
                net_natural_capital_value=round_half_up(net_value, 2),
                confidence_percent=round_half_up(item.confidence_percent, 2),
            )
        )

    transition_results: list[TransitionItemResult] = []
    transition_benefits = 0.0
    transition_costs = 0.0
    for item in definition.transition_items:
        adjusted = item.amount * item.probability_percent / 100
        present = _pv(adjusted, item.timing_years, rate)
        signed = present if item.kind == "benefit" else -present
        if item.kind == "benefit":
            transition_benefits += present
        else:
            transition_costs += present
        transition_results.append(
            TransitionItemResult(
                item_id=item.item_id,
                label=item.label,
                kind=item.kind,
                nominal_amount=round_half_up(item.amount, 2),
                probability_percent=round_half_up(item.probability_percent, 2),
                probability_adjusted_amount=round_half_up(adjusted, 2),
                timing_years=round_half_up(item.timing_years, 6),
                present_value=round_half_up(present, 2),
                signed_present_value=round_half_up(signed, 2),
            )
        )

    annual_financing_savings = (
        definition.green_financing_principal
        * (
            definition.conventional_interest_rate_percent
            - definition.green_interest_rate_percent
        )
        / 100
    )
    financing_savings = present_value_annuity(
        annual_financing_savings,
        definition.financing_term_years,
        rate,
    )
    net_transition = transition_benefits - transition_costs
    total = selected_carbon + natural_total + net_transition + financing_savings
    adjusted_npv = definition.base_project_npv + total
    implied_abatement = None if avoided <= 0 else transition_costs / avoided

    flags = [
        "Carbon value uses one selected valuation basis; shadow and market values are not added together.",
        "Natural-capital values require ownership, boundary, condition, and valuation evidence.",
    ]
    if definition.carbon_credit_quantity_tco2e > avoided:
        flags.append(
            "Requested carbon-credit quantity exceeded avoided emissions and was capped."
        )
    if definition.project_emissions_tco2e >= definition.baseline_emissions_tco2e:
        flags.append(
            "The project does not reduce emissions against the stated baseline."
        )
    if any(item.confidence_percent < 50 for item in definition.natural_capital_assets):
        flags.append(
            "At least one natural-capital estimate has confidence below 50 percent."
        )
    if adjusted_npv < 0:
        flags.append(
            "Adjusted project NPV remains negative after sustainable-value adjustments."
        )

    timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    return SustainablePublication(
        definition=definition,
        carbon=CarbonResult(
            baseline_emissions_tco2e=round_half_up(
                definition.baseline_emissions_tco2e, 6
            ),
            project_emissions_tco2e=round_half_up(
                definition.project_emissions_tco2e, 6
            ),
            avoided_emissions_tco2e=round_half_up(avoided, 6),
            emissions_reduction_percent=None
            if reduction_percent is None
            else round_half_up(reduction_percent, 6),
            shadow_carbon_value=round_half_up(shadow_value, 2),
            eligible_credit_quantity_tco2e=round_half_up(eligible_credits, 6),
            gross_market_credit_value=round_half_up(gross_credit, 2),
            discounted_market_credit_value=round_half_up(discounted_credit, 2),
            verification_cost=round_half_up(definition.verification_cost, 2),
            net_market_credit_value=round_half_up(net_credit, 2),
            selected_carbon_value=round_half_up(selected_carbon, 2),
            valuation_method=method,
            implied_abatement_cost_per_tco2e=None
            if implied_abatement is None
            else round_half_up(implied_abatement, 2),
        ),
        natural_capital_assets=asset_results,
        transition_items=transition_results,
        summary=SustainableSummary(
            carbon_value=round_half_up(selected_carbon, 2),
            natural_capital_value=round_half_up(natural_total, 2),
            transition_benefit_present_value=round_half_up(transition_benefits, 2),
            transition_cost_present_value=round_half_up(transition_costs, 2),
            net_transition_value=round_half_up(net_transition, 2),
            green_financing_savings_present_value=round_half_up(financing_savings, 2),
            total_sustainable_value=round_half_up(total, 2),
            base_project_npv=round_half_up(definition.base_project_npv, 2),
            adjusted_project_npv=round_half_up(adjusted_npv, 2),
        ),
        flags=flags,
        methodology=SustainableMethodology(),
        metadata=SustainableMetadata(
            generated_at=timestamp,
            asset_count=len(asset_results),
            transition_item_count=len(transition_results),
            disclaimer=DISCLAIMER,
        ),
    )
