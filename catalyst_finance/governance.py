"""Canonical evidence, review, governance, and publication engine."""

from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime, timezone
from typing import Any, cast

from .governance_models import (
    AuditEntry,
    GovernanceDefinition,
    GovernanceMetadata,
    GovernanceMethodology,
    GovernancePublication,
    HandoffRecord,
    ImmutableRunRecord,
    ReadinessSummary,
    TraceRecord,
)

DISCLAIMER = (
    "Decision-support publication only. Institutional owners remain responsible for "
    "source rights, accounting treatment, assurance, approvals, redaction, and final decisions."
)
ISSUE_ACTIONS = {"finding", "object", "revision_required"}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _audit(definition: GovernanceDefinition) -> list[AuditEntry]:
    entries: list[AuditEntry] = []
    previous: str | None = None
    for sequence, event in enumerate(definition.review_events, start=1):
        content = {
            "sequence": sequence,
            "event_id": event.event_id,
            "action": event.action,
            "actor_id": event.reviewer_id,
            "subject_id": event.subject_id,
            "created_at": event.created_at,
            "previous_hash": previous,
        }
        digest = _hash(content)
        entries.append(AuditEntry(**content, entry_hash=digest))
        previous = digest
    return entries


def _redacted(definition: GovernanceDefinition) -> dict[str, Any]:
    data = cast(dict[str, Any], definition.model_dump(mode="json"))
    if definition.publication.redaction_policy == "none":
        return data
    private_source_ids = {item.source_id for item in definition.sources if item.private}
    private_evidence_ids = {
        item.evidence_id
        for item in definition.evidence
        if item.private or item.source_id in private_source_ids
    }
    private_assumption_ids = {
        item.assumption_id for item in definition.assumptions if item.private
    }
    data["sources"] = [item for item in data["sources"] if not item["private"]]
    data["evidence"] = [
        item
        for item in data["evidence"]
        if not item["private"] and item["source_id"] not in private_source_ids
    ]
    data["assumptions"] = [item for item in data["assumptions"] if not item["private"]]
    data["claims"] = [
        item
        for item in data["claims"]
        if item["public"]
        and not set(item["source_ids"]).intersection(private_source_ids)
        and not set(item["evidence_ids"]).intersection(private_evidence_ids)
        and not set(item["assumption_ids"]).intersection(private_assumption_ids)
    ]
    data["review_events"] = [
        item for item in data["review_events"] if not item["private"]
    ]
    data["attachments"] = [item for item in data["attachments"] if not item["private"]]
    return data


def _trace(definition: GovernanceDefinition) -> list[TraceRecord]:
    output: list[TraceRecord] = []
    for claim in definition.claims:
        has_metric = bool(claim.metric_paths or claim.calculation_ids)
        has_assumption = bool(claim.assumption_ids)
        has_evidence = bool(claim.evidence_ids and claim.source_ids)
        complete = has_evidence and (
            claim.classification == "limitation" or (has_metric and has_assumption)
        )
        output.append(
            TraceRecord(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                classification=claim.classification,
                metric_paths=list(claim.metric_paths),
                calculation_ids=list(claim.calculation_ids),
                assumption_ids=list(claim.assumption_ids),
                source_ids=list(claim.source_ids),
                evidence_ids=list(claim.evidence_ids),
                complete=complete,
            )
        )
    return output


def _brief(
    definition: GovernanceDefinition, readiness: ReadinessSummary
) -> tuple[str, str]:
    metrics = (
        "\n".join(
            f"- **{key}**: {value}"
            for key, value in definition.artifact.headline_metrics.items()
        )
        or "- No headline metrics supplied."
    )
    claims = (
        "\n".join(
            f"- {item.text}"
            for item in definition.claims
            if item.classification == "headline" and item.public
        )
        or "- No public headline claims supplied."
    )
    limitations = [
        text
        for methodology in definition.methodologies
        for text in methodology.limitations
    ]
    limitations_text = (
        "\n".join(f"- {item}" for item in limitations) or "- None declared."
    )
    markdown = (
        f"# {definition.publication.title}\n\n"
        f"{definition.publication.summary}\n\n"
        f"## Governed artifact\n\n"
        f"- Artifact: `{definition.artifact.artifact_id}`\n"
        f"- Revision: `{definition.artifact.revision_id}`\n"
        f"- Model: `{definition.artifact.model_id}` v{definition.artifact.model_version}\n"
        f"- Publication state: `{definition.publication.state}`\n"
        f"- Review readiness: `{readiness.status}`\n\n"
        f"## Headline metrics\n\n{metrics}\n\n"
        f"## Reviewed claims\n\n{claims}\n\n"
        f"## Limitations\n\n{limitations_text}\n\n"
        f"## Traceability\n\n"
        f"{readiness.fully_traced_headline_count} of {readiness.headline_claim_count} "
        "headline claims have complete metric, assumption, source, and evidence links.\n"
    )
    escaped = html.escape(markdown)
    body = escaped.replace("\n", "<br>\n")
    html_doc = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(definition.publication.title)}</title></head>"
        f"<body><main>{body}</main></body></html>"
    )
    return markdown, html_doc


