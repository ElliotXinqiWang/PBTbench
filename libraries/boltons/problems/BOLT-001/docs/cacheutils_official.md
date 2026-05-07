# cacheutils - Caches and Caching
# Source: https://boltons.readthedocs.io/en/latest/cacheutils.html
# boltons version: 25.0.0

## Overview

The `cacheutils` module provides consistent implementations of fundamental cache types. Currently available options include:

- **LRI** (Least-Recently Inserted): A simpler, lower-overhead cache using FIFO eviction
- **LRU** (Least-Recently Used): A more advanced cache that replaces the least-recently accessed item when capacity is reached

Both cache implementations are `dict` subtypes designed for interchangeability to facilitate performance testing. They track standard statistics:

- `hit_count`: Number of times a cached key was accessed
- `miss_count`: Number of times a key was absent or fetched
- `soft_miss_count`: Misses where a default was provided (subset of `miss_count`)

---

## Least-Recently Inserted (LRI)

### Class Definition

```python
class boltons.cacheutils.LRI(max_size=128, values=None, on_miss=None)
```

The LRI implements a basic "first-in, first-out" approach. It functions like a "SizeLimitedDefaultDict."

The `on_miss` parameter accepts a callable taking the missing key as an argument (unlike `collections.defaultdict`'s `default_factory`).

### Example Usage

```python
>>> cap_cache = LRI(max_size=2)
>>> cap_cache['a'], cap_cache['b'] = 'A', 'B'
>>> from pprint import pprint as pp
>>> pp(dict(cap_cache))
{'a': 'A', 'b': 'B'}
>>> [cap_cache['b'] for i in range(3)][0]
'B'
>>> cap_cache['c'] = 'C'
>>> print(cap_cache.get('a'))
None
>>> cap_cache.hit_count, cap_cache.miss_count, cap_cache.soft_miss_count
(3, 1, 1)
```

### LRI Methods

**clear()**
Remove all items from the cache.

**copy()**
Return a shallow copy of the cache.

**get(key, default=None)**
"Return the value for key if key is in the dictionary, else default."

**pop(k[, d])**
"Remove specified key and return the corresponding value. If the key is not found, return the default if given; otherwise, raise a KeyError."

**popitem()**
"Remove and return a (key, value) pair as a 2-tuple. Pairs are returned in LIFO (last-in, first-out) order. Raises KeyError if the dict is empty."

**setdefault(key, default=None)**
"Insert key with a value of default if key is not in the dictionary. Return the value for key if key is in the dictionary, else default."

**update([E, ] **F)**
"Update D from dict/iterable E and F. If E is present and has a .keys() method, then does: for k in E: D[k] = E[k] If E is present and lacks a .keys() method, then does: for k, v in E: D[k] = v In either case, this is followed by: for k in F: D[k] = F[k]"

---

## Least-Recently Used (LRU)

### Class Definition

```python
class boltons.cacheutils.LRU(max_size=128, values=None, on_miss=None)
```

The LRU is a `dict` subtype implementing the least-recently used caching strategy. When capacity is reached, new insertions replace the least-recently used item. This strategy is more effective than LRI for many applications, though it requires more operations for all APIs, especially reads. The LRU includes built-in thread safety.

### Parameters

- **max_size** (int): Maximum number of items to cache. Defaults to `128`.
- **values** (iterable): Initial values for the cache. Defaults to `None`.
- **on_miss** (callable): A callable accepting a single argument (the missing key) and returning the value to be cached.

### Example Usage

```python
>>> cap_cache = LRU(max_size=2)
>>> cap_cache['a'], cap_cache['b'] = 'A', 'B'
>>> from pprint import pprint as pp
>>> pp(dict(cap_cache))
{'a': 'A', 'b': 'B'}
>>> [cap_cache['b'] for i in range(3)][0]
'B'
>>> cap_cache['c'] = 'C'
>>> print(cap_cache.get('a'))
None
```

The LRU includes statistics collection with `hit_count`, `miss_count`, and `soft_miss_count`:

```python
>>> cap_cache.hit_count, cap_cache.miss_count, cap_cache.soft_miss_count
(3, 1, 1)
```

Beyond size-limiting caching behavior and statistics, "LRU acts like its parent class, the built-in Python dict."

---

## Automatic Function Caching

### cached() Decorator

```python
boltons.cacheutils.cached(cache, scoped=True, typed=False, key=None)
```

"Cache any function with the cache object of your choosing. Note that the function wrapped should take only hashable arguments."

#### Parameters

- **cache** (Mapping): Any dict-like object suitable for use as a cache. Instances of LRU and LRI are good choices, though a plain dict can work in some cases. Can also be a callable returning a mapping.
- **scoped** (bool): Whether the function itself is part of the cache key. Default `True`; different functions won't read each other's entries but can evict results. `False` is useful for certain shared cache scenarios.
- **typed** (bool): Whether to factor argument types into cache checks. Default `False`; setting to `True` treats `3` and `3.0` as distinct cache keys.

#### Example

```python
>>> my_cache = LRU()
>>> @cached(my_cache)
... def cached_lower(x):
...     return x.lower()
...
>>> cached_lower("CaChInG's FuN AgAiN!")
"caching's fun again!"
>>> len(my_cache)
1
```

### cachedmethod() Decorator

```python
boltons.cacheutils.cachedmethod(cache, scoped=True, typed=False, key=None)
```

"Similar to cached(), cachedmethod is used to cache methods based on their arguments, using any dict-like cache object."

#### Parameters

- **cache** (str/Mapping/callable): Can be an attribute name on the instance, any Mapping/dict-like object, or a callable returning a Mapping.
- **scoped** (bool): Whether the method and bound object are part of cache keys. Default `True`; different methods won't share results. `False` is useful for certain shared cache scenarios.
- **typed** (bool): Whether to factor argument types into cache checks. Default `False`.
- **key** (callable): A callable with signature matching `make_cache_key()` returning hashable tuple for cache keys.

#### Example

```python
>>> class Lowerer(object):
...     def __init__(self):
...         self.cache = LRI()
...
...     @cachedmethod('cache')
...     def lower(self, text):
...         return text.lower()
...
>>> lowerer = Lowerer()
>>> lowerer.lower('WOW WHO COULD GUESS CACHING COULD BE SO NEAT')
'wow who could guess caching could be so neat'
>>> len(lowerer.cache)
1
```

Similar functionality exists in Python 3.4's `functools.lru_cache()`, but that approach doesn't support cache strategy modification or sharing cache objects across functions.

### cachedproperty() Decorator

```python
boltons.cacheutils.cachedproperty(func)
```

"The cachedproperty is used similar to property, except that the wrapped method is only called once. This is commonly used to implement lazy attributes."

After accessing the property, the value is stored on the instance using the same name, allowing cache clearing via `delattr()` or instance `__dict__` manipulation.

---

## Threshold-bounded Counting

### Class Definition

```python
class boltons.cacheutils.ThresholdCounter(threshold=0.001)
```

A bounded dict-like mapping from keys to counts. The ThresholdCounter automatically compacts after every (1 / threshold) additions, maintaining exact counts for keys whose count represents at least the threshold ratio of total data. "In other words, if a particular key is not present in the ThresholdCounter, its count represents less than threshold of the total data."

### Example Usage

```python
>>> tc = ThresholdCounter(threshold=0.1)
>>> tc.add(1)
>>> tc.items()
[(1, 1)]
>>> tc.update([2] * 10)
>>> tc.get(1)
0
>>> tc.add(5)
>>> 5 in tc
True
>>> len(list(tc.elements()))
11
```

The API resembles `collections.Counter`, with notable omissions: items cannot be set directly, uncounted, or removed, as this would disrupt the mathematics.

Use ThresholdCounter for "best-effort long-lived counts for dynamically-keyed data." Without such a bounded structure, dynamic keys often represent memory leaks affecting reliability.

The item replacement strategy is fully deterministic, functioning as "_Amortized Least Relevant_." The maximum keys stored is _(2/threshold)_, realistically _(1/threshold)_ for uniformly random datastreams, and better for real-world data.

This implementation derives from the Lossy Counting algorithm described in "Approximate Frequency Counts over Data Streams" by Manku & Motwani.

### ThresholdCounter Methods

**add(key)**
"Increment the count of key by 1, automatically adding it if it does not exist. Cache compaction is triggered every 1/threshold additions."

**elements()**
"Return an iterator of all the common elements tracked by the counter. Yields each key as many times as it has been seen."

**get(key, default=0)**
"Get count for key, defaulting to 0."

**get_common_count()**
"Get the sum of counts for keys exceeding the configured data threshold."

**get_commonality()**
"Get a float representation of the effective count accuracy. The higher the number, the less uniform the keys being added, and the higher accuracy and efficiency of the ThresholdCounter."

If stronger data cardinality measurement is needed, consider hyperloglog.

**get_uncommon_count()**
"Get the sum of counts for keys that were culled because the associated counts represented less than the configured threshold. The long-tail counts."

**most_common(n=None)**
"Get the top n keys and counts as tuples. If n is omitted, returns all the pairs."

**update(iterable, **kwargs)**
"Like dict.update() but add counts instead of replacing them, used to add multiple items in one call. Source can be an iterable of keys to add, or a mapping of keys to integer counts."
