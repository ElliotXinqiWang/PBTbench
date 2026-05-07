# transitions 0.9.3 — Hierarchical State Machine Event Processing API

## Overview

The `transitions` library (v0.9.3) provides `HierarchicalMachine` in
`transitions.extensions.nesting`, which extends the basic `Machine` to support
nested (hierarchical) state machines (HSMs). HSMs allow states to contain child
states, forming a tree structure. Transitions can be defined at any level of the
hierarchy.

This document covers HSM event processing: how events resolve in nested
hierarchies, how the `done` set prevents duplicate transition firing, how
`get_transitions` with delegation walks parent scopes, how state remapping
preserves transition conditions, and how transitions are removed from nested
scopes.

---

## 1. Hierarchical State Structure

### 1.1 Defining Nested States

States can contain children, forming a tree. Children are declared via a
dictionary with `'name'` and `'children'` keys:

```python
from transitions.extensions.nesting import HierarchicalMachine

states = [
    {'name': 'A', 'children': [
        {'name': 'sub', 'children': ['leaf1', 'leaf2']},
        'other'
    ]},
    'B', 'C'
]

machine = HierarchicalMachine(states=states, initial='A_sub_leaf1')
```

State names use the separator `_` to denote nesting depth:
- `A` — top-level state
- `A_sub` — child of A
- `A_sub_leaf1` — grandchild of A, child of sub

### 1.2 Children with Internal Transitions

Children can define their own transitions via the `'transitions'` key. These
transitions are stored at the **nested scope level**, not at the top level:

```python
states = [
    {'name': 'workflow', 'children': ['step1', 'step2', 'done'],
     'transitions': [
         {'trigger': 'next', 'source': 'step1', 'dest': 'step2'},
         {'trigger': 'next', 'source': 'step2', 'dest': 'done'},
     ]},
    'idle'
]
```

Within the `workflow` scope, transitions are stored with local names (`step1`,
`step2`), not fully qualified names (`workflow_step1`).

### 1.3 State Remapping

When children have an "exit" state that should transition to a sibling at the
parent level, use `'remap'`:

```python
states = [
    'idle',
    {'name': 'workflow', 'children': ['step1', 'step2', 'finish'],
     'transitions': [
         {'trigger': 'go', 'source': 'step1', 'dest': 'finish'},
     ],
     'remap': {'finish': 'completed'}},
    'completed',
]
```

When the `finish` child state is reached via a transition within `workflow`,
the model is automatically redirected to `completed` at the parent level.

**Condition preservation**: Transitions with `conditions` or `unless` that
target a remapped state must preserve their condition semantics after remapping:

- `conditions=['check']` — transition only fires when `check()` returns `True`
- `unless=['check']` — transition only fires when `check()` returns `False`

The remapping process splits the transition's condition list into two
categories. Internally, each condition stores a `target` boolean that indicates
whether the condition was specified via `conditions` (`target=True`) or
`unless` (`target=False`). The remapping code reconstructs these lists using a
tuple indexing pattern:

```python
# For each condition object:
# cond.target == True  -> goes into conditions list
# cond.target == False -> goes into unless list
(unless, conditions)[cond.target].append(cond.func)
```

This preserves the original semantics: a condition marked `target=True` (from
`conditions`) remains a condition, and one marked `target=False` (from
`unless`) remains an unless guard.

---

## 2. Event Processing in HSMs

### 2.1 resolve_order(state_tree)

Before processing an event, the machine converts the model's current state
into an ordered list of state paths using `resolve_order()`. This function
performs a **breadth-first** traversal of the state tree and returns states in
**children-before-parents** order.

For a model in state `A_sub_leaf1`:

```python
state_tree = {'A': {'sub': {'leaf1': {}}}}
ordered = resolve_order(state_tree)
# Result: [['A', 'sub', 'leaf1'], ['A', 'sub'], ['A']]
```

Children are always processed **before** their parents. This ensures that the
most specific (deepest) matching transition fires first.

### 2.2 trigger_nested(event_data)

The `NestedEvent.trigger_nested()` method is the core event processor for HSMs.
It iterates through the ordered states and fires the first matching transition
for each state path, using a **done set** to prevent re-processing of ancestor
states after a successful child transition.

**Algorithm:**

1. Build the state tree from the model's current state
2. Compute `ordered_states` via `resolve_order()`
3. Initialize an empty `done` set
4. For each `state_path` in `ordered_states`:
   a. Compute `state_name` by joining the path elements
   b. If `state_name` is NOT in `done` AND has transitions for this trigger:
      - Process the transitions (fire the first matching one)
      - If successful, add all ancestor paths to `done`
5. Return the result

**The done set walkup**: When a transition fires successfully at state path
`['A', 'sub', 'leaf1']`, the done set must include all ancestor paths:

