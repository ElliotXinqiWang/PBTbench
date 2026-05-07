# Strategy Spec for ICAL-001

## Bug 1: EXDATE exclusion list missing "exdate"

**Trigger condition**: Pass a list of 2+ dates or datetimes to `component.add('exdate', [...])`.
The bug removes "exdate" from the exclusion list in `Component.add()`, causing EXDATE
lists to be individually encoded. Each date becomes a separate EXDATE property line
instead of a single comma-separated line. On roundtrip, this produces a list of
vDDDLists objects instead of a single vDDDLists.

**Why default strategy is insufficient**: Default PBT rarely tests EXDATE with multiple
values as a list and then checks the serialization structure (number of EXDATE lines
or parsed type). Most tests add single EXDATE values or don't verify line structure.

**Trigger probability with default strategy**: ~3% (few tests add multi-value EXDATE
lists and check output structure)

**Minimal trigger input**:
```python
event.add('exdate', [date(2024, 1, 15), date(2024, 2, 15)])
# Bug: produces two EXDATE lines instead of one comma-separated line
# Roundtrip: parsed EXDATE becomes list[vDDDLists] instead of single vDDDLists
```

## Bug 2: vPeriod.to_ical by_duration condition inverted

**Trigger condition**: Create a `vPeriod` with duration format `(start, timedelta)`,
call `to_ical()`, and check the output format. The bug causes duration-format periods
to serialize as explicit end-time format.

**Why default strategy is insufficient**: Most period tests create periods and check
`.overlaps()` or parse from ICS strings. Few tests create a period with duration
then check the serialization format. Trigger probability depends on testing the
serialization path with duration-based periods.

**Trigger probability with default strategy**: ~10% (period roundtrip rarely tested)

**Minimal trigger input**:
```python
period = vPeriod((datetime(2024,1,1,10,0, tzinfo=timezone.utc), timedelta(hours=2)))
ical = period.to_ical()
# Bug: outputs '20240101T100000Z/20240101T120000Z' instead of '20240101T100000Z/PT2H'
```

## Bug 3: _escape_char backslash/semicolon order swap

**Trigger condition**: Any TEXT property value containing a literal semicolon character.
The semicolon escaping creates a backslash that is then doubled by the backslash
escaping step (which should have happened first).

**Why default strategy is insufficient**: Random ASCII text has ~1% probability of
containing semicolons. However, if the strategy targets text with RFC special
characters, the trigger rate is much higher.

**Trigger probability with default strategy**: ~15-30% (semicolons in text are common)

**Minimal trigger input**:
```python
event.add('summary', 'Meeting; Room A')
ical = event.to_ical()
parsed = Event.from_ical(ical)
# Bug: parsed['summary'] == 'Meeting\\; Room A' (extra backslash)
```

## Bug 4: vRecur.to_ical uses semicolons instead of commas

**Trigger condition**: Any vRecur rule with multi-value fields (BYDAY, BYMONTH,
BYMONTHDAY, BYYEARDAY, BYWEEKNO, BYSETPOS, BYSECOND, BYMINUTE, BYHOUR) containing
more than one value. The semicolons cause the parser to interpret subsequent values
as separate key=value pairs.

**Why default strategy is insufficient**: Single-value RRULE fields (COUNT, INTERVAL,
FREQ, WKST) are not affected. Only multi-value fields with 2+ values trigger the bug.
Many basic RRULE tests use single values.

**Trigger probability with default strategy**: ~40% (multi-value BYDAY is common)

**Minimal trigger input**:
```python
recur = vRecur.from_ical('FREQ=WEEKLY;BYDAY=MO,WE,FR')
serialized = recur.to_ical()
# Bug: b'FREQ=WEEKLY;BYDAY=MO;WE;FR' — parser sees WE and FR as separate entries
parsed = vRecur.from_ical(serialized.decode())
# parsed['BYDAY'] == ['MO'] — WE and FR are lost
```
