# sortedcontainers API Reference

Version: 2.4.0

The `sortedcontainers` library provides `SortedList`, `SortedDict`, and
`SortedSet` — pure-Python sorted collection types with performance
comparable to C extensions.

---

## SortedList

`SortedList` is a sorted sequence type that maintains values in ascending
order. It supports efficient `O(log n)` addition, removal, and positional
lookup.

### Internal Architecture

`SortedList` uses a **list-of-lists** (B-tree-like) internal structure:

- `_lists`: a list of sorted sublists. Each sublist holds between
  `_load // 2` and `2 * _load` elements.
- `_maxes`: the maximum element of each sublist. Used for binary search
  to locate the correct sublist for add/remove/search operations.
- `_len`: total number of elements across all sublists.
- `_load`: the load factor. Default is `1000`. Can be changed with `_reset(load)`.
- `_index`: a flat array representing a positional B-tree for `O(log n)`
  element access by integer index. Built lazily; cleared whenever the
  sublist structure changes (splits or merges).
- `_offset`: integer marking the start of leaf nodes in `_index`. Leaf
  node at `_index[_offset + i]` contains `len(_lists[i])`.

**Sublist splitting**: when a sublist exceeds `2 * _load` elements, it is
split into two halves. After a split, `_maxes[pos]` is updated to the
maximum of the left half (= `_lists[pos][-1]`).

**Sublist merging**: when a sublist falls below `_load // 2` elements
after a deletion, it is merged with the adjacent sublist.

**Index rebuilding**: `_index` is built by `_build_index()` on demand.
The index represents cumulative sublist sizes in a balanced binary tree
stored in level-order (breadth-first) in a flat array. `_offset` marks
where the leaf level starts. The left child of node at position `p` is
at `2p+1` and the right child at `2p+2`. `_loc(pos, idx)` and `_pos(k)`
use this index for `O(log n)` global index arithmetic.

### Constructor

```python
SortedList(iterable=None)
```

Create a new SortedList. Optional `iterable` provides initial values.

```python
sl = SortedList([3, 1, 4, 1, 5])
# sl == SortedList([1, 1, 3, 4, 5])
```

### Adding Elements

```python
sl.add(value)
```
Add a value to the sorted list. `O(log n)`.

```python
sl.update(iterable)
```
Add all values from `iterable`. `O(k * log n)`.

```python
sl = SortedList()
sl.add(5)
sl.add(1)
sl.add(3)
list(sl)  # [1, 3, 5]

sl.update([2, 4])
list(sl)  # [1, 2, 3, 4, 5]
```

### Removing Elements

```python
sl.discard(value)
```
Remove `value` if present; do nothing if not. `O(log n)`.

```python
sl.remove(value)
```
Remove `value`; raises `ValueError` if not present. `O(log n)`.

```python
sl.pop(index=-1)
```
Remove and return the element at position `index`. Default is `-1` (last
element). Negative indices are supported. Raises `IndexError` if empty or
out of range. `O(log n)`.

```python
sl = SortedList([1, 2, 3, 4, 5])
sl.pop()    # returns 5, sl = [1, 2, 3, 4]
sl.pop(0)   # returns 1, sl = [2, 3, 4]
sl.pop(-1)  # returns 4, sl = [2, 3]
sl.pop(1)   # returns 3, sl = [2]
```

### Element Access

```python
sl[index]
```
Return element at `index`. Supports negative indices and slicing. `O(log n)`.

```python
sl = SortedList([10, 20, 30, 40, 50])
sl[0]   # 10
sl[-1]  # 50
sl[1:3] # [20, 30]
```

```python
len(sl)
```
Return the number of elements. `O(1)`.

### Iteration

```python
for x in sl: ...          # ascending order
for x in reversed(sl): ... # descending order
```

```python
sl.islice(start=None, stop=None, reverse=False)
```
Return an iterator over elements from index `start` (inclusive) to
`stop` (exclusive). When `reverse=True`, yields in descending order.
Both `start` and `stop` are integer indices (like `range()`), not values.

```python
sl = SortedList([1, 2, 3, 4, 5])
list(sl.islice(1, 4))               # [2, 3, 4]
list(sl.islice(1, 4, reverse=True)) # [4, 3, 2]
list(sl.islice(2))                  # [3, 4, 5]  (start=2, stop=None)
```

```python
sl.irange(minimum=None, maximum=None, inclusive=(True, True), reverse=False)
```
Return an iterator over values between `minimum` and `maximum`.

