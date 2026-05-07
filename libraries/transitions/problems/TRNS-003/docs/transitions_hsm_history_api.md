# transitions 0.9.3 Hierarchical State Machine API

## Overview

`transitions` is a lightweight, object-oriented state machine library for Python.
The `HierarchicalMachine` extension adds support for nested (hierarchical) state
machines, allowing states to contain sub-states with automatic scope management,
hierarchical transitions, and ordered state enumeration.

---

## Core Module: `transitions.Machine`

### Constructor

```python
Machine(model=Machine.self_literal, states=None, initial='initial',
        transitions=None, send_event=False, auto_transitions=True,
        ordered_transitions=False, ignore_invalid_triggers=None,
        before_state_change=None, after_state_change=None, name=None,
        queued=False, prepare_event=None, finalize_event=None,
        model_attribute='state', model_override=False,
        on_exception=None, on_final=None)
```

**Parameters**:
- `model`: The object whose state is managed. Use `Machine.self_literal` to use
  the machine itself as the model.
- `states`: List of state names (strings), State objects, dicts, or Enum members.
- `initial`: The initial state name.
- `transitions`: List of transition definitions.
- `send_event`: When True, callbacks receive an `EventData` object.
- `auto_transitions`: When True, generates `to_<state>()` methods on the model.
- `ordered_transitions`: When True, creates sequential transitions between states.
- `queued`: When True, transitions triggered during callbacks are queued.
- `before_state_change`: Machine-level callback(s) invoked before ANY state change.
- `after_state_change`: Machine-level callback(s) invoked after ANY state change.
- `on_final`: Callback(s) invoked when a final state is entered.

### States

States can be defined as strings, dicts, or `State` objects:

```python
states = ['idle', 'running', 'finished']
# or with callbacks:
states = [
    {'name': 'idle', 'on_enter': 'log_idle', 'on_exit': 'cleanup_idle'},
    {'name': 'running', 'on_enter': ['start_timer', 'log_start']},
    'finished'
]
```

### Transitions

Transitions connect states and are triggered by events:

```python
transitions = [
    {'trigger': 'start', 'source': 'idle', 'dest': 'running'},
    {'trigger': 'finish', 'source': 'running', 'dest': 'finished',
     'before': 'save_results', 'after': 'notify_complete'},
]
```

### Callbacks

The library supports multiple callback types that fire in a specific order during
state transitions:

1. **`prepare`** (transition-level): Runs first, before any conditions are checked.
2. **`conditions`/`unless`**: Guard conditions checked next.
3. **`before_state_change`** (machine-level): Runs before EVERY state change.
4. **`before`** (transition-level): Runs after machine-level before.
5. **Exit callbacks** (`on_exit`): Fire on the source state.
6. **State update**: The model's state attribute is updated.
7. **Enter callbacks** (`on_enter`): Fire on the destination state.
8. **`after`** (transition-level): Runs after the transition completes.
9. **`after_state_change`** (machine-level): Runs after EVERY state change.
10. **`finalize_event`** (machine-level): Always runs, even on error.

**Contract**: Machine-level callbacks wrap transition-level callbacks. So
`before_state_change` fires before `before`, and `after` fires before
`after_state_change`.

### Auto-transitions

When `auto_transitions=True` (default), the machine generates convenience methods
`to_<state_name>()` on the model for every state. These allow direct transitions
to any state without defining explicit transitions:

```python
m = Machine(model=model, states=['A', 'B', 'C'], initial='A',
            auto_transitions=True)
model.to_B()    # model.state == 'B'
model.to_C()    # model.state == 'C'
```

### model.to() Convenience Method

`HierarchicalMachine` provides a `model.to(state_name)` method that creates
a temporary transition from the current state to the specified destination and
executes it immediately:

```python
model.to('target_state')  # transitions from current state to target_state
```

