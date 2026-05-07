# cattrs 26.1.0 Converter API Reference

## Overview

`cattrs` is a Python library for structuring and unstructuring data. It converts
between unstructured types (dicts, lists, primitives) and structured types (attrs
classes, dataclasses, TypedDicts). The core component is the `Converter` class.

---

## Converter

### Constructor

```python
from cattrs import Converter

c = Converter(
    detailed_validation=True,    # Use detailed error reporting (slower but better errors)
    omit_if_default=False,       # Omit fields at their default value during unstructure
    forbid_extra_keys=False,     # Raise on unknown keys during structure
    type_overrides=None,         # Dict of {type: AttributeOverride} for customizing behavior
    unstruct_collection_overrides=None,  # Override collection unstructuring
    prefer_attrib_converters=False,      # Prefer attr.ib converter over type-based hooks
)
```

**Key parameters**:

- `detailed_validation`: When `True` (default), errors include context about which
  attribute failed. When `False`, uses a faster code path with less error detail.
  **Note**: The `False` code path generates different function code than the `True`
  path -- the two code paths are largely independent implementations.

- `omit_if_default`: When `True`, unstructuring omits fields whose values equal
  their defaults. The generated code compares each field's value against its default
  using `!=`. For example, if a field has `default=0` and the instance value is `0`,
  it is omitted from the output dict.

- `forbid_extra_keys`: When `True`, structuring raises if the input dict contains
  keys not corresponding to class attributes.

### Core Methods

#### `structure(obj, cl)`
Convert unstructured data to a structured type.

```python
import attr

@attr.s(auto_attribs=True)
class User:
    name: str
    age: int

c = Converter()
user = c.structure({"name": "Alice", "age": 30}, User)
# User(name='Alice', age=30)
```

#### `unstructure(obj, unstructure_as=None)`
Convert a structured object to primitives.

```python
d = c.unstructure(user)
# {'name': 'Alice', 'age': 30}
```

When `unstructure_as` is provided, the converter uses the hook registered for
that type instead of the object's actual type. This is important for unions:

```python
from typing import Union

d = c.unstructure(obj, Union[Cat, Dog])  # Use the union unstructure hook
```

### Registering Custom Hooks

#### `register_structure_hook(cl, func)`
Register a structure hook for a specific type.

```python
c.register_structure_hook(User, lambda d, t: User(name=d["name"].upper(), age=d["age"]))
```

#### `register_structure_hook_func(check_func, hook_func)`
Register a structure hook that applies to types matching `check_func`.

```python
# Apply to any type that has a 'from_dict' class method
c.register_structure_hook_func(
    lambda t: hasattr(t, 'from_dict'),
    lambda d, t: t.from_dict(d)
)
```

**Important**: These hooks are stored in a `FunctionDispatch` which uses a priority
queue. Newer hooks (registered later) take precedence over older ones.

#### `register_unstructure_hook(cl, func)` / `register_unstructure_hook_func(check_func, hook_func)`
Analogous to the structure hooks, for unstructuring.

### Converter.copy()

Creates a copy of the converter with all registered hooks preserved.

```python
c1 = Converter()
c1.register_structure_hook_func(
    lambda t: t is MyClass,
    lambda d, t: MyClass(**d)
)

c2 = c1.copy()
# c2 should have all hooks from c1, including custom func hooks
```

The copy mechanism works by copying the internal dispatch registries. Each dispatch
has three layers:
1. **singledispatch**: Type-specific hooks (via `register_structure_hook`)
2. **direct_dispatch**: Cached resolved hooks
3. **function_dispatch**: Predicate-based hooks (via `register_structure_hook_func`)

The `copy_to` method of `FunctionDispatch` copies handler pairs from the source
to the target, skipping the default handlers that the new converter already has.

---

## Code Generation: `cattrs.gen`

### `make_dict_structure_fn(cl, converter, **kwargs)`
Generate a structuring function for attrs classes.

```python
from cattrs.gen import make_dict_structure_fn

hook = make_dict_structure_fn(MyClass, converter)
converter.register_structure_hook(MyClass, hook)
```

**Key keyword arguments**:
- `_cattrs_use_alias`: When `True`, uses `attr.ib(alias=...)` as the dict key
  instead of the attribute name. Useful when the Python attribute name uses a
  private convention (e.g., `_host`) but the external representation uses a
  public name (e.g., `host`).
- `_cattrs_detailed_validation`: Override the converter's `detailed_validation`.
- `_cattrs_forbid_extra_keys`: Override the converter's `forbid_extra_keys`.
- `_cattrs_prefer_attrib_converters`: Override converter's prefer_attrib_converters.
- `_cattrs_include_init_false`: Include non-init attributes in structuring.

