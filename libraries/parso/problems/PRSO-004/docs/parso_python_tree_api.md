# parso 0.8.6 — Python AST Node API Reference

This document describes the Python-specific AST node classes in `parso/python/tree.py`.
All examples use `parso.parse(code)` to produce a tree and then navigate it.

---

## 1. Tree Structure Overview

When you call `parso.parse(source_code)`, you get a `Module` node (type `'file_input'`).
The tree is built from two kinds of objects:

- **Leaf nodes** — single tokens (operators, names, keywords, literals, newlines)
- **Node/BaseNode instances** — compound nodes with a `.children` list

Each node has:
- `.type` — a string like `'funcdef'`, `'classdef'`, `'expr_stmt'`, `'with_stmt'`
- `.children` — list of child nodes (nodes only, not leaves)
- `.parent` — the parent node
- `.start_pos`, `.end_pos` — `(line, column)` tuples

---

## 2. Function and Lambda Nodes

### `Function` (type `'funcdef'`)

Created for every `def` statement.

```python
import parso
module = parso.parse("def add(a, b=0):\n    return a + b\n")
func = list(module.iter_funcdefs())[0]
print(func)          # <Function: add@1-2>
print(func.name)     # <Name: add@1,4>
```

**Key methods:**

#### `func.get_params()` → `list[Param]`

Returns the list of `Param` nodes for all named parameters. Separator tokens
(`*`, `/`) are excluded from the returned list.

```python
module = parso.parse("def foo(a, b, *args, c=1, **kw): pass\n")
func = list(module.iter_funcdefs())[0]
params = func.get_params()
# [Param(a), Param(b), Param(*args), Param(c=1), Param(**kw)]
print([p.name.value for p in params])  # ['a', 'b', 'args', 'c', 'kw']
```

**Invariant:** `len(func.get_params())` equals the number of named parameters
(i.e., all params that have a name — positional, `*`, `**`, keyword-only, default).

#### `func.is_generator()` → `bool`

Returns `True` if the function body contains a `yield` expression.

```python
module = parso.parse("def gen():\n    yield 1\n    yield 2\n")
func = list(module.iter_funcdefs())[0]
print(func.is_generator())  # True
```

#### `func.annotation` → node or `None`

Returns the return type annotation node (after `->`) or `None`.

```python
module = parso.parse("def foo() -> int:\n    pass\n")
func = list(module.iter_funcdefs())[0]
print(func.annotation)  # <Name: int@1,10>
```

### `Lambda` (type `'lambdef'`)

Similar to `Function`. Has `get_params()` but no `name` attribute (raises `AttributeError`)
and no `annotation`.

---

## 3. Class Nodes

### `Class` (type `'classdef'`)

Created for every `class` statement.

```python
module = parso.parse("class Foo(Base1, Base2):\n    pass\n")
cls = list(module.iter_classdefs())[0]
print(cls.name)           # <Name: Foo@1,6>
```

#### `cls.get_super_arglist()` → node or `None`

Returns the argument list node of the base-class parentheses, or `None` if the
class has no parentheses or has empty parentheses.

```python
# class Foo: — no parens
module = parso.parse("class Foo:\n    pass\n")
cls = list(module.iter_classdefs())[0]
print(cls.get_super_arglist())   # None

# class Foo(): — empty parens
module = parso.parse("class Foo():\n    pass\n")
cls = list(module.iter_classdefs())[0]
print(cls.get_super_arglist())   # None

# class Foo(Base): — one base class
module = parso.parse("class Foo(Base):\n    pass\n")
cls = list(module.iter_classdefs())[0]
arglist = cls.get_super_arglist()
print(arglist)                   # <Name: Base@1,10>  (a single Name node)
```

---

## 4. Decorator Support — `get_decorators()`

Both `Function` and `Class` inherit from `ClassOrFunc`, which provides `get_decorators()`.

#### `node.get_decorators()` → `list[Decorator]`

Returns the list of `Decorator` nodes (type `'decorator'`) applied to the function
or class. If there are no decorators, returns `[]`.

**Grammar structure:**

- **No decorators:** the `funcdef`/`classdef` node is a direct child of a `suite`
  or `file_input`. `get_decorators()` returns `[]`.

- **One decorator:** parso wraps them in a `decorated` node:
  ```
  decorated
  ├── decorator      (@property\n)
  └── funcdef        (def foo(): ...)
  ```
  `get_decorators()` returns `[<Decorator: @property@...>]` — a list of length 1.

- **Multiple decorators:** parso adds an extra `decorators` wrapper:
  ```
  decorated
  ├── decorators
  │   ├── decorator  (@property\n)
  │   └── decorator  (@staticmethod\n)
  └── funcdef        (def foo(): ...)
  ```
  `get_decorators()` returns `[<Decorator: @property@...>, <Decorator: @staticmethod@...>]`
  — a list whose length equals the number of `@` lines.

