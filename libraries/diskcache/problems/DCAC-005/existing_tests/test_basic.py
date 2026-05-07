"""Basic tests for diskcache."""
import time
import tempfile
import pytest
from diskcache import Cache


def make_cache():
    return Cache(tempfile.mkdtemp())


def test_set_and_get_no_expire():
    """set() and get() without expiry work correctly."""
    c = make_cache()
    c.set('key', 'value')
    assert c.get('key') == 'value'
    c.close()


def test_set_overwrite():
    """set() overwrites existing value."""
    c = make_cache()
    c.set('k', 'v1')
    c.set('k', 'v2')
    assert c.get('k') == 'v2'
    c.close()


def test_add_to_empty_cache():
    """add() on missing key returns True and stores value."""
    c = make_cache()
    result = c.add('k', 'v')
    assert result is True
    assert c.get('k') == 'v'
    c.close()


def test_touch_no_expire():
    """touch() with no expire argument returns True for existing key."""
    c = make_cache()
    c.set('k', 'v')
    result = c.touch('k')
    assert result is True
    assert c.get('k') == 'v'
    c.close()


def test_touch_missing_key():
    """touch() returns False for missing key."""
    c = make_cache()
    result = c.touch('missing')
    assert result is False
    c.close()


def test_expire_no_items():
    """expire() on empty cache returns 0."""
    c = make_cache()
    result = c.expire()
    assert result == 0
    c.close()


def test_expire_no_expired_items():
    """expire() leaves non-expired items untouched."""
    c = make_cache()
    c.set('k', 'v')  # no expiry
    count_before = len(c)
    removed = c.expire()
    assert removed == 0
    assert len(c) == count_before
    assert c.get('k') == 'v'
    c.close()


def test_get_default():
    """get() returns default for missing key."""
    c = make_cache()
    assert c.get('missing', default='default_val') == 'default_val'
    c.close()


def test_delete():
    """delete() removes a key."""
    c = make_cache()
    c.set('k', 'v')
    c.delete('k')
    assert c.get('k') is None
    c.close()


def test_len():
    """len(cache) returns number of items."""
    c = make_cache()
    c.set('a', 1)
    c.set('b', 2)
    assert len(c) == 2
    c.close()


def test_contains():
    """in operator works for cache."""
    c = make_cache()
    c.set('k', 'v')
    assert 'k' in c
    assert 'missing' not in c
    c.close()


def test_incr_new_key():
    """incr() on new key starts from default."""
    c = make_cache()
    result = c.incr('counter')
    assert result == 1
    result2 = c.incr('counter')
    assert result2 == 2
    c.close()
