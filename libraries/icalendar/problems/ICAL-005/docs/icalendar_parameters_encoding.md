# icalendar Library: Property Parameters and Content Line Encoding

## Overview

The `icalendar` library (v7.0.3) implements RFC 5545 (Internet Calendaring and
Scheduling Core Object Specification) for Python. This document covers the
parameter encoding/decoding system and the content line folding mechanism,
which together form the serialization layer for iCalendar data.

iCalendar uses a text-based format where each property is represented as a
content line with the general form:

```
name;param1=value1;param2=value2:property-value
```

## Content Line Folding (RFC 5545 Section 3.1)

### Line Length Limit

RFC 5545 specifies that content lines SHOULD NOT be longer than **75 octets**,
excluding the line break (CRLF). Long content lines are split using a folding
technique: a CRLF immediately followed by a single whitespace character (SPACE
or HTAB).

### Folding and Unfolding

**Folding** breaks a long line into multiple shorter lines:

```
ATTENDEE;CN=Very Long Name;MEMBER="mailto:member1@very-long-domain-example.
 com","mailto:member2@another-domain-example.com":mailto:user@example.com
```

Each continuation line starts with a single space (or tab). The limit of
75 octets applies to each physical line independently, meaning:

- The **first line** must be at most 75 octets (including name, parameters,
  colon, and value content up to the fold point)
- Each **continuation line** must be at most 75 octets (including the leading
  space/tab character)

**Unfolding** reverses the process by removing CRLF followed by whitespace,
reconstructing the original long line.

### ASCII vs Non-ASCII Content

The library handles folding differently for ASCII and non-ASCII content:

- **ASCII content**: Characters are always 1 byte, so character count equals
  byte count. Folding can use simple string slicing.
- **Non-ASCII content** (e.g., UTF-8 accented characters): Characters may be
  2-4 bytes. Folding must track byte count to avoid splitting in the middle of
  a multi-byte character.

Example with non-ASCII:

```
SUMMARY;LANGUAGE=de:Besprechung mit Ölgesellschaft über Geschäftsmodell
 für Klimaschutzprojekte
```

The `ö`, `ü`, and `ä` characters are each 2 bytes in UTF-8, so the line's
byte length differs from its character count.

## Property Parameters (RFC 5545 Section 3.2)

### Parameter Syntax

Parameters modify properties and appear between the property name and the
colon delimiter:

```
property-name;PARAM1=value;PARAM2=value:property-value
```

### Quoting Rules

Parameter values must be quoted (enclosed in double-quotes) when they contain:

- Commas (`,`)
- Semicolons (`;`)
- Colons (`:`)

Certain parameters MUST always have their values quoted, regardless of content:

- `ALTREP` — alternate text representation URI
- `DELEGATED-FROM` — delegating calendar user addresses
- `DELEGATED-TO` — delegated calendar user addresses
- `DIR` — directory entry reference URI
- `MEMBER` — group membership calendar user addresses
- `SENT-BY` — acting-on-behalf-of calendar user address

The `CN` (Common Name) parameter is quoted when it contains a space or
single-quote character.

### Multi-Value Parameters

Some parameters support multiple values separated by commas:

```
ATTENDEE;MEMBER="mailto:group1@example.com","mailto:group2@example.com",
 "mailto:group3@example.com":mailto:user@example.com
```

Multi-value parameters include:

- **MEMBER**: Group/list membership (comma-separated list of quoted cal-addresses)
- **DELEGATED-FROM**: Delegating users (comma-separated list of quoted cal-addresses)
- **DELEGATED-TO**: Delegates (comma-separated list of quoted cal-addresses)

When parsing multi-value parameters, the library should produce a **list** of
individual values, not a single concatenated string:

```python
from icalendar.parser.parameter import Parameters

params = Parameters.from_ical(
    'MEMBER="mailto:a@x.com","mailto:b@x.com"'
)
# params["MEMBER"] should be:
# ['mailto:a@x.com', 'mailto:b@x.com']  (list of 2 strings)
# NOT:
# 'mailto:a@x.com'  (single string, first value only)
```

### Single vs Multi-Value Distinction

The parameter parser distinguishes between single-value and multi-value
parameters based on the number of comma-separated values found:

- **Zero values**: The raw string is stored directly
- **One value**: The single string is stored (not wrapped in a list)
- **Two or more values**: A list of strings is stored

This distinction is important for consumers that check the type of the
parameter value to determine if it's a single address or a group.

## RFC 6868: Parameter Value Encoding (Caret Escaping)

### Purpose

RFC 6868 defines a mechanism for encoding characters that cannot appear
directly in parameter values. It uses the caret (`^`) as an escape character.

### Escape Sequences

| Character | Escape Sequence | Description |
|-----------|----------------|-------------|
| `^` (caret) | `^^` | Literal caret |
| `"` (double-quote) | `^'` | Double-quote (forbidden in param values) |
| newline | `^n` | Line break |

### Escaping Rules

The escape function processes the input string and replaces special characters
with their escape sequences. The **order of replacement matters**:

1. `^` must be escaped to `^^` **before** other escape sequences are applied,
   to avoid double-escaping. For example, if `"` were escaped first to `^'`,
   then the `^` in `^'` would be incorrectly escaped again to `^^'`.

