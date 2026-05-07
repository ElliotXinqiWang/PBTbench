# cattrs 26.1.0 — Advanced API Reference

cattrs is a Python library for structuring (dict/list → typed class) and
unstructuring (typed class → dict/list) Python objects. It provides a Converter
object that manages hooks for these transformations.

---

## 1. Converter and BaseConverter

### 1.1 Creating Converters

```python
from cattrs import Converter, BaseConverter

# Converter (recommended): generates optimized hooks automatically
c = Converter()
c = Converter(detailed_validation=True)   # default; produces detailed errors
c = Converter(omit_if_default=False)       # default; include fields at defaults
c = Converter(forbid_extra_keys=False)     # default; ignore unknown keys
c = Converter(use_alias=False)             # default; use field names as dict keys
```

### 1.2 Copying Converters

Converters can be copied to create independent instances that inherit all
registered hooks. Hooks registered after the copy is made are independent.

```python
c1 = Converter()
c1.register_unstructure_hook(MyClass, lambda obj: {...})

c2 = c1.copy()
# c2 has all the same hooks as c1 at the time of copying
# Hooks registered after this point are independent:
c2.register_structure_hook(AnotherClass, lambda d, t: ...)
```

**Invariant**: `c.copy()` produces a converter `c2` such that for any object `obj`
and any hook registered before the copy, `c2.unstructure(obj)` equals
`c.unstructure(obj)`, and similarly for `c2.structure(d, T)`.

Specifically, hooks registered via `register_unstructure_hook_func` (predicate-based
hooks) **must** be preserved in the copy. The copy operation transfers all custom
hooks — both type-specific (registered via `register_unstructure_hook`) and
predicate-based (registered via `register_unstructure_hook_func`).

### 1.3 Registering Hooks

```python
# Type-specific hook (exact type match)
c.register_unstructure_hook(MyClass, lambda obj: {"value": obj.value})
c.register_structure_hook(MyClass, lambda d, t: MyClass(d["value"]))

# Predicate-based hook (matches types by predicate)
c.register_unstructure_hook_func(
    lambda t: hasattr(t, "__my_marker__"),   # predicate
    lambda obj: obj.to_dict(),               # hook
)
c.register_structure_hook_func(
    lambda t: issubclass(t, MyBase),
    lambda d, t: t.from_dict(d),
)
```

Both types of hooks are preserved by `.copy()`. The invariant: any hook that
functions correctly on `c` also functions correctly on `c.copy()`.

---

## 2. make_dict_unstructure_fn — Generating Custom Unstructure Hooks

`make_dict_unstructure_fn` generates a specialized, optimized unstructure function
for an attrs class or dataclass.

### 2.1 Signature

```python
from cattrs.gen import make_dict_unstructure_fn, override

fn = make_dict_unstructure_fn(
    cl,                              # attrs class or dataclass
    converter,
    _cattrs_omit_if_default=False,   # omit fields equal to their default
    _cattrs_use_alias=False,         # use field aliases as dict keys
    _cattrs_include_init_false=False,
    **field_overrides,               # override(rename=..., omit=..., ...) per field
)
```

### 2.2 use_alias: Alias vs. Attribute Name

When `_cattrs_use_alias=True`, the generated function uses each field's **alias**
as the dictionary key, rather than the internal attribute name.

```python
@attr.s(auto_attribs=True)
class Config:
    _host: str = attr.ib(alias="host", default="localhost")
    _port: int = attr.ib(alias="port", default=8080)

c = Converter()
fn = make_dict_unstructure_fn(Config, c, _cattrs_use_alias=True)
obj = Config(host="example.com", port=9090)

result = fn(obj)
# result == {"host": "example.com", "port": 9090}
# (alias "host" used, not internal "_host")
```

**Invariant**: With `_cattrs_use_alias=True`, the dict keys are the alias names.
With `_cattrs_use_alias=False`, the dict keys are the attribute names.

This interacts with `make_dict_structure_fn(_cattrs_use_alias=True)`: the structure
function expects alias keys as input, and the unstructure function must produce
alias keys for roundtrip to work.

### 2.3 omit_if_default: Omitting Default-Valued Fields

When `_cattrs_omit_if_default=True`, fields whose current value equals the default
are omitted from the output dict. Only non-default values are included.

```python
@attr.s(auto_attribs=True)
class Record:
    name: str
    count: int = 0
    tag: str = ""

c = Converter()
fn = make_dict_unstructure_fn(Record, c, _cattrs_omit_if_default=True)

obj = Record(name="test", count=5, tag="")
result = fn(obj)
# result == {"name": "test", "count": 5}
# "tag" is omitted because it equals its default ""
```

**Invariant**: Fields with default values that equal the current value are absent
from the result dict. Fields with non-default values are present.

### 2.4 Combining omit_if_default with rename Overrides

The `override(rename="new_key")` per-field override changes the key name in the
output dict. When combined with `omit_if_default=True`, the renamed key is used
in the output whenever the field has a non-default value.

```python
fn = make_dict_unstructure_fn(
    ServiceConfig,
    c,
    _cattrs_omit_if_default=True,
    host=override(rename="server_host"),
    label=override(rename="service_label"),
)

obj = ServiceConfig(host="prod.com", label="production")
result = fn(obj)
# result == {"server_host": "prod.com", "service_label": "production"}
# (renamed keys used, NOT original names "host"/"label")
```

**Invariant**: When a field has a rename override AND a non-default value, the
renamed key appears in the output. The original attribute name must NOT appear
as a key when a rename is specified.

### 2.5 Pairing with make_dict_structure_fn for Roundtrip

