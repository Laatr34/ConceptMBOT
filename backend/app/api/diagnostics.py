"""Project-scoped diagnostics for the current mechanical static-analysis scope."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.mechanical import analyze_project_contacts
from app.application import project_service
from app.application.project_service import ProjectNotFoundError
from app.domain.diagnostics import Diagnostic, DiagnosticSeverity
from app.domain.projects import ProjectMechanicalData
from app.domain.units import InvalidInputError
from app.engines.diagnostics import build_mechanical_diagnostics
from app.infrastructure.database import get_session


class DiagnosticsReport(BaseModel):
    project_id: UUID
    project_name: str
    scope: Literal["mechanical_static"] = "mechanical_static"
    generated_at: datetime
    status: Literal["clear", "incomplete", "attention"]
    diagnostics: list[Diagnostic]


router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


def _report_status(diagnostics: list[Diagnostic]) -> Literal["clear", "incomplete", "attention"]:
    if any(
        item.severity in {
            DiagnosticSeverity.CRITICAL,
            DiagnosticSeverity.HIGH,
            DiagnosticSeverity.MEDIUM,
        }
        for item in diagnostics
    ):
        return "attention"
    if diagnostics:
        return "incomplete"
    return "clear"


@router.post("/projects/{project_id}/analyze", response_model=DiagnosticsReport)
def analyze_project_diagnostics(
    project_id: UUID,
    session: Session = Depends(get_session),
) -> DiagnosticsReport:
    """Analyse saved project geometry and return visible, actionable mechanical findings."""

    try:
        project = project_service.get_project(session, project_id)
    except ProjectNotFoundError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error

    layout = ProjectMechanicalData.model_validate(project.data["mechanical"])
    diagnostics: list[Diagnostic] = []

    if len(layout.contacts) < 3:
        diagnostics.append(
            Diagnostic(
                code="mechanical.contacts_insufficient",
                component="Ground contacts",
                problem="At least three ground contacts are required.",
                value=float(len(layout.contacts)),
                unit="contacts",
                limit=3.0,
                limit_source="Static support-polygon model requirement.",
                explanation="The project does not contain enough ground-contact points to construct a support polygon.",
                correction="Configure at least three measured ground contacts, such as the two driven wheels and the caster.",
                severity=DiagnosticSeverity.INFO,
                source_result="mechanical.support_polygon_margin",
                missing_inputs=["mechanical.contacts"],
            )
        )
        return DiagnosticsReport(
            project_id=project.id,
            project_name=project.name,
            generated_at=datetime.now(UTC),
            status=_report_status(diagnostics),
            diagnostics=diagnostics,
        )

    missing_contacts = [
        f"{contact.name}.{field}"
        for contact in layout.contacts
        for field in ("x_m", "y_m")
        if getattr(contact, field) is None
    ]
    if missing_contacts:
        diagnostics.append(
            Diagnostic(
                code="mechanical.contact_coordinates_missing",
                component="Ground contacts",
                problem="Ground-contact coordinates are incomplete.",
                unit="m",
                limit_source="Project contact coordinates in the robot-fixed XY frame.",
                explanation="The support polygon cannot be constructed until every contact has an X and Y position.",
                correction="Enter measured or design-defined X/Y coordinates for every wheel and caster contact. Do not use zero as a placeholder for an unknown position.",
                severity=DiagnosticSeverity.INFO,
                source_result="mechanical.support_polygon_margin",
                missing_inputs=missing_contacts,
            )
        )
        return DiagnosticsReport(
            project_id=project.id,
            project_name=project.name,
            generated_at=datetime.now(UTC),
            status=_report_status(diagnostics),
            diagnostics=diagnostics,
        )

    try:
        analysis = analyze_project_contacts(project_id, session)
    except InvalidInputError as error:
        diagnostics.append(
            Diagnostic(
                code="mechanical.support_geometry_invalid",
                component="Ground-contact geometry",
                problem="The configured ground contacts do not form a valid support polygon.",
                limit_source="Convex-hull geometry requires at least three non-collinear contact points.",
                explanation=str(error),
                correction="Check the contact coordinates and verify that the points describe the robot's actual support geometry.",
                severity=DiagnosticSeverity.MEDIUM,
                source_result="mechanical.support_polygon_margin",
            )
        )
        return DiagnosticsReport(
            project_id=project.id,
            project_name=project.name,
            generated_at=datetime.now(UTC),
            status=_report_status(diagnostics),
            diagnostics=diagnostics,
        )

    mass_sources = [
        (source.name, source.source, source.detail) for source in analysis.mass_sources
    ]
    diagnostics.extend(
        build_mechanical_diagnostics(
            total_mass=analysis.center_of_gravity.total_mass,
            stability=analysis.stability,
            contact_loads=analysis.contact_loads,
            mass_sources=mass_sources,
            contact_count=len(layout.contacts),
        )
    )
    return DiagnosticsReport(
        project_id=project.id,
        project_name=project.name,
        generated_at=datetime.now(UTC),
        status=_report_status(diagnostics),
        diagnostics=diagnostics,
    )
