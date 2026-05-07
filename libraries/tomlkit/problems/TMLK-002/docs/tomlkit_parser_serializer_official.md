# tomlkit 0.14.0 - Parser and Serializer Documentation

## Overview

tomlkit is a **style-preserving TOML parser and serializer** for Python. Unlike standard TOML parsers, tomlkit preserves all formatting, comments, and whitespace from the original document, enabling lossless roundtrip: `tomlkit.dumps(tomlkit.loads(s)) == s`.

tomlkit implements the [TOML v1.0.0 specification](https://toml.io/en/v1.0.0).

## Core API

### `tomlkit.loads(s: str) -> TOMLDocument`

Parse a TOML string and return a `TOMLDocument` (which behaves like a dict).

```python
import tomlkit

doc = tomlkit.loads("""
[server]
host = "localhost"
port = 8080
""")
assert doc["server"]["host"] == "localhost"
```

### `tomlkit.dumps(doc: TOMLDocument) -> str`

Serialize a `TOMLDocument` back to a TOML string, preserving the original formatting.

```python
s = '[server]\nhost = "localhost"\nport = 8080\n'
assert tomlkit.dumps(tomlkit.loads(s)) == s
```

### `tomlkit.load(fp) -> TOMLDocument`

Parse TOML from a file-like object.

### `tomlkit.dump(doc, fp)`

Write a `TOMLDocument` to a file-like object.

## TOML Data Types

### Strings

TOML has four string types:

1. **Basic strings** (`"..."`) - Support escape sequences like `\n`, `\t`, `\\`, `\"`, `\uXXXX`, `\UXXXXXXXX`.
2. **Literal strings** (`'...'`) - No escape processing; what you see is what you get.
3. **Multiline basic strings** (`"""..."""`) - Like basic strings but can span multiple lines. A newline immediately following the opening delimiter is trimmed. A `\` at the end of a line trims the newline and all subsequent whitespace up to the next non-whitespace character (line ending backslash).
4. **Multiline literal strings** (`'''...'''`) - Like literal strings but can span multiple lines. A newline immediately following the opening delimiter is trimmed.

#### Multiline String Edge Cases

The TOML spec allows up to 2 additional quote characters to appear immediately before the closing delimiter in multiline strings:

```toml
# Multiline literal: up to 2 extra single quotes allowed before closing '''
key1 = '''text''''     # value = "text'"   (4 consecutive ' = 1 quote + closing ''')
key2 = '''text'''''    # value = "text''"  (5 consecutive ' = 2 quotes + closing ''')

# Multiline basic: up to 2 extra double quotes allowed before closing """
key3 = """text"""""    # value = 'text""'  (5 consecutive " = 2 quotes + closing """)
key4 = """text""""     # value = 'text"'   (4 consecutive " = 1 quote + closing """)

# 6 or more consecutive delimiters is an error
# key5 = '''text''''''  # ERROR
```

This allows embedding quote characters at the end of multiline strings without using escape sequences.

### Integers

TOML supports decimal, hexadecimal (`0x`), octal (`0o`), and binary (`0b`) integers. Underscores between digits are allowed for readability: `1_000_000`.

### Floats

Standard floating-point values, plus `inf`, `+inf`, `-inf`, `nan`, `+nan`, `-nan`. Underscores between digits are allowed.

### Booleans

`true` and `false` (lowercase only).

### Date-Time Types

tomlkit follows RFC 3339 for date-time values. All date-time types in parsed documents are represented as Python `datetime`, `date`, or `time` objects with their actual values accessible as attributes.

#### Offset Date-Time

Full date-time with timezone offset:

```toml
# UTC (Z suffix)
dt1 = 2024-01-15T10:30:00Z

# Positive offset
dt2 = 2024-01-15T10:30:00+05:00

# Negative offset
dt3 = 2024-01-15T10:30:00-08:00

# Non-whole-hour offset (e.g., India +05:30, Nepal +05:45, Iran +03:30)
dt4 = 2024-01-15T10:30:00+05:30
dt5 = 2024-01-15T10:30:00+05:45
dt6 = 2024-01-15T10:30:00+09:45
```

The timezone offset format is `+HH:MM` or `-HH:MM`. The `HH` ranges from 00-23, `MM` from 00-59.

**Parsed value**: The `utcoffset()` method of the parsed datetime returns a `timedelta` representing the exact offset. For `+05:30`, this is `timedelta(hours=5, minutes=30)`.

#### Fractional Seconds

TOML supports fractional seconds with arbitrary precision:

```toml
# Various precisions of fractional seconds
dt1 = 2024-01-15T10:30:00.5Z         # 0.5 seconds = 500000 microseconds
dt2 = 2024-01-15T10:30:00.12Z        # 0.12 seconds = 120000 microseconds
dt3 = 2024-01-15T10:30:00.123Z       # 0.123 seconds = 123000 microseconds
dt4 = 2024-01-15T10:30:00.1234Z      # 0.1234 seconds = 123400 microseconds
dt5 = 2024-01-15T10:30:00.12345Z     # 0.12345 seconds = 123450 microseconds
dt6 = 2024-01-15T10:30:00.123456Z    # 0.123456 seconds = 123456 microseconds
```

**Important**: Fractional seconds are interpreted as decimal fractions of a second. A single digit `.5` means 0.5 seconds = 500,000 microseconds, NOT 5 microseconds. The fractional value is conceptually **left-aligned**: `.5` = `.500000`, `.12` = `.120000`, `.123` = `.123000`.

The parsed `datetime` object's `microsecond` attribute reflects this: `.5` yields `microsecond=500000`.

#### Local Date-Time (no timezone)

```toml
dt = 2024-01-15T10:30:00
```

The parsed datetime has `tzinfo=None`.

#### Local Date

```toml
d = 2024-01-15
```

Parsed as a Python `date` object.

#### Local Time

```toml
t = 10:30:00
t_frac = 10:30:00.5    # 500000 microseconds
```

Parsed as a Python `time` object. Fractional seconds follow the same rules as for date-times.

### Arrays

```toml
arr = [1, 2, 3]
mixed = [1, "two", 3.0]
nested = [[1, 2], [3, 4]]
```

### Tables

```toml
[table]
key = "value"

[table.nested]
key = "nested value"

# Dotted keys in tables
[fruit]
apple.color = "red"
apple.taste = "sweet"
```

### Inline Tables

Inline tables provide a compact syntax for tables on a single line:

```toml
point = {x = 1, y = 2}
animal = {type.name = "pug"}
```

**TOML v1.0.0 rules for inline tables**:
- Inline tables are intended for small, self-contained data
- They must appear on a single line
- **No trailing commas are allowed**: `{a = 1, b = 2}` is valid, `{a = 1, b = 2,}` is NOT valid
- No newlines are allowed inside inline tables (in TOML 1.0)

**Roundtrip property**: For any valid TOML string `s` containing inline tables, `tomlkit.dumps(tomlkit.loads(s))` should produce the exact same string. The serialized output must also be valid TOML that can be re-parsed.

### Array of Tables (AoT)

```toml
[[products]]
name = "Hammer"
sku = 738594937

[[products]]
name = "Nail"
sku = 284758393
```

## Style Preservation (Roundtrip)

tomlkit's key feature is **style-preserving roundtrip**. This means:

1. Comments are preserved
2. Whitespace and indentation are preserved
3. Key quoting style is preserved (bare vs quoted)
4. String type is preserved (basic vs literal, single vs multiline)
5. Number format is preserved (hex, octal, binary, underscores)
6. Date-time format is preserved (the exact raw string representation)
7. Inline table formatting is preserved

**Core invariant**: For any valid TOML string `s`:
```python
assert tomlkit.dumps(tomlkit.loads(s)) == s
```

This invariant must hold for all valid TOML documents.

## Programmatic Document Creation

### Creating Values

```python
from tomlkit import item, inline_table, table, array

# Create an inline table
it = inline_table()
it.append("x", 1)
it.append("y", 2)
# it.as_string() → '{x = 1, y = 2}'

# Create from Python objects
from datetime import datetime, timezone, timedelta
dt = datetime(2024, 1, 15, 10, 30, 0, 500000, tzinfo=timezone.utc)
doc = tomlkit.document()
doc.append("dt", dt)
```

### String Creation

```python
from tomlkit.items import String, StringType

# Create a basic string
s = String.from_raw("hello world")
# s.as_string() → '"hello world"'

# Create with escape sequences
s = String.from_raw("hello\nworld")
# s.as_string() → '"hello\\nworld"'
```

## Internal Architecture

tomlkit's internal architecture consists of several layers:

1. **Source** (`source.py`) - Character-by-character input reader with state management
2. **Parser** (`parser.py`) - Recursive descent parser that builds the document tree
3. **Items** (`items.py`) - Rich item types (String, Integer, DateTime, Table, etc.) that wrap Python values and preserve formatting
4. **Container** (`container.py`) - Ordered dict-like structure that maintains document ordering
5. **Utils** (`_utils.py`) - RFC 3339 parsing, string escaping utilities

### Key Internal Functions

- `parse_rfc3339(string)` in `_utils.py` - Parses RFC 3339 date/time strings into Python datetime/date/time objects. Handles fractional seconds, timezone offsets, and various date-time formats.

- `escape_string(s, escape_sequences)` in `_utils.py` - Converts Python strings to TOML-escaped representations for basic strings.

- `Parser._parse_string(delim)` in `parser.py` - Parses all four string types (basic, literal, multiline basic, multiline literal). Handles escape sequences, line continuations, and closing delimiter detection.

- `InlineTable.as_string()` in `items.py` - Serializes an inline table back to TOML format, including proper comma placement between key-value pairs.

## Error Handling

tomlkit raises specific exceptions for parsing errors:

- `ParseError` - General parse error
- `UnexpectedCharError` - Unexpected character encountered
- `InvalidDateTimeError` - Invalid date-time format
- `EmptyKeyError` - Empty key encountered
- `KeyAlreadyPresent` - Duplicate key in table

All valid TOML documents should parse without errors, and `dumps()` output should always produce valid TOML that can be re-parsed.
