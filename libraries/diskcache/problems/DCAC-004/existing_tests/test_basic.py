"""Basic tests for diskcache."""
import pytest
from diskcache import Deque


def test_deque_append_and_iter():
    d = Deque()
    d.append(1)
    d.append(2)
    d.append(3)
    assert list(d) == [1, 2, 3]
    d._cache.close()


def test_deque_appendleft_empty():
    """appendleft on empty deque — no maxlen, no trimming."""
    d = Deque()
    d.appendleft('a')
    d.appendleft('b')
    assert list(d) == ['b', 'a']
    d._cache.close()


def test_deque_pop():
    d = Deque()
    d.extend([10, 20, 30])
    assert d.pop() == 30
    assert d.pop() == 20
    d._cache.close()


def test_deque_popleft():
    d = Deque()
    d.extend([10, 20, 30])
    assert d.popleft() == 10
    assert d.popleft() == 20
    d._cache.close()


def test_deque_pop_empty_raises():
    d = Deque()
    with pytest.raises(IndexError):
        d.pop()
    d._cache.close()


def test_deque_popleft_empty_raises():
    d = Deque()
    with pytest.raises(IndexError):
        d.popleft()
    d._cache.close()


def test_deque_rotate_zero():
    """rotate(0) is a no-op."""
    d = Deque()
    d.extend([1, 2, 3, 4, 5])
    d.rotate(0)
    assert list(d) == [1, 2, 3, 4, 5]
    d._cache.close()


def test_deque_rotate_negative_single():
    """rotate(-1) moves front to back."""
    d = Deque()
    d.extend([1, 2, 3])
    d.rotate(-1)
    assert list(d) == [2, 3, 1]
    d._cache.close()


def test_deque_maxlen_on_init():
    """maxlen passed to constructor is enforced from the start."""
    d = Deque([1, 2, 3, 4, 5], maxlen=3)
    assert list(d) == [3, 4, 5]
    assert len(d) == 3
    d._cache.close()


def test_deque_append_at_maxlen():
    """append() at maxlen drops the leftmost (oldest) element."""
    d = Deque([1, 2, 3], maxlen=3)
    d.append(4)
    assert list(d) == [2, 3, 4]
    d._cache.close()


def test_deque_positive_index():
    d = Deque()
    d.extend([10, 20, 30])
    assert d[0] == 10
    assert d[1] == 20
    assert d[2] == 30
    d._cache.close()


def test_deque_index_out_of_range():
    d = Deque()
    d.extend([10, 20, 30])
    with pytest.raises(IndexError):
        _ = d[3]
    with pytest.raises(IndexError):
        _ = d[-4]
    d._cache.close()


def test_deque_len():
    d = Deque()
    d.extend([1, 2, 3, 4])
    assert len(d) == 4
    d.pop()
    assert len(d) == 3
    d._cache.close()


def test_deque_peek_and_peekleft():
    d = Deque()
    d.extend([1, 2, 3])
    assert d.peek() == 3
    assert d.peekleft() == 1
    d._cache.close()
