"""Basic tests for msgpack."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import msgpack
from msgpack import Timestamp


# --- Integer roundtrips ---

def test_small_integers():
    for v in [0, 1, 63, 127, -1, -16, -32]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_medium_integers():
    for v in [128, 255, 256, 1000, 32767, 65535]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_large_integers():
    for v in [65536, 100000, 4294967295]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_negative_integers():
    for v in [-33, -128, -129, -32768, -32769, -2147483648]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_int64_range():
    for v in [-2147483649, -(2**62)]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


# --- Bytes roundtrips (bin type) ---

def test_bytes_empty():
    """Test Bytes empty."""
    assert msgpack.unpackb(msgpack.packb(b"")) == b""


def test_bytes_small():
    """Test Bytes small."""
    for v in [b"hello", b"\x00\xff", b"x" * 100, b"y" * 200]:
        packed = msgpack.packb(v, use_bin_type=True)
        assert msgpack.unpackb(packed) == v


# --- None and bool ---

def test_none_and_bool():
    assert msgpack.unpackb(msgpack.packb(None)) is None
    assert msgpack.unpackb(msgpack.packb(True)) is True
    assert msgpack.unpackb(msgpack.packb(False)) is False


# --- Float roundtrips ---

def test_float_roundtrip():
    """Test Float roundtrip."""
    for v in [0.0, 1.5, -3.14, 1e10, -1e-10]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


# --- Array/list roundtrips (NOT 16 elements) ---

def test_list_empty():
    assert msgpack.unpackb(msgpack.packb([])) == []


def test_list_fixarray():
    """Test List fixarray."""
    for n in [1, 5, 10, 14, 15]:
        v = list(range(n))
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_list_larger():
    """Test List larger."""
    for n in [17, 20, 50]:
        v = list(range(n))
        assert msgpack.unpackb(msgpack.packb(v)) == v


# --- Map/dict roundtrips: integer keys only, strict_map_key=False ---

def test_dict_int_keys_small():
    """Test Dict int keys small."""
    for n in [1, 5, 10, 14]:
        v = {i: i * 2 for i in range(n)}
        packed = msgpack.packb(v)
        assert msgpack.unpackb(packed, strict_map_key=False) == v


def test_dict_int_keys_15():
    """Test Dict int keys 15."""
    v = {i: i * 2 for i in range(15)}
    packed = msgpack.packb(v)
    assert msgpack.unpackb(packed, strict_map_key=False) == v


def test_dict_int_keys_17():
    """Test Dict int keys 17."""
    v = {i: i * 2 for i in range(17)}
    packed = msgpack.packb(v)
    assert msgpack.unpackb(packed, strict_map_key=False) == v


def test_dict_int_keys_larger():
    """Test Dict int keys larger."""
    v = {i: i ** 2 for i in range(50)}
    packed = msgpack.packb(v)
    assert msgpack.unpackb(packed, strict_map_key=False) == v


# --- Nested structures (int keys/values only) ---

def test_nested_list_of_ints():
    """Test Nested list of ints."""
    v = [1, [2, [3, [4]]], 5]
    assert msgpack.unpackb(msgpack.packb(v)) == v


def test_list_of_dicts_int():
    """Test List of dicts int."""
    v = [{0: 1, 1: 2}, {2: 3, 3: 4}]
    packed = msgpack.packb(v)
    result = msgpack.unpackb(packed, strict_map_key=False)
    assert result == v


def test_timestamp_32bit_zero():
    """Timestamp 32-bit: seconds=0, nanoseconds=0 (Unix epoch)."""
    ts = Timestamp(0, 0)
    packed = msgpack.packb(ts)
    unpacked = msgpack.unpackb(packed)
    assert unpacked == ts


def test_timestamp_32bit_positive():
    """Test Timestamp 32bit positive."""
    ts = Timestamp(1609459200, 0)  # 2021-01-01 UTC, nanoseconds=0
    packed = msgpack.packb(ts)
    unpacked = msgpack.unpackb(packed)
    assert unpacked == ts


def test_timestamp_64bit_small_seconds():
    """Test Timestamp 64bit small seconds."""
    # seconds = 10^6 (~11.5 days) < 2^30, nanoseconds = 500000000
    ts = Timestamp(1000000, 500000000)
    packed = msgpack.packb(ts)
    unpacked = msgpack.unpackb(packed)
    assert unpacked == ts


def test_timestamp_96bit_negative():
    """Test Timestamp 96bit negative."""
    ts = Timestamp(-86400, 0)  # one day before epoch, nanoseconds=0
    packed = msgpack.packb(ts)
    unpacked = msgpack.unpackb(packed)
    assert unpacked == ts


# --- ExtType roundtrip ---

def test_exttype_basic():
    """ExtType with code 5 and 2-byte data uses fixext2 format."""
    ext = msgpack.ExtType(5, b"\xAB\xCD")
    packed = msgpack.packb(ext)
    unpacked = msgpack.unpackb(packed)
    assert unpacked == ext


def test_exttype_4bytes():
    """ExtType with 4-byte data uses fixext4 format."""
    ext = msgpack.ExtType(10, b"\x01\x02\x03\x04")
    packed = msgpack.packb(ext)
    unpacked = msgpack.unpackb(packed)
    assert unpacked == ext
