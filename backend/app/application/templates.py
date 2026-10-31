"""Project templates. The museum-robot template mirrors docs/hardware (inventory only)."""

from __future__ import annotations

import json
import re
from importlib import resources
from typing import Any

from sqlalchemy.orm import Session

from app.application import components as comp_svc
from app.domain.component import Category, ComponentOrigin, ComponentSpec
from app.domain.project import (
    BatteryConfig,
    ComponentInstance,
    ElectricalConfig,
    MotorizationConfig,
    PowerLink,
    ProjectData,
    ProjectInfo,
    Rail,
)
from app.infrastructure.database import ComponentRow

MUSEUM_ROBOT = "museum-robot"


def load_bom() -> dict[str, Any]:
    text = resources.files("app.data").joinpath("museum_robot_bom.json").read_text("utf-8")
    return json.loads(text)  # type: ignore[no-any-return]


def _quantity(text: str) -> int:
    """Ranges use the lower bound; 'several'/'lot' -> 1 (placeholder, owner to refine)."""
    m = re.match(r"\s*(\d+)", text)
    return int(m.group(1)) if m else 1


def build_museum_robot(session: Session) -> ProjectData:
    bom = load_bom()
    instances: list[ComponentInstance] = []
    by_name: dict[str, str] = {}
    for item in bom["items"]:
        cid = f"bom-{item['ref']:02d}"
        if session.get(ComponentRow, cid) is None:
            comp_svc.create_component(
                session,
                ComponentSpec(
                    id=cid,
                    name=item["name"],
                    category=Category(item["component_category"]),
                    origin=ComponentOrigin.LIBRARY,
                    sources=["docs/hardware/liste-materiel-robot-musee.pdf (inventory only)"],
                    notes="Placeholder from inventory. No datasheet values known.",
                ),
            )
        inst_id = f"i{item['ref']:02d}"
        by_name[item["name"]] = inst_id
        instances.append(
            ComponentInstance(
                id=inst_id,
                component_id=cid,
                label=item["name"],
                quantity=_quantity(item["quantity_text"]),
            )
        )

    def iid(name: str) -> str:
        return by_name[name]

    # Rails: nominal voltages come from the document names ("12 V", "12→5 V", "12→6 V").
    rails = [
        Rail(id="r12", name="12 V", voltage_v=12.0, source_instance_id=iid("Batterie 12 V")),
        Rail(
            id="r5", name="5 V", voltage_v=5.0, source_instance_id=iid("Convertisseur DC-DC 12→5 V")
        ),
        Rail(
            id="r6", name="6 V", voltage_v=6.0, source_instance_id=iid("Convertisseur DC-DC 12→6 V")
        ),
    ]
    # Links only where the document's "utility" column states them (or is implied by "12 V motors").
    links = [
        PowerLink(load_instance_id=iid("Convertisseur DC-DC 12→5 V"), rail_id="r12"),
        PowerLink(load_instance_id=iid("Convertisseur DC-DC 12→6 V"), rail_id="r12"),
        PowerLink(load_instance_id=iid("Moteurs DC 12 V avec encodeurs"), rail_id="r12"),
        PowerLink(load_instance_id=iid("Driver moteur"), rail_id="r12"),
        PowerLink(load_instance_id=iid("Raspberry Pi 5 – 8 Go"), rail_id="r5"),
        PowerLink(load_instance_id=iid("Servomoteurs MG996R"), rail_id="r6"),
    ]
    return ProjectData(
        info=ProjectInfo(
            name="Robot Musée Interactif",
            description=(
                "Template generated from docs/hardware/liste-materiel-robot-musee.pdf. "
                "Inventory only: no datasheet values. Quantity ranges use the lower bound; "
                "'several'/'lot' count as 1 (placeholder). Rails and power links are limited to "
                "what the document states; wiring and grounds must be completed by the owner."
            ),
            robot_type="differential",
        ),
        components=instances,
        electrical=ElectricalConfig(rails=rails, power_links=links),
        battery=BatteryConfig(instance_id=iid("Batterie 12 V")),
        motorization=MotorizationConfig(
            motor_instance_id=iid("Moteurs DC 12 V avec encodeurs"),
            driver_instance_id=iid("Driver moteur"),
            motor_count=2,
        ),
    )
