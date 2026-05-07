"""Ground-truth PBT for GALS-004.

bug_1: FLFSR.to_galois_lfsr() omits state reversal → divergent output sequences.
bug_2: GLFSR.Taps() uses wrong subscript order for non-GF(2) fields → wrong polynomial reconstruction.
"""

import numpy as np
import galois
from hypothesis import given, settings, assume
from hypothesis import strategies as st


@settings(max_examples=300, deadline=None)
@given(
    degree=st.sampled_from([2, 3, 4]),
    pre_steps=st.integers(min_value=1, max_value=20),
    verify_steps=st.integers(min_value=5, max_value=20),
)
def test_to_galois_lfsr_equivalence_gf2(degree, pre_steps, verify_steps):
    """After conversion, GLFSR must produce the same sequence as the original FLFSR."""
    poly = galois.primitive_poly(2, degree).reverse()
    fibonacci_lfsr = galois.FLFSR(poly)

    # Advance to a non-trivial state
    _ = fibonacci_lfsr.step(pre_steps)

    # Convert to Galois LFSR
    galois_lfsr = fibonacci_lfsr.to_galois_lfsr()

    # Both should produce the same next N outputs
    fib_out = fibonacci_lfsr.step(verify_steps)
    gal_out = galois_lfsr.step(verify_steps)

    assert np.array_equal(fib_out, gal_out), (
        f"FLFSR and GLFSR sequences diverge after conversion:\n"
        f"  FLFSR: {fib_out.tolist()}\n"
        f"  GLFSR: {gal_out.tolist()}\n"
        f"  degree={degree}, pre_steps={pre_steps}"
    )


@settings(max_examples=200, deadline=None)
@given(
    pre_steps=st.integers(min_value=1, max_value=15),
    verify_steps=st.integers(min_value=3, max_value=15),
    sv=st.integers(min_value=1, max_value=6),
)
def test_to_galois_lfsr_equivalence_gf7(pre_steps, verify_steps, sv):
    """FLFSR to GLFSR conversion must work over GF(7)."""
    poly = galois.primitive_poly(7, 2).reverse()
    GF7 = galois.GF(7)
    state = GF7([sv % 7, (sv * 3 + 1) % 7])
    fibonacci_lfsr = galois.FLFSR(poly, state=state)

    _ = fibonacci_lfsr.step(pre_steps)
    galois_lfsr = fibonacci_lfsr.to_galois_lfsr()

    fib_out = fibonacci_lfsr.step(verify_steps)
    gal_out = galois_lfsr.step(verify_steps)

    assert np.array_equal(fib_out, gal_out), (
        f"FLFSR/GLFSR mismatch over GF(7): fib={fib_out.tolist()}, gal={gal_out.tolist()}"
    )


@settings(max_examples=200, deadline=None)
@given(
    degree=st.sampled_from([2, 3, 4]),
    verify_steps=st.integers(min_value=5, max_value=25),
)
def test_roundtrip_sequence_identity(degree, verify_steps):
    """FLFSR and converted GLFSR produce same output even from different starting points."""
    poly = galois.primitive_poly(2, degree).reverse()

    # Step the FLFSR 3 times to get a non-trivial state
    flfsr_ref = galois.FLFSR(poly)
    _ = flfsr_ref.step(3)

    flfsr_check = galois.FLFSR(poly)
    _ = flfsr_check.step(3)
    glfsr_check = flfsr_check.to_galois_lfsr()

    ref_out = flfsr_ref.step(verify_steps)
    gal_out = glfsr_check.step(verify_steps)

    assert np.array_equal(ref_out, gal_out), (
        f"Sequences diverge: degree={degree}\n"
        f"  FLFSR: {ref_out.tolist()}\n"
        f"  GLFSR: {gal_out.tolist()}"
    )


# ---------------------------------------------------------------------------
# bug_2: GLFSR.Taps() wrong subscript order for non-GF(2) fields
# ---------------------------------------------------------------------------

@settings(max_examples=200, deadline=None)
@given(
    q=st.sampled_from([3, 5, 7]),
    degree=st.sampled_from([2, 3, 4]),
)
def test_glfsr_taps_roundtrip_characteristic_poly(q, degree):
    """GLFSR.Taps() must reconstruct the original characteristic polynomial (non-GF(2))."""
    char_poly = galois.primitive_poly(q, degree)
    feedback_poly = char_poly.reverse()
    glfsr = galois.GLFSR(feedback_poly)

    glfsr2 = galois.GLFSR.Taps(glfsr.taps)
    assert glfsr2.characteristic_poly == char_poly, (
        f"Taps round-trip changed characteristic_poly over GF({q}):\n"
        f"  expected: {char_poly}\n"
        f"  got:      {glfsr2.characteristic_poly}"
    )


@settings(max_examples=200, deadline=None)
@given(
    q=st.sampled_from([3, 5, 7]),
    degree=st.sampled_from([2, 3]),
    steps=st.integers(min_value=5, max_value=20),
)
def test_glfsr_taps_roundtrip_output_sequence(q, degree, steps):
    """GLFSR reconstructed via Taps() must produce the same output sequence (non-GF(2))."""
    GF = galois.GF(q)
    char_poly = galois.primitive_poly(q, degree)
    feedback_poly = char_poly.reverse()
    state = GF([i % q + 1 for i in range(degree)])

    glfsr_orig = galois.GLFSR(feedback_poly, state=state)
    glfsr_taps = galois.GLFSR.Taps(glfsr_orig.taps, state=state)

    glfsr_ref = galois.GLFSR(feedback_poly, state=state)
    out_ref = glfsr_ref.step(steps)
    out_taps = glfsr_taps.step(steps)

    assert np.array_equal(out_ref, out_taps), (
        f"Taps round-trip output mismatch over GF({q}) degree={degree}:\n"
        f"  original: {out_ref.tolist()}\n"
        f"  via Taps: {out_taps.tolist()}"
    )
