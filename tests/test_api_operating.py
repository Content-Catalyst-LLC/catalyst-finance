from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from catalyst_finance.api import create_app
from catalyst_finance.repositories import JsonWorkspaceRepository

ROOT = Path(__file__).resolve().parents[1]


def test_operating_api_and_workspace_routes(tmp_path: Path) -> None:
    client = TestClient(create_app(JsonWorkspaceRepository(tmp_path)))
    definition = json.loads((ROOT / "data/sample_operating.json").read_text())
    response = client.post("/api/v1/operating/evaluate", json=definition)
    assert response.status_code == 200
    assert response.json()["total_summary"]["operating_profit_variance"] == 2185.0
    workspace = client.post(
        "/api/v1/workspaces", json={"name": "Operating API workspace"}
    ).json()
    workspace_id = workspace["workspace_id"]
    created = client.post(
        f"/api/v1/workspaces/{workspace_id}/operating-analyses",
        json={"definition": definition},
    )
    assert created.status_code == 201
    analysis_id = created.json()["operating_analyses"][0]["analysis_id"]
    definition["name"] = "Revised operating definition"
    revised = client.post(
        f"/api/v1/workspaces/{workspace_id}/operating-analyses/{analysis_id}/revisions",
        json={"definition": definition, "change_note": "API revision"},
    )
    assert revised.status_code == 200
    assert len(revised.json()["operating_analyses"][0]["revisions"]) == 2
    deleted = client.delete(
        f"/api/v1/workspaces/{workspace_id}/operating-analyses/{analysis_id}"
    )
    assert deleted.status_code == 200
    assert deleted.json()["operating_analyses"] == []


def test_operating_api_rejects_invalid_payload(tmp_path: Path) -> None:
    client = TestClient(create_app(JsonWorkspaceRepository(tmp_path)))
    response = client.post(
        "/api/v1/operating/evaluate",
        json={"contract_version": "1.9.0", "model_id": "catalyst-finance.operating"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "invalid_operating_definition"
