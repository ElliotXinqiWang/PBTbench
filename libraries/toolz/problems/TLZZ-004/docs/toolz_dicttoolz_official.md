# toolz.dicttoolz — Dictionary Utilities

## Overview

`toolz.dicttoolz` provides functional-style utilities for working with
Python dictionaries. All functions return new dictionaries without
modifying the originals (immutability guarantee).

## Functions

### update_in(d, keys, func, default=None, factory=dict)

Update a value in a potentially nested dictionary.

```python
from toolz.dicttoolz import update_in

inc = lambda x: x + 1
update_in({'a': 0}, ['a'], inc)
# {'a': 1}

# Nested updates
d = {'a': {'b': {'c': 10}}}
update_in(d, ['a', 'b', 'c'], inc)
# {'a': {'b': {'c': 11}}}

# Creates intermediate dicts if missing
update_in({}, [1, 2, 3], str, default="bar")
# {1: {2: {3: 'bar'}}}
```

**Key properties**:
- Does NOT mutate the original dictionary
- Creates copies at each level of nesting
- If a key in the path doesn't exist, creates nested dicts using `factory`
- The `func` is applied to the value at the deepest key
- If the deepest key doesn't exist, `func(default)` is used

**Nesting behavior**: For keys `[k0, k1, k2]`, the function traverses
`d[k0][k1]` and applies `func` to the value at `k2`. Each level is
copied to avoid mutating the original. The internal pointer must descend
through each level to build the correct nested structure.

### assoc_in(d, keys, value, factory=dict)

Set a value at a nested key path.

```python
from toolz.dicttoolz import assoc_in

assoc_in({'a': {'b': 1}}, ['a', 'b'], 2)
# {'a': {'b': 2}}

# Creates path if it doesn't exist
assoc_in({}, ['a', 'b', 'c'], 42)
# {'a': {'b': {'c': 42}}}
```

**Implementation**: `assoc_in` is implemented using `update_in` with a
function that always returns the new value:
`update_in(d, keys, lambda x: value, value, factory)`

**Key property**: When the key already exists, `assoc_in` should replace
the old value with the new one. When the key doesn't exist, the new value
is used as both the default and the replacement.

### dissoc(d, *keys, **kwargs)

Remove keys from a dictionary.

```python
from toolz.dicttoolz import dissoc

dissoc({'x': 1, 'y': 2}, 'y')
# {'x': 1}

dissoc({'x': 1, 'y': 2}, 'x', 'y')
# {}

dissoc({'x': 1}, 'z')  # missing keys are ignored
# {'x': 1}
```

**Implementation detail**: `dissoc` uses an optimization threshold. When
the number of keys to remove is small relative to the dictionary size
(< 60%), it copies the entire dict and deletes the specified keys. When
removing many keys (>= 60% of the dict), it computes the remaining keys
and builds a new dict from those.

**Key property**: The result should contain exactly the keys from `d`
that are NOT in the removal set, with their original values.

### keyfilter(predicate, d, factory=dict)

Filter dictionary items by key.

```python
from toolz.dicttoolz import keyfilter

iseven = lambda x: x % 2 == 0
keyfilter(iseven, {1: 2, 2: 3, 3: 4, 4: 5})
# {2: 3, 4: 5}
```

**Key property**: The result contains exactly the key-value pairs where
`predicate(key)` is `True`. Keys where the predicate returns `False`
are excluded.

### valfilter(predicate, d, factory=dict)

Filter dictionary items by value.

```python
from toolz.dicttoolz import valfilter

iseven = lambda x: x % 2 == 0
valfilter(iseven, {1: 2, 2: 3, 3: 4, 4: 5})
# {1: 2, 3: 4}
```

### keymap(func, d, factory=dict)

Apply a function to the keys of a dictionary.

```python
from toolz.dicttoolz import keymap

keymap(str.upper, {'a': 1, 'b': 2})
# {'A': 1, 'B': 2}
```

### valmap(func, d, factory=dict)

Apply a function to the values of a dictionary.

```python
from toolz.dicttoolz import valmap

valmap(str, {1: 10, 2: 20})
# {1: '10', 2: '20'}
```

### get_in(keys, coll, default=None, no_default=False)

Get a value from a nested collection.

```python
from toolz.dicttoolz import get_in

d = {'a': {'b': {'c': 42}}}
get_in(['a', 'b', 'c'], d)
# 42

get_in(['a', 'x'], d)
# None (default)

get_in(['a', 'x'], d, default=0)
# 0
```

### merge(*dicts) and merge_with(func, *dicts)

Merge dictionaries. `merge` uses last-write-wins; `merge_with` combines
values using a function.

```python
from toolz.dicttoolz import merge, merge_with

merge({'a': 1}, {'b': 2}, {'a': 3})
# {'a': 3, 'b': 2}

merge_with(sum, {'a': 1, 'b': 2}, {'a': 10, 'b': 20})
# {'a': 11, 'b': 22}
```

## Immutability Guarantee

All dicttoolz functions return NEW dictionaries. The original input
dictionary is never modified:

```python
d = {'a': 1}
d2 = assoc_in(d, ['b'], 2)
assert d == {'a': 1}  # original unchanged
assert d2 == {'a': 1, 'b': 2}
```
