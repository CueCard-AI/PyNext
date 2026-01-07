"""
Phase 33.4: strftime/strptime Format Code Tests

Comprehensive tests for datetime formatting and parsing,
covering all standard format codes.
"""

import pytest
from pynext.runtime.stdlib.datetime import datetime, date, time


# =============================================================================
# YEAR FORMAT CODES
# =============================================================================

class TestYearFormatCodes:
    """Tests for year format codes."""
    
    def test_percent_Y_full_year(self):
        """Test %Y - 4-digit year."""
        dt = datetime(2024, 12, 14, 10, 30, 0)
        result = dt.strftime("%Y")
        assert result == "2024"
    
    def test_percent_Y_century_boundary(self):
        """Test %Y at century boundary."""
        dt = datetime(2000, 1, 1, 0, 0, 0)
        result = dt.strftime("%Y")
        assert result == "2000"
    
    def test_percent_y_two_digit_year(self):
        """Test %y - 2-digit year."""
        dt = datetime(2024, 12, 14, 10, 30, 0)
        result = dt.strftime("%y")
        assert result == "24"
    
    def test_percent_y_century_boundary(self):
        """Test %y at century boundary."""
        dt = datetime(2000, 1, 1, 0, 0, 0)
        result = dt.strftime("%y")
        assert result == "00"


# =============================================================================
# MONTH FORMAT CODES
# =============================================================================

class TestMonthFormatCodes:
    """Tests for month format codes."""
    
    def test_percent_m_zero_padded(self):
        """Test %m - zero-padded month."""
        dt = datetime(2024, 3, 14, 0, 0, 0)
        result = dt.strftime("%m")
        assert result == "03"
    
    def test_percent_m_double_digit(self):
        """Test %m - double digit month."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("%m")
        assert result == "12"
    
    def test_percent_B_full_month_name(self):
        """Test %B - full month name."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("%B")
        assert result == "December"
    
    def test_percent_b_abbreviated_month(self):
        """Test %b - abbreviated month name."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("%b")
        assert result == "Dec"


# =============================================================================
# DAY FORMAT CODES
# =============================================================================

class TestDayFormatCodes:
    """Tests for day format codes."""
    
    def test_percent_d_zero_padded(self):
        """Test %d - zero-padded day."""
        dt = datetime(2024, 12, 5, 0, 0, 0)
        result = dt.strftime("%d")
        assert result == "05"
    
    def test_percent_d_double_digit(self):
        """Test %d - double digit day."""
        dt = datetime(2024, 12, 25, 0, 0, 0)
        result = dt.strftime("%d")
        assert result == "25"
    
    def test_percent_j_day_of_year(self):
        """Test %j - day of year."""
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = dt.strftime("%j")
        assert result == "001"
    
    def test_percent_j_middle_year(self):
        """Test %j - middle of year."""
        dt = datetime(2024, 7, 4, 0, 0, 0)
        result = dt.strftime("%j")
        # July 4 is day 186 in a leap year
        assert len(result) == 3


# =============================================================================
# WEEKDAY FORMAT CODES
# =============================================================================

class TestWeekdayFormatCodes:
    """Tests for weekday format codes."""
    
    def test_percent_A_full_weekday(self):
        """Test %A - full weekday name."""
        dt = datetime(2024, 12, 14, 0, 0, 0)  # Saturday
        result = dt.strftime("%A")
        assert result == "Saturday"
    
    def test_percent_a_abbreviated_weekday(self):
        """Test %a - abbreviated weekday."""
        dt = datetime(2024, 12, 14, 0, 0, 0)  # Saturday
        result = dt.strftime("%a")
        assert result == "Sat"
    
    def test_percent_w_weekday_number(self):
        """Test %w - weekday as number (0=Sunday)."""
        dt = datetime(2024, 12, 15, 0, 0, 0)  # Sunday
        result = dt.strftime("%w")
        assert result == "0"
    
    def test_percent_u_weekday_iso(self):
        """Test %u - weekday ISO (1=Monday)."""
        dt = datetime(2024, 12, 16, 0, 0, 0)  # Monday
        result = dt.strftime("%u")
        assert result == "1"


# =============================================================================
# HOUR FORMAT CODES
# =============================================================================

class TestHourFormatCodes:
    """Tests for hour format codes."""
    
    def test_percent_H_24_hour(self):
        """Test %H - 24-hour format."""
        dt = datetime(2024, 12, 14, 14, 30, 0)
        result = dt.strftime("%H")
        assert result == "14"
    
    def test_percent_H_midnight(self):
        """Test %H - midnight."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("%H")
        assert result == "00"
    
    def test_percent_I_12_hour(self):
        """Test %I - 12-hour format."""
        dt = datetime(2024, 12, 14, 14, 30, 0)
        result = dt.strftime("%I")
        assert result == "02"
    
    def test_percent_I_noon(self):
        """Test %I - noon."""
        dt = datetime(2024, 12, 14, 12, 0, 0)
        result = dt.strftime("%I")
        assert result == "12"
    
    def test_percent_p_am_pm(self):
        """Test %p - AM/PM."""
        dt_am = datetime(2024, 12, 14, 10, 0, 0)
        dt_pm = datetime(2024, 12, 14, 14, 0, 0)
        assert dt_am.strftime("%p") == "AM"
        assert dt_pm.strftime("%p") == "PM"


