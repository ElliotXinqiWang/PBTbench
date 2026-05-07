# dateutil.rrule — Recurrence Rule

The `rrule` module implements RFC 2445 (iCalendar) recurrence rules for Python. It allows generating sequences of dates/datetimes based on flexible recurrence patterns.

## Quick Start

```python
from datetime import datetime
from dateutil.rrule import rrule, YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY, SECONDLY
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

# Every day for 5 days
list(rrule(DAILY, count=5, dtstart=datetime(2024, 1, 1)))

# Every month on the 15th for 12 months
list(rrule(MONTHLY, count=12, dtstart=datetime(2024, 1, 15)))
```

## Constructor

```python
rrule(freq, dtstart=None, interval=1, wkst=None, count=None, until=None,
      bysetpos=None, bymonth=None, bymonthday=None, byyearday=None,
      byeaster=None, byweekno=None, byweekday=None, byhour=None,
      byminute=None, bysecond=None, cache=False)
```

### Parameters

- **freq** (int): Frequency constant — one of `YEARLY`, `MONTHLY`, `WEEKLY`, `DAILY`, `HOURLY`, `MINUTELY`, `SECONDLY`.

- **dtstart** (datetime): The recurrence start. If not given, `datetime.now()` is used.

- **interval** (int): The interval between each frequency iteration. Default is 1. For example, with `MONTHLY` frequency and `interval=2`, the rule fires every other month.

- **count** (int): If given, the rule will generate at most `count` occurrences.

- **until** (datetime): If given, the rule will generate occurrences up to and including this date.

- **wkst** (int or weekday): The week start day. Default is `MO` (Monday). Affects `WEEKLY` frequency calculations.

- **bysetpos** (int or sequence of int): Filters occurrences by their position within the frequency period. For example, `bysetpos=1` selects the first occurrence, `bysetpos=-1` selects the last. **Valid range: [-366, -1] and [1, 366]** (0 is not valid). A yearly frequency can have up to 366 occurrences (leap year), so 366 is the maximum valid position.

- **bymonth** (int or sequence): Limits occurrences to specific months (1-12).

- **bymonthday** (int or sequence): Limits occurrences to specific days of the month (1-31, or negative for counting from month end).

- **byyearday** (int or sequence): Limits occurrences to specific days of the year (1-366, or negative).

- **byweekno** (int or sequence): Limits occurrences to specific ISO week numbers.

- **byweekday** (weekday or sequence): Limits occurrences to specific weekdays. Can use `MO`, `TU`, etc. With `MONTHLY` or `YEARLY` frequency, can specify nth occurrence like `MO(1)` for "first Monday".

- **byhour** (int or sequence): Limits occurrences to specific hours (0-23). When used with `HOURLY` frequency, the rule only generates occurrences at these hours. **Important**: When `gcd(interval, 24) > 1`, not all hours are reachable from a given start hour. The implementation filters `byhour` to only include reachable values; if no values are reachable, a `ValueError` is raised.

- **byminute** (int or sequence): Limits occurrences to specific minutes (0-59). Same reachability filtering applies with `MINUTELY` frequency when `gcd(interval, 60) > 1`.

- **bysecond** (int or sequence): Limits occurrences to specific seconds (0-59). Same reachability filtering applies with `SECONDLY` frequency.

## Frequency Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `YEARLY` | 0 | Once per year |
| `MONTHLY` | 1 | Once per month |
| `WEEKLY` | 2 | Once per week |
| `DAILY` | 3 | Once per day |
| `HOURLY` | 4 | Once per hour |
| `MINUTELY` | 5 | Once per minute |
| `SECONDLY` | 6 | Once per second |

## MONTHLY Frequency Behavior

The `MONTHLY` frequency advances by `interval` months at each step. When the accumulated month exceeds 12, the year is incremented accordingly:

- `month += interval`
- If `month > 12`, use `divmod(month, 12)` to compute the year increment and new month
- Special case: when the remainder is 0 (landing on December), the month is set to 12 and the year increment is adjusted (decremented by 1) to avoid over-counting

