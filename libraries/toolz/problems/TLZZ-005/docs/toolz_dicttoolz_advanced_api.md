# toolz.dicttoolz — Advanced Dictionary Utilities

## Overview

`toolz.dicttoolz` provides functional-style utilities for working with Python
dictionaries. All functions create and return new dictionaries without modifying
the originals (immutability guarantee). This document covers advanced usage
patterns including the `factory` parameter, nested data access with mixed
types, value merging semantics, and type-preserving operations.

## The `factory` Parameter

Many dicttoolz functions accept a `factory` parameter that controls the type
of the returned dictionary. By default, `factory=dict`, but callers can pass
any callable that produces a mapping (e.g., `OrderedDict`, `defaultdict`,
custom dict subclasses).

**Functions that accept `factory`**:
- `merge(*dicts, factory=dict)`
- `merge_with(func, *dicts, factory=dict)`
- `valmap(func, d, factory=dict)`
- `keymap(func, d, factory=dict)`
- `itemmap(func, d, factory=dict)`
- `valfilter(predicate, d, factory=dict)`
- `keyfilter(predicate, d, factory=dict)`
- `itemfilter(predicate, d, factory=dict)`
- `assoc(d, key, value, factory=dict)`
- `dissoc(d, *keys, factory=dict)`
- `assoc_in(d, keys, value, factory=dict)`
- `update_in(d, keys, func, default=None, factory=dict)`

**Type preservation contract**: When `factory=X` is specified, the returned
dictionary MUST be of type `X`. This applies to:
- The top-level result dictionary
- All intermediate dictionaries created during nested operations (e.g.,
  `update_in`, `assoc_in`)

### Example: factory with OrderedDict

```python
from collections import OrderedDict
from toolz.dicttoolz import update_in, valmap, merge_with

# update_in creates OrderedDict at ALL levels when factory=OrderedDict
result = update_in({}, ['a', 'b', 'c'], lambda _: 1,
                   default=0, factory=OrderedDict)
assert isinstance(result, OrderedDict)
assert isinstance(result['a'], OrderedDict)       # intermediate level
assert isinstance(result['a']['b'], OrderedDict)   # intermediate level

# valmap returns OrderedDict when factory=OrderedDict
result = valmap(str, {'x': 1, 'y': 2}, factory=OrderedDict)
assert isinstance(result, OrderedDict)

# merge_with returns OrderedDict when factory=OrderedDict
result = merge_with(sum, {'a': 1}, {'a': 2}, factory=OrderedDict)
assert isinstance(result, OrderedDict)
```

### Example: factory with defaultdict

```python
from collections import defaultdict
from toolz.dicttoolz import valmap

# Using a factory that creates defaultdict
result = valmap(str, {1: 10, 2: 20},
                factory=lambda: defaultdict(str))
assert isinstance(result, defaultdict)
```

## update_in — Nested Dictionary Updates

### Signature

```python
update_in(d, keys, func, default=None, factory=dict)
```

### Behavior

`update_in` traverses a nested dictionary structure along the key path `keys`,
applies `func` to the value at the deepest key, and returns a new dictionary
with the updated value. The original dictionary is never mutated.

**Key path traversal**:
- For keys `[k0, k1, ..., kN]`, `update_in` traverses `d[k0][k1]...[k(N-1)]`
  and applies `func` to the value at `kN`.
- Each level is copied (using `factory()`) to avoid mutating the original.
- If a key does not exist at any level, a new empty dict is created using
  `factory()` for that level.

**Creating new paths**: When the key path leads to keys that don't exist in
the dictionary, `update_in` creates new intermediate dictionaries:

```python
# All intermediate dicts are created using factory
update_in({}, ['a', 'b', 'c', 'd'], lambda _: 42, default=0)
# {
#   'a': {           # created by factory()
#     'b': {         # created by factory()
#       'c': {       # created by factory()
#         'd': 42    # func(default) = lambda _: 42 applied to 0
#       }
#     }
#   }
# }
```

**Depth behavior**: The function handles key paths of any depth:
- Depth 1: `update_in(d, ['k'], func)` — direct key update
- Depth 2: `update_in(d, ['a', 'b'], func)` — one level of nesting
- Depth 3+: `update_in(d, ['a', 'b', 'c', ...], func)` — deep nesting

**Important**: When creating new intermediate dicts for paths that don't exist
in the original, the `factory` parameter determines the type of every
intermediate dict. This is critical for applications that need type consistency
throughout the nested structure.

### Immutability

```python
original = {'a': {'b': 1}}
result = update_in(original, ['a', 'b'], lambda x: x + 1)
assert original == {'a': {'b': 1}}  # unchanged
assert result == {'a': {'b': 2}}
assert original['a'] is not result['a']  # different objects
```

## get_in — Nested Data Access

### Signature

```python
get_in(keys, coll, default=None, no_default=False)
```

### Behavior

`get_in` retrieves a value from a nested data structure by following the
key path `keys`. It supports both dictionaries and sequences (lists, tuples)
at any level of nesting.

**Mixed-type nesting**: `get_in` works with any combination of dicts, lists,
and tuples:

