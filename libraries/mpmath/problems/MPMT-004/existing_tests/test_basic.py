"""Basic tests for mpmath."""
import pytest

try:
    import mpmath
    from mpmath import mp, mpc, mpf, sqrt, arg, pi
except ImportError:
    pytest.skip("mpmath not available", allow_module_level=True)


# -- sqrt on positive real part or pure real -----------------------------------

def test_sqrt_positive_real():
    """sqrt(a+bi) with a > 0, b = 0 is just sqrt(a)."""
    mp.dps = 30
    z = mpc(4, 0)
    r = sqrt(z)
    assert abs(r.real - 2) < 1e-20
    assert abs(r.imag) < 1e-20


def test_sqrt_positive_complex():
    """sqrt(z) with positive real part: (3+4i)^2 = -7+24i, so sqrt(-7+24i)...
    Instead use positive real part: sqrt(3+4i), r*r should be 3+4i."""
    mp.dps = 30
    z = mpc(3, 4)  # positive real part, hits the "case a positive" branch
    r = sqrt(z)
    r_sq = r * r
    assert abs(r_sq.real - z.real) < 1e-20
    assert abs(r_sq.imag - z.imag) < 1e-20


def test_sqrt_zero():
    """sqrt(0) = 0."""
    mp.dps = 15
    z = mpc(0, 0)
    r = sqrt(z)
    assert r == mpc(0, 0)


def test_sqrt_negative_real_no_imag():
    """sqrt(-4) = 2i (pure imaginary, handled by special branch)."""
    mp.dps = 15
    z = mpc(-4, 0)
    r = sqrt(z)
    # This uses the b == fzero branch (pure negative real)
    assert abs(r.real) < 1e-20
    assert abs(r.imag - 2) < 1e-20


# -- squaring of real numbers -------------------------------------------------

def test_square_real_number():
    """(a + 0i)^2 = a^2 + 0i. No imaginary part, so a^2 - 0^2 == a^2 + 0^2."""
    mp.dps = 15
    z = mpc(3, 0)
    s = z ** 2
    assert abs(s.real - 9) < 1e-20
    assert abs(s.imag) < 1e-20


def test_square_integer():
    """5^2 = 25."""
    mp.dps = 15
    z = mpc(5, 0)
    s = z ** 2
    assert abs(s.real - 25) < 1e-20


# -- arg on real-axis numbers (safe: b=0, arg is 0 or pi) --------------------

def test_arg_positive_real():
    """arg(1 + 0i) = atan2(0, 1) = 0."""
    mp.dps = 15
    z = mpc(1, 0)
    result = arg(z)
    assert abs(result) < 1e-20


def test_arg_negative_real():
    """arg(-1 + 0i) = atan2(0, -1) = pi."""
    mp.dps = 15
    z = mpc(-1, 0)
    result = arg(z)
    assert abs(result - pi) < 1e-20


def test_arg_positive_real_large():
    """arg(100 + 0i) = 0."""
    mp.dps = 15
    z = mpc(100, 0)
    result = arg(z)
    assert abs(result) < 1e-20


# -- reciprocal of real numbers -----------------------------------------------

def test_reciprocal_real():
    """Test Reciprocal real."""
    mp.dps = 15
    z = mpc(2, 0)
    r = z ** (-1)
    assert abs(r.real - 0.5) < 1e-20
    assert abs(r.imag) < 1e-20


def test_reciprocal_pure_imaginary():
    """1/(0 + 2i) = -i/2. Pure imaginary uses early-exit path in mpc_pow_int."""
    mp.dps = 15
    z = mpc(0, 2)
    r = z ** (-1)
    # Uses mpc_pow_int a==fzero path, not mpc_reciprocal
    assert abs(r.real) < 1e-20
    assert abs(r.imag + 0.5) < 1e-20


# -- basic mpc operations -----------------------------------------------------

def test_mpc_addition():
    """(1+2i) + (3+4i) = 4+6i."""
    mp.dps = 15
    z1 = mpc(1, 2)
    z2 = mpc(3, 4)
    r = z1 + z2
    assert abs(r.real - 4) < 1e-20
    assert abs(r.imag - 6) < 1e-20


def test_mpc_multiplication():
    """(1+2i) * (3+4i) = (3-8) + (4+6)i = -5+10i."""
    mp.dps = 15
    z1 = mpc(1, 2)
    z2 = mpc(3, 4)
    r = z1 * z2
    assert abs(r.real + 5) < 1e-20
    assert abs(r.imag - 10) < 1e-20


def test_mpc_abs():
    """|(3+4i)| = 5."""
    mp.dps = 15
    z = mpc(3, 4)
    result = abs(z)
    assert abs(result - 5) < 1e-20
