"""Pure battery pack and autonomy calculations.

Internal charge is coulombs (C), energy is joules (J), and time is seconds (s).
Ah and Wh conversions belong at the API/UI boundary. No discharge, temperature,
aging, or Peukert parameters are guessed when battery-specific data is absent.
"""

from __future__ import annotations

from app.domain.calc_result import CalcResult, Confidence, ResultStatus
from app.domain.units import InvalidInputError, require_non_negative, require_positive

AUTONOMY_LIMITS = [
    "Peukert effect is not modeled without a battery-specific exponent and test conditions.",
    "Temperature and battery aging are not modeled without measured battery-specific data.",
    "The result assumes a constant average load; real load profiles vary over time.",
]


def _not_evaluable(
    *,
    name: str,
    unit: str,
    formula: str,
    inputs: dict[str, float | None],
    missing: list[str],
) -> CalcResult:
    return CalcResult.not_evaluable(
        name=name,
        unit=unit,
        formula=formula,
        inputs=inputs,
        missing_inputs=missing,
    )


def _result(
    *,
    name: str,
    value: float,
    unit: str,
    formula: str,
    inputs: dict[str, float | None],
    status: ResultStatus = ResultStatus.THEORETICAL,
    confidence: Confidence = Confidence.HIGH,
    assumptions: list[str] | None = None,
    limits: list[str] | None = None,
) -> CalcResult:
    return CalcResult(
        name=name,
        value=value,
        unit=unit,
        formula=formula,
        inputs=inputs,
        status=status,
        confidence=confidence,
        assumptions=assumptions or [],
        limits=limits or [],
    )


def calculate_pack_voltage(
    cell_voltage_v: float | None, series_count: int | None
) -> CalcResult:
    """Calculate nominal pack voltage: Upack = Ucell × Ns (V)."""

    inputs = {
        "cell_voltage_v": cell_voltage_v,
        "series_count": float(series_count) if series_count is not None else None,
    }
    missing = [
        field
        for field, value in (("cell_voltage_v", cell_voltage_v), ("series_count", series_count))
        if value is None
    ]
    if missing:
        return _not_evaluable(
            name="battery.pack_voltage",
            unit="V",
            formula="Upack = Ucell × Ns",
            inputs=inputs,
            missing=missing,
        )
    assert cell_voltage_v is not None and series_count is not None
    require_positive("cell_voltage_v", cell_voltage_v)
    if not isinstance(series_count, int) or isinstance(series_count, bool) or series_count <= 0:
        raise InvalidInputError("series_count must be an integer > 0")
    return _result(
        name="battery.pack_voltage",
        value=cell_voltage_v * series_count,
        unit="V",
        formula="Upack = Ucell × Ns",
        inputs=inputs,
    )


def calculate_pack_capacity(
    cell_capacity_c: float | None, parallel_count: int | None
) -> CalcResult:
    """Calculate pack charge capacity: Qpack = Qcell × Np (C)."""

    inputs = {
        "cell_capacity_c": cell_capacity_c,
        "parallel_count": float(parallel_count) if parallel_count is not None else None,
    }
    missing = [
        field
        for field, value in (("cell_capacity_c", cell_capacity_c), ("parallel_count", parallel_count))
        if value is None
    ]
    if missing:
        return _not_evaluable(
            name="battery.pack_capacity",
            unit="C",
            formula="Qpack = Qcell × Np",
            inputs=inputs,
            missing=missing,
        )
    assert cell_capacity_c is not None and parallel_count is not None
    require_positive("cell_capacity_c", cell_capacity_c)
    if not isinstance(parallel_count, int) or isinstance(parallel_count, bool) or parallel_count <= 0:
        raise InvalidInputError("parallel_count must be an integer > 0")
    return _result(
        name="battery.pack_capacity",
        value=cell_capacity_c * parallel_count,
        unit="C",
        formula="Qpack = Qcell × Np",
        inputs=inputs,
    )


def calculate_pack_energy(
    nominal_voltage_v: float | None, capacity_c: float | None
) -> CalcResult:
    """Calculate nominal pack energy: E = U × Q (J)."""

    inputs = {"nominal_voltage_v": nominal_voltage_v, "capacity_c": capacity_c}
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="battery.pack_energy",
            unit="J",
            formula="E = U × Q",
            inputs=inputs,
            missing=missing,
        )
    assert nominal_voltage_v is not None and capacity_c is not None
    require_positive("nominal_voltage_v", nominal_voltage_v)
    require_positive("capacity_c", capacity_c)
    return _result(
        name="battery.pack_energy",
        value=nominal_voltage_v * capacity_c,
        unit="J",
        formula="E = U × Q",
        inputs=inputs,
        assumptions=["Nominal voltage and rated charge capacity are used."],
    )


