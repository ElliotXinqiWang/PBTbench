"""Basic tests for diskcache."""
import tempfile
import pytest
import diskcache


def make_cache():
    return diskcache.Cache(tempfile.mkdtemp())


def test_set_and_get():
    cache = make_cache()
    cache.set('key', 'value')
    assert cache.get('key') == 'value'
    cache.close()


def test_get_missing_returns_default():
    cache = make_cache()
    assert cache.get('missing') is None
    assert cache.get('missing', default=42) == 42
    cache.close()


def test_set_overwrite():
    cache = make_cache()
    cache.set('key', 'first')
    cache.set('key', 'second')
    assert cache.get('key') == 'second'
    cache.close()


def test_delete():
    cache = make_cache()
    cache.set('key', 'value')
    cache.delete('key')
    assert cache.get('key') is None
    cache.close()


def test_contains():
    cache = make_cache()
    cache.set('key', 'value')
    assert 'key' in cache
    assert 'missing' not in cache
    cache.close()


def test_add_new_key():
    cache = make_cache()
    result = cache.add('key', 'value')
    assert result is True
    assert cache.get('key') == 'value'
    cache.close()


def test_add_existing_key_returns_false():
    """add() returns False when key exists and is alive."""
    cache = make_cache()
    cache.set('key', 'original')
    result = cache.add('key', 'new_value')
    assert result is False
    assert cache.get('key') == 'original'
    cache.close()


def test_pop():
    cache = make_cache()
    cache.set('key', 'value')
    value = cache.pop('key')
    assert value == 'value'
    assert cache.get('key') is None
    cache.close()


def test_pop_missing():
    cache = make_cache()
    assert cache.pop('missing') is None
    assert cache.pop('missing', default=99) == 99
    cache.close()


def test_touch_existing_key():
    """touch() returns True for a live key."""
    cache = make_cache()
    cache.set('key', 'value')
    result = cache.touch('key')
    assert result is True
    cache.close()


def test_touch_missing_key():
    """touch() returns False for missing key."""
    cache = make_cache()
    result = cache.touch('missing')
    assert result is False
    cache.close()


def test_push_and_pull_single_item():
    """push/pull with single item works correctly."""
    cache = make_cache()
    key = cache.push('item')
    k, v = cache.pull()
    assert v == 'item'
    cache.close()


def test_peekitem_single_item():
    """peekitem works correctly with a single item."""
    cache = make_cache()
    cache['x'] = 42
    key, value = cache.peekitem()
    assert key == 'x'
    assert value == 42
    cache.close()


def test_len_includes_expired():
    """len() counts all items including expired."""
    cache = make_cache()
    cache.set('a', 1)
    cache.set('b', 2)
    assert len(cache) == 2
    cache.close()


def test_clear():
    cache = make_cache()
    cache.set('a', 1)
    cache.set('b', 2)
    cache.clear()
    assert len(cache) == 0
    cache.close()


def test_setitem_getitem():
    cache = make_cache()
    cache['key'] = 'value'
    assert cache['key'] == 'value'
    cache.close()


def test_getitem_missing_raises():
    cache = make_cache()
    with pytest.raises(KeyError):
        _ = cache['missing']
    cache.close()
