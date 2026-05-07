# msgpack API Reference

## Core Functions

### `packb(obj, **kwargs) -> bytes`

Serialize the object `obj` into msgpack bytes.

**Parameters**:
- `obj`: The Python object to serialize (supported types: `int`, `float`, `str`, `bytes`, `list`, `tuple`, `dict`, `None`, `bool`)
- `use_bin_type` (bool, default True): Use msgpack spec 2.0 bin type to encode `bytes`
- `use_single_float` (bool, default False): Use single precision (4 bytes) instead of double precision (8 bytes) for floats

**Returns**: Serialized data as `bytes`

**Examples**:
```python
import msgpack

msgpack.packb(42)           # b'*'
msgpack.packb(128)          # b'\xcc\x80'
msgpack.packb("hello")      # b'\xa5hello'
msgpack.packb([1, 2, 3])    # b'\x93\x01\x02\x03'
```

### `unpackb(packed, **kwargs) -> object`

Deserialize msgpack bytes `packed` into a Python object.

**Parameters**:
- `packed`: msgpack data as `bytes`
- `raw` (bool, default False): If True, return msgpack raw type as `bytes` instead of `str`
- `strict_map_key` (bool, default True): If True, only allow `str` or `bytes` as map keys

**Returns**: The deserialized Python object

**Exceptions**:
- `ExtraData`: `packed` contains extra trailing bytes
- `FormatError`: `packed` is not valid msgpack data
- `ValueError`: `packed` is incomplete

**Examples**:
```python
msgpack.unpackb(b'\xcc\x80')        # 128
msgpack.unpackb(b'\xa5hello', raw=False)  # 'hello'
```

## Supported Integer Range

The msgpack library supports the following range for Python `int`:
- Positive integers: `[0, 2^64 - 1]` (i.e., `[0, 18446744073709551615]`)
- Negative integers: `[-2^63, -1]` (i.e., `[-9223372036854775808, -1]`)

Values outside this range raise `OverflowError`.

## Usage Examples

```python
import msgpack

# Basic roundtrip
data = {"user_id": 40000, "score": -129, "name": "Alice"}
packed = msgpack.packb(data)
result = msgpack.unpackb(packed, raw=False)
assert result == data  # Should be True

# Streaming serialization
packer = msgpack.Packer()
items = [packb(i) for i in range(1000)]
```
