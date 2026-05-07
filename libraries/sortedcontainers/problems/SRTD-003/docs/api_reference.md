# SortedList API Reference

## Initialization

### `SortedList(iterable=None)`

Create a SortedList, optionally initialized from `iterable`.

```python
from sortedcontainers import SortedList

sl = SortedList()                    # empty list
sl = SortedList([3, 1, 4, 1, 5])    # SortedList([1, 1, 3, 4, 5])
sl = SortedList(range(100))         # SortedList([0, 1, ..., 99])
```

**Note**: When initialized via `iterable`, a bulk path is used (not individual `add()` calls), so `_expand` is not triggered.

## Adding Elements

### `add(value)`

Add a single element, maintaining sorted order.

```python
sl = SortedList()
sl.add(5)    # SortedList([5])
sl.add(3)    # SortedList([3, 5])
sl.add(7)    # SortedList([3, 5, 7])
```

Time complexity: `O(log n)`

### `update(iterable)`

Add multiple elements in bulk.

```python
sl.update([1, 2, 3])
```

Time complexity: `O(k * log n)` (approximate)

## Queries

### `__contains__(value)` -- `value in sl`

Check whether `value` is in the list.

```python
sl = SortedList([1, 2, 3])
assert 2 in sl    # True
assert 5 in sl    # False
```

### `count(value)`

Return the number of occurrences of `value` in the list.

```python
sl = SortedList([1, 1, 2, 3])
sl.count(1)    # 2
sl.count(5)    # 0
```

### `bisect_left(value)` / `bisect_right(value)`

Return the position where `value` should be inserted (equivalent to `bisect.bisect_left` / `bisect.bisect_right`).

```python
sl = SortedList([10, 20, 30, 40])
sl.bisect_left(20)    # 1
sl.bisect_right(20)   # 2
sl.bisect_left(25)    # 2
```

### `irange(minimum=None, maximum=None, inclusive=(True, True), reverse=False)`

Return an iterator over elements within the specified range.

```python
sl = SortedList(range(10))
list(sl.irange(3, 7))                          # [3, 4, 5, 6, 7]
list(sl.irange(3, 7, inclusive=(True, False))) # [3, 4, 5, 6]
```

### `index(value, start=None, stop=None)`

Return the index of `value` in the sorted list (first occurrence).

## Removal

### `discard(value)`

Remove one occurrence of `value` (if present). Silently ignores if not present.

### `remove(value)`

Remove one occurrence of `value`. Raises `ValueError` if not present.

### `pop(index=-1)`

Remove and return the element at the given position (default: last element).

## Access

### `__getitem__(index)`

Index access, supports negative indices and slicing.

```python
sl = SortedList([1, 2, 3, 4, 5])
sl[0]     # 1
sl[-1]    # 5
sl[1:3]   # [2, 3]
```

## Internal Parameters

### `DEFAULT_LOAD_FACTOR = 20`

Parameter controlling bucket size. The default value of **20** means:
- Each bucket's target size is 20 elements
- A bucket triggers automatic splitting when it exceeds `2 * 20 = 40` elements
- After splitting, each bucket's size is approximately 20 elements

**For correctness testing**: To trigger a bucket split (`_expand`), you need to accumulate **more than 40** elements in the same bucket via the `add()` method.

### `_reset(load)`

Reset the load factor and rebuild internal structures (primarily used for debugging and performance tuning).
