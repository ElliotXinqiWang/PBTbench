# Strategy Spec for MRSH-001

## Bug 1: pre_load processor ordering (L4)

**Trigger condition**: Schema with `many=True` loading AND both:
- At least one `@pre_load(pass_collection=True)` hook
- At least one `@pre_load` (per-item) hook

The collection-level hook must compute something based on the ORIGINAL values,
while the per-item hook must modify those values. The test verifies that the
collection-level computation uses original values (not already-processed values).

**Why default strategy doesn't trigger**: Baseline tests typically use schemas
without multiple pre_load hooks of different types, and even less so with `many=True`.
The bug only manifests when both `pass_collection=True` and per-item hooks are present
and the per-item transformation affects the values that the collection hook reads.

**Trigger probability with default strategy**: ~1% (baseline rarely constructs
schemas with multiple typed pre_load decorators + many=True)

**Minimum triggering example**:
```python
class S(ma.Schema):
    v = ma.fields.Integer()
    s = ma.fields.Integer()

    @ma.pre_load(pass_collection=True)
    def sum_pass(self, data, many, **kwargs):
        if many:
            t = sum(i["v"] for i in data)
            return [dict(i, s=t) for i in data]
        return data

    @ma.pre_load
    def double(self, data, many, **kwargs):
        return dict(data, v=data["v"] * 2)

result = S().load([{"v": 1}, {"v": 2}], many=True)
# Correct: result[0]["s"] == 3 (original sum)
# Buggy:   result[0]["s"] == 6 (doubled sum)
```

---

## Bug 2: Nested `only` uses union instead of intersection (L3)

**Trigger condition**: A `fields.Nested` field where:
1. The nested field's `nested` argument is a Schema **instance** (not class)
2. The Schema instance was created with `only=(...)` restriction
3. The `Nested` field also has its own `only=(...)` parameter

Both `only` sets must be non-empty and have at least one field that differs
between the two sets.

**Why default strategy doesn't trigger**: Most PBT strategies use Schema classes
(not instances) with Nested, or don't set `only` on both the instance and the field.
Requires composing Schema(only=A) with fields.Nested(..., only=B).

**Trigger probability with default strategy**: ~3%

**Minimum triggering example**:
```python
class Inner(ma.Schema):
    a = ma.fields.String()
    b = ma.fields.String()

inner_restricted = Inner(only=("a", "b"))

class Outer(ma.Schema):
    inner = ma.fields.Nested(inner_restricted, only=("b",))
    # Correct: effective only = {"a","b"} ∩ {"b"} = {"b"}
    # Buggy:   effective only = {"a","b"} ∪ {"b"} = {"a","b"}

result = Outer().dump({"inner": {"a": "X", "b": "Y"}})
# Correct: {"inner": {"b": "Y"}}
# Buggy:   {"inner": {"a": "X", "b": "Y"}}
```

---

## Bug 3: field `attribute` mapping ignored in _deserialize (L3)

**Trigger condition**: Schema field with `attribute="something"` where
`attribute != field_name`. Loading any valid value will trigger the bug
because the result key is wrong.

**Why default strategy doesn't trigger**: Most baseline tests use fields
without the `attribute` parameter. Only fields where `attribute != field_name`
trigger the bug.

**Trigger probability with default strategy**: ~5% (baseline rarely uses
`attribute` parameter on fields)

**Minimum triggering example**:
```python
class S(ma.Schema):
    external = ma.fields.String(attribute="internal")

result = S().load({"external": "hello"})
# Correct: {"internal": "hello"}  (stored under attribute name)
# Buggy:   {"external": "hello"}  (stored under field name)
```

---

## Bug 4: Range validator min boundary off-by-one (L2)

**Trigger condition**: Using `validate.Range(min=N)` (with default `min_inclusive=True`)
and loading a value exactly equal to `N`. Values strictly greater than `N` are
unaffected by the bug.

**Why default strategy doesn't trigger**: Default Hypothesis integer/float strategies
rarely land exactly on the minimum boundary value when testing random data.

**Trigger probability with default strategy**: ~1/range_size (very low for large ranges;
higher for small ranges)

**Minimum triggering example**:
```python
validator = ma.validate.Range(min=5)
validator(5)   # Correct: passes (5 >= 5)
               # Buggy:   raises ValidationError ("5 must be >= 5" paradox)

validator(6)   # Both correct and buggy: passes (6 > 5 regardless)
```

**Strategy**: Use `st.integers()` or `st.floats()` and test loading value=min_value.
The simplest targeted strategy:
```python
@given(min_val=st.integers(-100, 100))
def test_range_min_boundary(min_val):
    schema = SomeSchema()  # with Range(min=min_val) on a field
    schema.load({"value": min_val})  # should not raise
```
