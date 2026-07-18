"""Cost, budget, variance, and operating-economics contracts for v2.0.0."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .comparison_models import SourceRevision
from .models import ContractModel

OPERATING_CONTRACT_VERSION: Literal["2.0.0"] = "2.0.0"
OPERATING_MODEL_ID: Literal["catalyst-finance.operating"] = "catalyst-finance.operating"
PeriodFrequency = Literal["monthly", "quarterly", "annual"]
VarianceStatus = Literal["favorable", "unfavorable", "neutral"]
FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class OperatingPeriodInput(ContractModel):
    period: Annotated[int, Field(ge=1, le=1200)]
    label: str = Field(min_length=1, max_length=120)
    budget_units: NonNegative
    actual_units: NonNegative
    budget_unit_price: NonNegative
    actual_unit_price: NonNegative
    budget_variable_cost_per_unit: NonNegative
    actual_variable_cost_per_unit: NonNegative
    budget_direct_fixed_cost: NonNegative = 0
    actual_direct_fixed_cost: NonNegative = 0
    budget_allocated_overhead: NonNegative = 0
    actual_allocated_overhead: NonNegative = 0


class OperatingUnitInput(ContractModel):
    unit_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=200)
    cost_center: str = Field(default="General", min_length=1, max_length=160)
    periods: list[OperatingPeriodInput] = Field(min_length=1, max_length=1200)

    @model_validator(mode="after")
    def unique_periods(self) -> OperatingUnitInput:
        values = [item.period for item in self.periods]
        if values != sorted(values) or len(values) != len(set(values)):
            raise ValueError("operating periods must be unique and increasing")
        return self


class OperatingDefinition(ContractModel):
    contract_version: Literal["2.0.0"] = OPERATING_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.operating"] = OPERATING_MODEL_ID
    operating_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    source: SourceRevision
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    period_frequency: PeriodFrequency = "monthly"
    target_operating_profit: FiniteNumber = 0
    units: list[OperatingUnitInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_units(self) -> OperatingDefinition:
        values = [item.unit_id for item in self.units]
        if len(values) != len(set(values)):
            raise ValueError("operating unit IDs must be unique")
        return self


class VarianceResult(ContractModel):
    variance_id: str
    label: str
    amount: float
    status: VarianceStatus
    rationale: str


class OperatingPeriodResult(ContractModel):
    unit_id: str
    unit_label: str
    cost_center: str
    period: int
    label: str
    budget_units: float
    actual_units: float
    budget_revenue: float
    flexible_revenue: float
    actual_revenue: float
    budget_variable_cost: float
    flexible_variable_cost: float
    actual_variable_cost: float
    budget_fixed_cost: float
    actual_fixed_cost: float
    budget_contribution: float
    flexible_contribution: float
    actual_contribution: float
    budget_operating_profit: float
    flexible_operating_profit: float
    actual_operating_profit: float
    budget_contribution_per_unit: float
    actual_contribution_per_unit: float
    contribution_margin_percent: float | None
    break_even_units: float | None
    break_even_revenue: float | None
    margin_of_safety_units: float | None
    margin_of_safety_percent: float | None
    degree_of_operating_leverage: float | None
    target_profit_units: float | None
    variances: list[VarianceResult] = Field(min_length=5, max_length=5)
    variance_reconciliation: float


class OperatingSummary(ContractModel):
    summary_id: str
    label: str
    budget_units: float
    actual_units: float
    budget_revenue: float
    actual_revenue: float
    budget_variable_cost: float
    actual_variable_cost: float
    budget_fixed_cost: float
    actual_fixed_cost: float
    budget_contribution: float
    actual_contribution: float
    budget_operating_profit: float
    actual_operating_profit: float
    operating_profit_variance: float
    contribution_margin_percent: float | None
    break_even_units: float | None
    margin_of_safety_units: float | None
    degree_of_operating_leverage: float | None
    target_profit_units: float | None


class OperatingMethodology(ContractModel):
    model_id: Literal["catalyst-finance.operating"] = OPERATING_MODEL_ID
    model_version: Literal["2.0.0"] = OPERATING_CONTRACT_VERSION
    budget_policy: Literal["static_flexible_actual"] = "static_flexible_actual"
    variance_sign_policy: Literal["positive_is_favorable"] = "positive_is_favorable"
    volume_variance_policy: Literal["budget_contribution_margin"] = (
        "budget_contribution_margin"
    )
    fixed_cost_policy: Literal["direct_plus_allocated_overhead"] = (
        "direct_plus_allocated_overhead"
    )
    break_even_policy: Literal["budget_contribution_margin_per_unit"] = (
        "budget_contribution_margin_per_unit"
    )
    aggregation_policy: Literal["sum_rows_then_recompute_ratios"] = (
        "sum_rows_then_recompute_ratios"
    )


class OperatingMetadata(ContractModel):
    generated_at: str
    version: Literal["2.0.0"] = OPERATING_CONTRACT_VERSION
    row_count: int
    unit_count: int
    cost_center_count: int
    disclaimer: str


class OperatingPublication(ContractModel):
    contract_version: Literal["2.0.0"] = OPERATING_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.operating"] = OPERATING_MODEL_ID
    definition: OperatingDefinition
    rows: list[OperatingPeriodResult] = Field(min_length=1)
    unit_summaries: list[OperatingSummary] = Field(min_length=1)
    cost_center_summaries: list[OperatingSummary] = Field(min_length=1)
    total_summary: OperatingSummary
    flags: list[str] = Field(min_length=1)
    methodology: OperatingMethodology
    metadata: OperatingMetadata
