from fastapi.testclient import TestClient

from app.main import app


def _create_project(client: TestClient, name: str, layout: dict) -> str:
    project = client.post("/api/projects", json={"name": name}).json()
    project_id = project["id"]
    saved = client.put(f"/api/projects/{project_id}/mechanical", json=layout)
    assert saved.status_code == 200
    return project_id


def test_diagnostics_report_incomplete_ground_contacts() -> None:
    with TestClient(app) as client:
        project_id = _create_project(
            client,
            "Missing contacts",
            {"mass_points": [], "contacts": [{"name": "left_wheel", "x_m": None, "y_m": None}]},
        )
        response = client.post(f"/api/diagnostics/projects/{project_id}/analyze")

    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "incomplete"
    assert report["scope"] == "mechanical_static"
    assert report["diagnostics"][0]["severity"] == "info"
    assert report["diagnostics"][0]["limit"] == 3.0
    assert report["diagnostics"][0]["correction"]


def test_diagnostics_report_missing_contact_coordinates() -> None:
    contacts = [
        {"name": "left_wheel", "x_m": None, "y_m": 0.15},
        {"name": "right_wheel", "x_m": 0.0, "y_m": -0.15},
        {"name": "caster", "x_m": -0.2, "y_m": 0.0},
    ]
    with TestClient(app) as client:
        project_id = _create_project(
            client, "Missing positions", {"mass_points": [], "contacts": contacts}
        )
        response = client.post(f"/api/diagnostics/projects/{project_id}/analyze")

    assert response.status_code == 200
    diagnostic = response.json()["diagnostics"][0]
    assert diagnostic["code"] == "mechanical.contact_coordinates_missing"
    assert diagnostic["missing_inputs"] == ["left_wheel.x_m"]
    assert diagnostic["severity"] == "info"


def test_diagnostics_report_static_support_outside_polygon_as_critical() -> None:
    layout = {
        "mass_points": [
            {
                "name": "Battery",
                "component_id": None,
                "mass_kg": 5.0,
                "x_m": 0.35,
                "y_m": 0.0,
                "z_m": 0.1,
            }
        ],
        "contacts": [
            {"name": "left_wheel", "x_m": 0.0, "y_m": 0.15},
            {"name": "right_wheel", "x_m": 0.0, "y_m": -0.15},
            {"name": "caster", "x_m": -0.2, "y_m": 0.0},
        ],
    }
    with TestClient(app) as client:
        project_id = _create_project(client, "Unstable robot", layout)
        response = client.post(f"/api/diagnostics/projects/{project_id}/analyze")

    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "attention"
    assert any(
        item["code"] == "mechanical.static_support_unstable"
        and item["severity"] == "critical"
        and item["value"] < 0
        and item["limit"] == 0.0
        for item in report["diagnostics"]
    )


def test_diagnostics_report_unknown_mass_without_guessing() -> None:
    layout = {
        "mass_points": [
            {
                "name": "Raspberry Pi",
                "component_id": None,
                "mass_kg": None,
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.1,
            }
        ],
        "contacts": [
            {"name": "left_wheel", "x_m": 0.0, "y_m": 0.15},
            {"name": "right_wheel", "x_m": 0.0, "y_m": -0.15},
            {"name": "caster", "x_m": -0.2, "y_m": 0.0},
        ],
    }
    with TestClient(app) as client:
        project_id = _create_project(client, "Unknown mass", layout)
        response = client.post(f"/api/diagnostics/projects/{project_id}/analyze")

    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "incomplete"
    assert any(
        item["code"] == "mechanical.mass_unknown.1"
        and item["severity"] == "info"
        and item["missing_inputs"] == ["Raspberry Pi.mass_kg"]
        for item in report["diagnostics"]
    )


def test_diagnostics_report_clear_static_layout() -> None:
    layout = {
        "mass_points": [
            {
                "name": "Chassis",
                "component_id": None,
                "mass_kg": 8.0,
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.12,
            }
        ],
        "contacts": [
            {"name": "left_wheel", "x_m": 0.0, "y_m": 0.15},
            {"name": "right_wheel", "x_m": 0.0, "y_m": -0.15},
            {"name": "caster", "x_m": -0.2, "y_m": 0.0},
        ],
    }
    with TestClient(app) as client:
        project_id = _create_project(client, "Stable layout", layout)
        response = client.post(f"/api/diagnostics/projects/{project_id}/analyze")

    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "clear"
    assert report["diagnostics"] == []


def test_diagnostics_report_collinear_contacts_as_invalid_geometry() -> None:
    layout = {
        "mass_points": [
            {
                "name": "Chassis",
                "component_id": None,
                "mass_kg": 8.0,
                "x_m": 0.0,
                "y_m": 0.0,
                "z_m": 0.12,
            }
        ],
        "contacts": [
            {"name": "left", "x_m": -0.2, "y_m": 0.0},
            {"name": "centre", "x_m": 0.0, "y_m": 0.0},
            {"name": "right", "x_m": 0.2, "y_m": 0.0},
        ],
    }
    with TestClient(app) as client:
        project_id = _create_project(client, "Invalid geometry", layout)
        response = client.post(f"/api/diagnostics/projects/{project_id}/analyze")

    assert response.status_code == 200
    diagnostic = response.json()["diagnostics"][0]
    assert diagnostic["code"] == "mechanical.support_geometry_invalid"
    assert diagnostic["severity"] == "medium"
