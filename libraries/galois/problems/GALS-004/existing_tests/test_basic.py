"""Basic tests for galois."""
import numpy as np
import galois


def test_flfsr_creation():
    poly = galois.primitive_poly(7, 4).reverse()
    lfsr = galois.FLFSR(poly)
    assert lfsr.order == 4


def test_glfsr_creation():
    poly = galois.primitive_poly(7, 4).reverse()
    lfsr = galois.GLFSR(poly)
    assert lfsr.order == 4


def test_flfsr_step():
    poly = galois.primitive_poly(2, 4).reverse()
    lfsr = galois.FLFSR(poly)
    out = lfsr.step(10)
    assert out.size == 10


def test_to_galois_lfsr_returns_glfsr():
    """to_galois_lfsr() returns a GLFSR (type check, not sequence check)."""
    poly = galois.primitive_poly(7, 4).reverse()
    flfsr = galois.FLFSR(poly)
    glfsr = flfsr.to_galois_lfsr()
    assert isinstance(glfsr, galois.GLFSR)
    assert glfsr.order == flfsr.order


def test_same_feedback_poly():
    """Converted GLFSR has the same feedback polynomial."""
    poly = galois.primitive_poly(7, 4).reverse()
    flfsr = galois.FLFSR(poly)
    glfsr = flfsr.to_galois_lfsr()
    assert glfsr.feedback_poly == flfsr.feedback_poly
