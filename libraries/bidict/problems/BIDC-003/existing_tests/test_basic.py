"""Basic tests for bidict."""
import pytest
from bidict import bidict, OrderedBidict


# ---- Basic bidict operations ----

def test_basic_insert_and_lookup():
    b = bidict({'a': 1, 'b': 2, 'c': 3})
    assert b['a'] == 1
    assert b['b'] == 2
    assert b['c'] == 3


def test_inverse_lookup():
    b = bidict({'x': 10, 'y': 20, 'z': 30})
    assert b.inverse[10] == 'x'
    assert b.inverse[20] == 'y'
    assert b.inverse[30] == 'z'


def test_len_equals_inverse_len():
    b = bidict({'a': 1, 'b': 2, 'c': 3})
    assert len(b) == len(b.inverse) == 3


def test_setitem_fresh_key():
    """Setting a fresh key-value pair (no duplication) must work correctly."""
    b = bidict({'a': 1})
    b['b'] = 2
    assert b['b'] == 2
    assert b.inverse[2] == 'b'
    assert len(b) == 2


def test_delete_item():
    b = bidict({'a': 1, 'b': 2})
    del b['a']
    assert 'a' not in b
    assert 1 not in b.inverse
    assert len(b) == 1


def test_forceput_fresh_pair():
    """forceput with a completely new key and value must insert cleanly."""
    b = bidict({'a': 1, 'b': 2})
    b.forceput('c', 3)
    assert b['c'] == 3
    assert b.inverse[3] == 'c'
    assert len(b) == 3


def test_contains():
    b = bidict({'p': 100, 'q': 200})
    assert 'p' in b
    assert 'q' in b
    assert 'r' not in b
    assert 100 in b.inverse
    assert 200 in b.inverse


def test_update_fresh_keys():
    """Test Update fresh keys."""
    b = bidict({'a': 1})
    b.update({'b': 2, 'c': 3})
    assert b['b'] == 2
    assert b['c'] == 3
    assert b.inverse[2] == 'b'
    assert len(b) == 3


def test_keys_values_items():
    b = bidict({'a': 1, 'b': 2})
    assert set(b.keys()) == {'a', 'b'}
    assert set(b.values()) == {1, 2}
    assert set(b.items()) == {('a', 1), ('b', 2)}


# ---- OrderedBidict basics ----

def test_ordered_insertion_order():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    assert list(ob) == [1, 2, 3]
    assert list(ob.values()) == ['a', 'b', 'c']


def test_ordered_inverse():
    ob = OrderedBidict([(10, 'x'), (20, 'y')])
    assert ob.inverse['x'] == 10
    assert ob.inverse['y'] == 20


def test_ordered_setitem_fresh():
    """Adding a new item to OrderedBidict should append at the end."""
    ob = OrderedBidict([(1, 'a'), (2, 'b')])
    ob[3] = 'c'
    assert list(ob) == [1, 2, 3]
    assert ob[3] == 'c'
    assert ob.inverse['c'] == 3


def test_ordered_popitem_last():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    k, v = ob.popitem(last=True)
    assert k == 3
    assert v == 'c'
    assert list(ob) == [1, 2]


def test_ordered_popitem_first():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    k, v = ob.popitem(last=False)
    assert k == 1
    assert v == 'a'
    assert list(ob) == [2, 3]


def test_ordered_move_to_end_last():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    ob.move_to_end(1, last=True)
    assert list(ob) == [2, 3, 1]


def test_ordered_reversed():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    assert list(reversed(ob)) == [3, 2, 1]
