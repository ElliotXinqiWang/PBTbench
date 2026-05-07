# marshmallow 4.2.2 — Schema API Reference

marshmallow is a Python serialization/deserialization library. A `Schema` maps Python objects to
primitive data types (serialization / dump) and back (deserialization / load).

---

## 1. Schema Class Overview

```python
from marshmallow import Schema, fields, RAISE, EXCLUDE, INCLUDE

class UserSchema(Schema):
    name   = fields.String(required=True)
    email  = fields.Email(required=True)
    age    = fields.Integer(load_default=0)
```

A Schema instance has two primary methods:

| Method | Description |
|--------|-------------|
| `schema.dump(obj)` | Serialize a Python object → dict |
| `schema.load(data)` | Deserialize a dict → Python object |
| `schema.dump(objs, many=True)` | Serialize a list of objects → list of dicts |
| `schema.load(items, many=True)` | Deserialize a list of dicts → list of objects |

---

## 2. Field Parameters: `attribute` and `data_key`

Every field accepts two key parameters that control name mapping:

### `attribute`

The `attribute` parameter specifies the name of the **Python object attribute or dict key**
to read from during serialization (`dump`), and the key to store the result under during
deserialization (`load`).

```python
class ArticleSchema(Schema):
    # Field named 'title' but reads from obj.headline / stores under 'headline'
    title = fields.String(attribute="headline")
```

Behavior:
- **Dump**: `field.serialize("title", obj)` reads `obj.headline` (not `obj.title`)
- **Load**: result dict has key `"headline"` (not `"title"`)

### `data_key`

The `data_key` parameter specifies the key used in the **external representation** (serialized dict).

```python
class UserSchema(Schema):
    # Schema field named 'email', but external key is 'email_address'
    email = fields.String(data_key="email_address")
```

Behavior:
- **Dump**: output dict key is `"email_address"` (not `"email"`)
- **Load**: looks for `"email_address"` in the input dict (not `"email"`)
- `partial` parameter uses the **field name** (schema attribute name), not `data_key`

### Combined Example

```python
class UserSchema(Schema):
    name = fields.String(attribute="username", data_key="user_name")
```

When dumping `{"username": "alice"}`:
- reads `obj.username` → "alice"  (because `attribute="username"`)
- stores as `{"user_name": "alice"}`  (because `data_key="user_name"`)

When loading `{"user_name": "alice"}`:
- reads from `data["user_name"]`  (because `data_key="user_name"`)
- stores result under `"username"`  (because `attribute="username"`)

---

## 3. Meta Options for Field Access Control

### `Meta.load_only`

Fields listed in `Meta.load_only` are excluded from dump output and accepted in load input.
This is equivalent to setting `load_only=True` on individual fields.

```python
class UserSchema(Schema):
    class Meta:
        load_only = ("password",)   # password not in dump output; accepted in load

    username = fields.String()
    password = fields.String()

s = UserSchema()
s.dump({"username": "alice", "password": "secret"})
# → {"username": "alice"}   (password excluded from dump)

s.load({"username": "alice", "password": "secret"})
# → {"username": "alice", "password": "secret"}  (password accepted in load)
```

**Invariant**: A field in `Meta.load_only` satisfies:
- `schema.dump(obj)` does NOT include the field
- `schema.load(data)` DOES include the field

### `Meta.dump_only`

Fields listed in `Meta.dump_only` are included in dump output but ignored during load.

```python
class ArticleSchema(Schema):
    class Meta:
        dump_only = ("created_at",)  # read-only field from server

    title = fields.String()
    created_at = fields.DateTime()
```

---

## 4. Partial Loading

The `partial` parameter controls which fields may be missing without raising errors.

### `partial=True`

All fields are treated as optional (missing is allowed):

```python
result = schema.load({"name": "Alice"}, partial=True)
# All required fields are optional
```

### `partial=['field_name', ...]` — List of Field Names

Only the specified fields (by their **schema attribute name**) are treated as optional.
Other required fields still raise `ValidationError` if missing.

```python
class PersonSchema(Schema):
    name  = fields.String(required=True)
    email = fields.String(required=True)
    age   = fields.Integer(required=True)

s = PersonSchema()
result = s.load({"name": "Alice"}, partial=["email", "age"])
# → {"name": "Alice"}   (email and age are optional; name is still required)
```

**Important**: the strings in `partial` always refer to the **schema field name** (attr_name),
not the external `data_key`. For example:

```python
class Schema(Schema):
    email = fields.String(required=True, data_key="email_address")
    name  = fields.String(required=True)

# To make 'email' optional, use the field name "email":
s.load({"name": "Alice"}, partial=["email"])
# → {"name": "Alice"}  (works: "email" is the field's schema attr_name)
```

### Nested Partial Loading

Partial can specify nested fields using dot notation, using the **field name** (not data_key):

```python
s.load(data, partial=["address.city"])  # only address.city is optional
```

---

## 5. Schema Validators: `@validates_schema`

The `@validates_schema` decorator registers a schema-level validator that runs after field-level
deserialization.

```python
from marshmallow import validates_schema, ValidationError

class OrderSchema(Schema):
    quantity = fields.Integer()
    price    = fields.Float()
    total    = fields.Float()

    @validates_schema
    def validate_total(self, data, **kwargs):
        if data["total"] != data["quantity"] * data["price"]:
            raise ValidationError("total must equal quantity * price")
```

