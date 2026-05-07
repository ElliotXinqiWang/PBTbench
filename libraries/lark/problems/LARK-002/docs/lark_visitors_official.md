# lark Visitor and Transformer API Documentation (v1.3.1)

## Overview

lark provides a rich framework for walking and transforming parse trees. The main entry points are `Transformer`, `Visitor`, and `Interpreter`. This document covers the visitor/transformer subsystem, the `v_args` decorator, the `Tree` search API, and `Token` manipulation.

---

## Transformer Classes

All transformer classes share the same interface: they visit every node of a parse tree and call a user-defined callback for each node whose `data` matches a method name. The callback receives the node's **already-transformed** children and returns a replacement value.

### `Transformer`

The standard recursive transformer. Processes nodes **bottom-up** (depth-first, leaves before roots). For each node:

1. Recursively transforms all children.
2. Calls the corresponding method (e.g., `def my_rule(self, children)`) with the transformed children.
3. Returns the result, which replaces the node in the output.

```python
from lark import Lark, Transformer

GRAMMAR = r"""
start: expr ("+" expr)*
expr: NUMBER
NUMBER: /[0-9]+/
%ignore " "
"""

class Eval(Transformer):
    def NUMBER(self, tok):
        return int(tok)      # Token → int
    def expr(self, children):
        return children[0]   # unwrap
    def start(self, children):
        return sum(children)

parser = Lark(GRAMMAR, parser='lalr')
tree = parser.parse('3 + 7 + 2')
result = Eval().transform(tree)   # 12
```

**Key contract**: callbacks may **assume** that all children have already been transformed. A parent rule's callback will always receive the return values of its children's callbacks, not raw `Tree` or `Token` objects.

### `Transformer_InPlace`

Non-recursive variant. Modifies the tree **in-place** rather than creating new nodes. Processes subtrees in bottom-up (postorder) order using `iter_subtrees()`. Memory-efficient for very large trees.

```python
from lark.visitors import Transformer_InPlace

class UpperCase(Transformer_InPlace):
    def NAME(self, tok):
        return tok.upper()
```

### `Transformer_InPlaceRecursive`

Recursive in-place transformer. Like `Transformer_InPlace`, it modifies the tree in-place (does not create new node instances). Like `Transformer`, it processes nodes recursively top-down (calling `_transform_tree` recursively), but the children **of each visited subtree are updated in place** before the node's own callback fires.

```python
from lark.visitors import Transformer_InPlaceRecursive

class Calc(Transformer_InPlaceRecursive):
    def NUMBER(self, tok):
        return int(tok)
    def expr(self, children):
        return children[0] + children[1]
    def start(self, children):
        return children[0]
```

**Key contract**: `_transform_tree` must update `tree.children` with the results of transforming child nodes before calling the user callback. Failing to do so means the user callback receives un-transformed (raw Token) children.

### `Transformer_NonRecursive`

Iterative (non-recursive) transformer. Equivalent to `Transformer` but uses an explicit stack to avoid Python recursion limits. Useful for extremely deep trees. Processes nodes in postorder (bottom-up).

### `TransformerChain`

Chains multiple transformers sequentially. `T1 * T2` returns a `TransformerChain` that applies `T1` first, then passes its output to `T2`.

```python
from lark.visitors import TransformerChain

chain = T1() * T2()      # T1 runs first, then T2
chain = T1() * T2() * T3()  # T1, then T2, then T3

tree_result = chain.transform(tree)
```

**Order guarantee**: `T1 * T2` must apply `T1` before `T2`. The order is determined at composition time. Calling `(T1 * T2).transform(tree)` is equivalent to `T2.transform(T1.transform(tree))`.

---

## Visitor Classes

Visitors **do not** build a new tree. They walk the existing tree and call callbacks as side effects. The tree is returned unchanged (unless modified in-place).

### `Visitor`

Non-recursive visitor. Walks the tree using an explicit stack.

```python
from lark.visitors import Visitor

class Count(Visitor):
    def __init__(self):
        self.n = 0
    def NUMBER(self, tree):
        self.n += 1
```

**`Visitor.visit(tree)`** — Bottom-up (postorder). Visits all descendants before visiting a node's parent. The root is visited last.

```python
v = Count()
v.visit(tree)    # processes leaves before root
```

**`Visitor.visit_topdown(tree)`** — Top-down (preorder). Visits the root first, then its children, ending at the leaves. The order follows `iter_subtrees_topdown()` (breadth-first).

```python
v = Count()
v.visit_topdown(tree)   # processes root before leaves
```

**Contract for `visit_topdown`**: for any parent–child pair in the tree, the parent is guaranteed to be visited **before** the child. This is the opposite of `visit()`.

```python
class SetDepth(Visitor):
    def __init__(self):
        self.depth = {}
    def __default__(self, tree):
        # Called for every node; children have NOT been visited yet
        pass
```

