from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from app.infrastructure.database import Base, get_session
from app.infrastructure import project_models  # noqa: F401
from app.main import app
@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    testing_session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)
    def override_session() -> Generator[Session, None, None]:
        session = testing_session()
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
def test_project_lifecycle(client: TestClient) -> None:
    created_response = client.post("/api/projects", json={"name": "Robot médiateur", "description": "Prototype", "data": {}})
    assert created_response.status_code == 201
    created = created_response.json()
    project_id = created["id"]
    assert created["schema_version"] == 1
    assert len(client.get("/api/projects").json()) == 1
    updated_response = client.patch(f"/api/projects/{project_id}", json={"description": None, "data": {"notes": "Première version"}})
    assert updated_response.status_code == 200
    assert updated_response.json()["description"] is None
    assert updated_response.json()["data"]["notes"] == "Première version"
    history = client.get(f"/api/projects/{project_id}/history").json()
    assert [entry["action"] for entry in history] == ["updated", "created"]
    duplicate = client.post(f"/api/projects/{project_id}/duplicate")
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] != project_id
    assert duplicate.json()["data"] == {"notes": "Première version"}
    exported = client.get(f"/api/projects/{project_id}/export")
    imported = client.post("/api/projects/import", json=exported.json())
    assert imported.status_code == 201
    assert imported.json()["id"] != project_id
def test_autosave_and_missing_project(client: TestClient) -> None:
    created = client.post("/api/projects", json={"name": "Autosave"}).json()
    project_id = created["id"]
    saved = client.put(f"/api/projects/{project_id}/autosave", json={"data": {"draft": True}})
    assert saved.status_code == 200
    assert saved.json()["data"] == {"draft": True}
    assert client.get("/api/projects/00000000-0000-0000-0000-000000000000").status_code == 404
def test_import_rejects_unknown_schema_version(client: TestClient) -> None:
    response = client.post("/api/projects/import", json={"schema_version": 99})
    assert response.status_code == 422
