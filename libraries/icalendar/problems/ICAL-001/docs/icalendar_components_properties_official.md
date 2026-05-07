# icalendar Library — Components and Properties Reference

## Overview

The `icalendar` library (version 7.0.3) is a Python parser and generator for iCalendar
data as defined in RFC 5545. It provides a standards-compliant implementation for
creating, parsing, and manipulating calendar data including events, todos, journals,
free/busy information, and recurrence rules.

## Core Concepts

### Components

iCalendar data is organized into components (VCALENDAR, VEVENT, VTODO, VJOURNAL,
VFREEBUSY, VTIMEZONE). Each component contains properties and may contain
subcomponents.

```python
from icalendar import Calendar, Event
from datetime import datetime, date, timedelta, timezone

# Create a calendar with an event
cal = Calendar()
cal.add('prodid', '-//My App//EN')
cal.add('version', '2.0')

event = Event()
event.add('summary', 'Meeting')
event.add('dtstart', datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc))
cal.add_component(event)
```

### Serialization and Parsing

Components can be serialized to iCalendar format and parsed back:

```python
# Serialize
ical_bytes = cal.to_ical()

# Parse
cal2 = Calendar.from_ical(ical_bytes)
```

**Key invariant**: `Calendar.from_ical(cal.to_ical())` should produce a component
that is semantically equivalent to the original. This roundtrip property is
fundamental to the library's correctness.

## Property Types

### TEXT (vText)

Text values are the most common property type. Per RFC 5545 Section 3.3.11,
TEXT values require escaping of special characters:

- Backslash (`\`) must be escaped as `\\`
- Semicolon (`;`) must be escaped as `\;`
- Comma (`,`) must be escaped as `\,`
- Newline must be escaped as `\n` or `\N`

**The order of escaping operations is critical** to avoid double-escaping.
Backslashes must be escaped before semicolons and commas, because escaping
semicolons/commas introduces new backslashes that should not be re-escaped.

```python
event.add('summary', 'Meeting; Room A, Building 1')
# Serializes as: SUMMARY:Meeting\; Room A\, Building 1
```

The unescaping process reverses these operations in the opposite order.

### DATE and DATE-TIME

Date properties use the format `YYYYMMDD` (8 digits).
DateTime properties use the format `YYYYMMDDTHHMMSS` (15 characters) with
optional `Z` suffix for UTC (16 characters).

```python
event.add('dtstart', date(2024, 1, 15))        # DATE: 20240115
event.add('dtstart', datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc))  # DATE-TIME: 20240115T100000Z
```

### VALUE Parameter

The VALUE parameter specifies the value type of a property. When adding
properties with Python native types, the library automatically infers the
VALUE parameter:

- **All items are `date` (not `datetime`)**: VALUE=DATE is set
- **All items are `time`**: VALUE=TIME is set
- **Mixed or other types**: No VALUE parameter is inferred

This inference applies when passing lists of values to date-related
properties like RDATE and EXDATE.

```python
# List of pure dates — VALUE=DATE is automatically set
event.add('rdate', [date(2024, 1, 15), date(2024, 2, 15)])
# Output: RDATE;VALUE=DATE:20240115,20240215

# List of datetimes — no VALUE parameter needed (DATE-TIME is default)
event.add('rdate', [datetime(2024, 1, 15, 10, 0), datetime(2024, 2, 15, 10, 0)])
# Output: RDATE:20240115T100000,20240215T100000
```

**Important**: When a list contains mixed types (both `date` and `datetime`),
the VALUE parameter must reflect the actual content. Setting VALUE=DATE when
the list contains datetimes would cause loss of time information during
serialization.

### DURATION (vDuration)

Duration values follow ISO 8601 format:

```
dur-value  = (["+"] / "-") "P" (dur-date / dur-time / dur-week)
dur-date   = dur-day [dur-time]
dur-time   = "T" (dur-hour / dur-minute / dur-second)
```

Examples:
- `P15DT5H0M20S` — 15 days, 5 hours, 0 minutes, 20 seconds
- `P7W` — 7 weeks
- `PT2H30M` — 2 hours 30 minutes
- `-PT23H` — negative 23 hours

### PERIOD (vPeriod)

A period of time can be specified in two formats:

1. **Explicit format**: `datetime/datetime` — start and end times
2. **Duration format**: `datetime/duration` — start time and duration

```python
from icalendar.prop import vPeriod

# Duration format
period1 = vPeriod((
    datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
    timedelta(hours=2)
))
# Serializes as: 20240101T100000Z/PT2H

# Explicit format
period2 = vPeriod((
    datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
    datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
))
# Serializes as: 20240101T100000Z/20240101T120000Z
```

**Key property**: The serialization format must match the creation format.
A period created with a duration should serialize with the duration format
(containing `P` prefix in the second part), and a period created with an
explicit end time should serialize with two datetimes. This distinction
matters for interoperability with other calendar applications.

The `by_duration` attribute indicates which format was used to create the period.

### RECUR (vRecur)

Recurrence rules define repeating patterns per RFC 5545 Section 3.3.10.

```python
from icalendar.prop import vRecur

