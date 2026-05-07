# icalendar VALARM API Reference

## Overview

The `icalendar` library (v7.0.3) provides a comprehensive implementation of
RFC 5545 calendar components, including VALARM (alarm) support. This document
covers the VALARM component, its properties, and the alarm time computation API.

VALARM components define alarms or reminders associated with calendar events
(VEVENT) or to-dos (VTODO). Alarms can trigger at:
- A specific time offset **before or after** the start/end of an event (duration trigger)
- An absolute date-time (absolute trigger)

---

## 1. Core Classes

### 1.1 Alarm (icalendar.Alarm)

The `Alarm` class represents a VALARM component. It extends `Component`.

```python
from icalendar import Alarm
from datetime import timedelta, datetime, timezone

# Create an alarm that triggers 15 minutes before event start
alarm = Alarm()
alarm.add('action', 'DISPLAY')
alarm.add('description', 'Meeting reminder')
alarm.add('trigger', timedelta(minutes=-15))
```

**Required properties:**
- `ACTION`: The action type (`AUDIO`, `DISPLAY`, `EMAIL`)
- `TRIGGER`: When the alarm triggers (duration or absolute datetime)

**Optional properties:**
- `DESCRIPTION`: Text description of the alarm
- `SUMMARY`: Summary text (for EMAIL action)
- `DURATION`: Delay period between repeated triggers
- `REPEAT`: Number of additional trigger repetitions
- `ATTENDEE`: Attendees for EMAIL action
- `ACKNOWLEDGED`: UTC datetime when alarm was last acknowledged (RFC 9074)

### 1.2 TRIGGER Property

The TRIGGER property specifies when an alarm will trigger. It accepts two value types:

**Duration trigger** (default): A positive or negative duration relative to the
event start or end.

```python
# Negative duration = before the reference point
alarm.add('trigger', timedelta(minutes=-15))   # 15 min BEFORE event start
alarm.add('trigger', timedelta(hours=-1))      # 1 hour BEFORE event start

# Positive duration = after the reference point
alarm.add('trigger', timedelta(minutes=30))    # 30 min AFTER event start
alarm.add('trigger', timedelta(hours=2))       # 2 hours AFTER event start
```

RFC 5545 states: "An alarm with a negative duration is triggered before the
associated start or end of the event or to-do. An alarm with a positive duration
is triggered after the associated start or end."

**Important**: Negative durations use the standard iCalendar DURATION format with
a leading minus sign: `-PT15M` (15 minutes before), `-PT1H` (1 hour before),
`-P1DT5H` (1 day and 5 hours before). The serialization must preserve the sign
through roundtrip: `to_ical()` should produce `-PT15M` and `from_ical('-PT15M')`
should reconstruct the original negative timedelta.

**Absolute datetime trigger**: A specific UTC datetime when the alarm fires,
regardless of event timing.

```python
# Absolute trigger (always UTC)
alarm.add('trigger', datetime(2024, 6, 15, 9, 45, 0, tzinfo=timezone.utc))
```

### 1.3 TRIGGER RELATED Parameter

The RELATED parameter of the TRIGGER property specifies whether the duration
is relative to the START or END of the parent component.

```python
alarm = Alarm()
alarm.TRIGGER = timedelta(hours=-1)      # Duration trigger
alarm.TRIGGER_RELATED = "END"            # Relative to DTEND
```

**Values:**
- `"START"` (default): Alarm triggers relative to DTSTART
- `"END"`: Alarm triggers relative to DTEND

When RELATED=END is set, the alarm trigger time is computed as `DTEND + trigger_duration`.
For example, if DTEND is 11:00 and trigger is -PT15M, the alarm fires at 10:45.

When RELATED=START (default), the trigger time is `DTSTART + trigger_duration`.
For example, if DTSTART is 10:00 and trigger is -PT15M, the alarm fires at 09:45.

The RELATED parameter is accessed via `alarm.TRIGGER_RELATED`:

