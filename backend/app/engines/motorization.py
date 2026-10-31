"""Pure differential-drive, traction, torque and motor-current calculations.

Internal values use SI units. Wheel/motor speed is rad/s, torque N·m, force N,
mass kg, distance m and current A. Motor running current is never inferred from
stall current; the torque-current relation excludes no-load and driver losses.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict

from app.domain.calc_result import CalcResult, Confidence, ResultStatus
from app.domain.units import InvalidInputError, require_non_negative, require_positive


class DifferentialDriveResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    left_linear_speed: CalcResult
    right_linear_speed: CalcResult
    left_wheel_angular_speed: CalcResult
    right_wheel_angular_speed: CalcResult


def _not_evaluable(
    *,
    name: str,
    unit: str,
    formula: str,
    inputs: dict[str, float | None],
    missing: list[str],
) -> CalcResult:
    return CalcResult.not_evaluable(
        name=name,
        unit=unit,
        formula=formula,
        inputs=inputs,
        missing_inputs=missing,
    )


def _result(
    *,
    name: str,
    value: float,
    unit: str,
    formula: str,
    inputs: dict[str, float | None],
    assumptions: list[str] | None = None,
    limits: list[str] | None = None,
) -> CalcResult:
    return CalcResult(
        name=name,
        value=value,
        unit=unit,
        formula=formula,
        inputs=inputs,
        assumptions=assumptions or [],
        limits=limits or [],
        status=ResultStatus.THEORETICAL,
        confidence=Confidence.HIGH,
    )


def calculate_differential_drive(
    *,
    linear_speed_m_s: float | None,
    angular_speed_rad_s: float | None,
    track_width_m: float | None,
    wheel_radius_m: float | None,
) -> DifferentialDriveResult:
    """Calculate left/right wheel speeds for a differential-drive robot.

    vL = v − ωL/2; vR = v + ωL/2; wheel angular speed = wheel linear speed / r.
    Positive angular speed is counter-clockwise viewed from above.
    """

    inputs = {
        "linear_speed_m_s": linear_speed_m_s,
        "angular_speed_rad_s": angular_speed_rad_s,
        "track_width_m": track_width_m,
        "wheel_radius_m": wheel_radius_m,
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        results = {
            key: _not_evaluable(
                name=f"motorization.{key}",
                unit=unit,
                formula=formula,
                inputs=inputs,
                missing=missing,
            )
            for key, unit, formula in (
                ("left_linear_speed", "m/s", "vL = v − ωL/2"),
                ("right_linear_speed", "m/s", "vR = v + ωL/2"),
                ("left_wheel_angular_speed", "rad/s", "ωwheel = vwheel / r"),
                ("right_wheel_angular_speed", "rad/s", "ωwheel = vwheel / r"),
            )
        }
        return DifferentialDriveResult(**results)

    assert linear_speed_m_s is not None
    assert angular_speed_rad_s is not None
    assert track_width_m is not None
    assert wheel_radius_m is not None
    if not math.isfinite(linear_speed_m_s):
        raise InvalidInputError("linear_speed_m_s must be finite")
    if not math.isfinite(angular_speed_rad_s):
        raise InvalidInputError("angular_speed_rad_s must be finite")
    require_positive("track_width_m", track_width_m)
    require_positive("wheel_radius_m", wheel_radius_m)

    left_speed = linear_speed_m_s - angular_speed_rad_s * track_width_m / 2.0
    right_speed = linear_speed_m_s + angular_speed_rad_s * track_width_m / 2.0
    left_angular = left_speed / wheel_radius_m
    right_angular = right_speed / wheel_radius_m
    assumptions = ["Ideal differential-drive kinematics; wheel slip and deformation are ignored."]
    return DifferentialDriveResult(
        left_linear_speed=_result(
            name="motorization.left_linear_speed",
            value=left_speed,
            unit="m/s",
            formula="vL = v − ωL/2",
            inputs=inputs,
            assumptions=assumptions,
        ),
        right_linear_speed=_result(
            name="motorization.right_linear_speed",
            value=right_speed,
            unit="m/s",
            formula="vR = v + ωL/2",
            inputs=inputs,
            assumptions=assumptions,
        ),
        left_wheel_angular_speed=_result(
            name="motorization.left_wheel_angular_speed",
            value=left_angular,
            unit="rad/s",
            formula="ωL_wheel = vL / r",
            inputs=inputs,
            assumptions=assumptions,
        ),
        right_wheel_angular_speed=_result(
            name="motorization.right_wheel_angular_speed",
            value=right_angular,
            unit="rad/s",
            formula="ωR_wheel = vR / r",
            inputs=inputs,
            assumptions=assumptions,
        ),
    )


def calculate_slope_force(
    mass_kg: float | None,
    slope_angle_rad: float | None,
    rolling_resistance_coefficient: float | None,
) -> CalcResult:
    """Calculate uphill force at constant speed: F = mg(sin θ + Crr cos θ) (N)."""

    inputs = {
        "mass_kg": mass_kg,
        "slope_angle_rad": slope_angle_rad,
        "rolling_resistance_coefficient": rolling_resistance_coefficient,
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="motorization.slope_force",
            unit="N",
            formula="F = mg(sin θ + Crr cos θ)",
            inputs=inputs,
            missing=missing,
        )
    assert mass_kg is not None
    assert slope_angle_rad is not None
    assert rolling_resistance_coefficient is not None
    require_positive("mass_kg", mass_kg)
    if not math.isfinite(slope_angle_rad) or not 0.0 <= slope_angle_rad < math.pi / 2.0:
        raise InvalidInputError("slope_angle_rad must be finite and in [0, π/2)")
    require_non_negative("rolling_resistance_coefficient", rolling_resistance_coefficient)
    gravity_m_s2 = 9.80665
    value = (
        mass_kg
        * gravity_m_s2
        * (math.sin(slope_angle_rad) + rolling_resistance_coefficient * math.cos(slope_angle_rad))
    )
    return _result(
        name="motorization.slope_force",
        value=value,
        unit="N",
        formula="F = mg(sin θ + Crr cos θ)",
        inputs=inputs,
        assumptions=[
            "Robot moves uphill at constant speed on a uniform slope.",
            "Gravity is the standard value 9.80665 m/s².",
            "Aerodynamic drag and acceleration are not included.",
        ],
    )


def calculate_required_wheel_torque(
    required_force_n: float | None,
    wheel_radius_m: float | None,
    driven_wheel_count: int | None,
) -> CalcResult:
    """Calculate per-wheel torque with even load sharing: τ = F r / n (N·m)."""

    inputs = {
        "required_force_n": required_force_n,
        "wheel_radius_m": wheel_radius_m,
        "driven_wheel_count": (
            float(driven_wheel_count) if driven_wheel_count is not None else None
        ),
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="motorization.required_wheel_torque",
            unit="N·m",
            formula="τwheel = Frequired × r / n",
            inputs=inputs,
            missing=missing,
        )
    assert required_force_n is not None
    assert wheel_radius_m is not None
    assert driven_wheel_count is not None
    require_non_negative("required_force_n", required_force_n)
    require_positive("wheel_radius_m", wheel_radius_m)
    if (
        not isinstance(driven_wheel_count, int)
        or isinstance(driven_wheel_count, bool)
        or driven_wheel_count <= 0
    ):
        raise InvalidInputError("driven_wheel_count must be an integer > 0")
    return _result(
        name="motorization.required_wheel_torque",
        value=required_force_n * wheel_radius_m / driven_wheel_count,
        unit="N·m",
        formula="τwheel = Frequired × r / n",
        inputs=inputs,
        assumptions=["Required traction is shared equally by all driven wheels."],
    )


def calculate_gearbox_output_torque(
    motor_torque_nm: float | None,
    gear_ratio: float | None,
    gearbox_efficiency: float | None,
) -> CalcResult:
    """Calculate gearbox output torque: τout = τmotor × ratio × η (N·m)."""

    inputs = {
        "motor_torque_nm": motor_torque_nm,
        "gear_ratio": gear_ratio,
        "gearbox_efficiency": gearbox_efficiency,
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="motorization.gearbox_output_torque",
            unit="N·m",
            formula="τout = τmotor × ratio × η",
            inputs=inputs,
            missing=missing,
        )
    assert motor_torque_nm is not None
    assert gear_ratio is not None
    assert gearbox_efficiency is not None
    require_non_negative("motor_torque_nm", motor_torque_nm)
    require_positive("gear_ratio", gear_ratio)
    require_positive("gearbox_efficiency", gearbox_efficiency)
    if gearbox_efficiency > 1.0:
        raise InvalidInputError("gearbox_efficiency must be <= 1.0")
    return _result(
        name="motorization.gearbox_output_torque",
        value=motor_torque_nm * gear_ratio * gearbox_efficiency,
        unit="N·m",
        formula="τout = τmotor × ratio × η",
        inputs=inputs,
        assumptions=["Gearbox efficiency is the supplied operating-point value."],
    )


def calculate_max_traction_force(
    friction_coefficient: float | None, driven_normal_load_n: float | None
) -> CalcResult:
    """Calculate friction-limited traction: Fmax = μ × Ndriven (N)."""

    inputs = {
        "friction_coefficient": friction_coefficient,
        "driven_normal_load_n": driven_normal_load_n,
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="motorization.max_traction_force",
            unit="N",
            formula="Fmax = μ × Ndriven",
            inputs=inputs,
            missing=missing,
        )
    assert friction_coefficient is not None and driven_normal_load_n is not None
    require_non_negative("friction_coefficient", friction_coefficient)
    require_non_negative("driven_normal_load_n", driven_normal_load_n)
    return _result(
        name="motorization.max_traction_force",
        value=friction_coefficient * driven_normal_load_n,
        unit="N",
        formula="Fmax = μ × Ndriven",
        inputs=inputs,
        assumptions=["Coulomb friction model; the supplied normal load is on driven wheels only."],
    )


def calculate_traction_margin(
    max_traction_force_n: float | None, required_force_n: float | None
) -> CalcResult:
    """Calculate traction margin: ΔF = Fmax − Frequired (N)."""

    inputs = {
        "max_traction_force_n": max_traction_force_n,
        "required_force_n": required_force_n,
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="motorization.traction_margin",
            unit="N",
            formula="ΔF = Fmax − Frequired",
            inputs=inputs,
            missing=missing,
        )
    assert max_traction_force_n is not None and required_force_n is not None
    require_non_negative("max_traction_force_n", max_traction_force_n)
    require_non_negative("required_force_n", required_force_n)
    return _result(
        name="motorization.traction_margin",
        value=max_traction_force_n - required_force_n,
        unit="N",
        formula="ΔF = Fmax − Frequired",
        inputs=inputs,
        assumptions=[
            "A negative margin indicates that the required force exceeds the friction limit."
        ],
    )


def calculate_torque_current(
    motor_torque_nm: float | None, torque_constant_nm_per_a: float | None
) -> CalcResult:
    """Calculate torque-producing current: I = τ / Kt (A).

    This excludes no-load current, controller losses, thermal derating and
    transient/stall behavior. It must not be presented as total motor current.
    """

    inputs = {
        "motor_torque_nm": motor_torque_nm,
        "torque_constant_nm_per_a": torque_constant_nm_per_a,
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="motorization.torque_current",
            unit="A",
            formula="I = τ / Kt",
            inputs=inputs,
            missing=missing,
        )
    assert motor_torque_nm is not None and torque_constant_nm_per_a is not None
    if not math.isfinite(motor_torque_nm):
        raise InvalidInputError("motor_torque_nm must be finite")
    require_positive("torque_constant_nm_per_a", torque_constant_nm_per_a)
    return _result(
        name="motorization.torque_current",
        value=motor_torque_nm / torque_constant_nm_per_a,
        unit="A",
        formula="I = τ / Kt",
        inputs=inputs,
        assumptions=["Only torque-producing current is calculated; no-load current is excluded."],
        limits=[
            "This is not total running current and is not a substitute for a motor datasheet.",
            "Stall current must not be used as normal operating current.",
        ],
    )
