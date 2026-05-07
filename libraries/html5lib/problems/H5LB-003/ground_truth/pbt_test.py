"""
Ground-truth PBT for H5LB-003 (html5lib 1.1)

Bugs:
  bug_1: _tokenizer.py cdataSectionState — CDATA termination condition [-2:] == ']]' changed to [-1:] == ']'
  bug_2: _tokenizer.py consumeNumberEntity — hex radix 16 changed to 10
  bug_3: _tokenizer.py consumeEntity — fromAttribute flipped to not fromAttribute
  bug_4: _tokenizer.py emitCurrentToken — duplicate attr data.update(raw[::-1]) changed to data.update(raw)

F→P requirement: each test FAILS on buggy version, PASSES on fixed version.
"""

from hypothesis import given, settings, assume
from hypothesis import strategies as st
import html5lib
import xml.etree.ElementTree as ET


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _svg_cdata_text(content):
    """Parse an SVG element with a CDATA section and return the text content."""
    html_str = f"<svg><![CDATA[{content}]]></svg>"
    doc = html5lib.parseFragment(html_str, namespaceHTMLElements=False)
    svg = doc.find(".//{http://www.w3.org/2000/svg}svg")
    if svg is None:
        return None
    # Collect all text nodes
    parts = []
    if svg.text:
        parts.append(svg.text)
    for child in svg:
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def _parse_hex_entity(hex_code):
    """Parse a hex character entity reference and return the decoded text."""
    html_str = f"<p>&#x{hex_code};</p>"
    doc = html5lib.parseFragment(html_str, namespaceHTMLElements=False)
    p = doc.find(".//p")
    return p.text if p is not None else None


def _get_attr_value(elem_html, attr_name):
    """Parse a fragment and get attribute value from the first element."""
    doc = html5lib.parseFragment(elem_html, namespaceHTMLElements=False)
    # Find any element (first child of fragment)
    for child in doc:
        val = child.get(attr_name)
        if val is not None:
            return val
    return None


# ---------------------------------------------------------------------------
# Bug 1: CDATA section termination — wrong condition truncates content
#
# Property: In SVG/MathML context, a CDATA section containing ']>' in its
# content must preserve that ']>' verbatim. The spec says only ']]>' terminates
# a CDATA section, not ']>'.
#
# Bug: condition data[-1][-2:] == ']]' changed to data[-1][-1:] == ']'
# This makes any ']>' in the content prematurely terminate the CDATA section,
# truncating the content at the first ']>'.
# ---------------------------------------------------------------------------

# Safe alphabet for CDATA content (no null chars, but ] and > are allowed)
_CDATA_CHARS = st.characters(
    blacklist_characters="\x00\ufffd",
    blacklist_categories=("Cs",),
)

@settings(max_examples=500, deadline=None)
@given(
    prefix=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
                   min_size=1, max_size=10),
    suffix=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
                   min_size=1, max_size=10),
)
def test_bug1_cdata_with_bracket_gt_preserved(prefix, suffix):
    """
    CDATA section content containing ']>' must not be truncated.

    The HTML5 spec (section 8.2.4.72) specifies that a CDATA section ends with
    ']]>'. The single sequence ']>' inside CDATA content should be kept verbatim.

    With correct code: the ']]' check only terminates at ']]>', preserving ']>' in content.
    With bug: ']>' triggers termination, and content after ']>' is lost.
    """
    content = prefix + "]>" + suffix
    # Ensure content doesn't accidentally contain ']]>' which would end CDATA naturally
    assume("]]>" not in content)

    result = _svg_cdata_text(content)

    assert result is not None, "SVG element not found in parsed output"
    # The text content must contain the ']>' sequence we embedded
    assert "]>" in result, (
        f"Bug 1 triggered: CDATA content '{content!r}' was truncated. "
        f"Expected text to contain ']>' but got: {result!r}"
    )
    # Also verify the full content is preserved
    assert result == content, (
        f"Bug 1 triggered: CDATA content not preserved. "
        f"Expected {content!r}, got {result!r}"
    )


@settings(max_examples=500, deadline=None)
@given(
    before=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
                   min_size=1, max_size=8),
    middle=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
                   min_size=1, max_size=8),
    after=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
                  min_size=1, max_size=8),
)
def test_bug1_cdata_multiple_bracket_gt(before, middle, after):
    """
    CDATA with multiple ']>' sequences must preserve all of them.
    Only ']]>' terminates the section.
    """
    content = before + "]>" + middle + "]>" + after
    assume("]]>" not in content)

    result = _svg_cdata_text(content)

    assert result is not None, "SVG element not found"
    assert result == content, (
        f"Bug 1 triggered: CDATA content with multiple ']>' not preserved. "
        f"Expected {content!r}, got {result!r}"
    )


