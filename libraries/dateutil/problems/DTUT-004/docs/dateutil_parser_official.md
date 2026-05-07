# dateutil.parser — Official API Documentation

## Overview

`dateutil.parser` provides a flexible date/time string parser that can handle a wide
variety of date formats automatically. The main entry point is `parse()`.

## `parse(timestr, parserinfo=None, **kwargs)`

Parse a string into a `datetime.datetime` object.

```python
from dateutil.parser import parse
parse("2024-03-15")
parse("March 15, 2024")
parse("15 Mar 2024 10:30:00 AM")
```

### Parameters

- **timestr** (str): The string to parse.
- **parserinfo** (parserinfo, optional): Custom parser configuration.
- **default** (datetime, optional): Default datetime to use when fields are missing from
  the string. Fields not present in `timestr` are taken from this default. If not provided,
  defaults to `datetime.now()` with hour/min/sec/microsecond set to 0.
- **dayfirst** (bool, optional): If True, interprets the first value in ambiguous 3-integer
  date sequences as day. Default is False.
- **yearfirst** (bool, optional): If True, the first value in ambiguous 3-integer date
  sequences is interpreted as the year. Default is False. If both `dayfirst` and `yearfirst`
  are set, `yearfirst` is given precedence.
- **fuzzy** (bool, optional): Whether to allow fuzzy parsing, allowing for strings like
  "Today is 25 of March and we will need to wait 10 more days". Default is False.
- **fuzzy_with_tokens** (bool, optional): Like fuzzy, but returns a tuple containing the
  parsed datetime and a list of the tokens that were not recognized.
- **ignoretz** (bool, optional): If True, timezone information in the string is ignored.
- **tzinfos** (dict or callable, optional): Maps timezone name abbreviations to tzinfo
  objects or integer UTC offsets.

### AM/PM Conversion

When a time string includes AM or PM (12-hour clock format), the parser converts the
hour according to the following rules:

- `1:xx PM` → 13:xx (add 12 for PM hours 1–11)
- `2:xx PM` → 14:xx
- ...
- `11:xx PM` → 23:xx
- **`12:xx PM` → 12:xx (noon is 12:00 in 24-hour time)**
- `1:xx AM` → 1:xx (AM hours 1–11 stay the same)
- ...
- `11:xx AM` → 11:xx
- **`12:xx AM` → 0:xx (midnight is 0:00 in 24-hour time)**

**Property**: `parse("12:00 PM").hour == 12` (noon)
**Property**: `parse("12:00 AM").hour == 0` (midnight)
**Property**: `parse("1:00 PM").hour == 13`
**Property**: `parse("11:00 AM").hour == 11`

### Fractional Seconds (Microseconds)

Fractional seconds are parsed with microsecond precision (6 significant digits).

```
parse("12:00:00.1")      → microsecond = 100000
parse("12:00:00.12")     → microsecond = 120000
parse("12:00:00.123")    → microsecond = 123000
parse("12:00:00.1234")   → microsecond = 123400
parse("12:00:00.12345")  → microsecond = 123450
parse("12:00:00.123456") → microsecond = 123456
parse("12:00:00.999999") → microsecond = 999999
```

**Property**: The fractional part is left-justified to 6 characters with zeros,
then the first 6 characters are taken as the microsecond value.

**Property**: `parse(f"12:00:00.{us:06d}").microsecond == us` for any microsecond value.

### Default Date Filling and Month-End Clamping

When a field is missing from the string, it is taken from the `default` datetime.
For day field:
- If the string specifies month (and possibly year) but not day, the default day is used.
- **If the default day exceeds the number of days in the target month, the day is clamped
  to the last valid day of that month.**

```python
# January 31 as default; parsing February
default = datetime(2024, 1, 31)
parse("February 2024", default=default)
# → datetime(2024, 2, 29)  # Last day of Feb 2024 (leap year)
# NOT datetime(2024, 2, 28) — clamped to last day, not second-to-last

parse("April 2024", default=default)
# → datetime(2024, 4, 30)  # Last day of April
```

**Property**: If default.day > days_in_month(parsed_month, parsed_year),
the result day == days_in_month(parsed_month, parsed_year) (the last day).

### Year/Month/Day Disambiguation

For ambiguous date strings like "01/02/03", the parser uses heuristics and flags:

- **`yearfirst=True`**: The first token is interpreted as year (if the interpretation
  is consistent with valid month/day values). For "24/03/15" with yearfirst=True:
  year=24, month=3, day=15.
- **`dayfirst=True`**: The first token is the day.
- Default (both False): Month/day/year (US format).

**yearfirst logic (for 3 numeric tokens without explicit month string)**:

When `yearfirst=True` and the first token (potential year) is ≤ 31 (ambiguous),
the parser applies yearfirst when the second token (month) is ≤ 12 (valid month)
and the third token (day) is ≤ 31.

**Property**: `parse("24/03/15", yearfirst=True).month == 3`
**Property**: `parse("24/03/15", yearfirst=True).day == 15`

### Timezone Handling

Timezone abbreviations in the string (like "EST", "PST") require `tzinfos` mapping to be
interpreted correctly. Numeric offsets like "+05:30" are handled automatically.

```python
from dateutil.tz import gettz
parse("2024-03-15 10:00 EST", tzinfos={"EST": -18000})
parse("2024-03-15 10:00+05:30")
```
