from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from catalyst_finance.sustainable import evaluate_sustainable
from catalyst_finance.sustainable_migration import normalize_sustainable
from catalyst_finance.sustainable_models import SustainableDefinition

ROOT = Path(__file__).resolve().parents[1]
FIXED = "2026-07-17T00:00:00+00:00"


def sample() -> SustainableDefinition:
    return SustainableDefinition.model_validate(
        json.loads((ROOT / "data/sample_sustainable.json").read_text())
    )


def test_sustainable_value_reconciles_without_carbon_double_counting() -> None:
    p = evaluate_sustainable(sample(), generated_at=FIXED)
    assert p.carbon.avoided_emissions_tco2e == 4500.0
    assert p.carbon.shadow_carbon_value == 382500.0
    assert p.carbon.net_market_credit_value == 137232.0
    assert p.summary.carbon_value == 382500.0
    assert p.summary.total_sustainable_value == 1401250.9
    assert p.summary.adjusted_project_npv == 1526250.9


def test_natural_capital_and_transition_components() -> None:
    p = evaluate_sustainable(sample(), generated_at=FIXED)
    assert len(p.natural_capital_assets) == 2
    assert p.summary.natural_capital_value == 731295.32
    assert p.summary.transition_benefit_present_value == 245198.25
    assert p.summary.transition_cost_present_value == 85714.29
    assert p.summary.green_financing_savings_present_value == 127971.61


def test_credit_quantity_is_capped_at_avoided_emissions() -> None:
    d = sample().model_copy(
        update={
            "carbon_credit_quantity_tco2e": 9000,
            "carbon_valuation_method": "market_credit",
        }
    )
    p = evaluate_sustainable(d, generated_at=FIXED)
    assert p.carbon.eligible_credit_quantity_tco2e == 4500.0
    assert any("capped" in flag for flag in p.flags)


def test_invalid_green_rate_and_duplicate_assets_are_rejected() -> None:
    payload = json.loads((ROOT / "data/sample_sustainable.json").read_text())
    payload["green_interest_rate_percent"] = 7
    with pytest.raises(ValidationError):
        SustainableDefinition.model_validate(payload)
    payload = json.loads((ROOT / "data/sample_sustainable.json").read_text())
    payload["natural_capital_assets"].append(payload["natural_capital_assets"][0])
    with pytest.raises(ValidationError):
        SustainableDefinition.model_validate(payload)


def test_v170_sustainable_definition_migrates() -> None:
    payload = json.loads((ROOT / "data/legacy_v1.7.0_sustainable.json").read_text())
    assert normalize_sustainable(payload).contract_version == "1.8.0"


def test_browser_sustainable_parity() -> None:
    expected = evaluate_sustainable(sample(), generated_at=FIXED).model_dump(
        mode="json"
    )
    result = subprocess.run(
        [
            "node",
            "scripts/browser_sustainable_parity.js",
            "data/sample_sustainable.json",
            FIXED,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == expected
