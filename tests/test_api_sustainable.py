from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from catalyst_finance.api import create_app
from catalyst_finance.repositories import JsonWorkspaceRepository

ROOT = Path(__file__).resolve().parents[1]


def test_sustainable_api_and_workspace_routes(tmp_path: Path) -> None:
    client = TestClient(create_app(JsonWorkspaceRepository(tmp_path)))
    definition = json.loads((ROOT / "data/sample_sustainable.json").read_text())
    response = client.post("/api/v1/sustainable/evaluate", json=definition)
    assert response.status_code == 200
    assert response.json()["summary"]["total_sustainable_value"] == 1401250.9
    workspace = client.post(
        "/api/v1/workspaces", json={"name": "Sustainable workspace"}
    ).json()
    wid = workspace["workspace_id"]
    created = client.post(
        f"/api/v1/workspaces/{wid}/sustainable-analyses",
        json={"definition": definition},
    )
    assert created.status_code == 201
    aid = created.json()["sustainable_analyses"][0]["analysis_id"]
    definition["name"] = "Revised sustainable value"
    revised = client.post(
        f"/api/v1/workspaces/{wid}/sustainable-analyses/{aid}/revisions",
        json={"definition": definition, "change_note": "Updated evidence"},
    )
    assert len(revised.json()["sustainable_analyses"][0]["revisions"]) == 2
    deleted = client.delete(f"/api/v1/workspaces/{wid}/sustainable-analyses/{aid}")
    assert deleted.json()["sustainable_analyses"] == []


def test_sustainable_api_rejects_invalid_payload(tmp_path: Path) -> None:
    client = TestClient(create_app(JsonWorkspaceRepository(tmp_path)))
    response = client.post(
        "/api/v1/sustainable/evaluate",
        json={"contract_version": "1.9.0", "model_id": "catalyst-finance.sustainable"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "invalid_sustainable_definition"