```python
from toolz.dicttoolz import get_in

# Dict containing a list
data = {'users': [
    {'name': 'Alice', 'scores': [95, 87, 92]},
    {'name': 'Bob', 'scores': [78, 85]},
]}

get_in(['users', 0, 'name'], data)
# 'Alice'

get_in(['users', 1, 'scores', 0], data)
# 78

get_in(['users', 0, 'scores', 2], data)
# 92
```

### Default value handling

When the key path leads to a non-existent key or an out-of-range index,
`get_in` returns the `default` value (defaults to `None`). This applies to:

- **Missing dictionary keys**: `get_in(['missing'], {'a': 1})` returns `None`
- **Out-of-range list indices**: `get_in(['items', 99], {'items': [1,2,3]})` returns `None`
- **Type mismatches**: `get_in(['key'], [1, 2, 3])` returns `None`

```python
# Missing dict key — returns default
get_in(['x', 'y'], {'a': 1}, default=-1)
# -1

# Out-of-range list index — returns default
get_in(['data', 10], {'data': [1, 2, 3]}, default=0)
# 0

# Deep missing key — returns default
get_in(['a', 'b', 'c', 'd'], {'a': {'b': {}}}, default='NOT_FOUND')
# 'NOT_FOUND'
```

### Error handling with no_default

When `no_default=True`, `get_in` raises the original exception (`KeyError`,
`IndexError`, or `TypeError`) instead of returning a default:

```python
get_in(['missing'], {'a': 1}, no_default=True)
# Raises KeyError: 'missing'

get_in(['items', 99], {'items': [1, 2, 3]}, no_default=True)
# Raises IndexError

get_in([0], 42, no_default=True)
# Raises TypeError
```

### Non-mutation guarantee

`get_in` is a read-only operation. It should never modify the input
collection. For standard `dict` and `list` inputs, accessing a non-existent
key or index simply raises an exception (caught internally) without creating
entries.

**Note**: When using with `defaultdict`, callers should be aware that
`operator.getitem` on a `defaultdict` triggers `__missing__`, which creates
new entries. This is a Python `defaultdict` behavior, not a `get_in` behavior.

## merge_with — Dictionary Merging with Value Combination

### Signature

```python
merge_with(func, *dicts, factory=dict)
```

### Behavior

`merge_with` merges multiple dictionaries. When a key appears in more than
one dictionary, all values for that key are collected into a list and passed
to `func`. The result contains the return value of `func` for each key.

### Value collection order

Values are collected in **dictionary argument order**: values from `dicts[0]`
come before values from `dicts[1]`, which come before values from `dicts[2]`,
and so on. This ordering is significant for non-commutative functions.

```python
from toolz.dicttoolz import merge_with

# With sum (commutative) — order doesn't matter
merge_with(sum, {'a': 1}, {'a': 2}, {'a': 3})
# {'a': 6}

# With 'first' — takes the FIRST value (from first dict)
first = lambda vals: vals[0]
merge_with(first, {'a': 1, 'b': 2}, {'a': 10, 'b': 20})
# {'a': 1, 'b': 2}  — values from d1 come first

# With 'last' — takes the LAST value (from last dict)
last = lambda vals: vals[-1]
merge_with(last, {'a': 1}, {'a': 10})
# {'a': 10}  — values from d2 come last
```

### Non-commutative functions

When `func` is non-commutative (the result depends on argument order),
the value collection order is critical:

```python
# Subtraction: vals[0] - vals[1]
sub = lambda vals: vals[0] - vals[1]
merge_with(sub, {'x': 100}, {'x': 30})
# {'x': 70}  — 100 - 30, not 30 - 100

# Division: vals[0] / vals[1]
div = lambda vals: vals[0] / vals[1] if vals[1] != 0 else float('inf')
merge_with(div, {'rate': 10}, {'rate': 2})
# {'rate': 5.0}  — 10 / 2, not 2 / 10

# Custom aggregation
weighted = lambda vals: vals[0] * 0.7 + vals[1] * 0.3
merge_with(weighted, {'score': 90}, {'score': 60})
# {'score': 81.0}  — 90*0.7 + 60*0.3
```

### Keys appearing in only one dict

When a key appears in only one dictionary, `func` receives a single-element
list:

```python
merge_with(sum, {'a': 1, 'b': 2}, {'b': 3, 'c': 4})
# {'a': 1, 'b': 5, 'c': 4}
# 'a' and 'c' get func([val]), 'b' gets func([2, 3])
```

### Multiple (3+) dictionaries

```python
merge_with(sum, {'a': 1}, {'a': 2, 'b': 10}, {'a': 3, 'b': 20, 'c': 100})
# {'a': 6, 'b': 30, 'c': 100}
```

### Factory parameter

```python
from collections import OrderedDict

merge_with(sum, {'a': 1}, {'a': 2}, factory=OrderedDict)
# OrderedDict([('a', 3)])
```

## valmap — Apply Function to Values

### Signature

```python
valmap(func, d, factory=dict)
```

### Behavior

Applies `func` to each value in the dictionary, returning a new dictionary
with the same keys but transformed values.

