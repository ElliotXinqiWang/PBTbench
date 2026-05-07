# Arrow Library — Formatting, Membership, and Span API Reference

**Version**: 1.4.0
**Module**: `arrow`

---

## Overview

Arrow is a Python library for working with dates and times. It provides a sensible,
human-friendly approach to creating, manipulating, formatting, and converting dates
and times. Arrow is fully aware and timezone-safe.

This document covers four key areas:
1. `format()` — flexible datetime string formatting
2. `is_between()` — inclusive/exclusive range membership
3. `span()` — timespan computation with frame count
4. `humanize()` — human-readable relative time descriptions

---

## 1. `format()` — Datetime String Formatting

### Signature

```python
Arrow.format(fmt: str = "YYYY-MM-DD HH:mm:ssZZ", locale: str = "en-us") -> str
```

Returns a string representation of the Arrow object formatted according to `fmt`.

### Supported Format Tokens

#### Year
| Token | Example | Description |
|-------|---------|-------------|
| `YYYY` | `2023` | 4-digit year |
| `YY`   | `23`   | 2-digit year |

#### Month
| Token | Example | Description |
|-------|---------|-------------|
| `MMMM` | `June`  | Full month name |
| `MMM`  | `Jun`   | Abbreviated month name |
| `MM`   | `06`    | Zero-padded month number |
| `M`    | `6`     | Month number |

#### Day of Month
| Token | Example | Description |
|-------|---------|-------------|
| `DDDD` | `166`  | Zero-padded day of year |
| `DDD`  | `166`  | Day of year |
| `DD`   | `15`   | Zero-padded day of month |
| `D`    | `15`   | Day of month |
| `Do`   | `15th` | Ordinal day of month |

#### Day of Week
| Token | Example | Description |
|-------|---------|-------------|
| `dddd` | `Thursday` | Full weekday name |
| `ddd`  | `Thu`      | Abbreviated weekday name |
| `d`    | `4`        | ISO weekday number (1=Mon, 7=Sun) |

#### Hour
| Token | Example | Description |
|-------|---------|-------------|
| `HH` | `14` | Zero-padded 24-hour clock (00–23) |
| `H`  | `14` | 24-hour clock without padding |
| `hh` | `02` | Zero-padded **12-hour clock** (01–12) |
| `h`  | `2`  | 12-hour clock without padding |

**12-hour clock semantics (`hh` and `h`)**:
- Hours 1–11 AM: displayed as 1–11
- Hour 12 (noon): displayed as **12**
- Hour 0 (midnight): displayed as **12** (12:xx AM)
- Hours 13–23 (1 PM–11 PM): displayed as 1–11 (hour − 12)

The 12-hour format maps as follows:

| 24-hour (`HH`) | 12-hour (`hh`) |
|----------------|----------------|
| `00` (midnight) | `12` |
| `01` | `01` |
| `11` | `11` |
| `12` (noon) | `12` |
| `13` | `01` |
| `23` | `11` |

#### Minute / Second
| Token | Example | Description |
|-------|---------|-------------|
| `mm` | `30` | Zero-padded minute |
| `m`  | `30` | Minute |
| `ss` | `45` | Zero-padded second |
| `s`  | `45` | Second |

#### Sub-second
| Token | Example | Description |
|-------|---------|-------------|
| `SSSSSS` | `500000` | Microsecond (6 digits) |
| `SSSSS`  | `50000`  | 100-nanosecond (5 digits) |
| `SSSS`   | `5000`   | 10-microsecond (4 digits) |
| `SSS`    | `500`    | Millisecond (3 digits) |
| `SS`     | `50`     | 10-millisecond (2 digits) |
| `S`      | `5`      | 100-millisecond (1 digit) |

#### Timezone
| Token | Example | Description |
|-------|---------|-------------|
| `ZZZ` | `UTC`   | Timezone abbreviation |
| `ZZ`  | `+00:00`| UTC offset with colon |
| `Z`   | `+0000` | UTC offset without colon |

#### Meridiem
| Token | Example | Description |
|-------|---------|-------------|
| `a` | `am` / `pm` | Lowercase meridiem indicator |
| `A` | `AM` / `PM` | Uppercase meridiem indicator |

