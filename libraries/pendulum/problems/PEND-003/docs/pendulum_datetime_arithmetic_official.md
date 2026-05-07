# Pendulum DateTime Arithmetic Reference

**Pendulum version**: 3.2.0

Pendulum is a Python library that improves upon the standard `datetime` module by providing friendlier APIs for date/time manipulation, timezone handling, and duration arithmetic.

---

## Overview

Pendulum's `DateTime` class extends Python's built-in `datetime.datetime`. It provides:
- Fluent `add()` and `subtract()` methods for date/time arithmetic
- Automatic day clamping when adding months that result in dates beyond the last day of a month
- The `diff()` method that returns an `Interval` object for computing differences between dates
- Date properties like `day_of_year`, `day_of_week`, `week_of_year`

---

## DateTime.add()

```python
def add(
    self,
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: float = 0,
    microseconds: int = 0,
) -> DateTime:
```

Adds a duration to the DateTime instance. Returns a new `DateTime` object; the original is not modified.

**Month clamping**: When adding months, if the resulting day would exceed the number of days in the target month, the day is clamped to the last day of that month. The clamping uses the number of days in the **result month and result year** (including leap year status of the result year).

Examples:
```python
import pendulum

# Simple month addition
pendulum.datetime(2023, 1, 15).add(months=1)
# => DateTime(2023, 2, 15, 0, 0, 0, tzinfo=UTC)

# Month clamping: March 31 + 1 month = April 30
pendulum.datetime(2023, 3, 31).add(months=1)
# => DateTime(2023, 4, 30, 0, 0, 0, tzinfo=UTC)
# (April has only 30 days, so day is clamped to 30)

# Month clamping crossing a year boundary with leap year:
# October 31 + 4 months → February 2024 (2024 IS a leap year, so 29 days)
pendulum.datetime(2023, 10, 31).add(months=4)
# => DateTime(2024, 2, 29, 0, 0, 0, tzinfo=UTC)
# (The result year 2024 is a leap year, so February has 29 days)

# October 31 + 16 months → February 2026 (2026 is NOT a leap year, 28 days)
pendulum.datetime(2024, 10, 31).add(months=16)
# => DateTime(2026, 2, 28, 0, 0, 0, tzinfo=UTC)
# (The result year 2026 is not a leap year, so February has 28 days)

# Year crossing: December + 1 month = January of next year
pendulum.datetime(2023, 12, 15).add(months=1)
# => DateTime(2024, 1, 15, 0, 0, 0, tzinfo=UTC)

# November + 2 months = January of next year
pendulum.datetime(2023, 11, 15).add(months=2)
# => DateTime(2024, 1, 15, 0, 0, 0, tzinfo=UTC)

# Adding years
pendulum.datetime(2020, 2, 29).add(years=4)
# => DateTime(2024, 2, 29, 0, 0, 0, tzinfo=UTC)
# (2024 is a leap year, so Feb 29 is valid)
```

**Month normalization**: If `abs(months) > 11`, pendulum normalizes the months into years and remaining months before performing the arithmetic. For example, `months=13` is treated as `years=1, months=1`.

**Day-first addition order**: When both `months` (or `years`, `weeks`, `days`) and time components (`hours`, `minutes`, `seconds`) are provided, the date portion is computed first (handling month/year arithmetic and day clamping), then the time offset is added.

---

## DateTime.subtract()

```python
def subtract(
    self,
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: float = 0,
    microseconds: int = 0,
) -> DateTime:
```

Subtracts a duration from the DateTime instance. Equivalent to `add()` with negated arguments.

**Month clamping on subtraction**: Same as addition — the day is clamped to the last day of the **result month in the result year**.

