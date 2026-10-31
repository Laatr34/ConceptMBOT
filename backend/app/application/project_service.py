"""Project use cases; persistence is injected through a SQLAlchemy session."""
from __future__ import annotations
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.projects import ProjectCreate, ProjectDocument, ProjectHistoryEntry, ProjectSummary, ProjectUpdate, migrate_project_document
from app.infrastructure.project_models import ProjectRecord, ProjectRevisionRecord
class ProjectNotFoundError(LookupError):
    """Raised when a project does not exist."""
def _now() -> datetime:
    return datetime.now(UTC)
def _document(record: ProjectRecord) -> ProjectDocument:
    return migrate_project_document(record.document)
def _summary(record: ProjectRecord) -> ProjectSummary:
    return ProjectSummary(id=UUID(record.id), name=record.name, description=record.description,
        schema_version=int(record.document["schema_version"]), revision=record.revision,
        created_at=record.created_at, updated_at=record.updated_at)
def _record_history(session: Session, record: ProjectRecord, action: str) -> None:
    session.add(ProjectRevisionRecord(project_id=record.id, revision=record.revision,
        action=action, snapshot=deepcopy(record.document), created_at=_now()))
def list_projects(session: Session) -> list[ProjectSummary]:
    rows = session.scalars(select(ProjectRecord).order_by(ProjectRecord.updated_at.desc(), ProjectRecord.name)).all()
    return [_summary(row) for row in rows]
def get_project(session: Session, project_id: UUID) -> ProjectDocument:
    record = session.get(ProjectRecord, str(project_id))
    if record is None:
        raise ProjectNotFoundError(str(project_id))
    return _document(record)
def create_project(session: Session, payload: ProjectCreate) -> ProjectDocument:
    now = _now()
    doc = ProjectDocument(id=uuid4(), name=payload.name, description=payload.description,
        created_at=now, updated_at=now, data=payload.data)
    record = ProjectRecord(id=str(doc.id), name=doc.name, description=doc.description,
        document=doc.model_dump(mode="json"), revision=1, created_at=now, updated_at=now)
    session.add(record)
    _record_history(session, record, "created")
    session.commit()
    return doc
def update_project(session: Session, project_id: UUID, payload: ProjectUpdate, *, action: str = "updated") -> ProjectDocument:
    record = session.get(ProjectRecord, str(project_id))
    if record is None:
        raise ProjectNotFoundError(str(project_id))
    current = _document(record)
    changes = payload.model_dump(exclude_unset=True)
    doc = current.model_copy(update={**changes, "updated_at": _now()})
    record.name, record.description = doc.name, doc.description
    record.document = doc.model_dump(mode="json")
    record.revision += 1
    record.updated_at = doc.updated_at
    _record_history(session, record, action)
    session.commit()
    return doc
def duplicate_project(session: Session, project_id: UUID) -> ProjectDocument:
    source = get_project(session, project_id)
    now = _now()
    doc = ProjectDocument(id=uuid4(), name=f"{source.name} (copy)"[:120],
        description=source.description, created_at=now, updated_at=now, data=deepcopy(source.data))
    record = ProjectRecord(id=str(doc.id), name=doc.name, description=doc.description,
        document=doc.model_dump(mode="json"), revision=1, created_at=now, updated_at=now)
    session.add(record)
    _record_history(session, record, "duplicated")
    session.commit()
    return doc
def import_project(session: Session, raw: dict[str, Any]) -> ProjectDocument:
    imported = migrate_project_document(raw)
    now = _now()
    doc = imported.model_copy(update={"id": uuid4(), "created_at": now, "updated_at": now})
    record = ProjectRecord(id=str(doc.id), name=doc.name, description=doc.description,
        document=doc.model_dump(mode="json"), revision=1, created_at=now, updated_at=now)
    session.add(record)
    _record_history(session, record, "imported")
    session.commit()
    return doc
def project_history(session: Session, project_id: UUID) -> list[ProjectHistoryEntry]:
    if session.get(ProjectRecord, str(project_id)) is None:
        raise ProjectNotFoundError(str(project_id))
    rows = session.scalars(select(ProjectRevisionRecord).where(
        ProjectRevisionRecord.project_id == str(project_id)).order_by(ProjectRevisionRecord.revision.desc())).all()
    return [ProjectHistoryEntry(revision=row.revision, action=row.action, created_at=row.created_at) for row in rows]