```python
# Starting from state_path = ['A', 'sub', 'leaf1']
elems = state_path  # ['A', 'sub', 'leaf1']
while elems:
    done.add(separator.join(elems))  # 'A_sub_leaf1', then 'A_sub', then 'A'
    elems.pop()  # removes from END: leaf1, then sub, then A
```

After this loop, `done = {'A_sub_leaf1', 'A_sub', 'A'}`. This prevents the
`'A_sub'` and `'A'` entries in `ordered_states` from re-processing the event,
which would cause parent-scope transitions to fire after a child has already
handled the event.

**Critical**: The `pop()` operation removes from the **end** of the list, which
progressively shortens the path from the leaf upward to the root. This is
essential — popping from the front would produce paths like `'sub_leaf1'`,
`'leaf1'`, and `''` which are NOT the ancestor state names and would fail to
suppress parent processing.

### 2.3 Same Trigger at Multiple Levels

A common HSM pattern has the same trigger name at both a child and a parent
level:

```python
machine.add_transition('go', 'A_sub_leaf1', 'B')   # child level
machine.add_transition('go', 'A', 'C')              # parent level
```

When the model is in `A_sub_leaf1` and `go` fires:
1. `ordered_states` = `[['A', 'sub', 'leaf1'], ['A', 'sub'], ['A']]`
2. First iteration: `A_sub_leaf1` has a transition, it fires -> model moves to B
3. Done set walkup adds: `A_sub_leaf1`, `A_sub`, `A`
4. Second iteration: `A_sub` is in `done` -> skip
5. Third iteration: `A` is in `done` -> skip

Result: model ends up in B (child transition), parent transition to C is
correctly suppressed.

---

## 3. Querying Transitions with Delegation

### 3.1 get_transitions(trigger, source, dest, delegate)

The `get_transitions()` method retrieves transitions matching the specified
criteria. When `delegate=True`, it also includes transitions from parent scopes
— walking **up** the hierarchy from the source state.

```python
machine.add_transition('go', 'A', 'B')  # parent level

# Without delegation: only transitions at exact source level
trans = machine.get_transitions(source='A_sub_leaf1', delegate=False)
# -> [] (no transition directly from A_sub_leaf1)

# With delegation: includes parent transitions
trans = machine.get_transitions(source='A_sub_leaf1', delegate=True)
# -> [Transition(A -> B)] (found by walking up to A)
```

**Delegation algorithm:**

1. Split the source into a path: `['A', 'sub', 'leaf1']`
2. Collect transitions matching the full path
3. If `delegate=True` and path has more than 1 element:
   a. Pop from the **end**: `['A', 'sub']`
   b. Collect transitions matching this shorter path
   c. Continue popping and collecting until the path is empty

The pop direction is critical: popping from the end walks UP the hierarchy
(child -> parent). Popping from the front would walk in the wrong direction,
searching for states like `['sub', 'leaf1']` which may not exist at the top
scope, potentially causing errors or missing parent transitions.

### 3.2 get_nested_transitions(trigger, src_path, dest_path)

Internal method that searches for transitions within the current scope and
recursively descends into nested state scopes.

---

## 4. Removing Transitions from Nested Scopes

### 4.1 remove_transition(trigger, source, dest)

Removes transitions matching the given criteria:

```python
machine.remove_transition('go', source='A_sub_leaf1')
```

For nested states, this calls `_remove_nested_transitions()` which recursively
descends through state scopes.

### 4.2 _remove_nested_transitions(trigger, src_path, dest_path)

This method recursively removes transitions from nested state scopes. The key
mechanism is **path narrowing**: as the recursion enters a nested scope, the
`src_path` and `dest_path` are shortened by removing the first element when it
matches the current scope name.

**Path narrowing algorithm:**

For `src_path = ['gp', 'par', 'child0']`:

1. At top scope: iterate over states `['gp', 'sink', ...]`
2. For state `'gp'`: check if `state_name == src_path[0]` (i.e., `'gp' == 'gp'`)
   - Match! Narrow path to `src_path[1:]` = `['par', 'child0']`
   - Recurse into `gp` scope with narrowed path
3. Inside `gp` scope: iterate over states `['par']`
4. For state `'par'`: check if `state_name == src_path[0]` (i.e., `'par' == 'par'`)
   - Match! Narrow path to `src_path[1:]` = `['child0']`
   - Recurse into `par` scope with narrowed path
5. Inside `par` scope: find and remove transitions matching source `'child0'`

**Critical**: The comparison uses `src_path[0]` (the **first** element) because
at each scope level, the first element of the remaining path identifies which
child state to descend into. Using `src_path[-1]` (the last element) would
compare against the leaf state name at every level, which would fail to match
intermediate scope names and prevent the path from narrowing correctly.

### 4.3 Scope-Level Transitions

