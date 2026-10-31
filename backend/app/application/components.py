"""Component library use cases."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.component import ComponentSpec, ComponentStatus
from app.infrastructure.database import ComponentRow, utcnow

LIBRARY_BUNDLE_FORMAT = "robotlab-components"


class ComponentNotFoundError(LookupError):
    pass


class ComponentExistsError(ValueError):
    pass


def _to_spec(row: ComponentRow) -> ComponentSpec:
    return ComponentSpec.model_validate(row.data)


def component_view(spec: ComponentSpec) -> dict[str, Any]:
    out = spec.model_dump(mode="json")
    out["status"] = spec.status.value
    out["missing_required"] = spec.missing_required()
    return out


def create_component(session: Session, spec: ComponentSpec) -> ComponentSpec:
    if session.get(ComponentRow, spec.id) is not None:
        raise ComponentExistsError(f"component {spec.id} already exists")
    session.add(
        ComponentRow(
            id=spec.id,
            name=spec.name,
            category=spec.category.value,
            data=spec.model_dump(mode="json"),
        )
    )
    session.commit()
    return spec


def get_component(session: Session, component_id: str) -> ComponentSpec:
    row = session.get(ComponentRow, component_id)
    if row is None:
        raise ComponentNotFoundError(component_id)
    return _to_spec(row)


def update_component(session: Session, component_id: str, spec: ComponentSpec) -> ComponentSpec:
    row = session.get(ComponentRow, component_id)
    if row is None:
        raise ComponentNotFoundError(component_id)
    if spec.id != component_id:
        raise ValueError("component id cannot be changed")
    row.name = spec.name
    row.category = spec.category.value
    row.data = spec.model_dump(mode="json")
    row.updated_at = utcnow()
    session.commit()
    return spec


def delete_component(session: Session, component_id: str) -> None:
    row = session.get(ComponentRow, component_id)
    if row is None:
        raise ComponentNotFoundError(component_id)
    session.delete(row)
    session.commit()


def list_components(
    session: Session,
    *,
    q: str | None = None,
    category: str | None = None,
    status: ComponentStatus | None = None,
) -> list[ComponentSpec]:
    stmt = select(ComponentRow).order_by(ComponentRow.name)
    if category:
        stmt = stmt.where(ComponentRow.category == category)
    specs = [_to_spec(r) for r in session.scalars(stmt)]
    if q:
        needle = q.casefold()
        specs = [
            s
            for s in specs
            if needle in s.name.casefold()
            or needle in (s.manufacturer or "").casefold()
            or needle in (s.part_number or "").casefold()
        ]
    if status:
        specs = [s for s in specs if s.status is status]
    return specs


def library_map(session: Session) -> dict[str, ComponentSpec]:
    return {r.id: _to_spec(r) for r in session.scalars(select(ComponentRow))}


def export_library(specs: list[ComponentSpec]) -> dict[str, Any]:
    return {
        "format": LIBRARY_BUNDLE_FORMAT,
        "bundle_version": 1,
        "components": [s.model_dump(mode="json") for s in specs],
    }


def import_library(
    session: Session, bundle: dict[str, Any], *, overwrite: bool = False
) -> dict[str, int]:
    if bundle.get("format") != LIBRARY_BUNDLE_FORMAT:
        raise ValueError("not a RobotLab component library bundle")
    created = updated = skipped = 0
    for raw in bundle.get("components", []):
        spec = ComponentSpec.model_validate(raw)
        row = session.get(ComponentRow, spec.id)
        if row is None:
            session.add(
                ComponentRow(
                    id=spec.id,
                    name=spec.name,
                    category=spec.category.value,
                    data=spec.model_dump(mode="json"),
                )
            )
            created += 1
        elif overwrite:
            row.name = spec.name
            row.category = spec.category.value
            row.data = spec.model_dump(mode="json")
            row.updated_at = utcnow()
            updated += 1
        else:
            skipped += 1
    session.commit()
    return {"created": created, "updated": updated, "skipped": skipped}