# ---------------------------------------------------------------------------
# Bug 2: Hex numeric character reference radix error
#
# Property: A hex character reference &#xHH; must decode to chr(int('HH', 16)),
# not chr(int('HH', 10)). For digit-only hex codes, the two interpretations
# give different characters.
#
# Bug: radix = 16 changed to radix = 10 in consumeNumberEntity hex branch.
# This means &#x41; (=chr(0x41)='A') produces chr(41)=')' instead.
# ---------------------------------------------------------------------------

# Generate decimal-digit-only hex codepoints in printable ASCII range
# where hex vs decimal interpretation gives different results
# Hex codes using only digits 0-9: 0x10-0x39, 0x10-0x19 (avoid 0-9 range where hex==decimal for single digits)
# For 2-digit codes: 0x10 (hex=16,dec=10), 0x11(17,11),...0x19(25,19), 0x20(32,20),...0x39(57,39)

@settings(max_examples=500, deadline=None)
@given(
    # Use hex codes that are digit-only (0-9) in the range 0x10-0x39
    # so hex interpretation (16-57) differs from decimal (10-39)
    hex_code=st.sampled_from([
        "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
        "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
        "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
    ])
)
def test_bug2_hex_char_ref_digit_only(hex_code):
    """
    Hex character references with digit-only hex codes must decode correctly.

    &#xHH; should produce chr(int('HH', 16)). With the radix bug, it produces
    chr(int('HH', 10)), which for codes like '30' (hex=48='0', dec=30=RS) gives
    a completely different character.

    Example: &#x30; should be '0' (ASCII 48), not chr(30) (ASCII 30, RS control).
    Example: &#x39; should be '9' (ASCII 57), not chr(39) (ASCII 39, apostrophe).
    """
    expected_char = chr(int(hex_code, 16))
    result = _parse_hex_entity(hex_code)

    assert result is not None, f"Failed to parse &#x{hex_code};"
    assert result == expected_char, (
        f"Bug 2 triggered: &#x{hex_code}; decoded to {result!r} "
        f"but expected {expected_char!r} (chr(0x{hex_code})=chr({int(hex_code,16)})).\n"
        f"With radix=10 bug: chr({int(hex_code,10)}) = {chr(int(hex_code,10))!r}"
    )


@settings(max_examples=500, deadline=None)
@given(
    # Hex codes with letters (A-F): 0x1A, 0x2B, etc. — these cause ValueError with radix=10
    # Use only codes with exactly two chars where first or second is A-F digit
    hex_code=st.sampled_from([
        "41", "42", "43", "44", "45", "46", "47", "48", "49",
        "51", "52", "53", "54", "55", "56", "57", "58", "59",
        "61", "62", "63", "64", "65", "66", "67", "68", "69",
    ])
)
def test_bug2_hex_char_ref_pure_numeric_range(hex_code):
    """
    Hex character references for printable ASCII codes must decode correctly.
    These are all digit-only hex codes (no A-F letters) for values 65-105.
    &#x41; = 'A', &#x42; = 'B', etc. (hex interpretation).
    With radix=10 bug: &#x41; = chr(41) = ')'.
    """
    expected_char = chr(int(hex_code, 16))
    result = _parse_hex_entity(hex_code)

    assert result is not None, f"Failed to parse &#x{hex_code};"
    assert result == expected_char, (
        f"Bug 2 triggered: &#x{hex_code}; decoded to {result!r} "
        f"but expected {expected_char!r} (chr(0x{hex_code})=chr({int(hex_code,16)}))."
    )


# ---------------------------------------------------------------------------
# Bug 3: Named entity no-semicolon rule inverted for attribute vs content
#
# Property: In attribute values, a named entity without a trailing semicolon
# that is immediately followed by '=', an ASCII letter, or a digit must NOT
# be consumed — it should be treated as literal text. In text content, the
# same entity IS consumed.
#
# HTML5 spec (section 12.2.5.73 character reference state):
# "If the character reference was consumed as part of an attribute, and the
# last character matched is not a U+003B SEMICOLON character (;), and the
# next input character is either a U+003D EQUALS SIGN character (=) or an
# ASCII alphanumeric character, then, for historical reasons, flush code
# points consumed as a character reference and switch to the return state."
#
# Bug: 'fromAttribute' changed to 'not fromAttribute', inverting this rule:
# - Attribute values: entity IS consumed (wrong — breaks URL encoding)
# - Text content: entity is NOT consumed (wrong — entities left as literals)
# ---------------------------------------------------------------------------

