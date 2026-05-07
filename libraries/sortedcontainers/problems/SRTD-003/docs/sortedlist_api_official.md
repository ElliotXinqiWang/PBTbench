# sortedcontainers 2.4.0 — SortedList API Reference (Official Documentation)

Source: http://www.grantjenks.com/docs/sortedcontainers/sortedlist.html

---

## Overview

`SortedList` is a mutable sequence from the Sorted Containers library (Apache2 licensed) that automatically maintains values in sorted order. The implementation uses pure Python with performance comparable to C-extensions.

The documentation states: "Sorted list values are maintained in sorted order" and "values must be comparable. The total ordering of values must not change while they are stored in the sorted list."

---

## Adding Values

### `add(value)`

Inserts a single value while maintaining sort order.

- Runtime: O(log n) approximate
- Thread safety: not guaranteed without external locking

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
sl.update([4, 0, 2])
# sl is now SortedList([0, 1, 2, 2, 3, 4])
```

---

## Membership Testing

### `__contains__(value)`

Checks if a value exists in the sorted list.

- Runtime: O(log n)
- Usage: `value in sorted_list`

```python
sl = SortedList([1, 2, 3])
3 in sl   # True
4 in sl   # False
```

---

## Search Operations

### `bisect_left(value)`

Returns the leftmost index where `value` could be inserted to keep the list sorted. Insertions are placed *before* any existing equal values.

- Runtime: O(log n) approximate

```python
sl = SortedList([1, 2, 2, 3])
sl.bisect_left(2)   # 1
sl.bisect_left(4)   # 4
```

### `bisect_right(value)`

Returns the rightmost index where `value` could be inserted to keep the list sorted. Insertions are placed *after* any existing equal values.

- Runtime: O(log n) approximate

```python
sl = SortedList([1, 2, 2, 3])
sl.bisect_right(2)  # 3
```

### `index(value, start=None, stop=None)`

Returns the index of the first occurrence of `value`, or raises `ValueError` if absent. Supports negative indices and range parameters.

```python
sl = SortedList([1, 2, 3])
sl.index(2)         # 1
sl.index(99)        # raises ValueError
```

### `count(value)`

Returns the number of occurrences of `value`.

```python
sl = SortedList([1, 2, 2, 3])
sl.count(2)  # 2
```

---

## Removal Operations

### `remove(value)`

Removes the first occurrence of `value`, or raises `ValueError` if absent.

```python
sl = SortedList([1, 2, 3])
sl.remove(2)
# sl is now SortedList([1, 3])
```

### `discard(value)`

Removes `value` if present, otherwise does nothing (no exception).

```python
sl = SortedList([1, 2, 3])
sl.discard(99)  # No error
```

### `pop(index=-1)`

Removes and returns the value at the given index. Negative indices are supported.

```python
sl = SortedList([1, 2, 3])
sl.pop()    # 3  (last element)
sl.pop(0)   # 1  (first element)
```

### `clear()`

Removes all values from the sorted list.

---

## Iteration

### `irange(minimum=None, maximum=None, inclusive=(True, True), reverse=False)`

Creates an iterator over values within a range.

- `minimum`: lower bound (default: no lower bound)
- `maximum`: upper bound (default: no upper bound)
- `inclusive`: tuple of two booleans controlling whether bounds are inclusive
- `reverse`: if True, iterates in descending order

```python
sl = SortedList([1, 2, 3, 4, 5])
list(sl.irange(2, 4))                     # [2, 3, 4]
list(sl.irange(2, 4, inclusive=(True, False)))   # [2, 3]
list(sl.irange(2, 4, reverse=True))       # [4, 3, 2]
```

### `islice(start=None, stop=None, reverse=False)`

Returns an iterator over an indexed slice. Start is inclusive; stop is exclusive.

```python
sl = SortedList([1, 2, 3, 4, 5])
list(sl.islice(1, 3))   # [2, 3]
```

---

## Internal Bucketing and Load Factor

### `_reset(load)`

Adjusts the load factor for internal bucketing.

- **Default load factor**: `1000` — works well for most use cases
- Recommendation from the docs: "use a value that is the cube root of the list size"
- Runtime: O(n)

```python
sl = SortedList()
sl._reset(100)   # Set load factor to 100 for smaller lists
```

### How Internal Bucketing Works

`SortedList` uses a segmented (two-level) list internally:

- **`_lists`**: A list of sublists (buckets), each containing a sorted chunk of values
- **`_maxes`**: A list storing the maximum value of each sublist, used for binary search to find the right bucket

When a new value is added via `add()`, the implementation:
1. Binary-searches `_maxes` to find the target bucket
2. Inserts the value into the correct position within that bucket
3. If the bucket grows too large (> `2 * load`), it is split into two

When a bucket shrinks too small (< `load // 2`), it may be merged with a neighbor via `_collapse()`.

The `_expand()` method handles bucket splitting when a bucket becomes too large after an insertion.

### `_maxes` Invariant

The `_maxes` list always stores the **last** (maximum) element of each sublist. This invariant is critical for correct binary search behavior:

- `_maxes[i]` == `_lists[i][-1]` for all i
- After any structural modification, `_maxes` must be updated to reflect the true maximum of each bucket

If `_maxes[i]` is set to `_lists[i][0]` (the first element) instead of `_lists[i][-1]` (the last), binary search over `_maxes` will produce incorrect bucket indices for values larger than the first element of any bucket.

---

## SortedKeyList Subclass

Extends `SortedList` with key-function support for custom comparison logic.

### `__init__(iterable=None, key=<identity function>)`

```python
from sortedcontainers import SortedKeyList
skl = SortedKeyList([3, 1, 2], key=lambda x: -x)
# skl is now SortedKeyList([3, 2, 1], key=<lambda>)
```

### Additional methods

- `bisect_key_left(key)` — binary search on keys
- `bisect_key_right(key)` — binary search on keys
- `irange_key(min_key, max_key, inclusive=(True, True), reverse=False)` — range iteration by key values

---

## Methods That Raise `NotImplementedError`

The following methods raise `NotImplementedError` to prevent disrupting sort order:

- `append()`
- `extend()`
- `insert()`
- `reverse()`
- `__setitem__()`

---

## Performance Characteristics

| Operation | Time Complexity |
|-----------|----------------|
| `add(value)` | O(log n) |
| `__contains__(value)` | O(log n) |
| `remove(value)` / `discard(value)` | O(log n) |
| `pop(index)` | O(log n) |
| `bisect_left(value)` | O(log n) |
| `index(value)` | O(log n) |
| `__getitem__(index)` | O(log n) |
| `update(iterable)` | O(k·log n) |
| `_reset(load)` | O(n) |
