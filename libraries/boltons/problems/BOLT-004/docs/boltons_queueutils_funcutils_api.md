# boltons.queueutils and boltons.funcutils — API Reference

This document describes the public API for two boltons modules:
**queueutils** (priority queue implementations) and **funcutils**
(function introspection and wrapping utilities).

---

## Part 1: boltons.queueutils — Priority Queues

### Overview

The `queueutils` module provides two interchangeable priority queue
implementations sharing a common API via `BasePriorityQueue`:

- `HeapPriorityQueue` — backed by Python's `heapq` module
- `SortedPriorityQueue` — backed by a sorted list (via `bisect.insort`)

Both are re-exported as `PriorityQueue` (default alias: `SortedPriorityQueue`).

Priority values are numeric. **Higher numbers mean higher priority** (a task
with priority 10 is popped before a task with priority 1). Negative and
floating-point priorities are supported. The `priority_key` parameter controls
the effective priority (see Constructor).

### Import

```python
from boltons.queueutils import (
    PriorityQueue,          # Default alias (SortedPriorityQueue)
    HeapPriorityQueue,
    SortedPriorityQueue,
    BasePriorityQueue,
)
```

---

### Constructor

```python
HeapPriorityQueue(priority_key=None)
SortedPriorityQueue(priority_key=None)
PriorityQueue(priority_key=None)
```

**Arguments**:
- `priority_key` *(callable, optional)*: A function that transforms the
  *priority* value passed to `add()` into an internal numeric key. Defaults
  to `lambda p: -float(p or 0)`, which negates the priority so that the heap
  min-structure yields highest-priority items first.

```python
pq = HeapPriorityQueue()
pq = SortedPriorityQueue(priority_key=lambda p: -abs(p or 0))
```

---

### `add(task, priority=None)`

Add *task* to the queue with the given *priority* (default `0`).

- *task* can be any hashable Python object.
- If *task* is already in the queue, its priority is **updated** (the old
  entry is atomically removed and the new entry is inserted).
- Tasks with **higher numeric priority** are returned first by `pop()` and
  `peek()`.
- When two tasks have **identical priority**, they are returned in
  **FIFO (first-in, first-out) insertion order** — the task added earlier is
  returned first.

```python
pq = HeapPriorityQueue()
pq.add('task_a', priority=5)
pq.add('task_b', priority=5)   # same priority, added after task_a
pq.add('task_c', priority=3)

pq.pop()  # → 'task_a'  (priority 5, added first)
pq.pop()  # → 'task_b'  (priority 5, added second)
pq.pop()  # → 'task_c'  (priority 3, lowest)
```

**Re-prioritizing an existing task**:

```python
pq = HeapPriorityQueue()
pq.add('work', priority=1)
pq.add('work', priority=99)   # update priority
len(pq)  # → 1 (still one task)
pq.pop()  # → 'work'
```

---

### `pop(default=<sentinel>)`

Remove and return the highest-priority task.

- Returns the task object.
- If the queue is empty and *default* is not set, raises `IndexError`.
- If the queue is empty and *default* is provided, returns *default*.

```python
pq = HeapPriorityQueue()
pq.add('alpha', 10)
pq.add('beta', 20)

pq.pop()  # → 'beta'
pq.pop()  # → 'alpha'
pq.pop(default=None)  # → None (queue is now empty)
```

**Invariant**: After `pop()`, the task is no longer in the queue. `len(pq)`
decreases by 1 for each successful pop call.

```python
# Invariant: len(pq) before pop - 1 == len(pq) after pop
before = len(pq)
pq.pop()
after = len(pq)
assert after == before - 1
```

---

### `peek(default=<sentinel>)`

Return the highest-priority task **without removing it**.

- If the queue is empty and *default* is not set, raises `IndexError`.
- If the queue is empty and *default* is provided, returns *default*.
- Calling `peek()` does **not** change `len(pq)` or alter the pop order.

```python
pq = HeapPriorityQueue()
pq.add('high', 100)
pq.add('low', 1)

pq.peek()  # → 'high'
pq.peek()  # → 'high'  (unchanged)
len(pq)    # → 2
```

---

### `remove(task)`

Remove *task* from the queue. Raises `KeyError` if *task* is not present.
This uses **lazy deletion**: the internal heap entry is marked as removed,
and the actual heap slot is cleaned up the next time `pop()` or `peek()` is
called.

```python
pq = HeapPriorityQueue()
pq.add('a', 5)
pq.add('b', 3)
pq.remove('a')
pq.pop()   # → 'b' (only remaining task)
```

---

### `__len__()`

Return the number of **live** tasks currently in the queue (not counting
entries that have been removed or popped).