#### Unix Timestamps
| Token | Example | Description |
|-------|---------|-------------|
| `X` | `1686830400.5` | Unix timestamp in seconds (float) |
| `x` | `1686830400500000` | Unix timestamp in **microseconds** (integer) |

#### ISO Week Date (`W` token)
| Token | Example | Description |
|-------|---------|-------------|
| `W` | `2023-W24-4` | ISO 8601 week date |

The `W` token formats a date as `YYYY-Www-D`, where:
- `YYYY` is the ISO week-numbering year (may differ from calendar year near year boundaries)
- `ww` is the zero-padded ISO week number (01–53)
- `D` is the **ISO weekday number: 1=Monday, 2=Tuesday, ..., 7=Sunday**

**Important**: The weekday in the `W` token uses ISO 8601 weekday numbering (1-indexed,
1=Monday through 7=Sunday), NOT Python's `weekday()` method (0-indexed, 0=Monday through 6=Sunday).

Examples:
```python
arrow.Arrow(2023, 1, 2).format("W")   # Monday → "2023-W01-1"
arrow.Arrow(2023, 1, 7).format("W")   # Saturday → "2023-W01-6"
arrow.Arrow(2023, 1, 8).format("W")   # Sunday → "2023-W01-7"
```

#### Literal Text
Enclose text in square brackets to prevent token interpretation:
```python
arrow.Arrow(2023, 6, 15).format("[Today is] MMMM Do")  # "Today is June 15th"
```

---

## 2. `is_between()` — Range Membership

### Signature

```python
Arrow.is_between(
    start: Arrow,
    end: Arrow,
    bounds: str = "()"
) -> bool
```

Returns `True` if the Arrow object falls within the range `[start, end]` according
to the bounds specification.

### `bounds` Parameter

A 2-character string specifying endpoint inclusion:

| bounds | Meaning | Condition |
|--------|---------|-----------|
| `"()"` | Open interval (exclusive both) | `start < target < end` |
| `"[)"` | Left-closed, right-open | `start <= target < end` |
| `"(]"` | Left-open, right-closed | `start < target <= end` |
| `"[]"` | Closed interval (inclusive both) | `start <= target <= end` |

**Default is `"()"`** (exclusive on both ends).

### Boundary Semantics

The bounds control whether the target equals `start` or `end`:

- `"["` (left bracket): `start` IS included → `target == start` returns `True`
- `"("` (left paren): `start` is NOT included → `target == start` returns `False`
- `"]"` (right bracket): `end` IS included → `target == end` returns `True`
- `")"` (right paren): `end` is NOT included → `target == end` returns `False`

### Examples

```python
start = arrow.get("2013-05-05")
end   = arrow.get("2013-05-08")

arrow.get("2013-05-07").is_between(start, end)        # True  (default "()")
arrow.get("2013-05-08").is_between(start, end, "[]")  # True  (inclusive end)
arrow.get("2013-05-08").is_between(start, end, "[)")  # False (exclusive end)
arrow.get("2013-05-05").is_between(start, end, "[)")  # True  (inclusive start)
arrow.get("2013-05-05").is_between(start, end, "()")  # False (exclusive start)
```

### Key Invariants

1. For `"[)"` bounds: `start.is_between(start, end, "[)") == True` and `end.is_between(start, end, "[)") == False`
2. For `"(]"` bounds: `start.is_between(start, end, "(]") == False` and `end.is_between(start, end, "(]") == True`
3. For `"[]"` bounds: both endpoints return `True`
4. For `"()"` bounds: both endpoints return `False`

---

## 3. `span()` — Timespan Computation

### Signature

```python
Arrow.span(
    frame: str,
    count: int = 1,
    bounds: str = "[)",
    exact: bool = False,
    week_start: int = 1,
) -> Tuple[Arrow, Arrow]
```

Returns a tuple `(floor, ceil)` representing the timespan of the Arrow object in
the given timeframe.

### `frame` Parameter

Supported values: `"year"`, `"quarter"`, `"month"`, `"week"`, `"day"`, `"hour"`,
`"minute"`, `"second"`, `"microsecond"` (and their plural forms).

### `count` Parameter

**Default: `1`**

The number of frames to span. A count of `N` means the span covers exactly `N`
consecutive complete frames starting from the floor of the current frame.

