"""Basic tests for yaml."""
import datetime
import pytest

try:
    import yaml
except ImportError:
    pytest.skip("yaml not available", allow_module_level=True)


# -- Integer roundtrips -------------------------------------------------------

def test_integer_roundtrip():
    assert yaml.safe_load(yaml.safe_dump(42)) == 42


def test_negative_integer_roundtrip():
    """Negative integers are NOT floats; -8 as YAML text is ''-8'' (integer path)."""
    assert yaml.safe_load(yaml.safe_dump(-100)) == -100


def test_zero_roundtrip():
    assert yaml.safe_load(yaml.safe_dump(0)) == 0


def test_large_integer_roundtrip():
    assert yaml.safe_load(yaml.safe_dump(2**31 - 1)) == 2**31 - 1


def test_hex_parsing():
    """YAML 1.1 hex integer literal."""
    assert yaml.safe_load('0xFF') == 255
    assert yaml.safe_load('0x10') == 16


def test_binary_parsing():
    """YAML 1.1 binary integer literal."""
    assert yaml.safe_load('0b1010') == 10


def test_octal_parsing():
    """YAML 1.1 octal integer (leading 0 = octal)."""
    assert yaml.safe_load('010') == 8


# -- Float roundtrips (positive only, no scientific without decimal) ----------

def test_positive_float_roundtrip():
    for f in [1.5, 3.14, 100.0, 0.001, 0.5]:
        result = yaml.safe_load(yaml.safe_dump(f))
        assert abs(result - f) < 1e-12, f"Float {f!r} roundtrip failed"


def test_positive_float_scientific_roundtrip():
    """Positive scientific-notation floats with decimal in repr."""
    for f in [1.23e15, 9.9e-20, 1.1e100, 2.5e-4]:
        result = yaml.safe_load(yaml.safe_dump(f))
        assert result == f, f"Float {f!r} roundtrip failed: got {result!r}"


def test_float_special_values():
    """Positive inf roundtrips correctly; NaN is a special case."""
    import math
    pos_inf = float('inf')
    assert yaml.safe_load(yaml.safe_dump(pos_inf)) == pos_inf
    result_nan = yaml.safe_load(yaml.safe_dump(float('nan')))
    assert math.isnan(result_nan)


# -- String roundtrips --------------------------------------------------------

def test_regular_string_roundtrip():
    for s in ["hello", "world", "foo bar", "test123", "YAML", "Python"]:
        result = yaml.safe_load(yaml.safe_dump(s))
        assert result == s


def test_empty_string_roundtrip():
    result = yaml.safe_load(yaml.safe_dump(""))
    assert result == ""


# -- Bool / None roundtrips ---------------------------------------------------

def test_bool_roundtrip():
    assert yaml.safe_load(yaml.safe_dump(True)) is True
    assert yaml.safe_load(yaml.safe_dump(False)) is False


def test_none_roundtrip():
    assert yaml.safe_load(yaml.safe_dump(None)) is None


# -- Collection roundtrips (no set, no sexagesimal) ---------------------------

def test_list_roundtrip():
    data = [1, 2, 3, "hello", True, None]
    assert yaml.safe_load(yaml.safe_dump(data)) == data


def test_dict_roundtrip():
    data = {"key": "value", "num": 42, "flag": True}
    assert yaml.safe_load(yaml.safe_dump(data)) == data


def test_nested_dict_roundtrip():
    data = {"items": [1, 2, 3], "name": "test", "score": 3.14}
    assert yaml.safe_load(yaml.safe_dump(data)) == data


# -- Datetime roundtrips (no date objects, no fractional-hour timezones) ------

def test_naive_datetime_roundtrip():
    """Naive datetime (no timezone) should roundtrip correctly."""
    dt = datetime.datetime(2024, 3, 15, 8, 45, 30)
    result = yaml.safe_load(yaml.safe_dump(dt))
    assert result == dt


def test_datetime_with_microseconds():
    """Datetime with microseconds should roundtrip without loss."""
    dt = datetime.datetime(2024, 6, 15, 12, 30, 45, 123456)
    result = yaml.safe_load(yaml.safe_dump(dt))
    assert result == dt


def test_utc_datetime_roundtrip():
    """UTC-aware datetime should roundtrip correctly."""
    dt = datetime.datetime(2024, 6, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
    result = yaml.safe_load(yaml.safe_dump(dt))
    assert result == dt


def test_integer_hour_tz_datetime_roundtrip():
    """Integer-hour timezone offsets should roundtrip correctly."""
    for offset_h in [-8, -5, 1, 5, 9]:
        tz = datetime.timezone(datetime.timedelta(hours=offset_h))
        dt = datetime.datetime(2024, 1, 1, 10, 30, 0, tzinfo=tz)
        result = yaml.safe_load(yaml.safe_dump(dt))
        assert result == dt