Examples:
```python
import pendulum

# Simple month subtraction
pendulum.datetime(2023, 3, 15).subtract(months=1)
# => DateTime(2023, 2, 15, 0, 0, 0, tzinfo=UTC)

# Month clamping: March 31 - 1 month = February 28 (non-leap 2023)
pendulum.datetime(2023, 3, 31).subtract(months=1)
# => DateTime(2023, 2, 28, 0, 0, 0, tzinfo=UTC)

# March 31 - 1 month = February 29 (leap 2024)
pendulum.datetime(2024, 3, 31).subtract(months=1)
# => DateTime(2024, 2, 29, 0, 0, 0, tzinfo=UTC)
# (2024 is a leap year, February has 29 days)

# Year crossing backward: January - 1 month = December of previous year
pendulum.datetime(2024, 1, 15).subtract(months=1)
# => DateTime(2023, 12, 15, 0, 0, 0, tzinfo=UTC)

# February - 3 months = November of previous year
pendulum.datetime(2024, 2, 15).subtract(months=3)
# => DateTime(2023, 11, 15, 0, 0, 0, tzinfo=UTC)

# March - 4 months = November of previous year
pendulum.datetime(2024, 3, 15).subtract(months=4)
# => DateTime(2023, 11, 15, 0, 0, 0, tzinfo=UTC)
```

---

## Date.day_of_year

```python
@property
def day_of_year(self) -> int:
    """
    Returns the day of the year (1-366).
    """
```

Returns the ordinal day number within the current year. January 1 is day 1.

- In a **non-leap year** (365 days): January 1 = 1, December 31 = 365
- In a **leap year** (366 days): January 1 = 1, February 29 = 60, December 31 = 366

The leap year distinction affects days from **March 1 onwards**:
- In a non-leap year: March 1 = day 60
- In a leap year: March 1 = day 61 (because February has 29 days, not 28)

Examples:
```python
import pendulum

pendulum.date(2024, 1, 1).day_of_year    # => 1
pendulum.date(2024, 2, 29).day_of_year   # => 60  (leap year)
pendulum.date(2024, 3, 1).day_of_year    # => 61  (leap year, after Feb 29)
pendulum.date(2024, 12, 31).day_of_year  # => 366 (leap year)

pendulum.date(2023, 1, 1).day_of_year    # => 1
pendulum.date(2023, 2, 28).day_of_year   # => 59  (non-leap)
pendulum.date(2023, 3, 1).day_of_year    # => 60  (non-leap, after Feb 28)
pendulum.date(2023, 12, 31).day_of_year  # => 365 (non-leap)
```

---

## Interval and diff()

### DateTime.diff()

```python
def diff(
    self,
    dt: datetime | None = None,
    abs: bool = True,
) -> Interval:
```

Returns an `Interval` object representing the difference between two `DateTime` objects. If `dt` is None, it defaults to `DateTime.now()`. When `abs=True` (default), the result is always positive.

### Interval.in_months()

```python
def in_months(self) -> int:
    """
    Gives the duration of the Interval in full months.
    """
    return self.years * 12 + self.months
```

Returns the total number of complete months in the interval. Combines the years and months components.

Examples:
```python
import pendulum

d1 = pendulum.datetime(2023, 1, 15)
d2 = pendulum.datetime(2023, 4, 15)
iv = d1.diff(d2)
iv.in_months()  # => 3

# Interval spanning more than a year
d3 = pendulum.datetime(2021, 6, 1)
d4 = pendulum.datetime(2023, 9, 1)
iv2 = d3.diff(d4)
iv2.in_months()  # => 27 (2 years * 12 + 3 months)
```

### Precise month counting in Interval

Pendulum uses **precise calendar-based month counting** rather than simple 30-day approximations. The `months` component in an `Interval` tells you how many complete calendar months have elapsed.

**Full month boundary rule**: An interval from date D1 (in month M1) to date D2 (in month M2, M2 > M1 in the same year or M2 in a later year) counts as exactly N complete months if and only if D2.day >= D1.day. When D2.day < D1.day, the last partial month is counted as remaining days.

```python
import pendulum

# Exactly 1 month (same day of month)
pendulum.datetime(2023, 1, 15).diff(pendulum.datetime(2023, 2, 15)).in_months()  # => 1

# Not quite 1 month (day is earlier in the month)
pendulum.datetime(2023, 1, 15).diff(pendulum.datetime(2023, 2, 14)).months       # => 0

# One full month (when d2.day - d1.day == days_in_d2_month - days_in_prev_month)
# This handles the edge case of long months followed by short months:
# Jan 4 -> Feb 1 is exactly 1 full month (Jan has 31 days, Feb has 28 = 31-3 days,
# and 1 - 4 = -3 = 28 - 31, meaning exactly the "balance point")
pendulum.datetime(2023, 1, 4).diff(pendulum.datetime(2023, 2, 1)).in_months()    # => 1
```

