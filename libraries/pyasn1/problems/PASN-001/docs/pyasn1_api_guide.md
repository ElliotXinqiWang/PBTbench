# pyasn1 API Guide

**Version**: 0.6.x
**Language**: Python 3.8+
**Purpose**: Pure-Python ASN.1 library for defining types and encoding/decoding with BER, DER, CER codecs.

---

## Overview

pyasn1 implements the Abstract Syntax Notation One (ASN.1) type system and the
Basic Encoding Rules (BER), Distinguished Encoding Rules (DER), and Canonical
Encoding Rules (CER) codecs. It is used extensively in cryptography and network
protocol libraries (pyOpenSSL, pySnmp, cryptography, ldap3).

The library allows you to:
1. Define ASN.1 type schemas (subclassing built-in types or using `clone()`)
2. Encode Python/pyasn1 values into bytes (BER/DER octet streams)
3. Decode bytes back into pyasn1 value objects
4. Manipulate ASN.1 tags for IMPLICIT/EXPLICIT tagging

---

## Core Module Structure

```
pyasn1/
├── type/
│   ├── univ.py      # Universal types: Integer, OctetString, Sequence, etc.
│   ├── tag.py       # Tag, TagSet, tagging helpers
│   ├── constraint.py # Constraint types (ValueRangeConstraint, etc.)
│   ├── namedtype.py  # NamedType, NamedTypes for Sequence fields
│   └── namedval.py   # NamedValues for Integer named constants
└── codec/
    └── ber/
        ├── encoder.py  # BER encoder
        └── decoder.py  # BER decoder
```

---

## Basic Types (`pyasn1.type.univ`)

### Integer

Represents an ASN.1 INTEGER. Maps to Python `int`.

```python
from pyasn1.type import univ
from pyasn1.codec.ber import encoder, decoder

# Create a value
n = univ.Integer(42)
n = univ.Integer(-100)
n = univ.Integer(0)

# Arithmetic operations work
m = n + 1   # returns univ.Integer(43)

# Encode to BER bytes
encoded = encoder.encode(univ.Integer(42))
# Returns: b'\x02\x01\x2a'  (tag=0x02, length=1, value=42)

# Decode from BER bytes
decoded, remainder = decoder.decode(encoded, asn1Spec=univ.Integer())
int(decoded)  # 42
```

**Named values** (integer enumerations):

```python
from pyasn1.type import namedval

class Status(univ.Integer):
    namedValues = namedval.NamedValues(
        ('ok', 0), ('error', 1), ('pending', 2)
    )

s = Status('ok')     # int value = 0
s = Status(1)        # 'error'
```

**BER encoding rules for Integer**:
- Minimum number of bytes, big-endian, two's complement signed
- Zero encodes as single byte `0x00`
- No redundant leading zero/0xff bytes (except when needed for sign bit)
- Integers 0-127 encode as 3 bytes: tag(1) + len(1) + value(1)
- Integers 128-255 encode as 4 bytes: tag(1) + len(1) + 0x00(sign pad) + value(1)

### OctetString

Represents ASN.1 OCTET STRING. Maps to Python `bytes`.

```python
val = univ.OctetString(b'hello world')
val = univ.OctetString(bytes(range(256)))
val = univ.OctetString('')  # empty

# Access as bytes
raw = bytes(val)  # or val.asOctets()
length = len(val)

# BER encoding
encoded = encoder.encode(univ.OctetString(b'hello'))
# Returns: b'\x04\x05hello'  (tag=0x04, length=5, value)

# Chunked (constructed) encoding
# Use maxChunkSize to split into multiple primitive chunks
long_data = bytes(range(200))
chunked = encoder.encode(univ.OctetString(long_data), maxChunkSize=50)
# Encoding starts with 0x24 (constructed OctetString tag)
# Followed by sub-encodings of 50-byte chunks
```

**BER encoding rules for OctetString**:
- Short payload (≤ maxChunkSize or maxChunkSize=0): primitive encoding, tag byte = `0x04`
- Long payload with chunking: constructed encoding, tag byte = `0x24`
  - Each chunk is a primitive OctetString TLV
  - The outer length covers all inner TLVs
