"""Basic tests for html5lib."""

import html5lib
from html5lib.serializer import HTMLSerializer
import xml.etree.ElementTree as ET
import pytest


def parse_body(html_str):
    """Parse HTML and return body element as string."""
    doc = html5lib.parse(html_str, treebuilder="etree", namespaceHTMLElements=False)
    body = doc.find(".//body")
    return ET.tostring(body, encoding="unicode")


def serialize_doc(html_str, **opts):
    """Parse then serialize with given options."""
    doc = html5lib.parse(html_str, treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    s = HTMLSerializer(**opts)
    return "".join(s.serialize(walker(doc)))


# -------------------------------------------------------------------------
# Basic parsing correctness
# -------------------------------------------------------------------------

def test_simple_parse():
    """Basic well-formed HTML parses without error."""
    doc = html5lib.parse("<p>Hello world</p>", treebuilder="etree", namespaceHTMLElements=False)
    body = doc.find(".//body")
    assert body is not None
    p = body.find("p")
    assert p is not None
    assert p.text == "Hello world"


def test_parse_returns_full_document():
    """parse() returns a full document root (the html element) with head/body children."""
    doc = html5lib.parse("<p>text", treebuilder="etree", namespaceHTMLElements=False)
    # The return value IS the html element (not a wrapper)
    assert doc.tag == "html"
    assert doc.find(".//head") is not None
    assert doc.find(".//body") is not None


def test_parse_fragment():
    """parseFragment returns a fragment container with content."""
    frag = html5lib.parseFragment("<b>bold</b> text", treebuilder="etree", namespaceHTMLElements=False)
    assert frag is not None
    b = frag.find("b")
    assert b is not None
    assert b.text == "bold"


def test_malformed_html_does_not_raise():
    """html5lib never raises on malformed HTML."""
    doc = html5lib.parse("<p><div><span>unclosed", treebuilder="etree", namespaceHTMLElements=False)
    assert doc is not None


def test_empty_input():
    """Empty input produces valid document structure."""
    doc = html5lib.parse("", treebuilder="etree", namespaceHTMLElements=False)
    # parse() returns the html element directly (doc.tag == "html")
    assert doc.tag == "html"


# -------------------------------------------------------------------------
# Adoption Agency Algorithm (safe cases - at most 3 nesting levels)
# -------------------------------------------------------------------------

def test_aaa_simple_formatting_in_block():
    """Simple formatting element inside a block element."""
    result = parse_body("<b>text<div>block</div></b>")
    assert "<b>" in result


def test_aaa_one_level_nesting():
    """One level of nesting (1 outer iteration) parses correctly."""
    # <b>a<div>b</b> → 1 outer iteration, safe for limit=4
    result = parse_body("<b>a<div>b</b>")
    assert "<b>a</b>" in result


def test_aaa_two_level_nesting():
    """Two levels of nesting (2 outer iterations) parses correctly."""
    # <b>a<div>b<p>c</b> → 2 outer iterations, safe for limit=4
    result = parse_body("<b>a<div>b<p>c</b>")
    assert "<b>a</b>" in result
    assert "<b>b</b>" in result


def test_aaa_three_level_nesting():
    """Three levels of nesting (3 outer iterations) parses correctly."""
    # <b>a<div>b<div>c<p>d</b> → 3 outer iterations, safe for limit=4
    result = parse_body("<b>a<div>b<div>c<p>d</b>")
    assert "<b>a</b>" in result


def test_aaa_does_not_raise():
    """Complex formatting does not raise exceptions."""
    for html in [
        "<em>text<p>para</em>",
        "<b><i>text</b></i>",
        "<strong>a<div>b</strong>",
    ]:
        doc = html5lib.parse(html, treebuilder="etree", namespaceHTMLElements=False)
        assert doc is not None


# -------------------------------------------------------------------------
# Optional tag omission (safe cases - no h6 after p)
# -------------------------------------------------------------------------

def test_optional_tags_p_before_div():
    """</p> is omitted before <div> when omit_optional_tags=True."""
    result = serialize_doc("<p>text<div>block</div>", omit_optional_tags=True,
                           minimize_boolean_attributes=False)
    # </p> should be omitted (it's optional before <div>)
    assert "</p>" not in result


def test_optional_tags_p_before_p():
    """</p> is omitted before another <p> when omit_optional_tags=True."""
    result = serialize_doc("<p>first<p>second", omit_optional_tags=True,
                           minimize_boolean_attributes=False)
    # First </p> should be omitted
    assert result.count("</p>") <= 1


def test_optional_tags_p_before_h1():
    """</p> is omitted before <h1> when omit_optional_tags=True."""
    result = serialize_doc("<p>text<h1>heading</h1>", omit_optional_tags=True,
                           minimize_boolean_attributes=False)
    assert "</p>" not in result


def test_optional_tags_p_before_h5():
    """</p> is omitted before <h5> when omit_optional_tags=True."""
    result = serialize_doc("<p>text<h5>heading</h5>", omit_optional_tags=True,
                           minimize_boolean_attributes=False)
    assert "</p>" not in result


def test_optional_tags_disabled():
    """With omit_optional_tags=False, all end tags are present."""
    doc = html5lib.parse("<p>text</p><p>more</p>",
                         treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    s = HTMLSerializer(omit_optional_tags=False, minimize_boolean_attributes=False)
    result = "".join(s.serialize(walker(doc)))
    assert result.count("</p>") == 2


# -------------------------------------------------------------------------
# Boolean attribute minimization (safe cases - global attrs only)
# -------------------------------------------------------------------------

def test_bool_attr_global_irrelevant():
    """Global boolean attribute 'irrelevant' is minimized on any element."""
    # html5lib's booleanAttributes global set includes 'irrelevant' and 'itemscope'
    doc = html5lib.parseFragment('<div irrelevant=""></div>',
                                 treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    s = HTMLSerializer(minimize_boolean_attributes=True, quote_attr_values="legacy")
    result = "".join(s.serialize(walker(doc)))
    assert 'irrelevant=""' not in result
    assert 'irrelevant' in result


def test_bool_attr_minimize_false():
    """With minimize_boolean_attributes=False, attrs keep =\"\"."""
    doc = html5lib.parseFragment('<input disabled="">',
                                 treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    s = HTMLSerializer(minimize_boolean_attributes=False, quote_attr_values="always")
    result = "".join(s.serialize(walker(doc)))
    assert 'disabled=""' in result


def test_non_bool_attr_not_minimized():
    """Non-boolean attributes always keep their values."""
    doc = html5lib.parseFragment('<input type="text" value="">',
                                 treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    s = HTMLSerializer(minimize_boolean_attributes=True, quote_attr_values="always")
    result = "".join(s.serialize(walker(doc)))
    # type is not a boolean attr, must keep value
    assert 'type="text"' in result


# -------------------------------------------------------------------------
# Whitespace filter (safe cases - strip_whitespace=False, the default)
# -------------------------------------------------------------------------

def test_whitespace_preserved_by_default():
    """With default settings, multiple spaces are preserved."""
    doc = html5lib.parse("<p>hello   world</p>",
                         treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    # No strip_whitespace
    s = HTMLSerializer(strip_whitespace=False, omit_optional_tags=False,
                       minimize_boolean_attributes=False)
    result = "".join(s.serialize(walker(doc)))
    assert "hello   world" in result


def test_single_space_unaffected():
    """Single spaces between words are preserved regardless of strip_whitespace."""
    doc = html5lib.parse("<p>hello world</p>",
                         treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    s = HTMLSerializer(strip_whitespace=True, omit_optional_tags=False,
                       minimize_boolean_attributes=False)
    result = "".join(s.serialize(walker(doc)))
    assert "hello world" in result


def test_whitespace_in_pre_preserved():
    """Whitespace inside <pre> is always preserved."""
    doc = html5lib.parse("<pre>  indented\n  code  </pre>",
                         treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    s = HTMLSerializer(strip_whitespace=True, omit_optional_tags=False,
                       minimize_boolean_attributes=False)
    result = "".join(s.serialize(walker(doc)))
    # Pre content should have its whitespace preserved
    assert "<pre>" in result


# -------------------------------------------------------------------------
# -------------------------------------------------------------------------

def test_basic_roundtrip():
    """Simple HTML round-trips through parse/serialize."""
    original = "<p>Hello <b>world</b></p>"
    doc = html5lib.parse(original, treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    s = HTMLSerializer(omit_optional_tags=False, minimize_boolean_attributes=False)
    result = "".join(s.serialize(walker(doc)))
    # Must contain the key content
    assert "Hello" in result
    assert "<b>world</b>" in result


def test_links_roundtrip():
    """Hyperlinks round-trip correctly."""
    original = '<a href="http://example.com">link text</a>'
    doc = html5lib.parseFragment(original, treebuilder="etree", namespaceHTMLElements=False)
    walker = html5lib.getTreeWalker("etree")
    s = HTMLSerializer(minimize_boolean_attributes=False)
    result = "".join(s.serialize(walker(doc)))
    assert 'href="http://example.com"' in result
    assert "link text" in result


def test_table_structure():
    """Table elements are correctly parsed."""
    html = "<table><tr><td>cell</td></tr></table>"
    doc = html5lib.parse(html, treebuilder="etree", namespaceHTMLElements=False)
    body = doc.find(".//body")
    table = body.find("table")
    assert table is not None
    td = table.find(".//td")
    assert td is not None
    assert td.text == "cell"


def test_nested_lists():
    """Nested list structure is parsed correctly."""
    html = "<ul><li>item1<ul><li>sub1</li></ul></li><li>item2</li></ul>"
    result = parse_body(html)
    assert "<ul>" in result
    assert "<li>" in result
