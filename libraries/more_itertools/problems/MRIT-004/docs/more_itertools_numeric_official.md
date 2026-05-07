# more-itertools API Documentation — MRIT-004

This document covers the API for the functions tested in this problem.
Source: more-itertools 10.7.0 official documentation and docstrings.

---

## `numeric_range(*args)`

An extension of the built-in `range()` function whose arguments can be any orderable
numeric type.

### Signatures

```python
numeric_range(stop)
numeric_range(start, stop)
numeric_range(start, stop, step)
```

### Description

With only `stop` specified, `start` defaults to `0` and `step` defaults to `1`.
The output items will match the type of `stop`:

```python
>>> list(numeric_range(3.5))
[0.0, 1.0, 2.0, 3.0]
```

With only `start` and `stop` specified, `step` defaults to `1`. The output items
will match the type of `start`:

```python
>>> from decimal import Decimal
>>> start = Decimal('2.1')
>>> stop = Decimal('5.1')
>>> list(numeric_range(start, stop))
[Decimal('2.1'), Decimal('3.1'), Decimal('4.1')]
```

With `start`, `stop`, and `step` all specified:

```python
>>> from fractions import Fraction
>>> start = Fraction(1, 2)
>>> stop = Fraction(5, 2)
>>> step = Fraction(1, 2)
>>> list(numeric_range(start, stop, step))
[Fraction(1, 2), Fraction(1, 1), Fraction(3, 2), Fraction(2, 1)]
```

If `step` is zero, `ValueError` is raised. Negative steps are supported:

```python
>>> list(numeric_range(3, -1, -1.0))
[3.0, 2.0, 1.0, 0.0]
```

### Full Sequence Protocol

`numeric_range` implements `collections.abc.Sequence` and `collections.abc.Hashable`.
This means it supports:

- `__iter__`: iterate through elements in order
- `__reversed__`: iterate through elements in reverse order
- `__len__`: number of elements
- `__getitem__`: access by integer index or slice
- `__contains__`: membership testing (`elem in nr`)
- `__bool__`: truthiness (False if empty)
- `__eq__` / `__hash__`: equality and hashing
- `.count(value)`: count occurrences (0 or 1)
- `.index(value)`: find index of value

### `__reversed__`

Returns an iterator that yields elements in reverse order. The reversed sequence
must contain exactly the same elements as the forward sequence, in reverse order.

```python
>>> nr = numeric_range(0, 5, 1)
>>> list(reversed(nr))
[4, 3, 2, 1, 0]
>>> list(nr)[::-1]
[4, 3, 2, 1, 0]
```

The length of the reversed sequence must equal the length of the forward sequence:

```python
>>> len(list(reversed(numeric_range(0, 10, 2)))) == len(numeric_range(0, 10, 2))
True
```

### `__getitem__` (slicing)

Slicing returns a new `numeric_range`:

```python
>>> nr = numeric_range(0, 10, 1)
>>> nr[2:7]
numeric_range(2, 7)
>>> nr[::2]
numeric_range(0, 10, 2)
```

### `__contains__`

Membership testing does not iterate through all elements; it uses arithmetic:

```python
>>> 5 in numeric_range(0, 10, 2)  # 5 is odd, not in step-2 range
False
>>> 4 in numeric_range(0, 10, 2)  # 4 = 0 + 2*2
True
```

---

## `collapse(iterable, base_type=None, levels=None)`

Flatten an iterable with multiple levels of nesting into non-iterable types.

```python
>>> iterable = [(1, 2), ([3, 4], [[5], [6]])]
>>> list(collapse(iterable))
[1, 2, 3, 4, 5, 6]
```

Binary and text strings are not considered iterable and will not be collapsed:

```python
>>> iterable = ['ab', ('cd', 'ef'), ['gh', 'ij']]
>>> list(collapse(iterable, base_type=tuple))
['ab', ('cd', 'ef'), 'gh', 'ij']
```

### `levels` parameter

Specify `levels` to stop flattening after a certain nesting depth.
`levels=N` means: flatten exactly `N` levels deep.

```python
>>> iterable = [('a', ['b']), ('c', ['d'])]
>>> list(collapse(iterable))          # Fully flattened
['a', 'b', 'c', 'd']
>>> list(collapse(iterable, levels=1))  # Flatten tuples, but not inner lists
['a', ['b'], 'c', ['d']]
```

Another example with deeper nesting:

```python
>>> iterable = [[[1, 2], [3, 4]], [[5, 6]]]
>>> list(collapse(iterable, levels=1))   # Flatten one level
[[1, 2], [3, 4], [5, 6]]
>>> list(collapse(iterable, levels=2))   # Flatten two levels
[1, 2, 3, 4, 5, 6]
```

---

## `mark_ends(iterable)`

Yield 3-tuples of the form `(is_first, is_last, item)`.

```python
>>> list(mark_ends('ABC'))
[(True, False, 'A'), (False, False, 'B'), (False, True, 'C')]
```

Use this when looping over an iterable to take special action on its first
and/or last items:

```python
>>> iterable = ['Header', 100, 200, 'Footer']
>>> total = 0
>>> for is_first, is_last, item in mark_ends(iterable):
...     if is_first:
...         continue  # Skip the header
...     if is_last:
...         continue  # Skip the footer
...     total += item
>>> print(total)
300
```

### Semantics

- `is_first` is `True` only for the **first** element yielded.
- `is_last` is `True` only for the **last** element yielded.
- For a single-element iterable, both `is_first` and `is_last` are `True`.
- The items are yielded in the same order as the input.

```python
>>> list(mark_ends([42]))
[(True, True, 42)]
>>> list(mark_ends([1, 2]))
[(True, False, 1), (False, True, 2)]
>>> list(mark_ends([]))
[]
```

---

## `zip_offset(*iterables, offsets, longest=False, fillvalue=None)`

`zip` the input iterables together, but offset the `i`-th iterable by the
`i`-th item in `offsets`.

```python
>>> list(zip_offset('0123', 'abcdef', offsets=(0, 1)))
[('0', 'b'), ('1', 'c'), ('2', 'd'), ('3', 'e')]
```

This can be used as a lightweight alternative to SciPy or pandas to analyze
data sets in which some series have a lead or lag relationship.

### Parameters

- `offsets`: A sequence of integers. A **positive** offset `n` means skip the
  first `n` elements of that iterable (start from index `n`). A **negative**
  offset `-n` means prepend `n` fill values before that iterable.
- `longest`: If `True`, continue until the longest iterable is exhausted,
  using `fillvalue` for exhausted iterables.
- `fillvalue`: Value to use when `longest=True` and an iterable runs out,
  or when a negative offset is used.

```python
>>> list(zip_offset('0123', 'abcdef', offsets=(0, 1), longest=True))
[('0', 'b'), ('1', 'c'), ('2', 'd'), ('3', 'e'), (None, 'f')]

>>> list(zip_offset('0123', 'abcdef', offsets=(0, -1)))
[('0', None), ('1', 'a'), ('2', 'b'), ('3', 'c')]
```

### Offset semantics

| offset | effect on iterable |
|--------|--------------------|
| 0      | no change |
| +n     | skip first n elements (islice starting at index n) |
| -n     | prepend n fill values before the iterable |

An `offset` of `1` for `'abcdef'` gives `'bcdef'` (starting at index 1).
An `offset` of `2` gives `'cdef'` (starting at index 2).

If the number of iterables doesn't match the number of offsets, `ValueError`
is raised.
