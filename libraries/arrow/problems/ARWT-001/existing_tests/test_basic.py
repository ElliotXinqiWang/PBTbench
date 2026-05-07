"""Basic tests for arrow."""
import arrow
from datetime import datetime, timezone


# ── Creation and basic attributes ────────────────────────────────────────────

def test_creation_basic():
    a = arrow.Arrow(2020, 6, 15, 12, 30, 45)
    assert a.year == 2020
    assert a.month == 6
    assert a.day == 15
    assert a.hour == 12
    assert a.minute == 30
    assert a.second == 45


def test_utcnow_type():
    a = arrow.utcnow()
    assert isinstance(a, arrow.Arrow)


def test_now_type():
    a = arrow.now("UTC")
    assert isinstance(a, arrow.Arrow)


def test_arrow_get_from_datetime():
    dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
    a = arrow.Arrow.fromdatetime(dt)
    assert a.year == 2020
    assert a.month == 1
    assert a.day == 1


def test_shift_quarters_only():
    """shift(quarters=N) without explicit months should work correctly."""
    a = arrow.Arrow(2020, 1, 1)
    assert a.shift(quarters=1) == arrow.Arrow(2020, 4, 1)
    assert a.shift(quarters=2) == arrow.Arrow(2020, 7, 1)
    assert a.shift(quarters=4) == arrow.Arrow(2021, 1, 1)


def test_shift_days():
    a = arrow.Arrow(2020, 3, 1)
    assert a.shift(days=10) == arrow.Arrow(2020, 3, 11)
    assert a.shift(days=-1) == arrow.Arrow(2020, 2, 29)  # 2020 is leap year


def test_shift_months_only():
    """Test Shift months only."""
    a = arrow.Arrow(2020, 1, 1)
    assert a.shift(months=3) == arrow.Arrow(2020, 4, 1)
    assert a.shift(months=6) == arrow.Arrow(2020, 7, 1)
    assert a.shift(months=-1) == arrow.Arrow(2019, 12, 1)


def test_shift_years():
    a = arrow.Arrow(2020, 6, 15)
    assert a.shift(years=1) == arrow.Arrow(2021, 6, 15)
    assert a.shift(years=-1) == arrow.Arrow(2019, 6, 15)


def test_shift_weeks():
    a = arrow.Arrow(2020, 1, 6)  # Monday
    assert a.shift(weeks=1) == arrow.Arrow(2020, 1, 13)


# ── range: tests that end strictly BEFORE the endpoint ──────────────────────
# These tests use end that's not at the step boundary

def test_range_day_non_boundary():
    """Test Range day non boundary."""
    start = arrow.Arrow(2020, 1, 1, 0, 0)
    end = arrow.Arrow(2020, 1, 1, 12, 30)  # 12:30 - not on an hour boundary
    result = list(arrow.Arrow.range("hour", start, end))
    assert len(result) == 13  # 00:00 through 12:00 (12:00 < 12:30, so included)
    assert result[0] == start
    assert result[-1] == arrow.Arrow(2020, 1, 1, 12, 0)


def test_range_limit():
    """Range with limit — doesn't depend on endpoint comparison."""
    start = arrow.Arrow(2020, 1, 1)
    result = list(arrow.Arrow.range("day", start, limit=5))
    assert len(result) == 5
    assert result[0] == start
    assert result[-1] == arrow.Arrow(2020, 1, 5)


def test_range_month():
    start = arrow.Arrow(2020, 1, 1)
    end = arrow.Arrow(2020, 3, 1)
    result = list(arrow.Arrow.range("month", start, end))
    assert result[0] == start
    assert all(isinstance(r, arrow.Arrow) for r in result)


# ── span: tests using default [) bounds and non-quarter frames ───────────────

def test_span_day_floor():
    a = arrow.Arrow(2020, 6, 15, 14, 30)
    fl, cl = a.span("day")
    assert fl == arrow.Arrow(2020, 6, 15, 0, 0, 0)


def test_span_year():
    a = arrow.Arrow(2020, 6, 15)
    fl, cl = a.span("year")
    assert fl == arrow.Arrow(2020, 1, 1)


def test_span_month():
    a = arrow.Arrow(2020, 6, 15)
    fl, cl = a.span("month")
    assert fl == arrow.Arrow(2020, 6, 1)


def test_floor_day():
    a = arrow.Arrow(2020, 6, 15, 14, 30, 45)
    assert a.floor("day") == arrow.Arrow(2020, 6, 15, 0, 0, 0)


def test_floor_month():
    a = arrow.Arrow(2020, 6, 15)
    assert a.floor("month") == arrow.Arrow(2020, 6, 1)


def test_floor_year():
    a = arrow.Arrow(2020, 6, 15)
    assert a.floor("year") == arrow.Arrow(2020, 1, 1)


def test_floor_quarter_q1_only():
    """Test Floor quarter q1 only."""
    a1 = arrow.Arrow(2020, 1, 15)
    a2 = arrow.Arrow(2020, 2, 20)
    a3 = arrow.Arrow(2020, 3, 31)
    assert a1.floor("quarter") == arrow.Arrow(2020, 1, 1)
    assert a2.floor("quarter") == arrow.Arrow(2020, 1, 1)
    assert a3.floor("quarter") == arrow.Arrow(2020, 1, 1)


# ── timezone conversion ────────────────────────────────────────────────────

def test_to_timezone():
    utc = arrow.Arrow(2020, 6, 15, 12, 0, 0)
    eastern = utc.to("US/Eastern")
    assert eastern.hour == 8  # UTC-4 in summer


def test_to_utc_roundtrip():
    utc = arrow.Arrow(2020, 6, 15, 12, 0, 0)
    eastern = utc.to("US/Eastern")
    back = eastern.to("UTC")
    assert back == utc


# ── quarter property ──────────────────────────────────────────────────────

def test_quarter_property():
    assert arrow.Arrow(2020, 1, 1).quarter == 1
    assert arrow.Arrow(2020, 4, 1).quarter == 2
    assert arrow.Arrow(2020, 7, 1).quarter == 3
    assert arrow.Arrow(2020, 10, 1).quarter == 4


# ── comparison ────────────────────────────────────────────────────────────

def test_comparison():
    a = arrow.Arrow(2020, 1, 1)
    b = arrow.Arrow(2020, 1, 2)
    assert a < b
    assert b > a
    assert a <= a
    assert a == a


def test_datetime_property():
    a = arrow.Arrow(2020, 6, 15, 12, 30)
    dt = a.datetime
    assert dt.year == 2020
    assert dt.month == 6
