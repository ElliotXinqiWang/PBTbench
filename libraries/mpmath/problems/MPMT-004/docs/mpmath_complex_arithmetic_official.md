# mpmath Documentation — Complex Arithmetic: sqrt, square, arg, reciprocal

Source: https://mpmath.org/doc/current/general.html
Additional references: https://mpmath.org/doc/current/functions/powers.html

---

## Overview

mpmath provides arbitrary-precision complex arithmetic through the `mpc` type.
The fundamental operations must satisfy well-defined mathematical contracts:

```python
import mpmath
from mpmath import mp, mpc, sqrt, arg, power

mp.dps = 50  # decimal places of precision
```

---

## Complex Square Root: sqrt(z)

The principal square root of a complex number z = a + bi is defined by:

```
sqrt(a + bi) = sqrt((|z| + a) / 2) + sign(b) * sqrt((|z| - a) / 2) * i
```

where |z| = sqrt(a^2 + b^2) is the absolute value.

**Key invariants:**

1. `sqrt(z) ** 2 == z` — squaring the square root recovers z
2. For z on the negative real axis (b = 0, a < 0):
   `sqrt(a) == sqrt(-a) * i` — result is purely imaginary
3. Real part: `sqrt(z).real == sqrt((|z| + a) / 2)`
4. Imaginary part (when a < 0): `sqrt(z).imag == sqrt((|z| - a) / 2)`

**The crucial formula for negative real part (a < 0):**
- `t = |z| - a` (NOT `|z| + a`)
- `imag_part = sqrt(t/2)`

```python
z = mpc(-3, 4)
r = sqrt(z)
print(r)                # (1.0 + 2.0j) approximately
print(r * r)            # should equal z: (-3 + 4j) approximately
assert abs(r**2 - z) < mpmath.mpf(10)**(-mp.dps + 5)
```

### Roundtrip Contract

For any complex z (with appropriate branch convention):
```python
r = mpmath.sqrt(z)
assert abs(r * r - z) < mpmath.mpf(10)**(-mp.dps + 5)
```

For z with negative real part and zero imaginary part:
```python
z = mpc(-4, 0)
r = mpmath.sqrt(z)
assert abs(r.real) < 1e-40          # real part should be ~0
assert abs(r.imag - 2) < 1e-40     # imag part should be 2
```

---

## Complex Square: z ** 2

The formula for (a + bi)^2 is:
```
(a + bi)^2 = (a^2 - b^2) + 2ab*i
```

**Key invariants:**

1. Real part: `(z**2).real == a**2 - b**2` (subtraction, NOT addition)
2. Imaginary part: `(z**2).imag == 2*a*b`
3. `sqrt(z**2) == z` (up to branch cut and precision)

```python
z = mpc(3, 4)
s = z ** 2
print(s)        # (9 - 16) + 2*3*4*i = -7 + 24i
assert abs(s.real - (3**2 - 4**2)) < 1e-40   # -7
assert abs(s.imag - 2*3*4) < 1e-40           # 24
```

For a pure imaginary number z = bi:
```python
z = mpc(0, 3)
s = z ** 2
assert abs(s.real + 9) < 1e-40   # (0^2 - 3^2) = -9
assert abs(s.imag) < 1e-40        # 2*0*3 = 0
```

---

## Argument (Phase): arg(z)

The argument (phase) of a complex number z = a + bi is:
```
arg(z) = atan2(b, a)
```

Note: `atan2(y, x)` takes the **imaginary part as first argument** and the **real part as second**.

**Key invariants:**

1. `arg(1 + 0i) == 0`         (positive real axis)
2. `arg(0 + 1i) == pi/2`      (positive imaginary axis)
3. `arg(-1 + 0i) == pi`       (negative real axis)
4. `arg(0 - 1i) == -pi/2`     (negative imaginary axis)
5. `arg(1 + 1i) == pi/4`      (45 degrees)
6. `arg(1 - 1i) == -pi/4`     (-45 degrees)

```python
from mpmath import pi, j

assert abs(arg(mpc(1, 0)) - 0) < 1e-40
assert abs(arg(mpc(0, 1)) - pi/2) < 1e-40
assert abs(arg(mpc(-1, 0)) - pi) < 1e-40
assert abs(arg(mpc(0, -1)) + pi/2) < 1e-40
assert abs(arg(mpc(1, 1)) - pi/4) < 1e-40
```

### Polar Form Consistency

```python
import mpmath

z = mpc(3, 4)
r = abs(z)
theta = arg(z)
# Polar reconstruction: z = r * exp(i*theta)
z_reconstructed = r * mpmath.exp(1j * theta)
assert abs(z_reconstructed - z) < 1e-40
```

---

## Complex Reciprocal: 1/z

The formula for 1/(a + bi) is:
```
1/(a + bi) = a/(a^2 + b^2) - b/(a^2 + b^2) * i
```

**Key invariants:**

1. Real part of 1/z: `a / (a^2 + b^2)` (same sign as a)
2. Imaginary part of 1/z: `-b / (a^2 + b^2)` (opposite sign to b, with MINUS)
3. `z * (1/z) == 1`

```python
z = mpc(1, 2)
r = 1 / z
# r = 1/(1+2i) = (1-2i)/5 = 0.2 - 0.4i
assert abs(r.real - 0.2) < 1e-40
assert abs(r.imag + 0.4) < 1e-40   # note: -0.4, not +0.4

# Multiplication check
assert abs(z * r - 1) < 1e-40
```

For a pure imaginary number z = bi:
```python
z = mpc(0, 2)
r = 1 / z
# r = 1/(0+2i) = -i/2 = 0 - 0.5i
assert abs(r.real) < 1e-40
assert abs(r.imag + 0.5) < 1e-40   # imag is negative
```

---

## Summary of Invariants to Test

| Operation | Formula | Key property |
|-----------|---------|-------------|
| `sqrt(z)` | `sqrt((|z|+a)/2) + ...*i` | `sqrt(z)**2 == z`; for a<0 branch: `t = |z| - a` |
| `z**2` | `(a^2 - b^2) + 2abi` | real part uses subtraction; `im(z**2) = 2*re(z)*im(z)` |
| `arg(z)` | `atan2(im(z), re(z))` | arg(i) = pi/2; arg(-1) = pi; arg(1+i) = pi/4 |
| `1/z` | `a/m - b/m * i` where `m = a^2+b^2` | `z * (1/z) == 1`; im(1/z) has opposite sign to im(z) |
