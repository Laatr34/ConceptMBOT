"""Component library use cases."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.components import (
    ComponentCategory,
    ComponentCreate,
    ComponentDocument,
    ComponentStatus,
    ComponentSummary,
    ComponentUpdate,
    migrate_component_document,
)
from app.infrastructure.component_models import ComponentRecord


class ComponentNotFoundError(LookupError):
    """Raised when a component does not exist."""


def _now() -> datetime:
    return datetime.now(UTC)


def _document(record: ComponentRecord) -> ComponentDocument:
    return migrate_component_document(record.document)


def _summary(record: ComponentRecord) -> ComponentSummary:
    return ComponentSummary(
        id=UUID(record.id),
        name=record.name,
        category=ComponentCategory(record.category),
        status=ComponentStatus(record.status),
        manufacturer=record.document.get("manufacturer"),
        model=record.document.get("model"),
        revision=record.revision,
        updated_at=record.updated_at,
    )


def list_components(session: Session) -> list[ComponentSummary]:
    records = session.scalars(
        select(ComponentRecord).order_by(ComponentRecord.category, ComponentRecord.name)
    ).all()
    return [_summary(record) for record in records]


def get_component(session: Session, component_id: UUID) -> ComponentDocument:
    record = session.get(ComponentRecord, str(component_id))
    if record is None:
        raise ComponentNotFoundError(str(component_id))
    return _document(record)


def create_component(session: Session, payload: ComponentCreate) -> ComponentDocument:
    now = _now()
    document = ComponentDocument(
        id=uuid4(),
        **payload.model_dump(),
        created_at=now,
        updated_at=now,
    )
    record = ComponentRecord(
        id=str(document.id),
        name=document.name,
        category=document.category.value,
        status=document.status.value,
        document=document.model_dump(mode="json"),
        revision=1,
        created_at=now,
        updated_at=now,
    )
    session.add(record)
    session.commit()
    return document


def update_component(
    session: Session, component_id: UUID, payload: ComponentUpdate
) -> ComponentDocument:
    record = session.get(ComponentRecord, str(component_id))
    if record is None:
        raise ComponentNotFoundError(str(component_id))
    current = _document(record)
    changes = payload.model_dump(exclude_unset=True)
    document = ComponentDocument.model_validate(
        {
            **current.model_dump(mode="python"),
            **changes,
            "updated_at": _now(),
        }
    )
    record.name = document.name
    record.category = document.category.value
    record.status = document.status.value
    record.document = document.model_dump(mode="json")
    record.revision += 1
    record.updated_at = document.updated_at
    session.commit()
    return document


def delete_component(session: Session, component_id: UUID) -> None:
    record = session.get(ComponentRecord, str(component_id))
    if record is None:
        raise ComponentNotFoundError(str(component_id))
    session.delete(record)
    session.commit()


def import_component(session: Session, raw: dict[str, Any]) -> ComponentDocument:
    imported = migrate_component_document(raw)
    now = _now()
    document = imported.model_copy(
        update={"id": uuid4(), "created_at": now, "updated_at": now}
    )
    record = ComponentRecord(
        id=str(document.id),
        name=document.name,
        category=document.category.value,
        status=document.status.value,
        document=document.model_dump(mode="json"),
        revision=1,
        created_at=now,
        updated_at=now,
    )
    session.add(record)
    session.commit()
    return document
