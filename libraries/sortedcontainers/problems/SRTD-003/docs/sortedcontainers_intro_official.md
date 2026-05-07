# sortedcontainers 2.4.0 — Introduction & Overview (Official Documentation)

Source: http://www.grantjenks.com/docs/sortedcontainers/introduction.html

---

## Overview

Sorted Containers is an Apache2-licensed library for Python that provides sorted collection types implemented in pure Python. Despite being pure Python, it achieves performance comparable to C-extensions through careful use of Python's built-in list type and a segmented storage strategy.

The library provides three sorted collection types:

1. **`SortedList`** — A mutable sorted sequence
2. **`SortedKeyList`** — A mutable sorted sequence with a key function
3. **`SortedDict`** — A mutable sorted mapping
4. **`SortedSet`** — A mutable sorted set

---

## Installation

```
python3 -m pip install sortedcontainers
```

Or via pipenv:

```
pipenv install sortedcontainers
```

Or directly from GitHub:

```
pip install git+https://github.com/grantjenks/python-sortedcontainers
```

---

## SortedList

The `SortedList` is a mutable sequence that "maintains its values in ascending sort order."

### Basic Usage

```python
from sortedcontainers import SortedList

sl = SortedList(['e', 'a', 'c', 'd', 'b'])
# SortedList(['a', 'b', 'c', 'd', 'e'])

sl += ['f', 'g', 'h']
# SortedList(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])

sl[4]      # 'e'
sl[-1]     # 'h'
sl[2:5]    # ['c', 'd', 'e']
```

### Adding Elements

```python
sl = SortedList([3, 1, 4, 1, 5, 9, 2, 6])
sl.add(7)       # Inserts 7 in sorted position
sl.update([0, 8])  # Inserts multiple values
```

### Removing Elements

```python
sl.remove(1)    # Removes first occurrence of 1 (raises ValueError if absent)
sl.discard(99)  # Removes 99 if present, no error if absent
sl.pop()        # Removes and returns last element
sl.pop(0)       # Removes and returns first element
```

### Lookups

```python
sl = SortedList([1, 2, 3, 4, 5])
3 in sl         # True (O(log n) membership test)
sl.count(3)     # 1
sl.index(3)     # 2
sl.bisect_left(3)   # 2
sl.bisect_right(3)  # 3
```

---

## SortedKeyList

Accepts a key-function parameter, like Python's built-in `sorted()`, for custom ordering:

```python
from sortedcontainers import SortedKeyList

skl = SortedKeyList(key=lambda x: x % 10)
skl.update([14, 21, 33, 45])
# SortedKeyList([21, 33, 14, 45], key=<lambda>)
# Sorted by (value % 10): 1, 3, 4, 5
```

Additional key-based methods:
- `bisect_key_left(key)` / `bisect_key_right(key)`
- `irange_key(min_key, max_key)`

---

## SortedDict

Maintains keys in sorted order while functioning as a standard mapping:

```python
from sortedcontainers import SortedDict

sd = SortedDict({'b': 2, 'a': 1, 'c': 3})
sd.keys()    # SortedKeysView(['a', 'b', 'c'])
sd.peekitem(0)   # ('a', 1)
sd.popitem(0)    # ('a', 1)
```

---

## SortedSet

Provides sorted values with set operations, requiring hashable and comparable elements:

```python
from sortedcontainers import SortedSet

ss = SortedSet([3, 1, 4, 1, 5, 9, 2, 6, 5])
# SortedSet([1, 2, 3, 4, 5, 6, 9])
```

---

## Critical Requirements

Three mandatory requirements apply to all Sorted Containers types:

### 1. Total Ordering

Comparison values must have complete orderings. Python's built-in types (integers, strings, floats, tuples of comparable types) satisfy this requirement. The following do not and must not be used as sort keys:

- Sets and frozensets (partial ordering only)
- Dicts
- Objects without `__lt__` defined

### 2. Immutable Keys

Values' comparison keys **cannot change** while stored in the container. If the key changes after insertion, the sorted order invariant is violated and the data structure becomes corrupted.

```python
# WRONG: mutating a list used as a key
sl = SortedKeyList(key=lambda x: x[0])
lst = [1, 2, 3]
sl.add(lst)
lst[0] = 99   # CORRUPTS the sorted order!
```

### 3. Consistent Equality

When using key-functions: "equal values must have equal keys." If two values compare as equal under the key function but are treated as distinct by the equality operator, behavior is undefined.

---

## Internal Implementation: Segmented Storage

### Two-Level List Structure

`SortedList` uses a segmented (two-level) list structure internally:

- **`_lists`**: A list of sublists (buckets). Each sublist is itself sorted. The concatenation of all sublists equals the full sorted sequence.
- **`_maxes`**: A list of the maximum value of each sublist, used for O(log n) binary search to locate the right bucket.

This design avoids the O(n) insertion cost of a flat list while still allowing O(log n) access by index via prefix-sum bookkeeping.

### DEFAULT_LOAD_FACTOR

The default load factor is `1000`. This controls target sublist size:

- Target sublist size: approximately `load` elements
- Split threshold: `2 * load` — sublists larger than this are split in half
- Collapse threshold: `load // 2` — sublists smaller than this may be merged

The recommended value for a list of size `n` is approximately `cube_root(n)`.

```python
sl = SortedList()
sl._reset(100)   # Change load factor to 100
```

### The `_maxes` Invariant

`_maxes[i]` always stores the **last element** (maximum) of `_lists[i]`. This is critical for the binary search used in `add()`, `remove()`, `__contains__()`, and all bisect operations:

```python
# Conceptual check (not public API):
assert all(
    sl._maxes[i] == sl._lists[i][-1]
    for i in range(len(sl._lists))
)
```

If `_maxes[i]` incorrectly stores `_lists[i][0]` (first element) instead of `_lists[i][-1]` (last element), then:
- Binary search over `_maxes` will fail for any value larger than the first element of that bucket
- `add()` will insert values into the wrong bucket
- `__contains__()` will return `False` for values that are actually present
- The sorted order invariant may appear intact at the list level but lookups will be wrong

### `_expand()` — Bucket Split

When a bucket grows beyond `2 * load` elements (e.g., after many `add()` calls), `_expand(pos)` is called to split it:

```python
def _expand(self, pos):
    """Split the sublist at position `pos` into two halves."""
```

After the split, `_maxes[pos]` must be updated to reflect the new maximum of the (now smaller) left bucket. `_maxes` also gets a new entry for the right bucket.

---

## Performance Summary

All core operations run in O(log n) time. The library is benchmarked against:

- Python's built-in `list` (O(n) for sorted insertions)
- `blist` library
- `rbtree` (C-based red-black tree)

Sorted Containers matches or exceeds the performance of C-based alternatives for typical workloads, especially for list sizes in the range of 10,000 to 10,000,000 elements.
