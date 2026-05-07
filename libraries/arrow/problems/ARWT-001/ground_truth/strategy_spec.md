# ARWT-001 Strategy Spec

## Bug 1 (L4): _get_frames quarter step 3→4

**Location**: `arrow/arrow.py`, `_get_frames()` classmethod
**Trigger condition**: Any call to `span('quarter')` or `range('quarter')` — the
`_get_frames` helper returns 4 months per quarter instead of 3. Importantly,
`shift(quarters=n)` is NOT affected (it uses `_MONTHS_PER_QUARTER` directly).

**Trigger probability with default strategy**: ~100% — any Arrow object in Q2/Q3/Q4
will show the wrong span boundary, and any range over multiple quarters will show
wrong step sizes.

**Required strategy**: Any Arrow with month != 1 or month != 4 or month != 7 or
month != 10 (i.e., NOT at exact quarter boundaries), OR any range('quarter') call.
`st.builds(arrow.Arrow, year=..., month=st.integers(1,12), day=st.integers(1,28))`

**Property**: `span('quarter')[1].shift(microseconds=1)` must equal
`span('quarter')[0].shift(months=3)`. Or: consecutive elements in
`range('quarter', start, end)` must be exactly 3 months apart.

---

## Bug 2 (L2): range() < instead of <=

**Location**: `arrow/arrow.py`, `Arrow.range()` classmethod, line ~489
**Trigger condition**: Call `range(frame, start, end)` where `end` is at an exact
frame boundary from `start` (i.e., end - start is a whole number of frame steps).
The most reliable trigger: `range('day', start, start.shift(days=N))` for any N >= 0.
Simplest: `range('day', a, a)` (start == end) returns empty list instead of [a].

**Trigger probability with default strategy**: ~0% for typical tests that don't use
exact endpoints. ~100% when start == end or end is at exact step boundary.

**Required strategy**:
```python
st_arrow_day = st.builds(arrow.Arrow, year=..., month=..., day=...,
                          hour=st.just(0), minute=st.just(0), second=st.just(0), microsecond=st.just(0))
extra = st.integers(min_value=0, max_value=30)
# Then: range('day', a, a.shift(days=extra))
```
Or simply `range('day', a, a)` (zero-length range) for instant detection.

**Property**: `list(range(frame, start, start.shift(**{frame+'s': N})))` has length N+1.
Special case: `list(range(frame, a, a))` must have length 1.

---

## Bug 3 (L3): span() ceil microseconds -1 → -2

**Location**: `arrow/arrow.py`, `Arrow.span()` method, line ~594
**Trigger condition**: Any call to `span(frame)` with default `[)` bounds (or any
bounds with `)` on the right). The ceil is 1 microsecond too early.

**Trigger probability with default strategy**: ~100% — any datetime and any frame
will produce a ceil that is off by 1 microsecond.

**Required strategy**: Any Arrow object.
`st.builds(arrow.Arrow, year=st.integers(2000, 2030), month=st.integers(1,12), ...)`

**Property**: Span contiguity — `a.ceil(frame).shift(microseconds=1) == a.floor(frame).shift(**{frame+'s': 1})`
Equivalently: `a.span(frame)[1].shift(microseconds=1) == a.span(frame)[0].shift(**{frame+'s': 1})`

The key insight from docs: "The default [) span means spans tile the timeline
without overlap or gap." This implies ceil + 1us == next floor.

---

## Bug 4 (L3): span() quarter floor % 3 → % 4

**Location**: `arrow/arrow.py`, `Arrow.span()` method, line ~584
**Trigger condition**: Any Arrow in Q2 (months 4-6), Q3 (months 7-9), or Q4
(months 10-12). Q1 (months 1-3) is NOT affected because (month-1)%4 == (month-1)%3
for months 1, 2, 3.

**Trigger probability with default strategy**: 9/12 = 75% for uniform month
distribution. Only months 1, 2, 3 give correct results.

**Required strategy**: months 4-12:
`st.integers(min_value=4, max_value=12)` for month, or just uniform month sampling
since 75% of months trigger the bug.

**Property**: `a.floor('quarter').month` must be in {1, 4, 7, 10}, and must equal
`((a.month - 1) // 3) * 3 + 1`.
