"""Uncertainty, Monte Carlo, and stress-testing contracts for v1.6.0."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .cashflow_models import CashFlowScenarioInput
from .comparison_models import MetricId, SensitivityParameter, SourceRevision
from .models import ContractModel

UNCERTAINTY_CONTRACT_VERSION: Literal["1.6.0"] = "1.6.0"
UNCERTAINTY_MODEL_ID: Literal["catalyst-finance.uncertainty"] = (
    "catalyst-finance.uncertainty"
)

DistributionKind = Literal["uniform", "triangular", "normal", "lognormal", "discrete"]
FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]


class DistributionSpec(ContractModel):
    kind: DistributionKind
    minimum: FiniteNumber | None = None
    mode: FiniteNumber | None = None
    maximum: FiniteNumber | None = None
    mean: FiniteNumber | None = None
    standard_deviation: Annotated[
        float | None, Field(default=None, gt=0, allow_inf_nan=False)
    ] = None
    log_mean: FiniteNumber | None = None
    log_standard_deviation: Annotated[
        float | None, Field(default=None, gt=0, allow_inf_nan=False)
    ] = None
    values: list[FiniteNumber] = Field(default_factory=list, max_length=100)
    probabilities: list[Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]] = (
        Field(default_factory=list, max_length=100)
    )
    truncate_minimum: FiniteNumber | None = None
    truncate_maximum: FiniteNumber | None = None

    @model_validator(mode="after")
    def valid_distribution(self) -> DistributionSpec:
        if self.kind == "uniform":
            if (
                self.minimum is None
                or self.maximum is None
                or self.maximum <= self.minimum
            ):
                raise ValueError("uniform distributions require minimum < maximum")
        elif self.kind == "triangular":
            if self.minimum is None or self.mode is None or self.maximum is None:
                raise ValueError(
                    "triangular distributions require minimum, mode, and maximum"
                )
            if (
                not self.minimum <= self.mode <= self.maximum
                or self.maximum <= self.minimum
            ):
                raise ValueError(
                    "triangular distributions require minimum <= mode <= maximum"
                )
        elif self.kind == "normal":
            if self.mean is None or self.standard_deviation is None:
                raise ValueError(
                    "normal distributions require mean and standard_deviation"
                )
        elif self.kind == "lognormal":
            if self.log_mean is None or self.log_standard_deviation is None:
                raise ValueError(
                    "lognormal distributions require log_mean and log_standard_deviation"
                )
        elif self.kind == "discrete":
            if not self.values or len(self.values) != len(self.probabilities):
                raise ValueError(
                    "discrete distributions require equally sized values and probabilities"
                )
            if abs(sum(self.probabilities) - 1.0) > 1e-9:
                raise ValueError("discrete probabilities must sum to 1")
        if (
            self.truncate_minimum is not None
            and self.truncate_maximum is not None
            and self.truncate_maximum < self.truncate_minimum
        ):
            raise ValueError("truncate_maximum must be >= truncate_minimum")
        return self


class UncertaintyVariable(ContractModel):
    variable_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=200)
    parameter: SensitivityParameter
    distribution: DistributionSpec


class CorrelationPair(ContractModel):
    left_variable_id: str
    right_variable_id: str
    coefficient: Annotated[float, Field(gt=-1, lt=1, allow_inf_nan=False)]

    @model_validator(mode="after")
    def distinct_variables(self) -> CorrelationPair:
        if self.left_variable_id == self.right_variable_id:
            raise ValueError("correlation variables must be distinct")
        return self


class MonteCarloConfiguration(ContractModel):
    iterations: Annotated[int, Field(ge=100, le=100000)] = 1000
    seed: Annotated[int, Field(ge=0, le=4294967295)] = 20260717
    percentiles: list[Annotated[float, Field(gt=0, lt=100, allow_inf_nan=False)]] = (
        Field(default_factory=lambda: [5, 25, 50, 75, 95], min_length=1, max_length=19)
    )
    retain_samples: Annotated[int, Field(ge=0, le=1000)] = 100
    histogram_bins: Annotated[int, Field(ge=5, le=50)] = 12

    @model_validator(mode="after")
    def unique_percentiles(self) -> MonteCarloConfiguration:
        if len(self.percentiles) != len(set(self.percentiles)):
            raise ValueError("percentiles must be unique")
        return self


class StressAdjustment(ContractModel):
    parameter: SensitivityParameter
    value: FiniteNumber


class StressCase(ContractModel):
    stress_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    adjustments: list[StressAdjustment] = Field(min_length=1, max_length=50)


class UncertaintyDefinition(ContractModel):
    contract_version: Literal["1.6.0"] = UNCERTAINTY_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.uncertainty"] = UNCERTAINTY_MODEL_ID
    uncertainty_id: str = Field(
        min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$"
    )
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    source: SourceRevision
    scenario: CashFlowScenarioInput
    metric_ids: list[MetricId] = Field(
        default_factory=lambda: ["npv"], min_length=1, max_length=8
    )
    variables: list[UncertaintyVariable] = Field(min_length=1, max_length=50)
    correlations: list[CorrelationPair] = Field(default_factory=list, max_length=1225)
    stress_cases: list[StressCase] = Field(default_factory=list, max_length=50)
    downside_thresholds: dict[MetricId, FiniteNumber] = Field(
        default_factory=lambda: {"npv": 0}
    )
    monte_carlo: MonteCarloConfiguration = Field(
        default_factory=MonteCarloConfiguration
    )

    @model_validator(mode="after")
    def valid_definition(self) -> UncertaintyDefinition:
        variable_ids = [item.variable_id for item in self.variables]
        if len(variable_ids) != len(set(variable_ids)):
            raise ValueError("uncertainty variable IDs must be unique")
        metric_ids = list(self.metric_ids)
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("metric IDs must be unique")
        known = set(variable_ids)
        seen_pairs: set[tuple[str, str]] = set()
        for pair in self.correlations:
            if (
                pair.left_variable_id not in known
                or pair.right_variable_id not in known
            ):
                raise ValueError(
                    "correlations must reference known uncertainty variables"
                )
            key = (
                (pair.left_variable_id, pair.right_variable_id)
                if pair.left_variable_id < pair.right_variable_id
                else (pair.right_variable_id, pair.left_variable_id)
            )
            if key in seen_pairs:
                raise ValueError("correlation pairs must be unique")
            seen_pairs.add(key)
        stress_ids = [item.stress_id for item in self.stress_cases]
        if len(stress_ids) != len(set(stress_ids)):
            raise ValueError("stress case IDs must be unique")
        return self


class PercentileValue(ContractModel):
    percentile: float
    value: float


class MetricDistributionSummary(ContractModel):
    metric_id: MetricId
    sample_count: int
    mean: float
    median: float
    standard_deviation: float
    minimum: float
    maximum: float
    percentiles: list[PercentileValue]
    downside_threshold: float | None
    probability_above_zero: float
    probability_below_threshold: float | None
    value_at_risk_95: float
    expected_shortfall_5: float


class HistogramBin(ContractModel):
    metric_id: MetricId
    lower_bound: float
    upper_bound: float
    count: int


class VariableInfluence(ContractModel):
    variable_id: str
    label: str
    metric_id: MetricId
    pearson_correlation: float | None
    absolute_correlation: float | None


class RetainedSimulationSample(ContractModel):
    iteration: int
    variable_values: dict[str, float]
    metrics: dict[str, float | None]


class StressCaseResult(ContractModel):
    stress_id: str
    label: str
    description: str
    metrics: dict[str, float | None]
    deltas_from_base: dict[str, float | None]
    adjustments: list[StressAdjustment]
    flags: list[str]


class UncertaintyMethodology(ContractModel):
    model_id: Literal["catalyst-finance.uncertainty"] = UNCERTAINTY_MODEL_ID
    model_version: Literal["1.6.0"] = UNCERTAINTY_CONTRACT_VERSION
    random_generator: Literal["xorshift32_box_muller"] = "xorshift32_box_muller"
    correlation_policy: Literal["gaussian_copula_cholesky"] = "gaussian_copula_cholesky"
    percentile_policy: Literal["linear_interpolation"] = "linear_interpolation"
    risk_policy: Literal["lower_tail_var95_and_expected_shortfall5"] = (
        "lower_tail_var95_and_expected_shortfall5"
    )
    stress_policy: Literal["deterministic_parameter_substitution"] = (
        "deterministic_parameter_substitution"
    )


class UncertaintyMetadata(ContractModel):
    generated_at: str
    version: Literal["1.6.0"] = UNCERTAINTY_CONTRACT_VERSION
    configured_iterations: int
    completed_iterations: int
    rejected_iterations: int
    seed: int
    reproducibility_key: str
    disclaimer: str


class UncertaintyPublication(ContractModel):
    contract_version: Literal["1.6.0"] = UNCERTAINTY_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.uncertainty"] = UNCERTAINTY_MODEL_ID
    definition: UncertaintyDefinition
    base_metrics: dict[str, float | None]
    summaries: list[MetricDistributionSummary]
    histograms: list[HistogramBin]
    variable_influences: list[VariableInfluence]
    retained_samples: list[RetainedSimulationSample]
    stress_results: list[StressCaseResult]
    methodology: UncertaintyMethodology
    metadata: UncertaintyMetadata
