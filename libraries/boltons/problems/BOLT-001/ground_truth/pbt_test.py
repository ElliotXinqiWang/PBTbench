"""
Ground-truth PBT for BOLT-001.

Four properties, one per bug:

  test_indexedset_index_invariant_after_discard (Bug 1)
      After any sequence of adds and discards, s[s.index(x)] == x for
      every remaining element x, and list(s) == [s[i] for i in range(len(s))].
      The bug (apparent_index += instead of -=) makes index() return wrong
      values for elements that come after deleted elements.

  test_indexedset_difference_vs_builtin_set (Bug 2)
      a - b must equal the built-in set difference: set(a - b) == set(a) - set(b),
      and every element of the result must be in a but not in b.
      The bug makes difference() return the intersection instead.

  test_windowed_count_and_content (Bug 3)
      len(windowed(lst, size)) == max(0, len(lst) - size + 1).
      The bug (range(i+1) instead of range(i)) drops the first window,
      making the count one too small and the first window wrong.

  test_lru_read_promotes_to_mru (Bug 4)
      Reading a key in a full LRU cache must make it the MRU, so a subsequent
      insertion evicts a *different* key. The bug (no position update on read)
      means the read key is still evicted.
"""
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from boltons.setutils import IndexedSet
from boltons.iterutils import windowed
from boltons.cacheutils import LRU


# ---------------------------------------------------------------------------
# Bug 1: IndexedSet.index() after discard of non-last element
# ---------------------------------------------------------------------------

@st.composite
def indexed_set_with_ops(draw):
    """
    Draw a list of distinct integers, then a sequence of operations:
    add (from extras) or discard (of existing elements).
    Returns (initial_elements, ops_list).
    """
    n = draw(st.integers(min_value=3, max_value=12))
    initial = list(range(n))  # simple integers 0..n-1

    # Draw a sequence of operations: either discard an index from current set,
    # or add a new element.
    num_ops = draw(st.integers(min_value=1, max_value=8))
    ops = []
    current = list(initial)
    extra_pool = list(range(n, n + 20))

    for _ in range(num_ops):
        if current and draw(st.booleans()):
            # discard a random existing element
            idx = draw(st.integers(min_value=0, max_value=len(current) - 1))
            item = current[idx]
            ops.append(('discard', item))
            current.remove(item)
        elif extra_pool:
            # add a new element
            item = extra_pool.pop(0)
            ops.append(('add', item))
            current.append(item)

    # Ensure at least one discard of a non-last element happened
    # (otherwise the bug might not trigger)
    has_mid_discard = any(
        op == 'discard' and elem != initial[-1]
        for op, elem in ops
    )
    assume(has_mid_discard)
    return initial, ops


@settings(max_examples=500, deadline=None)
@given(indexed_set_with_ops())
def test_indexedset_index_invariant_after_discard(args):
    """
    After any sequence of add/discard ops, for every remaining element x:
      - s[s.index(x)] == x   (index() roundtrip)
      - list(s) == [s[i] for i in range(len(s))]   (iteration == indexing)
    """
    initial, ops = args
    s = IndexedSet(initial)
    for op, elem in ops:
        if op == 'discard':
            s.discard(elem)
        else:
            s.add(elem)

    elements = list(s)
    n = len(s)

    # Property 1: list(s) == [s[i] for i in range(len(s))]
    indexed_list = [s[i] for i in range(n)]
    assert elements == indexed_list, (
        f"list(s) != [s[i] for i in range(len(s))]: "
        f"list={elements}, indexed={indexed_list}"
    )

    # Property 2: s[s.index(x)] == x for every x in s
    for x in elements:
        i = s.index(x)
        retrieved = s[i]
        assert retrieved == x, (
            f"s.index({x!r}) = {i}, but s[{i}] = {retrieved!r} (expected {x!r}). "
            f"set contents: {elements}"
        )


# ---------------------------------------------------------------------------
# Bug 2: IndexedSet.difference() returns intersection instead of difference
# ---------------------------------------------------------------------------

