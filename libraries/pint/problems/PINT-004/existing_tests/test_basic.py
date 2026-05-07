"""Basic tests for pint."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pint
import pytest

ureg = pint.UnitRegistry()


# ─── Basic unit conversions (multiplicative, base-unit path) ─────────────

def test_meter_to_kilometer():
    """Test Meter to kilometer."""
    q = 1000 * ureg.meter
    assert abs(q.to("kilometer").magnitude - 1.0) < 1e-10


def test_kilometer_to_meter():
    q = 5 * ureg.kilometer
    assert abs(q.to("meter").magnitude - 5000.0) < 1e-10


def test_gram_to_kilogram():
    q = 1000 * ureg.gram
    assert abs(q.to("kilogram").magnitude - 1.0) < 1e-10


def test_second_to_minute():
    """Second -> minute: both through accumulators (second is base)."""
    q = 60 * ureg.second
    assert abs(q.to("minute").magnitude - 1.0) < 1e-10


def test_minute_to_second():
    q = 1 * ureg.minute
    assert abs(q.to("second").magnitude - 60.0) < 1e-10


# ─── Arithmetic with quantities ───────────────────────────────────────────

def test_addition():
    q1 = 1 * ureg.meter
    q2 = 2 * ureg.meter
    assert (q1 + q2).magnitude == 3.0


def test_multiplication():
    q1 = 2 * ureg.meter
    q2 = 3 * ureg.meter
    result = q1 * q2
    assert result.magnitude == 6.0
    assert str(result.units) == "meter ** 2"


def test_division():
    q1 = 10 * ureg.meter
    q2 = 2 * ureg.second
    result = q1 / q2
    assert result.magnitude == 5.0


# ─── Safe m/s conversion (s is base unit, no denominator fraction) ────────

def test_m_per_s_conversion():
    """m/s conversion is safe: second is a base unit, no denominator fraction."""
    q = 10 * ureg.meter / ureg.second
    q_cm_per_s = q.to("centimeter / second")
    assert abs(q_cm_per_s.magnitude - 1000.0) < 1e-9


# ─── Dimensionality checks ────────────────────────────────────────────────

def test_dimensionality():
    q = 1 * ureg.meter
    assert "[length]" in str(q.dimensionality)


def test_compatible_units():
    q1 = 1 * ureg.meter
    q2 = 1 * ureg.kilometer
    assert q1.dimensionality == q2.dimensionality


# ─── to_base_units (uses _get_root_units but not denominator fraction) ────

def test_kilometer_to_base():
    """km.to_base_units() uses scale=1000 in numerator, not denominator."""
    q = 5 * ureg.kilometer
    base = q.to_base_units()
    assert abs(base.magnitude - 5000.0) < 1e-10
    assert "meter" in str(base.units)


def test_newton_to_base():
    q = 1 * ureg.newton
    base = q.to_base_units()
    # 1 N = 1 kg*m/s^2
    assert abs(base.magnitude - 1.0) < 1e-10


# ─── Simple unit parsing ──────────────────────────────────────────────────

def test_parse_unit():
    q = ureg.parse_expression("5 meter")
    assert q.magnitude == 5.0


def test_unit_equality():
    u1 = ureg.meter
    u2 = ureg.Unit("meter")
    assert u1 == u2