```python
a = arrow.Arrow(2023, 3, 15, 10, 30)

a.span("day")           # one day: 2023-03-15 00:00:00 to 23:59:59.999999
a.span("day", count=2)  # two days: 2023-03-15 00:00:00 to 2023-03-16 23:59:59.999999
a.span("day", count=3)  # three days: 2023-03-15 00:00:00 to 2023-03-17 23:59:59.999999
```

**Key invariant for count=N**: The duration of `(ceil + 1 microsecond) - floor` must
equal exactly `N` frame-durations. For example:
- `span("day", count=N)`: `ceil + 1us - floor == timedelta(days=N)`
- `span("hour", count=N)`: `ceil + 1us - floor == timedelta(hours=N)`

### `bounds` Parameter

Controls endpoint inclusion (same syntax as `is_between()`). Default is `"[)"`.

```python
a.span("day", bounds="[]")  # includes both endpoints
a.span("day", bounds="[)")  # default: includes start, excludes end
a.span("day", bounds="()")  # excludes both endpoints
```

### `exact` Parameter

If `True`, the span starts exactly at the Arrow's time (not floored) and the end
is truncated to not extend beyond the natural period end.

### Examples

```python
>>> arrow.utcnow().span("hour")
(<Arrow [2013-05-09T03:00:00+00:00]>, <Arrow [2013-05-09T03:59:59.999999+00:00]>)

>>> arrow.utcnow().span("day")
(<Arrow [2013-05-09T00:00:00+00:00]>, <Arrow [2013-05-09T23:59:59.999999+00:00]>)

>>> arrow.utcnow().span("day", count=2)
(<Arrow [2013-05-09T00:00:00+00:00]>, <Arrow [2013-05-10T23:59:59.999999+00:00]>)

>>> arrow.utcnow().span("day", bounds="[]")
(<Arrow [2013-05-09T00:00:00+00:00]>, <Arrow [2013-05-10T00:00:00+00:00]>)
```

---

## 4. `humanize()` — Human-Readable Relative Time

### Signature

```python
Arrow.humanize(
    other: Union[Arrow, datetime, None] = None,
    locale: str = "en-us",
    only_distance: bool = False,
    granularity: Union[str, List[str]] = "auto"
) -> str
```

Returns a localized, human-readable representation of the relative difference in time
between the Arrow object and `other` (defaults to now).

### `other` Parameter

The reference time to compare against. Defaults to the current time in the Arrow
object's timezone.

### `granularity` Parameter

Controls the precision and format of the output:

**Single string** (one granularity level):

| Value | Example output |
|-------|----------------|
| `"auto"` (default) | `"2 hours ago"`, `"in 3 days"` |
| `"second"` | `"in 45 seconds"` |
| `"minute"` | `"in 30 minutes"` |
| `"hour"` | `"in 2 hours"` |
| `"day"` | `"in 3 days"` |
| `"week"` | `"in 2 weeks"` |
| `"month"` | `"in 3 months"` |
| `"quarter"` | `"in 2 quarters"` |
| `"year"` | `"in 2 years"` |

**List of strings** (multiple granularity levels):

When `granularity` is a list, the output decomposes the time difference into
multiple components. The components are ordered from largest to smallest unit
and joined with "and":

```python
earlier = arrow.Arrow(2023, 1, 1, 10, 0, 0)
later   = arrow.Arrow(2023, 1, 1, 12, 30, 0)

later.humanize(earlier, granularity=["hour", "minute"])
# "in 2 hours and 30 minutes"

later.humanize(earlier, granularity=["day", "hour", "minute"])
# "in 0 days 2 hours and 30 minutes"
```

The decomposition works by successively extracting the larger units from the
remaining time difference. For a difference of 9030 seconds with
`granularity=["hour", "minute", "second"]`:
- Hours: `floor(9030 / 3600) = 2` hours, remainder = `9030 % 3600 = 1830` seconds
- Minutes: `floor(1830 / 60) = 30` minutes, remainder = `1830 % 60 = 30` seconds
- Seconds: 30 seconds
- Result: "in 2 hours and 30 minutes and 30 seconds"

### `only_distance` Parameter

