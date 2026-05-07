# transitions 0.9.3 — Core State Machine API Reference

## Overview

`transitions` is a lightweight, object-oriented finite state machine (FSM)
implementation for Python. It provides a `Machine` class that manages states,
transitions, and models. The machine can be attached to any Python object
(the "model"), decorating it with state-checking methods and event triggers.

## Installation

```
pip install transitions==0.9.3
```

## Quick Start

```python
from transitions import Machine

class Matter:
    pass

model = Matter()
states = ['solid', 'liquid', 'gas']
transitions = [
    {'trigger': 'melt', 'source': 'solid', 'dest': 'liquid'},
    {'trigger': 'evaporate', 'source': 'liquid', 'dest': 'gas'},
    {'trigger': 'condense', 'source': 'gas', 'dest': 'liquid'},
]

machine = Machine(model=model, states=states, transitions=transitions,
                  initial='solid')

model.state     # 'solid'
model.melt()    # True
model.state     # 'liquid'
```

---

## Core Classes

### `Machine`

The central class managing states, transitions, and models.

#### Constructor

```python
Machine(
    model=Machine.self_literal,  # the model object, or Machine.self_literal for self-reference
    states=None,                 # list of state names, State objects, or Enums
    initial='initial',           # the initial state name
    transitions=None,            # list of transition definitions
    send_event=False,            # if True, pass EventData to callbacks
    auto_transitions=True,       # auto-create to_<state>() triggers for all states
    ordered_transitions=False,   # auto-create next_state() ordered transitions
    ignore_invalid_triggers=None,# silently ignore invalid triggers
    before_state_change=None,    # machine-level before-state-change callbacks
    after_state_change=None,     # machine-level after-state-change callbacks
    prepare_event=None,          # machine-level prepare callbacks
    finalize_event=None,         # machine-level finalize callbacks
    on_exception=None,           # machine-level exception handler callbacks
    on_final=None,               # callbacks triggered when entering a final state
    queued=False,                # queue transitions for sequential processing
    name=None,                   # machine name prefix for logging
    model_attribute='state',     # name of the state attribute on the model
    model_override=False,        # override existing model methods
    **kwargs
)
```

#### Key Methods

##### `add_state(states, on_enter=None, on_exit=None, ignore_invalid_triggers=None)`

Add one or more states to the machine. States can be strings, `State` objects,
Enum members, or dicts.

##### `add_transition(trigger, source, dest, conditions=None, unless=None, before=None, after=None, prepare=None)`

Add a single transition.

- **trigger** (str): Name of the trigger method (e.g., `'melt'` creates `model.melt()`).
- **source** (str or list or `'*'`): Source state(s). Use `'*'` for all states.
- **dest** (str or `'='` or None): Destination state. `'='` means reflexive (dest=source).
  `None` means internal transition (no state change, no enter/exit callbacks).
- **conditions** (str or list): Condition(s) that must ALL return `True` for the
  transition to proceed.
- **unless** (str or list): Condition(s) that must ALL return `False` for the
  transition to proceed. This is the logical inverse of `conditions`: if an
  `unless` callback returns `True`, the transition is **blocked**.
- **before** (str or list): Callbacks executed before the transition (after conditions pass).
- **after** (str or list): Callbacks executed after the transition completes.
- **prepare** (str or list): Callbacks executed before condition checks.

##### `add_ordered_transitions(states=None, trigger='next_state', loop=True, loop_includes_initial=True, conditions=None, unless=None, before=None, after=None, prepare=None)`

Create sequential transitions between states in order.

- **states** (list or None): Ordered list of state names. If None, uses all states
  in their registration order.
- **trigger** (str): The trigger name (default `'next_state'`).
- **loop** (bool): If True, add a transition from the last state back to complete
  the cycle.
