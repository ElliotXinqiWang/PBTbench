# pypdf 6.9.0 — Encryption, Filters, and Generic PDF Object API

This document covers the APIs relevant for writing property-based tests targeting
encryption handling, filter decoding, and generic PDF object types in pypdf 6.9.0.

---

## 1. Encryption API (`pypdf._encryption`, `PdfWriter.encrypt`, `PdfReader.decrypt`)

### 1.1 PdfWriter.encrypt()

```python
writer.encrypt(
    user_password: str,
    owner_password: Optional[str] = None,
    use_128bit: bool = True,
    permissions_flag: UserAccessPermissions = ALL_DOCUMENT_PERMISSIONS,
    *,
    algorithm: Optional[str] = None,
) -> None
```

Encrypts the PDF with the PDF Standard security handler.

**Parameters:**
- `user_password`: Password for opening and reading the PDF (with restrictions).
- `owner_password`: Password for unrestricted access. Defaults to `user_password` if `None`.
- `use_128bit`: Use 128-bit RC4 when `True` (default), 40-bit RC4 when `False`.
  Ignored when `algorithm` is specified.
- `permissions_flag`: A `UserAccessPermissions` integer flag (default: all permissions granted).
- `algorithm`: One of `"RC4-40"`, `"RC4-128"`, `"AES-128"`, `"AES-256-R5"`, `"AES-256"`.

**Encryption algorithms and revision numbers:**
| Algorithm   | V | R | Key bits |
|-------------|---|---|----------|
| RC4-40      | 1 | 2 | 40       |
| RC4-128     | 2 | 3 | 128      |
| AES-128     | 4 | 4 | 128      |
| AES-256-R5  | 5 | 5 | 256      |
| AES-256     | 5 | 6 | 256      |

**Usage example:**
```python
import io
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
writer.add_blank_page(width=612, height=792)
writer.add_metadata({"/Title": "Confidential"})
writer.encrypt("user_pass", "owner_pass", algorithm="AES-256")

buf = io.BytesIO()
writer.write(buf)
```

### 1.2 PdfReader.decrypt()

```python
reader.decrypt(password: Union[str, bytes]) -> PasswordType
```

Attempts to decrypt the PDF with the given password.

**Return values (PasswordType enum):**
- `0` / `PasswordType.NOT_DECRYPTED`: Password incorrect, PDF not decrypted.
- `1` / `PasswordType.USER_PASSWORD`: Correct user password; opened with user-level permissions.
- `2` / `PasswordType.OWNER_PASSWORD`: Correct owner password; full unrestricted access.

**Usage example:**
```python
buf.seek(0)
reader = PdfReader(buf)
result = reader.decrypt("user_pass")
assert result == 1  # PasswordType.USER_PASSWORD

buf.seek(0)
reader2 = PdfReader(buf)
result2 = reader2.decrypt("owner_pass")
assert result2 == 2  # PasswordType.OWNER_PASSWORD
```

**Important:** After successful `decrypt()`, `reader.pages`, `reader.metadata`, etc. are accessible.
If `decrypt()` returns 0, reading pages will raise `PdfReadError: file has not been decrypted`.

### 1.3 PdfReader.is_encrypted

```python
reader.is_encrypted  # bool: True if the PDF was encrypted
```

### 1.4 Encryption algorithms: V4 (RC4/AES-128) vs V5 (AES-256)

**V4 (RC4-128 and AES-128, rev 3 or 4):**
- Password verification uses MD5-based key derivation (AlgV4).
- U entry: 32-byte value; first 16 bytes are compared during user-password verification.
- O entry: 32-byte value derived from owner password via RC4 chain.
- Key derivation iterates MD5 50 times for rev >= 3.

**V5 (AES-256, rev 5 or 6):**
- Password verification uses SHA-256-based hashing (AlgV5).
- U entry: 48 bytes = 32-byte hash + 8-byte validation salt + 8-byte key salt.
- O entry: 48 bytes = 32-byte hash + 8-byte validation salt + 8-byte key salt.
  The O hash is computed over: `SHA256(password + owner_val_salt + full_48_byte_U_string)`.
- UE/OE entries: AES-256-CBC-encrypted file encryption keys.
- Perms entry: AES-256-ECB-encrypted permissions block for integrity check.

**Owner password verification (AES-256):**
The stored O entry's first 32 bytes are compared against:
```
SHA256(password + o_entry[32:40] + u_entry[:48])
```
where `u_entry[:48]` is the full 48-byte U string. The verification uses all 48 bytes
of U (hash + both salts), not just the 32-byte hash portion.

### 1.5 Permission flags

