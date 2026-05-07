# cattrs Advanced API Documentation

**Version**: 26.1.0
**Module**: `cattrs`

This document covers advanced features of cattrs: the `include_subclasses` strategy,
alias-based structuring, Optional type handling, and `init=False` field behavior.

---

## 1. include_subclasses Strategy

### Purpose

The `include_subclasses` strategy configures a converter to handle a class hierarchy
transparently. After applying this strategy, the converter can structure and unstructure
both the base class and all known subclasses using a single hook registered for the base
class.

### Signature

```python
from cattrs.strategies import include_subclasses

def include_subclasses(
    cl: type,
    converter: Converter,
    subclasses: tuple[type, ...] | None = None,
    union_strategy: Callable | None = None,
    overrides: dict[str, AttributeOverride] | None = None,
) -> None:
    ...
```

### Parameters

- `cl`: The base attrs or dataclass type
- `converter`: The converter to configure
- `subclasses`: Optional explicit tuple of subclasses. If `None`, detected automatically via `__subclasses__`
- `union_strategy`: Optional callable for union disambiguation (e.g., `configure_tagged_union`)
- `overrides`: Optional attribute overrides for the base class fields

### Structuring Behavior

When `converter.structure(data, BaseClass)` is called:
- The converter checks all registered subclasses for unique field signatures
- The correct subclass is selected via a disambiguation function
- The data is structured into the appropriate subclass instance

### Unstructuring Behavior

When `converter.unstructure(instance, BaseClass)` is called:
- If `instance.__class__` is exactly `BaseClass` (not a subclass), the base hook is used
- If `instance.__class__` is a **proper subclass**, the converter dispatches to the
  subclass-specific unstructure hook, which produces a dict containing ALL fields
  of the subclass (not just the base class fields)

This guarantees that all subclass-specific fields are preserved during unstructuring.

### Invariant

For any `instance` of type `T` where `T` is a subclass of `BaseClass`:

```python
include_subclasses(BaseClass, c)
unstructured = c.unstructure(instance, BaseClass)

# All subclass fields must appear in the output
for field in attr.fields(T):
    assert field.name in unstructured

# Roundtrip must return equal object
restructured = c.structure(unstructured, BaseClass)
assert restructured == instance
```

### Example

```python
import attr
from cattrs import Converter
from cattrs.strategies import include_subclasses

@attr.s(auto_attribs=True)
class Animal:
    name: str

@attr.s(auto_attribs=True)
class Dog(Animal):
    breed: str = "unknown"
    tricks: int = 0

@attr.s(auto_attribs=True)
class Cat(Animal):
    indoor: bool = True
    lives: int = 9

c = Converter()
include_subclasses(Animal, c)

# Structuring a dict into the right subtype
dog = c.structure({"name": "Rex", "breed": "husky", "tricks": 3}, Animal)
assert isinstance(dog, Dog)

# Unstructuring preserves all subclass fields
d = c.unstructure(dog, Animal)
assert d == {"name": "Rex", "breed": "husky", "tricks": 3}

# Roundtrip
assert c.structure(d, Animal) == dog
```

### Multi-level Subclasses

`include_subclasses` works recursively. If `Animal` has subclasses `Dog`, `Cat`,
and `Dog` has a subclass `GoldenRetriever`, all three levels are handled:

```python
@attr.s(auto_attribs=True)
class GoldenRetriever(Dog):
    fetch_score: int = 100

include_subclasses(Animal, c)

golden = GoldenRetriever(name="Buddy", breed="Golden", tricks=5, fetch_score=95)
d = c.unstructure(golden, Animal)
assert "fetch_score" in d  # GoldenRetriever-specific field preserved
assert c.structure(d, Animal) == golden
```

---

## 2. Attribute Aliases and use_alias

### Background

In Python, it is conventional to prefix private attributes with an underscore
(e.g., `_name`, `_score`). In attrs, when an attribute name starts with an underscore,
attrs automatically creates an alias for it without the underscore for use in
`__init__`.

```python
@attr.s(auto_attribs=True)
class Config:
    _host: str       # alias = "host", init takes host=...
    _port: int = 80  # alias = "port", init takes port=...
```

### use_alias Parameter

The `use_alias` parameter on `Converter` (and `_cattrs_use_alias` on codegen functions)
controls whether cattrs uses the **alias** (the external name) or the **attribute name**
(the internal name) as the dictionary key when structuring and unstructuring.

```python
c = Converter(use_alias=True)
# Dict keys will use aliases: {"host": ..., "port": ...}

c = Converter(use_alias=False)  # default
# Dict keys will use attribute names: {"_host": ..., "_port": ...}
```

