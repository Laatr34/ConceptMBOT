import math

import pytest

from app.domain.calc_result import ResultStatus
from app.domain.units import InvalidInputError
from app.engines.motorization import (
    calculate_differential_drive,
    calculate_gearbox_output_torque,
    calculate_max_traction_force,
    calculate_required_wheel_torque,
    calculate_slope_force,
    calculate_torque_current,
    calculate_traction_margin,
)


def test_differential_drive_straight_line_reference() -> None:
    result = calculate_differential_drive(
        linear_speed_m_s=1.0,
        angular_speed_rad_s=0.0,
        track_width_m=0.5,
        wheel_radius_m=0.1,
    )
    assert result.left_wheel_angular_speed.value == pytest.approx(10.0)
    assert result.right_wheel_angular_speed.value == pytest.approx(10.0)


def test_differential_drive_rotation_in_place_reference() -> None:
    result = calculate_differential_drive(
        linear_speed_m_s=0.0,
        angular_speed_rad_s=1.0,
        track_width_m=0.5,
        wheel_radius_m=0.1,
    )
    assert result.left_linear_speed.value == pytest.approx(-0.25)
    assert result.right_linear_speed.value == pytest.approx(0.25)
    assert result.left_wheel_angular_speed.value == pytest.approx(-2.5)
    assert result.right_wheel_angular_speed.value == pytest.approx(2.5)


def test_missing_differential_input_is_not_evaluable() -> None:
    result = calculate_differential_drive(
        linear_speed_m_s=1.0,
        angular_speed_rad_s=None,
        track_width_m=0.5,
        wheel_radius_m=0.1,
    )
    assert result.left_linear_speed.value is None
    assert result.left_linear_speed.status is ResultStatus.NOT_EVALUABLE
    assert result.left_linear_speed.missing_inputs == ["angular_speed_rad_s"]


def test_slope_force_reference() -> None:
    result = calculate_slope_force(10.0, 0.1, 0.02)
    expected = 10.0 * 9.80665 * (math.sin(0.1) + 0.02 * math.cos(0.1))
    assert result.value == pytest.approx(expected)
    assert result.unit == "N"


def test_unknown_rolling_resistance_is_not_guessed() -> None:
    result = calculate_slope_force(10.0, 0.1, None)
    assert result.value is None
    assert result.missing_inputs == ["rolling_resistance_coefficient"]


def test_required_wheel_torque_reference() -> None:
    result = calculate_required_wheel_torque(20.0, 0.05, 2)
    assert result.value == pytest.approx(0.5)
    assert result.unit == "N·m"


def test_gearbox_output_torque_reference() -> None:
    result = calculate_gearbox_output_torque(0.2, 10.0, 0.8)
    assert result.value == pytest.approx(1.6)


def test_max_traction_force_reference() -> None:
    result = calculate_max_traction_force(0.5, 100.0)
    assert result.value == pytest.approx(50.0)


def test_traction_margin_can_be_negative() -> None:
    result = calculate_traction_margin(40.0, 50.0)
    assert result.value == pytest.approx(-10.0)


def test_torque_current_reference_and_limits() -> None:
    result = calculate_torque_current(0.2, 0.05)
    assert result.value == pytest.approx(4.0)
    assert any("Stall current" in limit for limit in result.limits)


def test_unknown_torque_constant_is_not_guessed() -> None:
    result = calculate_torque_current(0.2, None)
    assert result.value is None
    assert result.missing_inputs == ["torque_constant_nm_per_a"]


@pytest.mark.parametrize("efficiency", [0.0, -0.1, 1.01])
def test_invalid_gearbox_efficiency_is_rejected(efficiency: float) -> None:
    with pytest.raises(InvalidInputError):
        calculate_gearbox_output_torque(0.2, 10.0, efficiency)


def test_negative_slope_angle_is_rejected_for_uphill_calculation() -> None:
    with pytest.raises(InvalidInputError):
        calculate_slope_force(10.0, -0.1, 0.02)


def test_invalid_track_width_is_rejected() -> None:
    with pytest.raises(InvalidInputError):
        calculate_differential_drive(
            linear_speed_m_s=1.0,
            angular_speed_rad_s=0.0,
            track_width_m=0.0,
            wheel_radius_m=0.1,
        )
