# tomlkit: Style-Preserving TOML Library

## Overview

**tomlkit** is a Python library for parsing and creating TOML documents. Unlike
standard TOML parsers, tomlkit preserves all style elements: comments, indentation,
whitespace, and formatting are maintained through parse-edit-dump cycles.

tomlkit is the TOML engine used by **Poetry** (Python package manager).

Version: 0.14.0

## Core Concepts

### Style Preservation (Roundtrip)

The fundamental guarantee of tomlkit is **roundtrip fidelity**:

```python
import tomlkit

original = """
# Database configuration
[database]
host = "localhost"  # production uses 10.0.0.1
port = 5432
"""

doc = tomlkit.loads(original)
assert tomlkit.dumps(doc) == original  # Exact preservation
```

After modifying values, only the changed values are affected; all surrounding
comments, whitespace, and formatting are preserved.

### Document Structure

A `TOMLDocument` extends `Container`, which maintains:

- **`_body`**: An ordered list of `(Key, Item)` tuples representing every element
  in the document (key-value pairs, tables, whitespace, comments).
- **`_map`**: A dictionary mapping each `Key` to its index (or tuple of indices)
  in `_body`. When a table key appears in multiple locations (out-of-order tables),
  the map stores a **tuple of indices** rather than a single integer.

### Out-of-Order Tables

TOML allows sub-tables to be defined separately from their parent:

```toml
[a]
x = 1

[b]
y = 2

[a.sub]    # This is a sub-table of [a], defined after [b]
z = 3
```

In this case, key `a` maps to a **tuple of body indices** `(0, 2)` because it has
entries at two positions in the body. The internal `_map` stores this tuple to track
all locations belonging to the same logical table.

## Public API

### Parsing and Serialization

```python
tomlkit.loads(string: str) -> TOMLDocument
tomlkit.dumps(data: Mapping) -> str
tomlkit.parse(string: str) -> TOMLDocument
```

### Creating Documents Programmatically

```python
doc = tomlkit.document()
doc.add("key", "value")          # Add key-value pair
doc.add("key2", 42)              # Add integer
doc.add(tomlkit.comment("# A comment"))  # Add comment
doc.add(tomlkit.nl())            # Add newline

# Tables
t = tomlkit.table()
t.add("x", 10)
doc.add("section", t)            # Adds [section] with x = 10

# Inline tables
it = tomlkit.inline_table()
it.update({"x": 1, "y": 2})     # {x = 1, y = 2}

# Arrays
a = tomlkit.array()
a.extend([1, 2, 3])
```

### Modifying Documents

```python
doc = tomlkit.loads(toml_string)

# Update values (preserves formatting)
doc["key"] = new_value

# Delete keys
del doc["key"]

# Access nested tables
doc["section"]["nested_key"] = value
```

## Container Internal Methods

### `_insert_after(key, other_key, item)`

Inserts a new `(other_key, item)` pair into the body immediately **after** the
entry identified by `key`.

When `key` maps to a **tuple of indices** (out-of-order table), the insertion
happens after the **last** (maximum) index. This ensures the new entry appears
after all sections belonging to that key, maintaining document coherence.

After insertion, all map indices greater than the insertion point are incremented
to reflect the shifted positions in `_body`.

### `_insert_at(idx, key, item)`

Inserts a new `(key, item)` pair at position `idx` in the body.

All existing map entries at or after `idx` are incremented to reflect the shift.
This includes both single-index entries and tuple entries (where each component
`>= idx` is incremented).

This method is called internally when adding key-value pairs to a document that
already contains table sections — the new pair must be placed before the first
table to maintain valid TOML structure.

### `_replace_at(idx, new_key, value)`

Replaces the entry at position `idx` with `(new_key, value)`. Trivia (indent,
comment whitespace, comment text, trailing whitespace) from the old entry is
copied to the new entry to preserve formatting.

### `_raw_append(key, item)`

Appends to the end of `_body`. If `key` already exists in `_map`, the map entry
is converted to (or extended as) a tuple of indices.

## Array Operations

### Array Creation