### `pass_collection=True`

When `pass_collection=True`, the validator receives the **entire collection** (list) when
`many=True` is used. This enables cross-item validation:

```python
class BatchSchema(Schema):
    value = fields.Integer()

    @validates_schema(pass_collection=True)
    def validate_batch(self, data, **kwargs):
        # data is the full list when many=True
        assert isinstance(data, list)
        if sum(item["value"] for item in data) > 1000:
            raise ValidationError("batch total too high")

    @validates_schema(pass_collection=False)
    def validate_item(self, data, **kwargs):
        # data is a single dict when many=True (called once per item)
        assert isinstance(data, dict)
        if data["value"] < 0:
            raise ValidationError("value must be non-negative")
```

**Invariant when `many=True`**:
- `@validates_schema(pass_collection=True)`: called **once** with the full list
- `@validates_schema(pass_collection=False)` (default): called **once per item** with individual dict

This invariant is critical for aggregate validations that require seeing all items together.

### `pass_original=True`

When `pass_original=True`, the validator receives **two arguments**:
1. The **deserialized data** (after field-level type conversion and validation)
2. The **original raw input** (before any deserialization)

```python
class TypedSchema(Schema):
    count = fields.Integer()  # converts string "42" -> int 42

    @validates_schema(pass_original=True)
    def check_transformation(self, data, original_data, **kwargs):
        # data["count"] is int (deserialized)
        # original_data["count"] is whatever was passed (e.g., str "42")
        pass
```

**Documented signature**: `validator(deserialized_data, original_data, *, partial, many, unknown)`

Use cases:
- Verify that type conversion happened correctly
- Cross-validate deserialized values against original input
- Log transformation differences

### `skip_on_field_errors=True` (default)

By default, `@validates_schema` validators are skipped if any field-level validation errors
occurred. Set `skip_on_field_errors=False` to run the schema validator even when fields failed.

```python
@validates_schema(skip_on_field_errors=False)
def always_run(self, data, **kwargs):
    ...
```

---

## 6. `dump()` and `load()` Pipeline

### Serialization Pipeline (dump)

```
obj → [PRE_DUMP processors] → _serialize() → [POST_DUMP processors] → result
```

1. **PRE_DUMP processors**: `@pre_dump` hooks modify the input object before serialization
2. **`_serialize()`**: iterates over `dump_fields`, calls `field.serialize(attr_name, obj)`
   - Uses `field.data_key or attr_name` as the key in the output dict
   - Uses `field.attribute or attr_name` to read from the object
3. **POST_DUMP processors**: `@post_dump` hooks modify the serialized result

### Deserialization Pipeline (load)

```
data → [PRE_LOAD processors] → _deserialize() → [field validators] → [schema validators] → [POST_LOAD processors] → result
```

1. **PRE_LOAD processors**: `@pre_load` hooks modify input data before deserialization
2. **`_deserialize()`**: iterates over `load_fields`:
   - Reads from `data[field.data_key or attr_name]`
   - Stores result under `field.attribute or attr_name`
3. **Field validators** (`@validates`): per-field validators
4. **Schema validators** (`@validates_schema`): cross-field validators
   - `pass_collection=True` validators run first (on full collection)
   - `pass_collection=False` validators run second (per-item)
5. **POST_LOAD processors**: `@post_load` hooks transform the deserialized result

---

## 7. Unknown Fields

The `unknown` parameter controls behavior when the input contains keys not declared in the schema:

| Value | Behavior |
|-------|----------|
| `RAISE` (default) | Raise `ValidationError` for unknown fields |
| `EXCLUDE` | Silently ignore unknown fields |
| `INCLUDE` | Pass through unknown fields unchanged |

```python
from marshmallow import EXCLUDE, INCLUDE, RAISE

# Set for all loads on this schema
class UserSchema(Schema):
    class Meta:
        unknown = EXCLUDE

# Or per-call
result = schema.load(data, unknown=EXCLUDE)
```

---

## 8. Error Handling

When validation fails, `schema.load()` raises `ValidationError`. The `.messages` attribute
contains a dict of field name → list of error messages:

```python
try:
    result = schema.load({"age": "not_a_number"})
except ValidationError as exc:
    print(exc.messages)   # {"age": ["Not a valid integer."]}
    print(exc.valid_data) # partially valid deserialized data
```

The `valid_data` attribute holds the result of fields that DID deserialize successfully.

---

## 9. Schema Invariants

The following invariants should always hold for a correctly-functioning marshmallow Schema:

1. **Dump excludes load_only fields**: for any field `f` in `Meta.load_only`, `f` does NOT appear in `schema.dump(obj)`
2. **Load accepts load_only fields**: `schema.load(data)` succeeds when `data` contains a `Meta.load_only` field
3. **Pass-collection invariant**: when `many=True`, a `@validates_schema(pass_collection=True)` validator sees the full list (not individual items)
4. **Pass-original argument order**: `@validates_schema(pass_original=True)` receives `(deserialized, original)` — first arg is deserialized
5. **Partial list uses attr_name**: `partial=["field_name"]` uses the schema field name, not the `data_key`
6. **Roundtrip consistency**: for simple schemas, `schema.load(schema.dump(obj))` should equal `obj` (modulo load_only fields)
