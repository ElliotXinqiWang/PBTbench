# portion — Interval and IntervalDict API Reference

`portion` (version 2.6.1) is a Python library providing data types and operations for intervals
and interval dictionaries.

## Core Interval Types

Intervals are created using factory functions:

```python
import portion as P

P.closed(0, 10)       # [0, 10]  — both endpoints included
P.open(0, 10)         # (0, 10)  — both endpoints excluded
P.closedopen(0, 10)   # [0, 10)  — lower included, upper excluded
P.openclosed(0, 10)   # (0, 10]  — lower excluded, upper included
P.singleton(5)        # [5, 5]   — a single point
P.empty()             # ()       — the empty interval
```

Boundary types are represented by `portion.Bound.CLOSED` and `portion.Bound.OPEN`.

## Interval Properties

- `.lower` / `.upper`: lower and upper bound values
- `.left` / `.right`: boundary type (`Bound.CLOSED` or `Bound.OPEN`) at each end
- `.empty`: `True` if the interval contains no points
- `.atomic`: `True` if the interval is a single contiguous piece (not a union of disjoint parts)
- `.enclosure`: the smallest single atomic interval enclosing all pieces of a non-atomic interval

## Interval Operations

### Union (`|`)

```python
P.closed(1, 3) | P.closed(5, 7)     # [1,3] | [5,7]  — disjoint union
P.closed(1, 5) | P.closed(3, 8)     # [1,8]           — overlapping, merges into one
```

**Boundary semantics for union**: When merging overlapping intervals, the union **includes** an
endpoint if either of the merged intervals includes it. For closed/open conflicts at a shared
endpoint, the CLOSED (inclusive) bound takes precedence.

**Adjacency merging**: Two intervals are merged in a union if they overlap OR if they are
adjacent at a shared point with at least one side being CLOSED. For example:
- `P.closedopen(1, 5) | P.closed(5, 9)` → `[1, 9]` (OPEN right meets CLOSED left at 5 → merged)
- `P.closed(1, 5) | P.openclosed(5, 9)` → `[1, 9]` (CLOSED right meets OPEN left at 5 → merged)
- `P.open(1, 5) | P.open(5, 9)` → `(1,5) | (5,9)` (both OPEN at 5 → NOT merged, gap remains)

### Intersection (`&`)

```python
P.closed(1, 7) & P.closed(4, 10)    # [4,7]
P.open(0, 5) & P.closed(2, 10)      # [2,5)  — OPEN boundary from left operand wins
```

**Boundary semantics for intersection**: When two intervals share the same upper bound value,
the intersection **excludes** the endpoint if either operand excludes it. For closed/open
conflicts at a shared upper bound, the OPEN (exclusive) bound takes precedence. Similarly,
for a shared lower bound, OPEN takes precedence.

Examples:
- `P.open(0, 5) & P.closed(2, 5)` → `[2, 5)` — shared upper bound 5: OPEN wins, 5 excluded
- `P.closed(0, 5) & P.open(2, 5)` → `[2, 5)` — shared upper bound 5: OPEN wins, 5 excluded
- `P.closed(5, 10) & P.open(5, 8)` → `(5, 8)` — shared lower bound 5: OPEN wins, 5 excluded

### Complement (`~`)

```python
~P.closed(0, 5)         # (-inf,0) | (5,+inf)
~P.open(0, 5)           # (-inf,0] | [5,+inf)
```

The complement of a CLOSED endpoint becomes OPEN, and vice versa.

### Difference (`-`)

```python
P.closed(0, 10) - P.closed(3, 7)    # [0,3) | (7,10]
```

### De Morgan's Laws

These algebraic identities always hold for interval operations:

```python
~(A | B) == ~A & ~B
~(A & B) == ~A | ~B
```

### Containment (`in`)

```python
5 in P.closed(1, 10)      # True  — 5 is strictly inside
1 in P.closed(1, 10)      # True  — 1 is the CLOSED lower bound
1 in P.open(1, 10)        # False — 1 is the OPEN lower bound (excluded)
10 in P.closed(1, 10)     # True  — 10 is the CLOSED upper bound
10 in P.open(1, 10)       # False — 10 is the OPEN upper bound (excluded)
```

