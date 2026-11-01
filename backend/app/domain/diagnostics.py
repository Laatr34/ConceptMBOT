"""Structured, traceable diagnostic records shared by calculation modules."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class DiagnosticSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    INFO = "info"


class Diagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    component: str
    problem: str
    value: float | None = None
    unit: str | None = None
    limit: float | None = None
    limit_source: str | None = None
    explanation: str
    correction: str
    severity: DiagnosticSeverity
    source_result: str
    missing_inputs: list[str] = []