```python
>>> alarm = Alarm()
>>> alarm.TRIGGER = timedelta(hours=-1)
>>> alarm.TRIGGER_RELATED       # default
'START'
>>> alarm.TRIGGER_RELATED = "END"
>>> alarm.TRIGGER_RELATED
'END'
```

### 1.4 REPEAT and DURATION (Repeated Alarms)

An alarm can trigger multiple times. Per RFC 5545:

> A definition of an alarm with a repeating trigger MUST include both
> the "DURATION" and "REPEAT" properties. The "DURATION" property
> specifies the delay period, after which the alarm will repeat.
> The "REPEAT" property specifies the number of **additional**
> repetitions that the alarm will be triggered. This repetition
> count is **in addition to** the initial triggering of the alarm.

```python
alarm = Alarm()
alarm.TRIGGER = timedelta(hours=-4)    # Initial trigger: 4h before start
alarm.DURATION = timedelta(hours=1)    # Repeat every 1 hour
alarm.REPEAT = 2                       # 2 additional repetitions
# Total triggers: 3 (initial + 2 repeats)
# Times: -4h, -3h, -2h (relative to start)
```

The total number of trigger times is always `REPEAT + 1`:
- The initial trigger at the TRIGGER time
- Plus REPEAT additional triggers, each DURATION apart

For REPEAT=0 or missing REPEAT/DURATION, only the initial trigger fires.

---

## 2. Alarm.triggers Property

The `Alarm.triggers` property computes the relative trigger times, taking
TRIGGER, DURATION, and REPEAT into account. It returns a named tuple with
three categories:

```python
class Triggers(NamedTuple):
    start: tuple[timedelta]     # Triggers relative to DTSTART
    end: tuple[timedelta]       # Triggers relative to DTEND
    absolute: tuple[datetime]   # Absolute trigger times
```

**Example:**

```python
>>> alarm = Alarm()
>>> alarm.TRIGGER = timedelta(hours=-4)
>>> alarm.DURATION = timedelta(hours=1)
>>> alarm.REPEAT = 2
>>> alarm.triggers.start
(timedelta(hours=-4), timedelta(hours=-3), timedelta(hours=-2))
>>> alarm.triggers.end
()
>>> alarm.triggers.absolute
()
```

The number of entries in the relevant tuple equals REPEAT + 1:
- For REPEAT=2: 3 entries (initial + 2 repeats)
- For REPEAT=0: 1 entry (initial only)
- For REPEAT=5: 6 entries (initial + 5 repeats)

The dispatch logic:
- If TRIGGER is a datetime: goes to `absolute` tuple
- If TRIGGER_RELATED == "START": goes to `start` tuple
- If TRIGGER_RELATED == "END": goes to `end` tuple

---

## 3. Alarms Class (Alarm Time Computation)

The `Alarms` class (from `icalendar.alarms`) computes the actual trigger times
by combining alarm definitions with event start/end times.

### 3.1 Basic Usage

```python
from icalendar import Event, Alarms

event = Event.from_ical('''BEGIN:VEVENT
DTSTART;TZID=America/New_York:20210302T103000
DTEND;TZID=America/New_York:20210302T113000
SUMMARY:Meeting
BEGIN:VALARM
TRIGGER:-PT30M
ACTION:DISPLAY
END:VALARM
BEGIN:VALARM
TRIGGER:-PT15M
RELATED:END
ACTION:DISPLAY
END:VALARM
END:VEVENT''')

alarms = Alarms(event)
for alarm_time in alarms.times:
    print(f"Trigger: {alarm_time.trigger}")
```

### 3.2 Manual Construction

```python
from icalendar import Alarm, Event
from icalendar.alarms import Alarms

alarms_calc = Alarms()
alarms_calc.set_start(dtstart)
alarms_calc.set_end(dtend)
alarms_calc.add_alarm(alarm)

for at in alarms_calc.times:
    print(at.trigger)
```

