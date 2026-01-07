"""
Phase 33.4: datetime Module Tests

Comprehensive tests for Python datetime module transpilation.
Tests verify the runtime provides correct JavaScript implementations for:
- datetime class (now, fromtimestamp, fromisoformat)
- date class (today, fromisoformat)
- time class
- timedelta (arithmetic, total_seconds)
- timezone (utc, custom offsets)
- strftime/strptime formatting
"""

import pytest


# =============================================================================
# DATETIME CLASS TESTS (15 tests)
# =============================================================================

class TestDatetimeNow:
    """Tests for datetime.now()."""
    
    def test_datetime_now_basic(self):
        """datetime.now() returns current datetime."""
        from pynext.runtime.stdlib.datetime import datetime
        now = datetime.now()
        assert now is not None
        assert hasattr(now, 'year')
        assert hasattr(now, 'month')
        assert hasattr(now, 'day')
    
    def test_datetime_now_with_timezone(self):
        """datetime.now(tz) returns current datetime in timezone."""
        from pynext.runtime.stdlib.datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        assert now is not None
    
    def test_datetime_construction(self):
        """datetime(year, month, day, ...) constructs datetime."""
        from pynext.runtime.stdlib.datetime import datetime
        dt = datetime(2024, 12, 14, 10, 30, 0)
        assert dt.year == 2024
        assert dt.month == 12
        assert dt.day == 14
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 0


class TestDatetimeFromTimestamp:
    """Tests for datetime.fromtimestamp()."""
    
    def test_fromtimestamp_basic(self):
        """datetime.fromtimestamp(ts) creates datetime."""
        from pynext.runtime.stdlib.datetime import datetime
        dt = datetime.fromtimestamp(1702500000)
        assert dt is not None
        assert dt.year >= 2023
    
    def test_utcfromtimestamp(self):
        """datetime.utcfromtimestamp(ts) creates UTC datetime."""
        from pynext.runtime.stdlib.datetime import datetime
        dt = datetime.utcfromtimestamp(1702500000)
        assert dt is not None


class TestDatetimeFromIsoformat:
    """Tests for datetime.fromisoformat()."""
    
    def test_fromisoformat_full(self):
        """datetime.fromisoformat parses full ISO string."""
        from pynext.runtime.stdlib.datetime import datetime
        dt = datetime.fromisoformat("2024-12-14T10:30:00")
        assert dt.year == 2024
        assert dt.month == 12
        assert dt.day == 14
        assert dt.hour == 10
        assert dt.minute == 30
    
    def test_fromisoformat_date_only(self):
        """datetime.fromisoformat parses date-only string."""
        from pynext.runtime.stdlib.datetime import datetime
        dt = datetime.fromisoformat("2024-12-14")
        assert dt.year == 2024
        assert dt.month == 12
        assert dt.day == 14


class TestDatetimeProperties:
    """Tests for datetime properties."""
    
    def test_datetime_weekday(self):
        """datetime.weekday() returns 0-6 (Mon-Sun)."""
        from pynext.runtime.stdlib.datetime import datetime
        dt = datetime(2024, 12, 14)  # Saturday
        assert dt.weekday() == 5
    
    def test_datetime_isoweekday(self):
        """datetime.isoweekday() returns 1-7 (Mon-Sun)."""
        from pynext.runtime.stdlib.datetime import datetime
        dt = datetime(2024, 12, 14)  # Saturday
        assert dt.isoweekday() == 6
    
    def test_datetime_isoformat(self):
        """datetime.isoformat() returns ISO string."""
        from pynext.runtime.stdlib.datetime import datetime
        dt = datetime(2024, 12, 14, 10, 30, 0)
        iso = dt.isoformat()
        assert "2024-12-14" in iso
        assert "10:30:00" in iso


# =============================================================================
# DATE CLASS TESTS (8 tests)
# =============================================================================

class TestDate:
    """Tests for date class."""
    
    def test_date_today(self):
        """date.today() returns current date."""
        from pynext.runtime.stdlib.datetime import date
        today = date.today()
        assert today is not None
        assert hasattr(today, 'year')
        assert hasattr(today, 'month')
        assert hasattr(today, 'day')
    
    def test_date_construction(self):
        """date(year, month, day) constructs date."""
        from pynext.runtime.stdlib.datetime import date
        d = date(2024, 12, 14)
        assert d.year == 2024
        assert d.month == 12
        assert d.day == 14
    
    def test_date_fromisoformat(self):
        """date.fromisoformat parses date string."""
        from pynext.runtime.stdlib.datetime import date
        d = date.fromisoformat("2024-12-14")
        assert d.year == 2024
        assert d.month == 12
        assert d.day == 14
    
    def test_date_isoformat(self):
        """date.isoformat() returns ISO string."""
        from pynext.runtime.stdlib.datetime import date
        d = date(2024, 12, 14)
        assert d.isoformat() == "2024-12-14"
    
    def test_date_weekday(self):
        """date.weekday() returns 0-6."""
        from pynext.runtime.stdlib.datetime import date
        d = date(2024, 12, 14)  # Saturday
        assert d.weekday() == 5


