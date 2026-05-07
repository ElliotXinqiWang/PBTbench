"""
Ground-truth PBT for SYMP-003.

Three bugs in sympy matrix decomposition/inverse routines, all triggered by
complex-valued matrices:

  bug_1: QR decomposition uses hermitian=False in inner product,
         breaking orthogonality for complex matrices.
  bug_2: Cholesky decomposition drops .conjugate() from diagonal element
         computation, producing L where L * L.H != A for complex matrices.
  bug_3: Pseudoinverse (_pinv_full_rank) uses M.T instead of M.H in the
         rows < cols branch, violating Moore-Penrose condition 4.

All bugs are invisible for real matrices because .H == .T and
conjugate(x) == x when there are no imaginary components.

Note: max_examples is kept low (10) because sympy exact symbolic matrix
operations are computationally expensive. The bugs trigger on essentially
all complex matrices (~92% after filtering), so even 10 examples is more
than sufficient for reliable detection. Uses .equals() instead of
simplify() for faster equality checks.
"""

from hypothesis import given, settings, assume
from hypothesis import strategies as st
from sympy import Matrix, I, eye, zeros


def complex_matrix_2x2(a_r, a_i, b_r, b_i, c_r, c_i, d_r, d_i):
    """Build a 2x2 complex Matrix from integer real/imag parts."""
    return Matrix([
        [a_r + a_i * I, b_r + b_i * I],
        [c_r + c_i * I, d_r + d_i * I],
    ])


def mat_equals(A, B):
    """Check A == B by testing (A - B).equals(zeros matrix)."""
    diff = A - B
    return all(e.equals(0) for e in diff)


small_ints = st.integers(min_value=-3, max_value=3)


@given(
    a_r=small_ints, a_i=small_ints,
    b_r=small_ints, b_i=small_ints,
    c_r=small_ints, c_i=small_ints,
    d_r=small_ints, d_i=small_ints,
)
@settings(max_examples=10, deadline=None)
def test_qr_orthogonality_complex(a_r, a_i, b_r, b_i, c_r, c_i, d_r, d_i):
    """QR decomposition: Q.H * Q must equal identity for complex matrices.

    bug_1 changes hermitian=True to hermitian=False in the Gram-Schmidt
    inner product, which makes Q non-unitary for complex input.
    """
    A = complex_matrix_2x2(a_r, a_i, b_r, b_i, c_r, c_i, d_r, d_i)

    # Need at least one imaginary component to trigger the bug
    assume(any(x != 0 for x in [a_i, b_i, c_i, d_i]))

    # Matrix must have full column rank for Q to be square
    assume(A.rank() == 2)

    Q, R = A.QRdecomposition()

    # Q.H * Q must be identity (column orthogonality)
    QHQ = Q.H * Q
    I2 = eye(Q.cols)
    assert mat_equals(QHQ, I2), (
        f"Q.H * Q != I for A={A}; got Q.H*Q = {QHQ}"
    )

    # Q * R must reconstruct A
    assert mat_equals(Q * R, A), (
        f"Q*R != A for A={A}"
    )


@given(
    a_r=st.integers(min_value=1, max_value=4),
    a_i=st.integers(min_value=0, max_value=3),
    b_r=small_ints, b_i=small_ints,
    d_r=st.integers(min_value=1, max_value=4),
    d_i=st.integers(min_value=0, max_value=3),
)
@settings(max_examples=10, deadline=None)
def test_cholesky_reconstruction_complex(a_r, a_i, b_r, b_i, d_r, d_i):
    """Cholesky: L * L.H must reconstruct A for Hermitian positive-definite matrices.

    bug_2 drops .conjugate() from the diagonal element computation in
    _cholesky(), so L[i,i]^2 = M[i,i] - sum(L[i,k]^2) instead of
    M[i,i] - sum(|L[i,k]|^2). For complex L entries, this produces
    wrong diagonal elements, so L * L.H != A.
    """
    # Build a Hermitian positive-definite matrix from a lower triangular L0
    # A = L0 * L0.H is always Hermitian PD
    # Use small entries to keep computation fast
    L0 = Matrix([
        [a_r + a_i * I, 0],
        [b_r + b_i * I, d_r + d_i * I],
    ])

    # L0 must have non-zero diagonal for positive definiteness
    assume(a_r**2 + a_i**2 > 0)
    assume(d_r**2 + d_i**2 > 0)

    # Need at least one off-diagonal imaginary part for bug to trigger
    assume(b_i != 0)

    A = L0 * L0.H

    # Verify A is Hermitian PD (it must be by construction)
    assert A.is_hermitian

    L = A.cholesky()

    # L * L.H must reconstruct A
    assert mat_equals(L * L.H, A), (
        f"L * L.H != A for A={A}"
    )


@given(
    a=st.integers(min_value=1, max_value=3),
    b=st.integers(min_value=-2, max_value=2),
)
@settings(max_examples=10, deadline=None)
def test_pinv_moore_penrose_complex(a, b):
    """Pseudoinverse: Moore-Penrose condition 4 must hold for complex matrices.

    bug_3 changes M.H to M.T in _pinv_full_rank (rows < cols branch).
    This breaks Moore-Penrose condition 4: (A+ * A).H == A+ * A.

    Uses a carefully constructed 1x2 wide complex matrix to exercise the buggy
    branch while keeping computation fast. The matrix always has full row rank
    and M*M.H is always invertible, avoiding expensive fallback paths.
    """
    # Construct a 1x2 complex wide matrix with guaranteed full rank
    A = Matrix([[a + I, b + a * I]])

    A_pinv = A.pinv()

    # Moore-Penrose condition 4: (A+ * A).H == A+ * A
    pinvA = A_pinv * A
    assert mat_equals(pinvA.H, pinvA), (
        f"MP condition 4 violated for A={A}"
    )
