# msgpack Integer Format Specification

msgpack uses compact variable-length encoding for integers, automatically selecting the smallest encoding type based on the value's range.

## Encoding Format Overview

| Format Name     | Marker Byte | Data Length | Valid Range                     |
|-----------------|-------------|-------------|---------------------------------|
| positive fixint | 0x00-0x7F   | 0 bytes     | [0, 127]                       |
| negative fixint | 0xE0-0xFF   | 0 bytes     | [-32, -1]                      |
| uint 8          | 0xCC        | 1 byte      | [0, 255]                       |
| uint **16**     | 0xCD        | **2 bytes** | **[0, 65535]** (unsigned 16-bit)|
| uint 32         | 0xCE        | 4 bytes     | [0, 4294967295]                |
| uint 64         | 0xCF        | 8 bytes     | [0, 2^64-1]                    |
| int 8           | 0xD0        | 1 byte      | [-128, 127]                    |
| int 16          | 0xD1        | 2 bytes     | [-32768, 32767] (signed 16-bit)|
| int 32          | 0xD2        | 4 bytes     | [-2^31, 2^31-1]                |
| int 64          | 0xD3        | 8 bytes     | [-2^63, 2^63-1]                |

**Note**: The packer automatically selects the smallest encoding based on the value, for example:
- `256` -> uint 16 (because > 255, but <= 65535)
- `65536` -> uint 32 (because > 65535)
- `-129` -> int 16 (because < -128, but >= -32768)

## Important Semantic Properties

### Roundtrip Invariant (Core Property)

For any valid integer `n`, serializing and then deserializing should recover the original value:
```
unpackb(packb(n)) == n
```

This applies to the entire integer range supported by msgpack: `[-(2^63), 2^64-1]`.

### The Special Nature of uint16

uint16 is an **unsigned** 16-bit integer format representing the range [0, 65535].
In contrast, int16 is a **signed** 16-bit integer format representing the range [-32768, 32767].

The key difference between the two formats lies in the handling of values in [32768, 65535]:
- As unsigned 16-bit, 0x8000 = **32768**
- As signed 16-bit, 0x8000 = **-32768** (the high bit is the sign bit)

Any correct msgpack implementation must distinguish between these two formats.

## Integer Distribution in Practice

Below is the actual selection logic of the packer (pseudocode):

```
n in [0, 127]              -> positive fixint (1 byte)
n in [-32, -1]             -> negative fixint (1 byte)
n in [128, 255]            -> uint 8  (2 bytes)
n in [256, 65535]          -> uint 16 (3 bytes, including marker byte)
n in [65536, 4294967295]   -> uint 32 (5 bytes, including marker byte)
n in [4294967296, 2^64-1]  -> uint 64 (9 bytes, including marker byte)
n in [-128, -33]           -> int 8  (2 bytes)
n in [-32768, -129]        -> int 16 (3 bytes)
n in [-2^31, -32769]       -> int 32 (5 bytes)
n in [-2^63, -2^31-1]      -> int 64 (9 bytes)
```
