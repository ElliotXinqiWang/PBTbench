"""Basic tests for tomlkit."""
import pytest
import tomlkit
from datetime import datetime, date, time, timezone, timedelta


class TestBasicParsing:
    """Test basic TOML parsing."""

    def test_parse_integer(self):
        doc = tomlkit.loads("x = 42\n")
        assert doc["x"] == 42

    def test_parse_float(self):
        doc = tomlkit.loads("x = 3.14\n")
        assert abs(doc["x"] - 3.14) < 1e-10

    def test_parse_string(self):
        doc = tomlkit.loads('x = "hello world"\n')
        assert doc["x"] == "hello world"

    def test_parse_boolean(self):
        doc = tomlkit.loads("x = true\ny = false\n")
        assert doc["x"] is True
        assert doc["y"] is False

    def test_parse_array(self):
        doc = tomlkit.loads("x = [1, 2, 3]\n")
        assert list(doc["x"]) == [1, 2, 3]

    def test_parse_table(self):
        doc = tomlkit.loads("[table]\nkey = \"value\"\n")
        assert doc["table"]["key"] == "value"

    def test_parse_nested_table(self):
        doc = tomlkit.loads("[a]\n[a.b]\nkey = 1\n")
        assert doc["a"]["b"]["key"] == 1


class TestStringTypes:
    """Test different string types."""

    def test_basic_string(self):
        doc = tomlkit.loads('x = "hello"\n')
        assert doc["x"] == "hello"

    def test_literal_string(self):
        doc = tomlkit.loads("x = 'hello'\n")
        assert doc["x"] == "hello"

    def test_multiline_basic_string(self):
        s = 'x = """hello\nworld"""\n'
        doc = tomlkit.loads(s)
        assert doc["x"] == "hello\nworld"

    def test_multiline_literal_string(self):
        s = "x = '''hello\nworld'''\n"
        doc = tomlkit.loads(s)
        assert doc["x"] == "hello\nworld"

    def test_basic_string_with_escapes(self):
        doc = tomlkit.loads('x = "hello\\tworld"\n')
        assert doc["x"] == "hello\tworld"

    def test_multiline_basic_line_continuation(self):
        s = 'x = """\\\n  hello"""\n'
        doc = tomlkit.loads(s)
        assert doc["x"] == "hello"

    def test_multiline_literal_two_quotes(self):
        """Two consecutive quotes inside MLL are fine."""
        s = "x = '''has '' inside'''\n"
        doc = tomlkit.loads(s)
        assert doc["x"] == "has '' inside"


class TestDatetime:
    """Test datetime parsing - only with full-precision and whole-hour timezones."""

    def test_datetime_utc(self):
        doc = tomlkit.loads("dt = 2024-01-15T10:30:00Z\n")
        dt = doc["dt"]
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 0

    def test_datetime_whole_hour_offset(self):
        """Only test whole-hour timezone offsets."""
        doc = tomlkit.loads("dt = 2024-06-15T14:00:00+05:00\n")
        dt = doc["dt"]
        assert dt.utcoffset() == timedelta(hours=5)

    def test_datetime_negative_offset(self):
        doc = tomlkit.loads("dt = 2024-06-15T14:00:00-08:00\n")
        dt = doc["dt"]
        assert dt.utcoffset() == timedelta(hours=-8)

    def test_datetime_full_microsecond(self):
        """Test Datetime full microsecond."""
        doc = tomlkit.loads("dt = 2024-01-15T10:30:00.123456Z\n")
        dt = doc["dt"]
        assert dt.microsecond == 123456

    def test_local_datetime(self):
        doc = tomlkit.loads("dt = 2024-01-15T10:30:00\n")
        dt = doc["dt"]
        assert dt.tzinfo is None

    def test_date(self):
        doc = tomlkit.loads("d = 2024-01-15\n")
        d = doc["d"]
        assert isinstance(d, date)
        assert d.year == 2024

    def test_time(self):
        doc = tomlkit.loads("t = 10:30:00\n")
        t = doc["t"]
        assert isinstance(t, time)
        assert t.hour == 10


class TestNumbers:
    """Test number parsing."""

    def test_integer(self):
        doc = tomlkit.loads("x = 1_000\n")
        assert doc["x"] == 1000

    def test_hex(self):
        doc = tomlkit.loads("x = 0xDEADBEEF\n")
        assert doc["x"] == 0xDEADBEEF

    def test_octal(self):
        doc = tomlkit.loads("x = 0o755\n")
        assert doc["x"] == 0o755

    def test_binary(self):
        doc = tomlkit.loads("x = 0b11010110\n")
        assert doc["x"] == 0b11010110

    def test_float_inf(self):
        doc = tomlkit.loads("x = inf\n")
        assert doc["x"] == float("inf")

    def test_float_nan(self):
        import math
        doc = tomlkit.loads("x = nan\n")
        assert math.isnan(doc["x"])


class TestRoundtrip:
    """Test style-preserving roundtrip - only safe cases."""

    def test_roundtrip_basic(self):
        s = 'x = 1\ny = "hello"\n'
        assert tomlkit.dumps(tomlkit.loads(s)) == s

    def test_roundtrip_table(self):
        s = "[server]\nhost = \"localhost\"\nport = 8080\n"
        assert tomlkit.dumps(tomlkit.loads(s)) == s

    def test_roundtrip_array(self):
        s = "x = [1, 2, 3]\n"
        assert tomlkit.dumps(tomlkit.loads(s)) == s

    def test_roundtrip_nested_table(self):
        s = "[a]\n[a.b]\nkey = 1\n"
        assert tomlkit.dumps(tomlkit.loads(s)) == s

    def test_roundtrip_multiline_string(self):
        s = 'x = """hello\nworld"""\n'
        assert tomlkit.dumps(tomlkit.loads(s)) == s

    def test_roundtrip_comment_preserved(self):
        s = "# This is a comment\nx = 1\n"
        assert tomlkit.dumps(tomlkit.loads(s)) == s

    def test_roundtrip_datetime_utc(self):
        s = "dt = 2024-01-15T10:30:00Z\n"
        assert tomlkit.dumps(tomlkit.loads(s)) == s

    def test_roundtrip_aot(self):
        s = "[[servers]]\nname = \"alpha\"\n\n[[servers]]\nname = \"beta\"\n"
        assert tomlkit.dumps(tomlkit.loads(s)) == s