# Parse from iCal string
rule = vRecur.from_ical('FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=10')

# Serialize back
ical = rule.to_ical()
# Output: b'FREQ=WEEKLY;COUNT=10;BYDAY=MO,WE,FR'
```

**RRULE format rules**:
- Key-value pairs are separated by semicolons: `KEY1=VALUE1;KEY2=VALUE2`
- Multiple values within a field are separated by commas: `BYDAY=MO,WE,FR`
- FREQ should appear first for maximum compatibility (Mac iCal requirement)

**Multi-value fields** (values separated by commas within a field):
- BYSECOND, BYMINUTE, BYHOUR — time components
- BYDAY — day of week (MO, TU, WE, TH, FR, SA, SU), optionally with position prefix (1MO, -1FR)
- BYMONTHDAY — day of month (1-31, negative values allowed)
- BYYEARDAY — day of year (1-366, negative values allowed)
- BYWEEKNO — week number (1-53, negative values allowed)
- BYMONTH — month (1-12)
- BYSETPOS — occurrence within set

**Single-value fields** (exactly one value):
- FREQ — frequency (SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY)
- UNTIL — end date/time
- COUNT — number of occurrences
- INTERVAL — interval between occurrences
- WKST — week start day

**Roundtrip property**: `vRecur.from_ical(vRecur(rule).to_ical().decode())` should
produce an equivalent recurrence rule with all values preserved.

### CATEGORIES (vCategory)

Categories are comma-separated text values with special escaping:

```python
event.add('categories', ['Work', 'Personal, Important', 'Fun; Games'])
# Serializes as: CATEGORIES:Work,Personal\, Important,Fun\; Games
```

Commas within category names are escaped with backslash.

### RDATE and EXDATE

Recurrence dates (RDATE) and exception dates (EXDATE) support lists of
date or datetime values:

```python
# Add multiple exclusion dates
event.add('exdate', [date(2024, 1, 15), date(2024, 2, 15)])
# Serializes as: EXDATE;VALUE=DATE:20240115,20240215

# Add multiple recurrence dates with times
event.add('rdate', [
    datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
    datetime(2024, 2, 15, 10, 0, tzinfo=timezone.utc)
])
# Serializes as: RDATE:20240115T100000Z,20240215T100000Z
```

These properties can hold lists of values separated by commas in a single
property line.

## Component Methods

### add(name, value, parameters=None, encode=True)

Add a property to a component. The `value` can be a Python native type
(str, date, datetime, timedelta, list, etc.) or an icalendar property type.

When `value` is a list:
- For RDATE, EXDATE, CATEGORIES: the list is passed as a whole to the encoder
  (supporting comma-separated multi-value lines)
- For other properties: each item is individually encoded

### to_ical(sorted=True)

Serialize the component to iCalendar bytes format.

### from_ical(st, multiple=False)

Parse iCalendar data from a string or bytes into component instances.

### walk(name=None, select=lambda _: True)

Recursively traverse component and subcomponents, returning matching components.

```python
events = calendar.walk('VEVENT')
todos = calendar.walk('VTODO')
```

## FREEBUSY Component

The VFREEBUSY component uses PERIOD values for the FREEBUSY property:

```python
from icalendar import FreeBusy

fb = FreeBusy()
fb.add('freebusy', [
    vPeriod((datetime(2024,1,1,10,0, tzinfo=timezone.utc), timedelta(hours=1))),
    vPeriod((datetime(2024,1,1,14,0, tzinfo=timezone.utc), timedelta(hours=2)))
])
```

## Content Line Folding

Per RFC 5545, content lines SHOULD NOT be longer than 75 octets. Long lines
are folded by inserting CRLF followed by a single space or tab character.

```
DESCRIPTION:This is a long description that will be folded to
 fit within the 75 octet limit specified by the RFC.
```

Unfolding reverses this by removing CRLF followed by whitespace.

## Error Handling

Components can be configured to ignore parsing exceptions:

```python
class MyComponent(Component):
    ignore_exceptions = True
```

When `ignore_exceptions` is True, malformed properties are stored as `vBroken`
values and errors are recorded in `component.errors`.

## Timezone Handling

The library supports timezone-aware datetimes using either `zoneinfo` (Python 3.9+)
or `pytz`:

```python
from zoneinfo import ZoneInfo

tz = ZoneInfo("America/New_York")
event.add('dtstart', datetime(2024, 1, 15, 10, 0, tzinfo=tz))
# Serializes with TZID parameter: DTSTART;TZID=America/New_York:20240115T100000
```

UTC datetimes are indicated with the `Z` suffix: `20240115T100000Z`
