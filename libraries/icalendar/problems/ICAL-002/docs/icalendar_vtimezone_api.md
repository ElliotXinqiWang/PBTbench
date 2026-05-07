# icalendar Library — VTIMEZONE Component Reference

## Overview

The `icalendar` library (version 7.0.3) implements RFC 5545 compliant VTIMEZONE
components for representing timezone definitions in iCalendar data. A VTIMEZONE
component encodes how a timezone's UTC offset changes over time, including
daylight saving time transitions.

This document covers the `Timezone`, `TimezoneStandard`, and `TimezoneDaylight`
classes in `icalendar.cal.timezone`, as well as the related conversion methods.

## RFC 5545 Section 3.6.5 — VTIMEZONE

A VTIMEZONE component consists of one or more subcomponents: STANDARD and
DAYLIGHT. Each subcomponent defines a period during which a particular UTC
offset is in effect.

### Key Properties

| Property | Required | Description |
|----------|----------|-------------|
| TZID | Yes | Unique identifier for the timezone (e.g., "America/New_York") |
| DTSTART | Yes (in sub) | Effective onset date/time for the observance (local time, no tzinfo) |
| TZOFFSETFROM | Yes (in sub) | UTC offset in effect BEFORE the transition |
| TZOFFSETTO | Yes (in sub) | UTC offset in effect AFTER the transition |
| TZNAME | Optional | Abbreviation for the timezone in this observance (e.g., "EST", "EDT") |
| RRULE | Optional | Recurrence rule for annual transitions |
| RDATE | Optional | Explicit list of additional transition dates |

### STANDARD vs DAYLIGHT Subcomponents

- **STANDARD**: Represents standard time (winter time). During standard time,
  `dst()` returns `timedelta(0)`. The transition to standard time means clocks
  "fall back" — the UTC offset decreases (TZOFFSETTO < TZOFFSETFROM).

- **DAYLIGHT**: Represents daylight saving time (summer time). During daylight
  saving time, `dst()` returns a non-zero timedelta. The transition to daylight
  time means clocks "spring forward" — the UTC offset increases
  (TZOFFSETTO > TZOFFSETFROM).

### UTC Transition Time Computation

The DTSTART in a VTIMEZONE subcomponent is specified in **local time** (the
time as it would appear on a wall clock at the moment of transition). To
convert this to UTC, you must subtract TZOFFSETFROM (the UTC offset that was
in effect *before* the transition):

```
UTC_transition_time = DTSTART - TZOFFSETFROM
```

This is because DTSTART is expressed in the timezone that was in effect just
before the transition occurs. TZOFFSETFROM represents "where we're coming from"
and TZOFFSETTO represents "where we're going to."

**Example**: Eastern US transition to EDT on March 10, 2024 at 2:00 AM local:
- DTSTART = 2024-03-10T02:00:00
- TZOFFSETFROM = -05:00 (EST, the offset before the transition)
- TZOFFSETTO = -04:00 (EDT, the offset after the transition)
- UTC time = 2024-03-10T02:00:00 - (-05:00) = 2024-03-10T07:00:00Z

## API Reference

### Class: `Timezone` (VTIMEZONE)

```python
from icalendar import Timezone
from icalendar.cal.timezone import TimezoneStandard, TimezoneDaylight
```

#### Constructor

```python
tz = Timezone()
tz.add("TZID", "My/Timezone")
```

#### `Timezone.from_tzinfo(timezone, tzid=None, first_date=None, last_date=None)`

Creates a VTIMEZONE component from a Python `tzinfo` object (works with
`zoneinfo.ZoneInfo`, `pytz`, `dateutil.tz`, etc.).

**Parameters**:
- `timezone` — a `tzinfo` instance
- `tzid` — string timezone identifier; if None, extracted from the tzinfo
- `first_date` — earliest date to include transitions for (default: 1970-01-01)
- `last_date` — latest date to include transitions for (default: 2038-01-01)

**Returns**: A `Timezone` component with STANDARD and DAYLIGHT subcomponents.

**Behavior details**:
- Uses binary search to find transition boundaries within the date range
- For each distinct (offset_from, offset_to, tzname, is_standard) combination,
  creates a subcomponent with the earliest occurrence as DTSTART and additional
  occurrences as RDATE values
- `is_standard` is determined by checking `start.dst() == timedelta(0)`:
  if the DST offset is zero, it's standard time; otherwise it's daylight time
- The initial subcomponent (where no prior offset is known, `offset_from is None`)
  uses the convention `offset_from = offset_to` since there is no prior state

**Example**:
```python
from zoneinfo import ZoneInfo
from datetime import date
from icalendar import Timezone

zi = ZoneInfo("Europe/Berlin")
vtimezone = Timezone.from_tzinfo(zi, "Europe/Berlin",
                                  date(2023, 1, 1), date(2025, 1, 1))

# vtimezone contains STANDARD and DAYLIGHT subcomponents
for sub in vtimezone.subcomponents:
    print(f"{sub.name}: DTSTART={sub.DTSTART}, "
          f"FROM={sub.TZOFFSETFROM}, TO={sub.TZOFFSETTO}")
```

