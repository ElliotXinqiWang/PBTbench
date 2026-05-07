# iterutils - itertools improvements
# Source: https://boltons.readthedocs.io/en/latest/iterutils.html
# boltons version: 25.0.0

The `iterutils` module fills gaps in Python's standard `itertools` library with tested, Pythonic solutions. Many functions have two versions: one returning an iterator (named with `_iter` suffix) and a convenience form returning a list.

## Iteration

### chunked()

Returns a list of `count` chunks, each with `size` elements, from iterable `src`. If not evenly divisible, the final chunk contains fewer elements. The `fill` keyword argument enables padding.

**Examples:**
```python
chunked(range(10), 3)
# [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

chunked(range(10), 3, fill=None)
# [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]

chunked(range(10), 3, count=2)
# [[0, 1, 2], [3, 4, 5]]
```

### chunked_iter()

Generates `size`-sized chunks from `src`. Without `fill`, final chunks may be smaller than `size`.

**Examples:**
```python
list(chunked_iter(range(10), 3))
# [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

list(chunked_iter(range(10), 3, fill=None))
# [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]
```

**Note:** `fill=None` uses `None` as the fill value.

### chunk_ranges()

Generates `chunk_size`-sized chunk ranges for input with length `input_size`. Returns iterator of (start, end) tuples.

**Parameters:**
- `input_size`: Length of input
- `chunk_size`: Size of chunks
- `input_offset`: Starting position (default: 0)
- `overlap_size`: Overlap between chunks (default: 0)
- `align`: Align items where `i % (chunk_size-overlap_size) == 0` (default: False)

**Examples:**
```python
list(chunk_ranges(input_offset=10, input_size=10, chunk_size=5))
# [(10, 15), (15, 20)]

list(chunk_ranges(input_offset=10, input_size=10, chunk_size=5, overlap_size=1))
# [(10, 15), (14, 19), (18, 20)]

list(chunk_ranges(input_offset=4, input_size=15, chunk_size=5, align=False))
# [(4, 9), (9, 14), (14, 19)]

list(chunk_ranges(input_offset=4, input_size=15, chunk_size=5, align=True))
# [(4, 5), (5, 10), (10, 15), (15, 19)]
```

### pairwise()

Convenience function calling `windowed()` with `size=2`.

**Parameters:**
- `src`: Input iterable
- `end`: Optional sentinel value for final pair

**Examples:**
```python
pairwise(range(5))
# [(0, 1), (1, 2), (2, 3), (3, 4)]

pairwise([])
# []

list(pairwise(range(3), end=None))
# [(0, 1), (1, 2), (2, None)]
```

**Note:** Returns one fewer pair than input length, except empty input yields empty list. With `end` set, returns pairs equal to input length with final pair's second element being `end`.

### pairwise_iter()

Generator version of `pairwise()`, calling `windowed_iter()` with `size=2`.

**Examples:**
```python
list(pairwise_iter(range(5)))
# [(0, 1), (1, 2), (2, 3), (3, 4)]

list(pairwise_iter([]))
# []

list(pairwise_iter(range(3), end=None))
# [(0, 1), (1, 2), (2, None)]
```

**Note:** For infinite iterators, setting `end` has no effect.

### windowed()

Returns tuples with exactly length `size`. If `fill` is unset and iterable is too short to make a window, no tuples are returned.

**Parameters:**
- `src`: Input iterable
- `size`: Window size
- `fill`: Optional padding value

### windowed_iter()

Returns tuples with length `size` representing a sliding window over `src`.

**Parameters:**
- `src`: Input iterable
- `size`: Window size
- `fill`: Optional padding value (unset by default)

**Examples:**
```python
list(windowed_iter(range(7), 3))
# [(0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5), (4, 5, 6)]

list(windowed_iter(range(3), 5))
# []

windowed(range(4), 3, fill=None)
# [(0, 1, 2), (1, 2, 3), (2, 3, None), (3, None, None)]
```

**Note:** Without `fill`, if iterable is too short, no windows are returned. With `fill` set, always yields windows equal to input length. For infinite iterators, `fill` has no effect.

### unique()

Returns a list of unique values in order of first appearance, determined by `key`.

**Parameters:**
- `src`: Input iterable
- `key`: Optional callable or string attribute name

**Example:**
```python
ones_n_zeros = '11010110001010010101010'
''.join(unique(ones_n_zeros))
# '10'
```

### unique_iter()

Yields unique elements from iterable based on `key`, in order of first appearance.

**Parameters:**
- `src`: Input iterable
- `key`: Optional callable or string attribute name

