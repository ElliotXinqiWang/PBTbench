# portion — Interval Arithmetic Library: Complete API Reference

## Overview

`portion` is a Python library for arbitrary interval arithmetic. It provides an
`Interval` class representing unions of atomic intervals, along with `IntervalDict`
for mapping intervals to values. All intervals are immutable and automatically
normalized (sorted and merged) on construction.

**Version**: 2.6.1
**Install**: `pip install portion`
**Import**: `import portion as P`
**Constants**: `P.inf` (positive infinity), `-P.inf` (negative infinity), `P.Bound.CLOSED`, `P.Bound.OPEN`

---

## 1. Interval Constructors

### `P.closed(lower, upper)` → `Interval`
Creates a closed interval `[lower, upper]` — both endpoints included.
```python
I = P.closed(1, 5)   # [1,5]
assert 1 in I        # True
assert 5 in I        # True
assert 3 in I        # True
assert 6 not in I    # True
```

### `P.open(lower, upper)` → `Interval`
Creates an open interval `(lower, upper)` — both endpoints excluded.
```python
I = P.open(1, 5)     # (1,5)
assert 1 not in I    # True (open at lower)
assert 5 not in I    # True (open at upper)
assert 3 in I        # True
```

### `P.openclosed(lower, upper)` → `Interval`
Creates a left-open, right-closed interval `(lower, upper]`.
```python
I = P.openclosed(1, 5)  # (1,5]
assert 1 not in I        # True
assert 5 in I            # True
```

### `P.closedopen(lower, upper)` → `Interval`
Creates a left-closed, right-open interval `[lower, upper)`.
```python
I = P.closedopen(1, 5)  # [1,5)
assert 1 in I            # True
assert 5 not in I        # True
```

### `P.singleton(value)` → `Interval`
Creates a singleton interval `[value, value]` containing exactly one point.
```python
I = P.singleton(7)  # [7]
assert 7 in I
assert I.atomic
assert I.lower == 7 and I.upper == 7
```

### `P.empty()` → `Interval`
Creates an empty interval `()` — contains no points.
```python
E = P.empty()
assert E.empty
assert not E.atomic or E.empty
```

---

## 2. Interval Properties

Every `Interval` has these read-only properties:

| Property | Type | Description |
|---|---|---|
| `lower` | value | Lowest lower bound (`inf` if empty) |
| `upper` | value | Highest upper bound (`-inf` if empty) |
| `left` | `Bound` | Left boundary type of the leftmost atomic piece |
| `right` | `Bound` | Right boundary type of the rightmost atomic piece |
| `empty` | bool | True if interval contains no points |
| `atomic` | bool | True if interval is empty or a single atomic piece |
| `enclosure` | `Interval` | Smallest single atomic interval enclosing `self` |

```python
I = P.closed(3, 7)
I.lower  # 3
I.upper  # 7
I.left   # Bound.CLOSED
I.right  # Bound.CLOSED
I.atomic # True

J = P.closed(1, 3) | P.closed(6, 9)
J.lower    # 1
J.upper    # 9
J.atomic   # False
J.enclosure  # [1,9] — the bounding box
```

### `enclosure` property

`enclosure` returns the smallest atomic interval that contains all points of `self`.
For an atomic interval, it returns a copy of itself. For non-atomic intervals, it
"fills the gaps".

```python
I = P.closed(1, 3) | P.closed(6, 9) | P.closed(12, 15)
I.enclosure  # [1,15]

# Always: I <= I.enclosure
# And: I.enclosure.atomic is always True
```

---

## 3. Set Operations

### Union: `a | b`
Returns the union of two intervals. Automatically merges overlapping and
adjacent atomic pieces.

```python
P.closed(1, 5) | P.closed(3, 9)         # [1,9]
P.closed(1, 5) | P.closed(6, 9)         # [1,5] | [6,9]  (disjoint)
P.closedopen(1, 5) | P.closed(5, 9)     # [1,9]  (adjacent, merges because one side is CLOSED)
P.open(1, 5) | P.openclosed(5, 9)       # (1,5) | (5,9]  (stays disjoint, both OPEN at 5)
```

**Adjacency merging rule**: Two atomic intervals `A` and `B` with `A.upper == B.lower`
are merged into a single interval if and only if `A.right == CLOSED or B.left == CLOSED`.
Both being OPEN creates a gap (the shared point belongs to neither).

```python
# Both CLOSED at 5: merges
P.closed(1, 5) | P.closed(5, 9) == P.closed(1, 9)   # True

# One side CLOSED, other OPEN: still merges (the point is covered)
P.closedopen(1, 5) | P.closed(5, 9) == P.closed(1, 9)   # True
P.closed(1, 5) | P.openclosed(5, 9) == P.closed(1, 9)   # True

# Both OPEN at 5: does NOT merge (point 5 is in neither)
P.open(1, 5) | P.open(5, 9)   # (1,5) | (5,9) — two pieces, 5 not in result
```

