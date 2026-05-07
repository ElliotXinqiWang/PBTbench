# Lark Parser Internals — Official API Reference

**Library**: lark 1.3.1
**Scope**: Terminal priority, Visitor_Recursive, Transformer_InPlaceRecursive, rule priority conflict resolution

---

## Overview

Lark is a parsing library that transforms a grammar string into a parser. Grammar rules
produce `Tree` objects; matched text produces `Token` objects. Lark supports multiple
parser backends (LALR, Earley) and a rich tree visitor/transformer framework.

---

## Terminal Priority

### Syntax

```
TERMINAL_NAME.priority: pattern
```

A terminal definition may include a priority number after a dot:

```
TOKEN_A.2: "hello"
TOKEN_B.1: /[a-z]+/
```

The priority is an integer. The default priority is **0**.

### Resolution Rule

When multiple terminals could match the same input text, the terminal with the
**highest priority number wins**. In the example above, the string `"hello"` will
always match `TOKEN_A` (priority 2), never `TOKEN_B` (priority 1), even though
the regex `/[a-z]+/` would also match it.

If two terminals have the **same priority** and both match the same text, the one
with the longer match is preferred. For string literals vs. regex patterns of the
same priority, string literals (PatternStr) take precedence over regex patterns
(PatternRE) through the `UnlessCallback` mechanism.

### Lexer Initialization

The lexer sorts all terminal definitions before building the scanner. **Higher-priority
terminals are placed earlier** so that the regex alternation engine tries them first.
The sort order is:

```
(-priority, -max_width, -len(pattern_value), terminal_name)
```

This guarantees that priority `.2` terminals appear before `.1` terminals in the
scanner, which in turn ensures the correct terminal is selected for ambiguous inputs.

### Example

```python
from lark import Lark

grammar = r"""
    start: (KW | NAME)+
    KW.2: "if" | "else" | "while"
    NAME.1: /[a-z][a-z0-9_]*/
    %ignore /\s+/
"""
parser = Lark(grammar, parser='lalr')
tree = parser.parse('if hello')
# tree.children: [Token('KW', 'if'), Token('NAME', 'hello')]
```

With priority correctly applied, `"if"` is always matched as `KW` (priority 2),
and ordinary words like `"hello"` are matched as `NAME` (priority 1).

---

## Visitor_Recursive

### Class Definition

```python
class Visitor_Recursive(VisitorBase):
    """Bottom-up visitor, recursive.

    Visiting a node calls its methods according to tree.data.
    Slightly faster than the non-recursive version (Visitor).
    """

    def visit(self, tree: Tree) -> Tree:
        "Visits the tree, starting with the leaves and finally the root (bottom-up)"
        ...

    def visit_topdown(self, tree: Tree) -> Tree:
        "Visit the tree, starting at the root, and ending at the leaves (top-down)"
        ...
```

### `visit()` — Bottom-Up Traversal

The `visit()` method implements **bottom-up (depth-first) traversal**:

1. Recursively visit all child subtrees first.
2. Then call the user callback for the current node.

This means: **leaves are processed before their parents**. For a tree:

```
start
└── a
    └── b
        └── c
```

The visit order of `visit()` is: `c → b → a → start`.

### `visit_topdown()` — Top-Down Traversal

The `visit_topdown()` method implements **top-down traversal**:

1. Call the user callback for the current node.
2. Then recursively visit all child subtrees.

Visit order: `start → a → b → c`.

### User Callbacks

Override methods named after the rule they handle:

```python
from lark.visitors import Visitor_Recursive

class MyVisitor(Visitor_Recursive):
    def item(self, tree):
        # Called for each 'item' node, AFTER all its children are visited
        print("visiting item:", tree)

    def start(self, tree):
        # Called last (root), after all items have been processed
        print("visiting start")
```

The `__default__` method is called for any node without a specific handler.

### Bottom-Up Guarantee

The documented contract: when `visit()` calls your callback for node N, all
callbacks for N's descendants have **already been called**. You can rely on
the state accumulated from child nodes when processing a parent node.

### Comparison with Other Visitors

| Class | Traversal | Recursive | In-Place |
|---|---|---|---|
| `Visitor` | Bottom-up | No (uses `iter_subtrees()`) | Yes |
| `Visitor_Recursive` | Bottom-up | Yes | Yes |
| `Visitor.visit_topdown()` | Top-down | No | Yes |
| `Visitor_Recursive.visit_topdown()` | Top-down | Yes | Yes |

---

## Transformer_InPlaceRecursive