```python
from pypdf.constants import UserAccessPermissions

# Common flags (bit positions in the P integer):
UserAccessPermissions.PRINT              # bit 3 (=4)
UserAccessPermissions.MODIFY             # bit 4 (=8)
UserAccessPermissions.EXTRACT            # bit 5 (=16)
UserAccessPermissions.ADD_OR_MODIFY      # bit 6 (=32)
UserAccessPermissions.FILL_FORM_FIELDS   # bit 9 (=256)
UserAccessPermissions.EXTRACT_TEXT_AND_GRAPHICS  # bit 10 (=512)
UserAccessPermissions.ASSEMBLE_DOC       # bit 11 (=1024)
UserAccessPermissions.PRINT_TO_REPRESENTATION    # bit 12 (=2048)

# All permissions granted:
ALL_DOCUMENT_PERMISSIONS = UserAccessPermissions.all()

# Restricted: only print allowed
perms = UserAccessPermissions.PRINT
writer.encrypt("pass", permissions_flag=perms)
```

---

## 2. PDF Filters (`pypdf.filters`)

### 2.1 FlateDecode

Zlib-compressed data (most common PDF stream filter).

```python
from pypdf.filters import FlateDecode

# Encode (compress)
compressed = FlateDecode.encode(data: bytes, level: int = -1) -> bytes

# Decode (decompress)
decompressed = FlateDecode.decode(data: bytes, decode_parms=None) -> bytes
```

`decode_parms` is a `DictionaryObject` with optional predictor information:
- `/Predictor`: 1 (none), 2 (TIFF), 10-15 (PNG predictors).
- `/Columns`: Number of columns (default 1).
- `/Colors`: Number of color components (default 1).
- `/BitsPerComponent`: Bits per component (default 8).

**Roundtrip property:** `FlateDecode.decode(FlateDecode.encode(data)) == data`
(holds for any bytes data, with no predictor).

### 2.2 ASCIIHexDecode

Hexadecimal encoding of binary data.

```python
from pypdf.filters import ASCIIHexDecode
import binascii

# Encoding (not in pypdf, use binascii):
hex_encoded = binascii.hexlify(data) + b">"

# Decoding:
decoded = ASCIIHexDecode.decode(hex_encoded) -> bytes
```

The encoded format: ASCII hex digits (0-9, A-F, a-f) optionally followed by `>` (end-of-data marker). Whitespace is ignored. If the number of hex digits is odd, a trailing `0` nibble is appended before decoding.

### 2.3 RunLengthDecode

Simple byte-oriented run-length encoding.

```python
from pypdf.filters import RunLengthDecode

decoded = RunLengthDecode.decode(data: bytes) -> bytes
```

**Format of encoded data:**
Each run consists of a length byte followed by data:
- **Length byte 0-127**: Copy the next `(length + 1)` bytes literally (1 to 128 bytes).
- **Length byte 129-255**: Repeat the next single byte `(257 - length)` times (2 to 128 repetitions).
- **Length byte 128**: End-of-data marker.

**Run-length repetition count formula:**
For a length byte `L` in the range 129-255:
- Number of repetitions = `257 - L`
- L=255 → 2 repetitions
- L=254 → 3 repetitions
- L=129 → 128 repetitions

**Manual construction example:**
```python
# Literal run: copy 3 bytes (length=2 → 2+1=3 bytes)
rle_literal = bytes([2, 0x41, 0x42, 0x43, 128])  # decodes to b"ABC"

# Run-length: repeat 0x58 (257-253)=4 times
rle_run = bytes([253, 0x58, 128])  # decodes to b"XXXX"

assert RunLengthDecode.decode(rle_literal) == b"ABC"
assert RunLengthDecode.decode(rle_run) == b"XXXX"
```

### 2.4 ASCII85Decode

Base-85 encoding used in some PDF streams.

```python
from pypdf.filters import ASCII85Decode

decoded = ASCII85Decode.decode(data: Union[str, bytes]) -> bytes
```

### 2.5 decode_stream_data

Decodes a StreamObject using its filter chain:

```python
from pypdf.filters import decode_stream_data
decoded = decode_stream_data(stream: StreamObject) -> bytes
```

---

## 3. Generic PDF Object Types (`pypdf.generic._base`)

### 3.1 BooleanObject

Represents PDF boolean values (`true` / `false`).

```python
from pypdf.generic import BooleanObject

b_true = BooleanObject(True)   # writes b"true" to stream
b_false = BooleanObject(False) # writes b"false" to stream

# Comparison
assert BooleanObject(True) == BooleanObject(True)
assert BooleanObject(True) == True
assert BooleanObject(False) != BooleanObject(True)
```

### 3.2 NumberObject

Represents PDF integer values.

