# html5lib 1.1 — HTML5 Tokenizer (`_tokenizer.py`) API Reference

## Overview

The html5lib tokenizer (`html5lib._tokenizer.HTMLTokenizer`) implements the HTML5 tokenization
algorithm as specified in the WHATWG HTML5 specification §8.2.4. It operates as a state machine,
reading input characters and emitting token objects consumed by the tree builder.

The tokenizer handles:
- **Data state** (`dataState`): normal HTML text, entity references
- **Tag states**: tag names, attributes, self-closing tags
- **RCDATA state** (`rcdataState`): content of `<title>`, `<textarea>` (entity references decoded, no tag processing)
- **RAWTEXT state** (`rawtextState`): content of `<style>`, `<noscript>`, `<iframe>` (no entity decoding, no tag processing)
- **Script data state** (`scriptDataState`): content of `<script>`
- **Character reference states**: processing of `&name;`, `&#NNN;`, `&#xHH;`
- **CDATA section state** (`cdataSectionState`): CDATA sections in foreign content (SVG, MathML)
- **Comment and DOCTYPE states**

The tokenizer does **not** require direct usage — it is invoked automatically by `html5lib.parse()`
and `html5lib.parseFragment()`.

---

## Key Invariants and Specification Requirements

### 1. Character Reference Decoding

The HTML5 spec defines three forms of character references:

#### Named character references
- `&amp;` → `&`, `&lt;` → `<`, `&gt;` → `>`, `&quot;` → `"`, `&nbsp;` → U+00A0
- Named references must end with `;` to be reliably consumed
- Over 2,000 named references are supported

**Invariant**: A named character reference `&name;` (with semicolon) must always be decoded to
its defined character value, both in text content and in attribute values.

#### Decimal numeric character references
- `&#NNN;` where NNN is a decimal integer
- `&#65;` → `A` (chr(65)), `&#32;` → space (chr(32)), `&#9;` → tab
- The decoded character is `chr(decimal_value)` for valid codepoints

**Invariant**: `&#NNN;` must produce `chr(NNN)` for any valid integer NNN.

#### Hexadecimal numeric character references
- `&#xHH;` or `&#XHH;` where HH is hexadecimal (digits 0-9, letters a-f, A-F)
- `&#x41;` → `A` (chr(0x41) = chr(65)), `&#x20;` → space (chr(0x20) = chr(32))
- `&#xFF;` → ÿ (chr(255)), `&#x100;` → Ā (chr(256))
- The decoded character is `chr(int(HH, 16))` — hexadecimal interpretation

**Invariant**: `&#xHH;` must produce `chr(int('HH', 16))`, NOT `chr(int('HH', 10))`.
For example, `&#x30;` = chr(0x30) = chr(48) = '0', not chr(30) = record separator.
Similarly, `&#x41;` = chr(0x41) = chr(65) = 'A', not chr(41) = ')'.

Both `&#x41;` and `&#X41;` (uppercase X) are valid and must produce the same result.

### 2. Named Entities Without Semicolons in Attribute Values

The HTML5 spec includes a special rule for named entity references without a semicolon when
appearing inside an attribute value:

> If the character reference was consumed as part of an attribute, and the last character
> matched is not a U+003B SEMICOLON (`;`), and the next input character is either
> U+003D EQUALS SIGN (`=`) or an ASCII alphanumeric character, then the entity is NOT
> consumed — the characters are treated as literal text.

This rule exists to handle legacy HTML with URL parameters like `href="?a=1&amp=foo"` where
`&amp` (no semicolon) followed by `=` should be treated as the literal string `&amp=`, not
decoded to `&=`.

**Invariant (attribute values)**: In an HTML attribute value, a named entity reference without a
trailing semicolon that is immediately followed by `=`, an ASCII letter, or a digit must NOT be
consumed as an entity. The literal text `&name=...` is preserved.

Examples:
```html
<!-- href must contain literal '&amp=' not just '&' -->
<a href="?key=1&amp=value">   →  href = "?key=1&amp=value"
<a href="?key=1&amp=">        →  href = "?key=1&amp="
<a href="?q=1&lt=test">       →  href = "?q=1&lt=test"
```

**Invariant (text content)**: In text content (not an attribute), the same no-semicolon entity
followed by `=` IS consumed. `<p>text &amp= more</p>` produces text `text &= more` (entity
decoded to `&`, then literal `=`).

The difference between attribute and content behavior is spec-defined:

```
Attribute context:  &amp=val  →  "&amp=val"  (NOT consumed)
Content context:    &amp=val  →  "&=val"     (consumed, & is the entity result)
```

### 3. CDATA Sections in Foreign Content