### `Visitor_Recursive`

Recursive visitor (may hit Python's recursion limit on deep trees). Has the same `visit()` (bottom-up) and `visit_topdown()` (top-down) API as `Visitor`.

### `VisitorBase.__default__`

Called for any tree node whose `data` does not match a method name. By default, does nothing and returns the tree.

---

## Interpreter

Unlike transformers and visitors, the `Interpreter` does **not** automatically recurse into children. The user controls traversal explicitly.

```python
from lark.visitors import Interpreter

class MyInterp(Interpreter):
    def start(self, tree):
        return self.visit_children(tree)    # explicit recursion

    def expr(self, tree):
        children = self.visit_children(tree)
        return sum(children)

    def NUMBER(self, tree):
        return int(tree.children[0])
```

**`Interpreter.visit_children(tree)`** — Visits each child that is a `Tree` by calling `self._visit_tree(child)`, and returns non-Tree children as-is. Returns the list of results.

**Contract**: Non-Tree children (tokens, literals) are returned unchanged. This allows `visit_children` to be used to selectively recurse while preserving leaf values.

---

## `v_args` Decorator

`v_args` modifies how transformer callback methods receive their arguments.

```python
from lark.visitors import v_args
```

### Parameters

- **`inline=True`**: Children are passed as `*args` (positional arguments) instead of a single list. Use when the number of children is fixed.

  ```python
  @v_args(inline=True)
  class Arith(Transformer):
      def add(self, left, right):
          return left + right   # receives two args, not [left, right]

      def number(self, n):
          return int(n)
  ```

  **Contract**: the method receives exactly `len(children)` positional arguments. If the rule can produce a variable number of children, `inline=True` is not recommended.

- **`meta=True`**: The method receives `meta` as its first argument, followed by `children` as the second argument.

  ```python
  @v_args(meta=True)
  def my_rule(self, meta, children):
      print(f"Rule at line {meta.line}")
      return children
  ```

- **`tree=True`**: The method receives the entire `Tree` object (data + children + meta) as its single argument, instead of just children.

  ```python
  @v_args(tree=True)
  def my_rule(self, tree):
      tree.children = tree.children[::-1]   # reverse children in-place
  ```

- **`wrapper=<callable>`**: Provides a custom wrapping function. Mutually exclusive with `tree`, `meta`, and `inline`.

### Class-level vs Method-level

`v_args` can decorate an entire class (applies to all methods) or a single method:

```python
@v_args(inline=True)
class T(Transformer):
    def add(self, a, b): return a + b      # inline
    def mul(self, a, b): return a * b      # inline

    @v_args(meta=True)   # overrides class-level for this method
    def expr(self, meta, children): ...
```

---

## Tree Search API

### `Tree.find_pred(pred)`

Returns an **iterator** over all subtree nodes for which `pred(node)` is `True`. Iterates using `iter_subtrees()` (bottom-up postorder).

```python
# Find all nodes whose children list has exactly 2 elements
large = list(tree.find_pred(lambda t: len(t.children) == 2))
```

### `Tree.find_data(data)`

Returns an iterator over all subtree nodes whose `data` attribute equals the given string.

```python
# Find all 'expr' nodes anywhere in the tree
exprs = list(tree.find_data('expr'))
```

**Contract**: every node `n` in the result satisfies `n.data == data`. Nodes whose `data` differs from the query are excluded.

### `Tree.find_token(token_type)`

Returns an iterator over all **leaf tokens** (non-Tree children, recursively) whose `type` attribute equals `token_type`.

```python
# Find all tokens of type 'NUMBER' anywhere in the tree
numbers = list(tree.find_token('NUMBER'))
for tok in numbers:
    assert tok.type == 'NUMBER'   # guaranteed
```

**Contract**: every element `t` in the result satisfies `isinstance(t, Token) and t.type == token_type`. Tokens of a different type are excluded from the result.

```python
# Example: tree contains NAME and NUMBER tokens
names = list(tree.find_token('NAME'))
nums  = list(tree.find_token('NUMBER'))
assert all(t.type == 'NAME'   for t in names)   # True for correct implementation
assert all(t.type == 'NUMBER' for t in nums)    # True for correct implementation
```

---

## Token API

`Token` is a subclass of `str` that carries lexical metadata.

### Constructor

```python
Token(type, value, start_pos=None, line=None, column=None,
      end_line=None, end_column=None, end_pos=None)
```

**Attributes**:
- `type` (`str`): The terminal name from the grammar (e.g., `'NUMBER'`, `'NAME'`).
- `value` (`Any`): The matched text (also the string value of the Token itself).
- `line` (`int | None`): 1-indexed line number of the token start.
- `column` (`int | None`): 1-indexed column number of the token start.
- `end_line` (`int | None`): 1-indexed line number of the token end.
- `end_column` (`int | None`): 1-indexed column just **after** the token end. For a single-char token at column 4, `end_column` is 5.
- `start_pos` (`int | None`): Zero-indexed character offset of the token start.
- `end_pos` (`int | None`): Zero-indexed character offset just after the token end.

### `Token.new_borrow_pos(type_, value, borrow_t)`

Class method. Creates a new `Token` with the given `type_` and `value`, **borrowing all position attributes** (`start_pos`, `line`, `column`, `end_line`, `end_column`, `end_pos`) from `borrow_t`.

```python
# Create a new Token of type 'IDENTIFIER' at the same position as `src_token`
new_tok = Token.new_borrow_pos('IDENTIFIER', 'foo', src_token)

# Position attributes are copied exactly:
assert new_tok.line       == src_token.line
assert new_tok.column     == src_token.column
assert new_tok.end_line   == src_token.end_line    # same end line
assert new_tok.end_column == src_token.end_column  # same end column
assert new_tok.start_pos  == src_token.start_pos
assert new_tok.end_pos    == src_token.end_pos
```

**Contract**: `new_borrow_pos` copies position attributes faithfully. In particular, `result.end_line` must equal `borrow_t.end_line` and `result.end_column` must equal `borrow_t.end_column`. Swapping these two would produce incorrect position metadata for any downstream processing (syntax highlighting, error reporting, etc.).

### `Token.update(type=None, value=None)`

Returns a new `Token` with the specified fields replaced; unspecified fields are inherited from the original token, including all position attributes.

```python
tok = Token('NAME', 'hello', start_pos=0, line=1, column=1,
            end_line=1, end_column=6, end_pos=5)

# Update only the type:
new_tok = tok.update(type='KEYWORD')
assert new_tok.type      == 'KEYWORD'
assert str(new_tok)      == 'hello'      # value preserved
assert new_tok.end_line  == tok.end_line   # position preserved
assert new_tok.end_column == tok.end_column

# Update only the value:
new_tok2 = tok.update(value='world')
assert new_tok2.type     == 'NAME'       # type preserved
assert str(new_tok2)     == 'world'
assert new_tok2.end_line == tok.end_line  # position preserved
```

**Contract**: `update()` internally calls `new_borrow_pos()`. All position attributes (including `end_line` and `end_column`) must be preserved unchanged.

### `Token.__eq__`

Two tokens are equal if they have the same string value. Additionally, if both operands are `Token` instances, they must also have the same `type`:

```python
Token('NAME', 'foo') == Token('NAME', 'foo')   # True
Token('NAME', 'foo') == Token('NUMBER', 'foo') # False — types differ
Token('NAME', 'foo') == 'foo'                  # True — str comparison
```

---

## Tree Iteration API

### `Tree.iter_subtrees()`

**Bottom-up (postorder) depth-first** iteration. Yields each subtree exactly once; a node is yielded only after all its descendants have been yielded.

```python
for subtree in tree.iter_subtrees():
    print(subtree.data)
# inner nodes appear before outer nodes
```

### `Tree.iter_subtrees_topdown()`

**Top-down (preorder) breadth-first** iteration. Yields the root first, then its children, then their children, etc.

```python
for subtree in tree.iter_subtrees_topdown():
    print(subtree.data)
# root appears before inner nodes
```

---

## Example: Complete Workflow

```python
from lark import Lark
from lark.visitors import Transformer, Visitor, v_args

GRAMMAR = r"""
start: stmt+
stmt: NAME "=" expr NEWLINE
expr: term ("+" term)*
term: NUMBER
NAME: /[a-z]+/
NUMBER: /[0-9]+/
NEWLINE: /\n/
%ignore " "
"""

@v_args(inline=True)
class Calculator(Transformer):
    def NUMBER(self, n):
        return int(n)

    def term(self, n):
        return n

    def expr(self, *terms):
        return sum(terms)

    def stmt(self, name, value, _nl):
        return (str(name), value)

    def start(self, *stmts):
        return dict(stmts)

parser = Lark(GRAMMAR, parser='lalr')
tree = parser.parse('x = 3 + 4\ny = 10\n')
result = Calculator().transform(tree)
# {'x': 7, 'y': 10}
```

---

## Summary of Key Contracts

| API | Contract |
|---|---|
| `Transformer` | Callbacks receive already-transformed children (bottom-up) |
| `Transformer_InPlaceRecursive` | Children are updated in-place before parent callback fires |
| `TransformerChain` (T1 * T2) | T1 executes before T2; composition order is preserved |
| `Visitor.visit_topdown()` | Root is visited before its descendants |
| `Tree.find_token(type)` | Returns ONLY tokens whose `type == token_type` |
| `Token.new_borrow_pos()` | Copies all position attributes including `end_line` and `end_column` |
| `Token.update()` | Preserves all position attributes of the original token |
