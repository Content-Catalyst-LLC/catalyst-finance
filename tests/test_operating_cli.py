from __future__ import annotations

import json
import sys
from pathlib import Path

from catalyst_finance.operating_cli import main


def test_operating_cli_writes_json_and_csv(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "operating.json"
    csv_path = tmp_path / "operating.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "catalyst-finance-operating",
            "data/sample_operating.json",
            "--output",
            str(output),
            "--csv",
            str(csv_path),
        ],
    )
    assert main() == 0
    payload = json.loads(output.read_text())
    assert payload["model_id"] == "catalyst-finance.operating"
    assert len(csv_path.read_text().splitlines()) == 5
