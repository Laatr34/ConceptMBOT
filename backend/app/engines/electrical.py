"""Electrical engine (pure functions, SI units).

Formulas
--------
P = U x I ; I = P / U                                    (power law)
I_in(converter) = sum(I_out_k x U_out_k) / (U_in x eta)   (energy balance, eta from datasheet)
R_cable = rho x 2 L / A ; dV = I x R_cable                (round-trip copper conductor)
A_min = rho x 2 L x I / (f x U)                           (section for a voltage-drop fraction f)

Assumptions (also returned in results)
--------------------------------------
* Average current = datasheet nominal current x quantity x duty cycle. If only power is known,
  I = P / U_rail (constant-power load model).
* Peak current = sum of all datasheet peaks occurring simultaneously (conservative).
* Copper resistivity 1.68e-8 ohm.m at 20 degC; temperature rise of conductors is ignored.
* Cable ampacity / heating is NOT evaluated (needs insulation, bundling, ambient data).
* Unknown data is never replaced by a default: affected results are ``not_evaluable``.
"""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from app.domain.calc_result import CalcResult, Confidence, ResultStatus
from app.domain.component import Category, ComponentSpec, ElectricalRole
from app.domain.finding import Finding, Severity, Text
from app.domain.project import ComponentInstance, ProjectData, Rail
from app.domain.units import InvalidInputError, require_non_negative, require_positive

COPPER_RESISTIVITY_OHM_M = 1.68e-8


def power_w(u_v: float, i_a: float) -> CalcResult:
    """P = U x I."""
    require_non_negative("u_v", u_v)
    require_non_negative("i_a", i_a)
    return CalcResult(
        name="electrical.power",
        value=u_v * i_a,
        unit="W",
        formula="P = U × I",
        inputs={"u_v": u_v, "i_a": i_a},
        status=ResultStatus.THEORETICAL,
        confidence=Confidence.HIGH,
    )


def current_a(p_w: float, u_v: float) -> CalcResult:
    """I = P / U."""
    require_non_negative("p_w", p_w)
    require_positive("u_v", u_v)
    return CalcResult(
        name="electrical.current",
        value=p_w / u_v,
        unit="A",
        formula="I = P / U",
        inputs={"p_w": p_w, "u_v": u_v},
        status=ResultStatus.THEORETICAL,
        confidence=Confidence.HIGH,
    )


def cable_voltage_drop_v(current_a_: float, length_m: float, section_mm2: float) -> float:
    """dV = I x rho x 2L / A (A converted from mm^2 to m^2)."""
    require_non_negative("current_a", current_a_)
    require_positive("length_m", length_m)
    require_positive("section_mm2", section_mm2)
    resistance = COPPER_RESISTIVITY_OHM_M * 2.0 * length_m / (section_mm2 * 1e-6)
    return current_a_ * resistance


def cable_min_section_mm2(
    current_a_: float, length_m: float, rail_voltage_v: float, max_drop_fraction: float
) -> float:
    """Smallest section (mm^2) keeping the drop below ``max_drop_fraction`` of the rail voltage."""
    require_non_negative("current_a", current_a_)
    require_positive("length_m", length_m)
    require_positive("rail_voltage_v", rail_voltage_v)
    require_positive("max_drop_fraction", max_drop_fraction)
    area_m2 = (
        COPPER_RESISTIVITY_OHM_M
        * 2.0
        * length_m
        * current_a_
        / (max_drop_fraction * rail_voltage_v)
    )
    return area_m2 * 1e6


# --------------------------------------------------------------------------- result models
class RailResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    rail_id: str
    name: str
    voltage_v: float | None
    source_instance_id: str | None
    avg_current: CalcResult
    peak_current: CalcResult
    avg_power: CalcResult
    partial_avg_current_a: float  # sum of the loads whose data is known (lower bound)
    unknown_loads: list[str]  # labels of loads with missing data
    source_limit_a: float | None


class CableResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    cable_id: str
    rail_id: str
    current: CalcResult
    voltage_drop: CalcResult
    drop_fraction: CalcResult
    min_section_mm2: CalcResult


class ElectricalAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)
    rails: list[RailResult]
    cables: list[CableResult]
    findings: list[Finding]


# --------------------------------------------------------------------------- helpers
def _ne(name: str, unit: str, formula: str, missing: list[str]) -> CalcResult:
    return CalcResult.not_evaluable(name=name, unit=unit, formula=formula, missing_inputs=missing)


def _fnd(
    code: str,
    sev: Severity,
    inst: ComponentInstance | None,
    problem: Text,
    explanation: Text,
    suggestion: Text,
    *,
    value: float | None = None,
    unit: str | None = None,
    limit: float | None = None,
    limit_source: str | None = None,
    category: str = "electrical",
) -> Finding:
    return Finding(
        code=code,
        severity=sev,
        category=category,
        component_id=inst.id if inst else None,
        component_label=inst.label if inst else None,
        problem=problem,
        value=value,
        unit=unit,
        limit=limit,
        limit_source=limit_source,
        explanation=explanation,
        suggestion=suggestion,
    )


