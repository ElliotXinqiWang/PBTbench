"""Basic tests for boltons."""
import pytest
from boltons.listutils import BarrelList
from boltons.statsutils import Stats


# ---------------------------------------------------------------------------
# BarrelList — single-barrel behaviour (< 22 000 elements via insert)
# ---------------------------------------------------------------------------

def test_barrellist_append_and_index():
    bl = BarrelList()
    for i in range(10):
        bl.append(i)
    assert list(bl) == list(range(10))
    assert bl[0] == 0
    assert bl[9] == 9
    assert bl[-1] == 9
    assert bl[-2] == 8


def test_barrellist_insert():
    bl = BarrelList([1, 2, 3, 4])
    bl.insert(2, 99)
    assert list(bl) == [1, 2, 99, 3, 4]
    assert len(bl) == 5


def test_barrellist_len():
    bl = BarrelList(range(20))
    assert len(bl) == 20
    bl.append(100)
    assert len(bl) == 21


def test_barrellist_contains_small():
    bl = BarrelList([10, 20, 30, 40])
    assert 10 in bl
    assert 30 in bl
    assert 99 not in bl
    assert 0 not in bl


def test_barrellist_pop_small():
    bl = BarrelList([1, 2, 3, 4, 5])
    assert bl.pop() == 5
    assert bl.pop() == 4
    assert list(bl) == [1, 2, 3]


def test_barrellist_pop_with_index():
    bl = BarrelList([10, 20, 30, 40])
    assert bl.pop(1) == 20
    assert list(bl) == [10, 30, 40]


def test_barrellist_index_small():
    bl = BarrelList(['a', 'b', 'c', 'd'])
    assert bl.index('a') == 0
    assert bl.index('c') == 2
    assert bl.index('d') == 3


def test_barrellist_setitem_getitem():
    bl = BarrelList(range(5))
    bl[2] = 99
    assert bl[2] == 99
    assert list(bl) == [0, 1, 99, 3, 4]


def test_barrellist_delitem():
    bl = BarrelList([1, 2, 3, 4, 5])
    del bl[2]
    assert list(bl) == [1, 2, 4, 5]


def test_barrellist_slice():
    bl = BarrelList(range(10))
    assert list(bl[2:5]) == [2, 3, 4]
    assert list(bl[:3]) == [0, 1, 2]
    assert list(bl[7:]) == [7, 8, 9]


def test_barrellist_repr():
    bl = BarrelList([1, 2, 3])
    r = repr(bl)
    assert 'BarrelList' in r or 'BList' in r or '[1, 2, 3]' in r


def test_barrellist_count():
    bl = BarrelList([1, 2, 2, 3, 2, 4])
    assert bl.count(2) == 3
    assert bl.count(1) == 1
    assert bl.count(99) == 0


def test_barrellist_reverse():
    bl = BarrelList([1, 2, 3, 4, 5])
    bl.reverse()
    assert list(bl) == [5, 4, 3, 2, 1]


def test_barrellist_sort_single_barrel():
    bl = BarrelList([3, 1, 4, 1, 5, 9, 2, 6])
    bl.sort()
    assert list(bl) == sorted([3, 1, 4, 1, 5, 9, 2, 6])


# ---------------------------------------------------------------------------
# Stats — basic statistical properties
# ---------------------------------------------------------------------------

def test_stats_mean():
    s = Stats([1, 2, 3, 4, 5])
    assert s.mean == 3.0


def test_stats_mean_range():
    s = Stats(range(20))
    assert s.mean == 9.5


def test_stats_median_odd():
    s = Stats([1, 3, 5, 7, 9])
    assert s.median == 5


def test_stats_median_even():
    s = Stats([1, 2, 3, 4])
    assert s.median == 2.5


def test_stats_min_max():
    s = Stats([3, 1, 4, 1, 5, 9])
    assert s.min == 1
    assert s.max == 9


def test_stats_count():
    s = Stats(range(15))
    assert s.count == 15


def test_stats_mean_with_outlier():
    s = Stats(list(range(19)) + [949])
    assert s.mean == 56.0


def test_stats_get_quantile_zero_one():
    s = Stats([10, 20, 30, 40, 50])
    assert s.get_quantile(0.0) == 10
    assert s.get_quantile(1.0) == 50
    assert s.get_quantile(0.5) == 30


def test_stats_get_quantile_median():
    s = Stats(range(101))
    assert s.get_quantile(0.5) == 50.0


def test_stats_std_dev_simple():
    # std_dev = sqrt(variance)
    s = Stats([1, 2, 3, 4, 5])
    expected = s.variance ** 0.5
    assert abs(s.std_dev - expected) < 1e-10


def test_stats_describe_keys():
    s = Stats(range(10))
    d = s.describe(format='dict')
    assert 'mean' in d
    assert 'std_dev' in d
    assert 'min' in d
    assert 'max' in d


def test_stats_trim_relative():
    s = Stats(list(range(20)))
    s.trim_relative(0.25)
    # 25% trimmed from each end of 20 elements → 5 removed each side → 10 remaining
    assert len(s.data) == 10


def test_stats_default_on_empty():
    s = Stats([], default=42.0)
    assert s.mean == 42.0
    assert s.median == 42.0