### 3.3 Alarm Dispatch in add_alarm()

When an alarm is added via `add_alarm()`, it is classified internally:

1. If the TRIGGER is a datetime (absolute): stored in `_absolute_alarms`
2. If TRIGGER_RELATED == "START" (default): stored in `_start_alarms`
3. If TRIGGER_RELATED == "END": stored in `_end_alarms`

The correct dispatch ensures that:
- START-related alarms are computed against the parent's DTSTART
- END-related alarms are computed against the parent's DTEND
- Absolute alarms use their datetime directly

### 3.4 Repeated Alarm Time Computation

For alarms with REPEAT and DURATION, the `_repeat()` method generates all
trigger times:

```
trigger_times = [initial_trigger]
for i in range(1, repeat + 1):
    trigger_times.append(initial_trigger + duration * i)
```

The total count of generated times is `REPEAT + 1` (1 initial + REPEAT repeats).

### 3.5 AlarmTime Objects

Each computed alarm time is wrapped in an `AlarmTime` object:

```python
alarm_time = alarms.times[0]
alarm_time.trigger        # datetime: when to fire
alarm_time.alarm          # Alarm: the source alarm component
alarm_time.parent         # Event/Todo: the parent component
alarm_time.acknowledged   # datetime or None: when acknowledged
alarm_time.is_active()    # bool: whether still active
```

---

## 4. Duration Serialization (vDuration)

The `vDuration` class handles serialization of duration values to/from
iCalendar format.

### 4.1 Format

Duration format follows RFC 5545:

```
dur-value = (["+"] / "-") "P" (dur-date / dur-time / dur-week)
```

Examples:
- `PT15M` - 15 minutes
- `PT1H` - 1 hour
- `PT1H30M` - 1 hour 30 minutes
- `P1D` - 1 day
- `P1DT5H` - 1 day 5 hours
- `P7W` - 7 weeks
- `-PT15M` - negative 15 minutes (15 minutes before)
- `-PT1H` - negative 1 hour
- `-P1DT5H` - negative 1 day 5 hours

### 4.2 Serialization

```python
from icalendar.prop import vDuration
from datetime import timedelta

vd = vDuration(timedelta(minutes=15))
vd.to_ical()        # b'PT15M'

vd = vDuration(timedelta(minutes=-15))
vd.to_ical()        # b'-PT15M'

vd = vDuration(timedelta(days=-1, hours=-5))
vd.to_ical()        # b'-P1DT5H'
```

### 4.3 Roundtrip Guarantee

Duration values must roundtrip correctly:

```python
td = timedelta(minutes=-15)
assert vDuration.from_ical(vDuration(td).to_ical().decode()) == td
```

This applies to all durations including negative ones. The sign must be
preserved: a negative duration serialized and parsed back must produce
the same negative timedelta.

---

## 5. Complete VALARM Lifecycle Example

```python
from icalendar import Calendar, Event, Alarm
from icalendar.alarms import Alarms
from datetime import datetime, timedelta, timezone

# Create event with multiple alarms
cal = Calendar()
cal.add('prodid', '-//Test//EN')
cal.add('version', '2.0')

event = Event()
event.add('dtstart', datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc))
event.add('dtend', datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc))
event.add('summary', 'Team Meeting')

# Alarm 1: 30 min before START
alarm1 = Alarm()
alarm1.add('action', 'DISPLAY')
alarm1.add('description', 'Meeting in 30 min')
alarm1.add('trigger', timedelta(minutes=-30))
event.add_component(alarm1)

# Alarm 2: 15 min before END, repeats 2 more times every 5 min
alarm2 = Alarm()
alarm2.add('action', 'DISPLAY')
alarm2.add('description', 'Meeting ending soon')
alarm2.add('trigger', timedelta(minutes=-15))
alarm2['TRIGGER'].params['RELATED'] = 'END'
alarm2.add('duration', timedelta(minutes=5))
alarm2.add('repeat', 2)
event.add_component(alarm2)

# Alarm 3: Absolute trigger at a specific time
alarm3 = Alarm()
alarm3.add('action', 'DISPLAY')
alarm3.add('description', 'Absolute reminder')
alarm3.add('trigger', datetime(2024, 6, 15, 9, 0, tzinfo=timezone.utc))
event.add_component(alarm3)

cal.add_component(event)

# Compute all alarm times
alarms = Alarms(event)
for at in alarms.times:
    print(f"  Trigger: {at.trigger}, Related: {at.alarm.TRIGGER_RELATED}")

# Expected:
# Alarm 1: 09:30 (DTSTART 10:00 - 30min)
# Alarm 2: 11:45 (DTEND 12:00 - 15min), 11:50 (+5min), 11:55 (+5min)
# Alarm 3: 09:00 (absolute)
```

