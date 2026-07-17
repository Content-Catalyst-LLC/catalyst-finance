"""Deterministic comparison, sensitivity, and break-even engine."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timezone
from math import ceil, floor
from typing import Any, cast

from .calculation import round_half_up
from .cashflow import evaluate_cash_flow
from .cashflow_models import CashFlowPublication, CashFlowScenarioInput
from .comparison_models import (
    AlignedMetricComparison,
    AlternativeEvaluation,
    AlternativeMetricValue,
    AlternativeRanking,
    BreakEvenCrossing,
    BreakEvenDefinition,
    BreakEvenResult,
    ComparisonDefinition,
    ComparisonMetadata,
    ComparisonMethodology,
    ComparisonPublication,
    CrossoverPoint,
    DifferenceExplanation,
    DriverContribution,
    MetricId,
    MetricObjective,
    OneWaySensitivityDefinition,
    OneWaySensitivityResult,
    SensitivityParameter,
    SensitivityPoint,
    TornadoBar,
    TwoWaySensitivityCell,
    TwoWaySensitivityDefinition,
    TwoWaySensitivityResult,
)

DISCLAIMER = (
    "Catalyst Finance provides transparent analytical support, not investment, "
    "accounting, tax, legal, or fiduciary advice. Rankings are financial-model "
    "outputs and do not replace governance review or non-financial judgment."
)

METRIC_LABELS: dict[MetricId, str] = {
    "npv": "Net present value",
    "net_cash_flow": "Net cash flow",
    "discounted_payback_periods": "Discounted payback",
    "irr_percent_annual": "Internal rate of return",
    "mirr_percent_annual": "Modified internal rate of return",
    "profitability_index": "Profitability index",
    "benefit_cost_ratio": "Benefit-cost ratio",
    "equivalent_annual_value": "Equivalent annual value",
}


def _metric(publication: CashFlowPublication, metric_id: MetricId) -> float | None:
    value = getattr(publication.metrics, metric_id)
    return None if value is None else float(value)


def _canonical_key(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _parameter_value(
    scenario: CashFlowScenarioInput, parameter: SensitivityParameter
) -> float | None:
    if parameter.operation == "multiply":
        return 1.0
    if parameter.operation == "shift_periods":
        return 0.0
    if parameter.path in {
        "analysis_horizon_periods",
        "discount_rate_percent_annual",
        "finance_rate_percent_annual",
        "reinvestment_rate_percent_annual",
    }:
        return float(getattr(scenario, parameter.path))
    parts = parameter.path.split(":")
    if len(parts) == 3 and parts[0] == "line":
        _, flow_id, field = parts
        for line in scenario.lines:
            if line.flow_id == flow_id:
                value = getattr(line, field, None)
                return None if value is None else float(value)
    if len(parts) == 3 and parts[0] == "category":
        return None
    return None


def _apply_parameter(
    scenario: CashFlowScenarioInput,
    parameter: SensitivityParameter,
    value: float,
) -> CashFlowScenarioInput:
    payload = scenario.model_dump(mode="json")
    if parameter.value_kind == "integer":
        value = float(round(value))
    if parameter.path in {
        "analysis_horizon_periods",
        "discount_rate_percent_annual",
        "finance_rate_percent_annual",
        "reinvestment_rate_percent_annual",
    }:
        payload[parameter.path] = (
            int(value) if parameter.path == "analysis_horizon_periods" else float(value)
        )
        return cast(
            CashFlowScenarioInput, CashFlowScenarioInput.model_validate(payload)
        )

    parts = parameter.path.split(":")
    if parameter.operation == "shift_periods":
        shift = int(round(value))
        for line in payload["lines"]:
            if line["start_period"] == 0:
                continue
            if line["category"] in {
                "residual_value",
                "decommissioning_cost",
                "working_capital_recovery",
            }:
                continue
            line["start_period"] = max(0, line["start_period"] + shift)
            if line.get("end_period") is not None:
                line["end_period"] = min(
                    payload["analysis_horizon_periods"],
                    max(line["start_period"], line["end_period"] + shift),
                )
            line["start_period"] = min(
                payload["analysis_horizon_periods"], line["start_period"]
            )
        return cast(
            CashFlowScenarioInput, CashFlowScenarioInput.model_validate(payload)
        )

    matched = False
    for line in payload["lines"]:
        if len(parts) == 3 and parts[0] == "line" and line["flow_id"] == parts[1]:
            field = parts[2]
            if field not in {
                "amount",
                "escalation_rate_percent_annual",
                "start_period",
                "end_period",
                "interval_periods",
            }:
                raise ValueError(f"unsupported line sensitivity field: {field}")
            line[field] = (
                int(value)
                if field in {"start_period", "end_period", "interval_periods"}
                else (
                    float(line[field]) * value
                    if parameter.operation == "multiply"
                    else float(value)
                )
            )
            matched = True
        elif (
            len(parts) == 3 and parts[0] == "category" and line["category"] == parts[1]
        ):
            field = parts[2]
            if field != "amount":
                raise ValueError(f"unsupported category sensitivity field: {field}")
            line[field] = (
                float(line[field]) * value
                if parameter.operation == "multiply"
                else float(value)
            )
            matched = True
    if not matched:
        raise ValueError(
            f"sensitivity path did not match the scenario: {parameter.path}"
        )
    return cast(CashFlowScenarioInput, CashFlowScenarioInput.model_validate(payload))


def _evaluate_parameter(
    scenario: CashFlowScenarioInput,
    parameter: SensitivityParameter,
    value: float,
    metric_id: MetricId,
) -> float | None:
    adjusted = _apply_parameter(scenario, parameter, value)
    return _metric(evaluate_cash_flow(adjusted), metric_id)


def _rank_values(
    values: list[tuple[str, float | None]], objective: MetricObjective
) -> dict[str, int | None]:
    valid = [(item_id, value) for item_id, value in values if value is not None]
    valid.sort(key=lambda item: item[1], reverse=objective == "maximize")
    ranks: dict[str, int | None] = {item_id: None for item_id, _ in values}
    previous_value: float | None = None
    previous_rank = 0
    for index, (item_id, value) in enumerate(valid, start=1):
        numeric = value
        rank = previous_rank if previous_value == numeric else index
        ranks[item_id] = rank
        previous_value = numeric
        previous_rank = rank
    return ranks


def _normalized_scores(
    evaluations: list[AlternativeEvaluation],
    definition: ComparisonDefinition,
) -> dict[str, float]:
    totals = {item.alternative_id: 0.0 for item in evaluations}
    weights = {item.alternative_id: 0.0 for item in evaluations}
    for selection in definition.selected_metrics:
        pairs = [
            (item.alternative_id, item.metrics.get(selection.metric_id))
            for item in evaluations
        ]
        valid_values = [value for _, value in pairs if value is not None]
        if not valid_values:
            continue
        low = min(valid_values)
        high = max(valid_values)
        for alternative_id, value in pairs:
            if value is None:
                continue
            if abs(high - low) < 1e-12:
                normalized = 1.0
            elif selection.objective == "maximize":
                normalized = (value - low) / (high - low)
            else:
                normalized = (high - value) / (high - low)
            totals[alternative_id] += normalized * selection.weight
            weights[alternative_id] += selection.weight
    return {
        item_id: round_half_up(
            0.0 if weights[item_id] == 0 else totals[item_id] / weights[item_id] * 100,
            4,
        )
        for item_id in totals
    }


def _dominance(
    left: AlternativeEvaluation,
    right: AlternativeEvaluation,
    definition: ComparisonDefinition,
) -> bool:
    no_worse = True
    strictly_better = False
    for selection in definition.selected_metrics:
        left_value = left.metrics.get(selection.metric_id)
        right_value = right.metrics.get(selection.metric_id)
        if left_value is None or right_value is None:
            return False
        if selection.objective == "maximize":
            no_worse = no_worse and left_value >= right_value
            strictly_better = strictly_better or left_value > right_value
        else:
            no_worse = no_worse and left_value <= right_value
            strictly_better = strictly_better or left_value < right_value
    return no_worse and strictly_better


def _aligned_metrics(
    evaluations: list[AlternativeEvaluation], definition: ComparisonDefinition
) -> list[AlignedMetricComparison]:
    baseline = next(
        item
        for item in evaluations
        if item.alternative_id == definition.baseline_alternative_id
    )
    rows: list[AlignedMetricComparison] = []
    for selection in definition.selected_metrics:
        values = [
            (item.alternative_id, item.metrics.get(selection.metric_id))
            for item in evaluations
        ]
        ranks = _rank_values(values, selection.objective)
        baseline_value = baseline.metrics.get(selection.metric_id)
        rows.append(
            AlignedMetricComparison(
                metric_id=selection.metric_id,
                label=METRIC_LABELS[selection.metric_id],
                objective=selection.objective,
                baseline_value=baseline_value,
                values=[
                    AlternativeMetricValue(
                        alternative_id=item.alternative_id,
                        label=item.label,
                        value=item.metrics.get(selection.metric_id),
                        delta_from_baseline=(
                            None
                            if baseline_value is None
                            or item.metrics.get(selection.metric_id) is None
                            else round_half_up(
                                cast(float, item.metrics[selection.metric_id])
                                - baseline_value,
                                4,
                            )
                        ),
                        rank=ranks[item.alternative_id],
                    )
                    for item in evaluations
                ],
            )
        )
    return rows


def _rankings(
    evaluations: list[AlternativeEvaluation], definition: ComparisonDefinition
) -> list[AlternativeRanking]:
    scores = _normalized_scores(evaluations, definition)
    ordered = sorted(
        evaluations,
        key=lambda item: (
            -scores[item.alternative_id],
            item.label,
            item.alternative_id,
        ),
    )
    result: list[AlternativeRanking] = []
    for rank, item in enumerate(ordered, start=1):
        dominates = sorted(
            other.alternative_id
            for other in evaluations
            if other.alternative_id != item.alternative_id
            and _dominance(item, other, definition)
        )
        dominated_by = sorted(
            other.alternative_id
            for other in evaluations
            if other.alternative_id != item.alternative_id
            and _dominance(other, item, definition)
        )
        result.append(
            AlternativeRanking(
                alternative_id=item.alternative_id,
                label=item.label,
                rank=rank,
                weighted_score=scores[item.alternative_id],
                dominates=dominates,
                dominated_by=dominated_by,
            )
        )
    return result


def _one_way(
    item: OneWaySensitivityDefinition,
    alternative_scenario: CashFlowScenarioInput,
    baseline_scenario: CashFlowScenarioInput,
) -> OneWaySensitivityResult:
    base_metric = _metric(evaluate_cash_flow(alternative_scenario), item.metric_id)
    points: list[SensitivityPoint] = []
    for value in item.values:
        metric_value = _evaluate_parameter(
            alternative_scenario, item.parameter, value, item.metric_id
        )
        baseline_metric = _evaluate_parameter(
            baseline_scenario, item.parameter, value, item.metric_id
        )
        points.append(
            SensitivityPoint(
                parameter_value=value,
                metric_value=metric_value,
                baseline_metric_value=baseline_metric,
                delta_from_baseline=(
                    None
                    if metric_value is None or baseline_metric is None
                    else round_half_up(metric_value - baseline_metric, 4)
                ),
            )
        )
    key = _canonical_key(
        {
            "definition": item.model_dump(mode="json"),
            "alternative": alternative_scenario.model_dump(mode="json"),
            "baseline": baseline_scenario.model_dump(mode="json"),
        }
    )
    return OneWaySensitivityResult(
        sensitivity_id=item.sensitivity_id,
        alternative_id=item.alternative_id,
        metric_id=item.metric_id,
        parameter=item.parameter,
        base_parameter_value=_parameter_value(alternative_scenario, item.parameter),
        base_metric_value=base_metric,
        points=points,
        reproducibility_key=key,
    )


def _two_way(
    item: TwoWaySensitivityDefinition,
    scenario: CashFlowScenarioInput,
) -> TwoWaySensitivityResult:
    cells: list[TwoWaySensitivityCell] = []
    for row_value in item.row_values:
        row_scenario = _apply_parameter(scenario, item.row_parameter, row_value)
        for column_value in item.column_values:
            adjusted = _apply_parameter(
                row_scenario, item.column_parameter, column_value
            )
            cells.append(
                TwoWaySensitivityCell(
                    row_value=row_value,
                    column_value=column_value,
                    metric_value=_metric(evaluate_cash_flow(adjusted), item.metric_id),
                )
            )
    return TwoWaySensitivityResult(
        sensitivity_id=item.sensitivity_id,
        alternative_id=item.alternative_id,
        metric_id=item.metric_id,
        row_parameter=item.row_parameter,
        column_parameter=item.column_parameter,
        cells=cells,
        reproducibility_key=_canonical_key(
            {
                "definition": item.model_dump(mode="json"),
                "scenario": scenario.model_dump(mode="json"),
            }
        ),
    )


def _break_even(
    item: BreakEvenDefinition,
    scenario: CashFlowScenarioInput,
) -> BreakEvenResult:
    key = _canonical_key(
        {
            "definition": item.model_dump(mode="json"),
            "scenario": scenario.model_dump(mode="json"),
        }
    )
    notes: list[str] = []
    base_parameter = _parameter_value(scenario, item.parameter)
    try:
        base_metric = _metric(evaluate_cash_flow(scenario), item.metric_id)
        if (
            base_metric is not None
            and abs(base_metric - item.target_value) <= item.tolerance
        ):
            return BreakEvenResult(
                threshold_id=item.threshold_id,
                alternative_id=item.alternative_id,
                metric_id=item.metric_id,
                parameter=item.parameter,
                target_value=item.target_value,
                status="already_at_target",
                threshold_value=base_parameter,
                metric_value=base_metric,
                crossings=[],
                iterations=0,
                reproducibility_key=key,
                notes=["The source scenario already meets the requested target."],
            )

        if item.parameter.value_kind == "integer":
            start = ceil(item.lower_bound)
            stop = floor(item.upper_bound)
            if stop - start > 2000:
                raise ValueError("integer threshold range exceeds 2,001 evaluations")
            sample_values = [float(value) for value in range(start, stop + 1)]
        else:
            width = item.upper_bound - item.lower_bound
            sample_values = [
                item.lower_bound + width * index / 100 for index in range(101)
            ]
        evaluated: list[tuple[float, float]] = []
        iterations = 0
        for value in sample_values:
            metric = _evaluate_parameter(
                scenario, item.parameter, value, item.metric_id
            )
            iterations += 1
            if metric is not None:
                evaluated.append((value, metric - item.target_value))
        crossings: list[BreakEvenCrossing] = []
        for (left_value, left_delta), (right_value, right_delta) in zip(
            evaluated, evaluated[1:], strict=False
        ):
            if abs(left_delta) <= item.tolerance:
                crossings.append(
                    BreakEvenCrossing(
                        lower_value=left_value,
                        upper_value=left_value,
                        threshold_value=left_value,
                        metric_value=left_delta + item.target_value,
                    )
                )
                continue
            if (left_delta < 0) == (right_delta < 0):
                continue
            chosen_metric: float | None
            if item.parameter.value_kind == "integer":
                chosen = (
                    left_value if abs(left_delta) <= abs(right_delta) else right_value
                )
                chosen_metric = _evaluate_parameter(
                    scenario, item.parameter, chosen, item.metric_id
                )
            else:
                left = left_value
                right = right_value
                chosen = (left + right) / 2
                chosen_metric = None
                for _ in range(item.max_iterations):
                    chosen = (left + right) / 2
                    chosen_metric = _evaluate_parameter(
                        scenario, item.parameter, chosen, item.metric_id
                    )
                    iterations += 1
                    if chosen_metric is None:
                        break
                    delta = chosen_metric - item.target_value
                    if abs(delta) <= item.tolerance:
                        break
                    if (left_delta < 0) == (delta < 0):
                        left = chosen
                        left_delta = delta
                    else:
                        right = chosen
            crossings.append(
                BreakEvenCrossing(
                    lower_value=left_value,
                    upper_value=right_value,
                    threshold_value=round_half_up(chosen, 6),
                    metric_value=(
                        None
                        if chosen_metric is None
                        else round_half_up(chosen_metric, 6)
                    ),
                )
            )
        unique: list[BreakEvenCrossing] = []
        for crossing in crossings:
            if not any(
                abs(crossing.threshold_value - existing.threshold_value) < 1e-5
                for existing in unique
            ):
                unique.append(crossing)
        if not unique:
            return BreakEvenResult(
                threshold_id=item.threshold_id,
                alternative_id=item.alternative_id,
                metric_id=item.metric_id,
                parameter=item.parameter,
                target_value=item.target_value,
                status="no_crossing",
                threshold_value=None,
                metric_value=None,
                crossings=[],
                iterations=iterations,
                reproducibility_key=key,
                notes=["No target crossing was found inside the declared bounds."],
            )
        if len(unique) > 1:
            notes.append(
                "Multiple target crossings were detected; the nearest source value is selected."
            )
        reference = base_parameter if base_parameter is not None else item.lower_bound
        selected = min(
            unique, key=lambda crossing: abs(crossing.threshold_value - reference)
        )
        return BreakEvenResult(
            threshold_id=item.threshold_id,
            alternative_id=item.alternative_id,
            metric_id=item.metric_id,
            parameter=item.parameter,
            target_value=item.target_value,
            status="found",
            threshold_value=selected.threshold_value,
            metric_value=selected.metric_value,
            crossings=unique,
            iterations=iterations,
            reproducibility_key=key,
            notes=notes,
        )
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        return BreakEvenResult(
            threshold_id=item.threshold_id,
            alternative_id=item.alternative_id,
            metric_id=item.metric_id,
            parameter=item.parameter,
            target_value=item.target_value,
            status="invalid_parameter",
            threshold_value=None,
            metric_value=None,
            crossings=[],
            iterations=0,
            reproducibility_key=key,
            notes=[str(exc)],
        )


def _tornado(results: list[OneWaySensitivityResult]) -> list[TornadoBar]:
    bars: list[TornadoBar] = []
    for result in results:
        if len(result.points) < 2 or result.base_metric_value is None:
            continue
        low = min(result.points, key=lambda point: point.parameter_value)
        high = max(result.points, key=lambda point: point.parameter_value)
        low_impact = (
            None
            if low.metric_value is None
            else round_half_up(low.metric_value - result.base_metric_value, 4)
        )
        high_impact = (
            None
            if high.metric_value is None
            else round_half_up(high.metric_value - result.base_metric_value, 4)
        )
        bars.append(
            TornadoBar(
                sensitivity_id=result.sensitivity_id,
                alternative_id=result.alternative_id,
                parameter_id=result.parameter.parameter_id,
                label=result.parameter.label,
                low_value=low.parameter_value,
                high_value=high.parameter_value,
                low_impact=low_impact,
                high_impact=high_impact,
                absolute_swing=(
                    None
                    if low_impact is None or high_impact is None
                    else round_half_up(abs(high_impact - low_impact), 4)
                ),
            )
        )
    return sorted(
        bars,
        key=lambda item: (
            -(item.absolute_swing or 0),
            item.label,
            item.sensitivity_id,
        ),
    )


def _crossovers(
    results: list[OneWaySensitivityResult], baseline_id: str
) -> list[CrossoverPoint]:
    output: list[CrossoverPoint] = []
    for result in results:
        if result.alternative_id == baseline_id:
            continue
        points = sorted(result.points, key=lambda item: item.parameter_value)
        for left, right in zip(points, points[1:], strict=False):
            if left.delta_from_baseline is None or right.delta_from_baseline is None:
                continue
            if abs(left.delta_from_baseline) < 1e-10:
                value = left.parameter_value
                metric = cast(float, left.metric_value)
            elif (left.delta_from_baseline < 0) == (right.delta_from_baseline < 0):
                continue
            else:
                span = right.parameter_value - left.parameter_value
                fraction = -left.delta_from_baseline / (
                    right.delta_from_baseline - left.delta_from_baseline
                )
                value = left.parameter_value + span * fraction
                left_metric = cast(float, left.metric_value)
                right_metric = cast(float, right.metric_value)
                metric = left_metric + (right_metric - left_metric) * fraction
            output.append(
                CrossoverPoint(
                    sensitivity_id=result.sensitivity_id,
                    alternative_id=result.alternative_id,
                    baseline_alternative_id=baseline_id,
                    parameter_id=result.parameter.parameter_id,
                    parameter_value=round_half_up(value, 6),
                    metric_id=result.metric_id,
                    metric_value=round_half_up(metric, 4),
                )
            )
            break
    return output


def _mutated_npv(
    baseline: CashFlowScenarioInput, mutate: Callable[[dict[str, Any]], None]
) -> float | None:
    payload = baseline.model_dump(mode="json")
    mutate(payload)
    try:
        return evaluate_cash_flow(
            CashFlowScenarioInput.model_validate(payload)
        ).metrics.npv
    except (KeyError, TypeError, ValueError):
        return None


def _difference_explanation(
    baseline: AlternativeEvaluation,
    alternative: AlternativeEvaluation,
) -> DifferenceExplanation:
    base_scenario = baseline.publication.assumptions
    alt_scenario = alternative.publication.assumptions
    base_npv = baseline.publication.metrics.npv
    alt_npv = alternative.publication.metrics.npv
    drivers: list[DriverContribution] = []

    def add_driver(
        path: str,
        label: str,
        base_value: float | int | None,
        alt_value: float | int | None,
        mutate: Callable[[dict[str, Any]], None],
    ) -> None:
        changed_npv = _mutated_npv(base_scenario, mutate)
        if changed_npv is None:
            return
        drivers.append(
            DriverContribution(
                path=path,
                label=label,
                baseline_value=base_value,
                alternative_value=alt_value,
                npv_impact=round_half_up(changed_npv - base_npv, 4),
            )
        )

    top_fields = [
        ("discount_rate_percent_annual", "Discount rate"),
        ("finance_rate_percent_annual", "Finance rate"),
        ("reinvestment_rate_percent_annual", "Reinvestment rate"),
        ("analysis_horizon_periods", "Analysis horizon"),
    ]
    for field, label in top_fields:
        base_value = getattr(base_scenario, field)
        alt_value = getattr(alt_scenario, field)
        if base_value == alt_value:
            continue

        def set_top_field(
            payload: dict[str, Any],
            field: str = field,
            alt_value: float | int = alt_value,
        ) -> None:
            payload[field] = alt_value

        add_driver(field, label, base_value, alt_value, set_top_field)

    base_lines = {line.flow_id: line for line in base_scenario.lines}
    alt_lines = {line.flow_id: line for line in alt_scenario.lines}
    for flow_id in sorted(set(base_lines) | set(alt_lines)):
        base_line = base_lines.get(flow_id)
        alt_line = alt_lines.get(flow_id)
        if base_line is None and alt_line is not None:

            def add_line(payload: dict[str, Any], alt_line: Any = alt_line) -> None:
                payload["lines"].append(alt_line.model_dump(mode="json"))

            add_driver(
                f"line:{flow_id}",
                f"Added {alt_line.label}",
                None,
                alt_line.amount,
                add_line,
            )
            continue
        if base_line is not None and alt_line is None:

            def remove_line(payload: dict[str, Any], flow_id: str = flow_id) -> None:
                payload["lines"] = [
                    line for line in payload["lines"] if line["flow_id"] != flow_id
                ]

            add_driver(
                f"line:{flow_id}",
                f"Removed {base_line.label}",
                base_line.amount,
                None,
                remove_line,
            )
            continue
        assert base_line is not None and alt_line is not None
        for field, suffix in [
            ("amount", "amount"),
            ("escalation_rate_percent_annual", "escalation"),
            ("start_period", "start period"),
            ("end_period", "end period"),
        ]:
            base_value = getattr(base_line, field)
            alt_value = getattr(alt_line, field)
            if base_value == alt_value:
                continue

            def mutate(
                payload: dict[str, Any],
                flow_id: str = flow_id,
                field: str = field,
                alt_value: float | int | None = alt_value,
            ) -> None:
                for line in payload["lines"]:
                    if line["flow_id"] == flow_id:
                        line[field] = alt_value

            add_driver(
                f"line:{flow_id}:{field}",
                f"{alt_line.label} {suffix}",
                base_value,
                alt_value,
                mutate,
            )
    drivers.sort(key=lambda item: (-abs(item.npv_impact), item.label, item.path))
    notes = [
        "Driver impacts change one assumption at a time from the baseline; they are not additive when assumptions interact."
    ]
    if base_scenario.context.period_frequency != alt_scenario.context.period_frequency:
        notes.append("The alternatives use different period frequencies.")
    return DifferenceExplanation(
        alternative_id=alternative.alternative_id,
        relative_to_alternative_id=baseline.alternative_id,
        npv_delta=round_half_up(alt_npv - base_npv, 4),
        top_drivers=drivers[:10],
        non_financial_caveats=alternative.non_financial_caveats,
        notes=notes,
    )


def evaluate_comparison(
    definition: ComparisonDefinition,
    *,
    generated_at: str | None = None,
) -> ComparisonPublication:
    evaluations: list[AlternativeEvaluation] = []
    for alternative in definition.alternatives:
        publication = evaluate_cash_flow(
            alternative.scenario, generated_at=generated_at
        )
        metrics = {
            metric_id: _metric(publication, metric_id) for metric_id in METRIC_LABELS
        }
        evaluations.append(
            AlternativeEvaluation(
                alternative_id=alternative.alternative_id,
                label=alternative.label,
                kind=alternative.kind,
                source=alternative.source,
                non_financial_caveats=alternative.non_financial_caveats,
                metrics=metrics,
                publication=publication,
            )
        )
    by_id = {item.alternative_id: item for item in definition.alternatives}
    baseline_scenario = by_id[definition.baseline_alternative_id].scenario
    one_way_results = [
        _one_way(item, by_id[item.alternative_id].scenario, baseline_scenario)
        for item in definition.one_way_sensitivities
    ]
    two_way_results = [
        _two_way(item, by_id[item.alternative_id].scenario)
        for item in definition.two_way_sensitivities
    ]
    break_even_results = [
        _break_even(item, by_id[item.alternative_id].scenario)
        for item in definition.break_even_definitions
    ]
    baseline_evaluation = next(
        item
        for item in evaluations
        if item.alternative_id == definition.baseline_alternative_id
    )
    explanations = [
        _difference_explanation(baseline_evaluation, item)
        for item in evaluations
        if item.alternative_id != definition.baseline_alternative_id
    ]
    return ComparisonPublication(
        definition=definition,
        alternatives=evaluations,
        aligned_metrics=_aligned_metrics(evaluations, definition),
        rankings=_rankings(evaluations, definition),
        difference_explanations=explanations,
        one_way_sensitivities=one_way_results,
        two_way_sensitivities=two_way_results,
        break_even_results=break_even_results,
        tornado=_tornado(one_way_results),
        crossover_points=_crossovers(
            one_way_results, definition.baseline_alternative_id
        ),
        methodology=ComparisonMethodology(),
        metadata=ComparisonMetadata(
            generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        ),
    )
