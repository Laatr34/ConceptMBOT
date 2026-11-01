import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_mechanical_analysis_returns_center_of_gravity_and_loads() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/mechanical/analyze",
            json={
                "mass_points": [
                    {"name": "left", "mass_kg": 1.0, "x_m": -0.1, "y_m": 0.0, "z_m": 0.2},
                    {"name": "right", "mass_kg": 1.0, "x_m": 0.1, "y_m": 0.0, "z_m": 0.2},
                ],
                "wheelbase_m": 0.5,
                "track_width_m": 0.4,
            },
        )
    assert response.status_code == 200
    result = response.json()
    assert result["center_of_gravity"]["total_mass"]["value"] == 2.0
    assert result["center_of_gravity"]["x_m"]["value"] == 0.0
    assert result["stability"]["status"] == "stable"
    assert result["wheel_loads"]["front_left_n"]["value"] > 0.0


def test_mechanical_analysis_keeps_unknown_mass_unknown() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/mechanical/analyze",
            json={
                "mass_points": [
                    {"name": "unknown_part", "mass_kg": None, "x_m": 0.0, "y_m": 0.0, "z_m": 0.0}
                ],
                "wheelbase_m": 0.5,
                "track_width_m": 0.4,
            },
        )
    assert response.status_code == 200
    result = response.json()
    assert result["center_of_gravity"]["total_mass"]["value"] is None
    assert result["wheel_loads"]["front_left_n"]["value"] is None
    assert result["stability"]["status"] == "unknown"


def test_physically_invalid_input_returns_422_not_500() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/mechanical/analyze",
            json={
                "mass_points": [{"name": "p", "mass_kg": 1.0, "x_m": 0.0, "y_m": 0.0, "z_m": 0.0}],
                "wheelbase_m": -0.5,
                "track_width_m": 0.4,
            },
        )
    assert response.status_code == 422
    assert "wheelbase_m" in response.json()["detail"]


_MASSES = [
    {"name": "body", "mass_kg": 10.0, "x_m": -0.05, "y_m": 0.0, "z_m": 0.2},
]
_TRIANGLE = [
    {"name": "left_wheel", "x_m": 0.0, "y_m": 0.15},
    {"name": "right_wheel", "x_m": 0.0, "y_m": -0.15},
    {"name": "caster", "x_m": -0.2, "y_m": 0.0},
]


def test_contacts_analysis_three_contacts_hand_computed() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/mechanical/analyze-contacts",
            json={"mass_points": _MASSES, "contacts": _TRIANGLE},
        )
    assert response.status_code == 200
    body = response.json()
    weight = 10.0 * 9.80665
    loads = {load["name"]: load["value"] for load in body["contact_loads"]}
    assert loads["mechanical.contact_load.left_wheel"] == pytest.approx(0.375 * weight)
    assert loads["mechanical.contact_load.caster"] == pytest.approx(0.25 * weight)
    assert body["stability"]["margin_m"]["value"] == pytest.approx(0.05)
    assert body["stability"]["status"] == "stable"


def test_contacts_analysis_four_contacts_loads_not_evaluable_but_margin_given() -> None:
    four = [*_TRIANGLE, {"name": "extra", "x_m": -0.2, "y_m": 0.3}]
    with TestClient(app) as client:
        response = client.post(
            "/api/mechanical/analyze-contacts",
            json={"mass_points": _MASSES, "contacts": four},
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body["contact_loads"]) == 4
    assert all(load["value"] is None for load in body["contact_loads"])
    assert any("indeterminate" in lim for lim in body["contact_loads"][0]["limits"])
    assert body["stability"]["margin_m"]["value"] is not None


def test_contacts_analysis_unknown_mass_stays_unknown() -> None:
    masses = [{"name": "b", "mass_kg": None, "x_m": 0.0, "y_m": 0.0, "z_m": 0.0}]
    with TestClient(app) as client:
        response = client.post(
            "/api/mechanical/analyze-contacts",
            json={"mass_points": masses, "contacts": _TRIANGLE},
        )
    body = response.json()
    assert all(load["value"] is None for load in body["contact_loads"])
    assert body["stability"]["status"] == "unknown"


