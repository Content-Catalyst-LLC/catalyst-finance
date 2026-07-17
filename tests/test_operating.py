from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from catalyst_finance.operating import evaluate_operating
from catalyst_finance.operating_migration import normalize_operating
from catalyst_finance.operating_models import OperatingDefinition

ROOT = Path(__file__).resolve().parents[1]
FIXED = "2026-07-17T00:00:00+00:00"


def sample() -> OperatingDefinition:
    return OperatingDefinition.model_validate(
        json.loads((ROOT / "data/sample_operating.json").read_text())
    )


def test_operating_statement_and_variance_reconcile() -> None:
    publication = evaluate_operating(sample(), generated_at=FIXED)
    assert publication.metadata.row_count == 4
    assert publication.total_summary.budget_operating_profit == 60350.0
    assert publication.total_summary.actual_operating_profit == 62535.0
    assert publication.total_summary.operating_profit_variance == 2185.0
    for row in publication.rows:
        assert row.variance_reconciliation == row.variances[-1].amount


def test_known_january_implementation_variances() -> None:
    row = evaluate_operating(sample(), generated_at=FIXED).rows[0]
    values = {item.variance_id: item.amount for item in row.variances}
    assert values == {
        "sales_volume": 3200.0,
        "sales_price": 2600.0,
        "variable_cost_spending": -1300.0,
        "fixed_cost_spending": -700.0,
        "operating_profit": 3800.0,
    }
    assert row.break_even_units == 78.125
    assert row.margin_of_safety_units == 51.875


def test_cost_centers_and_unit_summaries() -> None:
    publication = evaluate_operating(sample(), generated_at=FIXED)
    assert [item.label for item in publication.cost_center_summaries] == [
        "Client Success",
        "Delivery",
    ]
    assert len(publication.unit_summaries) == 2
    assert publication.total_summary.target_profit_units == 633.333333


def test_nonpositive_contribution_margin_has_no_break_even() -> None:
    definition = sample()
    first = (
        definition.units[0]
        .periods[0]
        .model_copy(update={"budget_variable_cost_per_unit": 700})
    )
    unit = definition.units[0].model_copy(
        update={"periods": [first, *definition.units[0].periods[1:]]}
    )
    changed = definition.model_copy(update={"units": [unit, *definition.units[1:]]})
    row = evaluate_operating(changed, generated_at=FIXED).rows[0]
    assert row.break_even_units is None
    assert row.target_profit_units is None


def test_duplicate_periods_are_rejected() -> None:
    payload = json.loads((ROOT / "data/sample_operating.json").read_text())
    payload["units"][0]["periods"][1]["period"] = 1
    with pytest.raises(ValidationError):
        OperatingDefinition.model_validate(payload)


def test_v160_operating_definition_migrates() -> None:
    payload = json.loads((ROOT / "data/sample_operating.json").read_text())
    payload["contract_version"] = "1.6.0"
    migrated = normalize_operating(payload)
    assert migrated.contract_version == "1.9.0"


def test_browser_operating_parity() -> None:
    expected = evaluate_operating(sample(), generated_at=FIXED).model_dump(mode="json")
    completed = subprocess.run(
        [
            "node",
            "scripts/browser_operating_parity.js",
            "data/sample_operating.json",
            FIXED,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout) == expected
