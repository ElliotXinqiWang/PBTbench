# Strategy Specification — LARK-003

## Bug 1: Terminal Priority Sort (L4)

**File**: `lark/lexer.py:583`
**Patch**: Change `-x.priority` to `x.priority` in `BasicLexer.__init__` sort key.

### Trigger Condition

Parse any input using a grammar that has two terminals with **different explicit
priorities**, where the lower-priority terminal (e.g., `NAME.1`) is a regex that
could also match the text the higher-priority terminal (e.g., `TOKEN.2`) is designed
to capture. Any single-word input that exactly matches a keyword string will produce
the wrong token type.

### Why Default Strategy Is Insufficient

A test that only uses a grammar with default-priority (priority=0) terminals won't
trigger this bug, because the sort key only inverts ordering for non-zero priorities.
Similarly, a grammar where keywords are at the same priority as the catch-all regex
won't trigger this bug (different code path via `_create_unless`).

You must use a grammar where at least two terminals have **explicitly specified
different priority numbers**, and input that matches both terminals.

### Trigger Probability with Default Strategy

- With a random grammar using default priorities: **0%** (bug never manifests)
- With a grammar using `.2` and `.1` priorities: **~100%** for keyword inputs

### Minimum Trigger Example

```python
GRAMMAR = """
start: (TOKEN | NAME)+
TOKEN.2: "if"
NAME.1: /[a-z]+/
"""
tree = parser.parse("if")
# Should be Token('TOKEN', 'if') but with bug gets Token('NAME', 'if')
```

---

## Bug 2: Visitor_Recursive.visit() Top-Down Instead of Bottom-Up (L3)

**File**: `lark/visitors.py:393`
**Patch**: Move `self._call_userfunc(tree)` before child recursion.

### Trigger Condition

Use `Visitor_Recursive.visit()` with a tree of depth ≥ 2, where the user's
callback is sensitive to visit order (e.g., it checks whether children have been
processed before the parent is called). Any nested grammar with at least two
levels of rules will expose the ordering bug.

### Why Default Strategy Is Insufficient

A test that only uses `Visitor` (non-recursive) or checks the visit result
without caring about order won't detect this. Also, `Visitor_Recursive.visit_topdown()`
already visits top-down by design — using that method would not reveal the bug
in `visit()`.

You need a test that explicitly verifies the bottom-up ordering contract:
**callback for child is called before callback for parent**.

### Trigger Probability with Default Strategy

- With a visitor that ignores visit order: **0%** (observable only via ordering check)
- With a depth≥2 tree and an order-checking visitor: **100%**

### Minimum Trigger Example

```python
visit_order = []
class OrderCheck(Visitor_Recursive):
    def __default__(self, t):
        visit_order.append(t.data)

root = Tree('root', [Tree('child', ['x'])])
OrderCheck().visit(root)
# Correct: ['child', 'root']
# With bug: ['root', 'child']
```

---

## Bug 3: Transformer_InPlaceRecursive Skips Child Transformation (L3)

**File**: `lark/visitors.py:339`
**Patch**: Remove `tree.children = list(self._transform_children(tree.children))`.

### Trigger Condition

Use `Transformer_InPlaceRecursive` with a grammar of depth ≥ 2, where a callback
for a child rule converts the type of a token (e.g., `NUMBER` → `int`), and a
parent rule's callback depends on having already-transformed (typed) children.
The bug causes parent callbacks to receive raw `Token` objects instead of
the converted values.

### Why Default Strategy Is Insufficient

A transformer that only has a single-level callback (no nested rules, no type
conversion) won't trigger this bug. Also, using the standard `Transformer` or
`Transformer_InPlace` classes won't trigger this — only `Transformer_InPlaceRecursive`
is affected.

### Trigger Probability with Default Strategy

- With a transformer that doesn't convert token types: **0%**
- With a transformer that converts `NUMBER→int` in a 2+ level grammar: **100%**

### Minimum Trigger Example

```python
class Calc(Transformer_InPlaceRecursive):
    def NUMBER(self, tok): return int(tok)
    def expr(self, ch): return ch[0] + ch[1]  # expects int + int
    def start(self, ch): return ch[0]

tree = parser.parse("3 + 4")
result = Calc().transform(tree)
# Correct: 7 (int)
# With bug: Tree('expr', [Token('NUMBER','3'), Token('NUMBER','4')]) or TypeError
```

---

## Bug 4: Rule Priority Conflict Resolution Picks Lowest Instead of Highest (L2)

**File**: `lark/parsers/lalr_analysis.py:276`
**Patch**: Change `p = [(r.options.priority or 0, r) for r in rules]` to
`p = [(-(r.options.priority or 0), r) for r in rules]`.

### Trigger Condition

Create a grammar with a **reduce/reduce conflict** where two rules can reduce
the same terminal, and the rules have **different explicit priorities** (e.g., `.2`
and `.1`). Parse any input that triggers the ambiguous rule. The wrong rule will
be selected.

Key requirement: the grammar must actually have a reduce/reduce conflict. This
happens when two rules derive the same terminal sequence and the LALR lookahead
doesn't disambiguate them. The grammar must use explicit priority numbers (not
default priority 0, which would cause a GrammarError under both correct and buggy
code for the same reasons).

### Why Default Strategy Is Insufficient

A grammar that is unambiguous (no reduce/reduce conflicts) won't exercise the
conflict resolution path at all. Any grammar without explicit rule priorities
(`.N`) won't expose the negation bug. You must construct a grammar that naturally
has a reduce/reduce conflict and uses explicit priorities to resolve it.

### Trigger Probability with Default Strategy

- Without priority-annotated reduce/reduce grammar: **0%**
- With a correctly constructed conflict-with-priorities grammar: **100%** for any input

### Minimum Trigger Example

```python
GRAMMAR = r"""
    start: value
    ?value: high_rule | low_rule
    high_rule.2: WORD
    low_rule.1: WORD
    WORD: /[a-z]+/
"""
parser = Lark(GRAMMAR, parser='lalr')
tree = parser.parse('hello')
# Correct: tree.children[0].data == 'high_rule' (priority 2 wins)
# With bug: tree.children[0].data == 'low_rule' (negated priority: -1 > -2)
```
