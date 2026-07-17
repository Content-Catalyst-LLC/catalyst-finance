from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from catalyst_finance.repositories import (
    JsonWorkspaceRepository,
    SQLiteWorkspaceRepository,
    WorkspaceNotFoundError,
    WorkspaceRepository,
)
from catalyst_finance.templates import get_template, list_templates
from catalyst_finance.workspace import WorkspaceConflictError, WorkspaceService
from catalyst_finance.workspace_models import FinanceWorkspace, WorkspaceDefaults


class TickClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 7, 17, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(seconds=1)
        return current


class Ids:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def __call__(self, prefix: str) -> str:
        self.counts[prefix] = self.counts.get(prefix, 0) + 1
        return f"{prefix}_{self.counts[prefix]:03d}"


@pytest.fixture(params=["json", "sqlite"])
def repository(tmp_path: Path, request: pytest.FixtureRequest) -> WorkspaceRepository:
    if request.param == "json":
        return JsonWorkspaceRepository(tmp_path / "json")
    return SQLiteWorkspaceRepository(tmp_path / "finance.sqlite3")


@pytest.fixture
def service(repository: WorkspaceRepository) -> WorkspaceService:
    return WorkspaceService(repository, clock=TickClock(), id_factory=Ids())


def _workspace_with_scenario(service: WorkspaceService) -> tuple[str, str]:
    workspace = service.create_workspace("Investment review")
    workspace = service.add_project(workspace.workspace_id, "Facilities")
    workspace = service.create_scenario(
        workspace.workspace_id,
        "Retrofit",
        project_id=workspace.projects[0].project_id,
        template_id="sustainability-investment",
    )
    return workspace.workspace_id, workspace.scenarios[0].scenario_id


def test_workspace_reopens_with_multiple_scenarios_and_history(
    service: WorkspaceService,
) -> None:
    workspace_id, scenario_id = _workspace_with_scenario(service)
    workspace = service.get_workspace(workspace_id)
    first = workspace.scenarios[0].current_revision.scenario
    revised = first.model_copy(
        update={
            "assumptions": first.assumptions.model_copy(
                update={"annual_savings": first.assumptions.annual_savings + 5000}
            )
        }
    )
    service.save_revision(
        workspace_id, scenario_id, revised, change_note="Revised savings"
    )
    service.create_scenario(
        workspace_id,
        "Controls alternative",
        alternative_label="Alternative A",
        template_id="operating-change",
    )

    reopened = service.get_workspace(workspace_id)
    assert len(reopened.scenarios) == 2
    assert len(reopened.scenarios[0].revisions) == 2
    assert (
        reopened.scenarios[0].revisions[0].revision_id
        != reopened.scenarios[0].revisions[1].revision_id
    )
    assert (
        reopened.scenarios[0].current_revision.scenario.assumptions.annual_savings
        == revised.assumptions.annual_savings
    )


def test_scenario_lifecycle_operations_preserve_source_history(
    service: WorkspaceService,
) -> None:
    workspace_id, scenario_id = _workspace_with_scenario(service)
    original = service.get_workspace(workspace_id).scenarios[0]

    workspace = service.duplicate_scenario(workspace_id, scenario_id, name="Retrofit B")
    duplicate = workspace.scenarios[1]
    assert duplicate.scenario_id != original.scenario_id
    assert (
        duplicate.current_revision.revision_id != original.current_revision.revision_id
    )
    assert duplicate.current_revision.scenario == original.current_revision.scenario

    workspace = service.rename_scenario(
        workspace_id, duplicate.scenario_id, "Retrofit C"
    )
    assert workspace.scenarios[1].name == "Retrofit C"
    workspace = service.archive_scenario(workspace_id, duplicate.scenario_id)
    assert workspace.scenarios[1].status == "archived"
    assert workspace.scenarios[1].archived_at is not None
    workspace = service.restore_scenario(workspace_id, duplicate.scenario_id)
    assert workspace.scenarios[1].status == "active"
    assert workspace.scenarios[1].archived_at is None
    workspace = service.delete_scenario(workspace_id, duplicate.scenario_id)
    assert [item.scenario_id for item in workspace.scenarios] == [scenario_id]


