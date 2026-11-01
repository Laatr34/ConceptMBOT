import pytest

from app.domain.calc_result import ResultStatus
from app.domain.project import BatteryConfig
from app.domain.units import InvalidInputError
from app.engines import battery as b


def cfg(**kw):
    base = dict(
        cells_series=3,
        strings_parallel=2,
        cell_capacity_ah=2.5,
        cell_nominal_v=3.6,
        cell_max_v=4.2,
        cell_min_v=3.0,
        usable_fraction=0.8,
        discharge_efficiency=0.95,
    )
    base.update(kw)
    return BatteryConfig(**base)


def test_pack_hand_computed():
    p = b.pack(cfg(), max_discharge_current_a=10.0)
    assert p.nominal_voltage.value == pytest.approx(10.8)  # 3 x 3.6
    assert p.max_voltage.value == pytest.approx(12.6)  # 3 x 4.2
    assert p.min_voltage.value == pytest.approx(9.0)  # 3 x 3.0
    assert p.capacity_ah.value == pytest.approx(5.0)  # 2 x 2.5
    assert p.energy_wh.value == pytest.approx(54.0)  # 10.8 x 5
    assert p.usable_energy_wh.value == pytest.approx(43.2)  # 54 x 0.8
    assert p.max_power.value == pytest.approx(108.0)  # 10.8 x 10


def test_autonomy_three_distinct_quantities():
    p = b.pack(cfg())
    a = b.autonomy(
        cfg(measured_runtime_h=3.2, target_runtime_h=4.0), p, avg_current_a=1.0, peak_current_a=5.0
    )
    assert a.average_power.value == pytest.approx(10.8)  # 1 A x 10.8 V
    assert a.theoretical_h.value == pytest.approx(5.0)  # 54 / 10.8
    assert a.estimated_h.value == pytest.approx(54 * 0.8 * 0.95 / 10.8)  # 3.8
    assert a.measured_h.value == 3.2
    assert a.theoretical_h.status is ResultStatus.THEORETICAL
    assert a.estimated_h.status is ResultStatus.ESTIMATED
    assert a.measured_h.status is ResultStatus.MEASURED
    assert a.energy_margin.value == pytest.approx((3.8 - 4.0) / 4.0)
    assert a.theoretical_h.value > a.estimated_h.value  # ideal bound is above the estimate


def test_not_evaluable_without_data():
    p = b.pack(BatteryConfig())
    assert p.energy_wh.value is None and p.energy_wh.status is ResultStatus.NOT_EVALUABLE
    a = b.autonomy(BatteryConfig(), p, avg_current_a=None, peak_current_a=None)
    assert a.estimated_h.value is None and a.measured_h.value is None


def test_estimated_requires_dod_and_efficiency():
    c = cfg(discharge_efficiency=None)
    a = b.autonomy(c, b.pack(c), avg_current_a=1.0, peak_current_a=None)
    assert a.theoretical_h.value is not None
    assert a.estimated_h.value is None and "discharge_efficiency" in a.estimated_h.missing_inputs


def test_zero_power_no_division_by_zero():
    p = b.pack(cfg())
    a = b.autonomy(cfg(), p, avg_current_a=0.0, peak_current_a=0.0)
    assert a.theoretical_h.value is None
    with pytest.raises(InvalidInputError):
        b.autonomy_hours(10.0, 0.0)


def test_inconsistent_cell_voltages_rejected():
    with pytest.raises(InvalidInputError):
        b.pack(cfg(cell_min_v=4.0))
    with pytest.raises(InvalidInputError):
        b.pack(cfg(cell_max_v=3.0))


def test_findings():
    r = b.analyze(
        cfg(target_runtime_h=4.0),
        avg_current_a=11.0,
        peak_current_a=12.0,
        max_discharge_current_a=10.0,
        max_discharge_source="datasheet",
        rail_voltage_v=12.0,
    )
    codes = {f.code for f in r.findings}
    assert {"BATT_AVG_OVER_LIMIT", "BATT_PEAK_OVER_LIMIT", "BATT_AUTONOMY_SHORT"} <= codes
    avg = next(f for f in r.findings if f.code == "BATT_AVG_OVER_LIMIT")
    assert avg.severity.value == "critical" and avg.limit_source == "datasheet"
    r = b.analyze(
        cfg(),
        avg_current_a=1.0,
        peak_current_a=2.0,
        max_discharge_current_a=10.0,
        rail_voltage_v=5.0,
    )
    assert "BATT_RAIL_VOLTAGE_OUT_OF_RANGE" in {f.code for f in r.findings}


def test_empty_battery_reports_info_not_silence():
    r = b.analyze(BatteryConfig(), avg_current_a=None, peak_current_a=None)
    assert {"BATT_CONFIG_INCOMPLETE", "BATT_DISCHARGE_LIMIT_UNKNOWN"} <= {
        f.code for f in r.findings
    }
