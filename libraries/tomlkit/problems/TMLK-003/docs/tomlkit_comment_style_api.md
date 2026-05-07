# tomlkit Comment Operations & Style Preservation API Reference

## Overview

**tomlkit** (v0.14.0) is a style-preserving TOML parser and serializer for Python. Unlike
standard TOML parsers that discard comments, whitespace, and formatting during parsing,
tomlkit preserves all style information and allows round-trip editing: parse a TOML file,
modify values programmatically, and write it back with the original formatting intact.

This document covers tomlkit's comment handling, trivia (metadata) system, and the
style-preservation guarantees that must hold across parse-edit-dump cycles.

## Key Concepts

### Trivia

Every TOML item in tomlkit carries **trivia** — metadata about the surrounding whitespace,
comments, and formatting. The trivia is stored as a `Trivia` dataclass with these fields:

- `indent` (str): whitespace before the item (e.g., leading spaces or `\n`)
- `comment_ws` (str): whitespace between the value and the comment (e.g., `" "`)
- `comment` (str): the comment text, starting with `#` (e.g., `"# my comment"`)
- `trail` (str): trailing content including newline (e.g., `"\n"`)

The serialization order for a key-value pair is:
```
{indent}{key}{separator}{value}{comment_ws}{comment}{trail}
```

For example, parsing `  key = "value" # explanation\n` produces:
- `indent = "  "`
- `key = "key"`
- `separator = " = "`
- `value = "value"` (as a String item)
- `comment_ws = " "`
- `comment = "# explanation"`
- `trail = "\n"`

### Comment Types

tomlkit supports two kinds of comments:

1. **Inline comments**: attached to a key-value pair or table header via trivia
   ```toml
   key = "value"  # this is an inline comment
   [section] # this is a table header comment
   [[array]] # this is an AoT header comment
   ```

2. **Standalone comments**: independent Comment items in the document body
   ```toml
   # This is a standalone comment
   key = "value"
   ```

## Public API

### Creating Comments

```python
import tomlkit

# Create a standalone comment item
c = tomlkit.comment("my standalone comment")
# This creates a Comment item with:
#   trivia.indent = ""
#   trivia.comment_ws = "  "
#   trivia.comment = "# my standalone comment"
#   trivia.trail = "\n"
```

### Attaching Inline Comments

```python
# Attach a comment to any item
doc = tomlkit.parse("key = 1\n")
doc.item("key").comment("explanation")
# Result: key = 1 # explanation

# The comment() method:
# - Automatically adds "# " prefix if not present
# - Sets comment_ws to " " (one space separator)
# - Stores the comment in the item's trivia
```

### Adding Standalone Comments to Documents

```python
doc = tomlkit.document()
doc.add("x", 1)
doc.add(tomlkit.comment("between items"))
doc.add("y", 2)
# Result:
# x = 1
# # between items
# y = 2
```

### Comments on Table Sections

```python
# Table headers can have inline comments
doc = tomlkit.parse("[section]\nkey = 1\n")
section = doc.item("section")
section.comment("section description")
# Result: [section] # section description
#         key = 1
```

### Comments on Array of Tables

```python
# AoT section headers can have comments
doc = tomlkit.parse("[[items]]\nname = \"first\"\n")
aot = doc.item("items")
aot.body[0].comment("first entry")
# Result: [[items]] # first entry
#         name = "first"
```

## Style Preservation Guarantees

### Roundtrip Invariant

The fundamental guarantee of tomlkit:
```python
tomlkit.dumps(tomlkit.parse(s)) == s
```

This must hold for any valid TOML string `s`. The parse-dump cycle must produce
**byte-identical** output, preserving:
- All whitespace (indentation, blank lines, trailing spaces)
- All comments (both inline and standalone)
- Key quoting style (bare, basic, literal)
- Number format (hex, octal, binary, scientific notation)
- String type (basic, literal, multiline)

### Comment Preservation

When editing a document, comments must be preserved correctly:

1. **Inline comments survive value replacement**: When you replace a value using
   `doc["key"] = new_value`, the trivia (including comments) follows specific
   priority rules:
   - If the new value has its own comment, the **new comment takes priority**
   - If the new value has no comment, the old value's comment is preserved
   - The same priority applies to `comment_ws`

2. **Standalone comments maintain position**: Standalone comments in the document
   body remain at their original positions relative to surrounding items.

3. **Table header comments are preserved**: Comments on `[table]` and `[[aot]]`
   headers survive through parse-dump cycles.

### Table Header Rendering

Table sections render their headers with a specific format:
```
{indent}[{key}]{comment_ws}{comment}{trail}
```

For Array of Tables:
```
{indent}[[{key}]]{comment_ws}{comment}{trail}
```

The rendering ensures:
- The `comment_ws` (whitespace separator) appears BETWEEN the closing bracket(s) and the `#` character
- The comment text (starting with `#`) appears AFTER the whitespace separator
- A newline follows the header before the first key-value pair in the section

### Table Section Types

tomlkit distinguishes between regular tables and **super tables**:

- A **regular table** like `[section]` renders its header explicitly
- A **super table** is an intermediate parent in a dotted path. For example,
  in `[a.b.c]`, if `[a]` has no direct content (only sub-tables), it may be
  a super table. Super tables may omit their header in the output since they
  are implicitly defined by their children.

