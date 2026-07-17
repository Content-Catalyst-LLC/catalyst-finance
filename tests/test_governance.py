from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from catalyst_finance.governance import evaluate_governance
from catalyst_finance.governance_migration import normalize_governance
from catalyst_finance.governance_models import GovernanceDefinition

ROOT = Path(__file__).resolve().parents[1]
FIXED = "2026-07-17T00:00:00+00:00"


def sample() -> GovernanceDefinition:
    return GovernanceDefinition.model_validate(
        json.loads((ROOT / "data/sample_governance.json").read_text())
    )


def test_published_case_is_ready_and_reproducible() -> None:
    a = evaluate_governance(sample(), generated_at=FIXED)
    b = evaluate_governance(sample(), generated_at=FIXED)
    assert a == b
    assert a.readiness.status == "published"
    assert a.readiness.publication_allowed
    assert a.readiness.fully_traced_headline_count == 2
    assert a.run_record.input_hash == b.run_record.input_hash


def test_private_records_and_dependent_claims_are_redacted() -> None:
    p = evaluate_governance(sample(), generated_at=FIXED)
    assert {x["source_id"] for x in p.public_payload["sources"]} == {
        "source_carbon_policy",
        "source_ecosystem_study",
    }
    assert {x["claim_id"] for x in p.public_payload["claims"]} == {
        "claim_adjusted_npv",
        "claim_emissions",
        "claim_transferability",
    }
    assert p.public_payload["attachments"] == []


def test_audit_chain_and_handoffs_preserve_identifiers() -> None:
    p = evaluate_governance(sample(), generated_at=FIXED)
    assert p.audit_history[0].previous_hash is None
    assert p.audit_history[-1].previous_hash == p.audit_history[-2].entry_hash
    assert p.run_record.audit_head_hash == p.audit_history[-1].entry_hash
    assert [x.target for x in p.handoffs] == ["knowledge_library", "decision_studio"]
    assert all(x.artifact_revision_id == "revision_8" for x in p.handoffs)


def test_unresolved_objection_blocks_publication() -> None:
    d = sample()
    events = d.review_events[:-2] + [
        d.review_events[-2].model_copy(
            update={"action": "object", "event_id": "event_new_objection"}
        )
    ]
    p = evaluate_governance(
        d.model_copy(update={"review_events": events}), generated_at=FIXED
    )
    assert p.readiness.status == "blocked"
    assert not p.readiness.publication_allowed
    assert p.readiness.unresolved_issue_count == 1


def test_incomplete_headline_trace_blocks_publication() -> None:
    d = sample()
    claims = list(d.claims)
    claims[0] = claims[0].model_copy(update={"evidence_ids": []})
    p = evaluate_governance(d.model_copy(update={"claims": claims}), generated_at=FIXED)
    assert p.readiness.fully_traced_headline_count == 1
    assert not p.readiness.publication_allowed


def test_invalid_references_and_public_no_redaction_are_rejected() -> None:
    payload = json.loads((ROOT / "data/sample_governance.json").read_text())
    payload["evidence"][0]["source_id"] = "missing"
    with pytest.raises(ValidationError):
        GovernanceDefinition.model_validate(payload)
    payload = json.loads((ROOT / "data/sample_governance.json").read_text())
    payload["publication"]["redaction_policy"] = "none"
    with pytest.raises(ValidationError):
        GovernanceDefinition.model_validate(payload)


def test_v180_governance_definition_migrates() -> None:
    payload = json.loads((ROOT / "data/legacy_v1.8.0_governance.json").read_text())
    d = normalize_governance(payload)
    assert d.contract_version == "1.9.0"
    assert d.artifact.model_version == "1.8.0"


def test_browser_governance_parity() -> None:
    import subprocess

    expected = evaluate_governance(sample(), generated_at=FIXED).model_dump(mode="json")
    result = subprocess.run(
        [
            "node",
            "scripts/browser_governance_parity.js",
            "data/sample_governance.json",
            FIXED,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    observed = json.loads(result.stdout)
    for payload in (expected, observed):
        payload.pop("decision_brief_markdown", None)
        payload.pop("decision_brief_html", None)
        payload["run_record"].pop("input_hash", None)
        payload["run_record"].pop("public_payload_hash", None)
        payload["run_record"].pop("run_id", None)
        payload["run_record"].pop("audit_head_hash", None)
        for event in payload["audit_history"]:
            event.pop("entry_hash", None)
            event.pop("previous_hash", None)
    assert observed == expected
