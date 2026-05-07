"""Basic tests for diskcache."""
import tempfile
from diskcache import Cache, Deque


def test_cache_set_get():
    with tempfile.TemporaryDirectory() as d:
        c = Cache(d)
        c.set('key', 'value')
        assert c['key'] == 'value'
        c.close()


def test_cache_delete():
    with tempfile.TemporaryDirectory() as d:
        c = Cache(d)
        c['key'] = 'value'
        del c['key']
        assert 'key' not in c
        c.close()


def test_cache_set_with_tag():
    with tempfile.TemporaryDirectory() as d:
        c = Cache(d)
        c.set('k1', 'v1', tag='group_a')
        c.set('k2', 'v2', tag='group_a')
        c.set('k3', 'v3', tag='group_b')
        assert c['k1'] == 'v1'
        assert c['k2'] == 'v2'
        assert c['k3'] == 'v3'
        c.close()


def test_cache_evict_by_tag():
    """Test basic eviction by tag (does NOT re-set with different tag)."""
    with tempfile.TemporaryDirectory() as d:
        c = Cache(d)
        c.set('k1', 'v1', tag='group_a')
        c.set('k2', 'v2', tag='group_b')
        c.evict('group_a')
        assert 'k1' not in c
        assert 'k2' in c
        c.close()


def test_cache_pop():
    with tempfile.TemporaryDirectory() as d:
        c = Cache(d)
        c.set('key', 42)
        val = c.pop('key')
        assert val == 42
        assert 'key' not in c
        c.close()


def test_cache_expire():
    with tempfile.TemporaryDirectory() as d:
        c = Cache(d)
        c.set('key', 'val', expire=0.001)
        import time
        time.sleep(0.01)
        assert c.get('key') is None
        c.close()


def test_cache_add():
    with tempfile.TemporaryDirectory() as d:
        c = Cache(d)
        assert c.add('key', 'first')
        assert not c.add('key', 'second')  # already exists
        assert c['key'] == 'first'
        c.close()


def test_cache_contains():
    with tempfile.TemporaryDirectory() as d:
        c = Cache(d)
        c['x'] = 1
        assert 'x' in c
        assert 'y' not in c
        c.close()


def test_cache_incr_decr():
    with tempfile.TemporaryDirectory() as d:
        c = Cache(d)
        c['counter'] = 0
        c.incr('counter')
        assert c['counter'] == 1
        c.decr('counter')
        assert c['counter'] == 0
        c.close()


def test_deque_basic():
    with tempfile.TemporaryDirectory() as d:
        dq = Deque(directory=d)
        dq.append(1)
        dq.append(2)
        dq.appendleft(0)
        assert list(dq) == [0, 1, 2]
