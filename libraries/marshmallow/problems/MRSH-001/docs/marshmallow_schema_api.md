# marshmallow 4.2.2 Schema API Reference

marshmallow is a schema-based Python serialization/deserialization library.
Schemas define how to convert Python objects to/from native Python datatypes (dicts, lists).

---

## Core Concepts

### Schema Definition

A `Schema` subclass declares fields as class attributes:

```python
import marshmallow as ma

class UserSchema(ma.Schema):
    name = ma.fields.String(required=True)
    age = ma.fields.Integer(load_default=0)
    email = ma.fields.Email()
```

### Dump (Serialize)

`Schema.dump(obj)` converts an object to a dict:

```python
schema = UserSchema()
result = schema.dump({"name": "Alice", "age": 30})
# => {'name': 'Alice', 'age': 30}

# Many=True for lists
result = schema.dump([{"name": "A"}, {"name": "B"}], many=True)
# => [{'name': 'A'}, {'name': 'B'}]
```

### Load (Deserialize + Validate)

`Schema.load(data)` converts a dict to a Python object (also validates):

```python
result = schema.load({"name": "Bob", "age": 25})
# => {'name': 'Bob', 'age': 25}
```

### Dumps/Loads (JSON)

`dumps()` and `loads()` wrap `dump()`/`load()` with JSON encoding/decoding.

---

## Field Types

### Basic Fields

| Field | Python Type | Notes |
|---|---|---|
| `String` / `Str` | `str` | |
| `Integer` / `Int` | `int` | |
| `Float` | `float` | |
| `Boolean` / `Bool` | `bool` | |
| `Decimal` | `decimal.Decimal` | |
| `Date` | `datetime.date` | ISO 8601 format by default |
| `DateTime` | `datetime.datetime` | ISO 8601 format by default |
| `Time` | `datetime.time` | |
| `TimeDelta` | `datetime.timedelta` | |
| `UUID` | `uuid.UUID` | |
| `Email` | `str` | validates email format |
| `Url` | `str` | validates URL format |
| `Raw` | any | pass-through |

### Common Field Parameters

All fields accept:
- `required=True` — raise `ValidationError` if field is missing during load
- `load_default=value` — default value when field is missing during load
- `dump_default=value` — default value when field is missing during dump
- `allow_none=True` — accept `None` as a valid value
- `load_only=True` — field is excluded from dump output
- `dump_only=True` — field is excluded from load output
- `validate=callable` — validator(s) called during deserialization
- `data_key="ext_name"` — use a different key in the external (serialized) representation
- `attribute="internal_name"` — use a different attribute/key in the internal (deserialized) representation

#### The `attribute` parameter

The `attribute` parameter controls the key used in the **internal** (Python-side) representation:

```python
class MySchema(ma.Schema):
    # Field named 'status' in the schema (external key)
    # but maps to 'is_active' in the deserialized result
    status = ma.fields.String(attribute="is_active")

schema = MySchema()
result = schema.load({"status": "active"})
# => {'is_active': 'active'}   # key is 'is_active', not 'status'

# For dump: reads from obj.is_active, outputs as 'status'
result = schema.dump({"is_active": "active"})
# => {'status': 'active'}
```

**Invariant**: `schema.load({"field": v})["attr_value"] == v` when `attribute="attr_value"` is set.
That is, `load()` stores values under the `attribute` name, not the field name.

#### The `data_key` parameter

The `data_key` parameter controls the key used in the **external** (wire) representation:

```python
class MySchema(ma.Schema):
    # Internal key is 'full_name', external key is 'name'
    full_name = ma.fields.String(data_key="name")

schema = MySchema()
result = schema.load({"name": "Alice"})
# => {'full_name': 'Alice'}

result = schema.dump({"full_name": "Alice"})
# => {'name': 'Alice'}
```

---

## Nested Schemas

`fields.Nested` allows embedding one schema inside another:

```python
class AddressSchema(ma.Schema):
    street = ma.fields.String()
    city = ma.fields.String()
    zip_code = ma.fields.String()

class PersonSchema(ma.Schema):
    name = ma.fields.String()
    address = ma.fields.Nested(AddressSchema)
```

### Nested Field Parameters

- `many=True` — the nested field is a list
- `only=(...)` — whitelist of nested fields to include
- `exclude=(...)` — blacklist of nested fields to exclude

### Combining `only` on Schema Instance and Nested Field

When you pass a Schema **instance** (not class) to `Nested` and both the schema instance and the `Nested` field have `only` parameters, the resulting field set is the **intersection**:

```python
# AddressSchema instance restricted to ('city', 'zip_code')
address_restricted = AddressSchema(only=('city', 'zip_code'))

class PersonSchema(ma.Schema):
    # Nested field further restricts to only 'city'
    address = ma.fields.Nested(address_restricted, only=('city',))

# The effective only = intersection({'city'}, {'city', 'zip_code'}) = {'city'}
# So only 'city' will appear in the output
schema = PersonSchema()
result = schema.dump({"name": "Alice", "address": {"street": "Main", "city": "NYC", "zip_code": "10001"}})
# => {'name': 'Alice', 'address': {'city': 'NYC'}}
```

**Invariant**: The `only` parameter is a **whitelist** — fields NOT in `only` will not appear.
When both the schema instance and the Nested field specify `only`, the effective set is
the **intersection** (the more restrictive of the two sets). A field only appears if it is
present in **all** specified `only` lists.

```python
# If only sets are disjoint, NO fields will appear
address_with_city = AddressSchema(only=('city',))
class PersonSchema(ma.Schema):
    address = ma.fields.Nested(address_with_city, only=('street',))
# effective only = intersection({'street'}, {'city'}) = {} -> empty dict
```

---

## `many=True` Schemas

Schemas can process collections:

```python
# Via parameter
schema = UserSchema(many=True)
result = schema.dump([{"name": "A"}, {"name": "B"}])

# Via method argument (takes precedence)
schema = UserSchema()
result = schema.dump([{"name": "A"}], many=True)
```

**Invariant**: `schema.dump(obj, many=True)[i]` equals `schema.dump(obj[i], many=False)` for all valid `i`.

---

## `partial` Loading

The `partial` parameter controls which fields are required during load:

```python
# All fields optional
result = schema.load({"name": "Alice"}, partial=True)

# Only specific fields optional
result = schema.load({"name": "Alice"}, partial=("age",))
```

---

## Unknown Fields

Control how unknown (extra) fields in input are handled via `Meta.unknown` or the `unknown` parameter:

```python
from marshmallow import EXCLUDE, INCLUDE, RAISE

class MySchema(ma.Schema):
    class Meta:
        unknown = EXCLUDE  # silently drop unknown fields

# Or at load time:
result = schema.load(data, unknown=EXCLUDE)
```

- `RAISE` (default) — raise `ValidationError` for unknown fields
- `EXCLUDE` — silently ignore unknown fields
- `INCLUDE` — include unknown fields in the result as-is

---

## Decorators: Pre/Post Processing Hooks

Schemas support decorator-based hooks for pre/post processing.

### Available Decorators

| Decorator | When Called | Input | Output |
|---|---|---|---|
| `@pre_load` | before `load()`'s deserialization | raw input data | transformed data |
| `@post_load` | after `load()`'s deserialization | deserialized result | final result |
| `@pre_dump` | before `dump()`'s serialization | object to serialize | transformed object |
| `@post_dump` | after `dump()`'s serialization | serialized dict | final result |
| `@validates("field")` | field-level validation during `load()` | field value | raise `ValidationError` or return value |
| `@validates_schema` | schema-level validation during `load()` | deserialized data | raise `ValidationError` |

### The `pass_collection` Parameter

By default, when `many=True`, hooks receive **individual items** one at a time.
With `pass_collection=True`, the hook receives the **entire collection** at once:

```python
class MySchema(ma.Schema):
    items = ma.fields.List(ma.fields.Integer())

    @ma.pre_load(pass_collection=True)
    def unwrap_envelope(self, data, many, **kwargs):
        # Receives the full list when many=True
        # Called BEFORE per-item processors
        if many and isinstance(data, dict):
            return data.get("results", data)
        return data

    @ma.pre_load
    def add_defaults(self, data, many, **kwargs):
        # Receives individual items when many=True
        # Called AFTER pass_collection=True processors
        if "items" not in data:
            data = dict(data, items=[])
        return data
```

**Critical ordering invariant**: When `many=True`, `@pre_load(pass_collection=True)` processors
run **before** `@pre_load` (per-item) processors. This ensures that collection-level
transformations (e.g., unwrapping an envelope, computing collection-wide statistics)
see the **original, untransformed collection data** before per-item processors have modified
individual items.

Similarly for `@post_load`: `pass_collection=True` runs AFTER per-item processors
(symmetric with `@pre_load`).

The documented ordering for pre-load processing is:
1. All `@pre_load(pass_collection=True)` hooks run first (see full collection)
2. Then all `@pre_load` hooks run per-item (see individual items)