def calculate_usable_energy(
    nominal_energy_j: float | None,
    depth_of_discharge: float | None,
    efficiency: float | None,
) -> CalcResult:
    """Calculate usable energy: Eusable = Enominal × DoD × η (J)."""

    inputs = {
        "nominal_energy_j": nominal_energy_j,
        "depth_of_discharge": depth_of_discharge,
        "efficiency": efficiency,
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="battery.usable_energy",
            unit="J",
            formula="Eusable = Enominal × DoD × η",
            inputs=inputs,
            missing=missing,
        )
    assert nominal_energy_j is not None
    assert depth_of_discharge is not None
    assert efficiency is not None
    require_non_negative("nominal_energy_j", nominal_energy_j)
    require_non_negative("depth_of_discharge", depth_of_discharge)
    require_positive("efficiency", efficiency)
    if depth_of_discharge > 1.0:
        raise InvalidInputError("depth_of_discharge must be <= 1.0")
    if efficiency > 1.0:
        raise InvalidInputError("efficiency must be <= 1.0")
    return _result(
        name="battery.usable_energy",
        value=nominal_energy_j * depth_of_discharge * efficiency,
        unit="J",
        formula="Eusable = Enominal × DoD × η",
        inputs=inputs,
        assumptions=["Depth of discharge and conversion efficiency are supplied values."],
    )


def calculate_theoretical_autonomy(
    usable_energy_j: float | None, average_power_w: float | None
) -> CalcResult:
    """Calculate ideal constant-load autonomy: t = Eusable / Paverage (s)."""

    inputs = {"usable_energy_j": usable_energy_j, "average_power_w": average_power_w}
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="battery.autonomy_theoretical",
            unit="s",
            formula="t = Eusable / Paverage",
            inputs=inputs,
            missing=missing,
        )
    assert usable_energy_j is not None and average_power_w is not None
    require_non_negative("usable_energy_j", usable_energy_j)
    require_positive("average_power_w", average_power_w)
    return _result(
        name="battery.autonomy_theoretical",
        value=usable_energy_j / average_power_w,
        unit="s",
        formula="t = Eusable / Paverage",
        inputs=inputs,
        assumptions=["Average power remains constant for the full discharge."],
        limits=AUTONOMY_LIMITS,
    )


def estimate_autonomy(
    usable_energy_j: float | None,
    estimated_average_power_w: float | None,
    *,
    assumptions: list[str],
) -> CalcResult:
    """Estimate autonomy from estimated average power; assumptions stay visible."""

    inputs = {
        "usable_energy_j": usable_energy_j,
        "estimated_average_power_w": estimated_average_power_w,
    }
    missing = [field for field, value in inputs.items() if value is None]
    if missing:
        return _not_evaluable(
            name="battery.autonomy_estimated",
            unit="s",
            formula="t ≈ Eusable / Paverage_estimated",
            inputs=inputs,
            missing=missing,
        )
    assert usable_energy_j is not None and estimated_average_power_w is not None
    require_non_negative("usable_energy_j", usable_energy_j)
    require_positive("estimated_average_power_w", estimated_average_power_w)
    return _result(
        name="battery.autonomy_estimated",
        value=usable_energy_j / estimated_average_power_w,
        unit="s",
        formula="t ≈ Eusable / Paverage_estimated",
        inputs=inputs,
        status=ResultStatus.ESTIMATED,
        confidence=Confidence.MEDIUM,
        assumptions=assumptions + ["Average power is an estimate, not a measured load profile."],
        limits=AUTONOMY_LIMITS,
    )


def record_measured_autonomy(duration_s: float | None) -> CalcResult:
    """Represent an observed runtime without reclassifying it as a prediction."""

    inputs = {"measured_duration_s": duration_s}
    if duration_s is None:
        return _not_evaluable(
            name="battery.autonomy_measured",
            unit="s",
            formula="t = measured runtime",
            inputs=inputs,
            missing=["measured_duration_s"],
        )
    require_non_negative("measured_duration_s", duration_s)
    return _result(
        name="battery.autonomy_measured",
        value=duration_s,
        unit="s",
        formula="t = measured runtime",
        inputs=inputs,
        status=ResultStatus.MEASURED,
        confidence=Confidence.HIGH,
        assumptions=["Duration is recorded from a physical discharge test."],
        limits=["The measurement applies only to the recorded test conditions."],
    )
