"""Basic tests for mpmath."""
import mpmath
from mpmath import *
from mpmath.libmp import *
import random
import sys

try:
    long = long
except NameError:
    long = int


def test_type_compare():
    assert mpf(2) == mpc(2,0)
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
    assert (3+0j) + mpf(2.5) == 5.5
    assert mpc(2.5) + mpf(3) == 5.5
    assert mpc(2.5) + 3 == 5.5
    assert mpc(2.5) + 3.0 == 5.5
    assert mpc(2.5) + (3+0j) == 5.5
    assert 3 + mpc(2.5) == 5.5
    assert 3.0 + mpc(2.5) == 5.5
    assert (3+0j) + mpc(2.5) == 5.5


def test_sub():
    assert mpf(2.5) - mpf(3) == -0.5
    assert mpf(2.5) - 3 == -0.5
    assert mpf(2.5) - 3.0 == -0.5


def test_mul():
    assert mpf(2.5) * mpf(3) == 7.5
    assert mpf(2.5) * 3 == 7.5
    assert mpf(2.5) * 3.0 == 7.5


def test_div():
    assert mpf(6) / mpf(3) == 2.0
    assert mpf(6) / 3 == 2.0
    assert mpf(6) / 3.0 == 2.0


def test_pow():
    assert mpf(6) ** mpf(3) == 216.0
    assert mpf(6) ** 3 == 216.0


def test_hash():
    for i in range(-256, 256):
        assert hash(mpf(i)) == hash(i)
    assert hash(mpf(0.5)) == hash(0.5)
    assert hash(mpc(2,3)) == hash(2+3j)


def test_almost_equal():
    assert mpf(1.2).ae(mpf(1.20000001), 1e-7)
    assert not mpf(1.2).ae(mpf(1.20000001), 1e-9)
    assert not mpf(-0.7818314824680298).ae(mpf(-0.774695868667929))


def test_isnan_etc():
    from mpmath.rational import mpq
    assert isnan(nan) == True
    assert isnan(3) == False
    assert isnan(mpf(3)) == False
    assert isnan(inf) == False
    assert isinf(inf) == True
    assert isinf(-inf) == True
    assert isinf(3) == False
    assert isnormal(3) == True
    assert isnormal(mpf(0)) == False


def test_pi_e_constants():
    """Test Pi e constants."""
    mp.dps = 50
    p = mp.pi
    e = mp.e
    assert p.ae(mpf('3.14159265358979323846264338327950288419716939937510'))
    assert e.ae(mpf('2.71828182845904523536028747135266249775724709369995'))
    mp.dps = 15


def test_trig_basic():
    """Test Trig basic."""
    mp.dps = 15
    assert sin(0) == 0
    assert cos(0) == 1
    assert sin(pi/2).ae(1)
    assert cos(pi).ae(-1)
    assert tan(pi/4).ae(1)


def test_exp_log_basic():
    """Test Exp log basic."""
    mp.dps = 15
    assert exp(0) == 1
    assert log(1) == 0
    assert exp(log(2)).ae(2)
    assert log(exp(3)).ae(3)


def test_sqrt_basic():
    """Test Sqrt basic."""
    mp.dps = 15
    assert sqrt(4) == 2
    assert sqrt(9) == 3
    assert sqrt(2).ae(mpf('1.4142135623730950488'))


def test_agm_equal_args():
    """Test Agm equal args."""
    mp.dps = 15
    assert agm(1, 1) == 1
    assert agm(3, 3) == 3
    assert agm(mpf('0.5'), mpf('0.5')) == mpf('0.5')


def test_agm_near_unity():
    """Test Agm near unity."""
    mp.dps = 15
    # b = 0.5 has mag = -1, which is > -8 and < 20, so n = 0
    result = agm(1, mpf('0.5'))
    assert result > 0
    assert result < 1
    # agm(1, 0.5) ~ 0.72839... (check to 12 digits)
    assert result.ae(mpf('0.728395515523'), 1e-12)


def test_ellipk_zero():
    """K(0) = pi/2. m=0 is a special case."""
    mp.dps = 15
    # K(0) = pi/2
    assert ellipk(0).ae(pi / 2)


def test_ellipe_zero():
    """E(0) = pi/2."""
    mp.dps = 15
    assert ellipe(0).ae(pi / 2)


def test_ellipe_one():
    """E(1) = 1."""
    mp.dps = 15
    assert ellipe(1).ae(1)


def test_issue_438():
    assert mpf(finf) == mpf('inf')
    assert mpf(fninf) == mpf('-inf')
    assert mpf(fnan)._mpf_ == mpf('nan')._mpf_
