from __future__ import annotations

import json
from pathlib import Path

from catalyst_finance.platform_models import PlatformDefinition
from catalyst_finance.repositories import JsonWorkspaceRepository
from catalyst_finance.workspace import WorkspaceService

ROOT = Path(__file__).resolve().parents[1]


def test_platform_analysis_revision_lifecycle(tmp_path: Path) -> None:
    counter = iter(["workspace_demo", "platform_demo", "revision_one", "revision_two"])
    service = WorkspaceService(
        JsonWorkspaceRepository(tmp_path),
        id_factory=lambda prefix: f"{prefix}_{next(counter)}",
    )
    workspace = service.create_workspace("Connected platform workspace")
    definition = PlatformDefinition.model_validate(
        json.loads((ROOT / "data/sample_platform.json").read_text())
    )
    workspace = service.create_platform_analysis(workspace.workspace_id, definition)
    record = workspace.platform_analyses[0]
    changed = definition.model_copy(update={"name": "Updated connected platform"})
    workspace = service.save_platform_revision(
        workspace.workspace_id,
        record.analysis_id,
        changed,
        change_note="Updated product registry",
    )
    assert len(workspace.platform_analyses[0].revisions) == 2
    assert workspace.platform_analyses[0].current_revision.definition.name == (
        "Updated connected platform"
    )
    workspace = service.delete_platform_analysis(
        workspace.workspace_id, record.analysis_id
    )
    assert workspace.platform_analyses == []