When transitions are defined via the `'transitions'` key in state definitions
(see Section 1.2), they are stored at the nested scope level with local names.
Removing such transitions requires the recursive descent through
`_remove_nested_transitions` to reach the correct scope.

Example:

```python
states = [
    {'name': 'gp', 'children': [
        {'name': 'par', 'children': ['child0', 'child1'],
         'transitions': [
             {'trigger': 'go', 'source': 'child0', 'dest': 'child1'},
             {'trigger': 'go', 'source': 'child1', 'dest': 'child0'},
         ]},
    ]},
    'sink'
]

machine = HierarchicalMachine(states=states, initial='gp_par_child0',
                               auto_transitions=False)

# Remove only child0's transition (child1's should be preserved)
machine.remove_transition('go', source='gp_par_child0')
```

After removal, `child1`'s transition should still exist because the removal
only targeted `gp_par_child0`.

---

## 5. Usage Patterns and Invariants

### 5.1 Child-Before-Parent Processing Invariant

When the same trigger has transitions at multiple hierarchy levels, the
deepest (most specific) matching transition always fires first. The done set
mechanism then prevents parent transitions from firing redundantly.

**Invariant**: For any event trigger, if a child-level transition fires
successfully, no ancestor-level transition with the same trigger should fire.

### 5.2 Condition Semantics Invariant

The `conditions` and `unless` lists on transitions have opposite semantics:
- `conditions`: ALL functions must return `True` for the transition to proceed
- `unless`: ALL functions must return `False` for the transition to proceed

This invariant must be preserved through ALL transformations, including state
remapping. A transition with `unless=['check']` that passes when `check()`
returns `False` must continue to pass when `check()` returns `False` after
remapping.

### 5.3 Delegation Walk Direction

The `get_transitions(delegate=True)` call walks UP the hierarchy (from child
to parent), not down. For a state path `['A', 'sub', 'leaf']`:
- First query: exact match at `['A', 'sub', 'leaf']`
- Second query: parent `['A', 'sub']`
- Third query: grandparent `['A']`

### 5.4 Selective Removal Invariant

When removing transitions from a specific nested source, sibling states'
transitions must not be affected. The removal targets only the specified source
path, and the recursive descent narrows the path correctly at each level.

---

## 6. API Reference Summary

| Method | Scope | Description |
|--------|-------|-------------|
| `HierarchicalMachine(states, initial, ...)` | Constructor | Creates HSM with nested states |
| `machine.add_transition(trigger, source, dest, ...)` | Top level | Adds transition (source/dest can be nested paths) |
| `machine.remove_transition(trigger, source, dest)` | Top level | Removes matching transitions recursively |
| `machine.get_transitions(trigger, source, dest, delegate)` | Top level | Queries transitions, optionally walking up hierarchy |
| `model.trigger(name)` / `model.<name>()` | Model | Fires event, processed by trigger_nested() |
| `model.may_<trigger>()` | Model | Checks if trigger can fire from current state |
| `machine.get_state(name)` | Internal | Retrieves State object by full path name |
| `machine.build_state_tree(state, sep)` | Internal | Converts state string to tree dict |
| `resolve_order(state_tree)` | Internal | Returns ordered state paths (children first) |

---

## 7. Common Patterns

### 7.1 Multi-Level Event Handling

```python
states = [
    {'name': 'editing', 'children': [
        {'name': 'text', 'children': ['typing', 'selecting']},
        'formatting'
    ]},
    'saved', 'error'
]

machine = HierarchicalMachine(states=states, initial='editing_text_typing',
                               auto_transitions=False)

# Specific handler at leaf level
machine.add_transition('save', 'editing_text_typing', 'saved')
# Fallback handler at parent level
machine.add_transition('save', 'editing', 'saved')

# If in editing_text_typing: leaf handler fires, parent is suppressed
# If in editing_formatting: parent handler fires (no leaf match)
```

### 7.2 Conditional Remapped Workflows

```python
class Job:
    def __init__(self):
        self.validated = False

    def is_valid(self):
        return self.validated

states = [
    'pending',
    {'name': 'processing', 'children': ['validate', 'execute', 'complete'],
     'transitions': [
         {'trigger': 'proceed', 'source': 'validate', 'dest': 'execute',
          'conditions': ['is_valid']},
         {'trigger': 'proceed', 'source': 'execute', 'dest': 'complete'},
     ],
     'remap': {'complete': 'done'}},
    'done'
]

machine = HierarchicalMachine(model=Job(), states=states, initial='pending',
                               auto_transitions=False)
# The conditions=['is_valid'] guard is preserved through remapping
```

### 7.3 Querying Available Transitions

```python
# From a deeply nested state, find all possible transitions
# including those inherited from parent states
all_trans = machine.get_transitions(source='editing_text_typing', delegate=True)
# Returns transitions defined at editing_text_typing, editing_text, and editing levels
```
