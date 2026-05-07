# marshmallow Validators API Reference

**Version**: marshmallow 4.2.2
**Module**: `marshmallow.validate`

## 1. Validator Protocol

Every built-in validator is a callable that accepts a value and either returns it unchanged (on success) or raises `marshmallow.exceptions.ValidationError` (on failure):

```python
def __call__(self, value: T) -> T:
    # Returns value unchanged if valid
    # Raises ValidationError if invalid
```

Validators are composable: they can be passed to field definitions via the `validate` parameter, used as standalone callables, or composed with `And`.

### ValidationError

```python
from marshmallow.exceptions import ValidationError
raise ValidationError("Error message")
raise ValidationError(["Error 1", "Error 2"])  # multiple messages
```

`ValidationError.messages` is either a `list[str]` or `dict`. When raised by `And`, it is always a `list` containing one message per failing validator.

---

## 2. Range Validator

```python
class Range(Validator):
    def __init__(
        self,
        min=None,
        max=None,
        *,
        min_inclusive: bool = True,
        max_inclusive: bool = True,
        error: str | None = None,
    )
```

Validates that a numeric value falls within a specified range.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `min` | numeric or None | `None` | Lower bound. If `None`, no lower bound is checked. |
| `max` | numeric or None | `None` | Upper bound. If `None`, no upper bound is checked. |
| `min_inclusive` | bool | `True` | Whether `min` is included in the valid range. |
| `max_inclusive` | bool | `True` | Whether `max` is included in the valid range. |
| `error` | str or None | `None` | Custom error message template. |

### Boundary Semantics

The `min_inclusive` and `max_inclusive` flags control whether the boundary values themselves are considered valid:

| `min_inclusive` | Condition to PASS | Equivalent comparison |
|---|---|---|
| `True` (default) | value >= min | `value >= self.min` — values **equal to** min pass |
| `False` | value > min | `value > self.min` — values **equal to** min fail |

| `max_inclusive` | Condition to PASS | Equivalent comparison |
|---|---|---|
| `True` (default) | value <= max | `value <= self.max` — values **equal to** max pass |
| `False` | value < max | `value < self.max` — values **equal to** max fail |

### Boundary Examples

```python
from marshmallow.validate import Range
from marshmallow.exceptions import ValidationError

# Inclusive bounds (default)
v = Range(min=0, max=10)
v(0)   # PASSES — exact min is valid (min_inclusive=True)
v(10)  # PASSES — exact max is valid (max_inclusive=True)
v(5)   # PASSES — within range
v(-1)  # RAISES ValidationError
v(11)  # RAISES ValidationError

# Exclusive lower bound
v = Range(min=0, min_inclusive=False)
v(0)   # RAISES — 0 is NOT in range [0, ∞) exclusive
v(1)   # PASSES
v(-1)  # RAISES

# Exclusive upper bound
v = Range(max=10, max_inclusive=False)
v(10)  # RAISES — 10 is NOT in range (-∞, 10) exclusive
v(9)   # PASSES
v(11)  # RAISES

# Mixed bounds: exclusive min, inclusive max
v = Range(min=0, max=10, min_inclusive=False, max_inclusive=True)
v(0)   # RAISES
v(1)   # PASSES
v(10)  # PASSES
v(11)  # RAISES
```

### Property Invariants for Range

- **P1**: `Range(min=x)(x)` must PASS when `min_inclusive=True` (inclusive lower bound)
- **P2**: `Range(min=x, min_inclusive=False)(x)` must FAIL (exclusive lower bound excludes boundary)
- **P3**: `Range(max=x)(x)` must PASS when `max_inclusive=True` (inclusive upper bound)
- **P4**: `Range(max=x, max_inclusive=False)(x)` must FAIL (exclusive upper bound excludes boundary)
- **P5**: For any `x > min`, `Range(min=min)(x)` must PASS (values strictly above min always pass)
- **P6**: For any `x < max`, `Range(max=max)(x)` must PASS (values strictly below max always pass)

