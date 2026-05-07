# mpmath: AGM and Complete Elliptic Integrals API Reference

## Overview

mpmath provides arbitrary-precision implementations of the Arithmetic-Geometric Mean (AGM) and complete elliptic integrals of the first and second kind. These functions support both real and complex arguments.

## Functions

### `mpmath.agm(a, b)` - Arithmetic-Geometric Mean

Computes the AGM of two nonnegative numbers `a` and `b`.

**Definition**: Starting from `a_0 = a`, `b_0 = b`, iterate:
- `a_{n+1} = (a_n + b_n) / 2`
- `b_{n+1} = sqrt(a_n * b_n)`

The sequences converge to a common limit, which is `agm(a, b)`.

**Key properties**:
- `agm(a, a) = a`
- `agm(0, a) = 0`
- **Homogeneity**: `agm(k*a, k*b) = k * agm(a, b)` for any `k > 0`
- **Symmetry**: `agm(a, b) = agm(b, a)`
- `agm(a, b) >= 0` when `a, b >= 0`

**Implementation note**: Internally uses fixed-point arithmetic. When inputs are very small or very large, they are rescaled to be near unity before the fixed-point computation, then the result is scaled back.

**Examples**:
```python
>>> mp.dps = 25
>>> agm(1, 2)
mpf('1.4567910310469068691864323')
>>> agm(1, mpf('0.5'))
mpf('0.72839551552345602306894836')
>>> # Homogeneity
>>> agm(100, 200) == 100 * agm(1, 2)
True
```

### `mpmath.ellipk(m)` - Complete Elliptic Integral of the First Kind

Computes K(m) for real or complex argument `m`.

**Definition**:
```
K(m) = integral from 0 to pi/2 of dt / sqrt(1 - m*sin(t)^2)
```

Equivalently, `K(m) = pi / (2 * agm(1, sqrt(1 - m)))`.

**Key properties**:
- `K(0) = pi/2`
- `K(m) -> infinity` as `m -> 1`
- `K(m) > 0` for `0 <= m < 1`
- K(m) is monotonically increasing on `[0, 1)`
- For complex `z`: `K(conj(z)) = conj(K(z))` (conjugate symmetry)
- K is analytic in the complex plane cut along `[1, +infinity)`

**High-precision behavior**: At higher working precisions (dps >= 50), the AGM-based computation requires careful internal precision management to maintain accuracy, especially for `m` close to 0 or close to 1.

**Examples**:
```python
>>> mp.dps = 25
>>> ellipk(0)
mpf('1.5707963267948966192313217')  # pi/2
>>> ellipk(0.5)
mpf('1.8540746773013719184338503')
>>> ellipk(0.99)
mpf('3.3566005233611923253243697')
>>> # Complex argument
>>> ellipk(mpc(0, 1))  # K(i)
mpc(real='1.3111028777146120044860712', imag='-0.62514567989008872178714835')
```

### `mpmath.ellipe(m)` - Complete Elliptic Integral of the Second Kind

Computes E(m) for real or complex argument `m`.

**Definition**:
```
E(m) = integral from 0 to pi/2 of sqrt(1 - m*sin(t)^2) dt
```

**Key properties**:
- `E(0) = pi/2`
- `E(1) = 1`
- `1 <= E(m) <= pi/2` for `0 <= m <= 1`
- E(m) is monotonically decreasing on `[0, 1]`
- **Legendre relation**: `E(m)*K(1-m) + E(1-m)*K(m) - K(m)*K(1-m) = pi/2`
  This identity holds exactly for all `0 < m < 1`

**Implementation note**: E(m) is computed using K(m) and a numerical approximation of K'(m) via a finite difference. The formula is:
```
E(m) = (1-m) * (K(m) + 2*m * K'(m))
```
where K'(m) is approximated as `(K(m) - K(m-h)) / h` for a suitably small `h`.

**Examples**:
```python
>>> mp.dps = 25
>>> ellipe(0)
mpf('1.5707963267948966192313217')  # pi/2
>>> ellipe(0.5)
mpf('1.3506438810476755025201747')
>>> ellipe(1)
mpf('1.0')
>>> # Legendre relation check
>>> m = mpf('0.3')
>>> ellipe(m)*ellipk(1-m) + ellipe(1-m)*ellipk(m) - ellipk(m)*ellipk(1-m)
mpf('1.5707963267948966192313217')  # pi/2
```

## Mathematical Relationships

### AGM and Elliptic K
```
K(m) = pi / (2 * agm(1, sqrt(1-m)))
```

### Legendre Relation
```
E(m)*K(1-m) + E(1-m)*K(m) - K(m)*K(1-m) = pi/2
```
This is one of the most important identities in elliptic function theory, connecting K and E at complementary arguments.

### AGM Scaling
```
agm(k*a, k*b) = k * agm(a, b)  for k > 0
```

### E(m) Derivative Relation
```
dK/dm = [E(m)/(1-m) - K(m)] / (2m)
```

## Precision and Accuracy

mpmath supports arbitrary precision. Set `mp.dps` (decimal places) or `mp.prec` (binary bits):

```python
>>> mp.dps = 50  # 50 decimal places
>>> ellipk(0.5)
mpf('1.8540746773013719184338503471478044038139746593468')
```

At high precision (dps >= 50), results should be accurate to the full working precision. You can verify accuracy by:
1. Computing at two different precisions and comparing
2. Checking the Legendre relation
3. Verifying `K(m) = pi/(2*agm(1, sqrt(1-m)))` directly

## Edge Cases

- `K(0) = pi/2`, `E(0) = pi/2`
- `K(1) = infinity`, `E(1) = 1`
- `agm(0, b) = 0`, `agm(a, 0) = 0`
- `agm(inf, b) = inf` for `b > 0`
- For `m > 1` (real), `K(m)` raises `ComplexResult` (must use `mpc` type)
- For complex arguments, K and E are analytic in the plane cut along `[1, +infinity)`
