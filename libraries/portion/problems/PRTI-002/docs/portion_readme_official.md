# portion 2.6.1 — Official README & API Documentation

Sources:
- https://github.com/AlexandreDecan/portion (README)
- https://pypi.org/project/portion/2.6.1/

---

## Overview

The `portion` library is a Python package that provides data structures and operations for working with intervals. It supports intervals of any comparable objects with features including:

- Closed/open and finite/infinite interval support
- Atomic interval unions with automatic simplification
- Set operations (intersection, union, complement, difference)
- Containment testing and adjacency checks
- Discrete iteration capabilities
- Dict-like interval-to-data mapping (`IntervalDict`)
- String import/export functionality

## Installation

```
pip install portion
```

Development dependencies (pytest, ruff): `pip install --group dev`

---

## Interval Creation

Core creation functions:

| Function | Description | Notation |
|----------|-------------|----------|
| `P.closed(a, b)` | Both endpoints included | `[a, b]` |
| `P.open(a, b)` | Both endpoints excluded | `(a, b)` |
| `P.openclosed(a, b)` | Left open, right closed | `(a, b]` |
| `P.closedopen(a, b)` | Left closed, right open | `[a, b)` |
| `P.singleton(x)` | Single-point interval | `[x, x]` |
| `P.empty()` | Empty interval | `()` |

Bounds may be any comparable type (numbers, strings, dates). Infinity is supported via `P.inf` and `-P.inf`, which automatically convert boundaries to open form.

```python
import portion as P

P.closed(0, 2)          # [0, 2]
P.open(0, 2)            # (0, 2)
P.openclosed(0, 2)      # (0, 2]
P.closedopen(0, 2)      # [0, 2)
P.singleton(1)          # [1, 1]
P.empty()               # ()
P.closed(-P.inf, P.inf) # (-inf, +inf)  — inf forces open boundary
```

---

## Boundary Constants (Bound Enum)

The `P.CLOSED` and `P.OPEN` constants represent boundary types:

- `P.CLOSED` — the endpoint is included in the interval
- `P.OPEN` — the endpoint is excluded from the interval
- By definition: `P.CLOSED == ~P.OPEN` (they are complementary)

```python
P.closed(0, 1).left   # P.CLOSED
P.open(0, 1).left     # P.OPEN
P.closed(0, 1).right  # P.CLOSED
~P.CLOSED             # P.OPEN
~P.OPEN               # P.CLOSED
```

---

## Interval Properties

Every interval exposes these attributes:

| Attribute | Description |
|-----------|-------------|
| `i.empty` | `True` if interval contains no elements |
| `i.atomic` | `True` if empty or single contiguous interval |
| `i.enclosure` | Smallest atomic interval containing it |
| `i.left` | Left boundary type (`CLOSED` or `OPEN`) |
| `i.right` | Right boundary type (`CLOSED` or `OPEN`) |
| `i.lower` | Lower bound value |
| `i.upper` | Upper bound value |

For non-atomic intervals (unions), `left`/`right`/`lower`/`upper` refer to the enclosure's extremes.

```python
i = P.closed(0, 2)
i.left    # P.CLOSED
i.lower   # 0
i.upper   # 2
i.right   # P.CLOSED
i.atomic  # True
i.empty   # False
```

---

## Containment Testing (`__contains__` / `in` operator)

The `in` operator tests whether a value (or another interval) is contained within the interval.

```python
2 in P.closed(0, 2)     # True  — 2 is the closed right endpoint
2 in P.open(0, 2)       # False — 2 is the open right endpoint (excluded)
0 in P.closed(0, 2)     # True  — 0 is the closed left endpoint
0 in P.open(0, 2)       # False — 0 is the open left endpoint (excluded)
1 in P.closed(0, 2)     # True  — 1 is strictly inside
```

Interval containment (checking if one interval is a subset of another):

```python
P.open(0, 1) in P.closed(0, 2)    # True
P.closed(0, 1) in P.open(0, 2)    # False — left boundary mismatch
P.closed(0, 2) in P.closed(0, 2)  # True  — equal intervals
```

### Containment Logic for Atomic Intervals

For a value `x` to be contained in an atomic interval `[l, u]` (or variants), the following must hold:

- **Left boundary check:**
  - If `left == CLOSED`: `x >= lower` (inclusive)
  - If `left == OPEN`: `x > lower` (exclusive)
- **Right boundary check:**
  - If `right == CLOSED`: `x <= upper` (inclusive)
  - If `right == OPEN`: `x < upper` (exclusive)

Both conditions must be satisfied simultaneously.

---

## Set Operations

