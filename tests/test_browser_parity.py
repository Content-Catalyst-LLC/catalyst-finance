import json
import shutil
import subprocess
from pathlib import Path

import pytest

from catalyst_finance.engine import evaluate_scenario
from catalyst_finance.io import load_scenario

ROOT = Path(__file__).resolve().parents[1]
FIXED = "2026-07-17T00:00:00+00:00"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
@pytest.mark.parametrize(
    "filename",
    [
        "sample_finance_scenario.json",
        "legacy_v1.0.0_scenario.json",
        "legacy_v1.1.0_scenario.json",
        "legacy_v1.2.0_scenario.json",
        "legacy_v1.3.0_scenario.json",
    ],
)
def test_browser_engine_matches_python(filename: str) -> None:
    path = ROOT / "data" / filename
    scenario, migration = load_scenario(path)
    python_payload = evaluate_scenario(
        scenario, generated_at=FIXED, migration=migration
    ).model_dump(mode="json")
    completed = subprocess.run(
        ["node", "scripts/browser_parity.js", str(path), FIXED],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    browser_payload = json.loads(completed.stdout)
    assert browser_payload == python_payload


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
@pytest.mark.parametrize(
    "filename",
    [
        "sample_cash_flow_scenario.json",
        "irregular_cash_flow_scenario.json",
        "negative_cash_flow_scenario.json",
        "zero_cost_cash_flow_scenario.json",
        "multiple_sign_cash_flow_scenario.json",
    ],
)
def test_cashflow_browser_engine_matches_python(filename: str) -> None:
    from catalyst_finance.cashflow import evaluate_cash_flow
    from catalyst_finance.cashflow_models import CashFlowScenarioInput

    path = ROOT / "data" / filename
    scenario = CashFlowScenarioInput.model_validate(json.loads(path.read_text()))
    python_payload = evaluate_cash_flow(scenario, generated_at=FIXED).model_dump(
        mode="json"
    )
    completed = subprocess.run(
        ["node", "scripts/browser_cashflow_parity.js", str(path), FIXED],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    browser_payload = json.loads(completed.stdout)
    assert browser_payload == python_payload


def _comparison_core(payload: dict[str, object]) -> dict[str, object]:
    selected = {
        key: payload[key]
        for key in [
            "contract_version",
            "model_id",
            "alternatives",
            "aligned_metrics",
            "rankings",
            "one_way_sensitivities",
            "two_way_sensitivities",
            "break_even_results",
            "tornado",
        ]
    }
    for item in selected["one_way_sensitivities"]:  # type: ignore[union-attr]
        item.pop("reproducibility_key", None)
    for item in selected["two_way_sensitivities"]:  # type: ignore[union-attr]
        item.pop("reproducibility_key", None)
    for item in selected["break_even_results"]:  # type: ignore[union-attr]
        item.pop("reproducibility_key", None)
        item.pop("notes", None)
    return selected


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_comparison_browser_engine_matches_python_core() -> None:
    from catalyst_finance.comparison import evaluate_comparison
    from catalyst_finance.comparison_models import ComparisonDefinition

    path = ROOT / "data/sample_comparison.json"
    definition = ComparisonDefinition.model_validate(json.loads(path.read_text()))
    python_payload = evaluate_comparison(definition, generated_at=FIXED).model_dump(
        mode="json"
    )
    completed = subprocess.run(
        ["node", "scripts/browser_comparison_parity.js", str(path), FIXED],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    browser_payload = json.loads(completed.stdout)
    assert _comparison_core(python_payload) == _comparison_core(browser_payload)
