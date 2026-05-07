"""Basic tests for bidict."""
import pytest
from bidict import bidict as Bidict, OrderedBidict, frozenbidict
from bidict._dup import OnDup, RAISE, DROP_OLD


def test_basic_create():
    b = Bidict({1: 'a', 2: 'b', 3: 'c'})
    assert len(b) == 3
    assert b[1] == 'a'
    assert b.inverse['a'] == 1


def test_setitem_new_key():
    b = Bidict({1: 'a'})
    b[2] = 'b'
    assert b[2] == 'b'
    assert b.inverse['b'] == 2
    assert len(b) == 2


def test_delitem():
    b = Bidict({1: 'a', 2: 'b'})
    del b[1]
    assert 1 not in b
    assert 'a' not in b.inverse
    assert len(b) == 1


def test_inverse_property():
    b = Bidict({'x': 10, 'y': 20})
    assert b.inverse[10] == 'x'
    assert b.inverse[20] == 'y'


def test_forceput_new_key_new_val():
    b = Bidict({'a': 1})
    b.forceput('b', 2)
    assert b['b'] == 2
    assert b.inverse[2] == 'b'


def test_putall_no_conflict():
    b = Bidict({1: 'a', 2: 'b'})
    b.putall([(3, 'c'), (4, 'd')])
    assert b[3] == 'c'
    assert b[4] == 'd'
    assert len(b) == 4


def test_putall_rollback_on_key_dup_raise():
    """putall with on_dup=RAISE rolls back on key-dup failure."""
    b = Bidict({1: 'a', 2: 'b'})
    snap = dict(b)
    try:
        b.putall([(1, 'c')], on_dup=OnDup(key=RAISE, val=DROP_OLD))
    except Exception:
        pass
    assert dict(b) == snap


def test_update_from_dict():
    b = Bidict({'a': 1})
    b.update({'b': 2, 'c': 3})
    assert b['b'] == 2
    assert b['c'] == 3
    assert b['a'] == 1


def test_orderedbidict_insertion_order():
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    assert list(ob.keys()) == [1, 2, 3]
    assert list(ob.values()) == ['a', 'b', 'c']


def test_orderedbidict_move_to_end_last():
    """move_to_end(last=True) moves to back."""
    ob = OrderedBidict([(1, 'a'), (2, 'b'), (3, 'c')])
    ob.move_to_end(1, last=True)
    assert list(ob.keys()) == [2, 3, 1]


def test_orderedbidict_popitem():
    ob = OrderedBidict([(1, 'a'), (2, 'b')])
    k, v = ob.popitem(last=True)
    assert k == 2
    assert v == 'b'
    assert len(ob) == 1


def test_frozenbidict_hash():
    fb = frozenbidict({'x': 10})
    h = hash(fb)
    assert isinstance(h, int)
    assert hash(fb) == h  # stable


def test_bidict_copy():
    b = Bidict({'a': 1, 'b': 2})
    b2 = b.copy()
    assert dict(b2) == dict(b)
    assert b2 is not b


def test_bidict_len_and_iter():
    b = Bidict({i: i * 10 for i in range(5)})
    assert len(b) == 5
    keys = list(b)
    assert set(keys) == {0, 1, 2, 3, 4}
