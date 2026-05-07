# SRTD-005 Strategy Specification

## Bug 1: `_build_index` offset off-by-one

**Location**: `sortedcontainers/sortedlist.py:761`, `SortedList._build_index()`

**Bug**: `self._offset = size * 2 - 1` changed to `self._offset = size * 2` (off by one).

**Trigger Condition**:
- SortedList must have at least 3 sublists such that `row1` has length > 1,
  reaching the `size = 2 ** (int(log(len(row1) - 1, 2)) + 1)` computation.
- A positional access (`sl[k]`) must be performed AFTER `_index` has been cleared
  (which happens after any split or merge), so `_build_index()` is called.
- The accessed position `k` must be beyond the first sublist.

**Default Strategy Trigger Probability**: ~0%
- Hypothesis generates lists of ~10-50 elements with default load=1000.
- With 1000 elements per sublist, you need 2001+ elements for 2+ sublists,
  and 3001+ for 3 sublists where `len(row1) > 1`.
- Default strategies never reach this threshold.

**Targeted Strategy**:
- Use `sl._reset(4)` to set load=4, which causes splits at 9 elements.
- With 20-50 unique elements and load=4, the list has 4-12 sublists.
- With 3+ sublists, `row0` has 3+ entries, `row1` has 2+ entries (after pairing),
  and `len(row1) > 1`, so the full `size` computation runs.
- Accessing `sl[k]` for any k beyond the first sublist (k >= 5 with load=4)
  triggers `_pos(k)` -> `_build_index()` with wrong offset.

**Minimum Trigger Input**:
- `xs = [0, 1, 2, ..., 19]`, `_reset(4)`, then `sl[7]` — this creates 4 sublists
  and accesses position 7 (in sublist 1), triggering the offset bug.

**Expected Test Failure Mode**:
- `sl[k]` returns the element from the wrong sublist, or raises `IndexError`
  when the computed (sublist, idx) is out of bounds.

---

## Bug 2: `_delete` sublist merge direction reversed

**Location**: `sortedcontainers/sortedlist.py:504`, `SortedList._delete()`

**Bug**: `_lists[prev].extend(_lists[pos])` changed to `_lists[pos].extend(_lists[prev])`.

**Trigger Condition**:
1. The SortedList must have at least 2 sublists (multiple sublists).
2. A deletion must cause a sublist to fall below `load/2` elements, triggering
   the merge branch (`elif len(_lists) > 1:`).
3. With DEFAULT_LOAD_FACTOR=1000, threshold is 500 elements — practically impossible
   with typical test lists (< 100 elements).

**Default Strategy Trigger Probability**: ~0%
- Small lists (< 1000 elements) form only 1 sublist; the merge branch never fires.
- Only very large lists (1000+ elements with deletions) would trigger this.

**Targeted Strategy**:
- Use `sl._reset(4)` to set load=4: merge threshold becomes 2 elements.
- Build a list of 20-50 unique integers → creates 4-12 sublists.
- Delete 3-6 elements from the smallest sublist to trigger a merge.
- Verify `list(sl)` equals the expected remaining elements.
- `list(sl)` uses `chain.from_iterable(sl._lists)` — independent of `_offset`,
  so this test is unaffected by bug_1.

**Minimum Trigger Input**:
- `sl = SortedList(range(20))` with `_reset(4)` creates 4 sublists.
- Deleting the first 4 elements (0, 1, 2, 3) leaves the first sublist with
  1 element (if it had 5), triggering the merge. `list(sl)` should be `[4..19]`
  but the bug drops elements.

**Expected Test Failure Mode**:
- `list(sl)` is shorter than expected after deletions.
- Elements from the absorbed sublist disappear from the list.

---

## Bug 3: `irange` exclusive-minimum uses `bisect_left` instead of `bisect_right`

**Location**: `sortedcontainers/sortedlist.py:1126`, `SortedList.irange()`

**Bug**: `bisect_right(_lists[min_pos], minimum)` changed to `bisect_left(...)`.

**Trigger Condition**:
1. `irange()` must be called with `inclusive[0]=False` (exclusive minimum).
2. The minimum value must be present in the SortedList.
3. There must be at least one occurrence of minimum in the list
   (so `bisect_left` and `bisect_right` differ).

With these conditions, `bisect_right` points past the minimum (correct:
exclude it), while `bisect_left` points to it (buggy: include it).

**Default Strategy Trigger Probability**: ~5%
- An agent testing `irange` with exclusive min and a value that happens to be
  in the list will find the bug. But many agents test with non-present values.

**Targeted Strategy**:
- Build `sl = SortedList(xs)` with any non-empty xs.
- Pick `min_val` in xs (guaranteed to be in sl by construction).
- Call `sl.irange(min_val, max(sl), inclusive=(False, True))`.
- Assert no element in result equals `min_val`.
- This test uses `in sl` via `__contains__` and `sl._maxes[-1]` — both
  independent of `_pos()`/`_offset` (bug_1 safe).

**Minimum Trigger Input**:
- `sl = SortedList([1, 2, 3, 4, 5])`, `sl.irange(2, 5, inclusive=(False, True))`
  should return `[3, 4, 5]`. With the bug, returns `[2, 3, 4, 5]`.

**Expected Test Failure Mode**:
- `irange(v, max, inclusive=(False, True))` yields `v` in its output.
- The result has one too many elements (includes minimum).

---

## Bug 4: `SortedDict.popitem` returns `(value, key)` instead of `(key, value)`

**Location**: `sortedcontainers/sorteddict.py:480`, `SortedDict.popitem()`

**Bug**: `return (key, value)` changed to `return (value, key)`.

**Trigger Condition**:
- Any call to `SortedDict.popitem(index)` where the caller examines which
  element of the returned tuple is the key and which is the value.
- Both `popitem(0)` (first/smallest key) and `popitem(-1)` (last/largest key)
  are affected.

**Default Strategy Trigger Probability**: ~20%
- Agents who test `popitem` and check the return value order will find this.
- Some agents may call `popitem` but not validate the key/value positions.

**Targeted Strategy**:
- `sd = SortedDict({k: v, ...})` with known key-value pairs.
- `result = sd.popitem(0)`.
- Assert `result[0] == min(sd_keys)` (the key) and `result[1] == sd[min_key]`.
- With the bug: `result[0]` is the value, `result[1]` is the key.

**Minimum Trigger Input**:
- `sd = SortedDict({1: 100, 2: 200})`.
- `sd.popitem(0)` should return `(1, 100)`. Bug returns `(100, 1)`.
