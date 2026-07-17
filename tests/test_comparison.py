import csv
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from catalyst_finance.comparison import _crossovers, evaluate_comparison
from catalyst_finance.comparison_cli import render_html, render_markdown, write_csv
from catalyst_finance.comparison_models import (
    ComparisonDefinition,
    OneWaySensitivityResult,
    SensitivityParameter,
    SensitivityPoint,
)

ROOT = Path(__file__).resolve().parents[1]
FIXED = "2026-07-17T00:00:00+00:00"


def load() -> ComparisonDefinition:
    return ComparisonDefinition.model_validate(
        json.loads((ROOT / "data" / "sample_comparison.json").read_text())
    )


def test_comparison_requires_at_least_three_alternatives() -> None:
    payload = load().model_dump(mode="json")
    payload["alternatives"] = payload["alternatives"][:2]
    with pytest.raises(ValidationError):
        ComparisonDefinition.model_validate(payload)


def test_comparison_aligns_metrics_and_ranks_alternatives() -> None:
    result = evaluate_comparison(load(), generated_at=FIXED)
    assert [item.alternative_id for item in result.rankings] == [
        "upside",
        "base",
        "downside",
    ]
    assert result.rankings[0].weighted_score == 100
    assert len(result.aligned_metrics) == 4
    assert all(len(row.values) == 3 for row in result.aligned_metrics)


def test_comparison_preserves_revision_traceability_and_caveats() -> None:
    result = evaluate_comparison(load())
    base = next(item for item in result.alternatives if item.alternative_id == "base")
    upside = next(
        item for item in result.alternatives if item.alternative_id == "upside"
    )
    assert base.source.revision_id == "revision_base_003"
    assert "Grant award is not yet confirmed" in upside.non_financial_caveats


def test_one_way_and_two_way_sensitivity_are_reproducible() -> None:
    first = evaluate_comparison(load(), generated_at=FIXED)
    second = evaluate_comparison(load(), generated_at=FIXED)
    assert first.one_way_sensitivities == second.one_way_sensitivities
    assert first.two_way_sensitivities == second.two_way_sensitivities
    assert len(first.one_way_sensitivities) == 5
    assert len(first.two_way_sensitivities[0].cells) == 12
    assert len(first.one_way_sensitivities[0].reproducibility_key) == 64


def test_break_even_thresholds_are_found_and_bounded() -> None:
    result = evaluate_comparison(load())
    thresholds = {item.threshold_id: item for item in result.break_even_results}
    assert thresholds["savings-break-even"].status == "found"
    assert thresholds["savings-break-even"].threshold_value == pytest.approx(
        29274.963379, abs=0.01
    )
    assert thresholds["capital-cost-threshold"].threshold_value == pytest.approx(
        500183.433533, abs=0.01
    )
    assert thresholds["delay-threshold"].threshold_value == 5


def test_tornado_is_sorted_by_absolute_swing() -> None:
    result = evaluate_comparison(load())
    swings = [item.absolute_swing or 0 for item in result.tornado]
    assert swings == sorted(swings, reverse=True)
    assert {item.parameter_id for item in result.tornado} >= {
        "annual-savings",
        "discount-rate",
        "capital-cost",
        "implementation-delay",
        "carbon-value",
    }


def test_difference_explanations_identify_material_drivers() -> None:
    result = evaluate_comparison(load())
    downside = next(
        item
        for item in result.difference_explanations
        if item.alternative_id == "downside"
    )
    paths = {item.path for item in downside.top_drivers}
    assert "line:capex:amount" in paths
    assert "line:savings:amount" in paths
    assert downside.npv_delta < 0
    assert "not additive" in downside.notes[0]


def test_dominance_is_financial_only_and_disclosed() -> None:
    result = evaluate_comparison(load())
    upside = next(item for item in result.rankings if item.alternative_id == "upside")
    assert upside.financial_only is True
    assert "downside" in upside.dominates
    assert upside.dominated_by == []


def test_crossover_interpolation_contract() -> None:
    result = OneWaySensitivityResult(
        sensitivity_id="cross",
        alternative_id="custom",
        metric_id="npv",
        parameter=SensitivityParameter(
            parameter_id="price",
            label="Price",
            path="line:revenue:amount",
            unit="USD",
        ),
        base_parameter_value=10,
        base_metric_value=0,
        points=[
            SensitivityPoint(
                parameter_value=10,
                metric_value=90,
                baseline_metric_value=100,
                delta_from_baseline=-10,
            ),
            SensitivityPoint(
                parameter_value=20,
                metric_value=120,
                baseline_metric_value=100,
                delta_from_baseline=20,
            ),
        ],
        reproducibility_key="x" * 64,
    )
    points = _crossovers([result], "base")
    assert len(points) == 1
    assert points[0].parameter_value == pytest.approx(13.333333, abs=1e-6)
    assert points[0].metric_value == 100


def test_json_markdown_csv_and_printable_html_exports(tmp_path: Path) -> None:
    result = evaluate_comparison(load(), generated_at=FIXED)
    markdown = render_markdown(result)
    html = render_html(result)
    assert "Weighted ranking" in markdown
    assert "<!doctype html>" in html
    csv_path = tmp_path / "comparison.csv"
    write_csv(result, csv_path)
    rows = list(csv.reader(csv_path.open()))
    assert rows[0][0] == "record_type"
    assert {row[0] for row in rows[1:]} >= {
        "aligned_metric",
        "ranking",
        "one_way_sensitivity",
        "break_even",
    }


def test_publication_is_byte_reproducible_with_fixed_timestamp() -> None:
    first = evaluate_comparison(load(), generated_at=FIXED).model_dump_json()
    second = evaluate_comparison(load(), generated_at=FIXED).model_dump_json()
    assert first == second
