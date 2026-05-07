# tomlkit Multiline String API Reference

## Overview

**tomlkit** is a style-preserving TOML parser and serializer for Python. It
maintains comments, formatting, and whitespace through parse-edit-dump cycles.
This document covers the multiline string handling capabilities of tomlkit 0.14.0.

TOML defines four string types:

| Type | Delimiter | Escape Processing | Multiline |
|------|-----------|-------------------|-----------|
| Basic | `"..."` | Yes (`\n`, `\t`, `\"`, `\\`, etc.) | No |
| Multi-line Basic (MLB) | `"""..."""` | Yes (same as basic + line continuation) | Yes |
| Literal | `'...'` | No (content is taken as-is) | No |
| Multi-line Literal (MLL) | `'''...'''` | No (content is taken as-is) | Yes |

---

## String Types (`tomlkit.items.StringType`)

The `StringType` enum defines the four TOML string types:

```python
class StringType(Enum):
    SLB = '"'       # Single Line Basic
    MLB = '"""'     # Multi Line Basic
    SLL = "'"       # Single Line Literal
    MLL = "'''"     # Multi Line Literal
```

### Properties

- **`value`**: The full delimiter string (e.g., `'"""'` for MLB, `"'''"` for MLL).
- **`unit`**: The single delimiter character (e.g., `'"'` for MLB, `"'"` for MLL).
- **`is_basic()`**: True for SLB and MLB.
- **`is_literal()`**: True for SLL and MLL.
- **`is_multiline()`**: True for MLB and MLL.
- **`is_singleline()`**: True for SLB and SLL.

### `select(literal=False, multiline=False)`

Factory method to select a string type:

```python
StringType.select(literal=False, multiline=False)  # SLB
StringType.select(literal=False, multiline=True)   # MLB
StringType.select(literal=True, multiline=False)    # SLL
StringType.select(literal=True, multiline=True)     # MLL
```

### `toggle()`

Converts between single-line and multi-line variants:

```python
StringType.SLB.toggle()  # -> MLB
StringType.MLB.toggle()  # -> SLB
StringType.SLL.toggle()  # -> MLL
StringType.MLL.toggle()  # -> SLL
```

### Escape Sequences

**`escaped_sequences`** — Characters/sequences that must be escaped in basic
strings:

For **MLB**: All control characters except `\n` and `\r`, plus `\\` (backslash)
and `"""` (triple double-quote). Newlines and carriage returns are allowed
unescaped in multiline basic strings.

For **MLL**: Empty set. Literal strings do not process escape sequences.

**`invalid_sequences`** — Characters/sequences that are forbidden in the string:

For **SLL**: Control characters (except tab) plus `'` (single quote).

For **MLL**: Control characters (except tab, newline, carriage return) plus
`'''` (triple single-quote). The triple single-quote is forbidden because it
would prematurely close the string. Content with `'''` cannot be represented
as an MLL string.

For **SLB** and **MLB**: No forbidden sequences (empty set). All characters can
be represented using escape sequences.

---

## String Item (`tomlkit.items.String`)

### Constructor

```python
String(t: StringType, value: str, original: str, trivia: Trivia)
```

- **`t`**: The string type (SLB, MLB, SLL, MLL).
- **`value`**: The decoded Python string value.
- **`original`**: The raw TOML representation (between delimiters, unquoted).
  For basic strings, this includes escape sequences (e.g., `\\n` for newline).
  For literal strings, this is identical to `value`.
- **`trivia`**: Metadata (indent, comment, trailing whitespace).

### `from_raw(value, type_=StringType.SLB, escape=True)`

Creates a `String` from a Python string value:

```python
String.from_raw("hello world")
# -> String(SLB, "hello world", "hello world", Trivia())

String.from_raw("hello\nworld", type_=StringType.MLB)
# -> String(MLB, "hello\nworld", "hello\nworld", Trivia())
# as_string: '"""hello\nworld"""'

String.from_raw("hello\nworld", type_=StringType.MLL)
# -> String(MLL, "hello\nworld", "hello\nworld", Trivia())
# as_string: "'''hello\nworld'''"
```

**Validation**: `from_raw` checks the `invalid_sequences` of the target type.
If the value contains any forbidden sequence, `InvalidStringError` is raised.
For example, trying to create an MLL string with `'''` in the content will fail.

**Escaping**: When `escape=True` (default) and the type has `escaped_sequences`,
the value is processed through `escape_string()` to produce the `original` field.
For MLB strings, this escapes control characters, backslashes, and embedded
triple double-quotes (`"""`).

### `as_string()`

Returns the TOML representation including delimiters:

```python
s = String(StringType.MLB, "hello\nworld", "hello\nworld", Trivia())
s.as_string()  # '"""hello\nworld"""'
```

