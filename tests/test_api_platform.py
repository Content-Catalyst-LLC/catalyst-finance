from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from catalyst_finance.api import create_app
from catalyst_finance.repositories import JsonWorkspaceRepository

ROOT = Path(__file__).resolve().parents[1]


def test_platform_api_and_workspace_routes(tmp_path: Path) -> None:
    client = TestClient(create_app(JsonWorkspaceRepository(tmp_path)))
    definition = json.loads((ROOT / "data/sample_platform.json").read_text())
    response = client.post("/api/v1/platform/evaluate", json=definition)
    assert response.status_code == 200
    assert response.json()["portfolio"]["case_count"] == 2
    models = client.get("/api/v1/models").json()["models"]
    assert any(item["model_id"] == "catalyst-finance.platform" for item in models)
    workspace = client.post(
        "/api/v1/workspaces", json={"name": "Connected finance workspace"}
    ).json()
    wid = workspace["workspace_id"]
    created = client.post(
        f"/api/v1/workspaces/{wid}/platform-analyses",
        json={"definition": definition},
    )
    assert created.status_code == 201
    aid = created.json()["platform_analyses"][0]["analysis_id"]
    definition["name"] = "Revised connected platform"
    revised = client.post(
        f"/api/v1/workspaces/{wid}/platform-analyses/{aid}/revisions",
        json={"definition": definition, "change_note": "Updated product health"},
    )
    assert len(revised.json()["platform_analyses"][0]["revisions"]) == 2
    deleted = client.delete(f"/api/v1/workspaces/{wid}/platform-analyses/{aid}")
    assert deleted.json()["platform_analyses"] == []


def test_platform_api_rejects_invalid_payload(tmp_path: Path) -> None:
    client = TestClient(create_app(JsonWorkspaceRepository(tmp_path)))
    response = client.post(
        "/api/v1/platform/evaluate",
        json={"contract_version": "2.0.0", "model_id": "catalyst-finance.platform"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "invalid_platform_definition"