```python
from pypdf.generic import NumberObject

n = NumberObject(42)
# NumberObject is a subclass of int; supports arithmetic
assert int(n) == 42
```

### 3.3 FloatObject

Represents PDF real (floating-point) values. Written with up to 8 significant digits.

```python
from pypdf.generic import FloatObject
import io

f = FloatObject(1.23456789)
buf = io.BytesIO()
f.write_to_stream(buf)
print(buf.getvalue())  # b'1.23456789'

# Roundtrip:
written_bytes = buf.getvalue()
parsed_value = float(written_bytes)
# abs(parsed_value - 1.23456789) should be < 1e-8
```

**Precision:** `FLOAT_WRITE_PRECISION = 8` significant digits. For a value `x`:
- Number of decimal places = `FLOAT_WRITE_PRECISION - int(log10(abs(x)))`
- For `x = 1.23456789`: 8 - 0 = 8 decimal places → `"1.23456789"`
- For `x = 12.3456789`: 8 - 1 = 7 decimal places → `"12.345679"`
- For `x = 0.12345678`: 8 - (-1) = 9 decimal places → `"0.12345678"`
- Trailing zeros and trailing decimal points are stripped: `1.50000` → `"1.5"`, `2.00000` → `"2"`

**Write to stream helper:**
```python
import io
from pypdf.generic import FloatObject

def float_roundtrip(x: float) -> float:
    f = FloatObject(x)
    buf = io.BytesIO()
    f.write_to_stream(buf)
    return float(buf.getvalue())
```

### 3.4 ByteStringObject

Represents a raw binary PDF string. Written as hexadecimal between `<` and `>`.

```python
from pypdf.generic import ByteStringObject

bso = ByteStringObject(b"\x00\xff\xab")
buf = io.BytesIO()
bso.write_to_stream(buf)
# buf.getvalue() == b"<00ffab>"
```

### 3.5 TextStringObject

Represents a text PDF string. Written as a parenthesized literal with octal escapes for special characters.

```python
from pypdf.generic import TextStringObject

tso = TextStringObject("Hello World")
buf = io.BytesIO()
tso.write_to_stream(buf)
# writes b"(Hello World)"
```

### 3.6 NameObject

Represents a PDF name (starts with `/`).

```python
from pypdf.generic import NameObject

name = NameObject("/Filter")
```

### 3.7 NullObject

Represents the PDF null value.

```python
from pypdf.generic import NullObject
null = NullObject()
# writes b"null"
```

---

## 4. Writing and Reading Encrypted PDFs: Complete Example

```python
import io
from pypdf import PdfWriter, PdfReader
from pypdf.constants import UserAccessPermissions

def encrypt_and_decrypt_roundtrip(
    user_password: str,
    owner_password: str,
    algorithm: str = "AES-256",
    metadata_title: str = "Test",
) -> tuple[int, int]:
    """
    Returns (user_decrypt_result, owner_decrypt_result).
    Each is 0 (fail), 1 (user), or 2 (owner).
    """
    # Write
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_metadata({"/Title": metadata_title})
    writer.encrypt(user_password, owner_password, algorithm=algorithm)
    buf = io.BytesIO()
    writer.write(buf)

    # Read with user password
    buf.seek(0)
    reader1 = PdfReader(buf)
    user_result = reader1.decrypt(user_password)

    # Read with owner password
    buf.seek(0)
    reader2 = PdfReader(buf)
    owner_result = reader2.decrypt(owner_password)

    return user_result, owner_result

# Correct behavior:
u, o = encrypt_and_decrypt_roundtrip("user", "owner", algorithm="AES-256")
assert u == 1  # PasswordType.USER_PASSWORD
assert o == 2  # PasswordType.OWNER_PASSWORD

u2, o2 = encrypt_and_decrypt_roundtrip("user", "owner", algorithm="RC4-128")
assert u2 == 1
assert o2 == 2
```

---

## 5. Key Invariants to Test

1. **AES-256 owner password roundtrip**: After `writer.encrypt(user_pass, owner_pass, algorithm="AES-256")`,
   `reader.decrypt(owner_pass)` must return `2` (OWNER_PASSWORD).

2. **RC4-128 user password roundtrip**: After `writer.encrypt(user_pass, algorithm="RC4-128")`,
   `reader.decrypt(user_pass)` must return at least `1` (USER_PASSWORD or OWNER_PASSWORD).

3. **RunLengthDecode repetition count**: For a run-length byte `L` in 129-255, decoding
   `bytes([L, data_byte, 128])` must return `bytes([data_byte]) * (257 - L)`.

4. **FloatObject precision**: Writing a `FloatObject(x)` and parsing back the bytes must
   yield a float within `1e-7` of `x` for any `x` in the range `[0.001, 9999.0]`.
