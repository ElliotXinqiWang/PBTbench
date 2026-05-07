# Strategy Spec for PRSO-001

## Bug 1: _FUNC_CONTAINERS missing 'decorated' — iter_funcdefs/iter_classdefs miss decorated definitions

**Trigger condition**: Call `module.iter_funcdefs()` or `module.iter_classdefs()` on a module that contains at least one `@decorator`-decorated function or class. The decorated definition will not appear in the results.

**Why default strategy is insufficient**: A default PBT generating random Python snippets would need to include decorator syntax (`@name\ndef foo(): pass`). Simple single-function code without decorators never triggers this bug, so tests using `parso.parse("def foo(): pass")` would all pass.

**Trigger probability without targeted strategy**: ~30% (only if random code generation happens to include `@decorator` syntax, which basic generators typically don't). With targeted strategy: 100%.

**Minimum triggering input**:
```python
code = "@my_decorator\ndef foo(): pass\n"
module = parso.parse(code)
assert len(list(module.iter_funcdefs())) == 1  # fails: returns 0
```

**Strategy**: Generate code with exactly one decorated function/class (using `@dummy_decorator` or similar) and one plain function/class, then assert both are found.

---

## Bug 2: get_used_names() reverses occurrence order (arr.insert(0) vs arr.append)

**Trigger condition**: Call `module.get_used_names()` on a module that contains a name appearing in more than one location. The returned list of Name nodes for that name will be in REVERSE source order instead of ascending order.

**Why default strategy is insufficient**: A default PBT generating arbitrary code might not check the ORDER of occurrences — it would check that the name appears but not that occurrences are in source order. Also, single-occurrence names (unique identifiers) never trigger this bug.

**Trigger probability without targeted strategy**: ~5% (requires: multiple occurrences of same name AND checking order). With targeted strategy: 100%.

**Minimum triggering input**:
```python
code = "x = 1\ny = x + 1\nz = x\n"
module = parso.parse(code)
x_nodes = module.get_used_names()['x']
# Bug: positions are [(3, 4), (2, 4), (1, 0)] instead of [(1, 0), (2, 4), (3, 4)]
```

**Strategy**: Generate code with a name appearing on N≥3 distinct lines, collect its occurrences, assert positions are non-decreasing.

---

## Bug 3: Param.position_index wrong for keyword-only params when both '/' and '*' are present

**Trigger condition**: Call `param.position_index` on a keyword-only parameter (after `*`) in a function signature that ALSO has positional-only parameters (before `/`). The value will be inflated: when both `/` and `*` are present, swapping their processing order causes the second adjustment to be skipped (because after the first subtraction of 2, `index == keyword_only_index` and `>` is False).

**Why default strategy is insufficient**: Functions with BOTH `/` and `*` in their signature are uncommon in generated code. Tests using functions with only `*args` or only `/` would not trigger this bug. The trigger requires a signature of the form `def foo(a, ..., /, b, ..., *, c, ...)`.

**Trigger probability without targeted strategy**: ~2% (requires generating signatures with BOTH positional-only AND keyword-only separators). With targeted strategy: 100%.

**Minimum triggering input**:
```python
code = "def foo(a, /, b, *, c): pass\n"
module = parso.parse(code)
func = list(module.iter_funcdefs())[0]
params = func.get_params()
# c.position_index should be 2, but bug returns 3
```

**Strategy**: Generate functions with N positional-only params + M regular params + K keyword-only params (all >= 1), then verify position_index equals the sequential index 0..N+M+K-1.

---

## Bug 4: ImportFrom.level wrong for imports using '...' token

**Trigger condition**: Access the `.level` property on an `ImportFrom` node where the relative import uses 3+ consecutive dots that form a `...` token. The `...` token has `len(value) == 3` but the bug adds only 1 instead of 3.

**Why default strategy is insufficient**: Most generated import code uses absolute imports or single-dot relative imports (`from . import x`). Multi-dot relative imports (`from ... import x`) are uncommon in naively generated code. Single dots are unaffected (len('.')=1 == 1).

**Trigger probability without targeted strategy**: ~5% (needs `from ...` or deeper). With targeted strategy: 100%.

**Minimum triggering input**:
```python
code = "from ... import x\n"
module = parso.parse(code)
imp = list(module.iter_imports())[0]
assert imp.level == 3  # fails: returns 1
```

**Boundary**: `from .` (level=1) and `from ..` (level=2) are unaffected since they use only single-dot tokens. `from ...` (level=3) is the minimal trigger — the `...` ellipsis token is a single token with value `"..."`.

**Strategy**: Generate relative imports with total level 1 to 6, then assert `imp.level` matches the dot count.
