# sympy Polynomial Arithmetic Internals — API Documentation

## Overview

`sympy.polys` provides exact polynomial arithmetic over multiple coefficient domains
(integers ZZ, rationals QQ, finite fields GF(p), algebraic numbers, etc.). The
primary user-facing API is the `Poly` class, but the performance-critical internal
routines operate on **dense polynomial lists**.

**Coefficient domains**: ZZ (integers), QQ (rationals), GF(p) (finite fields).

**Polynomial representations**:
- `dup_*` functions: **univariate** dense polynomials, stored as Python lists
  `[a_n, a_{n-1}, ..., a_1, a_0]` (highest degree first).
- `dmp_*` functions: **multivariate** dense polynomials, stored as nested lists.
  For a bivariate polynomial in x,y, each element of the outer list is a
  univariate polynomial in y.

---

## Polynomial GCD

### `Poly.gcd(f, g)`

Computes the monic GCD of two `Poly` objects. Returns a `Poly`.

```python
from sympy import Poly, symbols
x = symbols('x')
f = Poly(x**2 - 1, x, domain='QQ')
g = Poly(x**2 - 3*x + 2, x, domain='QQ')
h = Poly.gcd(f, g)
# h == Poly(x - 1, x, domain='QQ')
```

**Invariants**:
- `h` divides both `f` and `g`
- There exist cofactors `cff, cfg` such that `f == h * cff` and `g == h * cfg`
- For polynomials over a field (QQ), `h` is monic (leading coefficient = 1)

### `dup_qq_heu_gcd(f, g, K)` — Univariate QQ heuristic GCD

Internal function. Returns `(h, cff, cfg)` where:
- `h` is the GCD (monic over QQ)
- `cff` is the cofactor such that `h * cff == f` (using `dup_mul`)
- `cfg` is the cofactor such that `h * cfg == g` (using `dup_mul`)

The algorithm clears denominators to get integer polynomials, computes the
integer GCD via heuristic evaluation, then reconstructs the QQ cofactors.
The normalization step scales `cff` and `cfg` back to QQ using the
denominator clearing factors `cf` and `cg`.

**Critical invariant**: `dup_mul(h, cff, QQ) == f` and `dup_mul(h, cfg, QQ) == g`

**Trigger condition for bugs**: The invariant is violated when `cf != cg`
(the two inputs have different denominator structures after clearing).

```python
from sympy.polys.euclidtools import dup_qq_heu_gcd
from sympy.polys.domains import QQ

f = [QQ(1,2), QQ(1,1), QQ(1,2)]  # (1/2)*x^2 + x + 1/2
g = [QQ(1,3), QQ(1,3)]           # (1/3)*x + 1/3
h, cff, cfg = dup_qq_heu_gcd(f, g, QQ)
# Must hold: dup_mul(h, cff, QQ) == f
# Must hold: dup_mul(h, cfg, QQ) == g
```

### `dmp_qq_heu_gcd(f, g, u, K)` — Multivariate QQ heuristic GCD

Same semantics as `dup_qq_heu_gcd` but for multivariate polynomials.
`u` is the number of variables minus 1 (u=0 univariate, u=1 bivariate, etc.).
Returns `(h, cff, cfg)` with:
- `dmp_mul(h, cff, u, QQ) == f`
- `dmp_mul(h, cfg, u, QQ) == g`

**Critical invariant**: Both cofactor relationships must hold exactly.

```python
from sympy.polys.euclidtools import dmp_qq_heu_gcd, dmp_mul
from sympy.polys.domains import QQ

# Bivariate QQ polynomial (u=1):
# f = (1/2)*x^2 + x + 1/2  (constant in y)
f = [[QQ(1,2)], [QQ(1,1)], [QQ(1,2)]]
g = [[QQ(1,3)], [QQ(1,3)]]
h, cff, cfg = dmp_qq_heu_gcd(f, g, 1, QQ)
# Must hold: dmp_mul(h, cff, 1, QQ) == f
# Must hold: dmp_mul(h, cfg, 1, QQ) == g
```

---

## Polynomial LCM

### `Poly.lcm(f, g)`

Computes the monic LCM of two `Poly` objects. Returns a `Poly`.

**Invariants**:
- Both `f` and `g` divide `h = lcm(f, g)`
- For polynomials over a field (QQ), `h` is monic (leading coefficient = 1)
- `lcm(f, g) * gcd(f, g) == f * g` (up to scaling)

### `dmp_ff_lcm(f, g, u, K)` — Multivariate field LCM

Internal function for multivariate LCM over a field (e.g., QQ).
`u >= 1` (u=0 is univariate, handled by the separate `dup_ff_lcm`).

**Invariant**: For any field K, the LCM must be monic. The leading coefficient
(`dmp_ground_LC(result, u, K)`) must equal `K.one` (= 1 for QQ).

