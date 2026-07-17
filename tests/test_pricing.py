from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from catalyst_finance.pricing import evaluate_pricing
from catalyst_finance.pricing_migration import normalize_pricing
from catalyst_finance.pricing_models import DemandCurve, PricingDefinition

ROOT = Path(__file__).resolve().parents[1]
FIXED = "2026-07-17T00:00:00+00:00"


@pytest.fixture(scope="module")
def definition() -> PricingDefinition:
    return PricingDefinition.model_validate_json(
        (ROOT / "data/sample_pricing.json").read_text()
    )


@pytest.fixture(scope="module")
def publication(definition: PricingDefinition):
    return evaluate_pricing(definition, generated_at=FIXED)


def test_contract_and_grid(definition: PricingDefinition, publication) -> None:
    assert definition.contract_version == "1.6.0"
    assert len(definition.segments) == 3
    assert len(publication.rows) == 51
    assert publication.rows[0].price == 30
    assert publication.rows[-1].price == 80


def test_known_optima(publication) -> None:
    by_objective = {item.objective: item for item in publication.optima}
    assert by_objective["revenue"].price == 46
    assert by_objective["profit"].price == 55
    assert publication.recommendation.recommended_price == 55
    assert publication.recommendation.expected_objective_gain == pytest.approx(
        6160.820037
    )


def test_capacity_and_minimum_volume_flags(publication) -> None:
    assert publication.rows[0].capacity_constrained is True
    assert publication.rows[-1].minimum_volume_met is True
    assert any("Capacity" in item for item in publication.flags)
    assert any("endpoint-clamped" in item for item in publication.flags)


def test_segment_elasticity_methods(publication) -> None:
    row = publication.current_position
    assert row is not None
    methods = {item.segment_id: item.interpolation_policy for item in row.segments}
    assert methods == {
        "commuter": "analytical_linear",
        "hybrid": "analytical_constant_elasticity",
        "student": "interpolated",
    }
    assert {item.demand_classification for item in row.segments} <= {
        "elastic",
        "inelastic",
        "unit_elastic",
    }


def test_break_even_and_margin(publication) -> None:
    row = publication.current_position
    assert row is not None
    assert row.break_even_quantity is not None
    assert row.break_even_met is True
    assert row.contribution_margin_percent is not None
    assert 0 < row.contribution_margin_percent < 100


def test_maximum_price_change_can_bind(definition: PricingDefinition) -> None:
    changed = definition.model_copy(
        update={
            "current_price": 40,
            "constraints": definition.constraints.model_copy(
                update={"maximum_price_change_percent": 5}
            ),
        }
    )
    result = evaluate_pricing(changed, generated_at=FIXED)
    assert result.recommendation.constraint_limited is True
    assert result.recommendation.recommended_price == 42


def test_observed_contract_validation() -> None:
    with pytest.raises(ValidationError):
        DemandCurve(kind="observed", observed_points=[{"price": 10, "quantity": 10}])
    with pytest.raises(ValidationError):
        DemandCurve(
            kind="observed",
            observed_points=[
                {"price": 20, "quantity": 10},
                {"price": 10, "quantity": 20},
            ],
        )


def test_v15_pricing_definition_migration(definition: PricingDefinition) -> None:
    payload = definition.model_dump(mode="json")
    payload["contract_version"] = "1.5.0"
    upgraded = normalize_pricing(payload)
    assert upgraded.contract_version == "1.6.0"


def test_checked_in_publication_is_reproducible(publication) -> None:
    expected = json.loads((ROOT / "examples/sample_pricing.output.json").read_text())
    assert publication.model_dump(mode="json") == expected
