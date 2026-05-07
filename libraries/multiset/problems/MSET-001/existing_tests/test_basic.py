"""Basic tests for multiset."""
import pytest
from multiset import Multiset


def test_construction_from_iterable():
    ms = Multiset('aabc')
    assert ms['a'] == 2
    assert ms['b'] == 1
    assert ms['c'] == 1
    assert ms['z'] == 0


def test_construction_from_dict():
    ms = Multiset({'x': 5, 'y': 3})
    assert ms['x'] == 5
    assert ms['y'] == 3
    assert ms['z'] == 0


def test_len_is_sum_of_multiplicities():
    ms = Multiset({'a': 3, 'b': 2, 'c': 1})
    assert len(ms) == 6

    empty = Multiset()
    assert len(empty) == 0


def test_containment_positive_multiplicity():
    ms = Multiset({'a': 2, 'b': 1})
    assert 'a' in ms
    assert 'b' in ms
    assert 'c' not in ms


def test_union_takes_max_multiplicity():
    a = Multiset({'x': 3, 'y': 1})
    b = Multiset({'x': 1, 'y': 4, 'z': 2})
    result = a | b
    assert result['x'] == 3
    assert result['y'] == 4
    assert result['z'] == 2


def test_intersection_takes_min_multiplicity():
    a = Multiset({'x': 3, 'y': 1, 'w': 5})
    b = Multiset({'x': 1, 'y': 4, 'z': 2})
    result = a & b
    assert result['x'] == 1
    assert result['y'] == 1
    assert result['z'] == 0
    assert result['w'] == 0


def test_addition_sums_multiplicities():
    a = Multiset({'a': 2, 'b': 1})
    b = Multiset({'a': 1, 'c': 3})
    result = a + b
    assert result['a'] == 3
    assert result['b'] == 1
    assert result['c'] == 3


def test_subtraction_removes_element_when_fully_cancelled():
    # Subtraction (ms - other) clips at 0 and removes the element.
    # This does NOT go through the combine() zero-cancellation path;
    # subtraction uses a separate code path that always clips to 0.
    a = Multiset({'a': 2, 'b': 3})
    b = Multiset({'b': 3})
    result = a - b
    assert 'b' not in result
    assert result['b'] == 0
    assert result['a'] == 2


def test_inclusion_exclusion_identity():
    a = Multiset({'a': 3, 'b': 2})
    b = Multiset({'a': 1, 'b': 4, 'c': 2})
    assert len(a | b) + len(a & b) == len(a) + len(b)


def test_combine_with_positive_delta():
    # combine() adding elements — does not touch zero-cancellation path.
    ms = Multiset({'a': 2})
    result = ms.combine({'a': 3, 'b': 1})
    assert result['a'] == 5
    assert result['b'] == 1
    assert len(result) == 6


def test_internal_elements_are_positive():
    # All stored multiplicities must be strictly positive integers.
    ms = Multiset({'a': 3, 'b': 1, 'c': 5})
    for elem, mult in ms._elements.items():
        assert mult > 0, f"Element '{elem}' has non-positive multiplicity {mult}"