- `minimum`: start of range. `None` means beginning of list.
- `maximum`: end of range. `None` means end of list.
- `inclusive`: tuple `(include_minimum, include_maximum)`.
  - `(True, True)`: both endpoints included (default).
  - `(True, False)`: minimum included, maximum excluded.
  - `(False, True)`: minimum excluded, maximum included.
  - `(False, False)`: both endpoints excluded.
- `reverse`: if `True`, yields values in descending order.

```python
sl = SortedList([1, 2, 3, 4, 5, 6, 7])

# Default: both endpoints inclusive
list(sl.irange(2, 5))                          # [2, 3, 4, 5]

# Exclusive maximum
list(sl.irange(2, 5, inclusive=(True, False))) # [2, 3, 4]

# Exclusive minimum
list(sl.irange(2, 5, inclusive=(False, True))) # [3, 4, 5]

# Both exclusive
list(sl.irange(2, 5, inclusive=(False, False))) # [3, 4]

# Reverse iteration
list(sl.irange(2, 5, reverse=True))            # [5, 4, 3, 2]

# Open-ended ranges
list(sl.irange(maximum=4))                    # [1, 2, 3, 4]
list(sl.irange(minimum=4))                    # [4, 5, 6, 7]
```

**Key invariants for irange**:
- All yielded values satisfy `minimum <= x <= maximum` (with `inclusive=(True,True)`).
- For `inclusive=(False, True)`: all yielded values satisfy `x > minimum`.
  The minimum value is NEVER in the output when `inclusive[0]=False`.
- For `inclusive=(True, False)`: all yielded values satisfy `x < maximum`.
- The order of output matches the sorted order of the SortedList.
- `list(sl.irange(a, b)) == [x for x in sl if a <= x <= b]` (for default inclusive).

### Membership and Counting

```python
value in sl      # True if value is present. O(log n).
sl.count(value)  # Number of occurrences. O(log n).
```

```python
sl = SortedList([1, 2, 2, 3, 3, 3])
3 in sl        # True
sl.count(3)    # 3
sl.count(99)   # 0
```

### Bisect Operations

These return the index at which `value` could be inserted to keep the
list sorted. They do NOT modify the list.

```python
sl.bisect_left(value)
```
Return the leftmost index where `value` can be inserted. If `value` is
already present, returns the index of the **first** occurrence (to the
left of all equal values).

```python
sl.bisect_right(value)
sl.bisect(value)  # alias for bisect_right
```
Return the rightmost index where `value` can be inserted. If `value` is
already present, returns the index **after** the last occurrence (to the
right of all equal values).

```python
sl = SortedList([1, 2, 2, 3, 3, 3, 4])

sl.bisect_left(2)   # 1  (index of first '2')
sl.bisect_right(2)  # 3  (index after last '2')
sl.bisect_left(3)   # 3  (index of first '3')
sl.bisect_right(3)  # 6  (index after last '3')
sl.bisect_left(5)   # 7  (would insert at end)
sl.bisect_right(0)  # 0  (would insert at start)
```

**Key invariants**:
- `sl[sl.bisect_left(x)] == x` for any `x` in `sl`.
- `sl.bisect_right(x) - sl.bisect_left(x) == sl.count(x)` for any `x`.
- For `x` not in `sl`: `sl.bisect_left(x) == sl.bisect_right(x)`.
- `sl.bisect_left(x) <= sl.bisect_right(x)` always.

### Finding Position

```python
sl.index(value, start=None, stop=None)
```
Return the first index of `value` in `sl[start:stop]`. Raises `ValueError`
if not found. `O(log n)`.

```python
sl = SortedList([10, 20, 30, 40, 50])
sl.index(30)     # 2
sl.index(10)     # 0
sl.index(99)     # raises ValueError
```

### Utility

```python
sl.copy()  # Shallow copy. O(n).
sl._reset(load)  # Reset the internal load factor. Rebuilds internal structure.
```

`_reset(load)` changes the sublist size threshold. With `load=4`, sublists
split when they exceed 8 elements. This is useful for testing sublist
boundary behavior with small datasets.

---

## SortedDict

`SortedDict` is a sorted mutable mapping (subclass of `dict`) that maintains
keys in sorted order using an internal `SortedList`. All dict operations are
available, plus additional sorted-key operations.

### Constructor

```python
SortedDict(*args, **kwargs)
SortedDict(key_function, *args, **kwargs)
```

Optional first positional argument: a `key` function (like `sorted(key=...)`).
Remaining arguments are the same as `dict()`.