---

## 6. RFC 5545 Section 3.6.6 — VALARM Properties

### 6.1 ACTION

Defines the action type. Required.

| Value   | Description                              |
|---------|------------------------------------------|
| AUDIO   | Triggers a sound                         |
| DISPLAY | Displays a text message                  |
| EMAIL   | Sends an email                           |

### 6.2 TRIGGER

Specifies when the alarm fires. Required.

- **Default value type**: DURATION (timedelta)
- **Alternative**: DATE-TIME (absolute UTC datetime)
- **Parameters**: RELATED (START or END), VALUE (DURATION or DATE-TIME)

### 6.3 DURATION and REPEAT

For repeated alarms:
- DURATION: delay between each repetition
- REPEAT: number of **additional** repetitions after the initial trigger
- Both MUST be present if either is present
- Total triggers = REPEAT + 1

### 6.4 ACKNOWLEDGED (RFC 9074)

UTC datetime when the alarm was last acknowledged. Used by calendar software
to track dismissed alarms.

---

## 7. Key Invariants

The following invariants should hold for correct VALARM behavior:

1. **Duration roundtrip**: `vDuration.from_ical(vDuration(td).to_ical().decode()) == td`
   for all valid timedeltas, including negative ones.

2. **RELATED dispatch**: An alarm with RELATED=START should compute trigger
   time as `DTSTART + trigger_duration`. An alarm with RELATED=END should
   compute as `DTEND + trigger_duration`.

3. **Repeat count**: For REPEAT=N with DURATION, exactly N+1 trigger times
   are generated (1 initial + N repeats), both in `Alarm.triggers` and
   `Alarms.times`.

4. **Repeat timing**: The Nth repeat fires at `initial_trigger + N * duration`.
   For N=0 (initial), N=1 (first repeat), ..., N=REPEAT (last repeat).

5. **Category dispatch**: `Alarm.triggers` returns triggers in the correct
   category (start/end/absolute) based on the TRIGGER value type and
   RELATED parameter.

6. **Alarm times consistency**: `Alarms.times` produces the same number
   of triggers as `Alarm.triggers` for the same alarm configuration.

---

## 8. Edge Cases

### 8.1 Negative Sub-Day Durations

Python represents `timedelta(minutes=-15)` as `timedelta(days=-1, seconds=85500)`.
The iCalendar representation is `-PT15M`. Serialization must correctly handle this
internal representation and produce the correct signed output.

### 8.2 Zero REPEAT

When REPEAT is 0 or absent, only the initial trigger fires. DURATION is ignored
if REPEAT is 0.

### 8.3 Mixed Alarm Types

An event can have multiple alarms with different trigger types (duration vs
absolute) and different RELATED values. The `Alarms` class handles all types
correctly by dispatching each alarm to the appropriate internal list.

### 8.4 Date-Only Events

When DTSTART is a `date` (not `datetime`) and the trigger duration has a time
component, the date is converted to a datetime at midnight before adding the
duration.