def _source_ref(spec: ComponentSpec) -> str | None:
    return "; ".join(spec.sources) if spec.sources else None


def _avg_current_one(
    spec: ComponentSpec, rail_v: float | None, override: float | None
) -> tuple[float | None, list[str]]:
    if override is not None:
        return override, []
    if spec.nominal_current_a is not None:
        return spec.nominal_current_a, []
    if spec.power_w is not None and rail_v:
        return spec.power_w / rail_v, []
    if spec.category is Category.DC_MOTOR:
        return None, ["motor running current (motorization model) or nominal_current_a"]
    return None, ["nominal_current_a|power_w"]


def _peak_current_one(spec: ComponentSpec) -> tuple[float | None, list[str]]:
    if spec.category in (Category.DC_MOTOR, Category.SERVO) and spec.stall_current_a is not None:
        return spec.stall_current_a, []
    if spec.peak_current_a is not None:
        return spec.peak_current_a, []
    if spec.max_current_a is not None:
        return spec.max_current_a, []
    if spec.category in (Category.DC_MOTOR, Category.SERVO):
        return None, ["stall_current_a"]
    return None, ["peak_current_a|max_current_a"]


class _Ctx:
    def __init__(
        self,
        project: ProjectData,
        library: Mapping[str, ComponentSpec],
        motor_running_current_a: Mapping[str, float],
    ) -> None:
        self.p = project
        self.lib = library
        self.override = motor_running_current_a
        self.inst = {c.id: c for c in project.components}
        self.rails = {r.id: r for r in project.electrical.rails}
        self.links_by_rail: dict[str, list[str]] = {}
        for pl in project.electrical.power_links:
            self.links_by_rail.setdefault(pl.rail_id, []).append(pl.load_instance_id)
        self.rails_by_source: dict[str, list[Rail]] = {}
        for r in project.electrical.rails:
            if r.source_instance_id:
                self.rails_by_source.setdefault(r.source_instance_id, []).append(r)
        self.memo: dict[str, RailResult] = {}
        self.stack: list[str] = []
        self.findings: list[Finding] = []

    def spec(self, inst: ComponentInstance) -> ComponentSpec | None:
        return self.lib.get(inst.component_id)


