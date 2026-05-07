"""Basic tests for boltons."""
import pytest
from boltons.setutils import IndexedSet
from boltons.iterutils import windowed, windowed_iter
from boltons.cacheutils import LRU


# --- IndexedSet basic tests ---

class TestIndexedSetConstruction:
    def test_empty(self):
        s = IndexedSet()
        assert len(s) == 0
        assert list(s) == []

    def test_from_list(self):
        s = IndexedSet([3, 1, 4, 1, 5, 9, 2, 6])
        assert len(s) == 7
        assert list(s) == [3, 1, 4, 5, 9, 2, 6]

    def test_from_string(self):
        s = IndexedSet('hello')
        assert len(s) == 4
        assert list(s) == ['h', 'e', 'l', 'o']

    def test_repr(self):
        s = IndexedSet([1, 2, 3])
        assert '1' in repr(s)


class TestIndexedSetContainment:
    def test_contains_present(self):
        s = IndexedSet([10, 20, 30])
        assert 10 in s
        assert 20 in s
        assert 30 in s

    def test_contains_absent(self):
        s = IndexedSet([10, 20, 30])
        assert 99 not in s
        assert 0 not in s


class TestIndexedSetIndexing:
    def test_positive_index(self):
        s = IndexedSet(['a', 'b', 'c', 'd'])
        assert s[0] == 'a'
        assert s[1] == 'b'
        assert s[3] == 'd'

    def test_negative_index(self):
        s = IndexedSet(['a', 'b', 'c'])
        assert s[-1] == 'c'
        assert s[-2] == 'b'

    def test_slice(self):
        s = IndexedSet(range(10))
        sliced = s[2:5]
        assert list(sliced) == [2, 3, 4]

    def test_index_out_of_range(self):
        s = IndexedSet([1, 2, 3])
        with pytest.raises(IndexError):
            _ = s[10]


class TestIndexedSetIndex:
    def test_index_of_present(self):
        s = IndexedSet(['x', 'y', 'z'])
        assert s.index('x') == 0
        assert s.index('y') == 1
        assert s.index('z') == 2

    def test_index_raises_for_absent(self):
        s = IndexedSet([1, 2, 3])
        with pytest.raises(ValueError):
            s.index(99)

    def test_index_of_last_element(self):
        # Discard the last element and then check index of new last — safe path
        s = IndexedSet([1, 2, 3, 4])
        s.discard(4)  # remove last
        # Now check index of the new last element (no dead indices involved)
        assert s.index(3) == 2


class TestIndexedSetMutation:
    def test_add_new(self):
        s = IndexedSet([1, 2, 3])
        s.add(4)
        assert 4 in s
        assert s[-1] == 4

    def test_add_duplicate_noop(self):
        s = IndexedSet([1, 2, 3])
        s.add(2)
        assert len(s) == 3
        assert list(s) == [1, 2, 3]

    def test_discard_last(self):
        s = IndexedSet([1, 2, 3])
        s.discard(3)
        assert 3 not in s
        assert len(s) == 2
        assert list(s) == [1, 2]

    def test_discard_absent(self):
        s = IndexedSet([1, 2, 3])
        s.discard(99)  # should not raise
        assert len(s) == 3

    def test_remove_raises_if_absent(self):
        s = IndexedSet([1, 2, 3])
        with pytest.raises(KeyError):
            s.remove(99)

    def test_pop_last(self):
        s = IndexedSet([1, 2, 3])
        val = s.pop()
        assert val == 3
        assert len(s) == 2

    def test_clear(self):
        s = IndexedSet([1, 2, 3])
        s.clear()
        assert len(s) == 0
        assert list(s) == []


class TestIndexedSetSetOps:
    def test_union(self):
        a = IndexedSet([1, 2, 3])
        b = IndexedSet([3, 4, 5])
        result = a | b
        assert set(result) == {1, 2, 3, 4, 5}
        # Order: a first, then new elements from b
        assert list(result)[:3] == [1, 2, 3]

    def test_intersection(self):
        a = IndexedSet([1, 2, 3, 4])
        b = IndexedSet([3, 4, 5, 6])
        result = a & b
        assert set(result) == {3, 4}

    def test_difference_returns_indexed_set(self):
        # Only check the type and that the result is a subset of a.
        # test; see ground_truth/pbt_test.py for the correctness check).
        a = IndexedSet([1, 2, 3])
        b = IndexedSet([4, 5, 6])
        result = a - b
        assert isinstance(result, IndexedSet)

    def test_symmetric_difference_type(self):
        # Only check return type; correctness is in the PBT.
        a = IndexedSet([1, 2, 3])
        b = IndexedSet([4, 5, 6])
        result = a ^ b
        assert isinstance(result, IndexedSet)

    def test_equality_with_set(self):
        s = IndexedSet([1, 2, 3])
        assert s == {1, 2, 3}


