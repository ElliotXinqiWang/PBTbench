# icalendar EXDATE/RDATE API Reference

## Overview

The `icalendar` library (v7.0.3) provides a comprehensive implementation of
RFC 5545 calendar components. This document covers the EXDATE and RDATE
properties, which control exception dates and recurrence dates in recurring
events, including their serialization, parsing, and timezone handling.

EXDATE defines dates/datetimes to exclude from a recurrence set.
RDATE defines additional dates/datetimes (or periods) to include.

Both properties support:
- DATE values (all-day events)
- DATE-TIME values (with optional timezone via TZID parameter)
- Multiple values in a single property (comma-separated)
- Multiple property instances per component

RDATE additionally supports PERIOD values (start/end or start/duration).

---

## 1. Adding EXDATE/RDATE to Events

### 1.1 Component.add()

The primary API for adding properties to components:

```python
from icalendar import Event, Calendar
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

event = Event()
event.add('dtstart', datetime(2024, 6, 1, 9, 0, tzinfo=ZoneInfo('America/New_York')))
event.add('rrule', {'freq': 'daily', 'count': 10})

# Add EXDATE as datetime (timezone-aware)
tz = ZoneInfo('America/New_York')
event.add('exdate', [datetime(2024, 6, 3, 9, 0, tzinfo=tz)])

# Add RDATE as datetime
event.add('rdate', [datetime(2024, 7, 1, 9, 0, tzinfo=tz)])
```

### 1.2 Value Type Inference

When adding a list of values, `Component._infer_value_type()` determines the
VALUE parameter automatically:

- If **all** items are `date` objects (not `datetime`): infers `VALUE=DATE`
- If **all** items are `time` objects: infers `VALUE=TIME`
- Mixed types or all-datetime: returns `None` (no VALUE parameter added)

This inference ensures correct serialization format. For example, a list of
pure `date` objects serializes as `EXDATE;VALUE=DATE:20240603,20240605` while
datetime objects serialize with time components.

**Important**: A list containing both `date` and `datetime` objects is
considered mixed-type and should NOT have `VALUE=DATE` inferred, as this
would strip time information from the datetime values.

### 1.3 Multiple EXDATE Properties

RFC 5545 allows multiple EXDATE properties per component:

```python
# Each call to add() creates a separate EXDATE property
event.add('exdate', [datetime(2024, 6, 3, 9, 0, tzinfo=tz)])
event.add('exdate', [datetime(2024, 6, 5, 9, 0, tzinfo=tz)])
```

When accessing `event.exdates`, all EXDATE properties are merged into a
single flat list of datetime values.

---

## 2. EXDATE/RDATE Serialization (vDDDLists)

### 2.1 vDDDLists Class

The `vDDDLists` class (in `icalendar.prop.dt.list`) handles serialization
of date/datetime list properties including EXDATE and RDATE.

```python
from icalendar.prop.dt.list import vDDDLists
from icalendar.prop.dt.types import vDDDTypes

# Internal: vDDDLists wraps a list of vDDDTypes
ddd_list = vDDDLists([dt1, dt2, dt3])
```

### 2.2 TZID Propagation

When constructing a `vDDDLists` from timezone-aware datetimes, the
constructor iterates over the datetime list and extracts the TZID parameter
from each `vDDDTypes` wrapper:

```python
# Pseudocode of vDDDLists.__init__:
for dt_l in dt_list:
    dt = vDDDTypes(dt_l)
    vddd.append(dt)
    if "TZID" in dt.params:     # check if this item has TZID
        tzid = dt.params["TZID"]

if tzid:
    self.params["TZID"] = tzid  # propagate TZID to the list-level params
```

The TZID parameter at the list level is critical for correct serialization:
`EXDATE;TZID=America/New_York:20240603T090000,20240605T090000`

Without TZID in the serialized output, the datetimes are interpreted as
"floating" (no timezone) on roundtrip parsing.

### 2.3 to_ical() Output

```python
ddd_list = vDDDLists(dts)
ical_bytes = ddd_list.to_ical()
# b'20240603T090000,20240605T090000'
# With TZID in params: EXDATE;TZID=America/New_York:20240603T090000,...
```

---

## 3. Parsing EXDATE/RDATE (from_ical)

### 3.1 Component.from_ical()