- DER requires primitive encoding (no chunking)

### Boolean

```python
val = univ.Boolean(True)
val = univ.Boolean(False)
encoded = encoder.encode(val)  # b'\x01\x01\xff' or b'\x01\x01\x00'
decoded, _ = decoder.decode(encoded, asn1Spec=univ.Boolean())
bool(decoded)  # True or False
```

### Null

```python
val = univ.Null('')
encoded = encoder.encode(val)  # b'\x05\x00'  (tag + zero length)
```

### ObjectIdentifier

Represents ASN.1 OBJECT IDENTIFIER. Stored as a tuple of integer arcs.

```python
oid = univ.ObjectIdentifier((1, 2, 840, 113549, 1, 1, 5))  # sha1WithRSAEncryption
encoded = encoder.encode(oid)

decoded, _ = decoder.decode(encoded, asn1Spec=univ.ObjectIdentifier())
tuple(decoded)  # (1, 2, 840, 113549, 1, 1, 5)
```

**OID encoding rules**:
- First two arcs combined: `combined = arc[0] * 40 + arc[1]`
  - arc[0] == 0: combined = arc[1] (0..39)
  - arc[0] == 1: combined = arc[1] + 40 (40..79)
  - arc[0] == 2: combined = arc[1] + 80 (80+)
- Subsequent arcs encoded as base-128 big-endian with continuation bits
- All subsequent arcs with values 0-127 encode as single byte

**Important invariant**: For any valid OID, `encode(decode(encode(oid))) == encode(oid)`.

---

## Structured Types

### Sequence

```python
from pyasn1.type import namedtype

class PersonRecord(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('name', univ.OctetString()),
        namedtype.NamedType('age', univ.Integer()),
        namedtype.OptionalNamedType('email', univ.OctetString()),
    )

# Create and populate
record = PersonRecord()
record['name'] = univ.OctetString(b'Alice')
record['age'] = univ.Integer(30)

encoded = encoder.encode(record)
decoded, _ = decoder.decode(encoded, asn1Spec=PersonRecord())
bytes(decoded['name'])  # b'Alice'
int(decoded['age'])     # 30
```

### SequenceOf / SetOf

```python
# SequenceOf: ordered collection of same type
seq = univ.SequenceOf(componentType=univ.Integer())
seq.extend([univ.Integer(1), univ.Integer(2), univ.Integer(3)])

encoded = encoder.encode(seq)
decoded, _ = decoder.decode(encoded, asn1Spec=univ.SequenceOf(componentType=univ.Integer()))
[int(decoded[i]) for i in range(len(decoded))]  # [1, 2, 3]
```

---

## Tag System (`pyasn1.type.tag`)

### Tag constants

```python
from pyasn1.type import tag

# Tag classes
tag.tagClassUniversal    # 0x00 — built-in ASN.1 types
tag.tagClassApplication  # 0x40 — application-specific
tag.tagClassContext      # 0x80 — context-specific (most common for tagging)
tag.tagClassPrivate      # 0xC0 — private use

# Tag formats
tag.tagFormatSimple      # 0x00 — PRIMITIVE encoding (scalars)
tag.tagFormatConstructed # 0x20 — CONSTRUCTED encoding (containers)

# Tag categories
tag.tagCategoryImplicit  # 0x01
tag.tagCategoryExplicit  # 0x02
```

### Tag object

A `Tag` is an immutable 3-tuple `(tagClass, tagFormat, tagId)`.

```python
# Context-specific, PRIMITIVE, ID=0
t = tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 0)

# Context-specific, CONSTRUCTED, ID=2
tc = tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 2)

# Access components
t.tagClass   # 0x80
t.tagFormat  # 0x00
t.tagId      # 0
```

### TagSet and tagging operations

A `TagSet` holds one or more `Tag` objects representing the full tag path from
base type to outermost wrapper.

