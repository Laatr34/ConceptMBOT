from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.schemas import (
    DuplicateRequest,
    ImportRequest,
    ProjectCreate,
    ProjectDetail,
    ProjectSummary,
    ProjectUpdate,
    RevisionOut,
)
from app.application import projects as svc
from app.application import templates
from app.infrastructure.database import ProjectRow, get_session
from app.infrastructure.migrations import SchemaVersionError

router = APIRouter(prefix="/projects", tags=["projects"])
Db = Annotated[Session, Depends(get_session)]


def _summary(row: ProjectRow) -> ProjectSummary:
    return ProjectSummary(
        id=row.id,
        name=row.name,
        description=row.description,
        revision=row.revision,
        schema_version=row.schema_version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _detail(row: ProjectRow) -> ProjectDetail:
    s = _summary(row)
    return ProjectDetail(**s.model_dump(), data=svc.get_project_data_from_row(row))


def _guard(fn: Any) -> Any:
    try:
        return fn()
    except svc.ProjectNotFoundError as e:
        raise HTTPException(404, f"project not found: {e}") from e
    except svc.RevisionConflictError as e:
        raise HTTPException(409, str(e)) from e
    except (SchemaVersionError, ValidationError, ValueError) as e:
        raise HTTPException(422, str(e)) from e


@router.get("", response_model=list[ProjectSummary])
def list_projects(db: Db) -> list[ProjectSummary]:
    return [_summary(r) for r in svc.list_projects(db)]


@router.post("", response_model=ProjectDetail, status_code=201)
def create(body: ProjectCreate, db: Db) -> ProjectDetail:
    row = svc.create_project(db, svc.new_project_data(body.name, body.description))
    return _detail(row)


@router.post("/from-template/{template}", response_model=ProjectDetail, status_code=201)
def from_template(template: str, db: Db) -> ProjectDetail:
    if template != templates.MUSEUM_ROBOT:
        raise HTTPException(404, f"unknown template {template}")
    data = templates.build_museum_robot(db)
    return _detail(svc.create_project(db, data, summary="created from template"))


@router.post("/import", response_model=ProjectDetail, status_code=201)
def import_(body: ImportRequest, db: Db) -> ProjectDetail:
    return _detail(_guard(lambda: svc.import_project(db, body.bundle)))


@router.get("/{project_id}", response_model=ProjectDetail)
def get(project_id: str, db: Db) -> ProjectDetail:
    return _detail(_guard(lambda: svc.get_row(db, project_id)))


@router.put("/{project_id}", response_model=ProjectDetail)
def update(project_id: str, body: ProjectUpdate, db: Db) -> ProjectDetail:
    row = _guard(
        lambda: svc.update_project(
            db,
            project_id,
            body.data,
            summary=body.summary,
            expected_revision=body.expected_revision,
        )
    )
    return _detail(row)


@router.delete("/{project_id}", status_code=204)
def delete(project_id: str, db: Db) -> Response:
    _guard(lambda: svc.delete_project(db, project_id))
    return Response(status_code=204)


@router.post("/{project_id}/duplicate", response_model=ProjectDetail, status_code=201)
def duplicate(project_id: str, body: DuplicateRequest, db: Db) -> ProjectDetail:
    return _detail(_guard(lambda: svc.duplicate_project(db, project_id, body.name)))


@router.get("/{project_id}/export")
def export(project_id: str, db: Db) -> dict[str, Any]:
    return _guard(lambda: svc.export_project(db, project_id))  # type: ignore[no-any-return]


@router.get("/{project_id}/history", response_model=list[RevisionOut])
def history(project_id: str, db: Db) -> list[RevisionOut]:
    rows = _guard(lambda: svc.history(db, project_id))
    return [
        RevisionOut(revision=r.revision, summary=r.summary, created_at=r.created_at) for r in rows
    ]


@router.post("/{project_id}/history/{revision}/restore", response_model=ProjectDetail)
def restore(project_id: str, revision: int, db: Db) -> ProjectDetail:
    return _detail(_guard(lambda: svc.restore_revision(db, project_id, revision)))