def evaluate_governance(
    definition: GovernanceDefinition, *, generated_at: str | None = None
) -> GovernancePublication:
    trace = _trace(definition)
    resolved = {
        event.resolves_event_id
        for event in definition.review_events
        if event.action == "resolve" and event.resolves_event_id is not None
    }
    unresolved = [
        event
        for event in definition.review_events
        if event.action in ISSUE_ACTIONS and event.event_id not in resolved
    ]
    approvals = {
        event.reviewer_id
        for event in definition.review_events
        if event.action == "approve"
    }
    verified_sources = sum(
        item.review_status == "verified" for item in definition.sources
    )
    headline = [item for item in trace if item.classification == "headline"]
    fully_traced = sum(item.complete for item in trace)
    fully_traced_headline = sum(item.complete for item in headline)
    private_count = (
        sum(item.private for item in definition.sources)
        + sum(item.private for item in definition.evidence)
        + sum(item.private for item in definition.assumptions)
        + sum(not item.public for item in definition.claims)
        + sum(item.private for item in definition.review_events)
        + sum(item.private for item in definition.attachments)
    )
    evidence_ready = bool(
        definition.sources and definition.evidence and definition.claims
    )
    traces_ready = fully_traced_headline == len(headline) and bool(headline)
    publication_allowed = (
        evidence_ready and traces_ready and not unresolved and bool(approvals)
    )
    state = definition.publication.state
    if state == "published" and publication_allowed:
        status = "published"
    elif state in {"approved", "published"} and publication_allowed:
        status = "approved"
    elif evidence_ready and traces_ready and not unresolved:
        status = "ready_for_review"
    else:
        status = "blocked"
    readiness = ReadinessSummary(
        status=status,
        source_count=len(definition.sources),
        verified_source_count=verified_sources,
        evidence_count=len(definition.evidence),
        claim_count=len(definition.claims),
        fully_traced_claim_count=fully_traced,
        headline_claim_count=len(headline),
        fully_traced_headline_count=fully_traced_headline,
        approval_count=len(approvals),
        unresolved_issue_count=len(unresolved),
        private_record_count=private_count,
        publication_allowed=publication_allowed,
    )
    public_payload = _redacted(definition)
    audit = _audit(definition)
    timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    brief_md, brief_html = _brief(definition, readiness)
    run_id = f"run_{_hash({'definition': definition.model_dump(mode='json'), 'at': timestamp})[:24]}"
    audit_head = audit[-1].entry_hash if audit else None
    handoffs: list[HandoffRecord] = []
    if definition.publication.knowledge_library_collection_id is not None:
        handoffs.append(
            HandoffRecord(
                target="knowledge_library",
                handoff_id=f"handoff_kl_{definition.governance_id}",
                source_governance_id=definition.governance_id,
                artifact_id=definition.artifact.artifact_id,
                artifact_revision_id=definition.artifact.revision_id,
                evidence_ids=[
                    item.evidence_id for item in definition.evidence if not item.private
                ],
                review_event_ids=[
                    item.event_id
                    for item in definition.review_events
                    if not item.private
                ],
                methodology_ids=[
                    item.methodology_id for item in definition.methodologies
                ],
                destination_id=definition.publication.knowledge_library_collection_id,
                audience=definition.publication.audience,
            )
        )
    if definition.publication.decision_studio_packet_id is not None:
        handoffs.append(
            HandoffRecord(
                target="decision_studio",
                handoff_id=f"handoff_ds_{definition.governance_id}",
                source_governance_id=definition.governance_id,
                artifact_id=definition.artifact.artifact_id,
                artifact_revision_id=definition.artifact.revision_id,
                evidence_ids=[item.evidence_id for item in definition.evidence],
                review_event_ids=[item.event_id for item in definition.review_events],
                methodology_ids=[
                    item.methodology_id for item in definition.methodologies
                ],
                destination_id=definition.publication.decision_studio_packet_id,
                audience="internal",
            )
        )
    flags = [
        "Review events are append-only and represented by a SHA-256 hash chain.",
        "Public exports exclude records marked private and claims dependent on private records.",
    ]
    if unresolved:
        flags.append(
            "Unresolved findings, objections, or revision requirements block publication."
        )
    if fully_traced_headline < len(headline):
        flags.append(
            "At least one headline claim lacks complete metric-to-evidence traceability."
        )
    if (
        definition.publication.state in {"approved", "published"}
        and not publication_allowed
    ):
        flags.append(
            "The requested publication state is not supported by the current review record."
        )
    return GovernancePublication(
        definition=definition,
        readiness=readiness,
        trace_matrix=trace,
        audit_history=audit,
        run_record=ImmutableRunRecord(
            run_id=run_id,
            generated_at=timestamp,
            input_hash=_hash(definition.model_dump(mode="json")),
            public_payload_hash=_hash(public_payload),
            audit_head_hash=audit_head,
            artifact_id=definition.artifact.artifact_id,
            artifact_revision_id=definition.artifact.revision_id,
            model_id=definition.artifact.model_id,
            model_version=definition.artifact.model_version,
        ),
        public_payload=public_payload,
        decision_brief_markdown=brief_md,
        decision_brief_html=brief_html,
        handoffs=handoffs,
        flags=flags,
        methodology=GovernanceMethodology(),
        metadata=GovernanceMetadata(generated_at=timestamp, disclaimer=DISCLAIMER),
    )
