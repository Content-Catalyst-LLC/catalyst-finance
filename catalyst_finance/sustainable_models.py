"""Sustainable-finance, carbon, and natural-capital contracts for v2.0.0."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .comparison_models import SourceRevision
from .models import ContractModel

SUSTAINABLE_CONTRACT_VERSION: Literal["2.0.0"] = "2.0.0"
SUSTAINABLE_MODEL_ID: Literal["catalyst-finance.sustainable"] = (
    "catalyst-finance.sustainable"
)
FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Percentage = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
CarbonValuationMethod = Literal[
    "shadow_price", "market_credit", "higher_of", "lower_of"
]
NaturalCapitalCategory = Literal[
    "water", "biodiversity", "soil", "forest", "ecosystem_service", "other"
]
TransitionKind = Literal["benefit", "cost"]


class NaturalCapitalAssetInput(ContractModel):
    asset_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=200)
    category: NaturalCapitalCategory
    quantity: NonNegative
    unit: str = Field(min_length=1, max_length=80)
    baseline_unit_value: NonNegative
    projected_unit_value: NonNegative
    annual_service_value: NonNegative = 0
    restoration_cost: NonNegative = 0
    confidence_percent: Percentage = 100


class TransitionItemInput(ContractModel):
    item_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=200)
    kind: TransitionKind
    amount: NonNegative
    probability_percent: Percentage = 100
    timing_years: NonNegative = 0


class SustainableDefinition(ContractModel):
    contract_version: Literal["2.0.0"] = SUSTAINABLE_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.sustainable"] = SUSTAINABLE_MODEL_ID
    analysis_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    source: SourceRevision
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    reporting_period: str = Field(min_length=1, max_length=120)
    horizon_years: Annotated[float, Field(gt=0, le=100, allow_inf_nan=False)] = 10
    discount_rate_percent: Annotated[
        float, Field(gt=-100, le=100, allow_inf_nan=False)
    ] = 5
    base_project_npv: FiniteNumber = 0
    baseline_emissions_tco2e: NonNegative
    project_emissions_tco2e: NonNegative
    carbon_price_per_tco2e: NonNegative
    carbon_credit_quantity_tco2e: NonNegative = 0
    carbon_credit_price_per_tco2e: NonNegative = 0
    carbon_credit_discount_percent: Percentage = 0
    verification_cost: NonNegative = 0
    carbon_valuation_method: CarbonValuationMethod = "shadow_price"
    natural_capital_assets: list[NaturalCapitalAssetInput] = Field(
        default_factory=list, max_length=200
    )
    transition_items: list[TransitionItemInput] = Field(
        default_factory=list, max_length=200
    )
    green_financing_principal: NonNegative = 0
    conventional_interest_rate_percent: Percentage = 0
    green_interest_rate_percent: Percentage = 0
    financing_term_years: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)] = 0

    @model_validator(mode="after")
    def validate_definition(self) -> SustainableDefinition:
        asset_ids = [item.asset_id for item in self.natural_capital_assets]
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError("natural-capital asset IDs must be unique")
        item_ids = [item.item_id for item in self.transition_items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("transition item IDs must be unique")
        if self.green_interest_rate_percent > self.conventional_interest_rate_percent:
            raise ValueError("green interest rate cannot exceed conventional rate")
        if self.green_financing_principal > 0 and self.financing_term_years <= 0:
            raise ValueError("green financing requires a positive financing term")
        return self


class NaturalCapitalAssetResult(ContractModel):
    asset_id: str
    label: str
    category: NaturalCapitalCategory
    quantity: float
    unit: str
    baseline_stock_value: float
    projected_stock_value: float
    gross_stock_uplift: float
    confidence_adjusted_stock_uplift: float
    annual_service_value: float
    service_value_present_value: float
    restoration_cost: float
    net_natural_capital_value: float
    confidence_percent: float


class TransitionItemResult(ContractModel):
    item_id: str
    label: str
    kind: TransitionKind
    nominal_amount: float
    probability_percent: float
    probability_adjusted_amount: float
    timing_years: float
    present_value: float
    signed_present_value: float


class CarbonResult(ContractModel):
    baseline_emissions_tco2e: float
    project_emissions_tco2e: float
    avoided_emissions_tco2e: float
    emissions_reduction_percent: float | None
    shadow_carbon_value: float
    eligible_credit_quantity_tco2e: float
    gross_market_credit_value: float
    discounted_market_credit_value: float
    verification_cost: float
    net_market_credit_value: float
    selected_carbon_value: float
    valuation_method: CarbonValuationMethod
    implied_abatement_cost_per_tco2e: float | None


class SustainableSummary(ContractModel):
    carbon_value: float
    natural_capital_value: float
    transition_benefit_present_value: float
    transition_cost_present_value: float
    net_transition_value: float
    green_financing_savings_present_value: float
    total_sustainable_value: float
    base_project_npv: float
    adjusted_project_npv: float


class SustainableMethodology(ContractModel):
    model_id: Literal["catalyst-finance.sustainable"] = SUSTAINABLE_MODEL_ID
    model_version: Literal["2.0.0"] = SUSTAINABLE_CONTRACT_VERSION
    carbon_double_count_policy: Literal["select_one_valuation_basis"] = (
        "select_one_valuation_basis"
    )
    credit_quantity_policy: Literal["capped_at_avoided_emissions"] = (
        "capped_at_avoided_emissions"
    )
    natural_capital_policy: Literal[
        "confidence_adjusted_stock_plus_discounted_services_less_restoration"
    ] = "confidence_adjusted_stock_plus_discounted_services_less_restoration"
    transition_policy: Literal["probability_adjusted_discounted_cash_flow"] = (
        "probability_adjusted_discounted_cash_flow"
    )
    financing_policy: Literal["discounted_interest_rate_differential"] = (
        "discounted_interest_rate_differential"
    )


class SustainableMetadata(ContractModel):
    generated_at: str
    version: Literal["2.0.0"] = SUSTAINABLE_CONTRACT_VERSION
    asset_count: int
    transition_item_count: int
    disclaimer: str


class SustainablePublication(ContractModel):
    contract_version: Literal["2.0.0"] = SUSTAINABLE_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.sustainable"] = SUSTAINABLE_MODEL_ID
    definition: SustainableDefinition
    carbon: CarbonResult
    natural_capital_assets: list[NaturalCapitalAssetResult]
    transition_items: list[TransitionItemResult]
    summary: SustainableSummary
    flags: list[str] = Field(min_length=1)
    methodology: SustainableMethodology
    metadata: SustainableMetadata
