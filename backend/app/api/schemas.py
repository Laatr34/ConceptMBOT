from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.project import ProjectData


class ProjectSummary(BaseModel):
    id: str
    name: str
    description: str
    revision: int
    schema_version: int
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectSummary):
    data: ProjectData


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""


class ProjectUpdate(BaseModel):
    data: ProjectData
    summary: str = ""
    expected_revision: int | None = None


class DuplicateRequest(BaseModel):
    name: str | None = None


class RevisionOut(BaseModel):
    revision: int
    summary: str
    created_at: datetime


class ImportRequest(BaseModel):
    bundle: dict[str, Any]
