import json
from pathlib import Path

from catalyst_finance.cashflow_cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cashflow_cli_writes_json_markdown_and_csv(tmp_path: Path) -> None:
    json_output = tmp_path / "result.json"
    markdown_output = tmp_path / "result.md"
    csv_output = tmp_path / "periods.csv"
    status = main(
        [
            str(ROOT / "data" / "sample_cash_flow_scenario.json"),
            "--json-output",
            str(json_output),
            "--markdown-output",
            str(markdown_output),
            "--csv-output",
            str(csv_output),
        ]
    )
    assert status == 0
    assert json.loads(json_output.read_text())["metrics"]["npv"] == 198884.69
    assert "Capital-budgeting metrics" in markdown_output.read_text()
    assert csv_output.read_text().splitlines()[0].startswith("period,period_label")


def test_cashflow_cli_returns_structured_error(tmp_path: Path, capsys: object) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}")
    assert main([str(invalid)]) == 2
