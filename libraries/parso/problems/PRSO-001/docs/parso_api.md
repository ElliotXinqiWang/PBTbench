# parso 0.8.6 API Documentation

parso is a Python 2/3 parser that supports error recovery and provides a
stable API for working with Python syntax trees. It is used by Jedi
(an autocomplete/static analysis library) and IPython.

## Overview

parso exposes a tree-based representation of Python source code. The key
entry point is `parso.parse()`, which returns a `Module` node (the root
of the syntax tree). From there, you can traverse the tree, inspect node
positions, iterate over definitions, and reconstruct the original source.

**Core invariants** (documented properties that must always hold):
1. **Roundtrip**: `parso.parse(code).get_code() == code` for any string `code`.
2. **Position consistency**: For any leaf `L`, `L.start_pos < L.end_pos` (unless empty),
   and consecutive leaves have non-decreasing positions.
3. **Tree structure**: Every non-root `NodeOrLeaf` node has `node.parent` set correctly,
   and every parent's `children` list contains the node.
4. **Name occurrence ordering**: `module.get_used_names()[name]` returns Name nodes in
   the order they appear in the source (ascending line number, then column).
5. **Iterator completeness**: `iter_funcdefs()`, `iter_classdefs()`, and `iter_imports()`
   recursively traverse the full scope including decorated definitions and nested flows.
6. **Parameter indexing**: `param.position_index` returns the 0-based positional index of
   the parameter within the full parameter list, accounting correctly for both
   positional-only (`/`) and keyword-only (`*`) separators.
7. **Import level**: `import_from.level` correctly returns the number of leading dots
   (relative import depth), counting each `.` character individually.

---

## Entry Point: `parso.parse()`

```python
import parso
module = parso.parse(source, *, version=None, path=None, error_recovery=True)
```

- `source` (str or bytes): The Python source code to parse.
- `version` (str, optional): Python version string like `"3.8"` or `"3.10"`.
  Defaults to the current interpreter's version.
- `path` (str or pathlib.Path, optional): File path for caching.
- `error_recovery` (bool): If True (default), the parser attempts to recover
  from syntax errors and produces an approximate tree.

Returns: a `Module` node.

---

## Node Hierarchy

All nodes inherit from `NodeOrLeaf`. There are two concrete base types:

- `Leaf` — terminal tokens (identifiers, operators, keywords, literals).
- `BaseNode` — composite nodes with child nodes/leaves.

### `NodeOrLeaf` — Base class

#### Attributes

- `parent` (`Optional[BaseNode]`): The parent node. `None` for the root node.
- `type` (str): Node type string matching the Python grammar (e.g., `'name'`,
  `'funcdef'`, `'import_from'`, `'expr_stmt'`).

#### Methods

**`get_root_node()`**
Returns the root of the tree (a `Module` node).

**`get_next_sibling()`**
Returns the next sibling in the parent's `children` list, or `None`.

**`get_previous_sibling()`**
Returns the previous sibling, or `None`.

**`get_next_leaf()`**
Returns the next leaf in DFS order across the whole tree. Returns `None` at
the last leaf.

**`get_previous_leaf()`**
Returns the previous leaf in DFS order. Returns `None` at the first leaf.

**`get_first_leaf()`**
For leaves: returns `self`. For nodes: returns the leftmost descendant leaf.

**`get_last_leaf()`**
For leaves: returns `self`. For nodes: returns the rightmost descendant leaf.

**`get_code(include_prefix=True)`**
Reconstructs the source code for this node (or leaf). When `include_prefix=True`
(default), the whitespace/comments that precede the first token are included.
The roundtrip invariant: `module.get_code() == original_source`.

**`search_ancestor(*node_types)`**
Walks up `parent` links until a node whose `type` is in `node_types` is found.
Returns the first matching ancestor, or `None`.

**`get_start_pos_of_prefix()`**
Returns the `(line, column)` position at which this node's prefix begins —
i.e., the end position of the preceding leaf (or `(1, 0)` for the first leaf).

---

### `Leaf` — Token nodes

A leaf represents a single token from the tokenizer.

#### Attributes

- `value` (str): The text of the token (e.g., `"def"`, `"x"`, `"+"`, `"123"`).
- `prefix` (str): Whitespace and comments that appear before this token.
- `line` (int): 1-based line number where the token starts.
- `column` (int): 0-based column where the token starts.
- `start_pos` (tuple): `(line, column)` — equivalent to `(self.line, self.column)`.
- `end_pos` (tuple): `(end_line, end_column)` — computed from the token value.
  For multi-line tokens (docstrings, multi-line strings), `end_line > start_pos[0]`.

---

### `BaseNode` — Composite nodes

#### Attributes

- `children` (list): The list of child `NodeOrLeaf` objects.
- `start_pos` (tuple): `children[0].start_pos`.
- `end_pos` (tuple): `children[-1].end_pos`.

---

## Python-Specific Node Classes

### `Module` — Top-level file

