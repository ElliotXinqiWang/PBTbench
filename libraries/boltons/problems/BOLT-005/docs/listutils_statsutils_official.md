# boltons.listutils and boltons.statsutils — API Reference

This document covers two modules from boltons 25.0.0:

- **`boltons.listutils`**: List utilities, including `BarrelList`
- **`boltons.statsutils`**: Descriptive-statistics utilities, including `Stats`

---

## Part 1: `boltons.listutils`

### `BarrelList` (also aliased as `BList`)

`BarrelList` is a `list` subtype backed by many dynamically-scaled sublists
("barrels"), providing better scaling and random-insertion/deletion characteristics
than Python's built-in `list` for very large datasets.  It has an **identical API**
to `list` and supports indexing, slicing, sorting, and all standard sequence operations.

```python
from boltons.listutils import BarrelList, BList

bl = BarrelList(range(100_000))
bl.pop(50_000)      # → 50000
len(bl)             # → 99999
bl[0]               # → 0
bl[-1]              # → 99999
```

#### Construction

```python
bl = BarrelList()           # empty list
bl = BarrelList(iterable)   # from any iterable
bl = BarrelList.from_iterable(iterable)
```

#### Internal barrel structure

Internally, `BarrelList` maintains `bl.lists`, a list of Python lists.  Each
sub-list is called a **barrel**.  When a barrel grows beyond `_cur_size_limit`
(a function of total list length), `_balance_list()` splits it into smaller pieces.
The split threshold is approximately `1520 * log2(n + 2)` elements, meaning:

- A list with ≤ ~21 000 elements typically lives in a **single barrel**.
- A list with ~22 000 or more elements — especially after `insert()` operations
  that trigger `_balance_list()` — will typically span **multiple barrels**
  (often 3 or more).

The barrel structure is transparent to callers: all public API methods
maintain the invariant that the concatenation of all barrel contents equals
the logical list contents in order.

#### Core invariants (all must hold for any BarrelList `bl`)

1. **Content invariant**: `list(bl) == [bl[i] for i in range(len(bl))]`
2. **Length invariant**: `len(bl) == sum(len(cur) for cur in bl.lists)`
3. **Index roundtrip** (for lists with distinct elements):
   `bl[bl.index(x)] == x` for every `x` in `bl`
4. **Pop-last invariant**: `bl.pop()` returns `list(bl)[-1]` before the pop,
   and `len(bl)` decreases by exactly 1.
5. **Membership invariant**: `(x in bl) == (x in list(bl))` for every `x`.

#### Methods

##### `bl.append(item)`

Append `item` to the end of the list.  O(1) amortized.

```python
bl = BarrelList([1, 2, 3])
bl.append(4)
list(bl)  # → [1, 2, 3, 4]
```

##### `bl.extend(iterable)`

Extend the list by appending all items from `iterable`.

##### `bl.insert(index, item)`

Insert `item` before position `index`.  After insertion, `_balance_list` may
split the affected barrel if it has grown past the size limit.  This is the
primary operation that triggers multi-barrel behaviour for large lists.

```python
bl = BarrelList(range(5))
bl.insert(2, 99)
list(bl)  # → [0, 1, 99, 2, 3, 4]
```

##### `bl.pop([index])`

Remove and return item at `index` (default: last element).

- `bl.pop()` — returns and removes the **last** element.
- `bl.pop(i)` — returns and removes the element at position `i`.

For a multi-barrel list, `bl.pop()` must return the globally last element
(the last element of the last barrel), not an element from an earlier barrel.

```python
bl = BarrelList([10, 20, 30])
bl.pop()    # → 30
bl.pop(0)   # → 10
list(bl)    # → [20]
```

##### `bl.index(item)`

Return the index of the first occurrence of `item` in `bl`.  Raises `ValueError`
if not present.

The returned index `i` must satisfy `bl[i] == item`.  For a multi-barrel list
this requires correctly summing the lengths of all barrels that were searched
before the barrel containing `item`.  Specifically, if `item` is found in
the k-th barrel at relative position `r`, the correct global index is:

```
sum(len(barrel) for barrel in bl.lists[:k]) + r
```

```python
bl = BarrelList(['a', 'b', 'c', 'd'])
bl.index('c')   # → 2
bl[bl.index('c')]  # → 'c'  (always)
```

