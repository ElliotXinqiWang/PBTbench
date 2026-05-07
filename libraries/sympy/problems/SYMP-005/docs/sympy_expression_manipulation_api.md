# sympy 1.14.0 Expression Manipulation API Reference

This document covers sympy's expression substitution, simplification, collection,
and expansion routines, focusing on the algebraic properties they must satisfy.

---

## 1. `xreplace(rule)` — Rule-Based Substitution

### Overview

`expr.xreplace(rule)` applies a substitution rule (a dict mapping expressions to
replacement expressions) to all matching subexpressions simultaneously. Unlike
`subs()`, it does not recurse into matched subexpressions and does not attempt
structural simplification during substitution.

### Signature

```python
expr.xreplace(rule: dict) -> Expr
```

### Key properties

- **Completeness**: Every occurrence of a key in `rule` that appears anywhere in the
  expression tree must be replaced. The substitution must not be silently skipped
  for any subterm.
- **Independence**: Replacements are applied simultaneously, not sequentially. If
  `rule = {a: b, b: a}`, then `(a + b).xreplace(rule)` gives `b + a`, not `a + b`.
- **Depth-first**: xreplace visits leaf nodes first, substituting matched symbols
  before rebuilding parent nodes.
- **Partial match handling**: When only some subterms of an Add or Mul match the
  rule, the matched subterms must still be replaced and the unmatched ones kept.
  For example, `(x + b).xreplace({x: 0})` must give `b`, not `x + b`.

### Examples

```python
from sympy import symbols, Integer

x, a, b, c = symbols('x a b c')

# Basic substitution
assert (x + 1).xreplace({x: 3}) == 4

# Partial match: only x matches, b is unaffected
assert (x + b).xreplace({x: 5}) == 5 + b

# Multi-symbol: both a and x replaced
expr = a + x * b
result = expr.xreplace({a: 0, x: 1})
assert a not in result.free_symbols
assert x not in result.free_symbols

# With coefficient: c*x + b, substituting x
c_val = Integer(3)
expr = c_val * x + b
result = expr.xreplace({x: Integer(2)})
assert result == c_val * Integer(2) + b
assert x not in result.free_symbols
```

### Contrast with `subs()`

`subs(x, val)` attempts algebraic simplification after substitution, while
`xreplace` performs exact tree replacement. For testing substitution correctness,
`xreplace` is the preferred method because its semantics are simpler.

---

## 2. `powsimp(expr, ...)` — Power Simplification

### Overview

`powsimp(expr)` simplifies expressions involving powers by combining terms with the
same base (collecting exponents) and combining terms with the same exponent
(collecting bases). The function is in `sympy.simplify`.

### Signature

```python
powsimp(
    expr,
    deep: bool = False,
    combine: str = 'all',   # 'all', 'exp', 'base'
    force: bool = False,
    measure=count_ops
) -> Expr
```

### `combine` parameter

- `'exp'`: Combine exponents only. `x**a * x**b → x**(a+b)` for same base.
- `'base'`: Combine bases only. `x**n * y**n → (x*y)**n` for same exponent.
- `'all'`: Apply both (default).

### Key property: exponent combination

For a positive symbol `x` and symbolic exponents `a`, `b`:

```
powsimp(x**a * x**b, combine='exp') == x**(a+b)
```

More generally, for any list of exponents `e1, e2, ..., en` with the same base `x`:

```
powsimp(x**e1 * x**e2 * ... * x**en) == x**(e1 + e2 + ... + en)
```

**All exponents must be included in the sum.** No exponent should be silently
dropped.

### Examples

```python
from sympy import symbols, powsimp, Integer

x = symbols('x', positive=True)
a, b = symbols('a b')

# Basic: two symbolic exponents combined
result = powsimp(x**a * x**b, combine='exp')
assert (result / x**(a + b)).simplify() == 1

# With integer offsets: ensures symbolic form before powsimp
e1 = Integer(2)
e2 = Integer(-1)
expr = x**(a + e1) * x**(b + e2)
result = powsimp(expr, combine='exp')
expected = x**(a + b + e1 + e2)
assert (result / expected).simplify() == 1

# Multiple bases
y = symbols('y', positive=True)
result = powsimp(x**a * y**a, combine='base')
assert result == (x * y)**a
```

### Note on integer exponents

