"""
PyNext Runtime - operator Module (Python implementation)

This module provides Python operator functionality.
The JavaScript equivalent is in operator.js.

For testing, this re-exports Python's standard operator module
to ensure tests validate expected behavior.
"""

# Re-export from Python's standard operator module
from operator import (
    # Getter functions
    itemgetter,
    attrgetter,
    methodcaller,
    
    # Arithmetic operators
    add,
    sub,
    mul,
    truediv,
    floordiv,
    mod,
    pow,
    neg,
    pos,
    abs as abs_,
    
    # Comparison operators
    eq,
    ne,
    lt,
    le,
    gt,
    ge,
    
    # Boolean operators
    and_,
    or_,
    not_,
    
    # Bitwise operators
    lshift,
    rshift,
    xor,
    inv,
    
    # Sequence operators
    concat,
    contains,
    countOf,
    indexOf,
    
    # Item access
    getitem,
    setitem,
    delitem,
)

__all__ = [
    # Getters
    'itemgetter',
    'attrgetter',
    'methodcaller',
    
    # Arithmetic
    'add',
    'sub',
    'mul',
    'truediv',
    'floordiv',
    'mod',
    'pow',
    'neg',
    'pos',
    'abs_',
    
    # Comparison
    'eq',
    'ne',
    'lt',
    'le',
    'gt',
    'ge',
    
    # Boolean
    'and_',
    'or_',
    'not_',
    
    # Bitwise
    'lshift',
    'rshift',
    'xor',
    'inv',
    
    # Sequence
    'concat',
    'contains',
    'countOf',
    'indexOf',
    
    # Item access
    'getitem',
    'setitem',
    'delitem',
]

