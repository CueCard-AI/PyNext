"""
PyNext Transpiler - Exception Context Tracking

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Tracks the current exception being handled in except blocks to automatically
set __context__ when new exceptions are raised during exception handling.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Python automatically sets __context__ when an exception is raised during
exception handling (not explicitly chained with `from`):

```python
try:
    raise ValueError("original")
except ValueError:  # _e is the caught ValueError
    raise TypeError("during handling")  # TypeError.__context__ = ValueError automatically
```

JavaScript doesn't have this behavior, so we need to track the exception
context and emit code that sets __context__ automatically.

=============================================================================
HOW IT WORKS
=============================================================================

Maintains a stack of exception variable names. When entering an except block,
push the exception variable onto the stack. When exiting, pop it. When emitting
a raise statement, check if we're inside an except block and automatically
set __context__ to the current exception.
"""

from __future__ import annotations
from typing import Optional


# Global exception context stack
_exception_context_stack: list[str] = []


def push_exception_context(exc_var: str) -> None:
    """
    Push exception variable onto context stack.
    
    WHAT: Tracks that we're entering an except block with a caught exception.
    WHY: Need to know which exception to use as __context__ for new exceptions.
    HOW: Adds exception variable name to global stack.
    WHO: Called by _emit_try() when entering catch block.
    WHEN: When emitting try/except statements.
    WHERE: Part of exception context tracking system.
    
    Args:
        exc_var: Name of the exception variable (e.g., "_e", "e")
    """
    global _exception_context_stack
    _exception_context_stack.append(exc_var)


def pop_exception_context() -> None:
    """
    Pop exception variable from context stack.
    
    WHAT: Tracks that we're leaving an except block.
    WHY: Need to remove exception from context when leaving except block.
    HOW: Removes last exception variable from global stack.
    WHO: Called by _emit_try() when leaving catch block.
    WHEN: When emitting try/except statements.
    WHERE: Part of exception context tracking system.
    """
    global _exception_context_stack
    if _exception_context_stack:
        _exception_context_stack.pop()


def get_current_exception_context() -> Optional[str]:
    """
    Get current exception context variable.
    
    WHAT: Returns the exception variable name for the current except block.
    WHY: Used to set __context__ when raising exceptions inside except blocks.
    HOW: Returns the top of the exception context stack.
    WHO: Called by _emit_expr_stmt() when emitting raise statements.
    WHEN: When checking if we should set __context__ automatically.
    WHERE: Part of exception context tracking system.
    
    Returns:
        Exception variable name if inside an except block, None otherwise.
    
    Example:
        try:
            raise ValueError("original")
        except ValueError:  # push_exception_context("_e")
            raise TypeError("new")  # get_current_exception_context() → "_e"
            # Emit: const _exc = new TypeError("new"); _exc.__context__ = _e; throw _exc;
    """
    global _exception_context_stack
    return _exception_context_stack[-1] if _exception_context_stack else None


def reset_exception_context() -> None:
    """
    Reset exception context stack (for new program).
    
    WHAT: Clears the exception context stack.
    WHY: Start fresh for each new program/transpilation.
    HOW: Clears the global stack.
    WHO: Called by _emit_program() at the start.
    WHEN: When starting to emit a new program.
    WHERE: Part of exception context tracking system.
    """
    global _exception_context_stack
    _exception_context_stack = []