If both exponents are pure integers (e.g., `x**2 * x**3`), sympy may auto-combine
them to `x**5` before `powsimp` is even called. To reliably test the `powsimp`
exponent-combination code path, use at least one symbolic component in each
exponent (e.g., `x**(a + 2)` and `x**(b - 1)`).

---

## 3. `collect(expr, syms, ...)` — Polynomial Collection

### Overview

`collect(expr, syms)` collects additive terms in `expr` that share the same power
of a symbol (or list of symbols). It factors out the common power, grouping all
coefficients that multiply that power into a single sum.

### Signature

```python
collect(
    expr,
    syms,               # symbol or list of symbols to collect by
    func=None,
    evaluate=None,
    exact: bool = False,
    distribute_order_term: bool = True,
) -> Expr
```

### Key property: algebraic equivalence

The result of `collect` must always be algebraically equivalent to the input:

```
(collect(expr, x) - expr).expand() == 0
```

This invariant holds for any expression, regardless of how many terms share a
given power of `x`.

### Key property: coefficient completeness

When multiple additive terms share the same power of `x`, ALL their coefficients
must be summed together:

```python
from sympy import symbols, collect

x, a, b = symbols('x a b')

# Two terms both have x**1: (a+1)*x and (b+2)*x
expr = (a + 1)*x + (b + 2)*x
result = collect(expr, x)

# The coefficient of x must include both a+1 and b+2
coeff = result.coeff(x)
assert (coeff - ((a + 1) + (b + 2))).expand() == 0
```

### Examples

```python
from sympy import symbols, collect, Integer

x, a, b = symbols('x a b')

# Basic collection: integer coefficients auto-combine before collect
expr = 2*x + 3*x
assert collect(expr, x) == 5*x  # auto-combined before collect

# Symbolic coefficients: two terms with same power
expr = a*x + b*x
result = collect(expr, x)
# Must be algebraically equal to a*x + b*x
assert (result - expr).expand() == 0
# Coefficient of x must be a + b
coeff = result.coeff(x)
assert (coeff - (a + b)).expand() == 0

# Higher powers: collect on x**2 with symbolic coefficients
expr = a*x**2 + b*x**2 + 3*x
result = collect(expr, x)
assert (result - expr).expand() == 0
coeff_x2 = result.coeff(x, 2)
assert (coeff_x2 - (a + b)).expand() == 0

# Constant term is unaffected
expr = a*x + b*x + 5
result = collect(expr, x)
assert (result - expr).expand() == 0
```

### Note on integer vs. symbolic coefficients

With pure integer coefficients, sympy simplifies `1*x + 1*x → 2*x` at construction
time, before `collect` is called. In that case, `collect` sees only one term per
power and there is nothing to combine. To exercise the multi-coefficient collection
code path, use at least one symbolic component in each coefficient (e.g.,
`(a + 1)*x + (b + 2)*x` rather than `1*x + 1*x`).

---

## 4. `expand(expr)` — Expansion of Products and Powers

### Overview

`expand(expr)` distributes products and powers into sums. For integer powers of
binomials (including complex binomials involving `I`), it computes the expansion
symbolically.

### Signature

```python
expand(
    expr,
    deep: bool = True,
    modulus=None,
    power_base: bool = True,
    power_exp: bool = True,
    mul: bool = True,
    log: bool = True,
    multinomial: bool = True,
    basic: bool = True,
    **hints
) -> Expr
```

### Key property: complex binomial expansion

For integer constants `p`, `q` (with `q != 0`) and positive integer `n`:

```
expand((p + q*I)**n) == (p + q*1j)**n   [as complex arithmetic]
```

The real and imaginary parts of the sympy result must match Python's native
complex arithmetic:

```python
import cmath
from sympy import Integer, I, expand

p, q, n = 1, 2, 3

# Python reference
py_result = (p + q * 1j) ** n
expected_real = round(py_result.real)   # -11
expected_imag = round(py_result.imag)   # 2

# Sympy
sp, sq, sn = Integer(p), Integer(q), Integer(n)
sympy_result = expand((sp + sq * I) ** sn)
real_part, imag_part = sympy_result.as_real_imag()

assert int(real_part) == expected_real
assert int(imag_part) == expected_imag
```

### Examples

