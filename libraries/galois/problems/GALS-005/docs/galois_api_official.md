# galois Polynomial Arithmetic API

## galois.lagrange_poly(x, y)

Computes the Lagrange interpolating polynomial `L(x)` such that `L(x_i) = y_i`.

**Arguments:**
- `x`: An array of x_i values for coordinates (x_i, y_i). Must be 1-D with no duplicate entries.
- `y`: An array of y_i values for coordinates (x_i, y_i). Must be 1-D, same size as x.

**Returns:** `Poly` — The Lagrange polynomial L(x).

**Key guarantee:** The returned polynomial satisfies `L(x_i) == y_i` for all i.

**Mathematical definition:**

The Lagrange interpolating polynomial is defined as:

    L(x) = sum_{j=0}^{k-1} y_j * ell_j(x)

where the basis polynomials are:

    ell_j(x) = prod_{m != j} (x - x_m) / (x_j - x_m)

It is the unique polynomial of minimal degree (at most k-1) that passes through all k points.

**Examples:**

```python
import galois
import numpy as np

GF = galois.GF(7)
x = GF([0, 1, 2, 3])
y = GF([1, 3, 2, 6])

L = galois.lagrange_poly(x, y)
# Verify interpolation property
assert np.array_equal(L(x), y)
```

## galois.Poly evaluation (Horner's method)

A polynomial `f(x)` over a Galois field can be evaluated at field elements using `f(value)`.

**Key guarantee:** For a polynomial `f(x) = a_d * x^d + ... + a_1 * x + a_0`,
evaluation at any field element `v` should satisfy:

    f(v) == sum(a_i * v^i for i in range(d+1))  (computed as field arithmetic)

Evaluation uses Horner's method internally:

    f(v) = a_0 + v*(a_1 + v*(a_2 + ... + v*a_d))

Which processes coefficients from highest to lowest degree:

    y = a_d
    y = a_{d-1} + y * v
    y = a_{d-2} + y * v
    ...
    y = a_0 + y * v

**Examples:**

```python
import galois
import numpy as np

GF = galois.GF(7)
f = galois.Poly([3, 0, 1, 4], field=GF)  # 3x^3 + x + 4
v = GF(5)

# Direct evaluation
result = f(v)

# Verify by manual Horner
expected = GF(3)*v**3 + GF(0)*v**2 + GF(1)*v + GF(4)
assert result == expected
```

## galois.Poly.derivative(k=1)

Computes the k-th formal derivative of the polynomial f(x).

**Arguments:**
- `k`: The number of derivatives to compute. Default is 1.

**Returns:** `Poly` — The k-th formal derivative.

**Mathematical definition:**

For `f(x) = a_d * x^d + a_{d-1} * x^{d-1} + ... + a_1 * x + a_0`, the first derivative is:

    f'(x) = d*a_d * x^{d-1} + (d-1)*a_{d-1} * x^{d-2} + ... + 2*a_2 * x + a_1

where the integer multiplier `i` represents scalar multiplication (i.e., adding a_i to itself i times),
not finite field multiplication. In GF(p), the scalar multiplier is taken mod p.

**Key properties:**

1. Linearity: `(a*f + b*g)' == a*f' + b*g'`
2. Product rule: `(f * g)' == f'*g + f*g'`
3. Power rule: `(x^n)' == n * x^{n-1}` (as scalar multiplication)
4. In GF(p): `f'` has degree at most `d-1`; taking p derivatives gives 0

**Examples:**

```python
import galois

GF = galois.GF(7)
f = galois.Poly([3, 2, 1, 4], field=GF)  # 3x^3 + 2x^2 + x + 4
fp = f.derivative()
# Expected: 9x^2 + 4x + 1 = 2x^2 + 4x + 1 (mod 7)
assert fp == galois.Poly([2, 4, 1], field=GF)
```

## galois.Poly.roots(multiplicity=False)

Calculates the roots r of the polynomial f(x) such that f(r) = 0.

**Arguments:**
- `multiplicity`: If True, also return multiplicities of each root. Default is False.

**Returns:**
- An array of roots (field elements where f evaluates to 0), sorted in increasing order.
- If `multiplicity=True`, also returns an array of multiplicities.

**Key guarantee:** Every returned element `r` must satisfy `f(r) == 0`.

**Mathematical properties:**

1. **Root identity:** For each returned root r, f(r) == 0 must hold.
2. **Exhaustiveness:** All roots in the field are found.
3. **Degree bound:** A degree-d polynomial has at most d roots in any field.
4. **Factorization:** `f(x) = (x - r_1)^m_1 * (x - r_2)^m_2 * ... * (x - r_k)^m_k`

Implementation uses **Chien's search** which tests all non-zero field elements using
the recurrence relation on `f(alpha^i)`.

**Examples:**

```python
import galois
import numpy as np

GF = galois.GF(7)
# Construct polynomial from known roots
f = galois.Poly.Roots([1, 3, 5], field=GF)  # (x-1)(x-3)(x-5)
roots = f.roots()
assert set(int(r) for r in roots) == {1, 3, 5}
# Verify each root evaluates to 0
assert all(f(r) == GF(0) for r in roots)

# Example with multiplicities
g = galois.Poly.Roots([2, 2, 4], multiplicities=[2, 1, 1], field=GF)
# Wait, Roots takes separate roots and multiplicities
g2 = galois.Poly.Roots([2, 4], multiplicities=[2, 1], field=GF)
roots2, mults2 = g2.roots(multiplicity=True)
```

## galois.Poly — Polynomial Arithmetic Properties

### Division consistency

For polynomials a(x) and b(x) (b non-zero), the quotient q and remainder r satisfy:

    a == q * b + r   (polynomial identity)
    r.degree < b.degree

Both `a // b` (quotient) and `a % b` (remainder) must satisfy this identity:

```python
GF = galois.GF(7)
a = galois.Poly.Random(7, field=GF)
b = galois.Poly.Random(3, field=GF)
# Ensure monic b for cleaner test
q = a // b
r = a % b
assert a == q * b + r
assert r.degree < b.degree or r == galois.Poly([0], field=GF)
```

### GCD and LCM properties

For polynomials a(x) and b(x) over GF(q):

- `gcd(a, b)` divides both a and b
- `lcm(a, b)` is divisible by both a and b
- `gcd(a, b) * lcm(a, b) == a * b / leading_coeff` (up to scalar factor)
- `gcd(a, b)` is monic (leading coefficient is 1)

```python
import galois

GF = galois.GF(5)
a = galois.Poly.Random(4, field=GF)
b = galois.Poly.Random(3, field=GF)
d = galois.gcd(a, b)
# GCD divides both
assert a % d == galois.Poly([0], field=GF)
assert b % d == galois.Poly([0], field=GF)
```

## Field Element Arithmetic in GF(q)

### GF(p) — Prime field

Elements are integers mod p. Field operations:
- Addition: `(a + b) % p`
- Multiplication: `(a * b) % p`
- Multiplicative inverse: `pow(a, p-2, p)` for `a != 0`

### GF(p^m) — Extension field

Elements can be represented as polynomials in GF(p)[x] of degree < m, modulo an irreducible polynomial.
The field order is q = p^m.

**Primitive element:** A generator of the multiplicative group GF(q)^×.
Every non-zero element can be written as alpha^k for some k.

**Frobenius endomorphism:** For any element a in GF(p^m):
    a^(p^m) == a
    a^p is also in GF(p^m) (the Frobenius automorphism)
