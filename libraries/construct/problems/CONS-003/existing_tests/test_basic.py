"""Basic tests for construct."""
import pytest

try:
    import construct as C
except ImportError:
    pytest.skip("construct not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# Basic integer roundtrips
# ---------------------------------------------------------------------------

def test_int8ub_roundtrip():
    """Int8ub parses and builds single bytes correctly."""
    for n in [0, 1, 127, 128, 200, 255]:
        assert C.Int8ub.parse(C.Int8ub.build(n)) == n


def test_int16ub_roundtrip():
    """Int16ub handles 16-bit unsigned big-endian values."""
    for n in [0, 1, 255, 1000, 32767, 65535]:
        assert C.Int16ub.parse(C.Int16ub.build(n)) == n


def test_int32ub_roundtrip():
    """Int32ub handles 32-bit unsigned big-endian values."""
    for n in [0, 1, 255, 65535, 2**31 - 1, 2**32 - 1]:
        assert C.Int32ub.parse(C.Int32ub.build(n)) == n


# ---------------------------------------------------------------------------
# Bytes / GreedyBytes
# ---------------------------------------------------------------------------

def test_greedy_bytes_roundtrip():
    """GreedyBytes parses and builds arbitrary byte strings."""
    for data in [b"", b"hello", b"\x00\xff\xfe", b"a" * 20]:
        assert C.GreedyBytes.parse(C.GreedyBytes.build(data)) == data


def test_bytes_fixed_roundtrip():
    """Bytes(n) reads and writes exactly n bytes."""
    d = C.Bytes(4)
    for data in [b"\x00\x00\x00\x00", b"TEST", b"\xff\xfe\xfd\xfc"]:
        assert d.parse(d.build(data)) == data


# ---------------------------------------------------------------------------
# Struct
# ---------------------------------------------------------------------------

def test_struct_basic_roundtrip():
    """Struct with Int8ub and Int16ub fields."""
    d = C.Struct("a" / C.Int8ub, "b" / C.Int16ub)
    obj = {"a": 42, "b": 1000}
    result = d.parse(d.build(obj))
    assert result.a == 42 and result.b == 1000


def test_struct_bytes_field():
    """Struct containing a fixed Bytes field."""
    d = C.Struct("magic" / C.Bytes(4), "version" / C.Int8ub)
    obj = {"magic": b"CONS", "version": 3}
    result = d.parse(d.build(obj))
    assert result.magic == b"CONS" and result.version == 3


# ---------------------------------------------------------------------------
# Array
# ---------------------------------------------------------------------------

def test_array_byte_roundtrip():
    """Array of 5 Bytes parses and builds correctly."""
    d = C.Array(5, C.Byte)
    values = [0, 1, 2, 3, 4]
    assert list(d.parse(d.build(values))) == values


def test_array_int16ub_roundtrip():
    """Array of Int16ub with diverse values."""
    d = C.Array(3, C.Int16ub)
    values = [0, 1000, 65535]
    assert list(d.parse(d.build(values))) == values


# ---------------------------------------------------------------------------
# RepeatUntil tests
# ---------------------------------------------------------------------------

def test_repeat_until_all_nonterminating_elements_present():
    """Test Repeat until all nonterminating elements present."""
    # Predicate: stop when element equals 99
    d = C.RepeatUntil(lambda x, lst, ctx: x == 99, C.Byte)
    data_bytes = d.build([1, 2, 3, 99])
    result = d.parse(data_bytes)
    # On both versions, elements 1, 2, 3 are in result (only 99 differs)
    assert 1 in result and 2 in result and 3 in result


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_zigzag_zero_roundtrip():
    """ZigZag encoding of zero is correct on both versions."""
    assert C.ZigZag.parse(C.ZigZag.build(0)) == 0


def test_zigzag_positive_roundtrip():
    """Test Zigzag positive roundtrip."""
    for n in [1, 2, 63, 64, 127, 128, 1000, 2**15]:
        result = C.ZigZag.parse(C.ZigZag.build(n))
        assert result == n, f"ZigZag roundtrip failed for {n}: got {result}"
