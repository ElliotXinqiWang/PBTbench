# boltons API Reference (version 25.0.0)

This document covers three modules from boltons that are in scope for this problem: `IndexedSet` (from `boltons.setutils`), `windowed` / `windowed_iter` (from `boltons.iterutils`), and `LRU` (from `boltons.cacheutils`).

---

## 1. `IndexedSet` — `boltons.setutils`

`IndexedSet` is a hybrid of `set` and `list`: it maintains **insertion order**, **uniqueness**, and supports **integer indexing** in O(1) time.

```python
from boltons.setutils import IndexedSet
```

### Construction

```python
s = IndexedSet()                          # empty
s = IndexedSet([3, 1, 4, 1, 5, 9, 2])    # from iterable; duplicates dropped
# IndexedSet([3, 1, 4, 5, 9, 2])
```

### Core Invariants

1. **Uniqueness**: each value appears at most once.
2. **Insertion order**: elements are ordered by first insertion time.
3. **Index consistency**: for every element `x` in the set,
   - `s[s.index(x)] == x`
   - `s.index(x)` returns the 0-based position of `x` in iteration order.
4. **Length**: `len(s)` equals the number of distinct elements.
5. **Iteration**: `list(s)` yields all elements in insertion order; equivalent to `[s[i] for i in range(len(s))]`.

### Element Access and Indexing

```python
s = IndexedSet(['a', 'b', 'c', 'd'])

# By integer index (like a list)
s[0]    # 'a'
s[-1]   # 'd'
s[1:3]  # IndexedSet(['b', 'c'])

# index() — position of a value
s.index('c')   # 2
s.index('z')   # raises ValueError

# Containment
'b' in s    # True
'z' in s    # False

# Length
len(s)   # 4
```

### Mutation

#### `add(item)`
Adds `item` to the end of the set if not already present. No-op if already present.

```python
s = IndexedSet([1, 2, 3])
s.add(4)    # IndexedSet([1, 2, 3, 4])
s.add(2)    # IndexedSet([1, 2, 3, 4])  — no change, 2 already present
```

#### `discard(item)`
Removes `item` from the set if present; does nothing if absent (no exception).

```python
s = IndexedSet([1, 2, 3, 4])
s.discard(2)    # IndexedSet([1, 3, 4])
s.discard(99)   # no-op
```

After `discard(item)`:
- `item not in s`
- All remaining elements are still accessible by `s[i]` for `i in range(len(s))`
- `s.index(x)` returns the correct position for every remaining element `x`
- `list(s) == [s[i] for i in range(len(s))]` still holds

#### `remove(item)`
Like `discard()`, but raises `KeyError` if `item` is not present.

#### `pop(index=-1)`
Removes and returns the element at `index` (default: last element).

#### `clear()`
Removes all elements.

### Set Operations

All standard set operations are supported. They return a new `IndexedSet` whose elements are in the order they appeared in the *left operand*.

#### `difference(*others)` / `a - b`

Returns a new `IndexedSet` with elements from `self` that are **not** in any of `others`.

```python
a = IndexedSet([1, 2, 3, 4, 5])
b = IndexedSet([3, 4, 5, 6, 7])
a - b    # IndexedSet([1, 2])   — elements in a but not in b
b - a    # IndexedSet([6, 7])   — elements in b but not in a
```

**Documented properties:**
- `set(a - b) == set(a) - set(b)` (equals the built-in set difference)
- All elements of `a - b` come from `a`: `all(x in a for x in (a - b))`
- No element of `a - b` is in `b`: `all(x not in b for x in (a - b))`
- Order preservation: the order of elements in `a - b` is the same as their order in `a`

#### `intersection(*others)` / `a & b`

Returns elements in `self` that are also in all of `others`.

```python
a = IndexedSet([1, 2, 3])
b = IndexedSet([2, 3, 4])
a & b    # IndexedSet([2, 3])
```

**Property**: `set(a & b) == set(a) & set(b)`

#### `union(*others)` / `a | b`

Returns all elements from `self` and `others`, deduplicated, in insertion order.

```python
a = IndexedSet([1, 2, 3])
b = IndexedSet([3, 4, 5])
a | b    # IndexedSet([1, 2, 3, 4, 5])
```

**Property**: `set(a | b) == set(a) | set(b)`

#### `symmetric_difference(other)` / `a ^ b`

Returns elements that are in exactly one of `a` or `b`.

**Property**: `set(a ^ b) == set(a) ^ set(b)`

### Index Invariant After Mutations

After any sequence of `add()` and `discard()` operations, the following must all hold simultaneously for every element `x` in the set:

```python
# (1) Roundtrip: index → element → index
s[s.index(x)] == x

# (2) List reconstruction
list(s) == [s[i] for i in range(len(s))]

# (3) Membership consistency
(x in s) == (s.index(x) >= 0)  # index() raises ValueError if absent
```

---

## 2. `windowed` / `windowed_iter` — `boltons.iterutils`

Sliding-window iteration over sequences.

```python
from boltons.iterutils import windowed, windowed_iter
```

### `windowed(src, size, fill=<unset>)`

Returns a **list** of tuples of length `size`, representing a sliding window over `src`.