def _compute_rail(ctx: _Ctx, rail: Rail) -> RailResult:
    if rail.id in ctx.memo:
        return ctx.memo[rail.id]
    if rail.id in ctx.stack:
        ctx.findings.append(
            _fnd(
                "ELEC_RAIL_CYCLE",
                Severity.CRITICAL,
                None,
                Text(
                    en=f"Power rail loop involving rail {rail.name}",
                    fr=f"Boucle d'alimentation impliquant le rail {rail.name}",
                ),
                Text(
                    en="A converter is (indirectly) supplying its own input.",
                    fr="Un convertisseur alimente (indirectement) sa propre entrée.",
                ),
                Text(
                    en="Remove the circular power link.",
                    fr="Supprimer la liaison d'alimentation circulaire.",
                ),
            )
        )
        raise RecursionError(rail.id)
    ctx.stack.append(rail.id)
    try:
        avg_sum = 0.0
        peak_sum = 0.0
        avg_missing: list[str] = []
        peak_missing: list[str] = []
        unknown: list[str] = []
        for load_id in ctx.links_by_rail.get(rail.id, []):
            inst = ctx.inst[load_id]
            spec = ctx.spec(inst)
            if spec is None:
                avg_missing.append(f"{inst.label}: component not in library")
                peak_missing.append(f"{inst.label}: component not in library")
                unknown.append(inst.label)
                continue
            role = spec.role
            if role is ElectricalRole.SOURCE:
                # converter fed by this rail: input current from its downstream rails
                a, ap = _converter_input(ctx, inst, spec, rail)
                if a is None:
                    avg_missing += [f"{inst.label}: {m}" for m in ap]
                    unknown.append(inst.label)
                else:
                    avg_sum += a
                pk, pm = _converter_input_peak(ctx, inst, spec, rail)
                if pk is None:
                    peak_missing += [f"{inst.label}: {m}" for m in pm]
                else:
                    peak_sum += pk
                continue
            if (
                role is ElectricalRole.PASSIVE
                and spec.nominal_current_a is None
                and spec.power_w is None
            ):
                continue  # passive part without a load model contributes nothing
            override = ctx.override.get(inst.id)
            i1, m1 = _avg_current_one(spec, rail.voltage_v, override)
            if i1 is None:
                avg_missing += [f"{inst.label}: {m}" for m in m1]
                unknown.append(inst.label)
            else:
                avg_sum += i1 * inst.quantity * inst.duty_cycle
            pk1, pm1 = _peak_current_one(spec)
            if pk1 is None:
                peak_missing += [f"{inst.label}: {m}" for m in pm1]
            else:
                peak_sum += pk1 * inst.quantity

        rail_inputs: dict[str, float | None] = {"rail_voltage_v": rail.voltage_v}
        avg_assump = [
            "average current = nominal current × quantity × duty cycle",
            "power-only datasheets: I = P / U_rail (constant-power load)",
            "converter input current from energy balance with datasheet efficiency",
        ]
        if avg_missing:
            avg = CalcResult(
                name=f"electrical.rail_avg_current.{rail.id}",
                value=None,
                unit="A",
                formula="I_rail = Σ I_load,avg",
                inputs=rail_inputs,
                status=ResultStatus.NOT_EVALUABLE,
                missing_inputs=avg_missing,
                limits=[f"known part of the sum (lower bound): {avg_sum:.6g} A"],
            )
        else:
            avg = CalcResult(
                name=f"electrical.rail_avg_current.{rail.id}",
                value=avg_sum,
                unit="A",
                formula="I_rail = Σ I_load,avg",
                inputs=rail_inputs,
                assumptions=avg_assump,
                status=ResultStatus.ESTIMATED,
                confidence=Confidence.MEDIUM,
                limits=["no inrush/transient model; copper temperature effects ignored"],
            )
        if peak_missing:
            peak = CalcResult(
                name=f"electrical.rail_peak_current.{rail.id}",
                value=None,
                unit="A",
                formula="I_rail,peak = Σ I_load,peak",
                inputs=rail_inputs,
                status=ResultStatus.NOT_EVALUABLE,
                missing_inputs=peak_missing,
                limits=[f"known part of the sum (lower bound): {peak_sum:.6g} A"],
            )
        else:
            peak = CalcResult(
                name=f"electrical.rail_peak_current.{rail.id}",
                value=peak_sum,
                unit="A",
                formula="I_rail,peak = Σ I_load,peak",
                inputs=rail_inputs,
                assumptions=["all peaks (stall/peak/max currents) occur simultaneously"],
                status=ResultStatus.THEORETICAL,
                confidence=Confidence.LOW,
                limits=["worst-case upper bound, not a measured transient"],
            )
        if avg.value is not None and rail.voltage_v:
            pw = CalcResult(
                name=f"electrical.rail_avg_power.{rail.id}",
                value=avg.value * rail.voltage_v,
                unit="W",
                formula="P = U × I",
                inputs={"u_v": rail.voltage_v, "i_a": avg.value},
                status=ResultStatus.ESTIMATED,
                confidence=Confidence.MEDIUM,
            )
        else:
            miss = ["rail voltage_v"] if not rail.voltage_v else []
            pw = _ne(
                f"electrical.rail_avg_power.{rail.id}",
                "W",
                "P = U × I",
                miss + ["rail average current"],
            )
        limit = None
        if rail.source_instance_id:
            src = ctx.inst.get(rail.source_instance_id)
            sspec = ctx.spec(src) if src else None
            if sspec is not None and sspec.category is not Category.BATTERY:
                limit = sspec.output_max_current_a
        res = RailResult(
            rail_id=rail.id,
            name=rail.name,
            voltage_v=rail.voltage_v,
            source_instance_id=rail.source_instance_id,
            avg_current=avg,
            peak_current=peak,
            avg_power=pw,
            partial_avg_current_a=avg_sum,
            unknown_loads=unknown,
            source_limit_a=limit,
        )
        ctx.memo[rail.id] = res
        return res
    finally:
        ctx.stack.pop()


def _downstream(ctx: _Ctx, inst: ComponentInstance) -> list[RailResult]:
    out = []
    for r in ctx.rails_by_source.get(inst.id, []):
        out.append(_compute_rail(ctx, r))
    return out


def _converter_input(
    ctx: _Ctx, inst: ComponentInstance, spec: ComponentSpec, in_rail: Rail
) -> tuple[float | None, list[str]]:
    if spec.category is Category.BATTERY:
        return 0.0, []
    missing: list[str] = []
    if in_rail.voltage_v is None:
        missing.append("input rail voltage_v")
    if spec.efficiency is None:
        missing.append("efficiency")
    p_out = 0.0
    for d in _downstream(ctx, inst):
        if d.avg_current.value is None or d.voltage_v is None:
            missing.append(f"downstream rail {d.name} current/voltage")
        else:
            p_out += d.avg_current.value * d.voltage_v
    if missing:
        return None, missing
    assert spec.efficiency is not None and in_rail.voltage_v is not None
    i_in = p_out / (in_rail.voltage_v * spec.efficiency)
    if spec.idle_current_a is not None:
        i_in += spec.idle_current_a
    return i_in * inst.quantity, []


def _converter_input_peak(
    ctx: _Ctx, inst: ComponentInstance, spec: ComponentSpec, in_rail: Rail
) -> tuple[float | None, list[str]]:
    missing: list[str] = []
    if in_rail.voltage_v is None:
        missing.append("input rail voltage_v")
    if spec.efficiency is None:
        missing.append("efficiency")
    p_out = 0.0
    for d in _downstream(ctx, inst):
        if d.peak_current.value is None or d.voltage_v is None:
            missing.append(f"downstream rail {d.name} peak current/voltage")
        else:
            p_out += d.peak_current.value * d.voltage_v
    if missing:
        return None, missing
    assert spec.efficiency is not None and in_rail.voltage_v is not None
    return p_out / (in_rail.voltage_v * spec.efficiency) * inst.quantity, []


