"""
Ground-truth PBT for BINT-001.

Bug 1 (L4): succ_item() candidate update < changed to > in abctree.py:706
  - succ_item(k) returns wrong successor when the search path makes >= 2
    consecutive left turns with no right child at k.
  - Simplest trigger: succ_item(min_key()) on tree with n >= 5.

Bug 2 (L3): prev_item() candidate update > changed to < in abctree.py:744
  - Symmetric: prev_item(k) returns wrong predecessor when the search path
    makes >= 2 consecutive right turns with no left child at k.
  - Simplest trigger: prev_item(max_key()) on tree with n >= 5.

Bug 3 (L2): iter_items() start boundary: <= changed to < in abctree.py:860
  - iter_items(start, end) excludes start_key even when it exists in the tree.
  - Trigger: iter_items(k, k+N) where k IS in the tree.

Bug 4 (L3): floor_item() candidate update > changed to < in abctree.py:777
  - floor_item(q) returns wrong floor when q is NOT in the tree and the
    search path visits >= 2 nodes via right turns.
  - Trigger: floor_item(q) where q is not in tree and multiple keys < q exist.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hypothesis import given, settings, assume
from hypothesis import strategies as st
from bintrees import AVLTree


# ---------------------------------------------------------------------------
# Bug 1: succ_item() returns wrong successor
#
# Strategy: build tree with n >= 5 keys, then verify succ_item for ALL
# consecutive pairs. This catches the bug whenever the tree has height >= 3
# and we query succ(min_key). With n >= 5 and AVL, height is always >= 3.
#
# Invariant: for any two consecutive keys k1 < k2 in sorted order,
#   t.succ_item(k1) == (k2, k2)
# ---------------------------------------------------------------------------
@settings(max_examples=500, deadline=None)
@given(
    keys=st.lists(
        st.integers(min_value=0, max_value=200),
        min_size=5,
        max_size=30,
        unique=True,
    )
)
def test_succ_item_correctness(keys):
    """succ_item(k1) must return the next larger key k2 for all consecutive pairs."""
    t = AVLTree({k: k for k in keys})
    sorted_keys = sorted(keys)
    for i in range(len(sorted_keys) - 1):
        k1 = sorted_keys[i]
        k2 = sorted_keys[i + 1]
        result = t.succ_item(k1)
        assert result == (k2, k2), (
            f"succ_item({k1}) returned {result}, expected ({k2}, {k2}). "
            f"Keys: {sorted_keys}"
        )


# ---------------------------------------------------------------------------
# Bug 2: prev_item() returns wrong predecessor
#
# Invariant: for any two consecutive keys k1 < k2 in sorted order,
#   t.prev_item(k2) == (k1, k1)
# ---------------------------------------------------------------------------
@settings(max_examples=500, deadline=None)
@given(
    keys=st.lists(
        st.integers(min_value=0, max_value=200),
        min_size=5,
        max_size=30,
        unique=True,
    )
)
def test_prev_item_correctness(keys):
    """prev_item(k2) must return the next smaller key k1 for all consecutive pairs."""
    t = AVLTree({k: k for k in keys})
    sorted_keys = sorted(keys)
    for i in range(1, len(sorted_keys)):
        k1 = sorted_keys[i - 1]
        k2 = sorted_keys[i]
        result = t.prev_item(k2)
        assert result == (k1, k1), (
            f"prev_item({k2}) returned {result}, expected ({k1}, {k1}). "
            f"Keys: {sorted_keys}"
        )


# ---------------------------------------------------------------------------
# Bug 3: iter_items() excludes start_key when it is in the tree
#
# Strategy: build tree, pick start_key that IS in the tree, pick end_key
# that is larger than start_key. Verify start_key appears in results.
#
# Invariant: start_key <= k < end_key for all (k, v) in iter_items(start, end)
# AND start_key itself appears if it is in the tree.
# ---------------------------------------------------------------------------
@settings(max_examples=500, deadline=None)
@given(
    keys=st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=3,
        max_size=20,
        unique=True,
    ),
    offset=st.integers(min_value=1, max_value=10),
)
def test_iter_items_includes_start_key(keys, offset):
    """iter_items(start, end) must include start_key when start_key is in the tree."""
    t = AVLTree({k: k for k in keys})
    sorted_keys = sorted(keys)
    start_key = sorted_keys[0]  # min key is always in tree
    end_key = start_key + offset

    result_keys = [k for k, v in t.iter_items(start_key, end_key)]
    assert start_key in result_keys, (
        f"iter_items({start_key}, {end_key}) returned keys {result_keys}, "
        f"but start_key {start_key} (which IS in the tree) is missing. "
        f"Tree keys: {sorted_keys}"
    )


@settings(max_examples=500, deadline=None)
@given(
    keys=st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=3,
        max_size=20,
        unique=True,
    ),
    start_idx=st.integers(min_value=0, max_value=5),
    end_idx=st.integers(min_value=1, max_value=8),
)
def test_iter_items_boundary_semantics(keys, start_idx, end_idx):
    """iter_items(s, e) must yield all k with s <= k < e."""
    t = AVLTree({k: k for k in keys})
    sorted_keys = sorted(keys)
    assume(start_idx < len(sorted_keys))
    assume(end_idx < len(sorted_keys))
    assume(start_idx < end_idx)

    start_key = sorted_keys[start_idx]
    end_key = sorted_keys[end_idx]

    result_keys = [k for k, v in t.iter_items(start_key, end_key)]
    expected_keys = [k for k in sorted_keys if start_key <= k < end_key]

    assert result_keys == expected_keys, (
        f"iter_items({start_key}, {end_key}) returned {result_keys}, "
        f"expected {expected_keys}. Tree keys: {sorted_keys}"
    )


# ---------------------------------------------------------------------------
# Bug 4: floor_item() returns wrong floor for non-member queries
#
# Strategy: build tree with keys, query floor of a value NOT in the tree
# that has multiple keys below it. Compare against expected floor computed
# from the sorted key list.
#
# Invariant: floor_item(q) returns (k, k) where k = max(x for x in keys if x <= q)
# ---------------------------------------------------------------------------
@settings(max_examples=500, deadline=None)
@given(
    keys=st.lists(
        st.integers(min_value=1, max_value=199),
        min_size=5,
        max_size=30,
        unique=True,
    ),
    query=st.integers(min_value=0, max_value=200),
)
def test_floor_item_correctness(keys, query):
    """floor_item(q) must return the largest key <= q."""
    t = AVLTree({k: k for k in keys})
    sorted_keys = sorted(keys)

    floor_keys = [k for k in sorted_keys if k <= query]
    if not floor_keys:
        # No key <= query: should raise KeyError
        try:
            t.floor_item(query)
            assert False, f"floor_item({query}) should raise KeyError, got a result"
        except KeyError:
            return

    expected_floor = max(floor_keys)
    result = t.floor_item(query)
    assert result == (expected_floor, expected_floor), (
        f"floor_item({query}) returned {result}, expected ({expected_floor}, {expected_floor}). "
        f"Tree keys: {sorted_keys}"
    )
