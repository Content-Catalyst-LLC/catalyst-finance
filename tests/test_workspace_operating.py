from __future__ import annotations

import json
from pathlib import Path

from catalyst_finance.operating_models import OperatingDefinition
from catalyst_finance.repositories import JsonWorkspaceRepository
from catalyst_finance.workspace import WorkspaceService

ROOT = Path(__file__).resolve().parents[1]


def test_operating_analysis_revision_lifecycle(tmp_path: Path) -> None:
    counter = iter(["workspace_demo", "operating_demo", "revision_one", "revision_two"])
    service = WorkspaceService(
        JsonWorkspaceRepository(tmp_path),
        id_factory=lambda prefix: f"{prefix}_{next(counter)}",
    )
    workspace = service.create_workspace("Operating workspace")
    definition = OperatingDefinition.model_validate(
        json.loads((ROOT / "data/sample_operating.json").read_text())
    )
    workspace = service.create_operating_analysis(workspace.workspace_id, definition)
    record = workspace.operating_analyses[0]
    assert record.current_revision.revision_number == 1
    changed = definition.model_copy(update={"name": "Updated operating plan"})
    workspace = service.save_operating_revision(
        workspace.workspace_id,
        record.analysis_id,
        changed,
        change_note="Updated budget",
    )
    assert len(workspace.operating_analyses[0].revisions) == 2
    assert workspace.operating_analyses[0].name == "Updated operating plan"
    workspace = service.delete_operating_analysis(
        workspace.workspace_id, record.analysis_id
    )
    assert workspace.operating_analyses == []