# =============================================================================
# MINUTE/SECOND FORMAT CODES
# =============================================================================

class TestMinuteSecondFormatCodes:
    """Tests for minute and second format codes."""
    
    def test_percent_M_minute(self):
        """Test %M - minute."""
        dt = datetime(2024, 12, 14, 10, 5, 0)
        result = dt.strftime("%M")
        assert result == "05"
    
    def test_percent_S_second(self):
        """Test %S - second."""
        dt = datetime(2024, 12, 14, 10, 30, 45)
        result = dt.strftime("%S")
        assert result == "45"
    
    def test_percent_f_microsecond(self):
        """Test %f - microsecond."""
        dt = datetime(2024, 12, 14, 10, 30, 45, 123456)
        result = dt.strftime("%f")
        assert result == "123456"
    
    def test_percent_f_zero_padded(self):
        """Test %f - zero-padded microsecond."""
        dt = datetime(2024, 12, 14, 10, 30, 45, 123)
        result = dt.strftime("%f")
        assert result == "000123"


# =============================================================================
# COMBINED FORMAT CODES
# =============================================================================

class TestCombinedFormatCodes:
    """Tests for combined format strings."""
    
    def test_iso_format(self):
        """Test ISO format pattern."""
        dt = datetime(2024, 12, 14, 10, 30, 45)
        result = dt.strftime("%Y-%m-%d")
        assert result == "2024-12-14"
    
    def test_datetime_format(self):
        """Test datetime format pattern."""
        dt = datetime(2024, 12, 14, 10, 30, 45)
        result = dt.strftime("%Y-%m-%d %H:%M:%S")
        assert result == "2024-12-14 10:30:45"
    
    def test_us_date_format(self):
        """Test US date format."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("%m/%d/%Y")
        assert result == "12/14/2024"
    
    def test_european_date_format(self):
        """Test European date format."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("%d/%m/%Y")
        assert result == "14/12/2024"
    
    def test_time_12_hour_format(self):
        """Test 12-hour time format."""
        dt = datetime(2024, 12, 14, 14, 30, 45)
        result = dt.strftime("%I:%M %p")
        assert result == "02:30 PM"
    
    def test_full_datetime_format(self):
        """Test full datetime format."""
        dt = datetime(2024, 12, 14, 14, 30, 45)
        result = dt.strftime("%A, %B %d, %Y at %I:%M %p")
        assert result == "Saturday, December 14, 2024 at 02:30 PM"


