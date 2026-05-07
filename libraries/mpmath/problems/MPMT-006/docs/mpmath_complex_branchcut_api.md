# mpmath Complex Inverse Trigonometric Functions API

## Overview

mpmath is a Python library for arbitrary-precision floating-point arithmetic.
This document covers the complex extensions of `asin` and `acos`, which are
defined for all complex numbers and satisfy important mathematical identities.

## Installation

```python
pip install mpmath==1.3.0
```

## Setting Precision

mpmath uses a global precision context `mp.dps` (decimal places):

```python
from mpmath import mp, mpf, mpc, asin, acos, sin, cos, pi

mp.dps = 50  # 50 decimal places of precision
```

## Complex Number Construction

Complex numbers are created using `mpc(real, imag)` or arithmetic:

```python
z = mpc(3, 4)       # 3 + 4i
z = mpc(0.5, -0.7)  # 0.5 - 0.7i
z = mpf(2.5)         # pure real
```

## Functions

### `asin(z)` — Complex Arcsine

Computes the inverse sine of a complex number `z`.

**Definition**: For any complex z, `asin(z)` returns a complex number w such that
`sin(w) = z`. The principal branch is chosen.

**Mathematical properties**:
- For real x in [-1, 1]: `asin(x)` is real, in [-pi/2, pi/2]
- For real x > 1: `asin(x) = pi/2 - i*acosh(x)` (imaginary part is negative)
- For real x < -1: `asin(x) = -pi/2 + i*acosh(-x)` (imaginary part is positive)
- For all complex z: `sin(asin(z)) = z` (roundtrip identity)
- For all complex z: `asin(z) + acos(z) = pi/2` (complement identity)
- Odd function: `asin(-z) = -asin(z)`
- Conjugate symmetry: `asin(conj(z)) = conj(asin(z))` for z not on branch cuts

**Branch cuts**: The branch cuts for asin are on the real axis at
`(-inf, -1)` and `(1, +inf)`. The function is continuous from above
on `(-inf, -1)` and from below on `(1, +inf)`.

**Parameters**:
- `z`: mpf or mpc number (or Python int/float/complex)
- Returns: mpf (if result is real) or mpc (otherwise)

**Usage examples**:
```python
mp.dps = 50

# Real argument in [-1, 1]
asin(mpf(0.5))  # returns pi/6

# Real argument > 1 (complex result)
asin(mpf(2))    # returns pi/2 - i*acosh(2)

# Complex argument
z = mpc(3, 4)
w = asin(z)
sin(w)  # should equal z (roundtrip)
```

### `acos(z)` — Complex Arccosine

Computes the inverse cosine of a complex number `z`.

**Definition**: For any complex z, `acos(z)` returns a complex number w such that
`cos(w) = z`. The principal branch is chosen.

**Mathematical properties**:
- For real x in [-1, 1]: `acos(x)` is real, in [0, pi]
- For real x > 1: `acos(x) = i*acosh(x)` (pure imaginary, positive imaginary part)
- For real x < -1: `acos(x) = pi - i*acosh(-x)` (imaginary part is negative)
- For all complex z: `cos(acos(z)) = z` (roundtrip identity)
- For all complex z: `asin(z) + acos(z) = pi/2` (complement identity)
- Symmetry: `acos(-z) = pi - acos(z)`
- Conjugate symmetry: `acos(conj(z)) = conj(acos(z))` for z not on branch cuts

**Branch cuts**: Same as asin — on the real axis at `(-inf, -1)` and `(1, +inf)`.

**Parameters**:
- `z`: mpf or mpc number
- Returns: mpf (if result is real) or mpc (otherwise)

**Usage examples**:
```python
mp.dps = 50

# Real argument
acos(mpf(0.5))  # returns pi/3

# Complex argument
z = mpc(2, 1)
w = acos(z)
cos(w)  # should equal z (roundtrip)
```

## Key Mathematical Identities

These identities hold for **all** complex numbers z at arbitrary precision:

### 1. Complement Identity
```
asin(z) + acos(z) = pi/2
```
This is the most fundamental identity. It must hold exactly (to working precision)
for all z, including real values outside [-1, 1] and complex values.

### 2. Roundtrip Identities
```
sin(asin(z)) = z
cos(acos(z)) = z
```
These must hold to working precision for all complex z.

### 3. Sign Conventions for Real Extensions

For real x > 1:
- `Re(asin(x)) = pi/2` (the real part is exactly pi/2)
- `Im(asin(x)) < 0` (the imaginary part is negative: `-acosh(x)`)
- `Re(acos(x)) = 0` (the real part is exactly 0)
- `Im(acos(x)) > 0` (the imaginary part is positive: `+acosh(x)`)

For real x < -1:
- `Re(asin(x)) = -pi/2`
- `Im(asin(x)) > 0` (positive: `+acosh(-x)`)
- `Re(acos(x)) = pi`
- `Im(acos(x)) < 0` (negative: `-acosh(-x)`)

### 4. Alternative Computation via Logarithm
```
asin(z) = -i * log(i*z + sqrt(1 - z^2))
acos(z) = -i * log(z + sqrt(z^2 - 1))
```
These logarithm-based formulas provide an independent way to compute the functions,
useful for cross-validation.

## Precision and Accuracy