In SVG and MathML content ("foreign content"), CDATA sections are allowed:
```html
<svg><![CDATA[ content here ]]></svg>
```

The CDATA section begins with `<![CDATA[` and ends with the exact three-character sequence `]]>`.

**Key invariant**: Only `]]>` terminates a CDATA section. The two-character sequence `]>` is NOT
a terminator and must appear literally in the output:

```html
<!-- These CDATA contents must be preserved verbatim: -->
<svg><![CDATA[text]>more]]></svg>     →  text content = "text]>more"
<svg><![CDATA[a]>b]>c]]></svg>        →  text content = "a]>b]>c"
<svg><![CDATA[1]2]]></svg>            →  text content = "1]2"  (single ] is fine)
<svg><![CDATA[simple]]></svg>         →  text content = "simple"
```

CDATA sections preserve their content literally — no entity decoding, no tag processing.
All characters including `<`, `&`, `>` (when not part of `]]>`) appear in output as-is:

```html
<svg><![CDATA[<b>bold</b> & more]]></svg>
→  text content = "<b>bold</b> & more"  (literal, not markup)
```

CDATA sections in SVG require an explicit SVG context — they are not recognized in plain HTML.

### 4. Duplicate Attribute Handling

HTML5 spec section 12.2.4.33 specifies that when a start tag contains the same attribute name
more than once, only the **first** occurrence is used. Subsequent occurrences with the same name
are silently ignored.

**Invariant**: For duplicate attributes, the first value wins:
```html
<div class="first" class="second">   →  class = "first"
<a href="/first" href="/second">     →  href = "/first"
<input type="text" type="password">  →  type = "text"
```

This applies to all attributes on all elements.

### 5. Attribute Name Normalization

All attribute names are normalized to lowercase by the tokenizer:
```html
<div CLASS="value">     →  class = "value"
<a HREF="/path">        →  href = "/path"
<input TYPE="text">     →  type = "text"
```

### 6. Tag Name Normalization

All tag names are normalized to lowercase:
```html
<DIV> = <div>, <P> = <p>, </TITLE> = </title>
```

End tags in RCDATA context (`<title>`, `<textarea>`) must also be recognized case-insensitively:
`</TITLE>` closes `<title>` just as `</title>` does.

---

## API Usage

### Parsing HTML documents

```python
import html5lib

# Parse a complete HTML document
doc = html5lib.parse("<html><body><p>hello</p></body></html>",
                     treebuilder="etree", namespaceHTMLElements=False)

# Parse an HTML fragment
fragment = html5lib.parseFragment("<p>hello &amp; world</p>",
                                  treebuilder="etree", namespaceHTMLElements=False)
```

### Using the HTMLParser directly

```python
parser = html5lib.HTMLParser(treebuilder="etree", namespaceHTMLElements=False)
doc = parser.parse("<html>...</html>")
fragment = parser.parseFragment("<p>...</p>")
```

### Character reference examples

```python
import html5lib, xml.etree.ElementTree as ET

# Named entities
doc = html5lib.parseFragment("<p>&amp;&lt;&gt;&nbsp;</p>", namespaceHTMLElements=False)
p = doc.find(".//p")
# p.text = '&<>' + '\xa0'

# Decimal numeric references
doc = html5lib.parseFragment("<p>&#65;&#66;&#67;</p>", namespaceHTMLElements=False)
p = doc.find(".//p")
# p.text = 'ABC'

# Hex numeric references
doc = html5lib.parseFragment("<p>&#x41;&#x42;&#x43;</p>", namespaceHTMLElements=False)
p = doc.find(".//p")
# p.text = 'ABC'  (0x41=65='A', 0x42=66='B', 0x43=67='C')

# Mixed hex and decimal for same codepoint
assert html5lib.parseFragment("<p>&#x41;</p>", namespaceHTMLElements=False).find(".//p").text == \
       html5lib.parseFragment("<p>&#65;</p>", namespaceHTMLElements=False).find(".//p").text
# Both must equal 'A'
```

### Attribute value examples

```python
import html5lib

# Entity in attribute with semicolon — always consumed
doc = html5lib.parseFragment('<a href="?a=1&amp;b=2">', namespaceHTMLElements=False)
# href = '?a=1&b=2'  (&amp; consumed)

# No-semicolon entity in attribute followed by = — NOT consumed
doc = html5lib.parseFragment('<a href="?a=1&amp=b">', namespaceHTMLElements=False)
# href = '?a=1&amp=b'  (literal, &amp NOT consumed because followed by =)

# No-semicolon entity in text content followed by = — IS consumed
doc = html5lib.parseFragment('<p>a &amp= b</p>', namespaceHTMLElements=False)
# p.text = 'a &= b'  (&amp consumed to &, then literal =)
```