For the initial subcomponent (the one with the earliest DTSTART), the
TZOFFSETFROM should equal TZOFFSETTO because there is no preceding transition
to come from. For non-UTC timezones, this initial TZOFFSETFROM should reflect
the timezone's actual offset, not UTC (timedelta(0)).

#### `Timezone.get_transitions()`

Extracts transition times and transition info from the VTIMEZONE component.

**Returns**: A tuple `(transition_times, transition_info)` where:
- `transition_times` — list of `datetime` objects representing UTC times when
  each transition takes effect
- `transition_info` — list of `(utcoffset, dst_offset, tzname)` tuples

**Transition time computation**:
Each transition time is computed as `DTSTART - TZOFFSETFROM`. The local
DTSTART is converted to UTC by subtracting the offset that was in effect
before the transition (TZOFFSETFROM), not the offset after (TZOFFSETTO).

**DST offset computation**:
- For STANDARD transitions: `dst_offset = timedelta(0)` (no DST during
  standard time)
- For DAYLIGHT transitions: `dst_offset = TZOFFSETTO - previous_STANDARD_TZOFFSETTO`.
  The DST offset is the difference between the daylight UTC offset and the
  most recent standard UTC offset.

The algorithm searches backward through transitions to find the most recent
STANDARD transition. If no STANDARD transition exists before the current one
(e.g., the first transition in the list is DAYLIGHT), it searches forward
to find the next STANDARD transition and uses its TZOFFSETTO for the
computation.

**Example**:
```python
tz = Timezone()
tz.add("TZID", "US/Eastern")

std = TimezoneStandard()
std.DTSTART = datetime(2020, 11, 1, 2, 0, 0)
std.TZOFFSETFROM = timedelta(hours=-4)   # coming from EDT
std.TZOFFSETTO = timedelta(hours=-5)     # going to EST
std.add("TZNAME", "EST")
tz.add_component(std)

dlt = TimezoneDaylight()
dlt.DTSTART = datetime(2020, 3, 8, 2, 0, 0)
dlt.TZOFFSETFROM = timedelta(hours=-5)   # coming from EST
dlt.TZOFFSETTO = timedelta(hours=-4)     # going to EDT
dlt.add("TZNAME", "EDT")
tz.add_component(dlt)

transition_times, transition_info = tz.get_transitions()

# transition_times[0] = datetime(2020, 3, 8, 7, 0, 0)  # 2:00 - (-5:00) = 7:00 UTC
# transition_info[0] = (timedelta(hours=-4), timedelta(hours=1), "EDT")
#   utcoffset = -4h (EDT), dst_offset = 1h (-4h - (-5h)), name = "EDT"

# transition_times[1] = datetime(2020, 11, 1, 6, 0, 0)  # 2:00 - (-4:00) = 6:00 UTC
# transition_info[1] = (timedelta(hours=-5), timedelta(0), "EST")
#   utcoffset = -5h (EST), dst_offset = 0h (standard time), name = "EST"
```

#### `Timezone.to_tz(tzp=tzp, lookup_tzid=True)`

Converts the VTIMEZONE component to a Python timezone object using the
configured timezone provider.

#### `Timezone.from_tzid(tzid, tzp=tzp, first_date=..., last_date=...)`

Class method to create a VTIMEZONE from a timezone ID string like
`"Europe/Berlin"`.

#### `Timezone.tz_name`

Property returning the TZID string value.

#### `Timezone.standard`

Property returning a list of `TimezoneStandard` subcomponents.

#### `Timezone.daylight`

Property returning a list of `TimezoneDaylight` subcomponents.

### Class: `TimezoneStandard` (STANDARD subcomponent)

```python
from icalendar.cal.timezone import TimezoneStandard
```

Represents a STANDARD observance within a VTIMEZONE.

**Required properties**: DTSTART, TZOFFSETTO, TZOFFSETFROM

**Accessible as attributes**:
```python
std = TimezoneStandard()
std.DTSTART = datetime(2020, 11, 1, 2, 0, 0)
std.TZOFFSETFROM = timedelta(hours=-4)
std.TZOFFSETTO = timedelta(hours=-5)
std.add("TZNAME", "EST")
```

### Class: `TimezoneDaylight` (DAYLIGHT subcomponent)

```python
from icalendar.cal.timezone import TimezoneDaylight
```

Represents a DAYLIGHT observance within a VTIMEZONE.

**Required properties**: DTSTART, TZOFFSETTO, TZOFFSETFROM (same as STANDARD)

```python
dlt = TimezoneDaylight()
dlt.DTSTART = datetime(2020, 3, 8, 2, 0, 0)
dlt.TZOFFSETFROM = timedelta(hours=-5)
dlt.TZOFFSETTO = timedelta(hours=-4)
dlt.add("TZNAME", "EDT")
```

