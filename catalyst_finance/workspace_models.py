"""Versioned workspace records for Catalyst Finance v1.5.0."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .cashflow_models import (
    CashFlowScenarioInput,
)
from .comparison_models import ComparisonDefinition
from .models import (
    CONTRACT_VERSION,
    MODEL_ID,
    ContractModel,
    FinanceContext,
    FinanceScenarioInput,
)
from .uncertainty_models import UncertaintyDefinition

WORKSPACE_CONTRACT_VERSION: Literal["1.5.0"] = "1.5.0"

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
    default_model_id: Literal[
        "catalyst-finance.screening", "catalyst-finance.cash-flow"
    ] = MODEL_ID
    default_model_version: Literal["1.5.0"] = CONTRACT_VERSION

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


ScenarioPayload = FinanceScenarioInput | CashFlowScenarioInput


class ScenarioRevision(ContractModel):
    revision_id: Identifier
    revision_number: Annotated[int, Field(ge=1)]
    created_at: datetime
    model_id: Literal["catalyst-finance.screening", "catalyst-finance.cash-flow"] = (
        MODEL_ID
    )
    model_version: Literal["1.5.0"] = CONTRACT_VERSION
    change_note: str = Field(default="", max_length=1000)
    scenario: ScenarioPayload


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


class ComparisonRevision(ContractModel):
    revision_id: Identifier
    revision_number: Annotated[int, Field(ge=1)]
    created_at: datetime
    change_note: str = Field(default="", max_length=1000)
    definition: ComparisonDefinition


class WorkspaceComparison(ContractModel):
    comparison_id: Identifier
    name: str = Field(min_length=1, max_length=240)
    status: Literal["draft", "active", "archived"] = "active"
    created_at: datetime
    updated_at: datetime
    current_revision_id: Identifier
    revisions: list[ComparisonRevision] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_revision_chain(self) -> WorkspaceComparison:
        revision_ids = [item.revision_id for item in self.revisions]
        if len(revision_ids) != len(set(revision_ids)):
            raise ValueError("comparison revision IDs must be unique")
        if [item.revision_number for item in self.revisions] != list(
            range(1, len(self.revisions) + 1)
        ):
            raise ValueError(
                "comparison revision numbers must be contiguous and ordered"
            )
        if self.current_revision_id != self.revisions[-1].revision_id:
            raise ValueError(
                "comparison current_revision_id must reference the latest revision"
            )
        return self

    @property
    def current_revision(self) -> ComparisonRevision:
        return self.revisions[-1]


class UncertaintyRevision(ContractModel):
    revision_id: Identifier
    revision_number: Annotated[int, Field(ge=1)]
    created_at: datetime
    change_note: str = Field(default="", max_length=1000)
    definition: UncertaintyDefinition


class WorkspaceUncertaintyAnalysis(ContractModel):
    analysis_id: Identifier
    name: str = Field(min_length=1, max_length=240)
    status: Literal["draft", "active", "archived"] = "active"
    created_at: datetime
    updated_at: datetime
    current_revision_id: Identifier
    revisions: list[UncertaintyRevision] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_revision_chain(self) -> WorkspaceUncertaintyAnalysis:
        revision_ids = [item.revision_id for item in self.revisions]
        if len(revision_ids) != len(set(revision_ids)):
            raise ValueError("uncertainty revision IDs must be unique")
        if [item.revision_number for item in self.revisions] != list(
            range(1, len(self.revisions) + 1)
        ):
            raise ValueError(
                "uncertainty revision numbers must be contiguous and ordered"
            )
        if self.current_revision_id != self.revisions[-1].revision_id:
            raise ValueError(
                "uncertainty current_revision_id must reference the latest revision"
            )
        return self

    @property
    def current_revision(self) -> UncertaintyRevision:
        return self.revisions[-1]


class FinanceWorkspace(ContractModel):
    workspace_contract_version: Literal["1.5.0"] = WORKSPACE_CONTRACT_VERSION
    workspace_id: Identifier
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    status: Literal["active", "archived"] = "active"
    defaults: WorkspaceDefaults = Field(default_factory=WorkspaceDefaults)
    created_at: datetime
    updated_at: datetime
    projects: list[WorkspaceProject] = Field(default_factory=list)
    scenarios: list[WorkspaceScenario] = Field(default_factory=list)
    comparisons: list[WorkspaceComparison] = Field(default_factory=list)
    uncertainty_analyses: list[WorkspaceUncertaintyAnalysis] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def unique_identifiers(self) -> FinanceWorkspace:
        project_ids = [item.project_id for item in self.projects]
        scenario_ids = [item.scenario_id for item in self.scenarios]
        comparison_ids = [item.comparison_id for item in self.comparisons]
        analysis_ids = [item.analysis_id for item in self.uncertainty_analyses]
        if len(project_ids) != len(set(project_ids)):
            raise ValueError("workspace project IDs must be unique")
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("workspace scenario IDs must be unique")
        if len(comparison_ids) != len(set(comparison_ids)):
            raise ValueError("workspace comparison IDs must be unique")
        if len(analysis_ids) != len(set(analysis_ids)):
            raise ValueError("workspace uncertainty analysis IDs must be unique")
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
    export_contract_version: Literal["1.5.0"] = WORKSPACE_CONTRACT_VERSION
    exported_at: datetime
    workspace: FinanceWorkspace


class ScenarioTemplate(ContractModel):
    template_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1000)
    category: str = Field(min_length=1, max_length=120)
    scenario: ScenarioPayload