@st.composite
def two_overlapping_indexed_sets(draw):
    """
    Draw two IndexedSets that share at least one element and each have at
    least one unique element. This ensures the difference is non-trivially
    different from both the intersection and the full set.
    """
    # shared: elements in both a and b
    shared = draw(st.lists(
        st.integers(min_value=0, max_value=50),
        min_size=1, max_size=5,
        unique=True,
    ))
    # only_a: elements only in a
    only_a = draw(st.lists(
        st.integers(min_value=51, max_value=100),
        min_size=1, max_size=5,
        unique=True,
    ))
    # only_b: elements only in b
    only_b = draw(st.lists(
        st.integers(min_value=101, max_value=150),
        min_size=0, max_size=5,
        unique=True,
    ))

    a_elems = only_a + shared
    b_elems = shared + only_b

    a = IndexedSet(a_elems)
    b = IndexedSet(b_elems)
    return a, b, set(only_a), set(shared)


@settings(max_examples=500, deadline=None)
@given(two_overlapping_indexed_sets())
def test_indexedset_difference_vs_builtin_set(args):
    """
    a - b must equal set(a) - set(b).
    Every result element must be in a and not in b.
    """
    a, b, only_a, shared = args

    result = a - b
    result_set = set(result)
    expected_set = set(a) - set(b)

    assert result_set == expected_set, (
        f"a - b = {result_set}, expected {expected_set}. "
        f"a={set(a)}, b={set(b)}, intersection={shared}"
    )

    # Element-wise checks
    for x in result:
        assert x in a, f"Result element {x!r} is not in a"
        assert x not in b, f"Result element {x!r} should not be in b"


@settings(max_examples=500, deadline=None)
@given(
    a_elems=st.lists(st.integers(0, 30), min_size=1, max_size=10, unique=True),
    b_elems=st.lists(st.integers(0, 30), min_size=0, max_size=10, unique=True),
)
def test_indexedset_difference_model_based(a_elems, b_elems):
    """Model-based: result of a - b matches built-in set difference."""
    a = IndexedSet(a_elems)
    b = IndexedSet(b_elems)

    result = a - b
    assert set(result) == set(a) - set(b), (
        f"a - b mismatch: got {set(result)}, expected {set(a) - set(b)}"
    )
    assert all(x in a for x in result), "Some result element is not in a"
    assert all(x not in b for x in result), "Some result element is in b"


# ---------------------------------------------------------------------------
# Bug 3: windowed_iter off-by-one — wrong number of windows
# ---------------------------------------------------------------------------

@st.composite
def list_and_window_size(draw):
    """
    Draw a list and a window size such that len(list) >= size.
    This ensures there are windows to check.
    """
    size = draw(st.integers(min_value=1, max_value=8))
    # length can be exactly size (1 window expected) or larger
    extra = draw(st.integers(min_value=0, max_value=10))
    length = size + extra
    lst = draw(st.lists(
        st.integers(min_value=0, max_value=100),
        min_size=length, max_size=length,
    ))
    return lst, size


@settings(max_examples=500, deadline=None)
@given(list_and_window_size())
def test_windowed_count_and_content(args):
    """
    len(windowed(lst, size)) must equal max(0, len(lst) - size + 1).
    Also, each window must equal the corresponding slice of lst.
    The bug makes the count one too small and shifts all windows forward.
    """
    lst, size = args
    n = len(lst)
    windows = windowed(lst, size)

    expected_count = max(0, n - size + 1)
    assert len(windows) == expected_count, (
        f"windowed(lst, {size}) returned {len(windows)} windows, "
        f"expected {expected_count} (len(lst)={n})"
    )

    # Verify each window content
    for i, w in enumerate(windows):
        expected_w = tuple(lst[i:i + size])
        assert w == expected_w, (
            f"Window {i}: got {w}, expected {expected_w}"
        )


@settings(max_examples=500, deadline=None)
@given(
    lst=st.lists(st.integers(), min_size=1, max_size=20),
    size=st.integers(min_value=1, max_value=20),
)
def test_windowed_first_window_is_correct(lst, size):
    """When len(lst) >= size, the first window must be tuple(lst[:size])."""
    assume(len(lst) >= size)
    windows = windowed(lst, size)
    assert len(windows) >= 1, (
        f"Expected at least 1 window for lst of length {len(lst)} and size {size}"
    )
    assert windows[0] == tuple(lst[:size]), (
        f"First window wrong: got {windows[0]}, expected {tuple(lst[:size])}"
    )


