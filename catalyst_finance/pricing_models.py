"""Demand, elasticity, pricing, and revenue contracts for v1.7.0."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .comparison_models import SourceRevision
from .models import ContractModel

PRICING_CONTRACT_VERSION: Literal["1.7.0"] = "1.7.0"
PRICING_MODEL_ID: Literal["catalyst-finance.pricing"] = "catalyst-finance.pricing"
FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]
DemandKind = Literal["linear", "constant_elasticity", "observed"]
PricingObjective = Literal["revenue", "contribution", "profit"]


class ObservedDemandPoint(ContractModel):
    price: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    quantity: Annotated[float, Field(ge=0, allow_inf_nan=False)]


class DemandCurve(ContractModel):
    kind: DemandKind
    intercept: Annotated[
        float | None, Field(default=None, gt=0, allow_inf_nan=False)
    ] = None
    slope: Annotated[float | None, Field(default=None, gt=0, allow_inf_nan=False)] = (
        None
    )
    reference_price: Annotated[
        float | None, Field(default=None, gt=0, allow_inf_nan=False)
    ] = None
    reference_quantity: Annotated[
        float | None, Field(default=None, ge=0, allow_inf_nan=False)
    ] = None
    elasticity: Annotated[
        float | None, Field(default=None, lt=0, allow_inf_nan=False)
    ] = None
    observed_points: list[ObservedDemandPoint] = Field(
        default_factory=list, max_length=500
    )

    @model_validator(mode="after")
    def valid_curve(self) -> DemandCurve:
        if self.kind == "linear":
            if self.intercept is None or self.slope is None:
                raise ValueError("linear demand requires intercept and slope")
        elif self.kind == "constant_elasticity":
            if (
                self.reference_price is None
                or self.reference_quantity is None
                or self.elasticity is None
            ):
                raise ValueError(
                    "constant_elasticity demand requires reference_price, reference_quantity, and elasticity"
                )
        else:
            if len(self.observed_points) < 2:
                raise ValueError("observed demand requires at least two points")
            prices = [point.price for point in self.observed_points]
            if prices != sorted(prices) or len(prices) != len(set(prices)):
                raise ValueError("observed demand prices must be unique and increasing")
        return self


class DemandSegment(ContractModel):
    segment_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=200)
    quantity_multiplier: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 1
    curve: DemandCurve


class PricingCostStructure(ContractModel):
    fixed_cost: Annotated[float, Field(ge=0, allow_inf_nan=False)] = 0
    unit_variable_cost: Annotated[float, Field(ge=0, allow_inf_nan=False)] = 0
    unit_fulfillment_cost: Annotated[float, Field(ge=0, allow_inf_nan=False)] = 0
    channel_fee_percent: Annotated[float, Field(ge=0, lt=100, allow_inf_nan=False)] = 0


class PricingGrid(ContractModel):
    minimum_price: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    maximum_price: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    steps: Annotated[int, Field(ge=3, le=1001)] = 41

    @model_validator(mode="after")
    def ordered(self) -> PricingGrid:
        if self.maximum_price <= self.minimum_price:
            raise ValueError("maximum_price must be greater than minimum_price")
        return self


class PricingConstraints(ContractModel):
    capacity_units: Annotated[
        float | None, Field(default=None, gt=0, allow_inf_nan=False)
    ] = None
    minimum_volume_units: Annotated[
        float | None, Field(default=None, ge=0, allow_inf_nan=False)
    ] = None
    maximum_price_change_percent: Annotated[
        float | None, Field(default=None, gt=0, allow_inf_nan=False)
    ] = None


class PricingDefinition(ContractModel):
    contract_version: Literal["1.7.0"] = PRICING_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.pricing"] = PRICING_MODEL_ID
    pricing_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    source: SourceRevision
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    objective: PricingObjective = "profit"
    current_price: Annotated[
        float | None, Field(default=None, gt=0, allow_inf_nan=False)
    ] = None
    segments: list[DemandSegment] = Field(min_length=1, max_length=50)
    costs: PricingCostStructure = Field(default_factory=PricingCostStructure)
    grid: PricingGrid
    constraints: PricingConstraints = Field(default_factory=PricingConstraints)

    @model_validator(mode="after")
    def valid_definition(self) -> PricingDefinition:
        ids = [segment.segment_id for segment in self.segments]
        if len(ids) != len(set(ids)):
            raise ValueError("pricing segment IDs must be unique")
        return self


class SegmentPriceResult(ContractModel):
    segment_id: str
    label: str
    unconstrained_quantity: float
    quantity: float
    elasticity: float | None
    demand_classification: str
    interpolation_policy: str


class PriceResult(ContractModel):
    price: float
    segments: list[SegmentPriceResult]
    unconstrained_quantity: float
    quantity: float
    gross_revenue: float
    variable_cost: float
    contribution: float
    operating_profit: float
    contribution_margin_percent: float | None
    average_elasticity: float | None
    capacity_constrained: bool
    minimum_volume_met: bool | None
    break_even_quantity: float | None
    break_even_met: bool | None


class PricingOptimum(ContractModel):
    objective: PricingObjective
    price: float
    quantity: float
    value: float
    row_index: int


class PricingRecommendation(ContractModel):
    objective: PricingObjective
    current_price: float | None
    recommended_price: float
    absolute_price_change: float | None
    percent_price_change: float | None
    current_objective_value: float | None
    recommended_objective_value: float
    expected_objective_gain: float | None
    constraint_limited: bool
    narrative: str


class PricingMethodology(ContractModel):
    model_id: Literal["catalyst-finance.pricing"] = PRICING_MODEL_ID
    model_version: Literal["1.7.0"] = PRICING_CONTRACT_VERSION
    grid_policy: Literal["inclusive_even_price_grid"] = "inclusive_even_price_grid"
    observed_policy: Literal["piecewise_linear_with_endpoint_clamping"] = (
        "piecewise_linear_with_endpoint_clamping"
    )
    capacity_policy: Literal["proportional_segment_allocation"] = (
        "proportional_segment_allocation"
    )
    optimum_tie_policy: Literal["lowest_price"] = "lowest_price"
    elasticity_policy: Literal[
        "point_linear_constant_or_local_observed_quantity_weighted"
    ] = "point_linear_constant_or_local_observed_quantity_weighted"


class PricingMetadata(ContractModel):
    generated_at: str
    version: Literal["1.7.0"] = PRICING_CONTRACT_VERSION
    grid_rows: int
    constrained_rows: int
    disclaimer: str


class PricingPublication(ContractModel):
    contract_version: Literal["1.7.0"] = PRICING_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.pricing"] = PRICING_MODEL_ID
    definition: PricingDefinition
    rows: list[PriceResult] = Field(min_length=3)
    current_position: PriceResult | None
    optima: list[PricingOptimum] = Field(min_length=3, max_length=3)
    recommendation: PricingRecommendation
    flags: list[str]
    methodology: PricingMethodology
    metadata: PricingMetadata
