# parso 0.8.6 — Diff Parser, Normalizer, and Tree API Reference

This document covers the APIs relevant to incremental parsing, tree normalisation,
and position-aware node/leaf inspection in parso 0.8.6.

---

## 1. Parsing a Python Module

```python
import parso

# Full parse — always produces a correct parse tree
module = parso.parse(code)

# Parse with a specific Python version
grammar = parso.load_grammar(version='3.8')
module = grammar.parse(code)
```

`parso.parse()` returns a **Module** (a subclass of `BaseNode`) representing the
complete parse tree. The invariant `module.get_code() == code` always holds after a
full parse.

---

## 2. Incremental (Diff-Based) Re-parse

parso provides a `DiffParser` that re-uses nodes from a previous parse when only
part of the source has changed. This is the mechanism used by Jedi for fast
autocompletion on large files.

### Setting up DiffParser

```python
from parso.python.diff import DiffParser
from parso.utils import split_lines

grammar = parso.load_grammar(version='3.8')

# Initial parse
code1 = 'x = 1\ny = 2\nz = 3\n'
module = grammar.parse(code1)

# Prepare for incremental re-parse
old_lines = split_lines(code1, keepends=True)
new_lines = split_lines(code2, keepends=True)

# Create and run the diff parser
dp = DiffParser(grammar._pgen_grammar, grammar._tokenizer, module)
module = dp.update(old_lines, new_lines)
```

`DiffParser.update(old_lines, new_lines)` modifies the module **in place** and
returns it. After calling `update()`:
- `module.get_code()` should equal `''.join(new_lines)`
- Node positions should reflect the new source positions

### Key invariant

```python
# After incremental re-parse:
assert module.get_code() == ''.join(new_lines)
```

### When DiffParser copies vs. re-parses

The diff algorithm uses `difflib.SequenceMatcher` to find equal/changed regions.
For **equal** regions, nodes from the old tree are copied (with position offsets
applied). For **replace/insert** regions, the sub-parser re-parses the new lines.

The internal `parsed_until_line` property tracks how many lines have been
processed. The copy loop terminates when `until_line_new <= parsed_until_line`.

---

## 3. Tree Node Types

### BaseNode

The base class for all non-leaf nodes.

```python
from parso.tree import BaseNode, Leaf

# Key properties
node.type          # str, e.g. 'file_input', 'simple_stmt', 'expr_stmt'
node.children      # list of NodeOrLeaf children
node.start_pos     # (line, column) tuple, 1-based lines, 0-based columns
node.end_pos       # (line, column) tuple — position after last character
node.parent        # parent BaseNode, or None for root
node.get_code()    # str — reconstruct source including whitespace
node.get_first_leaf()   # leftmost Leaf descendant
node.get_last_leaf()    # rightmost Leaf descendant
```

### Leaf

Leaf nodes represent individual tokens.

```python
leaf.value         # str — the token text (e.g. 'x', '=', '1', '\n')
leaf.prefix        # str — whitespace/comments preceding this token
leaf.type          # str — token type (e.g. 'name', 'number', 'operator', 'newline')
leaf.start_pos     # (line, column) — where the token value starts (not the prefix)
leaf.end_pos       # (line, column) — position immediately after the token value
leaf.line          # int — line number of start_pos (1-based)
leaf.column        # int — column of start_pos (0-based)
leaf.get_code(include_prefix=True)  # prefix + value (default) or just value
```

### Position conventions

- Lines are 1-based: the first line is line 1
- Columns are 0-based: the first column is 0
- `start_pos` points to the start of `value` (not counting `prefix`)
- `end_pos` is the position of the character **after** the last character of `value`
- For adjacent leaves: `leaf.end_pos == leaf.get_next_leaf().start_pos`

### Newline leaves

Newline tokens (`'\n'`, `'\r\n'`) are special:
- `leaf.type == 'newline'`
- `leaf.value` is `'\n'` or `'\r\n'`
- A newline at position `(L, C)` has `end_pos = (L+1, 0)` (next line, column 0)
- `split_lines('\n')` returns `['', '']` (two elements)

### get_code() invariant

```python
# For the root module after any parse or re-parse:
module.get_code() == original_source_code

# For any node:
node.get_code() == ''.join(leaf.prefix + leaf.value for leaf in all_leaves(node))
```

---

## 4. Walking the Leaf Sequence

```python
# Iterate all leaves in source order
leaf = module.get_first_leaf()
while leaf is not None:
    # process leaf
    leaf = leaf.get_next_leaf()

# Or use get_previous_leaf() to go backwards
```

