"""Pure mass, center-of-gravity, wheel-load and static-stability calculations.

The four-wheel load model explicitly assumes four coplanar contacts and equal
vertical stiffness. Real chassis compliance and suspension can change reactions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.domain.calc_result import CalcResult, Confidence, ResultStatus
from app.domain.units import InvalidInputError, require_positive

STANDARD_GRAVITY_M_S2 = 9.80665


@dataclass(frozen=True)
class MassPoint:
    """A part or assembly mass located in the robot coordinate frame."""

    name: str
    mass_kg: float | None
    x_m: float | None
    y_m: float | None
    z_m: float | None


class CenterOfGravityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_mass: CalcResult
    x_m: CalcResult
    y_m: CalcResult
    z_m: CalcResult


class FourWheelLoads(BaseModel):
    model_config = ConfigDict(frozen=True)

    front_left_n: CalcResult
    front_right_n: CalcResult
    rear_left_n: CalcResult
    rear_right_n: CalcResult


class StabilityStatus(str, Enum):
    UNKNOWN = "unknown"
    STABLE = "stable"
    MARGINAL = "marginal"
    UNSTABLE = "unstable"


class StaticStabilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    margin_x_m: CalcResult
    margin_y_m: CalcResult
    overall_margin_m: CalcResult
    status: StabilityStatus


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


def calculate_center_of_gravity(points: list[MassPoint]) -> CenterOfGravityResult:
    """Calculate total mass and 3D center of gravity from component mass points."""

    inputs: dict[str, float | None] = {}
    missing: list[str] = []
    if not points:
        missing = ["mass_points"]
        return CenterOfGravityResult(
            total_mass=_not_evaluable(
                name="mechanical.total_mass",
                unit="kg",
                formula="M = Σ mi",
                inputs=inputs,
                missing=missing,
            ),
            x_m=_not_evaluable(
                name="mechanical.center_of_gravity_x",
                unit="m",
                formula="xcg = Σ(mi × xi) / Σmi",
                inputs=inputs,
                missing=missing,
            ),
            y_m=_not_evaluable(
                name="mechanical.center_of_gravity_y",
                unit="m",
                formula="ycg = Σ(mi × yi) / Σmi",
                inputs=inputs,
                missing=missing,
            ),
            z_m=_not_evaluable(
                name="mechanical.center_of_gravity_z",
                unit="m",
                formula="zcg = Σ(mi × zi) / Σmi",
                inputs=inputs,
                missing=missing,
            ),
        )

    total_mass_kg = 0.0
    weighted_x = 0.0
    weighted_y = 0.0
    weighted_z = 0.0
    for point in points:
        values = {
            f"{point.name}.mass_kg": point.mass_kg,
            f"{point.name}.x_m": point.x_m,
            f"{point.name}.y_m": point.y_m,
            f"{point.name}.z_m": point.z_m,
        }
        inputs.update(values)
        missing.extend(name for name, value in values.items() if value is None)
        if any(value is None for value in values.values()):
            continue
        assert point.mass_kg is not None
        assert point.x_m is not None
        assert point.y_m is not None
        assert point.z_m is not None
        require_positive(f"{point.name}.mass_kg", point.mass_kg)
        for name, value in (
            (f"{point.name}.x_m", point.x_m),
            (f"{point.name}.y_m", point.y_m),
            (f"{point.name}.z_m", point.z_m),
        ):
            if not math.isfinite(value):
                raise InvalidInputError(f"{name} must be finite")
        total_mass_kg += point.mass_kg
        weighted_x += point.mass_kg * point.x_m
        weighted_y += point.mass_kg * point.y_m
        weighted_z += point.mass_kg * point.z_m

    if missing:
        return CenterOfGravityResult(
            total_mass=_not_evaluable(
                name="mechanical.total_mass",
                unit="kg",
                formula="M = Σ mi",
                inputs=inputs,
                missing=missing,
            ),
            x_m=_not_evaluable(
                name="mechanical.center_of_gravity_x",
                unit="m",
                formula="xcg = Σ(mi × xi) / Σmi",
                inputs=inputs,
                missing=missing,
            ),
            y_m=_not_evaluable(
                name="mechanical.center_of_gravity_y",
                unit="m",
                formula="ycg = Σ(mi × yi) / Σmi",
                inputs=inputs,
                missing=missing,
            ),
            z_m=_not_evaluable(
                name="mechanical.center_of_gravity_z",
                unit="m",
                formula="zcg = Σ(mi × zi) / Σmi",
                inputs=inputs,
                missing=missing,
            ),
        )

    return CenterOfGravityResult(
        total_mass=_result(
            name="mechanical.total_mass",
            value=total_mass_kg,
            unit="kg",
            formula="M = Σ mi",
            inputs=inputs,
        ),
        x_m=_result(
            name="mechanical.center_of_gravity_x",
            value=weighted_x / total_mass_kg,
            unit="m",
            formula="xcg = Σ(mi × xi) / Σmi",
            inputs=inputs,
        ),
        y_m=_result(
            name="mechanical.center_of_gravity_y",
            value=weighted_y / total_mass_kg,
            unit="m",
            formula="ycg = Σ(mi × yi) / Σmi",
            inputs=inputs,
        ),
        z_m=_result(
            name="mechanical.center_of_gravity_z",
            value=weighted_z / total_mass_kg,
            unit="m",
            formula="zcg = Σ(mi × zi) / Σmi",
            inputs=inputs,
        ),
    )


def calculate_four_wheel_loads(
    *,
    mass_kg: float | None,
    cg_x_m: float | None,
    cg_y_m: float | None,
    wheelbase_m: float | None,
    track_width_m: float | None,
) -> FourWheelLoads:
    """Estimate four corner reactions using equal-stiffness rectangular support."""

    inputs = {
        "mass_kg": mass_kg,
        "cg_x_m": cg_x_m,
        "cg_y_m": cg_y_m,
        "wheelbase_m": wheelbase_m,
        "track_width_m": track_width_m,
    }
    missing = [field for field, value in inputs.items() if value is None]
    formulas = {
        "front_left_n": "RFL = Mg(0.5 + xcg/L)(0.5 + ycg/W)",
        "front_right_n": "RFR = Mg(0.5 + xcg/L)(0.5 − ycg/W)",
        "rear_left_n": "RRL = Mg(0.5 − xcg/L)(0.5 + ycg/W)",
        "rear_right_n": "RRR = Mg(0.5 − xcg/L)(0.5 − ycg/W)",
    }
    if missing:
        return FourWheelLoads(
            **{
                key: _not_evaluable(
                    name=f"mechanical.{key}",
                    unit="N",
                    formula=formula,
                    inputs=inputs,
                    missing=missing,
                )
                for key, formula in formulas.items()
            }
        )

    assert mass_kg is not None
    assert cg_x_m is not None
    assert cg_y_m is not None
    assert wheelbase_m is not None
    assert track_width_m is not None
    require_positive("mass_kg", mass_kg)
    require_positive("wheelbase_m", wheelbase_m)
    require_positive("track_width_m", track_width_m)
    if not math.isfinite(cg_x_m) or not math.isfinite(cg_y_m):
        raise InvalidInputError("center-of-gravity coordinates must be finite")

    weight_n = mass_kg * STANDARD_GRAVITY_M_S2
    front_fraction = 0.5 + cg_x_m / wheelbase_m
    left_fraction = 0.5 + cg_y_m / track_width_m
    reactions = {
        "front_left_n": weight_n * front_fraction * left_fraction,
        "front_right_n": weight_n * front_fraction * (1.0 - left_fraction),
        "rear_left_n": weight_n * (1.0 - front_fraction) * left_fraction,
        "rear_right_n": weight_n * (1.0 - front_fraction) * (1.0 - left_fraction),
    }
    assumptions = [
        "Four wheel contact points are coplanar.",
        "All four supports have equal vertical stiffness.",
        "The chassis is treated as a rigid body in static equilibrium.",
        "Dynamic load transfer, suspension compliance and structural flex are excluded.",
    ]
    return FourWheelLoads(
        **{
            key: _result(
                name=f"mechanical.{key}",
                value=value,
                unit="N",
                formula=formulas[key],
                inputs=inputs,
                assumptions=assumptions,
                limits=[
                    (
                        "A negative reaction means that the assumed contact cannot maintain compression; "
                        "the robot is outside the static support polygon."
                    )
                ],
            )
            for key, value in reactions.items()
        }
    )


def calculate_static_stability(
    *,
    cg_x_m: float | None,
    cg_y_m: float | None,
    wheelbase_m: float | None,
    track_width_m: float | None,
) -> StaticStabilityResult:
    """Calculate rectangular support-polygon margins from the projected CoG."""

    inputs = {
        "cg_x_m": cg_x_m,
        "cg_y_m": cg_y_m,
        "wheelbase_m": wheelbase_m,
        "track_width_m": track_width_m,
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return StaticStabilityResult(
            margin_x_m=_not_evaluable(
                name="mechanical.stability_margin_x",
                unit="m",
                formula="mx = L/2 − |xcg|",
                inputs=inputs,
                missing=missing,
            ),
            margin_y_m=_not_evaluable(
                name="mechanical.stability_margin_y",
                unit="m",
                formula="my = W/2 − |ycg|",
                inputs=inputs,
                missing=missing,
            ),
            overall_margin_m=_not_evaluable(
                name="mechanical.stability_margin",
                unit="m",
                formula="m = min(mx, my)",
                inputs=inputs,
                missing=missing,
            ),
            status=StabilityStatus.UNKNOWN,
        )

    assert cg_x_m is not None
    assert cg_y_m is not None
    assert wheelbase_m is not None
    assert track_width_m is not None
    require_positive("wheelbase_m", wheelbase_m)
    require_positive("track_width_m", track_width_m)
    if not math.isfinite(cg_x_m) or not math.isfinite(cg_y_m):
        raise InvalidInputError("center-of-gravity coordinates must be finite")
    margin_x = wheelbase_m / 2.0 - abs(cg_x_m)
    margin_y = track_width_m / 2.0 - abs(cg_y_m)
    overall = min(margin_x, margin_y)
    if overall < 0.0:
        stability = StabilityStatus.UNSTABLE
    elif overall == 0.0:
        stability = StabilityStatus.MARGINAL
    else:
        stability = StabilityStatus.STABLE
    assumptions = ["Static projection of the center of gravity onto a rectangular support polygon."]
    return StaticStabilityResult(
        margin_x_m=_result(
            name="mechanical.stability_margin_x",
            value=margin_x,
            unit="m",
            formula="mx = L/2 − |xcg|",
            inputs=inputs,
            assumptions=assumptions,
        ),
        margin_y_m=_result(
            name="mechanical.stability_margin_y",
            value=margin_y,
            unit="m",
            formula="my = W/2 − |ycg|",
            inputs=inputs,
            assumptions=assumptions,
        ),
        overall_margin_m=_result(
            name="mechanical.stability_margin",
            value=overall,
            unit="m",
            formula="m = min(mx, my)",
            inputs=inputs,
            assumptions=assumptions,
        ),
        status=stability,
    )


# --------------------------------------------------------------------------- support polygon
@dataclass(frozen=True)
class ContactPoint:
    """Ground contact of a wheel/caster in the robot frame (x forward, y left, metres)."""

    name: str
    x_m: float
    y_m: float


class ThreeContactLoads(BaseModel):
    model_config = ConfigDict(frozen=True)

    loads: list[CalcResult]  # same order as the input contacts, newtons


class SupportPolygonStabilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    margin_m: CalcResult
    status: StabilityStatus


def _require_contacts(contacts: list[ContactPoint], *, exactly: int | None = None) -> None:
    if exactly is not None and len(contacts) != exactly:
        raise InvalidInputError(f"exactly {exactly} contacts are required, got {len(contacts)}")
    if len(contacts) < 3:
        raise InvalidInputError("at least 3 contacts are required")
    for contact in contacts:
        if not (math.isfinite(contact.x_m) and math.isfinite(contact.y_m)):
            raise InvalidInputError(f"contact {contact.name}: coordinates must be finite")


def _cross(o: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Counter-clockwise convex hull (Andrew's monotone chain); collinear points removed."""

    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    lower: list[tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def calculate_three_contact_loads(
    *,
    mass_kg: float | None,
    cg_x_m: float | None,
    cg_y_m: float | None,
    contacts: list[ContactPoint],
) -> ThreeContactLoads:
    """Static reactions on exactly three ground contacts (statically determinate).

    Solves  ΣR = Mg,  ΣR·x = Mg·xcg,  ΣR·y = Mg·ycg  (Cramer's rule). Valid for any
    non-collinear triangle, e.g. two drive wheels plus one caster.
    """

    _require_contacts(contacts, exactly=3)
    inputs: dict[str, float | None] = {"mass_kg": mass_kg, "cg_x_m": cg_x_m, "cg_y_m": cg_y_m}
    for c in contacts:
        inputs[f"{c.name}.x_m"] = c.x_m
        inputs[f"{c.name}.y_m"] = c.y_m
    formula = "R1+R2+R3 = Mg ; ΣRi·xi = Mg·xcg ; ΣRi·yi = Mg·ycg"
    missing = [k for k in ("mass_kg", "cg_x_m", "cg_y_m") if inputs[k] is None]
    if missing:
        return ThreeContactLoads(
            loads=[
                _not_evaluable(
                    name=f"mechanical.contact_load.{c.name}",
                    unit="N",
                    formula=formula,
                    inputs=inputs,
                    missing=missing,
                )
                for c in contacts
            ]
        )
    assert mass_kg is not None and cg_x_m is not None and cg_y_m is not None
    require_positive("mass_kg", mass_kg)
    if not (math.isfinite(cg_x_m) and math.isfinite(cg_y_m)):
        raise InvalidInputError("center-of-gravity coordinates must be finite")

    (x1, y1), (x2, y2), (x3, y3) = [(c.x_m, c.y_m) for c in contacts]
    det = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)  # 2 × triangle area
    if abs(det) < 1e-12:
        raise InvalidInputError("the three contacts are collinear: no stable support")
    weight = mass_kg * STANDARD_GRAVITY_M_S2
    # Barycentric coordinates of the CoG in the contact triangle; Ri = W · λi.
    l1 = ((x2 - cg_x_m) * (y3 - cg_y_m) - (x3 - cg_x_m) * (y2 - cg_y_m)) / det
    l2 = ((x3 - cg_x_m) * (y1 - cg_y_m) - (x1 - cg_x_m) * (y3 - cg_y_m)) / det
    l3 = 1.0 - l1 - l2
    assumptions = [
        "Rigid chassis in static equilibrium on flat ground.",
        "Exactly three contacts: reactions are fully determined by statics (no stiffness assumption).",
        "Dynamic load transfer, suspension and structural flex are excluded.",
    ]
    limits = [
        "A negative reaction means that contact would lift off: the CoG is outside the support triangle."
    ]
    return ThreeContactLoads(
        loads=[
            _result(
                name=f"mechanical.contact_load.{c.name}",
                value=weight * lam,
                unit="N",
                formula=formula,
                inputs=inputs,
                assumptions=assumptions,
                limits=limits,
            )
            for c, lam in zip(contacts, (l1, l2, l3), strict=True)
        ]
    )


