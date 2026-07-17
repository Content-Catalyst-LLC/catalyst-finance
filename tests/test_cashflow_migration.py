import json
from pathlib import Path

from catalyst_finance.cashflow_migration import normalize_cash_flow

ROOT = Path(__file__).resolve().parents[1]


def test_v130_cash_flow_migrates_without_field_loss() -> None:
    raw = json.loads((ROOT / "data/legacy_v1.3.0_cash_flow_scenario.json").read_text())
    migrated = normalize_cash_flow(raw)
    assert migrated.contract_version == "1.6.0"
    assert len(migrated.lines) == len(raw["lines"])
    assert migrated.lines[0].amount == raw["lines"][0]["amount"]
