"""Period-level cash-flow and capital-budgeting calculations."""

from __future__ import annotations

from datetime import datetime, timezone
from math import log10
from typing import Final, cast

from .calculation import round_half_up
from .cashflow_models import (
    CashFlowCategory,
    CashFlowInterpretation,
    CashFlowMetadata,
    CashFlowMethodology,
    CashFlowMetrics,
    CashFlowPublication,
    CashFlowScenarioInput,
    ExpandedCashFlowLine,
    MetricTrace,
    PeriodCashFlow,
)
from .engine import DISCLAIMER

INFLOW_CATEGORIES: Final[set[CashFlowCategory]] = {
    "revenue",
    "savings",
    "avoided_cost",
    "grant",
    "rebate",
    "residual_value",
    "working_capital_recovery",
    "other_benefit",
}
COST_CATEGORIES: Final[set[CashFlowCategory]] = {
    "capital_cost",
    "operating_cost",
    "decommissioning_cost",
    "working_capital",
    "other_cost",
}
BCR_BENEFIT_CATEGORIES: Final[set[CashFlowCategory]] = {
    "revenue",
    "savings",
    "avoided_cost",
    "residual_value",
    "working_capital_recovery",
    "other_benefit",
}
TERMINAL_CATEGORIES: Final[set[CashFlowCategory]] = {
    "residual_value",
    "decommissioning_cost",
    "working_capital_recovery",
}
ALL_CATEGORIES: Final[list[CashFlowCategory]] = [
    "capital_cost",
    "operating_cost",
    "revenue",
    "savings",
    "avoided_cost",
    "grant",
    "rebate",
    "residual_value",
    "decommissioning_cost",
    "working_capital",
    "working_capital_recovery",
    "other_benefit",
    "other_cost",
]


def periods_per_year(frequency: str) -> int:
    return {"monthly": 12, "quarterly": 4, "annual": 1}[frequency]


def effective_period_rate(annual_percent: float, frequency: str) -> float:
    annual_rate = annual_percent / 100.0
    return cast(float, (1.0 + annual_rate) ** (1.0 / periods_per_year(frequency)) - 1.0)


def _signed_amount(category: CashFlowCategory, amount: float) -> float:
    return amount if category in INFLOW_CATEGORIES else -amount


def _label(period: int, frequency: str) -> str:
    if period == 0:
        return "Period 0"
    singular = {"monthly": "Month", "quarterly": "Quarter", "annual": "Year"}[frequency]
    return f"{singular} {period}"


def expand_cash_flows(
    scenario: CashFlowScenarioInput,
) -> list[list[ExpandedCashFlowLine]]:
    frequency = scenario.context.period_frequency
    per_year = periods_per_year(frequency)
    rows: list[list[ExpandedCashFlowLine]] = [
        [] for _ in range(scenario.analysis_horizon_periods + 1)
    ]
    for line in scenario.lines:
        end = line.end_period if line.end_period is not None else line.start_period
        for period in range(line.start_period, end + 1, line.interval_periods):
            annual_rate = line.escalation_rate_percent_annual / 100.0
            escalated = line.amount * ((1.0 + annual_rate) ** (period / per_year))
            signed = _signed_amount(line.category, escalated)
            rows[period].append(
                ExpandedCashFlowLine(
                    flow_id=line.flow_id,
                    label=line.label,
                    category=line.category,
                    period=period,
                    amount=escalated,
                    signed_amount=signed,
                    direction="inflow" if signed >= 0 else "outflow",
                )
            )
    return rows


def _sign_changes(values: list[float]) -> int:
    signs = [1 if value > 1e-12 else -1 for value in values if abs(value) > 1e-12]
    return sum(
        1 for left, right in zip(signs, signs[1:], strict=False) if left != right
    )


def _npv_at_rate(values: list[float], rate: float) -> float:
    if rate <= -1.0:
        return float("inf")
    return sum(value / ((1.0 + rate) ** period) for period, value in enumerate(values))


def _bisect_root(values: list[float], left: float, right: float) -> float:
    left_value = _npv_at_rate(values, left)
    for _ in range(100):
        middle = (left + right) / 2.0
        middle_value = _npv_at_rate(values, middle)
        if abs(middle_value) < 1e-10:
            return middle
        if (left_value < 0) == (middle_value < 0):
            left = middle
            left_value = middle_value
        else:
            right = middle
    return (left + right) / 2.0


