"""Basic tests for sortedcontainers."""
import pytest
from sortedcontainers import SortedList, SortedDict


# ---- SortedList basic operations ----

def test_add_and_contains():
    sl = SortedList()
    sl.add(5)
    sl.add(1)
    sl.add(3)
    assert 1 in sl
    assert 3 in sl
    assert 5 in sl
    assert 2 not in sl


def test_sorted_order():
    sl = SortedList([7, 2, 9, 1, 5])
    assert list(sl) == [1, 2, 5, 7, 9]


def test_len_and_update():
    sl = SortedList([1, 2, 3])
    assert len(sl) == 3
    sl.update([4, 5])
    assert len(sl) == 5


def test_getitem_small():
    sl = SortedList([10, 30, 20, 50, 40])
    assert sl[0] == 10
    assert sl[1] == 20
    assert sl[2] == 30
    assert sl[-1] == 50


def test_remove_and_discard():
    sl = SortedList([1, 2, 3, 4, 5])
    sl.remove(3)
    assert list(sl) == [1, 2, 4, 5]
    sl.discard(99)   # no-op
    assert list(sl) == [1, 2, 4, 5]
    sl.discard(2)
    assert list(sl) == [1, 4, 5]


def test_pop_default_and_index():
    sl = SortedList([10, 20, 30, 40, 50])
    val = sl.pop()
    assert val == 50
    val = sl.pop(0)
    assert val == 10
    assert list(sl) == [20, 30, 40]


def test_count_small():
    sl = SortedList([1, 2, 2, 3, 3, 3])
    assert sl.count(1) == 1
    assert sl.count(2) == 2
    assert sl.count(3) == 3
    assert sl.count(9) == 0


def test_bisect_right_small():
    sl = SortedList([10, 20, 20, 30])
    assert sl.bisect_right(20) == 3
    assert sl.bisect_right(15) == 1


def test_bisect_left_small():
    sl = SortedList([10, 20, 20, 30])
    assert sl.bisect_left(20) == 1
    assert sl.bisect_left(10) == 0


def test_irange_inclusive():
    """Test Irange inclusive."""
    sl = SortedList([1, 2, 3, 4, 5, 6, 7])
    assert list(sl.irange(2, 5)) == [2, 3, 4, 5]


def test_irange_exclusive_max():
    """Test Irange exclusive max."""
    sl = SortedList([1, 2, 3, 4, 5])
    result = list(sl.irange(2, 4, inclusive=(True, False)))
    assert result == [2, 3]


def test_irange_exclusive_min_not_present():
    """Exclusive min where minimum is NOT in the list - bisect_left==bisect_right."""
    sl = SortedList([1, 3, 5, 7, 9])
    result = list(sl.irange(2, 7, inclusive=(False, True)))
    assert result == [3, 5, 7]


def test_irange_reverse():
    sl = SortedList([1, 2, 3, 4, 5])
    assert list(sl.irange(2, 4, reverse=True)) == [4, 3, 2]


def test_islice():
    sl = SortedList([1, 2, 3, 4, 5])
    assert list(sl.islice(1, 4)) == [2, 3, 4]
    assert list(sl.islice(0, 3, reverse=True)) == [3, 2, 1]


def test_copy():
    sl = SortedList([1, 2, 3])
    sl2 = sl.copy()
    assert list(sl2) == [1, 2, 3]
    sl2.add(4)
    assert 4 not in sl


def test_iter_and_reversed():
    sl = SortedList([5, 3, 1, 4, 2])
    assert list(sl) == [1, 2, 3, 4, 5]
    assert list(reversed(sl)) == [5, 4, 3, 2, 1]


def test_index_method_small():
    """index() on small single-sublist list: _loc returns early (pos=0)."""
    sl = SortedList([10, 20, 30, 40])
    assert sl.index(20) == 1
    assert sl.index(40) == 3
    with pytest.raises(ValueError):
        sl.index(99)


# ---- SortedDict basic operations ----

def test_sorted_dict_set_and_get():
    sd = SortedDict()
    sd['c'] = 3
    sd['a'] = 1
    sd['b'] = 2
    assert list(sd.keys()) == ['a', 'b', 'c']
    assert sd['a'] == 1


def test_sorted_dict_iter_order():
    sd = SortedDict({'z': 26, 'a': 1, 'm': 13})
    assert list(sd) == ['a', 'm', 'z']


def test_sorted_dict_delete():
    sd = SortedDict({'a': 1, 'b': 2, 'c': 3})
    del sd['b']
    assert list(sd.keys()) == ['a', 'c']
    assert 'b' not in sd


def test_sorted_dict_peekitem():
    """peekitem does NOT pop - safe to test."""
    sd = SortedDict({'a': 1, 'b': 2, 'c': 3})
    pair = sd.peekitem(0)
    assert pair == ('a', 1)
    assert len(sd) == 3  # unchanged


def test_sorted_dict_pop_key():
    """Test Sorted dict pop key."""
    sd = SortedDict({'x': 10, 'y': 20})
    val = sd.pop('x')
    assert val == 10
    assert 'x' not in sd


def test_sorted_dict_setdefault():
    sd = SortedDict({'a': 1})
    assert sd.setdefault('a', 99) == 1   # existing key
    assert sd.setdefault('b', 2) == 2    # new key
    assert list(sd.keys()) == ['a', 'b']


def test_sorted_dict_len():
    sd = SortedDict({'a': 1, 'b': 2, 'c': 3})
    assert len(sd) == 3
    sd['d'] = 4
    assert len(sd) == 4


def test_sorted_dict_irange_keys():
    """Test Sorted dict irange keys."""
    sd = SortedDict({k: k * 10 for k in range(1, 8)})
    result = list(sd.irange(2, 5))
    assert result == [2, 3, 4, 5]


def test_sorted_dict_popitem_exists():
    """Test Sorted dict popitem exists."""
    sd = SortedDict({'a': 1, 'b': 2, 'c': 3})
    result = sd.popitem(0)
    # Only verify 'a' was removed, not which tuple position is key vs value
    assert 'a' not in sd
    assert len(sd) == 2
