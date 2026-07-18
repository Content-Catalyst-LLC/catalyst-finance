from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from catalyst_finance.platform import evaluate_platform
from catalyst_finance.platform_migration import normalize_platform
from catalyst_finance.platform_models import PlatformDefinition

ROOT = Path(__file__).resolve().parents[1]
FIXED = "2026-07-17T18:30:00+00:00"


def load_sample() -> dict[str, object]:
    return json.loads((ROOT / "data/sample_platform.json").read_text())


def test_connected_platform_portfolio_and_readiness() -> None:
    publication = evaluate_platform(
        PlatformDefinition.model_validate(load_sample()), generated_at=FIXED
    )
    assert publication.portfolio.artifact_count == 7
    assert publication.portfolio.case_count == 2
    assert publication.portfolio.total_adjusted_npv == pytest.approx(2_286_250.90)
    assert publication.portfolio.total_capital_required == pytest.approx(2_980_000)
    assert publication.portfolio.risk_adjusted_value == pytest.approx(1_580_250.61)
    assert publication.portfolio.value_to_capital_ratio == pytest.approx(0.7672)
    assert [item.status for item in publication.case_assessments] == [
        "decided",
        "decision_ready",
    ]
    assert publication.case_assessments[0].readiness_score == pytest.approx(99.37)
    assert publication.handoffs.completed == 5
    assert publication.handoffs.rejected == 1
    assert publication.handoffs.noncompliant_handoff_ids == ["handoff_pricing_library"]
    assert publication.dependency_order.index(
        "artifact_market"
    ) < publication.dependency_order.index("artifact_cashflow")
    assert publication.run_record.input_hash
    assert publication.run_record.output_hash


def test_platform_is_reproducible_for_fixed_timestamp() -> None:
    definition = PlatformDefinition.model_validate(load_sample())
    first = evaluate_platform(definition, generated_at=FIXED)
    second = evaluate_platform(definition, generated_at=FIXED)
    assert first == second


def test_platform_migrates_v190_definition() -> None:
    payload = json.loads((ROOT / "data/legacy_v1.9.0_platform.json").read_text())
    definition = normalize_platform(payload)
    assert definition.contract_version == "2.0.0"
    assert all(
        artifact.model_version == "2.0.0"
        for artifact in definition.artifacts
        if artifact.source_product_id == "catalyst-finance"
    )


def test_platform_rejects_dependency_cycle() -> None:
    payload = load_sample()
    dependencies = payload["dependencies"]
    assert isinstance(dependencies, list)
    dependencies.append(
        {
            "edge_id": "edge_cycle",
            "upstream_artifact_id": "artifact_governance",
            "downstream_artifact_id": "artifact_market",
            "relationship": "depends_on",
            "required": True,
            "note": "Invalid cycle",
        }
    )
    with pytest.raises(ValidationError, match="acyclic"):
        PlatformDefinition.model_validate(payload)


def test_completed_handoff_requires_target_classification() -> None:
    payload = load_sample()
    handoffs = payload["handoffs"]
    assert isinstance(handoffs, list)
    handoffs[-1]["status"] = "completed"
    with pytest.raises(ValidationError, match="classification is not accepted"):
        PlatformDefinition.model_validate(payload)


def test_derived_artifacts_are_not_double_counted() -> None:
    payload = load_sample()
    artifacts = payload["artifacts"]
    assert isinstance(artifacts, list)
    comparison = next(
        item for item in artifacts if item["artifact_id"] == "artifact_comparison"
    )
    comparison["financial"]["adjusted_npv"] = 99_000_000
    definition = PlatformDefinition.model_validate(payload)
    publication = evaluate_platform(definition, generated_at=FIXED)
    assert publication.portfolio.total_adjusted_npv == pytest.approx(2_286_250.90)
