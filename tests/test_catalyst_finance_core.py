from catalyst_finance.calculation import present_value_annuity, round_half_up
from catalyst_finance.domain import FinanceInputs, FinanceProject, evaluate
from catalyst_finance.engine import evaluate_payload, evaluate_scenario
from catalyst_finance.models import FinanceScenarioInput
from catalyst_finance.version import __version__


def canonical(**overrides: object) -> FinanceScenarioInput:
    assumptions: dict[str, object] = {
        "capital_cost": 100000,
        "external_funding": 10000,
        "annual_savings": 25000,
        "annual_operating_cost": 2000,
        "time_horizon_years": 8,
        "discount_rate_percent": 6,
        "annual_emissions_reduced_tons": 60,
        "carbon_price_per_ton": 25,
        "confidence_percent": 75,
        "implementation_risk_percent": 30,
    }
    assumptions.update(overrides)
    return FinanceScenarioInput.model_validate(
        {
            "contract_version": "1.5.0",
            "model_id": "catalyst-finance.screening",
            "project": {"name": "Efficiency retrofit", "category": "Energy"},
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
            "assumptions": assumptions,
        }
    )


def test_present_value_annuity_positive() -> None:
    value = present_value_annuity(1000, 3, 5)
    assert 2700 < value < 2800


def test_fractional_horizon_is_prorated() -> None:
    full = present_value_annuity(1000, 2, 0)
    fractional = present_value_annuity(1000, 2.5, 0)
    assert full == 2000
    assert fractional == 2500


def test_half_up_rounding_is_explicit() -> None:
    assert round_half_up(1.005, 2) == 1.01
    assert round_half_up(-1.005, 2) == -1.01


def test_evaluate_positive_case_has_contract_and_trace() -> None:
    publication = evaluate_scenario(
        canonical(), generated_at="2026-07-17T00:00:00+00:00"
    )
    payload = publication.model_dump(mode="json")
    assert payload["contract_version"] == "1.5.0"
    assert payload["model_id"] == "catalyst-finance.screening"
    assert payload["results"]["net_capital_cost"] == 90000
    assert payload["results"]["net_annual_benefit"] == 24500
    assert len(payload["results"]["score_components"]) == 4
    assert payload["metadata"]["version"] == __version__
    assert payload["methodology"]["score_policy"] == "transparent_weighted_components"


def test_score_equals_disclosed_weighted_components() -> None:
    payload = evaluate_scenario(canonical()).model_dump(mode="json")
    expected = sum(
        component["raw_score"] * component["weight"]
        for component in payload["results"]["score_components"]
    )
    assert payload["results"]["risk_adjusted_score"] == round_half_up(expected, 1)


def test_negative_case_flags_are_separate_from_narrative() -> None:
    payload = evaluate_scenario(
        canonical(
            annual_savings=1000,
            annual_operating_cost=5000,
            annual_emissions_reduced_tons=0,
            carbon_price_per_ton=0,
            confidence_percent=40,
            implementation_risk_percent=80,
        )
    ).model_dump(mode="json")
    flags = payload["interpretation"]["flags"]
    assert any("Negative NPV" in flag for flag in flags)
    assert any("confidence" in flag.lower() for flag in flags)
    assert "decision_note" not in payload["interpretation"]
    assert payload["narrative"]["decision_note"]


def test_overfunding_and_zero_cost_ratios_have_defined_policy() -> None:
    payload = evaluate_scenario(
        canonical(capital_cost=10000, external_funding=15000)
    ).model_dump(mode="json")
    assert payload["results"]["net_capital_cost"] == 0
    assert payload["results"]["payback_years"] == 0
    assert payload["results"]["roi_percent"] is None
    assert payload["results"]["benefit_cost_ratio"] is None
    assert any("floored at zero" in flag for flag in payload["interpretation"]["flags"])


def test_missing_emissions_excludes_carbon_value() -> None:
    payload = evaluate_scenario(
        canonical(annual_emissions_reduced_tons=None, carbon_price_per_ton=0)
    ).model_dump(mode="json")
    assert payload["results"]["carbon_value_per_year"] == 0
    assert payload["results"]["carbon_cost_per_ton"] is None
    assert any(
        "Emissions data not provided" in flag
        for flag in payload["interpretation"]["flags"]
    )


def test_negative_discount_rate_is_supported_and_flagged() -> None:
    payload = evaluate_scenario(canonical(discount_rate_percent=-2)).model_dump(
        mode="json"
    )
    assert payload["results"]["present_value_benefits"] > 0
    assert any(
        "Negative discount rate" in flag for flag in payload["interpretation"]["flags"]
    )


def test_backward_compatible_domain_evaluate() -> None:
    payload = evaluate(
        FinanceProject(name="Compatibility"),
        FinanceInputs(
            capital_cost=100,
            external_funding=0,
            annual_savings=30,
            annual_operating_cost=0,
            time_horizon_years=5,
            discount_rate_percent=5,
            annual_emissions_reduced_tons=0,
            carbon_price_per_ton=0,
            confidence_percent=75,
            implementation_risk_percent=25,
        ),
    )
    assert payload["metadata"]["version"] == "1.5.0"


def test_evaluate_payload_migrates_v100_without_losing_values() -> None:
    legacy = {
        "project": {"name": "Legacy", "category": "Energy"},
        "inputs": canonical().assumptions.model_dump(mode="json"),
    }
    payload = evaluate_payload(
        legacy, generated_at="2026-07-17T00:00:00+00:00"
    ).model_dump(mode="json")
    assert payload["assumptions"] == legacy["inputs"]
    assert payload["metadata"]["migration"]["source_contract_version"] == "1.0.0"
    assert len(payload["metadata"]["migration"]["preserved_fields"]) == 12
