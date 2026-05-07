# Arrow 1.4.0 API Reference

`arrow` is a Python library for working with dates and times. It provides a clean,
sensible API for creating, manipulating, formatting, and converting dates and times.
Version: 1.4.0

## Core Class: `Arrow`

An `Arrow` object is an enhanced `datetime` replacement. It is always timezone-aware.

```python
import arrow

# Creation
a = arrow.Arrow(2020, 6, 15, 12, 30, 0)       # direct construction (UTC default)
a = arrow.utcnow()                             # current UTC time
a = arrow.now('US/Eastern')                   # current time in timezone
a = arrow.get('2020-06-15T12:30:00+00:00')    # parse from string
```

### `Arrow.shift(**kwargs) -> Arrow`

Returns a new `Arrow` with attributes shifted relative to the current value.

**Supported kwargs**: `years`, `months`, `days`, `hours`, `minutes`, `seconds`,
`microseconds`, `weeks`, `quarters`, `weekday`.

**Quarters**: A quarter is 3 calendar months. `shift(quarters=1)` advances 3 months.
`shift(quarters=2)` advances 6 months, etc.

```python
arrow.Arrow(2020, 1, 1).shift(years=1, months=-1)   # 2020-12-01
arrow.Arrow(2020, 1, 1).shift(quarters=1)            # 2020-04-01 (Q2 starts Apr)
arrow.Arrow(2020, 1, 1).shift(quarters=4)            # 2021-01-01
arrow.Arrow(2020, 1, 1).shift(months=6, days=3)      # 2020-07-04
```

**Quarters and months combined**: When both `quarters` and `months` are specified,
the total shift equals `quarters * 3 + months` months. For example:
```python
arrow.Arrow(2020, 1, 1).shift(quarters=1, months=1)  # 2020-05-01 (3+1=4 months)
arrow.Arrow(2020, 1, 1).shift(quarters=2, months=-1) # 2020-06-01 (6-1=5 months)
```

### `Arrow.floor(frame) -> Arrow`

Returns a new `Arrow` truncated to the start of the given `frame`.

**Supported frames**: `year`, `quarter`, `month`, `week`, `day`, `hour`, `minute`,
`second`, `microsecond`.

**Quarter behavior**: A year has 4 quarters: Q1 (Jan–Mar), Q2 (Apr–Jun), Q3 (Jul–Sep),
Q4 (Oct–Dec). `floor('quarter')` returns the first day of the current quarter
(month 1, 4, 7, or 10 of the year), at midnight UTC.

```python
arrow.Arrow(2020, 1, 15, 14, 30).floor('day')      # 2020-01-15T00:00:00+00:00
arrow.Arrow(2020, 1, 15, 14, 30).floor('hour')     # 2020-01-15T14:00:00+00:00
arrow.Arrow(2020, 5, 15).floor('quarter')          # 2020-04-01T00:00:00+00:00
arrow.Arrow(2020, 8, 15).floor('quarter')          # 2020-07-01T00:00:00+00:00
arrow.Arrow(2020, 11, 15).floor('quarter')         # 2020-10-01T00:00:00+00:00
```

### `Arrow.ceil(frame) -> Arrow`

Returns a new `Arrow` at the end of the given `frame`. Equivalent to the second
element of `span(frame, bounds='[)')`.

```python
arrow.Arrow(2020, 1, 15, 14, 30).ceil('hour')    # 2020-01-15T14:59:59.999999+00:00
arrow.Arrow(2020, 1, 15, 14, 30).ceil('day')     # 2020-01-15T23:59:59.999999+00:00
```

**Important**: `ceil(frame)` returns the last microsecond *within* the frame period.
That is, `ceil(frame) + 1 microsecond == floor(frame).shift(**{frame+'s': 1})`.
This means consecutive spans tile the timeline without overlap or gap.

### `Arrow.span(frame, count=1, bounds='[)', exact=False, week_start=1) -> (Arrow, Arrow)`

Returns a `(floor, ceil)` tuple representing the timespan of the Arrow in the given frame.

**bounds**: A 2-character string specifying whether the start and end are included:
- `'[)'` (default): includes start, excludes end. `floor <= self < floor.shift(frame=count)`.
  The `ceil` is 1 microsecond before the next period's floor.
