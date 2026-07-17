"""Canonical cost, budget, variance, and operating-economics engine."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from .calculation import round_half_up
from .operating_models import (
    OperatingDefinition,
    OperatingMetadata,
    OperatingMethodology,
    OperatingPeriodInput,
    OperatingPeriodResult,
    OperatingPublication,
    OperatingSummary,
    OperatingUnitInput,
    VarianceResult,
    VarianceStatus,
)

DISCLAIMER = (
    "Decision-support output only. Validate accounting classifications, allocation "
    "bases, taxes, timing, capacity, and source-system controls before operational use."
)


def _status(amount: float) -> VarianceStatus:
    if abs(amount) <= 1e-9:
        return "neutral"
    return "favorable" if amount > 0 else "unfavorable"


def _variance(
    variance_id: str, label: str, amount: float, rationale: str
) -> VarianceResult:
    rounded = round_half_up(amount, 6)
    return VarianceResult(
        variance_id=variance_id,
        label=label,
        amount=rounded,
        status=_status(rounded),
        rationale=rationale,
    )


def _evaluate_period(
    unit: OperatingUnitInput, item: OperatingPeriodInput, target: float
) -> OperatingPeriodResult:
    budget_revenue = item.budget_units * item.budget_unit_price
    flexible_revenue = item.actual_units * item.budget_unit_price
    actual_revenue = item.actual_units * item.actual_unit_price
    budget_variable = item.budget_units * item.budget_variable_cost_per_unit
    flexible_variable = item.actual_units * item.budget_variable_cost_per_unit
    actual_variable = item.actual_units * item.actual_variable_cost_per_unit
    budget_fixed = item.budget_direct_fixed_cost + item.budget_allocated_overhead
    actual_fixed = item.actual_direct_fixed_cost + item.actual_allocated_overhead
    budget_contribution = budget_revenue - budget_variable
    flexible_contribution = flexible_revenue - flexible_variable
    actual_contribution = actual_revenue - actual_variable
    budget_profit = budget_contribution - budget_fixed
    flexible_profit = flexible_contribution - budget_fixed
    actual_profit = actual_contribution - actual_fixed
    budget_cm_unit = item.budget_unit_price - item.budget_variable_cost_per_unit
    actual_cm_unit = item.actual_unit_price - item.actual_variable_cost_per_unit
    cm_percent = (
        None if actual_revenue <= 0 else actual_contribution / actual_revenue * 100
    )
    break_even_units = None if budget_cm_unit <= 0 else budget_fixed / budget_cm_unit
    break_even_revenue = (
        None if break_even_units is None else break_even_units * item.budget_unit_price
    )
    margin_units = (
        None if break_even_units is None else item.actual_units - break_even_units
    )
    margin_percent = (
        None
        if margin_units is None or item.actual_units <= 0
        else margin_units / item.actual_units * 100
    )
    leverage = (
        None if abs(actual_profit) <= 1e-12 else actual_contribution / actual_profit
    )
    target_units = (
        None if budget_cm_unit <= 0 else (budget_fixed + target) / budget_cm_unit
    )

    volume = flexible_contribution - budget_contribution
    price = actual_revenue - flexible_revenue
    variable_spending = flexible_variable - actual_variable
    fixed_spending = budget_fixed - actual_fixed
    profit_variance = actual_profit - budget_profit
    variances = [
        _variance(
            "sales_volume",
            "Sales volume variance",
            volume,
            "Actual versus budget volume valued at the budget contribution margin per unit.",
        ),
        _variance(
            "sales_price",
            "Sales price variance",
            price,
            "Actual volume multiplied by the difference between actual and budget unit price.",
        ),
        _variance(
            "variable_cost_spending",
            "Variable cost spending variance",
            variable_spending,
            "Actual volume multiplied by budget variable cost less actual variable cost.",
        ),
        _variance(
            "fixed_cost_spending",
            "Fixed cost spending variance",
            fixed_spending,
            "Budget direct fixed cost and allocated overhead less the corresponding actual amount.",
        ),
        _variance(
            "operating_profit",
            "Operating profit variance",
            profit_variance,
            "Actual operating profit less static-budget operating profit.",
        ),
    ]
    reconciliation = volume + price + variable_spending + fixed_spending
    return OperatingPeriodResult(
        unit_id=unit.unit_id,
        unit_label=unit.label,
        cost_center=unit.cost_center,
        period=item.period,
        label=item.label,
        budget_units=round_half_up(item.budget_units, 6),
        actual_units=round_half_up(item.actual_units, 6),
        budget_revenue=round_half_up(budget_revenue, 6),
        flexible_revenue=round_half_up(flexible_revenue, 6),
        actual_revenue=round_half_up(actual_revenue, 6),
        budget_variable_cost=round_half_up(budget_variable, 6),
        flexible_variable_cost=round_half_up(flexible_variable, 6),
        actual_variable_cost=round_half_up(actual_variable, 6),
        budget_fixed_cost=round_half_up(budget_fixed, 6),
        actual_fixed_cost=round_half_up(actual_fixed, 6),
        budget_contribution=round_half_up(budget_contribution, 6),
        flexible_contribution=round_half_up(flexible_contribution, 6),
        actual_contribution=round_half_up(actual_contribution, 6),
        budget_operating_profit=round_half_up(budget_profit, 6),
        flexible_operating_profit=round_half_up(flexible_profit, 6),
        actual_operating_profit=round_half_up(actual_profit, 6),
        budget_contribution_per_unit=round_half_up(budget_cm_unit, 6),
        actual_contribution_per_unit=round_half_up(actual_cm_unit, 6),
        contribution_margin_percent=None
        if cm_percent is None
        else round_half_up(cm_percent, 6),
        break_even_units=None
        if break_even_units is None
        else round_half_up(break_even_units, 6),
        break_even_revenue=None
        if break_even_revenue is None
        else round_half_up(break_even_revenue, 6),
        margin_of_safety_units=None
        if margin_units is None
        else round_half_up(margin_units, 6),
        margin_of_safety_percent=None
        if margin_percent is None
        else round_half_up(margin_percent, 6),
        degree_of_operating_leverage=None
        if leverage is None
        else round_half_up(leverage, 6),
        target_profit_units=None
        if target_units is None
        else round_half_up(target_units, 6),
        variances=variances,
        variance_reconciliation=round_half_up(reconciliation, 6),
    )


def _summary(
    summary_id: str, label: str, rows: list[OperatingPeriodResult], target: float
) -> OperatingSummary:
    budget_units = sum(row.budget_units for row in rows)
    actual_units = sum(row.actual_units for row in rows)
    budget_revenue = sum(row.budget_revenue for row in rows)
    actual_revenue = sum(row.actual_revenue for row in rows)
    budget_variable = sum(row.budget_variable_cost for row in rows)
    actual_variable = sum(row.actual_variable_cost for row in rows)
    budget_fixed = sum(row.budget_fixed_cost for row in rows)
    actual_fixed = sum(row.actual_fixed_cost for row in rows)
    budget_contribution = budget_revenue - budget_variable
    actual_contribution = actual_revenue - actual_variable
    budget_profit = budget_contribution - budget_fixed
    actual_profit = actual_contribution - actual_fixed
    budget_cm_unit = None if budget_units <= 0 else budget_contribution / budget_units
    break_even = (
        None
        if budget_cm_unit is None or budget_cm_unit <= 0
        else budget_fixed / budget_cm_unit
    )
    margin = None if break_even is None else actual_units - break_even
    leverage = (
        None if abs(actual_profit) <= 1e-12 else actual_contribution / actual_profit
    )
    target_units = (
        None
        if budget_cm_unit is None or budget_cm_unit <= 0
        else (budget_fixed + target) / budget_cm_unit
    )
    return OperatingSummary(
        summary_id=summary_id,
        label=label,
        budget_units=round_half_up(budget_units, 6),
        actual_units=round_half_up(actual_units, 6),
        budget_revenue=round_half_up(budget_revenue, 6),
        actual_revenue=round_half_up(actual_revenue, 6),
        budget_variable_cost=round_half_up(budget_variable, 6),
        actual_variable_cost=round_half_up(actual_variable, 6),
        budget_fixed_cost=round_half_up(budget_fixed, 6),
        actual_fixed_cost=round_half_up(actual_fixed, 6),
        budget_contribution=round_half_up(budget_contribution, 6),
        actual_contribution=round_half_up(actual_contribution, 6),
        budget_operating_profit=round_half_up(budget_profit, 6),
        actual_operating_profit=round_half_up(actual_profit, 6),
        operating_profit_variance=round_half_up(actual_profit - budget_profit, 6),
        contribution_margin_percent=None
        if actual_revenue <= 0
        else round_half_up(actual_contribution / actual_revenue * 100, 6),
        break_even_units=None if break_even is None else round_half_up(break_even, 6),
        margin_of_safety_units=None if margin is None else round_half_up(margin, 6),
        degree_of_operating_leverage=None
        if leverage is None
        else round_half_up(leverage, 6),
        target_profit_units=None
        if target_units is None
        else round_half_up(target_units, 6),
    )


def evaluate_operating(
    definition: OperatingDefinition, *, generated_at: str | None = None
) -> OperatingPublication:
    rows = [
        _evaluate_period(unit, period, definition.target_operating_profit)
        for unit in definition.units
        for period in unit.periods
    ]
    unit_summaries = [
        _summary(
            unit.unit_id,
            unit.label,
            [row for row in rows if row.unit_id == unit.unit_id],
            definition.target_operating_profit,
        )
        for unit in definition.units
    ]
    centers: dict[str, list[OperatingPeriodResult]] = defaultdict(list)
    for row in rows:
        centers[row.cost_center].append(row)
    cost_center_summaries = [
        _summary(
            f"cost-center-{index + 1}",
            name,
            centers[name],
            definition.target_operating_profit,
        )
        for index, name in enumerate(sorted(centers))
    ]
    total = _summary(
        "total", "All operating units", rows, definition.target_operating_profit
    )
    flags: list[str] = []
    if any(row.actual_operating_profit < 0 for row in rows):
        flags.append("One or more operating periods report an actual operating loss.")
    if any(
        row.margin_of_safety_units is not None and row.margin_of_safety_units < 0
        for row in rows
    ):
        flags.append(
            "One or more periods operate below the budget-basis break-even volume."
        )
    if any(row.variance_reconciliation != row.variances[-1].amount for row in rows):
        flags.append(
            "A rounded variance reconciliation differs from the reported operating-profit variance."
        )
    if any(
        row.degree_of_operating_leverage is not None
        and abs(row.degree_of_operating_leverage) >= 5
        for row in rows
    ):
        flags.append(
            "One or more periods have high operating leverage and elevated profit sensitivity."
        )
    if not flags:
        flags.append(
            "No operating loss, break-even shortfall, or high-leverage flag was detected."
        )
    return OperatingPublication(
        definition=definition,
        rows=rows,
        unit_summaries=unit_summaries,
        cost_center_summaries=cost_center_summaries,
        total_summary=total,
        flags=flags,
        methodology=OperatingMethodology(),
        metadata=OperatingMetadata(
            generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
            row_count=len(rows),
            unit_count=len(unit_summaries),
            cost_center_count=len(cost_center_summaries),
            disclaimer=DISCLAIMER,
        ),
    )