```python
# Base TagSet for Integer: single tag [UNIVERSAL, PRIMITIVE, 2]
ts = univ.Integer.tagSet
len(ts)   # 1
ts[0]     # Tag(0x00, 0x00, 0x02)

# tagExplicitly: WRAPS the type in a new outer CONSTRUCTED tag
#   - Adds a tag to the TagSet
#   - Outer tag is always CONSTRUCTED (per ASN.1 spec)
#   - Preserves all inner tags
explicit_ts = ts.tagExplicitly(tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 3))
len(explicit_ts)  # 2
explicit_ts[0]    # inner: Tag(0x00, 0x00, 0x02) — base Integer tag
explicit_ts[-1]   # outer: Tag(0x80, 0x20, 0x03) — context [3] CONSTRUCTED

# tagImplicitly: REPLACES the outermost tag
#   - Replaces the last tag in the TagSet
#   - The new tag inherits tagFormat from the replaced tag
#   - The base type's tag is preserved at index 0
implicit_ts = ts.tagImplicitly(tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 5))
len(implicit_ts)  # 1 (replaced, not added)
implicit_ts[0]    # Tag(0x80, 0x00, 0x05) — PRIMITIVE inherited from Integer
```

**CRITICAL**: `tagImplicitly()` inherits `tagFormat` from `self.__superTags[-1]`
(the current outermost tag), **not** from `self.__superTags[0]` (the base type tag).
This distinction matters only when a TagSet has 2+ elements:

```python
# Example: OctetString with explicit outer, then implicit on top
base = univ.OctetString.tagSet  # PRIMITIVE base
exp = base.tagExplicitly(tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 2))
# exp has 2 tags: [PRIMITIVE_base, CONSTRUCTED_wrapper]
# exp[-1].tagFormat == tagFormatConstructed  (0x20)

imp = exp.tagImplicitly(tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 7))
# imp[-1] replaces exp[-1], inheriting CONSTRUCTED format
# imp[-1].tagFormat == tagFormatConstructed  (correct)
# If tagFormat came from exp[0]: imp[-1].tagFormat == tagFormatSimple (wrong)
```

**Why this matters for encoding**: The encoder uses the outermost tag's `tagFormat`
to set the CONSTRUCTED bit in the encoded tag byte. If the format is wrong, the
decoder receives a tag with the wrong CONSTRUCTED flag and cannot match it to
the expected type, causing a `PyAsn1Error`.

---

## BER Length Encoding

BER length encoding has two forms:

### Short form (0 ≤ length ≤ 127)
Single byte: `length` value directly.
```
length = 5   → encoded as 0x05
length = 127 → encoded as 0x7f
```

### Long form (length ≥ 128)
First byte: `0x80 | N` where N = number of subsequent length bytes.
Then N bytes encoding the length as big-endian integer.
```
length = 128 → encoded as 0x81 0x80  (1 byte follows, value=128)
length = 256 → encoded as 0x82 0x01 0x00  (2 bytes follow)
length = 300 → encoded as 0x82 0x01 0x2c
```

**IMPORTANT**: The single byte `0x80` (short form of 128) is **NOT valid** as a
length encoding — it is reserved as the **indefinite-length indicator** in BER.
Only definite-length encoding is supported by the pyasn1 decoder by default.

**Summary**:
- `length < 128`: use short form (1 byte)
- `length >= 128`: use long form (2+ bytes starting with `0x80 | N`)

---

## BER TLV Encoding Format

Every ASN.1 value is encoded as TLV (Tag-Length-Value):

```
+--------+--------+---------+
|  Tag   | Length |  Value  |
+--------+--------+---------+

Tag byte (1 byte for tag ID < 31):
  bits 7-6: class (00=UNIVERSAL, 01=APPLICATION, 10=CONTEXT, 11=PRIVATE)
  bit  5:   format (0=PRIMITIVE, 1=CONSTRUCTED)
  bits 4-0: tag ID (0-30 for short form)

Tag bytes (2+ bytes for tag ID >= 31):
  first byte:  class | format | 0x1F
  subsequent:  base-128 encoded tag ID, MSB bits set to 1 except last

Length:
  short form: 1 byte, value 0-127
  long form:  first byte = 0x80 | N, then N bytes for length

Value:
  for PRIMITIVE: raw bytes
  for CONSTRUCTED: sequence of TLVs (for Sequence, SequenceOf, EXPLICIT wrapper)
```

---

## Roundtrip Invariants

pyasn1 guarantees these invariants for well-formed values:

