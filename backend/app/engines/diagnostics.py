"""Pure conversion of mechanical analysis evidence into actionable diagnostics."""

from __future__ import annotations

from app.domain.calc_result import CalcResult
from app.domain.diagnostics import Diagnostic, DiagnosticSeverity
from app.engines.mechanical import StabilityStatus, SupportPolygonStabilityResult


def build_mechanical_diagnostics(
    *,
    total_mass: CalcResult,
    stability: SupportPolygonStabilityResult,
    contact_loads: list[CalcResult],
    mass_sources: list[tuple[str, str, str | None]],
    contact_count: int,
) -> list[Diagnostic]:
    """Create traceable diagnostics without inventing thresholds or measurements."""

    diagnostics: list[Diagnostic] = []

    if not mass_sources and total_mass.value is None:
        diagnostics.append(
            Diagnostic(
                code="mechanical.mass_points_missing",
                component="Robot mass model",
                problem="No mass points are configured.",
                unit="kg",
                limit_source="No project mass-point entries are available.",
                explanation="The centre of gravity cannot be calculated without at least one configured mass point.",
                correction="Add the robot's component and assembly mass points, including their measured or documented masses and positions.",
                severity=DiagnosticSeverity.INFO,
                source_result="mechanical.total_mass",
                missing_inputs=total_mass.missing_inputs,
            )
        )

    for index, (name, source, detail) in enumerate(mass_sources):
        if source == "unknown":
            diagnostics.append(
                Diagnostic(
                    code=f"mechanical.mass_unknown.{index + 1}",
                    component=name,
                    problem="Component mass is unknown and was excluded from the calculation.",
                    unit="kg",
                    limit_source="No accepted project override or owner-verified component mass parameter.",
                    explanation=detail or "The linked component did not provide an acceptable mass value.",
                    correction="Enter a project-specific mass in kg, or link a component declared verified with exactly one numeric 'mass' parameter in kg.",
                    severity=DiagnosticSeverity.INFO,
                    source_result="mechanical.total_mass",
                    missing_inputs=[f"{name}.mass_kg"],
                )
            )

    margin = stability.margin_m
    if stability.status is StabilityStatus.UNSTABLE:
        diagnostics.append(
            Diagnostic(
                code="mechanical.static_support_unstable",
                component="Robot support polygon",
                problem="The projected centre of gravity is outside the support polygon.",
                value=margin.value,
                unit="m",
                limit=0.0,
                limit_source="Convex hull computed from the project's ground-contact coordinates.",
                explanation="The signed geometric margin is negative. In this static model, at least one contact would require a negative reaction.",
                correction="Review the measured mass-point positions and ground-contact geometry. Reposition heavy assemblies or redesign the support layout, then remeasure and recalculate.",
                severity=DiagnosticSeverity.CRITICAL,
                source_result=margin.name,
            )
        )
    elif stability.status is StabilityStatus.MARGINAL:
        diagnostics.append(
            Diagnostic(
                code="mechanical.static_support_marginal",
                component="Robot support polygon",
                problem="The projected centre of gravity lies on the support-polygon boundary.",
                value=margin.value,
                unit="m",
                limit=0.0,
                limit_source="Convex hull computed from the project's ground-contact coordinates.",
                explanation="The geometric static margin is zero; the model provides no positive planar margin.",
                correction="Review mass placement and contact geometry. Do not treat this planar result as a dynamic tip-over safety factor.",
                severity=DiagnosticSeverity.HIGH,
                source_result=margin.name,
            )
        )
    elif stability.status is StabilityStatus.UNKNOWN:
        diagnostics.append(
            Diagnostic(
                code="mechanical.static_support_unknown",
                component="Robot support polygon",
                problem="Static support stability could not be evaluated.",
                unit="m",
                limit_source="Not evaluated because required mass or centre-of-gravity inputs are missing.",
                explanation="The support polygon is configured, but the projected centre of gravity is unavailable.",
                correction="Complete every mass, x/y/z position and linked component mass needed by the project, then run the analysis again.",
                severity=DiagnosticSeverity.INFO,
                source_result=margin.name,
                missing_inputs=margin.missing_inputs,
            )
        )

    for index, load in enumerate(contact_loads):
        if load.value is not None and load.value < 0:
            diagnostics.append(
                Diagnostic(
                    code=f"mechanical.contact_lift_off.{index + 1}",
                    component=load.name.rsplit(".", 1)[-1],
                    problem="The calculated static contact reaction is negative.",
                    value=load.value,
                    unit=load.unit,
                    limit=0.0,
                    limit_source="Three-contact static-equilibrium model; a ground contact cannot sustain tension.",
                    explanation="A negative reaction indicates that the assumed contact would lift off under the configured static mass distribution.",
                    correction="Review the centre of gravity and support geometry. Confirm the robot's actual contact state before relying on this result.",
                    severity=DiagnosticSeverity.CRITICAL,
                    source_result=load.name,
                )
            )
        elif load.value is None and load.limits and contact_count > 3:
            diagnostics.append(
                Diagnostic(
                    code=f"mechanical.contact_load_indeterminate.{index + 1}",
                    component=load.name.rsplit(".", 1)[-1],
                    problem="Individual contact load is statically indeterminate.",
                    unit=load.unit,
                    limit_source="More than three contacts without a stiffness/suspension model.",
                    explanation="The total support polygon can be assessed, but individual reactions cannot be resolved from rigid-body statics alone for this contact count.",
                    correction="Provide a validated support-stiffness/suspension model or keep individual contact reactions marked as unevaluable.",
                    severity=DiagnosticSeverity.INFO,
                    source_result=load.name,
                )
            )

    return diagnostics
