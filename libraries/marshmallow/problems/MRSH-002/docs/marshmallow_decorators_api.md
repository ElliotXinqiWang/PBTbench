# marshmallow 4.2.2 — Decorators, Field Hooks, and Specialized Field API

## Overview

marshmallow provides a decorator-based hook system that allows schema methods to
pre-process or post-process data at various stages of serialization and
deserialization. This document covers the hook decorators, their `pass_collection`
semantics, and the specialized field types relevant to this problem.

---

## 1. Hook Decorators

### @pre_load

```python
@pre_load
def method(self, data, many, **kwargs):
    ...
    return data
```

Registered method is called **before** `Schema.load()` deserializes data. The method
receives the raw input data and must return the (possibly modified) data to pass to
deserialization.

By default, when `schema.load(items, many=True)` is called, marshmallow calls the
`@pre_load` method **once per item** in the collection. Each call receives a single
item dict.

### @pre_load(pass_collection=True)

```python
@pre_load(pass_collection=True)
def method(self, data, many, **kwargs):
    ...
    return data
```

When `pass_collection=True`, the method receives the **entire collection** (the list)
as a single call when `many=True`. This is used for operations that must see all items
at once, such as removing an outer envelope, reordering items, or filtering the
collection.

**Execution order (load pipeline)**:
1. `@pre_load(pass_collection=True)` hooks run first (collection-level)
2. `@pre_load` hooks run second (per-item)
3. Field deserialization happens
4. `@validates` and `@validates_schema` run
5. `@post_load` hooks run (per-item, then collection-level)

### @post_load

```python
@post_load
def method(self, data, many, **kwargs):
    ...
    return data
```

Called **after** deserialization. By default called per-item when `many=True`.

### @post_load(pass_collection=True)

Receives the full deserialized list as one call. Used for adding envelopes or
transforming the collection as a whole.

### @pre_dump

```python
@pre_dump
def method(self, obj, many, **kwargs):
    ...
    return obj
```

Called before `Schema.dump()` serializes an object. Receives the input object and
returns the (possibly modified) object to serialize.

### @pre_dump(pass_collection=True)

Receives the whole collection when `schema.dump(objs, many=True)` is called.

### @post_dump

```python
@post_dump
def method(self, data, many, **kwargs):
    ...
    return data
```

Called after serialization. Returns the (possibly modified) serialized dict.

### @post_dump(pass_collection=True)

Receives the full list of serialized dicts. Used for adding outer envelopes:

```python
@post_dump(pass_collection=True)
def add_envelope(self, data, many, **kwargs):
    return {"results": data}
```

When `schema.dump(objs, many=True)` is called, the output will be
`{"results": [item1, item2, ...]}` instead of `[item1, item2, ...]`.

**Execution order (dump pipeline)**:
1. `@pre_dump` hooks (per-item, then collection-level)
2. Field serialization
3. `@post_dump` hooks (per-item first, then `pass_collection=True`)

---

## 2. @validates

```python
@validates("field_name")
def validate_field(self, value, **kwargs):
    if not valid:
        raise ValidationError("message")
```

Called during deserialization to validate a single field's deserialized value.
Can validate multiple fields by passing multiple names:

```python
@validates("field_a", "field_b")
def validate_fields(self, value, **kwargs):
    ...
```

---

## 3. @validates_schema

```python
@validates_schema
def validate_schema(self, data, **kwargs):
    if data["end"] <= data["start"]:
        raise ValidationError("end must be after start")
```

Called after all field-level validation. Receives the full deserialized dict.
By default `skip_on_field_errors=True`, so it is skipped if any field has errors.

---

## 4. pass_many (legacy) vs pass_collection

In marshmallow 4.0, `pass_many` was renamed to `pass_collection`. They have the
same semantics. Old code using `pass_many=True` should be updated to
`pass_collection=True`.

---

## 5. Schema.dump() and Schema.load() Pipeline

### dump(obj, many=False)

```python
result = schema.dump({"name": "Alice", "age": 30})
result = schema.dump([{"name": "Alice"}, {"name": "Bob"}], many=True)
```

Pipeline:
1. Run `@pre_dump` processors (per-item, then pass_collection)
2. Serialize each field
3. Run `@post_dump` processors (per-item, then pass_collection)

### load(data, many=False, partial=False, unknown=RAISE)

```python
result = schema.load({"name": "Alice", "age": "30"})
result = schema.load([{"name": "Alice"}, {"name": "Bob"}], many=True)
```

Pipeline:
1. Run `@pre_load` processors (pass_collection first, then per-item)
2. Deserialize each field
3. Run `@validates` field validators
4. Run `@validates_schema` schema validators
5. Run `@post_load` processors (per-item, then pass_collection)

---

## 6. Field Types

### DateTime

