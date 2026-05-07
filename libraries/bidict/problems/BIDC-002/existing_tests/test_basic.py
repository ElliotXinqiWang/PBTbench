"""Basic tests for bidict."""
import pytest
from bidict import bidict, OrderedBidict


def test_basic_insert_and_retrieve():
    b = bidict({'a': 1, 'b': 2})
    assert b['a'] == 1
    assert b['b'] == 2


def test_inverse_access():
    b = bidict({'x': 10, 'y': 20})
    assert b.inverse[10] == 'x'
    assert b.inverse[20] == 'y'


def test_inverse_alias():
    b = bidict({'p': 100})
    assert b.inv[100] == 'p'


def test_setitem_and_contains():
    b = bidict()
    b['hello'] = 'world'
    assert 'hello' in b
    assert 'world' in b.inverse


def test_delitem():
    b = bidict({'a': 1, 'b': 2})
    del b['a']
    assert 'a' not in b
    assert 1 not in b.inverse


def test_len():
    b = bidict({'a': 1, 'b': 2, 'c': 3})
    assert len(b) == 3


def test_iter_keys():
    b = bidict({'k1': 'v1', 'k2': 'v2'})
    assert set(b) == {'k1', 'k2'}


def test_update():
    b = bidict({'a': 1})
    b.update({'b': 2, 'c': 3})
    assert b['b'] == 2
    assert b['c'] == 3
    assert b.inverse[2] == 'b'


def test_ordered_bidict_insertion_order():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    assert list(ob) == [1, 2, 3]
    assert list(ob.values()) == ['a', 'b', 'c']


def test_ordered_bidict_inverse():
    ob = OrderedBidict([(10, 'x'), (20, 'y')])
    assert ob.inverse['x'] == 10
    assert ob.inverse['y'] == 20


def test_ordered_bidict_setitem():
    ob = OrderedBidict()
    ob[5] = 50
    ob[6] = 60
    assert ob[5] == 50
    assert ob.inverse[60] == 6


def test_ordered_bidict_popitem_last():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    key, val = ob.popitem(last=True)
    assert key == 3
    assert val == 'c'
    assert len(ob) == 2


def test_ordered_bidict_popitem_first():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    key, val = ob.popitem(last=False)
    assert key == 1
    assert val == 'a'
    assert len(ob) == 2


def test_move_to_end_last():
    """Test Move to end last."""
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    ob.move_to_end(1, last=True)
    assert list(ob) == [2, 3, 1]


def test_equals_order_sensitive_same_content_same_order():
    """equals_order_sensitive returns True for identical ordered bidicts — passes on both."""
    ob1 = OrderedBidict([(1, 10), (2, 20)])
    ob2 = OrderedBidict([(1, 10), (2, 20)])
    assert ob1.equals_order_sensitive(ob2)


def test_equals_order_sensitive_different_order():
    """equals_order_sensitive returns False for same items in different order — passes on both."""
    ob1 = OrderedBidict([(1, 10), (2, 20)])
    ob2 = OrderedBidict([(2, 20), (1, 10)])
    assert not ob1.equals_order_sensitive(ob2)


def test_equals_order_sensitive_non_mapping():
    """equals_order_sensitive returns False for non-Mapping — passes on both."""
    ob = OrderedBidict([(1, 10)])
    assert not ob.equals_order_sensitive([1, 10])
    assert not ob.equals_order_sensitive(None)
