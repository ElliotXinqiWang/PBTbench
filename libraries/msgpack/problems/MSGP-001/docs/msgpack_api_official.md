# msgpack-python API Reference (Official Documentation)

> Source: https://msgpack-python.readthedocs.io/en/latest/api.html
> Library version: msgpack 1.1.2

---

## Top-Level Functions

### `msgpack.packb(o, **kwargs)`

Serialize an object to MessagePack bytes.

**Alias:** `msgpack.dumps()`

**Description:** Pack object `o` and return packed bytes. All keyword arguments are forwarded to the `Packer` class (see below).

---

### `msgpack.unpackb(packed, *, object_hook=None, list_hook=None, use_list=True, raw=False, timestamp=0, strict_map_key=True, unicode_errors=None, object_pairs_hook=None, ext_hook=ExtType, max_str_len=-1, max_bin_len=-1, max_array_len=-1, max_map_len=-1, max_ext_len=-1)`

Deserialize MessagePack bytes to a Python object.

**Alias:** `msgpack.loads()`

**Description:** Unpack `packed` bytes to object. Returns an unpacked object.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `packed` | bytes | (required) | Data to deserialize |
| `object_hook` | callable | None | Called with a dict after unpacking each msgpack map |
| `list_hook` | callable | None | Custom list processing during unpacking |
| `use_list` | bool | True | Return `list` instead of `tuple` for msgpack arrays |
| `raw` | bool | False | Return `bytes` instead of `str` for msgpack strings (raw bytes mode) |
| `timestamp` | int | 0 | How to handle Timestamp type: `0`=`Timestamp` object, `1`=`float`, `2`=`int`, `3`=`datetime` |
| `strict_map_key` | bool | True | Require `str` or `bytes` keys only in dicts |
| `unicode_errors` | str | None | Error handler for UTF-8 decoding (e.g. `'replace'`) |
| `object_pairs_hook` | callable | None | Called with key-value pairs after unpacking a map |
| `ext_hook` | callable | ExtType | Handler for extension types |
| `max_str_len` | int | -1 | Maximum allowed string length (-1 = unlimited) |
| `max_bin_len` | int | -1 | Maximum allowed binary length (-1 = unlimited) |
| `max_array_len` | int | -1 | Maximum allowed array length (-1 = unlimited) |
| `max_map_len` | int | -1 | Maximum allowed map length (-1 = unlimited) |
| `max_ext_len` | int | -1 | Maximum allowed extension type size (-1 = unlimited) |

**Exceptions raised:**
- `ExtraData` — extra bytes remain after unpacking
- `ValueError` — incomplete or invalid data
- `FormatError` — invalid MessagePack format
- `StackError` — data nesting is too deep

---

## `Packer` Class

```python
msgpack.Packer(default=None, *, use_single_float=False, autoreset=True,
               use_bin_type=True, strict_types=False, datetime=False,
               unicode_errors=None, buf_size=0x40000)
```

Serializes Python objects to MessagePack bytes with internal buffering.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `default` | callable | None | Converts unsupported types to supported builtin types; called with the object and should return a serializable value |
| `use_single_float` | bool | False | Use 32-bit (single precision) floats instead of 64-bit (double precision) |
| `autoreset` | bool | True | Clear internal buffer after each `pack()` call; set to `False` for streaming |
| `use_bin_type` | bool | True | Use msgpack binary type for `bytes` and `str8` format for unicode strings |
| `strict_types` | bool | False | If True, reject subclasses of builtin types; tuples will not be serialized as lists |
| `datetime` | bool | False | If True, pack timezone-aware `datetime` objects as msgpack Timestamp type |
| `unicode_errors` | str | None | Error handler for unicode encoding errors |
| `buf_size` | int | 262144 | Internal buffer size in bytes (default: 256 KB) |

**Methods:**