`type == 'file_input'`

A `Module` is the root node returned by `parso.parse()`. It inherits from
`Scope`.

**`get_used_names()`**
Returns a `UsedNamesMapping` (a `Mapping[str, list[Name]]`) that maps each
identifier name to a list of all `Name` leaf nodes where that identifier
appears in the module.

The returned list for each name preserves the **source order**: names are
listed in the order they appear in the source (ascending line number; within
the same line, ascending column).

```python
code = "x = 1\ny = x + 2\nprint(x)\n"
module = parso.parse(code)
used = module.get_used_names()
# used['x'] -> [Name x@1,0,  Name x@2,4,  Name x@3,6]
# Order is always ascending by start_pos
```

---

### `Scope` — Base class for scopes (Module, Function, Class, Lambda)

All `Scope` nodes support three iteration methods that perform **deep recursive
search** through the scope's children, including nested flow-control blocks
(`if`, `while`, `for`, `try`, `with`, `async`) and decorated definitions.

**`iter_funcdefs()`**
Generator yielding all `Function` nodes (`type == 'funcdef'`) within this scope.
This includes functions defined inside `if`/`for`/`while`/`try`/`with` blocks,
and — critically — functions that are decorated with `@decorator` syntax.
Does NOT recurse into nested function bodies.

```python
code = """
@staticmethod
def foo(): pass

def bar(): pass

if True:
    def baz(): pass
"""
module = parso.parse(code)
list(module.iter_funcdefs())
# -> [Function(foo), Function(bar), Function(baz)]
# All three functions are found, including the @staticmethod-decorated one.
```

**`iter_classdefs()`**
Generator yielding all `Class` nodes (`type == 'classdef'`) within this scope,
including decorated classes.

**`iter_imports()`**
Generator yielding all `ImportName` and `ImportFrom` nodes within this scope.
Searches recursively through all flow containers and suite blocks.

---

### `Function` — Function definitions

`type == 'funcdef'`

**`name`** (property): The `Name` leaf for the function name.

**`get_params()`**
Returns a list of `Param` nodes for this function's parameters.
Does not include the `*`, `/`, `,` separators — only actual parameter nodes.

**`iter_yield_exprs()`**
Returns a generator of `yield_expr` nodes (for generators).

**`iter_return_stmts()`**
Returns a generator of `return_stmt` nodes.

**`is_generator()`**
Returns `True` if the function contains any yield expression.

**`annotation`** (property): Returns the return annotation node (after `->`)
or `None` if there is no return annotation.

---

### `Param` — Function parameters

`type == 'param'`

Represents a single function parameter (including `*args` and `**kwargs`).
Note: `*` (bare star for keyword-only separator) and `/` (positional-only
separator) are NOT Param nodes — they are `Operator` leafs in `children`.

**`name`** (property): The `Name` leaf for the parameter name.

**`star_count`** (property): 0 for normal params, 1 for `*args`, 2 for `**kwargs`.

**`default`** (property): The default value node (after `=`), or `None`.

**`annotation`** (property): The type annotation node (after `:`), or `None`.

**`position_index`** (property)
Returns the 0-based positional index of this parameter within the full
parameter list. The index is computed by counting the parameter's position
in the parent's children list and subtracting adjustments for the `*` and `/`
separator markers.

For a function `def foo(a, b, /, c, *, d)`:
- `a.position_index == 0`
- `b.position_index == 1`
- `c.position_index == 2`
- `d.position_index == 3`

The computation must handle both separators together: when a function has
both `/` (positional-only separator) AND `*` (keyword-only separator),
the index adjustment for each separator must be applied in the correct order.
For a keyword-only parameter `d` (after `*`) in a function that also has
positional-only params (before `/`), both adjustments of 2 must be applied,
yielding the correct sequential position.

**`get_parent_function()`**
Returns the nearest enclosing `Function` or `Lambda`.

---

### `Class` — Class definitions

`type == 'classdef'`

**`name`** (property): The `Name` leaf.

**`get_super_arglist()`**
Returns the arglist node for base classes, or `None` if no parentheses or
empty parentheses.

---

### `ImportFrom` — `from X import Y` statements

`type == 'import_from'`

**`level`** (property)
The relative import depth: number of leading dots.
`from . import x` → `level == 1`.
`from .. import x` → `level == 2`.
`from ... import x` → `level == 3`.
`from ....x import y` → `level == 4`.

The dots can be represented as individual `.` tokens or as the `...` ellipsis
token (which has `len(value) == 3`). The `level` property sums `len(token.value)`
for each leading dot token, so:
- A single `.` token contributes 1 to the level.
- The `...` ellipsis token contributes 3 to the level.
- `from .....` (5 dots) = `...` + `.` + `.` = level 5.

```python
code = "from ... import x\n"
module = parso.parse(code)
imp = list(module.iter_imports())[0]
imp.level  # -> 3 (NOT 1)
```

