"""Basic tests for sympy."""

import pytest
from sympy.polys import ring, ZZ, QQ
from sympy.polys.densearith import (
    dup_rr_div, dup_mul,
    dup_pdiv, dup_ff_div, dmp_rr_div,
)
from sympy.polys.euclidtools import (
    dup_zz_heu_gcd, dup_rr_prs_gcd, dup_qq_heu_gcd,
    dup_ff_prs_gcd, dmp_lcm, dup_rr_lcm,
)
from sympy.polys.densebasic import dup_normal, dmp_normal
from sympy import Poly, symbols


# ---------------------------------------------------------------------------
# dup_rr_div: loop body never executes (lc_r % lc_g != 0 on first iteration)
# ---------------------------------------------------------------------------

def test_dup_rr_div_no_division():
    """dup_rr_div returns (0, f) when lc_g does not divide lc_f."""
    f = dup_normal([3, 1, 1, 5], ZZ)
    g = dup_normal([5, -3, 1], ZZ)
    q, r = [], f
    assert dup_rr_div(f, g, ZZ) == (q, r)


# ---------------------------------------------------------------------------
# dup_rr_lcm: all test inputs have positive leading coefficients
# ---------------------------------------------------------------------------

def test_dup_rr_lcm_positive_coefficients():
    """dup_rr_lcm with positive-leading-coefficient polynomials."""
    R, x = ring("x", ZZ)
    assert R.dup_lcm(2, 6) == 6
    assert R.dup_lcm(2*x**3, 6*x) == 6*x**3
    assert R.dup_lcm(2*x**3, 3*x) == 6*x**3
    assert R.dup_lcm(x**2 + x, x) == x**2 + x
    assert R.dup_lcm(x**2 + x, 2*x) == 2*x**2 + 2*x


# ---------------------------------------------------------------------------
# dup_mul: only small polynomials tested (n < 100, no Karatsuba path)
# ---------------------------------------------------------------------------

def test_dup_mul_small():
    """dup_mul with small polynomials uses naive algorithm, not Karatsuba."""
    R, x = ring("x", ZZ)
    assert R.dup_mul(x - 2, x + 2) == x**2 - 4
    assert R.dup_mul(x**2 + 1, x**2 - 1) == x**4 - 1
    assert R.dup_mul(3*x**2 + 2*x + 1, x + 1) == 3*x**3 + 5*x**2 + 3*x + 1


# ---------------------------------------------------------------------------
# dup_zz_heu_gcd: test coefficients small (< x//2 threshold)
# ---------------------------------------------------------------------------

def test_dup_zz_heu_gcd_small_coefficients():
    """dup_zz_heu_gcd with small-coefficient polynomials."""
    R, x = ring("x", ZZ)
    # GCD coefficients are well below the evaluation point threshold
    assert R.dup_zz_heu_gcd(x**2 - 1, x**2 - 3*x + 2) == (x - 1, x + 1, x - 2)
    assert R.dup_zz_heu_gcd(2*x**2 - 4, 2*x) == (2, x**2 - 2, x)


def test_dup_rr_prs_gcd():
    """dup_rr_prs_gcd on standard polynomials."""
    R, x = ring("x", ZZ)
    assert R.dup_rr_prs_gcd(x**2 - 1, x**2 - 3*x + 2) == (x - 1, x + 1, x - 2)


def test_dup_ff_prs_gcd():
    """dup_ff_prs_gcd on QQ polynomials."""
    R, x = ring("x", QQ)
    f = x**2 + QQ(7,2)*x + 3
    g = x**2 + 2*x
    h, cff, cfg = R.dup_ff_prs_gcd(f, g)
    # Verify cofactor relationship: h*cff == f and h*cfg == g
    assert R.dup_mul(h, cff) == f
    assert R.dup_mul(h, cfg) == g


# ---------------------------------------------------------------------------
# dup_qq_heu_gcd: test inputs have equal denominators (cf == cg)
# ---------------------------------------------------------------------------

def test_dup_qq_heu_gcd_equal_denominators():
    """dup_qq_heu_gcd with equal-denominator inputs (cf == cg, swap is invisible)."""
    R, x = ring("x", QQ)
    f = QQ(1,2)*x**2 + x + QQ(1,2)
    g = QQ(1,2)*x + QQ(1,2)
    h = x + 1
    assert R.dup_qq_heu_gcd(f, g) == (h, g, QQ(1,2))


# ---------------------------------------------------------------------------
# dmp_lcm: only ZZ ring tested (does not call dmp_ff_lcm)
# ---------------------------------------------------------------------------

def test_dmp_lcm_integer_ring():
    """dmp_lcm with ZZ ring uses dmp_rr_lcm, not dmp_ff_lcm."""
    R, x, y = ring("x,y", ZZ)
    assert R.dmp_lcm(x, y) == x*y
    assert R.dmp_lcm(2*x**3, 6*x*y**2) == 6*x**3*y**2
    assert R.dmp_lcm(x**2*y, x*y**2) == x**2*y**2


# ---------------------------------------------------------------------------
# dup_pdiv: specific case where N ends at 0 after loop
# ---------------------------------------------------------------------------

def test_dup_pdiv():
    """dup_pdiv standard case with lc_g = 5."""
    f = dup_normal([3, 1, 1, 5], ZZ)
    g = dup_normal([5, -3, 1], ZZ)
    q = dup_normal([15, 14], ZZ)
    r = dup_normal([52, 111], ZZ)
    assert dup_pdiv(f, g, ZZ) == (q, r)


# ---------------------------------------------------------------------------
# Poly API smoke tests
# ---------------------------------------------------------------------------

def test_poly_gcd_basic():
    """Poly.gcd() with basic integer polynomials."""
    x = symbols('x')
    f = Poly(x**2 - 1, x, domain='ZZ')
    g = Poly(x**2 - 3*x + 2, x, domain='ZZ')
    assert Poly.gcd(f, g) == Poly(x - 1, x, domain='ZZ')


def test_poly_lcm_univariate_qq():
    """Poly.lcm() with univariate QQ polynomial."""
    x = symbols('x')
    pfq = Poly(4*x**2 + x + 2, domain='QQ')
    assert pfq.lcm(pfq) == pfq.monic()


def test_poly_div_basic():
    """Poly.div() satisfies q*g + r == f."""
    x = symbols('x')
    f = Poly(x**3 + 2*x**2 + x + 1, x, domain='ZZ')
    g = Poly(x + 1, x, domain='ZZ')
    q, r = f.div(g)
    assert q * g + r == f
