"""Basic tests for more_itertools."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from more_itertools import (
    numeric_range, collapse, mark_ends, zip_offset
)


def test_numeric_range_forward_iteration():
    """Test Numeric range forward iteration."""
    nr = numeric_range(0, 5, 1)
    assert list(nr) == [0, 1, 2, 3, 4]


def test_numeric_range_contains():
    """__contains__ is independent of __reversed__."""
    nr = numeric_range(0, 10, 2)
    assert 4 in nr
    assert 5 not in nr
    assert 0 in nr
    assert 8 in nr
    assert 10 not in nr


def test_numeric_range_len():
    """Test Numeric range len."""
    assert len(numeric_range(0, 10, 1)) == 10
    assert len(numeric_range(0, 10, 2)) == 5
    assert len(numeric_range(5, 0, -1)) == 5
    assert len(numeric_range(0, 0)) == 0


def test_numeric_range_getitem():
    """Test Numeric range getitem."""
    nr = numeric_range(0, 10, 1)
    assert nr[0] == 0
    assert nr[9] == 9
    assert nr[-1] == 9


def test_numeric_range_step():
    """Fractional step works correctly for forward iteration."""
    from fractions import Fraction
    nr = numeric_range(Fraction(0), Fraction(1), Fraction(1, 4))
    assert list(nr) == [Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)]


def test_collapse_basic():
    """Test Collapse basic."""
    result = list(collapse([(1, 2), ([3, 4], [[5], [6]])]))
    assert result == [1, 2, 3, 4, 5, 6]


def test_collapse_strings_not_collapsed():
    """Strings are never collapsed, regardless of levels."""
    result = list(collapse(['hello', ['world']]))
    assert result == ['hello', 'world']


def test_collapse_empty():
    """Empty input returns empty output."""
    assert list(collapse([])) == []


def test_collapse_flat_input():
    """Already-flat input returns the same elements."""
    assert list(collapse([1, 2, 3])) == [1, 2, 3]


def test_mark_ends_is_last_multi():
    """Test Mark ends is last multi."""
    result = list(mark_ends([1, 2, 3, 4]))
    # is_last: only last element should be True
    is_last_flags = [t[1] for t in result]
    assert is_last_flags == [False, False, False, True]


def test_mark_ends_items_preserved():
    """All items are yielded in order."""
    items = [10, 20, 30, 40]
    result = list(mark_ends(items))
    assert [t[2] for t in result] == items


def test_mark_ends_empty():
    """Empty iterable yields nothing."""
    assert list(mark_ends([])) == []


def test_mark_ends_tuple_length():
    """Each element is a 3-tuple."""
    for t in mark_ends('abc'):
        assert len(t) == 3


def test_zip_offset_zero_offset():
    """Test Zip offset zero offset."""
    result = list(zip_offset('abc', '123', offsets=(0, 0)))
    assert result == [('a', '1'), ('b', '2'), ('c', '3')]


def test_zip_offset_negative_offset():
    """Test Zip offset negative offset."""
    result = list(zip_offset('abc', 'xyz', offsets=(0, -1), fillvalue='_'))
    # second iterable gets '_' prepended, so zip with 'abc'[0..2] and ['_','x','y']
    assert result == [('a', '_'), ('b', 'x'), ('c', 'y')]


def test_zip_offset_mixed_zero_negative():
    """Mix of zero and negative offsets."""
    result = list(zip_offset([1, 2, 3, 4], [10, 20], offsets=(0, -1), fillvalue=0))
    # second: [0, 10, 20]; zip with [1,2,3,4] -> [(1,0),(2,10),(3,20)]
    assert result == [(1, 0), (2, 10), (3, 20)]
