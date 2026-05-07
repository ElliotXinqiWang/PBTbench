# intervaltree 3.1.0 — API Documentation

## Overview

`intervaltree` is a mutable, self-balancing interval tree implementation for Python.
Intervals are half-open: `[begin, end)`. An `Interval(1, 5)` contains points 1, 2, 3, 4 but not 5.

## Installation

```
pip install intervaltree==3.1.0
```

## Core Classes

### `Interval(begin, end, data=None)`

An immutable half-open interval `[begin, end)`.

- `begin`: The inclusive lower bound
- `end`: The exclusive upper bound
- `data`: Optional arbitrary data attached to the interval
- An interval is "null" if `begin == end` (null intervals are not allowed in IntervalTree)
- `iv.contains_point(p)`: True iff `begin <= p < end`

### `IntervalTree`

A mutable, ordered set of `Interval` objects.

```python
from intervaltree import IntervalTree, Interval
t = IntervalTree()
t.addi(1, 5, 'hello')    # same as t.add(Interval(1, 5, 'hello'))
```

## Modifying the Tree

### `add(interval)` / `addi(begin, end, data=None)` / `append` / `appendi`

Add an interval to the tree. Duplicates are ignored. Null intervals raise `ValueError`.

### `remove(interval)`

Remove the interval; raise `ValueError` if not found.

### `discard(interval)`

Remove the interval if present, do nothing otherwise.

### `update(intervals)`

Add all intervals from an iterable.

## Point and Range Queries

### `at(p)`

Returns a set of all intervals `[a, b)` containing point `p`, i.e., `a <= p < b`.

**Important**: An interval `[a, b)` IS returned by `at(a)` — the begin point is inclusive.
`at(b)` does NOT return `[a, b)` — the end point is exclusive.

```python
t = IntervalTree.from_tuples([(1, 5), (3, 8)])
t.at(1)  # {Interval(1, 5)} — begin is inclusive
t.at(5)  # {Interval(3, 8)} — 5 is not in [1,5) but is in [3,8)
t.at(8)  # {} — end is exclusive
```

### `overlap(begin, end)` / `overlap(interval)`

Returns all intervals overlapping the range `[begin, end)`.
Two intervals overlap if they share at least one point.

```python
t.overlap(2, 4)  # all intervals [a, b) where a < 4 and b > 2
```

### `overlaps(begin, end=None)` / `overlaps(point)`

Returns `True` if any interval in the tree overlaps the given point or range.

### `overlaps_point(p)`

Returns `True` if any interval contains point `p`.

### `overlaps_range(begin, end)`

Returns `True` if any interval overlaps the range `[begin, end)`.
Returns `False` if `begin >= end`.

### `envelop(begin, end)` / `envelop(interval)`

Returns all intervals **fully contained** within `[begin, end)`.
An interval `[a, b)` is enveloped by `[begin, end)` iff `begin <= a` and `b <= end`.

**Important**: The begin boundary is inclusive — `envelop(a, b)` includes interval `[a, x)` where `x <= b`.

```python
t = IntervalTree.from_tuples([(2, 5), (1, 8), (3, 6)])
t.envelop(2, 6)  # {Interval(2, 5), Interval(3, 6)} — NOT Interval(1, 8) since 1 < 2
```

## Merging Operations

### `merge_overlaps(data_reducer=None, data_initializer=None, strict=True)`

Merges overlapping intervals. With `strict=True` (default), touching intervals are NOT merged.
With `strict=False`, touching intervals (end of one == begin of next) ARE merged.

### `merge_equals(data_reducer=None, data_initializer=None)`

Merges intervals with identical ranges `[a, b)`.

### `merge_neighbors(data_reducer=None, data_initializer=None, distance=1, ...)`

Merges intervals within `distance` of each other.

## Tree Properties

### `begin()`, `end()`

Return the minimum begin and maximum end of all intervals. Return 0 for empty tree.

### `span()`

Returns `end() - begin()` (0 for empty tree).

### `range()`

Returns a minimum-spanning `Interval(begin(), end())`.

### `is_empty()`

Returns `True` if the tree contains no intervals.

## Internal: `boundary_table`

The tree maintains a `boundary_table` dict mapping each endpoint value to its reference count
(how many intervals have that point as a begin or end). This is used internally for efficient queries.
After adding interval `[a, b)`, `boundary_table[a] += 1` and `boundary_table[b] += 1`.
After removing interval `[a, b)`, both counts are decremented (and the key deleted if count reaches 0).

## Half-Open Interval Semantics

All intervals are `[begin, end)`:
- `at(p)` returns intervals where `begin <= p < end`
- `overlap(a, b)` returns intervals `[x, y)` where `x < b and y > a`
- `envelop(a, b)` returns intervals `[x, y)` where `x >= a and y <= b`

Boundary points:
- Begin (`begin`) is INCLUSIVE in all queries
- End (`end`) is EXCLUSIVE in all queries
