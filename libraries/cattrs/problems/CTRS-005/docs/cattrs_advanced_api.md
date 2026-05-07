# cattrs 26.1.0 — Advanced Converter API Reference

cattrs is a Python library for structuring (dict/list/tuple → typed class) and
unstructuring (typed class → dict/list/tuple) Python objects. It supports attrs
classes, dataclasses, NamedTuples, and standard Python types. This document
covers advanced usage patterns needed to write property-based tests for converter
correctness.

---

## 1. Core Converter Classes

### 1.1 BaseConverter

`BaseConverter` is the foundational converter.  It provides the `structure`
and `unstructure` methods and a hook registry.

```python
from cattrs import BaseConverter
from cattrs.converters import UnstructureStrategy

# Default: attrs classes unstructure to dicts, structure from dicts
c = BaseConverter()

# AS_TUPLE strategy: attrs classes unstructure to tuples, structure from tuples
c = BaseConverter(unstruct_strat=UnstructureStrategy.AS_TUPLE)
```

When `unstruct_strat=UnstructureStrategy.AS_TUPLE`:
- `unstructure(obj)` produces a plain `tuple` of field values in declaration order
- `structure((v1, v2, ...), MyClass)` reads values from the tuple in declaration order
  and converts each to the declared field type

**Field-order invariant**: for any attrs class instance `obj` and
`AS_TUPLE` converter `c`, round-tripping must satisfy:
```python
restored = c.structure(c.unstructure(obj), type(obj))
assert restored == obj
```

### 1.2 Converter

`Converter` extends `BaseConverter` with code-generation for faster hooks.  It
also provides `gen_unstructure_optional` for `Optional[T]` fields.

```python
from cattrs import Converter

c = Converter()
c = Converter(detailed_validation=True)  # default
c = Converter(omit_if_default=False)     # default
c = Converter(use_alias=False)           # default; use field names as dict keys
```

**Optional field invariant**: for any `Optional[T]` field where `T` is an
attrs class, `unstructure` must convert the inner value using the hook for `T`,
not leave it as the Python object.  Round-trip must hold:
```python
@attr.s(auto_attribs=True)
class Inner:
    x: int

@attr.s(auto_attribs=True)
class Outer:
    val: Optional[Inner]

c = Converter()
obj = Outer(val=Inner(x=42))
assert c.structure(c.unstructure(obj), Outer) == obj
# c.unstructure(obj) must equal {'val': {'x': 42}}, not {'val': Inner(x=42)}
```

---

## 2. Structuring and Unstructuring

### 2.1 Basic Usage

```python
import attr
from cattrs import Converter

@attr.s(auto_attribs=True)
class Point:
    x: int
    y: float

c = Converter()
obj = c.structure({'x': 1, 'y': 2.5}, Point)   # dict → attrs
d   = c.unstructure(obj)                         # attrs → dict
assert d == {'x': 1, 'y': 2.5}
```

### 2.2 Structuring from Tuples (AS_TUPLE strategy)

```python
from cattrs import BaseConverter
from cattrs.converters import UnstructureStrategy

@attr.s(auto_attribs=True)
class Record:
    name: str
    value: int
    score: float

c = BaseConverter(unstruct_strat=UnstructureStrategy.AS_TUPLE)

obj  = Record(name='alice', value=7, score=0.9)
tup  = c.unstructure(obj)       # ('alice', 7, 0.9) — elements in field order
obj2 = c.structure(tup, Record) # structure from tuple in field order
assert obj2 == obj
```

The tuple elements are matched to fields **positionally in declaration order**.
The i-th tuple element is converted to the type of the i-th declared field.

### 2.3 Structuring NamedTuples

`Converter` automatically registers a structuring hook for `NamedTuple`
subclasses.  The hook accepts any iterable and maps each element to the
corresponding annotated field in declaration order.

```python
from typing import NamedTuple
from cattrs import Converter

class Measurement(NamedTuple):
    sensor_id: int
    reading: float
    unit: str

c = Converter()
result = c.structure([101, 9.8, 'ms-2'], Measurement)
# Must yield Measurement(sensor_id=101, reading=9.8, unit='ms-2')
assert result.sensor_id == 101
assert result.reading   == pytest.approx(9.8)
assert result.unit      == 'ms-2'
```

**Order invariant**: the i-th element of the input iterable must map to the
i-th annotated field of the NamedTuple.  Reversal or any other permutation is
incorrect.

### 2.4 Optional Fields

For `Optional[T]` fields (equivalent to `Union[T, None]`), the unstructuring
hook must apply the hook for `T` to any non-None value:

