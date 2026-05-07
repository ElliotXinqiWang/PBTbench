# attrs Class Construction API — Official Documentation Excerpt

**Library**: attrs 25.4.0
**Scope**: Class-building machinery, inheritance, field collection, hashability, kw_only

---

## Overview

attrs generates Python classes automatically. When you decorate a class with
`@attrs.define` or `@attr.s`, attrs inspects the class body, collects field
definitions, and injects generated dunder methods (`__init__`, `__repr__`,
`__eq__`, `__hash__`, etc.).

The class-building process is implemented in `attr/_make.py` and involves:
1. Collecting fields from base classes via MRO traversal
2. Combining base attrs with the class's own attrs
3. Generating `__init__` code from the combined field list
4. Determining hashability based on `eq` and `frozen` settings
5. Handling `kw_only` propagation for subclasses

---

## Class Decorators

### `@attrs.define` (modern API)
```python
@attrs.define
class Point:
    x: int
    y: int = 0
```
- Collects fields via MRO (method resolution order) — always uses `collect_by_mro=True`
- `eq=True`, `order=True`, `frozen=False` by default
- Slots by default (creates a new slotted class)

### `@attr.s` / `@attrs.attrs` (classic API)
```python
@attr.s
class Point:
    x = attr.ib()
    y = attr.ib(default=0)
```
- `collect_by_mro=False` by default (old incorrect behavior, preserved for compatibility)
- Use `@attr.s(collect_by_mro=True)` for correct MRO-based collection

### `attr.make_class(name, attrs, bases=(object,), **kwargs)`
A convenience function for creating attrs classes dynamically. Accepts all the
same keyword arguments as `@attr.s`. Pass `collect_by_mro=True` to enable
correct MRO-based field collection.

---

## Field Collection and Inheritance

### MRO-based Collection (`collect_by_mro=True`)

When `collect_by_mro=True` is set (default for `@attrs.define`), attrs collects
base class fields by traversing the MRO from **least specific** (most distant
ancestor) to **most specific** (closest ancestor). This ensures that when a
parent class overrides a grandparent's field, the parent's version wins.

**Invariant**: `attrs.fields(Child)` starts with all inherited fields (from base
classes in MRO order), followed by the child class's own fields.

```python
@attrs.define
class GrandParent:
    x: int = 0
    y: int = 10

@attrs.define
class Parent(GrandParent):
    x: int = 100  # overrides GrandParent.x with different default

@attrs.define
class Child(Parent):
    z: int = 5   # own field, comes AFTER inherited fields

# attrs.fields(Child) == (x_from_Parent, y_from_GrandParent, z)
# attrs.fields(Child).x.default == 100  (Parent's version, NOT GrandParent's 0)
# attrs.fields(Child) order: [x, y, z]   # inherited first, own last
```

### Field Order Invariant

`attrs.fields(SomeClass)` always returns:
1. **Inherited fields** (from base attrs classes) in MRO order
2. **Own fields** (defined directly on `SomeClass`) in definition order

This ordering directly determines the `__init__` parameter order. Positional
instantiation assigns values in this order:
```python
child = Child(x_val, y_val, z_val)
# child.x == x_val, child.y == y_val, child.z == z_val
```

---

## Hashability

### Rules (when `hash=None`, the default)

| `eq`  | `frozen` | Hashability |
|-------|----------|-------------|
| True  | True     | **Hashable** — attrs generates `__hash__` |
| True  | False    | **Unhashable** — attrs sets `__hash__ = None` |
| False | any      | Not touched — class inherits hash from parent |

**Frozen + eq = hashable**: Python convention for immutable classes. A frozen
attrs class with `eq=True` (the default) MUST support `hash()`. Instances
can be used as dictionary keys and in sets.

```python
@attrs.define(frozen=True)
class FrozenPoint:
    x: int
    y: int

fp = FrozenPoint(1, 2)
d = {fp: "hello"}         # OK: frozen class is hashable
s = {FrozenPoint(1, 2)}   # OK: frozen class can be in a set
```

**Mutable + eq = unhashable**: Python convention prevents mutable objects from
being hashable to avoid silent bugs with containers. A non-frozen attrs class
with `eq=True` MUST have `__hash__ = None`:

```python
@attrs.define  # eq=True, frozen=False
class MutablePoint:
    x: int
    y: int

mp = MutablePoint(1, 2)
hash(mp)  # raises TypeError: unhashable type: 'MutablePoint'
```

### Explicit hash Control

Pass `hash=True` to force hash generation even without `frozen=True`:
```python
@attr.s(hash=True)
class ExplicitHash:
    x = attr.ib()
```

Pass `hash=False` to suppress hash generation entirely.
Pass `cache_hash=True` (with `frozen=True` or `hash=True`) to cache the hash value.

---

## Keyword-Only Fields (`kw_only`)

### Per-Field kw_only
```python
@attrs.define
class Config:
    host: str           # positional
    port: int = 8080   # positional with default
    debug: bool = attrs.field(default=False, kw_only=True)  # keyword-only
```

### Class-Level kw_only

`@attrs.define(kw_only=True)` applies keyword-only behavior to the **current
class's own fields** only. Inherited fields from base classes are not affected
unless they already had `kw_only=True`.