# --------------------------------------------------------------------------- analysis
def analyze(
    project: ProjectData,
    library: Mapping[str, ComponentSpec],
    *,
    motor_running_current_a: Mapping[str, float] | None = None,
) -> ElectricalAnalysis:
    """Full electrical analysis: per-rail currents, cable drops and findings."""
    ctx = _Ctx(project, library, motor_running_current_a or {})
    e = project.electrical
    results: list[RailResult] = []
    for rail in e.rails:
        try:
            results.append(_compute_rail(ctx, rail))
        except RecursionError:
            continue
    findings = ctx.findings
    findings += _check_data_and_wiring(ctx)
    findings += _check_voltages(ctx)
    findings += _check_capacity(ctx, results)
    findings += _check_grounds(ctx)
    findings += _check_protection(ctx)
    findings += _check_temperature(ctx)
    cables, cfind = _check_cables(ctx, results)
    findings += cfind
    return ElectricalAnalysis(rails=results, cables=cables, findings=findings)


def _check_data_and_wiring(ctx: _Ctx) -> list[Finding]:
    out: list[Finding] = []
    linked = {pl.load_instance_id for pl in ctx.p.electrical.power_links}
    for inst in ctx.p.components:
        spec = ctx.spec(inst)
        if spec is None:
            out.append(
                _fnd(
                    "DATA_COMPONENT_MISSING",
                    Severity.HIGH,
                    inst,
                    Text(
                        en="Component not found in the library",
                        fr="Composant introuvable dans la bibliothèque",
                    ),
                    Text(
                        en=f"Library id {inst.component_id} does not exist.",
                        fr=f"L'identifiant {inst.component_id} n'existe pas.",
                    ),
                    Text(
                        en="Re-link the instance to an existing library component.",
                        fr="Relier l'instance à un composant existant.",
                    ),
                    category="data",
                )
            )
            continue
        if spec.role is ElectricalRole.LOAD and inst.id not in linked:
            out.append(
                _fnd(
                    "ELEC_UNPOWERED",
                    Severity.HIGH,
                    inst,
                    Text(
                        en="No power connection (incomplete electrical connection)",
                        fr="Aucune alimentation connectée (connexion électrique incomplète)",
                    ),
                    Text(
                        en="This electrical load is not connected to any power rail.",
                        fr="Cette charge électrique n'est reliée à aucun rail d'alimentation.",
                    ),
                    Text(
                        en="Connect it to a rail in the electrical editor.",
                        fr="La relier à un rail dans l'éditeur électrique.",
                    ),
                )
            )
        if spec.role is ElectricalRole.SOURCE and spec.category is not Category.BATTERY:
            if inst.id not in linked:
                out.append(
                    _fnd(
                        "ELEC_SOURCE_NO_INPUT",
                        Severity.HIGH,
                        inst,
                        Text(
                            en="Converter has no input supply",
                            fr="Le convertisseur n'a pas d'alimentation d'entrée",
                        ),
                        Text(
                            en="No power link feeds this converter's input.",
                            fr="Aucune liaison n'alimente l'entrée de ce convertisseur.",
                        ),
                        Text(en="Link it to its input rail.", fr="Le relier à son rail d'entrée."),
                    )
                )
            if inst.id not in ctx.rails_by_source:
                out.append(
                    _fnd(
                        "ELEC_SOURCE_NO_OUTPUT",
                        Severity.MEDIUM,
                        inst,
                        Text(
                            en="Source defines no output rail",
                            fr="La source ne définit aucun rail de sortie",
                        ),
                        Text(
                            en="No rail uses this component as its source.",
                            fr="Aucun rail n'utilise ce composant comme source.",
                        ),
                        Text(
                            en="Create an output rail with this source.",
                            fr="Créer un rail de sortie avec cette source.",
                        ),
                    )
                )
    for rail in ctx.p.electrical.rails:
        if rail.source_instance_id is None:
            out.append(
                _fnd(
                    "ELEC_RAIL_NO_SOURCE",
                    Severity.HIGH,
                    None,
                    Text(
                        en=f"Rail {rail.name} has no source",
                        fr=f"Le rail {rail.name} n'a pas de source",
                    ),
                    Text(en="Nothing supplies this rail.", fr="Rien n'alimente ce rail."),
                    Text(
                        en="Select a battery or converter as source.",
                        fr="Choisir une batterie ou un convertisseur comme source.",
                    ),
                )
            )
        if rail.voltage_v is None:
            out.append(
                _fnd(
                    "ELEC_RAIL_NO_VOLTAGE",
                    Severity.MEDIUM,
                    None,
                    Text(
                        en=f"Rail {rail.name} has no defined voltage",
                        fr=f"Le rail {rail.name} n'a pas de tension définie",
                    ),
                    Text(
                        en="Voltage compatibility and currents cannot be evaluated.",
                        fr="La compatibilité en tension et les courants ne peuvent pas être évalués.",
                    ),
                    Text(en="Set the rail voltage.", fr="Définir la tension du rail."),
                )
            )
        elif rail.source_instance_id and rail.source_instance_id in ctx.inst:
            src = ctx.inst[rail.source_instance_id]
            ss = ctx.spec(src)
            if (
                ss
                and ss.output_voltage_v is not None
                and abs(ss.output_voltage_v - rail.voltage_v) > 1e-9
            ):
                out.append(
                    _fnd(
                        "ELEC_RAIL_SOURCE_MISMATCH",
                        Severity.HIGH,
                        src,
                        Text(
                            en="Rail voltage differs from the source output voltage",
                            fr="La tension du rail diffère de la tension de sortie de la source",
                        ),
                        Text(
                            en="The rail is declared at a voltage the source does not output.",
                            fr="Le rail est déclaré à une tension que la source ne délivre pas.",
                        ),
                        Text(
                            en="Align the rail voltage with the datasheet output voltage.",
                            fr="Aligner la tension du rail sur celle de la fiche technique.",
                        ),
                        value=rail.voltage_v,
                        unit="V",
                        limit=ss.output_voltage_v,
                        limit_source=_source_ref(ss),
                    )
                )
    per_load: dict[str, set[str]] = {}
    for pl in ctx.p.electrical.power_links:
        per_load.setdefault(pl.load_instance_id, set()).add(pl.rail_id)
    for iid, rails in per_load.items():
        if len(rails) > 1:
            inst = ctx.inst[iid]
            out.append(
                _fnd(
                    "ELEC_BACKFEED_RISK",
                    Severity.MEDIUM,
                    inst,
                    Text(
                        en="Component supplied from several rails (back-feed risk)",
                        fr="Composant alimenté par plusieurs rails (risque de retour de courant)",
                    ),
                    Text(
                        en="Two supplies on one device can back-feed one rail from the other.",
                        fr="Deux alimentations sur un même appareil peuvent se rétro-alimenter.",
                    ),
                    Text(
                        en="Verify isolation (diodes/ideal diodes/separate inputs per datasheet).",
                        fr="Vérifier l'isolation (diodes, séparation des entrées selon la fiche technique).",
                    ),
                )
            )
    return out