If `True`, returns only the distance without "in" or "ago":

```python
earlier.humanize(later, only_distance=True)  # "2 hours"
```

### Auto Granularity Thresholds

When `granularity="auto"`, the output transitions between units at these thresholds:

| Threshold | Output |
|-----------|--------|
| < 10 seconds | "just now" |
| < 45 seconds | "X seconds ago/in" |
| < 90 seconds | "a minute ago/in" |
| < 45 minutes | "X minutes ago/in" |
| < 90 minutes | "an hour ago/in" |
| < 22 hours | "X hours ago/in" |
| < 36 hours | "a day ago/in" |
| < 26 days | "X days ago/in" |
| < 1 month | "a week ago/in" |
| < 1 year | "X months ago/in" |
| < 18 months | "a year ago/in" |
| 18+ months | "X years ago/in" |

---

## 5. `floor()` and `ceil()`

### Signatures

```python
Arrow.floor(frame: str) -> Arrow
Arrow.ceil(frame: str) -> Arrow
```

`floor()` returns the start of the given timeframe. `ceil()` returns the end.

```python
a = arrow.Arrow(2023, 6, 15, 14, 30, 45)
a.floor("day")   # Arrow [2023-06-15T00:00:00+00:00]
a.ceil("day")    # Arrow [2023-06-15T23:59:59.999999+00:00]
a.floor("month") # Arrow [2023-06-01T00:00:00+00:00]
a.ceil("month")  # Arrow [2023-06-30T23:59:59.999999+00:00]
```

These are equivalent to `span(frame)[0]` and `span(frame)[1]` respectively.

---

## 6. `shift()` — Date Arithmetic

```python
Arrow.shift(**kwargs) -> Arrow
```

Returns a new Arrow object with the given time fields shifted. Accepts keyword
arguments corresponding to relativedelta parameters:

```python
a = arrow.Arrow(2023, 6, 15)
a.shift(days=1)      # 2023-06-16
a.shift(months=-1)   # 2023-05-15
a.shift(years=2)     # 2025-06-15
a.shift(hours=3, minutes=30)  # 2023-06-15T03:30:00
```

Supported kwargs: `years`, `months`, `weeks`, `days`, `hours`, `minutes`,
`seconds`, `microseconds`, `quarters`.

---

## 7. Property Reference

| Property | Type | Description |
|----------|------|-------------|
| `year` | int | Calendar year |
| `month` | int | Calendar month (1–12) |
| `day` | int | Day of month (1–31) |
| `hour` | int | Hour (0–23) |
| `minute` | int | Minute (0–59) |
| `second` | int | Second (0–59) |
| `microsecond` | int | Microsecond (0–999999) |
| `week` | int | ISO week number |
| `quarter` | int | Calendar quarter (1–4) |
| `tzinfo` | tzinfo | Timezone info |
| `int_timestamp` | int | Unix timestamp (integer seconds) |
| `float_timestamp` | float | Unix timestamp (float seconds) |

---

## 8. Comparison and Operators

Arrow objects support standard comparison operators: `<`, `<=`, `==`, `!=`, `>=`, `>`.

Arithmetic with `timedelta` is supported:
```python
a = arrow.utcnow()
b = a + timedelta(days=3)
c = a - timedelta(hours=2)
```

---

## 9. Common Usage Patterns

```python
import arrow

# Create
now = arrow.utcnow()
a = arrow.Arrow(2023, 6, 15, 10, 30, 0)

# Format
print(a.format("YYYY-MM-DD"))         # 2023-06-15
print(a.format("hh:mm A"))            # 10:30 AM
print(a.format("W"))                  # ISO week date like "2023-W24-4"

# Range membership
start = arrow.Arrow(2023, 1, 1)
end   = arrow.Arrow(2023, 12, 31)
print(a.is_between(start, end, "[)"))  # True if start <= a < end

# Span
floor, ceil = a.span("month")          # whole month containing 'a'
floor, ceil = a.span("day", count=7)  # 7-day span starting at floor of 'a'

# Humanize
earlier = a.shift(hours=-2)
print(a.humanize(earlier))                              # "in 2 hours"
print(a.humanize(earlier, granularity=["hour", "minute"])) # "in 2 hours and 0 minutes"
```
