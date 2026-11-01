"""Structured, versioned component datasheet models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator

CURRENT_COMPONENT_SCHEMA_VERSION: Literal[1] = 1


class ComponentCategory(str, Enum):
    CONTROLLER = "controller"
    MOTOR = "motor"
    BATTERY = "battery"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    POWER = "power"
    DISPLAY = "display"
    AUDIO = "audio"
    MECHANICAL = "mechanical"
    COMMUNICATION = "communication"
    OTHER = "other"


class ComponentStatus(str, Enum):
    VERIFIED = "verified"
    CUSTOM = "custom"
    INCOMPLETE = "incomplete"


class ComponentParameter(BaseModel):
    """One datasheet field. Unknown values remain None, never zero."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    value: float | str | bool | None = None
    unit: str | None = Field(default=None, max_length=32)
    source_page: str | None = Field(default=None, max_length=80)


class ComponentDocument(BaseModel):
    """Portable component record. The library intentionally has no seed records."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = CURRENT_COMPONENT_SCHEMA_VERSION
    id: UUID
    name: str = Field(min_length=1, max_length=160)
    category: ComponentCategory
    status: ComponentStatus = ComponentStatus.INCOMPLETE
    manufacturer: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2_000)
    datasheet_url: AnyHttpUrl | None = None
    parameters: list[ComponentParameter] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def verified_requires_datasheet(self) -> ComponentDocument:
        if self.status is ComponentStatus.VERIFIED and self.datasheet_url is None:
            raise ValueError("verified components must include a datasheet URL")
        return self


class ComponentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
    category: ComponentCategory
    status: ComponentStatus = ComponentStatus.INCOMPLETE
    manufacturer: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2_000)
    datasheet_url: AnyHttpUrl | None = None
    parameters: list[ComponentParameter] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def verified_requires_datasheet(self) -> ComponentCreate:
        if self.status is ComponentStatus.VERIFIED and self.datasheet_url is None:
            raise ValueError("verified components must include a datasheet URL")
        return self


class ComponentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=160)
    category: ComponentCategory | None = None
    status: ComponentStatus | None = None
    manufacturer: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2_000)
    datasheet_url: AnyHttpUrl | None = None
    parameters: list[ComponentParameter] | None = None
    missing_fields: list[str] | None = None


class ComponentSummary(BaseModel):
    id: UUID
    name: str
    category: ComponentCategory
    status: ComponentStatus
    manufacturer: str | None
    model: str | None
    revision: int
    updated_at: datetime


def migrate_component_document(raw: dict[str, Any]) -> ComponentDocument:
    """Validate the supported component schema and reject unknown versions."""

    version = raw.get("schema_version")
    if version != CURRENT_COMPONENT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported component schema version: {version!r}")
    return ComponentDocument.model_validate(raw)
