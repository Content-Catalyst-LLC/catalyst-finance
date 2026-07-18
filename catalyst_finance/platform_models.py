"""Connected financial decision-intelligence platform contracts for v2.0.0."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from .comparison_models import SourceRevision
from .models import ContractModel

PLATFORM_CONTRACT_VERSION: Literal["2.0.0"] = "2.0.0"
PLATFORM_MODEL_ID: Literal["catalyst-finance.platform"] = "catalyst-finance.platform"

Identifier = Annotated[
    str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
]
Money = Annotated[float, Field(allow_inf_nan=False)]
Percentage = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
Classification = Literal["public", "internal", "confidential", "restricted"]
ProductStatus = Literal["online", "degraded", "offline"]
ArtifactStatus = Literal["draft", "in_review", "approved", "published", "withdrawn"]
GovernanceStatus = Literal["blocked", "ready_for_review", "approved", "published"]
HandoffStatus = Literal["queued", "accepted", "rejected", "completed", "failed"]


class ConnectedProduct(ContractModel):
    product_id: Identifier
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=80)
    role: Literal[
        "finance",
        "decision",
        "knowledge",
        "compute",
        "data",
        "intelligence",
        "research",
        "design",
        "support",
    ]
    status: ProductStatus = "online"
    artifact_kinds: list[str] = Field(default_factory=list, max_length=100)
    supported_contracts: list[str] = Field(default_factory=list, max_length=100)
    accepted_classifications: list[Classification] = Field(
        default_factory=lambda: ["public", "internal"], min_length=1
    )
    api_base: str | None = Field(default=None, max_length=500)


class ArtifactFinancialSummary(ContractModel):
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    base_npv: Money = 0
    adjusted_npv: Money = 0
    capital_required: Annotated[float, Field(ge=0, allow_inf_nan=False)] = 0
    annual_value: Money = 0
    confidence_percent: Percentage = 100
    downside_probability_percent: Percentage = 0


class PlatformArtifact(ContractModel):
    artifact_id: Identifier
    revision_id: Identifier
    source_product_id: Identifier
    model_id: Identifier
    model_version: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=240)
    artifact_kind: str = Field(min_length=1, max_length=120)
    status: ArtifactStatus
    governance_status: GovernanceStatus
    classification: Classification = "internal"
    include_in_portfolio: bool = True
    checksum_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    financial: ArtifactFinancialSummary = Field(
        default_factory=ArtifactFinancialSummary
    )
    headline_metrics: dict[str, float | int | str | None] = Field(
        default_factory=dict, max_length=100
    )
    source_uri: str | None = Field(default=None, max_length=1000)


class DecisionCase(ContractModel):
    case_id: Identifier
    name: str = Field(min_length=1, max_length=240)
    objective: str = Field(min_length=1, max_length=2000)
    owner: str = Field(min_length=1, max_length=200)
    status: Literal["draft", "active", "in_review", "decided", "archived"] = "active"
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    artifact_ids: list[Identifier] = Field(min_length=1, max_length=100)
    required_product_ids: list[Identifier] = Field(default_factory=list, max_length=50)
    decision_packet_id: Identifier | None = None
    knowledge_collection_id: Identifier | None = None


class DependencyEdge(ContractModel):
    edge_id: Identifier
    upstream_artifact_id: Identifier
    downstream_artifact_id: Identifier
    relationship: Literal[
        "informs", "depends_on", "evidence_for", "calculation_for", "supersedes"
    ]
    required: bool = True
    note: str = Field(default="", max_length=1000)


class HandoffEnvelope(ContractModel):
    handoff_id: Identifier
    source_product_id: Identifier
    target_product_id: Identifier
    artifact_id: Identifier
    artifact_revision_id: Identifier
    contract_id: str = Field(min_length=1, max_length=200)
    classification: Classification
    status: HandoffStatus = "queued"
    payload_hash_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    requested_at: str = Field(min_length=1, max_length=80)
    updated_at: str = Field(min_length=1, max_length=80)
    destination_id: Identifier | None = None
    error_code: str | None = Field(default=None, max_length=120)
    note: str = Field(default="", max_length=2000)


class PlatformPolicy(ContractModel):
    require_governance_for_completed_handoffs: bool = True
    require_approved_artifact_for_completed_handoffs: bool = True
    require_checksums: bool = True
    minimum_case_confidence_percent: Percentage = 70
    allowed_public_statuses: list[ArtifactStatus] = Field(
        default_factory=lambda: ["approved", "published"], min_length=1
    )


class PlatformDefinition(ContractModel):
    contract_version: Literal["2.0.0"] = PLATFORM_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.platform"] = PLATFORM_MODEL_ID
    platform_id: Identifier
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    source: SourceRevision
    products: list[ConnectedProduct] = Field(min_length=2, max_length=100)
    artifacts: list[PlatformArtifact] = Field(min_length=1, max_length=1000)
    cases: list[DecisionCase] = Field(min_length=1, max_length=500)
    dependencies: list[DependencyEdge] = Field(default_factory=list, max_length=5000)
    handoffs: list[HandoffEnvelope] = Field(default_factory=list, max_length=5000)
    policy: PlatformPolicy = Field(default_factory=PlatformPolicy)

    @model_validator(mode="after")
    def validate_graph_and_references(self) -> PlatformDefinition:
        product_ids = [item.product_id for item in self.products]
        artifact_ids = [item.artifact_id for item in self.artifacts]
        case_ids = [item.case_id for item in self.cases]
        edge_ids = [item.edge_id for item in self.dependencies]
        handoff_ids = [item.handoff_id for item in self.handoffs]
        for label, values in (
            ("product", product_ids),
            ("artifact", artifact_ids),
            ("case", case_ids),
            ("dependency", edge_ids),
            ("handoff", handoff_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        products = {item.product_id: item for item in self.products}
        artifacts = {item.artifact_id: item for item in self.artifacts}
        if not any(item.include_in_portfolio for item in self.artifacts):
            raise ValueError(
                "at least one artifact must be included in portfolio aggregation"
            )
        for artifact in self.artifacts:
            if artifact.source_product_id not in products:
                raise ValueError(
                    f"artifact {artifact.artifact_id} references unknown source product"
                )
        for case in self.cases:
            if not set(case.artifact_ids).issubset(artifacts):
                raise ValueError(f"case {case.case_id} references unknown artifact")
            if not set(case.required_product_ids).issubset(products):
                raise ValueError(f"case {case.case_id} references unknown product")
        for edge in self.dependencies:
            if edge.upstream_artifact_id not in artifacts:
                raise ValueError(f"dependency {edge.edge_id} has unknown upstream")
            if edge.downstream_artifact_id not in artifacts:
                raise ValueError(f"dependency {edge.edge_id} has unknown downstream")
            if edge.upstream_artifact_id == edge.downstream_artifact_id:
                raise ValueError("dependency edges cannot be self-referential")
        self._validate_acyclic(artifact_ids)
        for handoff in self.handoffs:
            if handoff.source_product_id not in products:
                raise ValueError(f"handoff {handoff.handoff_id} has unknown source")
            if handoff.target_product_id not in products:
                raise ValueError(f"handoff {handoff.handoff_id} has unknown target")
            handoff_artifact = artifacts.get(handoff.artifact_id)
            if handoff_artifact is None:
                raise ValueError(f"handoff {handoff.handoff_id} has unknown artifact")
            if handoff_artifact.revision_id != handoff.artifact_revision_id:
                raise ValueError(
                    f"handoff {handoff.handoff_id} revision does not match artifact"
                )
            if handoff_artifact.source_product_id != handoff.source_product_id:
                raise ValueError(
                    f"handoff {handoff.handoff_id} source does not own artifact"
                )
            if handoff.status in {"accepted", "completed"}:
                target = products[handoff.target_product_id]
                if handoff.classification not in target.accepted_classifications:
                    raise ValueError(
                        f"handoff {handoff.handoff_id} classification is not accepted"
                    )
            if handoff.status == "completed":
                if (
                    self.policy.require_approved_artifact_for_completed_handoffs
                    and handoff_artifact.status not in {"approved", "published"}
                ):
                    raise ValueError(
                        f"completed handoff {handoff.handoff_id} requires approved artifact"
                    )
                if (
                    self.policy.require_governance_for_completed_handoffs
                    and handoff_artifact.governance_status
                    not in {"approved", "published"}
                ):
                    raise ValueError(
                        f"completed handoff {handoff.handoff_id} requires governance approval"
                    )
        return self

    def _validate_acyclic(self, artifact_ids: list[str]) -> None:
        graph: dict[str, list[str]] = {item: [] for item in artifact_ids}
        indegree = {item: 0 for item in artifact_ids}
        for edge in self.dependencies:
            graph[edge.upstream_artifact_id].append(edge.downstream_artifact_id)
            indegree[edge.downstream_artifact_id] += 1
        queue = sorted(item for item, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            for target in sorted(graph[node]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
                    queue.sort()
        if visited != len(artifact_ids):
            raise ValueError("platform dependency graph must be acyclic")


class PortfolioSummary(ContractModel):
    artifact_count: int
    case_count: int
    currency: str
    total_base_npv: Money
    total_adjusted_npv: Money
    total_capital_required: Money
    total_annual_value: Money
    risk_adjusted_value: Money
    value_to_capital_ratio: float | None
    weighted_confidence_percent: Percentage
    weighted_downside_probability_percent: Percentage


class ProductHealth(ContractModel):
    product_id: str
    status: Literal["healthy", "warning", "blocked"]
    artifact_count: int
    inbound_handoff_count: int
    outbound_handoff_count: int
    completed_handoff_count: int
    failed_or_rejected_handoff_count: int


class CaseAssessment(ContractModel):
    case_id: str
    name: str
    status: Literal["blocked", "ready_for_review", "decision_ready", "decided"]
    readiness_score: Percentage
    artifact_count: int
    approved_artifact_count: int
    governance_ready_artifact_count: int
    completed_handoff_count: int
    required_handoff_count: int
    risk_adjusted_value: Money
    blocked_reasons: list[str]


class HandoffSummary(ContractModel):
    total: int
    queued: int
    accepted: int
    completed: int
    rejected: int
    failed: int
    noncompliant_handoff_ids: list[str]


class PlatformMethodology(ContractModel):
    model_id: Literal["catalyst-finance.platform"] = PLATFORM_MODEL_ID
    model_version: Literal["2.0.0"] = PLATFORM_CONTRACT_VERSION
    aggregation_policy: Literal["artifact_level_no_cross_case_deduplication"] = (
        "artifact_level_no_cross_case_deduplication"
    )
    risk_adjustment_policy: Literal["adjusted_npv_x_confidence_x_inverse_downside"] = (
        "adjusted_npv_x_confidence_x_inverse_downside"
    )
    graph_policy: Literal["acyclic_required_dependencies"] = (
        "acyclic_required_dependencies"
    )
    handoff_policy: Literal["classification_and_governance_gated"] = (
        "classification_and_governance_gated"
    )


class PlatformRunRecord(ContractModel):
    run_id: str
    generated_at: str
    input_hash: str
    output_hash: str
    dependency_head: str | None
    platform_id: str


class PlatformMetadata(ContractModel):
    generated_at: str
    version: Literal["2.0.0"] = PLATFORM_CONTRACT_VERSION
    disclaimer: str


class PlatformPublication(ContractModel):
    contract_version: Literal["2.0.0"] = PLATFORM_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.platform"] = PLATFORM_MODEL_ID
    platform_id: str
    name: str
    source: SourceRevision
    portfolio: PortfolioSummary
    product_health: list[ProductHealth]
    case_assessments: list[CaseAssessment]
    handoffs: HandoffSummary
    dependency_order: list[str]
    integration_manifest: dict[str, Any]
    flags: list[str]
    methodology: PlatformMethodology
    run_record: PlatformRunRecord
    metadata: PlatformMetadata