```python
sd = SortedDict({'c': 3, 'a': 1, 'b': 2})
list(sd.keys())  # ['a', 'b', 'c'] — sorted

sd = SortedDict(abs, {-3: 'neg3', 1: 'one', -2: 'neg2'})
list(sd.keys())  # [1, -2, -3] — sorted by abs value
```

### Key Ordering

`SortedDict` keys are ALWAYS maintained in sorted order. Iteration (`for k in sd`),
`sd.keys()`, `sd.items()`, and `sd.values()` all iterate in sorted key order.

```python
sd = SortedDict()
sd['z'] = 26
sd['a'] = 1
sd['m'] = 13
list(sd)         # ['a', 'm', 'z']
list(sd.items()) # [('a', 1), ('m', 13), ('z', 26)]
```

### Standard Dict Operations

All standard `dict` methods work as expected, but the key order is always sorted:

```python
sd['key'] = value          # set item
del sd['key']              # delete item
sd['key']                  # get item
'key' in sd                # membership test
sd.pop('key')              # remove and return value for key
sd.pop('key', default)     # with default if key missing
sd.get('key', default)     # get with default
sd.setdefault('key', val)  # insert if missing
sd.update(...)             # update from dict or pairs
sd.clear()                 # remove all items
len(sd)                    # number of items
```

### Positional Access

Since keys are sorted, items can be accessed by position:

```python
sd.peekitem(index=-1)
```
Return `(key, value)` pair at the given sorted position WITHOUT removing it.
Default `index=-1` returns the last (largest-key) item.
`index=0` returns the first (smallest-key) item.

```python
sd = SortedDict({'a': 1, 'b': 2, 'c': 3})
sd.peekitem(0)   # ('a', 1) — first item, not removed
sd.peekitem(-1)  # ('c', 3) — last item, not removed
sd.peekitem(1)   # ('b', 2) — middle item
```

```python
sd.popitem(index=-1)
```
Remove and return the `(key, value)` pair at the given sorted position.
Default `index=-1` removes and returns the last (largest-key) item.
`index=0` removes and returns the first (smallest-key) item.

**Return value**: `(key, value)` tuple — the key is always the first element
and the value is always the second element.

```python
sd = SortedDict({'a': 1, 'b': 2, 'c': 3})
sd.popitem(0)    # returns ('a', 1) — smallest key 'a' with value 1
# sd is now {'b': 2, 'c': 3}

sd.popitem(-1)   # returns ('c', 3) — largest key 'c' with value 3
# sd is now {'b': 2}

sd.popitem()     # returns ('b', 2) — default index -1
# sd is now {}
```

**Key invariant**: `key, value = sd.popitem(i)` guarantees that `key` is the
key that was at sorted position `i`, and `value` is its associated value.
Specifically: `key == list(sd.keys())[i]` before the call.

### Views

```python
sd.keys()    # SortedKeysView — live view of sorted keys
sd.items()   # SortedItemsView — live view of sorted (key, value) pairs
sd.values()  # SortedValuesView — live view of values in sorted-key order
```

Views support integer indexing and slicing:

```python
sd = SortedDict({'a': 1, 'b': 2, 'c': 3, 'd': 4})
kv = sd.keys()
kv[0]    # 'a' — first key
kv[-1]   # 'd' — last key
kv[1:3]  # ['b', 'c'] — slice of keys

iv = sd.items()
iv[0]    # ('a', 1)
iv[-1]   # ('d', 4)
iv[:]    # [('a', 1), ('b', 2), ('c', 3), ('d', 4)]
```

### Sorted-List Methods (Delegated to Internal Key List)

`SortedDict` exposes the following SortedList methods that operate on keys:

```python
sd.bisect_left(key)   # index before which key would be inserted
sd.bisect_right(key)  # index after which key would be inserted
sd.bisect(key)        # alias for bisect_right
sd.index(key)         # integer index of key in sorted order
sd.irange(min, max, inclusive=(True,True), reverse=False)
sd.islice(start, stop, reverse=False)
sd._reset(load)
```

These have the same semantics as the corresponding `SortedList` methods
but operate on dict keys:

```python
sd = SortedDict({1: 'a', 3: 'c', 5: 'e', 7: 'g'})
sd.bisect_left(3)   # 1
sd.bisect_right(3)  # 2
list(sd.irange(2, 6))  # [3, 5]
list(sd.irange(3, 5, inclusive=(False, True)))  # [5]
```

---

## Key Invariants (For Property-Based Testing)

### SortedList Invariants