## Internal Data Flow

### `_extract_offsets(component, tzname)`

Static method that extracts offset and transition time data from a STANDARD
or DAYLIGHT subcomponent. Returns `(is_dst, transitions)` where:
- `is_dst` — 0 for STANDARD, 1 for DAYLIGHT
- `transitions` — list of `(transtime, offsetfrom, offsetto, tzname)` tuples

When RRULE is present, transition times are expanded using `dateutil.rrule`.
The RRULE evaluation uses the TZOFFSETFROM as the timezone context, ensuring
correct weekday computation for rules like "first Sunday in November."

When RDATE is present, transition times come from the explicit date list
plus the DTSTART.

### Transition Tuple Format

Throughout `get_transitions()`, transitions are stored as 4-tuples:
```
(transtime, offsetfrom, offsetto, tzname)
  index 0     index 1    index 2   index 3
```

- `transtime` (index 0): local datetime of the transition
- `offsetfrom` (index 1): TZOFFSETFROM as timedelta
- `offsetto` (index 2): TZOFFSETTO as timedelta
- `tzname` (index 3): name string (e.g., "EST", "EDT")

The UTC transition time is computed as: `transtime - offsetfrom` (index 0 - index 1).

## Common Timezone Patterns

### Timezone with DST (e.g., US/Eastern)

```
VTIMEZONE
  TZID: US/Eastern
  STANDARD:
    DTSTART: 20201101T020000
    TZOFFSETFROM: -0400   (coming from EDT)
    TZOFFSETTO: -0500     (going to EST)
    TZNAME: EST
  DAYLIGHT:
    DTSTART: 20200308T020000
    TZOFFSETFROM: -0500   (coming from EST)
    TZOFFSETTO: -0400     (going to EDT)
    TZNAME: EDT
```

### Fixed-Offset Timezone (no DST)

```
VTIMEZONE
  TZID: Asia/Kolkata
  STANDARD:
    DTSTART: 19700101T000000
    TZOFFSETFROM: +0530
    TZOFFSETTO: +0530
    TZNAME: IST
```

### From Python tzinfo

```python
from zoneinfo import ZoneInfo
from icalendar import Timezone
from datetime import date

# Create VTIMEZONE from ZoneInfo
vtimezone = Timezone.from_tzinfo(
    ZoneInfo("America/New_York"),
    "America/New_York",
    date(2020, 1, 1),
    date(2025, 1, 1),
)

# The resulting VTIMEZONE should have:
# - STANDARD subcomponent(s) with offset_to < offset_from (fall back)
# - DAYLIGHT subcomponent(s) with offset_to > offset_from (spring forward)
# - Initial subcomponent with TZOFFSETFROM == TZOFFSETTO
# - Correct TZNAME labels matching the timezone's actual names
```

## Key Invariants

1. **UTC transition time**: `transition_time = DTSTART - TZOFFSETFROM`
   (NOT DTSTART - TZOFFSETTO). The local time is relative to the old offset.

2. **Initial TZOFFSETFROM**: When `from_tzinfo()` creates the first
   subcomponent (where no prior offset is known), TZOFFSETFROM should equal
   TZOFFSETTO. For non-UTC timezones, this value should be the timezone's
   actual offset, not zero.

3. **DST offset computation**: For DAYLIGHT transitions, the DST offset is
   `TZOFFSETTO_daylight - TZOFFSETTO_standard` where TZOFFSETTO_standard
   comes from the nearest STANDARD transition (searching backward first,
   then forward if needed). The standard TZOFFSETTO (index 2 in transition
   tuple), not TZOFFSETFROM (index 1), must be used.

4. **STANDARD/DAYLIGHT labeling**: `from_tzinfo()` determines whether a
   period is standard time by checking `start.dst() == timedelta(0)`.
   Standard time has zero DST offset; daylight time has non-zero DST offset.
   STANDARD subcomponents represent "fall back" (offset decreases) and
   DAYLIGHT subcomponents represent "spring forward" (offset increases).

5. **Offset direction**:
   - DAYLIGHT transitions: `TZOFFSETTO > TZOFFSETFROM` (clocks move forward)
   - STANDARD transitions: `TZOFFSETTO < TZOFFSETFROM` (clocks move backward)

## Property Access Patterns

The `TimezoneStandard` and `TimezoneDaylight` classes use `create_single_property`
to expose required properties as Python attributes:

```python
sub.DTSTART       # datetime — onset of this observance
sub.TZOFFSETTO    # timedelta — UTC offset after transition
sub.TZOFFSETFROM  # timedelta — UTC offset before transition
sub.name          # str — "STANDARD" or "DAYLIGHT"
```

These properties support both read and write access. The underlying iCalendar
property is automatically wrapped in the appropriate type (e.g., `vUTCOffset`
for offset properties).