### Error Messages

The error message indicates whether the bound is inclusive or exclusive:
- Inclusive min: `"Must be greater than or equal to {min}."`
- Exclusive min: `"Must be greater than {min}."`
- Inclusive max: `"Must be less than or equal to {max}."`
- Exclusive max: `"Must be less than {max}."`
- Both bounds: `"Must be {min_op} {min} and {max_op} {max}."`

---

## 3. Length Validator

```python
class Length(Validator):
    def __init__(
        self,
        min: int | None = None,
        max: int | None = None,
        *,
        equal: int | None = None,
        error: str | None = None,
    )
```

Validates that a value's length (as returned by `len()`) falls within a specified range. Works for strings, lists, tuples, dicts, and any `Sized` type.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `min` | int or None | `None` | Minimum length (inclusive). |
| `max` | int or None | `None` | Maximum length (inclusive). |
| `equal` | int or None | `None` | Exact required length. Mutually exclusive with `min`/`max`. |
| `error` | str or None | `None` | Custom error message template. |

**Constraint**: `equal` cannot be combined with `min` or `max`. Providing both raises `ValueError`.

### Semantics

**When `equal` is set**:
- Precisely: `len(value) == equal` must be true.
- Both shorter and longer values are invalid.
- If `len(value) < equal` → `ValidationError`
- If `len(value) > equal` → `ValidationError`
- If `len(value) == equal` → valid, returns value unchanged

**When `min` and/or `max` are set** (and `equal` is None):
- `min` is inclusive: `len(value) >= min` must hold
- `max` is inclusive: `len(value) <= max` must hold
- Values of exactly `min` length are valid
- Values of exactly `max` length are valid

### Length Examples

```python
from marshmallow.validate import Length
from marshmallow.exceptions import ValidationError

# Exact length requirement
v = Length(equal=5)
v("hello")   # PASSES — len("hello") == 5
v("hi")      # RAISES — len("hi") == 2, not 5
v("world!")  # RAISES — len("world!") == 6, not 5
v("")        # RAISES — len("") == 0, not 5
v([1,2,3,4,5])  # PASSES — len([1,2,3,4,5]) == 5

# Minimum length (inclusive)
v = Length(min=3)
v("abc")    # PASSES — len == 3 == min (inclusive boundary)
v("abcd")   # PASSES — len == 4 > min
v("ab")     # RAISES — len == 2 < min
v("")       # RAISES — len == 0 < min

# Maximum length (inclusive)
v = Length(max=5)
v("hello")   # PASSES — len == 5 == max (inclusive boundary)
v("hi")      # PASSES — len == 2 < max
v("toolong")  # RAISES — len == 7 > max

# Combined min and max
v = Length(min=2, max=5)
v("ab")      # PASSES — len == 2 == min
v("hello")   # PASSES — len == 5 == max
v("a")       # RAISES — len == 1 < min
v("toolong")  # RAISES — len == 7 > max
```

### Property Invariants for Length

- **P7**: `Length(equal=n)(s)` passes if and only if `len(s) == n`
  - This means BOTH shorter AND longer values must fail
- **P8**: `Length(min=m)(s)` passes if and only if `len(s) >= m`
  - Exact minimum boundary (`len(s) == m`) must pass
- **P9**: `Length(max=m)(s)` passes if and only if `len(s) <= m`
  - Exact maximum boundary (`len(s) == m`) must pass

---

## 4. OneOf Validator

```python
class OneOf(Validator):
    def __init__(
        self,
        choices: Iterable,
        labels: Iterable[str] | None = None,
        *,
        error: str | None = None,
    )
```

Validates that a value is a member of the given `choices` collection.

### Semantics

- `value in choices` must be true
- Uses `__contains__` for membership check
- Raises `ValidationError` if value is not in choices
- Also raises `ValidationError` if a `TypeError` occurs during the check (e.g., unhashable type against a set-based collection)