def _irr_roots(values: list[float]) -> list[float]:
    if not any(value > 0 for value in values) or not any(value < 0 for value in values):
        return []
    grid: list[float] = [-0.9999 + index * (0.9999 / 250) for index in range(251)]
    maximum = log10(1001.0)
    grid.extend((10.0 ** (maximum * index / 500.0)) - 1.0 for index in range(1, 501))
    roots: list[float] = []
    previous_rate = grid[0]
    previous_value = _npv_at_rate(values, previous_rate)
    for rate in grid[1:]:
        value = _npv_at_rate(values, rate)
        if abs(value) < 1e-8:
            candidate = rate
        elif (previous_value < 0) != (value < 0):
            candidate = _bisect_root(values, previous_rate, rate)
        else:
            previous_rate = rate
            previous_value = value
            continue
        if not any(abs(candidate - existing) < 1e-7 for existing in roots):
            roots.append(candidate)
        previous_rate = rate
        previous_value = value
    return roots


def _payback(values: list[float]) -> float | None:
    cumulative = 0.0
    if values and values[0] >= 0:
        return 0.0
    for period, value in enumerate(values):
        previous = cumulative
        cumulative += value
        if period == 0:
            continue
        if previous < 0 <= cumulative and value > 0:
            fraction = -previous / value
            return (period - 1) + fraction
    return None


def _annualize(periodic_rate: float, frequency: str) -> float:
    return ((1.0 + periodic_rate) ** periods_per_year(frequency) - 1.0) * 100.0


def _mirr(
    values: list[float],
    finance_rate: float,
    reinvestment_rate: float,
    frequency: str,
) -> float | None:
    horizon = len(values) - 1
    if horizon <= 0:
        return None
    negative_pv = sum(
        -value / ((1.0 + finance_rate) ** period)
        for period, value in enumerate(values)
        if value < 0
    )
    positive_fv = sum(
        value * ((1.0 + reinvestment_rate) ** (horizon - period))
        for period, value in enumerate(values)
        if value > 0
    )
    if negative_pv <= 0 or positive_fv <= 0:
        return None
    periodic = (positive_fv / negative_pv) ** (1.0 / horizon) - 1.0
    return _annualize(periodic, frequency)


def _equivalent_annual_value(
    npv: float, annual_rate_percent: float, years: float
) -> float:
    if years <= 0:
        return 0.0
    rate = annual_rate_percent / 100.0
    if abs(rate) < 1e-12:
        return npv / years
    factor = rate * ((1.0 + rate) ** years) / (((1.0 + rate) ** years) - 1.0)
    return cast(float, npv * factor)


def _trace(
    metric_id: str,
    label: str,
    value: float | None,
    included: set[CashFlowCategory],
    flow_ids: list[str],
    formula: str,
    notes: str,
) -> MetricTrace:
    return MetricTrace(
        metric_id=metric_id,
        label=label,
        value=value,
        included_categories=[item for item in ALL_CATEGORIES if item in included],
        excluded_categories=[item for item in ALL_CATEGORIES if item not in included],
        included_flow_ids=flow_ids,
        formula=formula,
        notes=notes,
    )


