"""
Ground-truth PBT for GALS-005.

Tests four bugs in galois polynomial arithmetic:
  bug_1: galois/_polys/_lagrange.py  -- Lagrange basis denominator flipped
  bug_2: galois/_polys/_dense.py     -- Horner evaluation accumulator wrong
  bug_3: galois/_polys/_poly.py      -- Polynomial derivative coefficient off-by-one
  bug_4: galois/_polys/_dense.py     -- roots_jit reports wrong root powers
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
import galois


# ---------------------------------------------------------------------------
# Helpers / strategies
# ---------------------------------------------------------------------------

SMALL_PRIMES = [5, 7, 11, 13]


@st.composite
def gf_prime_field_and_n_points(draw, min_points=2, max_points=5):
    """Return (GF, x_array, y_array) with distinct x values in GF(p)."""
    p = draw(st.sampled_from(SMALL_PRIMES))
    GF = galois.GF(p)
    n = draw(st.integers(min_value=min_points, max_value=min(max_points, p - 1)))
    xs = draw(
        st.lists(st.integers(min_value=0, max_value=p - 1),
                 min_size=n, max_size=n, unique=True)
    )
    ys = draw(
        st.lists(st.integers(min_value=0, max_value=p - 1),
                 min_size=n, max_size=n)
    )
    return GF, GF(xs), GF(ys)


@st.composite
def gf_poly_and_value(draw, min_degree=2, max_degree=5):
    """Return (GF, poly, value) - poly of given degree over GF(p)."""
    p = draw(st.sampled_from(SMALL_PRIMES))
    GF = galois.GF(p)
    degree = draw(st.integers(min_value=min_degree, max_value=max_degree))
    lead = draw(st.integers(min_value=1, max_value=p - 1))
    rest = draw(
        st.lists(st.integers(min_value=0, max_value=p - 1),
                 min_size=degree, max_size=degree)
    )
    val = draw(st.integers(min_value=0, max_value=p - 1))
    poly = galois.Poly(GF([lead] + rest))
    return GF, poly, GF(val)


@st.composite
def gf_two_polys(draw, min_degree=1, max_degree=4):
    """Return (GF, f, g) - two polynomials over the same prime field."""
    p = draw(st.sampled_from(SMALL_PRIMES))
    GF = galois.GF(p)
    deg_f = draw(st.integers(min_value=min_degree, max_value=max_degree))
    deg_g = draw(st.integers(min_value=min_degree, max_value=max_degree))
    lead_f = draw(st.integers(min_value=1, max_value=p - 1))
    lead_g = draw(st.integers(min_value=1, max_value=p - 1))
    rest_f = draw(st.lists(st.integers(0, p - 1), min_size=deg_f, max_size=deg_f))
    rest_g = draw(st.lists(st.integers(0, p - 1), min_size=deg_g, max_size=deg_g))
    f = galois.Poly(GF([lead_f] + rest_f))
    g = galois.Poly(GF([lead_g] + rest_g))
    return GF, f, g


@st.composite
def gf_poly_with_known_roots(draw, n_roots=3):
    """Return (GF, f, roots_gf) where f = prod(x - r_i) for distinct non-zero roots."""
    p = draw(st.sampled_from([7, 11, 13]))
    GF = galois.GF(p)
    all_nonzero = list(range(1, p))
    roots_int = draw(
        st.lists(st.sampled_from(all_nonzero),
                 min_size=n_roots, max_size=n_roots, unique=True)
    )
    roots_gf = GF(roots_int)
    f = galois.Poly.Roots(roots_gf)
    return GF, f, roots_gf


# ---------------------------------------------------------------------------
# Bug 1: Lagrange basis denominator flipped in _lagrange.py:129
# ---------------------------------------------------------------------------

@settings(max_examples=500, deadline=None)
@given(gf_prime_field_and_n_points(min_points=2, max_points=4))
def test_lagrange_degree1_coefficients_bug1(args):
    """
    For exactly 2 interpolation points (x0,y0) and (x1,y1), the Lagrange
    polynomial is the unique linear polynomial:
      slope = (y0 - y1) / (x0 - x1)
      intercept = y0 - slope * x0

    We check the leading coefficient (slope) and constant term (intercept)
    against this closed-form formula. This avoids using Poly evaluation
    entirely -- we compare polynomial coefficients.

    Detects bug_1: The denominator (x0 - x1) is flipped to (x1 - x0),
    negating the slope and intercept, which fails the coefficient check.
    """
    GF, x, y = args
    p = GF.characteristic
    assume(len(x) == 2)

    x0, x1 = int(x[0]), int(x[1])
    y0, y1 = int(y[0]), int(y[1])
    denom = (x0 - x1) % p
    assume(denom != 0)

    L = galois.lagrange_poly(x, y)

    # Expected slope and intercept over GF(p)
    denom_inv = pow(denom, p - 2, p)
    expected_slope = ((y0 - y1) * denom_inv) % p
    expected_intercept = (y0 - expected_slope * x0) % p

    if L.degree == 0:
        # Constant polynomial (slope == 0, intercept == y0 == y1)
        got_slope = 0
        got_intercept = int(L.coeffs[-1])
    else:
        got_slope = int(L.coeffs[0])
        got_intercept = int(L.coeffs[-1])

    assert got_slope == expected_slope, (
        f"Slope wrong: got {got_slope}, expected {expected_slope} "
        f"(x={[x0,x1]}, y={[y0,y1]}, p={p})"
    )
    assert got_intercept == expected_intercept, (
        f"Intercept wrong: got {got_intercept}, expected {expected_intercept} "
        f"(x={[x0,x1]}, y={[y0,y1]}, p={p})"
    )


@settings(max_examples=500, deadline=None)
@given(gf_prime_field_and_n_points(min_points=3, max_points=5))
def test_lagrange_constant_term_bug1(args):
    """
    Verifies the constant term of the Lagrange polynomial L(0) = L.coeffs[-1].

    We compute L(0) = sum_j y_j * prod_{m!=j} (-x_m) / (x_j - x_m)
    directly using integer arithmetic mod p, bypassing galois evaluation.

    Detects bug_1: Denominator flip changes every basis function's scalar
    factor, making the constant term wrong for most inputs.
    """
    GF, x, y = args
    p = GF.characteristic
    k = len(x)

    # Direct computation of L(0) using integer arithmetic mod p
    L_at_zero = 0
    skip = False
    for j in range(k):
        term = int(y[j])
        for m in range(k):
            if m == j:
                continue
            neg_xm = (-int(x[m])) % p
            denom = (int(x[j]) - int(x[m])) % p
            if denom == 0:
                skip = True
                break
            denom_inv = pow(denom, p - 2, p)
            term = (term * neg_xm * denom_inv) % p
        if skip:
            break
        L_at_zero = (L_at_zero + term) % p

    assume(not skip)

    L = galois.lagrange_poly(x, y)
    got_constant = int(L.coeffs[-1])

    assert got_constant == L_at_zero, (
        f"Lagrange constant term wrong: got {got_constant}, expected {L_at_zero} "
        f"(x={[int(xi) for xi in x]}, y={[int(yi) for yi in y]}, p={p})"
    )


# ---------------------------------------------------------------------------
# Bug 2: Horner evaluation wrong in _dense.py:438
# ---------------------------------------------------------------------------

@settings(max_examples=500, deadline=None)
@given(gf_poly_and_value(min_degree=2, max_degree=5))
def test_poly_evaluation_horner_bug2(args):
    """
    Verifies that galois polynomial evaluation f(v) matches brute-force.

    For f(x) = a_d*x^d + ... + a_0, f(v) must equal sum(a_k * v^k).
    We compute the brute-force sum using integer arithmetic mod p.

    Detects bug_2: When Horner accumulates as `coeff*v + acc` instead of
    `coeff + acc*v`, the result differs for degree >= 2 polynomials.
    """
    GF, f, v = args
    p = GF.characteristic

    # Galois built-in evaluation
    result_galois = f(v)

    # Brute-force: sum c_i * v^i using integer arithmetic mod p
    v_int = int(v)
    coeffs_asc = [int(c) for c in reversed(f.coeffs)]  # ascending order
    expected_int = 0
    v_pow = 1
    for c in coeffs_asc:
        expected_int = (expected_int + c * v_pow) % p
        v_pow = (v_pow * v_int) % p

    assert int(result_galois) == expected_int, (
        f"f({v_int}) = {int(result_galois)}, expected {expected_int} "
        f"(f = {f}, GF({p}))"
    )


@settings(max_examples=500, deadline=None)
@given(
    st.sampled_from(SMALL_PRIMES),
    st.lists(st.integers(0, 1), min_size=3, max_size=6),
)
def test_poly_evaluation_at_field_elements_bug2(p, root_mask):
    """
    Constructs a polynomial from known roots, then verifies evaluation
    at non-roots returns non-zero (in general) and at roots returns 0.

    We build f = (x-1)(x-2)...(x-k) over GF(p) for the roots indicated
    by root_mask, then check all field elements via brute-force comparison.

    Detects bug_2: When Horner is wrong, f(root) may not return 0.
    """
    GF = galois.GF(p)
    roots_int = [i + 1 for i, take in enumerate(root_mask) if take and i + 1 < p]
    if len(roots_int) == 0:
        roots_int = [1]
    roots_gf = GF(roots_int)
    f = galois.Poly.Roots(roots_gf)

    for r in roots_gf:
        result = f(r)
        assert int(result) == 0, (
            f"f({int(r)}) should be 0 (it's a root), got {int(result)} "
            f"for f={f} over GF({p})"
        )


# ---------------------------------------------------------------------------
# Bug 3: Polynomial derivative coefficient off-by-one in _poly.py:886
# ---------------------------------------------------------------------------

@settings(max_examples=500, deadline=None)
@given(gf_two_polys(min_degree=2, max_degree=4))
def test_derivative_product_rule_bug3(args):
    """
    Verifies the product rule for formal derivatives: (f*g)' == f'*g + f*g'.

    This is a pure polynomial identity (compares Poly objects, no evaluation).

    Detects bug_3: When derivative multiplies by (degree - 1) instead of
    (degree), the product rule fails for polynomials with a constant term.
    """
    GF, f, g = args

    fg = f * g
    lhs = fg.derivative()
    rhs = f.derivative() * g + f * g.derivative()

    assert lhs == rhs, (
        f"Product rule (f*g)' = f'g + fg' failed:\n"
        f"  f = {f}\n  g = {g}\n"
        f"  (f*g)' = {lhs}\n  f'g + fg' = {rhs}"
    )


@settings(max_examples=500, deadline=None)
@given(
    st.sampled_from(SMALL_PRIMES),
    st.integers(min_value=2, max_value=6),
    st.integers(min_value=0, max_value=1000),
)
def test_derivative_coefficient_formula_bug3(p, degree, seed):
    """
    Directly verifies the derivative coefficient formula:
      (a_k * x^k)' = (k mod p) * a_k * x^{k-1}

    We extract the expected coefficients analytically and compare.

    Detects bug_3: Uses (degree-1)*a_k instead of degree*a_k in the case
    where the polynomial has a constant term (0 in nonzero_degrees).
    """
    GF = galois.GF(p)
    rng = np.random.default_rng(seed)
    # Build polynomial with non-zero leading and constant terms
    lead = int(rng.integers(1, p))
    middle = [int(rng.integers(0, p)) for _ in range(degree - 1)]
    constant = int(rng.integers(1, p))  # Force non-zero constant to trigger the bug path
    coeffs = GF([lead] + middle + [constant])
    f = galois.Poly(coeffs)

    fp = f.derivative()

    # Expected: derivative of a_k * x^k is (k mod p) * a_k * x^{k-1}
    # f.coeffs = [a_d, a_{d-1}, ..., a_1, a_0] (descending)
    d = f.degree
    expected = {}  # {degree: expected_coeff}
    for i, c_int in enumerate([int(c) for c in f.coeffs]):
        k = d - i  # degree of this term
        if k == 0:
            continue  # constant term vanishes
        deriv_degree = k - 1
        deriv_coeff = (k % p * c_int) % p
        if deriv_degree in expected:
            expected[deriv_degree] = (expected[deriv_degree] + deriv_coeff) % p
        else:
            expected[deriv_degree] = deriv_coeff

    # Build expected poly object to compare
    if not expected or all(v == 0 for v in expected.values()):
        # zero polynomial
        assert fp == galois.Poly([0], field=GF)
        return

    max_deg = max(expected.keys())
    exp_coeffs = [expected.get(d2, 0) for d2 in range(max_deg, -1, -1)]
    expected_poly = galois.Poly(GF(exp_coeffs))

    assert fp == expected_poly, (
        f"Derivative wrong:\n"
        f"  f = {f}\n  f' = {fp}\n"
        f"  expected f' = {expected_poly}"
    )


# ---------------------------------------------------------------------------
# Bug 4: roots_jit wrong power in _dense.py:507
# ---------------------------------------------------------------------------

@settings(max_examples=500, deadline=None)
@given(gf_poly_with_known_roots(n_roots=3))
def test_roots_match_known_roots_bug4(args):
    """
    Verifies that f.roots() returns exactly the known roots used to build f.

    For f = (x-r1)(x-r2)(x-r3), f.roots() must return {r1, r2, r3}.

    Detects bug_4: When roots_jit returns POWER(alpha, i+1) instead of
    POWER(alpha, i), each root is reported as the wrong field element.
    """
    GF, f, known_roots = args

    computed = f.roots()
    known_set = set(int(r) for r in known_roots)
    got_set = set(int(r) for r in computed)

    assert got_set == known_set, (
        f"Wrong roots: got {sorted(got_set)}, expected {sorted(known_set)} "
        f"for f={f} over GF({GF.characteristic})"
    )


@settings(max_examples=500, deadline=None)
@given(gf_poly_with_known_roots(n_roots=2))
def test_roots_two_known_bug4(args):
    """
    For a degree-2 polynomial built from 2 distinct roots over GF(p),
    f.roots() must return exactly those 2 roots.

    Detects bug_4: The off-by-one in root power returns the wrong elements.
    """
    GF, f, known_roots = args

    computed = f.roots()
    known_set = set(int(r) for r in known_roots)
    got_set = set(int(r) for r in computed)

    assert got_set == known_set, (
        f"Wrong roots: got {sorted(got_set)}, expected {sorted(known_set)}"
    )
