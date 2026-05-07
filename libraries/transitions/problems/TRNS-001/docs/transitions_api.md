# transitions 0.9.3 API Documentation

## Overview

`transitions` is a lightweight, object-oriented state machine library for Python.
It supports basic flat state machines and hierarchical (nested) state machines
via the `HierarchicalMachine` extension. Key features include callbacks, conditions,
parallel states, and queued event processing.

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
- `send_event`: When True, callbacks receive an `EventData` object instead of
  `*args, **kwargs`.
- `auto_transitions`: When True, auto-generates `to_<state>()` convenience methods.
- `queued`: When True, transitions triggered during callbacks are queued and
  processed sequentially rather than immediately.
- `before_state_change`: Machine-level callback(s) invoked before ANY state change.
- `after_state_change`: Machine-level callback(s) invoked after ANY state change.
- `prepare_event`: Callback(s) invoked before event processing.
- `finalize_event`: Callback(s) invoked after event processing (even on error).
- `on_final`: Callback(s) invoked when a final state is entered.
- `on_exception`: Callback(s) invoked when an exception occurs during transition.

### States

States can be defined as strings, dicts, or `State` objects:

```python
states = ['idle', 'running', 'finished']
# or with callbacks:
states = [
    {'name': 'idle'},
    {'name': 'running', 'on_enter': 'start_task', 'on_exit': 'cleanup'},
    {'name': 'finished', 'final': True}
]
```

**State properties**:
- `name` (str): The state's identifier.
- `on_enter` (str/list/callable): Callbacks triggered when entering the state.
- `on_exit` (str/list/callable): Callbacks triggered when exiting the state.
- `final` (bool): Marks the state as a final/accepting state.
- `ignore_invalid_triggers` (bool): Silently ignore invalid triggers in this state.

### Transitions

```python
machine.add_transition(trigger, source, dest,
                       conditions=None, unless=None,
                       before=None, after=None, prepare=None)
```

**Parameters**:
- `trigger` (str): Name of the trigger method (e.g., 'go' creates `model.go()`).
- `source` (str/list): Source state(s). Use `'*'` for all states.
- `dest` (str): Destination state. Use `'='` for reflexive transitions. Use `None`
  for internal transitions (no state change, no exit/enter callbacks).
- `conditions` (str/list): Callback(s) that must return True for transition to proceed.
- `unless` (str/list): Callback(s) that must return False for transition to proceed.
- `before` (str/list/callable): Transition-specific callbacks invoked before state change.
- `after` (str/list/callable): Transition-specific callbacks invoked after state change.
- `prepare` (str/list/callable): Callbacks invoked before condition evaluation.

### Callback Execution Order

When a transition is triggered, callbacks execute in this specific order:

1. **`prepare`** (transition-level): Invoked before conditions are evaluated.
2. **Conditions**: All conditions and unless checks are evaluated.
3. **`before_state_change`** (machine-level): Global before callbacks.
4. **`before`** (transition-level): Transition-specific before callbacks.
5. **State exit** (`on_exit`): Source state's exit callbacks.
6. **State change**: Model's state attribute is updated.
7. **State enter** (`on_enter`): Destination state's enter callbacks.
8. **`after`** (transition-level): Transition-specific after callbacks.
9. **`after_state_change`** (machine-level): Global after callbacks.
10. **`finalize_event`** (machine-level): Always invoked, even on error.

**Important**: Machine-level `before_state_change` runs BEFORE transition-level
`before`. Conversely, transition-level `after` runs BEFORE machine-level
`after_state_change`. This ordering ensures machine-level hooks wrap the
transition-specific callbacks.

### Conditions

Conditions are callbacks that must return True (or False for `unless`) for the
transition to proceed:

```python
machine.add_transition('go', 'idle', 'running',
                       conditions=['is_ready'],
                       unless=['is_locked'])
```

### Queued Processing

With `queued=True`, transitions triggered within callbacks are queued and processed
sequentially after the current transition completes:

```python
m = Machine(model=model, states=['A', 'B', 'C'], initial='A', queued=True)
```

### Final States

States marked with `final=True` trigger the machine's `on_final` callback when
entered:

```python
states = ['processing', {'name': 'done', 'final': True}]
m = Machine(model=model, states=states, initial='processing',
            on_final='handle_final')
```

---

## Hierarchical State Machine: `transitions.extensions.HierarchicalMachine`

### Overview

`HierarchicalMachine` extends `Machine` with support for nested (hierarchical)
states, parallel states, and scoped transitions. It uses `NestedState`,
`NestedTransition`, and `NestedEvent` internally.

### Constructor

```python
HierarchicalMachine(model=Machine.self_literal, states=None, initial='initial',
                    transitions=None, send_event=False, auto_transitions=True,
                    ordered_transitions=False, ignore_invalid_triggers=None,
                    before_state_change=None, after_state_change=None, name=None,
                    queued=False, prepare_event=None, finalize_event=None,
                    model_attribute='state', model_override=False,
                    on_exception=None, on_final=None)
```

Same parameters as `Machine`, with additional support for nested state definitions.

### Nested States

States can have children (substates):

```python
states = [
    {'name': 'active', 'initial': 'idle', 'children': [
        'idle',
        {'name': 'working', 'on_enter': 'start_work'},
        {'name': 'done', 'final': True}
    ]},
    'inactive'
]
```

**Key semantics**:
- State names use separator (default `'_'`) to form paths: `'active_idle'`,
  `'active_working'`.
