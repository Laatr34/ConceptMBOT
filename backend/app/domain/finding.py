"""Diagnostic finding (bilingual). Never hidden: every finding is reported."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    INFO = "info"


SEVERITY_ORDER = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.INFO: 3}


class Text(BaseModel):
    model_config = ConfigDict(frozen=True)
    en: str
    fr: str

    def get(self, lang: str) -> str:
        return self.fr if lang == "fr" else self.en


class Finding(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    severity: Severity
    category: str  # electrical | battery | motor | mechanical | interfaces | data
    component_id: str | None
    component_label: str | None
    problem: Text
    value: float | None = None
    unit: str | None = None
    limit: float | None = None
    limit_source: str | None = None  # manufacturer source when the limit is a datasheet value
    explanation: Text
    suggestion: Text


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.category, f.code))
