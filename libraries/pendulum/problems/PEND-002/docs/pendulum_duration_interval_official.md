# Pendulum Duration & Interval API Reference

## Overview

Pendulum is a Python package that provides a drop-in replacement for the standard `datetime` module. It offers a more intuitive and complete API for working with dates, times, durations, and time intervals.

## Duration

The `Duration` class extends Python's `timedelta` with richer component-based access and arithmetic.

### Creating Durations

```python
import pendulum

d = pendulum.duration(days=5, hours=3, minutes=30, seconds=15)
d = pendulum.duration(weeks=2, days=3)
d = pendulum.duration(years=1, months=6)
d = pendulum.duration(seconds=3661)  # 1 hour, 1 minute, 1 second
```

**Parameters**: `years`, `months`, `weeks`, `days`, `hours`, `minutes`, `seconds`, `microseconds`, `milliseconds`

**Internal normalization**: The Duration class normalizes the input into internal components:
- `_years`: years component (as given)
- `_months`: months component (as given)
- `_weeks`: total weeks from time-based components (days/hours/minutes/seconds)
- `_remaining_days`: leftover days after extracting weeks (0-6)
- `_days`: total days from time-based components (`_weeks * 7 + _remaining_days`)
- `_seconds`: sub-day seconds component

### Component Properties

| Property | Description | Range |
|----------|-------------|-------|
| `.years` | Years component | any int |
| `.months` | Months component | any int |
| `.weeks` | Weeks from total days | any int |
| `.remaining_days` | Days remaining after weeks | 0-6 |
| `.hours` | Hours from sub-day seconds | 0-23 |
| `.minutes` | Minutes from sub-day seconds | 0-59 |
| `.remaining_seconds` | Seconds remaining after hours and minutes | 0-59 |
| `.microseconds` | Microseconds component | 0-999999 |

**Component decomposition invariant**: The sub-day seconds are decomposed as:
```
hours * 3600 + minutes * 60 + remaining_seconds == abs(_seconds)
```

And the total days are decomposed as:
```
weeks * 7 + remaining_days == abs(_days)
```

### Total Methods

| Method | Description |
|--------|-------------|
| `.total_seconds()` | Total duration in seconds (float) |
| `.total_minutes()` | Total duration in minutes (float) |
| `.total_hours()` | Total duration in hours (float) |
| `.total_days()` | Total duration in days (float) |
| `.total_weeks()` | Total duration in weeks (float) |

### Conversion Methods

| Method | Description |
|--------|-------------|
| `.in_seconds()` | Total full seconds (int) |
| `.in_minutes()` | Total full minutes (int) |
| `.in_hours()` | Total full hours (int) |
| `.in_days()` | Total full days (int) |
| `.in_weeks()` | Total full weeks (int) |
| `.in_words()` | Human-readable string |

### Arithmetic Operations

Duration supports standard arithmetic:

```python
d1 = pendulum.duration(hours=2)
d2 = pendulum.duration(hours=3)

d1 + d2      # Duration of 5 hours
d1 - d2      # Duration of -1 hour
-d1          # Negated duration (-2 hours)
d1 * 3       # Duration of 6 hours
d1 / 2       # Duration of 1 hour
```

**Negation semantics**: For any Duration `d`, the following must hold:
- `d + (-d)` equals a zero duration (total_seconds == 0)
- `(-d).total_seconds() == -d.total_seconds()`
- All components are negated independently

### The `.invert` Property

```python
d = pendulum.duration(hours=-2)
d.invert  # True (duration is negative)
```

## Interval (Period)

The `Interval` class (also known as Period in earlier versions) represents the difference between two specific datetime points. It extends Duration and adds start/end awareness.

### Creating Intervals

```python
import pendulum

start = pendulum.datetime(2020, 1, 1)
end = pendulum.datetime(2021, 3, 15)

# Via subtraction
iv = end - start

# Via constructor
iv = pendulum.interval(start, end)

# Absolute interval (always positive)
iv = pendulum.interval(start, end, absolute=True)
```

### Interval Properties

| Property | Description |
|----------|-------------|
| `.start` | Start datetime |
| `.end` | End datetime |
| `.years` | Full years in the interval |
| `.months` | Remaining months (0-11) |
| `.weeks` | Weeks from remaining days |
| `.remaining_days` | Days remaining after weeks |
| `.hours` | Hours component |
| `.minutes` | Minutes component |

### Interval Calculation Methods

| Method | Description |
|--------|-------------|
| `.in_years()` | Full years |
| `.in_months()` | Total months (years * 12 + months) |
| `.in_weeks()` | Total full weeks |
| `.in_days()` | Total days |

**`in_months()` semantics**: Returns `years * 12 + months`, where:
- `years` is the number of full years in the interval
- `months` is the remaining months after extracting full years (0-11)

For example:
```python
start = pendulum.datetime(2020, 1, 1)
end = pendulum.datetime(2021, 3, 1)
iv = end - start

iv.years      # 1
iv.months     # 2
iv.in_months()  # 14 (= 1 * 12 + 2)
```

### Interval Iteration

```python
start = pendulum.datetime(2023, 1, 1)
end = pendulum.datetime(2023, 1, 5)
iv = pendulum.interval(start, end)

# Iterate by days (default)
for dt in iv:
    print(dt)

# Iterate by custom unit
for dt in iv.range('hours', 6):
    print(dt)
```

### Containment Check

```python
mid = pendulum.datetime(2023, 6, 15)
mid in iv  # True if start <= mid <= end
```

## Key Relationships

1. **Duration negation identity**: `d + (-d)` must be zero for any Duration
2. **Component reconstruction**: `hours * 3600 + minutes * 60 + remaining_seconds == abs(_seconds)`
3. **Days decomposition**: `weeks * 7 + remaining_days == abs(_days)`
4. **Interval months**: `in_months() == years * 12 + months`
5. **Duration total_seconds symmetry**: `(-d).total_seconds() == -d.total_seconds()`
