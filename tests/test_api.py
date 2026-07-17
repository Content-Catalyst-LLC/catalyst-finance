from fastapi.testclient import TestClient

from app import app
from catalyst_finance.version import __version__


def test_healthz() -> None:
    response = TestClient(app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_version_endpoint() -> None:
    response = TestClient(app).get("/api/v1/version")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Catalyst Finance",
        "version": __version__,
        "status": "ok",
    }