- `'[]'`: includes both. The `ceil` equals `floor.shift(frame=count)` exactly.
- `'()'`: excludes both. `floor` is shifted 1 microsecond forward.
- `'(]'`: excludes start, includes end.

**Quarter spans**: A quarter spans exactly 3 calendar months.
- Q1: Jan 1 – Mar 31 (inclusive)
- Q2: Apr 1 – Jun 30
- Q3: Jul 1 – Sep 30
- Q4: Oct 1 – Dec 31

```python
a = arrow.Arrow(2020, 5, 15, 14, 30)

a.span('hour')             # ([14:00:00], [14:59:59.999999])
a.span('day')              # ([2020-05-15 00:00:00], [2020-05-15 23:59:59.999999])
a.span('quarter')          # ([2020-04-01 00:00:00], [2020-06-30 23:59:59.999999])

a.span('hour', bounds='[]')   # ([14:00:00], [15:00:00])    — includes next boundary
a.span('day', bounds='()')    # ([00:00:00.000001], [23:59:59.999999])
```

**Span tiling invariant**: With default `[)` bounds, spans tile the timeline:
```python
fl, cl = a.span('hour')
assert cl.shift(microseconds=1) == fl.shift(hours=1)  # no gap, no overlap
```

### `Arrow.range(frame, start, end=None, tz=None, limit=None) -> Generator`

Returns a generator of `Arrow` objects at each `frame` step from `start` to `end`.

**Endpoint inclusiveness**: Unlike Python's `range()`, arrow's `range()` **includes
the endpoint** when `end` is at an exact step boundary from `start`. That is, the
iteration continues **while `current <= end`** (not strictly less than).

```python
start = arrow.Arrow(2020, 1, 1)
end = arrow.Arrow(2020, 1, 3)
list(arrow.Arrow.range('day', start, end))
# [2020-01-01, 2020-01-02, 2020-01-03]  — endpoint Jan 3 IS included

# When start == end, yields exactly one element:
list(arrow.Arrow.range('day', start, start))
# [2020-01-01]  — single element

# Quarterly range (each step is exactly 3 months):
s = arrow.Arrow(2020, 1, 1)
e = arrow.Arrow(2020, 12, 31)
list(arrow.Arrow.range('quarter', s, e))
# [2020-01-01, 2020-04-01, 2020-07-01, 2020-10-01]
```

**NOTE on end parameter**: `end` is the upper bound for iteration. The last yielded
value is the largest step that is `<= end`. When `end` falls exactly on a step, it
is included.

### `Arrow.span_range(frame, start, end, ...) -> Iterable[(Arrow, Arrow)]`

Returns an iterator of `(floor, ceil)` span tuples covering the period from `start`
to `end`.

### Supported Frames Summary

| Frame | Plural | Notes |
|---|---|---|
| `year` | `years` | |
| `quarter` | `quarters` | 3 calendar months |
| `month` | `months` | |
| `week` | `weeks` | |
| `day` | `days` | |
| `hour` | `hours` | |
| `minute` | `minutes` | |
| `second` | `seconds` | |
| `microsecond` | `microseconds` | |

### `Arrow.to(tz) -> Arrow`

Converts to a different timezone.

```python
utc = arrow.utcnow()
eastern = utc.to('US/Eastern')
back = eastern.to('UTC')
assert back == utc  # roundtrip preserves the instant
```

### `Arrow.quarter` property

Returns the quarter number (1–4) of the Arrow's date.

```python
arrow.Arrow(2020, 1, 15).quarter   # 1
arrow.Arrow(2020, 4, 15).quarter   # 2
arrow.Arrow(2020, 7, 15).quarter   # 3
arrow.Arrow(2020, 10, 15).quarter  # 4
```

## Calendar Quarter Reference

| Quarter | Months | Start date | End date |
|---|---|---|---|
| Q1 | Jan, Feb, Mar | January 1 | March 31 |
| Q2 | Apr, May, Jun | April 1 | June 30 |
| Q3 | Jul, Aug, Sep | July 1 | September 30 |
| Q4 | Oct, Nov, Dec | October 1 | December 31 |

Each quarter is **exactly 3 calendar months**. A year has exactly 4 quarters.