2. `"` is escaped to `^'`
3. Newlines (`\n`, `\r`, `\r\n`) are escaped to `^n`

### Unescaping Rules (Reverse)

The unescape function reverses the process:

1. `^^` → `^`
2. `^n` → (system newline)
3. `^'` → `"`

### Roundtrip Guarantee

For any parameter value string `s`, the following must hold:

```python
from icalendar.parser.parameter import rfc_6868_escape, rfc_6868_unescape

assert rfc_6868_unescape(rfc_6868_escape(s)) == s
```

This roundtrip property is essential for preserving parameter values through
serialization and parsing.

### Example

```python
from icalendar.parser.parameter import Parameters

# CN with special characters
params = Parameters()
params["CN"] = "John^Doe"  # contains caret
ical = params.to_ical()
# Should produce: b'CN=John^^Doe'

parsed = Parameters.from_ical(ical.decode())
assert parsed["CN"] == "John^Doe"  # roundtrip preserved
```

## Content Line Parsing

### Structure

A content line has three parts: **name**, **parameters**, and **value**:

```
ATTENDEE;CN="John Doe";ROLE=REQ-PARTICIPANT:mailto:john@example.com
^name    ^-- parameters --^                 ^-- value --^
```

The parser splits on:
- First unquoted `;` or `:` → separates name from parameters/value
- First unquoted `:` → separates parameters from value

### Parameter Parsing Flow

1. Split content line into name, parameter string, and value
2. Split parameter string on unquoted `;` to get individual parameters
3. For each parameter, split on `=` to get key and value
4. For the value, split on unquoted `,` to get individual values
5. Unquote quoted values (strip `"` delimiters)
6. Apply RFC 6868 unescaping to each value

### Parameter Serialization Flow

1. For each parameter key-value pair:
   a. Apply RFC 6868 escaping to the value
   b. Apply quoting (add `"` delimiters) if the value contains special
      characters or the parameter requires always-quoting
   c. For multi-value parameters, join values with `,`
2. Join all parameters with `;`
3. Combine with name and value: `name;params:value`

## API Reference

### Parameters Class

```python
from icalendar.parser.parameter import Parameters

# Create and serialize
params = Parameters()
params["CN"] = "John Doe"
params["ROLE"] = "REQ-PARTICIPANT"
params["MEMBER"] = ["mailto:group1@x.com", "mailto:group2@x.com"]
ical_bytes = params.to_ical()
# b'CN="John Doe";MEMBER="mailto:group1@x.com","mailto:group2@x.com";ROLE=REQ-PARTICIPANT'

# Parse
parsed = Parameters.from_ical(ical_bytes.decode())
```

### vCalAddress with Parameters

```python
from icalendar import Event
from icalendar.prop import vCalAddress

# Create an attendee with parameters
addr = vCalAddress.new(
    "john@example.com",
    cn="John Doe",
    role="REQ-PARTICIPANT"
)

# Set multi-value parameters
addr.params["MEMBER"] = [
    "mailto:team-a@example.com",
    "mailto:team-b@example.com"
]
addr.params["DELEGATED-TO"] = [
    "mailto:alice@example.com",
    "mailto:bob@example.com"
]

# Add to event and serialize
event = Event()
event.add("attendee", addr)
ical_bytes = event.to_ical()

# Parse back
from icalendar import Calendar
cal = Calendar.from_ical(b"BEGIN:VCALENDAR\r\n" + ical_bytes + b"END:VCALENDAR\r\n")
for comp in cal.walk("VEVENT"):
    att = comp["attendee"]
    print(att.params["MEMBER"])       # list of member addresses
    print(att.params["DELEGATED-TO"]) # list of delegate addresses
```

### Content Line Folding

```python
from icalendar.parser.string import foldline

# Fold a long line
line = "SUMMARY:" + "A" * 100
folded = foldline(line)
# Result: 'SUMMARY:AAAAAA...AAAA\r\n AAAA...AAAA\r\n AAAA...'
# Each segment <= 74 characters (75 bytes including continuation space)
```

### RFC 6868 Escaping

```python
from icalendar.parser.parameter import rfc_6868_escape, rfc_6868_unescape

# Escape special characters in parameter values
escaped = rfc_6868_escape('Hello ^ "World"')
# Result: 'Hello ^^ ^\'World^\\''

# Unescape
original = rfc_6868_unescape(escaped)
# Result: 'Hello ^ "World"'
```

## Key Invariants

The following properties should hold for any valid iCalendar data:

1. **Parameter roundtrip**: `from_ical(to_ical(params))` preserves all
   parameter keys, values, and value types (string vs list)

2. **RFC 6868 roundtrip**: `unescape(escape(s)) == s` for any string `s`

3. **Line length conformance**: Every line in `to_ical()` output is at most
   75 octets (UTF-8 encoded), excluding the CRLF line terminator

4. **Content line roundtrip**: `from_ical(to_ical(component))` preserves all
   properties and their parameter values

5. **Multi-value preservation**: Parameters with multiple values (MEMBER,
   DELEGATED-TO, DELEGATED-FROM) must be preserved as lists through
   serialization and parsing, not collapsed to single values