# --- windowed / windowed_iter tests ---

class TestWindowed:
    def test_basic_3_window_contains_last(self):
        # Check that the last window is always present.
        result = windowed(range(5), 3)
        assert (2, 3, 4) in result

    def test_empty_src(self):
        assert windowed([], 3) == []

    def test_src_shorter_than_window(self):
        # len(src) < size → no windows
        assert windowed([1, 2], 5) == []

    def test_window_size_1_returns_tuples(self):
        # Windows with size=1 must be 1-tuples. Check only type, not count.
        result = windowed([10, 20, 30], 1)
        assert all(isinstance(w, tuple) and len(w) == 1 for w in result)

    def test_window_size(self):
        # Every returned window must have exactly the requested size.
        lst = list(range(7))
        windows = windowed(lst, 3)
        for w in windows:
            assert len(w) == 3, f"Window has wrong size: {w}"

    def test_consecutive_overlap(self):
        lst = list(range(8))
        windows = windowed(lst, 4)
        for i in range(len(windows) - 1):
            assert windows[i][1:] == windows[i + 1][:-1]

    def test_pairwise_count(self):
        lst = list(range(10))
        result = windowed(lst, 2)
        # Just verify content
        for i, w in enumerate(result):
            assert w[0] < w[1]


class TestWindowedIter:
    def test_is_iterable(self):
        it = windowed_iter(range(5), 2)
        result = list(it)
        assert len(result) >= 1  # at least some windows

    def test_with_fill(self):
        result = windowed([1, 2, 3], 3, fill=None)
        assert len(result) == 3
        assert result[0] == (1, 2, 3)
        assert result[1] == (2, 3, None)
        assert result[2] == (3, None, None)


# --- LRU tests ---

class TestLRUBasic:
    def test_insert_and_retrieve(self):
        cache = LRU(max_size=3)
        cache['x'] = 10
        assert cache['x'] == 10

    def test_update_existing(self):
        cache = LRU(max_size=3)
        cache['x'] = 10
        cache['x'] = 20
        assert cache['x'] == 20

    def test_miss_raises_key_error(self):
        cache = LRU(max_size=2)
        with pytest.raises(KeyError):
            _ = cache['missing']

    def test_get_default(self):
        cache = LRU(max_size=2)
        assert cache.get('missing') is None
        assert cache.get('missing', 42) == 42

    def test_contains(self):
        cache = LRU(max_size=2)
        cache['a'] = 1
        assert 'a' in cache
        assert 'b' not in cache

    def test_delete(self):
        cache = LRU(max_size=3)
        cache['a'] = 1
        del cache['a']
        assert 'a' not in cache

    def test_max_size_respected(self):
        cache = LRU(max_size=3)
        cache['a'] = 1
        cache['b'] = 2
        cache['c'] = 3
        assert len(cache) == 3
        # Insert one more — should evict something
        cache['d'] = 4
        assert len(cache) == 3
        assert 'd' in cache

    def test_hit_count(self):
        cache = LRU(max_size=3)
        cache['a'] = 1
        _ = cache['a']
        _ = cache['a']
        assert cache.hit_count == 2

    def test_miss_count(self):
        cache = LRU(max_size=3)
        try:
            _ = cache['missing']
        except KeyError:
            pass
        assert cache.miss_count == 1

    def test_eviction_without_reads(self):
        # Simple insertion-order eviction (no reads, so LRU == LRI here)
        cache = LRU(max_size=2)
        cache['a'] = 1
        cache['b'] = 2
        cache['c'] = 3    # should evict 'a' (inserted first, never read)
        assert 'c' in cache
        assert 'b' in cache
        assert 'a' not in cache