##### `bl[index]` / `bl[index] = value` / `del bl[index]`

Get, set, or delete the element at `index`.  Negative indices are supported
(`bl[-1]` is the last element, `bl[-2]` is second-to-last, etc.).

##### `bl[start:stop:step]` — slicing

Returns a new `BarrelList` with the specified slice.  Slicing works across
barrel boundaries.

```python
bl = BarrelList(range(10))
list(bl[2:5])   # → [2, 3, 4]
list(bl[::2])   # → [0, 2, 4, 6, 8]
```

##### `item in bl`

Return `True` if `item` is in the list, `False` otherwise.  This checks **all**
barrels.  For a multi-barrel list, `x in bl` must agree with `x in list(bl)`.

##### `bl.count(item)`

Return the total number of occurrences of `item`, summed across all barrels.

##### `len(bl)`

Return the total number of elements.

##### `bl.sort()`

Sort the list in place.  For large (multi-barrel) lists, a merge-sort approach
is used.

##### `bl.reverse()`

Reverse the list in place.

---

## Part 2: `boltons.statsutils`

### `Stats`

The `Stats` type wraps a dataset (a list of numbers) and provides all standard
descriptive-statistics measures as **cached property attributes**.  Accessing
`s.mean` computes and stores the mean; subsequent accesses are free.

```python
from boltons.statsutils import Stats

s = Stats(range(42))
s.mean      # → 20.5
s.median    # → 20.5
s.variance  # → 146.75
```

#### Construction

```python
Stats(data, default=0.0, use_copy=True, is_sorted=False)
```

| Parameter   | Description |
|-------------|-------------|
| `data`      | List (or any iterable) of numeric values. |
| `default`   | Value returned when a statistic is undefined (e.g. empty data). |
| `use_copy`  | If `True` (default), the data is copied to avoid unintended mutations. |
| `is_sorted` | If `True`, skips the sorting step when accessing order-dependent statistics. |

#### Statistical measures

All measures below are **property attributes**.  They are computed lazily
and cached on first access.  Call `s.clear_cache()` after adding data to
recompute.

##### `s.count`

Number of data points (`int`).  Equivalent to `len(s)`.

```python
Stats(range(20)).count   # → 20
```

##### `s.mean`

Arithmetic mean (average): `sum(data) / len(data)`.

```python
Stats(range(20)).mean    # → 9.5
```

##### `s.median`

Middle value (or average of two middle values) of the sorted dataset.
Equivalent to `s.get_quantile(0.5)`.

```python
Stats([2, 1, 3]).median       # → 2    (odd count)
Stats([1, 2, 3, 4]).median    # → 2.5  (even count: average of 2 and 3)
```

##### `s.variance`

**Population variance**: the average of the squared deviations from the mean.

```
variance = sum((v - mean)^2 for v in data) / n
```

This is the **population** formula (denominator `n`), **not** the Bessel-corrected
sample formula (denominator `n-1`).  For `n >= 2`, these two values differ.

```python
Stats(range(97)).variance   # → 784.0
Stats([1, 2, 3, 4, 5]).variance  # → 2.0  (population), NOT 2.5 (sample)
```

##### `s.std_dev`

Standard deviation: `sqrt(variance)`.

```python
Stats(range(97)).std_dev   # → 28.0
```

##### `s.min` / `s.max`

Minimum and maximum values in the dataset.

##### `s.iqr`

**Inter-Quartile Range** (IQR): `get_quantile(0.75) - get_quantile(0.25)`.

A robust measure of dispersion, less influenced by outliers than `std_dev`.

```python
Stats([1, 2, 3, 4, 5]).iqr   # → 2
Stats(range(1001)).iqr        # → 500
```

##### `s.trimean`

Weighted average of the median and the two quartiles:

```
trimean = (Q1 + 2*Q2 + Q3) / 4
```

where `Q1 = get_quantile(0.25)`, `Q2 = get_quantile(0.5)`,
`Q3 = get_quantile(0.75)`.

```python
Stats([2, 1, 3]).trimean     # → 2.0
Stats(range(97)).trimean     # → 48.0
```

##### `s.median_abs_dev` (alias: `s.mad`)

Median Absolute Deviation: `median(|v - median(data)| for v in data)`.

##### `s.skewness`

Asymmetry of the distribution.  0 for symmetric data.

