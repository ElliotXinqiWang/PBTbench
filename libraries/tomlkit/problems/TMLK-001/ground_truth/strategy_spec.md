# Strategy Spec for TMLK-001

## Bug 1: _insert_after uses min(idx) for out-of-order tables (L4)
**Trigger**: Call `_insert_after(key, ...)` where `key` maps to a tuple of body indices (out-of-order table, created when `[a]` and `[a.sub]` sections are separated by `[b]`). The method uses `min(idx)` instead of `max(idx)`, placing the new entry after the first occurrence of the table instead of the last.
**Why hard**: Out-of-order tables are a rare TOML pattern. Most tests use simple sequential table definitions. The `_map` tuple representation is an internal detail not documented in the public API. Only triggers when there are multiple body entries for the same table key, which happens with sub-tables separated by other sections.
**Probability**: ~5% default (requires constructing out-of-order tables), 100% targeted.
**Minimal trigger**: `[a]\nx=1\n\n[b]\ny=2\n\n[a.sub]\nz=3\n` then `doc._insert_after("a", "new", 1)`.

## Bug 2: Array.__delitem__ inverts trailing comma removal (L3)
**Trigger**: Delete the last element from a single-line array where the last `_value` group is not whitespace. The `is_whitespace()` check is inverted, so the trailing comma on the now-last element is not removed.
**Why hard**: The bug only manifests when deleting the LAST element of a single-line array. Deleting middle elements works correctly. Multiline arrays (which have a trailing whitespace group) also behave differently. The trailing comma `[1, 2,]` is valid TOML, so the semantic values are preserved through re-parsing — only the formatting invariant is violated.
**Probability**: ~15% default (need to specifically delete the last element), 100% targeted.
**Minimal trigger**: `doc = parse("a = [1, 2, 3]"); del doc["a"][-1]; dumps(doc)` produces `a = [1, 2,]`.

## Bug 3: Array.insert inverts comma-existence check (L3)
**Trigger**: Insert an element at the end of a single-line array. The previous last element has `comma = None`. The inverted check `comma is not None` skips adding a comma, producing output like `[1, 2 3]` (missing separator).
**Why hard**: Only triggers when inserting at the END of the array (position = len(array)). Inserting at the beginning or middle uses a different code path where the NEW element gets the comma, not the previous one. The result is invalid TOML that causes a parse error, but only when the serialized form is re-parsed.
**Probability**: ~20% default (need to specifically insert at end position), 100% targeted.
**Minimal trigger**: `doc = parse("a = [1, 2]"); doc["a"].insert(2, 3); dumps(doc)` produces `a = [1, 2 3]`.

## Bug 4: _insert_at off-by-one in index shifting (L2)
**Trigger**: Add a key-value pair to a document that already has a table section (e.g., `[section]`). The `append()` method calls `_insert_at()` to place the new key before the table. Inside `_insert_at`, the index-shifting loop uses `>` instead of `>=`, failing to shift the table's map entry. After insertion, `doc["section"]` returns the newly inserted value instead of the table.
**Why hard**: Only triggers when adding entries to a document that already has table sections. Pure table-only or pure key-value-only documents are not affected. The corruption is in the internal `_map`, not the `_body` — `dumps()` still produces correct output since it iterates `_body` directly.
**Probability**: ~30% default (any test that adds keys to a document with tables), 100% targeted.
**Minimal trigger**: `doc = parse("[section]\nx=10"); doc.add("name", "test"); doc["section"]` returns `"test"` instead of the table.
