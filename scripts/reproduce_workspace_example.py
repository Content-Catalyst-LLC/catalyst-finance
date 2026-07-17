#!/usr/bin/env python3
"""Reproduce the checked-in persistent workspace example."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalyst_finance.repositories import JsonWorkspaceRepository  # noqa: E402
from catalyst_finance.workspace import WorkspaceService  # noqa: E402
from catalyst_finance.workspace_models import WorkspaceDefaults  # noqa: E402

FIXED = datetime(2026, 7, 17, tzinfo=timezone.utc)


class SequentialIds:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def __call__(self, prefix: str) -> str:
        self.counts[prefix] = self.counts.get(prefix, 0) + 1
        return f"{prefix}_{self.counts[prefix]:03d}"


def reproduce(path: Path) -> Path:
    with tempfile.TemporaryDirectory(
        prefix="catalyst-finance-workspace-example-"
    ) as tmp:
        service = WorkspaceService(
            JsonWorkspaceRepository(Path(tmp)),
            clock=lambda: FIXED,
            id_factory=SequentialIds(),
        )
        workspace = service.create_workspace(
            "Facilities investment review",
            description="Persistent finance scenarios for the facilities portfolio.",
            defaults=WorkspaceDefaults(currency="USD", locale="en-US"),
        )
        workspace = service.add_project(
            workspace.workspace_id,
            "Main campus efficiency",
            tags=["facilities", "energy"],
        )
        project_id = workspace.projects[0].project_id
        workspace = service.create_scenario(
            workspace.workspace_id,
            "Building efficiency retrofit",
            project_id=project_id,
            template_id="sustainability-investment",
            alternative_label="Base",
            tags=["retrofit", "capital"],
        )
        scenario = workspace.scenarios[0]
        revised = scenario.current_revision.scenario.model_copy(
            update={
                "assumptions": scenario.current_revision.scenario.assumptions.model_copy(
                    update={"external_funding": 65000, "confidence_percent": 75}
                )
            }
        )
        service.save_revision(
            workspace.workspace_id,
            scenario.scenario_id,
            revised,
            change_note="Updated grant and evidence confidence",
        )
        export_path = Path(tmp) / "export.json"
        service.export_workspace(workspace.workspace_id, export_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.loads(export_path.read_text(encoding="utf-8"))
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "examples" / "sample_finance_workspace.export.json",
    )
    args = parser.parse_args()
    print(f"Wrote {reproduce(args.output.resolve())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