##### `s.kurtosis`

"Peakedness" of the distribution.  Normal distribution ≈ 3.

#### `s.get_quantile(q)`

Return the `q`-th quantile of the data, for `q` in `[0.0, 1.0]`.

Uses **linear interpolation** between adjacent sorted values:

```
idx = q * (n - 1)
result = data[floor(idx)] * (ceil(idx) - idx)
       + data[ceil(idx)]  * (idx - floor(idx))
```

When `idx` is an integer (no interpolation needed), `result = data[idx]`.

Key identities:
- `s.get_quantile(0.0)` == `s.min`
- `s.get_quantile(1.0)` == `s.max`
- `s.get_quantile(0.5)` == `s.median`

The **weights** in the interpolation formula are `(ceil(idx) - idx)` for the
lower value and `(idx - floor(idx))` for the upper value.  These are
distance-based weights: the closer `idx` is to a grid point, the higher the
weight for that grid point.  Reversing the two weights gives incorrect results
for any `q` where `idx` is not an integer.

```python
s = Stats([1, 2, 3, 4])  # n=4
s.get_quantile(0.0)   # → 1
s.get_quantile(0.25)  # → 1.75   (idx=0.75: data[0]*0.25 + data[1]*0.75)
s.get_quantile(0.5)   # → 2.5    (idx=1.5:  data[1]*0.5  + data[2]*0.5)
s.get_quantile(0.75)  # → 3.25   (idx=2.25: data[2]*0.75 + data[3]*0.25)
s.get_quantile(1.0)   # → 4
```

#### `s.get_zscore(value)`

Z-score of `value` relative to the dataset:

```
z = (value - mean) / std_dev
```

Special cases: if `std_dev == 0`, returns 0 (for `value == mean`),
`float('inf')` (for `value > mean`), or `float('-inf')` (for `value < mean`).

```python
s = Stats([0, 10, 20, 30, 40])
s.get_zscore(s.mean)             # → 0.0
s.get_zscore(s.mean + s.std_dev) # → 1.0
```

#### `s.describe(quantiles=None, format='dict')`

Return a summary of common statistics.

```python
stats = Stats(range(1, 8))
print(stats.describe(format='text'))
# count:    7
# mean:     4.0
# std_dev:  2.0
# mad:      2.0
# min:      1
# 0.25:     2.5
# 0.5:      4
# 0.75:     5.5
# max:      7
```

#### `s.trim_relative(amount=0.15)`

Remove `amount` fraction of values from each end of the sorted data in place.

```python
s = Stats(list(range(20)))
s.trim_relative(0.25)   # removes 5 from each end
len(s.data)             # → 10
```

After trimming, `clear_cache()` is called automatically so subsequent
statistics reflect the trimmed dataset.

#### Module-level convenience functions

All `Stats` properties have module-level equivalents for one-shot use:

```python
from boltons.statsutils import mean, median, variance, std_dev, iqr, trimean

mean(range(20))       # → 9.5
median([2, 1, 3])     # → 2
variance(range(97))   # → 784.0   (population variance)
```

---

## Key invariants to test

### BarrelList

- **Index roundtrip**: for any `x` in `bl`, `bl[bl.index(x)] == x`
  (critical when `bl` spans multiple internal barrels).
- **Pop-last**: `bl.pop()` returns the element at position `len(bl) - 1`
  before the call, regardless of how many internal barrels exist.
- **Membership**: `(x in bl) == any(x in cur for cur in bl.lists)`.
- **Length consistency**: `len(bl) == len(list(bl))`.
- **Model-based**: `list(bl) == [bl[i] for i in range(len(bl))]`.

### Stats

- **Variance formula**: `Stats(data).variance == sum((v - mean)^2 for v in data) / n`
  (population variance, denominator `n`, not `n-1`).
- **Quantile interpolation**: `get_quantile(q)` must match the documented
  linear-interpolation formula; the two weights are `(ceil_idx - idx)` and
  `(idx - floor_idx)`, assigned to the lower and upper sorted values respectively.
- **IQR definition**: `iqr == get_quantile(0.75) - get_quantile(0.25)`.
- **Trimean definition**: `trimean == (Q1 + 2*Q2 + Q3) / 4`.
- **Z-score**: `get_zscore(mean + std_dev) == 1.0` (when `std_dev != 0`).
