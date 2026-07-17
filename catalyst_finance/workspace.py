"""Workspace lifecycle and revision services for Catalyst Finance v1.5.0."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from .cashflow_migration import normalize_cash_flow
from .cashflow_models import CashFlowScenarioInput
from .comparison_models import ComparisonDefinition
from .migration import normalize_scenario
from .models import FinanceScenarioInput
from .repositories import WorkspaceNotFoundError, WorkspaceRepository
from .templates import get_template
from .uncertainty_models import UncertaintyDefinition
from .workspace_migration import migrate_workspace_payload
from .workspace_models import (
    ComparisonRevision,
    FinanceWorkspace,
    ScenarioPayload,
    ScenarioRevision,
    UncertaintyRevision,
    WorkspaceComparison,
    WorkspaceDefaults,
    WorkspaceExport,
    WorkspaceProject,
    WorkspaceScenario,
    WorkspaceUncertaintyAnalysis,
)

Clock = Callable[[], datetime]
IdFactory = Callable[[str], str]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def random_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class WorkspaceConflictError(ValueError):
    """Raised when an import would overwrite an existing workspace."""


def normalize_workspace_scenario(
    scenario: ScenarioPayload | dict[str, Any],
) -> ScenarioPayload:
    if isinstance(scenario, (FinanceScenarioInput, CashFlowScenarioInput)):
        return scenario
    if scenario.get("model_id") == "catalyst-finance.cash-flow":
        return cast(CashFlowScenarioInput, normalize_cash_flow(scenario))
    return normalize_scenario(scenario)[0]


class WorkspaceService:
    """Application service preserving identifiers and revision history."""

    def __init__(
        self,
        repository: WorkspaceRepository,
        *,
        clock: Clock = utc_now,
        id_factory: IdFactory = random_id,
    ) -> None:
        self.repository = repository
        self.clock = clock
        self.id_factory = id_factory

    def list_workspaces(self) -> list[FinanceWorkspace]:
        return self.repository.list()

    def get_workspace(self, workspace_id: str) -> FinanceWorkspace:
        return self.repository.get(workspace_id)

    def create_workspace(
        self,
        name: str,
        *,
        description: str = "",
        defaults: WorkspaceDefaults | None = None,
    ) -> FinanceWorkspace:
        now = self.clock()
        workspace = FinanceWorkspace(
            workspace_id=self.id_factory("workspace"),
            name=name,
            description=description,
            defaults=defaults or WorkspaceDefaults(),
            created_at=now,
            updated_at=now,
        )
        return self.repository.save(workspace)

    def rename_workspace(self, workspace_id: str, name: str) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        return self.repository.save(
            workspace.model_copy(update={"name": name, "updated_at": self.clock()})
        )

    def archive_workspace(self, workspace_id: str) -> FinanceWorkspace:
        return self._set_workspace_status(workspace_id, "archived")

    def restore_workspace(self, workspace_id: str) -> FinanceWorkspace:
        return self._set_workspace_status(workspace_id, "active")

    def _set_workspace_status(self, workspace_id: str, status: str) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        return self.repository.save(
            workspace.model_copy(update={"status": status, "updated_at": self.clock()})
        )

    def delete_workspace(self, workspace_id: str) -> None:
        self.repository.delete(workspace_id)

    def add_project(
        self,
        workspace_id: str,
        name: str,
        *,
        description: str = "",
        tags: list[str] | None = None,
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        now = self.clock()
        project = WorkspaceProject(
            project_id=self.id_factory("project"),
            name=name,
            description=description,
            tags=tags or [],
            created_at=now,
            updated_at=now,
        )
        return self.repository.save(
            workspace.model_copy(
                update={
                    "projects": [*workspace.projects, project],
                    "updated_at": now,
                }
            )
        )

    def rename_project(
        self, workspace_id: str, project_id: str, name: str
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        now = self.clock()
        found = False
        projects: list[WorkspaceProject] = []
        for project in workspace.projects:
            if project.project_id == project_id:
                projects.append(
                    project.model_copy(update={"name": name, "updated_at": now})
                )
                found = True
            else:
                projects.append(project)
        if not found:
            raise WorkspaceNotFoundError(project_id)
        return self.repository.save(
            workspace.model_copy(update={"projects": projects, "updated_at": now})
        )

    def create_scenario(
        self,
        workspace_id: str,
        name: str,
        *,
        scenario: ScenarioPayload | dict[str, Any] | None = None,
        project_id: str | None = None,
        alternative_label: str = "Base",
        template_id: str | None = "capital-project",
        notes: str = "",
        tags: list[str] | None = None,
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        if project_id is not None and not any(
            item.project_id == project_id for item in workspace.projects
        ):
            raise WorkspaceNotFoundError(project_id)
        if scenario is None:
            template = get_template(
                template_id or "capital-project", workspace.defaults
            )
            if template is None:
                raise WorkspaceNotFoundError(template_id or "capital-project")
            scenario_input = template.scenario.model_copy(
                update={
                    "project": template.scenario.project.model_copy(
                        update={"name": name}
                    )
                }
            )
        else:
            scenario_input = normalize_workspace_scenario(scenario)
        now = self.clock()
        revision = ScenarioRevision(
            revision_id=self.id_factory("revision"),
            revision_number=1,
            created_at=now,
            change_note="Initial scenario",
            model_id=scenario_input.model_id,
            scenario=scenario_input,
        )
        record = WorkspaceScenario(
            scenario_id=self.id_factory("scenario"),
            project_id=project_id,
            name=name,
            alternative_label=alternative_label,
            template_id=template_id,
            notes=notes,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            current_revision_id=revision.revision_id,
            revisions=[revision],
        )
        return self.repository.save(
            workspace.model_copy(
                update={
                    "scenarios": [*workspace.scenarios, record],
                    "updated_at": now,
                }
            )
        )

    def save_revision(
        self,
        workspace_id: str,
        scenario_id: str,
        scenario: ScenarioPayload | dict[str, Any],
        *,
        change_note: str = "Saved revision",
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        return self._revision_workspace(
            workspace,
            scenario_id,
            scenario,
            change_note=change_note,
            autosave=False,
        )

    def autosave_revision(
        self,
        workspace_id: str,
        scenario_id: str,
        scenario: ScenarioPayload | dict[str, Any],
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        return self._revision_workspace(
            workspace,
            scenario_id,
            scenario,
            change_note="Recovered autosave",
            autosave=True,
        )

    def _revision_workspace(
        self,
        workspace: FinanceWorkspace,
        scenario_id: str,
        scenario: ScenarioPayload | dict[str, Any],
        *,
        change_note: str,
        autosave: bool,
    ) -> FinanceWorkspace:
        scenario_input = normalize_workspace_scenario(scenario)
        now = self.clock()
        found = False
        records: list[WorkspaceScenario] = []
        for record in workspace.scenarios:
            if record.scenario_id != scenario_id:
                records.append(record)
                continue
            found = True
            if scenario_input.model_id != record.current_revision.model_id:
                raise ValueError("scenario revisions cannot change the model_id")
            revision = ScenarioRevision(
                revision_id=self.id_factory("revision"),
                revision_number=len(record.revisions) + 1,
                created_at=now,
                change_note=change_note,
                model_id=scenario_input.model_id,
                scenario=scenario_input,
            )
            records.append(
                record.model_copy(
                    update={
                        "updated_at": now,
                        "current_revision_id": revision.revision_id,
                        "revisions": [*record.revisions, revision],
                    }
                )
            )
        if not found:
            raise WorkspaceNotFoundError(scenario_id)
        updated = workspace.model_copy(update={"scenarios": records, "updated_at": now})
        if autosave:
            return self.repository.save_autosave(updated)
        return self.repository.save(updated)

    def recover_workspace(self, workspace_id: str) -> FinanceWorkspace | None:
        return self.repository.recover_autosave(workspace_id)

    def commit_recovery(self, workspace_id: str) -> FinanceWorkspace:
        recovered = self.repository.recover_autosave(workspace_id)
        if recovered is None:
            raise WorkspaceNotFoundError(f"{workspace_id}:autosave")
        return self.repository.save(recovered)

    def duplicate_scenario(
        self,
        workspace_id: str,
        scenario_id: str,
        *,
        name: str | None = None,
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        source = self._scenario(workspace, scenario_id)
        now = self.clock()
        revision = ScenarioRevision(
            revision_id=self.id_factory("revision"),
            revision_number=1,
            created_at=now,
            change_note=f"Duplicated from {source.scenario_id}",
            model_id=source.current_revision.model_id,
            scenario=source.current_revision.scenario,
        )
        duplicate = WorkspaceScenario(
            scenario_id=self.id_factory("scenario"),
            project_id=source.project_id,
            name=name or f"{source.name} copy",
            alternative_label=source.alternative_label,
            template_id=source.template_id,
            notes=source.notes,
            tags=list(source.tags),
            created_at=now,
            updated_at=now,
            current_revision_id=revision.revision_id,
            revisions=[revision],
        )
        return self.repository.save(
            workspace.model_copy(
                update={
                    "scenarios": [*workspace.scenarios, duplicate],
                    "updated_at": now,
                }
            )
        )

    def rename_scenario(
        self, workspace_id: str, scenario_id: str, name: str
    ) -> FinanceWorkspace:
        return self._update_scenario_metadata(workspace_id, scenario_id, name=name)

    def update_scenario_metadata(
        self,
        workspace_id: str,
        scenario_id: str,
        *,
        alternative_label: str | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> FinanceWorkspace:
        return self._update_scenario_metadata(
            workspace_id,
            scenario_id,
            alternative_label=alternative_label,
            notes=notes,
            tags=tags,
        )

    def _update_scenario_metadata(
        self,
        workspace_id: str,
        scenario_id: str,
        **changes: object,
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        now = self.clock()
        found = False
        records: list[WorkspaceScenario] = []
        clean_changes = {
            key: value for key, value in changes.items() if value is not None
        }
        clean_changes["updated_at"] = now
        for record in workspace.scenarios:
            if record.scenario_id == scenario_id:
                records.append(record.model_copy(update=clean_changes))
                found = True
            else:
                records.append(record)
        if not found:
            raise WorkspaceNotFoundError(scenario_id)
        return self.repository.save(
            workspace.model_copy(update={"scenarios": records, "updated_at": now})
        )

    def archive_scenario(self, workspace_id: str, scenario_id: str) -> FinanceWorkspace:
        return self._set_scenario_status(workspace_id, scenario_id, "archived")

    def restore_scenario(self, workspace_id: str, scenario_id: str) -> FinanceWorkspace:
        return self._set_scenario_status(workspace_id, scenario_id, "active")

    def _set_scenario_status(
        self, workspace_id: str, scenario_id: str, status: str
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        now = self.clock()
        found = False
        records: list[WorkspaceScenario] = []
        for record in workspace.scenarios:
            if record.scenario_id == scenario_id:
                records.append(
                    record.model_copy(
                        update={
                            "status": status,
                            "archived_at": now if status == "archived" else None,
                            "updated_at": now,
                        }
                    )
                )
                found = True
            else:
                records.append(record)
        if not found:
            raise WorkspaceNotFoundError(scenario_id)
        return self.repository.save(
            workspace.model_copy(update={"scenarios": records, "updated_at": now})
        )

    def delete_scenario(self, workspace_id: str, scenario_id: str) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        records = [
            record
            for record in workspace.scenarios
            if record.scenario_id != scenario_id
        ]
        if len(records) == len(workspace.scenarios):
            raise WorkspaceNotFoundError(scenario_id)
        return self.repository.save(
            workspace.model_copy(
                update={"scenarios": records, "updated_at": self.clock()}
            )
        )

    def create_comparison(
        self,
        workspace_id: str,
        definition: ComparisonDefinition | dict[str, Any],
        *,
        name: str | None = None,
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        comparison_definition = (
            definition
            if isinstance(definition, ComparisonDefinition)
            else ComparisonDefinition.model_validate(definition)
        )
        now = self.clock()
        revision = ComparisonRevision(
            revision_id=self.id_factory("revision"),
            revision_number=1,
            created_at=now,
            change_note="Initial comparison definition",
            definition=comparison_definition,
        )
        record = WorkspaceComparison(
            comparison_id=self.id_factory("comparison"),
            name=name or comparison_definition.name,
            created_at=now,
            updated_at=now,
            current_revision_id=revision.revision_id,
            revisions=[revision],
        )
        return self.repository.save(
            workspace.model_copy(
                update={
                    "comparisons": [*workspace.comparisons, record],
                    "updated_at": now,
                }
            )
        )

    def save_comparison_revision(
        self,
        workspace_id: str,
        comparison_id: str,
        definition: ComparisonDefinition | dict[str, Any],
        *,
        change_note: str = "Saved comparison revision",
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        comparison_definition = (
            definition
            if isinstance(definition, ComparisonDefinition)
            else ComparisonDefinition.model_validate(definition)
        )
        now = self.clock()
        found = False
        records: list[WorkspaceComparison] = []
        for record in workspace.comparisons:
            if record.comparison_id != comparison_id:
                records.append(record)
                continue
            found = True
            revision = ComparisonRevision(
                revision_id=self.id_factory("revision"),
                revision_number=len(record.revisions) + 1,
                created_at=now,
                change_note=change_note,
                definition=comparison_definition,
            )
            records.append(
                record.model_copy(
                    update={
                        "name": comparison_definition.name,
                        "updated_at": now,
                        "current_revision_id": revision.revision_id,
                        "revisions": [*record.revisions, revision],
                    }
                )
            )
        if not found:
            raise WorkspaceNotFoundError(comparison_id)
        return self.repository.save(
            workspace.model_copy(update={"comparisons": records, "updated_at": now})
        )

    def delete_comparison(
        self, workspace_id: str, comparison_id: str
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        records = [
            record
            for record in workspace.comparisons
            if record.comparison_id != comparison_id
        ]
        if len(records) == len(workspace.comparisons):
            raise WorkspaceNotFoundError(comparison_id)
        return self.repository.save(
            workspace.model_copy(
                update={"comparisons": records, "updated_at": self.clock()}
            )
        )

    def create_uncertainty_analysis(
        self,
        workspace_id: str,
        definition: UncertaintyDefinition | dict[str, Any],
        *,
        name: str | None = None,
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        uncertainty_definition = (
            definition
            if isinstance(definition, UncertaintyDefinition)
            else UncertaintyDefinition.model_validate(definition)
        )
        now = self.clock()
        revision = UncertaintyRevision(
            revision_id=self.id_factory("revision"),
            revision_number=1,
            created_at=now,
            change_note="Initial uncertainty definition",
            definition=uncertainty_definition,
        )
        record = WorkspaceUncertaintyAnalysis(
            analysis_id=self.id_factory("analysis"),
            name=name or uncertainty_definition.name,
            created_at=now,
            updated_at=now,
            current_revision_id=revision.revision_id,
            revisions=[revision],
        )
        return self.repository.save(
            workspace.model_copy(
                update={
                    "uncertainty_analyses": [*workspace.uncertainty_analyses, record],
                    "updated_at": now,
                }
            )
        )

    def save_uncertainty_revision(
        self,
        workspace_id: str,
        analysis_id: str,
        definition: UncertaintyDefinition | dict[str, Any],
        *,
        change_note: str = "Saved uncertainty revision",
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        uncertainty_definition = (
            definition
            if isinstance(definition, UncertaintyDefinition)
            else UncertaintyDefinition.model_validate(definition)
        )
        now = self.clock()
        found = False
        records: list[WorkspaceUncertaintyAnalysis] = []
        for record in workspace.uncertainty_analyses:
            if record.analysis_id != analysis_id:
                records.append(record)
                continue
            found = True
            revision = UncertaintyRevision(
                revision_id=self.id_factory("revision"),
                revision_number=len(record.revisions) + 1,
                created_at=now,
                change_note=change_note,
                definition=uncertainty_definition,
            )
            records.append(
                record.model_copy(
                    update={
                        "name": uncertainty_definition.name,
                        "updated_at": now,
                        "current_revision_id": revision.revision_id,
                        "revisions": [*record.revisions, revision],
                    }
                )
            )
        if not found:
            raise WorkspaceNotFoundError(analysis_id)
        return self.repository.save(
            workspace.model_copy(
                update={"uncertainty_analyses": records, "updated_at": now}
            )
        )

    def delete_uncertainty_analysis(
        self, workspace_id: str, analysis_id: str
    ) -> FinanceWorkspace:
        workspace = self.repository.get(workspace_id)
        records = [
            record
            for record in workspace.uncertainty_analyses
            if record.analysis_id != analysis_id
        ]
        if len(records) == len(workspace.uncertainty_analyses):
            raise WorkspaceNotFoundError(analysis_id)
        return self.repository.save(
            workspace.model_copy(
                update={"uncertainty_analyses": records, "updated_at": self.clock()}
            )
        )

    def export_workspace(self, workspace_id: str, path: Path) -> WorkspaceExport:
        export = WorkspaceExport(
            exported_at=self.clock(), workspace=self.repository.get(workspace_id)
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(export.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        return export

    def import_workspace(
        self,
        payload: WorkspaceExport | FinanceWorkspace | dict[str, Any],
        *,
        replace: bool = False,
    ) -> FinanceWorkspace:
        if isinstance(payload, WorkspaceExport):
            workspace = payload.workspace
        elif isinstance(payload, FinanceWorkspace):
            workspace = payload
        elif "workspace" in payload:
            workspace = WorkspaceExport.model_validate(
                migrate_workspace_payload(payload)
            ).workspace
        else:
            workspace = FinanceWorkspace.model_validate(
                migrate_workspace_payload(payload)
            )
        try:
            self.repository.get(workspace.workspace_id)
        except WorkspaceNotFoundError:
            pass
        else:
            if not replace:
                raise WorkspaceConflictError(
                    f"workspace {workspace.workspace_id} already exists"
                )
        return self.repository.save(workspace)

    def import_workspace_file(
        self, path: Path, *, replace: bool = False
    ) -> FinanceWorkspace:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("workspace import must be a JSON object")
        return self.import_workspace(payload, replace=replace)

    @staticmethod
    def _scenario(workspace: FinanceWorkspace, scenario_id: str) -> WorkspaceScenario:
        for scenario in workspace.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        raise WorkspaceNotFoundError(scenario_id)