```python
# From parsing
doc = tomlkit.loads("arr = [1, 2, 3]")
arr = doc["arr"]  # Array object

# Programmatic
arr = tomlkit.array()
arr.extend([1, 2, 3])
```

### Array Internal Structure

Each `Array` maintains:
- A Python list (via `_CustomList`) of the actual values
- `_value`: A list of `_ArrayItemGroup` objects, each containing:
  - `indent`: Whitespace before the value
  - `value`: The actual Item (or Null for comment-only groups)
  - `comma`: Whitespace containing the comma separator (or None)
  - `comment`: Optional comment after the value

For multiline arrays, the last group is typically a whitespace-only group
representing the closing bracket's indentation.

### Array.insert(pos, value)

Inserts `value` at position `pos`.

The method handles comma management:
- If inserting before the end (`pos < length`), the new element gets a comma
  after it to separate from the next element.
- If inserting at the end, the **previous** last element must receive a comma
  (if it doesn't already have one) to separate from the new element.
- Indentation is inherited from surrounding elements for consistent formatting.

### Array.__delitem__(key)

Deletes the element at index `key` (supports negative indices and slices).

The deletion process manages comma cleanup:
1. The corresponding `_ArrayItemGroup` is removed from `_value`.
2. Comma bookkeeping: if the removed group had both an indent-comma and a
   value-comma, one is transferred to the next group. If it had neither,
   a comma from the next group is removed.
3. After all removals, the **last** `_value` group's trailing comma is cleaned:
   if the last group is a **value group** (not whitespace), its comma is removed
   to avoid a trailing comma in the serialized output.

### Array.as_string()

For single-line arrays: `[item1, item2, item3]`
For multiline arrays:
```
[
    item1,
    item2,
    item3,
]
```

Note: TOML allows trailing commas in arrays, but tomlkit's programmatic
operations maintain clean formatting without unnecessary trailing commas
in single-line arrays.

## Table Types

### Regular Table

```toml
[section]
key = "value"
```

### Super Table

A table that exists only to contain other tables (no direct key-value pairs):

```toml
[a.b]      # 'a' is implicitly a super table
key = 1
```

### Inline Table

```toml
point = {x = 1, y = 2}
```

### Array of Tables (AoT)

```toml
[[servers]]
name = "alpha"

[[servers]]
name = "beta"
```

## Trivia (Formatting Metadata)

Every `Item` carries a `Trivia` object with:
- `indent`: Whitespace/newlines before the key
- `comment_ws`: Whitespace between the value and the comment
- `comment`: The comment text (including `#`)
- `trail`: Whitespace after the value/comment (usually `\n`)

When values are replaced, trivia from the old value is inherited to preserve
the document's visual layout.

## Key Types

### SingleKey
A bare key or quoted key: `name`, `"quoted.key"`

### DottedKey
A dotted key path: `a.b.c` — represented as a sequence of SingleKey objects.
`key.is_dotted()` returns `True` for dotted keys.

### Key.sep
The separator string between key and value (typically ` = `).

## Common Patterns

### Parse, Modify, Dump

```python
doc = tomlkit.loads(config_string)
doc["version"] = "2.0"
doc["database"]["port"] = 3306
updated = tomlkit.dumps(doc)
```

### Adding Entries to Existing Documents

When adding key-value pairs to a document that already has table sections,
the new entries are automatically placed **before** the first table section
to maintain valid TOML structure:

```python
doc = tomlkit.loads("[section]\nkey = 1\n")
doc.add("name", "test")      # Inserted before [section]
doc.add("version", "1.0")    # Also inserted before [section]
# Result:
# name = "test"
# version = "1.0"
# [section]
# key = 1
```

### Array Manipulation

```python
doc = tomlkit.loads("deps = [\"a\", \"b\", \"c\"]\n")
arr = doc["deps"]
arr.insert(3, "d")           # Append at end
del arr[0]                    # Remove first
# dumps preserves inline format: deps = ["b", "c", "d"]
```

### Multiline Arrays

```python
doc = tomlkit.loads('''
deps = [
    "a",
    "b",
    "c",
]
''')
arr = doc["deps"]
del arr[-1]                   # Remove last
# Result preserves multiline format:
# deps = [
#     "a",
#     "b",
# ]
```