**Per-attribute overrides** (passed as keyword args with attribute names):
```python
from cattrs.gen import override

hook = make_dict_structure_fn(
    MyClass, converter,
    field_name=override(rename="external_name", struct_hook=custom_hook)
)
```

### `make_dict_unstructure_fn(cl, converter, **kwargs)`
Generate an unstructuring function for attrs classes.

Similar keyword arguments to `make_dict_structure_fn`, plus:
- `_cattrs_omit_if_default`: Override the converter's `omit_if_default` for this
  specific type. When `True`, generated code checks each field against its default
  and only includes non-default values in the output dict.
- `_cattrs_use_alias`: When `True`, uses attribute aliases as dict keys.

### Attribute handling: kw_only and alias

When an attrs class uses `kw_only=True`, all attributes must be passed as keyword
arguments to `__init__`. Combined with `alias`, this means:

```python
import attr

@attr.s(auto_attribs=True, kw_only=True)
class Server:
    _host: str = attr.ib(alias="host")
    _port: int = attr.ib(alias="port", default=8080)

# Construction uses aliases as keyword names:
s = Server(host="localhost", port=9090)
# s._host == "localhost", s._port == 9090
```

When generating structure code with `_cattrs_use_alias=True`, the generated function
must:
1. Read from dict keys using the alias (e.g., `o['host']`)
2. Pass values to `__init__` using the alias as keyword name (e.g., `host=value`)

The alias is what `__init__` expects as the keyword argument name when `kw_only=True`.

---

## Strategies: Tagged Unions

### `configure_tagged_union(union, converter, tag_name="_type", tag_generator=None, ...)`

Configures structure/unstructure hooks for a union type using a type tag field.

```python
from typing import Union
from cattrs.strategies import configure_tagged_union

@attr.s(auto_attribs=True)
class Cat:
    name: str

@attr.s(auto_attribs=True)
class Dog:
    name: str

c = Converter()
configure_tagged_union(Union[Cat, Dog], c)
# Default tag_generator uses cl.__name__: Cat -> "Cat", Dog -> "Dog"
```

**Parameters**:
- `tag_name`: The key in the dict that holds the type tag (default: `"_type"`).
- `tag_generator`: A callable `(type) -> str` that produces the tag for each
  union member. Default is `lambda t: t.__name__`.
- `default`: Default type to use when the tag doesn't match any member.

**Custom tag_generator example**:
```python
configure_tagged_union(
    Union[Cat, Dog], c,
    tag_generator=lambda t: t.__name__.lower()
)
# Tags are: Cat -> "cat", Dog -> "dog"

d = c.unstructure(Cat(name="Whiskers"), Union[Cat, Dog])
# d == {"_type": "cat", "name": "Whiskers"}

result = c.structure(d, Union[Cat, Dog])
# result == Cat(name="Whiskers")
```

The tag is used bidirectionally:
- **Structuring**: The `_type` field is read from the input dict, looked up in a
  `tag -> class` mapping, and the corresponding class is structured.
- **Unstructuring**: The object's class is looked up in a `class -> tag` mapping,
  and the tag is added to the output dict.

Both mappings must use the same tag values for roundtrip to work correctly.

---

## Union Disambiguation

cattrs can automatically disambiguate union types based on:

1. **Unique fields**: If each union member has a unique field name, the presence
   of that field determines the type.

2. **Literal discriminators**: If union members have `Literal` type fields, the
   literal values can serve as discriminators. The field with the best (lowest
   max-overlap) discrimination is selected.

```python
from typing import Literal, Union

@attr.s(auto_attribs=True)
class Success:
    status: Literal["ok"] = "ok"
    data: str = ""

@attr.s(auto_attribs=True)
class Error:
    status: Literal["error"] = "error"
    message: str = ""

c = Converter()
# Automatically uses 'status' field for disambiguation
c.structure({"status": "ok", "data": "hello"}, Union[Success, Error])
# -> Success(status='ok', data='hello')
```

---

## Dispatch Mechanism

cattrs uses a multi-layer dispatch system:
1. **singledispatch**: Type-specific hooks registered via `register_structure_hook`
2. **direct_dispatch**: Cached/resolved hooks for fast lookup
3. **function_dispatch**: Predicate-based hooks (via `register_structure_hook_func`)

When a type needs to be structured/unstructured:
1. Check singledispatch first
2. Then check direct_dispatch cache
3. Finally iterate function_dispatch predicates (newest first)

The function_dispatch uses `FunctionDispatch`, which stores `(predicate, handler)`
pairs. When copying converters, `FunctionDispatch.copy_to()` transfers these pairs
from the source to the target, preserving custom hooks alongside the new converter's
default handlers.
