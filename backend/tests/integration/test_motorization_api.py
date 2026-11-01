import math

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_motorization_analysis_keeps_missing_inputs_unevaluable() -> None:
    with TestClient(app) as client:
        response = client.post("/api/motorization/analyze", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["differential_drive"]["left_linear_speed"]["value"] is None
    assert body["differential_drive"]["left_linear_speed"]["missing_inputs"] == [
        "linear_speed_m_s",
        "angular_speed_rad_s",
        "track_width_m",
        "wheel_radius_m",
    ]
    assert body["slope_force"]["value"] is None
    assert body["required_wheel_torque"]["value"] is None
    assert body["gearbox_output_torque"]["value"] is None
    assert body["max_traction_force"]["value"] is None
    assert body["traction_margin"]["value"] is None
    assert body["torque_current"]["value"] is None


def test_motorization_analysis_reference_values() -> None:
    payload = {
        "linear_speed_m_s": 1.0,
        "angular_speed_rad_s": 0.0,
        "track_width_m": 0.5,
        "wheel_radius_m": 0.1,
        "mass_kg": 10.0,
        "slope_angle_rad": 0.1,
        "rolling_resistance_coefficient": 0.02,
        "driven_wheel_count": 2,
        "motor_torque_nm": 0.2,
        "gear_ratio": 10.0,
        "gearbox_efficiency": 0.8,
        "friction_coefficient": 0.5,
        "driven_normal_load_n": 100.0,
        "torque_constant_nm_per_a": 0.05,
    }
    with TestClient(app) as client:
        response = client.post("/api/motorization/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["differential_drive"]["left_wheel_angular_speed"]["value"] == pytest.approx(10.0)
    assert body["differential_drive"]["right_wheel_angular_speed"]["value"] == pytest.approx(10.0)
    expected_slope_force = 10.0 * 9.80665 * (math.sin(0.1) + 0.02 * math.cos(0.1))
    assert body["slope_force"]["value"] == pytest.approx(expected_slope_force)
    assert body["required_wheel_torque"]["value"] == pytest.approx(expected_slope_force * 0.1 / 2)
    assert body["gearbox_output_torque"]["value"] == pytest.approx(1.6)
    assert body["max_traction_force"]["value"] == pytest.approx(50.0)
    assert body["traction_margin"]["value"] == pytest.approx(50.0 - expected_slope_force)
    assert body["torque_current"]["value"] == pytest.approx(4.0)
    assert any("not total running current" in limit for limit in body["torque_current"]["limits"])


def test_motorization_analysis_rejects_impossible_efficiency() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/motorization/analyze",
            json={"motor_torque_nm": 0.2, "gear_ratio": 10, "gearbox_efficiency": 1.2},
        )
    assert response.status_code == 422


def test_motorization_api_does_not_accept_stall_current_as_a_running_input() -> None:
    with TestClient(app) as client:
        response = client.post("/api/motorization/analyze", json={"stall_current_a": 4.5})
    assert response.status_code == 422
