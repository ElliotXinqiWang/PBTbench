"""Basic tests for sortedcontainers."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sortedcontainers import SortedList


def test_empty():
    sl = SortedList()
    assert len(sl) == 0
    assert list(sl) == []


def test_init_from_list():
    sl = SortedList([3, 1, 4, 1, 5, 9, 2, 6])
    assert list(sl) == [1, 1, 2, 3, 4, 5, 6, 9]


def test_add_single():
    sl = SortedList()
    sl.add(5)
    sl.add(2)
    sl.add(8)
    assert list(sl) == [2, 5, 8]


def test_sorted_invariant():
    data = [5, 3, 8, 1, 9, 2, 7, 4, 6, 10, -1, 0]
    sl = SortedList(data)
    assert list(sl) == sorted(data)


def test_membership():
    data = list(range(20))
    sl = SortedList(data)
    for x in data:
        assert x in sl


def test_add_then_discard():
    sl = SortedList([1, 2, 3, 4, 5])
    sl.discard(3)
    assert list(sl) == [1, 2, 4, 5]
    assert 3 not in sl


def test_count_small():
    """Test Count small."""
    sl = SortedList([1, 1, 2, 3, 3, 3])
    assert sl.count(1) == 2
    assert sl.count(3) == 3
    assert sl.count(99) == 0


def test_count_single():
    sl = SortedList([10, 20, 30, 40])
    assert sl.count(20) == 1
    assert sl.count(15) == 0


def test_pop_last():
    """Test Pop last."""
    sl = SortedList([1, 2, 3, 4, 5])
    assert sl.pop() == 5
    assert sl.pop(-1) == 4
    assert list(sl) == [1, 2, 3]


def test_pop_first():
    """pop(0) — uses the fast path for index 0."""
    sl = SortedList([10, 20, 30])
    assert sl.pop(0) == 10
    assert list(sl) == [20, 30]


def test_pop_positive_index():
    """Test Pop positive index."""
    sl = SortedList(range(10))
    val = sl.pop(5)
    assert val == 5
    assert 5 not in sl


def test_irange_basic():
    sl = SortedList([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert list(sl.irange(3, 7)) == [3, 4, 5, 6, 7]


def test_bisect():
    sl = SortedList([10, 20, 30, 40])
    assert sl.bisect_left(20) == 1
    assert sl.bisect_right(20) == 2
