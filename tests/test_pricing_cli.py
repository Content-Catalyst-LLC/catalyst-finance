from __future__ import annotations

import json
from pathlib import Path

from catalyst_finance.pricing_cli import main


def test_pricing_cli_writes_json_and_csv(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "pricing.json"
    csv_path = tmp_path / "pricing.csv"
    monkeypatch.setattr(
        "sys.argv",
        [
            "catalyst-finance-pricing",
            "data/sample_pricing.json",
            "--output",
            str(output),
            "--csv",
            str(csv_path),
        ],
    )
    assert main() == 0
    payload = json.loads(output.read_text())
    assert payload["recommendation"]["recommended_price"] == 55
    assert len(csv_path.read_text().splitlines()) == 52
