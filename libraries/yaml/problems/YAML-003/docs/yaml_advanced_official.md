# PyYAML Documentation — Advanced Scalar Parsing and Type Roundtrip

Source: https://pyyaml.org/wiki/PyYAMLDocumentation (PyYAML 6.x)
Additional references: https://yaml.org/type/int.html, https://yaml.org/type/float.html,
https://yaml.org/type/set.html, https://yaml.org/type/timestamp.html

---

## Overview

PyYAML is a full-featured YAML framework for Python supporting YAML 1.1. It provides
a safe API (`safe_dump` / `safe_load`) and a full API (`dump` / `load`).

The fundamental contract of `safe_dump` / `safe_load` is:

```python
yaml.safe_load(yaml.safe_dump(obj)) == obj
```

This must hold for all supported types: `int`, `float`, `str`, `bool`, `None`,
`list`, `dict`, `set`, `datetime.date`, `datetime.datetime`.

Additionally, PyYAML must correctly parse valid YAML 1.1 scalar literals when
passed directly to `yaml.safe_load()`.

---

## Integer Parsing (`!!int`)

### Decimal Integers

Plain decimal integers are represented and parsed straightforwardly:

```python
yaml.safe_load('42')    # -> 42
yaml.safe_load('-5')    # -> -5
yaml.safe_load('0')     # -> 0
```

### Non-Decimal Integer Formats (YAML 1.1)

YAML 1.1 supports several integer literal formats beyond decimal:

| Format | Example | Expected value |
|--------|---------|---------------|
| Binary  | `0b1010` | 10 |
| Octal   | `010`    | 8  |
| Hex     | `0xFF`   | 255 |
| Sexagesimal | `1:30` | 90 |

These formats are recognized by PyYAML's implicit resolver and passed to
`construct_yaml_int`.

### Sexagesimal (Base-60) Integers

YAML 1.1 specifies a sexagesimal integer format using colon notation, derived
from the Babylonian base-60 number system (as used in time: hours:minutes:seconds).

**Format**: `[sign][group]:[group]:[group]...` where each group after the first
is a two-digit number 00–59.

**Parsing rule**: Each group represents a coefficient for the corresponding power
of 60. Groups are listed from most-significant to least-significant:

```
H:MM       = H * 60  + MM
H:MM:SS    = H * 3600 + MM * 60 + SS
H:MM:SS:SS = H * 216000 + MM * 3600 + SS * 60 + SS
```

**Examples**:

| YAML literal | Calculation | Python value |
|---|---|---|
| `1:30` | 1 × 60 + 30 | 90 |
| `2:00` | 2 × 60 + 0  | 120 |
| `0:45` | 0 × 60 + 45 | 45 |
| `1:00:00` | 1 × 3600 + 0 × 60 + 0 | 3600 |
| `1:02:03` | 1 × 3600 + 2 × 60 + 3 | 3723 |
| `0:01:00` | 0 × 3600 + 1 × 60 + 0 | 60 |

The regex that triggers sexagesimal parsing is:
`[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+`

Note: the first group must start with 1–9 (not 0). Each subsequent group is
00–59 (but the regex allows single digits for the leading group per colon).

**Invariant**: For any non-negative integers `H` and `MM` (0 ≤ MM ≤ 59):
```python
yaml.safe_load(f"{H}:{MM:02d}") == H * 60 + MM
```

---

## Float Parsing (`!!float`)

### Valid Float Representations

YAML 1.1 defines these float literal formats:

- **Decimal with fraction**: `3.14`, `-0.5`, `100.0`
- **Scientific notation**: `1.5e+10`, `-2.3e-4` (must include decimal in mantissa)
- **Infinity**: `.inf`, `+.inf`, `-.inf`
- **Not a Number**: `.nan`

### Implicit Resolver for Floats

PyYAML's resolver uses the first character of a scalar to quickly look up which
implicit resolvers to try. The float resolver is registered for the characters:

```
- + 0 1 2 3 4 5 6 7 8 9 .
```

This means:
- Scalars starting with `-` can be negative floats (or negative integers)
- Scalars starting with `+` can be positive floats (or positive integers)
- Scalars starting with `.` are `.inf`, `+.inf`, `-.inf`, `.nan`

**Parsing contract for negative floats**:

Any scalar matching the YAML 1.1 float pattern that starts with `-` must be
parsed as a Python `float`, not as a string:

```python
yaml.safe_load('-1.5')    # must return -1.5 (float)
yaml.safe_load('-0.5')    # must return -0.5 (float)
yaml.safe_load('-100.0')  # must return -100.0 (float)
yaml.safe_load('-.inf')   # must return float('-inf')
```

If the resolver does not check negative float literals, these scalars fall
through to the string constructor and return strings instead of floats.

### Float Roundtrip

For any finite Python float `f`:

```python
yaml.safe_load(str(f)) == f
```

This invariant holds for positive and negative floats alike.

---

## Set Representation (`!!set`)

### Python `set` to YAML

The `safe_dump` function serializes Python `set` objects using the YAML `!!set`
tag. A YAML set is a mapping where all values are `null`:

