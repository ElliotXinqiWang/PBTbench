# MessagePack Wire Format Specification

> Source: https://github.com/msgpack/msgpack/blob/master/spec.md
> Official specification for the MessagePack serialization format.

---

## Overview

MessagePack is an efficient binary serialization format. Objects such as integers, floats, booleans, strings, binary data, arrays, and maps can be represented in a compact binary form.

**Key serialization principle:**
> "If an object can be represented in multiple possible output formats, serializers SHOULD use the format which represents the data in the smallest number of bytes."

---

## Integer Formats

### Positive Fixint

| Property | Value |
|----------|-------|
| Format byte | `0xxxxxxx` (binary) |
| Byte range | `0x00` – `0x7f` |
| Value range | 0 to 127 |
| Total bytes | 1 |

Encodes small non-negative integers directly in the first (and only) byte.

```
+--------+
|0XXXXXXX|
+--------+
```

### Negative Fixint

| Property | Value |
|----------|-------|
| Format byte | `111yyyyy` (binary) |
| Byte range | `0xe0` – `0xff` |
| Value range | −32 to −1 |
| Total bytes | 1 |

Encodes small negative integers in the lower 5 bits (signed).

```
+--------+
|111YYYYY|
+--------+
```

### uint 8

| Property | Value |
|----------|-------|
| Header byte | `0xcc` |
| Value range | 0 to 255 |
| Total bytes | 2 (header + 1 data byte) |
| Encoding | Unsigned 8-bit integer |

```
+--------+--------+
|  0xcc  |ZZZZZZZZ|
+--------+--------+
```

### uint 16

| Property | Value |
|----------|-------|
| Header byte | `0xcd` |
| Value range | 0 to 65,535 |
| Total bytes | 3 (header + 2 data bytes) |
| Encoding | Unsigned 16-bit integer, big-endian |

```
+--------+--------+--------+
|  0xcd  |ZZZZZZZZ|ZZZZZZZZ|
+--------+--------+--------+
```

**Note:** The 2 data bytes are interpreted as an **unsigned** 16-bit big-endian integer. The value range is 0–65535. This is distinct from int 16 which is signed (−32768 to 32767).

### uint 32

| Property | Value |
|----------|-------|
| Header byte | `0xce` |
| Value range | 0 to 4,294,967,295 |
| Total bytes | 5 (header + 4 data bytes) |
| Encoding | Unsigned 32-bit integer, big-endian |

```
+--------+--------+--------+--------+--------+
|  0xce  |ZZZZZZZZ|ZZZZZZZZ|ZZZZZZZZ|ZZZZZZZZ|
+--------+--------+--------+--------+--------+
```

### uint 64

| Property | Value |
|----------|-------|
| Header byte | `0xcf` |
| Value range | 0 to 18,446,744,073,709,551,615 |
| Total bytes | 9 (header + 8 data bytes) |
| Encoding | Unsigned 64-bit integer, big-endian |

### int 8

| Property | Value |
|----------|-------|
| Header byte | `0xd0` |
| Value range | −128 to 127 |
| Total bytes | 2 (header + 1 data byte) |
| Encoding | Signed 8-bit integer |

### int 16

| Property | Value |
|----------|-------|
| Header byte | `0xd1` |
| Value range | −32,768 to 32,767 |
| Total bytes | 3 (header + 2 data bytes) |
| Encoding | Signed 16-bit integer, big-endian |

```
+--------+--------+--------+
|  0xd1  |ZZZZZZZZ|ZZZZZZZZ|
+--------+--------+--------+
```

**Note:** The 2 data bytes are interpreted as a **signed** 16-bit big-endian integer. The value range is −32768 to 32767. This is distinct from uint 16 which is unsigned (0 to 65535).

### int 32

| Property | Value |
|----------|-------|
| Header byte | `0xd2` |
| Value range | −2,147,483,648 to 2,147,483,647 |
| Total bytes | 5 (header + 4 data bytes) |
| Encoding | Signed 32-bit integer, big-endian |

### int 64

| Property | Value |
|----------|-------|
| Header byte | `0xd3` |
| Value range | −9,223,372,036,854,775,808 to 9,223,372,036,854,775,807 |
| Total bytes | 9 (header + 8 data bytes) |
| Encoding | Signed 64-bit integer, big-endian |

