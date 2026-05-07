# mpmath Arbitrary-Precision Arithmetic — Official API Reference

## Overview

**mpmath** is a Python library for arbitrary-precision floating-point arithmetic.
All computations are performed using a configurable number of decimal places (`mp.dps`)
or binary digits (`mp.prec`).  The default is `mp.dps = 15` (approximately IEEE 754
double precision).

```python
from mpmath import mp, mpf, mpc
mp.dps = 50  # set working precision to 50 decimal places
```

Numbers are stored as `mpf` (real) or `mpc` (complex) objects.  Internally an `mpf`
is represented as a 4-tuple `(sign, man, exp, bc)` where the value equals
`(-1)^sign * man * 2^exp` and `bc = bitcount(man)`.

---

## Setting Precision

```python
mp.dps = 50        # 50 decimal places (~166 bits)
mp.prec = 200      # 200 binary digits
x = mpf('1.5')     # construct from string (exact)
y = mpf(1.5)       # construct from Python float (may lose bits)
```

`mp.prec` and `mp.dps` are linked: `mp.prec ≈ mp.dps * 3.32193`.

---

## Elementary Functions

All elementary functions accept `mpf` or plain Python `int`/`float` arguments and
return `mpf` (or `mpc` for complex results).  Results are accurate to the working
precision `mp.prec`.

### Exponential and Logarithm

```python
from mpmath import exp, log, ln

exp(x)          # e^x
log(x)          # natural logarithm  (raises ValueError for x <= 0)
log(x, b)       # base-b logarithm
```

**Key property**: `log(exp(x)) == x` and `exp(log(x)) == x` for positive `x`.

**Near-1 behavior**: For `x` close to 1, `log(x) ≈ x - 1`.  More precisely:
```
log(1 + eps) = eps - eps^2/2 + eps^3/3 - ...
```
This Taylor series converges rapidly for small `eps`, and mpmath uses it internally
(via `log_taylor_cached`) when the working precision is below ~2500 bits.  For higher
precision, an AGM-based algorithm is used.

### Trigonometric and Inverse-Trigonometric

```python
from mpmath import sin, cos, tan, atan, atan2, pi

sin(x), cos(x), tan(x)   # standard trig
atan(x)                   # arctangent, result in (-pi/2, pi/2)
atan2(y, x)               # two-argument arctangent, result in (-pi, pi]
```

**Key identity**: For any `x > 0`:
```
atan(x) + atan(1/x) == pi/2
```

**Key identity**: For any `x`:
```
sin(x)**2 + cos(x)**2 == 1
```

**Implementation note**: mpmath uses a Taylor-series path for atan at moderate
precision, and a Newton-Raphson iteration (`atan_newton`) at very high precision
(working precision `wp >= 3000` bits, approximately `mp.dps >= 900`).

### Hyperbolic Functions

```python
from mpmath import sinh, cosh, tanh

sinh(x)   # (e^x - e^{-x}) / 2
cosh(x)   # (e^x + e^{-x}) / 2
tanh(x)   # sinh(x) / cosh(x)
```

**Key identity**: `cosh(x)**2 - sinh(x)**2 == 1` for all `x`.

**Key identity**: `sinh(x) / x -> 1` as `x -> 0`.  More precisely, for small `x`:
```
sinh(x) = x + x^3/6 + x^5/120 + x^7/5040 + ...
```

The mpmath implementation increases working precision when `|x|` is small (to
compensate for catastrophic cancellation in `e^x - e^{-x}`).  This ensures that
sinh is accurate even for `|x|` as small as `10^{-300}`.

### Square Root

```python
from mpmath import sqrt

sqrt(x)      # square root; raises for x < 0 (returns mpc if x < 0 in mpc context)
```

**Key invariant**: `sqrt(x)**2 == x` for positive `x` (to working precision).

**Key invariant**: `sqrt(x * y) == sqrt(x) * sqrt(y)` for positive `x`, `y`.

### Rounding Functions

```python
from mpmath import floor, ceil, nint, frac

floor(x)    # largest integer <= x
ceil(x)     # smallest integer >= x
nint(x)     # nearest integer (round half to even)
frac(x)     # fractional part: x - floor(x)
```

**Key invariants**:
- `ceil(x) == -floor(-x)` for all `x`
- `floor(x) <= x < floor(x) + 1` for all `x`
- `ceil(x) - 1 < x <= ceil(x)` for all `x`
- For any non-integer `x`: `ceil(x) == floor(x) + 1`
- For integer `n`: `ceil(n) == floor(n) == n`
- For `0 < x < 1`: `floor(x) == 0` and `ceil(x) == 1`
- For `-1 < x < 0`: `floor(x) == -1` and `ceil(x) == 0`

---

## Power Functions

```python
from mpmath import power, root, cbrt

x**y          # standard power (uses mpf arithmetic if x or y is mpf)
power(x, y)   # same as x**y but always uses mpmath
root(x, n)    # n-th root of x (= x**(1/n))
cbrt(x)       # cube root (= x**(1/3))
```

**Key invariant**: `root(x, n)**n == x` for positive `x` and integer `n >= 1`.

---

## Constants

```python
from mpmath import pi, e, phi, euler, catalan

pi       # 3.14159...
e        # 2.71828...
phi      # golden ratio 1.61803...
```

All constants are computed to the current working precision `mp.dps`.

---

## Context Manager for Temporary Precision

```python
from mpmath import workdps, workprec

with workdps(100):
    result = sin(mpf('0.5'))  # computed at 100 dps

with workprec(1000):
    result = exp(mpf('1'))    # computed at 1000 bits
```

---

## Precision and Accuracy

The mpmath documentation guarantees that all elementary functions are accurate
to within 1 ULP (unit in the last place) of the working precision `mp.prec`.

A result `r` is within 1 ULP of the true value `v` if:
```
|r - v| <= 2^(floor(log2|v|) - mp.prec + 1)
```

For most functions, mpmath achieves results within a few ULPs (typically 1-3).

---

## Numerical Comparison

Due to floating-point rounding, exact equality checks between `mpf` objects should
use a tolerance:

```python
def nearly_equal(a, b, rel_tol=None, abs_tol=None):
    if rel_tol is None:
        rel_tol = mpf(2)**(-(mp.prec - 4))  # a few ULPs
    return abs(a - b) <= rel_tol * max(abs(a), abs(b))
```

For integer-valued functions like `ceil` and `floor`, exact equality is appropriate:
```python
assert ceil(x) == 1   # exact, since the result should be an integer
```

---

## Example: Property-Based Testing with mpmath

The following pattern is typical for testing mpmath functions:

```python
from mpmath import mp, mpf, sin, cos, sqrt, ceil, log, atan, pi

# Test an algebraic identity at moderate precision
mp.dps = 50
x = mpf('1.23456789')
assert abs(sin(x)**2 + cos(x)**2 - 1) < mpf(2)**(-mp.prec + 4)

# Test a rounding identity
x = mpf('0.7')
assert ceil(x) == 1

# Test sqrt roundtrip
n = 42
assert abs(sqrt(n)**2 - n) < n * mpf(2)**(-mp.prec + 4)

# Test log near 1
k = 30
mp.dps = 100
eps = mpf(1) / mpf(2)**k
assert abs(log(1 + eps) - eps) < eps**2  # log(1+eps) ≈ eps for small eps

# Test atan identity at high precision
mp.dps = 1000
x = mpf('2.5')
assert abs(atan(x) + atan(1/x) - pi/2) < mpf(2)**(-mp.prec + 4)
```
