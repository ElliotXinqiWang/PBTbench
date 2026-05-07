# SYMP-005 Ground Truth Strategy Specification

## Bug 1: xreplace partial-match failure (`basic.py`)

**Trigger condition**: Any expression where the substitution rule matches only a
proper subset of the top-level args of an Add or Mul node.

**Key insight**: `c*x + b` is an Add with args `(c*x, b)`. When we xreplace `{x: val}`,
only `c*x` matches (not `b`). The `changed` flag should become True via `|=` when
ANY child changes. With `&=`, changed stays False (False & True = False), so the
parent node is not rebuilt and returns the original expression unchanged.

**Why default strategy fails**: Most xreplace uses test pure single-symbol substitution
`(x + 1).xreplace({x: 3})`. Here all args of `x+1` that could match do match (the
literal `1` has no `_xreplace` method). This bypasses the bug entirely.

**Strategy**:
- `st.integers(min_value=-5, max_value=5).filter(lambda v: v != 0)` for coefficient
- `st.integers(min_value=-5, max_value=5)` for replacement
- Build `expr = Integer(coeff) * x + b` where `b` is a free symbol
- Assert `x not in expr.xreplace({x: rep}).free_symbols`

**Trigger rate**: ~100% (every non-zero integer coefficient gives a partial-match Add)

---

## Bug 2: powsimp drops last exponent (`powsimp.py`)

**Trigger condition**: `powsimp(x**e1 * x**e2, combine='exp')` where e1, e2 are
symbolic (not pure integer). The exponents accumulate as `e = [e1, e2]` in
`c_powers[x]`. The bug uses `Add(*e[:-1])` which gives `e1` instead of `e1+e2`.

**Why default strategy fails**: With pure integer exponents like `x**2 * x**3`,
sympy evaluates `x**2 * x**3 = x**5` at construction time before `powsimp` is called.
The powsimp exponent-accumulation code path is never reached.

**Strategy**:
- `st.integers(min_value=-4, max_value=4)` for offsets e1, e2
- Build `x**(a + e1) * x**(b + e2)` where a, b are free symbols
- Call `powsimp(expr, combine='exp')`
- Assert `(result / x**(a + b + e1 + e2)).simplify() == 1`

**Trigger rate**: ~100% (symbolic exponents prevent auto-combination; two exponents
always exist in the list so `e[:-1]` always drops e2)

---

## Bug 3: collect drops last coefficient (`radsimp.py`)

**Trigger condition**: Two or more additive terms with the same power of the
collection variable, where the coefficients are symbolic. The collected list
`v = [coeff1, coeff2]` for that power key should become `Add(*v)` = `coeff1 + coeff2`,
but the bug uses `Add(*v[:-1])` = `coeff1`, silently dropping `coeff2`.

**Why default strategy fails**: With pure integer coefficients like `2*x + 3*x`,
sympy evaluates `2*x + 3*x = 5*x` before `collect` is called. There is only one
term per power in the collected dict, so `v = [5]` and `Add(*v[:-1])` = `Add()` = 0
would be wrong, but the `len(v) > 1` guard keeps `v[0] = 5`. The bug only triggers
when `len(v) > 1`, which requires two distinct symbolic terms.

**Strategy**:
- Use sympy symbols `a, b` as free variables in coefficients
- `st.integers(min_value=-3, max_value=3)` for integer offsets
- Build `expr = (a + off1)*x + (b + off2)*x + const`
- Assert `(collect(expr, x) - expr).expand() == 0`
- Assert `(result.coeff(x) - ((a + off1) + (b + off2))).expand() == 0`

**Trigger rate**: ~100% (symbolic a, b prevent auto-combination; both terms map to
x**1 so len(v) == 2 and the last is dropped)

---

## Bug 4: complex integer power real part sign error (`power.py`)

**Trigger condition**: `expand((p + q*I)**n)` with integer p, q (q≠0), n≥3.

The squaring-and-multiply loop:
```python
while n:
    if n & 1:        # odd step
        c, d = a*c - b*d, b*c + a*d   # CORRECT: new_real = a*c - b*d
    a, b = a*a - b*b, 2*a*b            # squaring step
    n //= 2
```

The bug changes `a*c - b*d` to `a*c + b*d`. For n=1, the loop executes once
(odd step then done) but there's nothing to corrupt since the initial accumulator
is (c, d) = (1, 0) and the base is (a, b) = (p, q), so:
- Correct: c, d = p*1 - q*0, q*1 + p*0 = (p, q)  ← correct
- Buggy: c, d = p*1 + q*0, q*1 + p*0 = (p, q)  ← also correct for n=1

For n=2, only the squaring step is used (loop exits after squaring since n becomes 1
then 0): (a, b) = (p*p - q*q, 2*p*q), no odd step. Result is correct.

For n=3: odd step (n=3→2), squaring (n=2→1), odd step (n=1→0).
First odd step computes the accumulator from the base, which is always correct
since (c,d) starts at (1,0). Second odd step uses the squared value and the
already-computed accumulator — this is where the sign error corrupts the result.

**Why default strategy fails**: Tests that only use n=1 or n=2 don't reach the
corrupted code path. Tests with q=0 are safe because b*d = q_component * 0 = 0.

**Strategy**:
- `st.integers(min_value=-4, max_value=4)` for p
- `st.integers(min_value=-4, max_value=4).filter(lambda v: v != 0)` for q
- `st.integers(min_value=3, max_value=6)` for n
- Compare `expand((Integer(p) + Integer(q)*I)**Integer(n))` real/imag parts
  to Python's `(p + q*1j)**n`

**Trigger rate**: ~100% for (q≠0, n≥3)