def test_workspace_rename_archive_restore_and_delete(service: WorkspaceService) -> None:
    workspace = service.create_workspace("Old name")
    workspace = service.rename_workspace(workspace.workspace_id, "New name")
    assert workspace.name == "New name"
    assert service.archive_workspace(workspace.workspace_id).status == "archived"
    assert service.restore_workspace(workspace.workspace_id).status == "active"
    service.delete_workspace(workspace.workspace_id)
    with pytest.raises(WorkspaceNotFoundError):
        service.get_workspace(workspace.workspace_id)


def test_export_import_preserves_every_identifier(
    service: WorkspaceService, tmp_path: Path
) -> None:
    workspace_id, scenario_id = _workspace_with_scenario(service)
    original = service.get_workspace(workspace_id)
    export_path = tmp_path / "workspace-export.json"
    bundle = service.export_workspace(workspace_id, export_path)
    service.delete_workspace(workspace_id)

    imported = service.import_workspace_file(export_path)
    assert imported == original
    assert imported.workspace_id == bundle.workspace.workspace_id
    assert imported.scenarios[0].scenario_id == scenario_id
    assert (
        imported.scenarios[0].current_revision_id
        == original.scenarios[0].current_revision_id
    )

    with pytest.raises(WorkspaceConflictError):
        service.import_workspace_file(export_path)
    assert service.import_workspace_file(export_path, replace=True) == original


def test_autosave_recovery_does_not_overwrite_explicit_history(
    service: WorkspaceService,
) -> None:
    workspace_id, scenario_id = _workspace_with_scenario(service)
    canonical = service.get_workspace(workspace_id)
    scenario = canonical.scenarios[0].current_revision.scenario
    interrupted = scenario.model_copy(
        update={
            "assumptions": scenario.assumptions.model_copy(
                update={"capital_cost": 999999}
            )
        }
    )
    autosaved = service.autosave_revision(workspace_id, scenario_id, interrupted)
    assert len(autosaved.scenarios[0].revisions) == 2
    assert len(service.get_workspace(workspace_id).scenarios[0].revisions) == 1

    recovered = service.recover_workspace(workspace_id)
    assert recovered is not None
    assert (
        recovered.scenarios[0].current_revision.scenario.assumptions.capital_cost
        == 999999
    )
    committed = service.commit_recovery(workspace_id)
    assert committed == service.get_workspace(workspace_id)
    assert service.recover_workspace(workspace_id) is None


def test_workspace_templates_inherit_defaults() -> None:
    defaults = WorkspaceDefaults(currency="EUR", locale="de-DE")
    templates = list_templates(defaults)
    assert {item.template_id for item in templates} == {
        "capital-project",
        "operating-change",
        "pricing-decision",
        "sustainability-investment",
        "public-value-initiative",
    }
    assert all(item.scenario.context.currency == "EUR" for item in templates)
    assert get_template("missing", defaults) is None


def test_workspace_contract_rejects_identifier_loss(service: WorkspaceService) -> None:
    workspace_id, _ = _workspace_with_scenario(service)
    payload = service.get_workspace(workspace_id).model_dump(mode="json")
    payload["scenarios"][0]["current_revision_id"] = "revision_missing"
    with pytest.raises(ValueError, match="current_revision_id"):
        FinanceWorkspace.model_validate(payload)


def test_json_repository_uses_atomic_canonical_and_autosave_files(
    tmp_path: Path,
) -> None:
    repository = JsonWorkspaceRepository(tmp_path)
    service = WorkspaceService(repository, clock=TickClock(), id_factory=Ids())
    workspace_id, scenario_id = _workspace_with_scenario(service)
    scenario = (
        service.get_workspace(workspace_id).scenarios[0].current_revision.scenario
    )
    service.autosave_revision(workspace_id, scenario_id, scenario)
    assert (tmp_path / f"{workspace_id}.json").exists()
    assert (tmp_path / f"{workspace_id}.autosave.json").exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_sqlite_and_json_exports_are_contract_equivalent(tmp_path: Path) -> None:
    payloads: list[dict[str, object]] = []
    repositories: Iterator[WorkspaceRepository] = iter(
        [
            JsonWorkspaceRepository(tmp_path / "json"),
            SQLiteWorkspaceRepository(tmp_path / "workspace.sqlite3"),
        ]
    )
    for repository in repositories:
        service = WorkspaceService(repository, clock=TickClock(), id_factory=Ids())
        workspace_id, _ = _workspace_with_scenario(service)
        payloads.append(service.get_workspace(workspace_id).model_dump(mode="json"))
    assert json.dumps(payloads[0], sort_keys=True) == json.dumps(
        payloads[1], sort_keys=True
    )