### Interaction with make_dict_structure_fn

```python
from cattrs.gen import make_dict_structure_fn, override

# Generate a structure function that uses aliases for dict keys
hook = make_dict_structure_fn(
    Config,
    converter,
    _cattrs_use_alias=True,
    _cattrs_detailed_validation=False,  # faster non-detailed mode
)
```

### Invariant for Optional Fields with Aliases

When using `use_alias=True`, **all fields** (required and optional) must be accessible
via their alias names in the input dict. The structure function reads values using
alias keys and passes them to `__init__` using the alias as the keyword argument name.

```python
@attr.s(auto_attribs=True)
class Player:
    _name: str = attr.ib(alias="name")         # required
    _score: int = attr.ib(default=0, alias="score")  # optional

c = Converter(detailed_validation=False)
hook = make_dict_structure_fn(Player, c, _cattrs_use_alias=True)
c.register_structure_hook(Player, hook)

# Works: all alias keys provided
p = c.structure({"name": "Alice", "score": 100}, Player)
assert p._name == "Alice" and p._score == 100

# Works: optional field omitted
p2 = c.structure({"name": "Bob"}, Player)
assert p2._name == "Bob" and p2._score == 0

# Works: optional field provided (must use alias key "score", not "_score")
p3 = c.structure({"name": "Carol", "score": 42}, Player)
assert p3._score == 42
```

### Roundtrip with Aliases

```python
hook_u = make_dict_unstructure_fn(Player, c, _cattrs_use_alias=True)
c.register_unstructure_hook(Player, hook_u)

player = Player(_name="Alice", _score=50)  # using alias kwarg: Player(name="Alice", score=50)
d = c.unstructure(player)
# {"name": "Alice", "score": 50}

p2 = c.structure(d, Player)
assert p2 == player  # roundtrip must preserve all fields
```

---

## 3. Optional[T] Unstructuring

### Overview

`Optional[T]` (i.e., `Union[T, None]`) fields are handled specially by cattrs.
When unstructuring an `Optional[T]` field:
- If the value is `None`, the output is `None`
- If the value is non-None, it is unstructured using the hook for type `T`

### Converter.gen_unstructure_optional

The `Converter` class generates specialized hooks for `Optional[T]` fields. This hook
selects the correct handler for the non-None type `T` and applies it to non-None values.

```python
@attr.s(auto_attribs=True)
class Address:
    street: str
    city: str

@attr.s(auto_attribs=True)
class Person:
    name: str
    address: Optional[Address] = None

c = Converter()

# Non-None value: address must be unstructured to a dict
p = Person(name="Alice", address=Address(street="123 Main", city="Springfield"))
d = c.unstructure(p)
# d == {"name": "Alice", "address": {"street": "123 Main", "city": "Springfield"}}
assert isinstance(d["address"], dict)

# None value: address must be None
p2 = Person(name="Bob")
d2 = c.unstructure(p2)
# d2 == {"name": "Bob", "address": None}
assert d2["address"] is None
```

### Invariant

For all `Optional[AttrsClass]` fields:
1. `unstructure(None_value)` → `None`
2. `unstructure(instance)` → `dict` (not the attrs instance itself)
3. `structure(unstructure(instance), Optional[AttrsClass]) == instance`

The unstructured result of a non-None `Optional[T]` field must be of the same type
that `structure` expects — typically a `dict` for attrs classes.

### Nested Optional

```python
@attr.s(auto_attribs=True)
class Tree:
    value: int
    left: Optional["Tree"] = None
    right: Optional["Tree"] = None

c = Converter()

# Even with recursive Optional, unstructuring must produce dicts not instances
t = Tree(value=1, left=Tree(value=2), right=None)
d = c.unstructure(t)
assert isinstance(d["left"], dict)
assert d["right"] is None

# Roundtrip
assert c.structure(d, Tree) == t
```

---

## 4. init=False Fields

### Overview

In attrs, a field can be marked with `init=False` to indicate it should NOT be
included in the `__init__` constructor. Such fields are typically computed in
`__attrs_post_init__` or set later.

```python
@attr.s(auto_attribs=True)
class Record:
    name: str
    value: int
    _hash: str = attr.ib(init=False)

    def __attrs_post_init__(self):
        import hashlib
        self._hash = hashlib.md5(f"{self.name}:{self.value}".encode()).hexdigest()
```

### Default Unstructuring Behavior

By default, `init=False` fields are **excluded** from the unstructured dict.
This is correct behavior because:
1. These fields cannot be passed to the constructor during structuring
2. They are derived/computed and should be regenerated from the init fields
3. Including them would introduce unnecessary data into serialized output

