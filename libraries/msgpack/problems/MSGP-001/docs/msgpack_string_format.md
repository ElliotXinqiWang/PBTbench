# msgpack String and Bytes Format Specification

msgpack uses different format markers for strings (`str`) and byte strings (`bytes`), and automatically selects the most compact encoding based on data length.

## String Format Overview

| Format Name | Marker Byte   | Length Field | Valid Range (byte count)         |
|-------------|---------------|-------------|----------------------------------|
| fixstr      | 0xA0-0xBF     | 0 bytes     | **[0, 31]** (length encoded in low 5 bits of marker byte) |
| str 8       | 0xD9          | **1 byte**  | **[32, 255]**                    |
| str 16      | 0xDA          | 2 bytes     | [256, 65535]                     |
| str 32      | 0xDB          | 4 bytes     | [65536, 2^32-1]                  |

**Important**: The length refers to the string's **UTF-8 encoded byte count**, not the number of Python characters.

### fixstr Format Details

The fixstr marker byte is `0xA0 | length`, where `length` is at most `0x1F = 31`:
- `0xA0` -> 0-byte string
- `0xBF` -> 31-byte string (maximum fixstr)

A string of 32 bytes in length **cannot** use fixstr and must use str 8 (0xD9).

### Encoding Selection Logic

```
len(s_bytes) in [0, 31]         -> fixstr  (marker byte 0xA0 + len, no separate length field)
len(s_bytes) in [32, 255]       -> str 8   (0xD9 + 1-byte length)
len(s_bytes) in [256, 65535]    -> str 16  (0xDA + 2-byte length)
len(s_bytes) in [65536, 2^32-1] -> str 32  (0xDB + 4-byte length)
```

Where `s_bytes = s.encode("utf-8")`.

## Bytes Format Overview

| Format Name | Marker Byte | Length Field | Valid Range (byte count) |
|-------------|-------------|-------------|--------------------------|
| bin 8       | 0xC4        | 1 byte      | [0, 255]                 |
| bin 16      | 0xC5        | 2 bytes     | [256, 65535]             |
| bin 32      | 0xC6        | 4 bytes     | [65536, 2^32-1]          |

## Roundtrip Invariant

For any valid string `s`, serializing and then deserializing should recover the original value:

```python
unpackb(packb(s), raw=False) == s
```

For any valid byte string `b`:

```python
unpackb(packb(b)) == b
```

This applies to the entire length range supported by msgpack.

## Importance of Format Boundaries

A correct implementation must maintain semantic correctness at format switching boundaries:

- **fixstr / str8 boundary**: 31 bytes vs 32 bytes. Lengths <= 31 use fixstr; lengths >= 32 use str8.
  Errors at this boundary cause the marker byte to be written as an illegal value (e.g., 0xC0),
  which in msgpack is the reserved nil marker.
- **str8 / str16 boundary**: 255 bytes vs 256 bytes.

Any correct msgpack Python implementation must guarantee roundtrip correctness at these boundaries.

## Usage Examples

```python
import msgpack

# fixstr (0-31 bytes)
s_short = "hello"                     # 5 bytes
assert msgpack.unpackb(msgpack.packb(s_short), raw=False) == s_short

# str8 (32-255 bytes)
s_32 = "a" * 32                       # exactly 32 bytes -- fixstr/str8 boundary
assert msgpack.unpackb(msgpack.packb(s_32), raw=False) == s_32

s_100 = "x" * 100                     # 100 bytes, str8
assert msgpack.unpackb(msgpack.packb(s_100), raw=False) == s_100

# str16 (256+ bytes)
s_long = "b" * 300                    # 300 bytes, str16
assert msgpack.unpackb(msgpack.packb(s_long), raw=False) == s_long
```

## Notes

- Non-ASCII characters in Python `str` (e.g., CJK, emoji) take 2-4 bytes in UTF-8,
  so the character count != byte count. When testing byte-length boundaries, use ASCII
  characters (codepoint <= 127) to ensure each character is exactly 1 byte.
- `packb` with `use_bin_type=True` (default) encodes Python `bytes` objects using the bin format,
  and Python `str` using the str format (raw format = False).
