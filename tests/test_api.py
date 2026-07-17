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
    model = response.json()["models"][0]
    assert model["model_id"] == "catalyst-finance.screening"
    assert model["model_version"] == "1.1.0"


def test_evaluate_endpoint_uses_canonical_contract() -> None:
    payload = json.loads((ROOT / "data" / "sample_finance_scenario.json").read_text())
    response = CLIENT.post("/api/v1/evaluate", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["contract_version"] == "1.1.0"
    assert result["results"]["score_components"]


def test_evaluate_endpoint_returns_structured_validation_error() -> None:
    payload = json.loads((ROOT / "data" / "sample_finance_scenario.json").read_text())
    payload["assumptions"]["time_horizon_years"] = 0
    response = CLIENT.post("/api/v1/evaluate", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "invalid_finance_scenario"
    assert detail["issues"][0]["path"]