```python
pq = HeapPriorityQueue()
len(pq)         # → 0
pq.add('x', 1)
len(pq)         # → 1
pq.add('y', 2)
len(pq)         # → 2
pq.pop()
len(pq)         # → 1
```

The invariant `len(pq) == (number of tasks that can still be popped)` must
hold at all times.

---

### Priority Queue Invariants

The following invariants are guaranteed by the documented API and must hold
for all valid usage patterns, including interleaved add/pop/remove sequences:

1. **Priority ordering**: `pop()` always returns the highest-priority task.
2. **FIFO tie-breaking**: Among equal-priority tasks, `pop()` returns them in
   the order they were added (first-in, first-out).
3. **len() accuracy**: `len(pq)` always equals the number of tasks that
   `pop()` would successfully return before raising `IndexError`.
4. **Peek consistency**: `peek()` returns the same value as the next `pop()`
   would return, without modifying the queue state.
5. **Idempotent re-add**: `add(task, p2)` when `task` is already in the queue
   is equivalent to `remove(task); add(task, p2)` — exactly one entry for
   that task remains.

---

### Multi-step Sequence Example

```python
pq = HeapPriorityQueue()

# Phase 1: fill
for i, name in enumerate(['slow', 'medium', 'fast']):
    pq.add(name, priority=i)   # slow=0, medium=1, fast=2

# Phase 2: partial drain
assert pq.pop() == 'fast'    # highest priority
assert len(pq) == 2          # two items remain

# Phase 3: re-fill
pq.add('urgent', priority=10)
pq.add('medium_2', priority=1)  # same priority as 'medium'

# Phase 4: drain remainder in order
order = [pq.pop() for _ in range(len(pq))]
# Expected: ['urgent', 'medium', 'medium_2', 'slow']
# ('medium' was added before 'medium_2', FIFO among priority-1 tasks)
```

---

## Part 2: boltons.funcutils — Function Utilities

### Overview

`funcutils` extends Python's built-in `functools` with tools for function
introspection, signature manipulation, and decorator creation. The two main
components are:

- **`FunctionBuilder`** — build or reconstruct functions from their components
- **`wraps` / `update_wrapper`** — decorator utilities that preserve the full
  signature of the wrapped function

---

### Import

```python
from boltons.funcutils import (
    FunctionBuilder,
    wraps,
    update_wrapper,
    NO_DEFAULT,
    MissingArgument,
    ExistingArgument,
)
```

---

## FunctionBuilder

`FunctionBuilder` provides a programmable interface for creating and modifying
Python functions. It stores all components of a function's definition
(name, args, defaults, annotations, body, etc.) as mutable attributes, and
compiles a new function object on demand via `get_func()`.

### Constructor

```python
FunctionBuilder(name, **kwargs)
```

Key keyword arguments:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | str | (required) | Function name |
| `doc` | str | `''` | Docstring |
| `args` | list | `[]` | Positional argument names |
| `varargs` | str or None | `None` | Name for `*args` catch-all |
| `varkw` | str or None | `None` | Name for `**kwargs` catch-all |
| `defaults` | tuple or None | `None` | Default values for the **last N** positional args |
| `kwonlyargs` | list | `[]` | Keyword-only argument names |
| `kwonlydefaults` | dict | `{}` | Default values for keyword-only args |
| `annotations` | dict | `{}` | Type annotation mapping |
| `body` | str | `'pass'` | Python source code for the function body |
| `module` | str or None | `None` | `__module__` attribute |

**Relationship between `args` and `defaults`**:

`defaults` is a tuple of default values for the **last `len(defaults)`
positional arguments** in `args`. For example:

```python
# Function: f(a, b=10, c=20)
fb = FunctionBuilder('f', args=['a', 'b', 'c'], defaults=(10, 20))
# args[-2] == 'b' → default 10
# args[-1] == 'c' → default 20
```

---

### `FunctionBuilder.from_func(func)` (classmethod)

Create a `FunctionBuilder` from an existing function. All signature
components (args, defaults, kwonlyargs, kwonlydefaults, annotations, etc.)
are extracted and stored as attributes.

```python
def greet(name, greeting='Hello', *, punctuation='!'):
    return f"{greeting}, {name}{punctuation}"

fb = FunctionBuilder.from_func(greet)
# fb.args == ['name', 'greeting']
# fb.defaults == ('Hello',)
# fb.kwonlyargs == ['punctuation']
# fb.kwonlydefaults == {'punctuation': '!'}
```

---

### `get_func(execdict=None, add_source=True, with_dict=True)`

Compile and return a new function object from the current builder state.

- `execdict` *(dict)*: Namespace available inside the compiled function body.
  Use this to pass in helper functions referenced in `body`.
