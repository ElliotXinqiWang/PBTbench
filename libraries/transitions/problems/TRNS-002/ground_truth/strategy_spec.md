# TRNS-002 Strategy Spec

## Bug 1: After-callback execution ordering (L4)

**Trigger condition**: Set both machine-level `after_state_change` and transition-level `after` callbacks on the same transition. Execute the transition and record execution order.

**Why default strategy is insufficient**: Default testing only uses one type of callback (either machine-level or transition-level), never both. The ordering only matters when both are present.

**Trigger probability with default strategy**: <5% — a random PBT would need to simultaneously set up both callback types and check their relative ordering.

**Minimal trigger input**: 2 states (A, B), one transition A->B with `after=cb1`, machine created with `after_state_change=cb2`. Trigger the transition and verify `cb1` executes before `cb2`.

---

## Bug 2: Unless condition semantics inversion (L3)

**Trigger condition**: Add a transition with `unless='condition_name'` where the condition callable returns `True`. The transition should be blocked.

**Why default strategy is insufficient**: Most baseline tests use `conditions=` parameter, not `unless=`. The `unless` parameter is a less commonly tested feature. Even when `unless` is used, if the condition returns `False` (the common case for "should this be blocked? No"), the bug is invisible.

**Trigger probability with default strategy**: <10% — requires specifically testing `unless` with a condition that returns `True`.

**Minimal trigger input**: 2 states, transition with `unless='is_blocked'`, model has `def is_blocked(self): return True`. After triggering, state should remain at source.

---

## Bug 3: loop_includes_initial flag inversion (L3)

**Trigger condition**: Create ordered transitions with `loop=True` and `loop_includes_initial=True` on 3+ states. Cycle through all states and observe the loop-back destination.

**Why default strategy is insufficient**: Most tests of ordered transitions use the default `loop_includes_initial=True` but don't verify the specific loop-back destination — they just verify transitions work. The bug only manifests when explicitly checking WHERE the loop goes back to.

**Trigger probability with default strategy**: <10% — requires explicitly checking the loop-back destination with both True and False values of `loop_includes_initial`.

**Minimal trigger input**: States [A, B, C], initial=A, `loop=True, loop_includes_initial=True`. After cycling A->B->C->?, with bug goes to B (should go to A).

---

## Bug 4: get_transitions source/dest filter swap (L2)

**Trigger condition**: Call `get_transitions(source=X)` or `get_transitions(dest=X)` on a machine with asymmetric transitions (A->B but not B->A). Verify returned transitions match the filter.

**Why default strategy is insufficient**: Most baseline tests call `get_transitions()` without source/dest filters, or use the wildcard default. The bug is invisible with wildcard filters.

**Trigger probability with default strategy**: <15% — requires using specific source or dest filter parameters with asymmetric transitions.

**Minimal trigger input**: States [A, B, C], transitions A->B and B->C. `get_transitions(source='A')` should return [A->B] but with bug returns [C->A] (matching dest='A' instead).
