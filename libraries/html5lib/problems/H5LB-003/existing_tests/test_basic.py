"""Basic tests for html5lib."""
import pytest
import html5lib
import xml.etree.ElementTree as ET


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def parse_fragment(html_str):
    return html5lib.parseFragment(html_str, namespaceHTMLElements=False)


def get_text(doc, tag):
    el = doc.find(f".//{tag}")
    return el.text if el is not None else None


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_simple_element():
    """Parse a simple element."""
    doc = parse_fragment("<p>hello</p>")
    assert get_text(doc, "p") == "hello"


def test_nested_elements():
    """Parse nested elements."""
    doc = parse_fragment("<div><p>text</p></div>")
    p = doc.find(".//p")
    assert p is not None
    assert p.text == "text"


def test_named_entity_amp():
    """Named entity &amp; decodes to &."""
    doc = parse_fragment("<p>&amp;</p>")
    assert get_text(doc, "p") == "&"


def test_named_entity_lt():
    """Named entity &lt; decodes to <."""
    doc = parse_fragment("<p>&lt;</p>")
    assert get_text(doc, "p") == "<"


def test_named_entity_gt():
    """Named entity &gt; decodes to >."""
    doc = parse_fragment("<p>&gt;</p>")
    assert get_text(doc, "p") == ">"


def test_named_entity_with_semicolon_in_attribute():
    """Named entity with semicolon in attribute is always consumed."""
    doc = parse_fragment('<a href="?a=1&amp;b=2">')
    a = doc.find(".//a")
    assert a is not None
    assert "&" in a.get("href", "")


def test_decimal_char_ref():
    """Decimal numeric character reference decodes correctly."""
    doc = parse_fragment("<p>&#65;</p>")
    assert get_text(doc, "p") == "A"


def test_decimal_char_ref_space():
    """Decimal &#32; is a space."""
    doc = parse_fragment("<p>&#32;</p>")
    assert get_text(doc, "p") == " "


def test_tag_name_lowercase():
    """Tag names are normalized to lowercase."""
    doc = parse_fragment("<DIV><P>text</P></DIV>")
    div = doc.find(".//div")
    assert div is not None


def test_attribute_simple():
    """Simple attribute value is parsed correctly."""
    doc = parse_fragment('<a href="/path/to/page">')
    a = doc.find(".//a")
    assert a is not None
    assert a.get("href") == "/path/to/page"


def test_attribute_double_quoted():
    """Double-quoted attributes work."""
    doc = parse_fragment('<div class="main">')
    div = doc.find(".//div")
    assert div is not None
    assert div.get("class") == "main"


def test_attribute_single_quoted():
    """Single-quoted attributes work."""
    doc = parse_fragment("<div class='main'>")
    div = doc.find(".//div")
    assert div is not None
    assert div.get("class") == "main"


def test_svg_element_basic():
    """SVG element parsed correctly."""
    doc = parse_fragment("<svg></svg>")
    svg = doc.find(".//{http://www.w3.org/2000/svg}svg")
    assert svg is not None


def test_svg_cdata_simple():
    """CDATA section in SVG with no special content works."""
    doc = parse_fragment("<svg><![CDATA[hello world]]></svg>")
    svg = doc.find(".//{http://www.w3.org/2000/svg}svg")
    assert svg is not None
    assert svg.text == "hello world"


def test_svg_cdata_with_bracket():
    """CDATA section with single ] (not followed by >) works."""
    doc = parse_fragment("<svg><![CDATA[text]more]]></svg>")
    svg = doc.find(".//{http://www.w3.org/2000/svg}svg")
    assert svg is not None
    assert svg.text == "text]more"


def test_title_entity():
    """Entity inside title (RCDATA) decodes correctly."""
    doc = parse_fragment("<title>&amp; test</title>")
    title = doc.find(".//title")
    assert title is not None
    assert title.text == "& test"


def test_comment_parsing():
    """Comments are parsed correctly."""
    doc = parse_fragment("<!-- comment --><p>text</p>")
    p = doc.find(".//p")
    assert p is not None
    assert p.text == "text"


def test_self_closing_void():
    """Self-closing void elements parse correctly."""
    doc = parse_fragment("<p>before<br>after</p>")
    p = doc.find(".//p")
    assert p is not None


def test_attribute_name_lowercase():
    """Attribute names are normalized to lowercase."""
    doc = parse_fragment('<div CLASS="value">')
    div = doc.find(".//div")
    assert div is not None
    assert div.get("class") == "value"
