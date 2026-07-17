import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import app
from catalyst_finance.version import __version__

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_healthz() -> None:
    response = CLIENT.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_version_endpoint() -> None:
    response = CLIENT.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Catalyst Finance",
        "version": __version__,
        "status": "ok",
    }


def test_model_registry_endpoint() -> None:
    response = CLIENT.get("/api/v1/models")
    assert response.status_code == 200
    models = response.json()["models"]
    assert [model["model_id"] for model in models] == [
        "catalyst-finance.screening",
        "catalyst-finance.cash-flow",
    ]
    assert all(model["model_version"] == "1.3.0" for model in models)


def test_evaluate_endpoint_uses_canonical_contract() -> None:
    payload = json.loads((ROOT / "data" / "sample_finance_scenario.json").read_text())
    response = CLIENT.post("/api/v1/evaluate", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["contract_version"] == "1.3.0"
    assert result["results"]["score_components"]


def test_evaluate_endpoint_returns_structured_validation_error() -> None:
    payload = json.loads((ROOT / "data" / "sample_finance_scenario.json").read_text())
    payload["assumptions"]["time_horizon_years"] = 0
    response = CLIENT.post("/api/v1/evaluate", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "invalid_finance_scenario"
    assert detail["issues"][0]["path"]


def test_workspace_api_lifecycle(tmp_path: Path) -> None:
    from catalyst_finance.api import create_app
    from catalyst_finance.repositories import JsonWorkspaceRepository

    client = TestClient(create_app(JsonWorkspaceRepository(tmp_path / "workspaces")))
    created = client.post(
        "/api/v1/workspaces",
        json={
            "name": "API workspace",
            "defaults": {"currency": "USD", "locale": "en-US"},
        },
    )
    assert created.status_code == 201
    workspace_id = created.json()["workspace_id"]

    project = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        json={"name": "Facilities", "tags": ["energy"]},
    )
    assert project.status_code == 201
    project_id = project.json()["projects"][0]["project_id"]

    scenario = client.post(
        f"/api/v1/workspaces/{workspace_id}/scenarios",
        json={
            "name": "Retrofit",
            "project_id": project_id,
            "template_id": "sustainability-investment",
        },
    )
    assert scenario.status_code == 201
    scenario_id = scenario.json()["scenarios"][0]["scenario_id"]

    duplicate = client.post(
        f"/api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/duplicate"
    )
    assert duplicate.status_code == 200
    assert len(duplicate.json()["scenarios"]) == 2

    archived = client.post(
        f"/api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/archive"
    )
    assert archived.json()["scenarios"][0]["status"] == "archived"
    restored = client.post(
        f"/api/v1/workspaces/{workspace_id}/scenarios/{scenario_id}/restore"
    )
    assert restored.json()["scenarios"][0]["status"] == "active"

    listed = client.get("/api/v1/workspaces")
    assert listed.status_code == 200
    assert listed.json()["workspaces"][0]["workspace_id"] == workspace_id


def test_templates_api() -> None:
    response = CLIENT.get("/api/v1/templates")
    assert response.status_code == 200
    assert len(response.json()["templates"]) == 5


def test_cash_flow_evaluate_endpoint() -> None:
    payload = json.loads((ROOT / "data" / "sample_cash_flow_scenario.json").read_text())
    response = CLIENT.post("/api/v1/cash-flow/evaluate", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["model_id"] == "catalyst-finance.cash-flow"
    assert result["metrics"]["npv"] == 198884.69
    assert len(result["periods"]) == 11


def test_cash_flow_endpoint_returns_basis_error() -> None:
    payload = json.loads((ROOT / "data" / "sample_cash_flow_scenario.json").read_text())
    payload["context"]["discount_rate_basis"] = "real"
    response = CLIENT.post("/api/v1/cash-flow/evaluate", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "invalid_cash_flow_scenario"
    assert any("must match" in issue["message"] for issue in detail["issues"])