1. **Encode-decode roundtrip**: `decode(encode(value), asn1Spec=type(value)) == value`
2. **Decode-encode roundtrip**: `encode(decode(bytes, asn1Spec=T)) == bytes` (for DER)
3. **Tag preservation**: The `tagSet` of a decoded value matches the `asn1Spec`'s tagSet

These invariants hold for:
- All integer values (positive, negative, zero)
- OctetStrings of all lengths, with and without chunked encoding
- ObjectIdentifiers with any valid first/second arc combination
- Sequences with any combination of field types
- All tagging modes (single IMPLICIT, single EXPLICIT, chained)

**Encoding options affecting invariants**:

```python
# Default encoding (primitive for scalars, definite-length)
encoder.encode(val)

# Indefinite length encoding
encoder.encode(val, defMode=False)

# Chunked OctetString (constructed encoding)
encoder.encode(octet_val, maxChunkSize=16)
# Creates constructed TLV: each chunk is a primitive OctetString TLV
# Decoder reassembles chunks into single OctetString value
```

---

## IMPLICIT vs EXPLICIT Tagging

### IMPLICIT tagging
Replaces the outermost tag with a new tag, preserving the encoding structure:

```
IMPLICIT example:
  [CONTEXT 3] IMPLICIT INTEGER ::= 42

Encoding: tag=0x83 (context 3, PRIMITIVE), length=1, value=0x2a
           Note: PRIMITIVE because base type (INTEGER) is PRIMITIVE
           (NOT the wrapper CONSTRUCTED bit — IMPLICIT keeps the inner encoding)
```

```python
# Define an implicitly tagged Integer
ImplicitInt = univ.Integer().clone(
    tagSet=univ.Integer.tagSet.tagImplicitly(
        tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 3)
    )
)
val = ImplicitInt.clone(42)
encoder.encode(val)  # b'\x83\x01\x2a'
```

### EXPLICIT tagging
Wraps the value in an outer CONSTRUCTED tag, preserving the inner encoding:

```
EXPLICIT example:
  [CONTEXT 0] EXPLICIT INTEGER ::= 42

Encoding: tag=0xa0 (context 0, CONSTRUCTED), length=3, then inner INTEGER TLV
```

```python
ExplicitInt = univ.Integer().clone(
    tagSet=univ.Integer.tagSet.tagExplicitly(
        tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 0)
    )
)
val = ExplicitInt.clone(42)
encoder.encode(val)  # b'\xa0\x03\x02\x01\x2a'
```

### Chained tagging

Sometimes a type is EXPLICITLY tagged, then IMPLICITLY tagged again:

```
MyType ::= [APPLICATION 5] IMPLICIT ([CONTEXT 2] EXPLICIT OctetString)
```

```python
# Step 1: apply EXPLICIT tag
base = univ.OctetString.tagSet  # [UNIVERSAL PRIMITIVE 4]
exp_ts = base.tagExplicitly(tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 2))
# exp_ts has 2 tags: [(UNIV, PRIM, 4), (CTXT, CONS, 2)]
# The EXPLICIT wrapper means the outer tag is CONSTRUCTED

# Step 2: apply IMPLICIT tag on the explicitly-tagged type
imp_ts = exp_ts.tagImplicitly(tag.Tag(tag.tagClassApplication, tag.tagFormatSimple, 5))
# The new tag REPLACES the outermost (index -1), inheriting its tagFormat
# Since exp_ts[-1] is CONSTRUCTED, imp_ts[-1] must also be CONSTRUCTED
# imp_ts has 2 tags: [(UNIV, PRIM, 4), (APP, CONS, 5)]

# The format bit (CONSTRUCTED=0x20) is critical:
# Correct: 0x65 = APPLICATION(0x40) | CONSTRUCTED(0x20) | 5 = outer tag
# Wrong:   0x45 = APPLICATION(0x40) | PRIMITIVE(0x00) | 5 = wrong!
```

---

## Codec Usage Patterns

### Basic encode/decode

