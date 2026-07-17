import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from catalyst_finance.cashflow import (
    effective_period_rate,
    evaluate_cash_flow,
    expand_cash_flows,
)
from catalyst_finance.cashflow_models import CashFlowScenarioInput

ROOT = Path(__file__).resolve().parents[1]
FIXED = "2026-07-17T00:00:00+00:00"


def load(name: str) -> CashFlowScenarioInput:
    raw = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
    return CashFlowScenarioInput.model_validate(raw)


def test_conventional_cash_flow_reconciles_periods_and_aggregate() -> None:
    publication = evaluate_cash_flow(
        load("sample_cash_flow_scenario.json"), generated_at=FIXED
    )
    assert len(publication.periods) == 11
    assert sum(row.net_cash_flow for row in publication.periods) == pytest.approx(
        publication.metrics.net_cash_flow, abs=0.02
    )
    assert sum(
        row.discounted_net_cash_flow for row in publication.periods
    ) == pytest.approx(publication.metrics.npv, abs=0.03)
    assert (
        publication.periods[-1].cumulative_cash_flow
        == publication.metrics.net_cash_flow
    )
    assert publication.metrics.npv == 198884.69


def test_conventional_metrics_and_terminal_value() -> None:
    metrics = evaluate_cash_flow(load("sample_cash_flow_scenario.json")).metrics
    assert metrics.simple_payback_periods == 4.2681
    assert metrics.discounted_payback_periods == 5.0483
    assert metrics.irr_status == "unique"
    assert metrics.irr_percent_annual == 20.9047
    assert metrics.mirr_percent_annual == 11.481
    assert metrics.terminal_value == 30000


def test_escalation_expands_recurring_lines() -> None:
    scenario = load("sample_cash_flow_scenario.json")
    rows = expand_cash_flows(scenario)
    year_one = next(item for item in rows[1] if item.flow_id == "savings")
    year_ten = next(item for item in rows[10] if item.flow_id == "savings")
    assert year_one.amount == pytest.approx(61200)
    assert year_ten.amount == pytest.approx(73139.665)


def test_irregular_quarterly_cash_flows_are_supported() -> None:
    publication = evaluate_cash_flow(load("irregular_cash_flow_scenario.json"))
    assert len(publication.periods) == 13
    assert publication.periods[2].outflows == 43500
    assert publication.periods[3].inflows == 10000
    assert publication.periods[12].net_cash_flow == 58500
    assert publication.metrics.net_cash_flow == 5000


def test_monthly_effective_rate_reconciles_to_annual_rate() -> None:
    monthly = effective_period_rate(12, "monthly")
    assert ((1 + monthly) ** 12) - 1 == pytest.approx(0.12)


def test_negative_case_has_no_payback_and_negative_npv() -> None:
    publication = evaluate_cash_flow(load("negative_cash_flow_scenario.json"))
    assert publication.metrics.npv < 0
    assert publication.metrics.simple_payback_periods is None
    assert publication.metrics.discounted_payback_periods is None
    assert any("not achieved" in flag for flag in publication.interpretation.flags)


def test_zero_cost_case_has_defined_undefined_ratios() -> None:
    publication = evaluate_cash_flow(load("zero_cost_cash_flow_scenario.json"))
    assert publication.metrics.npv > 0
    assert publication.metrics.simple_payback_periods == 0
    assert publication.metrics.irr_status == "not_applicable"
    assert publication.metrics.irr_percent_annual is None
    assert publication.metrics.profitability_index is None
    assert publication.metrics.benefit_cost_ratio is None


def test_multiple_sign_changes_report_all_roots_and_suppress_single_irr() -> None:
    publication = evaluate_cash_flow(load("multiple_sign_cash_flow_scenario.json"))
    assert publication.metrics.sign_changes == 2
    assert publication.metrics.irr_status == "ambiguous_multiple_sign_changes"
    assert publication.metrics.irr_percent_annual is None
    assert publication.metrics.irr_roots_percent_annual == [10.0, 20.0]
    assert any("ambiguous" in flag for flag in publication.interpretation.flags)


def test_basis_mismatch_is_detected() -> None:
    payload = json.loads((ROOT / "data" / "sample_cash_flow_scenario.json").read_text())
    payload["context"]["discount_rate_basis"] = "real"
    with pytest.raises(ValidationError, match="must match"):
        CashFlowScenarioInput.model_validate(payload)


def test_line_basis_mismatch_is_detected() -> None:
    payload = json.loads((ROOT / "data" / "sample_cash_flow_scenario.json").read_text())
    payload["lines"][0]["price_basis"] = "real"
    with pytest.raises(ValidationError, match="price_basis must match context"):
        CashFlowScenarioInput.model_validate(payload)


def test_line_outside_horizon_is_rejected() -> None:
    payload = json.loads((ROOT / "data" / "sample_cash_flow_scenario.json").read_text())
    payload["lines"][0]["start_period"] = 11
    with pytest.raises(ValidationError, match="exceeds the analysis horizon"):
        CashFlowScenarioInput.model_validate(payload)


def test_metric_trace_discloses_included_and_excluded_categories() -> None:
    metrics = evaluate_cash_flow(load("sample_cash_flow_scenario.json")).metrics
    trace = {item.metric_id: item for item in metrics.metric_trace}
    assert set(trace) >= {
        "npv",
        "simple_payback",
        "discounted_payback",
        "irr",
        "mirr",
        "profitability_index",
        "benefit_cost_ratio",
        "equivalent_annual_value",
        "terminal_value",
    }
    assert trace["npv"].excluded_categories == []
    assert set(trace["benefit_cost_ratio"].excluded_categories) >= {"grant", "rebate"}
    assert trace["terminal_value"].included_flow_ids == [
        "residual",
        "working-capital-recovery",
        "decommission",
    ]


def test_working_capital_without_recovery_is_flagged() -> None:
    scenario = load("sample_cash_flow_scenario.json")
    lines = [
        line for line in scenario.lines if line.category != "working_capital_recovery"
    ]
    publication = evaluate_cash_flow(scenario.model_copy(update={"lines": lines}))
    assert any(
        "without an explicit recovery" in flag
        for flag in publication.interpretation.flags
    )
