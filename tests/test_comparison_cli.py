import json
from pathlib import Path

from catalyst_finance.comparison_cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_comparison_cli_writes_all_formats(tmp_path: Path) -> None:
    outputs = {
        "json": tmp_path / "result.json",
        "csv": tmp_path / "result.csv",
        "md": tmp_path / "result.md",
        "html": tmp_path / "result.html",
    }
    status = main(
        [
            str(ROOT / "data/sample_comparison.json"),
            "--json-output",
            str(outputs["json"]),
            "--csv-output",
            str(outputs["csv"]),
            "--markdown-output",
            str(outputs["md"]),
            "--html-output",
            str(outputs["html"]),
        ]
    )
    assert status == 0
    assert all(path.exists() for path in outputs.values())
    assert json.loads(outputs["json"].read_text())["model_id"] == (
        "catalyst-finance.comparison"
    )


def test_comparison_cli_returns_structured_validation_error(
    tmp_path: Path, capsys
) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{}")
    assert main([str(path)]) == 2
    assert json.loads(capsys.readouterr().out)["error"] == "invalid_comparison"
