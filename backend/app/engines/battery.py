"""Battery pack and autonomy engine (pure functions, SI + Wh/Ah at the boundary).

Formulas
--------
V_nom = Ns x V_cell,nom        V_max = Ns x V_cell,max        V_min = Ns x V_cell,min
C_pack = Np x C_cell (Ah)      E_nom = V_nom x C_pack (Wh)    E_usable = E_nom x DoD_usable
P_max = V_nom x I_max          (nominal-voltage approximation of the power available)
t_theoretical = E_nom / P_avg                      ideal bound: no depth-of-discharge limit, no losses
t_estimated   = E_nom x DoD x eta_discharge / P_avg  uses usable fraction and discharge efficiency
t_measured    = value entered by the user from a physical test (never computed)
margin        = (t_estimated - t_target) / t_target

Assumptions / limits
--------------------
P_avg is the average power drawn at the battery (converter losses are already in it).
Peukert effect, temperature, ageing and voltage sag under load are NOT modelled.
The three autonomies are distinct quantities and are never merged.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.domain.calc_result import CalcResult, Confidence, ResultStatus
from app.domain.finding import Finding, Severity, Text
from app.domain.project import BatteryConfig
from app.domain.units import InvalidInputError, require_positive


class PackResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    nominal_voltage: CalcResult
    max_voltage: CalcResult
    min_voltage: CalcResult
    capacity_ah: CalcResult
    energy_wh: CalcResult
    usable_energy_wh: CalcResult
    max_power: CalcResult


class AutonomyResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    average_power: CalcResult
    theoretical_h: CalcResult
    estimated_h: CalcResult
    measured_h: CalcResult
    energy_margin: CalcResult
    discharge_current_avg: CalcResult
    discharge_current_peak: CalcResult


class BatteryAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)
    pack: PackResult
    autonomy: AutonomyResult
    findings: list[Finding]


def _ne(name: str, unit: str, formula: str, missing: list[str]) -> CalcResult:
    return CalcResult.not_evaluable(name=name, unit=unit, formula=formula, missing_inputs=missing)


def _missing(**fields: object) -> list[str]:
    return [k for k, v in fields.items() if v is None]


def _ok(
    name: str,
    value: float,
    unit: str,
    formula: str,
    inputs: dict[str, float | None],
    *,
    status: ResultStatus = ResultStatus.THEORETICAL,
    conf: Confidence = Confidence.HIGH,
    assumptions: list[str] | None = None,
    limits: list[str] | None = None,
) -> CalcResult:
    return CalcResult(
        name=name,
        value=value,
        unit=unit,
        formula=formula,
        inputs=inputs,
        assumptions=assumptions or [],
        status=status,
        confidence=conf,
        limits=limits or [],
    )


def pack(cfg: BatteryConfig, max_discharge_current_a: float | None = None) -> PackResult:
    """Pack characteristics. ``max_discharge_current_a`` overrides/complements the config value."""
    if (
        cfg.cell_min_v is not None
        and cfg.cell_nominal_v is not None
        and cfg.cell_min_v > cfg.cell_nominal_v
    ):
        raise InvalidInputError("cell_min_v must be <= cell_nominal_v")
    if (
        cfg.cell_max_v is not None
        and cfg.cell_nominal_v is not None
        and cfg.cell_nominal_v > cfg.cell_max_v
    ):
        raise InvalidInputError("cell_nominal_v must be <= cell_max_v")
    ns, np_ = cfg.cells_series, cfg.strings_parallel
    imax = (
        cfg.max_discharge_current_a
        if cfg.max_discharge_current_a is not None
        else max_discharge_current_a
    )

    def series(name: str, cell_v: float | None, label: str) -> CalcResult:
        m = _missing(cells_series=ns, **{label: cell_v})
        if m:
            return _ne(f"battery.{name}", "V", f"Ns × {label}", m)
        assert ns is not None and cell_v is not None
        return _ok(
            f"battery.{name}",
            ns * cell_v,
            "V",
            f"Ns × {label}",
            {"cells_series": ns, label: cell_v},
        )

    vnom = series("nominal_voltage", cfg.cell_nominal_v, "cell_nominal_v")
    vmax = series("max_voltage", cfg.cell_max_v, "cell_max_v")
    vmin = series("min_voltage", cfg.cell_min_v, "cell_min_v")
    m = _missing(strings_parallel=np_, cell_capacity_ah=cfg.cell_capacity_ah)
    if m:
        cap = _ne("battery.capacity", "Ah", "Np × C_cell", m)
    else:
        assert np_ is not None and cfg.cell_capacity_ah is not None
        cap = _ok(
            "battery.capacity",
            np_ * cfg.cell_capacity_ah,
            "Ah",
            "Np × C_cell",
            {"strings_parallel": np_, "cell_capacity_ah": cfg.cell_capacity_ah},
            limits=["rated capacity; real capacity depends on discharge rate and temperature"],
        )
    if vnom.value is None or cap.value is None:
        energy = _ne(
            "battery.energy", "Wh", "E = V_nom × C", vnom.missing_inputs + cap.missing_inputs
        )
    else:
        energy = _ok(
            "battery.energy",
            vnom.value * cap.value,
            "Wh",
            "E = V_nom × C",
            {"v_nom": vnom.value, "capacity_ah": cap.value},
            status=ResultStatus.THEORETICAL,
        )
    if energy.value is None or cfg.usable_fraction is None:
        usable = _ne(
            "battery.usable_energy",
            "Wh",
            "E_usable = E × DoD",
            energy.missing_inputs + _missing(usable_fraction=cfg.usable_fraction),
        )
    else:
        usable = _ok(
            "battery.usable_energy",
            energy.value * cfg.usable_fraction,
            "Wh",
            "E_usable = E × DoD",
            {"energy_wh": energy.value, "usable_fraction": cfg.usable_fraction},
            status=ResultStatus.ESTIMATED,
            conf=Confidence.MEDIUM,
            assumptions=["usable fraction supplied by the user"],
        )
    if vnom.value is None or imax is None:
        pmax = _ne(
            "battery.max_power",
            "W",
            "P_max = V_nom × I_max",
            vnom.missing_inputs + _missing(max_discharge_current_a=imax),
        )
    else:
        pmax = _ok(
            "battery.max_power",
            vnom.value * imax,
            "W",
            "P_max = V_nom × I_max",
            {"v_nom": vnom.value, "i_max_a": imax},
            status=ResultStatus.ESTIMATED,
            conf=Confidence.MEDIUM,
            limits=["nominal-voltage approximation; ignores voltage sag"],
        )
    return PackResult(
        nominal_voltage=vnom,
        max_voltage=vmax,
        min_voltage=vmin,
        capacity_ah=cap,
        energy_wh=energy,
        usable_energy_wh=usable,
        max_power=pmax,
    )


def autonomy_hours(energy_wh: float, power_w: float) -> float:
    """t = E / P (hours). Rejects non-positive power (no division by zero)."""
    require_positive("power_w", power_w)
    return energy_wh / power_w


def autonomy(
    cfg: BatteryConfig,
    p: PackResult,
    *,
    avg_current_a: float | None,
    peak_current_a: float | None,
    avg_missing: list[str] | None = None,
    peak_missing: list[str] | None = None,
) -> AutonomyResult:
    avg_missing = avg_missing or ["battery rail average current"]
    peak_missing = peak_missing or ["battery rail peak current"]
    ia = (
        _ok(
            "battery.discharge_current_avg",
            avg_current_a,
            "A",
            "I = Σ rail currents",
            {"avg_current_a": avg_current_a},
            status=ResultStatus.ESTIMATED,
            conf=Confidence.MEDIUM,
        )
        if avg_current_a is not None
        else _ne("battery.discharge_current_avg", "A", "I = Σ rail currents", avg_missing)
    )
    ip = (
        _ok(
            "battery.discharge_current_peak",
            peak_current_a,
            "A",
            "I = Σ rail peak currents",
            {"peak_current_a": peak_current_a},
            status=ResultStatus.THEORETICAL,
            conf=Confidence.LOW,
            limits=["worst-case: all peaks simultaneous"],
        )
        if peak_current_a is not None
        else _ne("battery.discharge_current_peak", "A", "I = Σ rail peak currents", peak_missing)
    )
    vnom = p.nominal_voltage.value
    if avg_current_a is None or vnom is None:
        pw = _ne(
            "battery.average_power",
            "W",
            "P_avg = I_avg × V_nom",
            (avg_missing if avg_current_a is None else []) + p.nominal_voltage.missing_inputs,
        )
    else:
        pw = _ok(
            "battery.average_power",
            avg_current_a * vnom,
            "W",
            "P_avg = I_avg × V_nom",
            {"avg_current_a": avg_current_a, "v_nom": vnom},
            status=ResultStatus.ESTIMATED,
            conf=Confidence.MEDIUM,
            assumptions=["energy drawn at the pack nominal voltage"],
        )
    e = p.energy_wh.value
    power_issue = ["average power must be > 0"] if pw.value is not None and pw.value <= 0 else []
    if e is None or pw.value is None or pw.value <= 0:
        miss = p.energy_wh.missing_inputs + pw.missing_inputs + power_issue
        theo = _ne("battery.autonomy_theoretical", "h", "t = E_nom / P_avg", miss)
    else:
        theo = _ok(
            "battery.autonomy_theoretical",
            autonomy_hours(e, pw.value),
            "h",
            "t = E_nom / P_avg",
            {"energy_wh": e, "power_w": pw.value},
            status=ResultStatus.THEORETICAL,
            conf=Confidence.LOW,
            limits=["ideal upper bound: no depth-of-discharge limit, no losses"],
        )
    if (
        e is None
        or pw.value is None
        or pw.value <= 0
        or cfg.usable_fraction is None
        or cfg.discharge_efficiency is None
    ):
        miss = (
            p.energy_wh.missing_inputs
            + pw.missing_inputs
            + power_issue
            + _missing(
                usable_fraction=cfg.usable_fraction, discharge_efficiency=cfg.discharge_efficiency
            )
        )
        est = _ne("battery.autonomy_estimated", "h", "t = E_nom × DoD × η / P_avg", miss)
    else:
        est = _ok(
            "battery.autonomy_estimated",
            autonomy_hours(e * cfg.usable_fraction * cfg.discharge_efficiency, pw.value),
            "h",
            "t = E_nom × DoD × η / P_avg",
            {
                "energy_wh": e,
                "usable_fraction": cfg.usable_fraction,
                "discharge_efficiency": cfg.discharge_efficiency,
                "power_w": pw.value,
            },
            status=ResultStatus.ESTIMATED,
            conf=Confidence.MEDIUM,
            assumptions=[
                "constant average power",
                "usable fraction and efficiency supplied by the user",
            ],
            limits=["Peukert effect, temperature, ageing and voltage sag not modelled"],
        )
    if cfg.measured_runtime_h is None:
        meas = _ne(
            "battery.autonomy_measured", "h", "entered from a physical test", ["measured_runtime_h"]
        )
    else:
        meas = _ok(
            "battery.autonomy_measured",
            cfg.measured_runtime_h,
            "h",
            "entered from a physical test",
            {"measured_runtime_h": cfg.measured_runtime_h},
            status=ResultStatus.MEASURED,
            conf=Confidence.HIGH,
            limits=["valid only for the conditions of the test"],
        )
    if est.value is None or cfg.target_runtime_h is None:
        marg = _ne(
            "battery.energy_margin",
            "1",
            "(t_est − t_target) / t_target",
            est.missing_inputs + _missing(target_runtime_h=cfg.target_runtime_h),
        )
    else:
        marg = _ok(
            "battery.energy_margin",
            (est.value - cfg.target_runtime_h) / cfg.target_runtime_h,
            "1",
            "(t_est − t_target) / t_target",
            {"t_est_h": est.value, "t_target_h": cfg.target_runtime_h},
            status=ResultStatus.ESTIMATED,
            conf=Confidence.MEDIUM,
        )
    return AutonomyResult(
        average_power=pw,
        theoretical_h=theo,
        estimated_h=est,
        measured_h=meas,
        energy_margin=marg,
        discharge_current_avg=ia,
        discharge_current_peak=ip,
    )


def _f(
    code: str,
    sev: Severity,
    problem: Text,
    expl: Text,
    sugg: Text,
    label: str | None,
    cid: str | None,
    *,
    value: float | None = None,
    unit: str | None = None,
    limit: float | None = None,
    source: str | None = None,
) -> Finding:
    return Finding(
        code=code,
        severity=sev,
        category="battery",
        component_id=cid,
        component_label=label,
        problem=problem,
        value=value,
        unit=unit,
        limit=limit,
        limit_source=source,
        explanation=expl,
        suggestion=sugg,
    )


def analyze(
    cfg: BatteryConfig,
    *,
    avg_current_a: float | None,
    peak_current_a: float | None,
    avg_missing: list[str] | None = None,
    peak_missing: list[str] | None = None,
    max_discharge_current_a: float | None = None,
    max_discharge_source: str | None = None,
    rail_voltage_v: float | None = None,
    label: str | None = None,
) -> BatteryAnalysis:
    p = pack(cfg, max_discharge_current_a)
    a = autonomy(
        cfg,
        p,
        avg_current_a=avg_current_a,
        peak_current_a=peak_current_a,
        avg_missing=avg_missing,
        peak_missing=peak_missing,
    )
    cid = cfg.instance_id
    findings: list[Finding] = []
    imax = (
        cfg.max_discharge_current_a
        if cfg.max_discharge_current_a is not None
        else max_discharge_current_a
    )
    if p.nominal_voltage.value is None or p.capacity_ah.value is None:
        miss = "; ".join(p.nominal_voltage.missing_inputs + p.capacity_ah.missing_inputs)
        findings.append(
            _f(
                "BATT_CONFIG_INCOMPLETE",
                Severity.INFO,
                Text(en="Battery pack not fully defined", fr="Pack batterie incomplet"),
                Text(en=f"Missing: {miss}", fr=f"Manquant : {miss}"),
                Text(
                    en="Define cells in series/parallel and cell data.",
                    fr="Définir les cellules série/parallèle et leurs caractéristiques.",
                ),
                label,
                cid,
            )
        )
    if imax is None:
        findings.append(
            _f(
                "BATT_DISCHARGE_LIMIT_UNKNOWN",
                Severity.INFO,
                Text(
                    en="Maximum discharge current unknown", fr="Courant de décharge maximal inconnu"
                ),
                Text(
                    en="Cannot check the battery current limit.",
                    fr="Impossible de vérifier la limite de courant de la batterie.",
                ),
                Text(
                    en="Enter the datasheet maximum discharge current.",
                    fr="Saisir le courant de décharge maximal de la fiche technique.",
                ),
                label,
                cid,
            )
        )
    else:
        if a.discharge_current_avg.value is not None and a.discharge_current_avg.value > imax:
            findings.append(
                _f(
                    "BATT_AVG_OVER_LIMIT",
                    Severity.CRITICAL,
                    Text(
                        en="Average discharge current exceeds battery limit",
                        fr="Le courant moyen de décharge dépasse la limite de la batterie",
                    ),
                    Text(
                        en="Continuous load above the maximum discharge rating.",
                        fr="Charge continue supérieure au courant de décharge maximal.",
                    ),
                    Text(
                        en="Use a higher-rated pack or reduce the load.",
                        fr="Utiliser un pack de calibre supérieur ou réduire la charge.",
                    ),
                    label,
                    cid,
                    value=a.discharge_current_avg.value,
                    unit="A",
                    limit=imax,
                    source=max_discharge_source,
                )
            )
        if a.discharge_current_peak.value is not None and a.discharge_current_peak.value > imax:
            findings.append(
                _f(
                    "BATT_PEAK_OVER_LIMIT",
                    Severity.HIGH,
                    Text(
                        en="Worst-case peak current exceeds battery limit",
                        fr="Le pic de courant pire cas dépasse la limite de la batterie",
                    ),
                    Text(
                        en="Sum of simultaneous peaks above the rating (may be transient).",
                        fr="Somme des pics simultanés supérieure au calibre (peut être transitoire).",
                    ),
                    Text(
                        en="Check startup sequencing, or use a higher-rated pack.",
                        fr="Vérifier la séquence de démarrage ou utiliser un pack de calibre supérieur.",
                    ),
                    label,
                    cid,
                    value=a.discharge_current_peak.value,
                    unit="A",
                    limit=imax,
                    source=max_discharge_source,
                )
            )
    vlo, vhi = p.min_voltage.value, p.max_voltage.value
    if (
        rail_voltage_v is not None
        and vlo is not None
        and vhi is not None
        and not (vlo <= rail_voltage_v <= vhi)
    ):
        findings.append(
            _f(
                "BATT_RAIL_VOLTAGE_OUT_OF_RANGE",
                Severity.HIGH,
                Text(
                    en="Battery rail voltage outside the pack voltage window",
                    fr="Tension du rail batterie hors de la plage du pack",
                ),
                Text(
                    en="The declared rail voltage is not reachable by the pack.",
                    fr="La tension déclarée du rail n'est pas atteignable par le pack.",
                ),
                Text(
                    en="Correct the rail voltage or the number of series cells.",
                    fr="Corriger la tension du rail ou le nombre de cellules en série.",
                ),
                label,
                cid,
                value=rail_voltage_v,
                unit="V",
                limit=p.min_voltage.value,
            )
        )
    t_est, t_target = a.estimated_h.value, cfg.target_runtime_h
    if t_est is not None and t_target is not None and t_est < t_target:
        findings.append(
            _f(
                "BATT_AUTONOMY_SHORT",
                Severity.HIGH,
                Text(
                    en="Estimated autonomy below the target",
                    fr="Autonomie estimée inférieure à l'objectif",
                ),
                Text(
                    en="Estimated runtime does not reach the required runtime.",
                    fr="L'autonomie estimée n'atteint pas l'autonomie requise.",
                ),
                Text(
                    en="Increase capacity (parallel strings) or reduce consumption.",
                    fr="Augmenter la capacité (branches en parallèle) ou réduire la consommation.",
                ),
                label,
                cid,
                value=t_est,
                unit="h",
                limit=t_target,
            )
        )
    if (
        a.estimated_h.value is None
        and a.theoretical_h.value is None
        and p.nominal_voltage.value is not None
    ):
        miss = "; ".join((a.estimated_h.missing_inputs or a.average_power.missing_inputs)[:6])
        findings.append(
            _f(
                "BATT_AUTONOMY_NOT_EVALUABLE",
                Severity.INFO,
                Text(en="Autonomy cannot be evaluated", fr="Autonomie non évaluable"),
                Text(en=f"Missing data: {miss}", fr=f"Données manquantes : {miss}"),
                Text(
                    en="Complete load and battery data.",
                    fr="Compléter les données de charges et de batterie.",
                ),
                label,
                cid,
            )
        )
    return BatteryAnalysis(pack=p, autonomy=a, findings=findings)
