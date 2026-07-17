"""Seeded Monte Carlo uncertainty and deterministic stress-testing engine."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, cast

from .calculation import round_half_up
from .cashflow import evaluate_cash_flow
from .cashflow_models import CashFlowPublication, CashFlowScenarioInput
from .comparison import _apply_parameter, _metric
from .uncertainty_models import (
    DistributionSpec,
    HistogramBin,
    MetricDistributionSummary,
    PercentileValue,
    RetainedSimulationSample,
    StressCaseResult,
    UncertaintyDefinition,
    UncertaintyMetadata,
    UncertaintyMethodology,
    UncertaintyPublication,
    VariableInfluence,
)

DISCLAIMER = (
    "Catalyst Finance provides transparent analytical support, not investment, "
    "accounting, tax, legal, or fiduciary advice. Probability estimates depend "
    "on the stated distributions, correlations, model structure, and evidence."
)


class XorShift32:
    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF or 0x6D2B79F5
        self._spare: float | None = None

    def next_uint32(self) -> int:
        value = self.state
        value ^= (value << 13) & 0xFFFFFFFF
        value ^= value >> 17
        value ^= (value << 5) & 0xFFFFFFFF
        self.state = value & 0xFFFFFFFF
        return self.state

    def uniform(self) -> float:
        return (self.next_uint32() + 0.5) / 4294967296.0

    def normal(self) -> float:
        if self._spare is not None:
            value = self._spare
            self._spare = None
            return value
        radius = math.sqrt(-2.0 * math.log(self.uniform()))
        theta = 2.0 * math.pi * self.uniform()
        self._spare = radius * math.sin(theta)
        return radius * math.cos(theta)


def _erf_approx(value: float) -> float:
    sign = -1.0 if value < 0 else 1.0
    absolute = abs(value)
    t = 1.0 / (1.0 + 0.3275911 * absolute)
    polynomial = (
        ((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t
        + 0.254829592
    ) * t
    return sign * (1.0 - polynomial * math.exp(-(absolute * absolute)))


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + _erf_approx(value / math.sqrt(2.0)))


def _cholesky(matrix: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    lower = [[0.0 for _ in range(size)] for _ in range(size)]
    for row in range(size):
        for column in range(row + 1):
            subtotal = sum(lower[row][k] * lower[column][k] for k in range(column))
            if row == column:
                diagonal = matrix[row][row] - subtotal
                if diagonal < -1e-10:
                    raise ValueError("correlation matrix is not positive semidefinite")
                lower[row][column] = math.sqrt(max(diagonal, 0.0))
            elif abs(lower[column][column]) < 1e-15:
                lower[row][column] = 0.0
            else:
                lower[row][column] = (matrix[row][column] - subtotal) / lower[column][
                    column
                ]
    return lower


def _correlation_factor(definition: UncertaintyDefinition) -> list[list[float]]:
    ids = [item.variable_id for item in definition.variables]
    index = {item_id: position for position, item_id in enumerate(ids)}
    matrix = [
        [1.0 if row == column else 0.0 for column in range(len(ids))]
        for row in range(len(ids))
    ]
    for pair in definition.correlations:
        left = index[pair.left_variable_id]
        right = index[pair.right_variable_id]
        matrix[left][right] = pair.coefficient
        matrix[right][left] = pair.coefficient
    return _cholesky(matrix)


def _sample_distribution(spec: DistributionSpec, z_value: float) -> float:
    probability = min(max(_normal_cdf(z_value), 1e-15), 1.0 - 1e-15)
    if spec.kind == "uniform":
        assert spec.minimum is not None and spec.maximum is not None
        value = spec.minimum + probability * (spec.maximum - spec.minimum)
    elif spec.kind == "triangular":
        assert (
            spec.minimum is not None
            and spec.mode is not None
            and spec.maximum is not None
        )
        split = (spec.mode - spec.minimum) / (spec.maximum - spec.minimum)
        if probability < split:
            value = spec.minimum + math.sqrt(
                probability * (spec.maximum - spec.minimum) * (spec.mode - spec.minimum)
            )
        else:
            value = spec.maximum - math.sqrt(
                (1.0 - probability)
                * (spec.maximum - spec.minimum)
                * (spec.maximum - spec.mode)
            )
    elif spec.kind == "normal":
        assert spec.mean is not None and spec.standard_deviation is not None
        value = spec.mean + spec.standard_deviation * z_value
    elif spec.kind == "lognormal":
        assert spec.log_mean is not None and spec.log_standard_deviation is not None
        value = math.exp(spec.log_mean + spec.log_standard_deviation * z_value)
    else:
        cumulative = 0.0
        value = spec.values[-1]
        for candidate, weight in zip(spec.values, spec.probabilities, strict=True):
            cumulative += weight
            if probability <= cumulative:
                value = candidate
                break
    if spec.truncate_minimum is not None:
        value = max(value, spec.truncate_minimum)
    if spec.truncate_maximum is not None:
        value = min(value, spec.truncate_maximum)
    return float(value)


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or len(left) != len(right):
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum(
        (x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True)
    )
    left_ss = sum((x - left_mean) ** 2 for x in left)
    right_ss = sum((y - right_mean) ** 2 for y in right)
    if left_ss <= 0 or right_ss <= 0:
        return None
    return numerator / math.sqrt(left_ss * right_ss)


def _metric_map(
    publication: CashFlowPublication, metric_ids: list[str]
) -> dict[str, float | None]:
    return {
        metric_id: _metric(publication, cast(Any, metric_id))
        for metric_id in metric_ids
    }


def _summary(
    metric_id: Any,
    values: list[float],
    percentiles: list[float],
    threshold: float | None,
) -> MetricDistributionSummary:
    mean = sum(values) / len(values)
    variance = sum((item - mean) ** 2 for item in values) / len(values)
    lower_tail_cutoff = _percentile(values, 5)
    lower_tail = [item for item in values if item <= lower_tail_cutoff]
    return MetricDistributionSummary(
        metric_id=metric_id,
        sample_count=len(values),
        mean=round_half_up(mean, 6),
        median=round_half_up(_percentile(values, 50), 6),
        standard_deviation=round_half_up(math.sqrt(variance), 6),
        minimum=round_half_up(min(values), 6),
        maximum=round_half_up(max(values), 6),
        percentiles=[
            PercentileValue(
                percentile=item, value=round_half_up(_percentile(values, item), 6)
            )
            for item in sorted(percentiles)
        ],
        downside_threshold=threshold,
        probability_above_zero=round_half_up(
            sum(item > 0 for item in values) / len(values), 6
        ),
        probability_below_threshold=(
            None
            if threshold is None
            else round_half_up(
                sum(item < threshold for item in values) / len(values), 6
            )
        ),
        value_at_risk_95=round_half_up(lower_tail_cutoff, 6),
        expected_shortfall_5=round_half_up(sum(lower_tail) / len(lower_tail), 6),
    )


def _histogram(metric_id: Any, values: list[float], bins: int) -> list[HistogramBin]:
    low = min(values)
    high = max(values)
    if abs(high - low) < 1e-15:
        return [
            HistogramBin(
                metric_id=metric_id,
                lower_bound=low,
                upper_bound=high,
                count=len(values),
            )
        ]
    width = (high - low) / bins
    counts = [0] * bins
    for value in values:
        index = min(bins - 1, int((value - low) / width))
        counts[index] += 1
    return [
        HistogramBin(
            metric_id=metric_id,
            lower_bound=round_half_up(low + index * width, 6),
            upper_bound=round_half_up(low + (index + 1) * width, 6),
            count=count,
        )
        for index, count in enumerate(counts)
    ]


def _stress_results(
    definition: UncertaintyDefinition, base_metrics: dict[str, float | None]
) -> list[StressCaseResult]:
    output: list[StressCaseResult] = []
    for case in definition.stress_cases:
        scenario = definition.scenario
        for adjustment in case.adjustments:
            scenario = _apply_parameter(
                scenario, adjustment.parameter, adjustment.value
            )
        metrics = _metric_map(evaluate_cash_flow(scenario), list(definition.metric_ids))
        deltas = {
            metric_id: (
                None
                if value is None or base_metrics.get(metric_id) is None
                else round_half_up(value - cast(float, base_metrics[metric_id]), 6)
            )
            for metric_id, value in metrics.items()
        }
        flags = [
            f"{metric_id} falls below {definition.downside_thresholds[cast(Any, metric_id)]}."
            for metric_id, value in metrics.items()
            if value is not None
            and metric_id in definition.downside_thresholds
            and value < definition.downside_thresholds[cast(Any, metric_id)]
        ] or ["No configured downside threshold is breached."]
        output.append(
            StressCaseResult(
                stress_id=case.stress_id,
                label=case.label,
                description=case.description,
                metrics=metrics,
                deltas_from_base=deltas,
                adjustments=case.adjustments,
                flags=flags,
            )
        )
    return output


def evaluate_uncertainty(
    definition: UncertaintyDefinition,
    *,
    generated_at: str | None = None,
) -> UncertaintyPublication:
    factor = _correlation_factor(definition)
    generator = XorShift32(definition.monte_carlo.seed)
    metric_values: dict[str, list[float]] = {item: [] for item in definition.metric_ids}
    variable_values: dict[str, list[float]] = {
        item.variable_id: [] for item in definition.variables
    }
    retained: list[RetainedSimulationSample] = []
    rejected = 0
    completed = 0
    attempts = 0
    maximum_attempts = definition.monte_carlo.iterations * 20
    while completed < definition.monte_carlo.iterations and attempts < maximum_attempts:
        attempts += 1
        independent = [generator.normal() for _ in definition.variables]
        correlated = [
            sum(factor[row][column] * independent[column] for column in range(row + 1))
            for row in range(len(definition.variables))
        ]
        sampled: dict[str, float] = {}
        scenario: CashFlowScenarioInput = definition.scenario
        try:
            for variable, z_value in zip(definition.variables, correlated, strict=True):
                value = _sample_distribution(variable.distribution, z_value)
                if variable.parameter.value_kind == "integer":
                    value = float(round(value))
                sampled[variable.variable_id] = value
                scenario = _apply_parameter(scenario, variable.parameter, value)
            metrics = _metric_map(
                evaluate_cash_flow(scenario), list(definition.metric_ids)
            )
            if any(
                value is None or not math.isfinite(value) for value in metrics.values()
            ):
                raise ValueError("simulation produced a non-finite metric")
        except (ValueError, OverflowError):
            rejected += 1
            continue
        completed += 1
        for variable_id, value in sampled.items():
            variable_values[variable_id].append(value)
        for metric_id, metric_value in metrics.items():
            if metric_value is None:
                raise AssertionError("validated simulation metric unexpectedly missing")
            metric_values[metric_id].append(metric_value)
        if len(retained) < definition.monte_carlo.retain_samples:
            retained.append(
                RetainedSimulationSample(
                    iteration=completed,
                    variable_values={
                        key: round_half_up(value, 8) for key, value in sampled.items()
                    },
                    metrics={
                        key: None if value is None else round_half_up(value, 8)
                        for key, value in metrics.items()
                    },
                )
            )
    if completed < definition.monte_carlo.iterations:
        raise ValueError(
            "unable to complete configured Monte Carlo iterations with valid samples"
        )
    base_metrics = _metric_map(
        evaluate_cash_flow(definition.scenario), list(definition.metric_ids)
    )
    summaries = [
        _summary(
            metric_id,
            metric_values[metric_id],
            definition.monte_carlo.percentiles,
            definition.downside_thresholds.get(cast(Any, metric_id)),
        )
        for metric_id in definition.metric_ids
    ]
    histograms = [
        item
        for metric_id in definition.metric_ids
        for item in _histogram(
            metric_id, metric_values[metric_id], definition.monte_carlo.histogram_bins
        )
    ]
    influences: list[VariableInfluence] = []
    for variable in definition.variables:
        for metric_id in definition.metric_ids:
            correlation = _pearson(
                variable_values[variable.variable_id], metric_values[metric_id]
            )
            influences.append(
                VariableInfluence(
                    variable_id=variable.variable_id,
                    label=variable.label,
                    metric_id=metric_id,
                    pearson_correlation=None
                    if correlation is None
                    else round_half_up(correlation, 6),
                    absolute_correlation=None
                    if correlation is None
                    else round_half_up(abs(correlation), 6),
                )
            )
    influences.sort(
        key=lambda item: (item.metric_id, -(item.absolute_correlation or 0), item.label)
    )
    canonical = json.dumps(
        definition.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return UncertaintyPublication(
        definition=definition,
        base_metrics=base_metrics,
        summaries=summaries,
        histograms=histograms,
        variable_influences=influences,
        retained_samples=retained,
        stress_results=_stress_results(definition, base_metrics),
        methodology=UncertaintyMethodology(),
        metadata=UncertaintyMetadata(
            generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
            configured_iterations=definition.monte_carlo.iterations,
            completed_iterations=completed,
            rejected_iterations=rejected,
            seed=definition.monte_carlo.seed,
            reproducibility_key=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            disclaimer=DISCLAIMER,
        ),
    )
