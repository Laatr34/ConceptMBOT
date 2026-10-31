"""Versioned project document models and schema migration entry point."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

CURRENT_SCHEMA_VERSION = 1


class ProjectDocument(BaseModel):
    """Portable, versioned JSON representation of a RobotLab project."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = CURRENT_SCHEMA_VERSION
    id: UUID
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2_000)
    created_at: datetime
    updated_at: datetime
    data: dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2_000)
    data: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Partial update; omitted fields stay unchanged, description may be cleared."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2_000)
    data: dict[str, Any] | None = None

    @model_validator(mode="after")
    def reject_null_replacements(self) -> ProjectUpdate:
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        if "data" in self.model_fields_set and self.data is None:
            raise ValueError("data cannot be null")
        return self


class ProjectSummary(BaseModel):
    id: UUID
    name: str
    description: str | None
    schema_version: int
    revision: int
    created_at: datetime
    updated_at: datetime


class ProjectHistoryEntry(BaseModel):
    revision: int
    action: str
    created_at: datetime


def migrate_project_document(raw: dict[str, Any]) -> ProjectDocument:
    """Validate v1 documents; reject unknown versions instead of guessing."""

    version = raw.get("schema_version")
    if version != CURRENT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported project schema version: {version!r}")
    return ProjectDocument.model_validate(raw)
