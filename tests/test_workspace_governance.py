from __future__ import annotations

import json
from pathlib import Path

from catalyst_finance.governance_models import GovernanceDefinition
from catalyst_finance.repositories import JsonWorkspaceRepository
from catalyst_finance.workspace import WorkspaceService

ROOT = Path(__file__).resolve().parents[1]


def test_governance_analysis_revision_lifecycle(tmp_path: Path) -> None:
    counter = iter(
        ["workspace_demo", "governance_demo", "revision_one", "revision_two"]
    )
    service = WorkspaceService(
        JsonWorkspaceRepository(tmp_path),
        id_factory=lambda prefix: f"{prefix}_{next(counter)}",
    )
    workspace = service.create_workspace("Governance workspace")
    definition = GovernanceDefinition.model_validate(
        json.loads((ROOT / "data/sample_governance.json").read_text())
    )
    workspace = service.create_governance_analysis(workspace.workspace_id, definition)
    record = workspace.governance_analyses[0]
    changed = definition.model_copy(update={"name": "Updated governed case"})
    workspace = service.save_governance_revision(
        workspace.workspace_id,
        record.analysis_id,
        changed,
        change_note="Updated evidence",
    )
    assert len(workspace.governance_analyses[0].revisions) == 2
    assert (
        workspace.governance_analyses[0].revisions[0].definition.name
        != workspace.governance_analyses[0].revisions[1].definition.name
    )
    workspace = service.delete_governance_analysis(
        workspace.workspace_id, record.analysis_id
    )
    assert workspace.governance_analyses == []