```python
from marshmallow.validate import OneOf

v = OneOf(["a", "b", "c"])
v("a")   # PASSES
v("d")   # RAISES

v = OneOf(range(10))
v(5)    # PASSES
v(10)   # RAISES
```

### Property Invariants for OneOf

- **P10**: `OneOf(choices)(x)` passes if and only if `x in choices`
- **P11**: For any `x in choices`, `OneOf(choices)(x)` must return `x` unchanged

---

## 5. NoneOf Validator

```python
class NoneOf(Validator):
    def __init__(
        self,
        iterable: Iterable,
        *,
        error: str | None = None,
    )
```

Validates that a value is **not** a member of the given `iterable`. Opposite of `OneOf`.

### Semantics

- `value not in iterable` must be true
- Raises `ValidationError` if value is found in iterable
- Returns value unchanged if not found (passes)
- If a `TypeError` occurs during the membership check, validation passes (no error)

```python
from marshmallow.validate import NoneOf

v = NoneOf(["banned1", "banned2"])
v("allowed")   # PASSES
v("banned1")   # RAISES

v = NoneOf(range(10))
v(10)   # PASSES — 10 not in range(10)
v(5)    # RAISES — 5 in range(10)
```

### Property Invariants for NoneOf

- **P12**: `NoneOf(forbidden)(x)` passes if and only if `x not in forbidden`
- **P13**: `NoneOf(x_included_in)(x)` must raise (x is forbidden)

---

## 6. ContainsOnly Validator

```python
class ContainsOnly(OneOf):
    # inherits __init__ from OneOf
```

Validates that every element in a sequence is a member of `choices`. Inherits from `OneOf`.

### Semantics

- Iterates through all elements of the input sequence
- Each element must pass `element in self.choices`
- Empty sequences are always valid (no elements to check)
- Duplicate values in the input are permitted

```python
from marshmallow.validate import ContainsOnly

v = ContainsOnly([1, 2, 3])
v([1, 2])       # PASSES
v([1, 1, 2])    # PASSES — duplicates allowed
v([])           # PASSES — empty is valid
v([1, 4])       # RAISES — 4 not in choices
v([4, 5])       # RAISES
```

### Property Invariants for ContainsOnly

- **P14**: `ContainsOnly(choices)(seq)` passes if and only if all elements of `seq` are in `choices`
- **P15**: `ContainsOnly(choices)([])` always passes (empty sequence is valid)
- **P16**: `ContainsOnly(choices)(list(choices))` always passes (a sequence of all choices is valid)

---

## 7. ContainsNoneOf Validator

```python
class ContainsNoneOf(NoneOf):
    # inherits __init__ from NoneOf
```

Validates that no element in a sequence is a member of `iterable`. Opposite of `ContainsOnly`.

### Semantics

- Iterates through all elements of the input sequence
- Each element must fail `element in self.iterable` (i.e., must NOT be in iterable)
- Empty sequences are always valid

```python
from marshmallow.validate import ContainsNoneOf

v = ContainsNoneOf([1, 2, 3])
v([4, 5, 6])   # PASSES — no forbidden elements
v([])          # PASSES — empty is valid
v([1, 4, 5])   # RAISES — 1 is in the forbidden iterable
v([1, 2, 3])   # RAISES — all are forbidden
```

---

## 8. And Validator

```python
class And(Validator):
    def __init__(self, *validators: Validator)
```

Composes multiple validators, running ALL of them and combining their error messages into a single `ValidationError`.

### Critical Semantics

**`And` always runs ALL validators**, even after some have already failed. This ensures that the caller receives complete information about ALL validation failures at once.

```python
from marshmallow.validate import And, Range, ValidationError

def is_even(value):
    if value % 2 != 0:
        raise ValidationError("Not an even value.")

v = And(Range(min=0), is_even)

v(-1)   # RAISES ValidationError with BOTH messages:
        # ['Must be greater than or equal to 0.', 'Not an even value.']

v(-2)   # RAISES ValidationError with ONLY Range message:
        # ['Must be greater than or equal to 0.']
        # (is_even(-2) passes since -2 is even)

v(1)    # RAISES ValidationError with ONLY is_even message:
        # ['Not an even value.']

v(2)    # PASSES — both validators pass
```

