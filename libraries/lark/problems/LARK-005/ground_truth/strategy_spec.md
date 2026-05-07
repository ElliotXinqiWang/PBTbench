# Strategy Spec: LARK-005

## Bug 1: _vargs_inline() passes list instead of *args

**Trigger condition**: A Transformer class decorated with `@v_args(inline=True)`
where at least one callback method expects 2+ positional arguments (one per child).

**Why default strategy fails**: If all callbacks have single-arg signatures or
the decorator is not used, the bug never manifests.

**Trigger probability with default strategy**: 0% (bug requires specifically
crafted multi-arg inline callbacks)

**Minimum trigger input**:
- Grammar: `expr: NUMBER op NUMBER`
- Transformer: `@v_args(inline=True)` class with `def expr(self, left, op, right)`
- Input: any expression like `"3 + 4"`

**Strategy**: Use `st.integers(0, 100)` for both operands, transform and check
arithmetic result. `max_examples=500` ensures consistent detection.

---

## Bug 2: Visitor.visit() traverses top-down instead of bottom-up

**Trigger condition**: A Visitor with callbacks on both a parent rule and at
least one child rule. Recording visit order and verifying children come before
parent.

**Why default strategy fails**: If callbacks only exist on leaf rules, no
ordering can be observed.

**Trigger probability with default strategy**: ~90% (any multi-level grammar
exposes the order inversion when both parent and child callbacks are registered)

**Minimum trigger input**:
- Grammar: `start: item+; item: NAME`
- Visitor: records 'item' visit and 'start' visit in a list
- Input: any string with at least 1 name token

**Strategy**: `st.lists(st.text(...), min_size=1, max_size=5)` for input names.

---

## Bug 3: Transformer_NonRecursive stack deletion corrupts siblings

**Trigger condition**: Any tree with at least 2 sibling subtrees at the same
level. The bug deletes the first `size` stack items instead of the last `size`,
corrupting subsequent siblings.

**Why default strategy fails**: Single-sibling or leaf-only trees (min_size=1)
don't expose the corruption because there are no subsequent siblings to receive
wrong children.

**Trigger probability with default strategy**: 0% (single pairs don't corrupt
the stack; need min_size >= 2)

**Minimum trigger input**:
- Grammar: `start: pair pair; pair: NAME "=" NUMBER` (at least 2 pairs)
- Compare `Transformer` vs `Transformer_NonRecursive` result
- Input: `"a=1, b=2"` (2 pairs)

**Boundary**: min_size=2 in the pairs list strategy.

**Strategy**: `st.lists(st.tuples(name_strategy, int_strategy), min_size=2, max_size=5)`

---

## Bug 4: _vargs_tree() passes Tree with reversed children

**Trigger condition**: A Transformer callback decorated with `@v_args(tree=True)`
that reads `tree.children` by index for a non-commutative operation where
`a op b ≠ b op a`.

**Why default strategy fails**: Commutative operations (addition, equality
check) don't expose the reversal because `a + b == b + a`.

**Trigger probability with default strategy**: ~50% (depends on whether operation
is commutative and whether operands are equal)

**Minimum trigger input**:
- Grammar: `expr: NUMBER op NUMBER; op: MINUS`
- Transformer: `@v_args(tree=True)` callback computes `tree.children[0] - tree.children[2]`
- Input: `"5 - 3"` (non-zero difference, non-commutative)

**Boundary**: For subtraction `a - b`, we need `a ≠ b` for the bug to be
detectable (if a == b, both orders give 0).

**Strategy**: `st.integers(0, 100)` for both operands; the assertion catches
any `a - b ≠ b - a` case, which is most non-equal pairs.
