from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.application import components as svc
from app.domain.component import ComponentSpec, ComponentStatus
from app.infrastructure.database import get_session

router = APIRouter(prefix="/components", tags=["components"])
Db = Annotated[Session, Depends(get_session)]


class LibraryImport(BaseModel):
    bundle: dict[str, Any]
    overwrite: bool = False


@router.get("")
def list_(
    db: Db,
    q: str | None = None,
    category: str | None = None,
    status: Annotated[ComponentStatus | None, Query()] = None,
) -> list[dict[str, Any]]:
    return [
        svc.component_view(s)
        for s in svc.list_components(db, q=q, category=category, status=status)
    ]


@router.get("/export")
def export(db: Db) -> dict[str, Any]:
    return svc.export_library(svc.list_components(db))


@router.post("/import")
def import_(body: LibraryImport, db: Db) -> dict[str, int]:
    try:
        return svc.import_library(db, body.bundle, overwrite=body.overwrite)
    except (ValueError, ValidationError) as e:
        raise HTTPException(422, str(e)) from e


@router.post("", status_code=201)
def create(spec: ComponentSpec, db: Db) -> dict[str, Any]:
    try:
        return svc.component_view(svc.create_component(db, spec))
    except svc.ComponentExistsError as e:
        raise HTTPException(409, str(e)) from e


@router.get("/{component_id}")
def get(component_id: str, db: Db) -> dict[str, Any]:
    try:
        return svc.component_view(svc.get_component(db, component_id))
    except svc.ComponentNotFoundError as e:
        raise HTTPException(404, f"component not found: {e}") from e


@router.put("/{component_id}")
def update(component_id: str, spec: ComponentSpec, db: Db) -> dict[str, Any]:
    try:
        return svc.component_view(svc.update_component(db, component_id, spec))
    except svc.ComponentNotFoundError as e:
        raise HTTPException(404, f"component not found: {e}") from e
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.delete("/{component_id}", status_code=204)
def delete(component_id: str, db: Db) -> Response:
    try:
        svc.delete_component(db, component_id)
    except svc.ComponentNotFoundError as e:
        raise HTTPException(404, f"component not found: {e}") from e
    return Response(status_code=204)
