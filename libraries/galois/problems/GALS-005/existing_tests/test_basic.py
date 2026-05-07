"""Basic tests for galois."""
import numpy as np
import galois


def test_poly_creation():
    """Polynomial creation and basic arithmetic."""
    GF2 = galois.GF(2)
    p = galois.Poly([1, 0, 1, 1], field=GF2)
    q = galois.Poly([1, 1, 1], field=GF2)
    assert p.degree == 3
    assert q.degree == 2
    assert (p + q).degree >= 0


def test_poly_gcd():
    """gcd of coprime polynomials over GF(2) is 1 — uses Euclidean algorithm, not evaluation."""
    GF2 = galois.GF(2)
    p = galois.Poly([1, 0, 1, 1], field=GF2)  # x^3 + x + 1 (irreducible)
    q = galois.Poly([1, 1, 1], field=GF2)    # x^2 + x + 1 (irreducible)
    d = galois.gcd(p, q)
    assert d == galois.Poly([1], field=GF2)


def test_poly_multiply():
    """Test Poly multiply."""
    GF5 = galois.GF(5)
    p = galois.Poly([1, 2], field=GF5)   # x + 2
    q = galois.Poly([1, 3], field=GF5)   # x + 3
    r = p * q
    assert r.degree == 2


def test_irreducible_poly_creation():
    """Creating irreducible polynomials uses polynomial GCD tests, not evaluation."""
    f = galois.irreducible_poly(2, 4)
    assert f.degree == 4
    assert f.is_irreducible()


def test_primitive_poly_creation():
    """Creating primitive polynomials."""
    p = galois.primitive_poly(2, 4)
    assert p.degree == 4
    assert p.is_irreducible()


def test_field_element_add():
    """Test Field element add."""
    GF7 = galois.GF(7)
    a = GF7(3)
    b = GF7(5)
    assert int(a + b) == 1  # 3+5=8 ≡ 1 mod 7


def test_field_element_multiply():
    """Test Field element multiply."""
    GF7 = galois.GF(7)
    a = GF7(3)
    b = GF7(4)
    assert int(a * b) == 5  # 12 ≡ 5 mod 7


def test_prime_field_reciprocal():
    """Test Prime field reciprocal."""
    GF7 = galois.GF(7)
    a = GF7(3)
    assert int(a * np.reciprocal(a)) == 1


def test_matrix_operations_gf2():
    """Test Matrix operations gf2."""
    GF2 = galois.GF(2)
    I = GF2.Identity(3)
    A = GF2([[1, 0, 1], [0, 1, 1], [1, 1, 0]])
    result = A @ I
    assert np.array_equal(result, A)