**Behavior**: `model.to(dest)` internally:
1. Reads the current state from the model
2. Creates a one-off transition from current_state to dest
3. Executes the transition (including all exit/enter callbacks)
4. After execution, `model.state` equals `dest`

This works with both flat and nested state names:

```python
model.to('parent_child')      # transition to nested state
model.to('sibling')           # transition to top-level state
```

**Contract**: After `model.to('X')`, `model.state` MUST equal `'X'` (or the
nested equivalent). The method creates a transition FROM current TO destination,
never the reverse.

### Ordered Transitions

`add_ordered_transitions()` creates a chain of transitions that move through
states in sequence:

```python
m = Machine(states=['A', 'B', 'C'], initial='A')
m.add_ordered_transitions(trigger='next_state')
# Creates: A -next_state-> B -next_state-> C -next_state-> A (loop)
```

**Parameters**:
- `states`: List of states to chain. If None, uses all machine states.
- `trigger`: The trigger name (default: `'next_state'`).
- `loop`: If True, last state loops back to first (default: True).
- `loop_includes_initial`: If True, loop-back goes to initial state (default: True).

**State ordering contract**: When `states` is None, the machine enumerates
all states using `get_nested_state_names()`. The enumeration follows
**parent-first** order: a parent state appears before any of its children
in the returned list.

---

## Hierarchical (Nested) State Machine: `HierarchicalMachine`

### Import

```python
from transitions.extensions import HierarchicalMachine
```

### Nested State Definition

States can contain children, creating a hierarchy:

```python
states = [
    {'name': 'idle'},
    {'name': 'active',
     'children': [
         {'name': 'running', 'on_enter': 'start_run'},
         {'name': 'paused', 'on_enter': 'pause_run'},
     ],
     'initial': 'running'},  # default child state
    {'name': 'done', 'final': True}
]
```

### State Naming Convention

Nested states are referenced using underscore-separated paths:

```
parent_child          -> child state within parent
parent_child_grandchild -> three levels deep
```

The separator character is `_` by default (configurable via
`NestedState.separator`).

### Hierarchical Enter/Exit Callback Order

When transitioning into a nested state, callbacks fire **top-down** (parent
first, then children):

```python
# Transitioning to 'parent_child_grandchild':
# 1. parent.on_enter fires
# 2. child.on_enter fires
# 3. grandchild.on_enter fires
```

When exiting a nested state, callbacks fire **bottom-up** (children first,
then parents):

```python
# Exiting from 'parent_child_grandchild':
# 1. grandchild.on_exit fires
# 2. child.on_exit fires
# 3. parent.on_exit fires
```

**Contract**: Enter callbacks ALWAYS fire in parent-to-child order. Exit
callbacks ALWAYS fire in child-to-parent order. This matches the "onion"
model of nested state machines: you enter from outside-in and exit from
inside-out.

### State Update Timing

During a transition, the model's state attribute is updated AFTER exit
callbacks complete but BEFORE enter callbacks fire:

```
exit callbacks -> model.state updated -> enter callbacks
```

This means:
- During `on_exit`, `model.state` still reflects the source state
- During `on_enter`, `model.state` already reflects the destination state

### Exit Callback Scope

During exit callbacks, each state's `on_exit` is called with proper scope
resolution. The state's `name` property returns the **fully qualified name**
(global name) of the state being exited.

For a state hierarchy `A > mid > deep`:
- When exiting `deep`, the exit callback for `deep` sees name = `A_mid_deep`
- When exiting `mid`, the exit callback for `mid` sees name = `A_mid`
- When exiting `A`, the exit callback for `A` sees name = `A`

**Contract**: The state name reported during exit callbacks must be the
correct global path. The last segment should NOT be duplicated (e.g.,
`A_mid_mid` would be incorrect for state `mid` under parent `A`).

### Parallel (Orthogonal) States

A state can have multiple initial children, creating parallel regions:

```python
states = [
    {'name': 'active',
     'initial': ['region1', 'region2'],  # parallel children
     'children': [
         {'name': 'region1', ...},
         {'name': 'region2', ...},
     ]},
]
```