@settings(max_examples=500, deadline=None)
@given(
    key=st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=8),
    val=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Nd")), min_size=1, max_size=8),
)
def test_bug3_no_semicolon_entity_in_attribute_preserved(key, val):
    """
    In an attribute value, a no-semicolon named entity followed by '=' must
    NOT be consumed. This is the HTML5 spec rule for legacy URL handling:
    href='?a=1&amp=foo' must keep '&amp=' as literal text, not decode it.

    With correct code: 'fromAttribute=True' keeps the entity literal when
    followed by '=' (or alphanumeric).
    With bug: 'not fromAttribute=True' = False, so the entity IS consumed,
    producing '&' instead of '&amp='.
    """
    # Build a URL-like attribute with no-semicolon entity followed by =
    # e.g., <a href="?key=val&amp=more">
    html_str = f'<a href="?{key}=1&amp={val}">'
    doc = html5lib.parseFragment(html_str, namespaceHTMLElements=False)
    a = doc.find(".//a")
    assume(a is not None)
    href = a.get("href")

    # The '&amp' without semicolon followed by '=' must NOT be consumed
    # So the href should contain '&amp=' literally, not just '&'
    assert href is not None, "href attribute not found"
    assert "&amp=" in href, (
        f"Bug 3 triggered: '&amp=' in attribute href was consumed as entity. "
        f"Input: {html_str!r}\nExpected href to contain '&amp=' literally, got: {href!r}\n"
        f"With the bug, 'fromAttribute' check is inverted, causing "
        f"no-semicolon entities in attributes to be wrongly consumed."
    )


@settings(max_examples=500, deadline=None)
@given(
    word1=st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=8),
    word2=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Nd")), min_size=1, max_size=8),
)
def test_bug3_no_semicolon_entity_in_content_consumed(word1, word2):
    """
    In text content (not an attribute), a no-semicolon named entity followed
    by '=' SHOULD be consumed (decoded). The HTML5 spec only exempts attribute
    values, not text content.

    With correct code: entity in content IS consumed (fromAttribute=False, so
    the 'fromAttribute' check fails, entity is decoded).
    With bug: 'not fromAttribute=False' = True, so entity is NOT consumed in
    content — it stays as literal '&amp=' text instead of '&='.
    """
    # In text content: &amp= should be consumed to '&=' (entity decoded)
    html_str = f"<p>{word1}&amp={word2}</p>"
    doc = html5lib.parseFragment(html_str, namespaceHTMLElements=False)
    p = doc.find(".//p")
    assume(p is not None)
    text = p.text or ""

    # The '&amp' in content (no semicolon, followed by '=') should be consumed
    # to '&', so the text should contain '&=' not '&amp='
    assert "&amp=" not in text, (
        f"Bug 3 triggered: '&amp=' in text content was NOT consumed as entity. "
        f"Input: {html_str!r}\nExpected text not to contain '&amp=' literally, got: {text!r}\n"
        f"With the bug, 'not fromAttribute' makes content entities stay unconsumed."
    )


# ---------------------------------------------------------------------------
# Bug 4: Duplicate attribute deduplication — last wins instead of first
#
# Property: When an HTML start tag has the same attribute name multiple times,
# only the first occurrence is kept (HTML5 spec section 12.2.4.33).
# The tokenizer must deduplicate keeping the first occurrence.
#
# Bug: data.update(raw[::-1]) changed to data.update(raw).
# The correct code reverses the list before update so that earlier items
# overwrite later items (first wins). The bug uses forward order, making
# later items overwrite earlier ones (last wins).
# ---------------------------------------------------------------------------

@settings(max_examples=500, deadline=None)
@given(
    attr_name=st.sampled_from(["class", "id", "href", "src", "style", "data-x", "title"]),
    first_val=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
        min_size=1, max_size=12
    ),
    second_val=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
        min_size=1, max_size=12
    ),
)
def test_bug4_duplicate_attr_first_wins(attr_name, first_val, second_val):
    """
    HTML5 spec section 12.2.4.33: when a start tag has duplicate attributes,
    only the first occurrence is used — subsequent occurrences are ignored.

    With correct code: data.update(raw[::-1]) reverses the raw list so that
    earlier attributes (lower indices) overwrite later ones when building the dict.
    With bug: data.update(raw) uses forward order, making later attributes overwrite
    earlier ones — so the LAST occurrence wins instead of the first.
    """
    assume(first_val != second_val)

    html_str = f'<div {attr_name}="{first_val}" {attr_name}="{second_val}"></div>'
    doc = html5lib.parseFragment(html_str, namespaceHTMLElements=False)
    div = doc.find(".//div")
    assume(div is not None)

    actual = div.get(attr_name)
    assert actual == first_val, (
        f"Bug 4 triggered: duplicate attribute '{attr_name}' should use first value "
        f"'{first_val}' but got '{actual}'. "
        f"HTML5 spec requires first occurrence to win. "
        f"With the bug, data.update(raw) makes the last value '{second_val}' win. "
        f"Input: {html_str!r}"
    )