| Method | Description |
|--------|-------------|
| `pack(obj)` | Serialize a single object; returns bytes (or appends to buffer if `autoreset=False`) |
| `pack_array_header(size)` | Write array header for streaming array serialization |
| `pack_map_header(size)` | Write map/dict header for streaming map serialization |
| `pack_map_pairs(pairs)` | Serialize an iterable of `(key, value)` pairs as a msgpack map |
| `pack_ext_type(typecode, data)` | Serialize extension type with given typecode and raw bytes |
| `bytes()` | Return internal buffer contents as a `bytes` object |
| `getbuffer()` | Get a `memoryview` of the internal buffer |
| `reset()` | Clear the internal buffer (useful when `autoreset=False`) |

---

## `Unpacker` Class

```python
msgpack.Unpacker(file_like=None, read_size=0, *, use_list=True, raw=False,
                 timestamp=0, strict_map_key=True, object_hook=None,
                 object_pairs_hook=None, list_hook=None, unicode_errors=None,
                 max_buffer_size=0x6400000, ext_hook=ExtType,
                 max_str_len=-1, max_bin_len=-1, max_array_len=-1,
                 max_map_len=-1, max_ext_len=-1)
```

Streaming deserializer for reading multiple MessagePack objects from bytes or a file-like object.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_like` | object | None | File with a `.read(n)` method; if provided, disables `feed()` |
| `read_size` | int | 0 | Bytes to read per operation (default: `min(16384, max_buffer_size)`) |
| `use_list` | bool | True | Return `list` instead of `tuple` for arrays |
| `raw` | bool | False | Return `bytes` instead of decoded `str` for strings |
| `timestamp` | int | 0 | Timestamp handling mode (0–3, same as `unpackb`) |
| `strict_map_key` | bool | True | Accept only `str` or `bytes` as dict keys |
| `object_hook` | callable | None | Process dicts after unpacking |
| `object_pairs_hook` | callable | None | Process key-value pairs from maps |
| `list_hook` | callable | None | Process lists during unpacking |
| `unicode_errors` | str | None | UTF-8 decoding error handler |
| `max_buffer_size` | int | 104857600 | Max pending bytes in buffer; `0` means `2^32 - 1` (default: 100 MB) |
| `max_array_len` | int | -1 | Max array element count |
| `max_map_len` | int | -1 | Max map pair count |
| `max_str_len` | int | -1 | Max string byte length |
| `max_bin_len` | int | -1 | Max binary byte length |
| `max_ext_len` | int | -1 | Max extension type size |

**Methods:**

| Method | Description |
|--------|-------------|
| `unpack()` | Unpack and return one object |
| `feed(next_bytes)` | Append `next_bytes` to the internal buffer for subsequent `unpack()` calls |
| `read_array_header()` | Read array header, returning the array size; iterate contents with `unpack()` |
| `read_map_header()` | Read map header, returning the number of key-value pairs |
| `read_bytes(nbytes)` | Read a specified number of raw bytes from the stream |
| `skip()` | Read and discard one object, returning `None` |
| `tell()` | Return current byte position in the input stream |

---

## Data Type Mapping

| Python type | msgpack type |
|-------------|--------------|
| `int` (0–127) | positive fixint |
| `int` (−32–−1) | negative fixint |
| `int` (0–255) | uint 8 |
| `int` (0–65535) | uint 16 |
| `int` (0–4294967295) | uint 32 |
| `int` (0–2^64−1) | uint 64 |
| `int` (−128–127) | int 8 |
| `int` (−32768–32767) | int 16 |
| `int` (−2^31–2^31−1) | int 32 |
| `int` (−2^63–2^63−1) | int 64 |
| `str` (≤31 bytes) | fixstr |
| `str` (≤255 bytes) | str 8 |
| `str` (≤65535 bytes) | str 16 |
| `str` (≤4294967295 bytes) | str 32 |
| `bytes` | bin 8 / bin 16 / bin 32 |
| `list` / `tuple` | array |
| `dict` | map |
| `float` | float 32 or float 64 |
| `None` | nil |
| `bool` | true / false |