The main parsing entry point. When parsing iCal text, `from_ical()` handles
timezone application for certain property names listed in `datetime_names`:

```python
# Internal datetime_names tuple (simplified):
datetime_names = (
    "DTSTART", "DTEND", "RECURRENCE-ID", "DUE", "RDATE", "EXDATE"
)
```

For properties in this tuple, when a `TZID` parameter is present, the parser
applies the specified timezone to the parsed datetime values. This is
essential for correctly interpreting localized times like:

```
EXDATE;TZID=America/New_York:20240603T090000
```

Without timezone application, this would be parsed as a naive datetime
(no timezone info), losing the TZID information.

### 3.2 RDATE with PERIOD Values

RDATE supports PERIOD values that specify a time range:

```
RDATE;VALUE=PERIOD:20240615T100000Z/PT2H
RDATE;VALUE=PERIOD:20240615T100000Z/20240615T120000Z
```

Two forms:
1. **Start/Duration**: `start/PTnHnM` — end computed as `start + duration`
2. **Start/End**: `start/end` — explicit end datetime

### 3.3 Accessing Parsed Values

```python
cal = Calendar.from_ical(ical_string)
event = cal.walk('VEVENT')[0]

# Access EXDATE values (flat list of datetimes)
exdates = event.exdates  # [datetime(2024,6,3,9,0, tzinfo=...), ...]

# Access RDATE values (list of datetimes or (start, end) tuples)
rdates = event.rdates    # [(start, end), ...] for PERIOD values
                         # [datetime, ...] for DATE/DATE-TIME values
```

---

## 4. RDATE Period Processing (_get_rdates)

The `_get_rdates()` function in `attr.py` processes raw RDATE values into
a normalized list:

```python
# Pseudocode:
def _get_rdates(self):
    result = []
    for rdate in raw_rdates:
        if isinstance(rdate, tuple):
            # Period value
            if isinstance(rdate[1], timedelta):
                # Duration form: compute end = start + duration
                result.append((rdate[0], rdate[0] + rdate[1]))
            else:
                # Explicit end form: keep as-is
                result.append(rdate)
        else:
            # Simple datetime
            result.append(rdate)
    return result
```

**Invariant**: For period RDATEs with duration, the end time must always be
at or after the start time (since durations are positive values representing
forward time spans).

---

## 5. Roundtrip Behavior

A correct roundtrip for EXDATE/RDATE with timezone:

```python
from icalendar import Calendar, Event
from zoneinfo import ZoneInfo

tz = ZoneInfo('America/New_York')

# Create
cal = Calendar()
cal.add('prodid', '-//Test//EN')
cal.add('version', '2.0')
event = Event()
event.add('dtstart', datetime(2024, 6, 1, 9, 0, tzinfo=tz))
event.add('rrule', {'freq': 'daily', 'count': 10})
event.add('exdate', [datetime(2024, 6, 3, 9, 0, tzinfo=tz)])
cal.add_component(event)

# Serialize
ical_bytes = cal.to_ical()

# Parse back
cal2 = Calendar.from_ical(ical_bytes)
event2 = cal2.walk('VEVENT')[0]
exdates = event2.exdates

# Verify timezone preserved
assert exdates[0].tzinfo is not None  # Must have timezone
```

The roundtrip should preserve:
1. All date/datetime values
2. Timezone information (via TZID parameter)
3. VALUE type (DATE vs DATE-TIME)
4. Period end times for RDATE PERIOD values

---

## 6. RFC 5545 Key Rules

### 6.1 EXDATE (Section 3.8.5.1)
- EXDATE defines exception dates excluded from a recurrence set
- Value type must match DTSTART (DATE vs DATE-TIME)
- TZID parameter applies to all values in the property
- Multiple EXDATE properties are allowed and should be merged

### 6.2 RDATE (Section 3.8.5.2)
- RDATE adds dates/datetimes/periods to a recurrence set
- PERIOD value has two forms: start/end and start/duration
- For start/duration form, end = start + duration (positive delta)
- TZID parameter applies to datetime values

### 6.3 TZID Parameter (Section 3.2.19)
- Specifies the timezone for DATE-TIME values
- Applied during parsing to produce timezone-aware datetimes
- Must be preserved during serialization for roundtrip fidelity