```python
from sympy.polys.euclidtools import dmp_ff_lcm
from sympy.polys.densebasic import dmp_ground_LC
from sympy.polys.domains import QQ

# Bivariate QQ polynomials (u=1):
f = [[QQ(2), QQ(0)], [QQ(1), QQ(0)]]  # 2*x + 1
g = [[QQ(3), QQ(0)], [QQ(1), QQ(0)]]  # 3*x + 1
h = dmp_ff_lcm(f, g, 1, QQ)
# Must hold: dmp_ground_LC(h, 1, QQ) == QQ(1)  (monic)
```

**Note**: Only the multivariate case (u >= 1) uses `dmp_ff_lcm`. The univariate
case (u=0) uses the separate function `dup_ff_lcm`.

---

## Polynomial Multiplication

### `dup_mul(f, g, K)` — Univariate polynomial multiplication

Multiplies two univariate dense polynomials.

**Invariant (evaluation homomorphism)**: For any evaluation point `a`,
`eval(dup_mul(f, g, K), a) == eval(f, a) * eval(g, a)`

This property must hold for polynomials of any degree.

**Implementation detail**: For large polynomials, `dup_mul` uses the Karatsuba
algorithm for efficiency. The threshold is based on the length of the input
polynomials. Polynomials where `max(len(f), len(g)) >= 100` (degree >= 99)
are large enough to use this optimized path.

```python
from sympy.polys.densearith import dup_mul
from sympy.polys.domains import ZZ

# For any f, g, and evaluation point a:
# eval(dup_mul(f, g, ZZ), a) == eval(f, a) * eval(g, a)

def evaluate(poly, a):
    """Evaluate dense polynomial at integer point a."""
    result = 0
    for c in poly:
        result = result * a + c
    return result

f = list(range(1, 102))  # degree-100 polynomial
g = list(range(1, 102))
product = dup_mul(f, g, ZZ)
a = 3
assert evaluate(product, a) == evaluate(f, a) * evaluate(g, a)
```

### Dense polynomial arithmetic helpers

```python
from sympy.polys.densearith import (
    dup_mul,        # univariate multiplication
    dmp_mul,        # multivariate multiplication
    dup_mul_ground, # multiply poly by scalar
    dmp_mul_ground, # multivariate multiply by scalar
    dup_add,        # addition
    dup_sub,        # subtraction
)

from sympy.polys.densebasic import (
    dup_degree,     # degree of univariate poly
    dup_LC,         # leading coefficient
    dup_strip,      # remove leading zeros
    dmp_ground_LC,  # leading coefficient of multivariate poly
)
```

---

## Working with Coefficient Domains

### QQ (rational numbers)

```python
from sympy.polys.domains import QQ

# QQ elements
a = QQ(1, 2)   # 1/2
b = QQ(3, 4)   # 3/4
c = a + b      # 5/4
d = a * b      # 3/8

# QQ polynomial (univariate dense list)
f = [QQ(1, 2), QQ(3, 4), QQ(1, 1)]  # (1/2)*x^2 + (3/4)*x + 1
```

### ZZ (integers)

```python
from sympy.polys.domains import ZZ

f = [ZZ(3), ZZ(-2), ZZ(1)]  # 3*x^2 - 2*x + 1
```

---

## Key Properties to Test

1. **GCD cofactor identity**: `gcd(f, g) * cff == f` and `gcd(f, g) * cfg == g`
   - Both univariate (`dup_qq_heu_gcd`) and multivariate (`dmp_qq_heu_gcd`) versions
   - Must hold for polynomials with asymmetric denominator structures

2. **LCM monicness**: For field domains (QQ), `LC(lcm(f, g)) == 1`
   - The LCM must always be monic for polynomials over a field
   - Applies to multivariate QQ polynomials (`dmp_ff_lcm`)

3. **Multiplication evaluation homomorphism**: `(f * g)(a) == f(a) * g(a)`
   - Must hold for all polynomial sizes, including very large polynomials (degree >= 99)
   - Detectable without knowing the coefficients of the product explicitly

4. **LCM-GCD relationship**: `lcm(f, g) * gcd(f, g) == f * g / lc(f * g)`
   (after monic normalization)

---

## Useful Imports Summary

```python
from sympy.polys.euclidtools import (
    dup_qq_heu_gcd,    # univariate QQ heuristic GCD
    dmp_qq_heu_gcd,    # multivariate QQ heuristic GCD
    dmp_ff_lcm,        # multivariate field LCM
    dmp_gcd,           # generic multivariate GCD dispatcher
    dmp_mul,           # multivariate multiplication (also in densearith)
)
from sympy.polys.densearith import (
    dup_mul,           # univariate multiplication
    dmp_mul,           # multivariate multiplication
    dup_mul_ground,    # univariate scalar multiplication
    dmp_mul_ground,    # multivariate scalar multiplication
)
from sympy.polys.densebasic import (
    dup_degree,        # degree of univariate poly
    dup_LC,            # leading coefficient of univariate poly
    dmp_ground_LC,     # leading coefficient of multivariate poly
    dup_strip,         # strip leading zeros
)
from sympy.polys.domains import ZZ, QQ
from sympy.polys import ring
```