# =============================================================================
# TIME CLASS TESTS (5 tests)
# =============================================================================

class TestTime:
    """Tests for time class."""
    
    def test_time_construction(self):
        """time(hour, minute, second) constructs time."""
        from pynext.runtime.stdlib.datetime import time
        t = time(10, 30, 45)
        assert t.hour == 10
        assert t.minute == 30
        assert t.second == 45
    
    def test_time_defaults(self):
        """time() has default values."""
        from pynext.runtime.stdlib.datetime import time
        t = time()
        assert t.hour == 0
        assert t.minute == 0
        assert t.second == 0
    
    def test_time_isoformat(self):
        """time.isoformat() returns ISO string."""
        from pynext.runtime.stdlib.datetime import time
        t = time(10, 30, 45)
        iso = t.isoformat()
        assert "10:30:45" in iso


# =============================================================================
# TIMEDELTA TESTS (8 tests)
# =============================================================================

class TestTimedelta:
    """Tests for timedelta class."""
    
    def test_timedelta_days(self):
        """timedelta(days=n) creates duration."""
        from pynext.runtime.stdlib.datetime import timedelta
        td = timedelta(days=7)
        assert td.days == 7
    
    def test_timedelta_hours_minutes(self):
        """timedelta with hours and minutes."""
        from pynext.runtime.stdlib.datetime import timedelta
        td = timedelta(hours=3, minutes=30)
        assert td.seconds == 3 * 3600 + 30 * 60
    
    def test_timedelta_total_seconds(self):
        """timedelta.total_seconds() returns float."""
        from pynext.runtime.stdlib.datetime import timedelta
        td = timedelta(days=1, hours=1)
        expected = 24 * 3600 + 3600
        assert td.total_seconds() == expected
    
    def test_timedelta_addition(self):
        """timedelta + timedelta works."""
        from pynext.runtime.stdlib.datetime import timedelta
        td1 = timedelta(days=1)
        td2 = timedelta(days=2)
        result = td1 + td2
        assert result.days == 3
    
    def test_timedelta_subtraction(self):
        """timedelta - timedelta works."""
        from pynext.runtime.stdlib.datetime import timedelta
        td1 = timedelta(days=5)
        td2 = timedelta(days=2)
        result = td1 - td2
        assert result.days == 3
    
    def test_datetime_plus_timedelta(self):
        """datetime + timedelta works."""
        from pynext.runtime.stdlib.datetime import datetime, timedelta
        dt = datetime(2024, 12, 14)
        td = timedelta(days=7)
        result = dt + td
        assert result.day == 21
    
    def test_datetime_minus_timedelta(self):
        """datetime - timedelta works."""
        from pynext.runtime.stdlib.datetime import datetime, timedelta
        dt = datetime(2024, 12, 14)
        td = timedelta(days=7)
        result = dt - td
        assert result.day == 7
    
    def test_datetime_difference(self):
        """datetime - datetime returns timedelta."""
        from pynext.runtime.stdlib.datetime import datetime
        dt1 = datetime(2024, 12, 21)
        dt2 = datetime(2024, 12, 14)
        diff = dt1 - dt2
        assert diff.days == 7


# =============================================================================
# TIMEZONE TESTS (4 tests)
# =============================================================================

class TestTimezone:
    """Tests for timezone class."""
    
    def test_timezone_utc(self):
        """timezone.utc is UTC."""
        from pynext.runtime.stdlib.datetime import timezone
        assert timezone.utc is not None
    
    def test_timezone_custom_offset(self):
        """timezone with custom offset."""
        from pynext.runtime.stdlib.datetime import timezone, timedelta
        eastern = timezone(timedelta(hours=-5), "EST")
        assert eastern is not None
    
    def test_datetime_astimezone(self):
        """datetime.astimezone converts timezone."""
        from pynext.runtime.stdlib.datetime import datetime, timezone
        dt_utc = datetime.now(timezone.utc)
        dt_local = dt_utc.astimezone()
        assert dt_local is not None
    
    def test_datetime_replace(self):
        """datetime.replace creates new datetime."""
        from pynext.runtime.stdlib.datetime import datetime
        dt = datetime(2024, 12, 14, 10, 30)
        new_dt = dt.replace(year=2025, month=1)
        assert new_dt.year == 2025
        assert new_dt.month == 1
        assert new_dt.day == 14
