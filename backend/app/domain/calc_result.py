"""Traceable calculation result.

Every engine returns a ``CalcResult``. See docs/CONVENTIONS.md.

Invariant: ``value is None`` if and only if ``status == NOT_EVALUABLE``.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResultStatus(str, Enum):
    THEORETICAL = "theoretical"
    ESTIMATED = "estimated"
    MEASURED = "measured"
    NOT_EVALUABLE = "not_evaluable"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class CalcResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    value: float | None
    unit: str
    formula: str = Field(min_length=1)
    inputs: dict[str, float | None] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    status: ResultStatus
    confidence: Confidence = Confidence.UNKNOWN
    limits: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_invariants(self) -> CalcResult:
        not_evaluable = self.status is ResultStatus.NOT_EVALUABLE
        if not_evaluable and self.value is not None:
            raise ValueError("a not_evaluable result must have value=None")
        if not not_evaluable and self.value is None:
            raise ValueError("value=None requires status=not_evaluable")
        if not_evaluable and not (self.missing_inputs or self.limits):
            raise ValueError("a not_evaluable result must list missing_inputs or limits")
        return self

    @classmethod
    def not_evaluable(
        cls,
        *,
        name: str,
        unit: str,
        formula: str,
        missing_inputs: list[str],
        inputs: dict[str, float | None] | None = None,
    ) -> CalcResult:
        return cls(
            name=name,
            value=None,
            unit=unit,
            formula=formula,
            inputs=inputs or {},
            status=ResultStatus.NOT_EVALUABLE,
            confidence=Confidence.UNKNOWN,
            missing_inputs=missing_inputs,
        )