```python
@attrs.define
class Base:
    x: int         # positional

@attrs.define(kw_only=True)
class Child(Base):
    y: int = 5    # keyword-only (own field)

# Base fields keep their positional behavior:
c = Child(1, y=10)  # OK: x=1 positionally, y=10 by keyword
```

### `force_kw_only=True` — Forces ALL Fields to Keyword-Only

`@attrs.define(kw_only=True, force_kw_only=True)` forces **ALL** fields to be
keyword-only, **including inherited fields**.

```python
@attrs.define
class Base:
    x: int         # normally positional

@attrs.define(kw_only=True, force_kw_only=True)
class ForceChild(Base):
    y: int = 5

# ALL fields are now keyword-only:
# ForceChild(1)          # TypeError: takes 1 positional argument but 2 were given
# ForceChild(x=1)        # OK: x is now keyword-only
# ForceChild(x=1, y=10)  # OK

# attrs.fields(ForceChild).x.kw_only == True   (inherited field forced to kw_only)
# attrs.fields(ForceChild).y.kw_only == True   (own field)
```

**Invariant**: When `force_kw_only=True`, ALL entries in `attrs.fields(SomeClass)`
must have `kw_only=True`, including those inherited from base classes.

---

## Field Introspection

### `attrs.fields(cls)` → tuple of `attrs.Attribute`

Returns an ordered tuple of all attrs attributes for a class, including inherited ones.

Each `Attribute` has:
- `name` (str): field name
- `default`: default value or `attrs.NOTHING` if no default
- `kw_only` (bool): whether field is keyword-only in `__init__`
- `inherited` (bool): whether field comes from a base class
- `eq` (bool): whether field participates in equality comparison
- `hash` (bool | None): whether field participates in hash computation
- `repr` (bool): whether field appears in `__repr__`
- `init` (bool): whether field appears in `__init__`

```python
@attrs.define
class Point:
    x: int
    y: int = 0

f = attrs.fields(Point)
# f[0].name == "x",  f[0].default == attrs.NOTHING, f[0].kw_only == False
# f[1].name == "y",  f[1].default == 0, f[1].kw_only == False

@attrs.define
class SubPoint(Point):
    z: int = 5

sf = attrs.fields(SubPoint)
# sf[0].name == "x", sf[0].inherited == True    (from Point)
# sf[1].name == "y", sf[1].inherited == True    (from Point)
# sf[2].name == "z", sf[2].inherited == False   (own field)
```

### `attrs.fields_dict(cls)` → dict[str, Attribute]

Returns an ordered dictionary `{name: Attribute}` for all fields.

---

## Multiple Inheritance and MRO

attrs supports multiple inheritance. Field collection follows Python's MRO
(method resolution order, C3 linearization). When `collect_by_mro=True` is
used:

```python
@attrs.define
class A:
    x: int = 1

@attrs.define
class B(A):
    x: int = 2   # overrides A.x

@attrs.define
class C(B):
    pass

# attrs.fields(C).x.default == 2  (B's override wins, not A's original)
# This is because MRO is [C, B, A]: B is more specific than A
```

---

## Validation and Conversion

### Validators

Validators run during `__init__` and `attrs.validate()`. They are not affected
by MRO or field ordering bugs — they run on whatever value was set.

```python
@attrs.define
class Config:
    port: int = attrs.field(validator=attrs.validators.instance_of(int))
    host: str = attrs.field(validator=attrs.validators.instance_of(str))
```

---

## Frozen Classes

A frozen attrs class prevents attribute assignment after initialization. Combined
with `eq=True` (the default), it:
1. Generates `__hash__` (instances are hashable)
2. Raises `FrozenInstanceError` on any attribute assignment
3. Can be used as dictionary keys and in sets

```python
@attrs.define(frozen=True)
class ImmutableRecord:
    id: int
    name: str

r = ImmutableRecord(1, "Alice")
r.id = 2          # raises FrozenInstanceError
hash(r)           # works
d = {r: "data"}   # works as dict key
```

---

## __init__ Generation

attrs generates `__init__` from the field list. The parameter order follows
`attrs.fields(cls)` order: inherited fields come before own fields.

```python
@attrs.define
class Parent:
    x: int
    y: int = 0

@attrs.define
class Child(Parent):
    z: int = 5

# Generated __init__ signature: Child(x, y=0, z=5)
# attrs.fields(Child) == [x, y, z]  — inherited x, y first; own z last
```

If the field order were reversed (own before inherited), the signature would be
`Child(z=5, x, y=0)`, which has a mandatory parameter after an optional one
(only valid because z has a default, x doesn't in this example — but in
general this is problematic and violates the field-order invariant).

---

## attrs.evolve(inst, **changes)

Creates a new instance with specified field values changed. All unchanged fields
are copied from the original instance.

```python
@attrs.define(frozen=True)
class Point:
    x: int
    y: int

p = Point(1, 2)
p2 = attrs.evolve(p, x=10)
# p2.x == 10, p2.y == 2
# p unchanged: p.x == 1
```

`evolve()` works on both frozen and non-frozen classes.
