import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_battery_analysis_keeps_unknown_inputs_unevaluable() -> None:
    with TestClient(app) as client:
        response = client.post("/api/battery/analyze", json={})

    assert response.status_code == 200
    body = response.json()
    for key in (
        "pack_voltage",
        "pack_capacity_c",
        "pack_capacity_ah",
        "nominal_energy_j",
        "nominal_energy_wh",
        "usable_energy_j",
        "usable_energy_wh",
        "theoretical_autonomy_s",
        "theoretical_autonomy_h",
        "estimated_autonomy_s",
        "estimated_autonomy_h",
        "measured_autonomy_s",
        "measured_autonomy_h",
    ):
        assert body[key]["value"] is None
        assert body[key]["status"] == "not_evaluable"


def test_battery_analysis_reference_values_and_display_conversions() -> None:
    payload = {
        "cell_voltage_v": 3.7,
        "series_count": 3,
        "cell_capacity_ah": 2.0,
        "parallel_count": 2,
        "depth_of_discharge": 0.8,
        "efficiency": 0.9,
        "average_power_w": 12.0,
        "estimated_average_power_w": 10.0,
        "estimated_power_assumptions": ["Average load estimated from a documented duty cycle."],
        "measured_duration_s": 7200.0,
    }
    with TestClient(app) as client:
        response = client.post("/api/battery/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["pack_voltage"]["value"] == pytest.approx(11.1)
    assert body["pack_capacity_c"]["value"] == pytest.approx(14400.0)
    assert body["pack_capacity_ah"]["value"] == pytest.approx(4.0)
    assert body["nominal_energy_j"]["value"] == pytest.approx(159840.0)
    assert body["nominal_energy_wh"]["value"] == pytest.approx(44.4)
    assert body["usable_energy_j"]["value"] == pytest.approx(115084.8)
    assert body["usable_energy_wh"]["value"] == pytest.approx(31.968)
    assert body["theoretical_autonomy_s"]["value"] == pytest.approx(115084.8 / 12)
    assert body["theoretical_autonomy_h"]["value"] == pytest.approx(115084.8 / 12 / 3600)
    assert body["estimated_autonomy_h"]["value"] == pytest.approx(115084.8 / 10 / 3600)
    assert body["estimated_autonomy_s"]["status"] == "estimated"
    assert body["measured_autonomy_s"]["value"] == pytest.approx(7200)
    assert body["measured_autonomy_h"]["value"] == pytest.approx(2.0)
    assert body["measured_autonomy_s"]["status"] == "measured"


def test_estimated_autonomy_requires_explicit_assumptions() -> None:
    payload = {
        "cell_voltage_v": 3.7,
        "series_count": 3,
        "cell_capacity_ah": 2.0,
        "parallel_count": 2,
        "depth_of_discharge": 0.8,
        "efficiency": 0.9,
        "estimated_average_power_w": 10.0,
    }
    with TestClient(app) as client:
        response = client.post("/api/battery/analyze", json=payload)

    assert response.status_code == 200
    estimated = response.json()["estimated_autonomy_s"]
    assert estimated["value"] is None
    assert estimated["missing_inputs"] == ["estimated_power_assumptions"]


@pytest.mark.parametrize(
    "payload",
    [
        {"series_count": 2.5},
        {"parallel_count": 1.5},
        {"depth_of_discharge": 1.1},
        {"efficiency": 1.2},
    ],
)
def test_battery_analysis_rejects_invalid_integer_or_fraction_inputs(
    payload: dict[str, float],
) -> None:
    baseline = {
        "cell_voltage_v": 3.7,
        "series_count": 3,
        "cell_capacity_ah": 2.0,
        "parallel_count": 2,
        "depth_of_discharge": 0.8,
        "efficiency": 0.9,
    }
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/battery/analyze", json={**baseline, **payload})
    assert response.status_code == 422
