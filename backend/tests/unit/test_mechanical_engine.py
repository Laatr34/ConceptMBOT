import pytest

from app.domain.calc_result import ResultStatus
from app.domain.units import InvalidInputError
from app.engines.mechanical import (
    MassPoint,
    StabilityStatus,
    calculate_center_of_gravity,
    calculate_four_wheel_loads,
    calculate_static_stability,
)


def test_center_of_gravity_reference() -> None:
    result = calculate_center_of_gravity(
        [
            MassPoint("left", 1.0, -0.1, 0.0, 0.2),
            MassPoint("right", 1.0, 0.1, 0.0, 0.2),
        ]
    )
    assert result.total_mass.value == pytest.approx(2.0)
    assert result.x_m.value == pytest.approx(0.0)
    assert result.y_m.value == pytest.approx(0.0)
    assert result.z_m.value == pytest.approx(0.2)


def test_unknown_mass_or_position_is_not_guessed() -> None:
    result = calculate_center_of_gravity(
        [MassPoint("battery", None, 0.0, 0.0, 0.1)]
    )
    assert result.total_mass.value is None
    assert result.total_mass.status is ResultStatus.NOT_EVALUABLE
    assert result.total_mass.missing_inputs == ["battery.mass_kg"]


def test_four_wheel_loads_are_equal_when_centered() -> None:
    result = calculate_four_wheel_loads(
        mass_kg=10.0,
        cg_x_m=0.0,
        cg_y_m=0.0,
        wheelbase_m=0.5,
        track_width_m=0.4,
    )
    expected = 10.0 * 9.80665 / 4.0
    assert result.front_left_n.value == pytest.approx(expected)
    assert result.front_right_n.value == pytest.approx(expected)
    assert result.rear_left_n.value == pytest.approx(expected)
    assert result.rear_right_n.value == pytest.approx(expected)


def test_four_wheel_loads_shift_forward_with_forward_cog() -> None:
    result = calculate_four_wheel_loads(
        mass_kg=10.0,
        cg_x_m=0.125,
        cg_y_m=0.0,
        wheelbase_m=0.5,
        track_width_m=0.4,
    )
    front_total = result.front_left_n.value + result.front_right_n.value
    rear_total = result.rear_left_n.value + result.rear_right_n.value
    assert front_total == pytest.approx(0.75 * 10.0 * 9.80665)
    assert rear_total == pytest.approx(0.25 * 10.0 * 9.80665)


def test_static_stability_inside_support_polygon() -> None:
    result = calculate_static_stability(
        cg_x_m=0.1,
        cg_y_m=0.05,
        wheelbase_m=0.5,
        track_width_m=0.4,
    )
    assert result.status is StabilityStatus.STABLE
    assert result.overall_margin_m.value == pytest.approx(0.15)


def test_static_stability_outside_support_polygon() -> None:
    result = calculate_static_stability(
        cg_x_m=0.3,
        cg_y_m=0.0,
        wheelbase_m=0.5,
        track_width_m=0.4,
    )
    assert result.status is StabilityStatus.UNSTABLE
    assert result.overall_margin_m.value == pytest.approx(-0.05)


def test_static_stability_on_edge_is_marginal() -> None:
    result = calculate_static_stability(
        cg_x_m=0.25,
        cg_y_m=0.0,
        wheelbase_m=0.5,
        track_width_m=0.4,
    )
    assert result.status is StabilityStatus.MARGINAL
    assert result.overall_margin_m.value == pytest.approx(0.0)


def test_unknown_stability_input_is_not_evaluable() -> None:
    result = calculate_static_stability(
        cg_x_m=None,
        cg_y_m=0.0,
        wheelbase_m=0.5,
        track_width_m=0.4,
    )
    assert result.overall_margin_m.value is None
    assert result.overall_margin_m.missing_inputs == ["cg_x_m"]
    assert result.status is StabilityStatus.UNKNOWN


def test_non_positive_mass_is_rejected() -> None:
    with pytest.raises(InvalidInputError):
        calculate_center_of_gravity([MassPoint("part", 0.0, 0.0, 0.0, 0.0)])


def test_unknown_wheel_load_inputs_are_not_evaluable() -> None:
    result = calculate_four_wheel_loads(
        mass_kg=10.0,
        cg_x_m=None,
        cg_y_m=0.0,
        wheelbase_m=0.5,
        track_width_m=0.4,
    )
    assert result.front_left_n.value is None
    assert result.front_left_n.missing_inputs == ["cg_x_m"]