The format is: `{opening_delimiter}{original}{closing_delimiter}`

Both opening and closing delimiters use the full `StringType.value` —
for MLB that is `"""`, for MLL that is `'''`.

**Invariant**: For any valid String item `s`, the output of `as_string()` should
be valid TOML that can be reparsed to recover the original value:

```python
s = String.from_raw(content, type_=some_type)
reparsed = tomlkit.parse(f"key = {s.as_string()}\n")
assert str(reparsed["key"]) == content
```

### String Concatenation (`__add__`)

Strings can be concatenated using `+`:

```python
s1 = String.from_raw("hello\n", type_=StringType.MLB)
s2 = "world"
result = s1 + s2
# result is a String(MLB, "hello\nworld", "hello\nworld", Trivia())
```

The concatenation preserves the string type and produces a new String with
concatenated `value` and `original` fields.

---

## Public API Functions

### `tomlkit.string(raw, *, literal=False, multiline=False, escape=True)`

Creates a String item with the specified type:

```python
tomlkit.string("hello\nworld", multiline=True)
# MLB string: """hello\nworld"""

tomlkit.string("hello\nworld", literal=True, multiline=True)
# MLL string: '''hello\nworld'''

tomlkit.string("path\\to\\file", literal=True)
# SLL string: 'path\to\file' (backslashes are literal)
```

### `tomlkit.parse(string)` / `tomlkit.loads(string)`

Parses a TOML string into a `TOMLDocument`:

```python
doc = tomlkit.parse('key = """hello\nworld"""\n')
str(doc["key"])  # "hello\nworld"
```

### `tomlkit.dumps(data)`

Serializes a TOMLDocument back to a TOML string:

```python
output = tomlkit.dumps(doc)
# 'key = """hello\nworld"""\n'
```

**Roundtrip invariant**: `tomlkit.parse(tomlkit.dumps(doc))` should produce
a document with the same values as `doc`.

---

## Multiline Basic String (MLB) Specifics

### Leading Newline Trimming

Per the TOML specification, a newline immediately following the opening `"""`
delimiter is trimmed:

```toml
key = """
hello
world"""
```

Parsed value: `"hello\nworld"` (the newline after `"""` is removed).

Without the leading newline:

```toml
key = """hello
world"""
```

Parsed value: `"hello\nworld"` (same result; no leading newline to trim).

### Line-Ending Backslash (Line Continuation)

In MLB strings, a backslash at the end of a line trims the newline and all
following whitespace (including additional newlines) up to the next
non-whitespace character:

```toml
key = """\
  hello \
  world\
  """
```

Parsed value: `"hello world"` — all newlines and leading whitespace after each
`\` are removed, joining the text together.

This is useful for writing long strings across multiple lines without including
the newlines in the value.

**Important**: The line continuation only applies in MLB strings, not in MLL.
In MLL strings, backslashes are literal characters.

### Embedded Triple Quotes

Up to two consecutive double-quote characters can appear inside an MLB string
without any issues:

```toml
key = """hello ""world"""""
```

Parsed value: `'hello ""world""'` (the last 5 quotes are: 2 content quotes +
closing `"""`).

However, three or more consecutive double-quotes in the VALUE must be escaped.
The `escape_string()` function handles this by using the `_compact_escapes`
mapping:

- `"""` in content → `""\"` in TOML output (two literal quotes + one escaped
  quote)
- This is then reconstructed during parsing: `""` + `\"` → `"""`

### Control Character Escaping in MLB

MLB strings support all the standard TOML escape sequences:

| Escape | Character |
|--------|-----------|
| `\b` | Backspace (U+0008) |
| `\t` | Tab (U+0009) |
| `\n` | Newline (U+000A) |
| `\f` | Form feed (U+000C) |
| `\r` | Carriage return (U+000D) |
| `\"` | Double quote (U+0022) |
| `\\` | Backslash (U+005C) |
| `\uXXXX` | Unicode (4 hex digits) |
| `\UXXXXXXXX` | Unicode (8 hex digits) |

Control characters other than tab, newline, and carriage return must be escaped.

---

## Multiline Literal String (MLL) Specifics

### No Escape Processing

MLL strings (`'''...'''`) do not process any escape sequences. Backslashes,
double quotes, and all other characters are taken literally:

```toml
key = '''hello\nworld'''
```

Parsed value: `"hello\\nworld"` (the `\n` is two literal characters: backslash
and `n`, not a newline).

### Leading Newline Trimming

Same as MLB — a newline immediately after the opening `'''` is trimmed:

```toml
key = '''
hello
world'''
```

Parsed value: `"hello\nworld"`.

### Forbidden Content