### Intersection: `a & b`
Returns the intersection of two intervals. The result is empty if there is no overlap.

```python
P.closed(1, 7) & P.closed(4, 10)       # [4,7]
P.open(1, 7) & P.closed(4, 7)          # [4,7)   (OPEN wins at upper)
P.closed(1, 7) & P.open(4, 10)         # (4,7]  (actually [4,7]? No: [4,7])
P.closed(0, 3) & P.closed(5, 8)        # ()     (empty, no overlap)
```

**Boundary selection in intersection**:
When two intervals overlap, the intersection uses the most restrictive (tightest)
boundary at each endpoint:
- At shared lower bound: OPEN wins over CLOSED (OPEN is more restrictive — excludes the point)
- At shared upper bound: OPEN wins over CLOSED

```python
# Equal lower bounds: OPEN wins
P.open(3, 10) & P.closed(3, 7)    # (3,7]  — lower is OPEN (excludes 3)
P.closed(3, 10) & P.open(3, 7)    # (3,7)  — lower is OPEN (excludes 3)

# Equal upper bounds: OPEN wins
P.open(1, 7) & P.closed(4, 7)    # [4,7)  — upper is OPEN (excludes 7)
P.closed(1, 7) & P.open(4, 7)    # [4,7)  — upper is OPEN (excludes 7)
```

### Complement: `~a`
Returns the complement of an interval (all points NOT in `a`). Infinite bounds
are represented with `P.inf` and `-P.inf`.

```python
~P.closed(2, 8)      # (-inf,2) | (8,+inf)
~P.open(2, 8)        # (-inf,2] | [8,+inf)
~P.closedopen(2, 8)  # (-inf,2) | [8,+inf)
~P.openclosed(2, 8)  # (-inf,2] | (8,+inf)
~P.empty()           # (-inf,+inf)
```

**Complement of non-atomic interval**: The complement includes gaps between
atomic pieces. Each gap is an open interval bounded by the endpoints of the
surrounding pieces, with boundary types inverted.

```python
I = P.closed(1, 3) | P.closed(7, 9)
~I  # (-inf,1) | (3,7) | (9,+inf)
# Gap (3,7): OPEN at both ends because:
#   left boundary: ~(right of [1,3]) = ~CLOSED = OPEN
#   right boundary: ~(left of [7,9]) = ~CLOSED = OPEN
```

**De Morgan's Laws** (always hold for correct implementation):
```python
~(a | b) == ~a & ~b   # De Morgan 1
~(a & b) == ~a | ~b   # De Morgan 2
~~a == a               # Double complement identity
```

### Difference: `a - b`
Equivalent to `a & ~b`.
```python
P.closed(1, 10) - P.closed(4, 7)   # [1,4) | (7,10]
P.closed(1, 10) - P.closed(0, 15)  # ()
```

---

## 4. Containment and Comparison

### Value containment: `v in I`
Tests whether a scalar value `v` is contained in interval `I`.
```python
3 in P.closed(1, 5)    # True
1 in P.open(1, 5)      # False (OPEN boundary)
5 in P.open(1, 5)      # False (OPEN boundary)
5 in P.closed(1, 5)    # True  (CLOSED boundary)
```

### Interval containment: `J in I`
Tests whether interval `J` is a subset of interval `I`.
```python
P.closed(2, 4) in P.closed(1, 5)   # True
P.closed(2, 6) in P.closed(1, 5)   # False (6 not in [1,5])
P.empty() in P.closed(1, 5)        # True (empty is subset of everything)
```

**Key rule**: `J in I` iff every point in `J` is also in `I`. In particular:
- If `J.upper == I.upper`, containment at the upper boundary depends on boundary types:
  - `J.right == CLOSED and I.right == OPEN` → `J` includes the endpoint but `I` does not → NOT contained
  - `J.right == CLOSED and I.right == CLOSED` → OK, endpoint included in both → may be contained
  - `J.right == OPEN and I.right == OPEN` → both exclude endpoint → OK
  - `J.right == OPEN and I.right == CLOSED` → `J` excludes endpoint, `I` includes it → OK

```python
P.closed(3, 7) in P.open(1, 7)     # False: 7 in closed(3,7) but 7 not in open(1,7)
P.open(3, 7) in P.open(1, 7)       # True:  open(3,7) excludes 7, open(1,7) excludes 7 too
P.closed(3, 7) in P.closed(1, 7)   # True:  7 in both
```

### Ordering operators
- `a < b`: `a` is entirely to the left of `b` (with boundary sensitivity)
- `a > b`: `a` is entirely to the right of `b`
- `a <= b`: `a`'s right end is at most `b`'s right end (subset-like for atomic)
- `a >= b`: `a`'s left end is at most `b`'s left end

