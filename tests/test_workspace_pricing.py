from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from catalyst_finance.pricing_models import PricingDefinition
from catalyst_finance.repositories import JsonWorkspaceRepository
from catalyst_finance.workspace import WorkspaceService

ROOT = Path(__file__).resolve().parents[1]


def test_pricing_analysis_revision_lifecycle(tmp_path: Path) -> None:
    counter = iter(["workspace_demo", "pricing_demo", "revision_one", "revision_two"])
    service = WorkspaceService(
        JsonWorkspaceRepository(tmp_path),
        clock=lambda: datetime(2026, 7, 17, tzinfo=timezone.utc),
        id_factory=lambda prefix: f"{prefix}_{next(counter)}",
    )
    workspace = service.create_workspace("Pricing workspace")
    definition = PricingDefinition.model_validate_json(
        (ROOT / "data/sample_pricing.json").read_text()
    )
    workspace = service.create_pricing_analysis(workspace.workspace_id, definition)
    record = workspace.pricing_analyses[0]
    assert record.current_revision.revision_number == 1
    changed = definition.model_copy(update={"name": "Updated pricing"})
    workspace = service.save_pricing_revision(
        workspace.workspace_id, record.analysis_id, changed
    )
    assert len(workspace.pricing_analyses[0].revisions) == 2
    assert workspace.pricing_analyses[0].name == "Updated pricing"
    workspace = service.delete_pricing_analysis(
        workspace.workspace_id, record.analysis_id
    )
    assert workspace.pricing_analyses == []
