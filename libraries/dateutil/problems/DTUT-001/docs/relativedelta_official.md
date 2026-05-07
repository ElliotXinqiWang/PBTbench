# relativedelta - python-dateutil Documentation
# Source: https://dateutil.readthedocs.io/en/stable/relativedelta.html
# python-dateutil version: 2.9.0

## Class Definition

```python
class dateutil.relativedelta.relativedelta(
    dt1=None, dt2=None,
    years=0, months=0, days=0, leapdays=0, weeks=0,
    hours=0, minutes=0, seconds=0, microseconds=0,
    year=None, month=None, day=None, weekday=None,
    yearday=None, nlyearday=None,
    hour=None, minute=None, second=None, microsecond=None
)
```

## Overview

The `relativedelta` class applies adjustments to existing datetime objects. It can either represent a time interval or replace specific datetime components. Construction supports two approaches: comparing two datetime objects or using keyword arguments.

## Parameter Types

**Absolute Parameters** (singular form):
- `year`, `month`, `day`, `hour`, `minute`, `second`, `microsecond`
- These *replace* values in the original datetime rather than performing arithmetic

**Relative Parameters** (plural form):
- `years`, `months`, `weeks`, `days`, `hours`, `minutes`, `seconds`, `microseconds`
- Support negative values; perform arithmetic operations on the original datetime

**Special Parameters**:
- `weekday`: Weekday instances (MO, TU, etc.) with optional occurrence number
- `leapdays`: Additional days added if the result falls post-February in a leap year
- `yearday`, `nlyearday`: Set absolute day-of-year values

## Application Order

Attributes apply in this sequence:
1. Year
2. Month
3. Day
4. Hours
5. Minutes
6. Seconds
7. Microseconds
8. Weekday

## Month-End Behavior

When adding months crosses month boundaries with differing day counts, the result clamps to the target month's final day:

```python
date(2003, 1, 31) + relativedelta(months=+1)  # -> 2003-02-28
date(2003, 1, 31) + relativedelta(months=+2)  # -> 2003-03-31
date(2003, 5, 31) + relativedelta(months=-1)  # -> 2003-04-30
```

The same logic applies to leap year transitions:

```python
date(2000, 2, 29) + relativedelta(years=+1)  # -> 2001-02-28
```

The clamping uses the **last valid day** of the target month. For example, when January 31 advances by one month to February, the result is February 28 (or 29 in a leap year) — the last day of February — not February 27. Specifically, `days_in_month` (not `days_in_month - 1`) is used as the clamp ceiling.

## Methods

### normalized()

Returns a version using only integer values for relative attributes:

```python
relativedelta(days=1.5, hours=2).normalized()
# -> relativedelta(days=+1, hours=+14)
```

### weeks Property

Provides access to the weeks component of the relativedelta.

## Key Examples

**Next month plus one week**:
```python
NOW + relativedelta(months=+1, weeks=+1)
```

**Last Friday of month**:
```python
TODAY + relativedelta(day=31, weekday=FR(-1))
```

**Age calculation**:
```python
relativedelta(NOW, johnbirthday)
# -> relativedelta(years=+25, months=+5, days=+12, hours=+8, ...)
```

**One month before year end**:
```python
TODAY + relativedelta(yearday=1, months=-1)
```

**Next Monday**:
```python
TODAY + relativedelta(weekday=MO(+1))
```

**Last Monday of the month**:
```python
TODAY + relativedelta(day=31, weekday=MO(-1))
```