```python
from pyasn1.codec.ber import encoder, decoder

# Encode
enc = encoder.encode(value)              # from ASN.1 object
enc = encoder.encode(42, asn1Spec=univ.Integer())  # from Python value

# Decode
obj, remaining_bytes = decoder.decode(enc)                # auto-detect type
obj, remaining_bytes = decoder.decode(enc, asn1Spec=univ.Integer())  # with schema
```

### OctetString chunked encoding

Useful for streaming large binary data; BER allows constructed (chunked) encoding:

```python
data = bytes(range(256))  # 256-byte payload

# Primitive encoding (single TLV):
enc_prim = encoder.encode(univ.OctetString(data))
# Structure: [0x04] [0x82 0x01 0x00] [256 bytes data]

# Constructed encoding (multiple chunks):
enc_chunked = encoder.encode(univ.OctetString(data), maxChunkSize=64)
# Structure: [0x24] [len] { [0x04][0x40][64 bytes] × 4 }
# Each chunk is a separate primitive OctetString TLV

# Both decode to the same value:
dec, _ = decoder.decode(enc_chunked, asn1Spec=univ.OctetString())
bytes(dec) == data  # True
```

**maxChunkSize behavior**:
- `maxChunkSize=0` (default): use primitive encoding regardless of size
- `maxChunkSize=N` (N > 0): use constructed encoding if `len(data) > N`, splitting into N-byte chunks

### Indefinite length encoding

```python
# Indefinite length mode (BER allows this, DER forbids it)
enc_indef = encoder.encode(val, defMode=False)
dec, _ = decoder.decode(enc_indef, asn1Spec=type(val)())
```

---

## Error Handling

```python
from pyasn1 import error

try:
    obj, _ = decoder.decode(b'\x02\x01\xFF', asn1Spec=univ.Integer())
except error.PyAsn1Error as e:
    print(f"Decode error: {e}")

# Common errors:
# - PyAsn1Error: tag mismatch, malformed encoding, constraint violation
# - SubstrateUnderrunError: not enough bytes
# - ValueConstraintError: value violates subtype constraint
```

---

## Key API Reference

### univ module

| Class | ASN.1 type | Python type | Tag |
|---|---|---|---|
| `Integer` | INTEGER | int | `[UNIVERSAL PRIMITIVE 2]` |
| `Boolean` | BOOLEAN | int(0/1) | `[UNIVERSAL PRIMITIVE 1]` |
| `OctetString` | OCTET STRING | bytes | `[UNIVERSAL PRIMITIVE 4]` |
| `Null` | NULL | '' | `[UNIVERSAL PRIMITIVE 5]` |
| `ObjectIdentifier` | OID | tuple | `[UNIVERSAL PRIMITIVE 6]` |
| `Real` | REAL | float | `[UNIVERSAL PRIMITIVE 9]` |
| `Enumerated` | ENUMERATED | int | `[UNIVERSAL PRIMITIVE 10]` |
| `Sequence` | SEQUENCE | — | `[UNIVERSAL CONSTRUCTED 16]` |
| `SequenceOf` | SEQUENCE OF | — | `[UNIVERSAL CONSTRUCTED 16]` |
| `Set` | SET | — | `[UNIVERSAL CONSTRUCTED 17]` |
| `SetOf` | SET OF | — | `[UNIVERSAL CONSTRUCTED 17]` |
| `Choice` | CHOICE | — | (no universal tag) |
| `Any` | ANY | — | (no universal tag) |

### tag module

| Function/Class | Description |
|---|---|
| `Tag(class, format, id)` | Create an immutable Tag |
| `TagSet(baseTag, *superTags)` | Create a TagSet |
| `TagSet.tagExplicitly(tag)` | Add EXPLICIT outer tag (CONSTRUCTED) |
| `TagSet.tagImplicitly(tag)` | Replace outermost tag (inherits format) |
| `TagSet.isSuperTagSetOf(ts)` | Test if this TagSet is a supertype of ts |
| `initTagSet(tag)` | Create TagSet with single tag as both base and super |

### encoder/decoder

| Function | Description |
|---|---|
| `encoder.encode(val, asn1Spec=None, defMode=True, maxChunkSize=0)` | Encode to BER bytes |
| `decoder.decode(substrate, asn1Spec=None)` | Decode BER bytes, returns (value, remainder) |
