"""Ground-truth PBT for DCAC-001: Cache.set() stale tag on UPDATE path."""
import tempfile
import pytest
from hypothesis import given, settings, strategies as st
from diskcache import Cache


@settings(max_examples=500, deadline=None)
@given(
    key=st.text(min_size=1, max_size=10),
    val1=st.integers(),
    val2=st.integers(),
    tag1=st.text(min_size=1, max_size=5),
    tag2=st.text(min_size=1, max_size=5),
)
def test_tag_updated_on_reset(key, val1, val2, tag1, tag2):
    """When re-setting a key with a new tag, the tag should be updated."""
    if tag1 == tag2:
        return  # need different tags to observe the bug

    with tempfile.TemporaryDirectory() as d:
        cache = Cache(d)
        try:
            cache.set(key, val1, tag=tag1)
            cache.set(key, val2, tag=tag2)

            # The tag should now be tag2, not tag1
            # Evicting by old tag should NOT remove the key
            evicted = cache.evict(tag1)
            assert key in cache, (
                f"Key '{key}' was evicted by old tag '{tag1}' after re-set with tag '{tag2}'"
            )
            assert cache[key] == val2
        finally:
            cache.close()


@settings(max_examples=500, deadline=None)
@given(
    key=st.text(min_size=1, max_size=10),
    val1=st.integers(),
    val2=st.integers(),
    tag1=st.text(min_size=1, max_size=5),
    tag2=st.text(min_size=1, max_size=5),
)
def test_tag_retrievable_after_reset(key, val1, val2, tag1, tag2):
    """After re-setting a key, pop with tag=True should return the new tag."""
    if tag1 == tag2:
        return

    with tempfile.TemporaryDirectory() as d:
        cache = Cache(d)
        try:
            cache.set(key, val1, tag=tag1)
            cache.set(key, val2, tag=tag2)

            value, tag = cache.pop(key, tag=True)
            assert value == val2
            assert tag == tag2, (
                f"Expected tag '{tag2}' but got '{tag}' (stale tag from first set)"
            )
        finally:
            cache.close()
