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
    ["sample_finance_scenario.json", "legacy_v1.0.0_scenario.json"],
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
