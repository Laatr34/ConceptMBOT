import math

import pytest

from app.domain.calc_result import ResultStatus
from app.domain.project import CableRun
from app.domain.units import InvalidInputError
from app.engines import electrical as el
from tests.helpers import power_chain


def codes(an):
    return {f.code for f in an.findings}


def rail(an, rid):
    return next(r for r in an.rails if r.rail_id == rid)


# ---- basic laws -------------------------------------------------------------
def test_power_and_current_laws():
    assert el.power_w(12.0, 2.0).value == 24.0
    assert el.current_a(24.0, 12.0).value == 2.0
    assert el.power_w(0.0, 5.0).value == 0.0


@pytest.mark.parametrize(
    "fn,args",
    [
        (el.power_w, (-1, 1)),
        (el.current_a, (1, 0)),
        (el.current_a, (1, -3)),
        (el.power_w, (math.nan, 1)),
    ],
)
def test_laws_reject_impossible_inputs(fn, args):
    with pytest.raises(InvalidInputError):
        fn(*args)


def test_cable_formulas_reference_values():
    # rho=1.68e-8, L=2 m, A=1.5 mm^2, I=10 A: R = 1.68e-8*4/1.5e-6 = 0.0448 ohm -> 0.448 V
    assert el.cable_voltage_drop_v(10.0, 2.0, 1.5) == pytest.approx(0.448)
    # 12 V, 5 % -> 0.6 V allowed: A = 1.68e-8*2*2*10/0.6 = 1.12e-6 m^2 = 1.12 mm^2
    assert el.cable_min_section_mm2(10.0, 2.0, 12.0, 0.05) == pytest.approx(1.12)
    # consistency: section found gives exactly the allowed drop
    a = el.cable_min_section_mm2(10.0, 2.0, 12.0, 0.05)
    assert el.cable_voltage_drop_v(10.0, 2.0, a) == pytest.approx(0.05 * 12.0)


# ---- rail currents ------------------------------------------------------------
def test_rail_currents_hand_computed():
    project, lib = power_chain()
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    r5 = rail(an, "r5")
    # Pi 1.2 A + camera 5 W / 5 V = 1.0 A
    assert r5.avg_current.value == pytest.approx(2.2)
    # peaks: Pi 2.0 + camera max 1.5
    assert r5.peak_current.value == pytest.approx(3.5)
    assert r5.avg_power.value == pytest.approx(11.0)
    # converter input: 11 W / (12 V * 0.9) = 1.018518...; motors 2 x 0.5 A
    r12 = rail(an, "r12")
    assert r12.avg_current.value == pytest.approx(11.0 / 10.8 + 1.0)
    # peak 12 V: converter 3.5*5/(12*0.9) + motors 2*4 A stall
    assert r12.peak_current.value == pytest.approx(17.5 / 10.8 + 8.0)
    assert r5.avg_current.status is ResultStatus.ESTIMATED


def test_duty_cycle_scales_average_not_peak():
    project, lib = power_chain()
    project.components[2].duty_cycle = 0.5  # Pi
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    assert rail(an, "r5").avg_current.value == pytest.approx(0.6 + 1.0)
    assert rail(an, "r5").peak_current.value == pytest.approx(3.5)


def test_missing_data_is_not_evaluable_never_zero():
    project, lib = power_chain()
    an = el.analyze(project, lib)  # no motor running current provided
    r12 = rail(an, "r12")
    assert r12.avg_current.value is None
    assert r12.avg_current.status is ResultStatus.NOT_EVALUABLE
    assert any("motor" in m for m in r12.avg_current.missing_inputs)
    assert "m" in r12.unknown_loads
    assert r12.partial_avg_current_a == pytest.approx(11.0 / 10.8)  # known part only
    assert "ELEC_CAPACITY_NOT_EVALUABLE" not in codes(an)  # battery rail: no converter limit


def test_converter_without_efficiency_not_evaluable():
    project, lib = power_chain()
    lib["dcdc"] = lib["dcdc"].model_copy(update={"efficiency": None})
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    r12 = rail(an, "r12")
    assert r12.avg_current.value is None
    assert any("efficiency" in m for m in r12.avg_current.missing_inputs)


# ---- findings ----------------------------------------------------------------
def test_clean_design_has_no_critical_or_high():
    project, lib = power_chain()
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    bad = [f for f in an.findings if f.severity.value in ("critical", "high")]
    # only the worst-case peak (3.5 A > 3 A) is flagged
    assert [f.code for f in bad] == ["ELEC_PEAK_EXCEEDS_SOURCE"]


