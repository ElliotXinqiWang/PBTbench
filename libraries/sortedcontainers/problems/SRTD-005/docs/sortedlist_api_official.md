# sortedcontainers 2.4.0 — SortedList API Reference (Official Documentation)

Source: http://www.grantjenks.com/docs/sortedcontainers/sortedlist.html

---

## Overview

`SortedList` is a mutable sequence from the Sorted Containers library (Apache2 licensed) that automatically maintains values in sorted order. The implementation uses pure Python with performance comparable to C-extensions.

Key invariants guaranteed by the documentation:
- "Sorted list values are maintained in sorted order"
- "Values must be comparable. The total ordering of values must not change while they are stored in the sorted list."
- All indexing operations (`__getitem__`, `pop`, `index`) behave consistently with the logical sorted order.
- `bisect_left(x)` returns the leftmost index where `x` could be inserted while keeping the list sorted; `bisect_right(x)` returns the rightmost such index.

---

## Internal Structure

SortedList uses a list-of-lists (B-tree-like) internal structure:
- Elements are stored in `_lists`, a list of sorted sublists.
- `_maxes` stores the maximum element of each sublist. All binary searches on the overall list first consult `_maxes` to find the right sublist, then search within that sublist.
- When a sublist exceeds `2 * DEFAULT_LOAD_FACTOR` elements it is split into two halves. `DEFAULT_LOAD_FACTOR = 1000` by default, so the split fires when a single sublist reaches 2001 elements.
- A positional B-tree index (`_index`) is maintained for O(log n) indexing when there are multiple sublists. It stores cumulative sublist lengths and is updated incrementally on adds/removes to avoid full rebuilds.

---

## Adding Values

### `add(value)`

Inserts a single value while maintaining sort order.

- Runtime: O(log n) approximate
- The list remains sorted after every `add()` call.

```python
from sortedcontainers import SortedList
sl = SortedList()
sl.add(3)
sl.add(1)
sl.add(2)
# sl is now SortedList([1, 2, 3])
```

Adding values out of order results in the same sorted list:

```python
sl = SortedList()
sl.add(5)
sl.add(1)
sl.add(3)
# sl is now SortedList([1, 3, 5])
```

### `update(iterable)`

Adds multiple values from an iterable while maintaining sort order.

- Runtime: O(k·log n) approximate, where k is the number of items added

```python
sl = SortedList([1, 2, 3])
sl.update([4, 5, 6])
# sl is now SortedList([1, 2, 3, 4, 5, 6])
```

---

## Removing Values

### `remove(value)`

Removes `value` from the list. Raises `ValueError` if not present.

- Runtime: O(log n) approximate

```python
sl = SortedList([1, 2, 3, 4, 5])
sl.remove(3)
# sl is now SortedList([1, 2, 4, 5])
```

After any `remove()` call:
- `list(sl)` must equal `sorted(original_elements - {removed_value})`
- All index-based operations remain consistent with the new logical order

### `discard(value)`

Removes `value` if present; silently ignores if absent.

- Runtime: O(log n) approximate

### `pop(index=-1)`

Removes and returns the value at the given index (default: last element). Negative indices are supported.

- Runtime: O(log n) approximate
- `pop(i)` must return `list(sl)[i]` before the pop

```python
sl = SortedList([1, 2, 3, 4, 5])
sl.pop()     # returns 5
sl.pop(0)    # returns 1
sl.pop(-2)   # returns the second-to-last element
```

---

## Lookup / Search Operations

### `__getitem__(index)` — `sl[index]`

Retrieves the value at the given index. Supports both positive and negative indices, and slicing.

- Runtime: O(log n) for single-element access

```python
sl = SortedList([10, 20, 30, 40, 50])
sl[0]   # 10
sl[-1]  # 50
sl[2]   # 30
```

The element at index `i` must always equal the `i`-th element of `sorted(list(sl))`.

### `bisect_left(value)` — insertion point before equal values

Returns the index at which `value` should be inserted to keep the list sorted, placing the insertion point **before** any existing occurrences of `value`.

- Runtime: O(log n) approximate
- For `value` already present in the list: `sl[sl.bisect_left(value)] == value`
- `bisect_left(value) <= bisect_right(value)` always holds

```python
sl = SortedList([10, 20, 20, 30, 40])
sl.bisect_left(20)   # returns 1 — points to first occurrence of 20
sl.bisect_left(25)   # returns 3 — between 20 and 30
sl.bisect_left(10)   # returns 0 — points to first occurrence of 10
```

Key property: `sl[sl.bisect_left(x)] == x` whenever `x` is present in `sl`.

### `bisect_right(value)` — insertion point after equal values