def _check_voltages(ctx: _Ctx) -> list[Finding]:
    out: list[Finding] = []
    for pl in ctx.p.electrical.power_links:
        inst = ctx.inst[pl.load_instance_id]
        rail = ctx.rails[pl.rail_id]
        spec = ctx.spec(inst)
        if spec is None or rail.voltage_v is None:
            continue
        v = rail.voltage_v
        lo, hi = spec.min_voltage_v, spec.max_voltage_v
        if hi is not None and v > hi:
            out.append(
                _fnd(
                    "ELEC_OVERVOLTAGE",
                    Severity.CRITICAL,
                    inst,
                    Text(en="Overvoltage", fr="Surtension"),
                    Text(
                        en="Supply voltage exceeds the maximum allowed by the datasheet.",
                        fr="La tension d'alimentation dépasse le maximum de la fiche technique.",
                    ),
                    Text(
                        en="Use a lower-voltage rail or a regulator.",
                        fr="Utiliser un rail de tension plus basse ou un régulateur.",
                    ),
                    value=v,
                    unit="V",
                    limit=hi,
                    limit_source=_source_ref(spec),
                )
            )
        elif lo is not None and v < lo:
            out.append(
                _fnd(
                    "ELEC_UNDERVOLTAGE",
                    Severity.HIGH,
                    inst,
                    Text(en="Undervoltage", fr="Sous-tension"),
                    Text(
                        en="Supply voltage is below the minimum required by the datasheet.",
                        fr="La tension d'alimentation est inférieure au minimum de la fiche technique.",
                    ),
                    Text(
                        en="Use a higher-voltage rail or a boost converter.",
                        fr="Utiliser un rail de tension plus haute ou un convertisseur élévateur.",
                    ),
                    value=v,
                    unit="V",
                    limit=lo,
                    limit_source=_source_ref(spec),
                )
            )
        elif lo is None or hi is None:
            out.append(
                _fnd(
                    "ELEC_VOLTAGE_RANGE_UNKNOWN",
                    Severity.INFO,
                    inst,
                    Text(
                        en="Voltage compatibility cannot be verified",
                        fr="Compatibilité en tension non vérifiable",
                    ),
                    Text(
                        en="Min/max voltage missing. Equal nominal voltages do not prove compatibility.",
                        fr="Tensions min/max manquantes. Des tensions nominales égales ne prouvent pas la compatibilité.",
                    ),
                    Text(
                        en="Enter the datasheet voltage range.",
                        fr="Saisir la plage de tension de la fiche technique.",
                    ),
                    value=v,
                    unit="V",
                )
            )
    return out


