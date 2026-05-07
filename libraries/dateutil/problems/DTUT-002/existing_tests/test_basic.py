"""Basic tests for dateutil."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "buggy"))

from datetime import datetime
from dateutil.rrule import rrule, YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MO, TU, WE, TH, FR


def test_daily_count():
    """Basic DAILY rrule with count."""
    dates = list(rrule(DAILY, count=5, dtstart=datetime(2024, 3, 1)))
    assert len(dates) == 5
    assert dates[0] == datetime(2024, 3, 1)
    assert dates[4] == datetime(2024, 3, 5)


def test_weekly_count():
    """Basic WEEKLY rrule with count."""
    dates = list(rrule(WEEKLY, count=4, dtstart=datetime(2024, 1, 1)))
    assert len(dates) == 4
    assert dates[1] == datetime(2024, 1, 8)
    assert dates[3] == datetime(2024, 1, 22)


def test_monthly_same_year():
    """MONTHLY rrule that stays within the same year (no year overflow)."""
    # Jan to Jun, interval=1 — no month=12 crossing
    dates = list(rrule(MONTHLY, count=6, dtstart=datetime(2024, 1, 15)))
    assert len(dates) == 6
    assert dates[0] == datetime(2024, 1, 15)
    assert dates[5] == datetime(2024, 6, 15)


def test_monthly_interval_2_no_december():
    """MONTHLY with interval=2 starting from Jan — lands on odd months, skips Dec."""
    # Jan, Mar, May, Jul, Sep, Nov — never hits December
    dates = list(rrule(MONTHLY, count=6, dtstart=datetime(2024, 1, 10), interval=2))
    months = [d.month for d in dates]
    assert months == [1, 3, 5, 7, 9, 11]


def test_monthly_interval_3():
    """MONTHLY with interval=3 starting from Feb — Feb, May, Aug, Nov."""
    dates = list(rrule(MONTHLY, count=4, dtstart=datetime(2024, 2, 15), interval=3))
    months = [d.month for d in dates]
    assert months == [2, 5, 8, 11]


def test_monthly_forward_cross_year():
    """Test Monthly forward cross year."""
    dates = list(rrule(MONTHLY, count=3, dtstart=datetime(2024, 11, 10), interval=2))
    assert dates[1] == datetime(2025, 1, 10)
    assert dates[2] == datetime(2025, 3, 10)


def test_yearly_basic():
    """Basic YEARLY rrule."""
    dates = list(rrule(YEARLY, count=3, dtstart=datetime(2024, 6, 15)))
    assert dates[0] == datetime(2024, 6, 15)
    assert dates[1] == datetime(2025, 6, 15)
    assert dates[2] == datetime(2026, 6, 15)


def test_daily_until():
    """DAILY rrule with until parameter."""
    dates = list(rrule(DAILY, dtstart=datetime(2024, 1, 1),
                       until=datetime(2024, 1, 7)))
    assert len(dates) == 7


def test_weekly_byweekday():
    """WEEKLY rrule with byweekday (Mon and Wed)."""
    dates = list(rrule(WEEKLY, count=6, dtstart=datetime(2024, 1, 1),
                       byweekday=(MO, WE)))
    for d in dates:
        assert d.weekday() in (0, 2)  # Monday=0, Wednesday=2


def test_hourly_interval_1():
    """HOURLY with interval=1 (gcd(1,24)=1, no __construct_byset filtering)."""
    dates = list(rrule(HOURLY, count=24, dtstart=datetime(2024, 1, 1, 0, 0),
                       interval=1, byhour=[0, 6, 12, 18]))
    hours = [d.hour for d in dates]
    assert all(h in (0, 6, 12, 18) for h in hours)


def test_hourly_interval_1_byhour():
    """HOURLY with interval=1 and byhour — gcd(1,24)=1 so all hours reachable."""
    dates = list(rrule(HOURLY, count=5, dtstart=datetime(2024, 1, 1, 0, 0),
                       interval=1, byhour=[3, 7, 15]))
    hours = [d.hour for d in dates]
    assert all(h in (3, 7, 15) for h in hours)


def test_bysetpos_first_last():
    """rrule with bysetpos=1 and bysetpos=-1 (small values, not 366)."""
    # First weekday of each month
    dates = list(rrule(MONTHLY, count=3, dtstart=datetime(2024, 1, 1),
                       byweekday=(MO, TU, WE, TH, FR), bysetpos=1))
    assert len(dates) == 3
    # All results should be weekdays
    for d in dates:
        assert d.weekday() < 5

    # Last weekday of each month
    dates = list(rrule(MONTHLY, count=3, dtstart=datetime(2024, 1, 1),
                       byweekday=(MO, TU, WE, TH, FR), bysetpos=-1))
    assert len(dates) == 3


def test_bysetpos_small_values():
    """bysetpos with small positive values (2, 3) — well within valid range."""
    dates = list(rrule(MONTHLY, count=3, dtstart=datetime(2024, 1, 1),
                       byweekday=(MO, TU, WE, TH, FR), bysetpos=2))
    assert len(dates) == 3


def test_rrule_str():
    """rrule string representation should be parseable."""
    r = rrule(DAILY, count=5, dtstart=datetime(2024, 1, 1))
    s = str(r)
    assert "FREQ=DAILY" in s
    assert "COUNT=5" in s