```python
# Intersection
P.closed(0, 2) & P.closed(1, 3)     # [1, 2]
P.closed(0, 2).intersection(P.closed(1, 3))  # same

# Union (automatically simplifies overlapping/adjacent)
P.closed(0, 1) | P.closed(1, 3)     # [0, 3]
P.closed(0, 1).union(P.closed(2, 3))  # [0, 1] | [2, 3]

# Complement
~P.closed(0, 1)                      # (-inf, 0) | (1, +inf)

# Difference
P.closed(0, 3) - P.closed(1, 2)     # [0, 1) | (2, 3]
P.closed(0, 3).difference(P.closed(1, 2))  # same

# Overlap test
P.closed(0, 2).overlaps(P.closed(1, 3))   # True
P.closed(0, 1).overlaps(P.open(1, 2))     # False

# Adjacency test
P.closed(0, 1).adjacent(P.open(1, 2))     # True
```

---

## Comparison Operators

Comparisons follow specialized interval semantics:

- `a < b`: all values in `a` are strictly less than all values in `b`
- `a <= b`: `a` is a subset of `b` (subset containment)
- `a > b`: all values in `a` are strictly greater than all values in `b`
- `a >= b`: `a` is a superset of `b`

```python
P.closed(0, 1) < P.closed(2, 3)    # True
P.closed(0, 1) <= P.closed(0, 2)   # True  (subset)
```

---

## Interval Iteration

Intervals are iterable, yielding atomic intervals in sorted order:

```python
list(P.closed(0,1) | P.open(2,3))  # [P.closed(0,1), P.open(2,3)]
```

Indexing and slicing are supported:

```python
i = P.closed(0,1) | P.open(2,3)
i[0]    # P.closed(0, 1)
i[-1]   # P.open(2, 3)
```

---

## Interval Transformation

### `replace()`

Creates a modified interval by changing specific attributes:

```python
P.closed(0, 2).replace(upper=3)              # [0, 3]
P.closed(0, 2).replace(left=P.OPEN)          # (0, 2]
P.closed(0, 2).replace(lower=lambda v: v+1)  # [1, 2]
```

### `apply()`

Works like `map`, applying a function to each atomic interval:

```python
P.closed(0, 2).apply(lambda i: i.replace(upper=i.upper * 2))  # [0, 4]
```

---

## Discrete Iteration with `P.iterate()`

Generates values across an interval with a specified step:

```python
list(P.iterate(P.closed(0, 3), step=1))          # [0, 1, 2, 3]
list(P.iterate(P.open(0, 3), step=1))             # [1, 2]
list(P.iterate(P.closed(0, 3), step=1, reverse=True))  # [3, 2, 1, 0]
```

---

## IntervalDict

Maps intervals to data, like a dictionary keyed on intervals:

```python
d = P.IntervalDict()
d[P.closed(0, 3)] = 'low'
d[P.closed(3, 6)] = 'mid'

d[2]                  # 'low'
d[P.closed(1, 4)]     # IntervalDict({[1, 3]: 'low', (3, 4]: 'mid'})
d.domain()            # [0, 6]
```

Methods:

- `.find(value)` — returns the interval key containing `value`
- `.domain()` — returns the union of all keys
- `.combine(other, how)` — merges two IntervalDicts with a combining function

---

## String Import/Export

```python
# Export
str(P.closed(0, 2))                   # '[0, 2]'
P.to_string(P.closed(0, 2))           # '[0, 2]'

# Import
P.from_string('[0, 2]', conv=int)     # P.closed(0, 2)
```

Custom separators and boundary symbols are supported.

---

## Data Serialization

```python
# Export to list of 4-tuples (JSON-compatible)
P.to_data(P.closed(0, 2))
# [(P.CLOSED, 0, 2, P.CLOSED)]  — or with int encoding

# Reconstruct from tuples
P.from_data([(P.CLOSED, 0, 2, P.CLOSED)])
# [0, 2]
```

---

## Discrete Interval Subclasses

For domains like integers where adjacent intervals should be merged automatically:

```python
class IntInterval(P.AbstractDiscreteInterval):
    _step = 1

IInterval = P.create_api(IntInterval)
IInterval.closed(0, 1) | IInterval.closed(2, 3)
# [0, 3]  — automatically merged because they are adjacent with step=1
```

---

## Key Design Principles

1. **Immutability**: Interval objects are immutable and hashable (if bounds are hashable).
2. **Automatic simplification**: Overlapping or adjacent intervals are automatically merged on union.
3. **Infinity handling**: `P.inf` and `-P.inf` always force open boundaries.
4. **Type flexibility**: Any comparable type can be used as interval bounds.