def _check_capacity(ctx: _Ctx, results: list[RailResult]) -> list[Finding]:
    out: list[Finding] = []
    margin = ctx.p.settings.margin_limit_fraction
    for r in results:
        if r.source_instance_id is None:
            continue
        src = ctx.inst.get(r.source_instance_id)
        spec = ctx.spec(src) if src else None
        if src is None or spec is None or spec.category is Category.BATTERY:
            continue  # battery limits: see battery engine
        if r.avg_current.value is None:
            missing = "; ".join(r.avg_current.missing_inputs[:6])
            out.append(
                _fnd(
                    "ELEC_CAPACITY_NOT_EVALUABLE",
                    Severity.INFO,
                    src,
                    Text(
                        en=f"Capacity of rail {r.name} cannot be evaluated",
                        fr=f"Capacité du rail {r.name} non évaluable",
                    ),
                    Text(en=f"Missing data: {missing}", fr=f"Données manquantes : {missing}"),
                    Text(
                        en="Complete the datasheets of the loads on this rail.",
                        fr="Compléter les fiches techniques des charges de ce rail.",
                    ),
                    value=r.partial_avg_current_a,
                    unit="A",
                    limit=spec.output_max_current_a,
                )
            )
            continue
        lim = spec.output_max_current_a
        if lim is None:
            out.append(
                _fnd(
                    "ELEC_SOURCE_LIMIT_UNKNOWN",
                    Severity.INFO,
                    src,
                    Text(
                        en="Source current limit unknown",
                        fr="Limite de courant de la source inconnue",
                    ),
                    Text(en="output_max_current_a missing.", fr="output_max_current_a manquant."),
                    Text(
                        en="Enter the datasheet output current limit.",
                        fr="Saisir la limite de courant de sortie de la fiche technique.",
                    ),
                    value=r.avg_current.value,
                    unit="A",
                )
            )
            continue
        i = r.avg_current.value
        if lim == 0 or i > lim:
            out.append(
                _fnd(
                    "ELEC_REGULATOR_OVERLOAD",
                    Severity.CRITICAL,
                    src,
                    Text(
                        en=f"Rail {r.name}: load exceeds source capability",
                        fr=f"Rail {r.name} : la charge dépasse la capacité de la source",
                    ),
                    Text(
                        en="Average load current is above the source's maximum output current.",
                        fr="Le courant moyen de charge dépasse le courant de sortie maximal de la source.",
                    ),
                    Text(
                        en="Use a higher-rated converter or reduce the load.",
                        fr="Utiliser un convertisseur de calibre supérieur ou réduire la charge.",
                    ),
                    value=i,
                    unit="A",
                    limit=lim,
                    limit_source=_source_ref(spec),
                )
            )
        elif i > margin * lim:
            out.append(
                _fnd(
                    "ELEC_MARGIN_LOW",
                    Severity.HIGH,
                    src,
                    Text(
                        en=f"Rail {r.name}: insufficient safety margin",
                        fr=f"Rail {r.name} : marge de sécurité insuffisante",
                    ),
                    Text(
                        en=f"Load exceeds {margin:.0%} of the source limit (project margin setting).",
                        fr=f"La charge dépasse {margin:.0%} de la limite de la source (réglage de marge du projet).",
                    ),
                    Text(
                        en="Choose a source with more headroom.",
                        fr="Choisir une source avec plus de marge.",
                    ),
                    value=i,
                    unit="A",
                    limit=margin * lim,
                    limit_source=_source_ref(spec),
                )
            )
        pk = r.peak_current.value
        if pk is not None and pk > lim:
            out.append(
                _fnd(
                    "ELEC_PEAK_EXCEEDS_SOURCE",
                    Severity.HIGH,
                    src,
                    Text(
                        en=f"Rail {r.name}: worst-case peak exceeds source limit",
                        fr=f"Rail {r.name} : le pic pire cas dépasse la limite de la source",
                    ),
                    Text(
                        en="Sum of datasheet peaks exceeds the source maximum (may be transient; check startup behaviour).",
                        fr="La somme des pics de fiches techniques dépasse le maximum de la source (peut être transitoire ; vérifier le démarrage).",
                    ),
                    Text(
                        en="Stagger startups, add bulk capacitance, or upsize the source.",
                        fr="Étaler les démarrages, ajouter de la capacité, ou surdimensionner la source.",
                    ),
                    value=pk,
                    unit="A",
                    limit=lim,
                    limit_source=_source_ref(spec),
                )
            )
    return out


