from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_sustainable_cli_exports_json_and_csv(tmp_path: Path) -> None:
    out = tmp_path / "publication.json"
    csv = tmp_path / "summary.csv"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "catalyst_finance.sustainable_cli",
            "data/sample_sustainable.json",
            "--output",
            str(out),
            "--csv",
            str(csv),
        ],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(out.read_text())
    assert payload["model_id"] == "catalyst-finance.sustainable"
    assert payload["summary"]["adjusted_project_npv"] == 1526250.9
    assert "total_sustainable_value" in csv.read_text()
