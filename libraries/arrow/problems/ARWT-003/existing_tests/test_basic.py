"""Basic tests for arrow."""
import arrow
import pytest
from datetime import datetime, timezone


class TestArrowBasics:
    """Basic Arrow construction and properties."""

    def test_arrow_construction(self):
        a = arrow.Arrow(2023, 6, 15, 10, 30, 45)
        assert a.year == 2023
        assert a.month == 6
        assert a.day == 15
        assert a.hour == 10
        assert a.minute == 30
        assert a.second == 45

    def test_arrow_utcnow_type(self):
        a = arrow.utcnow()
        assert isinstance(a, arrow.Arrow)

    def test_arrow_from_datetime(self):
        dt = datetime(2023, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
        a = arrow.Arrow.fromdatetime(dt)
        assert a.year == 2023
        assert a.month == 3
        assert a.day == 20

    def test_arrow_shift_days(self):
        a = arrow.Arrow(2023, 1, 10)
        b = a.shift(days=5)
        assert b.day == 15
        assert b.month == 1
        assert b.year == 2023

    def test_arrow_shift_months(self):
        a = arrow.Arrow(2023, 1, 15)
        b = a.shift(months=2)
        assert b.month == 3
        assert b.year == 2023

    def test_arrow_shift_years(self):
        a = arrow.Arrow(2020, 6, 15)
        b = a.shift(years=3)
        assert b.year == 2023
        assert b.month == 6

    def test_arrow_shift_negative(self):
        a = arrow.Arrow(2023, 3, 1)
        b = a.shift(days=-1)
        assert b.day == 28
        assert b.month == 2

    def test_arrow_comparison(self):
        a = arrow.Arrow(2023, 1, 1)
        b = arrow.Arrow(2023, 6, 15)
        assert a < b
        assert b > a
        assert a != b

    def test_arrow_equality(self):
        a = arrow.Arrow(2023, 6, 15, 10, 30, 45)
        b = arrow.Arrow(2023, 6, 15, 10, 30, 45)
        assert a == b

    def test_arrow_timestamp(self):
        a = arrow.Arrow(2023, 1, 1, 0, 0, 0)
        ts = a.int_timestamp
        assert isinstance(ts, int)
        assert ts > 0

    def test_arrow_format_basic(self):
        a = arrow.Arrow(2023, 6, 15, 14, 30, 45)
        assert a.format("YYYY") == "2023"
        assert a.format("MM") == "06"
        assert a.format("DD") == "15"
        assert a.format("HH") == "14"
        assert a.format("mm") == "30"
        assert a.format("ss") == "45"

    def test_arrow_format_combined(self):
        a = arrow.Arrow(2023, 6, 15)
        result = a.format("YYYY-MM-DD")
        assert result == "2023-06-15"

    def test_arrow_isoformat(self):
        a = arrow.Arrow(2023, 6, 15, 10, 30, 0)
        iso = a.isoformat()
        assert "2023-06-15" in iso
        assert "10:30:00" in iso


class TestArrowSpanBasic:
    """Basic span() tests."""

    def test_span_day_floor(self):
        a = arrow.Arrow(2023, 6, 15, 14, 30)
        floor, ceil = a.span("day")
        # Only check the floor (start of span)
        assert floor.year == 2023
        assert floor.month == 6
        assert floor.day == 15
        assert floor.hour == 0
        assert floor.minute == 0
        assert floor.second == 0

    def test_span_hour_floor(self):
        a = arrow.Arrow(2023, 6, 15, 14, 30)
        floor, ceil = a.span("hour")
        assert floor.hour == 14
        assert floor.minute == 0
        assert floor.second == 0

    def test_span_month_floor(self):
        a = arrow.Arrow(2023, 6, 15)
        floor, ceil = a.span("month")
        assert floor.month == 6
        assert floor.day == 1
        assert floor.hour == 0

    def test_span_year_floor(self):
        a = arrow.Arrow(2023, 6, 15)
        floor, ceil = a.span("year")
        assert floor.year == 2023
        assert floor.month == 1
        assert floor.day == 1

    def test_span_returns_tuple(self):
        a = arrow.Arrow(2023, 6, 15)
        result = a.span("day")
        assert isinstance(result, tuple)
        assert len(result) == 2
        floor, ceil = result
        assert isinstance(floor, arrow.Arrow)
        assert isinstance(ceil, arrow.Arrow)
        # floor should always be <= ceil
        assert floor <= ceil


class TestArrowIsBetweenBasic:
    """Basic is_between() tests that don't test boundary equality."""

    def test_is_between_clearly_inside(self):
        start = arrow.Arrow(2023, 1, 1)
        end = arrow.Arrow(2023, 12, 31)
        mid = arrow.Arrow(2023, 6, 15)
        assert mid.is_between(start, end, "()")
        assert mid.is_between(start, end, "(]")
        assert mid.is_between(start, end, "[)")
        assert mid.is_between(start, end, "[]")

    def test_is_between_clearly_outside(self):
        start = arrow.Arrow(2023, 1, 1)
        end = arrow.Arrow(2023, 12, 31)
        before = arrow.Arrow(2022, 6, 15)
        after = arrow.Arrow(2024, 6, 15)
        assert not before.is_between(start, end, "[]")
        assert not after.is_between(start, end, "[]")

    def test_is_between_start_inclusive(self):
        start = arrow.Arrow(2023, 1, 1)
        end = arrow.Arrow(2023, 12, 31)
        # With '[', start IS included
        assert start.is_between(start, end, "[]")
        assert start.is_between(start, end, "[)")

    def test_is_between_start_exclusive(self):
        start = arrow.Arrow(2023, 1, 1)
        end = arrow.Arrow(2023, 12, 31)
        # With '(', start is NOT included
        assert not start.is_between(start, end, "()")
        assert not start.is_between(start, end, "(]")


class TestArrowHumanizeBasic:
    """Basic humanize tests."""

    def test_humanize_seconds_ago(self):
        a = arrow.Arrow(2023, 6, 15, 12, 0, 30)
        ref = arrow.Arrow(2023, 6, 15, 12, 1, 0)
        result = a.humanize(ref)
        assert "ago" in result or "second" in result

    def test_humanize_in_hours(self):
        a = arrow.Arrow(2023, 6, 15, 12, 0, 0)
        ref = arrow.Arrow(2023, 6, 15, 10, 0, 0)
        result = a.humanize(ref)
        assert "2 hours" in result

    def test_humanize_granularity_single_hour(self):
        a = arrow.Arrow(2023, 6, 15, 14, 0, 0)
        ref = arrow.Arrow(2023, 6, 15, 12, 0, 0)
        result = a.humanize(ref, granularity="hour")
        assert "2 hours" in result

    def test_humanize_granularity_single_minute(self):
        a = arrow.Arrow(2023, 6, 15, 12, 30, 0)
        ref = arrow.Arrow(2023, 6, 15, 12, 0, 0)
        result = a.humanize(ref, granularity="minute")
        assert "30 minutes" in result
