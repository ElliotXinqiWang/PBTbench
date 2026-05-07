# tomlkit Table Merge & Dotted Key API Reference

## Overview

`tomlkit` is a style-preserving TOML parser and editor for Python. Unlike
`tomllib` (which only parses) or `tomli_w` (which only writes), tomlkit
preserves comments, whitespace, and formatting through parse-edit-dump cycles.

This document covers the table merge, update, and dotted key handling APIs.

## Core Concepts

### Table Types

TOML tables can appear in several forms:

```toml
# Standard table header
[server]
host = "localhost"
port = 8080

# Dotted keys (inline nested assignment)
[server]
config.port = 8080
config.host = "localhost"

# Nested table header
[server.config]
port = 8080

# Super table (implicit parent of nested tables)
[a.b.c]    # 'a' and 'a.b' are super tables
x = 1
```

A **super table** is an intermediate parent table that exists only to hold
child tables. It does not have its own `[header]` in the TOML output but
is implied by the dotted path of its children.

### Out-of-Order Tables (OOT)

TOML allows table sections to be non-contiguous:

```toml
[a]          # First section of 'a'
x = 1

[b]          # Different table in between
y = 2

[a.sub]      # Second section extending 'a'
z = 3
```

Internally, tomlkit tracks OOT tables by storing a **tuple of body indices**
in `Container._map`. For the example above, `_map['a']` would be `(0, 2)`
indicating that key 'a' has body entries at positions 0 and 2.

When accessing an OOT table, tomlkit returns an `OutOfOrderTableProxy` that
merges the values from all sections.

## API Reference

### Creating Tables

```python
import tomlkit

# Create a document
doc = tomlkit.document()

# Create and add a table
tab = tomlkit.table()
tab.add("host", "localhost")
tab.add("port", 8080)
doc.add("server", tab)

# Output:
# [server]
# host = "localhost"
# port = 8080
```

### Dotted Keys

Dotted keys allow inline nested assignment without explicit table headers:

```python
from tomlkit.items import DottedKey, SingleKey

# Create a dotted key
dk = DottedKey([SingleKey("config"), SingleKey("port")])
doc.add(dk, 8080)

# Output: config.port = 8080
```

When adding a dotted key to a document, `Container._handle_dotted_key()`
creates a chain of super tables internally:

1. Splits the key into components: `name, *mid, last = key`
2. Sets `name._dotted = True` to mark it for dotted notation rendering
3. Creates intermediate super tables for mid components
4. Appends the final value under the last component
5. Appends the outermost super table to the container

The `_dotted` flag on key components determines whether the table renders
using dotted notation (`a.b = 1`) or table header notation (`[a]\nb = 1`).

### Table Updates

Tables support dict-like update operations:

```python
# Simple update
doc["server"]["port"] = 9090  # Replace existing value

# Dict-style update
doc["server"].update({"port": 9090, "timeout": 30})

# |= operator
doc["server"] |= {"port": 9090}
```

For OOT tables, `__setitem__` uses `OutOfOrderTableProxy` which delegates
to the appropriate internal table section.

### Container.value and Comparison

The `.value` property returns a plain `dict` representation of the document,
merging OOT sections:

```python
doc = tomlkit.parse("""
[a]
x = 1

[b]
y = 2

[a.sub]
z = 3
""")

# dict access (uses OutOfOrderTableProxy)
print(doc["a"])  # {'x': 1, 'sub': {'z': 3}}

# .value (merges via merge_dicts)
print(doc.value)  # {'a': {'x': 1, 'sub': {'z': 3}}, 'b': {'y': 2}}

# Comparison uses .value internally
assert doc == {'a': {'x': 1, 'sub': {'z': 3}}, 'b': {'y': 2}}
```

The `merge_dicts(d1, d2)` helper performs deep merge:
- If both `d1[k]` and `d2[k]` are dicts, recursively merge
- Otherwise, `d2[k]` overwrites `d1[k]`