**Examples:**
```python
repetitious = [1, 2, 3] * 10
list(unique_iter(repetitious))
# [1, 2, 3]

pleasantries = ['hi', 'hello', 'ok', 'bye', 'yes']
list(unique_iter(pleasantries, key=lambda x: len(x)))
# ['hi', 'hello', 'bye']
```

**Note:** `key` defaults to object itself but can be a callable or string attribute name, falling back to identity when attribute not present.

### redundant()

Complement of `unique()`. Returns non-unique/duplicate values as list of first redundant value in `src`. Pass `groups=True` for groups of all values with redundancies.

**Parameters:**
- `src`: Input iterable
- `key`: Optional callable for normalization
- `groups`: Return groups of duplicates (default: False)

**Examples:**
```python
redundant([1, 2, 3, 4])
# []

redundant([1, 2, 3, 2, 3, 3, 4])
# [2, 3]

redundant([1, 2, 3, 2, 3, 3, 4], groups=True)
# [[2, 2], [3, 3, 3]]

redundant(['hi', 'Hi', 'HI', 'hello'], key=str.lower)
# ['Hi']

redundant(['hi', 'Hi', 'HI', 'hello'], groups=True, key=str.lower)
# [['hi', 'Hi', 'HI']]
```

**Note:** Output designed for reporting duplicates. Use `key` with unhashable values. No streaming equivalent currently exists.

## Stripping and Splitting

### split()

Splits iterable based on separator. Like `str.split()` but for all iterables. Returns list of lists.

**Example:**
```python
split(['hi', 'hello', None, None, 'sup', None, 'soap', None])
# [['hi', 'hello'], ['sup'], ['soap']]
```

### split_iter()

Splits iterable based on separator `sep`, maximum `maxsplit` times.

**Parameters:**
- `src`: Input iterable
- `sep`: Separator (single value, iterable of separators, or callable)
- `maxsplit`: Maximum number of splits

**Examples:**
```python
list(split_iter(['hi', 'hello', None, None, 'sup', None, 'soap', None]))
# [['hi', 'hello'], ['sup'], ['soap']]

list(split_iter(['hi', 'hello', None, None, 'sup', None]))
# [['hi', 'hello'], ['sup']]

list(split_iter(['hi', 'hello', None, None, 'sup', None], sep=[None]))
# [['hi', 'hello'], [], ['sup'], []]

falsy_sep = lambda x: not x
list(split_iter(['hi', 'hello', None, '', 'sup', False], falsy_sep))
# [['hi', 'hello'], [], ['sup'], []]
```

**Note:** When `sep` is `None`, groups separators. Use `sep=[None]` for empty lists between contiguous `None` values.

### strip()

Strips values from beginning and end of iterable. Returns list.

**Example:**
```python
strip(['Fu', 'Foo', 'Bar', 'Bam', 'Fu'], 'Fu')
# ['Foo', 'Bar', 'Bam']
```

### strip_iter()

Strips values from beginning and end of iterable. Returns generator.

**Example:**
```python
list(strip_iter(['Fu', 'Foo', 'Bar', 'Bam', 'Fu'], 'Fu'))
# ['Foo', 'Bar', 'Bam']
```

### lstrip()

Strips values from beginning of iterable. Returns list.

**Example:**
```python
lstrip(['Foo', 'Bar', 'Bam'], 'Foo')
# ['Bar', 'Bam']
```

### lstrip_iter()

Strips values from beginning of iterable. Returns generator.

**Example:**
```python
list(lstrip_iter(['Foo', 'Bar', 'Bam'], 'Foo'))
# ['Bar', 'Bam']
```

### rstrip()

Strips values from end of iterable. Returns list.

**Example:**
```python
rstrip(['Foo', 'Bar', 'Bam'], 'Bam')
# ['Foo', 'Bar']
```

### rstrip_iter()

Strips values from end of iterable. Returns generator.

**Example:**
```python
list(rstrip_iter(['Foo', 'Bar', 'Bam'], 'Bam'))
# ['Foo', 'Bar']
```

## Nested Structures

### remap()

Traverses and transforms nested structures recursively. Supports lists, tuples, sets, and dictionaries.

**Parameters:**
- `root`: Object to traverse
- `visit`: Callable accepting (path, key, value); returns new key-value pair or True/False
- `enter`: Controls which items are traversed
- `exit`: Handles items after visiting
- `cache`: Controls object caching (default: True)
- `reraise_visit`: Ignore visit errors when False
- `trace`: Print traversal events

**Example:**
```python
reviews = {'Star Trek': {'TNG': 10, 'DS9': 8.5, 'ENT': None},
           'Babylon 5': 6, 'Dr. Who': None}
remap(reviews, lambda p, k, v: v is not None)
# {'Babylon 5': 6, 'Star Trek': {'DS9': 8.5, 'TNG': 10}}
```

