"""Canonical demand, elasticity, pricing, and revenue engine."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from .calculation import round_half_up
from .pricing_models import (
    DemandCurve,
    DemandSegment,
    PriceResult,
    PricingDefinition,
    PricingMetadata,
    PricingMethodology,
    PricingObjective,
    PricingOptimum,
    PricingPublication,
    PricingRecommendation,
    SegmentPriceResult,
)

DISCLAIMER = (
    "Decision-support output only. Validate demand assumptions, cost-to-serve, "
    "market response, legal constraints, taxes, and implementation effects before use."
)


def _classify(elasticity: float | None) -> str:
    if elasticity is None:
        return "undefined"
    magnitude = abs(elasticity)
    if abs(magnitude - 1.0) <= 1e-9:
        return "unit_elastic"
    return "elastic" if magnitude > 1 else "inelastic"


def _observed_quantity(
    curve: DemandCurve, price: float
) -> tuple[float, float | None, str]:
    points = curve.observed_points
    if price <= points[0].price:
        left, right = points[0], points[1]
        quantity = points[0].quantity
        policy = "clamped_below_range"
    elif price >= points[-1].price:
        left, right = points[-2], points[-1]
        quantity = points[-1].quantity
        policy = "clamped_above_range"
    else:
        left, right = points[0], points[1]
        for index in range(1, len(points)):
            if price <= points[index].price:
                left, right = points[index - 1], points[index]
                break
        fraction = (price - left.price) / (right.price - left.price)
        quantity = left.quantity + fraction * (right.quantity - left.quantity)
        policy = "interpolated"
    slope = (right.quantity - left.quantity) / (right.price - left.price)
    elasticity = None if quantity <= 0 else slope * price / quantity
    return max(0.0, quantity), elasticity, policy


def _segment_demand(
    segment: DemandSegment, price: float
) -> tuple[float, float | None, str]:
    curve = segment.curve
    if curve.kind == "linear":
        assert curve.intercept is not None and curve.slope is not None
        quantity = max(0.0, curve.intercept - curve.slope * price)
        elasticity = None if quantity <= 0 else -curve.slope * price / quantity
        policy = "analytical_linear"
    elif curve.kind == "constant_elasticity":
        assert (
            curve.reference_price is not None
            and curve.reference_quantity is not None
            and curve.elasticity is not None
        )
        quantity = (
            curve.reference_quantity
            * (price / curve.reference_price) ** curve.elasticity
        )
        elasticity = curve.elasticity
        policy = "analytical_constant_elasticity"
    else:
        quantity, elasticity, policy = _observed_quantity(curve, price)
    return quantity * segment.quantity_multiplier, elasticity, policy


def _evaluate_price(definition: PricingDefinition, price: float) -> PriceResult:
    raw: list[tuple[DemandSegment, float, float | None, str]] = [
        (segment, *_segment_demand(segment, price)) for segment in definition.segments
    ]
    unconstrained = sum(item[1] for item in raw)
    capacity = definition.constraints.capacity_units
    scale = 1.0
    capacity_constrained = capacity is not None and unconstrained > capacity
    if capacity_constrained and unconstrained > 0 and capacity is not None:
        scale = capacity / unconstrained
    segment_results = [
        SegmentPriceResult(
            segment_id=segment.segment_id,
            label=segment.label,
            unconstrained_quantity=round_half_up(quantity, 6),
            quantity=round_half_up(quantity * scale, 6),
            elasticity=None if elasticity is None else round_half_up(elasticity, 6),
            demand_classification=_classify(elasticity),
            interpolation_policy=policy,
        )
        for segment, quantity, elasticity, policy in raw
    ]
    quantity = sum(item.quantity for item in segment_results)
    revenue = price * quantity
    costs = definition.costs
    unit_cost = costs.unit_variable_cost + costs.unit_fulfillment_cost
    variable_cost = quantity * unit_cost + revenue * costs.channel_fee_percent / 100.0
    contribution = revenue - variable_cost
    profit = contribution - costs.fixed_cost
    weighted_elasticity = sum(
        item.quantity * item.elasticity
        for item in segment_results
        if item.elasticity is not None
    )
    weighted_quantity = sum(
        item.quantity for item in segment_results if item.elasticity is not None
    )
    average_elasticity = (
        None if weighted_quantity <= 0 else weighted_elasticity / weighted_quantity
    )
    contribution_per_unit = 0.0 if quantity <= 0 else contribution / quantity
    break_even_quantity = (
        None if contribution_per_unit <= 0 else costs.fixed_cost / contribution_per_unit
    )
    minimum = definition.constraints.minimum_volume_units
    return PriceResult(
        price=round_half_up(price, 6),
        segments=segment_results,
        unconstrained_quantity=round_half_up(unconstrained, 6),
        quantity=round_half_up(quantity, 6),
        gross_revenue=round_half_up(revenue, 6),
        variable_cost=round_half_up(variable_cost, 6),
        contribution=round_half_up(contribution, 6),
        operating_profit=round_half_up(profit, 6),
        contribution_margin_percent=(
            None if revenue <= 0 else round_half_up(contribution / revenue * 100.0, 6)
        ),
        average_elasticity=(
            None if average_elasticity is None else round_half_up(average_elasticity, 6)
        ),
        capacity_constrained=capacity_constrained,
        minimum_volume_met=None if minimum is None else quantity >= minimum,
        break_even_quantity=(
            None
            if break_even_quantity is None
            else round_half_up(break_even_quantity, 6)
        ),
        break_even_met=None
        if break_even_quantity is None
        else quantity >= break_even_quantity,
    )


def _objective_value(row: PriceResult, objective: PricingObjective) -> float:
    if objective == "revenue":
        return row.gross_revenue
    if objective == "contribution":
        return row.contribution
    return row.operating_profit


def _optimum(rows: list[PriceResult], objective: PricingObjective) -> PricingOptimum:
    index, row = max(
        enumerate(rows),
        key=lambda item: (_objective_value(item[1], objective), -item[1].price),
    )
    return PricingOptimum(
        objective=objective,
        price=row.price,
        quantity=row.quantity,
        value=_objective_value(row, objective),
        row_index=index,
    )


def _price_allowed(definition: PricingDefinition, candidate: float) -> bool:
    current = definition.current_price
    limit = definition.constraints.maximum_price_change_percent
    if current is None or limit is None:
        return True
    return abs(candidate - current) / current * 100.0 <= limit + 1e-9


def evaluate_pricing(
    definition: PricingDefinition,
    *,
    generated_at: str | None = None,
) -> PricingPublication:
    grid = definition.grid
    increment = (grid.maximum_price - grid.minimum_price) / (grid.steps - 1)
    rows = [
        _evaluate_price(definition, grid.minimum_price + increment * index)
        for index in range(grid.steps)
    ]
    optima = [
        _optimum(rows, "revenue"),
        _optimum(rows, "contribution"),
        _optimum(rows, "profit"),
    ]
    selected = next(item for item in optima if item.objective == definition.objective)
    allowed_rows = [row for row in rows if _price_allowed(definition, row.price)]
    constrained = False
    if allowed_rows:
        constrained_row = max(
            allowed_rows,
            key=lambda row: (_objective_value(row, definition.objective), -row.price),
        )
        if constrained_row.price != selected.price:
            constrained = True
            selected = PricingOptimum(
                objective=definition.objective,
                price=constrained_row.price,
                quantity=constrained_row.quantity,
                value=_objective_value(constrained_row, definition.objective),
                row_index=rows.index(constrained_row),
            )
    current = (
        None
        if definition.current_price is None
        else _evaluate_price(definition, definition.current_price)
    )
    current_value = (
        None if current is None else _objective_value(current, definition.objective)
    )
    absolute_change = (
        None if current is None else round_half_up(selected.price - current.price, 6)
    )
    percent_change = (
        None
        if current is None
        else round_half_up((selected.price - current.price) / current.price * 100.0, 6)
    )
    gain = (
        None
        if current_value is None
        else round_half_up(selected.value - current_value, 6)
    )
    direction = "maintain"
    if absolute_change is not None and absolute_change > 1e-9:
        direction = "increase"
    elif absolute_change is not None and absolute_change < -1e-9:
        direction = "decrease"
    flags: list[str] = []
    if any(row.capacity_constrained for row in rows):
        flags.append("Capacity constrains demand at one or more evaluated prices.")
    if any(
        segment.interpolation_policy.startswith("clamped")
        for row in rows
        for segment in row.segments
    ):
        flags.append(
            "Observed demand is endpoint-clamped outside its measured price range."
        )
    if any(row.minimum_volume_met is False for row in rows):
        flags.append(
            "One or more evaluated prices fall below the configured minimum volume."
        )
    if constrained:
        flags.append(
            "The recommended price is limited by the maximum price-change constraint."
        )
    if not flags:
        flags.append(
            "No configured capacity, volume, or price-change constraint is binding."
        )
    return PricingPublication(
        definition=definition,
        rows=rows,
        current_position=current,
        optima=optima,
        recommendation=PricingRecommendation(
            objective=definition.objective,
            current_price=None if current is None else current.price,
            recommended_price=selected.price,
            absolute_price_change=absolute_change,
            percent_price_change=percent_change,
            current_objective_value=current_value,
            recommended_objective_value=selected.value,
            expected_objective_gain=gain,
            constraint_limited=constrained,
            narrative=(
                f"{direction.capitalize()} price to {definition.currency} {selected.price:,.2f} "
                f"to maximize {definition.objective} within the declared grid and constraints."
            ),
        ),
        flags=flags,
        methodology=PricingMethodology(),
        metadata=PricingMetadata(
            generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
            grid_rows=len(rows),
            constrained_rows=sum(row.capacity_constrained for row in rows),
            disclaimer=DISCLAIMER,
        ),
    )


def objective_accessor(objective: PricingObjective) -> Callable[[PriceResult], float]:
    """Expose the canonical objective accessor for integrations and tests."""
    return lambda row: _objective_value(row, objective)
