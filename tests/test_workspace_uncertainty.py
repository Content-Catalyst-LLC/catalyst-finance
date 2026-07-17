from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from catalyst_finance.repositories import JsonWorkspaceRepository
from catalyst_finance.uncertainty_models import UncertaintyDefinition
from catalyst_finance.workspace import WorkspaceService

ROOT = Path(__file__).resolve().parents[1]


def test_uncertainty_revision_lifecycle(tmp_path: Path) -> None:
    counter = iter(range(1, 20))
    service = WorkspaceService(
        JsonWorkspaceRepository(tmp_path),
        clock=lambda: datetime(2026, 7, 17, tzinfo=timezone.utc),
        id_factory=lambda prefix: f"{prefix}_{next(counter)}",
    )
    workspace = service.create_workspace("Risk workspace")
    definition = UncertaintyDefinition.model_validate_json(
        (ROOT / "data/sample_uncertainty.json").read_text()
    )
    workspace = service.create_uncertainty_analysis(workspace.workspace_id, definition)
    record = workspace.uncertainty_analyses[0]
    assert record.current_revision.revision_number == 1
    changed = definition.model_copy(update={"name": "Updated risk analysis"})
    workspace = service.save_uncertainty_revision(
        workspace.workspace_id,
        record.analysis_id,
        changed,
        change_note="Updated evidence",
    )
    record = workspace.uncertainty_analyses[0]
    assert record.name == "Updated risk analysis"
    assert record.current_revision.revision_number == 2
    workspace = service.delete_uncertainty_analysis(
        workspace.workspace_id, record.analysis_id
    )
    assert workspace.uncertainty_analyses == []