- **loop_includes_initial** (bool): When `loop=True`:
  - If `True` (default): the loop-back transition goes to the **initial state**
    (the first state in the cycle).
  - If `False`: the loop-back transition **skips** the initial state and goes to
    the **second state** in the cycle.
  - This parameter has no effect if the initial state is not in the states list.
- **conditions/unless/before/after/prepare**: These parameters accept either a
  single value (applied to ALL transitions) or a list of values (one per
  transition). When `loop=True`, the number of transitions equals the number
  of states; when `loop=False`, it equals `len(states) - 1`.

**Example**:
```python
machine = Machine(model=m, states=['A', 'B', 'C'], initial='A')
machine.add_ordered_transitions(loop=True, loop_includes_initial=True)
# Creates: A->B, B->C, C->A (loops back to initial A)

machine2 = Machine(model=m2, states=['A', 'B', 'C'], initial='A')
machine2.add_ordered_transitions(loop=True, loop_includes_initial=False)
# Creates: A->B, B->C, C->B (loops back to B, skipping initial A)
```

##### `get_triggers(*args)`

Return a list of trigger names available from the given state(s).

```python
machine.get_triggers('solid')  # ['melt', 'to_solid', 'to_liquid', 'to_gas']
```

##### `get_transitions(trigger="", source="*", dest="*")`

Return a list of `Transition` objects matching the given filters.

- **trigger** (str): Filter by trigger/event name. Empty string matches all triggers.
- **source** (str): Filter by source state. `'*'` matches all sources.
- **dest** (str): Filter by destination state. `'*'` matches all destinations.

**Contract**: When `source` is specified (not `'*'`), every returned transition's
`.source` attribute must equal the specified source. When `dest` is specified,
every returned transition's `.dest` attribute must equal the specified dest.

```python
# Get all transitions triggered by 'go' from state 'A'
transitions = machine.get_transitions(trigger='go', source='A')
for t in transitions:
    assert t.source == 'A'  # guaranteed by the source filter
```

##### `remove_transition(trigger, source="*", dest="*")`

Remove transition(s) matching the given filters.

##### `dispatch(trigger, *args, **kwargs)`

Trigger an event on all models attached to the machine.

##### `set_state(state, model=None)`

Set the current state. If model is None, sets state on all models.

##### `get_state(state)`

Return the State object for the given state name.

---

### `State`

Represents a persistent state managed by a Machine.

#### Attributes

- **name** (str): The state name.
- **on_enter** (list): Callbacks executed when entering this state.
- **on_exit** (list): Callbacks executed when exiting this state.
- **ignore_invalid_triggers** (bool): Override machine-level setting.
- **final** (bool): If True, entering this state triggers `on_final` callbacks.

---

### `Transition`

Represents a transition between two states.

#### Attributes

- **source** (str): Source state name.
- **dest** (str): Destination state name (None for internal transitions).
- **conditions** (list): List of Condition objects that must all pass.
- **before** (list): Before-transition callbacks.
- **after** (list): After-transition callbacks.
- **prepare** (list): Pre-condition-check callbacks.

#### Execution Order

When a transition is triggered, callbacks execute in this specific order:

