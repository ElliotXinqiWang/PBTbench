"""Basic tests for mpmath."""

import mpmath
from mpmath import mp, mpf, mpc, inf, nan
from mpmath.libmp import (
    fone, fzero, finf, fninf, fnan,
    mpf_add, mpf_sub, mpf_mul, mpf_div,
    from_float, round_up, round_down, round_nearest,
)
import sys

try:
    long = long
except NameError:
    long = int


def test_type_compare():
    assert mpf(2) == mpc(2, 0)
    assert mpf(0) == mpc(0)
    assert mpf(2) != mpc(2, 0.00001)
    assert mpf(2) == 2.0
    assert mpf(2) != 3.0
    assert mpf(2) == 2
    assert mpf(2) != '2.0'
    assert mpc(2) != '2.0'


def test_add():
    assert mpf(2.5) + mpf(3) == 5.5
    assert mpf(2.5) + 3 == 5.5
    assert mpf(2.5) + 3.0 == 5.5
    assert 3 + mpf(2.5) == 5.5
    assert 3.0 + mpf(2.5) == 5.5
    assert mpc(2.5) + mpf(3) == 5.5
    assert mpc(2.5) + 3 == 5.5


def test_sub():
    assert mpf(2.5) - mpf(3) == -0.5
    assert mpf(2.5) - 3 == -0.5
    assert 3 - mpf(2.5) == 0.5
    assert mpc(2.5) - mpf(3) == -0.5


def test_mul():
    assert mpf(2.5) * mpf(3) == 7.5
    assert mpf(2.5) * 3 == 7.5
    assert 3 * mpf(2.5) == 7.5
    assert mpc(2.5) * mpf(3) == 7.5


def test_div():
    assert mpf(6) / mpf(3) == 2.0
    assert mpf(6) / 3 == 2.0
    assert 6 / mpf(3) == 2.0
    assert mpc(6) / mpf(3) == 2.0


def test_pow_int():
    # Only integer exponents — uses mpf_pow_int, not log/exp
    assert mpf(6) ** 3 == 216.0
    assert mpf(2) ** 10 == 1024.0
    assert mpf(3) ** 3 == 27.0
    assert mpf(4) ** 2 == 16.0
    # mpf(6)**mpf(3): texp=0 so mpf_pow_int is used (no log)
    assert mpf(6) ** mpf(3) == 216.0


def test_hash():
    for i in range(-10, 10):
        assert hash(mpf(i)) == hash(i)
    assert hash(mpf(0.5)) == hash(0.5)
    assert hash(mpc(2, 3)) == hash(2 + 3j)
    # '1e1000' parses via mpf_pow_int(10, 1000), no log
    assert hash(mpf('1e1000')) != hash('1e10000')


def test_add_rounding():
    mp.dps = 15
    a = from_float(1e-50)
    assert mpf_sub(mpf_add(fone, a, 53, round_up), fone, 53, round_up) == from_float(2.2204460492503131e-16)
    assert mpf_sub(fone, a, 53, round_up) == fone


def test_almost_equal():
    assert mpf(1.2).ae(mpf(1.20000001), 1e-7)
    assert not mpf(1.2).ae(mpf(1.20000001), 1e-9)


def test_special_values():
    # exp(0) = 1 and exp(x) for x in (-1, 1): no large-arg path, safe
    mp.dps = 15
    assert mpf('inf') == mpmath.inf
    assert mpmath.isnan(mpf('nan'))
    assert mpmath.isinf(mpf('inf'))
    assert not mpmath.isinf(mpf(3))

    result = mpmath.exp(mpf(0))
    assert result == 1

    result = mpmath.exp(mpf(1))
    assert abs(float(result) - 2.718281828459045) < 1e-12
