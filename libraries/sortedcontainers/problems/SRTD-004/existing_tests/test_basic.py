"""Basic tests for sortedcontainers."""
import pytest
from sortedcontainers import SortedList


def test_basic_add_and_contains():
    sl = SortedList()
    sl.add(3)
    sl.add(1)
    sl.add(2)
    assert 1 in sl
    assert 2 in sl
    assert 3 in sl
    assert 0 not in sl


def test_sorted_order_after_adds():
    sl = SortedList([5, 3, 1, 4, 2])
    assert list(sl) == [1, 2, 3, 4, 5]


def test_len():
    sl = SortedList([1, 2, 3])
    assert len(sl) == 3
    sl.add(4)
    assert len(sl) == 4


def test_getitem_positive():
    sl = SortedList([10, 30, 20, 40, 50])
    assert sl[0] == 10
    assert sl[1] == 20
    assert sl[2] == 30
    assert sl[4] == 50


def test_getitem_negative():
    sl = SortedList([1, 2, 3, 4, 5])
    assert sl[-1] == 5
    assert sl[-2] == 4


def test_remove():
    sl = SortedList([1, 2, 3, 4, 5])
    sl.remove(3)
    assert list(sl) == [1, 2, 4, 5]
    assert 3 not in sl


def test_discard_present():
    sl = SortedList([1, 2, 3])
    sl.discard(2)
    assert list(sl) == [1, 3]


def test_discard_absent():
    sl = SortedList([1, 2, 3])
    sl.discard(99)  # should not raise
    assert list(sl) == [1, 2, 3]


def test_irange_inclusive():
    sl = SortedList([1, 2, 3, 4, 5])
    assert list(sl.irange(2, 4)) == [2, 3, 4]


def test_irange_exclusive_min():
    sl = SortedList([1, 2, 3, 4, 5])
    result = list(sl.irange(2, 4, inclusive=(False, True)))
    assert result == [3, 4]


def test_irange_reverse():
    sl = SortedList([1, 2, 3, 4, 5])
    assert list(sl.irange(2, 4, reverse=True)) == [4, 3, 2]


def test_count_no_duplicates():
    sl = SortedList([1, 2, 3, 4, 5])
    assert sl.count(3) == 1
    assert sl.count(6) == 0


def test_count_with_duplicates():
    sl = SortedList([1, 2, 2, 3, 3, 3])
    assert sl.count(2) == 2
    assert sl.count(3) == 3
    assert sl.count(1) == 1


def test_pop_default():
    sl = SortedList([1, 2, 3, 4, 5])
    val = sl.pop()
    assert val == 5
    assert list(sl) == [1, 2, 3, 4]


def test_pop_index_zero():
    sl = SortedList([1, 2, 3, 4, 5])
    val = sl.pop(0)
    assert val == 1
    assert list(sl) == [2, 3, 4, 5]


def test_bisect_right():
    sl = SortedList([10, 20, 20, 30, 40])
    assert sl.bisect_right(20) == 3
    assert sl.bisect_right(15) == 1
    assert sl.bisect_right(50) == 5


def test_index_method():
    sl = SortedList([1, 2, 3, 4, 5])
    assert sl.index(3) == 2
    assert sl.index(1) == 0
    assert sl.index(5) == 4
    with pytest.raises(ValueError):
        sl.index(99)


def test_iter_and_reversed():
    sl = SortedList([3, 1, 4, 1, 5, 9])
    assert list(sl) == sorted([3, 1, 4, 1, 5, 9])
    assert list(reversed(sl)) == sorted([3, 1, 4, 1, 5, 9], reverse=True)


def test_update():
    sl = SortedList([1, 3, 5])
    sl.update([2, 4, 6])
    assert list(sl) == [1, 2, 3, 4, 5, 6]


def test_copy():
    sl = SortedList([1, 2, 3])
    sl2 = sl.copy()
    assert list(sl2) == [1, 2, 3]
    sl2.add(4)
    assert 4 not in sl  # copy is independent


def test_islice():
    sl = SortedList([1, 2, 3, 4, 5])
    assert list(sl.islice(1, 4)) == [2, 3, 4]
    assert list(sl.islice(0, 3, reverse=True)) == [3, 2, 1]
