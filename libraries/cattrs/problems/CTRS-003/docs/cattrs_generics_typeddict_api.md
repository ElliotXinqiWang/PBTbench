# cattrs API Reference: Generics, TypedDict, and Validation Options

This document covers four areas of the cattrs library relevant for property-based
testing: Generic class structuring, TypedDict structuring, the `forbid_extra_keys`
option, and the `detailed_validation` toggle.

---

## 1. Generic Class Structuring

cattrs supports structuring Python `Generic[T, U, ...]` classes (both attrs and
dataclasses) when the concrete type arguments are provided.

### Usage

```python
import attr
from typing import Generic, TypeVar
from cattrs import Converter

T = TypeVar("T")
U = TypeVar("U")

@attr.s(auto_attribs=True)
class Pair(Generic[T, U]):
    first: T
    second: U

c = Converter()

# Providing both type arguments; cattrs maps T→int and U→str
result = c.structure({"first": 42, "second": "hello"}, Pair[int, str])
# result.first is 42 (int), result.second is "hello" (str)
```

### Invariant: Type Argument Order Preserved

When structuring `Pair[int, str]`, cattrs must assign the first type argument
(`int`) to the first TypeVar (`T`) and the second type argument (`str`) to the
second TypeVar (`U`).  The ordering of type arguments in `Pair[int, str]` must
exactly correspond to the ordering of TypeVar parameters in `Generic[T, U]`.

Concretely: for any Generic class `C(Generic[T, U])` with fields `first: T`
and `second: U`, structuring `C[A, B]` from `{"first": a, "second": b}` must
produce an object where `first` has type `A` and `second` has type `B`.

### Multi-TypeVar vs Single-TypeVar

- **Single-TypeVar generics** (`Generic[T]`): structuring works identically for
  all concrete substitutions.
- **Multi-TypeVar generics** (`Generic[T, U]`): the mapping from TypeVar positions
  to concrete types is critical and must maintain argument order.

---

## 2. TypedDict Structuring

cattrs supports structuring `TypedDict` classes, respecting Python's `total`
parameter and `Required`/`NotRequired` annotations.

### total=True (default)

All keys are required.  Missing keys during structuring raise an error.

```python
from typing import TypedDict
from cattrs import Converter

class Config(TypedDict):        # total=True by default
    host: str
    port: int

c = Converter()
result = c.structure({"host": "localhost", "port": 8080}, Config)
# result == {"host": "localhost", "port": 8080}
```

### total=False

All keys become optional.  The structuring function must silently skip any keys
absent from the input dict — it must **not** raise an error for missing keys.

```python
class Profile(TypedDict, total=False):   # all keys optional
    name: str
    score: int

c = Converter()

# Only "name" provided — must succeed, "score" absent from result
result = c.structure({"name": "Alice"}, Profile)
assert result == {"name": "Alice"}

# Both keys provided — must succeed
result2 = c.structure({"name": "Bob", "score": 99}, Profile)
assert result2 == {"name": "Bob", "score": 99}
```

### Mixed Required / Optional Keys

Combine `total=True` with `NotRequired`, or `total=False` with `Required`:

```python
from typing import TypedDict
from typing_extensions import NotRequired, Required

class Partial(TypedDict):
    x: int
    y: NotRequired[str]   # y is optional despite total=True

class All(TypedDict, total=False):
    x: Required[int]      # x is required despite total=False
    y: str
```

**Invariant**: cattrs must correctly distinguish required keys from optional keys
per the TypedDict's declared semantics.  Optional keys absent from the input
dict must be absent from the structured output.  Required keys absent from the
input dict must raise an error.

---

## 3. forbid_extra_keys

The `forbid_extra_keys` option causes the structuring function to **raise
`ForbiddenExtraKeysError`** if the input dict contains keys that are not
declared fields of the target class.

### Enabling forbid_extra_keys

```python
from cattrs import Converter
from cattrs.gen import make_dict_structure_fn
import attr

@attr.s(auto_attribs=True)
class Point:
    x: int
    y: str

# Method 1: via Converter (applies globally)
c = Converter(forbid_extra_keys=True)

# Method 2: via make_dict_structure_fn (per-class)
c2 = Converter()
hook = make_dict_structure_fn(Point, c2, _cattrs_forbid_extra_keys=True)
c2.register_structure_hook(Point, hook)
```

### Error Behavior

When extra keys are present, `ForbiddenExtraKeysError` is raised:

```python
from cattrs.errors import ForbiddenExtraKeysError

try:
    c.structure({"x": 1, "y": "a", "z": 99}, Point)
except ForbiddenExtraKeysError as e:
    print(e.extra_fields)   # {"z"}
```

**Invariant**: `ForbiddenExtraKeysError` must be raised if and only if the input
dict contains keys that are not valid field names for the class.  In particular:

- Input `{"x": 1, "y": "a"}` — valid, no error
- Input `{"x": 1, "y": "a", "z": 99}` — extra key "z", must raise
- The `extra_fields` attribute of the error must contain exactly the unexpected
  keys, not the expected keys that happen to be missing

---

## 4. detailed_validation Toggle

The `detailed_validation` flag (default `True`) selects between two structuring
code generation paths:

### detailed_validation=True (default)

- Collects *all* validation errors before raising, accumulating them in a
  `ClassValidationError`.
- Provides detailed error messages with field names and expected types.
- Slower due to try/except per field.

```python
c = Converter(detailed_validation=True)   # default
```

### detailed_validation=False

- Fails fast on the first error encountered.
- Generates simpler, faster code.
- Used in performance-sensitive scenarios.

```python
c = Converter(detailed_validation=False)
```

Or per-class:

```python
hook = make_dict_structure_fn(
    MyClass, c,
    _cattrs_detailed_validation=False,
    _cattrs_forbid_extra_keys=True,  # can be combined
)
c.register_structure_hook(MyClass, hook)
```

### Optional Fields in non-detailed mode

When `detailed_validation=False`, attrs fields with default values are treated
as optional in the input dict.  The generated structuring code checks whether
the key is present in the input before reading it:

```python
@attr.s(auto_attribs=True)
class Config:
    name: str          # required: always read from input
    count: int = 0     # optional: read from input only if present

c = Converter(detailed_validation=False)

# count provided: use provided value
r = c.structure({"name": "Alice", "count": 5}, Config)
assert r.count == 5    # NOT the default 0

# count absent: use default
r2 = c.structure({"name": "Alice"}, Config)
assert r2.count == 0   # default is used
```

**Invariant**: When a key for an optional (defaulted) field IS present in the
input dict, its value must be used in the structured object.  The default value
is used only when the key is ABSENT from the input dict.

---

## 5. Combining forbid_extra_keys + detailed_validation=False

These options can be combined; the behavior must satisfy both invariants:

```python
@attr.s(auto_attribs=True)
class Config:
    name: str
    count: int = 0

c = Converter(detailed_validation=False)
hook = make_dict_structure_fn(
    Config, c,
    _cattrs_forbid_extra_keys=True,
    _cattrs_detailed_validation=False,
)
c.register_structure_hook(Config, hook)

# Valid: exact fields only
r = c.structure({"name": "Alice", "count": 5}, Config)
assert r.count == 5

# Extra key: must raise ForbiddenExtraKeysError
try:
    c.structure({"name": "Alice", "count": 5, "extra": 99}, Config)
    assert False, "should have raised"
except ForbiddenExtraKeysError:
    pass
```
