"""
PyNext Runtime - datetime Module (Python implementation)

This module provides Python datetime functionality.
The JavaScript equivalent is in datetime.js.

For testing, this re-exports Python's standard datetime module
to ensure tests validate expected behavior.
"""

# Re-export from Python's standard datetime module
from datetime import (
    datetime,
    date,
    time,
    timedelta,
    timezone,
    tzinfo,
    MINYEAR,
    MAXYEAR,
)

# Make timezone.utc available as expected
UTC = timezone.utc

__all__ = [
    'datetime',
    'date', 
    'time',
    'timedelta',
    'timezone',
    'tzinfo',
    'UTC',
    'MINYEAR',
    'MAXYEAR',
]

