# SYMP-003 Strategy Specification

## Bug Summary

Three bugs in sympy matrix decomposition and inverse routines, all caused by
using ordinary transpose/dot product/identity where the conjugate transpose,
Hermitian inner product, or complex conjugate is required. All three bugs are
invisible for real matrices.

### bug_1: QR decomposition hermitian flag

**Location**: `sympy/matrices/decompositions.py`, `_QRdecomposition_optional`, inner `dot()` function.

**Change**: `u.dot(v, hermitian=True)` changed to `u.dot(v, hermitian=False)`.

**Effect**: Gram-Schmidt orthogonalization uses ordinary dot product instead of
Hermitian inner product. For complex input, Q is not unitary: `Q.H * Q != I`.

### bug_2: Cholesky diagonal conjugate

**Location**: `sympy/matrices/decompositions.py`, `_cholesky`, hermitian branch.

**Change**: `L[i, k]*L[i, k].conjugate()` changed to `L[i, k]*L[i, k]` in the
diagonal element computation (line 271).

**Effect**: The diagonal element L[i,i] is computed as
`sqrt(M[i,i] - sum(L[i,k]^2))` instead of `sqrt(M[i,i] - sum(|L[i,k]|^2))`.
For complex L entries, `z^2 != |z|^2`, so L*L.H != A.

### bug_3: Pseudoinverse conjugate transpose

**Location**: `sympy/matrices/inverse.py`, `_pinv_full_rank`, `else` branch (rows < cols).

**Change**: `M.H.multiply(M.multiply(M.H).inv())` changed to `M.T.multiply(M.multiply(M.T).inv())`.

**Effect**: For wide complex matrices (rows < cols), the pseudoinverse violates
Moore-Penrose condition 4: `(A+ * A).H != A+ * A`.

## Trigger Condition

**All three bugs**: The matrix must contain at least one entry with a non-zero
imaginary component. For real matrices, `.H == .T`, `conjugate(x) == x`, and
`hermitian=True`/`False` give identical results.

### bug_2 specific trigger

The Cholesky bug requires that the off-diagonal entries of L have non-zero
imaginary parts. This happens whenever the Hermitian PD input matrix A has
off-diagonal entries with non-zero imaginary parts (which is the typical case
for complex Hermitian PD matrices).

Minimal example: `A = Matrix([[9, 3*I], [-3*I, 5]])`. The correct Cholesky
factor is `L = [[3, 0], [-I, 2]]`. With the bug, L[1,1] = sqrt(5 - (-I)^2)
= sqrt(6) instead of sqrt(5 - |-I|^2) = sqrt(4) = 2.

## Strategy Design

### Default (real matrices only): 0% trigger rate

If tests only use real-valued matrices, none of the bugs are detectable.

### Targeted: complex matrices with integer components

```python
small_ints = st.integers(min_value=-3, max_value=3)

# For QR (bug_1):
@given(a_r=small_ints, a_i=small_ints, ...)
def test_qr(a_r, a_i, ...):
    A = Matrix([[a_r+a_i*I, ...], [...]])
    assume(any imaginary part != 0)
    assume(A.rank() == 2)

# For Cholesky (bug_2):
# Construct Hermitian PD matrix as A = L0 * L0.H
@given(a_r=pos_ints, b_r=small_ints, b_i=small_ints, d_r=pos_ints)
def test_cholesky(...):
    L0 = Matrix([[a_r, 0], [b_r+b_i*I, d_r]])
    assume(b_i != 0)  # need complex off-diagonal
    A = L0 * L0.H

# For pinv (bug_3):
# Use 2x3 wide complex matrix
```

## Trigger Probability Analysis

| Bug | Strategy | Trigger Rate | Notes |
|-----|----------|-------------|-------|
| bug_1 | Real matrices | 0% | `.H == .T` for real |
| bug_1 | Complex 2x2, [-3,3] | ~92% | After rank + imaginary filters |
| bug_2 | Real matrices | 0% | `conjugate(x) == x` for real |
| bug_2 | Complex Hermitian PD | ~90%+ | Nearly all with complex off-diagonal |
| bug_3 | Real matrices | 0% | `M.H == M.T` for real |
| bug_3 | Complex wide 2x3 | ~92% | After rank + imaginary filters |

## Properties Being Tested

1. **QR orthogonality**: `Q.H * Q == I` (unitarity of Q)
2. **Cholesky reconstruction**: `L * L.H == A`
3. **Moore-Penrose condition 4**: `(A+ * A).H == A+ * A`

## Boundary Values

### Minimal triggers

- **bug_1**: `Matrix([[I, 0], [0, 1]])` — simplest complex matrix
- **bug_2**: `Matrix([[9, 3*I], [-3*I, 5]])` — simplest complex Hermitian PD
- **bug_3**: `Matrix([[I, 0, 0], [0, 1, 0]])` — wide complex matrix

### Why real matrices don't trigger

For real matrix A:
- `A.H == A.T` (conjugate of real number is itself)
- `u.dot(v, hermitian=True) == u.dot(v, hermitian=False)` (conjugate of real is real)
- `z * conjugate(z) == z * z == z^2` (for real z)
- All formulas produce identical results regardless of conjugation