```python
@attr.s(auto_attribs=True)
class Config:
    host: str
    port: int

@attr.s(auto_attribs=True)
class Container:
    cfg: Optional[Config]

c = Converter()
obj = Container(cfg=Config(host='localhost', port=8080))
d = c.unstructure(obj)
# d must be {'cfg': {'host': 'localhost', 'port': 8080}}
# NOT {'cfg': Config(host='localhost', port=8080)}
```

---

## 3. Hook Registration

### 3.1 Type-Based Hooks

```python
c = Converter()

# Register for a specific type
c.register_structure_hook(MyClass, lambda d, t: MyClass(**d))
c.register_unstructure_hook(MyClass, lambda obj: {'key': obj.value})
```

### 3.2 Predicate-Based Hooks

```python
c.register_structure_hook_func(
    lambda t: hasattr(t, '__my_marker__'),
    lambda d, t: t(d)
)
c.register_unstructure_hook_func(
    lambda t: hasattr(t, '__my_marker__'),
    lambda obj: obj.serialize()
)
```

Predicate-based hooks are evaluated in most-recently-registered-first order.

### 3.3 Hook Priority

1. Explicitly registered type hooks (most specific)
2. Predicate-based hooks (most recently registered first)
3. Built-in default hooks (least specific)

---

## 4. Union Handling

### 4.1 Bare Union Structuring

By default, `Converter` tries each arm of a `Union` in order and returns the
first successful conversion.  For `Optional[T]` (i.e., `Union[T, None]`), `None`
is passed through and non-None values are converted via the hook for `T`.

### 4.2 configure_union_passthrough

`configure_union_passthrough` in `cattrs.strategies` configures a converter to
accept values that are already instances of one of the union arms:

```python
from cattrs.strategies import configure_union_passthrough
from typing import Union

c = Converter()
configure_union_passthrough(Union[int, str, None], c)
# Now c.structure(42, Union[int, str, None]) == 42 (no conversion needed)
# And c.structure('hello', Union[int, str, None]) == 'hello'
```

**`accept_ints_as_floats` parameter**: when `True` (used by the JSON preconf
converter), integer values are accepted for `float` arms in unions:

```python
configure_union_passthrough(Union[float, str, None], c, accept_ints_as_floats=True)
# c.structure(42, Union[float, str, None]) must succeed and return 42
# (integers are valid JSON floats)
```

The invariant: with `accept_ints_as_floats=True`, structuring any `int` value
for a union that contains `float` must not raise `TypeError`.

---

## 5. JSON Preconf Converter

`make_converter()` from `cattrs.preconf.json` returns a `JsonConverter` with
pre-configured hooks for JSON-compatible types.  It calls
`configure_union_passthrough` with `accept_ints_as_floats=True`.

```python
from cattrs.preconf.json import make_converter

c = make_converter()

# Supports bytes (base85-encoded in JSON)
import attr

@attr.s(auto_attribs=True)
class Blob:
    data: bytes

obj = Blob(data=b'\x00\x01\x02')
d   = c.unstructure(obj)        # {'data': 'some_base85_string'}
obj2 = c.structure(d, Blob)     # Blob(data=b'\x00\x01\x02')
assert obj2 == obj

# Union with float accepts ints
result = c.structure(42, Union[float, str, None])
assert isinstance(result, (int, float))
```

---

## 6. NamedTuple Column Utilities

The `cattrs.cols` module provides factory functions for structuring NamedTuples.

### 6.1 namedtuple_structure_factory

```python
from cattrs.cols import namedtuple_structure_factory
from cattrs import Converter

class Pair(NamedTuple):
    first: int
    second: str

c = Converter()
hook = namedtuple_structure_factory(Pair, c)
# Converter() registers this hook automatically for NamedTuple subclasses

result = c.structure([10, 'hello'], Pair)
assert result == Pair(first=10, second='hello')
```

The factory creates a hook that:
1. Delegates to the heterogeneous-tuple hook for type conversion of each element
2. Constructs the NamedTuple from the converted elements **in the original order**

---

## 7. Generating Structure/Unstructure Functions

### 7.1 make_dict_structure_fn

```python
from cattrs.gen import make_dict_structure_fn, override

@attr.s(auto_attribs=True)
class User:
    _name: str = attr.ib(alias='name')
    age: int = 0

hook = make_dict_structure_fn(User, converter)
c.register_structure_hook(User, hook)
```

### 7.2 make_dict_unstructure_fn

```python
from cattrs.gen import make_dict_unstructure_fn, override

hook = make_dict_unstructure_fn(
    User,
    converter,
    _cattrs_omit_if_default=True,  # omit fields at default values
    name=override(rename='username'),  # rename key in output dict
)
c.register_unstructure_hook(User, hook)
```

