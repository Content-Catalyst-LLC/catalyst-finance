"""FastAPI application boundary for Catalyst Finance."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException
from pydantic import Field, ValidationError

from .cashflow import evaluate_cash_flow
from .cashflow_migration import normalize_cash_flow
from .comparison import evaluate_comparison
from .comparison_migration import normalize_comparison
from .comparison_models import ComparisonDefinition
from .engine import evaluate_payload
from .models import ContractModel, validation_issues
from .operating import evaluate_operating
from .operating_migration import normalize_operating
from .operating_models import OperatingDefinition
from .pricing import evaluate_pricing
from .pricing_migration import normalize_pricing
from .pricing_models import PricingDefinition
from .registry import get_model, list_models
from .repositories import (
    JsonWorkspaceRepository,
    WorkspaceNotFoundError,
    WorkspaceRepository,
)
from .templates import list_templates
from .uncertainty import evaluate_uncertainty
from .uncertainty_migration import normalize_uncertainty
from .uncertainty_models import UncertaintyDefinition
from .version import __version__
from .workspace import WorkspaceConflictError, WorkspaceService
from .workspace_models import FinanceWorkspace, WorkspaceDefaults, WorkspaceExport


class CreateWorkspaceRequest(ContractModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    defaults: WorkspaceDefaults = Field(default_factory=WorkspaceDefaults)


class CreateProjectRequest(ContractModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    tags: list[str] = Field(default_factory=list)


class CreateScenarioRequest(ContractModel):
    name: str = Field(min_length=1, max_length=200)
    project_id: str | None = None
    alternative_label: str = Field(default="Base", min_length=1, max_length=120)
    template_id: str | None = "capital-project"
    notes: str = Field(default="", max_length=10000)
    tags: list[str] = Field(default_factory=list)
    scenario: dict[str, Any] | None = None


class RevisionRequest(ContractModel):
    scenario: dict[str, Any]
    change_note: str = Field(default="Saved revision", max_length=1000)


class CreateComparisonRequest(ContractModel):
    definition: ComparisonDefinition
    name: str | None = Field(default=None, max_length=240)


class ComparisonRevisionRequest(ContractModel):
    definition: ComparisonDefinition
    change_note: str = Field(default="Saved comparison revision", max_length=1000)


class CreateUncertaintyRequest(ContractModel):
    definition: UncertaintyDefinition
    name: str | None = Field(default=None, max_length=240)


class UncertaintyRevisionRequest(ContractModel):
    definition: UncertaintyDefinition
    change_note: str = Field(default="Saved uncertainty revision", max_length=1000)


class CreatePricingRequest(ContractModel):
    definition: PricingDefinition
    name: str | None = Field(default=None, max_length=240)


class PricingRevisionRequest(ContractModel):
    definition: PricingDefinition
    change_note: str = Field(default="Saved pricing revision", max_length=1000)


class CreateOperatingRequest(ContractModel):
    definition: OperatingDefinition
    name: str | None = Field(default=None, max_length=240)


class OperatingRevisionRequest(ContractModel):
    definition: OperatingDefinition
    change_note: str = Field(default="Saved operating revision", max_length=1000)


class RenameRequest(ContractModel):
    name: str = Field(min_length=1, max_length=200)


class ImportWorkspaceRequest(ContractModel):
    bundle: WorkspaceExport | FinanceWorkspace
    replace: bool = False


def _default_repository() -> WorkspaceRepository:
    configured = os.environ.get("CATALYST_FINANCE_WORKSPACE_DIR")
    directory = (
        Path(configured).expanduser()
        if configured
        else Path.home() / ".catalyst-finance" / "workspaces"
    )
    return JsonWorkspaceRepository(directory)


def create_app(repository: WorkspaceRepository | None = None) -> FastAPI:
    application = FastAPI(
        title="Catalyst Finance API",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
    )
    service = WorkspaceService(repository or _default_repository())

    @application.get("/healthz", tags=["system"])
    def healthz() -> dict[str, bool]:
        return {"ok": True}

    @application.get("/api/v1/version", tags=["system"])
    def version() -> dict[str, str]:
        return {
            "name": "Catalyst Finance",
            "version": __version__,
            "status": "ok",
        }

    @application.get("/api/v1/models", tags=["models"])
    def models() -> dict[str, list[dict[str, Any]]]:
        return {"models": list_models()}

    @application.get("/api/v1/models/{model_id}", tags=["models"])
    def model(model_id: str) -> dict[str, Any]:
        record = get_model(model_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Unknown finance model")
        return record

    @application.post("/api/v1/cash-flow/evaluate", tags=["capital budgeting"])
    def evaluate_cash_flow_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            scenario = normalize_cash_flow(payload)
            return cast(
                dict[str, Any],
                evaluate_cash_flow(scenario).model_dump(mode="json"),
            )
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_cash_flow_scenario",
                    "issues": validation_issues(exc),
                },
            ) from exc

    @application.post("/api/v1/compare", tags=["comparison"])
    def compare_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            definition = normalize_comparison(payload)
            return cast(
                dict[str, Any],
                evaluate_comparison(definition).model_dump(mode="json"),
            )
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_comparison",
                    "issues": validation_issues(exc),
                },
            ) from exc

    @application.post("/api/v1/uncertainty/evaluate", tags=["uncertainty"])
    def evaluate_uncertainty_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            definition = normalize_uncertainty(payload)
            return cast(
                dict[str, Any],
                evaluate_uncertainty(definition).model_dump(mode="json"),
            )
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_uncertainty_definition",
                    "issues": validation_issues(exc),
                },
            ) from exc

    @application.post("/api/v1/pricing/evaluate", tags=["pricing"])
    def evaluate_pricing_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            definition = normalize_pricing(payload)
            return cast(
                dict[str, Any],
                evaluate_pricing(definition).model_dump(mode="json"),
            )
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_pricing_definition",
                    "issues": validation_issues(exc),
                },
            ) from exc

    @application.post("/api/v1/operating/evaluate", tags=["operating economics"])
    def evaluate_operating_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            definition = normalize_operating(payload)
            return cast(
                dict[str, Any],
                evaluate_operating(definition).model_dump(mode="json"),
            )
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_operating_definition",
                    "issues": validation_issues(exc),
                },
            ) from exc

    @application.post("/api/v1/evaluate", tags=["evaluation"])
    def evaluate_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                evaluate_payload(payload).model_dump(mode="json"),
            )
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_finance_scenario",
                    "issues": validation_issues(exc),
                },
            ) from exc

    @application.get("/api/v1/templates", tags=["workspaces"])
    def templates_endpoint() -> dict[str, list[dict[str, Any]]]:
        return {
            "templates": [
                cast(dict[str, Any], item.model_dump(mode="json"))
                for item in list_templates()
            ]
        }

    @application.get("/api/v1/workspaces", tags=["workspaces"])
    def list_workspaces_endpoint() -> dict[str, list[dict[str, Any]]]:
        return {
            "workspaces": [
                cast(dict[str, Any], item.model_dump(mode="json"))
                for item in service.list_workspaces()
            ]
        }

    @application.post("/api/v1/workspaces", tags=["workspaces"], status_code=201)
    def create_workspace_endpoint(payload: CreateWorkspaceRequest) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            service.create_workspace(
                payload.name,
                description=payload.description,
                defaults=payload.defaults,
            ).model_dump(mode="json"),
        )

    @application.post("/api/v1/workspaces/import", tags=["workspaces"])
    def import_workspace_endpoint(payload: ImportWorkspaceRequest) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.import_workspace(
                    payload.bundle, replace=payload.replace
                ).model_dump(mode="json"),
            )
        except WorkspaceConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @application.get("/api/v1/workspaces/{workspace_id}", tags=["workspaces"])
    def get_workspace_endpoint(workspace_id: str) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.get_workspace(workspace_id).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Unknown workspace") from exc

    @application.put("/api/v1/workspaces/{workspace_id}/name", tags=["workspaces"])
    def rename_workspace_endpoint(
        workspace_id: str, payload: RenameRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.rename_workspace(workspace_id, payload.name).model_dump(
                    mode="json"
                ),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Unknown workspace") from exc

    @application.delete("/api/v1/workspaces/{workspace_id}", tags=["workspaces"])
    def delete_workspace_endpoint(workspace_id: str) -> dict[str, str]:
        try:
            service.delete_workspace(workspace_id)
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Unknown workspace") from exc
        return {"deleted": workspace_id}

    @application.post(
        "/api/v1/workspaces/{workspace_id}/projects",
        tags=["workspaces"],
        status_code=201,
    )
    def add_project_endpoint(
        workspace_id: str, payload: CreateProjectRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.add_project(
                    workspace_id,
                    payload.name,
                    description=payload.description,
                    tags=payload.tags,
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Unknown workspace") from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/scenarios",
        tags=["workspaces"],
        status_code=201,
    )
    def add_scenario_endpoint(
        workspace_id: str, payload: CreateScenarioRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.create_scenario(
                    workspace_id,
                    payload.name,
                    scenario=payload.scenario,
                    project_id=payload.project_id,
                    alternative_label=payload.alternative_label,
                    template_id=payload.template_id,
                    notes=payload.notes,
                    tags=payload.tags,
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/revisions",
        tags=["workspaces"],
    )
    def add_revision_endpoint(
        workspace_id: str, scenario_id: str, payload: RevisionRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.save_revision(
                    workspace_id,
                    scenario_id,
                    payload.scenario,
                    change_note=payload.change_note,
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/duplicate",
        tags=["workspaces"],
    )
    def duplicate_scenario_endpoint(
        workspace_id: str, scenario_id: str
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.duplicate_scenario(workspace_id, scenario_id).model_dump(
                    mode="json"
                ),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/archive",
        tags=["workspaces"],
    )
    def archive_scenario_endpoint(
        workspace_id: str, scenario_id: str
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.archive_scenario(workspace_id, scenario_id).model_dump(
                    mode="json"
                ),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/restore",
        tags=["workspaces"],
    )
    def restore_scenario_endpoint(
        workspace_id: str, scenario_id: str
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.restore_scenario(workspace_id, scenario_id).model_dump(
                    mode="json"
                ),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/comparisons",
        tags=["comparison"],
        status_code=201,
    )
    def create_comparison_endpoint(
        workspace_id: str, payload: CreateComparisonRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.create_comparison(
                    workspace_id, payload.definition, name=payload.name
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/comparisons/{comparison_id}/revisions",
        tags=["comparison"],
    )
    def save_comparison_revision_endpoint(
        workspace_id: str,
        comparison_id: str,
        payload: ComparisonRevisionRequest,
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.save_comparison_revision(
                    workspace_id,
                    comparison_id,
                    payload.definition,
                    change_note=payload.change_note,
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.delete(
        "/api/v1/workspaces/{workspace_id}/comparisons/{comparison_id}",
        tags=["comparison"],
    )
    def delete_comparison_endpoint(
        workspace_id: str, comparison_id: str
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.delete_comparison(workspace_id, comparison_id).model_dump(
                    mode="json"
                ),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/uncertainty-analyses",
        tags=["uncertainty"],
        status_code=201,
    )
    def create_uncertainty_endpoint(
        workspace_id: str, payload: CreateUncertaintyRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.create_uncertainty_analysis(
                    workspace_id, payload.definition, name=payload.name
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/uncertainty-analyses/{analysis_id}/revisions",
        tags=["uncertainty"],
    )
    def save_uncertainty_revision_endpoint(
        workspace_id: str,
        analysis_id: str,
        payload: UncertaintyRevisionRequest,
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.save_uncertainty_revision(
                    workspace_id,
                    analysis_id,
                    payload.definition,
                    change_note=payload.change_note,
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.delete(
        "/api/v1/workspaces/{workspace_id}/uncertainty-analyses/{analysis_id}",
        tags=["uncertainty"],
    )
    def delete_uncertainty_endpoint(
        workspace_id: str, analysis_id: str
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.delete_uncertainty_analysis(
                    workspace_id, analysis_id
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/pricing-analyses",
        tags=["pricing"],
        status_code=201,
    )
    def create_pricing_endpoint(
        workspace_id: str, payload: CreatePricingRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.create_pricing_analysis(
                    workspace_id, payload.definition, name=payload.name
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/pricing-analyses/{analysis_id}/revisions",
        tags=["pricing"],
    )
    def save_pricing_revision_endpoint(
        workspace_id: str, analysis_id: str, payload: PricingRevisionRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.save_pricing_revision(
                    workspace_id,
                    analysis_id,
                    payload.definition,
                    change_note=payload.change_note,
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.delete(
        "/api/v1/workspaces/{workspace_id}/pricing-analyses/{analysis_id}",
        tags=["pricing"],
    )
    def delete_pricing_endpoint(workspace_id: str, analysis_id: str) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.delete_pricing_analysis(workspace_id, analysis_id).model_dump(
                    mode="json"
                ),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/operating-analyses",
        tags=["operating economics"],
        status_code=201,
    )
    def create_operating_endpoint(
        workspace_id: str, payload: CreateOperatingRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.create_operating_analysis(
                    workspace_id, payload.definition, name=payload.name
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.post(
        "/api/v1/workspaces/{workspace_id}/operating-analyses/{analysis_id}/revisions",
        tags=["operating economics"],
    )
    def save_operating_revision_endpoint(
        workspace_id: str, analysis_id: str, payload: OperatingRevisionRequest
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.save_operating_revision(
                    workspace_id,
                    analysis_id,
                    payload.definition,
                    change_note=payload.change_note,
                ).model_dump(mode="json"),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.delete(
        "/api/v1/workspaces/{workspace_id}/operating-analyses/{analysis_id}",
        tags=["operating economics"],
    )
    def delete_operating_endpoint(
        workspace_id: str, analysis_id: str
    ) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                service.delete_operating_analysis(workspace_id, analysis_id).model_dump(
                    mode="json"
                ),
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return application


app = create_app()
