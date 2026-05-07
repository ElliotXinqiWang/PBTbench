"""Basic tests for portion."""
import pytest

try:
    import portion as P
except ImportError:
    pytest.skip("portion not available", allow_module_level=True)


def test_atomic_complement_empty():
    """Complement of atomic interval intersected with itself is empty."""
    A = P.closed(0, 5)
    assert A & ~A == P.empty()


def test_complement_covers_all():
    """A | ~A should equal P.open(-inf, inf)."""
    A = P.closed(0, 5)
    assert A | ~A == P.open(-P.inf, P.inf)


def test_invert_open_interval():
    """Complement of open interval."""
    A = P.open(2, 7)
    result = ~A
    assert 2 in result  # 2 is in complement (was excluded by open bound)
    assert 7 in result
    assert 5 not in result  # 5 is inside original, not in complement


def test_invert_singleton():
    """Complement of singleton."""
    A = P.singleton(3)
    result = ~A
    assert 3 not in result
    assert 2 in result
    assert 4 in result


def test_invert_involution_atomic():
    """Test Invert involution atomic."""
    A = P.open(-P.inf, P.inf)
    assert ~~A == A
