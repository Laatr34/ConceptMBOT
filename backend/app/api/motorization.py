"""HTTP boundary for differential-drive motorization calculations."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.domain.calc_result import CalcResult
from app.engines.motorization import (
    DifferentialDriveResult,
    calculate_differential_drive,
    calculate_gearbox_output_torque,
    calculate_max_traction_force,
    calculate_required_wheel_torque,
    calculate_slope_force,
    calculate_torque_current,
    calculate_traction_margin,
)


class MotorizationAnalysisInput(BaseModel):
    """Optional SI inputs; omitted or null values remain unevaluable."""

    model_config = ConfigDict(extra="forbid")

    linear_speed_m_s: float | None = None
    angular_speed_rad_s: float | None = None
    track_width_m: float | None = None
    wheel_radius_m: float | None = None
    mass_kg: float | None = None
    slope_angle_rad: float | None = None
    rolling_resistance_coefficient: float | None = None
    driven_wheel_count: int | None = None
    motor_torque_nm: float | None = None
    gear_ratio: float | None = None
    gearbox_efficiency: float | None = None
    friction_coefficient: float | None = None
    driven_normal_load_n: float | None = None
    torque_constant_nm_per_a: float | None = None


class MotorizationAnalysisResponse(BaseModel):
    differential_drive: DifferentialDriveResult
    slope_force: CalcResult
    required_wheel_torque: CalcResult
    gearbox_output_torque: CalcResult
    max_traction_force: CalcResult
    traction_margin: CalcResult
    torque_current: CalcResult


router = APIRouter(prefix="/api/motorization", tags=["motorization"])


@router.post("/analyze", response_model=MotorizationAnalysisResponse)
def analyze_motorization(payload: MotorizationAnalysisInput) -> MotorizationAnalysisResponse:
    """Calculate kinematics, uphill force, torque, traction and torque-producing current."""

    drive = calculate_differential_drive(
        linear_speed_m_s=payload.linear_speed_m_s,
        angular_speed_rad_s=payload.angular_speed_rad_s,
        track_width_m=payload.track_width_m,
        wheel_radius_m=payload.wheel_radius_m,
    )
    slope_force = calculate_slope_force(
        mass_kg=payload.mass_kg,
        slope_angle_rad=payload.slope_angle_rad,
        rolling_resistance_coefficient=payload.rolling_resistance_coefficient,
    )
    required_torque = calculate_required_wheel_torque(
        required_force_n=slope_force.value,
        wheel_radius_m=payload.wheel_radius_m,
        driven_wheel_count=payload.driven_wheel_count,
    )
    gearbox_torque = calculate_gearbox_output_torque(
        motor_torque_nm=payload.motor_torque_nm,
        gear_ratio=payload.gear_ratio,
        gearbox_efficiency=payload.gearbox_efficiency,
    )
    max_traction = calculate_max_traction_force(
        friction_coefficient=payload.friction_coefficient,
        driven_normal_load_n=payload.driven_normal_load_n,
    )
    traction_margin = calculate_traction_margin(
        max_traction_force_n=max_traction.value,
        required_force_n=slope_force.value,
    )
    torque_current = calculate_torque_current(
        motor_torque_nm=payload.motor_torque_nm,
        torque_constant_nm_per_a=payload.torque_constant_nm_per_a,
    )
    return MotorizationAnalysisResponse(
        differential_drive=drive,
        slope_force=slope_force,
        required_wheel_torque=required_torque,
        gearbox_output_torque=gearbox_torque,
        max_traction_force=max_traction,
        traction_margin=traction_margin,
        torque_current=torque_current,
    )