### Class Definition

```python
class Transformer_InPlaceRecursive(Transformer):
    "Same as Transformer, recursive, but changes the tree in-place instead of returning new instances"
```

### Behavior

`Transformer_InPlaceRecursive` combines the behavior of `Transformer` (callbacks
receive processed children) with in-place modification (no new tree instances are
created). It is the recursive variant — the transformation is implemented through
direct recursion rather than the `iter_subtrees()` iteration.

**Processing order**: Children are **always transformed before the parent callback
is invoked**. This is the fundamental contract:

1. For each subtree, recursively transform all its children first.
2. Update `tree.children` with the transformed results.
3. Call the user callback `self.userfunc(tree)` with the updated children.

### Example

```python
from lark import Lark
from lark.visitors import Transformer_InPlaceRecursive

grammar = r"""
    start: expr
    expr: NUMBER "+" NUMBER
    NUMBER: /[0-9]+/
    %ignore " "
"""
parser = Lark(grammar, parser='lalr')

class Calc(Transformer_InPlaceRecursive):
    def NUMBER(self, tok):
        # Called for leaf terminals first
        return int(tok)

    def expr(self, children):
        # Called after NUMBER has already been converted to int
        return children[0] + children[1]  # int + int = int

    def start(self, children):
        return children[0]

tree = parser.parse("3 + 4")
result = Calc().transform(tree)
# result == 7  (not "3" + "4" = "34")
```

When `expr` is called, `children[0]` and `children[1]` are already `int` values
(not `Token` objects), because the `NUMBER` callback was applied to the children
before `expr` was called.

### Comparison with Transformer_InPlace

| Feature | `Transformer_InPlace` | `Transformer_InPlaceRecursive` |
|---|---|---|
| Implementation | Non-recursive (uses `iter_subtrees()`) | Recursive (direct calls) |
| In-place modification | Yes | Yes |
| New tree instances | No | No |
| Children pre-transformed | Yes | Yes |

Both classes guarantee that **when your callback fires, all child callbacks have
already been applied**. The difference is only the implementation strategy.

---

## Rule Priority and Reduce/Reduce Conflict Resolution

### Syntax

Rules can be assigned a priority using the `.N` notation:

```
rule_name.priority: expansion
```

Example:

```
start: value
?value: keyword_expr | generic_expr
keyword_expr.2: KW
generic_expr.1: WORD
KW: "select" | "from" | "where"
WORD: /[a-z]+/
```

### Reduce/Reduce Conflicts

A **reduce/reduce conflict** occurs in LALR parsing when the parser can reduce
the current item using more than one rule. This happens when multiple rules
derive the same sequence of terminals and the lookahead token doesn't disambiguate.

### Priority-Based Resolution

When a reduce/reduce conflict is detected and the conflicting rules have **different
priorities**, Lark automatically resolves the conflict by selecting the rule with
the **highest priority number**.

Resolution algorithm:

1. Collect all conflicting rules and their priorities.
2. Sort by priority in **descending order** (highest first).
3. If the highest-priority rule has a strictly greater priority than the second-highest,
   select it as the winner.
4. Otherwise (equal priorities), raise a `GrammarError`.

```
# Given: high_rule.2 and low_rule.1 conflict on lookahead T
# Resolution: high_rule.2 wins (priority 2 > priority 1)
```

### Effect

With correct priority resolution, parsing ambiguous input uses the higher-priority
rule. This allows grammar authors to express preference among alternative interpretations
without explicitly disambiguating the grammar structure.

```python
from lark import Lark

grammar = r"""
    start: value
    ?value: high_rule | low_rule
    high_rule.2: WORD
    low_rule.1: WORD
    WORD: /[a-z]+/
"""
parser = Lark(grammar, parser='lalr')
tree = parser.parse('hello')
# tree.children[0].data == 'high_rule'  (priority 2 wins)
```

### Default Priority

Rules without an explicit priority have a default priority of **0**. When all
conflicting rules have priority 0, the conflict is not resolved and a `GrammarError`
is raised.

---

## Tree.iter_subtrees()

### Signature

```python
def iter_subtrees(self) -> Iterator[Tree]:
    """Depth-first iteration.

    Iterates over all the subtrees, never returning to the same node twice.
    """
```

### Traversal Order

`iter_subtrees()` returns nodes in **postorder** (depth-first, leaves first, root last):

- Children are always yielded **before** their parent.
- The root node is the **last** element in the iteration.

For a tree:
```
root
├── child_a
│   └── leaf_1
└── child_b
    └── leaf_2
```

