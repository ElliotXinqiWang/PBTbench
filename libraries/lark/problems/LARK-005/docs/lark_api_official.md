# lark API Documentation (v1.3.1)

## Overview

lark is a modern parsing library for Python. It implements EBNF/PEG grammars and provides two parsing algorithms: LALR(1) and Earley. It includes a rich framework for traversing and transforming parse trees.

---

## Lark — Main Parser Class

```python
from lark import Lark

parser = Lark(grammar, parser='lalr')   # or 'earley'
tree = parser.parse(text)               # returns a Tree
```

`parser.parse(text)` raises `UnexpectedInput` if `text` does not match the grammar.

---

## Tree — Parse Tree Node

```python
from lark import Tree

tree = Tree(data, children, meta=None)
```

**Attributes**:
- `data` (`str`): The name of the grammar rule or alias that produced this node.
- `children` (`list`): List of child nodes. Each element is either a `Tree` or a `Token`.
- `meta`: Position metadata (available when `propagate_positions=True`).

**Key methods**:

### `Tree.__eq__(other)`
Two Trees are **equal** if and only if **both** `data` and `children` are equal:
```python
Tree('a', [1]) == Tree('a', [1])   # True
Tree('a', [1]) == Tree('b', [1])   # False — data differs
Tree('a', [1]) == Tree('a', [2])   # False — children differ
```

### `Tree.pretty(indent_str='  ')`
Returns an indented string representation of the tree. Each nesting level is indented by one additional `indent_str` (default two spaces).

**Contract**:
- The root node (depth 0) has **no** leading whitespace.
- A node at depth `d` has exactly `d * len(indent_str)` leading spaces.
- A node's children appear on subsequent lines, each indented one level deeper.

```python
t = Tree('root', [Tree('child', ['leaf'])])
print(t.pretty())
# root
#   child	leaf
```

For a tree of depth 2:
```python
t = Tree('root', [Tree('a', [Tree('b', ['x'])])])
print(t.pretty())
# root
#   a
#     b	x
```

### `Tree.iter_subtrees()`
**Bottom-up (postorder) depth-first** iteration. Yields all subtrees; each subtree is yielded only after all its descendants have been yielded. Leaves are visited before their parents.

### `Tree.iter_subtrees_topdown()`
**Top-down (preorder) breadth-first** iteration. The root is yielded first, then its children, etc. Parents are visited before their descendants.

### `Tree.scan_values(pred)`
Recursively yields all leaf values (non-Tree children) for which `pred(value)` is True.

---

## Token — Lexer Token

```python
from lark import Token

tok = Token(type, value, start_pos=None, line=None, column=None,
            end_line=None, end_column=None, end_pos=None)
```

`Token` inherits from `str`, so `str(token) == token.value` always holds.

**Position attributes** (populated by the lexer during parsing):
- `line` (`int`): The **1-indexed** line number where the token starts. Line 1 is the first line.
- `column` (`int`): The **1-indexed** column number where the token starts. Column 1 is the **first character on a line**.
- `end_line` (`int`): Line number where the token ends.
- `end_column` (`int`): Column number **after** the last character of the token. For a single-character token at column 4, `end_column` is 5.
- `start_pos` (`int`): Zero-indexed character offset from the start of the input string.
- `end_pos` (`int`): Character offset just past the last character of the token.

**Important**: Both `line` and `column` are 1-indexed. The very first character of any input has `line=1, column=1`. The character after a newline has `column=1` on the next line.

---

## Transformer — Bottom-Up Tree Transformation

```python
from lark import Transformer

class MyTransformer(Transformer):
    def rule_name(self, children):
        # called when a 'rule_name' node is visited
        # children have already been transformed
        return ...

    def TOKEN_TYPE(self, token):
        # called for each token of this type
        return ...

result = MyTransformer().transform(tree)
```

**Documented contract**: Transformers work **bottom-up (depth-first)**, starting with the leaves and working up to the root. When a callback for a rule is called, all of its children have **already been transformed**. This allows callbacks to assume children are already typed values (not raw Token objects).

All Transformer variants share this bottom-up contract:

### `Transformer` (base class)
Recursive, non-in-place. Returns new tree instances. Suitable for most uses.

```python
def transform(self, tree):
    # internally calls _transform_children recursively
    # children are transformed before parent callbacks
```

### `Transformer_InPlace`
Non-recursive. Modifies the tree in-place instead of creating new instances.
Useful for large trees (memory-efficient).

**Contract**: same bottom-up order as `Transformer`. Callbacks are invoked after all descendants have been processed.

```python
class DoubleNumbers(Transformer_InPlace):
    def NUMBER(self, tok):
        return Token('NUMBER', str(int(tok) * 2))
```

### `Transformer_InPlaceRecursive`
Recursive, in-place. Same bottom-up semantics.

### `Transformer_NonRecursive`
Non-recursive, non-in-place. Implements the same bottom-up transformation without recursion.

---

## Visitor — Bottom-Up Tree Visitor

```python
from lark import Visitor

class MyVisitor(Visitor):
    def rule_name(self, tree):
        # modify tree.children in place
        pass

MyVisitor().visit(tree)  # bottom-up: leaves first
MyVisitor().visit_topdown(tree)  # top-down: root first
```

`Visitor.visit()` is **bottom-up**: children are visited before parents.
`Visitor.visit_topdown()` is **top-down**: parents are visited before children.

---

## Interpreter — Top-Down Tree Interpreter

Unlike Transformer and Visitor, the Interpreter starts at the root and works top-down. The user explicitly calls `self.visit_children(tree)` to recurse.

---

## Grammar Syntax (EBNF)

```
start: rule+
rule: TERMINAL rule?
TERMINAL: /regex/ | "literal"
%ignore /whitespace_pattern/
```

- Rules are lowercase; terminals are UPPERCASE.
- `?` = optional, `+` = one or more, `*` = zero or more.
- `%ignore` patterns are matched and discarded by the lexer.

---

## LineCounter

Internal class used by the lexer to track position.

**Contract**: After consuming each token, the lexer updates:
- `line`: current line number (1-indexed, starts at 1)
- `column`: current column number (1-indexed, starts at 1)
- `char_pos`: zero-indexed absolute position in input

The column of the **first character** on any line is always **1** (not 0).

---

## Common Patterns

### Arithmetic evaluator using Transformer:
```python
from lark import Lark, Transformer, v_args

grammar = r"""
    start: expr
    expr: NUMBER "+" NUMBER
    NUMBER: /[0-9]+/
    %ignore " "
"""
parser = Lark(grammar, parser='lalr')

class Calc(Transformer):
    def NUMBER(self, tok):
        return int(tok)          # converts Token to int
    def expr(self, c):
        return c[0] + c[1]      # c[0] and c[1] are already ints

tree = parser.parse('3 + 4')
result = Calc().transform(tree)   # result == Tree('start', [7])
```

### Checking token positions:
```python
grammar = r"""
    start: NAME+
    NAME: /[a-z]+/
    %ignore " "
"""
parser = Lark(grammar, parser='lalr')
tree = parser.parse('foo bar')
for tok in tree.scan_values(lambda v: True):
    print(tok, tok.line, tok.column)
# foo 1 1
# bar 1 5
```

### Tree equality:
```python
from lark import Tree
assert Tree('a', [1, 2]) == Tree('a', [1, 2])   # same data, same children
assert Tree('a', [1, 2]) != Tree('b', [1, 2])   # different data
assert Tree('a', [1, 2]) != Tree('a', [1, 3])   # different children
```