mpmath guarantees results accurate to the working precision (`mp.dps` decimal digits
or `mp.prec` binary bits). The implementation uses the Hull-Fairgrieve-Tang algorithm
which has multiple code paths optimized for numerical stability in different regions
of the complex plane:

- **Near the unit circle** (|z| close to 1): Special formulas avoid cancellation.
  The parameter `alpha = (r+s)/2` where `r = |z+1|` and `s = |z-1|` determines
  the region. When `alpha` is close to 1 (specifically `alpha <= 1.5`), alternative
  formulas for `alpha - 1` are used.

- **Far from the unit circle** (large |z|): The standard formula
  `log(alpha + sqrt(alpha^2 - 1))` is used for the imaginary part.

- **Beta crossover** (beta = a/alpha): When `beta` exceeds approximately 0.6417,
  the real part is computed using `atan`-based formulas instead of `acos(beta)`/`asin(beta)`
  for better numerical stability.

The library handles all these regions automatically based on the input value.

## Testing Recommendations

When testing complex asin/acos, consider:

1. **Real arguments in [-1, 1]**: Basic real-valued results
2. **Real arguments outside [-1, 1]**: Complex results with specific sign conventions
3. **Complex arguments near the unit circle**: Where numerical cancellation is most likely
4. **Complex arguments far from the unit circle**: Different algorithm paths
5. **Arguments near the branch cuts**: Where sign/continuity conventions matter
6. **High precision**: Test at dps=50 or higher to verify precision
7. **Cross-validation**: Compare asin/acos results against log-based formulas

## Additional Functions

### `acosh(x)` — Inverse Hyperbolic Cosine
For real x >= 1: `acosh(x) = log(x + sqrt(x^2 - 1))`

### `sin(z)`, `cos(z)` — Complex Sine and Cosine
Standard trigonometric functions extended to complex arguments.

### `pi` — Mathematical constant pi
Available at arbitrary precision via `mp.dps`.

### `log(z)` — Complex Natural Logarithm
For complex z: `log(z) = log(|z|) + i*arg(z)`. Used in the alternative logarithmic
formulas for asin/acos.

### `sqrt(z)` — Complex Square Root
For complex z: returns the principal square root with `Re(sqrt(z)) >= 0`.

## Error Handling

- `asin(inf)` and `acos(inf)` return complex infinity.
- `asin(nan)` and `acos(nan)` return `nan`.
- The functions handle subnormal inputs correctly at all precisions.

## Implementation Details

The Hull-Fairgrieve-Tang algorithm partitions the complex plane into regions
and uses numerically stable formulas in each region. The key insight is that
naive computation of `asin(z) = -i * log(i*z + sqrt(1 - z^2))` suffers from
catastrophic cancellation near the real axis and near the points z = +/-1.

The algorithm avoids this by computing intermediate quantities `alpha` and `beta`
and using different formulas depending on their values:

- `alpha = (|z+1| + |z-1|) / 2` measures the "elliptical distance" from the origin
- `beta = |Re(z)| / alpha` is a normalized real-part measure

The crossover thresholds are:
- `alpha_crossover = 1.5`: Below this, use `Am1 = alpha - 1` formula
  to avoid cancellation in `log(alpha + sqrt(alpha^2 - 1))`
- `beta_crossover ~= 0.6417`: Below this, use direct `asin(beta)` or `acos(beta)`;
  above this, use `atan`-based formulas to avoid cancellation in `asin(beta)` near 1.

When `alpha <= alpha_crossover`:
- For `|Re(z)| < 1`: `Am1 = (1/2) * (b^2/(r+a+1) + b^2/(s+1-a))`
  where `r = |z+1|`, `s = |z-1|`, `a = |Re(z)|`, `b = |Im(z)|`
- For `|Re(z)| >= 1`: `Am1 = (1/2) * (b^2/(r+a+1) + (s-(1-a)))`
- Then `Im = log(1 + Am1 + sqrt(Am1 * (alpha + 1)))`

When `alpha > alpha_crossover`:
- `Im = log(alpha + sqrt(alpha^2 - 1))`

When `beta > beta_crossover`:
- For `|Re(z)| <= 1`: compute `alpha - a = (c + d)/2` where
  `c = b^2/(r+a+1)` and `d = s + (1-a)`
- For `|Re(z)| > 1`: different formula for `d`
- Then `Re = atan(...)` using the computed `alpha - a`

When `beta <= beta_crossover`:
- `Re = asin(beta)` or `Re = acos(beta)` directly

## Summary Table of Key Formulas

| Region | Real part formula | Imaginary part formula |
|---|---|---|
| beta <= 0.6417, alpha <= 1.5, a < 1 | asin(beta) | log(1 + Am1 + sqrt(Am1*(alpha+1))) |
| beta <= 0.6417, alpha > 1.5 | asin(beta) | log(alpha + sqrt(alpha^2 - 1)) |
| beta > 0.6417, a <= 1, alpha <= 1.5 | atan(...) | log(1 + Am1 + sqrt(Am1*(alpha+1))) |
| beta > 0.6417, a <= 1, alpha > 1.5 | atan(...) | log(alpha + sqrt(alpha^2 - 1)) |
| Real x > 1 | pi/2 | -acosh(x) |
| Real x < -1 | -pi/2 | acosh(-x) |