```python
windowed(range(5), 3)
# [(0, 1, 2), (1, 2, 3), (2, 3, 4)]

windowed(range(3), 5)
# []   — src shorter than window; no tuples returned

windowed(range(5), 1)
# [(0,), (1,), (2,), (3,), (4,)]
```

### `windowed_iter(src, size, fill=<unset>)`

Generator version of `windowed`. Equivalent to `iter(windowed(src, size, fill=fill))`.

### Documented Properties (no-fill mode)

When `fill` is not provided:

1. **Window count**: `len(windowed(src, size)) == max(0, len(src) - size + 1)`

2. **Window content**: The `i`-th window (0-indexed) contains elements `src[i], src[i+1], ..., src[i+size-1]`:
   ```python
   windows = windowed(lst, size)
   for i, w in enumerate(windows):
       assert w == tuple(lst[i:i+size])
   ```

3. **First window**: When `len(src) >= size`, the first window equals `tuple(src[:size])`.

4. **Last window**: When `len(src) >= size`, the last window equals `tuple(src[len(src)-size:])`.

5. **Consecutive overlap**: Adjacent windows overlap by `size - 1` elements:
   ```python
   windows = windowed(lst, size)
   for i in range(len(windows) - 1):
       assert windows[i][1:] == windows[i+1][:-1]
   ```

6. **Empty src**: `windowed([], size)` returns `[]` for any `size >= 1`.

7. **Boundary case**: `windowed(lst, len(lst))` returns exactly one window `[tuple(lst)]` when `lst` is non-empty.

### `windowed` with `fill`

When `fill` is provided, the number of windows equals `len(src)`:

```python
windowed(range(4), 3, fill=None)
# [(0, 1, 2), (1, 2, 3), (2, 3, None), (3, None, None)]
```

---

## 3. `LRU` — `boltons.cacheutils`

A **Least-Recently-Used** cache with a fixed maximum size.

```python
from boltons.cacheutils import LRU
```

### Construction

```python
cache = LRU(max_size=128)    # default max size
cache = LRU(max_size=3)      # capacity 3
```

### LRU Semantics

The cache holds at most `max_size` key-value pairs. When a new key is inserted into a full cache, the **least recently used** entry is evicted.

"Recently used" means recently **read** (`cache[key]`) or **written** (`cache[key] = value`). Any access—read or write—promotes the key to the most-recently-used (MRU) position.

### Key Operations

#### `cache[key] = value` — Insert / Update

Inserts the key-value pair. If the key already exists, updates the value and promotes the key to MRU.

If the cache is at capacity and the key is new, the **LRU** (least recently used) entry is evicted first.

```python
cache = LRU(max_size=2)
cache['a'] = 1    # cache: {a:1}
cache['b'] = 2    # cache: {a:1, b:2} — full
cache['c'] = 3    # evicts 'a' (LRU), cache: {b:2, c:3}
```

#### `cache[key]` — Read

Returns the value associated with `key`. **Promotes** `key` to MRU position.

Raises `KeyError` if `key` is absent.

```python
cache = LRU(max_size=2)
cache['a'] = 1
cache['b'] = 2    # cache full
_ = cache['a']    # read 'a' → 'a' becomes MRU, 'b' becomes LRU
cache['c'] = 3    # evicts 'b' (now LRU), NOT 'a'
assert 'a' in cache   # True: 'a' survived because it was read
assert 'b' not in cache  # True: 'b' was evicted
```

#### `cache.get(key, default=None)`

Like `cache[key]` but returns `default` instead of raising `KeyError`. Does **not** promote the key on a miss.

#### `key in cache`

Returns `True` if `key` is present (does **not** affect LRU order).

### Eviction Invariant

The LRU invariant: at the moment of eviction, the entry removed is the one whose **last access time** (read or write) is the oldest among all current entries.

Formally, if we record a timestamp for every read and write operation, the evicted entry always has the smallest timestamp.

```python
# Correct LRU eviction pattern:
cache = LRU(max_size=N)
# fill cache with keys k_1, k_2, ..., k_N (in insertion order)
# access k_1 (it becomes MRU)
# insert k_{N+1} (triggers eviction)
# evicted key must be k_2, not k_1
```

### Statistics

```python
cache.hit_count        # number of successful reads via cache[key]
cache.miss_count       # number of KeyErrors raised by cache[key]
cache.soft_miss_count  # number of misses via cache.get() (no exception)
```

---

## Summary of Key Properties to Test

| Module | Property | Notes |
|--------|----------|-------|
| `IndexedSet` | `s[s.index(x)] == x` for all `x in s` | Must hold after any add/discard sequence |
| `IndexedSet` | `list(s) == [s[i] for i in range(len(s))]` | Iteration == indexing |
| `IndexedSet` | `set(a - b) == set(a) - set(b)` | Difference matches built-in set |
| `windowed` | `len(windowed(lst, k)) == max(0, len(lst) - k + 1)` | Window count formula |
| `windowed` | `windowed(lst, k)[i] == tuple(lst[i:i+k])` | Window content |
| `LRU` | Evicted key is the LRU key | Read promotes to MRU |
