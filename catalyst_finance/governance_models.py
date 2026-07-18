"""Evidence, review, governance, and publication contracts for v2.0.0."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, HttpUrl, model_validator

from .comparison_models import SourceRevision
from .models import ContractModel

GOVERNANCE_CONTRACT_VERSION: Literal["2.0.0"] = "2.0.0"
GOVERNANCE_MODEL_ID: Literal["catalyst-finance.governance"] = (
    "catalyst-finance.governance"
)
Percentage = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
IdentifierText = Annotated[
    str, Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.:-]+$")
]
ReviewStatus = Literal["draft", "in_review", "verified", "rejected"]
PublicationState = Literal["draft", "in_review", "approved", "published", "withdrawn"]
Audience = Literal["private", "internal", "public"]


class GovernedArtifactReference(ContractModel):
    artifact_id: IdentifierText
    model_id: IdentifierText
    model_version: str = Field(min_length=1, max_length=40)
    revision_id: IdentifierText
    title: str = Field(min_length=1, max_length=240)
    headline_metrics: dict[str, float | int | str | None] = Field(
        default_factory=dict, max_length=100
    )


class SourceRecord(ContractModel):
    source_id: IdentifierText
    title: str = Field(min_length=1, max_length=300)
    source_type: Literal[
        "document", "dataset", "interview", "model", "policy", "website", "other"
    ]
    citation: str = Field(min_length=1, max_length=2000)
    url: HttpUrl | None = None
    published_date: str | None = Field(default=None, max_length=40)
    accessed_date: str | None = Field(default=None, max_length=40)
    owner: str = Field(min_length=1, max_length=200)
    confidence_percent: Percentage = 100
    applicability: str = Field(min_length=1, max_length=2000)
    review_status: ReviewStatus = "draft"
    private: bool = False
    attachment_ids: list[IdentifierText] = Field(default_factory=list, max_length=50)
    notes: str = Field(default="", max_length=4000)


class EvidenceRecord(ContractModel):
    evidence_id: IdentifierText
    source_id: IdentifierText
    evidence_type: Literal[
        "quantitative", "qualitative", "methodology", "assurance", "limitation"
    ]
    summary: str = Field(min_length=1, max_length=4000)
    locator: str = Field(min_length=1, max_length=500)
    confidence_percent: Percentage = 100
    private: bool = False


class AssumptionRecord(ContractModel):
    assumption_id: IdentifierText
    label: str = Field(min_length=1, max_length=240)
    value: str = Field(min_length=1, max_length=1000)
    unit: str | None = Field(default=None, max_length=100)
    owner: str = Field(min_length=1, max_length=200)
    confidence_percent: Percentage = 100
    applicability: str = Field(min_length=1, max_length=2000)
    review_status: ReviewStatus = "draft"
    source_ids: list[IdentifierText] = Field(default_factory=list, max_length=50)
    evidence_ids: list[IdentifierText] = Field(default_factory=list, max_length=50)
    private: bool = False
    rationale: str = Field(default="", max_length=4000)


class ClaimRecord(ContractModel):
    claim_id: IdentifierText
    text: str = Field(min_length=1, max_length=3000)
    classification: Literal["headline", "supporting", "limitation"] = "supporting"
    metric_paths: list[str] = Field(default_factory=list, max_length=50)
    calculation_ids: list[IdentifierText] = Field(default_factory=list, max_length=50)
    assumption_ids: list[IdentifierText] = Field(default_factory=list, max_length=50)
    source_ids: list[IdentifierText] = Field(default_factory=list, max_length=50)
    evidence_ids: list[IdentifierText] = Field(default_factory=list, max_length=50)
    review_status: ReviewStatus = "draft"
    public: bool = True


class MethodologyDeclaration(ContractModel):
    methodology_id: IdentifierText
    name: str = Field(min_length=1, max_length=240)
    version: str = Field(min_length=1, max_length=80)
    purpose: str = Field(min_length=1, max_length=3000)
    model_ids: list[IdentifierText] = Field(min_length=1, max_length=50)
    data_quality_notes: list[str] = Field(default_factory=list, max_length=100)
    conflicts: list[str] = Field(default_factory=list, max_length=100)
    limitations: list[str] = Field(default_factory=list, max_length=100)
    excluded_factors: list[str] = Field(default_factory=list, max_length=100)


class ReviewEvent(ContractModel):
    event_id: IdentifierText
    reviewer_id: IdentifierText
    reviewer_name: str = Field(min_length=1, max_length=200)
    role: Literal["author", "analyst", "reviewer", "approver", "auditor", "publisher"]
    action: Literal[
        "request",
        "comment",
        "finding",
        "approve",
        "object",
        "revision_required",
        "resolve",
        "publish",
        "withdraw",
    ]
    subject_id: IdentifierText
    created_at: str = Field(min_length=1, max_length=80)
    comment: str = Field(default="", max_length=4000)
    resolves_event_id: IdentifierText | None = None
    private: bool = False


class AttachmentRecord(ContractModel):
    attachment_id: IdentifierText
    filename: str = Field(min_length=1, max_length=300)
    media_type: str = Field(min_length=1, max_length=120)
    checksum_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    owner: str = Field(min_length=1, max_length=200)
    private: bool = True
    retention_note: str = Field(default="", max_length=1000)


class PublicationControls(ContractModel):
    state: PublicationState = "draft"
    audience: Audience = "private"
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(min_length=1, max_length=4000)
    redaction_policy: Literal["exclude_private", "none"] = "exclude_private"
    knowledge_library_collection_id: IdentifierText | None = None
    decision_studio_packet_id: IdentifierText | None = None

    @model_validator(mode="after")
    def public_requires_redaction(self) -> PublicationControls:
        if self.audience == "public" and self.redaction_policy != "exclude_private":
            raise ValueError("public publications must exclude private records")
        return self


class GovernanceDefinition(ContractModel):
    contract_version: Literal["2.0.0"] = GOVERNANCE_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.governance"] = GOVERNANCE_MODEL_ID
    governance_id: IdentifierText
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    source: SourceRevision
    artifact: GovernedArtifactReference
    assumptions: list[AssumptionRecord] = Field(default_factory=list, max_length=500)
    sources: list[SourceRecord] = Field(default_factory=list, max_length=500)
    evidence: list[EvidenceRecord] = Field(default_factory=list, max_length=1000)
    claims: list[ClaimRecord] = Field(default_factory=list, max_length=500)
    methodologies: list[MethodologyDeclaration] = Field(
        default_factory=list, max_length=100
    )
    review_events: list[ReviewEvent] = Field(default_factory=list, max_length=2000)
    attachments: list[AttachmentRecord] = Field(default_factory=list, max_length=200)
    publication: PublicationControls

    @model_validator(mode="after")
    def validate_references(self) -> GovernanceDefinition:
        groups = {
            "source": [item.source_id for item in self.sources],
            "evidence": [item.evidence_id for item in self.evidence],
            "assumption": [item.assumption_id for item in self.assumptions],
            "claim": [item.claim_id for item in self.claims],
            "methodology": [item.methodology_id for item in self.methodologies],
            "review event": [item.event_id for item in self.review_events],
            "attachment": [item.attachment_id for item in self.attachments],
        }
        for label, values in groups.items():
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        source_ids = set(groups["source"])
        evidence_ids = set(groups["evidence"])
        assumption_ids = set(groups["assumption"])
        attachment_ids = set(groups["attachment"])
        event_ids = set(groups["review event"])
        for source in self.sources:
            if not set(source.attachment_ids).issubset(attachment_ids):
                raise ValueError(
                    f"source {source.source_id} references unknown attachment"
                )
        for item in self.evidence:
            if item.source_id not in source_ids:
                raise ValueError(
                    f"evidence {item.evidence_id} references unknown source"
                )
        for item in self.assumptions:
            if not set(item.source_ids).issubset(source_ids):
                raise ValueError(
                    f"assumption {item.assumption_id} references unknown source"
                )
            if not set(item.evidence_ids).issubset(evidence_ids):
                raise ValueError(
                    f"assumption {item.assumption_id} references unknown evidence"
                )
        for claim in self.claims:
            if not set(claim.source_ids).issubset(source_ids):
                raise ValueError(f"claim {claim.claim_id} references unknown source")
            if not set(claim.evidence_ids).issubset(evidence_ids):
                raise ValueError(f"claim {claim.claim_id} references unknown evidence")
            if not set(claim.assumption_ids).issubset(assumption_ids):
                raise ValueError(
                    f"claim {claim.claim_id} references unknown assumption"
                )
            if claim.classification == "headline" and not claim.metric_paths:
                raise ValueError("headline claims require at least one metric path")
        for event in self.review_events:
            if (
                event.resolves_event_id is not None
                and event.resolves_event_id not in event_ids
            ):
                raise ValueError(
                    f"review event {event.event_id} resolves an unknown event"
                )
            if event.resolves_event_id == event.event_id:
                raise ValueError("a review event cannot resolve itself")
        return self


class TraceRecord(ContractModel):
    claim_id: str
    claim_text: str
    classification: str
    metric_paths: list[str]
    calculation_ids: list[str]
    assumption_ids: list[str]
    source_ids: list[str]
    evidence_ids: list[str]
    complete: bool


class ReadinessSummary(ContractModel):
    status: Literal["blocked", "ready_for_review", "approved", "published"]
    source_count: int
    verified_source_count: int
    evidence_count: int
    claim_count: int
    fully_traced_claim_count: int
    headline_claim_count: int
    fully_traced_headline_count: int
    approval_count: int
    unresolved_issue_count: int
    private_record_count: int
    publication_allowed: bool


class AuditEntry(ContractModel):
    sequence: int
    event_id: str
    action: str
    actor_id: str
    subject_id: str
    created_at: str
    previous_hash: str | None
    entry_hash: str


class ImmutableRunRecord(ContractModel):
    run_id: str
    generated_at: str
    input_hash: str
    public_payload_hash: str
    audit_head_hash: str | None
    artifact_id: str
    artifact_revision_id: str
    model_id: str
    model_version: str


class HandoffRecord(ContractModel):
    target: Literal["knowledge_library", "decision_studio"]
    contract_version: Literal["2.0.0"] = GOVERNANCE_CONTRACT_VERSION
    handoff_id: str
    source_governance_id: str
    artifact_id: str
    artifact_revision_id: str
    evidence_ids: list[str]
    review_event_ids: list[str]
    methodology_ids: list[str]
    destination_id: str | None
    audience: Audience


class GovernanceMethodology(ContractModel):
    model_id: Literal["catalyst-finance.governance"] = GOVERNANCE_MODEL_ID
    model_version: Literal["2.0.0"] = GOVERNANCE_CONTRACT_VERSION
    trace_policy: Literal["headline_metric_to_assumption_and_evidence"] = (
        "headline_metric_to_assumption_and_evidence"
    )
    review_policy: Literal["append_only_events_and_unresolved_issue_gate"] = (
        "append_only_events_and_unresolved_issue_gate"
    )
    redaction_policy: Literal["private_records_excluded_from_public_payload"] = (
        "private_records_excluded_from_public_payload"
    )
    audit_policy: Literal["sha256_hash_chained_events"] = "sha256_hash_chained_events"


class GovernanceMetadata(ContractModel):
    generated_at: str
    version: Literal["2.0.0"] = GOVERNANCE_CONTRACT_VERSION
    disclaimer: str


class GovernancePublication(ContractModel):
    contract_version: Literal["2.0.0"] = GOVERNANCE_CONTRACT_VERSION
    model_id: Literal["catalyst-finance.governance"] = GOVERNANCE_MODEL_ID
    definition: GovernanceDefinition
    readiness: ReadinessSummary
    trace_matrix: list[TraceRecord]
    audit_history: list[AuditEntry]
    run_record: ImmutableRunRecord
    public_payload: dict[str, Any]
    decision_brief_markdown: str
    decision_brief_html: str
    handoffs: list[HandoffRecord]
    flags: list[str] = Field(min_length=1)
    methodology: GovernanceMethodology
    metadata: GovernanceMetadata