When entering `active`, both `region1` and `region2` are entered simultaneously.
Events are processed in all active regions.

### on_final Callbacks

When `on_final` is set on the machine or a state, it fires when a state
marked with `final=True` is entered:

```python
m = HierarchicalMachine(
    states=[...],
    on_final=lambda: print("Final state reached!")
)
```

For parallel states, `on_final` fires only when ALL parallel children have
reached their final states.

### Nested State Enumeration

`get_nested_state_names()` returns a list of all state names in the machine,
using **parent-first** ordering:

```python
# For states: A (children: sub1, sub2), B
m.get_nested_state_names()
# Returns: ['A', 'A_sub1', 'A_sub2', 'B']
```

**Contract**: Parent states always appear before their children in the returned
list. This ordering is used by `add_ordered_transitions()` to determine the
transition chain sequence.

### Internal Transition Resolution

When a transition is triggered in a nested state machine, the library resolves
which states to exit and enter:

1. **Find common ancestor**: Identify the lowest common ancestor of source
   and destination states.
2. **Construct exit partials**: Build a list of exit callbacks for all states
   from source up to (but not including) the common ancestor. Exit callbacks
   fire bottom-up (deepest state first).
3. **Construct enter partials**: Build a list of enter callbacks for all states
   from the common ancestor down to the destination. Enter callbacks fire
   top-down (shallowest state first).
4. **Execute**: Exit partials -> update model state -> enter partials.

### Scoped Operations

`HierarchicalMachine` uses a context manager to scope operations to a
particular level of the state hierarchy:

```python
with machine(state_name):
    # operations scoped to state_name
    ...
```

This affects how state names are resolved and how the machine processes
nested state references.

### NestedState Properties

Each `NestedState` has:
- `name`: Returns the state's name in its current scope context
- `scoped_enter(event_data, scope)`: Enter with proper scope set
- `scoped_exit(event_data, scope)`: Exit with proper scope set
- `initial`: The initial child state(s)
- `final`: Whether this is a final state

The `scoped_enter` and `scoped_exit` methods set the internal `_scope`
before calling the regular `enter`/`exit` methods. This ensures that when
callbacks access `state.name`, they get the fully qualified name.

### resolve_order()

`resolve_order(state_tree)` takes a nested OrderedDict representing the
active state tree and returns an ordered list of state paths for processing.
The order is:
- Children before parents (for exit processing)
- Siblings in declaration order

This is used internally to determine the order of exit callbacks when
leaving nested/parallel states.

### Event Processing in Nested States

When an event is triggered:

1. The machine checks if the current state (or any parent) has a matching
   transition.
2. For parallel states, events are sent to all active regions.
3. A `done` set tracks which states have already processed the event to
   prevent double-processing.

### Auto-transitions in HSM

When `auto_transitions=True`, `HierarchicalMachine` generates `to_<state>()`
methods for all states in the hierarchy, including nested ones:

```python
states = [
    {'name': 'A', 'children': ['sub1', 'sub2']},
    'B'
]
m = HierarchicalMachine(model=model, states=states, initial='A',
                        auto_transitions=True)
model.to_A()       # go to A (enters initial child)
model.to_A_sub1()  # go directly to A_sub1
model.to_B()       # go to B
```

---

## Usage Examples

### Basic Nested State Machine

```python
from transitions.extensions import HierarchicalMachine

class Matter:
    pass

states = [
    'solid',
    {'name': 'liquid',
     'children': ['calm', 'turbulent'],
     'initial': 'calm'},
    'gas'
]

transitions = [
    {'trigger': 'melt', 'source': 'solid', 'dest': 'liquid'},
    {'trigger': 'evaporate', 'source': 'liquid', 'dest': 'gas'},
    {'trigger': 'condense', 'source': 'gas', 'dest': 'liquid'},
    {'trigger': 'freeze', 'source': 'liquid', 'dest': 'solid'},
    {'trigger': 'stir', 'source': 'liquid_calm', 'dest': 'liquid_turbulent'},
]

matter = Matter()
m = HierarchicalMachine(model=matter, states=states, transitions=transitions,
                        initial='solid')

matter.melt()
# matter.state == 'liquid_calm' (entered initial child)
matter.stir()
# matter.state == 'liquid_turbulent'
```

