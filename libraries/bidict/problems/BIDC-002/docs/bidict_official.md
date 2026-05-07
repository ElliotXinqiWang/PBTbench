# bidict 0.23.1 — Official API Documentation

## Overview

`bidict` is a bidirectional mapping library for Python. A `bidict` enforces
one-to-one (bijective) mappings: each key maps to exactly one value, and each
value maps to exactly one key. This invariant is maintained at all times.

---

## bidict — Basic Usage

### Creating a bidict

```python
from bidict import bidict

b = bidict({'a': 1, 'b': 2})
```

### Key-value operations

```python
# Get value by key
b['a']       # 1

# Set key-value pair
b['c'] = 3

# Delete by key
del b['a']

# Check membership
'b' in b     # True
```

### Inverse access

Every `bidict` exposes an `.inverse` (or `.inv`) attribute that is itself a `bidict`
mapping values back to keys:

```python
b = bidict({'a': 1, 'b': 2})
b.inverse[1]   # 'a'
b.inv[2]       # 'b'
```

The inverse is a live view, not a copy. Changes to `b` are immediately reflected
in `b.inverse`.

### Uniqueness constraint

Values must be unique just like keys. Attempting to insert a duplicate value raises
`ValueDuplicationError` by default:

```python
b = bidict({'a': 1})
b['b'] = 1   # raises ValueDuplicationError
```

Use `b.forceput('b', 1)` to overwrite the old key mapping to value `1`.

### update() / putall()

```python
b.update({'d': 4, 'e': 5})
```

---

## OrderedBidict — Insertion-Order Preserved

`OrderedBidict` is a mutable bidict that remembers the order in which items were
inserted, similar to `collections.OrderedDict`.

```python
from bidict import OrderedBidict

ob = OrderedBidict([(1, 'one'), (2, 'two'), (3, 'three')])
list(ob)       # [1, 2, 3]
list(ob.inv)   # ['one', 'two', 'three']
```

### Iteration

Forward and reverse iteration respect insertion order:

```python
list(ob)           # [1, 2, 3]
list(reversed(ob)) # [3, 2, 1]
```

### move_to_end(key, last=True)

Move the item with the given key to the end of the order (if `last=True`, the
default) or to the beginning (if `last=False`).

```python
ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])

ob.move_to_end(1)            # Move key 1 to end
list(ob)                     # [2, 3, 1]

ob.move_to_end(1, last=False)  # Move key 1 to beginning
list(ob)                     # [1, 2, 3]
```

After calling `move_to_end`, both forward and reverse iteration must reflect the
new order consistently:

```python
ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
ob.move_to_end(3, last=False)
list(ob)           # [3, 1, 2]
list(reversed(ob)) # [2, 1, 3]  — must be exactly reversed(list(ob))
```

Raises `KeyError` if the key is not present.

### popitem(last=True)

Remove and return the most recently added item as `(key, value)` if `last=True`,
or the least recently added item if `last=False`.

```python
ob = OrderedBidict([(1, 'a'), (2, 'b')])
ob.popitem()          # (2, 'b')
ob.popitem(last=False) # (1, 'a')
```

### equals_order_sensitive(other)

Order-aware equality check. Returns `True` if and only if:
1. `other` is a `Mapping`,
2. `self` and `other` have the **same length**, and
3. iterating both in order yields identical `(key, value)` pairs.

```python
ob1 = OrderedBidict([(1, 10), (2, 20)])
ob2 = OrderedBidict([(1, 10), (2, 20)])
ob3 = OrderedBidict([(2, 20), (1, 10)])
ob4 = OrderedBidict([(1, 10)])

ob1.equals_order_sensitive(ob2)  # True  — same items, same order
ob1.equals_order_sensitive(ob3)  # False — same items, different order
ob1.equals_order_sensitive(ob4)  # False — different lengths
ob4.equals_order_sensitive(ob1)  # False — different lengths
```

**Note**: `==` (inherited `__eq__`) is order-insensitive for `OrderedBidict`.
Use `equals_order_sensitive()` when order matters.

### clear()

Remove all items from the ordered bidict:

```python
ob.clear()
list(ob)  # []
```

---

## Duplication Handling

By default (`on_dup=ON_DUP_DEFAULT`):
- Duplicate **key**: raises `KeyDuplicationError`
- Duplicate **value**: raises `ValueDuplicationError`
- Both: raises `KeyAndValueDuplicationError`

Use `forceput(key, val)` or `on_dup=ON_DUP_DROP_OLD` to overwrite existing entries.

---

## Summary of Key Invariants

| Invariant | Description |
|---|---|
| Bijectivity | Each key maps to exactly one value; each value to exactly one key |
| Inverse consistency | `b[k] == v` iff `b.inverse[v] == k` at all times |
| Order preservation | `OrderedBidict` iterates in insertion order (forward and reverse) |
| Length check in `equals_order_sensitive` | Two ordered bidicts of different lengths are never order-sensitively equal |
| Reversal consistency | `list(reversed(ob))` always equals `list(reversed(list(ob)))` |
