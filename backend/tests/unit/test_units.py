import math

import pytest

from app.domain import units as u


def test_roundtrips():
    assert u.m_to_mm(u.mm_to_m(123.4)) == pytest.approx(123.4)
    assert u.coulomb_to_ah(u.ah_to_coulomb(2.2)) == pytest.approx(2.2)
    assert u.joule_to_wh(u.wh_to_joule(11.1)) == pytest.approx(11.1)
    assert u.rad_s_to_rpm(u.rpm_to_rad_s(300)) == pytest.approx(300)
    assert u.m_s_to_kmh(u.kmh_to_m_s(3.6)) == pytest.approx(3.6)


def test_known_values():
    assert u.wh_to_joule(1.0) == 3600.0
    assert u.ah_to_coulomb(1.0) == 3600.0
    assert u.rpm_to_rad_s(60.0) == pytest.approx(2 * math.pi)
    assert u.kmh_to_m_s(36.0) == pytest.approx(10.0)
    assert u.deg_to_rad(180.0) == pytest.approx(math.pi)


@pytest.mark.parametrize("bad", [0.0, -1.0, math.nan, math.inf])
def test_require_positive_rejects(bad):
    with pytest.raises(u.InvalidInputError):
        u.require_positive("mass_kg", bad)


@pytest.mark.parametrize("bad", [-0.1, math.nan, math.inf])
def test_require_non_negative_rejects(bad):
    with pytest.raises(u.InvalidInputError):
        u.require_non_negative("current_a", bad)


def test_require_non_negative_accepts_zero():
    assert u.require_non_negative("current_a", 0.0) == 0.0
