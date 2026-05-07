"""
Basic tests for msgpack integer and data roundtrip.
These tests verify the common use cases of the library.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import msgpack


def test_positive_fixint():
    """positive fixint: [0, 127] — single-byte encoding."""
    for v in [0, 1, 63, 127]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_negative_fixint():
    """negative fixint: [-32, -1] — single-byte encoding."""
    for v in [-1, -16, -32]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_uint8():
    """uint8: [128, 255] — 2-byte encoding."""
    for v in [128, 200, 255]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_int8():
    """int8: [-128, -33] — 2-byte signed encoding."""
    for v in [-33, -100, -128]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_uint16_small():
    """uint16 small values: [256, 32767] — 3-byte encoding."""
    for v in [256, 512, 1000, 10000, 32767]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_int16():
    """int16: [-32768, -129] — 3-byte signed encoding."""
    for v in [-129, -1000, -32768]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_uint32():
    """uint32: [65536, 4294967295] — 5-byte encoding."""
    for v in [65536, 100000, 4294967295]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_int32():
    """int32: [-2147483648, -32769] — 5-byte signed encoding."""
    for v in [-32769, -1000000, -2147483648]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_uint64():
    """uint64: [4294967296, 2^64-1] — 9-byte encoding."""
    for v in [4294967296, 2**63 - 1, 2**64 - 1]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_int64():
    """int64: [-2^63, -2147483649] — 9-byte signed encoding."""
    for v in [-2147483649, -(2**63)]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_none_and_bool():
    assert msgpack.unpackb(msgpack.packb(None)) is None
    assert msgpack.unpackb(msgpack.packb(True)) is True
    assert msgpack.unpackb(msgpack.packb(False)) is False


def test_bytes():
    for v in [b"", b"hello", b"x" * 100]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_string():
    for v in ["", "hello", "a" * 100]:
        assert msgpack.unpackb(msgpack.packb(v), raw=False) == v


def test_list():
    for v in [[], [1, 2, 3], [0, -1, 127, -128, 256]]:
        assert msgpack.unpackb(msgpack.packb(v)) == v


def test_dict():
    v = {"key": 1, "val": -100}
    assert msgpack.unpackb(msgpack.packb(v), raw=False) == v


def test_nested():
    v = [1, [2, [3, [4]]], {"a": 5}]
    assert msgpack.unpackb(msgpack.packb(v), raw=False) == v
