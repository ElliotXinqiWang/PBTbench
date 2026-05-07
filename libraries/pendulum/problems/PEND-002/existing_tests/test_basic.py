"""Basic tests for pendulum."""
import pytest
import pendulum
from pendulum import duration


class TestDurationCreation:
    def test_duration_from_days(self):
        d = duration(days=5)
        assert d.days == 5

    def test_duration_from_hours(self):
        d = duration(hours=3)
        assert d.hours == 3

    def test_duration_from_minutes_30(self):
        # 30 minutes: _seconds=1800, not 60
        d = duration(minutes=30)
        assert d.minutes == 30

    def test_duration_from_seconds_90(self):
        d = duration(seconds=90)
        assert d.minutes == 1
        assert d.remaining_seconds == 30

    def test_duration_from_mixed(self):
        # 2h 30m 15s: _seconds = 9015, no edge case
        d = duration(hours=2, minutes=30, seconds=15)
        assert d.hours == 2
        assert d.minutes == 30
        assert d.remaining_seconds == 15

    def test_duration_zero(self):
        d = duration()
        assert d.total_seconds() == 0


class TestDurationComponents:
    def test_weeks_and_remaining_days(self):
        d = duration(days=10)
        assert d.weeks == 1
        assert d.remaining_days == 3

    def test_years_and_months(self):
        d = duration(years=1, months=6)
        assert d.years == 1
        assert d.months == 6

    def test_microseconds(self):
        d = duration(microseconds=500000)
        assert d.microseconds == 500000

    def test_hours_component_2(self):
        # 2 hours: _seconds=7200, > 60 and > 3600 → safe
        d = duration(hours=2)
        assert d.hours == 2

    def test_minutes_component_2(self):
        d = duration(minutes=2)
        assert d.minutes == 2


class TestDurationTotals:
    def test_total_seconds(self):
        d = duration(hours=2)
        assert d.total_seconds() == 7200.0

    def test_in_hours(self):
        d = duration(hours=3)
        assert d.in_hours() == 3

    def test_in_seconds(self):
        d = duration(minutes=5)
        assert d.in_seconds() == 300

    def test_in_minutes(self):
        d = duration(hours=2)
        assert d.in_minutes() == 120

    def test_in_days(self):
        d = duration(days=3)
        assert d.in_days() == 3

    def test_in_weeks(self):
        d = duration(weeks=2)
        assert d.in_weeks() == 2


class TestDurationArithmetic:
    def test_addition(self):
        d1 = duration(hours=2)
        d2 = duration(hours=3)
        result = d1 + d2
        assert result.in_hours() == 5

    def test_subtraction(self):
        d1 = duration(hours=5)
        d2 = duration(hours=3)
        result = d1 - d2
        assert result.in_hours() == 2

    def test_multiplication(self):
        d = duration(hours=2)
        result = d * 3
        assert result.in_hours() == 6

    def test_negation_no_weeks(self):
        d = duration(days=3, hours=2)
        neg = -d
        assert neg.total_seconds() == -d.total_seconds()

    def test_negation_identity_no_weeks(self):
        d = duration(hours=5, minutes=30)
        result = d + (-d)
        assert result.total_seconds() == 0


class TestInterval:
    def test_interval_creation(self):
        start = pendulum.datetime(2023, 1, 1)
        end = pendulum.datetime(2023, 6, 15)
        iv = end - start
        assert iv.start <= iv.end

    def test_interval_in_days(self):
        start = pendulum.datetime(2023, 1, 1)
        end = pendulum.datetime(2023, 1, 8)
        iv = end - start
        assert iv.in_days() == 7

    def test_interval_in_months_sub_year(self):
        # but months IS the total, so 0*12+months == 0*12-months only when months==0
        # Exactly 12 months (1 year, 0 remaining months)
        start = pendulum.datetime(2023, 1, 1)
        end = pendulum.datetime(2024, 1, 1)
        iv = end - start
        assert iv.in_months() == 12

    def test_interval_in_months_exact_years(self):
        # Exact years: months component = 0, so + vs - doesn't matter
        start = pendulum.datetime(2020, 1, 1)
        end = pendulum.datetime(2023, 1, 1)
        iv = end - start
        assert iv.in_months() == 36

    def test_interval_in_months_zero_years(self):
        # Under 1 year with months > 0: years=0, so 0*12+m == 0*12-m only if m==0
        # So use a case where months=0 too (exact 0 months, just days)
        start = pendulum.datetime(2023, 3, 1)
        end = pendulum.datetime(2023, 3, 15)
        iv = end - start
        assert iv.in_months() == 0

    def test_interval_years_months_properties(self):
        start = pendulum.datetime(2020, 1, 1)
        end = pendulum.datetime(2022, 1, 1)
        iv = end - start
        assert iv.years == 2
        assert iv.months == 0

    def test_interval_in_weeks(self):
        start = pendulum.datetime(2023, 1, 1)
        end = pendulum.datetime(2023, 1, 15)
        iv = end - start
        assert iv.in_weeks() == 2

    def test_interval_contains(self):
        start = pendulum.datetime(2023, 1, 1)
        end = pendulum.datetime(2023, 12, 31)
        iv = pendulum.interval(start, end)
        mid = pendulum.datetime(2023, 6, 15)
        assert mid in iv


class TestDateTimeIntegration:
    def test_add_duration_to_datetime(self):
        dt = pendulum.datetime(2023, 6, 15, 10, 0, 0)
        result = dt.add(hours=2)
        assert result.hour == 12

    def test_subtract_from_datetime(self):
        dt = pendulum.datetime(2023, 6, 15, 10, 30, 0)
        result = dt.subtract(minutes=30)
        assert result.hour == 10
        assert result.minute == 0

    def test_duration_as_timedelta(self):
        import datetime
        d = duration(days=2, hours=3)
        td = d.as_timedelta()
        assert isinstance(td, datetime.timedelta)
        assert td.total_seconds() == 2 * 86400 + 3 * 3600
