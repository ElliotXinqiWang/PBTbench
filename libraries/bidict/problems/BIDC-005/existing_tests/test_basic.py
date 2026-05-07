"""Basic tests for bidict."""
import pytest
from bidict import bidict as Bidict, OrderedBidict, frozenbidict
from bidict._dup import OnDup, RAISE, DROP_OLD


def test_basic_bidict_create():
    b = Bidict({1: 'a', 2: 'b'})
    assert len(b) == 2
    assert b[1] == 'a'
    assert b.inverse['a'] == 1


def test_orderedbidict_insertion_order():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    assert list(ob.keys()) == [1, 2, 3]


def test_orderedbidict_forceput_no_dup():
    """forceput with completely fresh key and val — no duplication."""
    ob = OrderedBidict([(1, 'a'), (2, 'b')])
    ob.forceput(3, 'c')
    assert ob[3] == 'c'
    assert ob.inverse['c'] == 3
    assert len(ob) == 3


def test_orderedbidict_forceput_key_dup_only():
    """forceput with key-dup only (val is fresh) — safe branch."""
    ob = OrderedBidict([(1, 'a'), (2, 'b')])
    ob.forceput(1, 'c')
    assert ob[1] == 'c'
    assert ob.inverse['c'] == 1
    assert 'a' not in ob.inverse


def test_equals_order_sensitive_same_items_same_order():
    """equals_order_sensitive should return True for identical ordered bidicts."""
    ob1 = OrderedBidict([(1, 'a'), (2, 'b')])
    ob2 = OrderedBidict([(1, 'a'), (2, 'b')])
    assert ob1.equals_order_sensitive(ob2)


def test_equals_order_sensitive_different_order():
    """equals_order_sensitive should return False for same items, different order."""
    ob1 = OrderedBidict([(1, 'a'), (2, 'b')])
    ob2 = OrderedBidict([(2, 'b'), (1, 'a')])
    assert not ob1.equals_order_sensitive(ob2)


def test_equals_order_sensitive_non_mapping():
    """equals_order_sensitive should return False for non-mapping objects."""
    ob = OrderedBidict([(1, 'a'), (2, 'b')])
    assert not ob.equals_order_sensitive([1, 2])
    assert not ob.equals_order_sensitive("string")


def test_popitem_single_item():
    """popitem on a single-item bidict always returns that item."""
    ob = OrderedBidict([(42, 'x')])
    k, v = ob.popitem(last=True)
    assert k == 42
    assert v == 'x'
    assert len(ob) == 0


def test_popitem_empty_raises():
    """popitem on empty OrderedBidict raises KeyError."""
    ob = OrderedBidict()
    with pytest.raises(KeyError):
        ob.popitem()


def test_frozenbidict_hash_stable():
    """frozenbidict hash is stable (same value on repeated calls)."""
    fb = frozenbidict({1: 'a', 2: 'b'})
    h1 = hash(fb)
    h2 = hash(fb)
    assert h1 == h2


def test_frozenbidict_hash_equal_content():
    """Two frozenbidict instances with identical content have the same hash."""
    fb1 = frozenbidict({1: 'a'})
    fb2 = frozenbidict({1: 'a'})
    assert fb1 == fb2
    assert hash(fb1) == hash(fb2)


def test_frozenbidict_in_set():
    """frozenbidict can be stored in a set."""
    fb = frozenbidict({'x': 10})
    s = {fb}
    assert fb in s


def test_bidict_inverse_consistency():
    b = Bidict({'a': 1, 'b': 2})
    for k, v in b.items():
        assert b.inverse[v] == k


def test_orderedbidict_clear():
    ob = OrderedBidict([(1, 'a'), (2, 'b')])
    ob.clear()
    assert len(ob) == 0
    assert list(ob.keys()) == []
