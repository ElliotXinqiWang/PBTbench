# Lark Internals API Documentation

**Library**: lark 1.3.1
**Scope**: Parse-tree builder internals, Tree traversal, scan_values, Transformer

---

## 1. Overview

Lark is a parsing toolkit that parses text according to an EBNF/PEG grammar and
produces a tree of `Tree` and `Token` objects. The library has two main layers:

1. **Parsing layer** — LALR(1) and Earley parsers that drive the grammar rules.
2. **Tree layer** — `Tree`, `Token`, and visitor/transformer classes for post-processing
   the parse result.

The internal **parse-tree builder** (`parse_tree_builder.py`) sits between the raw
parser and the user-visible `Tree`. It handles inlining of anonymous rules, filtering
of "discard" terminals, and optional placeholder insertion.

---

## 2. `ChildFilter` and `ChildFilterLALR`

### Purpose

When a grammar rule is parsed, the LALR(1) engine produces a flat list of children
(the right-hand side symbols). The `ChildFilter` family of classes post-processes
this list before the `Tree` is constructed:

- **Discard tokens** marked `filter_out` (e.g., anonymous literals like `"+"` or `","`)
- **Inline children** of sub-rules whose names start with `_` (anonymous/transparent rules)
- **Insert `None` placeholders** for optional symbols that did not match (when
  `maybe_placeholders=True`)

### `ChildFilter` (base, used for Earley / ambiguous grammars)

```
ChildFilter(to_include, append_none, node_builder)
```

`to_include` is a list of `(index, to_expand, add_none)` tuples:
- `index` — position in the raw child list
- `to_expand` — `True` if this child is an anonymous sub-rule whose children should
  be inlined into the parent
- `add_none` — how many `None` placeholders to insert before this child

When `to_expand` is `True`, the child's `.children` list is appended to the
accumulated result.

### `ChildFilterLALR` (optimized for LALR)

```
ChildFilterLALR(to_include, append_none, node_builder)
```

Identical contract to `ChildFilter` but with a performance optimization for
**left-recursive** grammars:

> When the accumulated `filtered` list is **empty** at the time a `to_expand` entry
> is processed (which happens only for the *first* expansion in a left-recursive rule),
> the implementation directly assigns the child's `.children` list to `filtered`
> (avoiding a list copy). For **all subsequent** `to_expand` entries where `filtered`
> is already non-empty, the child's children are **appended** to `filtered` with `+=`.

**Contract**: After processing all `to_include` entries, `filtered` must contain
*every* child from every expanded sub-rule, in order. The optimization must not
alter the final content — only the cost of constructing the list.

**Important**: Rules with multiple inlined (`_`-prefixed) sub-rules produce multiple
`to_expand` entries. All of them must contribute their children to the result. For
a grammar rule `start: _xs _ys` where `_xs` and `_ys` are both left-recursive, a
parse of N items must yield exactly N Token children in `start`.

### `ChildFilterLALR_NoPlaceholders`

A further optimization that omits placeholder (`None`) handling. Same left-recursion
optimization and same contract.

### `maybe_create_child_filter`

```python
maybe_create_child_filter(expansion, keep_all_tokens, ambiguous, _empty_indices)
```

Factory function that selects the appropriate `ChildFilter` subclass based on the
grammar options. Returns `None` if no filtering is needed (all children are kept
as-is with no inlining).

---

## 3. `Tree` class

```python
class Tree:
    data: str         # rule or alias name
    children: list    # list of Tree or Token objects
```

### `Tree.iter_subtrees_topdown() -> Iterator[Tree]`

**Documented contract**: Iterates over all subtrees (Tree nodes), yielding nodes
in **breadth-first, left-to-right order** — root first, then its children
left-to-right, then grandchildren left-to-right, etc. The documentation states:

> "Iterates over all the subtrees, return nodes in order like pretty() does."

The `pretty()` method renders the tree root first, then children from left to right
(depth-first pre-order). Therefore, `iter_subtrees_topdown()` must yield sibling
subtrees in the same **left-to-right** order as they appear in `tree.children`.

**Implementation note**: The method uses a stack (LIFO). To achieve left-to-right
output for siblings, children must be pushed in **reversed order** so the leftmost
child is popped first.

