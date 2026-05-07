# msgpack-python Advanced API Reference

## Overview

msgpack is a fast, compact binary serialization format. This document covers the advanced
aspects of msgpack-python 1.1.0, including the Timestamp extension type, map encoding
boundaries, and unpacker configuration options.

## Installation

```
pip install msgpack==1.1.0
```

## Quick Reference

```python
import msgpack

# Basic pack/unpack
data = msgpack.packb(obj, use_bin_type=True)
obj = msgpack.unpackb(data, raw=False)

# Streaming
packer = msgpack.Packer(use_bin_type=True)
unpacker = msgpack.Unpacker(raw=False)
```

---

## Timestamp Extension Type

The Timestamp type represents a point in time as a combination of seconds and nanoseconds
since the Unix epoch (1970-01-01 00:00:00 UTC).

### Creating Timestamps

```python
from msgpack import Timestamp

# From seconds and nanoseconds
ts = Timestamp(seconds=1234567890, nanoseconds=123456789)

# From Unix time (float or int)
ts = Timestamp.from_unix(1234567890.123456789)

# From nanoseconds
ts = Timestamp.from_unix_nano(1234567890123456789)

# From datetime (must have tzinfo)
import datetime
dt = datetime.datetime(2021, 1, 1, tzinfo=datetime.timezone.utc)
ts = Timestamp.from_datetime(dt)
```

### Timestamp Fields

- `seconds` (int): Seconds since the Unix epoch. May be negative for times before epoch.
- `nanoseconds` (int): Sub-second nanoseconds, always in [0, 999_999_999].

**Invariant**: `nanoseconds` must be non-negative and strictly less than 10^9 (1 billion).
Negative timestamps (before epoch) use negative `seconds` with non-negative `nanoseconds`.

### Timestamp Wire Formats

The msgpack Timestamp extension type (code -1) uses three binary encodings:

| Format | Payload size | Conditions | Seconds range |
|--------|-------------|------------|---------------|
| Timestamp 32 | 4 bytes | nanoseconds == 0 AND seconds in [0, 2^32) | 0 to 4294967295 |
| Timestamp 64 | 8 bytes | seconds in [0, 2^34) AND (nanoseconds > 0 OR seconds >= 2^32) | 0 to 17179869183 |
| Timestamp 96 | 12 bytes | seconds < 0 OR seconds >= 2^34 | any int64 |

**Timestamp 64 bit layout** (8 bytes, big-endian uint64):
- Upper 30 bits: nanoseconds adjustment (0 to 999999999)
- Lower 34 bits: seconds (0 to 2^34-1 = 17179869183)

The encoding packs `data64 = (nanoseconds << 34) | seconds`. Decoding must reverse this:
- `seconds = data64 & 0x00000003FFFFFFFF` (34-bit mask for lower 34 bits)
- `nanoseconds = data64 >> 34` (upper 30 bits)

**Important**: The 34-bit mask `0x00000003FFFFFFFF` extracts bits 0–33. A 30-bit mask
`0x000000003FFFFFFF` would only extract bits 0–29 and incorrectly truncate seconds values
that use bits 30–33 (seconds >= 2^30 = 1073741824, i.e., dates after ~2004).

**Timestamp 96 bit layout** (12 bytes):
- Bytes 0–3: nanoseconds as signed 32-bit big-endian integer
- Bytes 4–11: seconds as signed 64-bit big-endian integer

### Roundtrip Requirement

Any Timestamp object packed and then unpacked must compare equal to the original:

```python
ts = Timestamp(seconds=1234567890, nanoseconds=500000000)
packed = msgpack.packb(ts)
unpacked = msgpack.unpackb(packed)
assert unpacked == ts  # must hold for ALL valid Timestamp values
```

---

## Map (Dict) Encoding

Python dicts are encoded as msgpack maps. The encoder selects from three map formats:

| Format  | Header    | Max pairs | When used |
|---------|-----------|-----------|-----------|
| fixmap  | 0x80+n    | 15 pairs  | 0 ≤ n ≤ 15 |
| map16   | 0xDE + 2 bytes | 65535 pairs | 16 ≤ n ≤ 65535 |
| map32   | 0xDF + 4 bytes | 4294967295 pairs | n > 65535 |

**Invariant**: The fixmap format supports exactly 0 to 15 key-value pairs. The header byte
for a fixmap with n pairs is `0x80 + n`. For n=15, this is `0x8F`. For n=16, the correct
format is map16 (header `0xDE 0x00 0x10`).

**Important**: The fixmap range is `0x80` to `0x8F` (n=0 to n=15). The next byte `0x90`
is the fixarray format for empty arrays — it does NOT encode a 16-pair map. Any encoder
that uses the fixmap format for n=16 would emit `0x90`, which the decoder would interpret
as an empty list, corrupting the data.

### Roundtrip for Variable-Size Dicts

```python
# All of these must roundtrip correctly:
for n in range(0, 20):
    d = {str(i): i for i in range(n)}
    packed = msgpack.packb(d, use_bin_type=True)
    assert msgpack.unpackb(packed, raw=False) == d
```

---

## strict_map_key Parameter

Controls which Python types are accepted as map keys during unpacking.

```python
msgpack.unpackb(data, strict_map_key=True)   # default: only str or bytes
msgpack.unpackb(data, strict_map_key=False)  # any hashable type
```

**Allowed key types when `strict_map_key=True`**:
- `str` — Unicode strings
- `bytes` — Binary strings

