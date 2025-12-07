"""
PyNext Relationship Filter Helpers.

Convenience functions for common filter values, especially date/time comparisons.

Usage:
    from pynext.db import has_many, eq, gte, days_ago, hours_ago
    
    class User(Table):
        # Posts from last 30 days
        recent_posts: List[Post] = has_many(Post, filter=[
            gte("created_at", days_ago(30))
        ])
        
        # Posts from last 24 hours
        todays_posts: List[Post] = has_many(Post, filter=[
            gte("created_at", hours_ago(24))
        ])
        
        # Posts from this week
        weekly_posts: List[Post] = has_many(Post, filter=[
            gte("created_at", weeks_ago(1))
        ])
"""

from __future__ import annotations

from datetime import datetime, timedelta, date, time
from typing import Union


# =============================================================================
# Date/Time Helpers
# =============================================================================

def days_ago(n: int) -> datetime:
    """
    Get datetime N days ago from now.
    
    Args:
        n: Number of days ago
    
    Returns:
        datetime N days before current time
    
    Example:
        filter=[gte("created_at", days_ago(30))]
        # Gets records from last 30 days
    """
    return datetime.now() - timedelta(days=n)


def hours_ago(n: int) -> datetime:
    """
    Get datetime N hours ago from now.
    
    Args:
        n: Number of hours ago
    
    Returns:
        datetime N hours before current time
    
    Example:
        filter=[gte("created_at", hours_ago(24))]
        # Gets records from last 24 hours
    """
    return datetime.now() - timedelta(hours=n)


def minutes_ago(n: int) -> datetime:
    """
    Get datetime N minutes ago from now.
    
    Args:
        n: Number of minutes ago
    
    Returns:
        datetime N minutes before current time
    
    Example:
        filter=[gte("updated_at", minutes_ago(5))]
        # Gets records updated in last 5 minutes
    """
    return datetime.now() - timedelta(minutes=n)


def seconds_ago(n: int) -> datetime:
    """
    Get datetime N seconds ago from now.
    
    Args:
        n: Number of seconds ago
    
    Returns:
        datetime N seconds before current time
    
    Example:
        filter=[gte("last_seen", seconds_ago(30))]
        # Gets records seen in last 30 seconds
    """
    return datetime.now() - timedelta(seconds=n)


def weeks_ago(n: int) -> datetime:
    """
    Get datetime N weeks ago from now.
    
    Args:
        n: Number of weeks ago
    
    Returns:
        datetime N weeks before current time
    
    Example:
        filter=[gte("created_at", weeks_ago(2))]
        # Gets records from last 2 weeks
    """
    return datetime.now() - timedelta(weeks=n)


def months_ago(n: int) -> datetime:
    """
    Get datetime N months ago from now (approximate: 30 days per month).
    
    Args:
        n: Number of months ago
    
    Returns:
        datetime approximately N months before current time
    
    Example:
        filter=[gte("created_at", months_ago(3))]
        # Gets records from last ~3 months
    
    Note:
        Uses 30 days per month approximation.
        For exact month calculation, use a date library.
    """
    return datetime.now() - timedelta(days=n * 30)


def years_ago(n: int) -> datetime:
    """
    Get datetime N years ago from now (approximate: 365 days per year).
    
    Args:
        n: Number of years ago
    
    Returns:
        datetime approximately N years before current time
    
    Example:
        filter=[gte("created_at", years_ago(1))]
        # Gets records from last ~year
    
    Note:
        Uses 365 days per year approximation.
        For exact year calculation, use a date library.
    """
    return datetime.now() - timedelta(days=n * 365)


# =============================================================================
# Future Date Helpers
# =============================================================================

def days_from_now(n: int) -> datetime:
    """
    Get datetime N days from now.
    
    Args:
        n: Number of days from now
    
    Returns:
        datetime N days after current time
    
    Example:
        filter=[lte("expires_at", days_from_now(7))]
        # Gets records expiring within 7 days
    """
    return datetime.now() + timedelta(days=n)


def hours_from_now(n: int) -> datetime:
    """
    Get datetime N hours from now.
    
    Args:
        n: Number of hours from now
    
    Returns:
        datetime N hours after current time
    """
    return datetime.now() + timedelta(hours=n)


def minutes_from_now(n: int) -> datetime:
    """
    Get datetime N minutes from now.
    
    Args:
        n: Number of minutes from now
    
    Returns:
        datetime N minutes after current time
    """
    return datetime.now() + timedelta(minutes=n)


# =============================================================================
# Date Boundary Helpers
# =============================================================================

def today() -> date:
    """
    Get today's date.
    
    Returns:
        Today's date (without time)
    
    Example:
        filter=[eq("date", today())]
        # Gets records from today
    """
    return date.today()


def yesterday() -> date:
    """
    Get yesterday's date.
    
    Returns:
        Yesterday's date
    
    Example:
        filter=[eq("date", yesterday())]
        # Gets records from yesterday
    """
    return date.today() - timedelta(days=1)


def tomorrow() -> date:
    """
    Get tomorrow's date.
    
    Returns:
        Tomorrow's date
    """
    return date.today() + timedelta(days=1)


def start_of_today() -> datetime:
    """
    Get datetime at start of today (midnight).
    
    Returns:
        datetime at 00:00:00 today
    
    Example:
        filter=[gte("created_at", start_of_today())]
        # Gets records created today
    """
    return datetime.combine(date.today(), time.min)


def end_of_today() -> datetime:
    """
    Get datetime at end of today (23:59:59.999999).
    
    Returns:
        datetime at 23:59:59.999999 today
    """
    return datetime.combine(date.today(), time.max)


def start_of_week() -> datetime:
    """
    Get datetime at start of current week (Monday 00:00:00).
    
    Returns:
        datetime at start of week
    
    Example:
        filter=[gte("created_at", start_of_week())]
        # Gets records from this week
    """
    today_dt = date.today()
    start = today_dt - timedelta(days=today_dt.weekday())
    return datetime.combine(start, time.min)


def start_of_month() -> datetime:
    """
    Get datetime at start of current month.
    
    Returns:
        datetime at first day of month, 00:00:00
    
    Example:
        filter=[gte("created_at", start_of_month())]
        # Gets records from this month
    """
    today_dt = date.today()
    start = today_dt.replace(day=1)
    return datetime.combine(start, time.min)


def start_of_year() -> datetime:
    """
    Get datetime at start of current year.
    
    Returns:
        datetime at January 1st, 00:00:00
    """
    today_dt = date.today()
    start = today_dt.replace(month=1, day=1)
    return datetime.combine(start, time.min)


# =============================================================================
# Value Helpers
# =============================================================================

def now() -> datetime:
    """
    Get current datetime.
    
    Returns:
        Current datetime
    
    Example:
        filter=[lte("scheduled_at", now())]
        # Gets records scheduled for now or earlier
    """
    return datetime.now()


def utc_now() -> datetime:
    """
    Get current UTC datetime.
    
    Returns:
        Current UTC datetime
    """
    from datetime import timezone
    return datetime.now(timezone.utc)