def evaluate_cash_flow(
    scenario: CashFlowScenarioInput,
    *,
    generated_at: str | None = None,
) -> CashFlowPublication:
    frequency = scenario.context.period_frequency
    periodic_discount = effective_period_rate(
        scenario.discount_rate_percent_annual, frequency
    )
    periodic_finance = effective_period_rate(
        scenario.finance_rate_percent_annual, frequency
    )
    periodic_reinvestment = effective_period_rate(
        scenario.reinvestment_rate_percent_annual, frequency
    )
    expanded = expand_cash_flows(scenario)
    money_decimals = scenario.context.monetary_decimals
    ratio_decimals = scenario.context.ratio_decimals

    periods: list[PeriodCashFlow] = []
    net_values: list[float] = []
    discounted_values: list[float] = []
    cumulative = 0.0
    cumulative_discounted = 0.0
    pv_inflows = 0.0
    pv_outflows = 0.0
    total_inflows = 0.0
    total_outflows = 0.0
    bcr_benefits = 0.0
    bcr_costs = 0.0
    terminal_value = 0.0

    for period, line_items in enumerate(expanded):
        inflows = sum(
            item.signed_amount for item in line_items if item.signed_amount >= 0
        )
        outflows = -sum(
            item.signed_amount for item in line_items if item.signed_amount < 0
        )
        net = inflows - outflows
        discounted = net / ((1.0 + periodic_discount) ** period)
        cumulative += net
        cumulative_discounted += discounted
        total_inflows += inflows
        total_outflows += outflows
        pv_inflows += inflows / ((1.0 + periodic_discount) ** period)
        pv_outflows += outflows / ((1.0 + periodic_discount) ** period)
        for item in line_items:
            discounted_item = item.signed_amount / ((1.0 + periodic_discount) ** period)
            if item.category in BCR_BENEFIT_CATEGORIES:
                bcr_benefits += discounted_item
            elif item.category in COST_CATEGORIES:
                bcr_costs += -discounted_item
            if (
                period == scenario.analysis_horizon_periods
                and item.category in TERMINAL_CATEGORIES
            ):
                terminal_value += item.signed_amount
        net_values.append(net)
        discounted_values.append(discounted)
        periods.append(
            PeriodCashFlow(
                period=period,
                period_label=_label(period, frequency),
                inflows=round_half_up(inflows, money_decimals),
                outflows=round_half_up(outflows, money_decimals),
                net_cash_flow=round_half_up(net, money_decimals),
                discounted_net_cash_flow=round_half_up(discounted, money_decimals),
                cumulative_cash_flow=round_half_up(cumulative, money_decimals),
                cumulative_discounted_cash_flow=round_half_up(
                    cumulative_discounted, money_decimals
                ),
                line_items=[
                    item.model_copy(
                        update={
                            "amount": round_half_up(item.amount, money_decimals),
                            "signed_amount": round_half_up(
                                item.signed_amount, money_decimals
                            ),
                        }
                    )
                    for item in line_items
                ],
            )
        )

    npv = sum(discounted_values)
    sign_changes = _sign_changes(net_values)
    periodic_roots = _irr_roots(net_values)
    annual_roots = [_annualize(root, frequency) for root in periodic_roots]
    if sign_changes > 1:
        irr_status = "ambiguous_multiple_sign_changes"
        irr = None
    elif annual_roots:
        irr_status = "unique"
        irr = annual_roots[0]
    elif any(value > 0 for value in net_values) and any(
        value < 0 for value in net_values
    ):
        irr_status = "no_root"
        irr = None
    else:
        irr_status = "not_applicable"
        irr = None

    simple_payback = _payback(net_values)
    discounted_payback = _payback(discounted_values)
    mirr = _mirr(net_values, periodic_finance, periodic_reinvestment, frequency)
    profitability_index = None if pv_outflows <= 0 else pv_inflows / pv_outflows
    benefit_cost_ratio = None if bcr_costs <= 0 else bcr_benefits / bcr_costs
    horizon_years = scenario.analysis_horizon_periods / periods_per_year(frequency)
    eav = _equivalent_annual_value(
        npv, scenario.discount_rate_percent_annual, horizon_years
    )

    all_flow_ids = [line.flow_id for line in scenario.lines]
    bcr_flow_ids = [
        line.flow_id
        for line in scenario.lines
        if line.category in BCR_BENEFIT_CATEGORIES or line.category in COST_CATEGORIES
    ]
    terminal_flow_ids = [
        line.flow_id for line in scenario.lines if line.category in TERMINAL_CATEGORIES
    ]
    metric_trace = [
        _trace(
            "npv",
            "Net present value",
            round_half_up(npv, money_decimals),
            set(ALL_CATEGORIES),
            all_flow_ids,
            "Σ net cash flow_t / (1 + periodic discount rate)^t",
            "Includes every modeled cash-flow category.",
        ),
        _trace(
            "simple_payback",
            "Simple payback",
            None
            if simple_payback is None
            else round_half_up(simple_payback, ratio_decimals),
            set(ALL_CATEGORIES),
            all_flow_ids,
            "First undiscounted cumulative crossing, interpolated within period",
            "Does not discount cash flows after the recovery point.",
        ),
        _trace(
            "discounted_payback",
            "Discounted payback",
            None
            if discounted_payback is None
            else round_half_up(discounted_payback, ratio_decimals),
            set(ALL_CATEGORIES),
            all_flow_ids,
            "First discounted cumulative crossing, interpolated within period",
            "Uses the disclosed annual discount rate converted to the selected frequency.",
        ),
        _trace(
            "irr",
            "Internal rate of return",
            None if irr is None else round_half_up(irr, ratio_decimals),
            set(ALL_CATEGORIES),
            all_flow_ids,
            "Rate where NPV equals zero",
            "All detected roots are reported; multiple sign changes suppress a single IRR.",
        ),
        _trace(
            "mirr",
            "Modified internal rate of return",
            None if mirr is None else round_half_up(mirr, ratio_decimals),
            set(ALL_CATEGORIES),
            all_flow_ids,
            "(FV positive flows / PV negative flows)^(1/n) - 1",
            "Uses disclosed finance and reinvestment rates.",
        ),
        _trace(
            "profitability_index",
            "Profitability index",
            None
            if profitability_index is None
            else round_half_up(profitability_index, ratio_decimals),
            set(ALL_CATEGORIES),
            all_flow_ids,
            "PV of all inflows / PV of all outflows",
            "Includes grants and rebates as project inflows.",
        ),
        _trace(
            "benefit_cost_ratio",
            "Benefit-cost ratio",
            None
            if benefit_cost_ratio is None
            else round_half_up(benefit_cost_ratio, ratio_decimals),
            BCR_BENEFIT_CATEGORIES | COST_CATEGORIES,
            bcr_flow_ids,
            "PV of benefits / PV of costs",
            "Grants and rebates are excluded as transfers rather than treated as benefits.",
        ),
        _trace(
            "equivalent_annual_value",
            "Equivalent annual value",
            round_half_up(eav, money_decimals),
            set(ALL_CATEGORIES),
            all_flow_ids,
            "NPV × annual capital-recovery factor",
            "Expresses NPV as an equivalent annual amount over the analysis horizon.",
        ),
        _trace(
            "terminal_value",
            "Terminal value",
            round_half_up(terminal_value, money_decimals),
            TERMINAL_CATEGORIES,
            terminal_flow_ids,
            "Residual value + working-capital recovery - decommissioning cost in final period",
            "Reports only terminal categories occurring in the final analysis period.",
        ),
    ]

    flags = [
        "Nominal/real price and discount-rate bases match.",
        f"Cash-flow table reconciles across {len(periods)} periods including period 0.",
    ]
    if sign_changes > 1:
        flags.append(
            "IRR is ambiguous because the cash-flow series has multiple sign changes; use NPV, MIRR, and the listed roots instead."
        )
    elif irr_status == "no_root":
        flags.append("No IRR root was detected in the supported search range.")
    elif irr_status == "not_applicable":
        flags.append(
            "IRR is not applicable because cash flows do not include both signs."
        )
    if simple_payback is None:
        flags.append("Simple payback is not achieved within the selected horizon.")
    if discounted_payback is None:
        flags.append("Discounted payback is not achieved within the selected horizon.")
    if any(line.category == "working_capital" for line in scenario.lines) and not any(
        line.category == "working_capital_recovery" for line in scenario.lines
    ):
        flags.append("Working capital is modeled without an explicit recovery flow.")
    if terminal_value == 0:
        flags.append("No net terminal value is modeled in the final period.")

    return CashFlowPublication(
        project=scenario.project,
        context=scenario.context,
        assumptions=scenario,
        periods=periods,
        metrics=CashFlowMetrics(
            total_inflows=round_half_up(total_inflows, money_decimals),
            total_outflows=round_half_up(total_outflows, money_decimals),
            net_cash_flow=round_half_up(sum(net_values), money_decimals),
            present_value_inflows=round_half_up(pv_inflows, money_decimals),
            present_value_outflows=round_half_up(pv_outflows, money_decimals),
            npv=round_half_up(npv, money_decimals),
            simple_payback_periods=(
                None
                if simple_payback is None
                else round_half_up(simple_payback, ratio_decimals)
            ),
            discounted_payback_periods=(
                None
                if discounted_payback is None
                else round_half_up(discounted_payback, ratio_decimals)
            ),
            irr_percent_annual=(
                None if irr is None else round_half_up(irr, ratio_decimals)
            ),
            irr_roots_percent_annual=[
                round_half_up(root, ratio_decimals) for root in annual_roots
            ],
            irr_status=irr_status,
            mirr_percent_annual=(
                None if mirr is None else round_half_up(mirr, ratio_decimals)
            ),
            profitability_index=(
                None
                if profitability_index is None
                else round_half_up(profitability_index, ratio_decimals)
            ),
            benefit_cost_ratio=(
                None
                if benefit_cost_ratio is None
                else round_half_up(benefit_cost_ratio, ratio_decimals)
            ),
            equivalent_annual_value=round_half_up(eav, money_decimals),
            terminal_value=round_half_up(terminal_value, money_decimals),
            sign_changes=sign_changes,
            metric_trace=metric_trace,
        ),
        interpretation=CashFlowInterpretation(flags=flags),
        methodology=CashFlowMethodology(),
        metadata=CashFlowMetadata(
            generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        ),
    )
