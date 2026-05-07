# multiset API Reference (version 3.2.0)

## Overview

The `multiset` library provides a `Multiset` class — a collection where elements may appear more than once. Each element has a **multiplicity** (a positive integer representing how many times it appears).

## Core Invariant

> **Elements with zero (or negative) multiplicities are not stored — they are automatically removed from the internal representation.**

This invariant is guaranteed by all mutating and combining operations. At any point, every key in `ms._elements` has a strictly positive integer value. Querying a missing element returns 0, not a stored zero. Any operation that would reduce an element's count to 0 or below must remove the element entirely from `_elements`.

---

## Construction

```python
from multiset import Multiset

ms = Multiset()                        # empty multiset
ms = Multiset('aabbc')                 # from iterable — counts occurrences
ms = Multiset({'a': 3, 'b': 1})        # from dict — explicit multiplicities
ms = Multiset({'a': 3, 'b': 0})        # zero entries are ignored (not stored)
```

---

## Element Access

### `ms[element]`
Returns the multiplicity of `element`. Returns `0` if the element is absent (never raises `KeyError`).

```python
ms = Multiset({'a': 3})
ms['a']   # 3
ms['z']   # 0
```

### `element in ms`
Returns `True` if and only if the multiplicity of `element` is strictly greater than 0.

```python
'a' in Multiset({'a': 2})   # True
'b' in Multiset({'a': 2})   # False
```

### `len(ms)`
Returns the **total element count** — the sum of all multiplicities.

```python
len(Multiset({'a': 3, 'b': 2}))   # 5
len(Multiset())                    # 0
```

### Iteration
Iterates over distinct elements (each element yielded once, regardless of multiplicity). Only elements with strictly positive multiplicity are yielded.

---

## Combining Operations

### `ms.combine(*others)` → `Multiset`
Returns a **new** multiset with multiplicities summed element-wise across `self` and all `others`.

- `others` may be `Multiset`, `dict`, or any iterable.
- Supports **negative multiplicities** in `others` to subtract counts.
- Elements whose resulting count drops to **0 or below are removed** from the result (per the core invariant).
- Elements not present in `self` that appear in `others` with positive multiplicity are added.

```python
ms = Multiset({'a': 3, 'b': 2})

ms.combine({'a': 2})           # Multiset({'a': 5, 'b': 2}) — add 2 'a's
ms.combine({'a': -3})          # Multiset({'b': 2})         — 'a' reaches 0, removed
ms.combine({'a': -2})          # Multiset({'a': 1, 'b': 2}) — partial subtraction
ms.combine({'a': -10})         # Multiset({'b': 2})         — 'a' goes negative, removed
```

Key rule: if `old_count > 0` and `old_count + delta <= 0`, the element is **deleted** from the result.

### `ms + other` → `Multiset`
Equivalent to `ms.combine(other)` for non-negative additions. `other` must be a `Multiset`, `set`, or `frozenset`.

### `ms - other` → `Multiset`
Subtracts `other` from `ms`. The result contains only elements with positive multiplicity after subtraction; elements reduced to 0 or below are removed.

```python
Multiset('aaab') - Multiset('aa')   # Multiset({'a': 1, 'b': 1})
Multiset('ab') - Multiset('ab')     # Multiset()  — both elements removed
```

---

## Set-like Operations

### `ms & other` — Intersection
Returns a new multiset containing each element with the **minimum** multiplicity from `ms` and `other`.

```python
Multiset({'a': 3, 'b': 1}) & Multiset({'a': 1, 'b': 2, 'c': 5})
# Multiset({'a': 1, 'b': 1})
```

### `ms | other` — Union
Returns a new multiset containing each element with the **maximum** multiplicity from `ms` and `other`.

```python
Multiset({'a': 3, 'b': 1}) | Multiset({'a': 1, 'b': 2, 'c': 5})
# Multiset({'a': 3, 'b': 2, 'c': 5})
```

**Algebraic identity (inclusion-exclusion):**

```
len(A | B) + len(A & B) == len(A) + len(B)
```

This holds for all multisets `A` and `B`.

### `ms.times(n)` → `Multiset`
Returns a new multiset with every multiplicity multiplied by `n`. If `n <= 0`, returns an empty multiset.

```python
Multiset({'a': 2, 'b': 3}).times(3)   # Multiset({'a': 6, 'b': 9})
Multiset({'a': 2}).times(0)            # Multiset()
```

---

## Internal Representation

### `ms._elements`
A plain Python `dict` mapping each element to its multiplicity. Per the core invariant:

- All values are **strictly positive integers** (never 0, never negative).
- An element absent from `_elements` has an implicit multiplicity of 0.
- After any operation, no key with a zero or negative value should remain in `_elements`.

```python
ms = Multiset({'a': 2, 'b': 1})
ms._elements   # {'a': 2, 'b': 1}

empty = Multiset()
empty._elements   # {}
```

---

## Containment Consistency

The following must always hold simultaneously:

```python
# For any element e and multiset ms:
(e in ms)          ==  (ms[e] > 0)
(e in ms._elements) == (ms[e] > 0)
ms[e]              ==  ms._elements.get(e, 0)
```

Any discrepancy between `in`, `[]`, and `_elements` indicates a violated invariant.
