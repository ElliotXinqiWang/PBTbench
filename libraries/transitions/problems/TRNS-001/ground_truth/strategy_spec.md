# Strategy Specification for TRNS-001

## Bug 1: BFS to DFS in _enter_nested (parallel initial entry order)

**Trigger condition**: Enter a state with 2+ parallel initial children, where
each child has its own nested initial substate. Track on_enter callback order.
With the bug (queue.pop() instead of queue.pop(0)), leaf-level enter callbacks
fire in reversed sibling order.

**Why default strategy is insufficient**: Most tests use simple flat states or
single-child nesting. Parallel states with nested initials (initial=['A', 'B']
where A and B each have initial substates) are rarely tested. The entry ORDER
is almost never checked.

**Trigger probability with default strategy**: <3% (requires parallel + nested + order check)

**Minimum trigger input**: 2 parallel children with nested initials, callback order tracking

## Bug 2: resolve_order sibling ordering

**Trigger condition**: Create parallel states with 2+ siblings. Track the order
in which exit callbacks fire when transitioning away. Without reversed(), siblings
exit in reversed declaration order (B before A instead of A before B).

**Why default strategy is insufficient**: Most tests don't verify callback ORDER,
only that callbacks fire. The reversed() call is an implementation detail of the
BFS ordering algorithm.

**Trigger probability with default strategy**: ~10% (if exit ordering is checked)

**Minimum trigger input**: 2 parallel siblings with exit callbacks

## Bug 3: Model state during on_enter

**Trigger condition**: Create a nested state machine with on_enter callbacks that
read model.state. Transition between states. The callback sees the source state
instead of the destination state because _update_model runs after enter callbacks.

**Why default strategy is insufficient**: Most tests check model.state AFTER the
transition completes (where it's correct). The bug only manifests during the
on_enter callback execution.

**Trigger probability with default strategy**: ~15% (if state-reading callbacks used)

**Minimum trigger input**: 2 nested states, 1 on_enter callback reading model.state

## Bug 4: before callback ordering

**Trigger condition**: Create a Machine with both before_state_change (machine-level)
and before (transition-level) callbacks. Record their execution order. With the bug,
transition-level before runs first instead of machine-level before_state_change.

**Why default strategy is insufficient**: Most tests use either machine-level OR
transition-level callbacks, not both simultaneously. The order difference is only
visible when both are used and their execution order is tracked.

**Trigger probability with default strategy**: ~30% (if both callback types tested)

**Minimum trigger input**: 1 transition with both callback types