The order from `iter_subtrees()` is: `leaf_1, child_a, leaf_2, child_b, root`.

### Usage

```python
# Correct: all children of a node appear before the node itself
for subtree in tree.iter_subtrees():
    # At this point, all of subtree's descendants have already been seen
    process(subtree)
```

This postorder guarantee is what allows `Visitor.visit()` and `Transformer_InPlace.transform()`
to process parent nodes with already-processed children.

### iter_subtrees_topdown()

For top-down (preorder) iteration — where the root comes first — use:

```python
def iter_subtrees_topdown(self) -> Iterator[Tree]:
    """Breadth-first iteration.
    Returns nodes in order like pretty() does (root first).
    """
```

---

## Grammar Rule Modifiers

### `?` Modifier (expand1)

A rule prefixed with `?` is **inlined** into its parent when it has exactly one child:

```
?value: NUMBER | string
```

If `value` matches a single `NUMBER`, the `NUMBER` token is returned directly
(no `Tree('value', [token])` wrapper). If `value` matches multiple children,
a `Tree('value', children)` is returned normally.

### `!` Modifier (keep_all_tokens)

A rule prefixed with `!` keeps all tokens including filtered ones (e.g., punctuation):

```
!expr: NUMBER "+" NUMBER
```

### `_` Prefix (anonymous rule / inline rule)

Rules whose name starts with `_` are **anonymous** (transparent). Their children
are **inlined** into the parent tree — no `Tree` node is created for the rule itself.

```
start: _items
_items: item item item
item: NAME
NAME: /[a-z]+/
```

When parsing `"a b c"`, `_items` is transparent:
- `start.children == [Tree('item', ['a']), Tree('item', ['b']), Tree('item', ['c'])]`

Named rules (without `_` prefix) create a `Tree` node:

```
start: items
items: item item item  # 'items' is NOT inlined
```

- `start.children == [Tree('items', [Tree('item', ['a']), ...])]`

---

## Lark Constructor Parameters

```python
Lark(
    grammar,                  # Grammar string or file-like object
    parser='earley',          # 'lalr', 'earley', or 'cyk'
    lexer='auto',             # Lexer type: 'auto', 'basic', 'contextual', 'dynamic'
    start='start',            # Start rule name(s)
    ambiguity='resolve',      # How to handle ambiguities: 'resolve', 'explicit', 'forest'
    propagate_positions=False,# Attach line/column info to all nodes
    maybe_placeholders=False, # Insert None for missing optional elements
    keep_all_tokens=False,    # Keep filtered terminals in tree
    regex=False,              # Use regex module instead of re
    g_regex_flags=0,          # Global regex flags
)
```

### `ambiguity` Parameter

- `'resolve'`: Silently pick one parse tree. Uses rule priority to select.
- `'explicit'`: Return an `_ambig` node containing all parses.
- `'forest'`: Return a SPPF forest (Earley only).

### `parser='lalr'`

LALR(1) is the most performant parser. It requires an unambiguous grammar (or
uses priority/disambiguation to resolve conflicts). Suitable for most programming
language grammars.

---

## Error Types

| Exception | Cause |
|---|---|
| `GrammarError` | Invalid grammar syntax or unresolvable conflicts |
| `UnexpectedCharacters` | Input text doesn't match any terminal at current position |
| `UnexpectedToken` | Parser receives a token it doesn't expect in the current state |
| `UnexpectedEOF` | Input ends prematurely |
| `ParseError` | General parse failure |

---

## Complete Example

```python
from lark import Lark, Tree, Token
from lark.visitors import Transformer, Visitor_Recursive, Transformer_InPlaceRecursive

GRAMMAR = r"""
    start: stmt+
    stmt: assignment | expr_stmt
    assignment: NAME "=" expr
    expr_stmt: expr
    ?expr: term ("+" term)*
    ?term: factor ("*" factor)*
    ?factor: NUMBER | NAME | "(" expr ")"
    NAME: /[a-z_][a-z0-9_]*/
    NUMBER: /[0-9]+/
    %ignore /\s+/
"""

parser = Lark(GRAMMAR, parser='lalr')

# Parse
tree = parser.parse("x = 3 + 4 * 2\nx")

# Traverse bottom-up with Visitor_Recursive
class NodeCounter(Visitor_Recursive):
    def __init__(self):
        self.count = 0
    def __default__(self, tree):
        self.count += 1

counter = NodeCounter()
counter.visit(tree)
print(f"Visited {counter.count} nodes bottom-up")
```
