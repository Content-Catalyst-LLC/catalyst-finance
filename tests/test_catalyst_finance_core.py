from catalyst_finance.domain import (
    FinanceInputs,
    FinanceProject,
    evaluate,
    present_value_annuity,
)
from catalyst_finance.version import __version__


def test_present_value_annuity_positive() -> None:
    value = present_value_annuity(1000, 3, 5)
    assert 2700 < value < 2800


def test_present_value_annuity_zero_rate() -> None:
    assert present_value_annuity(1000, 3, 0) == 3000


def test_evaluate_positive_case_has_expected_fields() -> None:
    payload = evaluate(
        FinanceProject(name="Efficiency retrofit", category="Energy"),
        FinanceInputs(
            capital_cost=100000,
            external_funding=10000,
            annual_savings=25000,
            annual_operating_cost=2000,
            time_horizon_years=8,
            discount_rate_percent=6,
            annual_emissions_reduced_tons=60,
            carbon_price_per_ton=25,
            confidence_percent=75,
            implementation_risk_percent=30,
        ),
        generated_at="2026-07-17T00:00:00+00:00",
    )
    assert payload["results"]["net_capital_cost"] == 90000
    assert payload["results"]["net_annual_benefit"] == 24500
    assert "risk_adjusted_score" in payload["results"]
    assert payload["interpretation"]["risk_level"] in {
        "Lower concern",
        "Moderate concern",
        "High concern",
    }
    assert payload["metadata"]["version"] == __version__


def test_evaluate_flags_negative_case() -> None:
    payload = evaluate(
        FinanceProject(name="Weak case"),
        FinanceInputs(
            capital_cost=100000,
            external_funding=0,
            annual_savings=1000,
            annual_operating_cost=5000,
            time_horizon_years=5,
            discount_rate_percent=6,
            annual_emissions_reduced_tons=0,
            carbon_price_per_ton=0,
            confidence_percent=40,
            implementation_risk_percent=80,
        ),
    )
    flags = payload["interpretation"]["flags"]
    assert any("Negative NPV" in flag for flag in flags)
    assert any("confidence" in flag.lower() for flag in flags)