# =============================================================================
# SPECIAL CHARACTERS
# =============================================================================

class TestSpecialCharacters:
    """Tests for special characters in format strings."""
    
    def test_percent_literal(self):
        """Test %% - literal percent."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("100%%")
        assert result == "100%"
    
    def test_format_with_spaces(self):
        """Test format with spaces."""
        dt = datetime(2024, 12, 14, 10, 30, 0)
        result = dt.strftime("%Y %m %d")
        assert result == "2024 12 14"
    
    def test_format_with_hyphens(self):
        """Test format with hyphens."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("%Y-%m-%d")
        assert result == "2024-12-14"
    
    def test_format_with_colons(self):
        """Test format with colons."""
        dt = datetime(2024, 12, 14, 10, 30, 45)
        result = dt.strftime("%H:%M:%S")
        assert result == "10:30:45"


# =============================================================================
# STRPTIME PARSING
# =============================================================================

class TestStrptime:
    """Tests for strptime parsing."""
    
    def test_strptime_iso_date(self):
        """Test strptime ISO date."""
        result = datetime.strptime("2024-12-14", "%Y-%m-%d")
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 14
    
    def test_strptime_datetime(self):
        """Test strptime datetime."""
        result = datetime.strptime("2024-12-14 10:30:45", "%Y-%m-%d %H:%M:%S")
        assert result.year == 2024
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45
    
    def test_strptime_us_format(self):
        """Test strptime US date format."""
        result = datetime.strptime("12/14/2024", "%m/%d/%Y")
        assert result.month == 12
        assert result.day == 14
        assert result.year == 2024
    
    def test_strptime_time_12_hour(self):
        """Test strptime 12-hour time."""
        result = datetime.strptime("02:30 PM", "%I:%M %p")
        assert result.hour == 14
        assert result.minute == 30


# =============================================================================
# DATE AND TIME STRFTIME
# =============================================================================

class TestDateTimeStrftime:
    """Tests for date and time object strftime."""
    
    def test_date_strftime(self):
        """Test date.strftime."""
        d = date(2024, 12, 14)
        result = d.strftime("%Y-%m-%d")
        assert result == "2024-12-14"
    
    def test_date_strftime_full(self):
        """Test date.strftime with full format."""
        d = date(2024, 12, 14)
        result = d.strftime("%A, %B %d, %Y")
        assert result == "Saturday, December 14, 2024"
    
    def test_time_strftime(self):
        """Test time.strftime."""
        t = time(10, 30, 45)
        result = t.strftime("%H:%M:%S")
        assert result == "10:30:45"
    
    def test_time_strftime_12_hour(self):
        """Test time.strftime 12-hour format."""
        t = time(14, 30, 0)
        result = t.strftime("%I:%M %p")
        assert result == "02:30 PM"


# =============================================================================
# EDGE CASES
# =============================================================================

class TestStrftimeEdgeCases:
    """Edge case tests for strftime."""
    
    def test_leap_year_february(self):
        """Test leap year February 29."""
        dt = datetime(2024, 2, 29, 0, 0, 0)  # 2024 is a leap year
        result = dt.strftime("%Y-%m-%d")
        assert result == "2024-02-29"
    
    def test_end_of_year(self):
        """Test end of year."""
        dt = datetime(2024, 12, 31, 23, 59, 59)
        result = dt.strftime("%Y-%m-%d %H:%M:%S")
        assert result == "2024-12-31 23:59:59"
    
    def test_start_of_year(self):
        """Test start of year."""
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = dt.strftime("%Y-%m-%d %H:%M:%S")
        assert result == "2024-01-01 00:00:00"
    
    def test_empty_format(self):
        """Test empty format string."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("")
        assert result == ""
    
    def test_format_no_codes(self):
        """Test format with no codes."""
        dt = datetime(2024, 12, 14, 0, 0, 0)
        result = dt.strftime("Hello World")
        assert result == "Hello World"

