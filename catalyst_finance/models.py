"""Validated Catalyst Finance v1.6.0 contract records."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CONTRACT_VERSION: Literal["1.6.0"] = "1.6.0"
MODEL_ID: Literal["catalyst-finance.screening"] = "catalyst-finance.screening"
METHODOLOGY_VERSION: Literal["1.6.0"] = "1.6.0"

Money = Annotated[
    float,
    Field(allow_inf_nan=False, json_schema_extra={"x-unit": "currency"}),
]
NonNegativeMoney = Annotated[
    float,
    Field(ge=0, allow_inf_nan=False, json_schema_extra={"x-unit": "currency"}),
]
Percent = Annotated[
    float,
    Field(
        ge=0,
        le=100,
        allow_inf_nan=False,
        json_schema_extra={"x-unit": "percent"},
    ),
]


class ContractModel(BaseModel):  # type: ignore[misc]
    """Base class for strict versioned contract records."""

    model_config = ConfigDict(extra="forbid")


class FinanceProject(ContractModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(
        default="Sustainability finance", min_length=1, max_length=120
    )


class FinanceContext(ContractModel):
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    price_basis: Literal["nominal", "real"] = "nominal"
    discount_rate_basis: Literal["nominal", "real"] = "nominal"
    period_frequency: Literal["annual"] = "annual"
    time_basis: Literal["end_of_period"] = "end_of_period"
    rounding_policy: Literal["half_up"] = "half_up"
    monetary_decimals: Literal[2] = 2
    ratio_decimals: Literal[2] = 2
    score_decimals: Literal[1] = 1

    @model_validator(mode="after")
    def matching_rate_basis(self) -> FinanceContext:
        if self.price_basis != self.discount_rate_basis:
            raise ValueError(
                "price_basis and discount_rate_basis must match for this model"
            )
        return self


class FinanceInputs(ContractModel):
    capital_cost: NonNegativeMoney
    external_funding: NonNegativeMoney
    annual_savings: NonNegativeMoney
    annual_operating_cost: NonNegativeMoney
    time_horizon_years: Annotated[
        float,
        Field(
            gt=0,
            le=100,
            allow_inf_nan=False,
            json_schema_extra={"x-unit": "years"},
        ),
    ]
    discount_rate_percent: Annotated[
        float,
        Field(
            gt=-100,
            le=100,
            allow_inf_nan=False,
            json_schema_extra={"x-unit": "percent_per_year"},
        ),
    ]
    annual_emissions_reduced_tons: Annotated[
        float | None,
        Field(
            default=None,
            ge=0,
            allow_inf_nan=False,
            json_schema_extra={"x-unit": "metric_tons_co2e_per_year"},
        ),
    ] = None
    carbon_price_per_ton: Annotated[
        float,
        Field(
            default=0,
            ge=0,
            allow_inf_nan=False,
            json_schema_extra={"x-unit": "currency_per_metric_ton_co2e"},
        ),
    ] = 0
    confidence_percent: Percent
    implementation_risk_percent: Percent

    @model_validator(mode="after")
    def emissions_price_pair(self) -> FinanceInputs:
        if (
            self.annual_emissions_reduced_tons is None
            and self.carbon_price_per_ton != 0
        ):
            raise ValueError(
                "carbon_price_per_ton must be 0 when emissions data is not provided"
            )
        return self


class FinanceScenarioInput(ContractModel):
    contract_version: Literal["1.6.0"] = CONTRACT_VERSION
    model_id: Literal["catalyst-finance.screening"] = MODEL_ID
    project: FinanceProject
    context: FinanceContext = Field(default_factory=FinanceContext)
    assumptions: FinanceInputs


class ScoreComponent(ContractModel):
    component_id: str
    label: str
    raw_score: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
    weight: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]
    weighted_contribution: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
    rationale: str


class FinanceResults(ContractModel):
    net_capital_cost: Money
    carbon_value_per_year: Money
    net_annual_benefit: Money
    present_value_benefits: Money
    npv: Money
    payback_years: Annotated[
        float | None,
        Field(json_schema_extra={"x-unit": "years"}),
    ]
    roi_percent: Annotated[
        float | None,
        Field(json_schema_extra={"x-unit": "percent"}),
    ]
    benefit_cost_ratio: float | None
    carbon_cost_per_ton: Annotated[
        float | None,
        Field(json_schema_extra={"x-unit": "currency_per_metric_ton_co2e"}),
    ]
    risk_adjusted_score: Annotated[float, Field(ge=0, le=100)]
    score_components: list[ScoreComponent] = Field(min_length=4, max_length=4)


class FinanceInterpretation(ContractModel):
    risk_level: Literal["Lower concern", "Moderate concern", "High concern"]
    flags: list[str] = Field(min_length=1)


class FinanceNarrative(ContractModel):
    decision_note: str = Field(min_length=1)
    review_boundary: str = Field(min_length=1)


class FinanceMethodology(ContractModel):
    model_id: Literal["catalyst-finance.screening"] = MODEL_ID
    model_version: Literal["1.6.0"] = METHODOLOGY_VERSION
    calculation_basis: Literal["annual_screening"] = "annual_screening"
    fractional_horizon_policy: Literal["prorated_final_period"] = (
        "prorated_final_period"
    )
    overfunding_policy: Literal["net_capital_cost_floor_zero"] = (
        "net_capital_cost_floor_zero"
    )
    zero_cost_ratio_policy: Literal["undefined_null"] = "undefined_null"
    missing_emissions_policy: Literal["exclude_carbon_value"] = "exclude_carbon_value"
    score_policy: Literal["transparent_weighted_components"] = (
        "transparent_weighted_components"
    )


class MigrationRecord(ContractModel):
    source_contract_version: str
    target_contract_version: Literal["1.6.0"] = CONTRACT_VERSION
    preserved_fields: list[str]


class FinanceMetadata(ContractModel):
    generated_at: str
    tool: Literal["Catalyst Finance scenario engine"] = (
        "Catalyst Finance scenario engine"
    )
    version: Literal["1.6.0"] = CONTRACT_VERSION
    disclaimer: str
    migration: MigrationRecord | None = None


class FinancePublication(ContractModel):
    contract_version: Literal["1.6.0"] = CONTRACT_VERSION
    model_id: Literal["catalyst-finance.screening"] = MODEL_ID
    project: FinanceProject
    context: FinanceContext
    assumptions: FinanceInputs
    results: FinanceResults
    interpretation: FinanceInterpretation
    narrative: FinanceNarrative
    methodology: FinanceMethodology
    metadata: FinanceMetadata


def validation_issues(exc: Exception) -> list[dict[str, Any]]:
    """Return stable structured validation issues for CLI and API clients."""
    errors = getattr(exc, "errors", None)
    if not callable(errors):
        return [{"path": [], "code": "validation_error", "message": str(exc)}]
    issues: list[dict[str, Any]] = []
    for item in errors(include_url=False):
        issues.append(
            {
                "path": [str(part) for part in item.get("loc", ())],
                "code": str(item.get("type", "validation_error")),
                "message": str(item.get("msg", "Invalid value")),
            }
        )
    return issues