**Invariant**:
- For a tree with children `[A, B, C]`, `iter_subtrees_topdown()` must yield the
  root, then `A`, then `B`, then `C` (and their descendants) — not `C`, `B`, `A`.
- Equivalently: if you record `n.data` for each `n` yielded by
  `iter_subtrees_topdown()`, the list must match the node names as they appear
  in `pretty()` output (top-to-bottom, left-to-right).

**Example**:
```python
root = Tree('root', [Tree('left', ['a']), Tree('right', ['b'])])
names = [n.data for n in root.iter_subtrees_topdown()]
# Correct: ['root', 'left', 'right']
# Wrong:   ['root', 'right', 'left']
```

### `Tree.iter_subtrees() -> Iterator[Tree]`

Iterates over all subtrees in **bottom-up (postorder)** order — leaves first, root
last. This is the *reverse* of `iter_subtrees_topdown()`.

**Invariant**: The root is always the **last** element yielded by `iter_subtrees()`.

### `Tree.scan_values(pred) -> Iterator`

```python
def scan_values(self, pred: Callable[[Any], bool]) -> Iterator
```

**Documented contract**: Recursively walk all tree nodes and yield each **leaf value**
(non-Tree child) for which `pred(value)` evaluates to **`True`**.

- Only leaf values (direct non-Tree children) are tested against `pred`.
- Tree nodes are recursed into but never directly yielded.
- A leaf is yielded **if and only if** `pred(leaf)` is `True`.

**Invariants**:
- `list(tree.scan_values(lambda v: False))` must always be `[]` — the never-True
  predicate returns no values.
- `list(tree.scan_values(lambda v: isinstance(v, Token)))` must return exactly all
  `Token` leaf values in the tree (in depth-first, left-to-right order).
- For any predicate `P`, every element in `list(tree.scan_values(P))` must satisfy
  `P(element) == True`.

**Example**:
```python
tree = Lark("start: NUMBER+ \n NUMBER: /[0-9]+/").parse("1 2 3")
tokens = list(tree.scan_values(lambda v: isinstance(v, Token)))
# Returns all 3 NUMBER tokens

digits_only = list(tree.scan_values(lambda v: isinstance(v, Token) and v.type == 'NUMBER'))
# Returns only NUMBER tokens (same here, but predicate is more selective)
```

### `Tree.find_token(token_type) -> Iterator[Token]`

Convenience wrapper around `scan_values`:
```python
def find_token(self, token_type: str) -> Iterator[Token]:
    return self.scan_values(lambda v: isinstance(v, Token) and v.type == token_type)
```

Returns all tokens whose `.type` equals `token_type`. Every returned token is
guaranteed to be a `Token` instance with `.type == token_type`.

### `Tree.find_pred(pred) -> Iterator[Tree]`

Returns all **Tree nodes** (not leaf values) that satisfy `pred`. Uses
`iter_subtrees()` (bottom-up) internally.

### `Tree.find_data(data) -> Iterator[Tree]`

Returns all `Tree` nodes whose `.data` attribute equals `data`.

### `Tree.pretty(indent_str='  ') -> str`

Renders the tree as an indented string. The root appears at indent level 0 (no
leading whitespace). Each level of nesting adds one `indent_str` of indentation.
Children appear left-to-right, depth-first.

---

## 4. `Transformer` class

```python
class Transformer:
    def transform(self, tree: Tree) -> Any
```

**Documented contract**: Transformers work **bottom-up (depth-first)**, starting
with the leaves and working up to the root. For each node, the transformer calls
the method named after `tree.data` (if defined), passing the **already-transformed**
children as a list argument. The return value replaces the node in the parent.

**Key invariant — transformed children**:
> When a parent rule's callback is invoked, its `children` argument must contain
> the values returned by the child callbacks — not the original `Token` objects.

For example, if a `NUMBER` token callback converts `Token → int`, then when the
parent `expr` callback fires, `children[0]` must be an `int`, not a `Token`.

### `Transformer._transform_children(children)`

Iterates over children; for each `Tree` child, recursively calls `_transform_tree`;
for each `Token` child, calls `_call_userfunc_token`. Yields transformed values
(skipping `Discard`).

### `Transformer._transform_tree(tree)`

Core per-node transform:
1. Collects transformed children by calling `_transform_children(tree.children)`.
2. Calls `_call_userfunc(tree, transformed_children)` with those transformed children.
3. Returns the result.

