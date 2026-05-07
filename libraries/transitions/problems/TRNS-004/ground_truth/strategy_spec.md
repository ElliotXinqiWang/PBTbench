# Strategy Specification — TRNS-004

## Bug 1: set_state uses state.name instead of state.value for Enum states

**Trigger condition**: Use Enum-based states (not string states). After any
transition or `set_state()` call, `model.state` is set to the string name
(e.g., `'A'`) instead of the Enum member (e.g., `States.A`). This causes
`is_<state>()` to return False because it compares `model.state` against
`state.value` (the Enum member).

**Why default strategy is insufficient**: Default Hypothesis strategies
generate string states. The bug is only triggered when using Python Enum
states, which is a specific API pattern that a PBT author must explicitly
test.

**Trigger probability with default strategy**: ~0% (string states are
unaffected since `state.name == state.value` for strings).

**Trigger probability with targeted strategy**: ~100% (any Enum state
machine triggers the bug on every transition).

**Minimum triggering input**: An Enum with 2 members, a Machine using those
Enum states, and one transition. After the transition, check
`isinstance(model.state, Enum)`.

**Example**:
```python
class S(Enum):
    A = 1
    B = 2
m = Model()
machine = Machine(model=m, states=S, initial=S.A)
machine.add_transition('go', S.A, S.B)
m.go()
assert isinstance(m.state, Enum)  # FAILS: m.state is 'B' not S.B
```

---

## Bug 2: Dynamic callback deduplication check inverted

**Trigger condition**: Define a model class with `on_enter_<state>()` or
`on_exit_<state>()` methods. The method is NOT explicitly listed in the
state's `on_enter`/`on_exit` definition. Normally, the Machine auto-discovers
and registers these methods. With the bug, the method is never registered
because the deduplication condition is inverted: it only adds the method if
it's already present (creating a duplicate), and skips it if it's absent.

**Why default strategy is insufficient**: Most baseline tests pass callbacks
explicitly (e.g., `on_enter='my_callback'`). The dynamic callback
convention (`on_enter_<state>` defined on the model class) is a separate
feature that requires specific knowledge of the auto-discovery mechanism.

**Trigger probability with default strategy**: ~3% (only if the test happens
to use convention-named methods without explicit registration).

**Trigger probability with targeted strategy**: ~100% (any model with
convention-named methods and no explicit callback registration triggers it).

**Minimum triggering input**: A model class with `on_enter_B(self)` method,
a Machine with states `['A', 'B']`, and a transition from A to B. Verify
the callback fires.

**Example**:
```python
class Model:
    def on_enter_working(self):
        self.entered = True

m = Model()
machine = Machine(model=m, states=['idle', 'working'], initial='idle')
machine.add_transition('go', 'idle', 'working')
m.go()
assert hasattr(m, 'entered')  # FAILS: callback was never registered
```

---

## Bug 3: remove_transition source/dest filter swap

**Trigger condition**: Call `remove_transition(trigger, source=X)` — this
should only remove transitions FROM state X. With the bug, it checks
`t.dest not in source` instead of `t.source not in source`, so it removes
transitions whose DESTINATION is not X (i.e., keeps only transitions TO X,
which is the opposite).

Similarly, `remove_transition(trigger, dest=Y)` checks `t.source not in dest`
instead of `t.dest not in dest`.

**Why default strategy is insufficient**: Most baseline tests don't test
`remove_transition` with specific source/dest filters. The default usage
pattern is to add transitions and trigger them, not to remove specific
transitions by filter.

**Trigger probability with default strategy**: ~5% (only if the test happens
to use remove_transition with a source or dest filter).

**Trigger probability with targeted strategy**: ~100% (any use of
`remove_transition` with a non-wildcard source or dest filter on an
asymmetric transition graph).

**Minimum triggering input**: A Machine with 3 states and transitions A->B,
B->C. Call `remove_transition('go', source='A')`. Verify A->B is removed
and B->C is preserved.

**Example**:
```python
machine.add_transition('go', 'A', 'B')
machine.add_transition('go', 'B', 'C')
machine.remove_transition('go', source='A')
remaining = machine.get_transitions(trigger='go')
# BUG: A->B is kept (dest='B' not in ['A']), B->C is removed
# (dest='C' not in ['A'])
```

---

## Bug 4: dispatch returns any() instead of all()

**Trigger condition**: Register 2+ models on a Machine. Put them in different
states such that some can trigger an event and some cannot. Call
`machine.dispatch(trigger)`. With `ignore_invalid_triggers=True`, models that
can't trigger return False. The bug returns `any(results)` instead of
`all(results)`, so dispatch returns True if ANY model succeeds.

**Why default strategy is insufficient**: Most baseline tests use single-model
machines. Multi-model dispatch is an advanced feature that requires specific
setup with models in different states.

**Trigger probability with default strategy**: ~5% (only if the test uses
multi-model machines AND checks dispatch return value AND has models in
different states).

**Trigger probability with targeted strategy**: ~100% (any multi-model
dispatch where not all models can trigger).

**Minimum triggering input**: 2 models on a Machine with 3 states, one model
advanced past the others, `ignore_invalid_triggers=True`, then dispatch.

**Example**:
```python
m1, m2 = Model(), Model()
machine = Machine(model=[m1, m2], states=['A', 'B', 'C'], initial='A',
                  ignore_invalid_triggers=True)
machine.add_transition('go', 'A', 'B')
machine.add_transition('go', 'B', 'C')
m1.go(); m1.go()  # m1 in C
result = machine.dispatch('go')  # m1: False, m2: True
# BUG: any([False, True]) = True, should be all([False, True]) = False
```