```python
class BatchSchema(ma.Schema):
    value = ma.fields.Integer()
    batch_sum = ma.fields.Integer()

    @ma.pre_load(pass_collection=True)
    def compute_batch_sum(self, data, many, **kwargs):
        # Runs FIRST: sees original values
        # batch_sum should equal sum of original 'value' fields
        if many:
            total = sum(item.get("value", 0) for item in data)
            return [dict(item, batch_sum=total) for item in data]
        return data

    @ma.pre_load
    def scale_value(self, data, many, **kwargs):
        # Runs SECOND: scales values by 100
        return dict(data, value=data.get("value", 0) * 100)
```

With the documented ordering, `compute_batch_sum` sees the original values (e.g., 1, 2)
and computes `batch_sum=3`. Then `scale_value` turns values into 100, 200.
Final result: `[{value: 100, batch_sum: 3}, {value: 200, batch_sum: 3}]`.

---

## Validators

### `validate.Range`

Validates that a numeric value is within a range:

```python
age = ma.fields.Integer(validate=ma.validate.Range(min=0, max=150))
score = ma.fields.Float(validate=ma.validate.Range(min=0.0, max=1.0))
```

Parameters:
- `min` — minimum value (default: `None`, no minimum)
- `max` — maximum value (default: `None`, no maximum)
- `min_inclusive=True` — whether the minimum is inclusive (default: `True`)
  - `True` (default): value **≥** min is valid
  - `False`: value **>** min is valid (strict)
- `max_inclusive=True` — whether the maximum is inclusive (default: `True`)
  - `True` (default): value **≤** max is valid
  - `False`: value **<** max is valid (strict)

**Invariant**: With `Range(min=N, min_inclusive=True)` (the default),
values **equal to N** MUST be accepted as valid. The boundary is **inclusive**.

```python
validator = ma.validate.Range(min=5)  # min_inclusive=True by default
validator(5)   # OK — equal to min, should pass
validator(6)   # OK — above min, should pass
validator(4)   # raises ValidationError — below min

validator_strict = ma.validate.Range(min=5, min_inclusive=False)
validator_strict(5)  # raises ValidationError — equal to min, strict mode rejects it
validator_strict(6)  # OK — above min
```

Similarly for `max`:
- `Range(max=10)`: values ≤ 10 are valid (including 10)
- `Range(max=10, max_inclusive=False)`: values < 10 are valid (10 is rejected)

### `validate.Length`

Validates string or collection length:

```python
name = ma.fields.String(validate=ma.validate.Length(min=1, max=100))
```

### `validate.OneOf`

Validates that the value is one of a set of choices:

```python
status = ma.fields.String(validate=ma.validate.OneOf(["active", "inactive", "pending"]))
```

---

## Error Handling

`Schema.load()` raises `ValidationError` with structured error messages:

```python
from marshmallow import ValidationError

try:
    result = schema.load(bad_data)
except ValidationError as e:
    e.messages  # dict: {field_name: [error_messages]}
    e.valid_data  # partially-valid data (if any)
```

For `many=True`, errors are keyed by index:
```python
# e.messages = {0: {'name': ['Missing data for required field.']}, 2: {'age': ['Not a valid integer.']}}
```

---

## Schema Inheritance and Meta Options

### Meta Class

```python
class UserSchema(ma.Schema):
    class Meta:
        unknown = ma.EXCLUDE   # how to handle unknown fields
        many = True             # default many=True for this schema
        load_only = ("password",)   # fields excluded from dump
        dump_only = ("created_at",) # fields excluded from load
```

### Schema.from_dict

Dynamically generate a schema class from a field dictionary:

```python
PersonSchema = ma.Schema.from_dict({
    "name": ma.fields.String(),
    "age": ma.fields.Integer(),
})
schema = PersonSchema()
```

---

## Key Invariants Summary

These are the documented invariants that valid marshmallow behavior must satisfy:

1. **Dump roundtrip**: `schema.load(schema.dump(obj)) == obj` for schemas where all fields are bidirectional
2. **Many consistency**: `schema.dump(lst, many=True)[i] == schema.dump(lst[i])` for all `i`
3. **`only` restriction**: Fields NOT in `only` never appear in dump/load output
4. **`only` intersection**: When a Nested field's `only` and the nested schema instance's `only` are both set, the effective fields = intersection of both sets
5. **`attribute` mapping**: `schema.load({"field": v})["attr"] == v` when `attribute="attr"` is set on the field
6. **`Range(min=N)` boundary**: Values equal to `N` are valid when `min_inclusive=True` (default)
7. **pre_load ordering**: `@pre_load(pass_collection=True)` runs before `@pre_load` when `many=True`
8. **Error isolation**: A validation error in field X does not affect the deserialized value of field Y
