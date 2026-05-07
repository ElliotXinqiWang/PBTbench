"""Basic tests for dateutil."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "buggy"))

from datetime import date
from dateutil.relativedelta import relativedelta


def test_add_one_month_midmonth():
    """Adding 1 month to a mid-month date should not require clamping."""
    d = date(2024, 3, 15)
    assert d + relativedelta(months=1) == date(2024, 4, 15)


def test_add_months_cross_year():
    """Adding months that cross a year boundary."""
    d = date(2024, 11, 10)
    assert d + relativedelta(months=3) == date(2025, 2, 10)


def test_add_one_year():
    """Adding one year should preserve month and day for non-leap dates."""
    d = date(2023, 6, 20)
    assert d + relativedelta(years=1) == date(2024, 6, 20)


def test_add_years_and_months():
    """Combining years and months with a mid-month date."""
    d = date(2022, 5, 5)
    assert d + relativedelta(years=2, months=3) == date(2024, 8, 5)


def test_subtract_months():
    """Subtracting months from a mid-month date."""
    d = date(2024, 9, 14)
    assert d + relativedelta(months=-3) == date(2024, 6, 14)


def test_add_days():
    """Adding days via relativedelta."""
    d = date(2024, 1, 20)
    assert d + relativedelta(days=10) == date(2024, 1, 30)


def test_month_stays_correct_after_addition():
    """Resulting month and year should be correct after month arithmetic."""
    d = date(2024, 1, 10)
    result = d + relativedelta(months=5)
    assert result.year == 2024
    assert result.month == 6
    assert result.day == 10
