# Strategy Specification for MRSH-004

## Bug 1: Range max boundary comparison swapped (L4)

### Trigger Condition
`Range(max=N, max_inclusive=True)(N)` raises ValidationError (should PASS).
`Range(max=N, max_inclusive=False)(N)` passes silently (should FAIL).

The bug is triggered only when the input value is EXACTLY equal to the `max` bound. Values strictly inside the range (< max) are unaffected.

### Why Default Strategy Is Insufficient
Random float/integer generation has a near-zero probability of hitting the exact boundary value. If `max=100` and you generate integers in `[-200, 200]`, the probability of exactly generating 100 is 1/401 ≈ 0.25%. For floats, it's essentially 0%.

Additionally, most baseline tests use `max_inclusive=True` (default) and test values well inside the range, never at the exact boundary. The non-default `max_inclusive=False` path is rarely tested by baselines.

### Ground Truth Strategy
Generate integer or float `max_val`, then test:
1. `Range(max=max_val, max_inclusive=True)(max_val)` — must NOT raise
2. `Range(max=max_val, max_inclusive=False)(max_val)` — must raise ValidationError

This directly targets the boundary condition at both inclusive and exclusive modes.

### Trigger Probability Estimate
- Default strategy (random values): ~0.25% per example for integers
- Targeted strategy (direct boundary test): 100%

### Minimum Trigger Input
```python
v = Range(max=0, max_inclusive=True)
v(0)  # Raises with bug (should pass)
```

---

## Bug 2: Length equal check uses > instead of != (L3)

### Trigger Condition
`Length(equal=N)(value)` passes when `len(value) < N` (should FAIL with "Length must be N").
Values with `len(value) > N` still correctly fail.
Values with `len(value) == N` correctly pass.

### Why Default Strategy Is Insufficient
Most baseline tests for `Length(equal=N)` check that values of the exact length pass, and may check a few longer values. They rarely check that shorter values are also rejected.

For a string test with `equal=5`, a baseline might test:
- `"hello"` (length 5) → passes ✓
- `"toolong"` (length 7) → fails correctly ✓
- But not `"hi"` (length 2) → incorrectly passes with bug (should fail)

### Ground Truth Strategy
Generate pairs `(equal_len, short_len)` where `short_len < equal_len`. Test that `Length(equal=equal_len)(value_of_short_len)` raises ValidationError.

Also test on lists to verify it's not string-specific.

### Trigger Probability Estimate
- Default strategy (random strings): ~50% if testing strings shorter than equal (half of random lengths are shorter)
- But most baselines focus on testing "correct" cases and one direction of "incorrect"
- Targeted strategy: 100%

### Minimum Trigger Input
```python
v = Length(equal=5)
v("hi")  # Passes with bug (should raise)
```

---

## Bug 3: And short-circuits after first error (L3)

### Trigger Condition
`And(v1, v2, ...)(x)` where ALL validators fail for `x`. Instead of collecting all N error messages, only the first validator's error is in `ValidationError.messages`.

### Why Default Strategy Is Insufficient
Most baseline tests check that `And` raises when validators fail, but don't verify the NUMBER of error messages. A test like:
```python
try:
    And(Range(min=0), is_even)(-1)
except ValidationError:
    pass  # Just checks that an error is raised, not how many messages
```
would not detect the short-circuit bug.

The bug requires explicitly checking `len(e.messages)` after catching the exception.

### Ground Truth Strategy
Use `N` copies of the same validator (e.g., `Range(min=0)`) so a known bad input (negative number) fails all N. Assert `len(e.messages) == N`.

Or: use two different validators that both fail on the same input, and assert exactly 2 messages.

### Trigger Probability Estimate
- Default strategy that only checks "error is raised": 0% detection
- Strategy checking message count: 100%

### Minimum Trigger Input
```python
v = And(Range(min=0), Range(min=0))  # 2 copies
try:
    v(-1)
except ValidationError as e:
    assert len(e.messages) == 2  # Fails with bug: only 1 message
```

---

## Bug 4: Length min boundary uses <= instead of < (L2)

### Trigger Condition
`Length(min=N)(value)` raises ValidationError when `len(value) == N` (should PASS).
Values with `len(value) > N` still correctly pass.
Values with `len(value) < N` still correctly fail.

### Why Default Strategy Is Insufficient
Random string generation rarely hits the exact minimum boundary. If `min=5` and you generate strings of random length 0-20, there's only a 1/21 ≈ 5% chance of hitting exactly length 5.

Additionally, most baseline tests don't explicitly test the exact minimum boundary value - they tend to test values clearly above the minimum.

### Ground Truth Strategy
Generate integer `min_len`, then test `Length(min=min_len)("x" * min_len)`. This directly tests the inclusive boundary: a string of exactly `min_len` characters must pass.

### Trigger Probability Estimate
- Default strategy (random string lengths): ~5% for typical ranges
- Targeted strategy (exact boundary): 100%

### Minimum Trigger Input
```python
v = Length(min=3)
v("abc")  # Raises with bug (should pass — "abc" has exactly 3 chars = min)
```
