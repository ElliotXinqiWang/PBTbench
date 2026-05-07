"""Basic tests for pendulum."""
import datetime

import pendulum
import pytest


# ---------------------------------------------------------------------------
# DateTime creation and basic properties
# ---------------------------------------------------------------------------

def test_datetime_create_basic():
    dt = pendulum.datetime(2023, 6, 15, 10, 30, 0)
    assert dt.year == 2023
    assert dt.month == 6
    assert dt.day == 15
    assert dt.hour == 10
    assert dt.minute == 30
    assert dt.second == 0


def test_datetime_timezone_aware():
    dt = pendulum.datetime(2023, 6, 15, tz="UTC")
    assert dt.timezone_name == "UTC"
    assert dt.offset == 0


def test_datetime_isoformat():
    dt = pendulum.datetime(2023, 6, 15, 12, 0, 0)
    iso = dt.isoformat()
    assert "2023-06-15" in iso
    assert "12:00:00" in iso


# ---------------------------------------------------------------------------
# DateTime.add() — tests NOT crossing year boundaries
# ---------------------------------------------------------------------------

def test_add_days_simple():
    dt = pendulum.datetime(2023, 6, 1)
    result = dt.add(days=10)
    assert result.year == 2023
    assert result.month == 6
    assert result.day == 11


def test_add_months_within_year():
    # Adding months within the same year (no year boundary crossing)
    dt = pendulum.datetime(2023, 3, 15)
    result = dt.add(months=3)
    assert result.year == 2023
    assert result.month == 6
    assert result.day == 15


def test_add_months_end_of_short_month():
    # Mar 31 + 1 month = Apr 30 (30-day month clamping)
    dt = pendulum.datetime(2023, 3, 31)
    result = dt.add(months=1)
    assert result.year == 2023
    assert result.month == 4
    assert result.day == 30  # April has 30 days


def test_add_months_stays_same_year():
    # May + 6 months = November (no year boundary)
    dt = pendulum.datetime(2023, 5, 15)
    result = dt.add(months=6)
    assert result.year == 2023
    assert result.month == 11
    assert result.day == 15


def test_add_hours_and_minutes():
    dt = pendulum.datetime(2023, 6, 15, 10, 0, 0)
    result = dt.add(hours=2, minutes=30)
    assert result.hour == 12
    assert result.minute == 30


def test_add_years():
    dt = pendulum.datetime(2020, 6, 15)
    result = dt.add(years=3)
    assert result.year == 2023
    assert result.month == 6
    assert result.day == 15


# ---------------------------------------------------------------------------
# DateTime.subtract() — tests NOT crossing year boundaries
# ---------------------------------------------------------------------------

def test_subtract_days():
    dt = pendulum.datetime(2023, 6, 15)
    result = dt.subtract(days=5)
    assert result.year == 2023
    assert result.month == 6
    assert result.day == 10


def test_subtract_months_within_year():
    dt = pendulum.datetime(2023, 9, 15)
    result = dt.subtract(months=3)
    assert result.year == 2023
    assert result.month == 6
    assert result.day == 15


def test_subtract_months_end_of_month():
    # Aug 31 - 1 month = Jul 31 (July has 31 days, no clamping needed)
    dt = pendulum.datetime(2023, 8, 31)
    result = dt.subtract(months=1)
    assert result.year == 2023
    assert result.month == 7
    assert result.day == 31


# ---------------------------------------------------------------------------
# day_of_year — non-leap year
# ---------------------------------------------------------------------------

def test_day_of_year_jan_1():
    # January 1 is always day 1
    dt = pendulum.date(2023, 1, 1)
    assert dt.day_of_year == 1


def test_day_of_year_dec_31_non_leap():
    # December 31 in a non-leap year is day 365
    dt = pendulum.date(2023, 12, 31)
    assert dt.day_of_year == 365


def test_day_of_year_feb_28_non_leap():
    # February 28 in a non-leap year is day 59
    dt = pendulum.date(2023, 2, 28)
    assert dt.day_of_year == 59


def test_day_of_year_mar_1_non_leap():
    # March 1 in a non-leap year is day 60
    dt = pendulum.date(2023, 3, 1)
    assert dt.day_of_year == 60


def test_day_of_year_jan_15_leap_year():
    # January 15 in a leap year is still day 15
    dt = pendulum.date(2024, 1, 15)
    assert dt.day_of_year == 15


def test_day_of_year_feb_15_leap_year():
    # February 15 in a leap year is day 46
    dt = pendulum.date(2024, 2, 15)
    assert dt.day_of_year == 46


def test_day_of_year_feb_29_leap_year():
    # February 29 is day 60 in a leap year
    dt = pendulum.date(2024, 2, 29)
    assert dt.day_of_year == 60


# ---------------------------------------------------------------------------
# Interval and diff — basic cases
# ---------------------------------------------------------------------------

def test_diff_in_days():
    d1 = pendulum.datetime(2023, 1, 1)
    d2 = pendulum.datetime(2023, 1, 11)
    iv = d1.diff(d2)
    assert iv.in_days() == 10


def test_diff_in_months_same_day():
    # Exactly 3 months apart, same day of month
    d1 = pendulum.datetime(2023, 3, 15)
    d2 = pendulum.datetime(2023, 6, 15)
    iv = d1.diff(d2)
    assert iv.in_months() == 3


def test_diff_in_years():
    d1 = pendulum.datetime(2020, 6, 15)
    d2 = pendulum.datetime(2023, 6, 15)
    iv = d1.diff(d2)
    assert iv.in_years() == 3