**Invariants:**
1. The length of `get_decorators()` equals the number of `@decorator` lines before
   the function/class definition.
2. Every element in the returned list has `.type == 'decorator'`.
3. Async functions wrapped in `async def` with decorators are also handled:
   `get_decorators()` correctly traverses the `async_funcdef` wrapper.

```python
module = parso.parse("@property\n@staticmethod\ndef foo(): pass\n")
func = list(module.iter_funcdefs())[0]
decs = func.get_decorators()
print(len(decs))                    # 2
print(all(d.type == 'decorator' for d in decs))  # True
print(decs[0].children[1].value)    # 'property'
print(decs[1].children[1].value)    # 'staticmethod'
```

```python
module = parso.parse("@my_decorator\ndef bar(): pass\n")
func = list(module.iter_funcdefs())[0]
decs = func.get_decorators()
print(len(decs))   # 1
print(decs[0].type)  # 'decorator'
```

---

## 5. Expression Statements — `ExprStmt`

### `ExprStmt` (type `'expr_stmt'`)

Covers all assignment forms:

| Code example       | Description                           |
|--------------------|---------------------------------------|
| `a = 1`            | simple assignment                     |
| `a = b = 1`        | chained assignment                    |
| `a += 1`           | augmented assignment (`+=`, `-=`, …)  |
| `x: int = 5`       | annotated assignment with value       |
| `x: int`           | annotated assignment without value    |

#### `expr_stmt.get_defined_names(include_setitem=False)` → `list[Name]`

Returns the `Name` leaf nodes that are **defined** (assigned) in this statement.
This includes:

- All names on the left-hand side of `=` in a simple or chained assignment:
  `a = b = 1` → `[Name('a'), Name('b')]`
- The name on the left of an augmented assignment:
  `a += 1` → `[Name('a')]`, `x //= 2` → `[Name('x')]`
- The name being annotated in an annotated assignment:
  `x: int = 5` → `[Name('x')]`, `x: int` → `[Name('x')]`

**Augmented assignment operators** (all contain `=` as a substring):
`+=`, `-=`, `*=`, `/=`, `//=`, `%=`, `**=`, `&=`, `|=`, `^=`, `>>=`, `<<=`

**Invariant:** for any assignment statement where a name is visibly being assigned
or modified, `get_defined_names()` must include that name. In particular, augmented
assignments (`x += 1`, `x //= 2`, etc.) **do** define the left-hand-side name.

```python
module = parso.parse("a = 1\n")
es = module.children[0].children[0]   # expr_stmt
print(es.get_defined_names())         # [<Name: a@1,0>]

module = parso.parse("a += 5\n")
es = module.children[0].children[0]
print(es.get_defined_names())         # [<Name: a@1,0>]

module = parso.parse("x -= 3\n")
es = module.children[0].children[0]
print(es.get_defined_names())         # [<Name: x@1,0>]

module = parso.parse("result **= 2\n")
es = module.children[0].children[0]
print(es.get_defined_names())         # [<Name: result@1,0>]
```

#### `expr_stmt.get_rhs()` → node

Returns the **right-hand-side** node of the assignment statement.

- Simple assignment `a = expr` → returns the `expr` node.
- Chained assignment `a = b = expr` → returns the last `expr` node.
- Annotated assignment with value `x: int = val` → returns the `val` node.
- Bare annotation `x: int` → returns the type annotation node (`int`).

**Grammar note:** An annotated assignment `x: int = 5` parses as:
```
expr_stmt
├── Name('x')
└── annassign
    ├── Operator(':')
    ├── Name('int')    ← children[1]: the type annotation
    ├── Operator('=')
    └── Number('5')    ← children[3]: the RHS value
```
The `annassign` node has **4 children** when a value is present, and **2 children**
when it is a bare annotation. `get_rhs()` must return `children[3]` (the value) for
the 4-children case, and `children[1]` (the annotation) for the 2-children case.

```python
module = parso.parse("x: int = 42\n")
es = module.children[0].children[0]
rhs = es.get_rhs()
print(rhs)           # <Number: 42@1,10>
print(rhs.value)     # '42'

module = parso.parse("x: int\n")
es = module.children[0].children[0]
rhs = es.get_rhs()
print(rhs)           # <Name: int@1,3>   (the type annotation)

module = parso.parse("a = b = 'hello'\n")
es = module.children[0].children[0]
rhs = es.get_rhs()
print(rhs)           # <String: 'hello'@1,8>
```

**Invariant:** for `x: T = val`, `get_rhs()` must return the value node `val`, not
the type annotation `T`. The value and the type annotation are different nodes with
different positions and typically different `.type` values.

---

## 6. With Statements — `WithStmt`

### `WithStmt` (type `'with_stmt'`)

Covers `with` statements with one or more context managers.