1. **Transition.prepare** callbacks
2. **Condition evaluation** (all conditions must pass, including `unless` conditions)
3. **Machine.before_state_change** callbacks, then **Transition.before** callbacks
4. **State exit** callbacks (`on_exit` of source state)
5. **State change** (model's state attribute updated)
6. **State enter** callbacks (`on_enter` of destination state)
7. **Transition.after** callbacks, then **Machine.after_state_change** callbacks

Note the ordering of step 3 and step 7: for `before` callbacks, machine-level
runs first then transition-level; for `after` callbacks, **transition-level runs
first** then machine-level. This ensures transition-specific after-processing
completes before machine-wide after-processing.

---

### `Condition`

Wraps a condition check function.

#### Constructor

```python
Condition(func, target=True)
```

- **func**: The callable or its name.
- **target** (bool): The expected return value.
  - `target=True`: condition passes when `func()` returns `True`
  - `target=False`: condition passes when `func()` returns `False`

#### How `conditions` and `unless` work

When you add a transition:
```python
machine.add_transition('go', 'A', 'B',
                       conditions=['is_ready'],
                       unless=['is_blocked'])
```

- `conditions` creates `Condition(func, target=True)` — func must return True
- `unless` creates `Condition(func, target=False)` — func must return False

All conditions are evaluated with AND logic: ALL must pass for the transition
to proceed. If any condition fails, the transition is halted.

**Key semantic**: `unless` is the logical negation of `conditions`. An `unless`
callback returning `True` means "yes, this should be blocked", so the transition
is halted. An `unless` callback returning `False` means "no, don't block", so
the transition proceeds.

---

### `Event`

A collection of transitions assigned to the same trigger name.

#### Processing Flow

1. **Machine.prepare_event** callbacks execute
2. For each transition matching the current source state:
   a. Execute `Transition.execute()` (which includes prepare, conditions, before,
      state change, after)
   b. If successful, stop (first matching transition wins)
3. **Machine.finalize_event** callbacks execute (always, even on exception)

---

### `EventData`

Data container passed to callbacks when `send_event=True`.

#### Attributes

- **state** (State): The source state.
- **event** (Event): The triggered event.
- **machine** (Machine): The machine instance.
- **model**: The model object.
- **args** (tuple): Positional arguments passed to the trigger.
- **kwargs** (dict): Keyword arguments passed to the trigger.
- **transition** (Transition): The current transition being processed.
- **result** (bool): The result of the transition attempt.
- **error** (Exception): Any exception that occurred.

---

## Auto-transitions

When `auto_transitions=True` (default), the machine automatically creates
`to_<state>()` methods for every state, allowing direct state jumps from
any state.

```python
model.to_liquid()  # Jump directly to 'liquid' from any state
```

## Queued Transitions

When `queued=True`, transitions triggered during callbacks are queued and
processed sequentially after the current transition completes.

```python
machine = Machine(model=m, states=['A', 'B', 'C'], initial='A', queued=True)
```

## Wildcard Transitions

Use `'*'` as the source to create a transition from all states:

```python
machine.add_transition('reset', '*', 'A')  # Reset to A from any state
```

Use `'='` as the destination for reflexive transitions:

```python
machine.add_transition('refresh', '*', '=')  # Stay in current state
```

## Internal Transitions

Set `dest=None` for transitions that execute callbacks without changing state
(no exit/enter callbacks):

```python
machine.add_transition('log', 'A', None, after='log_action')
```

## Dynamic Callbacks

Callbacks can be defined dynamically using naming conventions:

- `on_enter_<state>`: Called when entering `<state>`
- `on_exit_<state>`: Called when exiting `<state>`
- `before_<trigger>`: Called before `<trigger>` transition
- `after_<trigger>`: Called after `<trigger>` transition
- `prepare_<trigger>`: Called to prepare `<trigger>` transition

```python
class Model:
    def on_enter_liquid(self):
        print("Now liquid!")
    def before_melt(self):
        print("About to melt...")
```

## Model Attribute

The state is stored in the model's `state` attribute by default. This can be
changed with the `model_attribute` parameter:

```python
machine = Machine(model=m, states=['A', 'B'], initial='A',
                  model_attribute='my_state')
m.my_state  # 'A'
```

## State Convenience Methods

The machine adds `is_<state>()` methods and `may_<trigger>()` methods to the
model:

```python
model.is_solid()    # True if current state is 'solid'
model.may_melt()    # True if 'melt' can be triggered from current state
```

## Error Handling

- **MachineError**: Raised when attempting an invalid trigger from the current
  state (unless `ignore_invalid_triggers=True`).
- **on_exception** callbacks: Machine-level exception handlers that receive the
  EventData with the error.
- **finalize_event** callbacks: Always execute after a transition attempt,
  regardless of success or failure. Useful for cleanup.
