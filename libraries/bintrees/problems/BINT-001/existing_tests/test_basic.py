"""Basic tests for bintrees."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bintrees import AVLTree


def make_tree():
    """Tree with keys [2, 4, 6, 8, 10, 12, 14]."""
    return AVLTree({k: k * 10 for k in [2, 4, 6, 8, 10, 12, 14]})


def test_empty_tree():
    t = AVLTree()
    assert len(t) == 0
    assert list(t.keys()) == []
    assert t.is_empty()


def test_insert_and_sorted_keys():
    t = AVLTree()
    for k in [5, 2, 8, 1, 3, 7, 9]:
        t[k] = k
    assert list(t.keys()) == [1, 2, 3, 5, 7, 8, 9]


def test_sorted_after_any_insert_order():
    """BST ordering invariant: keys always sorted regardless of insert order."""
    for start in [1, 10, 100]:
        t = AVLTree()
        import random
        random.seed(start)
        nums = random.sample(range(200), 20)
        for n in nums:
            t[n] = n
        assert list(t.keys()) == sorted(nums)


def test_len_and_count():
    t = make_tree()
    assert len(t) == 7


def test_exact_lookup():
    t = make_tree()
    assert t[6] == 60
    assert t[2] == 20
    assert t[14] == 140


def test_containment():
    t = make_tree()
    assert 6 in t
    assert 7 not in t
    assert 0 not in t


def test_min_max():
    t = make_tree()
    assert t.min_key() == 2
    assert t.max_key() == 14
    assert t.min_item() == (2, 20)
    assert t.max_item() == (14, 140)


def test_succ_item_middle_keys():
    """Test Succ item middle keys."""
    t = make_tree()
    # 8 is the AVL root (center of [2,4,6,8,10,12,14]); its right child is 12
    # succ(8) finds min of right subtree (10), not path-ancestor path
    assert t.succ_item(8) == (10, 100)
    # succ(4) — 4 has right child 6 in the tree structure
    assert t.succ_item(4) == (6, 60)
    # succ(10) — has right child 12
    assert t.succ_item(10) == (12, 120)


def test_prev_item_middle_keys():
    """Test Prev item middle keys."""
    t = make_tree()
    # 8 is root; its left child is 4; prev(8) = 6
    assert t.prev_item(8) == (6, 60)
    # prev(12) — 12 has left child 10
    assert t.prev_item(12) == (10, 100)
    # prev(6) — has left child 4
    assert t.prev_item(6) == (4, 40)


def test_iter_items_start_not_in_tree():
    """Test Iter items start not in tree."""
    t = make_tree()
    # start=0 not in tree: same result for < or <=
    assert list(k for k, v in t.iter_items(0, 9)) == [2, 4, 6, 8]
    # start=1 not in tree
    assert list(k for k, v in t.iter_items(1, 9)) == [2, 4, 6, 8]
    # no bounds
    assert list(t.keys()) == [2, 4, 6, 8, 10, 12, 14]


def test_iter_items_reverse():
    t = make_tree()
    # start=0 not in tree, reverse
    assert list(k for k, v in t.iter_items(0, 9, reverse=True)) == [8, 6, 4, 2]


def test_floor_exact_key():
    """Test Floor exact key."""
    t = make_tree()
    assert t.floor_item(6) == (6, 60)
    assert t.floor_item(2) == (2, 20)
    assert t.floor_item(14) == (14, 140)
    assert t.floor_key(8) == 8


def test_ceiling_exact_key():
    """ceiling() with exact key matches — takes early-return path."""
    t = make_tree()
    assert t.ceiling_item(6) == (6, 60)
    assert t.ceiling_item(2) == (2, 20)
    assert t.ceiling_key(14) == 14


def test_ceiling_non_member():
    """Test Ceiling non member."""
    t = make_tree()
    # ceiling(7) should be 8 (7 not in tree, first key >= 7 is 8)
    assert t.ceiling_item(7) == (8, 80)
    assert t.ceiling_item(3) == (4, 40)
    assert t.ceiling_item(13) == (14, 140)


def test_delete():
    t = make_tree()
    del t[8]
    assert 8 not in t
    assert list(t.keys()) == [2, 4, 6, 10, 12, 14]


def test_update():
    t = AVLTree()
    t.update({1: 10, 2: 20, 3: 30})
    assert list(t.keys()) == [1, 2, 3]
    assert t[2] == 20


def test_pop_min_max():
    t = make_tree()
    assert t.pop_min() == (2, 20)
    assert t.pop_max() == (14, 140)
    assert list(t.keys()) == [4, 6, 8, 10, 12]
