# jsonschema 4.23.0 — String/Number/Dependency Validator Reference

This document describes the behavior of key JSON Schema keywords related to
strings, numbers, and object dependencies as implemented in the `jsonschema`
library (version 4.23.0). Use this to design property-based tests that validate
schema conformance.

---

## Overview

jsonschema validates Python objects against JSON Schema documents. The primary
entry points for modern drafts and legacy drafts are:

```python
from jsonschema import Draft7Validator, Draft4Validator, Draft202012Validator

schema = {"type": "string", "minLength": 3}

# Check validity
is_ok = Draft7Validator(schema).is_valid("hello")   # True
errors = list(Draft7Validator(schema).iter_errors("hi"))  # [ValidationError]

# Raise on first error
Draft7Validator(schema).validate("hello")   # passes silently
Draft7Validator(schema).validate("hi")      # raises ValidationError
```

---

## String Keywords: `minLength` and `maxLength`

### Semantics

- **`minLength`**: The string must have at least `minLength` **Unicode code points**.
  An empty string has length 0. Length is always measured in Unicode code points,
  not bytes. This is critical for multi-byte characters.
- **`maxLength`**: The string must have at most `maxLength` **Unicode code points**.

### Unicode Code Point Counting

The JSON Schema specification requires that `minLength` and `maxLength` count
**Unicode code points**, not bytes, not UTF-16 code units, not grapheme clusters.

```python
# ASCII: 1 byte per character = 1 code point
assert len("hello") == 5          # 5 code points

# CJK characters (U+4E00–U+9FFF): 3 bytes in UTF-8, 1 code point each
s = "中文"  # 2 CJK characters
assert len(s) == 2                 # 2 code points (correct length)
assert len(s.encode("utf-8")) == 6 # 6 bytes (NOT the length for schema purposes)

# Emoji (U+1F600–U+1F64F): 4 bytes in UTF-8, 1 code point each
e = "😀😁"  # 2 emoji
assert len(e) == 2                 # 2 code points (correct)
assert len(e.encode("utf-8")) == 8 # 8 bytes (NOT the length for schema purposes)
```

### Key Invariants

1. `{"minLength": N}` validates string `s` iff `len(s) >= N` (in code points).
2. `{"maxLength": N}` validates string `s` iff `len(s) <= N` (in code points).
3. Non-string values are always valid (keywords only apply to strings).
4. `{"minLength": 0}` always validates any string.

### Examples

```python
from jsonschema import Draft7Validator

# ASCII
Draft7Validator({"minLength": 3}).is_valid("abc")    # True (3 >= 3)
Draft7Validator({"minLength": 3}).is_valid("ab")     # False (2 < 3)
Draft7Validator({"maxLength": 5}).is_valid("hello")  # True (5 <= 5)
Draft7Validator({"maxLength": 5}).is_valid("toolong") # False (7 > 5)

# CJK (3 bytes per char in UTF-8, but counted as 1 code point)
Draft7Validator({"minLength": 2}).is_valid("中文")   # True (len=2 >= 2)
Draft7Validator({"minLength": 3}).is_valid("中文")   # False (len=2 < 3)

# Emoji (4 bytes per char, counted as 1 code point)
Draft7Validator({"maxLength": 2}).is_valid("😀😁")  # True (len=2 <= 2)
Draft7Validator({"maxLength": 1}).is_valid("😀😁")  # False (len=2 > 1)
```

### Property-Based Testing Hints

- Use `st.text(alphabet=st.characters(min_codepoint=0x4E00, max_codepoint=0x9FFF))`
  to generate CJK strings where each character encodes to 3 bytes.
- Use `st.text(alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F))`
  to generate emoji strings where each character encodes to 4 bytes.
- The key property: `Draft7Validator({"minLength": len(s)}).is_valid(s)` must always hold.
- Also: for any string `s` and integer `n <= len(s)`, schema `{"minLength": n}` must be valid.

---

## String Keywords: `pattern`

### Semantics

