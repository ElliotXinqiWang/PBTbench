# diskcache.Cache API Documentation

## Overview

diskcache provides disk-backed cache implementations using SQLite.
The Cache class is a key-value store that supports:
- Expiration (TTL)
- Tags for grouping and batch eviction  
- Multiple eviction policies (least-recently-stored, least-recently-used, least-frequently-used, none)
- Disk-based persistence
- Thread-safe and multi-process safe operations

Key concepts:
- **Tags**: Each cached item can have an optional string tag. Tags enable batch operations like evict(tag) to remove all items with a given tag.
- **Expiry**: Items can have a time-to-live (expire parameter in seconds). Expired items are automatically removed.
- **Eviction**: When the cache exceeds its size limit, items are removed according to the eviction policy.

## TTL Semantics and Consistency

When `cache.set(key, value, expire=N)` is called at time T, the item's internal
`expire_time` is set to `T + N`. An item is considered **expired** when the
current time is greater than or equal to the item's `expire_time`.

The cache operations that consult expiry must be **mutually consistent**:
- `get(key)`: returns default (miss) if `expire_time <= now` (item is expired at or before now)
- `expire(now=T)`: removes all items where `expire_time <= T`
- `incr(key, ..., default=D)`: if item is expired (`expire_time <= now`), treat as missing and use `default`

All three operations must agree: if an item is expired at time T
(i.e., `expire_time <= T`), then all operations at time T must treat it as absent.
In particular, `expire(now=T)` must remove items at the **exact** boundary
(`expire_time == T`), not just items that expired strictly before T.
### Cache.set()
Set `key` and `value` item in cache.

        When `read` is `True`, `value` should be a file-like object opened
        for reading in binary mode.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param key: key for item
        :param value: value for item
        :param float expire: seconds until item expires
            (default None, no expiry)
        :param bool read: read value as bytes from file (default False)
        :param str tag: text to associate with key (default None)
        :param bool retry: retry if database timeout occurs (default False)
        :return: True if item was set
        :raises Timeout: if database timeout occurs

        

### Cache.get()
Retrieve value from cache. If `key` is missing, return `default`.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param key: key for item
        :param default: value to return if key is missing (default None)
        :param bool read: if True, return file handle to value
            (default False)
        :param bool expire_time: if True, return expire_time in tuple
            (default False)
        :param bool tag: if True, return tag in tuple (default False)
        :param bool retry: retry if database timeout occurs (default False)
        :return: value for item or default if key not found
        :raises Timeout: if database timeout occurs

        

### Cache.pop()
Remove corresponding item for `key` from cache and return value.

        If `key` is missing, return `default`.

        Operation is atomic. Concurrent operations will be serialized.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param key: key for item
        :param default: value to return if key is missing (default None)
        :param bool expire_time: if True, return expire_time in tuple
            (default False)
        :param bool tag: if True, return tag in tuple (default False)
        :param bool retry: retry if database timeout occurs (default False)
        :return: value for item or default if key not found
        :raises Timeout: if database timeout occurs

        

### Cache.delete()
Delete corresponding item for `key` from cache.

        Missing keys are ignored.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param key: key matching item
        :param bool retry: retry if database timeout occurs (default False)
        :return: True if item was deleted
        :raises Timeout: if database timeout occurs

        

### Cache.__setitem__()
Set corresponding `value` for `key` in cache.

        :param key: key for item
        :param value: value for item
        :return: corresponding value
        :raises KeyError: if key is not found

        

### Cache.__getitem__()
Return corresponding value for `key` from cache.

        :param key: key matching item
        :return: corresponding value
        :raises KeyError: if key is not found

        

### Cache.__contains__()
Return `True` if `key` matching item is found in cache.

        :param key: key matching item
        :return: True if key matching item

        

### Cache.touch()
Touch `key` in cache and update `expire` time.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param key: key for item
        :param float expire: seconds until item expires
            (default None, no expiry)
        :param bool retry: retry if database timeout occurs (default False)
        :return: True if key was touched
        :raises Timeout: if database timeout occurs

        

### Cache.evict()
Remove items with matching `tag` from cache.

        Removing items is an iterative process. In each iteration, a subset of
        items is removed. Concurrent writes may occur between iterations.

        If a :exc:`Timeout` occurs, the first element of the exception's
        `args` attribute will be the number of items removed before the
        exception occurred.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param str tag: tag identifying items
        :param bool retry: retry if database timeout occurs (default False)
        :return: count of rows removed
        :raises Timeout: if database timeout occurs

        

### Cache.expire()
Remove expired items from cache.

        Removing items is an iterative process. In each iteration, a subset of
        items is removed. Concurrent writes may occur between iterations.

        If a :exc:`Timeout` occurs, the first element of the exception's
        `args` attribute will be the number of items removed before the
        exception occurred.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param float now: current time (default None, ``time.time()`` used)
        :param bool retry: retry if database timeout occurs (default False)
        :return: count of items removed
        :raises Timeout: if database timeout occurs

        

### Cache.clear()
Remove all items from cache.

        Removing items is an iterative process. In each iteration, a subset of
        items is removed. Concurrent writes may occur between iterations.

        If a :exc:`Timeout` occurs, the first element of the exception's
        `args` attribute will be the number of items removed before the
        exception occurred.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param bool retry: retry if database timeout occurs (default False)
        :return: count of rows removed
        :raises Timeout: if database timeout occurs

        

