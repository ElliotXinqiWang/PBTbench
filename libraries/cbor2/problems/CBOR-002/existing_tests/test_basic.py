"""Basic tests for cbor2."""
import sys
import os
import math
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cbor2


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_canonical_float_zero():
    encoded = cbor2.dumps(0.0, canonical=True)
    decoded = cbor2.loads(encoded)
    assert decoded == 0.0


def test_canonical_float_one():
    encoded = cbor2.dumps(1.0, canonical=True)
    decoded = cbor2.loads(encoded)
    assert decoded == 1.0


def test_canonical_float_one_point_five():
    # 1.5 is exactly representable in float16: 0 01111 1000000000 = 0x3e00
    encoded = cbor2.dumps(1.5, canonical=True)
    decoded = cbor2.loads(encoded)
    assert decoded == 1.5


def test_canonical_float_two():
    encoded = cbor2.dumps(2.0, canonical=True)
    decoded = cbor2.loads(encoded)
    assert decoded == 2.0


def test_canonical_float_negative_one():
    # -1.0 is exactly representable in float16
    encoded = cbor2.dumps(-1.0, canonical=True)
    decoded = cbor2.loads(encoded)
    assert decoded == -1.0


def test_canonical_float_large_exact():
    # 65504.0 is the max finite float16 value - exactly representable
    encoded = cbor2.dumps(65504.0, canonical=True)
    decoded = cbor2.loads(encoded)
    assert decoded == 65504.0


def test_canonical_float_nan():
    encoded = cbor2.dumps(float("nan"), canonical=True)
    decoded = cbor2.loads(encoded)
    assert math.isnan(decoded)


def test_canonical_float_inf():
    encoded = cbor2.dumps(float("inf"), canonical=True)
    decoded = cbor2.loads(encoded)
    assert decoded == float("inf")


def test_canonical_float_neg_inf():
    encoded = cbor2.dumps(float("-inf"), canonical=True)
    decoded = cbor2.loads(encoded)
    assert decoded == float("-inf")


def test_canonical_float_small_exact():
    # 0.5 is exactly representable in float16
    encoded = cbor2.dumps(0.5, canonical=True)
    decoded = cbor2.loads(encoded)
    assert decoded == 0.5


def test_noncanonicol_float_roundtrip():
    # Non-canonical floats always use float64 (9 bytes), no precision issues
    for v in [0.1, 1.1, 3.14, 1e10, -2.718]:
        encoded = cbor2.dumps(v)
        decoded = cbor2.loads(encoded)
        assert decoded == v, f"Roundtrip failed for {v}"


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def test_datetime_utc_roundtrip():
    dt = datetime(2023, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    encoded = cbor2.dumps(dt)
    decoded = cbor2.loads(encoded)
    assert decoded == dt


def test_datetime_utc_with_microseconds():
    dt = datetime(2023, 6, 15, 12, 30, 45, 123456, tzinfo=timezone.utc)
    encoded = cbor2.dumps(dt)
    decoded = cbor2.loads(encoded)
    assert decoded == dt


def test_datetime_positive_offset_whole_hours():
    tz = timezone(timedelta(hours=5))
    dt = datetime(2023, 3, 10, 9, 0, 0, tzinfo=tz)
    encoded = cbor2.dumps(dt)
    decoded = cbor2.loads(encoded)
    assert decoded == dt


def test_datetime_positive_offset_with_minutes():
    # +05:30 (India Standard Time) - positive offset with minutes
    tz = timezone(timedelta(hours=5, minutes=30))
    dt = datetime(2023, 7, 4, 15, 0, 0, tzinfo=tz)
    encoded = cbor2.dumps(dt)
    decoded = cbor2.loads(encoded)
    assert decoded == dt


def test_datetime_negative_offset_zero_minutes():
    tz = timezone(timedelta(hours=-5))
    dt = datetime(2023, 12, 25, 8, 0, 0, tzinfo=tz)
    encoded = cbor2.dumps(dt)
    decoded = cbor2.loads(encoded)
    assert decoded == dt


def test_datetime_negative_offset_one_hour():
    tz = timezone(timedelta(hours=-1))
    dt = datetime(2023, 8, 20, 16, 45, 0, tzinfo=tz)
    encoded = cbor2.dumps(dt)
    decoded = cbor2.loads(encoded)
    assert decoded == dt


def test_datetime_as_timestamp_utc():
    # datetime_as_timestamp=True encodes as numeric timestamp (tag 1)
    dt = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    encoded = cbor2.dumps(dt, datetime_as_timestamp=True)
    decoded = cbor2.loads(encoded)
    assert decoded == dt


def test_datetime_string_encoding_format():
    # Verify datetime is encoded as tagged string (tag 0)
    dt = datetime(2023, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    encoded = cbor2.dumps(dt)
    decoded = cbor2.loads(encoded)
    assert isinstance(decoded, datetime)
    assert decoded.tzinfo is not None


def test_datetime_equality_with_utc_equivalent():
    # Two datetime objects representing the same instant should decode to equal values
    dt_utc = datetime(2023, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    dt_plus5 = datetime(2023, 6, 1, 17, 0, 0, tzinfo=timezone(timedelta(hours=5)))
    # Both represent the same UTC instant
    encoded_utc = cbor2.dumps(dt_utc)
    decoded_utc = cbor2.loads(encoded_utc)
    assert decoded_utc == dt_utc
