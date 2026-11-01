import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_electrical_analysis_keeps_missing_values_unevaluable() -> None:
    with TestClient(app) as client:
        response = client.post("/api/electrical/analyze", json={})

    assert response.status_code == 200
    body = response.json()
    for key in (
        "power",
        "current",
        "voltage_drop",
        "regulator_output_power",
        "regulator_input_current",
        "regulator_power_loss",
        "rail_current",
    ):
        assert body[key]["value"] is None
        assert body[key]["status"] == "not_evaluable"
    assert {item["severity"] for item in body["anomalies"]} == {"info"}
    assert {item["code"] for item in body["anomalies"]} == {
        "voltage_min_not_configured",
        "voltage_max_not_configured",
        "voltage_measurement_missing",
        "current_limit_not_configured",
    }


def test_electrical_analysis_reference_values() -> None:
    payload = {
        "voltage_v": 12.0,
        "current_a": 2.0,
        "power_w": 24.0,
        "resistance_ohm": 0.5,
        "regulator": {
            "input_voltage_v": 12.0,
            "output_voltage_v": 5.0,
            "output_current_a": 2.0,
            "efficiency": 0.8,
        },
        "rail": {
            "voltage_v": 12.0,
            "measured_current_a": 2.0,
            "voltage_min_v": 10.0,
            "voltage_max_v": 14.0,
            "current_limit_a": 3.0,
            "loads": [
                {"name": "controller", "current_a": 1.0},
                {"name": "display", "power_w": 12.0},
            ],
        },
    }
    with TestClient(app) as client:
        response = client.post("/api/electrical/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["power"]["value"] == pytest.approx(24.0)
    assert body["current"]["value"] == pytest.approx(2.0)
    assert body["voltage_drop"]["value"] == pytest.approx(1.0)
    assert body["regulator_output_power"]["value"] == pytest.approx(10.0)
    assert body["regulator_input_current"]["value"] == pytest.approx(10 / (0.8 * 12))
    assert body["regulator_power_loss"]["value"] == pytest.approx(2.5)
    assert body["rail_current"]["value"] == pytest.approx(2.0)
    assert body["anomalies"] == []


def test_electrical_analysis_does_not_mark_empty_rail_as_zero_current() -> None:
    with TestClient(app) as client:
        response = client.post("/api/electrical/analyze", json={"rail": {"voltage_v": 12.0}})
    assert response.status_code == 200
    assert response.json()["rail_current"]["value"] is None
    assert response.json()["rail_current"]["missing_inputs"] == ["loads"]


def test_electrical_analysis_rejects_load_with_both_current_and_power() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/electrical/analyze",
            json={"rail": {"loads": [{"name": "ambiguous", "current_a": 1, "power_w": 12}]}},
        )
    assert response.status_code == 422


def test_electrical_analysis_rejects_invalid_regulator_efficiency() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/electrical/analyze",
            json={
                "regulator": {
                    "input_voltage_v": 12,
                    "output_voltage_v": 5,
                    "output_current_a": 2,
                    "efficiency": 1.1,
                }
            },
        )
    assert response.status_code == 422


def test_electrical_anomaly_checks_only_configured_limits() -> None:
    payload = {
        "rail": {
            "voltage_v": 4.2,
            "measured_current_a": 3.0,
            "voltage_min_v": 4.8,
            "voltage_max_v": 5.2,
            "current_limit_a": 2.0,
        }
    }
    with TestClient(app) as client:
        response = client.post("/api/electrical/analyze", json=payload)
    assert response.status_code == 200
    anomalies = response.json()["anomalies"]
    assert {item["code"] for item in anomalies} == {"rail_undervoltage", "rail_overcurrent"}
