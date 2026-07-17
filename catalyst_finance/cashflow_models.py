"""Typed cash-flow and capital-budgeting contracts for Catalyst Finance v1.6.0."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .models import ContractModel, FinanceProject

CASHFLOW_CONTRACT_VERSION: Literal["1.6.0"] = "1.6.0"
CASHFLOW_MODEL_ID: Literal["catalyst-finance.cash-flow"] = "catalyst-finance.cash-flow"

PeriodFrequency = Literal["monthly", "quarterly", "annual"]
PriceBasis = Literal["nominal", "real"]
CashFlowCategory = Literal[
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
IrrStatus = Literal[
    "unique",
    "ambiguous_multiple_sign_changes",
    "no_root",
    "not_applicable",
]

Money = Annotated[
    float,
    Field(allow_inf_nan=False, json_schema_extra={"x-unit": "currency"}),
]
NonNegativeMoney = Annotated[
    float,
    Field(ge=0, allow_inf_nan=False, json_schema_extra={"x-unit": "currency"}),
]
AnnualPercent = Annotated[
    float,
    Field(
        gt=-100,
        le=1000,
        allow_inf_nan=False,
        json_schema_extra={"x-unit": "percent_per_year"},
    ),
]


class CashFlowContext(ContractModel):
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    price_basis: PriceBasis = "nominal"
    discount_rate_basis: PriceBasis = "nominal"
    period_frequency: PeriodFrequency = "annual"
    time_basis: Literal["end_of_period"] = "end_of_period"
    rounding_policy: Literal["half_up"] = "half_up"
    monetary_decimals: Annotated[int, Field(ge=0, le=6)] = 2
    ratio_decimals: Annotated[int, Field(ge=0, le=6)] = 4

    @model_validator(mode="after")
    def matching_basis(self) -> CashFlowContext:
        if self.price_basis != self.discount_rate_basis:
            raise ValueError(
                "price_basis and discount_rate_basis must match for cash-flow analysis"
            )
        return self


class CashFlowLine(ContractModel):
    flow_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=240)
    category: CashFlowCategory
    amount: NonNegativeMoney
    start_period: Annotated[int, Field(ge=0)]
    end_period: Annotated[int | None, Field(default=None, ge=0)] = None
    interval_periods: Annotated[int, Field(ge=1)] = 1
    escalation_rate_percent_annual: AnnualPercent = 0
    price_basis: PriceBasis = "nominal"
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def valid_schedule(self) -> CashFlowLine:
        if self.end_period is not None and self.end_period < self.start_period:
            raise ValueError("end_period must be greater than or equal to start_period")
        return self


class CashFlowScenarioInput(ContractModel):
    contract_version: Literal["1.6.0"] = CASHFLOW_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.cash-flow"] = CASHFLOW_MODEL_ID
    project: FinanceProject
    context: CashFlowContext = Field(default_factory=CashFlowContext)
    analysis_horizon_periods: Annotated[int, Field(ge=1, le=1200)]
    discount_rate_percent_annual: AnnualPercent
    finance_rate_percent_annual: AnnualPercent = 0
    reinvestment_rate_percent_annual: AnnualPercent = 0
    lines: list[CashFlowLine] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_cash_flow_contract(self) -> CashFlowScenarioInput:
        ids = [line.flow_id for line in self.lines]
        if len(ids) != len(set(ids)):
            raise ValueError("cash-flow line IDs must be unique")
        for line in self.lines:
            end_period = (
                line.end_period if line.end_period is not None else line.start_period
            )
            if end_period > self.analysis_horizon_periods:
                raise ValueError(
                    f"cash-flow line {line.flow_id} exceeds the analysis horizon"
                )
            if line.price_basis != self.context.price_basis:
                raise ValueError(
                    f"cash-flow line {line.flow_id} price_basis must match context"
                )
        return self


class ExpandedCashFlowLine(ContractModel):
    flow_id: str
    label: str
    category: CashFlowCategory
    period: int
    amount: Money
    signed_amount: Money
    direction: Literal["inflow", "outflow"]


class PeriodCashFlow(ContractModel):
    period: int
    period_label: str
    inflows: Money
    outflows: Money
    net_cash_flow: Money
    discounted_net_cash_flow: Money
    cumulative_cash_flow: Money
    cumulative_discounted_cash_flow: Money
    line_items: list[ExpandedCashFlowLine]


class MetricTrace(ContractModel):
    metric_id: str
    label: str
    value: float | None
    included_categories: list[CashFlowCategory]
    excluded_categories: list[CashFlowCategory]
    included_flow_ids: list[str]
    formula: str
    notes: str


class CashFlowMetrics(ContractModel):
    total_inflows: Money
    total_outflows: Money
    net_cash_flow: Money
    present_value_inflows: Money
    present_value_outflows: Money
    npv: Money
    simple_payback_periods: float | None
    discounted_payback_periods: float | None
    irr_percent_annual: float | None
    irr_roots_percent_annual: list[float]
    irr_status: IrrStatus
    mirr_percent_annual: float | None
    profitability_index: float | None
    benefit_cost_ratio: float | None
    equivalent_annual_value: Money
    terminal_value: Money
    sign_changes: int
    metric_trace: list[MetricTrace] = Field(min_length=8)


class CashFlowInterpretation(ContractModel):
    basis_status: Literal["matched"] = "matched"
    flags: list[str] = Field(min_length=1)


class CashFlowMethodology(ContractModel):
    model_id: Literal["catalyst-finance.cash-flow"] = CASHFLOW_MODEL_ID
    model_version: Literal["1.6.0"] = CASHFLOW_CONTRACT_VERSION
    timing_policy: Literal["period_zero_then_end_of_period"] = (
        "period_zero_then_end_of_period"
    )
    annual_to_period_rate_policy: Literal["effective_rate_conversion"] = (
        "effective_rate_conversion"
    )
    escalation_policy: Literal["effective_annual_compounding"] = (
        "effective_annual_compounding"
    )
    payback_policy: Literal["linear_interpolation_within_crossing_period"] = (
        "linear_interpolation_within_crossing_period"
    )
    irr_policy: Literal["all_detected_roots_and_ambiguity_flag"] = (
        "all_detected_roots_and_ambiguity_flag"
    )
    transfer_policy: Literal["grants_and_rebates_excluded_from_bcr"] = (
        "grants_and_rebates_excluded_from_bcr"
    )


class CashFlowMetadata(ContractModel):
    generated_at: str
    tool: Literal["Catalyst Finance cash-flow engine"] = (
        "Catalyst Finance cash-flow engine"
    )
    version: Literal["1.6.0"] = CASHFLOW_CONTRACT_VERSION
    disclaimer: str


class CashFlowPublication(ContractModel):
    contract_version: Literal["1.6.0"] = CASHFLOW_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.cash-flow"] = CASHFLOW_MODEL_ID
    project: FinanceProject
    context: CashFlowContext
    assumptions: CashFlowScenarioInput
    periods: list[PeriodCashFlow]
    metrics: CashFlowMetrics
    interpretation: CashFlowInterpretation
    methodology: CashFlowMethodology
    metadata: CashFlowMetadata