## IntervalDict

`IntervalDict` is a dict-like structure that maps `Interval` keys to arbitrary values.
Keys can be `Interval` instances (returns an `IntervalDict` slice) or single values
(returns a single value with `KeyError` if not found).

### Creation

```python
d = P.IntervalDict({
    P.closed(0, 5): "low",
    P.closed(6, 10): "high",
})
```

### Access

```python
d[3]                       # "low"  — single value lookup
d[P.closed(2, 7)]          # IntervalDict slice restricted to [2,7]
d.domain()                 # Interval: the union of all keys
d.get(3, default="none")   # value or default
```

### combine()

```python
result = d1.combine(d2, how, *, missing=..., pass_interval=False)
```

`combine` merges two IntervalDicts using a combining function `how(x, y)`.

The result contains three types of regions:

1. **`d1`-exclusive** (`dom1 - dom2`): intervals in `d1` not covered by `d2`
2. **`d2`-exclusive** (`dom2 - dom1`): intervals in `d2` not covered by `d1`
3. **Intersection** (`dom1 & dom2`): intervals covered by both

**When `missing` is `Ellipsis` (default)**: Exclusive regions are kept as-is (no `how` call).
Only the intersection region applies `how(v1, v2)`.

**When `missing` is set to a value `m`**:
- `d1`-exclusive region: applies `how(v1, m)` — d1's value is first argument, missing is second
- `d2`-exclusive region: applies `how(m, v2)` — missing is first argument, d2's value is second
- Intersection region: applies `how(v1, v2)` as usual

This parameter ordering is consistent with the docstring: `f(x, missing)` for d1-only
and `f(missing, y)` for d2-only.

```python
d1 = P.IntervalDict({P.closed(0, 2): 10})
d2 = P.IntervalDict({P.closed(1, 3): 5})

# With asymmetric how and missing:
result = d1.combine(d2, lambda x, y: x - y, missing=0)
# [0,1): how(10, 0) = 10    — d1-exclusive: d1 value - missing
# [1,2]: how(10, 5) = 5     — intersection
# (2,3]: how(0, 5)  = -5    — d2-exclusive: missing - d2 value
```

**Symmetric functions** (e.g., addition `lambda x,y: x+y`) produce the same result
regardless of argument order, so the `missing` parameter ordering is irrelevant for them.
**Asymmetric functions** (e.g., subtraction, division) depend critically on argument order.

### Other IntervalDict methods

```python
d.find(value)              # returns Interval where d[i] == value
d.items()                  # sorted (interval, value) pairs
d.keys()                   # sorted intervals
d.values()                 # values in key order
d.domain()                 # union of all key intervals
d.copy()                   # shallow copy
d | other                  # union (other overwrites overlapping d keys)
```

## Interval Iteration

Non-atomic intervals (unions of disjoint pieces) can be iterated to get each atomic piece:

```python
I = P.closed(1, 3) | P.closed(6, 9)
for atomic in I:
    print(atomic)   # prints [1,3] then [6,9]
```

Indexing also works: `I[0]` returns the first atomic piece, `I[-1]` the last.

## apply()

```python
I.apply(func)
```

Applies a function to each atomic piece of the interval and returns their union.
`func` must return an `Interval` instance or a 4-tuple `(left, lower, upper, right)`.

```python
I = P.closed(1, 5) | P.closed(8, 10)
I.apply(lambda a: P.closed(a.lower * 2, a.upper * 2))
# Result: [2,10] | [16,20]
```

## replace()

```python
I.replace(left=None, lower=None, upper=None, right=None, ignore_inf=True)
```

Creates a new interval by replacing specified attributes of the current interval's enclosure.
Can accept callables that receive the current value.

```python
P.closed(2, 8).replace(lower=1)              # [1,8]
P.closed(2, 8).replace(right=Bound.OPEN)     # [2,8)
P.closed(2, 8).replace(lower=lambda x: x-1) # [1,8]
```
