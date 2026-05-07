"""Basic tests for intervaltree."""
import pytest
from intervaltree import IntervalTree, Interval


def test_create_empty():
    t = IntervalTree()
    assert len(t) == 0
    assert t.is_empty()


def test_add_interval():
    t = IntervalTree()
    t.addi(1, 5)
    assert len(t) == 1
    assert not t.is_empty()


def test_contains():
    t = IntervalTree()
    iv = Interval(1, 5)
    t.add(iv)
    assert iv in t


def test_at_interior_point():
    """at() returns intervals containing a point strictly inside."""
    t = IntervalTree.from_tuples([(1, 5), (3, 8), (10, 20)])
    result = t.at(4)
    assert Interval(1, 5) in result
    assert Interval(3, 8) in result
    assert Interval(10, 20) not in result


def test_overlap_basic():
    """overlap() returns intervals overlapping a range."""
    t = IntervalTree.from_tuples([(1, 5), (4, 8), (10, 20)])
    result = t.overlap(3, 6)
    assert Interval(1, 5) in result
    assert Interval(4, 8) in result
    assert Interval(10, 20) not in result


def test_remove_interval():
    t = IntervalTree.from_tuples([(1, 5), (3, 8)])
    t.remove(Interval(1, 5))
    assert len(t) == 1
    assert Interval(1, 5) not in t
    assert Interval(3, 8) in t


def test_discard_missing():
    t = IntervalTree.from_tuples([(1, 5)])
    t.discard(Interval(10, 20))
    assert len(t) == 1


def test_begin_end():
    t = IntervalTree.from_tuples([(3, 7), (1, 5), (8, 12)])
    assert t.begin() == 1
    assert t.end() == 12


def test_span():
    t = IntervalTree.from_tuples([(3, 7), (1, 5)])
    # span() should return a numeric value without raising; exact value tested in ground_truth
    s = t.span()
    assert isinstance(s, (int, float))


def test_update():
    t = IntervalTree()
    t.update([Interval(1, 5), Interval(3, 8)])
    assert len(t) == 2


def test_from_tuples():
    t = IntervalTree.from_tuples([(1, 5, 'a'), (3, 8, 'b')])
    assert len(t) == 2


def test_copy():
    t = IntervalTree.from_tuples([(1, 5), (3, 8)])
    t2 = t.copy()
    assert t == t2
    t2.addi(10, 20)
    assert len(t) == 2
    assert len(t2) == 3


def test_iter():
    ivs = [(1, 5), (3, 8), (10, 20)]
    t = IntervalTree.from_tuples(ivs)
    found = set()
    for iv in t:
        found.add((iv.begin, iv.end))
    assert found == set(ivs)


def test_null_interval_raises():
    t = IntervalTree()
    with pytest.raises(ValueError):
        t.addi(5, 5)  # null interval