def test_contacts_analysis_rejects_collinear_and_too_few_contacts() -> None:
    line = [
        {"name": "a", "x_m": 0.0, "y_m": 0.0},
        {"name": "b", "x_m": 0.1, "y_m": 0.0},
        {"name": "c", "x_m": 0.2, "y_m": 0.0},
    ]
    with TestClient(app, raise_server_exceptions=False) as client:
        collinear = client.post(
            "/api/mechanical/analyze-contacts", json={"mass_points": _MASSES, "contacts": line}
        )
        few = client.post(
            "/api/mechanical/analyze-contacts",
            json={"mass_points": _MASSES, "contacts": _TRIANGLE[:2]},
        )
    assert collinear.status_code == 422
    assert few.status_code == 422


def test_project_analysis_resolves_only_owner_verified_kg_mass() -> None:
    with TestClient(app) as client:
        component = client.post(
            "/api/components",
            json={
                "name": "Controller board",
                "category": "controller",
                "status": "verified",
                "datasheet_url": "https://example.invalid/datasheet.pdf",
                "parameters": [{"name": "mass", "value": 0.25, "unit": "kg", "source_page": "2"}],
            },
        )
        assert component.status_code == 201
        component_id = component.json()["id"]
        project = client.post("/api/projects", json={"name": "Linked robot"})
        assert project.status_code == 201
        project_id = project.json()["id"]
        layout = {
            "mass_points": [
                {
                    "name": "Controller board",
                    "component_id": component_id,
                    "mass_kg": None,
                    "x_m": 0.0,
                    "y_m": 0.0,
                    "z_m": 0.1,
                }
            ],
            "contacts": _TRIANGLE,
        }
        saved = client.put(f"/api/projects/{project_id}/mechanical", json=layout)
        assert saved.status_code == 200

        response = client.post(f"/api/mechanical/projects/{project_id}/analyze-contacts")

    assert response.status_code == 200
    body = response.json()
    assert body["center_of_gravity"]["total_mass"]["value"] == pytest.approx(0.25)
    assert body["mass_sources"] == [
        {
            "name": "Controller board",
            "source": "verified_component_parameter",
            "component_id": component_id,
            "source_page": "2",
            "detail": "Resolved from the component's owner-verified mass parameter (kg).",
        }
    ]


def test_project_analysis_does_not_use_custom_component_mass() -> None:
    with TestClient(app) as client:
        component = client.post(
            "/api/components",
            json={
                "name": "Custom board",
                "category": "controller",
                "status": "custom",
                "parameters": [{"name": "mass", "value": 0.25, "unit": "kg", "source_page": None}],
            },
        )
        component_id = component.json()["id"]
        project = client.post("/api/projects", json={"name": "Unverified robot"}).json()
        project_id = project["id"]
        layout = {
            "mass_points": [
                {
                    "name": "Custom board",
                    "component_id": component_id,
                    "mass_kg": None,
                    "x_m": 0.0,
                    "y_m": 0.0,
                    "z_m": 0.1,
                }
            ],
            "contacts": _TRIANGLE,
        }
        client.put(f"/api/projects/{project_id}/mechanical", json=layout)
        response = client.post(f"/api/mechanical/projects/{project_id}/analyze-contacts")

    assert response.status_code == 200
    body = response.json()
    assert body["center_of_gravity"]["total_mass"]["value"] is None
    assert body["mass_sources"][0]["source"] == "unknown"
    assert "not declared owner-verified" in body["mass_sources"][0]["detail"]


def test_project_analysis_reports_missing_contact_coordinates() -> None:
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"name": "Incomplete layout"}).json()
        project_id = project["id"]
        layout = {
            "mass_points": [],
            "contacts": [
                {"name": "left", "x_m": None, "y_m": 0.1},
                {"name": "right", "x_m": 0.0, "y_m": -0.1},
                {"name": "caster", "x_m": -0.2, "y_m": 0.0},
            ],
        }
        client.put(f"/api/projects/{project_id}/mechanical", json=layout)
        response = client.post(f"/api/mechanical/projects/{project_id}/analyze-contacts")

    assert response.status_code == 422
    assert response.json()["detail"]["missing_inputs"] == ["left.x_m"]