- **`pattern`**: The string must match the regular expression using `re.search`.
  This means the pattern can match **anywhere** in the string (not anchored).
  The pattern language is ECMA 262 regular expressions; Python's `re` module
  is used as an approximation.

### Key Invariants

1. `{"pattern": P}` validates string `s` iff `re.search(P, s)` is truthy.
2. Use `^` and `$` anchors to require full-string matching.
3. Non-string values are always valid.

### Examples

```python
Draft7Validator({"pattern": "abc"}).is_valid("xabcyz")  # True (substring match)
Draft7Validator({"pattern": "^abc$"}).is_valid("abc")   # True (full match)
Draft7Validator({"pattern": "^abc$"}).is_valid("xabc")  # False (not at start)
```

---

## Number Keywords: `multipleOf`

### Semantics

- **`multipleOf`**: The number must be divisible by `multipleOf`. A number `n` is
  a multiple of `d` if there exists an integer `k` such that `n = k * d`.

### Floating-Point Considerations

For integer `multipleOf` values, standard integer division suffices. For float
`multipleOf` values, exact floating-point representation issues mean that simple
modulo (`n % d == 0`) may produce spurious non-zero remainders for mathematically
exact multiples.

The correct implementation uses a **quotient-based** approach:

```python
quotient = n / d
is_multiple = int(quotient) == quotient  # exact integer check
```

This avoids the floating-point precision issue inherent in the modulo approach.

### Key Invariants

1. `{"multipleOf": d}` validates number `n` iff `n / d` is an integer.
2. 0 is always a valid multiple of any positive `d`.
3. For integer `d`: `n % d == 0` is equivalent and exact.
4. For float `d`: the quotient method is more reliable than modulo.
5. Non-number values are always valid.

### Examples

```python
from jsonschema import Draft7Validator

# Integer multipleOf
Draft7Validator({"multipleOf": 3}).is_valid(9)   # True (9/3=3, integer)
Draft7Validator({"multipleOf": 3}).is_valid(7)   # False (7/3≈2.33, not integer)
Draft7Validator({"multipleOf": 3}).is_valid(0)   # True (0/3=0, integer)

# Float multipleOf
Draft7Validator({"multipleOf": 0.1}).is_valid(0.3)  # True (0.3/0.1=3, integer)
Draft7Validator({"multipleOf": 0.1}).is_valid(1.0)  # True (1.0/0.1=10, integer)
Draft7Validator({"multipleOf": 0.1}).is_valid(0.15) # False (0.15/0.1=1.5, not integer)
Draft7Validator({"multipleOf": 0.25}).is_valid(1.75) # True (1.75/0.25=7, integer)
```

### Property-Based Testing Hints

- Generate exact multiples: `n = st.integers(1, 50); x = float(n) * mult`.
- Property: `Draft7Validator({"multipleOf": mult}).is_valid(float(n) * mult)` must hold.
- Edge case: 0 is always valid under any multipleOf.
- Non-multiples (e.g., 0.15 under 0.1) should be invalid.

---

## Number Keywords: `exclusiveMinimum` and `exclusiveMaximum`

### Draft 4 vs Draft 6+ Semantics

The `exclusiveMinimum` and `exclusiveMaximum` keywords changed semantics between
JSON Schema drafts.

#### Draft 4 (used by `Draft4Validator`)

In Draft 4, `exclusiveMinimum` and `exclusiveMaximum` are **booleans** that
modify the behavior of `minimum` and `maximum`:

- `{"minimum": n, "exclusiveMinimum": false}`: `instance >= n` (inclusive, default)
- `{"minimum": n, "exclusiveMinimum": true}`: `instance > n` (exclusive)
- `{"maximum": n, "exclusiveMaximum": false}`: `instance <= n` (inclusive, default)
- `{"maximum": n, "exclusiveMaximum": true}`: `instance < n` (exclusive)

When `exclusiveMinimum` is absent from the schema, `minimum` is **inclusive by default**.

