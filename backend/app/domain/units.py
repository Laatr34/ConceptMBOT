"""SI conventions and boundary conversions.

Internal values are SI floats. Name variables with a unit suffix
(``_v``, ``_a``, ``_w``, ``_nm``, ``_kg``, ``_m``, ``_s``).
Convert only at API/UI boundaries with the helpers below.
"""

from __future__ import annotations

import math

SECONDS_PER_HOUR = 3600.0


class InvalidInputError(ValueError):
    """Raised when an input is physically impossible (e.g. negative mass)."""


def require_positive(name: str, value: float) -> float:
    if not math.isfinite(value) or value <= 0:
        raise InvalidInputError(f"{name} must be a finite number > 0, got {value!r}")
    return value


def require_non_negative(name: str, value: float) -> float:
    if not math.isfinite(value) or value < 0:
        raise InvalidInputError(f"{name} must be a finite number >= 0, got {value!r}")
    return value


# --- length ---
def mm_to_m(mm: float) -> float:
    return mm / 1000.0


def m_to_mm(m: float) -> float:
    return m * 1000.0


# --- energy / charge ---
def ah_to_coulomb(ah: float) -> float:
    return ah * SECONDS_PER_HOUR


def coulomb_to_ah(coulomb: float) -> float:
    return coulomb / SECONDS_PER_HOUR


def wh_to_joule(wh: float) -> float:
    return wh * SECONDS_PER_HOUR


def joule_to_wh(joule: float) -> float:
    return joule / SECONDS_PER_HOUR


# --- rotation / speed ---
def rpm_to_rad_s(rpm: float) -> float:
    return rpm * 2.0 * math.pi / 60.0


def rad_s_to_rpm(rad_s: float) -> float:
    return rad_s * 60.0 / (2.0 * math.pi)


def kmh_to_m_s(kmh: float) -> float:
    return kmh / 3.6


def m_s_to_kmh(m_s: float) -> float:
    return m_s * 3.6


def deg_to_rad(deg: float) -> float:
    return math.radians(deg)


def rad_to_deg(rad: float) -> float:
    return math.degrees(rad)
