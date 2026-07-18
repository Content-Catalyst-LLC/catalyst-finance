"""Connected platform evaluation for Catalyst Finance v2.0.0."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .platform_models import (
    CaseAssessment,
    HandoffSummary,
    PlatformDefinition,
    PlatformMetadata,
    PlatformMethodology,
    PlatformPublication,
    PlatformRunRecord,
    PortfolioSummary,
    ProductHealth,
)

DISCLAIMER = (
    "Connected decision-support publication only. Institutional owners remain "
    "responsible for source systems, access control, accounting treatment, "
    "assurance, approvals, and final decisions."
)


def _json_compatible(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_compatible(item) for item in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _canonical(value: Any) -> str:
    return json.dumps(
        _json_compatible(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _dependency_order(definition: PlatformDefinition) -> list[str]:
    nodes = sorted(item.artifact_id for item in definition.artifacts)
    graph: dict[str, list[str]] = {item: [] for item in nodes}
    indegree = {item: 0 for item in nodes}
    for edge in definition.dependencies:
        graph[edge.upstream_artifact_id].append(edge.downstream_artifact_id)
        indegree[edge.downstream_artifact_id] += 1
    queue = sorted(item for item, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for target in sorted(graph[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
                queue.sort()
    return order


def _portfolio(definition: PlatformDefinition) -> PortfolioSummary:
    all_artifacts = definition.artifacts
    artifacts = [item for item in all_artifacts if item.include_in_portfolio]
    currencies = {item.financial.currency for item in artifacts}
    currency = next(iter(currencies)) if len(currencies) == 1 else "MIXED"
    base = sum(item.financial.base_npv for item in artifacts)
    adjusted = sum(item.financial.adjusted_npv for item in artifacts)
    capital = sum(item.financial.capital_required for item in artifacts)
    annual = sum(item.financial.annual_value for item in artifacts)
    weights = [max(abs(item.financial.adjusted_npv), 1.0) for item in artifacts]
    total_weight = sum(weights)
    confidence = (
        sum(
            weight * item.financial.confidence_percent
            for weight, item in zip(weights, artifacts, strict=True)
        )
        / total_weight
    )
    downside = (
        sum(
            weight * item.financial.downside_probability_percent
            for weight, item in zip(weights, artifacts, strict=True)
        )
        / total_weight
    )
    risk_adjusted = sum(
        item.financial.adjusted_npv
        * (item.financial.confidence_percent / 100)
        * (1 - item.financial.downside_probability_percent / 100)
        for item in artifacts
    )
    return PortfolioSummary(
        artifact_count=len(all_artifacts),
        case_count=len(definition.cases),
        currency=currency,
        total_base_npv=round(base, 2),
        total_adjusted_npv=round(adjusted, 2),
        total_capital_required=round(capital, 2),
        total_annual_value=round(annual, 2),
        risk_adjusted_value=round(risk_adjusted, 2),
        value_to_capital_ratio=(round(adjusted / capital, 4) if capital else None),
        weighted_confidence_percent=round(confidence, 2),
        weighted_downside_probability_percent=round(downside, 2),
    )


def _product_health(definition: PlatformDefinition) -> list[ProductHealth]:
    output: list[ProductHealth] = []
    for product in sorted(definition.products, key=lambda item: item.product_id):
        inbound = [
            item
            for item in definition.handoffs
            if item.target_product_id == product.product_id
        ]
        outbound = [
            item
            for item in definition.handoffs
            if item.source_product_id == product.product_id
        ]
        problematic = sum(
            item.status in {"rejected", "failed"} for item in [*inbound, *outbound]
        )
        if product.status == "offline":
            status = "blocked"
        elif product.status == "degraded" or problematic:
            status = "warning"
        else:
            status = "healthy"
        output.append(
            ProductHealth(
                product_id=product.product_id,
                status=status,
                artifact_count=sum(
                    item.source_product_id == product.product_id
                    for item in definition.artifacts
                ),
                inbound_handoff_count=len(inbound),
                outbound_handoff_count=len(outbound),
                completed_handoff_count=sum(
                    item.status == "completed" for item in [*inbound, *outbound]
                ),
                failed_or_rejected_handoff_count=problematic,
            )
        )
    return output


def _case_assessments(definition: PlatformDefinition) -> list[CaseAssessment]:
    artifacts = {item.artifact_id: item for item in definition.artifacts}
    output: list[CaseAssessment] = []
    for case in definition.cases:
        selected = [artifacts[item] for item in case.artifact_ids]
        value_artifacts = [item for item in selected if item.include_in_portfolio]
        approved = sum(item.status in {"approved", "published"} for item in selected)
        governed = sum(
            item.governance_status in {"approved", "published"} for item in selected
        )
        relevant_handoffs = [
            item
            for item in definition.handoffs
            if item.artifact_id in case.artifact_ids
        ]
        required = [
            item
            for item in relevant_handoffs
            if item.target_product_id in case.required_product_ids
        ]
        completed = sum(item.status == "completed" for item in required)
        dependencies = [
            edge
            for edge in definition.dependencies
            if edge.required and edge.downstream_artifact_id in case.artifact_ids
        ]
        blocked: list[str] = []
        if approved != len(selected):
            blocked.append("One or more case artifacts are not approved or published.")
        if governed != len(selected):
            blocked.append("One or more case artifacts have incomplete governance.")
        if completed != len(required):
            blocked.append("One or more required product handoffs are incomplete.")
        low_confidence = [
            item.artifact_id
            for item in selected
            if item.financial.confidence_percent
            < definition.policy.minimum_case_confidence_percent
        ]
        if low_confidence:
            blocked.append(
                "Case contains artifacts below the minimum confidence policy."
            )
        dependency_ids = {edge.upstream_artifact_id for edge in dependencies}
        if not dependency_ids.issubset(artifacts):
            blocked.append("A required dependency is unavailable.")
        artifact_ratio = approved / len(selected)
        governance_ratio = governed / len(selected)
        handoff_ratio = completed / len(required) if required else 1.0
        confidence_ratio = sum(
            item.financial.confidence_percent for item in selected
        ) / (100 * len(selected))
        score = round(
            100
            * (
                0.3 * artifact_ratio
                + 0.3 * governance_ratio
                + 0.25 * handoff_ratio
                + 0.15 * confidence_ratio
            ),
            2,
        )
        if blocked:
            status = "blocked"
        elif case.status == "decided":
            status = "decided"
        elif score >= 90:
            status = "decision_ready"
        else:
            status = "ready_for_review"
        value = sum(
            item.financial.adjusted_npv
            * (item.financial.confidence_percent / 100)
            * (1 - item.financial.downside_probability_percent / 100)
            for item in value_artifacts
        )
        output.append(
            CaseAssessment(
                case_id=case.case_id,
                name=case.name,
                status=status,
                readiness_score=score,
                artifact_count=len(selected),
                approved_artifact_count=approved,
                governance_ready_artifact_count=governed,
                completed_handoff_count=completed,
                required_handoff_count=len(required),
                risk_adjusted_value=round(value, 2),
                blocked_reasons=blocked,
            )
        )
    return output


def _handoff_summary(definition: PlatformDefinition) -> HandoffSummary:
    products = {item.product_id: item for item in definition.products}
    artifacts = {item.artifact_id: item for item in definition.artifacts}
    noncompliant: list[str] = []
    for handoff in definition.handoffs:
        target = products[handoff.target_product_id]
        artifact = artifacts[handoff.artifact_id]
        if handoff.classification not in target.accepted_classifications:
            noncompliant.append(handoff.handoff_id)
            continue
        if handoff.status == "completed" and artifact.governance_status not in {
            "approved",
            "published",
        }:
            noncompliant.append(handoff.handoff_id)
    counts = {
        status: 0
        for status in ("queued", "accepted", "completed", "rejected", "failed")
    }
    for handoff in definition.handoffs:
        counts[handoff.status] += 1
    return HandoffSummary(
        total=len(definition.handoffs),
        queued=counts["queued"],
        accepted=counts["accepted"],
        completed=counts["completed"],
        rejected=counts["rejected"],
        failed=counts["failed"],
        noncompliant_handoff_ids=sorted(noncompliant),
    )


def evaluate_platform(
    definition: PlatformDefinition, *, generated_at: str | None = None
) -> PlatformPublication:
    timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    order = _dependency_order(definition)
    portfolio = _portfolio(definition)
    health = _product_health(definition)
    cases = _case_assessments(definition)
    handoffs = _handoff_summary(definition)
    flags: list[str] = []
    if portfolio.currency == "MIXED":
        flags.append(
            "Portfolio contains multiple currencies; totals are not comparable."
        )
    if any(item.status == "blocked" for item in cases):
        flags.append("One or more decision cases are blocked.")
    if handoffs.noncompliant_handoff_ids:
        flags.append("One or more handoffs violate target classification policy.")
    if any(item.status != "healthy" for item in health):
        flags.append("One or more connected products require attention.")
    if not flags:
        flags.append("Connected portfolio is decision-ready under the supplied policy.")
    integration_manifest: dict[str, Any] = {
        "contract_version": definition.contract_version,
        "platform_id": definition.platform_id,
        "product_ids": sorted(item.product_id for item in definition.products),
        "artifact_ids": order,
        "case_ids": sorted(item.case_id for item in definition.cases),
        "api_routes": {
            "evaluate": "/api/v1/platform/evaluate",
            "models": "/api/v1/models",
            "workspaces": "/api/v1/workspaces",
        },
        "handoff_contracts": sorted({item.contract_id for item in definition.handoffs}),
    }
    input_hash = _hash(definition.model_dump(mode="json"))
    dependency_head = _hash(order) if order else None
    output_basis = {
        "portfolio": portfolio.model_dump(mode="json"),
        "product_health": [item.model_dump(mode="json") for item in health],
        "case_assessments": [item.model_dump(mode="json") for item in cases],
        "handoffs": handoffs.model_dump(mode="json"),
        "dependency_order": order,
        "integration_manifest": integration_manifest,
        "flags": flags,
    }
    output_hash = _hash(output_basis)
    return PlatformPublication(
        platform_id=definition.platform_id,
        name=definition.name,
        source=definition.source,
        portfolio=portfolio,
        product_health=health,
        case_assessments=cases,
        handoffs=handoffs,
        dependency_order=order,
        integration_manifest=integration_manifest,
        flags=flags,
        methodology=PlatformMethodology(),
        run_record=PlatformRunRecord(
            run_id=f"run_platform_{input_hash[:24]}",
            generated_at=timestamp,
            input_hash=input_hash,
            output_hash=output_hash,
            dependency_head=dependency_head,
            platform_id=definition.platform_id,
        ),
        metadata=PlatformMetadata(generated_at=timestamp, disclaimer=DISCLAIMER),
    )
