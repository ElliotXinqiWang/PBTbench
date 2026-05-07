# Strategy Specification for TMLK-003

## Bug 1: AoT table header comment rendering order

**Trigger condition**: Parse or construct a TOML document with an Array of Tables (`[[section]]`), then attach a comment to any AoT table element's header via `table.comment("text")`. Serialize with `dumps()`.

**Why default strategy is insufficient**: Default Hypothesis strategies would generate TOML key-value pairs and test roundtrip. They would not:
1. Construct Array of Tables specifically
2. Programmatically add comments to AoT section headers
3. Check the formatting of the serialized header line (e.g., whitespace before `#`)

**Trigger probability with default strategy**: ~5% (requires specifically creating AoT sections with comments)

**Minimum trigger input**:
```python
doc = tomlkit.parse("[[items]]\nname = \"first\"\n")
doc.item("items").body[0].comment("test")
result = tomlkit.dumps(doc)
# Bug: "[[items]]# test " instead of "[[items]] # test"
```

---

## Bug 2: Value replacement comment priority inversion

**Trigger condition**: Replace a value that already has a comment with a new value that also has its own comment. Both old and new must have non-empty `trivia.comment`.

**Why default strategy is insufficient**: Default PBT would test:
1. Setting values (not replacing)
2. Comments on new values (not comparing old vs new comments)
3. The semantic value (not the comment text)

The bug requires a *multi-step operation*: first parse/set a value with comment, then replace with a new value that has a different comment.

**Trigger probability with default strategy**: <1% (requires both old AND new values to have non-empty comments, and the test must compare comment text)

**Minimum trigger input**:
```python
doc = tomlkit.parse("x = 1 # old\n")
new_item = tomlkit.integer(2)
new_item.comment("new")
doc["x"] = new_item
result = tomlkit.dumps(doc)
# Bug: "x = 2 # old" instead of "x = 2 # new"
```

---

## Bug 3: Extra blank line after table header

**Trigger condition**: Parse ANY TOML with a table section header (e.g., `[section]\nkey = 1\n`), then serialize with `dumps()`.

**Why default strategy is insufficient**: Default PBT would test semantic values (dict content), not formatting. The bug is purely a formatting error — the parsed values are correct, but the serialized output has an extra blank line between `[section]` and the first key.

**Trigger probability with default strategy**: ~15% (any test using `[table]` sections that checks roundtrip string equality)

**Minimum trigger input**:
```python
toml_str = "[section]\nkey = 1\n"
doc = tomlkit.parse(toml_str)
result = tomlkit.dumps(doc)
# Bug: "[section]\n\nkey = 1\n" instead of "[section]\nkey = 1\n"
```

---

## Bug 4: Super-table header omission for tables with comments

**Trigger condition**: Parse TOML with a dotted table key like `[parent.sub]` (which creates an implicit super table `[parent]` with `_is_super_table=True`), then programmatically add a comment to `[parent]`'s body. The bug adds `Comment` to the exclusion list when checking if a super table has non-table content. Since the only non-table/AoT/Whitespace/Null item is a Comment, the check returns False, and the `[parent]` header is omitted from `dumps()` output.

**Why default strategy is insufficient**: Default PBT would:
1. Test tables with key-value content (not comment-only super tables)
2. Not construct implicit super tables via dotted keys and then add comments
3. Test semantic correctness (dict values), not header presence
4. Not programmatically insert comments into super table bodies

**Trigger probability with default strategy**: <3% (requires creating an implicit super table via dotted key, then programmatically adding a comment to it)

**Minimum trigger input**:
```python
toml_str = "[parent.sub]\nkey = 1\n"
doc = tomlkit.parse(toml_str)
parent = doc.item("parent")
parent.value._body.insert(0, (None, tomlkit.comment("test")))
result = tomlkit.dumps(doc)
# Bug: "# test\n[parent.sub]\nkey = 1\n" (missing [parent] header)
# Expected: "[parent]\n# test\n[parent.sub]\nkey = 1\n"
```