```python
from sympy import Integer, I, expand, symbols

# Simple: (1 + I)**2 = 2*I
result = expand((Integer(1) + I)**2)
real, imag = result.as_real_imag()
assert int(real) == 0
assert int(imag) == 2

# n=3: (1 + I)**3 = (1+I)*(2I) = 2I + 2I^2 = -2 + 2I
result = expand((Integer(1) + I)**3)
real, imag = result.as_real_imag()
assert int(real) == -2
assert int(imag) == 2

# n=4: (1 + I)**4 = ((1+I)**2)**2 = (2I)**2 = -4
result = expand((Integer(1) + I)**4)
real, imag = result.as_real_imag()
assert int(real) == -4
assert int(imag) == 0

# General verification via Python complex
for p in range(-3, 4):
    for q in range(1, 4):
        for n in range(3, 7):
            py = (p + q * 1j) ** n
            sy = expand((Integer(p) + Integer(q) * I) ** Integer(n))
            sy_real, sy_imag = sy.as_real_imag()
            assert int(sy_real) == round(py.real)
            assert int(sy_imag) == round(py.imag)
```

### Note on which values trigger the integer power path

sympy's `_eval_expand_multinomial` has a fast path for integer powers of complex
binomials (of the form `a + b*I` where `a`, `b` are integers). This path uses a
squaring-and-multiply algorithm. For `n=1`, no squaring or multiplying is needed.
For `n=2`, only squaring is used (no odd steps). For `n >= 3` with non-zero
imaginary component, the algorithm must execute the odd-step update formula, which
involves the real-part computation. Use `n >= 3` and `q != 0` to reliably exercise
this code path.

---

## 5. `symbols()` — Creating Symbolic Variables

```python
from sympy import symbols

# Unconstrained symbols
x, a, b, c = symbols('x a b c')

# Positive symbol (required for certain powsimp rules)
x_pos = symbols('x', positive=True)

# Integer symbol
n = symbols('n', integer=True, positive=True)
```

Use `positive=True` for the base in `powsimp` tests to enable the simplification
rules that combine exponents of the same base.

---

## 6. `Integer`, `Rational`, `S` — Sympy Integer Literals

```python
from sympy import Integer, Rational, S

# Explicit sympy integers (avoids Python int operations before sympy sees them)
n = Integer(5)
q = Integer(-3)
half = Rational(1, 2)

# Special constants
zero = S.Zero
one = S.One
```

Use `Integer(n)` rather than plain Python `int` when building sympy expressions to
ensure that arithmetic remains symbolic until explicitly evaluated.

---

## 7. `as_real_imag()` — Splitting into Real and Imaginary Parts

```python
from sympy import Integer, I, expand

result = expand((Integer(1) + Integer(2) * I) ** 3)
real_part, imag_part = result.as_real_imag()
# real_part and imag_part are sympy Integer objects
# Use int() to convert for comparison
```

---

## 8. `free_symbols` — Set of Unbound Symbols

```python
from sympy import symbols

x, a, b = symbols('x a b')
expr = a * x + b
assert x in expr.free_symbols      # True
assert b in expr.free_symbols      # True

after = expr.xreplace({x: 0, a: 1})
assert x not in after.free_symbols # True after substitution
```

---

## 9. `equals(other)` — Structural + Numeric Equality

```python
from sympy import symbols, Integer

x, a, b = symbols('x a b')
expr1 = a + b
expr2 = b + a
assert expr1.equals(expr2)   # True (mathematically equal)

# Useful when == might not detect equality due to symbolic form
expected = Integer(3) * Integer(2) + b
result = (some_xreplace_result)
assert result.equals(expected)
```

---

## 10. `coeff(x, n=1)` — Extracting a Polynomial Coefficient

```python
from sympy import symbols, collect

x, a, b = symbols('x a b')
expr = collect(a*x + b*x + 5, x)
c = expr.coeff(x)       # coefficient of x**1
c2 = expr.coeff(x, 2)   # coefficient of x**2
```

Returns 0 if the term is absent, otherwise the symbolic coefficient expression.

---

## Summary of Properties to Test

| Function | Property | Trigger Condition |
|---|---|---|
| `xreplace` | All occurrences replaced | Mixed expression with partial symbol match |
| `powsimp` | `x**a * x**b == x**(a+b)` | Symbolic exponents with same base |
| `collect` | Algebraic equivalence preserved | Multiple symbolic-coeff terms, same power |
| `collect` | All coefficients summed | Two+ terms with same power of x |
| `expand` | Complex power matches native complex | Integer p, q (q≠0), n≥3 |
