"""
PyNext Transpiler - Error Definitions

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Defines custom exception types for the transpiler with helpful error messages.
Every error includes source location (line, column) and suggestions for fixes.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Generic Python errors like "SyntaxError" are not helpful for debugging
transpilation issues. Users need to know:

1. WHAT went wrong (clear description)
2. WHERE it went wrong (file, line, column)
3. WHY it went wrong (explanation)
4. HOW to fix it (suggestion)

=============================================================================
HOW IT WORKS
=============================================================================

Each exception type represents a category of error:

- TranspileError: Base class for all transpiler errors
- UnsupportedSyntax: Python syntax that can't be transpiled
- SemanticError: Valid Python but can't map to JS semantics
- InternalError: Bug in the transpiler itself

=============================================================================
WHO USES THIS
=============================================================================

- parser.py: Raises errors when parsing unsupported syntax
- emitter.py: Raises errors when emitting impossible constructs
- __init__.py: Catches and formats errors for users

=============================================================================
EXAMPLES
=============================================================================

```python
raise UnsupportedSyntax(
    message="Generator functions are not supported",
    line=15,
    col=0,
    source="def count_up():\n    yield 1",
    suggestion="Use @server_action for generator functions"
)
```

Output:
```
TranspileError at line 15:

  def count_up():
      yield 1
      ^^^^^

Generator functions are not supported.

Suggestion: Use @server_action for generator functions
```
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import ast


@dataclass
class TranspileError(Exception):
    """
    Base class for all transpilation errors.
    
    Provides rich error messages with source context.
    """
    message: str
    line: int = 0
    col: int = 0
    source: Optional[str] = None
    suggestion: Optional[str] = None
    filename: Optional[str] = None
    
    def __post_init__(self):
        super().__init__(self.format())
    
    def format(self) -> str:
        """Format the error message with context."""
        parts = []
        
        # Header
        location = f"line {self.line}"
        if self.filename:
            location = f"{self.filename}:{self.line}"
        parts.append(f"TranspileError at {location}:")
        parts.append("")
        
        # Source context
        if self.source:
            lines = self.source.split("\n")
            if 0 < self.line <= len(lines):
                # Show the offending line
                line_content = lines[self.line - 1]
                parts.append(f"  {line_content}")
                # Show caret pointing to column
                if self.col >= 0:
                    caret = " " * (self.col + 2) + "^"
                    parts.append(caret)
            parts.append("")
        
        # Message
        parts.append(self.message)
        
        # Suggestion
        if self.suggestion:
            parts.append("")
            parts.append(f"Suggestion: {self.suggestion}")
        
        return "\n".join(parts)
    
    @classmethod
    def from_node(
        cls,
        message: str,
        node: ast.AST,
        source: Optional[str] = None,
        suggestion: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> "TranspileError":
        """Create an error from an AST node."""
        return cls(
            message=message,
            line=getattr(node, "lineno", 0),
            col=getattr(node, "col_offset", 0),
            source=source,
            suggestion=suggestion,
            filename=filename,
        )


@dataclass
class UnsupportedSyntax(TranspileError):
    """
    Python syntax that cannot be transpiled to JavaScript.
    
    Examples:
    - yield/yield from (generators)
    - async for / async with
    - match/case (pattern matching)
    - walrus operator :=
    """
    pass


@dataclass
class SemanticError(TranspileError):
    """
    Valid Python syntax but can't map to JavaScript semantics.
    
    Examples:
    - Multiple inheritance
    - Metaclasses
    - Descriptors
    """
    pass


@dataclass
class InternalError(TranspileError):
    """
    Bug in the transpiler itself.
    
    If users see this, they should report it.
    """
    def format(self) -> str:
        base = super().format()
        return base + "\n\nThis is a bug in the transpiler. Please report it!"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def unsupported(
    what: str,
    node: ast.AST,
    source: Optional[str] = None,
    suggestion: Optional[str] = None,
) -> UnsupportedSyntax:
    """
    Create an UnsupportedSyntax error with a standard message format.
    
    Args:
        what: What is unsupported (e.g., "Generator functions")
        node: The AST node that caused the error
        source: Original source code
        suggestion: How to work around this limitation
    
    Returns:
        UnsupportedSyntax exception (not raised, caller should raise)
    
    Example:
        raise unsupported("Generator functions", node, suggestion="Use @server_action")
    """
    return UnsupportedSyntax(
        message=f"{what} are not supported for client-side transpilation.",
        line=getattr(node, "lineno", 0),
        col=getattr(node, "col_offset", 0),
        source=source,
        suggestion=suggestion,
    )


def internal_error(
    message: str,
    node: Optional[ast.AST] = None,
) -> InternalError:
    """
    Create an InternalError for transpiler bugs.
    
    Args:
        message: Description of the internal error
        node: Optional AST node for location context
    
    Returns:
        InternalError exception
    """
    return InternalError(
        message=f"Internal error: {message}",
        line=getattr(node, "lineno", 0) if node else 0,
        col=getattr(node, "col_offset", 0) if node else 0,
    )


# =============================================================================
# COMMON ERROR MESSAGES (Phase 18.8 - Enhanced)
# =============================================================================

SUGGESTIONS = {
    # Generators
    "yield": (
        "Use @server_action for generator functions, or restructure as a regular function.\n\n"
        "Example using @server_action:\n"
        "    @server_action\n"
        "    def generate_items():\n"
        "        yield 1\n"
        "        yield 2\n\n"
        "Or restructure to return a list:\n"
        "    def get_items():\n"
        "        return [1, 2]"
    ),
    
    # Async
    "async_with": (
        "Use @server_action for async context managers.\n\n"
        "Example:\n"
        "    @server_action\n"
        "    async def fetch_with_session():\n"
        "        async with aiohttp.ClientSession() as session:\n"
        "            return await session.get(url)"
    ),
    "async_for": (
        "Use @server_action for async iteration.\n\n"
        "Example:\n"
        "    @server_action\n"
        "    async def process_stream():\n"
        "        async for chunk in stream:\n"
        "            process(chunk)"
    ),
    
    # Pattern matching
    "match": (
        "Use if/elif/else chains instead of match/case.\n\n"
        "Instead of:\n"
        "    match status:\n"
        "        case 'pending': ...\n"
        "        case 'done': ...\n\n"
        "Use:\n"
        "    if status == 'pending':\n"
        "        ...\n"
        "    elif status == 'done':\n"
        "        ..."
    ),
    
    # Walrus operator
    "walrus": (
        "Assign the value to a variable before the if statement.\n\n"
        "Instead of:\n"
        "    if (x := get_value()):\n"
        "        use(x)\n\n"
        "Use:\n"
        "    x = get_value()\n"
        "    if x:\n"
        "        use(x)"
    ),
    
    # Scope
    "global": (
        "Avoid global state in client-side handlers; use signals instead.\n\n"
        "Instead of:\n"
        "    global counter\n"
        "    counter += 1\n\n"
        "Use a signal:\n"
        "    counter = signal(0)\n"
        "    counter.set(counter() + 1)"
    ),
    "nonlocal": (
        "Pass values explicitly or use signals for shared state.\n\n"
        "JavaScript closures automatically capture outer variables by reference,\n"
        "so 'nonlocal' is often unnecessary. If you need to modify an outer\n"
        "variable, consider using a signal or store instead."
    ),
    
    # Classes (Phase 18.8)
    "class_multiple_inheritance": (
        "PyNext supports single inheritance only.\n"
        "Use composition instead:\n\n"
        "Instead of:\n"
        "    class Child(Parent1, Parent2):\n"
        "        pass\n\n"
        "Use:\n"
        "    class Child(Parent1):\n"
        "        def __init__(self):\n"
        "            super().__init__()\n"
        "            self.mixin = Parent2()  # Composition"
    ),
    "classmethod": (
        "Use @staticmethod instead, or move to @server_action.\n\n"
        "Instead of:\n"
        "    @classmethod\n"
        "    def from_dict(cls, data):\n"
        "        return cls(**data)\n\n"
        "Use:\n"
        "    @staticmethod\n"
        "    def from_dict(data):\n"
        "        return MyClass(**data)"
    ),
    "metaclass": (
        "Use regular classes or @server_action for complex class patterns.\n\n"
        "Metaclasses are not supported for client-side transpilation.\n"
        "If you need metaclass functionality, keep that code on the server\n"
        "and expose it via @server_action."
    ),
    "slots": (
        "Remove __slots__. JavaScript classes don't have this optimization.\n\n"
        "Instead of:\n"
        "    class Todo:\n"
        "        __slots__ = ['title', 'done']\n\n"
        "Just use:\n"
        "    class Todo:\n"
        "        def __init__(self, title):\n"
        "            self.title = title"
    ),
    "property_setter": (
        "Property setters (@name.setter) are not currently supported.\n"
        "Use a regular setter method instead.\n\n"
        "Instead of:\n"
        "    @value.setter\n"
        "    def value(self, val):\n"
        "        self._value = val\n\n"
        "Use:\n"
        "    def set_value(self, val):\n"
        "        self._value = val"
    ),
    
    # Imports
    "import": (
        "Imports are handled at the module level; use @server_action for dynamic imports.\n\n"
        "Client-side handlers can't import Python modules. Instead:\n"
        "1. Use browser APIs directly (fetch, localStorage, etc.)\n"
        "2. Use @server_action for server-side code\n"
        "3. Import at the module level, outside handlers"
    ),
    
    # Edge cases (Phase 18.8)
    "division_by_zero": (
        "Note: JavaScript returns Infinity for division by zero, not an error.\n\n"
        "Python:\n"
        "    1 / 0  → ZeroDivisionError\n\n"
        "JavaScript:\n"
        "    1 / 0  → Infinity\n\n"
        "Add explicit checks if you need Python-like behavior:\n"
        "    if divisor == 0:\n"
        "        raise ValueError('Division by zero')"
    ),
    "integer_overflow": (
        "Note: Large integers (>2^53) lose precision in JavaScript.\n\n"
        "Python:\n"
        "    x = 9007199254740993  # Precise\n\n"
        "JavaScript:\n"
        "    x = 9007199254740993  # May become 9007199254740992\n\n"
        "For precise large integers, use @server_action to keep\n"
        "computation on the server."
    ),
}


def get_suggestion(kind: str) -> Optional[str]:
    """Get a helpful suggestion for a specific error kind."""
    return SUGGESTIONS.get(kind)


def format_error_with_context(
    message: str,
    source: str,
    line: int,
    col: int = 0,
    suggestion: Optional[str] = None,
    num_context_lines: int = 3,
) -> str:
    """
    Format an error message with source context and caret.
    
    Args:
        message: Error message
        source: Full source code
        line: 1-indexed line number
        col: 0-indexed column number
        suggestion: Optional suggestion for fixing
        num_context_lines: Number of context lines to show
    
    Returns:
        Formatted error string with context
    """
    lines = source.split("\n")
    parts = []
    
    # Header
    parts.append(f"TranspileError at line {line}:")
    parts.append("")
    
    # Context lines before
    start = max(0, line - num_context_lines - 1)
    for i in range(start, line - 1):
        parts.append(f"  {i + 1:4d} | {lines[i]}")
    
    # Error line
    if 0 < line <= len(lines):
        parts.append(f"  {line:4d} | {lines[line - 1]}")
        # Caret
        if col >= 0:
            caret = " " * (9 + col) + "^"
            parts.append(caret)
    
    # Context lines after
    for i in range(line, min(len(lines), line + num_context_lines)):
        parts.append(f"  {i + 1:4d} | {lines[i]}")
    
    parts.append("")
    parts.append(message)
    
    # Suggestion
    if suggestion:
        parts.append("")
        parts.append("Suggestion:")
        for sug_line in suggestion.split("\n"):
            parts.append(f"  {sug_line}")
    
    return "\n".join(parts)