MLL strings cannot contain the sequence `'''` (triple single-quote), because
it would close the string. There is no escape mechanism for this in literal
strings.

Up to two consecutive single-quotes are allowed:

```toml
key = '''hello ''world'''
```

Parsed value: `"hello ''world"`.

But three consecutive single-quotes would close the string prematurely:

```toml
key = '''hello'''world'''   # INVALID — parses as "hello" then garbage
```

The `from_raw()` method enforces this restriction via `invalid_sequences`.

---

## Escape String Function (`tomlkit._utils.escape_string`)

The `escape_string()` function processes a raw Python string value and produces
a TOML-safe escaped form suitable for inclusion between delimiters.

### Behavior

1. Scans the input string for characters/sequences that need escaping.
2. For each found sequence, replaces it with the appropriate escape form:
   - Common escapes use `_compact_escapes` mapping (e.g., `\n` → `\\n`,
     `"""` → `""\\"`).
   - Uncommon control characters use Unicode escapes (`\\uXXXX`).
3. Returns the escaped string.

### The `_compact_escapes` Mapping

Maps raw characters/sequences to their TOML escape forms:

| Raw | TOML Escape | Description |
|-----|-------------|-------------|
| `\b` (U+0008) | `\\b` | Backspace |
| `\t` (U+0009) | `\\t` | Tab |
| `\n` (U+000A) | `\\n` | Newline |
| `\f` (U+000C) | `\\f` | Form feed |
| `\r` (U+000D) | `\\r` | Carriage return |
| `"` (U+0022) | `\\"` | Double quote |
| `\\` (U+005C) | `\\\\` | Backslash |
| `"""` | `""\\"` | Triple double-quote (for MLB) |

The triple-quote mapping is critical for MLB strings: when the raw content
contains `"""`, it must be escaped as `""\"` (two literal quotes + one escaped
quote) to avoid prematurely closing the string.

---

## Trivia and Style Preservation

### The `Trivia` Class

Each TOML item carries `Trivia` metadata:

```python
@dataclass
class Trivia:
    indent: str = ""       # Whitespace before the value
    comment_ws: str = ""   # Whitespace between value and comment
    comment: str = ""      # Comment text (starting with #)
    trail: str = "\n"      # Trailing newline
```

### Value Replacement and Trivia Copying

When replacing a value using `doc["key"] = new_value` (via `Container._replace_at`):

1. The old item's `trivia.indent` is copied to the new item.
2. The old item's `trivia.comment_ws` and `trivia.comment` are used if the new
   item has none.
3. The old item's `trivia.trail` is always copied to the new item.

This ensures that replacing a value preserves the document's formatting (indent
level, comments, trailing whitespace).

### Rendering

The `Container._render_simple_item()` method produces the final TOML output for
a key-value pair:

```
{indent}{key}{separator}{as_string()}{comment_ws}{comment}{trail}
```

For a multiline string, `as_string()` contains embedded newlines:

```
key = """hello
world"""
```

The `trail` (typically `"\n"`) follows the closing delimiter on the same line.

---

## Common Patterns and Invariants

### Roundtrip Invariant

For any valid TOML document `s`:

```python
assert tomlkit.dumps(tomlkit.parse(s)) == s
```

For programmatically created values:

```python
s = String.from_raw(content, type_=some_type)
doc = tomlkit.document()
doc.add("key", s)
output = tomlkit.dumps(doc)
reparsed = tomlkit.parse(output)
assert str(reparsed["key"]) == content
```

### Type Safety Invariant

`from_raw()` should reject content that cannot be validly represented in the
target string type:

```python
# Should raise: MLL cannot contain '''
String.from_raw("a'''b", type_=StringType.MLL)  # InvalidStringError
```

### Delimiter Invariant

`as_string()` must produce output with matching opening and closing delimiters:

```python
s = String.from_raw("hello\nworld", type_=StringType.MLB)
result = s.as_string()
assert result.startswith('"""')
assert result.endswith('"""')

s = String.from_raw("hello\nworld", type_=StringType.MLL)
result = s.as_string()
assert result.startswith("'''")
assert result.endswith("'''")
```

### Line Continuation Invariant (MLB only)

In MLB strings, a backslash followed by a newline and optional whitespace should
trim all of that whitespace:

```python
doc = tomlkit.parse('key = """\nhello \\\n  world"""\n')
assert str(doc["key"]) == "hello world"
```

### Escape Invariant (MLB only)

All control characters and special sequences in MLB strings must be properly
escaped so that the roundtrip value matches:

```python
content = 'text with """ triple quotes'
s = String.from_raw(content, type_=StringType.MLB)
doc = tomlkit.document()
doc.add("key", s)
reparsed = tomlkit.parse(tomlkit.dumps(doc))
assert str(reparsed["key"]) == content
```
