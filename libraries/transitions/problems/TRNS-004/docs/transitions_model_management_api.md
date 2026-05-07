# transitions 0.9.3 — Machine Model Management API

## Overview

The `transitions` library (v0.9.3) provides a lightweight, object-oriented
finite state machine (FSM) implementation for Python. A central concept is the
**Machine**, which manages states, transitions, and one or more **models**.

Models are plain Python objects that the Machine decorates with convenience
methods (triggers, state checks) and whose state attribute is managed
automatically during transitions.

This document covers the Machine's model management API: how models are
registered and removed, how triggers are bound, how Enum states interact with
models, how dynamic callbacks are auto-discovered, how transitions are
removed, and how events are dispatched across multiple models.

---

## 1. Machine Initialization and Model Registration

### 1.1 Constructor

```python
Machine(model='self', states=None, initial='initial', transitions=None,
        send_event=False, auto_transitions=True, ordered_transitions=False,
        ignore_invalid_triggers=None, before_state_change=None,
        after_state_change=None, name=None, queued=False,
        prepare_event=None, finalize_event=None, model_attribute='state',
        model_override=False, on_exception=None, on_final=None)
```

**Key parameters:**

- `model`: The object(s) to manage. Can be a single object, a list of objects,
  or the string `'self'` (default) which makes the Machine itself the model.
  An empty list means no model is attached initially.
- `states`: List of state names (strings), Enum members, or State objects.
- `initial`: The initial state assigned to all models on registration.
- `auto_transitions`: When `True`, creates `to_<state>()` methods on models.
- `model_attribute`: Name of the attribute on the model that holds the current
  state. Default is `'state'`.
- `model_override`: When `True`, existing attributes on the model with the same
  name as trigger methods will be overwritten. When `False` (default), existing
  attributes are preserved and a warning is logged.
- `ignore_invalid_triggers`: When `True`, calling a trigger that is not valid
  for the current state silently returns `False` instead of raising.

### 1.2 add_model(model, initial=None)

Registers one or more models with the Machine:

1. Binds `model.trigger(name, *args, **kwargs)` — generic trigger dispatcher.
2. Binds `model.may_trigger(name)` — checks if a trigger can fire.
3. For every registered event/trigger, binds `model.<trigger_name>()`.
4. For every state, binds `model.is_<state>()` check methods.
5. Auto-discovers dynamic callbacks on the model class (see Section 4).
6. Sets the model's initial state via `set_state()`.

```python
class Robot:
    pass

r1, r2 = Robot(), Robot()
machine = Machine(model=[r1, r2], states=['idle', 'working'], initial='idle')
# Both r1 and r2 now have .go(), .is_idle(), .is_working(), etc.
```

### 1.3 remove_model(model)

Removes a model from the Machine's model list. After removal:

- The model retains its existing trigger method bindings from when it was
  registered. These still reference the Machine's events.
- The model will NOT receive new triggers if transitions are added later.
- If the Machine uses queued processing, any queued events for the removed
  model are discarded (except the currently executing event).

```python
machine.remove_model(r2)
# r2 still has r2.go() but won't be included in dispatch() calls
```

---

## 2. State Types and Model State Attribute

### 2.1 String States

The simplest form. The model's `state` attribute is set to a plain string:

```python
machine = Machine(model=m, states=['A', 'B'], initial='A')
assert m.state == 'A'
assert m.is_A() is True
```

### 2.2 Enum States

States can be Python Enum members. When using Enum states, the model's `state`
attribute is set to the **Enum member itself** (not its name or value string):

```python
from enum import Enum

class TrafficLight(Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3

machine = Machine(model=m, states=TrafficLight, initial=TrafficLight.RED)
assert m.state == TrafficLight.RED          # Enum member, not string
assert isinstance(m.state, TrafficLight)    # True
assert m.is_RED() is True
```

**Important invariant:** After any transition or `set_state()` call with Enum
states, `model.state` must be an Enum member. The `is_<state>()` methods
compare `model.state` against the Enum member's value, so if `model.state`
were set to a string name instead, the comparison would fail.

### 2.3 set_state(state, model=None)

Directly sets the state of one or all models:

```python
machine.set_state(TrafficLight.GREEN, model=m)
assert m.state == TrafficLight.GREEN
assert m.is_GREEN() is True
```

When called without `model`, sets ALL attached models to the given state.

### 2.4 get_model_state(model)

Returns the `State` object for a model's current state:

```python
state_obj = machine.get_model_state(m)
print(state_obj.name)  # 'GREEN'
```

---

## 3. Trigger Methods and Event Binding