def test_overload_and_margin():
    project, lib = power_chain(conv_limit=2.0)
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    f = next(f for f in an.findings if f.code == "ELEC_REGULATOR_OVERLOAD")
    assert f.severity.value == "critical" and f.value == pytest.approx(2.2) and f.limit == 2.0

    project, lib = power_chain(conv_limit=2.5)  # 2.2 A > 0.8 * 2.5 = 2.0 A
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    f = next(f for f in an.findings if f.code == "ELEC_MARGIN_LOW")
    assert f.limit == pytest.approx(2.0)


def test_exactly_at_limit_is_not_overload():
    project, lib = power_chain(conv_limit=2.2)
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    assert "ELEC_REGULATOR_OVERLOAD" not in codes(an)
    assert "ELEC_MARGIN_LOW" in codes(an)


def test_overvoltage_undervoltage_and_unknown_range():
    project, lib = power_chain()
    project.electrical.rails[1].voltage_v = 6.0  # Pi max 5.25 V
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    assert {"ELEC_OVERVOLTAGE", "ELEC_RAIL_SOURCE_MISMATCH"} <= codes(an)

    project, lib = power_chain()
    project.electrical.rails[1].voltage_v = 4.0
    assert "ELEC_UNDERVOLTAGE" in codes(
        el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    )

    project, lib = power_chain()
    lib["pi"] = lib["pi"].model_copy(update={"min_voltage_v": None, "max_voltage_v": None})
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    f = next(f for f in an.findings if f.code == "ELEC_VOLTAGE_RANGE_UNKNOWN")
    assert f.severity.value == "info"  # same nominal voltage is NOT treated as compatible


def test_missing_ground_unpowered_and_source():
    project, lib = power_chain()
    project.electrical.ground_nets[0].instance_ids.remove("pi")
    project.electrical.power_links = [
        p for p in project.electrical.power_links if p.load_instance_id != "s"
    ]
    project.electrical.rails[0].source_instance_id = None
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    assert {"ELEC_NO_COMMON_GROUND", "ELEC_UNPOWERED", "ELEC_RAIL_NO_SOURCE"} <= codes(an)


def test_backfeed_and_protection_and_temperature():
    project, lib = power_chain()
    from app.domain.project import PowerLink

    project.electrical.power_links.append(PowerLink(load_instance_id="pi", rail_id="r12"))
    project.settings.ambient_temp_c = 40.0
    lib["pi"] = lib["pi"].model_copy(update={"temp_max_c": 30.0, "sources": ["datasheet X"]})
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    assert {
        "ELEC_BACKFEED_RISK",
        "ELEC_NO_FUSE",
        "ELEC_NO_ESTOP",
        "THERMAL_AMBIENT_ABOVE_MAX",
    } <= codes(an)
    t = next(f for f in an.findings if f.code == "THERMAL_AMBIENT_ABOVE_MAX")
    assert t.limit_source == "datasheet X" and t.limit == 30.0


def test_missing_library_component_flagged():
    project, lib = power_chain()
    del lib["pi"]
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    assert "DATA_COMPONENT_MISSING" in codes(an)


def test_power_loop_detected():
    project, lib = power_chain()
    from app.domain.project import PowerLink

    project.electrical.power_links.append(PowerLink(load_instance_id="c", rail_id="r5"))
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    assert "ELEC_RAIL_CYCLE" in codes(an)


# ---- cables ---------------------------------------------------------------------
def test_cable_analysis():
    project, lib = power_chain()
    project.electrical.cables = [
        CableRun(id="k1", rail_id="r5", length_m=2.0, section_mm2=0.25),
        CableRun(id="k2", rail_id="r5", length_m=1.0),
    ]
    an = el.analyze(project, lib, motor_running_current_a={"m": 0.5})
    k1, k2 = an.cables
    # I = 2.2 A on 5 V rail: dV = 2.2 * 1.68e-8*4/0.25e-6 = 0.59136 V -> 11.8 % > 5 %
    assert k1.voltage_drop.value == pytest.approx(0.59136)
    assert k1.drop_fraction.value == pytest.approx(0.59136 / 5.0)
    assert "ELEC_CABLE_DROP_HIGH" in codes(an)
    assert k2.voltage_drop.status is ResultStatus.NOT_EVALUABLE  # section unknown
    assert k2.min_section_mm2.value == pytest.approx(1.68e-8 * 2 * 1.0 * 2.2 / (0.05 * 5.0) * 1e6)
