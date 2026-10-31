import pytest

from app.domain.calc_result import ResultStatus
from app.domain.units import InvalidInputError
from app.engines.electrical import (
    AnomalySeverity,
    RailLoad,
    calculate_current,
    calculate_power,
    calculate_rail_current,
    calculate_regulator_input_current,
    calculate_regulator_power_loss,
    calculate_voltage_drop,
    detect_rail_anomalies,
)


def test_power_matches_hand_calculated_reference() -> None:
    result = calculate_power(12.0, 2.0)
    assert result.value == pytest.approx(24.0)
    assert result.unit == "W"
    assert result.formula == "P = U × I"
    assert result.status is ResultStatus.THEORETICAL


def test_current_matches_hand_calculated_reference() -> None:
    result = calculate_current(24.0, 12.0)
    assert result.value == pytest.approx(2.0)
    assert result.unit == "A"


def test_missing_current_is_not_evaluable() -> None:
    result = calculate_power(12.0, None)
    assert result.value is None
    assert result.status is ResultStatus.NOT_EVALUABLE
    assert result.missing_inputs == ["current_a"]


def test_negative_current_is_rejected() -> None:
    with pytest.raises(InvalidInputError):
        calculate_power(12.0, -0.1)


def test_zero_voltage_is_rejected_for_current_calculation() -> None:
    with pytest.raises(InvalidInputError):
        calculate_current(10.0, 0.0)


def test_voltage_drop_matches_hand_calculated_reference() -> None:
    result = calculate_voltage_drop(2.0, 0.5)
    assert result.value == pytest.approx(1.0)
    assert result.unit == "V"


def test_regulator_input_current_uses_supplied_efficiency() -> None:
    result = calculate_regulator_input_current(
        input_voltage_v=12.0,
        output_voltage_v=5.0,
        output_current_a=2.0,
        efficiency=0.8,
    )
    assert result.value == pytest.approx(1.0416666667)
    assert result.unit == "A"


def test_unknown_regulator_efficiency_is_not_guessed() -> None:
    result = calculate_regulator_input_current(
        input_voltage_v=12.0,
        output_voltage_v=5.0,
        output_current_a=2.0,
        efficiency=None,
    )
    assert result.value is None
    assert result.missing_inputs == ["efficiency"]


@pytest.mark.parametrize("efficiency", [0.0, -0.1, 1.01])
def test_invalid_efficiency_is_rejected(efficiency: float) -> None:
    with pytest.raises(InvalidInputError):
        calculate_regulator_power_loss(10.0, efficiency)


def test_regulator_power_loss_matches_hand_calculated_reference() -> None:
    result = calculate_regulator_power_loss(10.0, 0.8)
    assert result.value == pytest.approx(2.5)
    assert result.unit == "W"


def test_rail_current_sums_current_and_power_loads() -> None:
    result = calculate_rail_current(
        12.0,
        [
            RailLoad(name="controller", current_a=1.0),
            RailLoad(name="display", power_w=12.0),
        ],
    )
    assert result.value == pytest.approx(2.0)
    assert result.unit == "A"


def test_rail_current_is_not_evaluable_when_a_load_is_unknown() -> None:
    result = calculate_rail_current(
        12.0,
        [RailLoad(name="unknown_load")],
    )
    assert result.value is None
    assert result.missing_inputs == ["unknown_load.current_a_or_power_w"]


def test_rail_current_rejects_ambiguous_load_input() -> None:
    with pytest.raises(InvalidInputError):
        calculate_rail_current(
            12.0,
            [RailLoad(name="ambiguous", current_a=1.0, power_w=12.0)],
        )


def test_rail_anomaly_detection_reports_voltage_and_current_faults() -> None:
    anomalies = detect_rail_anomalies(
        voltage_v=4.2,
        current_a=3.0,
        voltage_min_v=4.8,
        voltage_max_v=5.2,
        current_limit_a=2.0,
    )
    assert {item.code for item in anomalies} == {
        "rail_undervoltage",
        "rail_overcurrent",
    }
    assert all(item.severity is AnomalySeverity.ERROR for item in anomalies)


def test_unconfigured_limits_are_reported_as_unchecked() -> None:
    anomalies = detect_rail_anomalies(
        voltage_v=5.0,
        current_a=0.5,
        voltage_min_v=None,
        voltage_max_v=None,
        current_limit_a=None,
    )
    assert {item.severity for item in anomalies} == {AnomalySeverity.INFO}
    assert len(anomalies) == 3


def test_rail_current_does_not_need_voltage_when_all_currents_are_known() -> None:
    result = calculate_rail_current(
        None,
        [RailLoad(name="controller", current_a=0.75)],
    )
    assert result.value == pytest.approx(0.75)
    assert result.status is ResultStatus.THEORETICAL