### 3.1 Trigger Binding

When a transition is added, the Machine creates an `Event` object and binds a
trigger method to each model:

```python
machine.add_transition('advance', 'idle', 'working')
# m.advance() is now available
```

The trigger method is a `functools.partial` of `Event.trigger(model, ...)`.

### 3.2 may_<trigger>() Methods

For each trigger, a `may_<trigger>()` method is also bound:

```python
if m.may_advance():
    m.advance()
```

This checks conditions without executing the transition.

### 3.3 model_override

By default (`model_override=False`), the Machine will NOT overwrite existing
attributes on the model. If a model already has a method named `advance`, the
trigger binding is skipped and a warning is logged.

With `model_override=True`, existing attributes are always overwritten.

---

## 4. Dynamic Callback Auto-Discovery

### 4.1 Convention-Based Callbacks

The Machine automatically discovers callback methods on the **model class**
that follow naming conventions:

- `on_enter_<state>(self)` — called when entering `<state>`
- `on_exit_<state>(self)` — called when exiting `<state>`

These are auto-registered as state callbacks during `add_model()`.

**Requirements:**

1. The method must be defined on the **model's class** (not set via `setattr`
   on the instance), so that `inspect.ismethod()` returns `True`.
2. The method must not already be listed in the state's `on_enter` /
   `on_exit` callback list. If it is already explicitly registered, the
   auto-discovery skips it to prevent duplicate calls.

```python
class Robot:
    def on_enter_working(self):
        print("Robot started working!")
    def on_exit_working(self):
        print("Robot stopped working!")

r = Robot()
machine = Machine(model=r, states=['idle', 'working'], initial='idle')
machine.add_transition('go', 'idle', 'working')
r.go()  # prints "Robot started working!"
```

### 4.2 Deduplication

If `on_enter_working` is already in the state's `on_enter` list (e.g., passed
via the `on_enter` parameter in the state definition), the auto-discovery will
NOT add it again:

```python
states = [
    'idle',
    {'name': 'working', 'on_enter': ['on_enter_working']}
]
# on_enter_working will NOT be duplicated
```

### 4.3 Transition-Level Dynamic Callbacks

Similar convention applies to transitions: if the model defines methods named
`before_<trigger>`, `after_<trigger>`, or `prepare_<trigger>`, they are
auto-discovered and registered as transition callbacks.

---

## 5. Transition Management

### 5.1 add_transition(trigger, source, dest, ...)

Creates a transition:

```python
machine.add_transition('run', 'idle', 'working',
                       conditions='is_charged',
                       before='log_start',
                       after='notify_complete')
```

**Parameters:**

- `trigger`: Method name that triggers the transition
- `source`: Source state (string, Enum, list, or `'*'` for all states)
- `dest`: Destination state (string, Enum, `'='` for reflexive, `None` for
  internal transition)
- `conditions`: Callbacks that must all return `True`
- `unless`: Callbacks that must all return `False`
- `before`: Callbacks executed before the transition
- `after`: Callbacks executed after the transition
- `prepare`: Callbacks executed when trigger is activated

### 5.2 remove_transition(trigger, source='*', dest='*')

Removes transitions matching the given criteria:

```python
# Remove all 'run' transitions FROM 'idle'
machine.remove_transition('run', source='idle')

# Remove all 'run' transitions TO 'working'
machine.remove_transition('run', dest='working')

# Remove all 'run' transitions from 'idle' to 'working'
machine.remove_transition('run', source='idle', dest='working')

# Remove ALL 'run' transitions (source='*' and dest='*' are defaults)
machine.remove_transition('run')
```

**Semantics:**

- When `source` is specified (not `'*'`), only transitions with matching
  `source` are removed.
- When `dest` is specified (not `'*'`), only transitions with matching
  `dest` are removed.
- When both are specified, only transitions matching BOTH are removed.
- When neither is specified (both `'*'`), ALL transitions for that trigger
  are removed.
- If removing transitions results in no transitions left for a trigger,
  the trigger method is also removed from all models.

**Invariant:** After `remove_transition('t', source='X')`, no remaining
transition for trigger `'t'` should have `source == 'X'`. Transitions from
other sources must be preserved. Similarly for `dest` filtering.

### 5.3 get_transitions(trigger='', source='*', dest='*')

Queries registered transitions:

```python
# All transitions for trigger 'run'
trans = machine.get_transitions(trigger='run')

# All transitions from 'idle'
trans = machine.get_transitions(source='idle')

# All transitions to 'working'
trans = machine.get_transitions(dest='working')
```

Each transition object has `.source` and `.dest` attributes.