Any other type (e.g., `int`, `float`, `tuple`) raises `ValueError` when
`strict_map_key=True`.

**Important**: Both `str` AND `bytes` are allowed by default. This means a dict packed
with bytes keys must unpack successfully with the default `strict_map_key=True`:

```python
d = {b"key": "value"}
packed = msgpack.packb(d, use_bin_type=True)
# Must NOT raise ValueError:
unpacked = msgpack.unpackb(packed, raw=False, strict_map_key=True)
assert unpacked == d
```

### Keys with strict_map_key=False

When `strict_map_key=False`, any hashable Python type can be a key:

```python
d = {1: "a", 2.5: "b", (1, 2): "c"}
packed = msgpack.packb(d)
unpacked = msgpack.unpackb(packed, strict_map_key=False)
assert unpacked == d
```

---

## raw Parameter

Controls how msgpack "raw" (str-family) bytes are decoded.

```python
msgpack.unpackb(data, raw=False)  # default: decode raw bytes to str (UTF-8)
msgpack.unpackb(data, raw=True)   # keep raw bytes as bytes
```

**Behavior**:
- `raw=False` (default): msgpack raw type → Python `str` (decoded with UTF-8)
- `raw=True`: msgpack raw type → Python `bytes` (no decoding)

**Invariant**: With `raw=False`, the return type for a packed string is `str`. With
`raw=True`, the return type is `bytes`. These must be consistent:

```python
s = "hello"
packed = msgpack.packb(s, use_bin_type=True)

result_str = msgpack.unpackb(packed, raw=False)
assert isinstance(result_str, str)     # must be str
assert result_str == s

result_bytes = msgpack.unpackb(packed, raw=True)
assert isinstance(result_bytes, bytes)  # must be bytes
assert result_bytes == s.encode("utf-8")
```

**Note**: The `raw` parameter only affects the msgpack "raw" (str family) type.
The msgpack "bin" type (used for Python `bytes` with `use_bin_type=True`) is always
returned as Python `bytes`, regardless of the `raw` setting.

---

## Packer Configuration

```python
packer = msgpack.Packer(
    use_bin_type=True,    # True (default): bytes→bin type, str→raw type
    use_single_float=False,  # False (default): float64; True: float32
    strict_types=False,   # False (default): subclasses OK; True: exact types only
    datetime=False,       # False (default): datetime not packed; True: datetime→Timestamp
    default=None,         # callable for unsupported types
)
```

### use_bin_type Effect on Strings

When `use_bin_type=True` (default since msgpack-python 1.0):
- Python `str` → msgpack raw type (fixstr/str8/str16/str32)
- Python `bytes` → msgpack bin type (bin8/bin16/bin32)

When `use_bin_type=False` (legacy mode):
- Python `str` → msgpack raw type
- Python `bytes` → msgpack raw type (same as str)

---

## Unpacker Class (Streaming)

For streaming deserialization:

```python
unpacker = msgpack.Unpacker(
    raw=False,             # False (default): raw→str; True: raw→bytes
    strict_map_key=True,   # True (default): only str/bytes map keys
    timestamp=0,           # 0: Timestamp object; 1: float; 2: int (ns); 3: datetime
    use_list=True,         # True (default): array→list; False: array→tuple
    max_buffer_size=100*1024*1024,  # 100 MiB default
)
unpacker.feed(data_chunk)
for obj in unpacker:
    process(obj)
```

### timestamp Parameter

Controls how Timestamp extension types are returned:

| Value | Return type | Description |
|-------|-------------|-------------|
| 0 | `Timestamp` | Native Timestamp object (default) |
| 1 | `float` | Seconds since epoch as floating-point |
| 2 | `int` | Nanoseconds since epoch as integer |
| 3 | `datetime.datetime` | UTC datetime object |

---

## ExtType

Custom extension types use integer codes 0–127:

```python
import msgpack

# Pack
ext = msgpack.ExtType(code=42, data=b"\x01\x02\x03\x04")
packed = msgpack.packb(ext)

# Unpack — ext_hook receives (code, data) and returns a Python object
def my_ext_hook(code, data):
    if code == 42:
        return {"code": code, "data": data}
    return msgpack.ExtType(code, data)

unpacked = msgpack.unpackb(packed, ext_hook=my_ext_hook)
```

**Wire format selection by data length**:

| Data length | Header format |
|-------------|---------------|
| 1 byte | fixext1 (0xD4) |
| 2 bytes | fixext2 (0xD5) |
| 4 bytes | fixext4 (0xD6) |
| 8 bytes | fixext8 (0xD7) |
| 16 bytes | fixext16 (0xD8) |
| 3, 5–15, 17–255 bytes | ext8 (0xC7) |
| 256–65535 bytes | ext16 (0xC8) |
| 65536+ bytes | ext32 (0xC9) |

---

## Pure Python Mode

By default, msgpack uses a compiled C extension. To force the pure Python fallback:

```python
import os
os.environ["MSGPACK_PUREPYTHON"] = "1"
import msgpack  # uses fallback.py
```

---

## Exceptions

| Exception | When raised |
|-----------|-------------|
| `msgpack.ExtraData` | Extra bytes after the first packed object |
| `msgpack.FormatError` | Invalid msgpack format bytes |
| `msgpack.StackError` | Too deeply nested structure |
| `ValueError` | Various: nanoseconds out of range, unknown format, key type violation |
| `UnicodeDecodeError` | UTF-8 decode failure when `raw=False` and `unicode_errors='strict'` |
