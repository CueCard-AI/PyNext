"""
PyNext Runtime - Standard Library Modules

This package provides Python implementations of stdlib modules
that are also available in JavaScript via the transpiler.
"""

from . import datetime
from . import collections
from . import itertools
from . import functools
from . import operator
from . import copy

__all__ = ['datetime', 'collections', 'itertools', 'functools', 'operator', 'copy']

