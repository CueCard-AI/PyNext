"""
PyNext Runtime - copy Module (Python implementation)

This module provides Python copy functionality.
The JavaScript equivalent is in copy.js.

For testing, this re-exports Python's standard copy module
to ensure tests validate expected behavior.
"""

# Re-export from Python's standard copy module
from copy import (
    copy,
    deepcopy,
    Error,
)

__all__ = [
    'copy',
    'deepcopy',
    'Error',
]