```yaml
!!set
element1: null
element2: null
element3: null
```

The `!!set` tag is essential. Without it, `safe_load` would interpret the mapping
as an ordinary Python `dict` (with `None` values), not a `set`.

### Set Roundtrip Contract

```python
s = {1, 2, 'hello', 42}
result = yaml.safe_load(yaml.safe_dump(s))
assert isinstance(result, set)
assert result == s
```

The loaded value must be a `set`, not a `dict`. If the `!!set` tag is missing
from the serialized output, `safe_load` returns `{1: None, 2: None, ...}`.

### Example

```python
import yaml

s = {'a', 'b', 'c'}
dumped = yaml.safe_dump(s)
# Expected output:
# !!set
# a: null
# b: null
# c: null

loaded = yaml.safe_load(dumped)
assert type(loaded) is set       # must be set, not dict
assert loaded == s               # elements must match
```

---

## Date and Datetime Representation (`!!timestamp`)

### Python Types Mapped to `!!timestamp`

PyYAML maps two Python types to YAML timestamps:

- `datetime.date` → ISO 8601 date: `YYYY-MM-DD`
- `datetime.datetime` → ISO 8601 datetime: `YYYY-MM-DD HH:MM:SS[.ffffff][+HH:MM]`

### Date Serialization Format

A `datetime.date` object is serialized as:

```yaml
2024-06-15
```

(The date-only form, without a time component.)

A `datetime.datetime` object is serialized as:

```yaml
2024-06-15 12:30:45
2024-06-15 12:30:45.123456
2024-06-15 12:30:45+05:30
```

### Date vs Datetime Disambiguation

The YAML timestamp constructor distinguishes date from datetime by the presence
of a time component:

- `2024-06-15` → `datetime.date(2024, 6, 15)`
- `2024-06-15 00:00:00` → `datetime.datetime(2024, 6, 15, 0, 0, 0)`

These are different Python objects even though they represent the same calendar day.

**Critical invariant**:

```python
import datetime
d = datetime.date(2024, 6, 15)
result = yaml.safe_load(yaml.safe_dump(d))
assert type(result) is datetime.date   # not datetime.datetime!
assert result == d
```

Note: `datetime.datetime` is a **subclass** of `datetime.date`, so
`isinstance(result, datetime.date)` is `True` for both — use `type(result) is datetime.date`
to check that the result is exactly a `date`, not a `datetime`.

### Datetime Roundtrip

For any `datetime.datetime` object `dt` (naive or timezone-aware):

```python
yaml.safe_load(yaml.safe_dump(dt)) == dt
```

This includes microseconds: if `dt.microsecond` is non-zero, the serialized form
includes the fractional-seconds part (up to 6 decimal places), and the loaded
value must have the same microsecond.

---

## SafeDumper Supported Types Summary

| Python type | YAML tag | Example output |
|---|---|---|
| `None` | `!!null` | `null` |
| `bool` | `!!bool` | `true`, `false` |
| `int` | `!!int` | `42`, `-5` |
| `float` | `!!float` | `3.14`, `-1.5`, `.inf`, `-.inf`, `.nan` |
| `str` | `!!str` | (plain or quoted) |
| `list` / `tuple` | `!!seq` | block or flow sequence |
| `dict` | `!!map` | block or flow mapping |
| `set` | `!!set` | mapping with null values, tagged `!!set` |
| `datetime.date` | `!!timestamp` | `2024-06-15` (date only) |
| `datetime.datetime` | `!!timestamp` | `2024-06-15 12:30:00[.ffffff][tz]` |

---

## YAML 1.1 Implicit Resolver Architecture

PyYAML's resolver uses a dispatch table (`yaml_implicit_resolvers`) keyed by the
first character of each scalar. When `safe_load` encounters a plain scalar, it:

1. Looks up the first character in the resolver table
2. Tries each registered `(tag, regexp)` pair for that character
3. If a regexp matches, uses the corresponding tag's constructor
4. If nothing matches, defaults to `!!str` (string)

The first-character optimization means that if a type's resolver is not registered
for a particular first character, scalars starting with that character will never
be parsed as that type — regardless of whether the full regex would match.

For example, the float resolver must be registered for `-` (as well as `+`,
digits, and `.`) to correctly parse negative float literals like `-1.5` and `-.inf`.

---

## Example: Safe Roundtrip

```python
import yaml
import datetime

# Integer roundtrip
assert yaml.safe_load(yaml.safe_dump(255)) == 255

# Negative float roundtrip
assert yaml.safe_load(yaml.safe_dump(-1.5)) == -1.5

# Set roundtrip
s = {1, 2, 'hello'}
assert yaml.safe_load(yaml.safe_dump(s)) == s
assert type(yaml.safe_load(yaml.safe_dump(s))) is set

# Date roundtrip
d = datetime.date(2024, 6, 15)
result = yaml.safe_load(yaml.safe_dump(d))
assert type(result) is datetime.date   # not datetime!
assert result == d

# Sexagesimal parsing
assert yaml.safe_load('1:30') == 90
assert yaml.safe_load('1:02:03') == 3723
```
