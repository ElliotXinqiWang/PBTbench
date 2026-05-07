# Strategy Spec — ARWT-003

## Bug 1: `format("W")` uses `weekday()` (0-6) instead of `isoweekday()` (1-7)

**Location**: `arrow/formatter.py`, `_format_token()`, token `"W"`

**Trigger condition**:
Any call to `arrow.Arrow(...).format("W")`. The bug fires 100% of the time
because `dt.weekday()` always differs from `dt.isoweekday()` by exactly 1:
- `weekday()`: 0=Mon, 1=Tue, ..., 5=Sat, 6=Sun
- `isoweekday()`: 1=Mon, 2=Tue, ..., 6=Sat, 7=Sun

For any date that is not also having `weekday() == isoweekday()` (which never
happens since they differ by exactly 1 for all days), every call will be wrong.

**Why default strategy is insufficient**:
The default arrow strategy would need the agent to know to test the `W` token.
Since `W` is an obscure token (not commonly used), agents testing only the common
tokens (`YYYY-MM-DD HH:mm:ss`) will miss this bug.

**Trigger probability with targeted strategy**: 100% (every date triggers it)

**Minimum trigger input**:
```python
arrow.Arrow(2023, 1, 2).format("W")  # Monday → returns "2023-W01-0", should be "2023-W01-1"
```

**Ground truth property**:
```python
# The day component in W output must equal isoweekday() (1-7)
a = arrow.Arrow(year, month, day)
w_str = a.format("W")
day_num = int(w_str.split("-")[2])
assert 1 <= day_num <= 7  # must be in valid ISO weekday range
assert day_num == a.isoweekday()
```

---

## Bug 2: `is_between()` exclusive end uses `<=` (treats target==end as True)

**Location**: `arrow/arrow.py`, `is_between()`, return statement

**Trigger condition**:
Call `target.is_between(start, end, "[)")` or `target.is_between(start, end, "()")`
where `target == end` exactly.

The bug changes `target_ts < end_ts` to `target_ts <= end_ts` in the exclusive-end
check. When `target == end`:
- Correct: `target_ts < end_ts` → `False` → `is_between` returns `False`
- Buggy: `target_ts <= end_ts` → `True` → `is_between` returns `True`

**Why default strategy is insufficient**:
Random datetimes extremely rarely land exactly on the endpoint. The strategy must
explicitly construct `end = some_date` and then test `end.is_between(start, end, "[)")`.

**Trigger probability with targeted strategy**: 100%

**Minimum trigger input**:
```python
start = arrow.Arrow(2023, 1, 1)
end   = arrow.Arrow(2023, 12, 31)
assert not end.is_between(start, end, "[)")  # should be False (exclusive end)
# With bug: returns True
```

**Ground truth property**:
```python
# For any start/end, end should never be between them with exclusive-end bounds
start = arrow.Arrow(year, month, day)
end   = start.shift(days=offset_days)
assert not end.is_between(start, end, "[)")
assert not end.is_between(start, end, "()")
```

---

## Bug 3: `span(count=N)` uses `(count+1)*steps` instead of `count*steps`

**Location**: `arrow/arrow.py`, `span()`, `ceil = floor.shift(...)`

**Trigger condition**:
Any call to `Arrow.span(frame, count=N)` for any frame and any count ≥ 1.
The bug always fires: `(count+1)*steps` instead of `count*steps`.

- `span("day", count=1)` → covers 2 days instead of 1
- `span("day", count=3)` → covers 4 days instead of 3
- `span("hour", count=5)` → covers 6 hours instead of 5

**Why default strategy is insufficient**:
The simple invariant (span with default count=1 should be exactly 1 frame) is
violated by this bug. The agent needs to know that `count=N` means exactly N frames
and write a property checking the duration.

**Trigger probability with targeted strategy**: 100%

**Minimum trigger input**:
```python
a = arrow.Arrow(2023, 3, 15)
floor, ceil = a.span("day", count=1)
# Expected: ceil + 1us - floor == timedelta(days=1)
# Buggy: ceil + 1us - floor == timedelta(days=2)
```

**Ground truth property**:
```python
a = arrow.Arrow(year, month, day)
floor, ceil = a.span("day", count=count)
next_after_ceil = ceil.shift(microseconds=1)
delta_days = (next_after_ceil.date() - floor.date()).days
assert delta_days == count  # should be count, not count+1
```

---

## Bug 4: `format("hh")` / `format("h")` — midnight (hour=0) returns `"0"` not `"12"`

**Location**: `arrow/formatter.py`, `_format_token()`, tokens `"hh"` and `"h"`

**Trigger condition**:
Call `format("hh")` or `format("h")` on any Arrow with `hour == 0` (midnight).

The bug changes `0 < dt.hour < 13` to `0 <= dt.hour < 13`:
- With correct `0 < dt.hour`: hour=0 is not `> 0`, so falls to `abs(0-12) = 12` → "12"
- With buggy `0 <= dt.hour`: hour=0 satisfies condition, returns `dt.hour = 0` → "0"

For hour=12 (noon), both versions return 12 (condition: `0<=12<13` is True in both cases
since `12 < 13` and `12 > 0`... actually with buggy `0 <= 12 < 13` is True so returns 12,
same as correct). The bug only affects midnight (hour=0).

**Why default strategy is insufficient**:
Random hour generation (0-23) triggers at hour=0, which is 1/24 ≈ 4% probability.
But agents not specifically testing the `hh` token with hour=0 will miss this.

**Trigger probability with uniform hour sampling**: 1/24 ≈ 4.2%

**Minimum trigger input**:
```python
a = arrow.Arrow(2023, 1, 1, 0, 30)  # midnight
assert a.format("hh") == "12"       # should be "12", bug gives "00"
assert a.format("h")  == "12"       # should be "12", bug gives "0"
```

**Ground truth property**:
```python
a = arrow.Arrow(year, month, day, 0, minute)  # fix hour=0
hh = a.format("hh")
assert hh == "12"  # midnight in 12-hour format is always 12
```
