# pyrsistent PBag and PList — Official API Documentation

## PBag

`PBag` is a persistent multiset (bag) that allows duplicate elements. Elements must
be hashable. PBag tracks multiplicities: adding the same element multiple times results
in multiple "copies" in the bag, reflected in counts.

### Factory functions

```python
pbag(iterable)  # Convert an iterable to a PBag
b(*elements)    # Construct a PBag from positional arguments
```

### Methods

#### `add(element) -> PBag`
Return a new PBag with `element` added (count increased by 1).

```python
>>> pbag([1, 2]).add(2)
pbag([1, 2, 2])
```

#### `remove(element) -> PBag`
Return a new PBag with one copy of `element` removed (count decreased by 1).
Raises `KeyError` if `element` is not in the bag.

```python
>>> pbag([1, 1, 2]).remove(1)
pbag([1, 2])
```

#### `update(iterable) -> PBag`
Return a new PBag containing all elements from self plus all elements in `iterable`.
The returned bag has counts equal to self's counts plus iterable's counts.
Elements present in self but not in iterable are preserved unchanged.

```python
>>> pbag([1]).update([1, 2])
pbag([1, 1, 2])
>>> pbag([1, 2]).update([3])
pbag([1, 2, 3])
```

#### `count(element) -> int`
Return the number of times `element` appears in the bag. Returns 0 if not present.

```python
>>> pbag([1, 1, 2]).count(1)
2
>>> pbag([1, 2]).count(3)
0
```

### Set-like operations

PBag supports multiset algebra. All operations return new PBag instances.

#### Addition: `a + b`
Returns a new PBag where each element's count is the sum of its counts in `a` and `b`.

```python
>>> pbag([1, 2, 2]) + pbag([2, 3])
pbag([1, 2, 2, 2, 3])
```

**Property**: `len(a + b) == len(a) + len(b)`
**Property**: `a + b == b + a` (commutativity)

#### Subtraction: `a - b`
Returns a new PBag where each element's count is `max(0, count_a - count_b)`.
Elements fully consumed (count becomes 0 or negative) are removed.
Elements in `b` but not in `a` are ignored.

```python
>>> pbag([1, 2, 2, 2, 3]) - pbag([2, 3, 3, 4])
pbag([1, 2, 2])
```

**Property**: For each element `e`, `(a - b).count(e) == max(0, a.count(e) - b.count(e))`
**Property**: If `a.count(e) >= b.count(e)` for all `e`, then `(a - b) + b == a`

#### Union: `a | b`
Returns a new PBag where each element's count is the maximum of its counts in `a` and `b`.

```python
>>> pbag([1, 2, 2, 2]) | pbag([2, 3, 3])
pbag([1, 2, 2, 2, 3, 3])
```

**Property**: `a | b == b | a` (commutativity)
**Property**: `a | a == a` (idempotency)
**Property**: `a | b` contains all elements from both `a` and `b`

#### Intersection: `a & b`
Returns a new PBag where each element's count is the minimum of its counts in `a` and `b`.
Elements that appear in only one of the bags are excluded from the result.

```python
>>> pbag([1, 2, 2, 2]) & pbag([2, 3, 3])
pbag([2])
```

**Property**: `a & b == b & a` (commutativity)
**Property**: `a & a == a` (idempotency)
**Property**: Every element `e` in `a & b` must satisfy `e in a and e in b`
**Property**: `(a & b).count(e) == min(a.count(e), b.count(e))` for all `e`
**Property**: Elements only in `a` (not in `b`) must not appear in `a & b`
**Property**: `len(a & b) <= min(len(a), len(b))`

### Container protocol

- `len(bag)` returns total count including duplicates
- `e in bag` returns True if element has count > 0
- `iter(bag)` yields each element once per occurrence (unordered)
- PBags are hashable: `hash(pbag([1, 2, 2])) == hash(pbag([2, 1, 2]))`

---

## PList

`PList` is a persistent singly-linked list (Lisp-style cons list). It supports O(1)
prepend via `cons()` and O(k) random access where k is the position.

### Factory functions

```python
plist(iterable, reverse=False)  # Create PList from iterable
l(*elements)                    # Create PList from positional arguments
```

### Properties and Methods

#### `first`
The head element of the list. Raises `AttributeError` on an empty list.

#### `rest`
The tail of the list (a PList without the head). For an empty list, returns itself.

#### `cons(elem) -> PList`
Return a new PList with `elem` prepended as the new head. O(1).

```python
>>> plist([1, 2]).cons(3)
plist([3, 1, 2])
```

#### `mcons(iterable) -> PList`
Return a new PList with all elements of `iterable` repeatedly cons-ed to the front.
**Important**: elements are inserted in reverse order of iteration.

```python
>>> plist([1, 2]).mcons([3, 4])
plist([4, 3, 1, 2])
```

#### `reverse() -> PList`
Return a reversed copy of the list. O(n).

```python
>>> plist([1, 2, 3]).reverse()
plist([3, 2, 1])
```

#### `split(index) -> (PList, PList)`
Split the list at `index`. Returns `(left, right)` where `left` contains the first
`index` elements and `right` contains the rest. O(index).

```python
>>> plist([1, 2, 3, 4]).split(2)
(plist([1, 2]), plist([3, 4]))
```

#### `remove(elem) -> PList`
Return a new list with the **first** occurrence of `elem` removed. O(k).
Raises `ValueError` if `elem` is not found.

```python
>>> plist([1, 2, 1]).remove(1)
plist([2, 1])
```

**Property**: The returned list has exactly one fewer occurrence of `elem` than the original.
**Property**: All elements before the first `elem` are preserved in order.
**Property**: All elements after the first `elem` are preserved in order.

#### `__getitem__(index)` — Indexing
Supports both positive and negative indices.

- `pl[k]` for `k >= 0`: returns element at position `k` (0-based). O(k).
- `pl[-k]` for `k >= 1`: returns element at position `len(pl) - k`.
  - `pl[-1]` is the **last** element.
  - `pl[-2]` is the second-to-last element.
  - `pl[-len(pl)]` is the first element (same as `pl[0]`).

```python
>>> pl = plist([10, 20, 30])
>>> pl[0]
10
>>> pl[-1]
30
>>> pl[-2]
20
```

**Property**: `pl[i] == pl[len(pl) + i]` for all negative `i` in `[-len(pl), -1]`
**Property**: `pl[-1]` is the last element
**Property**: `pl[-k] == list(pl)[-k]` for all valid negative indices

#### `__len__()`
Returns the total number of elements. O(n) (traversal required).

#### `__iter__()`
Iterate over all elements in order. O(n).

#### `__hash__()`
PList is hashable. Equal lists have the same hash.

### Sequence protocol

PList implements `collections.abc.Sequence` and `Hashable`:
- Supports `index(elem)`, `count(elem)` from Sequence mixin
- Supports slicing (falls back to `tuple(self)[slice]` for most cases)
- Supports `in` operator via `__contains__`
- Supports `reversed(pl)` (calls `reverse()`)