---

## 5. Iteration with `portion.func.iterate`

### `iterate(interval, step, *, base=None, reverse=False)` → iterator

Yields discrete values from an interval with a given step between consecutive values.

```python
from portion.func import iterate

list(iterate(P.closed(1, 5), 1))        # [1, 2, 3, 4, 5]
list(iterate(P.closedopen(1, 5), 1))    # [1, 2, 3, 4]      (5 excluded: OPEN)
list(iterate(P.openclosed(1, 5), 1))    # [2, 3, 4, 5]      (1 excluded: OPEN)
list(iterate(P.open(1, 5), 1))          # [2, 3, 4]         (both excluded)

# With a float step
list(iterate(P.closed(0, 1), 0.25))     # [0.0, 0.25, 0.5, 0.75, 1.0]

# Reverse iteration (requires negative step)
list(iterate(P.closed(1, 5), -1, reverse=True))  # [5, 4, 3, 2, 1]
```

**Boundary contract**: `iterate` strictly respects the interval's boundary types:
- For a CLOSED endpoint: the endpoint value IS yielded (included in iteration)
- For an OPEN endpoint: the endpoint value is NOT yielded (excluded from iteration)

```python
# CLOSED upper: last value equals upper bound
list(iterate(P.closed(1, 5), 1))[-1] == 5     # True

# OPEN upper: last value is strictly less than upper bound
list(iterate(P.closedopen(1, 5), 1))[-1] == 4  # True

# Singleton [3,3]: iterate should yield exactly [3]
list(iterate(P.singleton(3), 1)) == [3]        # True
```

**Non-atomic intervals**: When the interval has multiple atomic pieces, iteration
chains through each piece in order.
```python
I = P.closed(1, 3) | P.closed(7, 9)
list(iterate(I, 1))   # [1, 2, 3, 7, 8, 9]
```

---

## 6. `Interval.replace()` and `Interval.apply()`

### `replace(left=None, lower=None, upper=None, right=None)` → `Interval`
Creates a modified copy of the interval with selected bounds replaced.
```python
P.closed(1, 10).replace(left=P.Bound.OPEN)       # (1,10]
P.closed(1, 10).replace(lower=0)                  # [0,10]
P.closed(1, 10).replace(upper=lambda u: u * 2)    # [1,20]
```

### `apply(func)` → `Interval`
Applies a function to each atomic piece and returns the union.
```python
I = P.closed(1, 3) | P.closed(7, 9)
I.apply(lambda a: (a.left, a.lower * 2, a.upper * 2, a.right))
# [2,6] | [14,18]
```

---

## 7. `IntervalDict`

An `IntervalDict` maps intervals (as keys) to arbitrary values. Multiple intervals
can cover the same value, and overlapping insertions are automatically handled.

### Construction
```python
d = P.IntervalDict()
d[P.closed(0, 5)] = "a"
d[P.closed(3, 8)] = "b"   # Overwrites [3,5] portion of "a"
# d now has: {[0,3): "a", [3,5]: "b", (5,8]: "b"}  (simplified)
# Wait: actually "b" extends from 3 to 8, overwriting any existing
```

Or from a mapping:
```python
d = P.IntervalDict({
    P.closed(0, 5): 10,
    P.closed(7, 10): 20,
})
d[3]   # 10 (value lookup by scalar)
d[8]   # 20
```

### Methods

**`domain()`** → `Interval`
Returns the union of all key intervals (the set of defined values).
```python
d.domain()   # [0,5] | [7,10]
```

**`combine(other, how, *, missing=..., pass_interval=False)`** → `IntervalDict`
Merges two IntervalDicts using a combining function `how(v1, v2)`.

```python
d1 = P.IntervalDict({P.closed(0, 5): 10})
d2 = P.IntervalDict({P.closed(3, 8): 5})

# Without missing: keys exclusive to one side are kept as-is
result = d1.combine(d2, lambda x, y: x + y)
# [0,3): 10 (only d1), [3,5]: 15 (both), (5,8]: 5 (only d2)

# With missing=0: exclusive keys are processed through how() too
result = d1.combine(d2, lambda x, y: x + y, missing=0)
# [0,3): 10+0=10, [3,5]: 10+5=15, (5,8]: 0+5=5
```

The `missing` parameter specifies the "fill" value used for keys that exist
in only one of the two dicts. Convention:
- For keys in `self` but not in `other`: `how(value_from_self, missing, interval)`
- For keys in `other` but not in `self`: `how(missing, value_from_other, interval)`

