from fastapi.testclient import TestClient

from app.main import app


def test_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_openapi_available():
    r = TestClient(app).get("/openapi.json")
    assert r.status_code == 200
    assert "/health" in r.json()["paths"]