#### `with_stmt.get_defined_names(include_setitem=False)` → `list[Name]`

Returns the names bound by `as` clauses in the `with` statement.

**Grammar structure for `with_item`:**
```
with_item
├── children[0]  — the context manager expression (e.g., open('file'), lock, ctx())
├── children[1]  — the keyword 'as'
└── children[2]  — the bound name (e.g., Name('fp'), Name('result'))
```

The bound name is **always at index 2** in `with_item.children`. Index 0 is the
context manager expression, which is not the name being defined.

**Invariant:** `with ctx() as name:` → `get_defined_names()` returns `[Name('name')]`.
Multiple context managers: `with A() as a, B() as b:` → `[Name('a'), Name('b')]`.

```python
module = parso.parse("with open('file.txt') as f:\n    pass\n")
# Find the with_stmt node
from parso.python.tree import WithStmt
def find_with(node):
    if node.type == 'with_stmt':
        return node
    try:
        for child in node.children:
            r = find_with(child)
            if r: return r
    except AttributeError:
        pass

ws = find_with(module)
names = ws.get_defined_names()
print(names)                      # [<Name: f@1,23>]
print(names[0].value)             # 'f'

module = parso.parse("with lock() as a, conn() as b:\n    pass\n")
ws = find_with(module)
print([n.value for n in ws.get_defined_names()])  # ['a', 'b']
```

**Note:** `with` statements without `as` clauses have `get_defined_names()` return `[]`.
```python
module = parso.parse("with ctx():\n    pass\n")
ws = find_with(module)
print(ws.get_defined_names())  # []
```

---

## 7. Scope and Module Methods

### `Scope.iter_funcdefs()` → generator of `funcdef` nodes

Recursively scans the scope's children and yields all `funcdef` nodes at any
depth. Respects control flow containers (if/for/while/try/with) and function
containers (suite, decorated, async_funcdef). Does **not** recurse into nested
function or class bodies.

### `Scope.iter_classdefs()` → generator of `classdef` nodes

Same as `iter_funcdefs()` but yields `classdef` nodes.

### `Module.get_used_names()` → `UsedNamesMapping`

Returns a mapping from name strings to lists of `Name` leaf nodes. The lists
are in source order (ascending `start_pos`). All occurrences of a name across
the entire module are collected.

```python
module = parso.parse("x = 1\nprint(x)\ny = x + 1\n")
used = module.get_used_names()
print([n.start_pos for n in used['x']])  # [(1, 0), (2, 6), (3, 4)]
```

---

## 8. Param Nodes

### `Param` (type `'param'`)

**Properties:**
- `.name` — the `Name` leaf of the parameter
- `.star_count` — `0` for plain params, `1` for `*param`, `2` for `**param`
- `.default` — the default value node after `=`, or `None`
- `.annotation` — the type annotation node after `:`, or `None`

**Iteration:** use `func.get_params()` to get only `Param` objects (excluding `*` and `/` separators).

```python
module = parso.parse("def foo(a, b: int = 0, *args, c, **kw): pass\n")
func = list(module.iter_funcdefs())[0]
for param in func.get_params():
    print(param.name.value, 'star_count:', param.star_count,
          'has_default:', param.default is not None)
# a   star_count: 0  has_default: False
# b   star_count: 0  has_default: True
# args star_count: 1  has_default: False
# c   star_count: 0  has_default: False
# kw  star_count: 2  has_default: False
```

---

## 9. Import Nodes

### `ImportFrom` (type `'import_from'`)

**`level`** property: the number of leading dots in a relative import.

```python
module = parso.parse("from . import x\n")
imp = list(module.iter_imports())[0]
print(imp.level)   # 1

module = parso.parse("from .. import y\n")
imp = list(module.iter_imports())[0]
print(imp.level)   # 2

module = parso.parse("from ... import z\n")
imp = list(module.iter_imports())[0]
print(imp.level)   # 3
```

---

## 10. Summary of Key Invariants for PBT

These invariants should all hold on any valid parsed Python code:

| API | Invariant |
|-----|-----------|
| `func.get_decorators()` | Length equals number of `@` lines; each element has `.type == 'decorator'` |
| `expr_stmt.get_defined_names()` | Augmented assignments `a OP= b` define `a`; all assignment operators (including `+=`, `-=`, etc.) are recognized |
| `with_stmt.get_defined_names()` | `with ctx() as name:` returns `[Name('name')]`; bound name is always at index 2 in `with_item.children` |
| `expr_stmt.get_rhs()` | For `x: T = val` (annotated assignment with value), returns `val` node, not `T`; annassign with value has 4 children (`[':', T, '=', val]`) |
| `func.get_params()` | Returns only `Param` objects (not separator tokens); count matches named parameters |
| `imp.level` | `from {"."*N} import x` → `level == N`; `'...'` token counts as 3 |