```python
from jsonschema import Draft4Validator

# Default: inclusive minimum
Draft4Validator({"minimum": 5}).is_valid(5)   # True (5 >= 5, inclusive)
Draft4Validator({"minimum": 5}).is_valid(4)   # False (4 < 5)

# Explicit inclusive (same as default)
Draft4Validator({"minimum": 5, "exclusiveMinimum": False}).is_valid(5)  # True

# Exclusive minimum
Draft4Validator({"minimum": 5, "exclusiveMinimum": True}).is_valid(5)   # False (not > 5)
Draft4Validator({"minimum": 5, "exclusiveMinimum": True}).is_valid(6)   # True (6 > 5)
```

#### Draft 6+ (used by `Draft7Validator`, `Draft202012Validator`)

In Draft 6 and later, `exclusiveMinimum` and `exclusiveMaximum` are **standalone
number keywords** (not booleans):

- `{"exclusiveMinimum": n}`: `instance > n` (strictly greater than n)
- `{"exclusiveMaximum": n}`: `instance < n` (strictly less than n)

```python
from jsonschema import Draft7Validator

Draft7Validator({"exclusiveMinimum": 5}).is_valid(5)  # False (5 is NOT > 5)
Draft7Validator({"exclusiveMinimum": 5}).is_valid(6)  # True (6 > 5)
Draft7Validator({"exclusiveMaximum": 10}).is_valid(10) # False (10 is NOT < 10)
Draft7Validator({"exclusiveMaximum": 10}).is_valid(9)  # True (9 < 10)
```

### Property-Based Testing Hints

- Draft 4 key property: `Draft4Validator({"minimum": n}).is_valid(n)` must be True
  (inclusive by default, no `exclusiveMinimum` specified).
- Draft 7 key property: `Draft7Validator({"exclusiveMinimum": n}).is_valid(n)` must
  be False (n is NOT strictly greater than n).

---

## Object Keywords: `dependencies` (Draft 4 / Draft 7)

### Overview

The `dependencies` keyword (available in JSON Schema Draft 4 and Draft 7, but
superseded in Draft 2019-09+) allows specifying **property dependencies**: when
one property is present in the object, other properties become required or
additional schema constraints apply.

**Note**: In Draft 2019-09 and later, `dependencies` was split into
`dependentRequired` (for property dependencies) and `dependentSchemas`
(for schema dependencies).

### Two Dependency Modes

The `dependencies` keyword supports two distinct modes depending on the value type:

#### Mode 1: Property Dependencies (Array Value)

When the dependency value is a **list of strings**, the listed properties are
required whenever the trigger property is present.

```python
schema = {
    "dependencies": {
        "credit_card": ["billing_address"]
    }
}
```

- If `"credit_card"` is **present** in the instance → `"billing_address"` must also be present.
- If `"credit_card"` is **absent** → no constraint on `"billing_address"`.

#### Mode 2: Schema Dependencies (Object Value)

When the dependency value is a **JSON Schema object**, the schema is applied to
the entire instance whenever the trigger property is present.

```python
schema = {
    "dependencies": {
        "billing_address": {
            "properties": {
                "billing_zip": {"type": "string"}
            },
            "required": ["billing_zip"]
        }
    }
}
```

- If `"billing_address"` is **present** → the instance must satisfy the schema
  (i.e., `"billing_zip"` must be a string and must be present).
- If `"billing_address"` is **absent** → the schema is not applied.

### Key Invariants

1. **Trigger absent → always valid** (no constraints apply regardless of mode).
2. **Trigger present + array dep mode**: each listed property must be present.
3. **Trigger present + schema dep mode**: the entire schema must validate against the instance.
4. Multiple dependency entries can co-exist in one `dependencies` object.

### Examples

