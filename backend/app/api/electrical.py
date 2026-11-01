"""HTTP boundary for DC rail, regulator, voltage-drop and anomaly calculations."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.domain.calc_result import CalcResult
from app.engines.electrical import (
    ElectricalAnomaly,
    RailLoad,
    calculate_current,
    calculate_power,
    calculate_rail_current,
    calculate_regulator_input_current,
    calculate_regulator_power_loss,
    calculate_voltage_drop,
    detect_rail_anomalies,
)


class RailLoadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    current_a: float | None = None
    power_w: float | None = None


class RegulatorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_voltage_v: float | None = None
    output_voltage_v: float | None = None
    output_current_a: float | None = None
    efficiency: float | None = None


class RailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voltage_v: float | None = None
    measured_current_a: float | None = None
    voltage_min_v: float | None = None
    voltage_max_v: float | None = None
    current_limit_a: float | None = None
    loads: list[RailLoadInput] = Field(default_factory=list)


class ElectricalAnalysisInput(BaseModel):
    """All numeric values are SI; null means unknown, not zero."""

    model_config = ConfigDict(extra="forbid")

    voltage_v: float | None = None
    current_a: float | None = None
    power_w: float | None = None
    resistance_ohm: float | None = None
    regulator: RegulatorInput = Field(default_factory=RegulatorInput)
    rail: RailInput = Field(default_factory=RailInput)


class ElectricalAnalysisResponse(BaseModel):
    power: CalcResult
    current: CalcResult
    voltage_drop: CalcResult
    regulator_output_power: CalcResult
    regulator_input_current: CalcResult
    regulator_power_loss: CalcResult
    rail_current: CalcResult
    anomalies: list[ElectricalAnomaly]


router = APIRouter(prefix="/api/electrical", tags=["electrical"])


@router.post("/analyze", response_model=ElectricalAnalysisResponse)
def analyze_electrical_design(payload: ElectricalAnalysisInput) -> ElectricalAnalysisResponse:
    """Return every requested calculation without filling missing values."""

    power = calculate_power(payload.voltage_v, payload.current_a)
    current = calculate_current(payload.power_w, payload.voltage_v)
    voltage_drop = calculate_voltage_drop(payload.current_a, payload.resistance_ohm)

    regulator_output_power = calculate_power(
        payload.regulator.output_voltage_v, payload.regulator.output_current_a
    )
    regulator_input_current = calculate_regulator_input_current(
        input_voltage_v=payload.regulator.input_voltage_v,
        output_voltage_v=payload.regulator.output_voltage_v,
        output_current_a=payload.regulator.output_current_a,
        efficiency=payload.regulator.efficiency,
    )
    regulator_power_loss = calculate_regulator_power_loss(
        regulator_output_power.value, payload.regulator.efficiency
    )

    if payload.rail.loads:
        rail_current = calculate_rail_current(
            payload.rail.voltage_v,
            [
                RailLoad(name=load.name, current_a=load.current_a, power_w=load.power_w)
                for load in payload.rail.loads
            ],
        )
    else:
        rail_current = CalcResult.not_evaluable(
            name="electrical.rail_current",
            unit="A",
            formula="Irail = Σ Iload",
            missing_inputs=["loads"],
        )

    anomalies = detect_rail_anomalies(
        voltage_v=payload.rail.voltage_v,
        current_a=payload.rail.measured_current_a,
        voltage_min_v=payload.rail.voltage_min_v,
        voltage_max_v=payload.rail.voltage_max_v,
        current_limit_a=payload.rail.current_limit_a,
    )
    return ElectricalAnalysisResponse(
        power=power,
        current=current,
        voltage_drop=voltage_drop,
        regulator_output_power=regulator_output_power,
        regulator_input_current=regulator_input_current,
        regulator_power_loss=regulator_power_loss,
        rail_current=rail_current,
        anomalies=anomalies,
    )
