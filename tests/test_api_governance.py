from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from catalyst_finance.api import create_app
from catalyst_finance.repositories import JsonWorkspaceRepository

ROOT = Path(__file__).resolve().parents[1]


def test_governance_api_and_workspace_routes(tmp_path: Path) -> None:
    client = TestClient(create_app(JsonWorkspaceRepository(tmp_path)))
    definition = json.loads((ROOT / "data/sample_governance.json").read_text())
    response = client.post("/api/v1/governance/evaluate", json=definition)
    assert response.status_code == 200
    assert response.json()["readiness"]["status"] == "published"
    workspace = client.post(
        "/api/v1/workspaces", json={"name": "Governance workspace"}
    ).json()
    wid = workspace["workspace_id"]
    created = client.post(
        f"/api/v1/workspaces/{wid}/governance-analyses", json={"definition": definition}
    )
    assert created.status_code == 201
    aid = created.json()["governance_analyses"][0]["analysis_id"]
    definition["name"] = "Revised governed case"
    revised = client.post(
        f"/api/v1/workspaces/{wid}/governance-analyses/{aid}/revisions",
        json={"definition": definition, "change_note": "Updated review record"},
    )
    assert len(revised.json()["governance_analyses"][0]["revisions"]) == 2
    deleted = client.delete(f"/api/v1/workspaces/{wid}/governance-analyses/{aid}")
    assert deleted.json()["governance_analyses"] == []


def test_governance_api_rejects_invalid_payload(tmp_path: Path) -> None:
    client = TestClient(create_app(JsonWorkspaceRepository(tmp_path)))
    response = client.post(
        "/api/v1/governance/evaluate",
        json={"contract_version": "1.9.0", "model_id": "catalyst-finance.governance"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "invalid_governance_definition"