# ---------------------------------------------------------------------------
# Bug 4: LRU.__getitem__ does not update LRU position
# ---------------------------------------------------------------------------

@settings(max_examples=500, deadline=None)
@given(
    capacity=st.integers(min_value=2, max_value=6),
    read_key_idx=st.integers(min_value=0, max_value=0),  # always read first-inserted key
)
def test_lru_read_promotes_to_mru(capacity, read_key_idx):
    """
    Fill a cache to capacity with keys 0..capacity-1 (insertion order).
    Read key 0 (the oldest, first inserted).
    Insert a new key to trigger eviction.
    Key 0 must NOT be evicted (it was just read, so it is now MRU).
    Key 1 (second-oldest, never read) must be evicted.

    The bug makes key 0 the eviction victim despite being read, because
    __getitem__ does not update the LRU position.
    """
    cache = LRU(max_size=capacity)

    # Fill cache: keys 0, 1, ..., capacity-1
    for i in range(capacity):
        cache[i] = i * 10

    # Read key 0 — should make it MRU, key 1 becomes LRU
    _ = cache[0]

    # Insert a new key — should evict key 1 (now the LRU)
    new_key = capacity
    cache[new_key] = 999

    assert 0 in cache, (
        f"Key 0 was just read (should be MRU) but was evicted. "
        f"Cache contents: {dict(cache)}"
    )
    assert 1 not in cache, (
        f"Key 1 should have been evicted (it is LRU) but is still in cache. "
        f"Cache contents: {dict(cache)}"
    )
    assert new_key in cache, (
        f"Newly inserted key {new_key} is not in cache."
    )


@st.composite
def lru_access_pattern(draw):
    """
    Draw a capacity and a sequence of writes/reads designed to test LRU order.
    Returns (capacity, operations) where each op is ('write', key, val) or ('read', key).
    """
    capacity = draw(st.integers(min_value=2, max_value=4))
    keys = list(range(capacity + 3))  # more keys than capacity

    ops = []
    # Fill cache
    for i in range(capacity):
        ops.append(('write', keys[i], i))

    # Read some existing keys to refresh their LRU position
    num_reads = draw(st.integers(min_value=1, max_value=capacity))
    read_keys = draw(st.lists(
        st.sampled_from(keys[:capacity]),
        min_size=num_reads, max_size=num_reads,
    ))
    for k in read_keys:
        ops.append(('read', k))

    # Insert new keys to trigger eviction
    new_keys = keys[capacity:]
    num_new = draw(st.integers(min_value=1, max_value=len(new_keys)))
    for k in new_keys[:num_new]:
        ops.append(('write', k, 999))

    return capacity, ops


@settings(max_examples=500, deadline=None)
@given(lru_access_pattern())
def test_lru_eviction_order_after_reads(args):
    """
    After reads, the LRU cache must evict the key with the oldest last-access
    time, where reads count as accesses.

    We simulate the correct LRU behavior ourselves and verify the cache
    matches at every step.
    """
    capacity, ops = args

    cache = LRU(max_size=capacity)
    # Track access order manually: front = MRU, back = LRU
    access_order = []  # list where access_order[0] is MRU

    for op in ops:
        if op[0] == 'write':
            _, key, val = op
            # Update manual tracking
            if key in access_order:
                access_order.remove(key)
            elif len(access_order) >= capacity:
                # will evict LRU (last in access_order)
                evicted = access_order[-1]
                access_order.pop()
            access_order.insert(0, key)
            cache[key] = val
        else:  # read
            _, key = op
            if key in access_order:
                access_order.remove(key)
                access_order.insert(0, key)
                _ = cache[key]
            # skip reads of absent keys

    # Verify: keys in cache == keys in access_order
    cache_keys = set(cache.keys())
    expected_keys = set(access_order)
    assert cache_keys == expected_keys, (
        f"Cache has {cache_keys}, expected {expected_keys} after ops: {ops}"
    )