### Tracking Callback Order

```python
log = []

states = [
    {'name': 'A',
     'on_enter': lambda: log.append('enter_A'),
     'on_exit': lambda: log.append('exit_A'),
     'children': [
         {'name': 'deep',
          'on_enter': lambda: log.append('enter_A_deep'),
          'on_exit': lambda: log.append('exit_A_deep')}
     ],
     'initial': 'deep'},
    {'name': 'B',
     'on_enter': lambda: log.append('enter_B'),
     'on_exit': lambda: log.append('exit_B')},
]

class Model:
    pass

model = Model()
m = HierarchicalMachine(model=model, states=states, initial='A_deep')

m.add_transition('go', 'A_deep', 'B')
model.go()

# log == ['exit_A_deep', 'exit_A', 'enter_B']
# Exit: child first (A_deep), then parent (A)
# Enter: parent first (only B, no children)
```

### Using model.to()

```python
states = ['ready', 'processing', 'complete']
model = Model()
m = HierarchicalMachine(model=model, states=states, initial='ready',
                        auto_transitions=True)

model.to('processing')
assert model.state == 'processing'

model.to('complete')
assert model.state == 'complete'

# Also works with nested states
states2 = [
    'idle',
    {'name': 'work', 'children': ['task1', 'task2']},
]
model2 = Model()
m2 = HierarchicalMachine(model=model2, states=states2, initial='idle',
                         auto_transitions=True)
model2.to('work_task1')
assert model2.state == 'work_task1'
```

### Ordered Transitions with Nested States

```python
states = [
    {'name': 'phase1', 'children': ['setup', 'run']},
    {'name': 'phase2', 'children': ['validate', 'report']},
    'done'
]

model = Model()
m = HierarchicalMachine(model=model, states=states, initial='phase1')
m.add_ordered_transitions(trigger='next')

# Traversal follows parent-first enumeration:
# phase1 -> phase1_setup -> phase1_run -> phase2 -> phase2_validate ->
# phase2_report -> done -> (loop back to phase1)

model.next()  # phase1 -> phase1_setup
model.next()  # phase1_setup -> phase1_run
model.next()  # phase1_run -> phase2
model.next()  # phase2 -> phase2_validate
model.next()  # phase2_validate -> phase2_report
model.next()  # phase2_report -> done
```

---

## API Summary Table

| Method | Class | Description |
|--------|-------|-------------|
| `add_transition()` | Machine | Add a transition between states |
| `add_ordered_transitions()` | Machine | Create sequential transition chain |
| `get_transitions()` | Machine | Query transitions by source/dest |
| `add_states()` | Machine | Add new states to the machine |
| `to(state_name)` | Model (via HSM) | Direct transition to any state |
| `to_<state>()` | Model | Auto-generated convenience transition |
| `get_nested_state_names()` | HierarchicalMachine | List all states in parent-first order |
| `get_nested_transitions()` | HierarchicalMachine | List all transitions including nested |
| `trigger_event()` | HierarchicalMachine | Process events recursively |

---

## Key Invariants

1. **Enter order**: Parent on_enter fires before child on_enter (top-down).
2. **Exit order**: Child on_exit fires before parent on_exit (bottom-up).
3. **State update timing**: model.state updated after exit, before enter.
4. **Enumeration order**: `get_nested_state_names()` returns parent before children.
5. **to() semantics**: `model.to(X)` results in `model.state == X`.
6. **Exit scope**: State name during on_exit reflects the correct global path.
7. **Ordered transitions**: Chain follows `get_nested_state_names()` order.