**Critical**: The second argument to `_call_userfunc` must be the **transformed**
children list (step 1 result), not the original `tree.children`.

### `Transformer._call_userfunc(tree, new_children=None)`

Looks up the method named `tree.data` on the transformer instance and calls it
with `new_children` as the children list. If no method is found, calls
`__default__(tree.data, new_children, tree.meta)`.

### `Transformer.__default__(data, children, meta)`

Default callback when no method matches `data`. Returns `Tree(data, children, meta)`.

### `Transformer.transform()` entry point

```python
def transform(self, tree: Tree) -> Any:
    res = list(self._transform_children([tree]))
    ...
    return res[0]
```

Calls `_transform_children` with the root as the sole element, which internally
calls `_transform_tree(root)`, which recursively transforms the entire tree
bottom-up.

### `Transformer_InPlace`

Non-recursive variant. Iterates over subtrees using `iter_subtrees()` (bottom-up),
transforming children in-place before calling the node's callback. Useful for very
large trees where recursion depth is a concern.

### `Transformer_InPlaceRecursive`

Recursive variant that modifies the tree in-place. Each node's `children` attribute
is replaced with the list of transformed children before the node callback fires.

---

## 5. `Visitor` and `Visitor_Recursive`

### `Visitor.visit(tree)` — bottom-up

Calls the callback for each subtree in `iter_subtrees()` order (leaves first,
root last). Returns the tree (modified in place by callbacks).

### `Visitor.visit_topdown(tree)` — top-down

Calls the callback for each subtree in `iter_subtrees_topdown()` order (root first,
leaves last). Returns the tree.

### `Visitor_Recursive.visit(tree)` — bottom-up, recursive

Recursively visits children first, then calls the callback for the current node.
Root callback is invoked last.

### `Visitor_Recursive.visit_topdown(tree)` — top-down, recursive

Calls the callback for the current node first, then recursively visits children.
Root callback is invoked first.

---

## 6. Grammar features relevant to tree building

### Anonymous / transparent rules (`_` prefix)

Rules whose name starts with `_` are **transparent**: their children are inlined
into the parent tree node instead of creating a subtree. For example:

```
start: _items
_items: _items ITEM | ITEM
```

With input `"a b c"`, instead of `Tree('start', [Tree('_items', [...])])`,
you get `Tree('start', [Token('ITEM','a'), Token('ITEM','b'), Token('ITEM','c')])`.

The inlining is performed by `ChildFilter` / `ChildFilterLALR` during tree
construction, using the `to_expand` flag. The contract is that **all** children
from all inline points are accumulated in order — none are dropped.

### `?` prefix (expand single child)

Rules prefixed with `?` are inlined when they have exactly one child (they are
"transparent single-child" rules). This is handled by `ExpandSingleChild`.

### `keep_all_tokens` option

By default, literal string terminals (anonymous terminals used in grammar rules
like `"+"` or `","`) are filtered out of the tree. Setting `keep_all_tokens=True`
retains them.

### Terminal priority

Terminals can be given an explicit priority number: `NAME.2: /.../ `. Higher
priority numbers are matched first when two terminals could match the same input.
The default priority is 0.

---

## 7. `Token` class

```python
class Token(str):
    type: str
    value: str
    line: int        # 1-indexed
    column: int      # 1-indexed
    end_line: int
    end_column: int  # column after last character (exclusive)
    start_pos: int   # absolute character offset
    end_pos: int
```

`Token` inherits from `str`, so `str(token) == token.value` always.

**Column is 1-indexed**: the first character on any line has `column=1`.
`end_column` is one past the last character: a single-character token at column 4
has `end_column=5`.

---

## 8. Testing with Hypothesis

When writing property-based tests for lark, recommended strategies:

```python
from hypothesis import given, settings, strategies as st
from lark import Lark, Tree, Token

# Generate integers and format as number tokens
@given(st.lists(st.integers(0, 999), min_size=1, max_size=10))
@settings(max_examples=500, deadline=None)
def test_parse_property(nums):
    text = " ".join(str(n) for n in nums)
    ...
```

- Use `@settings(max_examples=500, deadline=None)` — parsing can be slow.
- Use `assume()` to filter edge cases.
- The `scan_values` method is useful for collecting all tokens from a tree.