**Note:** Designed primarily for `visit` callable. Handles duplicates and self-referential objects automatically.

### get_path()

Retrieves value from nested object via lookup path tuple.

**Parameters:**
- `root`: Target object
- `path`: Tuple of keys (or dot-separated string)
- `default`: Fallback value if lookup fails

**Example:**
```python
root = {'a': {'b': {'c': [[1], [2], [3]]}}}
get_path(root, ('a', 'b', 'c', 2, 0))
# 3
```

**Note:** Provides improved error messaging via `PathAccessError`.

### research()

Searches nested structures for values matching a query criterion.

**Parameters:**
- `root`: Target object to search
- `query`: Callable accepting (path, key, value) returning bool
- `reraise`: Reraise query exceptions (default: False)
- `enter`: Custom enter function

**Example:**
```python
root = {'a': {'b': 1, 'c': (2, 'd', 3)}, 'e': None}
research(root, query=lambda p, k, v: isinstance(v, int))
# [(('a', 'b'), 1), (('a', 'c', 0), 2), (('a', 'c', 2), 3)]
```

**Returns:** List of (path, value) tuples.

### flatten()

Returns collapsed list of all elements from iterable, collapsing nested iterables.

**Example:**
```python
nested = [[1, 2], [[3], [4, 5]]]
flatten(nested)
# [1, 2, 3, 4, 5]
```

### flatten_iter()

Yields all elements from iterable, collapsing nested iterables.

**Example:**
```python
nested = [[1, 2], [[3], [4, 5]]]
list(flatten_iter(nested))
# [1, 2, 3, 4, 5]
```

## Numeric

### backoff()

Returns list of geometrically-increasing floats for exponential backoff.

**Example:**
```python
backoff(1, 10)
# [1.0, 2.0, 4.0, 8.0, 10.0]
```

### backoff_iter()

Generates geometrically-increasing floats for exponential backoff.

**Parameters:**
- `start`: Positive baseline number
- `stop`: Positive maximum number
- `count`: Steps before stopping (or 'repeat' for infinite)
- `factor`: Exponential increase rate (default: 2.0)
- `jitter`: Randomization factor between -1.0 and 1.0

**Examples:**
```python
list(backoff_iter(1.0, 10.0, count=5))
# [1.0, 2.0, 4.0, 8.0, 10.0]

list(backoff_iter(1.0, 10.0, count=8))
# [1.0, 2.0, 4.0, 8.0, 10.0, 10.0, 10.0, 10.0]

list(backoff_iter(0.25, 100.0, factor=10))
# [0.25, 2.5, 25.0, 100.0]
```

**Note:** `jitter` helps avoid thundering herd in distributed systems.

### frange()

Float-based range clone.

**Parameters:**
- `stop`: End value
- `start`: Start value (default: None, starts at 0)
- `step`: Increment (default: 1.0)

**Examples:**
```python
frange(5)
# [0.0, 1.0, 2.0, 3.0, 4.0]

frange(6, step=1.25)
# [0.0, 1.25, 2.5, 3.75, 5.0]

frange(100.5, 101.5, 0.25)
# [100.5, 100.75, 101.0, 101.25]

frange(5, 0)
# []

frange(5, 0, step=-1.25)
# [5.0, 3.75, 2.5, 1.25]
```

### xfrange()

Generator-based version of `frange()`.

**Example:**
```python
tuple(xfrange(1, 3, step=0.75))
# (1.0, 1.75, 2.5)
```

## Categorization

### bucketize()

Groups values in `src` iterable by value returned by `key`.

**Parameters:**
- `src`: Input iterable
- `key`: Callable, string attribute name, or list of bucket assignments
- `value_transform`: Modify values before adding to buckets
- `key_filter`: Exclude certain buckets

**Examples:**
```python
bucketize(range(5))
# {False: [0], True: [1, 2, 3, 4]}

is_odd = lambda x: x % 2 == 1
bucketize(range(5), is_odd)
# {False: [0, 2, 4], True: [1, 3]}

bucketize([1+1j, 2+2j, 1, 2], key='real')
# {1.0: [(1+1j), 1], 2.0: [(2+2j), 2]}

bucketize([1,2,365,4,98], key=[0,1,2,0,2])
# {0: [1, 4], 1: [2], 2: [365, 98]}

bucketize(range(10), lambda x: x % 3)
# {0: [0, 3, 6, 9], 1: [1, 4, 7], 2: [2, 5, 8]}

bucketize(range(5), value_transform=lambda x: x*x)
# {False: [0], True: [1, 4, 9, 16]}

bucketize(range(10), key=lambda x: x % 3, key_filter=lambda k: k % 3 != 1)
# {0: [0, 3, 6, 9], 2: [2, 5, 8]}
```