- Returns a callable with the signature described by the builder's attributes.

```python
fb = FunctionBuilder('multiply', args=['x', 'y'], body='return x * y')
mul = fb.get_func()
mul(3, 4)   # → 12
```

**Default argument preservation**: The compiled function respects `defaults`
and `kwonlydefaults` as set on the builder:

```python
fb = FunctionBuilder('f', args=['x', 'y'], defaults=(99,), body='return x + y')
f = fb.get_func()
f(1)       # → 100  (y defaults to 99)
f(1, 2)   # → 3
```

---

### `get_defaults_dict()`

Return a `dict` mapping each argument name (positional or keyword-only) to
its default value. Arguments without defaults are omitted.

**Positional args**: The last `len(defaults)` args in `self.args` map to the
corresponding elements of `self.defaults` (in order — the Nth-from-last arg
maps to the Nth-from-last default).

**Keyword-only args**: Included from `self.kwonlydefaults`.

```python
def f(a, b=10, c=20):
    pass

fb = FunctionBuilder.from_func(f)
fb.get_defaults_dict()
# → {'b': 10, 'c': 20}
# NOT {'b': 20, 'c': 10} — order must match original definition
```

```python
def g(x, *, y=5, z=6):
    pass

fb = FunctionBuilder.from_func(g)
fb.get_defaults_dict()
# → {'y': 5, 'z': 6}
```

---

### `get_arg_names(only_required=False)`

Return a tuple of all argument names (positional + keyword-only).

- If `only_required=True`, omit arguments that have defaults.

```python
def f(a, b=1, *, c=2, d):
    pass

fb = FunctionBuilder.from_func(f)
fb.get_arg_names()                    # → ('a', 'b', 'c', 'd')
fb.get_arg_names(only_required=True)  # → ('a', 'd')
```

---

### `add_arg(arg_name, default=NO_DEFAULT, kwonly=False)`

Add a new argument to the function builder.

- If `kwonly=False` (default): adds a positional argument. If `default` is
  provided, it is appended to `self.defaults`.
- If `kwonly=True`: adds a keyword-only argument. If `default` is provided,
  it is stored in `self.kwonlydefaults[arg_name]`.
- Raises `ExistingArgument` if `arg_name` is already present in `args` or
  `kwonlyargs`.

```python
fb = FunctionBuilder('make_greeting', body='return name + suffix')
fb.add_arg('name')
fb.add_arg('suffix', default='!', kwonly=True)
make_greeting = fb.get_func()
make_greeting('Alice')          # → 'Alice!'
make_greeting('Bob', suffix='.') # → 'Bob.'
```

**Invariant for keyword-only args with defaults**: If `add_arg('x',
default=val, kwonly=True)` is called, then calling the resulting function
without passing `x` must produce a result as if `x == val`. Specifically,
`get_func()` must see `kwonlydefaults['x'] == val` (not `NO_DEFAULT` or any
other sentinel).

---

### `remove_arg(arg_name)`

Remove an argument from the function builder. The `defaults` tuple is
recomputed so that the remaining arguments retain their correct defaults.

- Raises `MissingArgument` if `arg_name` is not found.

```python
def f(a, b=10, c=20):
    return a + b + c

fb = FunctionBuilder.from_func(f)
fb.remove_arg('a')  # remove non-default arg
fb.get_defaults_dict()  # → {'b': 10, 'c': 20}  (unchanged)

fb2 = FunctionBuilder.from_func(f)
fb2.remove_arg('b')  # remove a default arg
fb2.get_defaults_dict()  # → {'c': 20}  (b is gone, c keeps its default 20)
```

**Key invariant**: After `remove_arg(x)`, each remaining argument retains the
same default value it had in the original function. The removal of `x` must
not alter the defaults of any other argument.

---

### FunctionBuilder: Complete Example

```python
def original(x, y=5, z=10):
    return x + y + z

fb = FunctionBuilder.from_func(original)
print(fb.get_defaults_dict())  # → {'y': 5, 'z': 10}

# Remove y
fb.remove_arg('y')
print(fb.args)                 # → ['x', 'z']
print(fb.get_defaults_dict())  # → {'z': 10}   (y gone, z still 10)

# Build a new function
fb.body = 'return x + z'
f = fb.get_func()
f(1)       # → 11  (z defaults to 10)
f(1, z=3)  # → 4
```

---

## wraps / update_wrapper

### `wraps(func, injected=None, expected=None, **kw)`

A decorator factory (analogous to `functools.wraps`) that makes a wrapper
function look like the wrapped function. Returns a decorator that calls
`update_wrapper(wrapper, func, ...)`.