```python
from marshmallow import fields
import datetime as dt

class EventSchema(Schema):
    created_at = fields.DateTime()                    # ISO8601 string (default)
    updated_at = fields.DateTime(format="rfc")        # RFC822 string
    ts = fields.DateTime(format="timestamp")          # POSIX timestamp float
    ts_ms = fields.DateTime(format="timestamp_ms")    # POSIX timestamp in milliseconds
```

**Supported formats**: `"iso"`, `"iso8601"`, `"rfc"`, `"rfc822"`, `"timestamp"`, `"timestamp_ms"`, or any `strftime`-compatible format string.

**timestamp format**: Serializes to a float representing seconds since Unix epoch
(1970-01-01T00:00:00 UTC). Valid values include 0.0 (the epoch itself) and any
non-negative float.

Naive datetimes are treated as UTC when serializing to timestamp format.

### UUID

```python
from marshmallow import fields
import uuid

class ResourceSchema(Schema):
    id = fields.UUID()
```

**Accepted input types for deserialization**:
- `uuid.UUID` objects: returned as-is
- `bytes` of exactly **16 bytes**: interpreted as UUID binary representation
  (equivalent to `uuid.UUID(bytes=value)`)
- Any string that `uuid.UUID(string)` accepts: hex strings with or without hyphens

**Serialization**: Always serializes to a hyphenated UUID string (e.g., `"550e8400-e29b-41d4-a716-446655440000"`).

**Example**:
```python
schema = ResourceSchema()
result = schema.load({"id": b"\x55\x0e\x84\x00\xe2\x9b\x41\xd4\xa7\x16\x44\x66\x55\x44\x00\x00"})
# result["id"] == uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
```

### Boolean

```python
from marshmallow import fields

class FlagSchema(Schema):
    active = fields.Boolean()
    custom = fields.Boolean(truthy={"yes"}, falsy={"no"})
```

**Default truthy values**: `"t"`, `"T"`, `"true"`, `"True"`, `"TRUE"`, `"on"`, `"On"`, `"ON"`,
`"y"`, `"Y"`, `"yes"`, `"Yes"`, `"YES"`, `"1"`, `1`

**Default falsy values**: `"f"`, `"F"`, `"false"`, `"False"`, `"FALSE"`, `"off"`, `"Off"`,
`"OFF"`, `"n"`, `"N"`, `"no"`, `"No"`, `"NO"`, `"0"`, `0`

**Custom truthy/falsy**: If you pass `truthy=set()` (empty set), any non-falsy Python
value will be converted using `bool(value)`.

### List

```python
from marshmallow import fields

class DataSchema(Schema):
    tags = fields.List(fields.String())
    scores = fields.List(fields.Integer())
```

Deserializes a list of values using the inner field for each element. Returns a list
of deserialized values. Raises `ValidationError` if the input is not a collection (but
rejects strings even though strings are iterable).

### Mapping / Dict

```python
from marshmallow import fields

class ConfigSchema(Schema):
    settings = fields.Dict(keys=fields.String(), values=fields.Integer())
    metadata = fields.Dict()  # no type enforcement
```

**Dict** is a subclass of **Mapping** with `mapping_type = dict`. Deserializes a dict
with optional key and value field validation.

### TimeDelta

```python
from marshmallow import fields
import datetime as dt

class DurationSchema(Schema):
    duration = fields.TimeDelta()                           # precision="seconds" (default)
    duration_ms = fields.TimeDelta(precision="milliseconds")
    duration_us = fields.TimeDelta(precision="microseconds")
```

**Supported precision values**: `"weeks"`, `"days"`, `"hours"`, `"minutes"`, `"seconds"`,
`"milliseconds"`, `"microseconds"`.

**Serialization**: Converts a `timedelta` to a `float` representing the number of
the specified units. For example:
- `timedelta(seconds=3, microseconds=500000)` with precision `"seconds"` → `3.5`
- `timedelta(seconds=3, microseconds=500000)` with precision `"microseconds"` → `3500000.0`

**Deserialization**: Converts a float back to a `timedelta` using the specified unit.

**Roundtrip**: `TimeDelta` guarantees that serializing and then deserializing a
`timedelta` returns the same value (within floating-point precision limits).

---

## 7. Missing Value Handling

The sentinel `marshmallow.missing` (from `marshmallow.constants`) is used to
represent a missing value that has not been provided. It is distinct from `None`.

```python
from marshmallow.constants import missing

field = fields.Integer(load_default=missing)
# field.load_default is marshmallow.missing → field is not required
```

Fields with `required=True` raise `ValidationError` if their key is absent from
the input. Fields without `required=True` return their `load_default` when absent.

---

## 8. Schema.from_dict()

A convenience method to create a Schema class from a dictionary of field definitions:

```python
from marshmallow import Schema, fields

PersonSchema = Schema.from_dict({
    "name": fields.String(required=True),
    "age": fields.Integer(),
    "created_at": fields.DateTime(format="timestamp"),
})

schema = PersonSchema()
result = schema.load({"name": "Alice", "age": 30, "created_at": 0.0})
```
