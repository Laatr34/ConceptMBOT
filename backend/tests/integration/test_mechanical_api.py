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
