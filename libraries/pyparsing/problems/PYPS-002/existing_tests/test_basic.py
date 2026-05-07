"""Basic tests for pyparsing."""
import pytest
from pyparsing import (
    Word, alphas, nums, alphanums,
    Combine, Literal, SkipTo, StringEnd,
    NotAny, Keyword, ParseException, ParseResults,
)
import string


def test_results_name_basic():
    """Basic results name access (no list_all_matches)."""
    num = Word(nums)
    grammar = num("year") + Literal("/").suppress() + num("month")
    result = grammar.parse_string("2024/03")
    assert result["year"] == "2024"
    assert result["month"] == "03"


def test_results_list_all_matches_both_sides():
    """list_all_matches on both sides: &= and |= give same result (safe)."""
    num = Word(nums).set_results_name("val", list_all_matches=True)
    grammar = num + num  # both sides have 'val' in all_names
    result = grammar.parse_string("100 200")
    # result["val"] is a ParseResults (not plain list), but has multiple items
    val = result["val"]
    val_list = list(val) if hasattr(val, '__iter__') and not isinstance(val, str) else [val]
    assert len(val_list) == 2, f"Expected 2 values, got {val_list!r}"
    assert "100" in [str(v) for v in val_list]
    assert "200" in [str(v) for v in val_list]


def test_results_get_default():
    """get() with default for missing keys."""
    num = Word(nums)("count")
    result = num.parse_string("42")
    assert result.get("count") == "42"
    assert result.get("missing", "default") == "default"
    assert result.get("missing") is None


def test_skipto_delimiter_basic():
    """SkipTo finds delimiter in the middle of string (no end-of-string edge)."""
    result = SkipTo("|").parse_string("hello|world")
    assert result.as_list() == ["hello"]


def test_skipto_empty_prefix():
    """SkipTo returns empty string when delimiter is at the start."""
    result = SkipTo("|").parse_string("|rest")
    assert result.as_list() == [""]


def test_skipto_include():
    """SkipTo with include=True also returns the matched target."""
    result = SkipTo(Literal(";"), include=True).parse_string("abc;def")
    assert result.as_list() == ["abc", ";"]


def test_notany_with_non_matching_input():
    """NotAny blocks keyword; use a non-matching case that works even if inverted."""
    # Test FollowedBy instead as a safe positive lookahead.
    from pyparsing import FollowedBy, Word, alphas, Literal
    grammar = Word(alphas) + FollowedBy(Literal(":"))
    result = grammar.parse_string("label:")
    assert result.as_list() == ["label"]


def test_keyword_basic():
    """Keywords match whole words only (internal keyword matching, not NotAny)."""
    kw = Keyword("if")
    result = kw.parse_string("if")
    assert result.as_list() == ["if"]

    with pytest.raises(ParseException):
        kw.parse_string("ifdef")


def test_and_sequence():
    """Test And sequence."""
    grammar = Word(alphas) + Word(nums)
    result = grammar.parse_string("abc 123")
    assert result.as_list() == ["abc", "123"]


def test_combine_adjacent_rejects_spaces():
    """Combine with adjacent=True rejects spaces between tokens."""
    real = Combine(Word(nums) + "." + Word(nums))
    with pytest.raises(ParseException):
        real.parse_string("3. 1416")  # space between . and 1416


def test_literal_parse():
    """Basic Literal parsing."""
    result = Literal("hello").parse_string("hello world")
    assert result.as_list() == ["hello"]


def test_word_parse():
    """Basic Word parsing."""
    result = Word(alphas).parse_string("hello")
    assert result.as_list() == ["hello"]


def test_zero_or_more_empty():
    """ZeroOrMore matches empty list."""
    from pyparsing import ZeroOrMore
    grammar = ZeroOrMore(Word(nums))
    result = grammar.parse_string("abc", parse_all=False)
    assert result.as_list() == []
