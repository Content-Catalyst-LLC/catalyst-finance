import json
from datetime import datetime, timezone
from pathlib import Path

from catalyst_finance.comparison_models import ComparisonDefinition
from catalyst_finance.repositories import JsonWorkspaceRepository
from catalyst_finance.workspace import WorkspaceService

ROOT = Path(__file__).resolve().parents[1]


def definition() -> ComparisonDefinition:
    return ComparisonDefinition.model_validate(
        json.loads((ROOT / "data/sample_comparison.json").read_text())
    )


def test_workspace_preserves_versioned_comparison_definitions(tmp_path: Path) -> None:
    counter = {"value": 0}

    def ids(prefix: str) -> str:
        counter["value"] += 1
        return f"{prefix}_{counter['value']:05d}"

    service = WorkspaceService(
        JsonWorkspaceRepository(tmp_path / "workspaces"),
        clock=lambda: datetime(2026, 7, 17, tzinfo=timezone.utc),
        id_factory=ids,
    )
    workspace = service.create_workspace("Comparison workspace")
    workspace = service.create_comparison(workspace.workspace_id, definition())
    comparison = workspace.comparisons[0]
    assert comparison.current_revision.definition.baseline_alternative_id == "base"
    assert comparison.revisions[0].revision_number == 1

    revised = definition().model_copy(update={"name": "Revised options"})
    workspace = service.save_comparison_revision(
        workspace.workspace_id,
        comparison.comparison_id,
        revised,
        change_note="Changed selected alternatives",
    )
    comparison = workspace.comparisons[0]
    assert len(comparison.revisions) == 2
    assert comparison.current_revision.definition.name == "Revised options"
    assert comparison.current_revision.change_note == "Changed selected alternatives"

    workspace = service.delete_comparison(
        workspace.workspace_id, comparison.comparison_id
    )
    assert workspace.comparisons == []