This ordering matters for asymmetric functions:
```python
d1 = P.IntervalDict({P.closed(0, 3): 10})
d2 = P.IntervalDict({P.closed(2, 6): 5})
sub = lambda x, y: x - y

# d1-exclusive [0,2): how(10, missing=0) = 10 - 0 = 10
# intersection [2,3]: how(10, 5) = 10 - 5 = 5
# d2-exclusive (3,6]: how(missing=0, 5) = 0 - 5 = -5
result = d1.combine(d2, sub, missing=0)
```

**`find(value)`** → `Interval`
Returns the interval of all keys mapping to `value`.
```python
d = P.IntervalDict({P.closed(1, 5): "x", P.closed(7, 9): "y"})
d.find("x")   # [1,5]
d.find("z")   # ()  (empty, not found)
```

**`as_dict(atomic=False)`** → `dict`
Returns contents as a plain Python dict. If `atomic=True`, all keys are atomic intervals.

---

## 8. Algebraic Properties (Reference for PBT)

The following identities should hold for all well-formed intervals A, B, C:

### Boolean algebra (set identities)
```
Commutativity:       A | B == B | A
                     A & B == B & A
Associativity:       (A | B) | C == A | (B | C)
                     (A & B) & C == A & (B & C)
Distributivity:      A & (B | C) == (A & B) | (A & C)
                     A | (B & C) == (A | B) & (A | C)
Idempotency:         A | A == A
                     A & A == A
Absorption:          A | (A & B) == A
                     A & (A | B) == A
De Morgan:           ~(A | B) == ~A & ~B
                     ~(A & B) == ~A | ~B
Double complement:   ~~A == A
Complement laws:     A | ~A == P.open(-P.inf, P.inf)  (the "universe")
                     A & ~A == P.empty()
```

### Containment properties
```
A <= A.enclosure                   # self is contained in its enclosure
A.enclosure.atomic == True         # enclosure is always atomic
A <= B iff (A | B) == B            # subset relation
(A & B) <= A and (A & B) <= B     # intersection is subset of both
A <= (A | B) and B <= (A | B)     # both are subsets of their union
```

### Iteration properties
```python
# All yielded values must be in the interval
for v in iterate(I, 1):
    assert v in I

# Number of values in closed integer interval:
len(list(iterate(P.closed(a, b), 1))) == b - a + 1

# Open endpoints excluded:
upper not in list(iterate(P.closedopen(lower, upper), 1))
lower not in list(iterate(P.openclosed(lower, upper), 1))
```

---

## 9. The `Bound` Enum

```python
from portion import Bound

Bound.CLOSED  # inclusive endpoint (value is contained)
Bound.OPEN    # exclusive endpoint (value is NOT contained)

# Complement of a bound:
~Bound.CLOSED == Bound.OPEN    # True
~Bound.OPEN == Bound.CLOSED    # True

# Bound has no truth value (use == comparison):
bool(Bound.CLOSED)  # raises ValueError
```

---

## 10. Working with Infinity

```python
import portion as P

P.inf          # positive infinity
-P.inf         # negative infinity

# Half-infinite intervals
P.closed(0, P.inf)   # [0, +inf)  — automatically OPEN at infinity
P.open(-P.inf, 5)    # (-inf, 5)

# Complement of a closed interval gives half-infinite intervals
~P.closed(1, 5)      # (-inf,1) | (5,+inf)
```

---

## 11. Common Patterns and Pitfalls

### Boundary type matters for containment
```python
5 in P.closed(1, 5)   # True  (CLOSED includes the endpoint)
5 in P.open(1, 5)     # False (OPEN excludes the endpoint)
5 in P.openclosed(1, 5)  # True
5 in P.closedopen(1, 5)  # False
```

### Intersection priority: OPEN wins
When two overlapping intervals are intersected at a shared boundary point:
- If one has OPEN and the other CLOSED at that point, the result is OPEN
- The more restrictive (exclusive) boundary always wins in intersection
```python
P.open(0, 5) & P.closed(2, 5)   # [2,5)  — upper is OPEN
P.closed(3, 5) & P.open(3, 10)  # (3,5]  — lower is OPEN
```

### Union priority: CLOSED wins
When two overlapping intervals are unioned and they share a lower or upper bound:
- If one has CLOSED and the other OPEN, the result is CLOSED
- The more inclusive boundary always wins in union
```python
P.open(3, 8) | P.closed(3, 5)   # [3,8]  — lower becomes CLOSED
P.closed(1, 5) | P.open(1, 8)   # [1,8]  — lower stays CLOSED
```

### Complement inverts boundary types
```python
~P.closed(1, 5)      # (-inf,1) | (5,+inf)   — boundaries become OPEN
~P.open(1, 5)        # (-inf,1] | [5,+inf)   — boundaries become CLOSED
~P.closedopen(1, 5)  # (-inf,1) | [5,+inf)   — mixed: left was CLOSED→OPEN, right was OPEN→CLOSED
```
