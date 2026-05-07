"""Basic tests for pyrsistent."""
import pytest
from pyrsistent import pbag, b, plist, l


# ─── PBag basic tests ─────────────────────────────────────────────────────────

def test_pbag_create_empty():
    bag = pbag([])
    assert len(bag) == 0


def test_pbag_create_from_list():
    bag = pbag([1, 2, 3])
    assert len(bag) == 3


def test_pbag_add_element():
    bag = pbag([1, 2])
    bag2 = bag.add(3)
    assert bag2.count(3) == 1
    assert bag.count(3) == 0  # immutability


def test_pbag_count():
    bag = pbag([1, 1, 2, 3])
    assert bag.count(1) == 2
    assert bag.count(2) == 1
    assert bag.count(3) == 1
    assert bag.count(99) == 0


def test_pbag_remove():
    bag = pbag([1, 1, 2])
    bag2 = bag.remove(1)
    assert bag2.count(1) == 1
    assert bag.count(1) == 2  # immutability


def test_pbag_contains():
    bag = pbag([1, 2, 3])
    assert 1 in bag
    assert 4 not in bag


def test_pbag_equality():
    assert pbag([1, 2, 2, 3]) == pbag([3, 2, 1, 2])
    assert pbag([1, 2]) != pbag([1, 2, 2])


def test_pbag_addition():
    a = pbag([1, 2])
    b = pbag([2, 3])
    result = a + b
    assert result.count(1) == 1
    assert result.count(2) == 2
    assert result.count(3) == 1


def test_pbag_update_empty_iterable():
    """update with empty iterable returns same bag."""
    bag = pbag([1, 2])
    updated = bag.update([])
    # Empty iterable: the if-branch is not taken, returns self
    assert updated.count(1) == 1


def test_pbag_subtract_nonoverlapping():
    """Subtracting elements not in self changes nothing."""
    a = pbag([1, 2, 3])
    b = pbag([4, 5])
    result = a - b
    assert result.count(1) == 1
    assert result.count(2) == 1
    assert result.count(3) == 1


def test_pbag_intersection_with_self():
    """a & a should return elements with same counts as a."""
    a = pbag([1, 1, 2])
    result = a & a
    assert result.count(1) == 2
    assert result.count(2) == 1


def test_pbag_union_nonoverlapping():
    """Union of disjoint bags contains all elements from both."""
    a = pbag([1, 2])
    b = pbag([3, 4])
    result = a | b
    assert result.count(1) == 1
    assert result.count(3) == 1


# ─── PList basic tests ────────────────────────────────────────────────────────

def test_plist_create():
    pl = plist([1, 2, 3])
    assert list(pl) == [1, 2, 3]


def test_plist_len():
    pl = plist([1, 2, 3])
    assert len(pl) == 3


def test_plist_cons():
    pl = plist([2, 3])
    pl2 = pl.cons(1)
    assert list(pl2) == [1, 2, 3]
    assert list(pl) == [2, 3]  # immutability


def test_plist_positive_indexing():
    pl = plist([10, 20, 30])
    assert pl[0] == 10
    assert pl[1] == 20
    assert pl[2] == 30


def test_plist_remove():
    pl = plist([1, 2, 3, 2])
    pl2 = pl.remove(2)
    assert list(pl2) == [1, 3, 2]


def test_plist_reverse():
    pl = plist([1, 2, 3])
    assert list(pl.reverse()) == [3, 2, 1]


def test_plist_split():
    pl = plist([1, 2, 3, 4])
    left, right = pl.split(2)
    assert list(left) == [1, 2]
    assert list(right) == [3, 4]


def test_plist_mcons_order():
    """mcons inserts in reverse order of iterable."""
    pl = plist([1, 2])
    result = pl.mcons([3, 4])
    assert list(result) == [4, 3, 1, 2]