Returns the index at which `value` should be inserted to keep the list sorted, placing the insertion point **after** any existing occurrences of `value`.

- Also available as `bisect(value)` (alias for `bisect_right`)
- Runtime: O(log n) approximate

```python
sl = SortedList([10, 20, 20, 30, 40])
sl.bisect_right(20)  # returns 3 — after the last occurrence of 20
sl.bisect_right(25)  # returns 3 — same as bisect_left for absent values
```

Key relationship: `bisect_right(x) - bisect_left(x) == count(x)` for any `x`.

### `count(value)`

Returns the number of occurrences of `value`.

- Runtime: O(log n) approximate

```python
sl = SortedList([1, 2, 2, 3])
sl.count(2)  # returns 2
sl.count(4)  # returns 0
```

### `__contains__(value)` — `value in sl`

Returns `True` if `value` is in the list.

- Runtime: O(log n)

### `index(value, start=None, stop=None)`

Returns the first index of `value` within `[start, stop)`. Raises `ValueError` if not found.

- Runtime: O(log n)

---

## Iteration

### `irange(minimum=None, maximum=None, inclusive=(True, True), reverse=False)`

Returns an iterator over values in `[minimum, maximum]` (or open/half-open intervals depending on `inclusive`).

- `inclusive` is a pair of booleans: `(include_minimum, include_maximum)`
- Default: `(True, True)` — both endpoints included
- When `inclusive[0] = False`: the minimum value itself is excluded
- When `inclusive[1] = False`: the maximum value itself is excluded
- `reverse=True`: yields values in descending order
- Runtime: O(log n + k) where k is the number of elements in range

```python
sl = SortedList([1, 2, 3, 4, 5])

list(sl.irange(2, 4))                           # [2, 3, 4]
list(sl.irange(2, 4, inclusive=(False, True)))  # [3, 4]
list(sl.irange(2, 4, inclusive=(True, False)))  # [2, 3]  — 4 excluded
list(sl.irange(2, 4, inclusive=(False, False))) # [3]
list(sl.irange(2, 4, reverse=True))             # [4, 3, 2]
```

The semantics are:
- `inclusive=(True, False)`: yields all values `v` such that `minimum <= v < maximum`
- `inclusive=(False, True)`: yields all values `v` such that `minimum < v <= maximum`
- `inclusive=(False, False)`: yields all values `v` such that `minimum < v < maximum`

When `minimum=None`, iteration starts from the smallest element.
When `maximum=None`, iteration continues to the largest element.

### `islice(start=None, stop=None, reverse=False)`

Returns an iterator that slices the sorted list by index range.

- `start` is inclusive (default: beginning of list)
- `stop` is exclusive (default: end of list)
- Runtime: O(log n + k)

```python
sl = SortedList([1, 2, 3, 4, 5])
list(sl.islice(1, 4))           # [2, 3, 4]
list(sl.islice(1, 4, reverse=True))  # [4, 3, 2]
```

### `__iter__()` and `__reversed__()`

Iterate over all elements in sorted order or reverse sorted order respectively.

---

## Consistency Invariants (from documentation)

The following invariants must hold at all times:

1. **Sorted order**: `list(sl)` is always sorted in ascending order.
2. **Length**: `len(sl)` equals the total count of inserted elements (minus removed ones).
3. **Indexing**: `sl[i] == sorted(list(sl))[i]` for all valid indices `i`.
4. **bisect consistency**: `sl[sl.bisect_left(x)] == x` for any `x` in `sl`.
5. **count relationship**: `sl.bisect_right(x) - sl.bisect_left(x) == sl.count(x)`.
6. **irange completeness**: `list(sl.irange(a, b, inclusive=(p, q)))` equals
   `[x for x in sl if (a < x if not p else a <= x) and (x < b if not q else x <= b)]`.
7. **pop correctness**: `sl.pop(i)` returns `list(sl)[i]` and removes exactly that element.
8. **Deletion integrity**: after `sl.remove(v)`, `list(sl) == sorted(e for e in original if e != v)`.

---

## Performance

| Method | Time Complexity |
|--------|----------------|
| `add` | O(log n) |
| `remove` | O(log n) |
| `__contains__` | O(log n) |
| `__getitem__` | O(log n) |
| `bisect_left/right` | O(log n) |
| `count` | O(log n) |
| `irange` | O(log n + k) |
| `index` | O(log n) |

Default `DEFAULT_LOAD_FACTOR = 1000`. The load factor controls sublist size:
sublists hold between `load/2` and `2*load` elements. When a sublist exceeds
`2*load`, it is split in two. When a sublist drops below `load/2`, it is merged
with its neighbor.
