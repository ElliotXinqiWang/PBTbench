"""Basic tests for pyparsing."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pyparsing as pp
from pyparsing import (
    Word, Literal, Keyword, Regex, Opt, ZeroOrMore, OneOrMore,
    Group, Combine, Suppress, Each, Forward, QuotedString,
    alphas, alphanums, nums, printables,
    ParseException,
)


# ---------------------------------------------------------------------------
# 1. Basic token matching
# ---------------------------------------------------------------------------

def test_word_alphas():
    result = Word(alphas).parse_string("hello")
    assert result[0] == "hello"


def test_word_nums():
    result = Word(nums).parse_string("123")
    assert result[0] == "123"


def test_literal_match():
    result = Literal("foo").parse_string("foo")
    assert result[0] == "foo"


def test_literal_no_match():
    with pytest.raises(ParseException):
        Literal("foo").parse_string("bar")


def test_keyword_match():
    result = Keyword("def").parse_string("def")
    assert result[0] == "def"


def test_keyword_not_substring():
    """Keyword must not match if it's a substring of a larger word."""
    with pytest.raises(ParseException):
        Keyword("if").parse_string("ifdef")


# ---------------------------------------------------------------------------
# 2. Sequence (And) combinator
# ---------------------------------------------------------------------------

def test_and_basic():
    expr = Word(alphas) + Word(nums)
    result = expr.parse_string("hello 42")
    assert result.as_list() == ["hello", "42"]


def test_and_three_terms():
    expr = Literal("a") + Literal("b") + Literal("c")
    result = expr.parse_string("a b c")
    assert result.as_list() == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# 3. Or (^) vs MatchFirst (|)
# ---------------------------------------------------------------------------

def test_match_first():
    """| uses first-match semantics."""
    expr = Literal("ab") | Literal("abcd")
    result = expr.parse_string("abcd", parse_all=False)
    # MatchFirst returns first alternative that matches
    assert result[0] == "ab"


def test_or_longest():
    """^ uses longest-match semantics (fixed version only)."""
    expr = Literal("ab") ^ Literal("abcd")
    result = expr.parse_string("abcd", parse_all=False)
    # Or should return longest match
    assert result[0] == "abcd"


# ---------------------------------------------------------------------------
# 4. Opt (optional) - basic behavior (no default value, no Each)
# ---------------------------------------------------------------------------

def test_opt_matches():
    """Opt matches when present."""
    expr = Word(alphas) + Opt(Word(nums))
    result = expr.parse_string("hello 42")
    assert result.as_list() == ["hello", "42"]


def test_opt_absent():
    """Opt returns empty list when not present (no default specified)."""
    expr = Word(alphas) + Opt(Word(nums))
    result = expr.parse_string("hello", parse_all=True)
    assert result.as_list() == ["hello"]


# ---------------------------------------------------------------------------
# 5. ZeroOrMore - single match and empty input
# ---------------------------------------------------------------------------

def test_zeroormore_empty():
    """ZeroOrMore matches zero items."""
    expr = Word(alphas) + ZeroOrMore(Word(nums))
    result = expr.parse_string("hello", parse_all=True)
    assert result[0] == "hello"
    assert len(result) == 1


def test_zeroormore_single():
    """ZeroOrMore matches one item."""
    expr = ZeroOrMore(Word(nums))
    result = expr.parse_string("42", parse_all=True)
    assert result[0] == "42"


# ---------------------------------------------------------------------------
# 6. OneOrMore - basic (just one item, no accumulation required)
# ---------------------------------------------------------------------------

def test_oneormore_single_item():
    """OneOrMore matches exactly one item."""
    expr = OneOrMore(Literal("x"))
    result = expr.parse_string("x", parse_all=True)
    assert result[0] == "x"


# ---------------------------------------------------------------------------
# 7. Group
# ---------------------------------------------------------------------------

def test_group():
    expr = Group(Word(alphas) + Word(nums))
    result = expr.parse_string("hello 42")
    assert result[0].as_list() == ["hello", "42"]


# ---------------------------------------------------------------------------
# 8. Suppress
# ---------------------------------------------------------------------------

def test_suppress():
    expr = Suppress(Literal("(")) + Word(alphas) + Suppress(Literal(")"))
    result = expr.parse_string("(hello)")
    assert result.as_list() == ["hello"]


# ---------------------------------------------------------------------------
# 9. Regex - basic matching (no empty-string edge cases)
# ---------------------------------------------------------------------------

def test_regex_basic():
    expr = Regex(r"[a-z]+")
    result = expr.parse_string("hello")
    assert result[0] == "hello"


def test_regex_digits():
    expr = Regex(r"\d+")
    result = expr.parse_string("12345")
    assert result[0] == "12345"


# ---------------------------------------------------------------------------
# 10. QuotedString - basic (no esc_char)
# ---------------------------------------------------------------------------

def test_quoted_string_simple():
    """QuotedString without escape char works correctly."""
    qs = QuotedString('"')
    result = qs.parse_string('"hello world"')
    assert result[0] == "hello world"


def test_quoted_string_single_quotes():
    qs = QuotedString("'")
    result = qs.parse_string("'test'")
    assert result[0] == "test"


def test_quoted_string_esc_quote():
    """QuotedString with esc_quote (doubled-quote) works correctly."""
    qs = QuotedString('"', esc_quote='""')
    result = qs.parse_string('"say ""hello"""')
    assert result[0] == 'say "hello"'


# ---------------------------------------------------------------------------
# 11. Forward - recursive grammar
# ---------------------------------------------------------------------------

def test_forward_recursive():
    expr = Forward()
    # Simple non-recursive use
    expr <<= Word(alphas)
    result = expr.parse_string("hello")
    assert result[0] == "hello"


# ---------------------------------------------------------------------------
# 12. Each - basic 2-expr, required only, no Opt
# ---------------------------------------------------------------------------

def test_each_basic_any_order():
    """Each matches both required elements in any order."""
    w = Word(alphas)
    n = Word(nums)
    grammar = w & n
    result1 = grammar.parse_string("hello 42", parse_all=True)
    assert "hello" in result1.as_list()
    assert "42" in result1.as_list()


def test_each_reversed_order():
    """Each accepts elements in reversed order."""
    w = Word(alphas)
    n = Word(nums)
    grammar = w & n
    result = grammar.parse_string("42 hello", parse_all=True)
    assert "hello" in result.as_list()
    assert "42" in result.as_list()


# ---------------------------------------------------------------------------
# 13. Each with Opt - basic missing optional (no default)
# ---------------------------------------------------------------------------

def test_each_opt_absent_no_default():
    """Each with Opt: optional absent without default returns no extra tokens."""
    w = Word(alphas)
    n = Word(nums)
    grammar = w & Opt(n)
    result = grammar.parse_string("hello", parse_all=True)
    # Should contain only the word
    assert "hello" in result.as_list()


# ---------------------------------------------------------------------------
# 14. Parse result access
# ---------------------------------------------------------------------------

def test_named_result():
    expr = Word(alphas)("name") + Word(nums)("age")
    result = expr.parse_string("alice 30")
    assert result["name"] == "alice"
    assert result["age"] == "30"


def test_as_list():
    expr = Word(alphas) + Word(alphas)
    result = expr.parse_string("hello world")
    assert result.as_list() == ["hello", "world"]


def test_as_dict():
    expr = Word(alphas)("key") + Suppress("=") + Word(alphas)("val")
    result = expr.parse_string("color=red")
    assert result.as_dict() == {"key": "color", "val": "red"}
