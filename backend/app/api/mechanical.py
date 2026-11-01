"""HTTP boundary for mechanical analysis; engines remain pure functions."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.domain.calc_result import CalcResult, ResultStatus
from app.engines.mechanical import (
    CenterOfGravityResult,
    ContactPoint,
    FourWheelLoads,
    MassPoint,
    StaticStabilityResult,
    SupportPolygonStabilityResult,
    calculate_center_of_gravity,
    calculate_four_wheel_loads,
    calculate_static_stability,
    calculate_support_polygon_stability,
    calculate_three_contact_loads,
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


class ContactInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    x_m: float
    y_m: float


class ContactsAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mass_points: list[MassPointInput] = Field(default_factory=list)
    contacts: list[ContactInput] = Field(min_length=3, max_length=16)


class ContactsAnalysisResponse(BaseModel):
    center_of_gravity: CenterOfGravityResult
    contact_loads: list[CalcResult]
    stability: SupportPolygonStabilityResult


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


def _to_mass_points(inputs: list[MassPointInput]) -> list[MassPoint]:
    return [MassPoint(p.name, p.mass_kg, p.x_m, p.y_m, p.z_m) for p in inputs]


@router.post("/analyze-contacts", response_model=ContactsAnalysisResponse)
def analyze_mechanical_contacts(payload: ContactsAnalysisInput) -> ContactsAnalysisResponse:
    """Support-polygon model for any contact layout (e.g. 2 drive wheels + 1 caster).

    Contact loads are exact for three contacts. With more contacts the reactions
    depend on stiffness and are reported as not evaluable; the margin is still given.
    """

    contacts = [ContactPoint(c.name, c.x_m, c.y_m) for c in payload.contacts]
    cog = calculate_center_of_gravity(_to_mass_points(payload.mass_points))
    stability = calculate_support_polygon_stability(
        cg_x_m=cog.x_m.value, cg_y_m=cog.y_m.value, contacts=contacts
    )
    if len(contacts) == 3:
        loads = calculate_three_contact_loads(
            mass_kg=cog.total_mass.value,
            cg_x_m=cog.x_m.value,
            cg_y_m=cog.y_m.value,
            contacts=contacts,
        ).loads
    else:
        loads = [
            CalcResult(
                name=f"mechanical.contact_load.{c.name}",
                value=None,
                unit="N",
                formula="statically indeterminate for more than 3 contacts",
                status=ResultStatus.NOT_EVALUABLE,
                limits=[
                    (
                        "Reactions are statically indeterminate with more than 3 contacts: "
                        "they depend on stiffness and suspension, which are not modelled."
                    )
                ],
            )
            for c in contacts
        ]
    return ContactsAnalysisResponse(center_of_gravity=cog, contact_loads=loads, stability=stability)
