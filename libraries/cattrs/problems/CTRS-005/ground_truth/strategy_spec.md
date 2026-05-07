# CTRS-005 Strategy Specification

## Overview

Four independent silent-failure bugs in cattrs 26.1.0.  Each test targets a
different execution path and requires a specific combination of types and
converter configuration to trigger.

---

## bug_1 — gen_unstructure_optional wrong union arm

**File**: `cattrs/converters.py:1277`
**Trigger path**:
1. Use `Converter()` (not `BaseConverter`)
2. Have an attrs class with a field typed `Optional[SomeAttrsClass]`
3. Set the field to a non-None instance
4. Call `converter.unstructure(outer_instance)`

**Why default PBT rarely triggers it**:
- Requires a *nested* attrs class inside Optional — a plain `Optional[int]` or
  `Optional[str]` still works because the hook for primitive types is identity
  anyway.  The failure is visible only when the inner type itself requires
  conversion (i.e., another attrs class or a complex type).
- Default strategies rarely generate two-level nested attrs structures.

**Minimum trigger example**:
```python
@attr.s(auto_attribs=True)
class Inner:
    x: int

@attr.s(auto_attribs=True)
class Outer:
    val: Optional[Inner]

c = Converter()
result = c.unstructure(Outer(val=Inner(x=1)))
# Buggy: {'val': Inner(x=1)}   Correct: {'val': {'x': 1}}
```

**Strategy for ground truth**: generate arbitrary `host` (str) and `port`
(int) values, wrap in `Config` inside `Container`, unstructure with
`Converter()`, assert `cfg` key is a dict and round-trips correctly.

---

## bug_2 — accept_ints_as_floats condition inverted

**File**: `cattrs/strategies/_unions.py:220`
**Trigger path**:
1. Use `make_converter()` from `cattrs.preconf.json` (which calls
   `configure_union_passthrough` with `accept_ints_as_floats=True`)
2. Call `converter.structure(int_value, Union[float, str, None])`
3. The union must contain both `float` and `int`-compatible types; `None`
   optional membership doesn't matter as long as `float` is present

**Why default PBT rarely triggers it**:
- Requires using the JSON preconf converter specifically (not bare `Converter`)
  AND a union type containing both `float` and a non-numeric type AND an
  integer value as input.  Most basic structuring tests use simple scalar
  types, not multi-arm unions.
- The bug turns an `int` value into a TypeError rather than silently returning
  wrong data, so it *is* detectable but only with the specific Union shape.

**Minimum trigger example**:
```python
from cattrs.preconf.json import make_converter
c = make_converter()
c.structure(42, Union[float, str, None])
# Buggy: TypeError — 42 not part of Union[float, str, NoneType]
# Correct: 42 (accepted as float-compatible int)
```

**Strategy for ground truth**: generate arbitrary integers and strings, test
structuring each as `Union[float, str, None]` — integers must not raise.

---

## bug_3 — namedtuple_structure_factory reverses values

**File**: `cattrs/cols.py:224`
**Trigger path**:
1. Use any `Converter()` (auto-registers the namedtuple hook)
2. Have a `NamedTuple` subclass with **at least 2 differently-typed fields**
3. Call `converter.structure(list_or_tuple, MyNamedTuple)`

**Why default PBT rarely triggers it**:
- Requires using a `NamedTuple` (not a plain tuple or attrs class), AND the
  namedtuple must have fields of distinct types so that the reversed order
  produces detectable wrong values.  A namedtuple with all `int` fields would
  still produce wrong *values* but only when values differ — a 1-field
  namedtuple never triggers it.
- The bug produces the *wrong value* silently; no exception is raised, so only
  a correctness assertion catches it.

**Minimum trigger example**:
```python
class Point(NamedTuple):
    x: int
    label: str
    weight: float

c = Converter()
result = c.structure([42, 'hello', 3.14], Point)
# Buggy: Point(x=3.14, y='hello', z=42)
# Correct: Point(x=42, y='hello', z=3.14)
```

**Strategy for ground truth**: generate distinct `(int, str, float)` values,
structure from a list, assert each field equals the corresponding input element
by position.

---

## bug_4 — structure_attrs_fromtuple reverses input tuple

**File**: `cattrs/converters.py:736`
**Trigger path**:
1. Create `BaseConverter(unstruct_strat=UnstructureStrategy.AS_TUPLE)` — this
   registers `structure_attrs_fromtuple` as the attrs structuring hook
2. Have an attrs class with **at least 2 fields of different types**
3. Call `converter.structure(some_tuple, MyAttrsClass)`

**Why default PBT rarely triggers it**:
- Requires `AS_TUPLE` strategy on the converter — the default `Converter()`
  uses `AS_DICT` and never calls `structure_attrs_fromtuple`.
- Requires at least 2 positionally distinguishable fields — a single-field
  class has nothing to swap.
- The failure is silent: coercion at the wrong slot produces a value of the
  right type but wrong content (e.g., `score=42.0` when `42` is the name
  field's intended value after int-coercion).

**Minimum trigger example**:
```python
from cattrs.converters import UnstructureStrategy
c = BaseConverter(unstruct_strat=UnstructureStrategy.AS_TUPLE)
original = Record(name='alice', value=7, score=0.9)
as_tuple = c.unstructure(original)   # ('alice', 7, 0.9)
restored = c.structure(as_tuple, Record)
# Buggy: Record(name=0.9_coerced, value=7, score='alice'_coerced)
# name slot receives 0.9 (last element), score slot receives 'alice' (first)
```

**Strategy for ground truth**: generate arbitrary `(name: str, value: int,
score: float)` combinations, unstructure with `AS_TUPLE`, re-structure, assert
each field equals the original.  Use `AS_TUPLE` converter explicitly.
