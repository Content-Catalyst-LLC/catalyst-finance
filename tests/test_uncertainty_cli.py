from __future__ import annotations

import csv
import json
from pathlib import Path

from catalyst_finance.uncertainty_cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_uncertainty_cli_writes_json_and_csv(tmp_path: Path) -> None:
    output = tmp_path / "uncertainty.json"
    csv_path = tmp_path / "summary.csv"
    assert (
        main(
            [
                str(ROOT / "data/sample_uncertainty.json"),
                "--output",
                str(output),
                "--summary-csv",
                str(csv_path),
                "--generated-at",
                "2026-07-17T00:00:00+00:00",
                "--seed",
                "123",
            ]
        )
        == 0
    )
    payload = json.loads(output.read_text())
    assert payload["metadata"]["seed"] == 123
    rows = list(csv.DictReader(csv_path.open()))
    assert {row["metric_id"] for row in rows} == {
        "npv",
        "mirr_percent_annual",
        "discounted_payback_periods",
    }