### Cache.add()
Add `key` and `value` item to cache.

        Similar to `set`, but only add to cache if key not present.

        Operation is atomic. Only one concurrent add operation for a given key
        will succeed.

        When `read` is `True`, `value` should be a file-like object opened
        for reading in binary mode.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param key: key for item
        :param value: value for item
        :param float expire: seconds until the key expires
            (default None, no expiry)
        :param bool read: read value as bytes from file (default False)
        :param str tag: text to associate with key (default None)
        :param bool retry: retry if database timeout occurs (default False)
        :return: True if item was added
        :raises Timeout: if database timeout occurs

        

### Cache.incr()
Increment value by delta for item with key.

        If key is missing and default is None then raise KeyError. Else if key
        is missing and default is not None then use default for value.

        Operation is atomic. All concurrent increment operations will be
        counted individually.

        Assumes value may be stored in a SQLite column. Most builds that target
        machines with 64-bit pointer widths will support 64-bit signed
        integers.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param key: key for item
        :param int delta: amount to increment (default 1)
        :param int default: value if key is missing (default 0)
        :param bool retry: retry if database timeout occurs (default False)
        :return: new value for item
        :raises KeyError: if key is not found and default is None
        :raises Timeout: if database timeout occurs

        

### Cache.decr()
Decrement value by delta for item with key.

        If key is missing and default is None then raise KeyError. Else if key
        is missing and default is not None then use default for value.

        Operation is atomic. All concurrent decrement operations will be
        counted individually.

        Unlike Memcached, negative values are supported. Value may be
        decremented below zero.

        Assumes value may be stored in a SQLite column. Most builds that target
        machines with 64-bit pointer widths will support 64-bit signed
        integers.

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).

        :param key: key for item
        :param int delta: amount to decrement (default 1)
        :param int default: value if key is missing (default 0)
        :param bool retry: retry if database timeout occurs (default False)
        :return: new value for item
        :raises KeyError: if key is not found and default is None
        :raises Timeout: if database timeout occurs

        

---

# diskcache.FanoutCache API Documentation

FanoutCache shards keys across multiple Cache instances for improved
concurrent performance. It has the same API as Cache.
The shard is selected by hash(key) % shard_count.
All Cache methods (set, get, pop, evict, etc.) are available on FanoutCache.
---

# diskcache.Deque API Documentation

Deque is a persistent, disk-backed double-ended queue.
It supports append, appendleft, pop, popleft, rotate, extend, extendleft,
and peek operations. Deques can be bounded with a maxlen parameter.
### Deque.append()
Add `value` to back of deque.

        >>> deque = Deque()
        >>> deque.append('a')
        >>> deque.append('b')
        >>> deque.append('c')
        >>> list(deque)
        ['a', 'b', 'c']

        :param value: value to add to back of deque

        

### Deque.appendleft()
Add `value` to front of deque.

        >>> deque = Deque()
        >>> deque.appendleft('a')
        >>> deque.appendleft('b')
        >>> deque.appendleft('c')
        >>> list(deque)
        ['c', 'b', 'a']

        :param value: value to add to front of deque

        

### Deque.pop()
Remove and return value at back of deque.

        If deque is empty then raise IndexError.

        >>> deque = Deque()
        >>> deque += 'ab'
        >>> deque.pop()
        'b'
        >>> deque.pop()
        'a'
        >>> deque.pop()
        Traceback (most recent call last):
            ...
        IndexError: pop from an empty deque

        :return: value at back of deque
        :raises IndexError: if deque is empty

        

### Deque.popleft()
Remove and return value at front of deque.

        >>> deque = Deque()
        >>> deque += 'ab'
        >>> deque.popleft()
        'a'
        >>> deque.popleft()
        'b'
        >>> deque.popleft()
        Traceback (most recent call last):
            ...
        IndexError: pop from an empty deque

        :return: value at front of deque
        :raises IndexError: if deque is empty

        

### Deque.rotate()
Rotate deque right by `steps`.

        If steps is negative then rotate left.

        >>> deque = Deque()
        >>> deque += range(5)
        >>> deque.rotate(2)
        >>> list(deque)
        [3, 4, 0, 1, 2]
        >>> deque.rotate(-1)
        >>> list(deque)
        [4, 0, 1, 2, 3]

        :param int steps: number of steps to rotate (default 1)

        

### Deque.extend()
Extend back side of deque with values from `iterable`.

        :param iterable: iterable of values

        

### Deque.extendleft()
Extend front side of deque with value from `iterable`.

        >>> deque = Deque()
        >>> deque.extendleft('abc')
        >>> list(deque)
        ['c', 'b', 'a']

        :param iterable: iterable of values

        

### Deque.peek()
Peek at value at back of deque.

        Faster than indexing deque at -1.

        If deque is empty then raise IndexError.

        >>> deque = Deque()
        >>> deque.peek()
        Traceback (most recent call last):
            ...
        IndexError: peek from an empty deque
        >>> deque += 'abc'
        >>> deque.peek()
        'c'

        :return: value at back of deque
        :raises IndexError: if deque is empty

        

### Deque.peekleft()
Peek at value at front of deque.

        Faster than indexing deque at 0.

        If deque is empty then raise IndexError.

        >>> deque = Deque()
        >>> deque.peekleft()
        Traceback (most recent call last):
            ...
        IndexError: peek from an empty deque
        >>> deque += 'abc'
        >>> deque.peekleft()
        'a'

        :return: value at front of deque
        :raises IndexError: if deque is empty

        