---

## 6. Multi-Model Machines

### 6.1 Registering Multiple Models

A Machine can manage multiple models simultaneously:

```python
class Worker:
    pass

w1, w2, w3 = Worker(), Worker(), Worker()
machine = Machine(model=[w1, w2, w3], states=['idle', 'busy'],
                  initial='idle')
```

Each model has its own independent state but shares the same set of states
and transitions.

### 6.2 dispatch(trigger, *args, **kwargs)

Triggers an event on ALL registered models:

```python
result = machine.dispatch('go')
```

**Return value:** The return value is the **conjunction (AND)** of all
individual trigger results. `dispatch` returns `True` only if ALL models
successfully executed the transition. If any model's trigger returns `False`
(e.g., the model is in a state where the trigger is invalid), `dispatch`
returns `False`.

```python
# If m1 can trigger 'go' (returns True) and m2 cannot (returns False):
result = machine.dispatch('go')  # Returns False (AND of [True, False])
```

**Invariant:** `dispatch(trigger)` must return `all(results)` where `results`
is the list of individual trigger return values. This ensures the caller knows
whether ALL models transitioned successfully, which is critical for maintaining
consistent multi-model state.

### 6.3 Independent Model States

Each model tracks its own state independently:

```python
w1.go()  # w1 transitions, w2 stays
assert w1.state == 'busy'
assert w2.state == 'idle'
```

---

## 7. Ordered Transitions

### 7.1 add_ordered_transitions(states=None, trigger='next_state', loop=True, loop_includes_initial=True, ...)

Creates a chain of transitions through states in order:

```python
machine = Machine(states=['A', 'B', 'C'], initial='A')
machine.add_ordered_transitions()
# Creates: A->B, B->C, C->A (loop back to initial)
```

**Parameters:**

- `states`: List of states defining the order. Default: all states.
- `trigger`: Trigger name. Default: `'next_state'`.
- `loop`: Whether to add a transition from last to first state.
- `loop_includes_initial`: When `True`, the loop-back goes to the initial
  state. When `False`, it goes to the second state (skipping initial).

---

## 8. Callback Execution Order

### 8.1 Machine-Level vs Transition-Level Callbacks

The Machine supports both machine-level and transition-level callbacks:

- **Machine-level:** `before_state_change`, `after_state_change`
- **Transition-level:** `before`, `after`

**Execution order during a transition:**

1. `prepare` (transition-level)
2. Condition checks (`conditions`, `unless`)
3. `before_state_change` (machine-level) — runs BEFORE transition `before`
4. `before` (transition-level)
5. State exit callbacks (`on_exit_<state>`)
6. State change (model attribute updated)
7. State enter callbacks (`on_enter_<state>`)
8. `after` (transition-level) — runs BEFORE machine `after_state_change`
9. `after_state_change` (machine-level)
10. `finalize_event` (always runs, even on error)

### 8.2 Condition Semantics

- `conditions`: List of callbacks that must ALL return `True` for the
  transition to proceed.
- `unless`: List of callbacks that must ALL return `False` for the
  transition to proceed.

---

## 9. State Attributes

### 9.1 State.name

The string name of the state. For Enum states, this is the Enum member's
name (e.g., `'RED'` for `TrafficLight.RED`).

### 9.2 State.value

The value associated with the state. For string states, this equals `name`.
For Enum states, this is the Enum member itself (e.g., `TrafficLight.RED`).

### 9.3 State.final

When `True`, reaching this state triggers `on_final` callbacks.

---

## 10. Error Handling

### 10.1 MachineError

Raised when an invalid transition is attempted (unless
`ignore_invalid_triggers=True`):

```python
try:
    m.go()  # invalid for current state
except MachineError:
    pass
```

### 10.2 on_exception

Machine-level callback for handling exceptions during transitions:

```python
machine = Machine(..., on_exception='handle_error')
```

---

## 11. Summary of Key Invariants

1. **Enum state identity**: After any transition or `set_state()` with Enum
   states, `model.state` is the Enum member (not a string name).
2. **Dynamic callback auto-discovery**: Model methods matching
   `on_enter_<state>` / `on_exit_<state>` are automatically registered unless
   already explicitly present in the state's callback list.
3. **remove_transition correctness**: Filtering by `source` removes only
   transitions FROM that source; filtering by `dest` removes only transitions
   TO that destination.
4. **dispatch AND semantics**: `dispatch()` returns `True` only when ALL
   models successfully trigger the event.
5. **is_<state> consistency**: `is_<state>()` always returns `True` for the
   current state, regardless of state type (string or Enum).
