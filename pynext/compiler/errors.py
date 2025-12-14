"""
PyNext Compiler - Error Messages

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This file defines compile-time error and warning classes with helpful,
AI-friendly error messages. Every error includes:

1. WHAT went wrong (clear description)
2. WHERE it happened (file, line, column)
3. WHY it's a problem (explanation)
4. HOW to fix it (solution with code example)
5. DOCS link for more information

Example output:
```
CompileError: Cannot compile Python class to JavaScript

  File "counter.py", line 15
    class Helper:
    ^^^^^

PROBLEM: Python classes cannot be compiled to JavaScript. The PyNext 
compiler only supports functions, signals, effects, and control flow.

SOLUTION: Move the class outside the @island component, or convert it 
to a plain function:

    # Instead of:
    class Helper:
        def format(self, x): return f"${x}"
    
    # Use:
    def format_currency(x): return f"${x}"

DOCS: https://pynext.dev/docs/compilation#classes
```

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Good error messages are CRITICAL for:

1. DEVELOPERS - Understand what went wrong without searching Stack Overflow
2. AI ASSISTANTS - LLMs can read the error and suggest fixes
3. DEBUGGING - Pinpoint exactly where the issue is

React's error messages are often cryptic. PyNext errors are designed to be
self-explanatory and actionable.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    CompileError
        │
        ├── message: str          # What went wrong
        ├── filename: str         # Which file  
        ├── line: int             # Which line
        ├── column: int           # Which column
        ├── source_line: str      # The actual code
        ├── suggestion: str       # How to fix it
        └── docs_url: str         # Link to docs

    When printed, formats as:
    
        [ERROR TYPE]: [MESSAGE]
        
          File "[FILENAME]", line [LINE]
            [SOURCE_LINE]
            [POINTER]
        
        PROBLEM: [EXPLANATION]
        
        SOLUTION: [SUGGESTION]
        
        DOCS: [URL]

=============================================================================
WHO USES THIS
=============================================================================

- Parser (parser.py) - Raises errors for invalid Python syntax
- Analyzer (analyzer.py) - Raises errors for non-compilable code
- Emitter (emitter.py) - Raises errors for unsupported patterns
- CLI - Displays errors to users
- IDE plugins - Show inline error markers

=============================================================================
WHEN TO USE (vs Alternatives)
=============================================================================

USE CompileError:
- Syntax errors (can't parse)
- Non-compilable constructs (class, await, etc.)
- Missing dependencies (signal not found)
- Type mismatches

USE CompileWarning:
- Suboptimal patterns (could be faster)
- Deprecated features
- Potential bugs (unused signal)

=============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List
import textwrap


# Documentation base URL
DOCS_BASE = "https://pynext.dev/docs"


@dataclass
class CompileError(Exception):
    """
    A compile-time error with helpful, actionable message.
    
    Attributes:
        message: Brief description of what went wrong
        filename: Source file where error occurred
        line: Line number (1-indexed)
        column: Column number (0-indexed)
        source_line: The actual line of code
        suggestion: How to fix the error
        docs_url: Link to documentation
        error_code: Machine-readable error code (e.g., "E001")
    
    Example:
        raise CompileError(
            message="Cannot compile 'await' expression",
            filename="counter.py",
            line=10,
            column=8,
            source_line="    result = await fetch_data()",
            suggestion="Use a server action for async operations",
            docs_url="compilation#async",
            error_code="E010",
        )
    """
    message: str
    filename: str = "<string>"
    line: int = 0
    column: int = 0
    source_line: str = ""
    suggestion: str = ""
    docs_url: str = ""
    error_code: str = ""
    
    def __post_init__(self):
        # Build full docs URL
        if self.docs_url and not self.docs_url.startswith("http"):
            self.docs_url = f"{DOCS_BASE}/{self.docs_url}"
        
        # Call Exception.__init__ with the formatted message
        super().__init__(str(self))
    
    def __str__(self) -> str:
        """Format the error for display."""
        lines = []
        
        # Header with error code
        header = f"CompileError"
        if self.error_code:
            header += f" [{self.error_code}]"
        header += f": {self.message}"
        lines.append(header)
        lines.append("")
        
        # Location
        if self.filename and self.line:
            lines.append(f"  File \"{self.filename}\", line {self.line}")
            
            # Source line with pointer
            if self.source_line:
                lines.append(f"    {self.source_line}")
                if self.column >= 0:
                    pointer = " " * (4 + self.column) + "^"
                    lines.append(pointer)
        
        # Suggestion
        if self.suggestion:
            lines.append("")
            lines.append("SOLUTION:")
            for line in self.suggestion.split("\n"):
                lines.append(f"  {line}")
        
        # Docs link
        if self.docs_url:
            lines.append("")
            lines.append(f"DOCS: {self.docs_url}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"CompileError({self.message!r}, line={self.line})"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": "error",
            "code": self.error_code,
            "message": self.message,
            "filename": self.filename,
            "line": self.line,
            "column": self.column,
            "source_line": self.source_line,
            "suggestion": self.suggestion,
            "docs_url": self.docs_url,
        }


@dataclass
class CompileWarning:
    """
    A compile-time warning (non-fatal).
    
    Warnings indicate potential issues or suboptimal patterns but don't
    prevent compilation from succeeding.
    
    Attributes:
        message: Brief description of the warning
        filename: Source file
        line: Line number
        suggestion: How to improve
        warning_code: Machine-readable code (e.g., "W001")
    
    Example:
        CompileWarning(
            message="Unused signal 'count' - consider removing",
            filename="counter.py",
            line=5,
            warning_code="W005",
        )
    """
    message: str
    filename: str = "<string>"
    line: int = 0
    column: int = 0
    source_line: str = ""
    suggestion: str = ""
    warning_code: str = ""
    
    def __str__(self) -> str:
        """Format the warning for display."""
        lines = []
        
        header = "Warning"
        if self.warning_code:
            header += f" [{self.warning_code}]"
        header += f": {self.message}"
        lines.append(header)
        
        if self.filename and self.line:
            lines.append(f"  File \"{self.filename}\", line {self.line}")
        
        if self.suggestion:
            lines.append(f"  Suggestion: {self.suggestion}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": "warning",
            "code": self.warning_code,
            "message": self.message,
            "filename": self.filename,
            "line": self.line,
            "column": self.column,
            "suggestion": self.suggestion,
        }


# =============================================================================
# PREDEFINED ERROR FACTORIES
# =============================================================================
# 
# These functions create common errors with consistent messages.
# Use these instead of creating CompileError directly.

def no_island_found(filename: str) -> CompileError:
    """Error: No @island decorator found in file."""
    return CompileError(
        message="No @island decorated function found",
        filename=filename,
        suggestion=textwrap.dedent("""
            Add the @island decorator to mark a component for client-side compilation:
            
                from pynext import island, signal
                
                @island
                def Counter():
                    count = signal(0)
                    return button()[count()]
        """).strip(),
        docs_url="compilation#island-decorator",
        error_code="E001",
    )


def invalid_syntax(filename: str, line: int, message: str) -> CompileError:
    """Error: Python syntax error."""
    return CompileError(
        message=f"Invalid Python syntax: {message}",
        filename=filename,
        line=line,
        suggestion="Fix the Python syntax error. Check for missing colons, brackets, or indentation.",
        docs_url="compilation#syntax",
        error_code="E002",
    )


def class_not_compilable(filename: str, line: int, source_line: str, class_name: str) -> CompileError:
    """Error: Class definition cannot be compiled."""
    return CompileError(
        message=f"Cannot compile class '{class_name}' to JavaScript",
        filename=filename,
        line=line,
        source_line=source_line,
        suggestion=textwrap.dedent(f"""
            Python classes cannot be compiled to JavaScript. Options:
            
            1. Move the class outside the @island component
            2. Convert to a plain function
            3. Use a server action for class-based logic
            
            # Instead of:
            class {class_name}:
                def method(self): ...
            
            # Use:
            def {class_name.lower()}_method(): ...
        """).strip(),
        docs_url="compilation#classes",
        error_code="E010",
    )


def await_not_compilable(filename: str, line: int, source_line: str) -> CompileError:
    """Error: await expression cannot be compiled."""
    return CompileError(
        message="Cannot compile 'await' expression to JavaScript",
        filename=filename,
        line=line,
        source_line=source_line,
        suggestion=textwrap.dedent("""
            Async/await cannot be compiled to client-side JavaScript.
            Use a server action instead:
            
                from pynext import island, signal, server_action
                
                @server_action
                async def fetch_data():
                    return await api.get_data()
                
                @island
                def DataDisplay():
                    data = signal(None)
                    
                    async def load():
                        result = await fetch_data()  # Calls server
                        data.set(result)
                    
                    return button(onclick=load)["Load Data"]
        """).strip(),
        docs_url="compilation#async",
        error_code="E011",
    )


def import_not_compilable(filename: str, line: int, source_line: str, module: str) -> CompileError:
    """Error: Import statement inside @island."""
    return CompileError(
        message=f"Cannot compile import '{module}' inside @island",
        filename=filename,
        line=line,
        source_line=source_line,
        suggestion=textwrap.dedent("""
            Move import statements outside the @island function.
            Only the function body is compiled to JavaScript.
            
                # DO THIS:
                from pynext import island, signal
                from myutils import format_date  # Import at module level
                
                @island
                def DateDisplay(date):
                    formatted = format_date(date)  # Use inside component
                    return span()[formatted]
            
            Note: If format_date has Python-only logic, pass the
            formatted result as a prop instead of calling it client-side.
        """).strip(),
        docs_url="compilation#imports",
        error_code="E012",
    )


def yield_not_compilable(filename: str, line: int, source_line: str) -> CompileError:
    """Error: yield/yield from cannot be compiled."""
    return CompileError(
        message="Cannot compile 'yield' expression to JavaScript",
        filename=filename,
        line=line,
        source_line=source_line,
        suggestion=textwrap.dedent("""
            Python generators cannot be compiled to JavaScript.
            Use a list or array instead:
            
                # Instead of:
                def items():
                    for i in range(10):
                        yield i
                
                # Use:
                items = [i for i in range(10)]
                
                # Or with signals:
                items = signal([1, 2, 3])
        """).strip(),
        docs_url="compilation#generators",
        error_code="E013",
    )


def global_not_compilable(filename: str, line: int, source_line: str, name: str) -> CompileError:
    """Error: global/nonlocal statement cannot be compiled."""
    return CompileError(
        message=f"Cannot compile 'global {name}' to JavaScript",
        filename=filename,
        line=line,
        source_line=source_line,
        suggestion=textwrap.dedent("""
            Use signals for shared state instead of global variables:
            
                # Instead of:
                count = 0
                
                @island
                def Counter():
                    global count
                    count += 1
                
                # Use:
                @island
                def Counter():
                    count = signal(0)
                    return button(onclick=lambda: count.update(lambda x: x + 1))
        """).strip(),
        docs_url="compilation#globals",
        error_code="E014",
    )


def signal_not_found(filename: str, line: int, name: str) -> CompileError:
    """Error: Signal referenced but not defined."""
    return CompileError(
        message=f"Signal '{name}' used but not defined",
        filename=filename,
        line=line,
        suggestion=textwrap.dedent(f"""
            Make sure to define the signal before using it:
            
                @island
                def MyComponent():
                    {name} = signal(initial_value)  # Define first
                    
                    return div()[{name}()]  # Then use
        """).strip(),
        docs_url="compilation#signals",
        error_code="E020",
    )


def invalid_handler(filename: str, line: int, source_line: str, reason: str) -> CompileError:
    """Error: Event handler cannot be compiled."""
    return CompileError(
        message=f"Invalid event handler: {reason}",
        filename=filename,
        line=line,
        source_line=source_line,
        suggestion=textwrap.dedent("""
            Event handlers must be simple lambdas or function references:
            
                # GOOD:
                onclick=lambda: count.set(count() + 1)
                onclick=lambda: do_something()
                onclick=handle_click
                
                # BAD:
                onclick=count.set(5)  # Missing lambda
                onclick=lambda: await fetch()  # No async
        """).strip(),
        docs_url="compilation#handlers",
        error_code="E030",
    )


def complex_comprehension(filename: str, line: int, source_line: str) -> CompileError:
    """Error: Complex comprehension cannot be compiled."""
    return CompileError(
        message="Complex comprehension cannot be compiled",
        filename=filename,
        line=line,
        source_line=source_line,
        suggestion=textwrap.dedent("""
            Only simple comprehensions can be compiled. Complex ones with
            multiple conditions or nested loops should use For() instead:
            
                # Instead of:
                [x for x in items if x.active and x.visible for y in x.children]
                
                # Use For() for complex iteration:
                For(each=lambda: items())[
                    lambda item: Show(when=lambda: item.active)[
                        For(each=lambda: item.children)[
                            lambda child: span()[child.name]
                        ]
                    ]
                ]
        """).strip(),
        docs_url="compilation#comprehensions",
        error_code="E040",
    )


# =============================================================================
# WARNING FACTORIES
# =============================================================================

def unused_signal(filename: str, line: int, name: str) -> CompileWarning:
    """Warning: Signal defined but never read."""
    return CompileWarning(
        message=f"Signal '{name}' is defined but never used",
        filename=filename,
        line=line,
        suggestion=f"Remove unused signal or add a read: {name}()",
        warning_code="W001",
    )


def signal_read_in_render(filename: str, line: int, name: str) -> CompileWarning:
    """Warning: Signal read outside effect (causes extra re-renders)."""
    return CompileWarning(
        message=f"Signal '{name}' read outside effect - may cause issues",
        filename=filename,
        line=line,
        suggestion="Wrap in effect() or memo() for proper tracking",
        warning_code="W002",
    )


def deprecated_api(filename: str, line: int, old_api: str, new_api: str) -> CompileWarning:
    """Warning: Using deprecated API."""
    return CompileWarning(
        message=f"'{old_api}' is deprecated, use '{new_api}' instead",
        filename=filename,
        line=line,
        suggestion=f"Replace {old_api} with {new_api}",
        warning_code="W010",
    )


def large_initial_value(filename: str, line: int, name: str, size: int) -> CompileWarning:
    """Warning: Signal has large initial value (affects bundle size)."""
    return CompileWarning(
        message=f"Signal '{name}' has large initial value ({size} bytes)",
        filename=filename,
        line=line,
        suggestion="Consider loading large data from server instead of embedding",
        warning_code="W020",
    )

