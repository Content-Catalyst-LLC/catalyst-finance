from __future__ import annotations

import json
from pathlib import Path

from catalyst_finance.repositories import JsonWorkspaceRepository
from catalyst_finance.sustainable_models import SustainableDefinition
from catalyst_finance.workspace import WorkspaceService

ROOT = Path(__file__).resolve().parents[1]


def test_sustainable_analysis_revision_lifecycle(tmp_path: Path) -> None:
    counter = iter(
        ["workspace_demo", "sustainable_demo", "revision_one", "revision_two"]
    )
    service = WorkspaceService(
        JsonWorkspaceRepository(tmp_path),
        id_factory=lambda prefix: f"{prefix}_{next(counter)}",
    )
    workspace = service.create_workspace("Sustainable workspace")
    definition = SustainableDefinition.model_validate(
        json.loads((ROOT / "data/sample_sustainable.json").read_text())
    )
    workspace = service.create_sustainable_analysis(workspace.workspace_id, definition)
    record = workspace.sustainable_analyses[0]
    changed = definition.model_copy(update={"name": "Updated natural-capital case"})
    workspace = service.save_sustainable_revision(
        workspace.workspace_id,
        record.analysis_id,
        changed,
        change_note="Updated valuation",
    )
    assert len(workspace.sustainable_analyses[0].revisions) == 2
    workspace = service.delete_sustainable_analysis(
        workspace.workspace_id, record.analysis_id
    )
    assert workspace.sustainable_analyses == []
