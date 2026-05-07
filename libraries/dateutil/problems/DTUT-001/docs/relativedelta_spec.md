# python-dateutil relativedelta Behavioral Specification

## Overview

`relativedelta` is an enhanced date arithmetic type provided by python-dateutil, filling the gap left by the standard library's `timedelta`, which does not support month/year addition and subtraction.

```python
from dateutil.relativedelta import relativedelta
from datetime import date

d = date(2024, 3, 15)
result = d + relativedelta(months=2)   # 2024-05-15
result = d + relativedelta(years=1)    # 2025-03-15
```

## Core Parameters

| Parameter | Type | Description |
|---|---|---|
| `years` | int | Number of years to add/subtract |
| `months` | int | Number of months to add/subtract (-11 to +11) |
| `days` | int | Number of days to add/subtract |
| `weeks` | int | Number of weeks to add/subtract (converted to days) |
| `hours` | int | Number of hours to add/subtract |
| `minutes` | int | Number of minutes to add/subtract |
| `seconds` | int | Number of seconds to add/subtract |
| `microseconds` | int | Number of microseconds to add/subtract |

Note: `months` and `years` are computed first, then `days`/`hours` etc. are applied.

## Month-End Clamping Rule

**This is one of the most important semantics of relativedelta.**

When adding/subtracting months from a date, if the target month has fewer days than the source date's day value, the result date's day is clamped to the **last day of the target month**.

### Official Examples

```python
from dateutil.relativedelta import relativedelta
from datetime import date

# January has 31 days, February 2024 (leap year) has 29 days
date(2024, 1, 31) + relativedelta(months=1)
# => date(2024, 2, 29)   <- clamped to the last day of February (29)

# January has 31 days, February 2023 (non-leap year) has 28 days
date(2023, 1, 31) + relativedelta(months=1)
# => date(2023, 2, 28)   <- clamped to the last day of February (28)

# March has 31 days, April has 30 days
date(2024, 3, 31) + relativedelta(months=1)
# => date(2024, 4, 30)   <- clamped to the last day of April (30)

# Mid-month dates are unaffected
date(2024, 1, 15) + relativedelta(months=1)
# => date(2024, 2, 15)   <- no clamping needed

# Adding multiple months
date(2024, 1, 31) + relativedelta(months=3)
# => date(2024, 4, 30)   <- clamped to the last day of April (30)
```

### Formal Description of the Clamping Rule

Let `d` be the source date and `n` be the number of months to add. The result date's day is:

```
target_year, target_month = computed from d.year, d.month, n
days_in_target = calendar.monthrange(target_year, target_month)[1]
result_day = min(d.day, days_in_target)
```

That is: **result day = min(source day, days in target month)**, never exceeding the maximum number of days in the target month.

## Days Per Month Reference

| Month     | Non-Leap Year | Leap Year |
|-----------|---------------|-----------|
| January   | 31 | 31 |
| February  | 28 | 29 |
| March     | 31 | 31 |
| April     | 30 | 30 |
| May       | 31 | 31 |
| June      | 30 | 30 |
| July      | 31 | 31 |
| August    | 31 | 31 |
| September | 30 | 30 |
| October   | 31 | 31 |
| November  | 30 | 30 |
| December  | 31 | 31 |

## Leap Year Rules

Year `y` is a leap year if and only if:
- `y % 4 == 0` and `y % 100 != 0`, or
- `y % 400 == 0`

Examples: 2000, 2004, 2008, 2024 are leap years; 1900, 2023, 2025 are non-leap years.

`calendar.isleap(year)` checks this; `calendar.monthrange(year, month)[1]` returns the number of days in that month.

## Testable Properties

The following properties should hold for all valid inputs:

### P1: Month-End Clamping Precision

For any month-end date (day == last day of month) `d` and integer `n` (1 <= n <= 11):

```python
result = d + relativedelta(months=n)
_, days_in_target = calendar.monthrange(result.year, result.month)
assert result.day == min(d.day, days_in_target)
```

In other words, the result's day value should be exactly `min(source day, days in target month)`, no more and no less.

### P2: Monotonicity

If `d1 <= d2`, then `d1 + relativedelta(months=n) <= d2 + relativedelta(months=n)`.

### P3: Month and Year Correctness

The values of `result.month` and `result.year` should match the expected target month (unaffected by clamping):

```python
result = d + relativedelta(months=n)
expected_month = (d.month - 1 + n) % 12 + 1
expected_year = d.year + (d.month - 1 + n) // 12
assert result.month == expected_month
assert result.year == expected_year
```

## Differences from timedelta

`timedelta` only supports days and cannot directly add/subtract months. The month semantics of `relativedelta` are "calendar months", meaning:

```python
date(2024, 1, 31) + timedelta(days=31)
# => date(2024, 3, 2)   <- not the end of February! timedelta does not do month-end clamping

date(2024, 1, 31) + relativedelta(months=1)
# => date(2024, 2, 29)  <- relativedelta clamps to the last day of February
```

## API Reference

```python
from dateutil.relativedelta import relativedelta
from datetime import date, datetime

# Basic usage
rd = relativedelta(years=1, months=2, days=3)
result = date(2024, 1, 15) + rd

# Negative values (subtraction)
result = date(2024, 3, 31) + relativedelta(months=-1)
# => date(2024, 2, 29)  <- clamping rule also applies

# Difference between two dates
rd = relativedelta(date(2024, 3, 31), date(2024, 1, 31))
# => relativedelta(months=+2)
```
