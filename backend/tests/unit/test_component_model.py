import pytest
from pydantic import ValidationError

from app.domain.component import Category, ComponentSpec, ComponentStatus, required_fields


def test_unknown_values_are_none_not_zero():
    c = ComponentSpec(id="a", name="Pi", category=Category.SBC)
    assert c.nominal_voltage_v is None and c.mass_kg is None
    assert c.status is ComponentStatus.INCOMPLETE
    assert "nominal_voltage_v" in c.missing_required()


def test_alternative_required_fields():
    base = {
        "id": "a",
        "name": "x",
        "category": Category.CAMERA,
        "nominal_voltage_v": 5.0,
        "min_voltage_v": 4.5,
        "max_voltage_v": 5.5,
        "max_current_a": 1.0,
        "mass_kg": 0.1,
    }
    c = ComponentSpec(**base)
    assert c.missing_required() == ["nominal_current_a|power_w"]
    assert ComponentSpec(**base, power_w=2.0).status is ComponentStatus.CUSTOM


def test_verified_needs_flag_and_source():
    spec = {
        "id": "a",
        "name": "frame",
        "category": Category.CHASSIS,
        "mass_kg": 2.0,
    }
    assert ComponentSpec(**spec).status is ComponentStatus.CUSTOM
    assert ComponentSpec(**spec, verified=True).status is ComponentStatus.CUSTOM
    assert ComponentSpec(**spec, verified=True, sources=["datasheet p.3"]).status is (
        ComponentStatus.VERIFIED
    )


@pytest.mark.parametrize(
    "kw",
    [
        {"min_voltage_v": 6.0, "max_voltage_v": 5.0},
        {"nominal_voltage_v": -1.0},
        {"efficiency": 1.2},
        {"rated_torque_nm": 2.0, "stall_torque_nm": 1.0},
        {"nominal_current_a": 3.0, "max_current_a": 2.0},
        {"mass_kg": -0.1},
    ],
)
def test_invalid_specs_rejected(kw):
    with pytest.raises(ValidationError):
        ComponentSpec(id="a", name="x", category=Category.OTHER, **kw)


def test_every_category_has_a_required_list():
    for cat in Category:
        assert required_fields(cat)
