# diskcache 5.6.3 — API Documentation (DCAC-003)

## Overview

diskcache provides disk-backed cache implementations using SQLite for persistence.
The `Cache` class is a key-value store supporting expiration (TTL), tags, eviction policies,
and thread-safe operations.

## TTL Semantics

When `cache.set(key, value, expire=N)` is called at time T, the item's internal
`expire_time` is set to `T + N`.

An item is **expired** when `expire_time <= now` (current time). An item is **alive**
when `expire_time > now` (or expire_time is None meaning no expiry).

All cache operations must be mutually consistent regarding expiry:
- `get(key)`: returns default (miss) if `expire_time <= now`
- `touch(key)`: returns True and updates expiry ONLY if item is alive (`expire_time > now`);
  returns False if item is expired
- `add(key, value)`: adds if key is absent OR if existing item is expired;
  returns True if added/replaced, False if key exists and is alive

## Queue Semantics (push/pull)

The `Cache` can be used as a FIFO queue using `push` and `pull`.

When `prefix=None`, integer keys are used starting at 500 trillion.

- `push(value, side='back')`: adds value to back (highest key), returns key
- `push(value, side='front')`: adds value to front (lowest key), returns key
- `pull(side='front')`: removes and returns (key, value) from front (lowest key = oldest)
- `pull(side='back')`: removes and returns (key, value) from back (highest key = newest)

**FIFO semantics**: `push(v, 'back')` then `pull('front')` returns items in push order.
**LIFO semantics**: `push(v, 'back')` then `pull('back')` returns items in reverse order.

### Cache.push()

```python
cache.push(value, prefix=None, side='back', expire=None, read=False, tag=None, retry=False)
```

Push value onto `side` of queue identified by `prefix` in cache.

- `side='back'` (default): pushes to back of queue (highest key)
- `side='front'`: pushes to front (lowest key)
- Returns key for the item in cache

```python
cache = Cache()
print(cache.push('first'))   # 500000000000000
print(cache.push('second'))  # 500000000000001
print(cache.push('third', side='front'))  # 499999999999999
```

### Cache.pull()

```python
cache.pull(prefix=None, default=(None, None), side='front', expire_time=False, tag=False, retry=False)
```

Pull key and value item pair from `side` of queue in cache.

- `side='front'` (default): pulls from front of queue (lowest key = oldest pushed item)
- `side='back'`: pulls from back of queue (highest key = newest pushed item)
- Returns `(key, value)` or `default` if queue is empty

The side parameter determines which end of the queue items are removed from:
- `front` uses `ORDER BY key ASC LIMIT 1` — returns smallest key (first pushed to back)
- `back` uses `ORDER BY key DESC LIMIT 1` — returns largest key (last pushed to back)

```python
cache = Cache()
for letter in 'abc':
    cache.push(letter)         # pushes to back: a=...000, b=...001, c=...002
key, value = cache.pull()      # side='front' returns ('a' at ...000)
_, value = cache.pull(side='back')  # returns ('c' at ...002)
```

### Cache.peek()

```python
cache.peek(prefix=None, default=(None, None), side='front', expire_time=False, tag=False, retry=False)
```

Same as `pull()` but does NOT remove the item from the cache.

### Cache.peekitem()

```python
cache.peekitem(last=True, expire_time=False, tag=False, retry=False)
```

Peek at key and value item pair in cache based on iteration order (rowid order).

- `last=True` (default): returns the LAST item in iteration order (most recently inserted rowid)
- `last=False`: returns the FIRST item in iteration order (oldest inserted rowid)
- Raises `KeyError` if cache is empty
- Expired items are deleted from cache during this operation

The iteration order is based on SQLite rowid:
- `last=True` uses `ORDER BY rowid DESC LIMIT 1`
- `last=False` uses `ORDER BY rowid ASC LIMIT 1`

```python
cache = Cache()
for num, letter in enumerate('abc'):
    cache[letter] = num
cache.peekitem()         # ('c', 2) — last inserted
cache.peekitem(last=False)  # ('a', 0) — first inserted
```

### Cache.touch()

```python
cache.touch(key, expire=None, retry=False)
```

Touch key in cache and update expire time.

- Returns `True` if the key was found **and is not expired** (expire_time > now)
- Returns `False` if the key is missing or expired

An item with `expire_time == now` is expired and `touch()` must return False.
(Consistent with `get()` which returns a miss for items at `expire_time <= now`.)

```python
cache = Cache()
cache.set('key', 'value', expire=10)
cache.touch('key', expire=20)  # True, extends expiry
cache.touch('missing', expire=5)  # False
```

### Cache.add()

```python
cache.add(key, value, expire=None, read=False, tag=None, retry=False)
```

Add key and value to cache. Similar to `set`, but only adds if key is not present
(or if existing entry is expired).

- Returns `True` if item was added (key was absent or expired)
- Returns `False` if key already exists and is NOT expired

An expired item (expire_time <= now) is treated as absent by `add()`:
it replaces the expired entry and returns True.

```python
cache = Cache()
cache.add('key', 'value')  # True
cache.add('key', 'other')  # False (key exists and is alive)
```

### Cache.set()

```python
cache.set(key, value, expire=None, read=False, tag=None, retry=False)
```

Set key and value in cache. Always succeeds. Returns True.

```python
cache.set('key', 'value', expire=10)  # sets with 10-second TTL
cache.set('key', 'new')               # overwrites unconditionally
```

### Cache.get()

```python
cache.get(key, default=None, read=False, expire_time=False, tag=False, retry=False)
```

Retrieve value from cache. Returns `default` if key is missing or expired.

An item is expired when `expire_time <= now`. Items at the exact expiry boundary
(`expire_time == now`) are treated as expired by `get()`.

### Cache.pop()

```python
cache.pop(key, default=None, expire_time=False, tag=False, retry=False)
```

Remove and return value for key. Returns `default` if key is missing.

### Cache.delete()

```python
cache.delete(key, retry=False)
```

Delete item for key. Missing keys are ignored. Returns True if deleted.

### Cache.__len__()

Returns count of items in cache **including expired items**.

### Cache.__contains__()

Returns True if key is found in cache and NOT expired.
