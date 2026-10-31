"""Project use cases: CRUD, duplicate, export/import, history, restore."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application import components as comp_svc
from app.domain.component import ComponentSpec
from app.domain.project import CURRENT_SCHEMA_VERSION, ProjectData, ProjectInfo
from app.infrastructure.database import ComponentRow, ProjectRow, RevisionRow, utcnow
from app.infrastructure.migrations import migrate_to_current

PROJECT_BUNDLE_FORMAT = "robotlab-project"


class ProjectNotFoundError(LookupError):
    pass


class RevisionConflictError(RuntimeError):
    pass


def _data(row: ProjectRow) -> ProjectData:
    return ProjectData.model_validate(migrate_to_current(dict(row.data)))


def _snapshot(session: Session, row: ProjectRow, summary: str) -> None:
    session.add(
        RevisionRow(project_id=row.id, revision=row.revision, summary=summary, data=row.data)
    )


def create_project(session: Session, data: ProjectData, *, summary: str = "created") -> ProjectRow:
    row = ProjectRow(
        id=str(uuid.uuid4()),
        name=data.info.name,
        description=data.info.description,
        schema_version=data.schema_version,
        revision=1,
        data=data.model_dump(mode="json"),
    )
    session.add(row)
    session.flush()
    _snapshot(session, row, summary)
    session.commit()
    return row


def new_project_data(name: str, description: str = "") -> ProjectData:
    return ProjectData(info=ProjectInfo(name=name, description=description))


def get_row(session: Session, project_id: str) -> ProjectRow:
    row = session.get(ProjectRow, project_id)
    if row is None:
        raise ProjectNotFoundError(project_id)
    return row


def get_project_data(session: Session, project_id: str) -> ProjectData:
    return _data(get_row(session, project_id))


def list_projects(session: Session) -> list[ProjectRow]:
    return list(session.scalars(select(ProjectRow).order_by(ProjectRow.updated_at.desc())))


def update_project(
    session: Session,
    project_id: str,
    data: ProjectData,
    *,
    summary: str = "",
    expected_revision: int | None = None,
) -> ProjectRow:
    row = get_row(session, project_id)
    if expected_revision is not None and expected_revision != row.revision:
        raise RevisionConflictError(
            f"revision conflict: server has {row.revision}, client sent {expected_revision}"
        )
    row.revision += 1
    row.name = data.info.name
    row.description = data.info.description
    row.schema_version = data.schema_version
    row.data = data.model_dump(mode="json")
    row.updated_at = utcnow()
    _snapshot(session, row, summary or "update")
    session.commit()
    return row


def delete_project(session: Session, project_id: str) -> None:
    row = get_row(session, project_id)
    for rev in session.scalars(select(RevisionRow).where(RevisionRow.project_id == project_id)):
        session.delete(rev)
    session.delete(row)
    session.commit()


def duplicate_project(session: Session, project_id: str, new_name: str | None = None) -> ProjectRow:
    data = get_project_data(session, project_id)
    copy = data.model_copy(deep=True)
    copy.info.name = new_name or f"{data.info.name} (copy)"
    copy.results = {}
    return create_project(session, copy, summary=f"duplicated from {project_id}")


def history(session: Session, project_id: str) -> list[RevisionRow]:
    get_row(session, project_id)
    stmt = (
        select(RevisionRow)
        .where(RevisionRow.project_id == project_id)
        .order_by(RevisionRow.revision.desc())
    )
    return list(session.scalars(stmt))


def restore_revision(session: Session, project_id: str, revision: int) -> ProjectRow:
    stmt = select(RevisionRow).where(
        RevisionRow.project_id == project_id, RevisionRow.revision == revision
    )
    rev = session.scalars(stmt).first()
    if rev is None:
        raise ProjectNotFoundError(f"{project_id} revision {revision}")
    data = ProjectData.model_validate(migrate_to_current(dict(rev.data)))
    return update_project(session, project_id, data, summary=f"restored revision {revision}")


def export_project(session: Session, project_id: str) -> dict[str, Any]:
    data = get_project_data(session, project_id)
    library = comp_svc.library_map(session)
    used = sorted({c.component_id for c in data.components})
    return {
        "format": PROJECT_BUNDLE_FORMAT,
        "bundle_version": 1,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "project": data.model_dump(mode="json"),
        "components": [library[i].model_dump(mode="json") for i in used if i in library],
    }


def import_project(session: Session, bundle: dict[str, Any]) -> ProjectRow:
    if bundle.get("format") != PROJECT_BUNDLE_FORMAT:
        raise ValueError("not a RobotLab project bundle")
    raw = migrate_to_current(dict(bundle["project"]))
    data = ProjectData.model_validate(raw)
    remap: dict[str, str] = {}
    for rc in bundle.get("components", []):
        spec = ComponentSpec.model_validate(rc)
        existing = session.get(ComponentRow, spec.id)
        if existing is None:
            comp_svc.create_component(session, spec)
        elif existing.data != spec.model_dump(mode="json"):
            new_id = f"{spec.id}-{uuid.uuid4().hex[:6]}"
            comp_svc.create_component(session, spec.model_copy(update={"id": new_id}))
            remap[spec.id] = new_id
    for inst in data.components:
        inst.component_id = remap.get(inst.component_id, inst.component_id)
    return create_project(session, data, summary="imported")


def get_project_data_from_row(row: ProjectRow) -> ProjectData:
    return _data(row)
