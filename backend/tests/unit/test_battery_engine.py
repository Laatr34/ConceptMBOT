import pytest

from app.domain.calc_result import Confidence, ResultStatus
from app.domain.units import InvalidInputError
from app.engines.battery import (
    calculate_pack_capacity,
    calculate_pack_energy,
    calculate_pack_voltage,
    calculate_theoretical_autonomy,
    calculate_usable_energy,
    estimate_autonomy,
    record_measured_autonomy,
)


def test_pack_voltage_series_reference() -> None:
    result = calculate_pack_voltage(3.7, 2)
    assert result.value == pytest.approx(7.4)
    assert result.unit == "V"


def test_pack_capacity_parallel_reference() -> None:
    result = calculate_pack_capacity(7200.0, 3)
    assert result.value == pytest.approx(21600.0)
    assert result.unit == "C"


def test_pack_energy_is_returned_in_joules() -> None:
    result = calculate_pack_energy(12.0, 3600.0)
    assert result.value == pytest.approx(43200.0)
    assert result.unit == "J"


def test_usable_energy_reference() -> None:
    result = calculate_usable_energy(43200.0, 0.8, 0.9)
    assert result.value == pytest.approx(31104.0)
    assert result.unit == "J"


def test_unknown_depth_of_discharge_is_not_guessed() -> None:
    result = calculate_usable_energy(43200.0, None, 0.9)
    assert result.value is None
    assert result.missing_inputs == ["depth_of_discharge"]


@pytest.mark.parametrize("depth", [-0.1, 1.01])
def test_invalid_depth_of_discharge_is_rejected(depth: float) -> None:
    with pytest.raises(InvalidInputError):
        calculate_usable_energy(1000.0, depth, 0.9)


def test_theoretical_autonomy_reference() -> None:
    result = calculate_theoretical_autonomy(31104.0, 12.0)
    assert result.value == pytest.approx(2592.0)
    assert result.unit == "s"
    assert result.status is ResultStatus.THEORETICAL
    assert any("Peukert" in limit for limit in result.limits)


def test_estimated_autonomy_keeps_its_status_and_assumptions() -> None:
    result = estimate_autonomy(
        31104.0,
        12.0,
        assumptions=["Average power estimated from a preliminary duty cycle."],
    )
    assert result.value == pytest.approx(2592.0)
    assert result.status is ResultStatus.ESTIMATED
    assert result.confidence is Confidence.MEDIUM
    assert "Average power estimated from a preliminary duty cycle." in result.assumptions


def test_estimated_autonomy_requires_assumptions_to_be_supplied() -> None:
    result = estimate_autonomy(None, 12.0, assumptions=[])
    assert result.value is None
    assert result.missing_inputs == ["usable_energy_j"]


def test_measured_autonomy_is_not_a_prediction() -> None:
    result = record_measured_autonomy(3600.0)
    assert result.value == 3600.0
    assert result.status is ResultStatus.MEASURED


def test_missing_measured_runtime_is_not_evaluable() -> None:
    result = record_measured_autonomy(None)
    assert result.value is None
    assert result.status is ResultStatus.NOT_EVALUABLE


def test_zero_average_power_is_rejected() -> None:
    with pytest.raises(InvalidInputError):
        calculate_theoretical_autonomy(1000.0, 0.0)
