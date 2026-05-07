"""Basic tests for sympy."""

from sympy import Matrix, eye, Rational, sqrt, simplify


# --- QR decomposition --------------------------------------------------------

def test_qr_3x3_integer():
    A = Matrix([[12, -51, 4], [6, 167, -68], [-4, 24, -41]])
    Q, R = A.QRdecomposition()
    assert Q * R == A
    assert simplify(Q.H * Q) == eye(3)


def test_qr_2x2_rational():
    A = Matrix([[Rational(1, 2), Rational(3, 4)],
                [Rational(5, 6), Rational(7, 8)]])
    Q, R = A.QRdecomposition()
    assert simplify(Q * R - A).is_zero_matrix
    assert simplify(Q.H * Q) == eye(2)


def test_qr_rank_deficient():
    A = Matrix([[1, 2, 3], [2, 4, 6], [1, 1, 1]])
    Q, R = A.QRdecomposition()
    assert simplify(Q * R - A).is_zero_matrix


def test_qr_identity():
    A = eye(3)
    Q, R = A.QRdecomposition()
    assert Q == eye(3)
    assert R == eye(3)


# --- Cholesky decomposition --------------------------------------------------

def test_cholesky_3x3_real():
    A = Matrix([[25, 15, -5], [15, 18, 0], [-5, 0, 11]])
    L = A.cholesky()
    assert L * L.T == A


def test_cholesky_2x2_real():
    A = Matrix([[4, 2], [2, 5]])
    L = A.cholesky()
    assert L * L.T == A
    # L must be lower triangular
    assert L[0, 1] == 0


def test_cholesky_identity():
    A = eye(3)
    L = A.cholesky()
    assert L == eye(3)


def test_cholesky_diagonal():
    A = Matrix([[9, 0], [0, 16]])
    L = A.cholesky()
    assert L == Matrix([[3, 0], [0, 4]])
    assert L * L.T == A


# --- Pseudoinverse ------------------------------------------------------------

def test_pinv_square_invertible():
    A = Matrix([[1, 2], [3, 4]])
    p = A.pinv()
    # For invertible matrices, pinv == inv
    assert simplify(p - A.inv()).is_zero_matrix


def test_pinv_wide_real():
    A = Matrix([[1, 2, 3], [4, 5, 6]])
    p = A.pinv()
    # Moore-Penrose condition 1
    assert simplify(A * p * A - A).is_zero_matrix
    # Moore-Penrose condition 4
    assert simplify((p * A).H - p * A).is_zero_matrix


def test_pinv_tall_real():
    A = Matrix([[1, 2], [3, 4], [5, 6]])
    p = A.pinv()
    assert simplify(A * p * A - A).is_zero_matrix


def test_pinv_zero_matrix():
    A = Matrix.zeros(2, 3)
    p = A.pinv()
    assert p == A.H


def test_pinv_identity():
    A = eye(3)
    p = A.pinv()
    assert p == eye(3)


def test_pinv_moore_penrose_all_conditions():
    """Verify all 4 Moore-Penrose conditions for a real wide matrix."""
    A = Matrix([[1, 0, 1], [0, 1, 1]])
    p = A.pinv()
    # C1: A * p * A = A
    assert simplify(A * p * A - A).is_zero_matrix
    # C2: p * A * p = p
    assert simplify(p * A * p - p).is_zero_matrix
    # C3: (A * p)^H = A * p
    assert simplify((A * p).H - A * p).is_zero_matrix
    # C4: (p * A)^H = p * A
    assert simplify((p * A).H - p * A).is_zero_matrix