def _check_grounds(ctx: _Ctx) -> list[Finding]:
    out: list[Finding] = []
    nets = ctx.p.electrical.ground_nets
    net_of: dict[str, set[str]] = {}
    for n in nets:
        for i in n.instance_ids:
            net_of.setdefault(i, set()).add(n.id)

    def common(a: str, b: str) -> bool:
        return bool(net_of.get(a, set()) & net_of.get(b, set()))

    for pl in ctx.p.electrical.power_links:
        rail = ctx.rails[pl.rail_id]
        if rail.source_instance_id is None:
            continue
        if not common(pl.load_instance_id, rail.source_instance_id):
            inst = ctx.inst[pl.load_instance_id]
            out.append(
                _fnd(
                    "ELEC_NO_COMMON_GROUND",
                    Severity.HIGH,
                    inst,
                    Text(
                        en=f"No common ground with the source of rail {rail.name}",
                        fr=f"Pas de masse commune avec la source du rail {rail.name}",
                    ),
                    Text(
                        en="Load and its supply are not in the same ground net.",
                        fr="La charge et son alimentation ne sont pas dans le même réseau de masse.",
                    ),
                    Text(
                        en="Add both to a common ground net.",
                        fr="Les ajouter à un même réseau de masse.",
                    ),
                )
            )
    for s in ctx.p.electrical.signal_links:
        if s.interface.value in ("wifi", "ethernet"):
            continue
        if not common(s.host_instance_id, s.peripheral_instance_id):
            out.append(
                _fnd(
                    "ELEC_SIGNAL_NO_COMMON_GROUND",
                    Severity.HIGH,
                    ctx.inst[s.peripheral_instance_id],
                    Text(
                        en=f"{s.interface.value.upper()} link without common ground",
                        fr=f"Liaison {s.interface.value.upper()} sans masse commune",
                    ),
                    Text(
                        en="Signals need a shared ground reference between both devices.",
                        fr="Les signaux nécessitent une référence de masse commune entre les deux appareils.",
                    ),
                    Text(
                        en="Put both devices in one ground net.",
                        fr="Mettre les deux appareils dans un même réseau de masse.",
                    ),
                    category="interfaces",
                )
            )
    return out


def _check_protection(ctx: _Ctx) -> list[Finding]:
    out: list[Finding] = []
    specs = [ctx.spec(i) for i in ctx.p.components]
    cats = {s.category for s in specs if s}
    if Category.BATTERY not in cats:
        return out
    if Category.FUSE not in cats:
        out.append(
            _fnd(
                "ELEC_NO_FUSE",
                Severity.MEDIUM,
                None,
                Text(en="No fuse in the project", fr="Aucun fusible dans le projet"),
                Text(
                    en="A battery without overcurrent protection is a fire risk.",
                    fr="Une batterie sans protection de surintensité présente un risque d'incendie.",
                ),
                Text(
                    en="Add fuses sized from the datasheets.",
                    fr="Ajouter des fusibles dimensionnés d'après les fiches techniques.",
                ),
            )
        )
    if Category.EMERGENCY_STOP not in cats:
        out.append(
            _fnd(
                "ELEC_NO_ESTOP",
                Severity.MEDIUM,
                None,
                Text(
                    en="No emergency stop in the project", fr="Aucun arrêt d'urgence dans le projet"
                ),
                Text(
                    en="A robot operating near visitors needs an emergency stop.",
                    fr="Un robot évoluant près de visiteurs nécessite un arrêt d'urgence.",
                ),
                Text(
                    en="Add an emergency stop cutting motor power.",
                    fr="Ajouter un arrêt d'urgence coupant l'alimentation des moteurs.",
                ),
            )
        )
    return out


def _check_temperature(ctx: _Ctx) -> list[Finding]:
    amb = ctx.p.settings.ambient_temp_c
    out: list[Finding] = []
    if amb is None:
        return out
    for inst in ctx.p.components:
        spec = ctx.spec(inst)
        if spec is None:
            continue
        if spec.temp_max_c is not None and amb > spec.temp_max_c:
            out.append(
                _fnd(
                    "THERMAL_AMBIENT_ABOVE_MAX",
                    Severity.HIGH,
                    inst,
                    Text(
                        en="Ambient temperature above operating maximum",
                        fr="Température ambiante supérieure au maximum de fonctionnement",
                    ),
                    Text(
                        en="Ambient exceeds the datasheet operating range (self-heating not included).",
                        fr="L'ambiante dépasse la plage de fonctionnement (auto-échauffement non inclus).",
                    ),
                    Text(
                        en="Cool the enclosure or choose a wider-range part.",
                        fr="Refroidir le boîtier ou choisir un composant à plage plus large.",
                    ),
                    value=amb,
                    unit="°C",
                    limit=spec.temp_max_c,
                    limit_source=_source_ref(spec),
                )
            )
        if spec.temp_min_c is not None and amb < spec.temp_min_c:
            out.append(
                _fnd(
                    "THERMAL_AMBIENT_BELOW_MIN",
                    Severity.HIGH,
                    inst,
                    Text(
                        en="Ambient temperature below operating minimum",
                        fr="Température ambiante inférieure au minimum de fonctionnement",
                    ),
                    Text(
                        en="Ambient is below the datasheet operating range.",
                        fr="L'ambiante est inférieure à la plage de fonctionnement.",
                    ),
                    Text(
                        en="Heat the enclosure or choose a wider-range part.",
                        fr="Chauffer le boîtier ou choisir un composant à plage plus large.",
                    ),
                    value=amb,
                    unit="°C",
                    limit=spec.temp_min_c,
                    limit_source=_source_ref(spec),
                )
            )
    return out


