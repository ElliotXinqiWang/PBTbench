# setutils - IndexedSet Type
# Source: https://boltons.readthedocs.io/en/latest/setutils.html
# boltons version: 25.0.0

## Overview

The `setutils` module provides an `IndexedSet` type that addresses limitations in Python's built-in `set` type. As noted in the documentation, "sets are not ordered" and "sets are not indexable," meaning operations like `my_set[8]` would raise a `TypeError`.

## IndexedSet Class

**boltons.setutils.IndexedSet(_other=None_)**

`IndexedSet` is a `collections.MutableSet` maintaining "insertion order and uniqueness of inserted elements." It functions as a hybrid between an ordered set and a list, supporting both set operations and indexing.

### Parameters

- **other** (iterable): An optional iterable to initialize the set.

### Example Usage

```python
x = IndexedSet(list(range(4)) + list(range(8)))
# Returns: IndexedSet([0, 1, 2, 3, 4, 5, 6, 7])

x - set(range(2))
# Returns: IndexedSet([2, 3, 4, 5, 6, 7])

x[-1]  # Returns: 7

fcr = IndexedSet('freecreditreport.com')
''.join(fcr[:fcr.index('.')])  # Returns: 'frecditpo'
```

### Core Methods

| Method | Description |
|--------|-------------|
| `add(item)` | Add item to the set |
| `clear()` | Empty the set |
| `count(val)` | Count instances of value (0 or 1) |
| `difference(*others)` | Get new set with elements not in others |
| `difference_update(*others)` | Discard self.intersection(*others) |
| `discard(item)` | Remove item without raising if absent |
| `from_iterable(it)` | Create set from iterable (classmethod) |
| `index(val)` | Get index of value, raises if absent |
| `intersection(*others)` | Get set with overlap |
| `intersection_update(*others)` | Discard self.difference(*others) |
| `isdisjoint(other)` | Return True if no overlap |
| `issubset(other)` | Return True if other contains this set |
| `issuperset(other)` | Return True if set contains other |
| `iter_difference(*others)` | Iterate over elements not in others |
| `iter_intersection(*others)` | Iterate over elements also in others |
| `iter_slice(start, stop, step=None)` | Iterate over a slice |
| `pop(index)` | Remove item at index (-1 by default) |
| `remove(item)` | Remove item, raises if absent |
| `reverse()` | Reverse contents in-place |
| `sort()` | Sort contents in-place |
| `symmetric_difference(*others)` | XOR set of this and others |
| `symmetric_difference_update(other)` | In-place XOR with other |
| `union(*others)` | Return new set containing this and others |
| `update(*others)` | Add values from iterables |

### Design Notes

The documentation explains why `__setitem__()` is not supported: "if you set an element at an index to a value already elsewhere in the set, the set's size would change unpredictably," violating list-like indexing expectations.

The API "strives to be as complete a union of the list and set APIs as possible" while maintaining set semantics.

## complement() Function

**boltons.setutils.complement(_wrapped_)**

This function "convert[s] it to a **complement set**" that "keeps track of what it does _not_ contain" rather than what it contains.

### Example

```python
list(set(range(5)) & complement(set([2, 3])))
# Returns: [0, 1, 4]
```

### Characteristics

- Supports all set methods and operators with other complement or regular sets
- Cannot use: `len()`, `iter()`, loops, or `.pop()`
- Can be inverted by complementing again: `complement(complement(s)) == s`
- An empty complement set represents the universal set mathematically

### Use Case Example

Rather than enumerating all allowed names:

```python
NamesFilter(complement(set()))
```

This expression is "short and robust" while making programmer intention "expressed succinctly and directly."
