"""Basic tests for galois."""
import galois


def test_poly_creation():
    GF2 = galois.GF(2)
    f = galois.Poly([1, 1, 1], field=GF2)
    assert f.degree == 2


def test_irreducible_poly_has_one_factor():
    """Irreducible polynomial has exactly one factor (itself) — no distinct-degree loop."""
    GF2 = galois.GF(2)
    f = galois.Poly([1, 1, 1], field=GF2)  # x^2+x+1 is irreducible
    factors, mults = f.factors()
    assert len(factors) == 1
    assert mults == [1]


def test_poly_is_irreducible():
    GF2 = galois.GF(2)
    f = galois.Poly([1, 1, 1], field=GF2)
    assert f.is_irreducible()


def test_linear_poly_factor():
    """Linear polynomial is irreducible — distinct_degree loop runs once and terminates."""
    GF2 = galois.GF(2)
    f = galois.Poly([1, 1], field=GF2)  # x+1
    factors, mults = f.factors()
    assert len(factors) == 1
    assert factors[0] == f


def test_same_degree_squared():
    """(x+1)^2 over GF(2) — factors of same degree only, no mixed-degree iteration."""
    GF2 = galois.GF(2)
    f = galois.Poly([1, 0, 1], field=GF2)  # x^2+1 = (x+1)^2
    factors, mults = f.factors()
    assert len(factors) == 1
    assert mults == [2]
