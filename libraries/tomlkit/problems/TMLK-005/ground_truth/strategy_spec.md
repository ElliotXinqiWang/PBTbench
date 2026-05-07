# Strategy Spec: TMLK-005

## Bug 1: OOT deep merge goes to wrong body position

**Trigger condition**: Parse TOML with 3+ sections for the same parent key,
where at least one other table key is interleaved (creating out-of-order tables).
When the third section arrives, the deep merge writes to `body[current_idx[0]]`
(first OOT position) instead of `body[current_idx[-1]]` (last position),
producing duplicate table sections in the serialized output.

**Why default strategy is insufficient**: Default Hypothesis strategies generate
simple flat TOML or single-table structures. The trigger requires 3+ interleaved
table sections for the same parent key, which is a very specific structural
pattern that random generation almost never produces.

**Trigger probability with default strategy**: ~0% (requires 3+ OOT sections
with specific interleaving pattern)

**Targeted strategy**: Generate TOML with `[parent.child1]...[other]...[parent.child2]...[parent.child3]`
structure. Parse, dump, and reparse. Alternatively, parse a 2-section OOT and
programmatically append a third super table.

**Minimal trigger input**:
```
[a.x]
v1 = 1

[b]
v2 = 2

[a.y]
v3 = 3

[a.z]
v4 = 4
```
-> Parse succeeds, but `dumps()` produces `[a.y]\nv3 = 3\n\n[a.z]\nv4 = 4\n[b]\nv2 = 2\n\n[a.y]\nv3 = 3\n`
with duplicate `[a.y]` section. Reparsing fails with "Key already exists".

---

## Bug 2: _handle_dotted_key drops dotted flag on first component

**Trigger condition**: Programmatically add a DottedKey to a Container using
`doc.add(DottedKey([...]), value)` or `table.add(DottedKey([...]), value)`.
The first key component loses its `_dotted = True` flag, causing the super
table to render with a `[header]` notation instead of dotted notation.

**Why default strategy is insufficient**: The DottedKey API is a programmatic
construction feature. Default string-based TOML generators don't use
`DottedKey([SingleKey(...), ...])` directly. The bug only manifests when
keys are created via the Python API, not when parsing TOML text.

**Trigger probability with default strategy**: ~5% (requires explicit
DottedKey usage in API tests)

**Targeted strategy**: Create DottedKey with 2+ components, add to a
document or table, and check that the output uses dotted notation
(contains `a.b = value` format).

**Minimal trigger input**: `doc.add(DottedKey([SingleKey('a'), SingleKey('b')]), 1)`
-> Expected output: `a.b = 1\n`
-> Buggy output: `[a]\nb = 1\n` (table header instead of dotted notation)

---

## Bug 3: merge_dicts swaps arguments, losing nested data

**Trigger condition**: Parse TOML with out-of-order tables where two sections
share a common nested dict key. Access `doc.value` or use `doc == dict` comparison.
The `merge_dicts(v, d1[k])` call merges d1's values INTO d2's dict (which is
then discarded) instead of merging d2's values into d1's accumulator dict.

**Why default strategy is insufficient**: The trigger requires OOT tables with
shared nested dict keys, which is a specific structural pattern. Additionally,
the bug only manifests through `.value` or `__eq__`, not through `doc['key']`
or `doc.unwrap()`. Most PBT tests use dict access or unwrap.

**Trigger probability with default strategy**: ~0% (requires OOT with shared
nested dict keys AND accessing through .value or ==)

**Targeted strategy**: Generate TOML with
`[parent.shared]...[other]...[parent.shared.sub]` pattern. Check that
`doc.value` contains both the direct values from `[parent.shared]` and the
nested values from `[parent.shared.sub]`.

**Minimal trigger input**:
```
[root.config]
port = 8080

[other]
x = 1

[root.config.db]
host = "localhost"
```
-> `doc.value` returns `{'root': {'config': {'port': 8080}}, 'other': {'x': 1}}`
   Missing `'db': {'host': 'localhost'}` from the config dict.
-> `doc == expected` returns False when expected includes the db sub-key.

---

## Bug 4: _render_table inverts dotted key prefix condition

**Trigger condition**: Parse TOML with dotted keys inside a table header
section (e.g., `[server]` followed by `config.port = 8080`). When
serializing, the inverted condition causes the table name to be prepended
to dotted keys, producing `server.config.port = 8080` instead of
`config.port = 8080`.

**Why default strategy is insufficient**: The trigger requires a specific
TOML structure: a table header `[name]` containing dotted key assignments.
Random TOML generators typically produce flat key-value pairs or fully
nested `[parent.child]` structures, not mixed dotted-inside-header patterns.

**Trigger probability with default strategy**: ~5% (requires dotted keys
inside table header sections in parsed TOML)

**Targeted strategy**: Generate TOML with `[table_name]\ndotted.key = value`
structure. Parse, dump, and verify the output matches the input. Check
that the dotted key does NOT have the table name prepended.

**Minimal trigger input**:
```
[server]
config.port = 8080
```
-> Buggy `dumps()`: `[server]\nserver.config.port = 8080\n`
-> Reparsed value: `{'server': {'server': {'config': {'port': 8080}}}}`
   instead of `{'server': {'config': {'port': 8080}}}`.
