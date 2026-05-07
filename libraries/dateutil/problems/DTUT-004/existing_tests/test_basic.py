"""Basic tests for dateutil."""
import datetime
import pytest
from dateutil.parser import parse


def test_parse_full_iso_date():
    """Parse a full ISO date string."""
    result = parse("2024-03-15")
    assert result.year == 2024
    assert result.month == 3
    assert result.day == 15


def test_parse_datetime_with_time():
    """Parse datetime with hours and minutes."""
    result = parse("2024-03-15 10:30")
    assert result.year == 2024
    assert result.hour == 10
    assert result.minute == 30


def test_parse_us_date_format():
    """Parse US-style date format."""
    result = parse("March 15, 2024")
    assert result.month == 3
    assert result.day == 15
    assert result.year == 2024


def test_parse_default_date_no_overflow():
    """Parse month+year where default day is within the target month (no clamping)."""
    default = datetime.datetime(2024, 1, 15)  # day=15, won't overflow
    result = parse("February 2024", default=default)
    assert result.month == 2
    assert result.year == 2024
    assert result.day == 15  # default day, no clamping needed


def test_parse_default_date_february_15():
    """Parse month+year with default day=15 (safe for all months)."""
    default = datetime.datetime(2024, 1, 15)
    result = parse("April 2024", default=default)
    assert result.day == 15  # 15 ≤ 30 days in April, no clamping


def test_parse_noon_hour():
    """Parse 12 AM and 12 PM: not touching the 12-hour edge cases."""
    # Only test unambiguous cases (non-12-hour noon/midnight edge)
    r1 = parse("1:00 PM")
    assert r1.hour == 13
    r2 = parse("11:00 AM")
    assert r2.hour == 11
    r3 = parse("1:00 AM")
    assert r3.hour == 1


def test_parse_seconds_no_fraction():
    """Parse integer seconds (no fractional part)."""
    result = parse("12:30:45")
    assert result.second == 45
    assert result.microsecond == 0


def test_parse_4digit_year_yearfirst():
    """4-digit year > 31: yearfirst is irrelevant (year auto-detected)."""
    result = parse("2024/03/15")
    assert result.year == 2024
    assert result.month == 3
    assert result.day == 15


def test_parse_weekday_with_date():
    """Parse date with weekday name."""
    result = parse("Monday, March 15, 2021")
    assert result.weekday() == 0  # Monday
    assert result.month == 3


def test_parse_timezone_offset():
    """Parse datetime with numeric timezone offset."""
    result = parse("2024-03-15 10:30:00+05:30")
    assert result.year == 2024
    assert result.utcoffset() is not None


def test_parse_iso_with_T_separator():
    """Parse ISO 8601 format with T separator."""
    result = parse("2024-03-15T14:30:00")
    assert result.hour == 14
    assert result.minute == 30


def test_parse_short_month_name():
    """Parse abbreviated month name."""
    result = parse("15 Mar 2024")
    assert result.month == 3
    assert result.day == 15


def test_parse_small_microseconds():
    """Parse time without fractional seconds."""
    result = parse("12:00:00")
    assert result.microsecond == 0  # no fractional part at all
