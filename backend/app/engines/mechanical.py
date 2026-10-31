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