- The `initial` property of a parent state determines which child state is
  entered when the parent is entered.
- Transitions can target any level: `'active'` (enters initial child),
  `'active_working'` (enters specific child).

### Parallel States

A parent state can have multiple initial children, creating parallel regions:

```python
states = [
    {'name': 'processing', 'initial': ['taskA', 'taskB'],
     'children': [
         {'name': 'taskA', 'initial': 'running', 'children': [
             'running', {'name': 'complete', 'final': True}
         ]},
         {'name': 'taskB', 'initial': 'running', 'children': [
             'running', {'name': 'complete', 'final': True}
         ]},
     ]}
]
```

When `initial` is a list, all listed children are entered simultaneously.
The model's state becomes a list of all active leaf states:
`['processing_taskA_running', 'processing_taskB_running']`.

### Parallel State Event Processing

Events in parallel states are processed using breadth-first ordering:
1. All children are evaluated BEFORE their parents.
2. Siblings are processed in their **declaration order**.
3. If a transition fires in one branch, that entire branch is marked as done
   and won't process further events.

### on_final Callback in Hierarchical States

The `on_final` callback in hierarchical machines has special semantics:

- **Leaf final states**: `on_final` fires when the state is entered.
- **Parent states with children**: `on_final` fires ONLY when **ALL** children
  have reached a final state. If a parent has parallel children (regions),
  ALL regions must be in a final state before the parent's `on_final` triggers.
- This check is recursive: a child is considered "final" only if it is a leaf
  final state OR all of its own children are final.

```python
# on_final for 'processing' fires only when BOTH taskA and taskB
# have reached their 'complete' (final) substates.
```

**Important**: In parallel states, entering a final state in ONE region does NOT
trigger the parent's `on_final`. The parent waits until ALL parallel regions
have reached final states.

### Nested Transition State Change Order

When a transition occurs between nested states, the following order is guaranteed:

1. **Exit callbacks**: All states being exited fire their `on_exit` callbacks,
   from deepest child to shallowest parent (inside-out).
2. **Model state update**: The model's state attribute is updated to reflect
   the new state(s).
3. **Enter callbacks**: All states being entered fire their `on_enter` callbacks,
   from shallowest parent to deepest child (outside-in).
4. **on_final check**: If the destination is a final state, on_final propagation
   is checked.

**Key guarantee**: During `on_enter` callbacks, `model.state` already reflects
the destination state. During `on_exit` callbacks, `model.state` still reflects
the source state.

### NestedState

`NestedState` extends `State` with:
- `states` (OrderedDict): Substates.
- `events` (dict): Events defined in this scope.
- `initial` (str/list): Initial child state(s).
- `on_final` (list): Callbacks for final state detection.

### NestedTransition

`NestedTransition` extends `Transition` with hierarchical state change logic:
- Handles entering/exiting nested state trees.
- Maintains parallel state consistency.
- Propagates on_final checks up the hierarchy.

### resolve_order Function

```python
resolve_order(state_tree) -> reversed iterator
```

Converts a state tree (dict of dicts) into an ordered list of state paths.
The ordering ensures:
1. ALL children are processed BEFORE their parents (BFS reversed).
2. Siblings maintain their **declaration order** in the final output.

This ordering is critical for:
- Exit callback sequencing (children exit before parents).
- Event processing in parallel states (deterministic sibling order).

---

## State Features (Mixins)

### Tags

```python
from transitions.extensions.states import Tags, add_state_features

@add_state_features(Tags)
class TagMachine(Machine):
    pass
```

Allows states to carry tags: `{'name': 'error', 'tags': ['critical']}`.
Check with `model.is_critical`.

### Timeout

States can have timeouts:
```python
{'name': 'waiting', 'timeout': 30, 'on_timeout': 'handle_timeout'}
```

### Volatile

Scoped temporary objects attached to states:
```python
{'name': 'processing', 'volatile': ProcessingContext, 'hook': 'ctx'}
```

### Retry

Limits re-entry count for self-transitions:
```python
{'name': 'attempting', 'retries': 3, 'on_failure': 'to_failed'}
```

---

## Common Patterns

### Conditional Transitions

```python
m.add_transition('proceed', 'checking', 'approved',
                 conditions=['has_valid_data', 'is_authorized'])
m.add_transition('proceed', 'checking', 'rejected',
                 unless=['has_valid_data'])
```

### Reflexive Transitions

```python
m.add_transition('retry', 'processing', '=')  # dest = source
```

### Internal Transitions

```python
m.add_transition('log', 'active', None)  # no state change, no exit/enter
```

### Wildcard Source

```python
m.add_transition('emergency_stop', '*', 'halted')  # from any state
```

### Multiple Models

```python
m = Machine(states=states, initial='idle')
m.add_model(model1)
m.add_model(model2)
# Each model has independent state
```

---

## Error Handling

- `MachineError`: Raised for invalid transitions (unless `ignore_invalid_triggers`).
- `on_exception` callback: Catches exceptions during transition execution.
- `finalize_event` callback: Always runs after transition (cleanup).

## EventData

When `send_event=True`, callbacks receive an `EventData` instance:
- `event_data.state`: Current state object.
- `event_data.transition`: Current transition object.
- `event_data.machine`: The machine instance.
- `event_data.model`: The model instance.
- `event_data.args`, `event_data.kwargs`: Arguments passed to trigger.
- `event_data.result`: Transition result (True/False).
- `event_data.error`: Exception if one occurred.
