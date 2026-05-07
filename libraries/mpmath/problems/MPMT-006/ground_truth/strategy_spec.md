# Strategy Specification for MPMT-006

## Bug 1: Am1 computation error (alpha <= 1.5, a < 1)

**Trigger condition**: Complex z = a + bi where:
- 0 < a < 1 (after taking |Re(z)|)
- alpha <= 1.5 (alpha = (r+s)/2 where r=|z+1|, s=|z-1|)
- a < 1 (the mpf_neg(am)[0] branch)
- b is moderate (0.05 to 0.8)

The bug is in the imaginary part computation: `c2 = mpf_sub(s, am)` instead of
`c2 = mpf_add(s, am)`, where `am = 1 - a`. This computes `s - (1-a)` instead of
`s + (1-a)` for the Am1 = alpha-1 formula.

**Why default strategy doesn't work**: Default complex strategies generate random
complex numbers. For most random z, alpha > 1.5, so the buggy code path is not
taken. Only inputs with |z| close to 1 trigger this path.

**Trigger probability**: ~30-40% if a is drawn from [0, 1] and b from [0, 1].
Much lower if a and b have wider ranges.

**Minimum trigger**: z = mpc(0.3, 0.4), alpha ~= 1.17

**Detection**: Compare Im(asin(z)) against the log-based reference formula
`asin(z) = -i * log(i*z + sqrt(1-z^2))`. The buggy Am1 produces wrong imaginary
part (error ~0.7).

## Bug 2: Im(asin(x)) sign error for real x > 1

**Trigger condition**: Real x > 1. The `acos_asin` function returns
`(pi/2, c)` instead of `(pi/2, mpf_neg(c))` for asin (n=1) with real a > 1,
making Im(asin(x)) positive instead of negative.

**Why default strategy doesn't work**: Default strategies for asin typically
test real x in [-1, 1]. Testing x > 1 requires specific construction, and
even then the sign error is only detectable if you know Im(asin(x)) should
be negative (from the identity asin(x) = pi/2 - i*acosh(x)).

**Trigger probability**: 100% for any real x > 1.

**Minimum trigger**: x = 1.01

**Detection**: Either (1) check asin(x) + acos(x) = pi/2, or
(2) check Im(asin(x)) = -acosh(x) < 0. The bug makes Im(asin(x)) = +acosh(x) > 0.

## Bug 3: sqrt(alpha^2 + 1) instead of sqrt(alpha^2 - 1) for alpha > 1.5

**Trigger condition**: Complex z where alpha > 1.5 (far from unit circle):
- a > 1 or |b| > 1 or any combination giving alpha > 1.5

The bug is in the imaginary part computation for the "alpha > alpha_crossover"
path: `mpf_add(alpha*alpha, 1)` instead of `mpf_sub(alpha*alpha, 1)`.

**Why default strategy doesn't work**: This bug DOES trigger for many complex
inputs, but the error is relatively small for alpha near 1.5 and grows for
larger alpha. A roundtrip test `sin(asin(z)) == z` detects it.

**Trigger probability**: ~50% for random complex with |Re|, |Im| in [0, 10].
Higher for larger magnitudes.

**Minimum trigger**: z = mpc(1.5, 0.1), alpha ~= 1.5

**Detection**: sin(asin(z)) != z or cos(acos(z)) != z for z with alpha > 1.5.

## Bug 4: d computation error (beta > 0.6417, a <= 1)

**Trigger condition**: Complex z = a + bi where:
- beta > 0.6417 (beta = a/alpha, so a is a significant fraction of alpha)
- 0 < a <= 1
- Specifically: a in (0.7, 0.99) and small b (0.01 to 0.3)

The bug is in the real part computation: `d = mpf_sub(s, am)` instead of
`d = mpf_add(s, am)`, where `am = 1 - a`. This computes `s - (1-a)` instead
of `s + (1-a)` for the atan-based real part formula.

**Why default strategy doesn't work**: beta > 0.6417 requires a to be close
to 1 relative to alpha. Random complex numbers with large imaginary part
will have small beta. Only inputs with a near 1 and small b trigger this.

**Trigger probability**: ~10-15% for random complex with a in [0, 1], b in [0, 1].

**Minimum trigger**: z = mpc(0.75, 0.25), beta ~= 0.71

**Detection**: Compare Re(asin(z)) against the log-based reference formula.
The buggy d produces wrong real part (error ~0.37).