```python
from boltons.funcutils import wraps

def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Done.")
        return result
    return wrapper

@log_calls
def compute(x, y=0):
    '''Computes x + y.'''
    return x + y

compute.__name__    # → 'compute'
compute.__doc__     # → 'Computes x + y.'
```

---

### `update_wrapper(wrapper, func, injected=None, expected=None, **kw)`

Copy the metadata and signature from *func* to *wrapper*. Returns a **new
function** (does not modify *wrapper* in place).

**Attributes transferred**:
- `__name__`, `__doc__`, `__module__`, `__annotations__`, `__dict__`
- The full call signature (positional args, defaults, keyword-only args)
- `__wrapped__` — set to *func* (the original function)

**Arguments**:
- `injected` *(list of str)*: Argument names in *func*'s signature that the
  wrapper provides internally and should **not** appear in the outer signature.
- `expected` *(list of str or (name, default) pairs)*: New arguments
  introduced by the wrapper that do not exist in *func*'s signature.
- `hide_wrapped` *(bool)*: If `True`, removes the `__wrapped__` attribute
  from the result.
- `update_dict` *(bool)*: If `True` (default), copies `func.__dict__` items
  to the wrapper.

---

### The `__wrapped__` Attribute

The boltons `wraps` / `update_wrapper` always sets `__wrapped__` on the
returned function, pointing to the **original unwrapped function** (*func*):

```python
from boltons.funcutils import wraps
import inspect

def original(x):
    return x * 2

@wraps(original)
def my_wrapper(*args, **kwargs):
    return original(*args, **kwargs)

my_wrapper.__wrapped__ is original  # → True
inspect.unwrap(my_wrapper) is original  # → True
```

**Invariant**: `wraps(func)(wrapper).__wrapped__ is func` must hold, where
`func` is the first argument to `wraps()`. This is what `inspect.unwrap()`
relies on to peel back decorator chains.

**Chain invariant**: For a chain of decorators, each layer's `__wrapped__`
points to the immediately wrapped function. `inspect.unwrap()` follows these
links until it reaches a function without `__wrapped__`:

```python
@wraps(original)
def layer2(*a, **kw): return original(*a, **kw)

@wraps(layer2)
def layer3(*a, **kw): return layer2(*a, **kw)

# layer3.__wrapped__ is layer2
# layer2.__wrapped__ is original
# inspect.unwrap(layer3) is original  → follows the full chain
```

**`hide_wrapped=True`**: Passing this keyword to `update_wrapper` omits the
`__wrapped__` attribute from the result entirely:

```python
wrapped = update_wrapper(my_wrapper, original, hide_wrapped=True)
hasattr(wrapped, '__wrapped__')  # → False
```

---

### Signature Preservation

Unlike `functools.wraps`, the boltons version **copies the full call
signature** (not just metadata), so `inspect.signature()` on the wrapper
returns the same signature as the original:

```python
def original(x: int, y: int = 10) -> int:
    return x + y

@wraps(original)
def my_wrapper(*args, **kwargs):
    return original(*args, **kwargs)

import inspect
str(inspect.signature(my_wrapper))  # → '(x: int, y: int = 10) -> int'
```

---

### Common Usage Patterns

**Pattern 1: Transparent logging decorator**

```python
def logged(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper
```

**Pattern 2: Inject a default argument**

```python
def with_default_timeout(func):
    @wraps(func, injected='timeout')
    def wrapper(timeout=30, **kwargs):
        return func(timeout=timeout, **kwargs)
    return wrapper
```

**Pattern 3: Add a new parameter to the wrapper**

```python
def with_retry(func):
    @wraps(func, expected=[('retries', 3)])
    def wrapper(*args, retries=3, **kwargs):
        for _ in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception:
                pass
    return wrapper
```

**Pattern 4: Double-wrapping and unwrap chain**

```python
@logged
@with_retry
def fetch(url: str) -> str:
    ...

# The chain: fetch → with_retry wrapper → logged wrapper
# inspect.unwrap(fetch) follows __wrapped__ all the way back to the
# original `fetch` function.
```

---

### Summary of Key Invariants

| Invariant | Property |
|---|---|
| Priority ordering | `pq.pop()` always returns the highest-priority task |
| FIFO tie-breaking | Equal-priority tasks are popped in insertion order |
| len() accuracy | `len(pq)` == number of remaining poppable tasks |
| FunctionBuilder defaults | `get_defaults_dict()` maps each arg to its correct default |
| remove_arg safety | Removing an arg does not alter defaults of remaining args |
| `__wrapped__` identity | `wraps(func)(wrapper).__wrapped__ is func` |
| unwrap chain | `inspect.unwrap(wraps(func)(wrapper)) is func` |
