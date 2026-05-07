# Strategy Specification — SRTD-004

## Bug 1: _delete() B-tree positional index corruption

**Trigger condition**: SortedList must have >= 3 sublists so that `_index` is non-empty. With `DEFAULT_LOAD_FACTOR=1000`, this requires 2001+ unique elements (3 sublists of ~1000 each). When `_delete()` is called, `child = self._offset + pos + 1` decrements the wrong sibling leaf node. Specifically:
- With 3 sublists (sizes 1000, 1000, 1) and `_offset=3`, the leaves are at index positions 3, 4, 5 in `_index`.
- Deleting from sublist at `pos=1`: correct `child = 3+1 = 4` (leaf for sublist 1), buggy `child = 3+1+1 = 5` (leaf for sublist 2).
- This decrements `_index[5]` (sublist 2's count) from 1 to 0 instead of decrementing `_index[4]` (sublist 1's count) from 1000 to 999.
- After corruption: `_pos(1999)` traverses the tree and computes `(1, 999)` — but `_lists[1]` only has 999 elements after the deletion, so index 999 is out of range → `IndexError`.

**Why default strategy fails**: Default `st.lists(st.integers())` generates lists of 0-100 elements, far below the 2001-element threshold needed for 3 sublists. Trigger probability: ~0%.

**Trigger probability with targeted strategy**: 100% for any permutation of range(2001) with `pop_idx` in range [1001, 1995].

**Minimum triggering input**:
```python
sl = SortedList(range(2001))  # 3 sublists: [0..999], [1000..1999], [2000]
sl.pop(1500)                  # corrupts _index[5] (sublist 2's leaf count → 0)
sl[1999]                      # IndexError: _pos(1999) → (1, 999), but _lists[1] has 999 items
```

**Note on strategy**: `st.permutations(range(2001))` is used instead of `st.lists(..., unique=True)` because Hypothesis cannot efficiently generate 2001 unique random integers (causes `data_too_large` health check failure). The permutation strategy generates exactly 2001 unique integers efficiently. Health checks `data_too_large` and `large_base_example` are suppressed.

## Bug 2: _expand() sets wrong _maxes[pos] after split

**Trigger condition**: A single sublist must accumulate > `2 * load` elements, causing `_expand()` to split it. The left half's maximum is incorrectly set to `_lists_pos[0]` (minimum) instead of `_lists_pos[-1]` (maximum). Any subsequent `add(v)` where `min_left < v <= max_left` then uses `bisect_right(_maxes, v)` which returns a sublist index one too far to the right, inserting `v` into the wrong sublist.

**Using `_reset(4)`**: With `_load = 4`, splits fire when any sublist exceeds 8 elements. After adding 9+ elements (one element per `add()` call), the first split corrupts `_maxes[0]`. Any element in the range `(min_left, max_left]` subsequently added will land in the wrong sublist, breaking sorted order.

**Why default strategy fails**: Default strategies generate small lists (<100 elements). With `DEFAULT_LOAD_FACTOR=1000`, the split never fires. Trigger probability: ~0%.

**Trigger probability with targeted strategy**: ~100% — any 25-element unique list with `_reset(4)` forces multiple splits. Subsequent adds of values in the left-half range (very likely to occur) then expose the corrupted `_maxes`.

**Minimum triggering input**:
```python
sl = SortedList()
sl._reset(4)
for i in range(9):  # 9 elements: forces split at element 9
    sl.add(i)
# _maxes[0] = 0 (wrong, should be 3)
sl.add(2)  # bisect_right([0, ...], 2) = 1 → wrong sublist
assert list(sl) == sorted(list(sl))  # FAILS
```

## Bug 3: irange() includes exclusive maximum at sublist boundary

**Trigger condition**: (1) SortedList must have at least 2 sublists. (2) `irange(min, max, inclusive=(True, False))` must be called with `max == _maxes[k]` for some sublist index `k`. The buggy `bisect_right(_maxes, max)` returns `k+1`, causing the slice to include all of sublist `k` (including its maximum element `max`), even though `inclusive[1]=False` should exclude it.

**Using `_reset(4)`**: With 20+ unique elements and `_load=4`, multiple sublists form. Setting `maximum = sl._maxes[0]` guarantees the boundary condition fires on every test example.

**Why default strategy fails**: Random `maximum` values rarely coincide with a sublist maximum. With `DEFAULT_LOAD_FACTOR=1000`, two sublists require 1001+ elements. Trigger probability: ~0.1%.

**Trigger probability with targeted strategy**: ~100% — `maximum = sl._maxes[0]` ensures exact boundary hit every time.

**Minimum triggering input**:
```python
sl = SortedList()
sl._reset(4)
for v in range(20):
    sl.add(v)
# _maxes = [3, 7, 11, 15, 19] with load=4
max_val = sl._maxes[0]  # = 3
result = list(sl.irange(0, max_val, inclusive=(True, False)))
# Expected: [0, 1, 2] (excluding 3)
# Buggy: [0, 1, 2, 3] (includes 3 because max_pos = bisect_right([3,7,...], 3) = 1)
```

## Bug 4: bisect_left() returns position after equal values

**Trigger condition**: Any SortedList with at least one element. `bisect_left(x)` uses `bisect_right` internally to search within the sublist, so it returns the index AFTER all equal values. For any `x` present in `sl`:
- Correct: `sl.bisect_left(x)` = index of first occurrence of `x`
- Buggy: `sl.bisect_left(x)` = index after last occurrence of `x` (same as `bisect_right`)
- Violation: `sl[sl.bisect_left(x)]` should equal `x` but returns the next element instead

**Why default strategy fails**: Most agents don't explicitly test `bisect_left`. This is a secondary API. However, any test that calls `bisect_left(x)` for a value `x` in the list immediately exposes the bug.

**Trigger probability with targeted strategy**: 100% — any list with at least one element. The property `sl[sl.bisect_left(v)] == v` fails for every element.

**Minimum triggering input**:
```python
sl = SortedList([1, 2, 3])
bl = sl.bisect_left(2)   # buggy: returns 2 (bisect_right behavior)
assert sl[bl] == 2       # FAILS: sl[2] = 3 != 2
# Also: bisect_right(2) - bisect_left(2) = 2 - 2 = 0 != count(2) = 1
```