**`get_from_names()`**
Returns a list of `Name` nodes for the module path after `from`.
For `from a.b import c`: returns `[Name('a'), Name('b')]`.
For `from . import x`: returns `[]`.

**`get_paths()`**
Returns a list of paths (lists of Name nodes) for what is being imported.

**`get_defined_names()`**
Returns the names being imported (aliases preferred over original names).

---

### `ImportName` — `import X` statements

`type == 'import_name'`

**`level`** (property): Always 0 (absolute import).

**`get_paths()`**
Returns a list of paths being imported.

**`is_nested()`**
Returns `True` for dotted imports like `import foo.bar` (without alias).

**`get_defined_names()`**
Returns the top-level names being bound.

---

### `Name` — Identifier leaves

`type == 'name'`

**`is_definition(include_setitem=False)`**
Returns `True` if this name is being defined (assigned, parameter, etc.).

**`get_definition(import_name_always=False, include_setitem=False)`**
Returns the definition statement node for this name, or `None`.

---

## Traversal Patterns

### Full leaf iteration

```python
# Iterate all leaves left-to-right
leaf = module.get_first_leaf()
while leaf is not None:
    print(leaf.type, repr(leaf.value), leaf.start_pos)
    leaf = leaf.get_next_leaf()
```

### Finding all names used in a module

```python
module = parso.parse(code)
used_names = module.get_used_names()
# Mapping from name string -> list of Name leaf nodes in source order
for name, nodes in sorted(used_names.items()):
    print(f"{name}: {len(nodes)} occurrences")
    for n in nodes:
        print(f"  line {n.start_pos[0]}, col {n.start_pos[1]}")
```

### Finding all function definitions (including decorated)

```python
module = parso.parse(code)
# iter_funcdefs finds ALL functions in the scope, including:
# - decorated functions (@staticmethod, @property, @my_decorator, etc.)
# - functions inside if/for/while/try/with blocks
for func in module.iter_funcdefs():
    decorators = func.get_decorators()
    print(f"def {func.name.value}: {len(decorators)} decorator(s)")
```

### Inspecting function parameters

```python
code = "def greet(name: str, /, greeting: str = 'Hi', *, loud: bool = False): pass\n"
module = parso.parse(code)
func = list(module.iter_funcdefs())[0]
for param in func.get_params():
    print(
        f"  {param.name.value}:"
        f"  position_index={param.position_index},"
        f"  star_count={param.star_count},"
        f"  has_default={param.default is not None},"
        f"  has_annotation={param.annotation is not None}"
    )
# greet has: name (pos-only), greeting (regular), loud (kw-only)
# position_index: name=0, greeting=1, loud=2
```

### Inspecting relative import levels

```python
code = "from ...utils import helper\n"
module = parso.parse(code)
imp = list(module.iter_imports())[0]
print(f"level: {imp.level}")   # -> 3
print(f"from_names: {[n.value for n in imp.get_from_names()]}")  # -> ['utils']
```

### Ancestor search

```python
module = parso.parse("class Foo:\n    def bar(self):\n        x = 1\n")
# Find the funcdef that contains a specific leaf
leaf = module.get_first_leaf()
while leaf.value != 'x':
    leaf = leaf.get_next_leaf()
enclosing_func = leaf.search_ancestor('funcdef')
print(enclosing_func.name.value)  # -> 'bar'
enclosing_class = leaf.search_ancestor('classdef')
print(enclosing_class.name.value)  # -> 'Foo'
```

---

## Position Tuples

All positions are 1-based line, 0-based column tuples `(line, column)`:
- Line 1 is the first line.
- Column 0 is the leftmost character.

`start_pos` is the position of the first character of the token/node's value
(not the prefix). `end_pos` is exclusive — it points just after the last
character.

For a `Name` leaf:
```python
leaf = module.get_first_leaf()
# leaf.start_pos: where the identifier starts
# leaf.end_pos:   leaf.start_pos[0], leaf.start_pos[1] + len(leaf.value)
```

For multi-line tokens (triple-quoted strings):
```python
code = 'x = """hello\nworld"""\n'
module = parso.parse(code)
leaf = module.get_first_leaf().get_next_leaf().get_next_leaf()  # the string
print(leaf.start_pos)  # (1, 4)
print(leaf.end_pos)    # (2, 8)
```

---

## Error Recovery

parso supports parsing syntactically invalid Python code. Errors are
represented by `ErrorNode` and `ErrorLeaf` nodes:
- `ErrorNode.type == 'error_node'`
- `ErrorLeaf.type == 'error_leaf'`

These appear in the tree where parsing failed. The roundtrip invariant still
holds for error-recovery parses: `module.get_code() == original_source`.

---

## Thread Safety and Caching

`get_used_names()` caches its result lazily in `module._used_names`. The cache
is reset to `None` when the incremental diff parser modifies the tree. The
cache is populated on the first call and reused on subsequent calls.

Multiple calls to `get_used_names()` on the same module return the same object.