```python
from jsonschema import Draft7Validator

# ── Array (property) dependency ──────────────────────────────────────────────
schema1 = {"dependencies": {"a": ["b", "c"]}}

Draft7Validator(schema1).is_valid({"a": 1, "b": 2, "c": 3})  # True (all present)
Draft7Validator(schema1).is_valid({"a": 1, "b": 2})          # False (c missing)
Draft7Validator(schema1).is_valid({"a": 1})                  # False (b, c missing)
Draft7Validator(schema1).is_valid({"b": 2, "c": 3})          # True (trigger absent)
Draft7Validator(schema1).is_valid({})                         # True (trigger absent)

# ── Schema dependency ─────────────────────────────────────────────────────────
schema2 = {
    "dependencies": {
        "name": {
            "required": ["email"],
            "properties": {"email": {"type": "string"}}
        }
    }
}

Draft7Validator(schema2).is_valid({"name": "Alice", "email": "a@b.com"})  # True
Draft7Validator(schema2).is_valid({"name": "Alice"})                      # False (email missing)
Draft7Validator(schema2).is_valid({"name": "Alice", "email": 42})         # False (email wrong type)
Draft7Validator(schema2).is_valid({"email": "x@y.com"})                   # True (name absent)
Draft7Validator(schema2).is_valid({})                                      # True (name absent)

# ── Mixed dependencies ────────────────────────────────────────────────────────
schema3 = {
    "dependencies": {
        "credit_card": ["billing_address"],      # array dep
        "billing_address": {                     # schema dep
            "properties": {"billing_zip": {"type": "string"}},
            "required": ["billing_zip"]
        }
    }
}

# Both triggers present + all constraints satisfied
Draft7Validator(schema3).is_valid({
    "credit_card": "1234",
    "billing_address": "123 Main St",
    "billing_zip": "12345"
})  # True

# credit_card present but billing_address absent
Draft7Validator(schema3).is_valid({"credit_card": "1234"})  # False
```

### Property-Based Testing Hints

- Key property for array deps: if trigger `T` is in instance and dep `D` is NOT
  in instance, the instance must be invalid.
  ```python
  schema = {"dependencies": {T: [D]}}
  instance = {T: some_value}  # D not in instance
  assert not Draft7Validator(schema).is_valid(instance)
  ```
- Key property for schema deps: if trigger `T` is in instance and the schema
  constraint is violated (e.g., required field `R` is missing), must be invalid.
  ```python
  schema = {"dependencies": {T: {"required": [R]}}}
  instance = {T: some_value}  # R not present
  assert not Draft7Validator(schema).is_valid(instance)
  ```
- Absence property: instance without trigger must always be valid.
  ```python
  schema = {"dependencies": {T: [D]}}
  instance = {}  # no T
  assert Draft7Validator(schema).is_valid(instance)
  ```

---

## Call Chain Reference

Understanding the internal dispatch helps locate potential bug sites:

```
Draft7Validator.validate(instance)
  → iter_errors(instance, schema)
    → VALIDATORS.get(keyword)  # looks up keyword function in registry
      → dependencies_draft4_draft6_draft7(validator, dependencies, instance, schema)
        # For each property with a dependency:
        #   if property in instance:  (trigger guard)
        #     if dependency is array: check each required property
        #     else: descend with schema
      → multipleOf(validator, dB, instance, schema)
        # if float dB: use quotient method (int(instance/dB) == instance/dB)
        # else: use integer modulo
      → minLength(validator, mL, instance, schema)
        # uses len(instance) for Unicode codepoints
      → minimum_draft3_draft4(validator, minimum, instance, schema)  [Draft4 only]
        # reads schema.get("exclusiveMinimum", False) to determine mode
```

---

## Format Keyword

The `format` keyword is informational by default (does not raise errors) unless
a `format_checker` is provided to the validator. To enable format validation:

```python
import jsonschema

format_checker = jsonschema.FormatChecker()
v = Draft7Validator({"format": "email"}, format_checker=format_checker)
```

Common format values: `"date"`, `"time"`, `"date-time"`, `"email"`, `"uri"`,
`"ipv4"`, `"ipv6"`, `"hostname"`, `"uuid"`.