**Example**: Starting from January (month=1) with `interval=11`:
- `month = 1 + 11 = 12`
- `divmod(12, 12) = (1, 0)` → year += 1, month = 0
- Correction: month = 12, year -= 1 (still same year)
- Result: December of the same year (correct)

**Example**: Starting from March (month=3) with `interval=12`:
- `month = 3 + 12 = 15`
- `divmod(15, 12) = (1, 3)` → year += 1, month = 3
- Result: March of the next year (correct)

When the target month has fewer days than the source date's day, the day is clamped to the last day of the target month.

## BYHOUR/BYMINUTE/BYSECOND Reachability

When `HOURLY` frequency is combined with `byhour`, the implementation checks which hours are actually reachable given the interval. This uses the concept of coprimality:

- If `gcd(interval, 24) == 1`, all 24 hours are reachable from any start hour
- If `gcd(interval, 24) > 1` (e.g., `interval=4`, `gcd=4`), only `24/gcd = 6` distinct hours are reachable
- The reachable hours are those where `(hour - start_hour) % gcd == 0`
- Any `byhour` values that are NOT reachable are silently filtered out
- If all specified `byhour` values are unreachable, a `ValueError` is raised

The same logic applies to `byminute` with base 60 and `bysecond` with base 60.

**Example**: `HOURLY`, `interval=4`, `dtstart` at hour 1, `byhour=[1, 5, 9, 13, 17, 21]`:
- `gcd(4, 24) = 4`, reachable hours from 1: {1, 5, 9, 13, 17, 21}
- All specified byhour values are reachable → accepted
- Output: datetimes at hours 1, 5, 9, 13, 17, 21

**Example**: `HOURLY`, `interval=4`, `dtstart` at hour 0, `byhour=[1, 2, 3]`:
- `gcd(4, 24) = 4`, reachable hours from 0: {0, 4, 8, 12, 16, 20}
- None of [1, 2, 3] are reachable → `ValueError`

## bysetpos Parameter

The `bysetpos` parameter selects occurrences by their position within the frequency period's result set.

- Positive values count from the start: `bysetpos=1` is the first occurrence
- Negative values count from the end: `bysetpos=-1` is the last occurrence
- **Valid range**: integers in `[-366, -1]` or `[1, 366]`
- The value 0 is NOT valid and raises `ValueError`
- The maximum value 366 corresponds to a `YEARLY` frequency where a leap year has 366 days

**Example**: First and last weekday of each month:
```python
# First weekday of each month
rrule(MONTHLY, byweekday=(MO,TU,WE,TH,FR), bysetpos=1, count=3, dtstart=...)

# Last weekday of each month
rrule(MONTHLY, byweekday=(MO,TU,WE,TH,FR), bysetpos=-1, count=3, dtstart=...)
```

**Example**: 366th day of the year (valid for leap years):
```python
# The 366th occurrence in a yearly set — valid for leap years
rrule(YEARLY, byweekday=range(7), bysetpos=366, count=1, dtstart=datetime(2024,1,1))
```

## Iteration

An `rrule` object is iterable and also supports indexing and slicing:

```python
r = rrule(DAILY, count=365, dtstart=datetime(2024, 1, 1))

# Iterate
for dt in r:
    print(dt)

# Index
print(r[0])   # First occurrence
print(r[-1])  # Last occurrence

# Slice
print(r[:5])  # First 5 occurrences

# Count and between
print(r.count())
print(r.between(datetime(2024,3,1), datetime(2024,3,31)))
```

## rruleset

The `rruleset` combines multiple `rrule` objects, and supports explicit inclusion (`rdate`) and exclusion (`exrule`, `exdate`):

```python
from dateutil.rrule import rruleset, rrule, DAILY

rs = rruleset()
rs.rrule(rrule(DAILY, count=10, dtstart=datetime(2024, 1, 1)))
rs.exdate(datetime(2024, 1, 5))  # Exclude Jan 5
```

## rrulestr

Parse an RFC 2445 string into an `rrule` or `rruleset`:

```python
from dateutil.rrule import rrulestr
r = rrulestr("DTSTART:20240101\nRRULE:FREQ=DAILY;COUNT=5")
```
