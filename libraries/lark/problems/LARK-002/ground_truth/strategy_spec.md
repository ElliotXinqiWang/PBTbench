# Strategy Spec for LARK-002

## bug_1: Transformer_InPlaceRecursive._transform_tree doesn't update children (L4)

**Trigger condition**: Use `Transformer_InPlaceRecursive` with callbacks that convert child token types (e.g., `NUMBER` → `int`), on a grammar with at least two nesting levels.

**Why default strategy is insufficient**: A random Hypothesis strategy that builds arbitrary Tree objects directly (bypassing the parser) would never exercise the Transformer's recursive call chain in the way the parser produces it. The bug is activated through the transformer's recursive `_transform_tree` call, which only fires when the tree has genuine subtree nodes (not just leaves).

**Trigger probability estimate**: ~100% for any transformer with type-conversion callbacks on a grammar with ≥2 nesting levels. The minimum trigger: any grammar with `rule_A: rule_B; rule_B: TOKEN`.

**Minimum trigger input**:
- Grammar: `start: sum; sum: term ("+" term)*; term: NUMBER; NUMBER: /[0-9]+/`
- Transformer: `NUMBER → int`, `term → children[0]`, `sum → sum(children)`
- Input text: `"0"` (single number) — the `sum → term → NUMBER` chain reveals the bug

**Why it's L4 (hard to find by code review)**:
- `Transformer_InPlaceRecursive._transform_tree` is a 2-line method override
- Dropping the assignment (`tree.children =`) appears harmless in isolation — the generator is still exhausted (callbacks fire), so no error occurs at the `list(...)` call
- The bug is only visible when you realize that the tree's children list is NEVER updated, so the parent callback still receives original tokens
- The call chain: `transform()` → `_transform_children()` → `_transform_tree()` → (assignment dropped) → `_call_userfunc(tree)` — requires tracing 4 levels

---

## bug_2: Visitor.visit_topdown() uses bottom-up order (L3)

**Trigger condition**: Use `Visitor.visit_topdown()` on any tree with depth ≥ 2 and callbacks that depend on the parent being visited before the child.

**Why default strategy is insufficient**: A test that only calls `Visitor.visit()` (bottom-up) will not trigger the bug. A test that calls `visit_topdown()` but doesn't check the ORDER of callbacks will also miss it. The key: the test must assert that the root is visited BEFORE its children.

**Trigger probability estimate**: 100% — any `visit_topdown()` call on a depth-2+ tree with order-checking callbacks will reveal the reversed order.

**Minimum trigger input**:
- Tree: `Tree('root', [Tree('child', ['x'])])`
- Visitor: records visit order
- Assert: `'root'` appears before `'child'` in recorded order

**Why it's L3 (moderate code review difficulty)**:
- `visit_topdown` and `visit` are nearly identical one-liners; the only difference is `iter_subtrees_topdown()` vs `iter_subtrees()`
- The bug reverses the method call but keeps the same structure — a reviewer might notice the wrong iterator is used, but only if they know which is which
- Domain knowledge required: `iter_subtrees()` is bottom-up, `iter_subtrees_topdown()` is top-down

---

## bug_3: Tree.find_token() returns non-matching tokens (L3)

**Trigger condition**: Call `find_token(token_type)` on a tree containing BOTH tokens of the target type AND tokens of other types.

**Why default strategy is insufficient**: If the tree only contains tokens of a single type, the condition `v.type == token_type` and `v.type != token_type` produce the same result (all or none). The bug is only visible when the tree contains mixed token types.

**Trigger probability estimate**: 100% for any tree with ≥2 different token types in a single parse. The minimum trigger: parse text with at least two different terminal types (e.g., NAME and NUMBER both present).

**Minimum trigger input**:
- Grammar: produces NAME and NUMBER tokens
- Tree: `Tree('root', [Token('NAME', 'foo'), Token('NUMBER', '42')])`
- `tree.find_token('NAME')` — with bug returns `[Token('NUMBER', '42')]` instead of `[Token('NAME', 'foo')]`

**Why it's L3 (moderate code review difficulty)**:
- `find_token` is a 3-line method with a single lambda
- The condition `v.type != token_type` vs `v.type == token_type` is a one-character difference
- Easy to miss in a code review because the surrounding logic (isinstance check, scan_values) looks correct

---

## bug_4: Token.new_borrow_pos swaps end_line and end_column (L2)

**Trigger condition**: Call `Token.new_borrow_pos()` or `Token.update()` on a token whose `end_line != end_column`, then inspect `end_line` or `end_column` of the result.

**Why default strategy is insufficient**: If `end_line == end_column` in the source token (e.g., both are 5), the swap is undetectable. The test must use tokens where these two values differ.

**Trigger probability estimate**: 100% for any token where `end_line != end_column`. For multi-line text or long lines, this is nearly always the case.

**Minimum trigger input**:
- `borrow = Token('X', 'x', ..., end_line=2, end_column=7, ...)`
- `tok = Token.new_borrow_pos('Y', 'y', borrow)`
- `assert tok.end_line == 2`  — fails with bug (got 7)

**Why it's L2 (relatively easy once found)**:
- `new_borrow_pos` is a single-line class method
- The swapped arguments `end_column, end_line` vs `end_line, end_column` are adjacent in the argument list — easy to spot on careful inspection
- But `end_line` and `end_column` are both integers of similar range, so runtime errors don't occur — silent failure
- The swap is exploitable if the argument names aren't checked carefully against the Token constructor signature