**Note:** Values are not deduplicated.

### partition()

Like `bucketize()` but for binary cases, returning collection for each predicate passed. Returns N+1 lists for N predicates.

**Parameters:**
- `src`: Input iterable
- `key`: Predicate function (default: bool) or string attribute name
- `*keys`: Additional predicate functions

**Examples:**
```python
nonempty, empty = partition(['', '', 'hi', '', 'bye'])
nonempty
# ['hi', 'bye']

import string
is_digit = lambda x: x in string.digits
decimal_digits, hexletters = partition(string.hexdigits, is_digit)
(''.join(decimal_digits), ''.join(hexletters))
# ('0123456789', 'abcdefABCDEF')

positive, negative, zero = partition(range(-1, 2),
                                     lambda i: i > 0,
                                     lambda i: i < 0)
# ([1], [-1], [0])
```

## Sorting

### soft_sorted()

Partial sort override. Float specific elements to top and/or sink to bottom while sorting rest.

**Parameters:**
- `iterable`: List or other iterable
- `first`: Sequence of elements for beginning
- `last`: Sequence of elements for end
- `key`: Callable for comparable keys
- `reverse`: Reverse sort for non-explicit elements

**Examples:**
```python
soft_sorted(['two', 'b', 'one', 'a'], first=['one', 'two'])
# ['one', 'two', 'a', 'b']

soft_sorted(range(7), first=[6, 15], last=[2, 4], reverse=True)
# [6, 5, 3, 1, 0, 2, 4]

import string
''.join(soft_sorted(string.hexdigits, first='za1', last='b', key=str.lower))
# 'aA1023456789cCdDeEfFbB'
```

### untyped_sorted()

Sorts heterogeneous type iterables, similar to legacy Python behavior.

**Parameters:**
- `iterable`: Input iterable
- `key`: Optional callable for comparable keys
- `reverse`: Reverse sort (default: False)

**Example:**
```python
untyped_sorted(['abc', 2.0, 1, 2, 'def'])
# [1, 2.0, 2, 'abc', 'def']
```

**Note:** Results may vary across Python versions. Mutually orderable types sort as expected.

## Reduction

### one()

Returns single object in iterable that evaluates to `True`, as determined by `key`. Like XOR over iterable.

**Parameters:**
- `src`: Input iterable
- `default`: Fallback value (default: None)
- `key`: Callable determining truthiness

**Examples:**
```python
one((True, False, False))
# True

one((True, False, True))
# None

one((0, 0, 'a'))
# 'a'

one((0, False, None))
# None

one((True, True), default=False)
# False

bool(one(('', 1)))
# True

one((10, 20, 30, 42), key=lambda i: i > 40)
# 42
```

**Note:** Returns `default` if no or multiple objects match condition.

### first()

Returns first element of iterable that evaluates to `True`, else `None` or optional `default`.

**Parameters:**
- `iterable`: Input iterable
- `default`: Fallback value (default: None)
- `key`: One-argument predicate function

**Examples:**
```python
first([0, False, None, [], (), 42])
# 42

first([0, False, None, [], ()]) is None
# True

first([0, False, None, [], ()], default='ohai')
# 'ohai'

import re
m = first(re.match(regex, 'abc') for regex in ['b.*', 'a(.*)'])
m.group(1)
# 'bc'

first([1, 1, 3, 4, 5], key=lambda x: x % 2 == 0)
# 4
```

### same()

Returns `True` when all values in iterable are equal to one another or optional reference value `ref`.

**Parameters:**
- `iterable`: Input iterable
- `ref`: Optional reference value

**Examples:**
```python
same([])
# True

same([1])
# True

same(['a', 'a', 'a'])
# True

same(range(20))
# False

same([[], []])
# True

same([[], []], ref='test')
# False
```

**Note:** Returns `True` for empty iterables.

## Type Checks

### is_iterable()

Returns `True` if object is iterable, `False` otherwise.

**Examples:**
```python
is_iterable([])
# True

is_iterable(object())
# False
```

### is_scalar()

Returns `False` if object is iterable container type. Strings are scalar.

**Examples:**
```python
is_scalar(object())
# True

is_scalar(range(10))
# False

is_scalar('hello')
# True
```

### is_collection()

Opposite of `is_scalar()`. Returns `True` if object is iterable other than string.

**Examples:**
```python
is_collection(object())
# False

is_collection(range(10))
# True

is_collection('hello')
# False
```
