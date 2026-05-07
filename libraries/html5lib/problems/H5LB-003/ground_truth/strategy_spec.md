# Strategy Spec for H5LB-003

## Bug 1: CDATA section termination condition (L4)

**Location**: `html5lib/_tokenizer.py`, `cdataSectionState`, line 1717

**Change**: `if data[-1][-2:] == "]]":` → `if data[-1][-1:] == "]":`

**Trigger condition**: Parse an SVG element containing a CDATA section whose content includes
the two-character sequence `]>` (right bracket followed by greater-than). The CDATA section
must NOT contain `]]>` (which would naturally terminate it).

Minimal trigger: `<svg><![CDATA[a]>b]]></svg>` — the `]>` in `a]>b` causes the buggy code
to terminate the CDATA section prematurely. Result: text is `ab]]>` (wrong) instead of
`a]>b` (correct).

**Why default strategy doesn't work**: A random generator producing arbitrary CDATA content
has roughly 1-2% probability of generating a `]>` sequence. With Hypothesis default examples
(~100), this will be found quickly, but a strategy that always includes `]>` is more reliable.

**Trigger probability with default strategy**: ~5-10% (depends on text length; short strings
less likely to contain `]>`)

**Targeted strategy**: Generate `prefix + "]>" + suffix` where prefix and suffix are alphanumeric
strings. This guarantees `]>` in the content. Use `assume("]]>" not in content)` to avoid
natural CDATA termination.

**Ground truth strategy used**: `st.text(alphanumeric)` for prefix and suffix, concatenate with
`"]>"`, filter out `"]]>"`. This gives 100% trigger rate.

---

## Bug 2: Hex numeric character reference radix (L3)

**Location**: `html5lib/_tokenizer.py`, `consumeNumberEntity`, line 81

**Change**: `radix = 16` → `radix = 10`

**Trigger condition**: Parse an HTML entity of the form `&#xHH;` where `HH` is a hex code
consisting entirely of decimal digits (0-9) — but where the hex and decimal interpretations
give different characters.

For example:
- `&#x30;` — hex 0x30 = 48 = '0', decimal 30 = chr(30) = record separator
- `&#x41;` — hex 0x41 = 65 = 'A', decimal 41 = chr(41) = ')'
- `&#x39;` — hex 0x39 = 57 = '9', decimal 39 = chr(39) = "'"

Note: hex codes containing A-F (like `&#xA0;`) would cause `int('A0', 10)` to raise
`ValueError` — which would be caught elsewhere. The silent failure only occurs for
digit-only hex codes.

**Why default strategy doesn't work**: A random strategy might generate `&#xAB;` etc.
which raise ValueError and don't produce a silent failure. The specific condition
requires digit-only hex codes.

**Trigger probability with default strategy**: 0% if generating arbitrary hex codes (A-F
trigger ValueError, not detectable failure). Must specifically generate digit-only hex codes.

**Targeted strategy**: Use `st.sampled_from(["30", "31", ..., "39", "41", ..., "69"])` —
digit-only hex codes in printable ASCII range. Every sample triggers the bug.

**Minimum input**: `&#x30;` — should be '0' (chr(48)), is ')' (chr(30)) with bug. 100% trigger.

---

## Bug 3: Named entity attribute no-semicolon rule inverted (L3)

**Location**: `html5lib/_tokenizer.py`, `consumeEntity`, line 198

**Change**: `and fromAttribute and` → `and not fromAttribute and`

**Trigger condition**: One of two scenarios:

**Scenario A (attribute)**: Parse an element with an attribute value containing a no-semicolon
named entity immediately followed by `=`. The entity should NOT be consumed (stay literal).

Minimal: `<a href="?x=1&amp=val">` — `&amp` (no `;`) followed by `=` in href attribute.
With correct code: href = `?x=1&amp=val` (literal)
With bug: href = `?x=1&=val` (`&amp` consumed)

**Scenario B (content)**: Parse text content with `&name=` (no semicolon, followed by `=`).
The entity SHOULD be consumed.

Minimal: `<p>text&amp=more</p>`
With correct code: text = `text&=more` (entity consumed, result is `&`)
With bug: text = `text&amp=more` (entity NOT consumed, stays literal)

**Why default strategy doesn't work**: Random HTML generation rarely produces no-semicolon
entities followed by `=`. This is a very specific edge case.

**Trigger probability with default strategy**: ~0.1% — must specifically construct
no-semicolon entity + `=` pattern.

**Targeted strategy**: Hardcode `&amp=` in the test value. Generate surrounding text randomly.
100% trigger with targeted input.

---

## Bug 4: Duplicate attribute deduplication (L2)

**Location**: `html5lib/_tokenizer.py`, `emitCurrentToken`, line 242

**Change**: `data.update(raw[::-1])` → `data.update(raw)`

**Trigger condition**: Parse an HTML tag with the same attribute name appearing twice with
different values. The first occurrence should be kept (HTML5 spec).

Minimal: `<div class="first" class="second">` — class attribute appears twice.
With correct code: class = "first"
With bug: class = "second"

**Why default strategy doesn't work**: Random HTML generation rarely produces duplicate
attributes. A test explicitly generating `<tag attr="v1" attr="v2">` is needed.

**Trigger probability with default strategy**: ~0.5% — must specifically construct
duplicate attribute HTML.

**Targeted strategy**: Generate two distinct values for the same attribute name, wrap in
an HTML element. `st.sampled_from(["class", "id", "href"])` for attribute names,
`st.text(alphanumeric)` for values. 100% trigger when values differ.
