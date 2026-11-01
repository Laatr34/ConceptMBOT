"""HTTP endpoints for project lifecycle management."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.application import project_service
from app.application.project_service import ProjectNotFoundError
from app.domain.projects import (
    ProjectCreate,
    ProjectDocument,
    ProjectHistoryEntry,
    ProjectMechanicalData,
    ProjectSummary,
    ProjectUpdate,
)
from app.infrastructure.database import get_session
from app.infrastructure.project_models import ProjectRecord, ProjectRevisionRecord

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _not_found(error: ProjectNotFoundError) -> HTTPException:
    return HTTPException(status_code=404, detail="Project not found")


@router.get("", response_model=list[ProjectSummary])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectSummary]:
    return project_service.list_projects(session)


@router.post("", response_model=ProjectDocument, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate, session: Session = Depends(get_session)
) -> ProjectDocument:
    return project_service.create_project(session, payload)


@router.post("/import", response_model=ProjectDocument, status_code=status.HTTP_201_CREATED)
def import_project(
    payload: dict[str, Any], session: Session = Depends(get_session)
) -> ProjectDocument:
    try:
        return project_service.import_project(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{project_id}", response_model=ProjectDocument)
def get_project(project_id: UUID, session: Session = Depends(get_session)) -> ProjectDocument:
    try:
        return project_service.get_project(session, project_id)
    except ProjectNotFoundError as error:
        raise _not_found(error) from error


@router.patch("/{project_id}", response_model=ProjectDocument)
def update_project(
    project_id: UUID, payload: ProjectUpdate, session: Session = Depends(get_session)
) -> ProjectDocument:
    try:
        return project_service.update_project(session, project_id, payload)
    except ProjectNotFoundError as error:
        raise _not_found(error) from error


@router.put("/{project_id}/autosave", response_model=ProjectDocument)
def autosave_project(
    project_id: UUID, payload: ProjectUpdate, session: Session = Depends(get_session)
) -> ProjectDocument:
    try:
        return project_service.update_project(session, project_id, payload, action="autosaved")
    except ProjectNotFoundError as error:
        raise _not_found(error) from error


@router.post("/{project_id}/duplicate", response_model=ProjectDocument)
def duplicate_project(project_id: UUID, session: Session = Depends(get_session)) -> ProjectDocument:
    try:
        return project_service.duplicate_project(session, project_id)
    except ProjectNotFoundError as error:
        raise _not_found(error) from error


@router.get("/{project_id}/export", response_model=ProjectDocument)
def export_project(project_id: UUID, session: Session = Depends(get_session)) -> ProjectDocument:
    try:
        return project_service.get_project(session, project_id)
    except ProjectNotFoundError as error:
        raise _not_found(error) from error


@router.get("/{project_id}/history", response_model=list[ProjectHistoryEntry])
def get_project_history(
    project_id: UUID, session: Session = Depends(get_session)
) -> list[ProjectHistoryEntry]:
    try:
        return project_service.project_history(session, project_id)
    except ProjectNotFoundError as error:
        raise _not_found(error) from error


@router.get("/{project_id}/mechanical", response_model=ProjectMechanicalData)
def get_project_mechanical_layout(
    project_id: UUID, session: Session = Depends(get_session)
) -> ProjectMechanicalData:
    try:
        project = project_service.get_project(session, project_id)
    except ProjectNotFoundError as error:
        raise _not_found(error) from error
    return ProjectMechanicalData.model_validate(project.data["mechanical"])


@router.put("/{project_id}/mechanical", response_model=ProjectMechanicalData)
def update_project_mechanical_layout(
    project_id: UUID,
    payload: ProjectMechanicalData,
    session: Session = Depends(get_session),
) -> ProjectMechanicalData:
    try:
        project = project_service.get_project(session, project_id)
        data = {**project.data, "mechanical": payload.model_dump(mode="json")}
        updated = project_service.update_project(
            session,
            project_id,
            ProjectUpdate(data=data),
            action="mechanical_layout_updated",
        )
    except ProjectNotFoundError as error:
        raise _not_found(error) from error
    return ProjectMechanicalData.model_validate(updated.data["mechanical"])


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, session: Session = Depends(get_session)) -> Response:
    record = session.get(ProjectRecord, str(project_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Project not found")
    session.execute(
        delete(ProjectRevisionRecord).where(ProjectRevisionRecord.project_id == str(project_id))
    )
    session.delete(record)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