```python
from toolz.dicttoolz import valmap

valmap(str, {1: 10, 2: 20})
# {1: '10', 2: '20'}

valmap(len, {'alice': [1,2,3], 'bob': [4,5]})
# {'alice': 3, 'bob': 2}
```

### Factory parameter

The `factory` parameter controls the type of the result dictionary:

```python
from collections import OrderedDict

result = valmap(str, {'a': 1, 'b': 2}, factory=OrderedDict)
assert isinstance(result, OrderedDict)
```

### Key preservation

`valmap` preserves all keys from the original dictionary. The result has
exactly the same set of keys as the input, with values transformed by `func`.

## keymap — Apply Function to Keys

### Signature

```python
keymap(func, d, factory=dict)
```

### Behavior

Applies `func` to each key in the dictionary:

```python
from toolz.dicttoolz import keymap

keymap(str.upper, {'hello': 1, 'world': 2})
# {'HELLO': 1, 'WORLD': 2}
```

## itemmap — Apply Function to Items

### Signature

```python
itemmap(func, d, factory=dict)
```

### Behavior

Applies `func` to each `(key, value)` pair. The function should return a
new `(key, value)` pair:

```python
from toolz.dicttoolz import itemmap

itemmap(reversed, {'Alice': 10, 'Bob': 20})
# {10: 'Alice', 20: 'Bob'}

itemmap(lambda kv: (kv[0].upper(), kv[1] * 2), {'a': 1, 'b': 2})
# {'A': 2, 'B': 4}
```

## assoc / assoc_in — Associating Values

### assoc(d, key, value, factory=dict)

Returns a new dict with the key set to the value:

```python
from toolz.dicttoolz import assoc

assoc({'x': 1}, 'y', 2)
# {'x': 1, 'y': 2}

assoc({'x': 1}, 'x', 99)
# {'x': 99}
```

### assoc_in(d, keys, value, factory=dict)

Sets a value at a nested key path:

```python
from toolz.dicttoolz import assoc_in

assoc_in({}, ['a', 'b', 'c'], 42)
# {'a': {'b': {'c': 42}}}

assoc_in({'a': {'b': 1}}, ['a', 'b'], 2)
# {'a': {'b': 2}}
```

`assoc_in` is implemented using `update_in`:
`assoc_in(d, keys, value, factory) = update_in(d, keys, lambda x: value, value, factory)`

## dissoc — Removing Keys

### Signature

```python
dissoc(d, *keys, factory=dict)
```

### Behavior

Returns a new dictionary with the specified keys removed. Missing keys are
silently ignored.

```python
from toolz.dicttoolz import dissoc

dissoc({'a': 1, 'b': 2, 'c': 3}, 'b')
# {'a': 1, 'c': 3}

dissoc({'a': 1, 'b': 2}, 'a', 'b')
# {}

dissoc({'a': 1}, 'z')  # missing key ignored
# {'a': 1}
```

## Filter Functions

### keyfilter(predicate, d, factory=dict)

Keeps items where `predicate(key)` is True:

```python
from toolz.dicttoolz import keyfilter

keyfilter(lambda k: k > 2, {1: 'a', 2: 'b', 3: 'c', 4: 'd'})
# {3: 'c', 4: 'd'}
```

### valfilter(predicate, d, factory=dict)

Keeps items where `predicate(value)` is True:

```python
from toolz.dicttoolz import valfilter

valfilter(lambda v: v > 10, {'a': 5, 'b': 15, 'c': 25})
# {'b': 15, 'c': 25}
```

### itemfilter(predicate, d, factory=dict)

Keeps items where `predicate((key, value))` is True:

```python
from toolz.dicttoolz import itemfilter

itemfilter(lambda kv: kv[0] + kv[1] > 5,
           {1: 2, 2: 3, 3: 4, 4: 5})
# {2: 3, 3: 4, 4: 5}
```

## Immutability Guarantee

All dicttoolz functions return NEW dictionaries. The original input
dictionary is never modified:

```python
d = {'a': {'b': 1}}
d2 = update_in(d, ['a', 'b'], lambda x: x + 1)
assert d == {'a': {'b': 1}}   # original unchanged
assert d2 == {'a': {'b': 2}}  # new dict with update
assert d['a'] is not d2['a']  # distinct nested objects
```

## Summary of Key Properties

| Function | Preserves keys | Preserves values | Respects factory | Non-mutating |
|----------|---------------|-----------------|-----------------|-------------|
| merge | from all dicts | last-write-wins | yes | yes |
| merge_with | from all dicts | combined by func | yes | yes |
| valmap | yes | transformed | yes | yes |
| keymap | transformed | yes | yes | yes |
| itemmap | transformed | transformed | yes | yes |
| valfilter | filtered | yes | yes | yes |
| keyfilter | filtered | yes | yes | yes |
| itemfilter | filtered | yes | yes | yes |
| assoc | yes + new | yes + new | yes | yes |
| dissoc | filtered | yes | yes | yes |
| assoc_in | yes (nested) | yes (nested) | yes | yes |
| update_in | yes (nested) | func(old) | yes | yes |
| get_in | read-only | read-only | N/A | yes |
