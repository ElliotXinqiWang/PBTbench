# cbor2 Type Encoding and Decoding Reference

**Version**: 5.6.5
**Standard**: RFC 7049 / RFC 8949 (CBOR — Concise Binary Object Representation)

---

## Overview

cbor2 is a pure-Python CBOR codec. It supports encoding and decoding of a wide range of Python types, including integers, floats, strings, bytes, lists, dicts, sets, datetimes, and more. It also supports optional "canonical" encoding mode, which selects the smallest possible representation for each value.

---

## Core API

### `cbor2.dumps(obj, *, canonical=False, datetime_as_timestamp=False, timezone=None, ...)`

Serialize `obj` to CBOR bytes.

**Key parameters**:

- `canonical` (`bool`, default `False`): When `True`, uses canonical CBOR encoding. For floats, this selects the smallest IEEE 754 format that can represent the value exactly (float16 → float32 → float64). For maps and sets, this also sorts keys deterministically.
- `datetime_as_timestamp` (`bool`, default `False`): When `True`, encodes `datetime` objects as UNIX timestamps (CBOR tag 1, numeric value) instead of ISO 8601 strings (CBOR tag 0).
- `timezone` (`tzinfo | None`): Default timezone for naive `datetime` objects. If `None` and a naive datetime is encoded, a `CBOREncodeValueError` is raised.

### `cbor2.loads(data)`

Deserialize CBOR bytes to a Python object.

---

## Float Encoding

### CBOR Float Representation

CBOR (major type 7) supports three IEEE 754 float formats:

| CBOR subtype | Format | Size | Python struct format |
|---|---|---|---|
| 25 (0xF9) | Half-precision (float16) | 2 bytes | `">e"` |
| 26 (0xFA) | Single-precision (float32) | 4 bytes | `">f"` |
| 27 (0xFB) | Double-precision (float64) | 8 bytes | `">d"` |

### Non-canonical Mode (default)

All finite floats are encoded as float64 (9 bytes including the type byte). This guarantees lossless roundtrip for any Python `float`.

Special values:
- `float("nan")` → `0xf97e00` (float16 NaN, 3 bytes)
- `float("inf")` → `0xf97c00` (float16 +Inf, 3 bytes)
- `float("-inf")` → `0xf9fc00` (float16 -Inf, 3 bytes)

### Canonical Mode (`canonical=True`)

In canonical mode, cbor2 uses `encode_minimal_float`, which tries to encode the float in the smallest format that preserves its exact value:

1. Start with float64 as the default.
2. Try float32: if `struct.unpack(">f", struct.pack(">f", value))[0] == value`, use float32.
3. Try float16: if `struct.unpack(">e", struct.pack(">e", value))[0] == value`, use float16.
4. Stop (use the smallest format that preserves precision exactly).

**Key property**: Canonical encoding is lossless. A value encoded canonically must decode to exactly the same Python `float`. The canonical format may use fewer bytes than float64, but the roundtrip value must be identical.

### float16 (Half-Precision) Range

float16 uses 1 sign bit, 5 exponent bits, 10 mantissa bits:
- Finite range: approximately `±6.1e-5` to `±65504`
- Only 2048 distinct positive finite values are representable exactly
- Most Python floats (e.g., `0.1`, `1.1`, `3.14`) are NOT exactly representable in float16

### float32 (Single-Precision) Range

float32 uses 1 sign bit, 8 exponent bits, 23 mantissa bits:
- Finite range: approximately `±1.18e-38` to `±3.4e38`
- About 2^24 ≈ 16.7 million distinct positive values per exponent range
- Many "nice" Python floats (e.g., `0.5`, `1.0`, `1.25`) are exactly representable

---

## Datetime Encoding

### Standard Mode (ISO 8601 String, CBOR Tag 0)

By default, `datetime` objects are encoded as CBOR tag 0 with an ISO 8601 string value:

```
Tag 0 → "2023-06-15T12:30:45.123456-05:30"
```

**Timezone representation**: The UTC offset is encoded in the ISO 8601 format `±HH:MM`. For example:
- UTC → trailing `Z`
- UTC+05:30 → `+05:30`
- UTC-03:30 → `-03:30`

