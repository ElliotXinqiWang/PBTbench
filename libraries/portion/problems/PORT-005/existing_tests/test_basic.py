"""Basic tests for portion."""
import pytest
import portion as P
from portion import Bound


# ---------------------------------------------------------------------------
# Interval creation
# ---------------------------------------------------------------------------

def test_closed_interval_basic():
    I = P.closed(1, 10)
    assert I.lower == 1
    assert I.upper == 10
    assert I.left == Bound.CLOSED
    assert I.right == Bound.CLOSED


def test_open_interval_basic():
    I = P.open(0, 5)
    assert I.lower == 0
    assert I.upper == 5
    assert I.left == Bound.OPEN
    assert I.right == Bound.OPEN


def test_openclosed_interval():
    I = P.openclosed(2, 8)
    assert I.left == Bound.OPEN
    assert I.right == Bound.CLOSED


def test_closedopen_interval():
    I = P.closedopen(2, 8)
    assert I.left == Bound.CLOSED
    assert I.right == Bound.OPEN


def test_singleton_interval():
    I = P.singleton(7)
    assert I.lower == 7
    assert I.upper == 7
    assert I.atomic


def test_empty_interval():
    E = P.empty()
    assert E.empty


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_union_disjoint_closed():
    A = P.closed(1, 3)
    B = P.closed(5, 7)
    union = A | B
    assert not union.atomic
    assert 2 in union
    assert 6 in union
    assert 4 not in union


def test_union_both_closed_same_lower():
    """Test Union both closed same lower."""
    A = P.closed(3, 8)
    B = P.closed(3, 5)
    union = A | B
    assert union == P.closed(3, 8)
    assert 3 in union


def test_union_overlapping_closed():
    A = P.closed(1, 5)
    B = P.closed(3, 9)
    union = A | B
    assert union == P.closed(1, 9)


def test_union_both_open_at_touching_point():
    """Test Union both open at touching point."""
    A = P.open(0, 5)
    B = P.open(5, 10)
    union = A | B
    assert not union.atomic
    assert 5 not in union


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_intersection_disjoint_is_empty():
    A = P.closed(0, 3)
    B = P.closed(5, 8)
    assert (A & B) == P.empty()


def test_intersection_overlapping_closed():
    A = P.closed(1, 7)
    B = P.closed(4, 10)
    result = A & B
    assert result == P.closed(4, 7)


def test_intersection_different_lower_bounds():
    """Test Intersection different lower bounds."""
    A = P.open(1, 10)    # lower=1
    B = P.closed(3, 8)   # lower=3 (different)
    result = A & B
    assert result == P.closed(3, 8)
    assert 3 in result


def test_intersection_both_same_type_lower():
    """Test Intersection both same type lower."""
    A = P.closed(3, 10)
    B = P.closed(3, 7)
    result = A & B
    assert result == P.closed(3, 7)
    assert 3 in result


def test_intersection_both_open_same_lower():
    """Test Intersection both open same lower."""
    A = P.open(3, 10)
    B = P.open(3, 7)
    result = A & B
    assert result == P.open(3, 7)
    assert 3 not in result


# ---------------------------------------------------------------------------
# Complement -- atomic only, single level (no double complement, no non-atomic)
# ---------------------------------------------------------------------------

def test_complement_interior_not_in_complement():
    """Test Complement interior not in complement."""
    I = P.closed(2, 8)
    C = ~I
    # Interior point 5 must not be in complement
    assert 5 not in C
    # Points outside the interval on both sides must be in complement
    assert -1 in C
    assert 20 in C


def test_complement_left_boundary_excluded_for_closed():
    """Test Complement left boundary excluded for closed."""
    I = P.closed(3, 9)
    C = ~I
    # Left boundary 3 must not be in the complement
    assert 3 not in C
    # Far left values must be in complement
    assert -5 in C


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_value_containment_closed():
    I = P.closed(3, 7)
    assert 3 in I
    assert 5 in I
    assert 7 in I
    assert 2 not in I
    assert 8 not in I


def test_value_containment_open():
    I = P.open(3, 7)
    assert 3 not in I
    assert 5 in I
    assert 7 not in I


def test_interval_subset_containment_strictly_smaller_upper():
    """Test Interval subset containment strictly smaller upper."""
    outer = P.closed(1, 10)
    inner = P.closed(3, 7)   # inner.upper=7 < outer.upper=10
    assert inner in outer
    assert outer not in inner


def test_interval_same_upper_both_closed():
    """Test Interval same upper both closed."""
    outer = P.closed(1, 10)
    inner = P.closed(5, 10)  # same upper=10, both CLOSED
    assert inner in outer


def test_interval_same_upper_both_open():
    """Test Interval same upper both open."""
    outer = P.open(1, 10)
    inner = P.open(5, 10)   # same upper=10, both OPEN
    assert inner in outer


# ---------------------------------------------------------------------------
# enclosure property
# ---------------------------------------------------------------------------

def test_enclosure_atomic_is_self():
    I = P.closed(1, 7)
    assert I.enclosure == I


def test_enclosure_non_atomic():
    """enclosure of non-atomic interval is the bounding box."""
    I = P.closed(1, 3) | P.closed(6, 9)
    enc = I.enclosure
    assert enc == P.closed(1, 9)
    assert enc.atomic


def test_enclosure_contains_original():
    I = P.closed(1, 3) | P.closed(7, 9)
    assert I <= I.enclosure


# ---------------------------------------------------------------------------
# IntervalDict basic operations
# ---------------------------------------------------------------------------

def test_interval_dict_creation():
    d = P.IntervalDict({P.closed(1, 5): "a", P.closed(7, 10): "b"})
    assert d[3] == "a"
    assert d[8] == "b"


def test_interval_dict_domain():
    d = P.IntervalDict({P.closed(0, 3): 1, P.closed(5, 8): 2})
    dom = d.domain()
    assert 1 in dom
    assert 6 in dom
    assert 4 not in dom


def test_interval_dict_combine_symmetric():
    """Test Interval dict combine symmetric."""
    d1 = P.IntervalDict({P.closed(0, 5): 10})
    d2 = P.IntervalDict({P.closed(3, 8): 5})
    result = d1.combine(d2, lambda x, y: x + y)
    assert result[4] == 15
    assert result[1] == 10


def test_interval_dict_find():
    d = P.IntervalDict({P.closed(1, 5): "x", P.closed(7, 9): "y"})
    assert d.find("x") == P.closed(1, 5)
    assert d.find("y") == P.closed(7, 9)
    assert d.find("z") == P.empty()
