"""Scenario comparison, sensitivity, and threshold contracts for v2.0.0."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .cashflow_models import CashFlowPublication, CashFlowScenarioInput
from .models import ContractModel

COMPARISON_CONTRACT_VERSION: Literal["2.0.0"] = "2.0.0"
COMPARISON_MODEL_ID: Literal["catalyst-finance.comparison"] = (
    "catalyst-finance.comparison"
)

AlternativeKind = Literal["base", "downside", "upside", "custom"]
MetricId = Literal[
    "npv",
    "net_cash_flow",
    "discounted_payback_periods",
    "irr_percent_annual",
    "mirr_percent_annual",
    "profitability_index",
    "benefit_cost_ratio",
    "equivalent_annual_value",
]
MetricObjective = Literal["maximize", "minimize"]
ParameterOperation = Literal["set", "multiply", "shift_periods"]
ParameterValueKind = Literal["continuous", "integer"]
ThresholdStatus = Literal[
    "found",
    "already_at_target",
    "no_crossing",
    "invalid_parameter",
]

FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]


class SourceRevision(ContractModel):
    workspace_id: str = Field(min_length=1, max_length=120)
    scenario_id: str = Field(min_length=1, max_length=120)
    revision_id: str = Field(min_length=1, max_length=120)
    revision_number: Annotated[int, Field(ge=1)]


class ComparisonAlternative(ContractModel):
    alternative_id: str = Field(
        min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$"
    )
    label: str = Field(min_length=1, max_length=200)
    kind: AlternativeKind = "custom"
    source: SourceRevision
    scenario: CashFlowScenarioInput
    non_financial_caveats: list[str] = Field(default_factory=list, max_length=50)


class MetricSelection(ContractModel):
    metric_id: MetricId
    objective: MetricObjective = "maximize"
    weight: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)] = 1


class SensitivityParameter(ContractModel):
    parameter_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=200)
    path: str = Field(min_length=1, max_length=240)
    operation: ParameterOperation = "set"
    value_kind: ParameterValueKind = "continuous"
    unit: str = Field(default="", max_length=80)


class OneWaySensitivityDefinition(ContractModel):
    sensitivity_id: str = Field(
        min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$"
    )
    alternative_id: str
    metric_id: MetricId = "npv"
    parameter: SensitivityParameter
    values: list[FiniteNumber] = Field(min_length=2, max_length=101)

    @model_validator(mode="after")
    def unique_values(self) -> OneWaySensitivityDefinition:
        if len(self.values) != len(set(self.values)):
            raise ValueError("one-way sensitivity values must be unique")
        return self


class TwoWaySensitivityDefinition(ContractModel):
    sensitivity_id: str = Field(
        min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$"
    )
    alternative_id: str
    metric_id: MetricId = "npv"
    row_parameter: SensitivityParameter
    row_values: list[FiniteNumber] = Field(min_length=2, max_length=25)
    column_parameter: SensitivityParameter
    column_values: list[FiniteNumber] = Field(min_length=2, max_length=25)

    @model_validator(mode="after")
    def distinct_parameters(self) -> TwoWaySensitivityDefinition:
        if self.row_parameter.parameter_id == self.column_parameter.parameter_id:
            raise ValueError("two-way sensitivity parameters must be distinct")
        return self


class BreakEvenDefinition(ContractModel):
    threshold_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    alternative_id: str
    metric_id: MetricId = "npv"
    parameter: SensitivityParameter
    target_value: FiniteNumber = 0
    lower_bound: FiniteNumber
    upper_bound: FiniteNumber
    tolerance: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 0.0001
    max_iterations: Annotated[int, Field(ge=10, le=500)] = 100

    @model_validator(mode="after")
    def ordered_bounds(self) -> BreakEvenDefinition:
        if self.upper_bound <= self.lower_bound:
            raise ValueError("upper_bound must be greater than lower_bound")
        return self


class ComparisonDefinition(ContractModel):
    contract_version: Literal["2.0.0"] = COMPARISON_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.comparison"] = COMPARISON_MODEL_ID
    comparison_id: str = Field(
        min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$"
    )
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    baseline_alternative_id: str
    alternatives: list[ComparisonAlternative] = Field(min_length=3, max_length=50)
    selected_metrics: list[MetricSelection] = Field(min_length=1, max_length=20)
    one_way_sensitivities: list[OneWaySensitivityDefinition] = Field(
        default_factory=list, max_length=50
    )
    two_way_sensitivities: list[TwoWaySensitivityDefinition] = Field(
        default_factory=list, max_length=20
    )
    break_even_definitions: list[BreakEvenDefinition] = Field(
        default_factory=list, max_length=50
    )

    @model_validator(mode="after")
    def valid_definition(self) -> ComparisonDefinition:
        alternative_ids = [item.alternative_id for item in self.alternatives]
        if len(alternative_ids) != len(set(alternative_ids)):
            raise ValueError("comparison alternative IDs must be unique")
        if self.baseline_alternative_id not in set(alternative_ids):
            raise ValueError("baseline_alternative_id must reference an alternative")
        metric_ids = [item.metric_id for item in self.selected_metrics]
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("selected metric IDs must be unique")
        known = set(alternative_ids)
        referenced = [
            item.alternative_id
            for item in [
                *self.one_way_sensitivities,
                *self.two_way_sensitivities,
                *self.break_even_definitions,
            ]
        ]
        unknown = sorted(set(referenced).difference(known))
        if unknown:
            raise ValueError(
                f"analysis definitions reference unknown alternatives: {unknown}"
            )
        return self


class AlternativeMetricValue(ContractModel):
    alternative_id: str
    label: str
    value: float | None
    delta_from_baseline: float | None
    rank: int | None


class AlignedMetricComparison(ContractModel):
    metric_id: MetricId
    label: str
    objective: MetricObjective
    baseline_value: float | None
    values: list[AlternativeMetricValue]


class AlternativeEvaluation(ContractModel):
    alternative_id: str
    label: str
    kind: AlternativeKind
    source: SourceRevision
    non_financial_caveats: list[str]
    metrics: dict[str, float | None]
    publication: CashFlowPublication


class AlternativeRanking(ContractModel):
    alternative_id: str
    label: str
    rank: int
    weighted_score: float
    dominates: list[str]
    dominated_by: list[str]
    financial_only: Literal[True] = True


class DriverContribution(ContractModel):
    path: str
    label: str
    baseline_value: float | int | None
    alternative_value: float | int | None
    npv_impact: float


class DifferenceExplanation(ContractModel):
    alternative_id: str
    relative_to_alternative_id: str
    npv_delta: float
    top_drivers: list[DriverContribution]
    non_financial_caveats: list[str]
    notes: list[str]


class SensitivityPoint(ContractModel):
    parameter_value: float
    metric_value: float | None
    baseline_metric_value: float | None
    delta_from_baseline: float | None


class OneWaySensitivityResult(ContractModel):
    sensitivity_id: str
    alternative_id: str
    metric_id: MetricId
    parameter: SensitivityParameter
    base_parameter_value: float | None
    base_metric_value: float | None
    points: list[SensitivityPoint]
    reproducibility_key: str


class TwoWaySensitivityCell(ContractModel):
    row_value: float
    column_value: float
    metric_value: float | None


class TwoWaySensitivityResult(ContractModel):
    sensitivity_id: str
    alternative_id: str
    metric_id: MetricId
    row_parameter: SensitivityParameter
    column_parameter: SensitivityParameter
    cells: list[TwoWaySensitivityCell]
    reproducibility_key: str


class BreakEvenCrossing(ContractModel):
    lower_value: float
    upper_value: float
    threshold_value: float
    metric_value: float | None


class BreakEvenResult(ContractModel):
    threshold_id: str
    alternative_id: str
    metric_id: MetricId
    parameter: SensitivityParameter
    target_value: float
    status: ThresholdStatus
    threshold_value: float | None
    metric_value: float | None
    crossings: list[BreakEvenCrossing]
    iterations: int
    reproducibility_key: str
    notes: list[str]


class TornadoBar(ContractModel):
    sensitivity_id: str
    alternative_id: str
    parameter_id: str
    label: str
    low_value: float
    high_value: float
    low_impact: float | None
    high_impact: float | None
    absolute_swing: float | None


class CrossoverPoint(ContractModel):
    sensitivity_id: str
    alternative_id: str
    baseline_alternative_id: str
    parameter_id: str
    parameter_value: float
    metric_id: MetricId
    metric_value: float


class ComparisonMethodology(ContractModel):
    model_id: Literal["catalyst-finance.comparison"] = COMPARISON_MODEL_ID
    model_version: Literal["2.0.0"] = COMPARISON_CONTRACT_VERSION
    ranking_policy: Literal["weighted_min_max_normalization"] = (
        "weighted_min_max_normalization"
    )
    dominance_policy: Literal["pareto_financial_metrics_only"] = (
        "pareto_financial_metrics_only"
    )
    sensitivity_policy: Literal["deterministic_parameter_substitution"] = (
        "deterministic_parameter_substitution"
    )
    break_even_policy: Literal["bounded_scan_then_bisection"] = (
        "bounded_scan_then_bisection"
    )
    difference_policy: Literal["one_assumption_at_a_time_npv_impacts"] = (
        "one_assumption_at_a_time_npv_impacts"
    )


class ComparisonMetadata(ContractModel):
    generated_at: str
    tool: Literal["Catalyst Finance comparison engine"] = (
        "Catalyst Finance comparison engine"
    )
    version: Literal["2.0.0"] = COMPARISON_CONTRACT_VERSION
    disclaimer: str


class ComparisonPublication(ContractModel):
    contract_version: Literal["2.0.0"] = COMPARISON_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.comparison"] = COMPARISON_MODEL_ID
    definition: ComparisonDefinition
    alternatives: list[AlternativeEvaluation]
    aligned_metrics: list[AlignedMetricComparison]
    rankings: list[AlternativeRanking]
    difference_explanations: list[DifferenceExplanation]
    one_way_sensitivities: list[OneWaySensitivityResult]
    two_way_sensitivities: list[TwoWaySensitivityResult]
    break_even_results: list[BreakEvenResult]
    tornado: list[TornadoBar]
    crossover_points: list[CrossoverPoint]
    methodology: ComparisonMethodology
    metadata: ComparisonMetadata
