"""Builders for engine tests (fictional test data, never used as product data)."""

from __future__ import annotations

from app.domain.component import Category, ComponentSpec
from app.domain.project import (
    ComponentInstance,
    ElectricalConfig,
    GroundNet,
    PowerLink,
    ProjectData,
    ProjectInfo,
    Rail,
)


def spec(cid: str, category: Category, **kw: object) -> ComponentSpec:
    return ComponentSpec(id=cid, name=cid, category=category, **kw)  # type: ignore[arg-type]


def inst(iid: str, cid: str, **kw: object) -> ComponentInstance:
    return ComponentInstance(id=iid, component_id=cid, label=iid, **kw)  # type: ignore[arg-type]


def power_chain(*, conv_limit: float = 3.0) -> tuple[ProjectData, dict[str, ComponentSpec]]:
    """Battery(12 V) -> converter(12->5 V, eta 0.9) -> Pi + sensor ; motor on 12 V rail."""
    lib = {
        "bat": spec(
            "bat",
            Category.BATTERY,
            nominal_voltage_v=12.0,
            max_current_a=20.0,
            capacity_ah=5.0,
            mass_kg=0.5,
        ),
        "dcdc": spec(
            "dcdc",
            Category.DCDC_CONVERTER,
            min_voltage_v=9.0,
            max_voltage_v=18.0,
            output_voltage_v=5.0,
            output_max_current_a=conv_limit,
            efficiency=0.9,
            mass_kg=0.05,
        ),
        "pi": spec(
            "pi",
            Category.SBC,
            nominal_voltage_v=5.0,
            min_voltage_v=4.75,
            max_voltage_v=5.25,
            nominal_current_a=1.2,
            peak_current_a=2.0,
            mass_kg=0.05,
        ),
        "sens": spec(
            "sens",
            Category.CAMERA,
            nominal_voltage_v=5.0,
            min_voltage_v=4.5,
            max_voltage_v=5.5,
            power_w=5.0,
            max_current_a=1.5,
            mass_kg=0.1,
        ),
        "mot": spec(
            "mot",
            Category.DC_MOTOR,
            nominal_voltage_v=12.0,
            min_voltage_v=6.0,
            max_voltage_v=13.0,
            rated_torque_nm=0.5,
            stall_torque_nm=2.0,
            no_load_speed_rpm=200.0,
            no_load_current_a=0.2,
            stall_current_a=4.0,
            mass_kg=0.3,
        ),
    }
    project = ProjectData(
        info=ProjectInfo(name="t"),
        components=[
            inst("b", "bat"),
            inst("c", "dcdc"),
            inst("pi", "pi"),
            inst("s", "sens"),
            inst("m", "mot", quantity=2),
        ],
        electrical=ElectricalConfig(
            rails=[
                Rail(id="r12", name="12V", voltage_v=12.0, source_instance_id="b"),
                Rail(id="r5", name="5V", voltage_v=5.0, source_instance_id="c"),
            ],
            power_links=[
                PowerLink(load_instance_id="c", rail_id="r12"),
                PowerLink(load_instance_id="m", rail_id="r12"),
                PowerLink(load_instance_id="pi", rail_id="r5"),
                PowerLink(load_instance_id="s", rail_id="r5"),
            ],
            ground_nets=[GroundNet(id="g", instance_ids=["b", "c", "pi", "s", "m"])],
        ),
    )
    return project, lib
