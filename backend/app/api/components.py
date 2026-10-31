"""HTTP endpoints for the component library."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.application import component_service
from app.application.component_service import ComponentNotFoundError
from app.domain.components import ComponentCreate, ComponentDocument, ComponentSummary, ComponentUpdate
from app.infrastructure.database import get_session

router = APIRouter(prefix="/api/components", tags=["components"])


def _not_found(error: ComponentNotFoundError) -> HTTPException:
    return HTTPException(status_code=404, detail="Component not found")


@router.get("", response_model=list[ComponentSummary])
def list_components(session: Session = Depends(get_session)) -> list[ComponentSummary]:
    return component_service.list_components(session)


@router.post("", response_model=ComponentDocument, status_code=status.HTTP_201_CREATED)
def create_component(
    payload: ComponentCreate, session: Session = Depends(get_session)
) -> ComponentDocument:
    return component_service.create_component(session, payload)


@router.post("/import", response_model=ComponentDocument, status_code=status.HTTP_201_CREATED)
def import_component(
    payload: dict[str, Any], session: Session = Depends(get_session)
) -> ComponentDocument:
    try:
        return component_service.import_component(session, payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/{component_id}", response_model=ComponentDocument)
def get_component(
    component_id: UUID, session: Session = Depends(get_session)
) -> ComponentDocument:
    try:
        return component_service.get_component(session, component_id)
    except ComponentNotFoundError as error:
        raise _not_found(error) from error


@router.patch("/{component_id}", response_model=ComponentDocument)
def update_component(
    component_id: UUID, payload: ComponentUpdate, session: Session = Depends(get_session)
) -> ComponentDocument:
    try:
        return component_service.update_component(session, component_id, payload)
    except ComponentNotFoundError as error:
        raise _not_found(error) from error


@router.get("/{component_id}/export", response_model=ComponentDocument)
def export_component(
    component_id: UUID, session: Session = Depends(get_session)
) -> ComponentDocument:
    try:
        return component_service.get_component(session, component_id)
    except ComponentNotFoundError as error:
        raise _not_found(error) from error


@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(
    component_id: UUID, session: Session = Depends(get_session)
) -> Response:
    try:
        component_service.delete_component(session, component_id)
    except ComponentNotFoundError as error:
        raise _not_found(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
