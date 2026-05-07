# cachetools — TLRUCache and Typed Keys

## TLRUCache (Time-aware Least Recently Used)

```python
from cachetools import TLRUCache

def ttu(key, value, time):
    """Return the absolute expiry time for this item."""
    return time + value  # example: value is the TTL

cache = TLRUCache(maxsize=100, ttu=ttu, timer=time.monotonic)
```

### Overview

TLRUCache extends the time-aware cache concept with **per-item** time-to-use
(TTU) values. Unlike TTLCache which uses a global TTL for all items, TLRUCache
allows each item to have a different expiry time computed by the `ttu` function.

### TTU Function

The `ttu(key, value, time)` function is called during `__setitem__` with:
- `key`: the cache key being set
- `value`: the value being stored
- `time`: the current time from the timer

It must return the absolute time at which the item expires. If the returned
expiry time is not in the future (i.e., `not (time < expires)`), the item
is not stored.

### Custom Timer

Like TTLCache, TLRUCache accepts a `timer` parameter:

```python
tick = [0]
cache = TLRUCache(maxsize=10, ttu=ttu, timer=lambda: tick[0])
```

This enables deterministic testing with integer time steps.

### Expiry Semantics

An item is considered expired when `timer() >= item.expires` (equivalently,
when `not (timer() < item.expires)`). At exactly `timer() == item.expires`,
the item is expired.

**Mapping Protocol Invariant**: `k in cache` must be consistent with
`cache[k]`. If `k in cache` returns True, then `cache[k]` must not
raise KeyError. If `k in cache` returns False, then `cache[k]` must
raise KeyError (or return via `__missing__`).

### Key Updates

When a key is updated (set again with a new value), the TTU function is
called again with the new value and current time. The old expiry is
**replaced** by the new one. The old entry in the internal expiry tracking
is **marked as removed** so it doesn't interfere with future expiry
processing.

```python
tick[0] = 0
cache['key'] = 5   # expires at t=5
tick[0] = 1
cache['key'] = 20  # now expires at t=21 (1+20)
tick[0] = 6
assert 'key' in cache  # True: new expiry is t=21, not t=5
```

### expire() Method

```python
expired = cache.expire(time=None)
```

Removes all expired items and returns a list of `(key, value)` pairs that
were removed. Items are processed in order of their expiry time (earliest
first). Items that have been marked as removed (due to key updates or
deletions) are skipped during processing.

### Internal Heap

TLRUCache uses a min-heap internally to efficiently find expired items.
The heap is ordered by expiry time (items with the **earliest** expiry
at the top). When expire() is called, it pops items from the top of the
heap until it finds an item that hasn't expired yet.

### Iteration

Iterating over a TLRUCache yields only non-expired, non-removed keys:

```python
for key in cache:
    print(key)  # only active (non-expired) keys
```

## Typed Cache Keys

### typedkey

```python
from cachetools.keys import typedkey

k1 = typedkey(x=1)      # includes type(1) = int
k2 = typedkey(x=1.0)    # includes type(1.0) = float
assert k1 != k2         # different types = different keys
```

`typedkey` extends `hashkey` by appending the **types of the values** to
the cache key. This means that calls with the same value but different
types (e.g., `1` vs `1.0`, `"1"` vs `1`) produce different cache keys.

**How type annotations work for kwargs**:
The sorted kwargs are iterated and `type(value)` is appended for each
keyword argument. This ensures that `f(x=1)` and `f(x=1.0)` are
treated as different cache entries.

### Usage with Decorators

```python
from cachetools.func import lfu_cache

@lfu_cache(maxsize=128, typed=True)
def compute(x=0):
    return x ** 2

compute(x=2)     # cached
compute(x=2.0)   # separate cache entry (typed=True)
```

### hashkey vs typedkey

| Feature | hashkey | typedkey |
|---------|---------|----------|
| `f(1)` vs `f(1.0)` | Same key | Different keys |
| `f(x=1)` vs `f(x=1.0)` | Same key | Different keys |
| `f(a=1, b=2)` vs `f(b=2, a=1)` | Same key | Same key |
| Performance | Faster | Slightly slower |

Both functions guarantee that keyword argument ORDER does not affect the
cache key (kwargs are sorted before inclusion in the key tuple).
