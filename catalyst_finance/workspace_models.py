"""Versioned workspace records for Catalyst Finance v1.2.0."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .models import (
    CONTRACT_VERSION,
    MODEL_ID,
    ContractModel,
    FinanceContext,
    FinanceScenarioInput,
)

WORKSPACE_CONTRACT_VERSION: Literal["1.2.0"] = "1.2.0"

Identifier = Annotated[
    str, Field(min_length=5, max_length=100, pattern=r"^[a-z]+_[A-Za-z0-9_-]+$")
]
Tag = Annotated[str, Field(min_length=1, max_length=80)]


class WorkspaceDefaults(ContractModel):
    """Defaults inherited when a new scenario is created."""

    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    locale: str = Field(default="en-US", min_length=2, max_length=35)
    time_basis: Literal["end_of_period"] = "end_of_period"
    price_basis: Literal["nominal", "real"] = "nominal"
    discount_rate_basis: Literal["nominal", "real"] = "nominal"
    default_model_id: Literal["catalyst-finance.screening"] = MODEL_ID
    default_model_version: Literal["1.2.0"] = CONTRACT_VERSION

    @model_validator(mode="after")
    def matching_basis(self) -> WorkspaceDefaults:
        if self.price_basis != self.discount_rate_basis:
            raise ValueError(
                "price_basis and discount_rate_basis must match in workspace defaults"
            )
        return self

    def finance_context(self) -> FinanceContext:
        return FinanceContext(
            currency=self.currency,
            price_basis=self.price_basis,
            discount_rate_basis=self.discount_rate_basis,
            time_basis=self.time_basis,
        )


class WorkspaceProject(ContractModel):
    project_id: Identifier
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    status: Literal["draft", "active", "completed", "archived"] = "active"
    tags: list[Tag] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ScenarioRevision(ContractModel):
    revision_id: Identifier
    revision_number: Annotated[int, Field(ge=1)]
    created_at: datetime
    model_id: Literal["catalyst-finance.screening"] = MODEL_ID
    model_version: Literal["1.2.0"] = CONTRACT_VERSION
    change_note: str = Field(default="", max_length=1000)
    scenario: FinanceScenarioInput


class WorkspaceScenario(ContractModel):
    scenario_id: Identifier
    project_id: Identifier | None = None
    name: str = Field(min_length=1, max_length=200)
    alternative_label: str = Field(default="Base", min_length=1, max_length=120)
    status: Literal["draft", "active", "archived"] = "active"
    template_id: str | None = Field(default=None, max_length=100)
    notes: str = Field(default="", max_length=10000)
    tags: list[Tag] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None
    current_revision_id: Identifier
    revisions: list[ScenarioRevision] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_revision_chain(self) -> WorkspaceScenario:
        revision_ids = [item.revision_id for item in self.revisions]
        if len(revision_ids) != len(set(revision_ids)):
            raise ValueError("scenario revision IDs must be unique")
        expected = list(range(1, len(self.revisions) + 1))
        actual = [item.revision_number for item in self.revisions]
        if actual != expected:
            raise ValueError("scenario revision numbers must be contiguous and ordered")
        if self.current_revision_id != self.revisions[-1].revision_id:
            raise ValueError("current_revision_id must reference the latest revision")
        if self.status == "archived" and self.archived_at is None:
            raise ValueError("archived scenarios require archived_at")
        if self.status != "archived" and self.archived_at is not None:
            raise ValueError("non-archived scenarios cannot have archived_at")
        return self

    @property
    def current_revision(self) -> ScenarioRevision:
        return self.revisions[-1]


class FinanceWorkspace(ContractModel):
    workspace_contract_version: Literal["1.2.0"] = WORKSPACE_CONTRACT_VERSION
    workspace_id: Identifier
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    status: Literal["active", "archived"] = "active"
    defaults: WorkspaceDefaults = Field(default_factory=WorkspaceDefaults)
    created_at: datetime
    updated_at: datetime
    projects: list[WorkspaceProject] = Field(default_factory=list)
    scenarios: list[WorkspaceScenario] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_identifiers(self) -> FinanceWorkspace:
        project_ids = [item.project_id for item in self.projects]
        scenario_ids = [item.scenario_id for item in self.scenarios]
        if len(project_ids) != len(set(project_ids)):
            raise ValueError("workspace project IDs must be unique")
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("workspace scenario IDs must be unique")
        known_projects = set(project_ids)
        for scenario in self.scenarios:
            if (
                scenario.project_id is not None
                and scenario.project_id not in known_projects
            ):
                raise ValueError(
                    f"scenario {scenario.scenario_id} references an unknown project"
                )
        return self


class WorkspaceExport(ContractModel):
    export_contract_version: Literal["1.2.0"] = WORKSPACE_CONTRACT_VERSION
    exported_at: datetime
    workspace: FinanceWorkspace


class ScenarioTemplate(ContractModel):
    template_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1000)
    category: str = Field(min_length=1, max_length=120)
    scenario: FinanceScenarioInput
