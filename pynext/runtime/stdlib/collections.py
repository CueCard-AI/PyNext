"""
PyNext Runtime - collections Module (Python implementation)

This module provides Python collections functionality.
The JavaScript equivalent is in collections.js.

For testing, this re-exports Python's standard collections module
to ensure tests validate expected behavior.
"""

# Re-export from Python's standard collections module
from collections import (
    Counter,
    defaultdict,
    deque,
    OrderedDict,
    namedtuple,
    ChainMap,
    UserDict,
    UserList,
    UserString,
)

__all__ = [
    'Counter',
    'defaultdict',
    'deque',
    'OrderedDict',
    'namedtuple',
    'ChainMap',
    'UserDict',
    'UserList',
    'UserString',
]