### Property Invariants for And

- **P17**: `And(v1, v2, ...)(x)` runs ALL validators, regardless of earlier failures
- **P18**: If `N` validators all fail for input `x`, then `And(*[v]*N)(x)` raises with `N` messages
- **P19**: The error messages list in `ValidationError.messages` contains one entry per failed validator
- **P20**: `And(v1, v2)(x)` passes if and only if both `v1(x)` and `v2(x)` pass independently

### Multi-validator Error Collection Example

```python
# THREE validators that all fail for -1
from marshmallow.validate import And, Range

v = And(Range(min=0), Range(min=1), Range(min=2))
try:
    v(-1)
except ValidationError as e:
    # e.messages has EXACTLY 3 entries, one from each Range
    assert len(e.messages) == 3
```

---

## 9. Predicate Validator

```python
class Predicate(Validator):
    def __init__(self, method: str, *, error: str | None = None, **kwargs)
```

Calls a named method on the value object. The validator passes if the method returns a truthy value.

### Semantics

- `method_name` is the name of a method to call on `value`
- Additional `**kwargs` are passed to the method
- If `getattr(value, method_name)(**kwargs)` returns truthy, validation passes
- If it returns falsy, `ValidationError` is raised

```python
from marshmallow.validate import Predicate

# Check that a string is uppercase
v = Predicate("isupper")
v("HELLO")   # PASSES — "HELLO".isupper() == True
v("hello")   # RAISES — "hello".isupper() == False

# Check that a string starts with a prefix
v = Predicate("startswith", prefix="http")
v("https://example.com")   # PASSES
v("ftp://example.com")     # RAISES
```

---

## 10. Using Validators with Schema Fields

All validators can be passed to field definitions:

```python
import marshmallow as ma
from marshmallow.validate import Range, Length, OneOf, And

class MySchema(ma.Schema):
    age = ma.fields.Integer(validate=Range(min=0, max=150))
    name = ma.fields.String(validate=Length(min=1, max=100))
    role = ma.fields.String(validate=OneOf(["admin", "user", "guest"]))
    score = ma.fields.Float(
        validate=And(Range(min=0.0, max=1.0), Range(min=0.0, max=1.0, max_inclusive=False))
    )
```

Multiple validators can be specified as a list:

```python
class AnotherSchema(ma.Schema):
    code = ma.fields.String(validate=[
        Length(min=3, max=10),
        Predicate("isupper"),
    ])
```

When multiple validators are listed, marshmallow runs them in order and collects all errors — similar to `And`.

---

## 11. Summary of Validator Properties

| Validator | Core Property | Boundary Behavior |
|---|---|---|
| `Range(min=M)` | `value >= M` must hold | Exact value `M` passes (inclusive by default) |
| `Range(min=M, min_inclusive=False)` | `value > M` must hold | Exact value `M` fails (exclusive) |
| `Range(max=M)` | `value <= M` must hold | Exact value `M` passes (inclusive by default) |
| `Range(max=M, max_inclusive=False)` | `value < M` must hold | Exact value `M` fails (exclusive) |
| `Length(equal=N)` | `len(value) == N` exactly | Both shorter AND longer values fail |
| `Length(min=M)` | `len(value) >= M` | Exact length `M` passes (inclusive) |
| `Length(max=M)` | `len(value) <= M` | Exact length `M` passes (inclusive) |
| `OneOf(choices)` | `value in choices` | Membership test |
| `NoneOf(iterable)` | `value not in iterable` | Inverse membership test |
| `ContainsOnly(choices)` | All elements in choices | Empty sequence always passes |
| `ContainsNoneOf(iterable)` | No elements in iterable | Empty sequence always passes |
| `And(*validators)` | All validators must pass | Collects ALL errors from ALL validators |
