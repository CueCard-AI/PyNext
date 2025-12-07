"""
Test Phase 7.5: Date/Time Helper Functions.

These tests verify that:
1. All date/time helpers return correct values
2. Values work with filter conditions
"""

import pytest
from datetime import datetime, date, time, timedelta, timezone

from pynext.db.relationships.helpers import (
    days_ago,
    hours_ago,
    minutes_ago,
    seconds_ago,
    weeks_ago,
    months_ago,
    years_ago,
    days_from_now,
    hours_from_now,
    minutes_from_now,
    today,
    yesterday,
    tomorrow,
    start_of_today,
    end_of_today,
    start_of_week,
    start_of_month,
    start_of_year,
    now,
    utc_now,
)
from pynext.db.relationships.conditions import eq, gte, lte


# =============================================================================
# Test days_ago
# =============================================================================

class TestDaysAgo:
    """Test days_ago helper."""
    
    def test_days_ago_1(self):
        """1 day ago."""
        result = days_ago(1)
        expected = datetime.now() - timedelta(days=1)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_days_ago_7(self):
        """7 days ago (week)."""
        result = days_ago(7)
        expected = datetime.now() - timedelta(days=7)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_days_ago_30(self):
        """30 days ago (month)."""
        result = days_ago(30)
        expected = datetime.now() - timedelta(days=30)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_days_ago_0(self):
        """0 days ago (now)."""
        result = days_ago(0)
        expected = datetime.now()
        assert abs((result - expected).total_seconds()) < 1
    
    def test_days_ago_365(self):
        """365 days ago (year)."""
        result = days_ago(365)
        expected = datetime.now() - timedelta(days=365)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_days_ago_returns_datetime(self):
        """Returns datetime object."""
        result = days_ago(7)
        assert isinstance(result, datetime)


# =============================================================================
# Test hours_ago
# =============================================================================

class TestHoursAgo:
    """Test hours_ago helper."""
    
    def test_hours_ago_1(self):
        """1 hour ago."""
        result = hours_ago(1)
        expected = datetime.now() - timedelta(hours=1)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_hours_ago_24(self):
        """24 hours ago (day)."""
        result = hours_ago(24)
        expected = datetime.now() - timedelta(hours=24)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_hours_ago_0(self):
        """0 hours ago (now)."""
        result = hours_ago(0)
        expected = datetime.now()
        assert abs((result - expected).total_seconds()) < 1
    
    def test_hours_ago_returns_datetime(self):
        """Returns datetime object."""
        result = hours_ago(12)
        assert isinstance(result, datetime)


# =============================================================================
# Test minutes_ago
# =============================================================================

class TestMinutesAgo:
    """Test minutes_ago helper."""
    
    def test_minutes_ago_1(self):
        """1 minute ago."""
        result = minutes_ago(1)
        expected = datetime.now() - timedelta(minutes=1)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_minutes_ago_60(self):
        """60 minutes ago (hour)."""
        result = minutes_ago(60)
        expected = datetime.now() - timedelta(minutes=60)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_minutes_ago_5(self):
        """5 minutes ago."""
        result = minutes_ago(5)
        expected = datetime.now() - timedelta(minutes=5)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_minutes_ago_returns_datetime(self):
        """Returns datetime object."""
        result = minutes_ago(30)
        assert isinstance(result, datetime)


# =============================================================================
# Test seconds_ago
# =============================================================================

class TestSecondsAgo:
    """Test seconds_ago helper."""
    
    def test_seconds_ago_1(self):
        """1 second ago."""
        result = seconds_ago(1)
        expected = datetime.now() - timedelta(seconds=1)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_seconds_ago_60(self):
        """60 seconds ago (minute)."""
        result = seconds_ago(60)
        expected = datetime.now() - timedelta(seconds=60)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_seconds_ago_30(self):
        """30 seconds ago."""
        result = seconds_ago(30)
        expected = datetime.now() - timedelta(seconds=30)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_seconds_ago_returns_datetime(self):
        """Returns datetime object."""
        result = seconds_ago(10)
        assert isinstance(result, datetime)


# =============================================================================
# Test weeks_ago
# =============================================================================

class TestWeeksAgo:
    """Test weeks_ago helper."""
    
    def test_weeks_ago_1(self):
        """1 week ago."""
        result = weeks_ago(1)
        expected = datetime.now() - timedelta(weeks=1)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_weeks_ago_4(self):
        """4 weeks ago (~month)."""
        result = weeks_ago(4)
        expected = datetime.now() - timedelta(weeks=4)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_weeks_ago_returns_datetime(self):
        """Returns datetime object."""
        result = weeks_ago(2)
        assert isinstance(result, datetime)


# =============================================================================
# Test months_ago
# =============================================================================

class TestMonthsAgo:
    """Test months_ago helper."""
    
    def test_months_ago_1(self):
        """1 month ago (~30 days)."""
        result = months_ago(1)
        expected = datetime.now() - timedelta(days=30)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_months_ago_3(self):
        """3 months ago (~90 days)."""
        result = months_ago(3)
        expected = datetime.now() - timedelta(days=90)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_months_ago_12(self):
        """12 months ago (~year)."""
        result = months_ago(12)
        expected = datetime.now() - timedelta(days=360)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_months_ago_returns_datetime(self):
        """Returns datetime object."""
        result = months_ago(6)
        assert isinstance(result, datetime)


# =============================================================================
# Test years_ago
# =============================================================================

