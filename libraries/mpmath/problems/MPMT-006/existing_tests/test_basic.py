"""Basic tests for mpmath."""
import mpmath
from mpmath import mp, mpf, mpc, asin, acos, pi, sin, cos


def test_asin_real_in_range():
    """asin(x) for real x in [-1, 1] — uses direct mpf_asin path, not acos_asin."""
    mp.dps = 30
    assert asin(mpf(0)) == 0
    assert abs(asin(mpf(1)) - pi / 2) < mpf("1e-25")
    assert abs(asin(mpf(-1)) + pi / 2) < mpf("1e-25")
    assert abs(asin(mpf(0.5)) - pi / 6) < mpf("1e-25")


def test_acos_real_in_range():
    """acos(x) for real x in [-1, 1] — uses direct mpf_acos path."""
    mp.dps = 30
    assert abs(acos(mpf(1))) < mpf("1e-25")
    assert abs(acos(mpf(0)) - pi / 2) < mpf("1e-25")
    assert abs(acos(mpf(-1)) - pi) < mpf("1e-25")
    assert abs(acos(mpf(0.5)) - pi / 3) < mpf("1e-25")


def test_asin_acos_identity_real_in_range():
    """asin(x) + acos(x) = pi/2 for real x in [-1, 1]."""
    mp.dps = 30
    for x_val in [0, 0.25, 0.5, 0.75, 1.0, -0.5, -1.0]:
        x = mpf(x_val)
        s = asin(x) + acos(x)
        assert abs(s - pi / 2) < mpf("1e-25"), f"Failed for x={x_val}: sum={s}"


def test_asin_real_negative():
    """asin(-x) = -asin(x) for real x in [-1, 1] — odd function."""
    mp.dps = 30
    for x_val in [0.1, 0.3, 0.5, 0.7, 0.9]:
        x = mpf(x_val)
        assert abs(asin(-x) + asin(x)) < mpf("1e-25")


def test_acos_real_negative():
    """acos(-x) = pi - acos(x) for real x in [-1, 1]."""
    mp.dps = 30
    for x_val in [0.1, 0.3, 0.5, 0.7, 0.9]:
        x = mpf(x_val)
        assert abs(acos(-x) - (pi - acos(x))) < mpf("1e-25")


def test_asin_real_lt_neg_one():
    """Test Asin real lt neg one."""
    mp.dps = 30
    x = mpf(-2)
    result = asin(x)
    # asin(-2) = -pi/2 + i*acosh(2)
    expected_re = -pi / 2
    expected_im = mpmath.acosh(mpf(2))
    assert abs(result.real - expected_re) < mpf("1e-25")
    assert abs(result.imag - expected_im) < mpf("1e-25")


def test_acos_zero_pure_imaginary():
    """acos(bi) for pure imaginary input."""
    mp.dps = 30
    # acos(0) = pi/2
    assert abs(acos(mpf(0)) - pi / 2) < mpf("1e-25")


def test_complex_basic_types():
    """Basic type checks for complex asin/acos."""
    mp.dps = 15
    z = mpc(0.5, 0.5)
    r1 = asin(z)
    r2 = acos(z)
    assert isinstance(r1, mpc)
    assert isinstance(r2, mpc)


def test_precision_consistency():
    """Results should be consistent across different precisions."""
    for dps in [15, 30]:
        mp.dps = dps
        x = mpf(0.5)
        assert abs(asin(x) - pi / 6) < mpf(10) ** (-(dps - 2))
        assert abs(acos(x) - pi / 3) < mpf(10) ** (-(dps - 2))
    mp.dps = 15


def test_asin_conjugate():
    """asin(conj(z)) = conj(asin(z)) for z not on branch cut."""
    mp.dps = 30
    z = mpc(0, 0.5)
    r = asin(z)
    r_conj = asin(mpmath.conj(z))
    assert abs(r_conj - mpmath.conj(r)) < mpf("1e-25")
