import json
from pathlib import Path

from catalyst_finance.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cli_writes_reproducible_outputs(tmp_path: Path) -> None:
    json_out = tmp_path / "out.json"
    markdown_out = tmp_path / "out.md"
    result = main(
        [
            "--input",
            str(ROOT / "data" / "sample_finance_scenario.json"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
            "--generated-at",
            "2026-07-17T00:00:00+00:00",
        ]
    )
    assert result == 0
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["metadata"]["version"] == "1.0.1"
    assert markdown_out.read_text(encoding="utf-8").startswith(
        "# Catalyst Finance Scenario Brief"
    )