This is used by `Container.value` and `Container.unwrap()` to combine
values from multiple OOT body positions.

### Super Table Merge During Parsing

When parsing TOML, the parser calls `Container.append()` for each table
section. When a table key already exists and both the existing and new
entries are super tables, tomlkit decides between two strategies:

1. **Deep merge**: Merge the new table's children into the existing table
   body entry. Used when tables are contiguous (the last appended table
   key matches the current key).

2. **Out-of-order (OOT)**: Create a new body entry with a tuple index.
   Used when tables are non-contiguous (another table was added between
   the first and second occurrence).

The deep merge path copies the existing table, appends new children,
and writes the merged result to `body[current_idx[-1]]` (the last body
position for the key). This preserves the OOT ordering when the key
already has multiple body positions.

### Rendering (as_string / dumps)

`Container.as_string()` (called by `tomlkit.dumps()`) serializes the
document by iterating over `_body` entries:

- **Regular tables**: Rendered with `[key]` header
- **Super tables**: Rendered without header (children rendered with prefix)
- **Dotted keys**: Rendered inline as `a.b.c = value`

For sub-tables within a table being rendered, the renderer checks:
- If the sub-table's key is dotted AND the parent key is not dotted:
  render without prefix (the dotted key handles its own path)
- Otherwise: render with parent prefix for proper nesting

This distinction ensures that `config.port = 8080` inside `[server]`
renders as `config.port = 8080` (not `server.config.port = 8080`).

## Common Patterns

### Parse-Edit-Dump Roundtrip

```python
import tomlkit

# Parse
doc = tomlkit.parse(toml_string)

# Edit
doc["server"]["port"] = 9090
doc["server"]["new_key"] = "value"

# Dump (preserves style)
output = tomlkit.dumps(doc)

# Roundtrip property: parse(dumps(doc)) should produce same values
reparsed = tomlkit.parse(output)
assert reparsed == doc  # Uses Container.__eq__ which calls .value
```

### OOT Roundtrip

```python
# TOML with interleaved table sections
toml_str = """
[database]
host = "localhost"

[logging]
level = "info"

[database.pool]
size = 10
min_idle = 2
"""

doc = tomlkit.parse(toml_str)

# Access OOT values
print(doc["database"]["host"])       # "localhost"
print(doc["database"]["pool"]["size"])  # 10

# Roundtrip
output = tomlkit.dumps(doc)
reparsed = tomlkit.parse(output)
assert doc.unwrap() == reparsed.unwrap()
```

### Programmatic Dotted Key Construction

```python
from tomlkit.items import DottedKey, SingleKey

doc = tomlkit.document()
doc.add("name", "my-app")

# Add dotted keys
dk = DottedKey([SingleKey("database"), SingleKey("host")])
doc.add(dk, "localhost")

dk2 = DottedKey([SingleKey("database"), SingleKey("port")])
doc.add(dk2, 5432)

# Output:
# name = "my-app"
# database.host = "localhost"
# database.port = 5432
```

### Value Integrity Check

```python
# For OOT documents, .value should contain all merged data
doc = tomlkit.parse("""
[app.server]
port = 8080

[other]
x = 1

[app.server.ssl]
enabled = true
""")

val = doc.value
assert val["app"]["server"]["port"] == 8080
assert val["app"]["server"]["ssl"]["enabled"] is True
assert val["other"]["x"] == 1
```

## Properties for Testing

1. **Roundtrip preservation**: `parse(dumps(parse(s))) == parse(s)` for valid TOML
2. **Value integrity**: `doc.value` and `doc.unwrap()` contain all parsed data
3. **Format preservation**: Dotted keys render as dotted notation, table headers as headers
4. **OOT consistency**: Interleaved table sections produce correct merged values
5. **Update semantics**: `table.update(dict)` preserves non-updated keys
