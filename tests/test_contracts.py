import pytest
from pydantic import ValidationError

from catalyst_finance.models import FinanceScenarioInput, validation_issues


def base_payload() -> dict[str, object]:
    return {
        "contract_version": "1.3.0",
        "model_id": "catalyst-finance.screening",
        "project": {"name": "Test", "category": "Test"},
        "context": {
            "currency": "USD",
            "price_basis": "nominal",
            "discount_rate_basis": "nominal",
            "period_frequency": "annual",
            "time_basis": "end_of_period",
            "rounding_policy": "half_up",
            "monetary_decimals": 2,
            "ratio_decimals": 2,
            "score_decimals": 1,
        },
        "assumptions": {
            "capital_cost": 100,
            "external_funding": 0,
            "annual_savings": 30,
            "annual_operating_cost": 0,
            "time_horizon_years": 5,
            "discount_rate_percent": 5,
            "annual_emissions_reduced_tons": 0,
            "carbon_price_per_ton": 0,
            "confidence_percent": 75,
            "implementation_risk_percent": 25,
        },
    }


def test_extra_fields_are_rejected() -> None:
    payload = base_payload()
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        FinanceScenarioInput.model_validate(payload)


def test_basis_mismatch_is_rejected_with_structured_issue() -> None:
    payload = base_payload()
    context = payload["context"]
    assert isinstance(context, dict)
    context["discount_rate_basis"] = "real"
    with pytest.raises(ValidationError) as error:
        FinanceScenarioInput.model_validate(payload)
    issues = validation_issues(error.value)
    assert issues[0]["path"] == ["context"]
    assert "must match" in issues[0]["message"]


def test_missing_emissions_requires_zero_carbon_price() -> None:
    payload = base_payload()
    assumptions = payload["assumptions"]
    assert isinstance(assumptions, dict)
    assumptions["annual_emissions_reduced_tons"] = None
    assumptions["carbon_price_per_ton"] = 10
    with pytest.raises(ValidationError):
        FinanceScenarioInput.model_validate(payload)


def test_v110_contract_migrates_without_value_loss() -> None:
    from catalyst_finance.migration import normalize_scenario

    payload = base_payload()
    payload["contract_version"] = "1.1.0"
    scenario, migration = normalize_scenario(payload)
    assert scenario.contract_version == "1.3.0"
    assert scenario.project.model_dump() == payload["project"]
    assert scenario.context.model_dump() == payload["context"]
    assert scenario.assumptions.model_dump() == payload["assumptions"]
    assert migration is not None
    assert migration.source_contract_version == "1.1.0"
    assert len(migration.preserved_fields) == 22
