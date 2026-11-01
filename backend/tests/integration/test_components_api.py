from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure import component_models, project_models  # noqa: F401
from app.infrastructure.database import Base, get_session
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)

    def override_session() -> Generator[Session]:
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


def test_component_library_starts_empty(client: TestClient) -> None:
    response = client.get("/api/components")
    assert response.status_code == 200
    assert response.json() == []


def test_create_export_import_and_delete_component(client: TestClient) -> None:
    created_response = client.post(
        "/api/components",
        json={
            "name": "Moteur de test",
            "category": "motor",
            "status": "incomplete",
            "parameters": [{"name": "tension_nominale", "value": None, "unit": "V"}],
        },
    )
    assert created_response.status_code == 201
    created = created_response.json()
    assert created["parameters"][0]["value"] is None

    exported = client.get(f"/api/components/{created['id']}/export")
    imported = client.post("/api/components/import", json=exported.json())
    assert imported.status_code == 201
    assert imported.json()["id"] != created["id"]

    deleted = client.delete(f"/api/components/{created['id']}")
    assert deleted.status_code == 204


def test_verified_component_requires_datasheet_url(client: TestClient) -> None:
    response = client.post(
        "/api/components",
        json={"name": "Contrôleur", "category": "controller", "status": "verified"},
    )
    assert response.status_code == 422


def test_unknown_component_schema_is_rejected(client: TestClient) -> None:
    response = client.post("/api/components/import", json={"schema_version": 8})
    assert response.status_code == 422


def test_verified_status_requires_a_datasheet_url(client: TestClient) -> None:
    created = client.post(
        "/api/components",
        json={"name": "Carte de test", "category": "controller"},
    ).json()
    verified = client.patch(
        f"/api/components/{created['id']}",
        json={"status": "verified", "datasheet_url": "https://example.org/datasheet.pdf"},
    )
    assert verified.status_code == 200
    assert verified.json()["status"] == "verified"

    removed_source = client.patch(
        f"/api/components/{created['id']}",
        json={"datasheet_url": None},
    )
    assert removed_source.status_code == 422