A table is considered a super table only if ALL of its direct children (accessible
via dict interface) are Tables or AoTs. Tables with any non-table content (including
key-value pairs) always render their headers.

**Important**: A table that contains only comments and sub-tables is NOT a super
table — the comment is "content" that requires the header to be present for
correct formatting. The header must be rendered to maintain the comment's context.

### Value Replacement Semantics

When replacing a value via `doc[key] = new_value`:

1. The document finds the existing item at the key's position
2. The new value inherits trivia from the old value:
   - `indent` is always copied from old to new
   - `comment_ws` uses the new value's if present, otherwise the old value's
   - `comment` uses the **new value's** if present, otherwise the old value's
   - `trail` is always copied from old to new

This ensures style preservation while allowing explicit comment updates:
```python
# Replace value, keeping old comment
doc["x"] = 42  # old comment is preserved

# Replace value WITH new comment
new_item = tomlkit.integer(42)
new_item.comment("new explanation")
doc["x"] = new_item  # new comment replaces old
```

## Array of Tables (AoT)

### Structure

An Array of Tables represents multiple table entries under the same key:
```toml
[[servers]]
name = "alpha"

[[servers]]
name = "beta"
```

Each `[[servers]]` entry is a separate Table with its own body (key-value pairs,
comments, whitespace).

### Comment Placement in AoT

Comments between AoT entries are stored in the **preceding** table's body:
```toml
[[items]]
name = "first"
# This comment is part of the first table's body

[[items]]
name = "second"
```

Comments can also appear on the AoT header lines:
```toml
[[items]] # section 1
name = "first"
[[items]] # section 2
name = "second"
```

### AoT Header Rendering

Each AoT table header renders with the format:
```
{indent}[[{key}]]{comment_ws}{comment}{trail}
```

The comment_ws and comment fields provide whitespace separation and comment text
respectively, following the same order as regular table headers.

## Table Formatting Details

### Newline After Header

When a table section has content (at least one key-value pair or comment), the
serializer ensures there is a newline between the header and the first item. If the
table's trivia `trail` already contains a newline, no additional newline is added.
If the `trail` does NOT contain a newline (e.g., for programmatically created tables),
a newline is inserted to separate the header from the content.

This prevents malformed output like:
```
[section]key = 1
```

Which should be:
```
[section]
key = 1
```

### Blank Lines

The serializer respects blank lines in the original document. It does not add or
remove blank lines during roundtrip. The only exception is the automatic newline
insertion described above for headers without trailing newlines.

## Nested Tables

### Out-of-Order Tables

TOML allows table sections to appear out of order:
```toml
[a]
x = 1

[b]
y = 2

[a.sub]
z = 3
```

Here `[a]` and `[a.sub]` are not adjacent. tomlkit tracks this using a tuple of
body indices in its internal `_map`. Operations on out-of-order tables (like
`_insert_after`) must use the **last** index to maintain correct positioning.

### Dotted Keys in Tables

Tables can contain dotted keys:
```toml
[section]
a.b.c = 1
```

These are different from nested table sections and are rendered with their dotted
key prefix when the parent key is dotted.

## Document Construction API

### Building Documents Programmatically

```python
doc = tomlkit.document()

# Add key-value pairs
doc.add("title", "My App")

# Add standalone comments
doc.add(tomlkit.comment("Server configuration"))

# Add tables
server = tomlkit.table()
server.add("host", "localhost")
server.add("port", 8080)
server.comment("main server")  # comment on table header
doc.add("server", server)

# Add Array of Tables
servers = tomlkit.aot()
for name in ["alpha", "beta"]:
    t = tomlkit.table()
    t.add("name", name)
    servers.append(t)
doc.add("servers", servers)
```

### Modifying Existing Documents

```python
doc = tomlkit.parse(toml_string)

# Read values
val = doc["key"]

# Update values (preserves formatting)
doc["key"] = new_value

# Delete keys
del doc["key"]

# Add comments
doc.item("key").comment("explanation")

# Access table sections
section = doc.item("section")  # returns Table object
section["new_key"] = "new_value"
```

## Error Handling

tomlkit raises specific exceptions:
- `KeyAlreadyPresent`: when adding a key that already exists
- `NonExistentKey`: when accessing or deleting a non-existent key
- `TOMLKitError`: general tomlkit errors
- Standard `toml` parse errors for invalid TOML syntax

## Invariants for Testing

When testing tomlkit's style preservation, these properties should hold:

1. **Roundtrip identity**: `dumps(parse(s)) == s` for any valid TOML string
2. **Value preservation**: `parse(dumps(doc))[key] == doc[key]` for all keys
3. **Comment preservation**: comments survive parse-dump cycles unchanged
4. **Header presence**: all explicitly defined table/AoT headers appear in output
5. **No extra whitespace**: parse-dump does not add blank lines or extra spaces
6. **Comment separator**: inline comments have whitespace before the `#` character
7. **Replacement priority**: new value's comment takes priority over old value's
8. **Format consistency**: `[table]` and `[[aot]]` headers use consistent format

These invariants should be tested across various TOML structures:
- Simple key-value pairs with/without comments
- Table sections with comments on headers
- Nested table sections (parent + child)
- Array of Tables with inter-section comments
- Value replacement with comment updates
- Mixed content (tables, comments, whitespace, key-value pairs)