```python
c = Converter()
r = Record(name="test", value=42)
d = c.unstructure(r)
# d == {"name": "test", "value": 42}
# _hash is NOT included
assert "_hash" not in d

# Roundtrip works because _hash is recomputed in __attrs_post_init__
r2 = c.structure(d, Record)
assert r2.name == r.name and r2.value == r.value
```

### Opt-in Inclusion via _cattrs_include_init_false

To explicitly include `init=False` fields in the unstructured output, pass
`_cattrs_include_init_false=True` to `make_dict_unstructure_fn`:

```python
from cattrs.gen import make_dict_unstructure_fn

hook = make_dict_unstructure_fn(Record, c, _cattrs_include_init_false=True)
c.register_unstructure_hook(Record, hook)

d = c.unstructure(r)
# d == {"name": "test", "value": 42, "_hash": "..."}
assert "_hash" in d
```

### Invariants

1. **Default exclusion**: `c.unstructure(obj)` must NOT include `init=False` fields
   unless `_cattrs_include_init_false=True`

2. **Explicit inclusion**: When `_cattrs_include_init_false=True`, all `init=False`
   fields MUST appear in the unstructured dict

3. **Consistency**: The behavior is the inverse of what `init=False` means —
   "this field was not set by init" implies "it should not be serialized by default"

```python
# All of these must hold:
obj = MyClass(...)  # has init=False field _computed

# Default: exclude
d_default = Converter().unstructure(obj)
assert "_computed" not in d_default

# Explicit include
from cattrs.gen import make_dict_unstructure_fn
c2 = Converter()
hook = make_dict_unstructure_fn(MyClass, c2, _cattrs_include_init_false=True)
c2.register_unstructure_hook(MyClass, hook)
d_include = c2.unstructure(obj)
assert "_computed" in d_include
```

---

## 5. Converter Modes

### detailed_validation (default: True)

Controls whether structured exceptions include detailed per-field error information.

- `detailed_validation=True` (default): Collects all field errors and raises
  `ClassValidationError` with per-field notes. Slower but more informative.
- `detailed_validation=False`: Stops at the first error and raises immediately.
  Faster for performance-sensitive paths.

Both modes must produce IDENTICAL results for valid input — they only differ in
error handling behavior.

### omit_if_default (default: False)

When `True`, fields that equal their default value are omitted from the unstructured
dict. Combined with structuring, this enables compact serialization:

```python
@attr.s(auto_attribs=True)
class Config:
    host: str
    port: int = 8080
    debug: bool = False

c = Converter(omit_if_default=True)

obj = Config(host="localhost")  # port=8080, debug=False (defaults)
d = c.unstructure(obj)
# d == {"host": "localhost"}  (defaults are omitted)
assert "port" not in d
assert "debug" not in d

# Roundtrip must still work
obj2 = c.structure(d, Config)
assert obj2 == obj
```

### forbid_extra_keys (default: False)

When `True`, structuring raises an error if the input dict contains keys not
corresponding to any field in the class.

### use_alias (default: False)

When `True`, the attribute alias is used as the dict key instead of the attribute name.
This affects both structuring (which dict key to read) and unstructuring (which dict
key to write).

---

## 6. API Patterns Summary

### Pattern 1: Basic roundtrip

```python
c = Converter()
obj = MyClass(...)
assert c.structure(c.unstructure(obj), MyClass) == obj
```

### Pattern 2: Subclass hierarchy with include_subclasses

```python
include_subclasses(BaseClass, c)
# Any subclass instance can be unstructured/structured via the base type
# All subclass-specific fields are preserved
```

### Pattern 3: Private attrs with aliases

```python
@attr.s(auto_attribs=True)
class Cfg:
    _host: str = attr.ib(alias="host")
    _port: int = attr.ib(default=80, alias="port")

c = Converter(detailed_validation=False)
hook = make_dict_structure_fn(Cfg, c, _cattrs_use_alias=True)
c.register_structure_hook(Cfg, hook)
# Use alias keys in dicts: {"host": ..., "port": ...}
```

### Pattern 4: Optional attrs class fields

```python
@attr.s(auto_attribs=True)
class Container:
    item: Optional[SomeClass] = None

c = Converter()
# Unstructure: None stays None, SomeClass instance → dict
# Structure: None stays None, dict → SomeClass instance
```

### Pattern 5: Classes with computed fields

```python
@attr.s(auto_attribs=True)
class WithComputed:
    x: int
    _computed: str = attr.ib(init=False)
    def __attrs_post_init__(self): self._computed = str(self.x)

c = Converter()
# Default: _computed excluded from unstructured output
# structure(unstructure(obj)) recomputes _computed in __attrs_post_init__
```
