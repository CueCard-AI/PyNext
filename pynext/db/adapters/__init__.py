"""
PyNext Database Adapters.

Adapters provide a consistent interface to different database backends.
"""

from pynext.db.adapters.base import Adapter
from pynext.db.adapters.memory import MemoryAdapter
from pynext.db.adapters.mock import MockAdapter

__all__ = ["Adapter", "MemoryAdapter", "MockAdapter"]