class TestYearsAgo:
    """Test years_ago helper."""
    
    def test_years_ago_1(self):
        """1 year ago (~365 days)."""
        result = years_ago(1)
        expected = datetime.now() - timedelta(days=365)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_years_ago_5(self):
        """5 years ago."""
        result = years_ago(5)
        expected = datetime.now() - timedelta(days=365*5)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_years_ago_returns_datetime(self):
        """Returns datetime object."""
        result = years_ago(2)
        assert isinstance(result, datetime)


# =============================================================================
# Test Future Helpers
# =============================================================================

class TestFutureHelpers:
    """Test future date helpers."""
    
    def test_days_from_now_1(self):
        """1 day from now."""
        result = days_from_now(1)
        expected = datetime.now() + timedelta(days=1)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_days_from_now_7(self):
        """7 days from now."""
        result = days_from_now(7)
        expected = datetime.now() + timedelta(days=7)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_hours_from_now_1(self):
        """1 hour from now."""
        result = hours_from_now(1)
        expected = datetime.now() + timedelta(hours=1)
        assert abs((result - expected).total_seconds()) < 1
    
    def test_minutes_from_now_30(self):
        """30 minutes from now."""
        result = minutes_from_now(30)
        expected = datetime.now() + timedelta(minutes=30)
        assert abs((result - expected).total_seconds()) < 1


# =============================================================================
# Test Date Boundary Helpers
# =============================================================================

class TestDateBoundaryHelpers:
    """Test date boundary helpers."""
    
    def test_today_returns_date(self):
        """today returns date object."""
        result = today()
        assert isinstance(result, date)
        assert result == date.today()
    
    def test_yesterday_returns_date(self):
        """yesterday returns date object."""
        result = yesterday()
        assert isinstance(result, date)
        assert result == date.today() - timedelta(days=1)
    
    def test_tomorrow_returns_date(self):
        """tomorrow returns date object."""
        result = tomorrow()
        assert isinstance(result, date)
        assert result == date.today() + timedelta(days=1)
    
    def test_start_of_today_returns_datetime(self):
        """start_of_today returns datetime at midnight."""
        result = start_of_today()
        assert isinstance(result, datetime)
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.date() == date.today()
    
    def test_end_of_today_returns_datetime(self):
        """end_of_today returns datetime at end of day."""
        result = end_of_today()
        assert isinstance(result, datetime)
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
        assert result.date() == date.today()
    
    def test_start_of_week_returns_datetime(self):
        """start_of_week returns datetime for Monday."""
        result = start_of_week()
        assert isinstance(result, datetime)
        assert result.weekday() == 0  # Monday
        assert result.hour == 0
    
    def test_start_of_month_returns_datetime(self):
        """start_of_month returns datetime for 1st."""
        result = start_of_month()
        assert isinstance(result, datetime)
        assert result.day == 1
        assert result.hour == 0
    
    def test_start_of_year_returns_datetime(self):
        """start_of_year returns datetime for Jan 1."""
        result = start_of_year()
        assert isinstance(result, datetime)
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 0


# =============================================================================
# Test now and utc_now
# =============================================================================

class TestNowHelpers:
    """Test now helpers."""
    
    def test_now_returns_datetime(self):
        """now returns current datetime."""
        result = now()
        assert isinstance(result, datetime)
        expected = datetime.now()
        assert abs((result - expected).total_seconds()) < 1
    
    def test_utc_now_returns_datetime(self):
        """utc_now returns UTC datetime."""
        result = utc_now()
        assert isinstance(result, datetime)
        # Should have timezone info
        assert result.tzinfo is not None


# =============================================================================
# Test Helpers with Conditions
# =============================================================================

class TestHelpersWithConditions:
    """Test helpers used with conditions."""
    
    def test_days_ago_with_gte(self):
        """days_ago with gte condition."""
        cond = gte("created_at", days_ago(30))
        assert cond.field == "created_at"
        assert cond.operator == ">="
        assert isinstance(cond.value, datetime)
    
    def test_hours_ago_with_gte(self):
        """hours_ago with gte condition."""
        cond = gte("updated_at", hours_ago(24))
        assert isinstance(cond.value, datetime)
    
    def test_future_with_lte(self):
        """days_from_now with lte condition."""
        cond = lte("expires_at", days_from_now(7))
        assert cond.operator == "<="
        assert isinstance(cond.value, datetime)
    
    def test_today_with_eq(self):
        """today with eq condition."""
        cond = eq("date", today())
        assert isinstance(cond.value, date)
    
    def test_start_of_today_with_gte(self):
        """start_of_today with gte for today's records."""
        cond = gte("created_at", start_of_today())
        assert isinstance(cond.value, datetime)
        assert cond.value.hour == 0


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestHelperEdgeCases:
    """Test edge cases for helpers."""
    
    def test_large_values(self):
        """Helpers work with large values."""
        result = days_ago(1000)
        assert isinstance(result, datetime)
    
    def test_zero_values(self):
        """Helpers work with zero."""
        assert abs((days_ago(0) - datetime.now()).total_seconds()) < 1
        assert abs((hours_ago(0) - datetime.now()).total_seconds()) < 1
        assert abs((minutes_ago(0) - datetime.now()).total_seconds()) < 1
    
    def test_consistency(self):
        """Related helpers are consistent."""
        # 7 days == 1 week
        d7 = days_ago(7)
        w1 = weeks_ago(1)
        assert abs((d7 - w1).total_seconds()) < 1
        
        # 24 hours == 1 day
        h24 = hours_ago(24)
        d1 = days_ago(1)
        assert abs((h24 - d1).total_seconds()) < 1
        
        # 60 minutes == 1 hour
        m60 = minutes_ago(60)
        h1 = hours_ago(1)
        assert abs((m60 - h1).total_seconds()) < 1

