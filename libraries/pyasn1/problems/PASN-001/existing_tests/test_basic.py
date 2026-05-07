"""Basic tests for pyasn1."""
import pytest
from pyasn1.type import univ, tag, namedtype, namedval
from pyasn1.codec.ber import encoder, decoder


# ---------------------------------------------------------------------------
# Integer encode/decode
# ---------------------------------------------------------------------------

def test_integer_zero():
    value = univ.Integer(0)
    encoded = encoder.encode(value)
    decoded, remainder = decoder.decode(encoded, asn1Spec=univ.Integer())
    assert int(decoded) == 0
    assert remainder == b''


def test_integer_positive():
    value = univ.Integer(42)
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.Integer())
    assert int(decoded) == 42


def test_integer_negative():
    value = univ.Integer(-1)
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.Integer())
    assert int(decoded) == -1


def test_integer_small_range():
    for n in range(-64, 65):
        value = univ.Integer(n)
        encoded = encoder.encode(value)
        decoded, _ = decoder.decode(encoded, asn1Spec=univ.Integer())
        assert int(decoded) == n, f"roundtrip failed for {n}"


def test_integer_named_values():
    class ErrorCode(univ.Integer):
        namedValues = namedval.NamedValues(
            ('ok', 0), ('error', 1), ('timeout', 2)
        )

    val = ErrorCode('ok')
    encoded = encoder.encode(val)
    decoded, _ = decoder.decode(encoded, asn1Spec=ErrorCode())
    assert int(decoded) == 0


# ---------------------------------------------------------------------------
# OctetString encode/decode (simple, short strings only)
# ---------------------------------------------------------------------------

def test_octetstring_empty():
    value = univ.OctetString(b'')
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.OctetString())
    assert bytes(decoded) == b''


def test_octetstring_hello():
    value = univ.OctetString(b'hello')
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.OctetString())
    assert bytes(decoded) == b'hello'


def test_octetstring_binary():
    value = univ.OctetString(bytes(range(32)))
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.OctetString())
    assert bytes(decoded) == bytes(range(32))


def test_octetstring_short_lengths():
    """Test OctetStrings of various sizes up to 63 bytes (well below 128-byte boundary)."""
    for size in [1, 5, 10, 32, 63]:
        data = bytes(b % 256 for b in range(size))
        value = univ.OctetString(data)
        encoded = encoder.encode(value)
        decoded, _ = decoder.decode(encoded, asn1Spec=univ.OctetString())
        assert bytes(decoded) == data, f"failed for size {size}"


# ---------------------------------------------------------------------------
# Boolean
# ---------------------------------------------------------------------------

def test_boolean_true():
    value = univ.Boolean(True)
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.Boolean())
    assert bool(decoded) is True


def test_boolean_false():
    value = univ.Boolean(False)
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.Boolean())
    assert bool(decoded) is False


# ---------------------------------------------------------------------------
# Null
# ---------------------------------------------------------------------------

def test_null_roundtrip():
    value = univ.Null('')
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.Null())
    assert decoded == univ.Null('')


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_oid_simple():
    """Test Oid simple."""
    value = univ.ObjectIdentifier((2, 5, 4, 3))
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.ObjectIdentifier())
    assert tuple(decoded) == (2, 5, 4, 3)


def test_oid_0_prefix():
    """Test Oid 0 prefix."""
    value = univ.ObjectIdentifier((0, 9, 2342))
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.ObjectIdentifier())
    assert tuple(decoded) == (0, 9, 2342)


# ---------------------------------------------------------------------------
# Sequence encode/decode
# ---------------------------------------------------------------------------

def test_sequence_simple():
    seq = univ.Sequence()
    seq.setComponentByPosition(0, univ.Integer(1))
    seq.setComponentByPosition(1, univ.Integer(2))
    encoded = encoder.encode(seq)
    decoded, _ = decoder.decode(encoded)
    assert int(decoded[0]) == 1
    assert int(decoded[1]) == 2


def test_sequence_of():
    seq = univ.SequenceOf(componentType=univ.Integer())
    seq.extend([univ.Integer(i) for i in range(5)])
    encoded = encoder.encode(seq)
    decoded, _ = decoder.decode(encoded, asn1Spec=univ.SequenceOf(componentType=univ.Integer()))
    assert [int(decoded[i]) for i in range(5)] == list(range(5))


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_implicit_tagging_single_level():
    """IMPLICIT tag on a simple OctetString (1-element TagSet): format bit unchanged."""
    # [CONTEXT 5] IMPLICIT OctetString
    taggedType = univ.OctetString().clone(
        tagSet=univ.OctetString.tagSet.tagImplicitly(
            tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 5)
        )
    )
    value = taggedType.clone(b'hello')
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=taggedType)
    assert bytes(decoded) == b'hello'


def test_explicit_tagging_simple():
    """EXPLICIT tag wrapping — should always work."""
    taggedType = univ.Integer().clone(
        tagSet=univ.Integer.tagSet.tagExplicitly(
            tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 0)
        )
    )
    value = taggedType.clone(99)
    encoded = encoder.encode(value)
    decoded, _ = decoder.decode(encoded, asn1Spec=taggedType)
    assert int(decoded) == 99


# ---------------------------------------------------------------------------
# Tag class and TagSet creation
# ---------------------------------------------------------------------------

def test_tag_creation():
    t = tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 3)
    assert t.tagClass == tag.tagClassContext
    assert t.tagFormat == tag.tagFormatSimple
    assert t.tagId == 3


def test_tagset_length():
    ts = univ.Integer.tagSet
    assert len(ts) == 1

    ts_explicit = ts.tagExplicitly(tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 0))
    assert len(ts_explicit) == 2


def test_tagset_isSuperTagSetOf():
    ts = univ.Integer.tagSet
    assert ts.isSuperTagSetOf(ts)
