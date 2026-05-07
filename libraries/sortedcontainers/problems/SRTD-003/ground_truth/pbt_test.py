"""
Ground-truth PBT for SRTD-003.

Bug 1: SortedList.count(value) returns wrong count when the value is the
maximum element of one sublist AND also appears at the start of the next
sublist. With DEFAULT_LOAD_FACTOR=20, this is triggered by adding 21+
copies of the same value so that they span across two sublists.

Bug 2: SortedList.pop(index) returns the wrong element when index is a
negative value (other than -1) that falls within the fast-path range of
the last sublist. The bug changes `loc = len_last + index` to
`loc = len_last + index + 1`, which shifts the result by +1, returning
the wrong element.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hypothesis import given, settings, assume
from hypothesis import strategies as st
from sortedcontainers import SortedList


# ---------------------------------------------------------------------------
# Bug 1: count() undercount when value straddles sublist boundary
#
# Strategy: build a list with many duplicates of a specific value so that
# it overflows one sublist into the next.  With DEFAULT_LOAD_FACTOR=20
# the first split happens at 40 elements; placing 21+ copies of the same
# value guarantees the value appears as the max of one sublist AND continues
# into the next.
#
# Invariant: sl.count(x) == sum(1 for v in sl if v == x)
# ---------------------------------------------------------------------------
@settings(max_examples=500, deadline=None)
@given(
    num_target=st.integers(min_value=21, max_value=30),
    target=st.integers(min_value=1, max_value=50),
    prefix=st.lists(st.integers(min_value=1, max_value=50), min_size=0, max_size=20),
)
def test_count_consistency(num_target, target, prefix):
    """count(x) must equal the true frequency of x regardless of sublist layout."""
    elements = prefix + [target] * num_target
    sl = SortedList(elements)
    for val in set(elements):
        expected = sum(1 for v in elements if v == val)
        assert sl.count(val) == expected, (
            f"count({val}) returned {sl.count(val)}, expected {expected}. "
            f"List size={len(sl)}, num_target={num_target}, target={target}, "
            f"_maxes={sl._maxes}"
        )


# ---------------------------------------------------------------------------
# Bug 2: pop(index) returns wrong element for negative index in last sublist
#
# Strategy: use a list of 3+ distinct elements, then call pop(-2) or pop(-3).
# The invariant is that sl.pop(i) must return list(sl)[i] (the element at
# that logical index before the pop).
#
# Trigger condition: any list with at least 3 elements in the last sublist,
# using a negative index (not -1) that falls within that last sublist.
# With DEFAULT_LOAD_FACTOR=1000, a 3-element list is entirely in one sublist,
# so pop(-2) on a 3-element list is sufficient to trigger the bug.
# ---------------------------------------------------------------------------
@settings(max_examples=500, deadline=None)
@given(
    data=st.lists(
        st.integers(min_value=0, max_value=1000),
        min_size=3,
        max_size=50,
        unique=True,
    ),
    neg_offset=st.integers(min_value=2, max_value=10),
)
def test_pop_negative_index(data, neg_offset):
    """pop(-k) for k>=2 must remove and return the element at logical index -k."""
    sl = SortedList(data)
    n = len(sl)
    # Only use offsets that are in the last sublist's valid negative range
    # and fit within the list
    assume(neg_offset <= n - 1)

    index = -neg_offset
    snapshot = list(sl)
    expected_val = snapshot[index]

    # Determine whether this index falls in the fast-path branch
    # (i.e., within the last sublist): the bug only fires in that branch.
    # We don't restrict here — let hypothesis find the triggering cases.
    popped = sl.pop(index)

    assert popped == expected_val, (
        f"pop({index}) returned {popped}, expected {expected_val}. "
        f"List was {snapshot}"
    )
    # The remaining elements should be snapshot without the popped element
    assert list(sl) == snapshot[:n + index] + snapshot[n + index + 1:]
