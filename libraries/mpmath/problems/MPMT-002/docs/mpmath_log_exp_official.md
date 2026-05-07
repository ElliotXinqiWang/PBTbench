# mpmath log and exp: Semantic Contracts

This document describes the semantic contracts for the `log`, `exp`, and `power` function families in mpmath 1.3.0, as specified by the official documentation and mathematical definitions.

## Overview

mpmath provides arbitrary-precision elementary transcendental functions. All functions operate under the current working precision (`mp.dps` decimal places, `mp.prec` binary bits). The results are correctly rounded (to nearest) to the working precision.

## `log(x, b=None)` — Natural Logarithm

**Definition**: `log(x)` computes the natural logarithm of `x`.

```python
>>> from mpmath import *
>>> mp.dps = 25
>>> log(e)
mpf('1.0')
>>> log(1)
mpf('0.0')
>>> log(mpf('0.5'))
mpf('-0.6931471805599453094172321')
```

**Semantic contracts** (from the mpmath documentation):

1. **Inverse of exp**: `log(exp(x)) == x` to working precision for all real `x`.

2. **Logarithm identity**: `log(x * y) == log(x) + log(y)` for all `x, y > 0`.

3. **Negation identity**: `log(x) + log(1/x) == 0` for all `x > 0`.

4. **Arbitrary precision**: For any given `mp.dps`, the result is accurate to that many decimal places. In particular, the relative error must be below `10^(-mp.dps)`.

5. **Base change**: `log(x, b) == log(x) / log(b)` for base `b > 0, b != 1`.

**Implementation notes**:

- For `0.5 <= x <= 2`: mpmath uses a cached Taylor-series method (`log_taylor_cached`). The correction term for the Taylor series is computed using the arctanh-like formula `v = (x-a)/(x+a)` where `a` is the nearest cache point, and the result is `2 * (v + v^3/3 + v^5/5 + ...)`.
- For very large or very small `x`: argument reduction via `log(x) = log(x/2^n) + n*log(2)`.
- For high precision (`dps >= ~750`): the Arithmetic-Geometric Mean (AGM) method is used, which requires additional guard bits proportional to the magnitude of the optimal argument reduction shift.

## `exp(x)` — Natural Exponential

**Definition**: `exp(x)` computes `e^x` where `e = 2.71828...`.

```python
>>> exp(0)
mpf('1.0')
>>> exp(1)
mpf('2.718281828459045235360287')
>>> exp(log(5))
mpf('5.0')
```

**Semantic contracts**:

1. **Inverse of log**: `exp(log(x)) == x` for all `x > 0`.

2. **Negation identity**: `exp(x) * exp(-x) == 1` for all real `x`.

3. **Addition law**: `exp(x + y) == exp(x) * exp(y)` for all real `x, y`.

4. **Arbitrary precision**: For any `mp.dps`, the result is accurate to that many decimal places.

5. **Special values**: `exp(0) == 1`, `exp(1) == e`.

**Implementation notes**:

- For large `|x| >= 2`: argument reduction via `exp(x) = exp(x - n*ln(2)) * 2^n` where `n = floor(x / ln(2))`. After reduction, the residual is in `[0, ln(2))`. Extra working bits (`mag` bits) are added to handle the large-argument case.
- For very high precision (binary precision `prec > 600`) with integer or half-integer `x`: uses `mpf_pow_int(e, x, ...)` where `e = mpmath.e` computed with extra precision `≈ 1.45 * log2(x)` bits. This extra precision compensates for the precision magnification in computing `e^n` when `n` is large.
- For small `|x| < 2`: direct Taylor series after argument squaring.

## `power(x, y)` — General Power `x^y`

**Definition**: `power(x, y)` computes `x^y` via `exp(y * log(x))` for non-integer `y`.

```python
>>> power(2, 0.5)
mpf('1.4142135623730950488016887')
>>> power(e, 2)
mpf('7.3890560989306502272304274')
```

**Semantic contracts**:

1. **Consistency**: `power(x, y)` should agree with `exp(y * log(x))` to working precision.

2. **Integer exponent**: For integer `n`, `power(x, n)` uses binary exponentiation and agrees with `x * x * ... * x` (n times) to full precision.

3. **Power law**: `power(x, a+b) == power(x, a) * power(x, b)` for all real `a, b`.

4. **Reciprocal**: `power(x, -n) == 1 / power(x, n)` for positive integer `n`.

## Precision Guarantees

mpmath guarantees that for standard inputs, all elementary functions are computed with relative error below `2^(-prec + 4)` where `prec = mp.prec`. This holds for:

- Log at any precision using the Taylor (prec <= ~2500 bits) or AGM (prec > ~2500 bits) methods.
- Exp at any precision using argument reduction and Taylor series.

The key algorithmic invariant is that internal working precision `wp` must exceed the target precision `prec` by enough guard bits to absorb rounding errors from multiple fixed-point operations.

## Reference Mathematical Identities

The following identities hold exactly in real arithmetic and should hold to full working precision in mpmath:

| Identity | Trigger condition |
|---|---|
| `log(x) + log(1/x) == 0` | All `x > 0` |
| `log(x * y) == log(x) + log(y)` | All `x, y > 0` |
| `exp(x) * exp(-x) == 1` | All real `x` |
| `exp(log(x)) == x` | All `x > 0` |
| `log(exp(x)) == x` | All real `x` |
| `exp(x + y) == exp(x) * exp(y)` | All real `x, y` |
