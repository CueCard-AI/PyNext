"""
PyNext Runtime - itertools Module (Python implementation)

This module provides Python itertools functionality.
The JavaScript equivalent is in itertools.js.

For testing, this re-exports Python's standard itertools module
to ensure tests validate expected behavior.
"""

# Re-export from Python's standard itertools module
from itertools import (
    # Infinite iterators
    count,
    cycle,
    repeat,
    
    # Terminating iterators
    accumulate,
    chain,
    compress,
    dropwhile,
    filterfalse,
    groupby,
    islice,
    starmap,
    takewhile,
    tee,
    zip_longest,
    
    # Combinatoric iterators
    product,
    permutations,
    combinations,
    combinations_with_replacement,
)

# pairwise was added in Python 3.10
try:
    from itertools import pairwise
except ImportError:
    def pairwise(iterable):
        """Return successive overlapping pairs."""
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)

__all__ = [
    'count',
    'cycle',
    'repeat',
    'accumulate',
    'chain',
    'compress',
    'dropwhile',
    'filterfalse',
    'groupby',
    'islice',
    'starmap',
    'takewhile',
    'tee',
    'zip_longest',
    'product',
    'permutations',
    'combinations',
    'combinations_with_replacement',
    'pairwise',
]

