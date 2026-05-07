# PRSO-004 Strategy Specification

## bug_1: ClassOrFunc.get_decorators() — 'decorator' vs 'decorators' type check

**Trigger condition:**
Call `get_decorators()` on any `Function` or `Class` node that has at least one
`@-decorator` applied. The bug causes wrong items to be returned regardless of
decorator count.

**Why default strategy fails:**
Baseline tests rarely call `get_decorators()` or verify that returned items have
the correct `.type == 'decorator'`. If they do call it, they typically use simple
test cases that don't check the number or type of returned items.

**Trigger probability with default strategy:** ~0% (must call get_decorators AND
check item types/count)

**Trigger probability with targeted strategy:** ~100% (any function with at least
1 decorator, verifying `len(result) == num_decorators` and all items have
`.type == 'decorator'`)

**Minimum triggering input:**
```python
@prop
def f(): pass
```
`func.get_decorators()` returns `[Op('@'), Name('prop'), Newline]` (3 items, wrong types)
instead of `[Decorator]` (1 item, correct type).

---

## bug_2: ExprStmt.get_defined_names() — '==' vs 'in' for augmented assignments

**Trigger condition:**
Call `get_defined_names()` on an `ExprStmt` that is an augmented assignment
(`a += 1`, `x -= 2`, `y *= 3`, `z //= 4`, etc.). Returns `[]` instead of `[Name(lhs)]`.

**Why default strategy fails:**
Baselines rarely test `get_defined_names()` on augmented assignments. They usually
test simple assignments (`a = 1`). Even if they test augmented assignments, they
rarely verify the defined names.

**Trigger probability with default strategy:** ~0% (requires specifically testing
augmented assignment with get_defined_names)

**Trigger probability with targeted strategy:** ~100% (any augmented assignment
operator, checking defined names returns the LHS name)

**Minimum triggering input:**
```python
a = 0
a += 1
```
`aug_stmt.get_defined_names()` returns `[]` instead of `[Name('a')]`.

**All 12 augmented operators trigger the bug:**
`+=`, `-=`, `*=`, `/=`, `//=`, `%=`, `**=`, `&=`, `|=`, `^=`, `>>=`, `<<=`

---

## bug_3: WithStmt.get_defined_names() — children[0] vs children[2]

**Trigger condition:**
Call `get_defined_names()` on a `WithStmt` that has at least one `as name` clause
with a function-call context manager (e.g., `with open('f') as fp:`). Returns `[]`
instead of `[Name('fp')]`.

**Why default strategy fails:**
Baselines rarely test `with_stmt.get_defined_names()` directly. They usually check
that names appear in `get_used_names()` (which works correctly — it scans all Name
leaves). The bug only affects the high-level `get_defined_names()` API.

**Trigger probability with default strategy:** ~0% (requires specifically calling
with_stmt.get_defined_names and checking the result)

**Trigger probability with targeted strategy:** ~100% (any with...as statement with
a call-expression context manager)

**Minimum triggering input:**
```python
with ctx() as name:
    pass
```
`with_stmt.get_defined_names()` returns `[]` instead of `[Name('name')]`.

**Note:** The bug triggers because `_defined_names(with_item.children[0], False)`
on a function-call expression (atom_expr) returns `[]`.

---

## bug_4: ExprStmt.get_rhs() — length check 2 vs 4 for annassign

**Trigger condition:**
Call `get_rhs()` on an `ExprStmt` that is an annotated assignment WITH an explicit
value: `x: int = 5`. Returns the type annotation node (`Name('int')`) instead of
the value node (`Number('5')`).

**Why default strategy fails:**
Annotated assignments with values are not the most common assignment form in test
code. Baselines rarely call `get_rhs()` on annotated assignments or verify that
the returned node is the value (not the type annotation).

**Trigger probability with default strategy:** ~1% (requires annotated assignment
with value AND calling get_rhs)

**Trigger probability with targeted strategy:** ~100% (any `x: T = val` annotated
assignment, verifying rhs.value == val)

**Minimum triggering input:**
```python
x: int = 42
```
`expr_stmt.get_rhs()` returns `Name('int')` instead of `Number('42')`.

**annassign structure:**
- `x: int = 5` → annassign children = `[':', Name('int'), '=', Number('5')]` (len=4)
- `x: int` → annassign children = `[':', Name('int')]` (len=2)
The correct check is `len == 4` (has value). The bug checks `len == 2` (bare annotation),
inverting which branch is taken for each case.
