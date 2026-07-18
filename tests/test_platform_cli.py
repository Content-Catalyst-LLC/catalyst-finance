from __future__ import annotations

import json
from pathlib import Path

from catalyst_finance.platform_cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_platform_cli_writes_publication(tmp_path: Path) -> None:
    output = tmp_path / "platform.json"
    assert (
        main(
            [
                str(ROOT / "data/sample_platform.json"),
                "--output",
                str(output),
                "--generated-at",
                "2026-07-17T18:30:00+00:00",
            ]
        )
        == 0
    )
    payload = json.loads(output.read_text())
    assert payload["model_id"] == "catalyst-finance.platform"
    assert payload["portfolio"]["risk_adjusted_value"] == 1580250.61


def test_platform_cli_rejects_invalid_input(tmp_path: Path, capsys: object) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}")
    assert main([str(invalid)]) == 2
