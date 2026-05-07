# Strategy Specification for ICAL-005

## Bug 1: rfc_6868_escape swaps ^ and " escape codes

**Trigger condition**: Any parameter value containing a caret character (`^`).
The buggy code maps `^` to `^'` (which unescapes to `"`) and `"` to `^^`
(which unescapes to `^`). On roundtrip, carets become double-quotes and
vice versa.

**Why default strategy is insufficient**: Most PBT strategies generate simple
alphanumeric parameter values. Caret characters are rare in common parameter
values (CN, ROLE, etc.). The bug requires deliberately including `^` in
parameter values, which is not a typical test pattern.

**Trigger probability with default strategy**: ~2% (very few tests include
caret characters in parameter values).

**Minimum trigger input**: `CN=test^team` — the caret in the CN value will
be escaped as `^'` (wrong) instead of `^^` (correct). On roundtrip, the
parsed CN will be `test"team` instead of `test^team`.

**Targeted strategy**: Generate parameter values containing `^` and optionally
`"`. Apply `rfc_6868_escape` then `rfc_6868_unescape` and assert equality.
Alternatively, create ATTENDEE properties with CN containing carets, serialize
to ical, parse back, and verify CN is preserved.

---

## Bug 2: foldline ASCII fast path exceeds 75-octet limit

**Trigger condition**: Any ASCII content line longer than 74 characters. The
buggy code uses `limit` (75) instead of `limit - 1` (74) as the chunk size,
producing first-line segments of 75 characters and continuation segments of
76 bytes on the wire (75 content + 1 space prefix).

**Why default strategy is insufficient**: Most baseline tests don't check the
raw byte length of individual lines in the serialized output. They only verify
that the parsed content matches the original. The roundtrip works correctly
because the unfolding regex doesn't care about line length.

**Trigger probability with default strategy**: ~5% (few tests check RFC 5545
line length conformance).

**Minimum trigger input**: An event with `SUMMARY` of 80+ ASCII characters,
or an ATTENDEE with long CN + email. The serialized output will have lines
exceeding 75 octets.

**Targeted strategy**: Generate events with long ASCII property values (76+
characters). Serialize to ical. Split output on `\r\n`. Assert each line is
<= 75 bytes when encoded as UTF-8.

---

## Bug 3: Parameters.from_ical collapses multi-value params

**Trigger condition**: Any parameter with 2+ comma-separated values in the
serialized form. The buggy condition `len(vals) >= 1` (instead of `== 1`)
always takes the single-value branch, storing only `vals[0]` and discarding
subsequent values.

**Why default strategy is insufficient**: Multi-value parameters (MEMBER,
DELEGATED-TO, DELEGATED-FROM) are uncommon in basic tests. Most baseline
tests use single attendees without delegation or group membership.

**Trigger probability with default strategy**: ~3% (few tests create
multi-value parameters and verify all values are preserved).

**Minimum trigger input**: `MEMBER="mailto:a@x.com","mailto:b@x.com"` —
after parsing, MEMBER will be the string `mailto:a@x.com` instead of a
list `['mailto:a@x.com', 'mailto:b@x.com']`.

**Targeted strategy**: Generate Parameters with multi-value MEMBER or
DELEGATED-TO. Serialize with `to_ical()`, parse back with `from_ical()`.
Assert the parsed value is a list with the correct number of elements.

---

## Bug 4: foldline non-ASCII path allows 75-byte segment

**Trigger condition**: Any content line containing at least one non-ASCII
character and with total byte length >= 75. The buggy condition `byte_count >
limit` (instead of `>= limit`) allows a line segment of exactly 75 bytes
before inserting the fold. With the continuation space prefix, the wire line
is 76 bytes, exceeding the RFC 5545 limit.

**Why default strategy is insufficient**: Similar to Bug 2, most tests don't
check raw line byte lengths. Additionally, triggering requires non-ASCII
content (e.g., accented characters in SUMMARY, DESCRIPTION, or LOCATION),
which many baseline tests don't generate.

**Trigger probability with default strategy**: ~2% (requires both non-ASCII
content and line length checking).

**Minimum trigger input**: `SUMMARY:` followed by 35 copies of `ä` (70 bytes
in UTF-8) produces a line of 78 bytes (8 prefix + 70 content). With the bug,
the first segment is 75 bytes instead of 74.

**Targeted strategy**: Generate events with non-ASCII SUMMARY or LOCATION
values of sufficient length. Serialize to ical. Check each line's byte
length is <= 75 octets.