---

## String Formats

### fixstr

| Property | Value |
|----------|-------|
| Format byte | `101xxxxx` (binary) |
| Byte range | `0xa0` – `0xbf` |
| Max length | 31 bytes |
| Total bytes | 1 + N (header encodes length in lower 5 bits + UTF-8 data) |

```
+--------+========+
|101XXXXX|  data  |
+--------+========+
```

The lower 5 bits of the header byte encode the string length (0–31). A string of exactly 31 bytes uses header `0xbf`.

**Boundary:** fixstr can encode strings of 0 to **31** bytes. Strings of 32 bytes or more use str 8, str 16, or str 32.

### str 8

| Property | Value |
|----------|-------|
| Header byte | `0xd9` |
| Max length | 255 bytes |
| Total bytes | 2 + N (header + 1-byte length + UTF-8 data) |

```
+--------+--------+========+
|  0xd9  |YYYYYYYY|  data  |
+--------+--------+========+
```

### str 16

| Property | Value |
|----------|-------|
| Header byte | `0xda` |
| Max length | 65,535 bytes |
| Total bytes | 3 + N (header + 2-byte big-endian length + UTF-8 data) |

```
+--------+--------+--------+========+
|  0xda  |ZZZZZZZZ|ZZZZZZZZ|  data  |
+--------+--------+--------+========+
```

### str 32

| Property | Value |
|----------|-------|
| Header byte | `0xdb` |
| Max length | 4,294,967,295 bytes |
| Total bytes | 5 + N (header + 4-byte big-endian length + UTF-8 data) |

```
+--------+--------+--------+--------+--------+========+
|  0xdb  |ZZZZZZZZ|ZZZZZZZZ|ZZZZZZZZ|ZZZZZZZZ|  data  |
+--------+--------+--------+--------+--------+========+
```

---

## Binary Formats

### bin 8

| Header | Length field | Max size |
|--------|-------------|---------|
| `0xc4` | 1 byte | 255 bytes |

### bin 16

| Header | Length field | Max size |
|--------|-------------|---------|
| `0xc5` | 2 bytes (big-endian) | 65,535 bytes |

### bin 32

| Header | Length field | Max size |
|--------|-------------|---------|
| `0xc6` | 4 bytes (big-endian) | 4,294,967,295 bytes |

---

## Format Selection Summary

Serializers SHOULD choose the most compact representation:

### Integer selection order

| Value range | Format chosen |
|-------------|--------------|
| 0 – 127 | positive fixint (1 byte) |
| −32 – −1 | negative fixint (1 byte) |
| 0 – 255 | uint 8 (2 bytes) |
| −128 – 127 | int 8 (2 bytes) |
| 0 – 65,535 | uint 16 (3 bytes) |
| −32,768 – 32,767 | int 16 (3 bytes) |
| 0 – 4,294,967,295 | uint 32 (5 bytes) |
| −2^31 – 2^31−1 | int 32 (5 bytes) |
| 0 – 2^64−1 | uint 64 (9 bytes) |
| −2^63 – 2^63−1 | int 64 (9 bytes) |

### String selection order

| String byte length | Format chosen |
|-------------------|--------------|
| 0 – 31 | fixstr (1 + N bytes) |
| 32 – 255 | str 8 (2 + N bytes) |
| 256 – 65,535 | str 16 (3 + N bytes) |
| 65,536 – 4,294,967,295 | str 32 (5 + N bytes) |

---

## Signed vs. Unsigned: Critical Distinction

The msgpack specification carefully distinguishes signed and unsigned integer types:

- **uint 16** (`0xcd`): 2 bytes interpreted as **unsigned** → range 0 to 65,535.
  - Python struct format: `">H"` (uppercase H = unsigned short)
- **int 16** (`0xd1`): 2 bytes interpreted as **signed** → range −32,768 to 32,767.
  - Python struct format: `">h"` (lowercase h = signed short)

Using a signed format where unsigned is required (or vice versa) will produce incorrect values for inputs in the range 32,768–65,535, as the high bit would be misinterpreted as a sign bit.