def calculate_support_polygon_stability(
    *,
    cg_x_m: float | None,
    cg_y_m: float | None,
    contacts: list[ContactPoint],
) -> SupportPolygonStabilityResult:
    """Static margin = signed distance from the projected CoG to the nearest hull edge.

    Positive inside the support polygon, negative outside. Works for 3 or more contacts.
    """

    _require_contacts(contacts)
    inputs: dict[str, float | None] = {"cg_x_m": cg_x_m, "cg_y_m": cg_y_m}
    for c in contacts:
        inputs[f"{c.name}.x_m"] = c.x_m
        inputs[f"{c.name}.y_m"] = c.y_m
    formula = "m = min over hull edges of signed distance(CoG, edge)"
    missing = [k for k in ("cg_x_m", "cg_y_m") if inputs[k] is None]
    if missing:
        return SupportPolygonStabilityResult(
            margin_m=_not_evaluable(
                name="mechanical.support_polygon_margin",
                unit="m",
                formula=formula,
                inputs=inputs,
                missing=missing,
            ),
            status=StabilityStatus.UNKNOWN,
        )
    assert cg_x_m is not None and cg_y_m is not None
    if not (math.isfinite(cg_x_m) and math.isfinite(cg_y_m)):
        raise InvalidInputError("center-of-gravity coordinates must be finite")
    hull = convex_hull([(c.x_m, c.y_m) for c in contacts])
    if len(hull) < 3:
        raise InvalidInputError("contacts are collinear: no support polygon")
    margin = math.inf
    for i, a in enumerate(hull):
        b = hull[(i + 1) % len(hull)]
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        margin = min(margin, _cross(a, b, (cg_x_m, cg_y_m)) / length)  # CCW hull: inside > 0
    if margin < 0.0:
        status = StabilityStatus.UNSTABLE
    elif margin == 0.0:
        status = StabilityStatus.MARGINAL
    else:
        status = StabilityStatus.STABLE
    return SupportPolygonStabilityResult(
        margin_m=_result(
            name="mechanical.support_polygon_margin",
            value=margin,
            unit="m",
            formula=formula,
            inputs=inputs,
            assumptions=[
                "Static projection of the CoG onto the convex hull of the ground contacts."
            ],
            limits=[
                (
                    "Margin is a geometric distance, not a tip-over safety factor: "
                    "it ignores CoG height, slopes, acceleration and braking."
                )
            ],
        ),
        status=status,
    )
