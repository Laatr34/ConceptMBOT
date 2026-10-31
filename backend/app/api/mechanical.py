"""HTTP boundary for mechanical analysis; engines remain pure functions."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.engines.mechanical import (
    CenterOfGravityResult,
    FourWheelLoads,
    MassPoint,
    StaticStabilityResult,
    calculate_center_of_gravity,
    calculate_four_wheel_loads,
    calculate_static_stability,
)


class MassPointInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    mass_kg: float | None = None
    x_m: float | None = None
    y_m: float | None = None
    z_m: float | None = None


class MechanicalAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mass_points: list[MassPointInput] = Field(default_factory=list)
    wheelbase_m: float | None = None
    track_width_m: float | None = None


class MechanicalAnalysisResponse(BaseModel):
    center_of_gravity: CenterOfGravityResult
    wheel_loads: FourWheelLoads
    stability: StaticStabilityResult


router = APIRouter(prefix="/api/mechanical", tags=["mechanical"])


@router.post("/analyze", response_model=MechanicalAnalysisResponse)
def analyze_mechanical_design(
    payload: MechanicalAnalysisInput,
) -> MechanicalAnalysisResponse:
    points = [
        MassPoint(
            name=point.name,
            mass_kg=point.mass_kg,
            x_m=point.x_m,
            y_m=point.y_m,
            z_m=point.z_m,
        )
        for point in payload.mass_points
    ]
    center_of_gravity = calculate_center_of_gravity(points)
    wheel_loads = calculate_four_wheel_loads(
        mass_kg=center_of_gravity.total_mass.value,
        cg_x_m=center_of_gravity.x_m.value,
        cg_y_m=center_of_gravity.y_m.value,
        wheelbase_m=payload.wheelbase_m,
        track_width_m=payload.track_width_m,
    )
    stability = calculate_static_stability(
        cg_x_m=center_of_gravity.x_m.value,
        cg_y_m=center_of_gravity.y_m.value,
        wheelbase_m=payload.wheelbase_m,
        track_width_m=payload.track_width_m,
    )
    return MechanicalAnalysisResponse(
        center_of_gravity=center_of_gravity,
        wheel_loads=wheel_loads,
        stability=stability,
    )
