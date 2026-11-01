import math

import pytest

from app.domain.calc_result import ResultStatus
from app.domain.units import InvalidInputError
from app.engines.mechanical import (
    STANDARD_GRAVITY_M_S2,
    ContactPoint,
    StabilityStatus,
    calculate_support_polygon_stability,
    calculate_three_contact_loads,
    convex_hull,
)

# Differential robot: left/right drive wheels at x=0, y=±0.15 (y positive = left),
# caster 0.2 m behind. x forward.
LEFT = ContactPoint("left_wheel", 0.0, 0.15)
RIGHT = ContactPoint("right_wheel", 0.0, -0.15)
CASTER = ContactPoint("caster", -0.2, 0.0)
TRI = [LEFT, RIGHT, CASTER]


def test_three_contact_loads_hand_computed() -> None:
    # W = 10 kg * g. CoG at x=-0.05, y=0.
    # Moment about y axis: R_caster * (-0.2) = W * (-0.05) -> R_caster = 0.25 W
    # Symmetry: R_left = R_right = 0.375 W
    w = 10.0 * STANDARD_GRAVITY_M_S2
    r = calculate_three_contact_loads(mass_kg=10.0, cg_x_m=-0.05, cg_y_m=0.0, contacts=TRI)
    assert r.loads[0].value == pytest.approx(0.375 * w)
    assert r.loads[1].value == pytest.approx(0.375 * w)
    assert r.loads[2].value == pytest.approx(0.25 * w)
    assert sum(x.value for x in r.loads if x.value is not None) == pytest.approx(w)


def test_loads_sum_to_weight_for_any_cog_and_satisfy_moments() -> None:
    cx, cy = -0.07, 0.03
    r = calculate_three_contact_loads(mass_kg=4.2, cg_x_m=cx, cg_y_m=cy, contacts=TRI)
    values = [x.value for x in r.loads]
    assert None not in values
    w = 4.2 * STANDARD_GRAVITY_M_S2
    assert sum(values) == pytest.approx(w)
    assert sum(v * c.x_m for v, c in zip(values, TRI, strict=True)) == pytest.approx(w * cx)
    assert sum(v * c.y_m for v, c in zip(values, TRI, strict=True)) == pytest.approx(w * cy)


def test_negative_reaction_when_cog_outside_polygon() -> None:
    # CoG 0.1 m in front of the wheel axis: lifts the caster (negative reaction).
    r = calculate_three_contact_loads(mass_kg=10.0, cg_x_m=0.1, cg_y_m=0.0, contacts=TRI)
    assert r.loads[2].value is not None and r.loads[2].value < 0
    assert any("negative" in lim.lower() for lim in r.loads[2].limits)


def test_missing_data_is_not_evaluable() -> None:
    r = calculate_three_contact_loads(mass_kg=None, cg_x_m=0.0, cg_y_m=None, contacts=TRI)
    for load in r.loads:
        assert load.status is ResultStatus.NOT_EVALUABLE
        assert set(load.missing_inputs) == {"mass_kg", "cg_y_m"}


def test_collinear_or_wrong_count_rejected() -> None:
    line = [ContactPoint("a", 0.0, 0.0), ContactPoint("b", 0.1, 0.0), ContactPoint("c", 0.2, 0.0)]
    with pytest.raises(InvalidInputError):
        calculate_three_contact_loads(mass_kg=1.0, cg_x_m=0.0, cg_y_m=0.0, contacts=line)
    with pytest.raises(InvalidInputError):
        calculate_three_contact_loads(mass_kg=1.0, cg_x_m=0.0, cg_y_m=0.0, contacts=TRI[:2])
    with pytest.raises(InvalidInputError):
        calculate_three_contact_loads(mass_kg=0.0, cg_x_m=0.0, cg_y_m=0.0, contacts=TRI)


def test_convex_hull_orders_counter_clockwise_and_drops_interior() -> None:
    pts = [(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5), (0.5, 0.0)]
    hull = convex_hull(pts)
    assert set(hull) == {(0, 0), (1, 0), (1, 1), (0, 1)}
    area2 = sum(
        hull[i][0] * hull[(i + 1) % 4][1] - hull[(i + 1) % 4][0] * hull[i][1] for i in range(4)
    )
    assert area2 > 0  # counter-clockwise


def test_polygon_margin_hand_computed() -> None:
    # CoG (-0.05, 0). Front edge x=0: distance 0.05. Side edges: 0.0225/0.25 = 0.09.
    r = calculate_support_polygon_stability(cg_x_m=-0.05, cg_y_m=0.0, contacts=TRI)
    assert r.margin_m.value == pytest.approx(0.05)
    assert r.status is StabilityStatus.STABLE


def test_polygon_margin_unstable_marginal_unknown() -> None:
    out = calculate_support_polygon_stability(cg_x_m=0.1, cg_y_m=0.0, contacts=TRI)
    assert out.margin_m.value == pytest.approx(-0.1)
    assert out.status is StabilityStatus.UNSTABLE
    on_edge = calculate_support_polygon_stability(cg_x_m=0.0, cg_y_m=0.0, contacts=TRI)
    assert on_edge.margin_m.value == pytest.approx(0.0)
    assert on_edge.status is StabilityStatus.MARGINAL
    unknown = calculate_support_polygon_stability(cg_x_m=None, cg_y_m=0.0, contacts=TRI)
    assert unknown.status is StabilityStatus.UNKNOWN
    assert unknown.margin_m.value is None


def test_polygon_margin_agrees_with_rectangle_model() -> None:
    # Same rectangle as the four-wheel model: margin must equal min(L/2-|x|, W/2-|y|).
    rect = [
        ContactPoint("fl", 0.25, 0.2),
        ContactPoint("fr", 0.25, -0.2),
        ContactPoint("rl", -0.25, 0.2),
        ContactPoint("rr", -0.25, -0.2),
    ]
    r = calculate_support_polygon_stability(cg_x_m=0.1, cg_y_m=0.05, contacts=rect)
    assert r.margin_m.value == pytest.approx(min(0.25 - 0.1, 0.2 - 0.05))


def test_non_finite_inputs_rejected() -> None:
    with pytest.raises(InvalidInputError):
        calculate_support_polygon_stability(cg_x_m=math.nan, cg_y_m=0.0, contacts=TRI)
    with pytest.raises(InvalidInputError):
        calculate_support_polygon_stability(cg_x_m=0.0, cg_y_m=0.0, contacts=TRI[:2])