---

## Leap Year Handling

Python and pendulum define a leap year as a year divisible by 4, except for century years which must be divisible by 400.

```python
import pendulum

# Check if a year is a leap year
pendulum.date(2024, 1, 1).is_leap_year()  # => True  (divisible by 4)
pendulum.date(2023, 1, 1).is_leap_year()  # => False
pendulum.date(2000, 1, 1).is_leap_year()  # => True  (divisible by 400)
pendulum.date(1900, 1, 1).is_leap_year()  # => False (divisible by 100 but not 400)
```

Leap year detection is critical for:
1. **Month clamping in `add()`/`subtract()`**: February in a leap year has 29 days
2. **`day_of_year` calculation**: Leap years have 366 days total, affecting day numbers from March 1 onward

---

## Date Properties Summary

| Property | Description | Range |
|----------|-------------|-------|
| `day_of_week` | Day of week (WeekDay enum) | 0=Monday ... 6=Sunday |
| `day_of_year` | Day number within the year | 1-366 |
| `week_of_year` | ISO week number | 1-53 |
| `days_in_month` | Number of days in the current month | 28-31 |
| `quarter` | Quarter of the year | 1-4 |
| `is_leap_year()` | Whether the current year is a leap year | bool |

---

## Duration class

`pendulum.Duration` extends Python's `timedelta` with named component access:

```python
d = pendulum.duration(years=1, months=6, days=3, hours=2)
d.years          # => 1
d.months         # => 6
d.remaining_days # => 3
d.hours          # => 2
d.total_seconds()
```

---

## Complete Add/Subtract Algorithm

The internal `add_duration()` helper performs these steps for month arithmetic:

1. **Normalize months**: If `abs(months) > 11`, convert excess to years
2. **Compute result year**: `year = dt.year + years`
3. **Compute result month**: `month = dt.month + months`
   - If `month > 12`: increment year by 1, subtract 12 from month
   - If `month < 1`: decrement year by 1, add 12 to month
4. **Clamp day**: `day = min(days_in_result_month(result_year), dt.day)`
   - The days in month is determined using the **result year's** leap year status
5. **Apply time delta**: add the remaining days/hours/minutes/seconds/microseconds

The clamp in step 4 ensures you never get an invalid date like February 30 or April 31.

---

## Add/Subtract Examples: Year Boundaries

```python
import pendulum

# Forward crossing (month overflow):
pendulum.datetime(2023, 12, 25).add(months=1)   # 2024-01-25
pendulum.datetime(2023, 11, 30).add(months=2)   # 2024-01-30
pendulum.datetime(2023, 10, 15).add(months=3)   # 2024-01-15
pendulum.datetime(2023, 10, 31).add(months=3)   # 2024-01-31

# Backward crossing (month underflow):
pendulum.datetime(2024, 1, 25).subtract(months=1)   # 2023-12-25
pendulum.datetime(2024, 2, 15).subtract(months=3)   # 2023-11-15
pendulum.datetime(2024, 3, 15).subtract(months=4)   # 2023-11-15

# Leap year transitions in month clamping:
pendulum.datetime(2023, 10, 31).add(months=4)   # 2024-02-29 (2024 is leap)
pendulum.datetime(2024, 10, 31).add(months=4)   # 2025-02-28 (2025 is not leap)
```

---

## Testing Considerations

When testing pendulum date arithmetic, consider:

1. **End-of-month dates** (28th-31st): these trigger day clamping
2. **Year boundaries**: adding/subtracting months that cross December/January
3. **Leap year February**: February 29 only exists in leap years (every 4 years)
4. **Leap year in the result year**: even if the *original* date is in a non-leap year,
   adding months might land in a leap year's February (and vice versa)

Key test patterns for month arithmetic:
```python
# Roundtrip property: adding N months then subtracting N months should return same date
# (with clamping caveat: if original day > days_in_result_month, the roundtrip is not exact)
dt = pendulum.datetime(2023, 1, 15)
assert dt.add(months=6).subtract(months=6) == dt  # True (day=15 survives all months)

# Year crossing property: month after year boundary is correct
pendulum.datetime(2023, 12, 15).add(months=1).month   # == 1 (January)
pendulum.datetime(2024, 1, 15).subtract(months=1).month  # == 12 (December)
```
