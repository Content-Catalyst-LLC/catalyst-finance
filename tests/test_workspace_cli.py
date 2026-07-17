from __future__ import annotations

import json
from pathlib import Path

from catalyst_finance.workspace_cli import main


def test_workspace_cli_create_list_and_export(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    directory = tmp_path / "workspaces"
    assert main(["--directory", str(directory), "create", "CLI workspace"]) == 0
    created = json.loads(capsys.readouterr().out)
    workspace_id = created["workspace_id"]

    assert (
        main(["--directory", str(directory), "add-scenario", workspace_id, "Case A"])
        == 0
    )
    capsys.readouterr()
    output = tmp_path / "export.json"
    assert (
        main(["--directory", str(directory), "export", workspace_id, str(output)]) == 0
    )
    capsys.readouterr()
    assert output.exists()

    assert main(["--directory", str(directory), "list"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["workspace_id"] == workspace_id


def test_workspace_cli_templates(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["templates"]) == 0
    templates = json.loads(capsys.readouterr().out)
    assert len(templates) == 5
