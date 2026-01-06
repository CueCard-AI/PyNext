"""
PyNext Transpiler - TYPE_CHECKING Context Tracking

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Tracks the TYPE_CHECKING context during AST parsing to correctly mark
imports inside `if TYPE_CHECKING:` blocks for stripping at runtime.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Python's `TYPE_CHECKING` is a constant that's `False` at runtime but `True`
for type checkers. Imports inside `if TYPE_CHECKING:` blocks should be
stripped from the transpiled JavaScript output since they're only for
type checking.

The parser needs to track when we're inside a TYPE_CHECKING block so it
can mark Import/ImportFrom nodes with `is_type_checking=True`, which the
emitter uses to skip emitting them.

=============================================================================
HOW IT WORKS
=============================================================================

Maintains a stack of TYPE_CHECKING context (boolean values). When entering
an `if TYPE_CHECKING:` block, push `True` onto the stack. When exiting,
pop it. When parsing imports, check if any level in the stack is `True`
to determine if the import should be marked as TYPE_CHECKING.

This handles nested cases like:
    if True:
        if TYPE_CHECKING:  # Stack: [False, True]
            from module import Type  # is_in_type_checking_context() → True

And functions/classes:
    def process():
        if TYPE_CHECKING:  # Stack: [True]
            from module import Type  # is_in_type_checking_context() → True
"""

from __future__ import annotations


# Global TYPE_CHECKING context stack
# Each entry is True if we're inside a TYPE_CHECKING block at that level
_type_checking_stack: list[bool] = []


def push_type_checking_context(is_type_checking: bool) -> None:
    """
    Push TYPE_CHECKING context onto stack.
    
    WHAT: Tracks that we're entering a conditional block (if statement).
    WHY: Need to know if we're inside a TYPE_CHECKING block to mark imports.
    HOW: Adds boolean value to global stack.
    WHO: Called by _parse_if() when parsing if statements.
    WHEN: During AST parsing when encountering if statements.
    WHERE: Part of TYPE_CHECKING context tracking system.
    
    Args:
        is_type_checking: True if this if statement is `if TYPE_CHECKING:`,
                         False otherwise
    """
    global _type_checking_stack
    _type_checking_stack.append(is_type_checking)


def pop_type_checking_context() -> None:
    """
    Pop TYPE_CHECKING context from stack.
    
    WHAT: Tracks that we're leaving a conditional block (if statement).
    WHY: Need to remove context when leaving if block.
    HOW: Removes last entry from global stack.
    WHO: Called by _parse_if() when finishing parsing if statement.
    WHEN: After parsing if statement body and orelse.
    WHERE: Part of TYPE_CHECKING context tracking system.
    """
    global _type_checking_stack
    if _type_checking_stack:
        _type_checking_stack.pop()


def is_in_type_checking_context() -> bool:
    """
    Check if currently inside TYPE_CHECKING block.
    
    WHAT: Returns whether we're currently inside any TYPE_CHECKING block.
    WHY: Used to mark imports as TYPE_CHECKING when parsing them.
    HOW: Returns True if any level in the stack is True.
    WHO: Called by parser when creating Import/ImportFrom nodes.
    WHEN: During import parsing to determine if import should be marked.
    WHERE: Part of TYPE_CHECKING context tracking system.
    
    Returns:
        True if we're inside a TYPE_CHECKING block at any level, False otherwise.
    
    Examples:
        if TYPE_CHECKING:  # push_type_checking_context(True)
            from module import Type  # is_in_type_checking_context() → True
            # Import will be marked with is_type_checking=True
        
        if True:
            if TYPE_CHECKING:  # Stack: [False, True]
                from module import Type  # is_in_type_checking_context() → True
    """
    global _type_checking_stack
    return any(_type_checking_stack)


def reset_type_checking_context() -> None:
    """
    Reset TYPE_CHECKING context stack (for new program).
    
    WHAT: Clears the TYPE_CHECKING context stack.
    WHY: Start fresh for each new program/transpilation.
    HOW: Clears the global stack.
    WHO: Called by parser at the start of program parsing.
    WHEN: When starting to parse a new program.
    WHERE: Part of TYPE_CHECKING context tracking system.
    """
    global _type_checking_stack
    _type_checking_stack = []