### Position lookup

```python
# Find the leaf at a given (line, column) position
leaf = module.get_leaf_for_position((line, col), include_prefixes=False)
```

The binary search uses `end_pos` for comparisons. The invariant:
if `position <= leaf.end_pos` for a child, the position is within that subtree.

---

## 5. Normalizer API

The `Normalizer` class provides a visitor that walks the parse tree and
reconstructs the source string. It is designed for checking code style (e.g.
PEP 8) and for code refactoring.

```python
from parso.normalizer import Normalizer, RefactoringNormalizer

# Basic Normalizer — visits all nodes and reconstructs source
normalizer = Normalizer(grammar, config=None)
reconstructed_code = normalizer.walk(module)
# Invariant: reconstructed_code == module.get_code()
```

### visit() and visit_leaf()

```python
class Normalizer:
    def visit(self, node):
        """Recursively visit a node or leaf, return reconstructed code str."""

    def visit_leaf(self, leaf):
        """Visit a single leaf, return prefix + value."""
        return leaf.prefix + leaf.value  # correct order

    def visit_node(self, node):
        """Context manager called when entering a node."""
```

The `walk()` method calls `initialize()`, `visit()`, then `finalize()`.

`visit()` is recursive:
- For a Leaf: calls `visit_leaf(leaf)` which returns `leaf.prefix + leaf.value`
- For a BaseNode: returns `''.join(self.visit(child) for child in children)`

**Key invariant**: `Normalizer(grammar, None).walk(module) == module.get_code()`

### RefactoringNormalizer

```python
from parso.normalizer import RefactoringNormalizer

# node_to_str_map: maps specific node objects to replacement strings
refactor = RefactoringNormalizer(node_to_str_map={})  # identity (no replacements)
result = refactor.visit(module)
# Invariant: result == module.get_code() when map is empty
```

`RefactoringNormalizer` overrides `visit()` and `visit_leaf()` to check the
replacement map first; if no replacement, it falls through to the base
`Normalizer` behavior.

### add_issue()

```python
normalizer.add_issue(node, code=42, message="error description")
# Adds an Issue to normalizer.issues list (deduplicated by start_pos + code)
normalizer.issues  # list of Issue objects
```

---

## 6. DiffParser Internals

For L4-level understanding, key internals:

### _NodesTreeNode.get_last_line(suffix)

Returns the last fully-parsed line number for this node group. Used internally
as `parsed_until_line`.

- `parsed_until_line` is computed from the last leaf's `end_pos` plus any
  `line_offset` adjustment
- For newline-terminated nodes: the last line is the line **containing** the
  newline (one less than `end_pos[0]`), because the newline belongs to the
  current statement, not the next

### _copy_from_old_parser(line_offset, start_old, until_old, until_new)

The copy loop:

```python
while until_line_new > self._nodes_tree.parsed_until_line:
    # Map current new-file position back to old-file position
    parsed_until_line_old = self._nodes_tree.parsed_until_line - line_offset
    line_stmt = self._get_old_line_stmt(parsed_until_line_old + 1)
    # ...
```

The mapping `new_line - line_offset = old_line` accounts for lines that were
inserted (positive offset) or deleted (negative offset) before this region.

### split_lines()

```python
from parso.utils import split_lines

lines = split_lines(code, keepends=True)
# Returns a list of lines, each ending with '\n' if keepends=True
# The last element is '' if code ends with '\n' (empty string after last newline)
# len(lines) == number_of_newlines + 1
```

---

## 7. Practical Example: Testing Incremental Re-parse

```python
import parso
from parso.utils import split_lines
from parso.python.diff import DiffParser

def test_incremental_roundtrip(code1, code2):
    """After re-parsing code2 incrementally, get_code() must equal code2."""
    grammar = parso.load_grammar(version='3.8')
    module = grammar.parse(code1)

    old_lines = split_lines(code1, keepends=True)
    new_lines = split_lines(code2, keepends=True)

    dp = DiffParser(grammar._pgen_grammar, grammar._tokenizer, module)
    module = dp.update(old_lines, new_lines)

    assert module.get_code() == code2
```

Common scenarios to test:
1. **Insertion at the start**: `code2 = new_line + code1`
2. **Deletion from middle**: `code2 = code1` with a line removed
3. **Replacement of middle lines**: `code2` replaces one or more lines of `code1`
4. **Appending to end**: `code2 = code1 + new_line`