1. **Ordering**: `list(sl) == sorted(list(sl))` always holds.
2. **Sequential ordering**: `sl[i] <= sl[i+1]` for all `0 <= i < len(sl)-1`.
3. **Bisect consistency**: `sl.bisect_right(x) - sl.bisect_left(x) == sl.count(x)`.
4. **Bisect access**: `sl[sl.bisect_left(x)] == x` for any `x` in `sl`.
5. **irange completeness** (inclusive both): `list(sl.irange(a, b)) == [x for x in sl if a <= x <= b]`.
6. **irange exclusive min**: no element in `sl.irange(v, m, inclusive=(False,True))` equals `v`.
7. **irange exclusive max**: no element in `sl.irange(m, v, inclusive=(True,False))` equals `v`.
8. **islice consistency**: `list(sl.islice(s, t)) == list(sl)[s:t]`.
9. **pop correctness**: `sl.pop(k)` returns `list(sl)[k]` before the call.
10. **Count/len consistency**: `sum(sl.count(x) for x in set(sl)) == len(sl)`.
11. **Index integrity**: `sl[k]` must return the k-th smallest element for all valid k.
12. **index() consistency**: `sl.index(v)` returns the same value as `list(sl).index(v)`.

### SortedDict Invariants

1. **Key ordering**: `list(sd.keys()) == sorted(sd.keys())`.
2. **peekitem contract**: `sd.peekitem(0) == (min(sd.keys()), sd[min(sd.keys())])`.
3. **popitem contract**: `k, v = sd.popitem(i)` gives `k == sorted(sd.keys())[i]`
   and `v == sd[k]` (before the call). The first tuple element is the KEY.
4. **items consistency**: `list(sd.items()) == [(k, sd[k]) for k in sorted(sd.keys())]`.
5. **Iteration = sorted keys**: `list(sd) == sorted(sd.keys())`.

---

## Usage Examples

### SortedList: Range Queries with Exclusion

```python
from sortedcontainers import SortedList

scores = SortedList([85, 90, 72, 88, 95, 60, 78])
# All scores in [80, 90]:
list(scores.irange(80, 90))  # [85, 88, 90]

# Scores strictly between 80 and 90 (both exclusive):
list(scores.irange(80, 90, inclusive=(False, False)))  # [85, 88]

# Scores above 80 (exclusive lower bound):
list(scores.irange(80, None, inclusive=(False, True)))  # [85, 88, 90, 95]
```

### SortedList: Positional Access

```python
from sortedcontainers import SortedList

primes = SortedList([2, 3, 5, 7, 11, 13, 17, 19, 23])
primes[0]   # 2  (smallest)
primes[-1]  # 23 (largest)
primes[4]   # 11 (5th element, 0-indexed)

# Where would 10 be inserted?
primes.bisect_left(10)   # 4
primes.bisect_right(10)  # 4  (same, since 10 not in list)

# Where would 11 be inserted?
primes.bisect_left(11)   # 4  (before 11)
primes.bisect_right(11)  # 5  (after 11)
```

### SortedDict: Ordered Key Access

```python
from sortedcontainers import SortedDict

inventory = SortedDict({'banana': 5, 'apple': 10, 'cherry': 3, 'date': 8})
list(inventory.keys())   # ['apple', 'banana', 'cherry', 'date']
list(inventory.items())  # [('apple', 10), ('banana', 5), ('cherry', 3), ('date', 8)]

# First item by key:
inventory.peekitem(0)    # ('apple', 10)

# Remove and return last item by key:
inventory.popitem(-1)    # ('date', 8)
# inventory is now: {'apple': 10, 'banana': 5, 'cherry': 3}

# Remove and return first item by key:
inventory.popitem(0)     # ('apple', 10)
# inventory is now: {'banana': 5, 'cherry': 3}
```

### SortedList: Duplicate Handling

```python
from sortedcontainers import SortedList

sl = SortedList([3, 1, 4, 1, 5, 9, 2, 6, 5, 3])
sl.count(1)          # 2
sl.count(5)          # 2
sl.bisect_left(3)    # 3   (index of first '3')
sl.bisect_right(3)   # 5   (index after last '3')
sl.bisect_right(3) - sl.bisect_left(3)  # 2 == sl.count(3)
```

### Load Factor Adjustment

The internal load factor controls when sublists split/merge. The default
of 1000 is optimized for large lists. For testing internal behavior:

```python
sl = SortedList()
sl._reset(4)  # load=4: sublists split at 9 elements

for i in range(20):
    sl.add(i)

# With load=4 and 20 elements, sl has ~4-5 sublists
# This exposes internal B-tree behavior with small test data
```