The offset string always uses `±HH:MM` format. Both the hours and minutes components carry the same sign.

**Decoding invariant**: The decoded `datetime` must represent the same instant in time as the original. Specifically:
```
decoded.utcoffset() == original.utcoffset()
```

### Timestamp Mode (`datetime_as_timestamp=True`, CBOR Tag 1)

When `datetime_as_timestamp=True`, datetimes are encoded as CBOR tag 1 with a numeric UNIX timestamp:
- No fractional seconds: tag 1 with integer value
- With fractional seconds: tag 1 with float value

Microseconds are preserved as a float fractional component.

### Roundtrip Invariant for Datetimes

For any timezone-aware `datetime` object `dt`:
```python
cbor2.loads(cbor2.dumps(dt)) == dt
```

This equality holds when both datetimes represent the same UTC instant. Since CBOR encodes the full UTC offset, the timezone information must be preserved exactly.

---

## bytes and bytearray Encoding

Both `bytes` and `bytearray` are encoded as CBOR major type 2 (byte string). The `bytearray` type is first converted to `bytes` before encoding.

**Decoding**: CBOR byte strings are always decoded as Python `bytes` objects.

```python
cbor2.loads(cbor2.dumps(b"hello")) == b"hello"        # True
cbor2.loads(cbor2.dumps(bytearray(b"hello"))) == b"hello"  # True (decoded as bytes)
```

**Roundtrip note**: `bytearray` values roundtrip to `bytes`, not `bytearray`. If you need to preserve the `bytearray` type, wrap the decoded value explicitly.

---

## CBORTag

`CBORTag` represents a CBOR semantic tag with a numeric tag number and an associated value:

```python
from cbor2 import CBORTag

tag = CBORTag(42, "some value")
encoded = cbor2.dumps(tag)
decoded = cbor2.loads(encoded)
assert isinstance(decoded, CBORTag)
assert decoded.tag == 42
assert decoded.value == "some value"
```

Standard tag numbers defined by IANA:
- 0: datetime string (ISO 8601)
- 1: epoch-based datetime (UNIX timestamp)
- 2: positive bignum
- 3: negative bignum
- 4: decimal fraction
- 5: bigfloat
- 30: rational number
- 37: UUID
- 258: set
- 260: IP address
- 261: IP network

---

## frozenset Encoding

`frozenset` values are encoded as CBOR tag 258 (set) with an array of elements. The encoding order of elements is not guaranteed to be stable in non-canonical mode.

In canonical mode (`canonical=True`), elements are sorted by their canonical byte encoding, ensuring deterministic output.

**Roundtrip**: `frozenset` encodes and decodes to `frozenset` when the decoded context requires an immutable type (e.g., as a dict key or array element in immutable mode). In most contexts, it decodes to a Python `set`.

---

## Error Handling

- `CBOREncodeValueError`: raised for values that cannot be encoded (e.g., naive datetime without default timezone)
- `CBORDecodeValueError`: raised for malformed CBOR input
- `CBORDecodeEOF`: raised when the input stream ends prematurely

---

## Timezone Handling Reference

Per RFC 8949 Section 3.4.1, a CBOR datetime string must be a valid RFC 3339 date-time. The UTC offset format is:

```
date-time = date "T" time-offset
time-offset = "Z" / ("+" / "-") hh ":" mm
```

Where:
- `"Z"` represents UTC (equivalent to `+00:00`)
- `hh` is the hours component (00–23)
- `mm` is the minutes component (00–59)
- The sign (`+` or `-`) applies to the **entire offset** (both hours and minutes)

**Important**: For a negative offset like `-05:30`, both the hours (-5) and minutes (-30) are negative. The total offset is `timedelta(hours=-5, minutes=-30)`, not `timedelta(hours=-5, minutes=30)`.

Examples of valid timezone offsets and their `timedelta` equivalents:
| ISO offset | Python timedelta |
|---|---|
| `+00:00` or `Z` | `timedelta(0)` |
| `+05:30` | `timedelta(hours=5, minutes=30)` |
| `-03:30` | `timedelta(hours=-3, minutes=-30)` |
| `-09:30` | `timedelta(hours=-9, minutes=-30)` |
| `+09:45` | `timedelta(hours=9, minutes=45)` |
