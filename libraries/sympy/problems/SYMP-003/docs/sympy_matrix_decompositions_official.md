# SymPy Matrix Decompositions — Official API Reference

## Overview

SymPy provides exact symbolic matrix decompositions including QR decomposition,
Cholesky decomposition, and Moore-Penrose pseudoinverse computation.
All operations work with both real and complex matrices using exact arithmetic
(no floating point).

For complex matrices, the *conjugate transpose* (Hermitian adjoint) `A.H` plays
the role that the ordinary transpose `A.T` plays for real matrices. Similarly,
`conjugate(x)` must be used instead of just `x` when computing inner products
and norms involving complex entries.

---

## QR Decomposition

### `Matrix.QRdecomposition()`

Decomposes matrix `A` into `Q * R` where:
- `Q` is a column-orthogonal (unitary) matrix: `Q.H * Q = I`
- `R` is upper triangular

For a full-rank square matrix, `Q` is fully unitary: both `Q.H * Q = I` and
`Q * Q.H = I` hold.

**Key invariant**: For any matrix `A`, if `Q, R = A.QRdecomposition()`, then:
1. `Q * R == A` (reconstruction)
2. `Q.H * Q == I` (column orthogonality / unitarity)

**Complex matrices**: The Gram-Schmidt process internally uses the *Hermitian
inner product* `<u, v> = u.H * v = sum(conjugate(u_i) * v_i)`. This is essential
for producing unitary Q matrices when the input contains complex entries.
Using the ordinary dot product `u.T * v` instead would break orthogonality.

### Example

```python
>>> from sympy import Matrix, I, eye, simplify
>>> A = Matrix([[1 + I, 2], [3, 4 - I]])
>>> Q, R = A.QRdecomposition()
>>> simplify(Q.H * Q) == eye(2)
True
>>> simplify(Q * R - A).is_zero_matrix
True
```

---

## Cholesky Decomposition

### `Matrix.cholesky(hermitian=True)`

Decomposes a Hermitian positive-definite matrix `A` into `L * L.H` where:
- `L` is a lower triangular matrix

For real symmetric PD matrices, `L * L.T == A`.

**Key invariant**: `L * L.H == A` (exact reconstruction).

The computation uses `conjugate()` when computing the diagonal elements:
```
L[i, i] = sqrt(A[i, i] - sum(L[i, k] * conjugate(L[i, k]) for k in range(i)))
         = sqrt(A[i, i] - sum(|L[i, k]|^2 for k in range(i)))
```

**Complex matrices**: For complex entries, `z * conjugate(z) = |z|^2` (always
real and non-negative), while `z * z = z^2` can be complex. Using `z * z` instead
of `z * conjugate(z)` produces wrong diagonal elements in L.

### Example

```python
>>> from sympy import Matrix, I, simplify
>>> A = Matrix([[9, 3*I], [-3*I, 5]])
>>> L = A.cholesky()
>>> L
Matrix([
[ 3, 0],
[-I, 2]])
>>> L * L.H == A
True
```

---

## Moore-Penrose Pseudoinverse

### `Matrix.pinv(method='RD')`

Computes the Moore-Penrose pseudoinverse `A+` of matrix `A`.

**Methods**:
- `'RD'` (default): Rank Decomposition — decomposes `A = B * C` (full-rank factors),
  then computes `A+ = C+ * B+` where each factor's pseudoinverse uses
  `M.H * (M * M.H)^{-1}` (for wide factor) or `(M.H * M)^{-1} * M.H` (for tall factor).
- `'ED'`: Eigenvalue Decomposition — uses diagonalization of `A.H * A` or `A * A.H`.

**Moore-Penrose conditions**: The unique pseudoinverse `A+` satisfies all four:
1. `A * A+ * A = A`
2. `A+ * A * A+ = A+`
3. `(A * A+).H = A * A+` (Hermiticity)
4. `(A+ * A).H = A+ * A` (Hermiticity)

**Complex matrices**: The pseudoinverse formulas require the *conjugate transpose*
`M.H`. Using the ordinary transpose `M.T` would produce a matrix satisfying
conditions 1-3 but violating condition 4 for complex input.

### Example

```python
>>> from sympy import Matrix, simplify
>>> A = Matrix([[1, 2, 3], [4, 5, 6]])
>>> p = A.pinv()
>>> simplify(A * p * A - A).is_zero_matrix  # Condition 1
True
>>> simplify((p * A).H - p * A).is_zero_matrix  # Condition 4
True
```

---

## Complex Number Support

SymPy uses `I` for the imaginary unit. Key operations for complex matrices:

| Operation | Syntax | Description |
|-----------|--------|-------------|
| Conjugate transpose | `A.H` | Transpose + complex conjugate |
| Ordinary transpose | `A.T` | Transpose only (no conjugate) |
| Hermitian inner product | `u.dot(v, hermitian=True)` | `sum(conj(u_i) * v_i)` |
| Ordinary dot product | `u.dot(v, hermitian=False)` | `sum(u_i * v_i)` |

**Critical distinction**: For real matrices, `A.H == A.T`. For complex matrices,
they differ. All standard linear algebra identities (orthogonality, unitarity,
Hermiticity of projectors) require `A.H`, not `A.T`.

---

## Properties for Testing

When testing matrix decomposition correctness, the following properties are
particularly useful:

1. **QR reconstruction**: `Q * R == A`
2. **QR orthogonality**: `Q.H * Q == I` (for full column rank)
3. **Cholesky reconstruction**: `L * L.H == A` (for Hermitian PD matrices)
4. **Pseudoinverse Moore-Penrose conditions** (all four)
5. **Real invariance**: For real matrices, `.H == .T` and `conjugate(x) == x`,
   so bugs involving conjugation are invisible

### Generating Test Matrices

For property-based testing, generate matrices with:
- Integer or small rational entries (exact arithmetic)
- Complex entries using `a + b*I` where `a, b` are small integers
- Ensure full rank when needed (check `A.rank()`)
- Use `simplify()` for comparison since sympy may not auto-simplify
