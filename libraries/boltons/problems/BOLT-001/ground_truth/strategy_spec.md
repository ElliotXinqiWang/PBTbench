# BOLT-001 Strategy Specification

## Bug 1: `IndexedSet._get_apparent_index` — wrong sign

### Bug Summary

In `boltons/setutils.py`, the method `_get_apparent_index` converts a real
list index (physical position in `item_list`) into an apparent index (the
0-based user-visible position). The method subtracts the count of dead slots
that precede the real index:

```python
# Fixed (correct):
apparent_index -= d_stop - d_start

# Buggy (injected):
apparent_index += d_stop - d_start
```

With `+=`, the apparent index is inflated by the number of dead slots before
the element, instead of being deflated. For example, if element `x` is at
real position 5 and there is one dead slot at position 2, the correct
apparent index is 4, but the bug returns 6.

### Why Default Strategies Miss This Bug

A test that only calls `add()` and checks membership or iteration will never
see the bug, because dead indices are only created by `remove()` / `discard()`.
A test that only discards the last element also avoids the bug, because the
dead slot is at the end and there are no subsequent elements to be affected.

The bug is invisible unless:
1. An element is discarded that is NOT the last element, AND
2. `index()` is called on any element that appeared AFTER the discarded element.

Random `add`/`discard` sequences without targeted `index()` checks will miss
this entirely. The bug also doesn't affect `in` (containment) or iteration,
only `index()` — which tests must explicitly call.

### Targeted Strategy

1. Start with `IndexedSet` of ≥ 3 elements.
2. `discard()` a non-last element (e.g., element at position 0 or 1).
3. For every remaining element `x`, assert `s[s.index(x)] == x`.
4. Also assert `list(s) == [s[i] for i in range(len(s))]`.

Trigger probability: 100% whenever a non-last element is discarded.

### Boundary Value

Minimal reproducing input:

```python
s = IndexedSet([0, 1, 2])
s.discard(0)         # discard first; dead_indices = [[0, 1]]
assert s.index(1) == 0   # correct: 0; buggy: 2
assert s[s.index(1)] == 1  # fails under bug: s[2] is out of range
```

---

## Bug 2: `IndexedSet.difference()` — returns intersection

### Bug Summary

In `boltons/setutils.py`, the optimised single-other path of `difference()`:

```python
# Fixed (correct):
return self.from_iterable(k for k in self if k not in other)

# Buggy (injected):
return self.from_iterable(k for k in self if k in other)
```

The condition is negated, turning the difference into an intersection.

### Why Default Strategies Miss This Bug

Any test that calls `a - b` on two **disjoint** sets will not see the bug:
if `a` and `b` share no elements, both the difference and the intersection
equal `a`, so both implementations return the same result.

The bug only manifests when `a` and `b` share at least one element AND `a`
has at least one element not in `b`.

### Targeted Strategy

1. Generate `shared`: elements in both `a` and `b`.
2. Generate `only_a`: elements unique to `a`.
3. Generate `only_b`: elements unique to `b` (optional).
4. Assert `set(a - b) == set(only_a)` and `all(x not in b for x in (a - b))`.

Trigger probability: 100% whenever `shared` is non-empty and `only_a` is non-empty.

### Boundary Value

Minimal reproducing input:

```python
a = IndexedSet([1, 2])
b = IndexedSet([2, 3])
result = a - b
# Correct: IndexedSet([1])
# Buggy:   IndexedSet([2])  (the intersection)
assert set(result) == {1}
```

---

## Bug 3: `windowed_iter` — off-by-one in tee advancement

### Bug Summary

In `boltons/iterutils.py`, the no-fill path of `windowed_iter` uses
`itertools.tee` and then advances each copy by `i` steps:

```python
# Fixed (correct):
for i, t in enumerate(tees):
    for _ in range(i):
        next(t)

# Buggy (injected):
for i, t in enumerate(tees):
    for _ in range(i + 1):
        next(t)
```

With `range(i + 1)`, each tee is advanced one extra step. For `i=0` (the first
tee), this advances 1 element instead of 0. All tees are shifted forward by one
position relative to the correct alignment, so all windows start one element
later. The first window `(lst[0], lst[1], ..., lst[size-1])` is missing, and
the total window count is one short of correct.

### Why Default Strategies Miss This Bug

Any test that only checks whether the returned list is non-empty will miss the
bug when `len(src) > size` (there are still some windows returned, just fewer).

A test that checks window *content* at index 0 will catch it, as will a test
that checks the exact count.

### Targeted Strategy

1. Generate a list of length `n >= size` (use `n = size` for the minimal case).
2. Call `windowed(lst, size)`.
3. Assert `len(result) == n - size + 1`.
4. Assert `result[0] == tuple(lst[:size])` (first window must start at index 0).

Trigger probability: 100% whenever `len(lst) >= size`.

### Boundary Value

Minimal reproducing input:

```python
lst = [10, 20, 30]
windows = windowed(lst, 3)
# Correct: [(10, 20, 30)]  — 1 window
# Buggy:   []              — 0 windows (StopIteration on i=0 extra advance)
assert len(windows) == 1
assert windows[0] == (10, 20, 30)
```

---

## Bug 4: `LRU.__getitem__` — does not update LRU position

### Bug Summary

In `boltons/cacheutils.py`, `LRU.__getitem__` overrides `LRI.__getitem__` to
call `_get_link_and_move_to_front_of_ll`, which splices the accessed node out
of the linked list and reinserts it at the MRU position (immediately before the
sentinel anchor).

The bug replaces this with a plain dict lookup:

```python
# Fixed (correct):
link = self._get_link_and_move_to_front_of_ll(key)

# Buggy (injected):
link = self._link_lookup[key]
```

The buggy version still returns the correct value, but does not update the
node's position in the linked list. The cache now behaves like an LRI (Least
Recently Inserted) cache: eviction order is insertion order, regardless of
subsequent reads.

### Why Default Strategies Miss This Bug

Any test that never reads a key (only writes) will not detect the bug, because
writes do update the LRU position. A test that reads but never checks which key
was evicted (only checks the value of a surviving key) will also miss it.

The bug requires:
1. The cache is at full capacity.
2. An existing key is **read** (not written).
3. A new key is **inserted**, triggering eviction.
4. The test **asserts** that the read key survived (and a non-read key was evicted).

### Targeted Strategy

1. `cache = LRU(max_size=2)`.
2. `cache['a'] = 1; cache['b'] = 2` (fill to capacity).
3. `_ = cache['a']` (read `a` → `a` should become MRU, `b` becomes LRU).
4. `cache['c'] = 3` (insert `c` → should evict `b`).
5. Assert `'a' in cache` and `'b' not in cache`.

Trigger probability: 100% for this exact sequence.

### Boundary Value

```python
cache = LRU(max_size=2)
cache['a'] = 1
cache['b'] = 2
_ = cache['a']   # 'a' should now be MRU
cache['c'] = 3   # triggers eviction
# Correct: 'b' evicted (LRU), 'a' survives
# Buggy:   'a' evicted (still at front of insertion order despite read)
assert 'a' in cache
assert 'b' not in cache
```

---

## SAS Estimates

| Bug | Default Strategy Trigger % | Targeted Strategy Trigger % |
|-----|---------------------------|----------------------------|
| Bug 1 (index after discard) | ~0% | 100% |
| Bug 2 (difference → intersection) | ~0% for disjoint sets; ~60% with overlap | 100% |
| Bug 3 (windowed off-by-one) | ~0% (count check not obvious) | 100% |
| Bug 4 (LRU no position update) | ~0% | 100% |