---

## 8. Property Testing Guide

### 8.1 Round-trip Properties

For any correctly configured converter, the following should hold for any
supported type `T` and any value `obj: T`:

```python
assert c.structure(c.unstructure(obj), type(obj)) == obj
```

This is the primary property to test.

### 8.2 Structural Correctness

For attrs classes unstructured to dicts:
- Every declared field must appear as a key in the output dict (unless omit_if_default)
- Each value must be of a JSON-compatible type (dict, list, str, int, float, bool, None)
- Nested attrs classes must recursively unstructure to dicts (not remain as Python objects)

For attrs classes structured from tuples (AS_TUPLE strategy):
- The i-th positional field in the result must equal the i-th element of the input tuple (after type conversion)
- No reordering of elements must occur

For NamedTuples structured from lists/tuples:
- The i-th field of the resulting NamedTuple must equal the i-th element of the input (after type conversion)
- Field order must be preserved exactly

### 8.3 Union Structuring Invariants

For `Union[float, str, None]` with a JSON converter:
- `None` input → `None` output
- `str` input → `str` output
- `int` or `float` input → numeric output (no TypeError)

### 8.4 Optional Unstructuring Invariants

For an attrs class with an `Optional[InnerClass]` field:
- If the field is `None`, the unstructured dict value must be `None`
- If the field is a non-None `InnerClass` instance, the unstructured dict value
  must be a `dict` (not a Python object), equal to what `c.unstructure(inner)` would return

---

## 9. Common Pitfalls

### 9.1 Converter vs BaseConverter

`Converter` generates optimized code-gen hooks and handles `Optional[T]`
specially.  `BaseConverter` uses interpreted hooks and is more predictable for
testing.  Use `Converter` for production and round-trip tests; use
`BaseConverter(unstruct_strat=AS_TUPLE)` to test tuple-based structuring.

### 9.2 AS_TUPLE vs AS_DICT

With `AS_DICT` (default), attrs classes unstructure to dicts and structure from
dicts.  With `AS_TUPLE`, they unstructure to plain tuples and structure from
positional tuples.  These two modes are incompatible: a tuple produced by
`AS_TUPLE` cannot be structured by an `AS_DICT` converter.

### 9.3 NamedTuple Auto-Registration

`Converter()` automatically registers `namedtuple_structure_factory` for all
`NamedTuple` subclasses.  You do not need to call
`register_structure_hook` manually unless you want a custom hook.

### 9.4 Union Passthrough and JSON

The JSON preconf converter (`make_converter()` from `cattrs.preconf.json`) uses
`configure_union_passthrough` internally with `accept_ints_as_floats=True`.
This means integer values are always valid inputs for union types that include
`float`.  If your tests use `JsonConverter` and `Union[float, ...]` types,
integer inputs must not raise `TypeError`.

---

## 10. Mapping (Dict) Unstructuring

### 10.1 Dict[K, V] Unstructuring Invariant

`Converter` automatically registers an unstructure hook for any `Dict[K, V]`
(or `Mapping[K, V]`) type via `mapping_unstructure_factory` in `cattrs.gen`.
The hook applies the appropriate unstructure hook to each key and value
independently.

The invariant: for any `Dict[K, V]` mapping where `V` is an attrs class, each
value in the unstructured output must be a plain dict, not the original Python
object.

```python
import attr
from typing import Dict
from cattrs import Converter

@attr.s(auto_attribs=True)
class Config:
    host: str
    port: int

c = Converter()
mapping = {'server1': Config(host='localhost', port=8080)}
result = c.unstructure(mapping)
# result must be {'server1': {'host': 'localhost', 'port': 8080}}
# NOT {'server1': Config(host='localhost', port=8080)}
assert isinstance(result['server1'], dict)
assert result['server1']['host'] == 'localhost'
```

### 10.2 Dict Roundtrip

For any `Dict[K, V]` where both K and V are supported types:

```python
mapping = {'server1': Config(host='localhost', port=8080)}
restored = c.structure(c.unstructure(mapping), Dict[str, Config])
assert restored == mapping
```

The round-trip must hold: `structure(unstructure(m), Dict[K, V]) == m`.

### 10.3 Key Types

Common key types (`str`, `int`) are passed through by identity during
unstructuring. Value types that are attrs classes, dataclasses, or other
supported types have dedicated hooks applied to convert them to plain dicts.
This means that even if the key hook is identity, the value hook must still
be applied.

```python
# str keys are passed through, but Config values must be converted
mapping: Dict[str, Config] = {'k': Config(host='x', port=80)}
result = c.unstructure(mapping)
assert isinstance(result['k'], dict)   # NOT Config instance
```
