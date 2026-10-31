"""Pure electrical calculations for DC rails and regulators.

All inputs and outputs use SI units. The functions do not assume component
ratings, operating currents, or regulator efficiencies that were not supplied.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.domain.calc_result import CalcResult, Confidence, ResultStatus
from app.domain.units import InvalidInputError, require_non_negative, require_positive


@dataclass(frozen=True)
class RailLoad:
    """One consumer on a DC rail; supply either current or power, not both."""

    name: str
    current_a: float | None = None
    power_w: float | None = None


class AnomalySeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ElectricalAnomaly(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    severity: AnomalySeverity
    message: str
    value: float | None = None
    threshold: float | None = None
    unit: str


def _result(
    *,
    name: str,
    value: float,
    unit: str,
    formula: str,
    inputs: dict[str, float | None],
    assumptions: list[str] | None = None,
) -> CalcResult:
    return CalcResult(
        name=name,
        value=value,
        unit=unit,
        formula=formula,
        inputs=inputs,
        assumptions=assumptions or ["DC steady-state calculation; transient behavior is not modeled."],
        status=ResultStatus.THEORETICAL,
        confidence=Confidence.HIGH,
    )


def calculate_power(voltage_v: float | None, current_a: float | None) -> CalcResult:
    """Calculate DC electrical power: P = U × I (W)."""

    inputs = {"voltage_v": voltage_v, "current_a": current_a}
    missing = [
        field
        for field, value in (("voltage_v", voltage_v), ("current_a", current_a))
        if value is None
    ]
    if missing:
        return CalcResult.not_evaluable(
            name="electrical.power",
            unit="W",
            formula="P = U × I",
            missing_inputs=missing,
            inputs=inputs,
        )
    assert voltage_v is not None and current_a is not None
    require_positive("voltage_v", voltage_v)
    require_non_negative("current_a", current_a)
    return _result(
        name="electrical.power",
        value=voltage_v * current_a,
        unit="W",
        formula="P = U × I",
        inputs=inputs,
    )


def calculate_current(power_w: float | None, voltage_v: float | None) -> CalcResult:
    """Calculate DC current from power and voltage: I = P / U (A)."""

    inputs = {"power_w": power_w, "voltage_v": voltage_v}
    missing = [
        field
        for field, value in (("power_w", power_w), ("voltage_v", voltage_v))
        if value is None
    ]
    if missing:
        return CalcResult.not_evaluable(
            name="electrical.current",
            unit="A",
            formula="I = P / U",
            missing_inputs=missing,
            inputs=inputs,
        )
    assert power_w is not None and voltage_v is not None
    require_non_negative("power_w", power_w)
    require_positive("voltage_v", voltage_v)
    return _result(
        name="electrical.current",
        value=power_w / voltage_v,
        unit="A",
        formula="I = P / U",
        inputs=inputs,
    )


def calculate_voltage_drop(
    current_a: float | None, resistance_ohm: float | None
) -> CalcResult:
    """Calculate resistive DC voltage drop: ΔU = I × R (V)."""

    inputs = {"current_a": current_a, "resistance_ohm": resistance_ohm}
    missing = [
        field
        for field, value in (("current_a", current_a), ("resistance_ohm", resistance_ohm))
        if value is None
    ]
    if missing:
        return CalcResult.not_evaluable(
            name="electrical.voltage_drop",
            unit="V",
            formula="ΔU = I × R",
            missing_inputs=missing,
            inputs=inputs,
        )
    assert current_a is not None and resistance_ohm is not None
    require_non_negative("current_a", current_a)
    require_non_negative("resistance_ohm", resistance_ohm)
    return _result(
        name="electrical.voltage_drop",
        value=current_a * resistance_ohm,
        unit="V",
        formula="ΔU = I × R",
        inputs=inputs,
        assumptions=["Resistance is treated as constant at the operating temperature."],
    )


def calculate_regulator_input_current(
    *,
    input_voltage_v: float | None,
    output_voltage_v: float | None,
    output_current_a: float | None,
    efficiency: float | None,
) -> CalcResult:
    """Estimate regulator input current using Iin = (Uout × Iout) / (η × Uin)."""

    inputs = {
        "input_voltage_v": input_voltage_v,
        "output_voltage_v": output_voltage_v,
        "output_current_a": output_current_a,
        "efficiency": efficiency,
    }
    missing = [
        field
        for field, value in inputs.items()
        if value is None
    ]
    if missing:
        return CalcResult.not_evaluable(
            name="electrical.regulator_input_current",
            unit="A",
            formula="Iin = (Uout × Iout) / (η × Uin)",
            missing_inputs=missing,
            inputs=inputs,
        )
    assert input_voltage_v is not None
    assert output_voltage_v is not None
    assert output_current_a is not None
    assert efficiency is not None
    require_positive("input_voltage_v", input_voltage_v)
    require_positive("output_voltage_v", output_voltage_v)
    require_non_negative("output_current_a", output_current_a)
    require_positive("efficiency", efficiency)
    if efficiency > 1.0:
        raise InvalidInputError("efficiency must be <= 1.0")
    value = (output_voltage_v * output_current_a) / (efficiency * input_voltage_v)
    return _result(
        name="electrical.regulator_input_current",
        value=value,
        unit="A",
        formula="Iin = (Uout × Iout) / (η × Uin)",
        inputs=inputs,
        assumptions=["Efficiency is the supplied operating-point value, not a guessed default."],
    )


def calculate_regulator_power_loss(
    output_power_w: float | None, efficiency: float | None
) -> CalcResult:
    """Calculate regulator loss: Ploss = Pout × (1 / η − 1) (W)."""

    inputs = {"output_power_w": output_power_w, "efficiency": efficiency}
    missing = [
        field
        for field, value in inputs.items()
        if value is None
    ]
    if missing:
        return CalcResult.not_evaluable(
            name="electrical.regulator_power_loss",
            unit="W",
            formula="Ploss = Pout × (1 / η − 1)",
            missing_inputs=missing,
            inputs=inputs,
        )
    assert output_power_w is not None and efficiency is not None
    require_non_negative("output_power_w", output_power_w)
    require_positive("efficiency", efficiency)
    if efficiency > 1.0:
        raise InvalidInputError("efficiency must be <= 1.0")
    return _result(
        name="electrical.regulator_power_loss",
        value=output_power_w * (1.0 / efficiency - 1.0),
        unit="W",
        formula="Ploss = Pout × (1 / η − 1)",
        inputs=inputs,
        assumptions=["Efficiency is treated as constant at the supplied operating point."],
    )


def calculate_rail_current(
    voltage_v: float | None, loads: list[RailLoad]
) -> CalcResult:
    """Sum DC rail consumer currents; convert supplied load power using P / U."""

    inputs: dict[str, float | None] = {"rail_voltage_v": voltage_v}
    missing: list[str] = []
    if voltage_v is not None:
        require_positive("rail_voltage_v", voltage_v)

    total_current_a = 0.0
    for index, load in enumerate(loads):
        current_key = f"loads[{index}].current_a"
        power_key = f"loads[{index}].power_w"
        if load.current_a is not None and load.power_w is not None:
            raise InvalidInputError(
                f"{load.name} must provide current_a or power_w, not both"
            )
        if load.current_a is not None:
            require_non_negative(current_key, load.current_a)
            inputs[current_key] = load.current_a
            total_current_a += load.current_a
        elif load.power_w is not None:
            require_non_negative(power_key, load.power_w)
            inputs[power_key] = load.power_w
            if voltage_v is None:
                missing.append(f"{load.name}.rail_voltage_v")
            else:
                total_current_a += load.power_w / voltage_v
        else:
            inputs[current_key] = None
            inputs[power_key] = None
            missing.append(f"{load.name}.current_a_or_power_w")

    if missing:
        return CalcResult.not_evaluable(
            name="electrical.rail_current",
            unit="A",
            formula="Irail = Σ Iload; Iload = Pload / Urail when only power is supplied",
            missing_inputs=missing,
            inputs=inputs,
        )
    return _result(
        name="electrical.rail_current",
        value=total_current_a,
        unit="A",
        formula="Irail = Σ Iload; Iload = Pload / Urail when only power is supplied",
        inputs=inputs,
        assumptions=["All listed loads operate simultaneously at steady state."],
    )


def detect_rail_anomalies(
    *,
    voltage_v: float | None,
    current_a: float | None,
    voltage_min_v: float | None,
    voltage_max_v: float | None,
    current_limit_a: float | None,
) -> list[ElectricalAnomaly]:
    """Compare supplied rail readings with explicitly supplied limits.

    Missing limits produce INFO entries so that 'no anomaly' cannot be mistaken
    for a completed safety check.
    """

    anomalies: list[ElectricalAnomaly] = []
    if voltage_min_v is not None:
        require_non_negative("voltage_min_v", voltage_min_v)
    else:
        anomalies.append(
            ElectricalAnomaly(
                code="voltage_min_not_configured",
                severity=AnomalySeverity.INFO,
                message="Lower voltage limit is not configured; undervoltage was not checked.",
                unit="V",
            )
        )
    if voltage_max_v is not None:
        require_positive("voltage_max_v", voltage_max_v)
    else:
        anomalies.append(
            ElectricalAnomaly(
                code="voltage_max_not_configured",
                severity=AnomalySeverity.INFO,
                message="Upper voltage limit is not configured; overvoltage was not checked.",
                unit="V",
            )
        )
    if (
        voltage_min_v is not None
        and voltage_max_v is not None
        and voltage_min_v >= voltage_max_v
    ):
        raise InvalidInputError("voltage_min_v must be lower than voltage_max_v")

    if voltage_v is None:
        anomalies.append(
            ElectricalAnomaly(
                code="voltage_measurement_missing",
                severity=AnomalySeverity.INFO,
                message="Rail voltage is unknown; voltage limits could not be checked.",
                unit="V",
            )
        )
    else:
        require_non_negative("voltage_v", voltage_v)
        if voltage_min_v is not None and voltage_v < voltage_min_v:
            anomalies.append(
                ElectricalAnomaly(
                    code="rail_undervoltage",
                    severity=AnomalySeverity.ERROR,
                    message="Rail voltage is below the configured lower limit.",
                    value=voltage_v,
                    threshold=voltage_min_v,
                    unit="V",
                )
            )
        if voltage_max_v is not None and voltage_v > voltage_max_v:
            anomalies.append(
                ElectricalAnomaly(
                    code="rail_overvoltage",
                    severity=AnomalySeverity.ERROR,
                    message="Rail voltage is above the configured upper limit.",
                    value=voltage_v,
                    threshold=voltage_max_v,
                    unit="V",
                )
            )

    if current_limit_a is None:
        anomalies.append(
            ElectricalAnomaly(
                code="current_limit_not_configured",
                severity=AnomalySeverity.INFO,
                message="Current limit is not configured; overcurrent was not checked.",
                unit="A",
            )
        )
    else:
        require_positive("current_limit_a", current_limit_a)
        if current_a is None:
            anomalies.append(
                ElectricalAnomaly(
                    code="current_measurement_missing",
                    severity=AnomalySeverity.INFO,
                    message="Rail current is unknown; overcurrent could not be checked.",
                    threshold=current_limit_a,
                    unit="A",
                )
            )
        else:
            require_non_negative("current_a", current_a)
            if current_a > current_limit_a:
                anomalies.append(
                    ElectricalAnomaly(
                        code="rail_overcurrent",
                        severity=AnomalySeverity.ERROR,
                        message="Rail current is above the configured current limit.",
                        value=current_a,
                        threshold=current_limit_a,
                        unit="A",
                    )
                )
    return anomalies
