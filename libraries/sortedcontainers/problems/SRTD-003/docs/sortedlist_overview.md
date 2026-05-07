# SortedList Concepts and Implementation Notes

## Definition

`SortedList` is a mutable sequence container that automatically maintains a sorted invariant. All elements added to a SortedList are stored and accessed in sorted order.

## Core Sorted Invariants

1. **Sorting invariant**: `list(sl)[i] <= list(sl)[i+1]` holds for all valid indices
2. **Membership consistency**: For any added element `x`, `x in sl` must return `True`
3. **Count consistency**: `sl.count(x)` equals the number of times `x` has been added to sl

## Internal Implementation: Bucket Structure

SortedList does not use a single list; instead it organizes elements into several **sorted buckets (sublists)**:

```
_lists  = [[sublist_0], [sublist_1], ...]   # actual elements, each bucket is internally sorted
_maxes  = [max_0,       max_1,      ...]    # maximum value of each bucket (used for fast routing)
```

`_maxes` is the routing index for buckets: when looking up element `x`, first use `bisect_left(_maxes, x)` to find the correct bucket, then binary search within that bucket.

## DEFAULT_LOAD_FACTOR = 20

`DEFAULT_LOAD_FACTOR` (default value **20**) controls the target bucket size:

- When a bucket's element count exceeds `2 * DEFAULT_LOAD_FACTOR = 40`, the bucket is **automatically split** into two
- The split operation is called `_expand(pos)`, which keeps the left half (first 20 elements) in place and inserts the right half (elements 21+) as a new bucket
- After splitting, **`_maxes[pos]` must be updated to the maximum value of the left bucket after the split** (i.e., the last element of the left bucket), to ensure routing correctness

## Conditions That Trigger a Split

Elements are added one at a time via the `add()` method, each inserted into the correct bucket while maintaining sorted order:
- If the bucket size > 40 after insertion, `_expand` runs automatically
- Initialization (`__init__` / `update`) uses a bulk path that directly partitions elements into buckets of size no larger than `DEFAULT_LOAD_FACTOR`, **without going through `_expand`**

## Practical Example

```python
from sortedcontainers import SortedList

# Small list: always within a single bucket, no split needed
sl = SortedList()
for x in range(40):
    sl.add(x)   # at most 40 elements, does not trigger _expand

# Large list: _expand is triggered after the 41st add()
for x in range(41):
    sl.add(x)   # the 41st insertion makes the bucket size 41 > 40, triggering a split
assert 20 in sl  # must be True regardless of whether the split was correct
```

## Invariant Verification

For any correct SortedList implementation, the following properties must hold for all inputs:

```python
# P1: Membership invariant
assert all(x in sl for x in added_elements)

# P2: Sorting invariant
assert list(sl) == sorted(added_elements)

# P3: Count consistency
from collections import Counter
ref = Counter(added_elements)
assert all(sl.count(x) == ref[x] for x in ref)

# P4: bisect consistency with sorted()
sorted_data = sorted(added_elements)
for x in added_elements:
    assert sl.bisect_left(x) == bisect.bisect_left(sorted_data, x)
```
