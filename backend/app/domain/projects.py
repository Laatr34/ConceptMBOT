"""Versioned project document models and schema migration entry point."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CURRENT_SCHEMA_VERSION: Literal[2] = 2


class ProjectMechanicalMassPoint(BaseModel):
    """Project-owned placement for one component or assembly mass point."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    component_id: UUID | None = None
    mass_kg: float | None = None
    x_m: float | None = None
    y_m: float | None = None
    z_m: float | None = None


class ProjectMechanicalContact(BaseModel):
    """Ground-contact position in the robot-fixed XY plane."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    x_m: float | None = None
    y_m: float | None = None


class ProjectMechanicalData(BaseModel):
    """Project-specific mechanical layout; unknown measurements remain null."""

    model_config = ConfigDict(extra="forbid")

    mass_points: list[ProjectMechanicalMassPoint] = Field(default_factory=list)
    contacts: list[ProjectMechanicalContact] = Field(default_factory=list)


class ProjectDocument(BaseModel):
    """Portable, versioned JSON representation of a RobotLab project."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = CURRENT_SCHEMA_VERSION
    id: UUID
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2_000)
    created_at: datetime
    updated_at: datetime
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("data", mode="before")
    @classmethod
    def validate_project_data(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("project data must be an object")
        data = dict(value)
        mechanical = ProjectMechanicalData.model_validate(data.get("mechanical", {}))
        data["mechanical"] = mechanical.model_dump(mode="json")
        return data


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
    """Migrate v1 documents explicitly; reject unknown versions instead of guessing."""

    version = raw.get("schema_version")
    migrated = dict(raw)
    if version == 1:
        data = migrated.get("data", {})
        if not isinstance(data, dict):
            raise ValueError("project data must be an object")
        data = dict(data)
        data.setdefault("mechanical", {})
        migrated["data"] = data
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
    elif version != CURRENT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported project schema version: {version!r}")
    return ProjectDocument.model_validate(migrated)