### Duplicate attribute handling

```python
import html5lib

# First occurrence wins
doc = html5lib.parseFragment('<div class="first" class="second">', namespaceHTMLElements=False)
div = doc.find(".//div")
# div.get("class") == "first"  (second ignored per HTML5 spec)
```

### CDATA sections in SVG

```python
import html5lib, xml.etree.ElementTree as ET

# Basic CDATA
doc = html5lib.parseFragment("<svg><![CDATA[hello world]]></svg>",
                              namespaceHTMLElements=False)
svg = doc.find(".//{http://www.w3.org/2000/svg}svg")
# svg.text == "hello world"

# CDATA with ]> inside — preserved verbatim
doc = html5lib.parseFragment("<svg><![CDATA[text]>more]]></svg>",
                              namespaceHTMLElements=False)
svg = doc.find(".//{http://www.w3.org/2000/svg}svg")
# svg.text == "text]>more"  (NOT "text" — ]> does NOT terminate CDATA)

# CDATA with markup characters — preserved as-is
doc = html5lib.parseFragment("<svg><![CDATA[<b>bold</b>]]></svg>",
                              namespaceHTMLElements=False)
svg = doc.find(".//{http://www.w3.org/2000/svg}svg")
# svg.text == "<b>bold</b>"  (literal text, no elements created)
```

---

## Tokenizer State Machine Overview

The tokenizer implements ~80 states corresponding to the HTML5 spec's tokenization algorithm.
Key state transitions:

| State | Trigger | Description |
|---|---|---|
| `dataState` | (initial) | Normal text; `&` → entity, `<` → tag |
| `entityDataState` | `&` in data | Processes named/numeric entity in data context |
| `rcdataState` | entering `<title>`, `<textarea>` | Text only; `&` → entity (decoded), `<` starts end-tag search |
| `characterReferenceInRcdata` | `&` in rcdata | Processes entity in RCDATA context; returns to `rcdataState` |
| `rawtextState` | entering `<style>`, `<noscript>`, etc. | Text only; no entity processing, no tag processing |
| `scriptDataState` | entering `<script>` | Special script content handling |
| `tagOpenState` | `<` in data | Reading start of a tag |
| `tagNameState` | tag letter in tagOpen | Reading tag name |
| `attributeValueDoubleQuotedState` | `"` in beforeAttrValue | Reading attr value between double quotes |
| `attributeValueSingleQuotedState` | `'` in beforeAttrValue | Reading attr value between single quotes |
| `cdataSectionState` | `<![CDATA[` in foreign content | Reading CDATA section content until `]]>` |

### Entity processing in different contexts

| Context | Entity decoded? | Example |
|---|---|---|
| Data (`<p>`, `<body>`, etc.) | Yes | `&amp;` → `&` |
| RCDATA (`<title>`, `<textarea>`) | Yes | `&amp;` → `&` |
| RAWTEXT (`<style>`, `<noscript>`) | **No** | `&amp;` stays literal |
| Script data (`<script>`) | **No** | `&amp;` stays literal |
| CDATA sections | **No** | `&amp;` stays literal |
| Attribute values (any) | Yes, unless no-; + followed by `=`/alnum | `&amp;` → `&` |

---

## Testing Patterns

### Property: Hex character references decode correctly

```python
# For any hex code HH, &#xHH; must equal chr(int('HH', 16))
for hex_code in ["10", "20", "30", "41", "42", "61"]:
    expected = chr(int(hex_code, 16))
    doc = html5lib.parseFragment(f"<p>&#x{hex_code};</p>", namespaceHTMLElements=False)
    assert doc.find(".//p").text == expected
```

### Property: CDATA content is verbatim in SVG

```python
# Any content (without ']]>') in CDATA must be preserved
content = "some text with ]> and more"
doc = html5lib.parseFragment(f"<svg><![CDATA[{content}]]></svg>",
                              namespaceHTMLElements=False)
svg = doc.find(".//{http://www.w3.org/2000/svg}svg")
assert svg.text == content
```

### Property: No-semicolon entities in attributes not consumed when followed by =

```python
# &amp= in href attribute must stay literal
doc = html5lib.parseFragment('<a href="?q=x&amp=y">', namespaceHTMLElements=False)
assert "&amp=" in doc.find(".//a").get("href", "")
```

### Property: First duplicate attribute wins

```python
doc = html5lib.parseFragment('<div class="a" class="b">', namespaceHTMLElements=False)
assert doc.find(".//div").get("class") == "a"
```
