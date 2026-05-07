# Multiset 3.2.0 — Official API Documentation

> Source: https://multiset.readthedocs.io/en/latest/
> Version: multiset 3.2.0

## Overview

The `multiset` library provides a data structure similar to Python's built-in `set`, but allowing elements to appear multiple times. It uses a dictionary internally where keys are elements and values represent their count (multiplicity).

**Key Difference from `collections.Counter`:** "no negative counts are allowed, elements with zero counts are removed from the dict, and set operations are supported."

Elements must be hashable. The underlying implementation uses a dictionary mapping elements to their multiplicities.

---

## Constructor

**`Multiset([mapping or iterable])`**

Creates a new multiset from an optional iterable or mapping. Mappings must contain positive integer values representing multiplicities. Returns an empty multiset if no argument is provided.

Examples:
- Empty: `Multiset()`
- From iterable: `Multiset('abc')`
- From mapping: `Multiset({'a': 4, 'b': 2})`

---

## Set Operations (Non-Mutating)

### `combine(*others)` / `+` operator

**Return a new multiset with elements from the multiset and all others. Each element's multiplicities are summed up for the new set.**

```python
ms = Multiset('aab')
sorted(ms.combine('bc'))  # ['a', 'a', 'b', 'b', 'c']
```

Also supports `+` operator with multisets only.

### `difference(*others)` / `-` operator

"Return a new multiset with elements in the multiset that are not in the others." Subtracts multiplicities and removes elements reaching zero multiplicity.

```python
ms = Multiset('aab')
sorted(ms.difference('bc'))  # ['a', 'a']
```

### `intersection(*others)` / `&` operator

"Return a new multiset with elements common to the multiset and all others. The minimal multiplicity over all sets is used for each element."

```python
ms = Multiset('aab')
sorted(ms.intersection('abc'))  # ['a', 'b']
```

### `union(*others)` / `|` operator

"Return a new multiset with elements from the multiset and all others. The maximal multiplicity over all sets is used for each element."

```python
ms = Multiset('aab')
sorted(ms.union('bc'))  # ['a', 'a', 'b', 'c']
```

### `symmetric_difference(other)` / `^` operator

"Return a new multiset with elements from either the multiset or other where their multiplicity is the absolute difference of the two multiplicities."

```python
ms = Multiset('aab')
sorted(ms.symmetric_difference('abc'))  # ['a', 'c']
```

### `times(factor)` / `*` operator

"Return a copy of the multiset where each multiplicity is multiplied by factor."

```python
ms = Multiset('aab')
sorted(ms.times(2))  # ['a', 'a', 'a', 'a', 'b', 'b']
```

---

## Subset / Superset Tests

### `issubset(other)` / `<=`

Tests whether each element's multiplicity in the multiset is less than or equal to its multiplicity in the other.

### `issuperset(other)` / `>=`

Tests whether each element's multiplicity in the other is less than or equal to its multiplicity in the multiset.

### `isdisjoint(other)`

"Return `True` if the multiset has no elements in common with other."

---

## Mutating Operations (Class: `Multiset`)

### `add(element, multiplicity=1)`

Adds an element with a specified multiplicity (default 1).

```python
ms = Multiset()
ms.add('a')
ms.add('b', 2)  # Add 'b' twice
```

### `remove(element, multiplicity=None)`

Removes all instances of an element or a specified multiplicity. Raises `KeyError` if element absent. Without multiplicity arg, removes all occurrences. Returns previous multiplicity.

```python
ms = Multiset('aabbbc')
ms.remove('a')      # Removes all 'a's (returns 2)
ms.remove('b', 2)   # Removes 2 'b's
```

### `discard(element, multiplicity=None)`

Like `remove()` but doesn't raise error if absent. Returns previous multiplicity (or 0 if not found).

```python
ms = Multiset('a')
ms.discard('b')  # Returns 0, no error
```

### `pop(element, default)`

Removes element and returns multiplicity, or returns default if absent.

### `clear()`

"Remove all elements from the multiset."

### `setdefault(element, default)`

Returns multiplicity if present; otherwise adds with default multiplicity and returns it.

### `update(*others)` / `+=` operator

"Update the multiset, adding elements from all others. Each element's multiplicities is summed up for the new multiset." (In-place version of `combine`.)

```python
ms = Multiset('aab')
ms.update('abc')
sorted(ms)  # ['a', 'a', 'a', 'b', 'b', 'c']
ms.update(a=1, e=2)  # Keyword arguments also supported
```

### `union_update(*others)` / `|=` operator

Updates the multiset using maximal multiplicities from all arguments.

### `intersection_update(*others)` / `&=` operator

Updates the multiset using minimal multiplicities from all arguments.

### `difference_update(*others)` / `-=` operator

Updates the multiset by subtracting multiplicities from other multisets.

### `symmetric_difference_update(other)` / `^=` operator

Updates the multiset with absolute differences of multiplicities.

### `times_update(factor)` / `*=` operator

Updates the multiset by multiplying all multiplicities by the factor.

---

## Dictionary-like Access

- **`s[element]`** — Returns multiplicity (0 if absent)
- **`s[element] = value`** — Sets multiplicity directly
- **`del s[element]`** — Removes element
- **`get(element, default)`** — Returns multiplicity or default value
- **`pop(element, default)`** — Removes and returns multiplicity
- **`popitem()`** — Removes and returns arbitrary `(element, multiplicity)` pair
- **`setdefault(element, default)`** — Returns multiplicity or inserts with default

---

## Iteration and Views

### `iter(s)`

"Return an iterator over the elements in the multiset" that repeats elements according to their multiplicity.

### `distinct_elements()` / `keys()`

"Return a new view of the multiset's distinct elements."

### `items()`

"Return a new view of the multiset's items (`(element, multiplicity)` pairs)."

### `multiplicities()` / `values()`

"Return a new view of the multiset's multiplicities."

---

## Utility Methods

### `copy()` / `Multiset(multiset)`

"Return a new shallow copy of the multiset."

### `from_elements(elements, multiplicity)` (classmethod)

"Create a new multiset with elements from elements and all multiplicities set to multiplicity."

### `len(s)`

Returns total count of all elements (sum of multiplicities), not distinct count.

---

## Special Handling

### Zero Multiplicities

**"Elements with a zero multiplicity are automatically removed from the multiset."**

This is a critical design feature: when an operation results in an element having zero count, that element is removed from the internal dictionary. This differs from `collections.Counter`, which retains zero-count entries.

### Negative Multiplicities

The package "only allows positive counts" — negative multiplicities are not permitted. This is a key distinction from `collections.Counter`, which allows negative counts.

### Mixed Operations

Binary operations mixing sets with multisets return `Multiset` instances.

---

## Immutable Version: `FrozenMultiset`

**`FrozenMultiset([mapping or iterable])`**

An immutable, hashable variant of `Multiset`. Supports all non-mutating methods from `BaseMultiset` but cannot be modified after creation. Can be used as a dictionary key.

---

## Key Implementation Details

- **Internal Storage:** Dictionary-based (`element → multiplicity` mapping)
- **Zero Counts:** Elements with zero multiplicity are automatically removed from internal storage
- **Negative Values:** Not permitted; the implementation enforces positive counts
- **Generic Support:** Supports type hints via `Generic[_TElement]`
- **Base Class:** Both `Multiset` and `FrozenMultiset` inherit from `BaseMultiset`
