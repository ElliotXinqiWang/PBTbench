# TRNS-005 Strategy Specification

## Bug 1: trigger_nested done-set pop direction

**Trigger condition**: HSM with nesting depth >= 2 where the same trigger name
has transitions at both a deep nested state and a parent/ancestor state. The
bug causes the done set to contain wrong path strings (e.g., `sub_leaf` instead
of `A_sub`), so parent-scope transitions are not suppressed after a child
transition fires.

**Minimum input**: A 3-level HSM (e.g., `A -> sub -> leaf`) with `go` trigger
defined at both `A_sub_leaf` -> B and `A` -> C. With the bug, the model ends
up in C instead of B because the parent transition fires after the child.

**Strategy range**: depth >= 2 (minimum 3-level nesting), same trigger at
child and parent with different destinations.

**Default strategy trigger probability**: ~0% (requires constructing nested
states AND having same trigger at multiple levels AND checking final state).

**Targeted strategy trigger probability**: ~100% (any depth >= 2 nested HSM
with dual-level triggers).

## Bug 2: _remap_state condition/unless swap

**Trigger condition**: HSM with state remapping where transitions within the
child scope use `conditions` or `unless` guards. The bug swaps the tuple
indexing so conditions end up in the unless list and vice versa.

**Minimum input**: A workflow state with a child transition guarded by
`conditions=['check']` or `unless=['check']`, and a remap that redirects the
destination. Any boolean return value from check() will demonstrate the swap.

**Strategy range**: Any condition_value (True/False) combined with either
conditions or unless.

**Default strategy trigger probability**: ~5% (requires remapping + conditions).

**Targeted strategy trigger probability**: ~100% (all 4 condition/unless
combinations trigger the bug for at least one case).

## Bug 3: get_transitions delegate pop direction

**Trigger condition**: Call `get_transitions(source=nested_state, delegate=True)`
where the source is a nested state (depth >= 2) and a transition exists at a
parent level. The bug pops from the front of source_path instead of the end,
walking in the wrong direction.

**Minimum input**: 2-level HSM (e.g., `A -> mid`) with a transition at the
`A` level. Query from `A_mid` with `delegate=True`. With the bug, the parent
transition is not found because the walk goes in the wrong direction.

**Strategy range**: depth >= 2, any parent_dest.

**Default strategy trigger probability**: ~0% (requires using delegate=True
parameter and checking results).

**Targeted strategy trigger probability**: ~100% (any 2-level HSM with
parent transition and delegate query).

## Bug 4: _remove_nested_transitions src_path narrowing

**Trigger condition**: HSM with transitions defined at a nested scope (via
children's `transitions` list, not via `machine.add_transition`) with nesting
depth >= 2 (so the source path has multiple elements). The bug checks
`src_path[-1]` instead of `src_path[0]` during recursive path narrowing,
preventing the path from being narrowed as recursion descends into scopes.

**Minimum input**: A 3-level HSM (`gp -> par -> child0, child1`) with
transitions defined in the `par` children's transitions list. Remove one
child's transition. With the bug, the removal silently fails because the
path is never narrowed to reach the correct scope.

**Strategy range**: depth >= 2 scope-level transitions, n_children >= 2.

**Default strategy trigger probability**: ~0% (requires scope-level transitions
AND specific removal pattern AND verifying removal succeeded).

**Targeted strategy trigger probability**: ~100% (any multi-level scope
transition with targeted removal).