```python
unstruct_fn = make_dict_unstructure_fn(
    MyClass, c,
    _cattrs_omit_if_default=True,
    field_a=override(rename="key_a"),
)
struct_fn = make_dict_structure_fn(
    MyClass, c,
    field_a=override(rename="key_a"),
)

obj = MyClass(field_a="value", field_b=0)
d = unstruct_fn(obj)   # {"key_a": "value"}   (field_b omitted, field_a renamed)
result = struct_fn(d, MyClass)
assert result == obj   # roundtrip must hold
```

---

## 3. make_dict_structure_fn — Generating Custom Structure Hooks

### 3.1 Signature

```python
from cattrs.gen import make_dict_structure_fn, override

fn = make_dict_structure_fn(
    cl,
    converter,
    _cattrs_forbid_extra_keys=False,
    _cattrs_use_alias=False,         # accept alias keys in input dict
    _cattrs_detailed_validation=True,
    **field_overrides,
)
```

### 3.2 use_alias in Structure

When `_cattrs_use_alias=True`, the function looks up alias names as dict keys
when reading from the input.

---

## 4. include_subclasses Strategy

`include_subclasses` configures a converter to handle attrs/dataclass class
hierarchies (base class + subclasses) transparently.

### 4.1 Basic Usage

```python
from cattrs.strategies import include_subclasses

@attr.s(auto_attribs=True)
class Animal:
    name: str

@attr.s(auto_attribs=True)
class Dog(Animal):
    breed: str

c = Converter()
include_subclasses(Animal, c)

dog = Dog(name="Rex", breed="Labrador")
d = c.unstructure(dog)
# d == {"name": "Rex", "breed": "Labrador"}
# (All fields, including Dog-specific ones, are included)

result = c.structure(d, Animal)
# result is a Dog instance (subclass preserved by structuring)
```

### 4.2 Unstructuring Through Typed Containers

When a container class has `List[Animal]` typed fields, unstructuring preserves
all fields for each element, regardless of whether the element is an `Animal`
or a `Dog`:

```python
@attr.s(auto_attribs=True)
class Zoo:
    animals: List[Animal]

zoo = Zoo(animals=[Dog(name="Rex", breed="Labrador"), Animal(name="Cat")])
d = c.unstructure(zoo)
# d == {"animals": [{"name": "Rex", "breed": "Labrador"}, {"name": "Cat"}]}
# Dog's "breed" field is preserved even though the list type is List[Animal]
```

**Invariant**: After `include_subclasses(Base, c)`, for any typed container
`List[Base]` containing subclass instances, `c.unstructure(container)` must
include ALL fields of each element (including subclass-specific ones). The
unstructuring must dispatch on the element's runtime type, not the static type.

### 4.3 Roundtrip Behavior

The roundtrip `c.structure(c.unstructure(obj, unstructure_as=Animal), Animal)`
must preserve all subclass information:

```python
dog = Dog(name="Rex", breed="Labrador")
d = c.unstructure(dog)            # {"name": "Rex", "breed": "Labrador"}
result = c.structure(d, Animal)   # Dog(name="Rex", breed="Labrador")
assert isinstance(result, Dog)    # Runtime type is Dog, not Animal
```

**Note**: Disambiguation of subclasses during structuring uses unique fields.
Each subclass must have at least one required field not present in sibling classes.

### 4.4 union_strategy Parameter

An optional `union_strategy` parameter allows customizing how the union of
subclasses is disambiguated:

```python
from cattrs.strategies import include_subclasses, configure_tagged_union

include_subclasses(
    Animal,
    c,
    union_strategy=lambda u, c: configure_tagged_union(u, c),
)
```

---

## 5. Converter.use_alias Configuration

Setting `use_alias=True` at the Converter level affects all auto-generated hooks:

```python
c = Converter(use_alias=True)
# All auto-generated structure/unstructure hooks use aliases as dict keys
```

This is equivalent to passing `_cattrs_use_alias=True` to every
`make_dict_structure_fn` and `make_dict_unstructure_fn` call.

**Invariant**: With `c = Converter(use_alias=True)`, for any attrs class with
aliased fields, `c.unstructure(obj)` uses alias names as keys, and
`c.structure(d, Cls)` accepts alias names as keys. The roundtrip
`c.structure(c.unstructure(obj), Cls) == obj` holds.

---

## 6. AttributeOverride and the override() Function

```python
from cattrs.gen import override

# Per-field customization
fn = make_dict_unstructure_fn(
    Cls, c,
    field_a=override(omit=True),                     # always omit this field
    field_b=override(omit_if_default=True),           # omit when at default
    field_c=override(rename="external_name"),         # rename in dict
    field_d=override(unstruct_hook=str),              # custom unstructure hook
)
```

Fields with `rename` have their key name changed in the output dict. Fields with
`omit_if_default=True` are omitted when at their default value. These settings
combine: a renamed field with `omit_if_default=True` uses the renamed key in the
output when the field has a non-default value.

---

## 7. Properties to Test

When writing property-based tests for cattrs, consider these invariants:

1. **Roundtrip**: `c.structure(c.unstructure(obj), type(obj)) == obj`
2. **Key invariant with use_alias**: With `use_alias=True`, `c.unstructure(obj)`
   uses alias names as keys
3. **omit_if_default correctness**: With `omit_if_default=True`, default-valued
   fields are absent; non-default-valued fields are present
4. **rename key invariant**: With `override(rename="new_key")`, the key `"new_key"`
   is in the unstructured dict (not the original field name) when the field is included
5. **copy hook preservation**: `c.copy()` preserves all hooks, including those
   registered via `register_unstructure_hook_func`
6. **include_subclasses field preservation**: Subclass fields are preserved in
   unstructuring, even through base-class-typed containers
