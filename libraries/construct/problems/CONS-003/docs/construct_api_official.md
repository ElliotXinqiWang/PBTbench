# construct — Binary Data Format API Reference

Source: https://construct.readthedocs.io/en/latest/

## Overview

construct is a declarative, symmetric parser and builder for binary data. The core property:

```
parse(build(obj)) == obj
```

This roundtrip invariant holds for all well-formed inputs.

---

## Prefixed

Wraps a subcon with a length prefix. The length field records how many bytes the subcon produces. On parsing, reads exactly that many bytes and feeds them to the subcon.

```python
Prefixed(lengthfield, subcon, includelength=False)
```

### Parameters

- `lengthfield`: A fixed-size integer construct (e.g. `Int8ub`, `Int16ub`, `VarInt`) used to encode/decode the length value.
- `subcon`: Any construct that processes the payload bytes.
- `includelength` (default `False`): When `True`, the stored length value **includes the size of the length field itself**. This is used in protocols (e.g. some binary framing formats) where the "message length" field counts its own bytes as part of the total message size.

### Semantics

When `includelength=False` (default):
- Build: writes `len(payload)` as the length, then the payload.
- Parse: reads the stored length `L`, then reads `L` bytes as the payload.

When `includelength=True`:
- Build: the stored length is `len(payload) + sizeof(lengthfield)`. This accounts for the length field itself.
- Parse: the stored length `L` is read; then `L - sizeof(lengthfield)` bytes are read as the payload.

### Example

```python
# Default: length = payload bytes
d = Prefixed(Int8ub, GreedyBytes)
d.build(b"hello")    # b'\x05hello'
d.parse(b'\x05hello')  # b'hello'

# includelength=True: stored length includes the 1-byte length field
d2 = Prefixed(Int8ub, GreedyBytes, includelength=True)
d2.build(b"hello")    # stored length = 5 + 1 = 6
d2.parse(d2.build(b"hello"))  # b'hello'
```

### Analog

`PrefixedArray(countfield, subcon)` is similar but stores an *element count* rather than a byte count.

---

## Array

Homogeneous fixed-size array of elements.

```python
Array(count, subcon, discard=False)
```

Also available via operator syntax: `subcon[count]` or `Byte[5]`.

### Parameters

- `count`: Integer or context lambda. The exact number of elements to parse/build.
- `subcon`: The construct for each element.
- `discard`: If `True`, parsed values are not collected (returns empty list).

### Semantics

- Parse: reads exactly `count` elements.
- Build: requires `len(obj) == count`; raises `RangeError` otherwise.
- Size: `count * subcon.sizeof()` (only if subcon has a fixed size).

### Context Index

During parsing and building, `this._index` (or `context._index`) is set to the **zero-based** position of the current element. Subcons can use this value via lambda expressions:

```python
Array(4, Bytes(lambda ctx: ctx._index + 1))
# element 0 → 1 byte, element 1 → 2 bytes, etc.
```

### Example

```python
d = Array(5, Byte)
d.build([0, 1, 2, 3, 4])   # b'\x00\x01\x02\x03\x04'
d.parse(b'\x00\x01\x02\x03\x04')  # [0, 1, 2, 3, 4]
```

---

## Struct

Sequence of named fields, similar to C structs.

```python
Struct(*subcons, **subconskw)
```

### Semantics

- Parse: returns a `Container` (dict-like object with attribute access).
- Build: takes a dict or `Container`; each field looks up its value by name.
- Fields are processed in declaration order.

### Context

Each field's subcon receives a context dictionary containing all previously parsed fields. This enables length-prefixed patterns:

```python
d = Struct(
    "length" / Int8ub,
    "data" / Bytes(this.length),
)
```

### Example

```python
d = Struct("x" / Int8ub, "y" / Int16ub)
d.build(dict(x=1, y=1000))   # b'\x01\x03\xe8'
d.parse(b'\x01\x03\xe8')     # Container(x=1, y=1000)
```

---

## BitsInteger

Variable-width integer for use inside a `Bitwise` context. The stream inside `Bitwise` represents individual bits as `\x00` or `\x01` bytes.

```python
BitsInteger(length, signed=False, swapped=False)
```

### Parameters

- `length`: Number of bits (integer or context lambda).
- `signed`: If `True`, interprets the value as a two's-complement signed integer. Default is `False` (unsigned).
- `swapped`: If `True`, swaps byte groups (little-endian byte order). Only valid when `length` is a multiple of 8. Default is `False`.

### Signed Semantics

When `signed=True`, the MSB (first bit in the bitstream) is the sign bit:
- MSB = 0: non-negative value; range `[0, 2^(n-1) - 1]`
- MSB = 1: negative value (two's-complement); range `[-2^(n-1), -1]`

For `BitsInteger(8, signed=True)`:
- Value range: `-128` to `127`
- `-1` is represented as all-ones: `b'\x01\x01\x01\x01\x01\x01\x01\x01'`
- `-128` is represented as `b'\x01\x00\x00\x00\x00\x00\x00\x00'`

### Usage

Must be enclosed in a `Bitwise` context:

```python
d = Bitwise(BitsInteger(8))          # 1-byte unsigned
d = Bitwise(BitsInteger(8, signed=True))  # 1-byte signed
d = Bitwise(BitsInteger(4))          # Nibble (4-bit unsigned)
```

### Equivalence with BytesInteger

```python
BytesInteger(n)                    # same as Bitwise(BitsInteger(8*n))
BitsInteger(8*n)                   # same as Bytewise(BytesInteger(n))
BytesInteger(n, swapped=True)      # same as Bitwise(BitsInteger(8*n, swapped=True))
```

### Example

```python
d = Bitwise(BitsInteger(8, signed=True))
d.build(127)    # b'\x7f'
d.build(-1)     # b'\xff'
d.build(-128)   # b'\x80'
d.parse(b'\x7f')   # 127
d.parse(b'\xff')   # -1
d.parse(b'\x80')   # -128
```

---

## BytesInteger

Arbitrary-width byte-level integer.

```python
BytesInteger(length, signed=False, swapped=False)
```

### Parameters

- `length`: Number of bytes.
- `signed`: Two's-complement signed if `True`.
- `swapped`: Little-endian byte order if `True`.

### Predefined Fields

```
Int8ub / Int8sb    (1 byte, unsigned/signed, big-endian)
Int16ub / Int16ul  (2 bytes, unsigned, big/little-endian)
Int32ub / Int32ul  (4 bytes, unsigned, big/little-endian)
Int64ub / Int64ul  (8 bytes, unsigned, big/little-endian)
```

---

## GreedyBytes

Reads all remaining bytes from the current stream or substream.

```python
GreedyBytes  # singleton
```

### Example

```python
GreedyBytes.parse(b"hello")   # b'hello'
GreedyBytes.build(b"hello")   # b'hello'
```

---

## GreedyRange

Repeats a subcon until end-of-stream or a parse error.

```python
GreedyRange(subcon, discard=False)
```

Parses until `EOF` or subcon fails; automatically backtracks to last successful parse position. Builds from any iterable.

---

## Key Invariants

1. **Roundtrip**: `parse(build(obj)) == obj` for all valid inputs.
2. **Symmetry**: build and parse use the same structural definition.
3. **Length fields**: When a length field encodes data size, its semantic must be consistent between build and parse. Any asymmetry (e.g. off-by-one, incorrect sign) silently corrupts the roundtrip.
4. **Signed bit integers**: The two's-complement representation requires precise bias handling. For an n-bit signed integer with MSB=1, the value is `unsigned_value - 2^n`.
