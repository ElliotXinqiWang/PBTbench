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

# Set key-value pair (key update: replaces old value)
b['a'] = 99   # old: a->1, new: a->99; 1 removed from inverse

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

The inverse is a **live view**, not a copy. Changes to `b` are immediately reflected
in `b.inverse` and vice versa.

### Fundamental invariant

For any bidict `b` at any point in time:

```
b[k] == v   if and only if   b.inverse[v] == k
```

This invariant must hold for every `(key, value)` pair in the bidict, both before
and after any mutation. In particular:

- After `b[k] = new_v` (key update), `b.inverse[new_v]` must equal `k`, and the
  old value must no longer appear in `b.inverse`.
- `len(b)` must always equal `len(b.inverse)`.
- `set(b.keys())` must always equal `set(b.inverse.values())`.

### Uniqueness constraint

Values must be unique just like keys. Attempting to insert a duplicate value raises
`ValueDuplicationError` by default:

```python
b = bidict({'a': 1})
b['b'] = 1   # raises ValueDuplicationError
```

Use `b.forceput('b', 1)` to overwrite the old key mapping to value `1`.

### forceput(key, val)

Unconditionally associate `key` with `val`. Replaces any existing mapping for
`key` or `val` as necessary to preserve uniqueness:

```python
b = bidict({'a': 1, 'b': 2})
b.forceput('c', 1)   # steals value 1 from 'a'; result: {'b': 2, 'c': 1}
b.forceput('c', 99)  # updates 'c' to 99; result: {'b': 2, 'c': 99}
b.forceput('c', 99)  # re-inserting same item: no-op, result unchanged
```

### update() / putall()

```python
b.update({'d': 4, 'e': 5})

# putall with atomic rollback on failure:
b.putall([('f', 6), ('g', 7)])  # all or nothing
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

The reverse of `list(ob)` must always equal `list(reversed(ob))`.

### copy()

`copy()` returns a shallow copy of the bidict with the same items in the same order:

```python
ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
ob2 = ob.copy()
list(ob2) == list(ob)  # True — same keys in same order
list(ob2.values()) == list(ob.values())  # True — same values in same order
```

Constructing an `OrderedBidict` from another `OrderedBidict` (e.g.,
`OrderedBidict(ob)`) preserves the same key iteration order:

```python
ob3 = OrderedBidict(ob)
list(ob3) == list(ob)  # True
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
new order consistently.

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
- Duplicate **key** (`b[k] = v2` where `k` already exists): overwrites old value
- Duplicate **value** (`b[k2] = v` where `v` already mapped to another key): raises `ValueDuplicationError`
- **Both** key and value duplicated across two different items: raises `KeyAndValueDuplicationError`

Use `forceput(key, val)` or `on_dup=ON_DUP_DROP_OLD` to overwrite existing entries silently.

---

## Summary of Key Invariants

| Invariant | Description |
|---|---|
| Bijectivity | Each key maps to exactly one value; each value to exactly one key |
| Inverse consistency | `b[k] == v` iff `b.inverse[v] == k` at all times |
| Size parity | `len(b) == len(b.inverse)` always |
| Key-inverse-value parity | `set(b.keys()) == set(b.inverse.values())` always |
| Forceput idempotence | `b.forceput(k, v)` where `(k, v)` is already in `b` is a no-op |
| Order preservation | `OrderedBidict` iterates in insertion order (forward and reverse) |
| Copy order fidelity | `list(ob.copy()) == list(ob)` for any `OrderedBidict` |
| Reversal consistency | `list(reversed(ob))` always equals `list(reversed(list(ob)))` |
