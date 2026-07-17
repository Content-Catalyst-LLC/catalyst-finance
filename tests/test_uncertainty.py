from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from catalyst_finance.uncertainty import evaluate_uncertainty
from catalyst_finance.uncertainty_models import (
    DistributionSpec,
    UncertaintyDefinition,
)

ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = "2026-07-17T00:00:00+00:00"


@pytest.fixture(scope="module")
def definition() -> UncertaintyDefinition:
    return UncertaintyDefinition.model_validate_json(
        (ROOT / "data/sample_uncertainty.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def publication(definition: UncertaintyDefinition):
    return evaluate_uncertainty(definition, generated_at=FIXED_TIME)


def test_sample_contract_validates(definition: UncertaintyDefinition) -> None:
    assert definition.contract_version == "1.6.0"
    assert len(definition.variables) == 5
    assert len(definition.stress_cases) == 3


def test_seeded_results_are_reproducible(definition: UncertaintyDefinition) -> None:
    first = evaluate_uncertainty(definition, generated_at=FIXED_TIME)
    second = evaluate_uncertainty(definition, generated_at=FIXED_TIME)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_different_seed_changes_results(definition: UncertaintyDefinition) -> None:
    changed = definition.model_copy(
        update={"monte_carlo": definition.monte_carlo.model_copy(update={"seed": 42})}
    )
    first = evaluate_uncertainty(definition, generated_at=FIXED_TIME)
    second = evaluate_uncertainty(changed, generated_at=FIXED_TIME)
    assert first.summaries[0].mean != second.summaries[0].mean


def test_summary_risk_statistics(publication) -> None:
    by_metric = {item.metric_id: item for item in publication.summaries}
    npv = by_metric["npv"]
    assert npv.sample_count == 500
    assert npv.minimum < npv.mean < npv.maximum
    assert npv.value_at_risk_95 <= npv.median
    assert npv.expected_shortfall_5 <= npv.value_at_risk_95
    assert 0 <= npv.probability_above_zero <= 1


def test_retained_samples_and_histograms(publication) -> None:
    assert len(publication.retained_samples) == 25
    npv_bins = [item for item in publication.histograms if item.metric_id == "npv"]
    assert len(npv_bins) == 12
    assert sum(item.count for item in npv_bins) == 500


def test_variable_influence_is_ranked(publication) -> None:
    npv = [item for item in publication.variable_influences if item.metric_id == "npv"]
    assert len(npv) == 5
    assert (npv[0].absolute_correlation or 0) >= (npv[-1].absolute_correlation or 0)
    assert {item.variable_id for item in npv} == {
        "capital-cost",
        "annual-savings",
        "operating-cost",
        "discount-rate",
        "implementation-delay",
    }


def test_stress_cases_report_deltas_and_flags(publication) -> None:
    assert [item.stress_id for item in publication.stress_results] == [
        "cost-overrun-delay",
        "benefit-shortfall",
        "combined-downside",
    ]
    assert all(
        item.deltas_from_base["npv"] is not None for item in publication.stress_results
    )
    assert (
        publication.stress_results[-1].metrics["npv"] < publication.base_metrics["npv"]
    )


def test_reproducibility_key_ignores_generated_timestamp(
    definition: UncertaintyDefinition,
) -> None:
    first = evaluate_uncertainty(definition, generated_at="2026-01-01T00:00:00+00:00")
    second = evaluate_uncertainty(definition, generated_at="2026-12-31T00:00:00+00:00")
    assert first.metadata.reproducibility_key == second.metadata.reproducibility_key


def test_invalid_distribution_contracts_are_rejected() -> None:
    with pytest.raises(ValidationError):
        DistributionSpec(kind="uniform", minimum=5, maximum=5)
    with pytest.raises(ValidationError):
        DistributionSpec(kind="discrete", values=[1, 2], probabilities=[0.4, 0.4])


def test_non_positive_semidefinite_correlation_is_rejected(
    definition: UncertaintyDefinition,
) -> None:
    payload = definition.model_dump(mode="json")
    payload["variables"] = payload["variables"][:3]
    payload["correlations"] = [
        {
            "left_variable_id": "capital-cost",
            "right_variable_id": "annual-savings",
            "coefficient": 0.9,
        },
        {
            "left_variable_id": "capital-cost",
            "right_variable_id": "operating-cost",
            "coefficient": 0.9,
        },
        {
            "left_variable_id": "annual-savings",
            "right_variable_id": "operating-cost",
            "coefficient": -0.9,
        },
    ]
    payload["monte_carlo"]["iterations"] = 100
    invalid = UncertaintyDefinition.model_validate(payload)
    with pytest.raises(ValueError, match="positive semidefinite"):
        evaluate_uncertainty(invalid)


def test_legacy_v14_nested_scenario_can_be_upgraded() -> None:
    payload = json.loads((ROOT / "data/sample_uncertainty.json").read_text())
    payload["scenario"]["contract_version"] = "1.4.0"
    from catalyst_finance.cashflow_migration import normalize_cash_flow

    upgraded = normalize_cash_flow(payload["scenario"])
    assert upgraded.contract_version == "1.6.0"
