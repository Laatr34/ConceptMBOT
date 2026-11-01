"""HTTP boundary for battery pack and autonomy calculations."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.domain.calc_result import CalcResult
from app.engines.battery import (
    calculate_pack_capacity,
    calculate_pack_energy,
    calculate_pack_voltage,
    calculate_theoretical_autonomy,
    calculate_usable_energy,
    estimate_autonomy,
    record_measured_autonomy,
)


class BatteryAnalysisInput(BaseModel):
    """Battery datasheet and load inputs; unknown values stay null."""

    model_config = ConfigDict(extra="forbid")

    cell_voltage_v: float | None = None
    series_count: int | None = None
    cell_capacity_ah: float | None = None
    parallel_count: int | None = None
    depth_of_discharge: float | None = None
    efficiency: float | None = None
    average_power_w: float | None = None
    estimated_average_power_w: float | None = None
    estimated_power_assumptions: list[str] = Field(default_factory=list)
    measured_duration_s: float | None = None


class BatteryAnalysisResponse(BaseModel):
    pack_voltage: CalcResult
    pack_capacity_c: CalcResult
    pack_capacity_ah: CalcResult
    nominal_energy_j: CalcResult
    nominal_energy_wh: CalcResult
    usable_energy_j: CalcResult
    usable_energy_wh: CalcResult
    theoretical_autonomy_s: CalcResult
    theoretical_autonomy_h: CalcResult
    estimated_autonomy_s: CalcResult
    estimated_autonomy_h: CalcResult
    measured_autonomy_s: CalcResult
    measured_autonomy_h: CalcResult


def _converted(result: CalcResult, divisor: float, unit: str, conversion: str) -> CalcResult:
    """Add a display-unit result without changing its status or calculation inputs."""

    return result.model_copy(
        update={
            "value": None if result.value is None else result.value / divisor,
            "unit": unit,
            "formula": f"{result.formula}; {conversion}",
        }
    )


router = APIRouter(prefix="/api/battery", tags=["battery"])


@router.post("/analyze", response_model=BatteryAnalysisResponse)
def analyze_battery(payload: BatteryAnalysisInput) -> BatteryAnalysisResponse:
    """Calculate pack sizing and theoretical, estimated and measured autonomy."""

    cell_capacity_c = (
        None if payload.cell_capacity_ah is None else payload.cell_capacity_ah * 3600.0
    )
    pack_voltage = calculate_pack_voltage(payload.cell_voltage_v, payload.series_count)
    pack_capacity_c = calculate_pack_capacity(cell_capacity_c, payload.parallel_count)
    nominal_energy_j = calculate_pack_energy(pack_voltage.value, pack_capacity_c.value)
    usable_energy_j = calculate_usable_energy(
        nominal_energy_j.value,
        payload.depth_of_discharge,
        payload.efficiency,
    )
    theoretical_autonomy_s = calculate_theoretical_autonomy(
        usable_energy_j.value, payload.average_power_w
    )

    assumptions = [item.strip() for item in payload.estimated_power_assumptions if item.strip()]
    if payload.estimated_average_power_w is not None and not assumptions:
        estimated_autonomy_s = CalcResult.not_evaluable(
            name="battery.autonomy_estimated",
            unit="s",
            formula="t ≈ Eusable / Paverage_estimated",
            inputs={
                "usable_energy_j": usable_energy_j.value,
                "estimated_average_power_w": payload.estimated_average_power_w,
            },
            missing_inputs=["estimated_power_assumptions"],
        )
    else:
        estimated_autonomy_s = estimate_autonomy(
            usable_energy_j.value,
            payload.estimated_average_power_w,
            assumptions=assumptions,
        )
    measured_autonomy_s = record_measured_autonomy(payload.measured_duration_s)

    return BatteryAnalysisResponse(
        pack_voltage=pack_voltage,
        pack_capacity_c=pack_capacity_c,
        pack_capacity_ah=_converted(pack_capacity_c, 3600.0, "Ah", "Qpack (Ah) = Qpack (C) / 3600"),
        nominal_energy_j=nominal_energy_j,
        nominal_energy_wh=_converted(nominal_energy_j, 3600.0, "Wh", "E (Wh) = E (J) / 3600"),
        usable_energy_j=usable_energy_j,
        usable_energy_wh=_converted(
            usable_energy_j, 3600.0, "Wh", "Eusable (Wh) = Eusable (J) / 3600"
        ),
        theoretical_autonomy_s=theoretical_autonomy_s,
        theoretical_autonomy_h=_converted(
            theoretical_autonomy_s, 3600.0, "h", "t (h) = t (s) / 3600"
        ),
        estimated_autonomy_s=estimated_autonomy_s,
        estimated_autonomy_h=_converted(estimated_autonomy_s, 3600.0, "h", "t (h) = t (s) / 3600"),
        measured_autonomy_s=measured_autonomy_s,
        measured_autonomy_h=_converted(measured_autonomy_s, 3600.0, "h", "t (h) = t (s) / 3600"),
    )