def _check_cables(ctx: _Ctx, results: list[RailResult]) -> tuple[list[CableResult], list[Finding]]:
    by_rail = {r.rail_id: r for r in results}
    cables: list[CableResult] = []
    out: list[Finding] = []
    frac = ctx.p.settings.max_voltage_drop_fraction
    for c in ctx.p.electrical.cables:
        rail = ctx.rails[c.rail_id]
        rr = by_rail.get(c.rail_id)
        cur: float | None = None
        missing: list[str] = []
        if c.load_instance_id is not None:
            inst = ctx.inst[c.load_instance_id]
            spec = ctx.spec(inst)
            if spec is None:
                missing.append("component spec")
            else:
                cur, m = _avg_current_one(spec, rail.voltage_v, ctx.override.get(inst.id))
                missing += m
                if cur is not None:
                    cur *= inst.quantity * inst.duty_cycle
        elif rr is not None and rr.avg_current.value is not None:
            cur = rr.avg_current.value
        else:
            missing.append("rail average current")
        if rail.voltage_v is None:
            missing.append("rail voltage_v")
        base = {"length_m": c.length_m, "section_mm2": c.section_mm2, "current_a": cur}
        formula_dv = "ΔV = I × ρ × 2L / A"
        if cur is None:
            cur_res = _ne(f"electrical.cable_current.{c.id}", "A", "I", missing)
        else:
            cur_res = CalcResult(
                name=f"electrical.cable_current.{c.id}",
                value=cur,
                unit="A",
                formula="I (from load/rail model)",
                inputs={"current_a": cur},
                status=ResultStatus.ESTIMATED,
                confidence=Confidence.MEDIUM,
            )
        if cur is not None and c.section_mm2 is not None:
            dv = cable_voltage_drop_v(cur, c.length_m, c.section_mm2)
            drop = CalcResult(
                name=f"electrical.cable_drop.{c.id}",
                value=dv,
                unit="V",
                formula=formula_dv,
                inputs=base,
                assumptions=[
                    f"copper resistivity {COPPER_RESISTIVITY_OHM_M:g} Ω·m at 20 °C",
                    "round trip = 2 × one-way length",
                ],
                status=ResultStatus.ESTIMATED,
                confidence=Confidence.MEDIUM,
                limits=[
                    "ampacity/heating not evaluated",
                    "connector and contact resistance ignored",
                ],
            )
        else:
            mm = list(missing)
            if c.section_mm2 is None:
                mm.append("section_mm2")
            drop = _ne(f"electrical.cable_drop.{c.id}", "V", formula_dv, mm)
        if drop.value is not None and rail.voltage_v:
            fr_res = CalcResult(
                name=f"electrical.cable_drop_fraction.{c.id}",
                value=drop.value / rail.voltage_v,
                unit="1",
                formula="ΔV / U_rail",
                inputs={"drop_v": drop.value, "rail_voltage_v": rail.voltage_v},
                status=ResultStatus.ESTIMATED,
                confidence=Confidence.MEDIUM,
            )
            if fr_res.value is not None and fr_res.value > frac:
                inst_for = ctx.inst.get(c.load_instance_id) if c.load_instance_id else None
                out.append(
                    _fnd(
                        "ELEC_CABLE_DROP_HIGH",
                        Severity.HIGH,
                        inst_for,
                        Text(
                            en=f"Cable {c.id}: voltage drop too high",
                            fr=f"Câble {c.id} : chute de tension trop élevée",
                        ),
                        Text(
                            en="Voltage drop exceeds the project limit (fraction of rail voltage).",
                            fr="La chute de tension dépasse la limite du projet (fraction de la tension du rail).",
                        ),
                        Text(
                            en="Increase the conductor section or shorten the run.",
                            fr="Augmenter la section du conducteur ou raccourcir le câble.",
                        ),
                        value=fr_res.value,
                        unit="1",
                        limit=frac,
                    )
                )
        else:
            fr_res = _ne(
                f"electrical.cable_drop_fraction.{c.id}",
                "1",
                "ΔV / U_rail",
                ["cable drop", "rail voltage_v"],
            )
        if cur is not None and rail.voltage_v:
            sec = CalcResult(
                name=f"electrical.cable_min_section.{c.id}",
                value=cable_min_section_mm2(cur, c.length_m, rail.voltage_v, frac),
                unit="mm²",
                formula="A_min = ρ × 2L × I / (f × U)",
                inputs={"current_a": cur, "length_m": c.length_m, "f": frac, "u_v": rail.voltage_v},
                assumptions=["voltage-drop criterion only"],
                status=ResultStatus.ESTIMATED,
                confidence=Confidence.MEDIUM,
                limits=["does not check ampacity/heating: round up to a standard size and verify"],
            )
        else:
            sec = _ne(
                f"electrical.cable_min_section.{c.id}",
                "mm²",
                "A_min",
                missing or ["rail voltage_v"],
            )
        cables.append(
            CableResult(
                cable_id=c.id,
                rail_id=c.rail_id,
                current=cur_res,
                voltage_drop=drop,
                drop_fraction=fr_res,
                min_section_mm2=sec,
            )
        )
    return cables, out


__all__ = [
    "COPPER_RESISTIVITY_OHM_M",
    "CableResult",
    "ElectricalAnalysis",
    "InvalidInputError",
    "RailResult",
    "analyze",
    "cable_min_section_mm2",
    "cable_voltage_drop_v",
    "current_a",
    "power_w",
]
