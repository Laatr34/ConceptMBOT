"""HTTP boundary for mechanical analysis; engines remain pure functions."""

from __future__ import annotations

import math
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.application import project_service
from app.application.project_service import ProjectNotFoundError
from app.domain.calc_result import CalcResult, ResultStatus
from app.domain.projects import ProjectMechanicalData, ProjectMechanicalMassPoint
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
from app.infrastructure.component_models import ComponentRecord
from app.infrastructure.database import get_session


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


class ProjectMassSource(BaseModel):
    name: str
    source: Literal["project_override", "verified_component_parameter", "unknown"]
    component_id: UUID | None = None
    source_page: str | None = None
    detail: str | None = None


class ProjectContactsAnalysisResponse(ContactsAnalysisResponse):
    mass_sources: list[ProjectMassSource]


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


def _resolve_project_mass(
    session: Session, point: ProjectMechanicalMassPoint
) -> tuple[float | None, ProjectMassSource]:
    """Use an explicit project mass first, otherwise one owner-verified kg parameter."""

    if point.mass_kg is not None:
        return point.mass_kg, ProjectMassSource(
            name=point.name,
            source="project_override",
            component_id=point.component_id,
            detail="Mass entered directly in this project.",
        )
    if point.component_id is None:
        return None, ProjectMassSource(
            name=point.name,
            source="unknown",
            detail="No project mass or linked component was provided.",
        )

    component = session.get(ComponentRecord, str(point.component_id))
    if component is None:
        return None, ProjectMassSource(
            name=point.name,
            source="unknown",
            component_id=point.component_id,
            detail="Linked component does not exist in the library.",
        )
    if component.status != "verified":
        return None, ProjectMassSource(
            name=point.name,
            source="unknown",
            component_id=point.component_id,
            detail="Linked component is not declared owner-verified.",
        )

    parameters = component.document.get("parameters", [])
    matches = [
        parameter
        for parameter in parameters
        if isinstance(parameter, dict)
        and parameter.get("name") == "mass"
        and parameter.get("unit") == "kg"
    ]
    if len(matches) != 1:
        return None, ProjectMassSource(
            name=point.name,
            source="unknown",
            component_id=point.component_id,
            detail="Expected exactly one numeric 'mass' parameter with unit 'kg'.",
        )

    parameter = matches[0]
    value = parameter.get("value")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value <= 0
    ):
        return None, ProjectMassSource(
            name=point.name,
            source="unknown",
            component_id=point.component_id,
            source_page=parameter.get("source_page"),
            detail="The verified component mass parameter is missing or not a positive finite number.",
        )

    return float(value), ProjectMassSource(
        name=point.name,
        source="verified_component_parameter",
        component_id=point.component_id,
        source_page=parameter.get("source_page"),
        detail="Resolved from the component's owner-verified mass parameter (kg).",
    )


@router.post(
    "/projects/{project_id}/analyze-contacts",
    response_model=ProjectContactsAnalysisResponse,
)
def analyze_project_contacts(
    project_id: UUID,
    session: Session = Depends(get_session),
) -> ProjectContactsAnalysisResponse:
    """Analyse the saved project layout, resolving only explicit or verified masses."""

    try:
        project = project_service.get_project(session, project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error

    layout = ProjectMechanicalData.model_validate(project.data["mechanical"])
    if len(layout.contacts) < 3:
        raise HTTPException(
            status_code=422,
            detail="At least three configured ground contacts are required for support-polygon analysis.",
        )
    missing_contacts = [
        f"{contact.name}.{field}"
        for contact in layout.contacts
        for field in ("x_m", "y_m")
        if getattr(contact, field) is None
    ]
    if missing_contacts:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Ground-contact coordinates are incomplete.",
                "missing_inputs": missing_contacts,
            },
        )

    resolved_points: list[MassPoint] = []
    mass_sources: list[ProjectMassSource] = []
    for point in layout.mass_points:
        mass_kg, source = _resolve_project_mass(session, point)
        mass_sources.append(source)
        resolved_points.append(
            MassPoint(
                name=point.name,
                mass_kg=mass_kg,
                x_m=point.x_m,
                y_m=point.y_m,
                z_m=point.z_m,
            )
        )

    contacts: list[ContactPoint] = []
    for contact in layout.contacts:
        assert contact.x_m is not None and contact.y_m is not None
        contacts.append(ContactPoint(contact.name, contact.x_m, contact.y_m))
    cog = calculate_center_of_gravity(resolved_points)
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
                name=f"mechanical.contact_load.{contact.name}",
                value=None,
                unit="N",
                formula="statically indeterminate for more than 3 contacts",
                status=ResultStatus.NOT_EVALUABLE,
                limits=[
                    (
                        "Reactions are statically indeterminate with more than 3 contacts; "
                        "support stiffness and suspension are not modelled."
                    )
                ],
            )
            for contact in contacts
        ]
    return ProjectContactsAnalysisResponse(
        center_of_gravity=cog,
        contact_loads=loads,
        stability=stability,
        mass_sources=mass_sources,
    )
