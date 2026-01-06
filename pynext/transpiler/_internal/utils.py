"""
PyNext Transpiler - Internal Utilities

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides shared utility functions used by parser.py and emitter.py.
These are low-level helpers for string manipulation, AST inspection,
and JavaScript code generation.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Both parser and emitter need common functionality:
- Generating unique variable names
- Escaping strings for JavaScript
- Formatting indentation
- Mapping Python operators to JavaScript

Centralizing these prevents duplication and ensures consistency.

=============================================================================
WHO USES THIS
=============================================================================

- parser.py: AST inspection helpers
- emitter.py: Code generation helpers
- (internal use only - not part of public API)
"""

from __future__ import annotations
from typing import Any, Iterator
import ast


# =============================================================================
# INDENTATION
# =============================================================================

def indent(code: str, level: int = 1, spaces: int = 4) -> str:
    """
    Indent a block of code.
    
    Args:
        code: The code to indent
        level: Number of indentation levels
        spaces: Spaces per indentation level
    
    Returns:
        Indented code
    
    Example:
        >>> indent("x = 1;\\ny = 2;", level=1)
        '    x = 1;\\n    y = 2;'
    """
    prefix = " " * (level * spaces)
    lines = code.split("\n")
    return "\n".join(prefix + line if line.strip() else line for line in lines)


def make_indent(level: int, spaces: int = 4) -> str:
    """
    Create an indentation string.
    
    Args:
        level: Number of indentation levels
        spaces: Spaces per level
    
    Returns:
        Indentation string
    """
    return " " * (level * spaces)


# =============================================================================
# STRING ESCAPING
# =============================================================================

def escape_js_string(s: str) -> str:
    """
    Escape a string for use in JavaScript.
    
    Handles:
    - Backslashes
    - Quotes
    - Newlines
    - Tabs
    - Unicode characters
    
    Args:
        s: The string to escape
    
    Returns:
        Escaped string (without surrounding quotes)
    
    Example:
        >>> escape_js_string('hello "world"')
        'hello \\"world\\"'
    """
    result = []
    for char in s:
        if char == "\\":
            result.append("\\\\")
        elif char == '"':
            result.append('\\"')
        elif char == "'":
            result.append("\\'")
        elif char == "\n":
            result.append("\\n")
        elif char == "\r":
            result.append("\\r")
        elif char == "\t":
            result.append("\\t")
        elif ord(char) < 32:
            # Other control characters
            result.append(f"\\x{ord(char):02x}")
        else:
            result.append(char)
    return "".join(result)


def to_js_string(s: str, quote: str = '"') -> str:
    """
    Convert a Python string to a JavaScript string literal.
    
    Args:
        s: The string to convert
        quote: Quote character to use ('"' or "'")
    
    Returns:
        JavaScript string literal with quotes
    
    Example:
        >>> to_js_string("hello")
        '"hello"'
    """
    return f'{quote}{escape_js_string(s)}{quote}'


# =============================================================================
# OPERATOR MAPPING
# =============================================================================

# Binary operators: Python AST operator class name → (JS operator, needs_runtime)
BINOP_MAP = {
    "Add": ("+", False),
    "Sub": ("-", False),
    "Mult": ("*", False),  # Note: string * int needs special handling
    "Div": ("/", False),
    "FloorDiv": ("//", True),  # Needs __py.floordiv()
    "Mod": ("%", True),  # Needs __py.mod() for negative numbers
    "Pow": ("**", False),
    "LShift": ("<<", False),
    "RShift": (">>", False),
    "BitOr": ("|", False),
    "BitXor": ("^", False),
    "BitAnd": ("&", False),
    "MatMult": ("@", True),  # Not supported
}


# Unary operators
UNARYOP_MAP = {
    "UAdd": ("+", False),
    "USub": ("-", False),
    "Not": ("!", True),  # Needs __py.bool() for truthiness
    "Invert": ("~", False),
}


# Comparison operators
CMPOP_MAP = {
    "Eq": ("===", True),  # Needs __py.eq() for collections
    "NotEq": ("!==", True),
    "Lt": ("<", False),
    "LtE": ("<=", False),
    "Gt": (">", False),
    "GtE": (">=", False),
    "Is": ("===", False),  # Identity
    "IsNot": ("!==", False),
    "In": ("in", True),  # Needs __py.in()
    "NotIn": ("in", True),  # Needs __py.in() with negation
}


def get_binop(op_class: type) -> tuple[str, bool]:
    """
    Get JavaScript operator for a Python binary operator.
    
    Args:
        op_class: The AST operator class (e.g., ast.Add)
    
    Returns:
        Tuple of (js_operator, needs_runtime)
    """
    name = op_class.__name__
    return BINOP_MAP.get(name, ("+", False))


def get_unaryop(op_class: type) -> tuple[str, bool]:
    """Get JavaScript operator for a Python unary operator."""
    name = op_class.__name__
    return UNARYOP_MAP.get(name, ("+", False))


def get_cmpop(op_class: type) -> tuple[str, bool]:
    """Get JavaScript operator for a Python comparison operator."""
    name = op_class.__name__
    return CMPOP_MAP.get(name, ("===", False))


# Augmented assignment operators
AUGOP_MAP = {
    "Add": "+=",
    "Sub": "-=",
    "Mult": "*=",
    "Div": "/=",
    "FloorDiv": "floordiv",  # Needs runtime
    "Mod": "mod",  # Needs runtime
    "Pow": "**=",
    "LShift": "<<=",
    "RShift": ">>=",
    "BitOr": "|=",
    "BitXor": "^=",
    "BitAnd": "&=",
}


def get_augop(op_class: type) -> str:
    """Get JavaScript operator for a Python augmented assignment operator."""
    name = op_class.__name__
    return AUGOP_MAP.get(name, "+=")


# =============================================================================
# UNIQUE NAME GENERATION
# =============================================================================

class NameGenerator:
    """
    Generate unique variable names for temporary values.
    
    Used when we need to create intermediate variables in generated code.
    
    Example:
        gen = NameGenerator()
        gen.next("temp")  # → "_temp_0"
        gen.next("temp")  # → "_temp_1"
        gen.next("loop")  # → "_loop_0"
    """
    
    def __init__(self, prefix: str = "_"):
        self._counters: dict[str, int] = {}
        self._prefix = prefix
    
    def next(self, base: str = "tmp") -> str:
        """Generate the next unique name for a given base."""
        count = self._counters.get(base, 0)
        self._counters[base] = count + 1
        return f"{self._prefix}{base}_{count}"
    
    def reset(self) -> None:
        """Reset all counters."""
        self._counters.clear()


# Global instance for convenience
_name_gen = NameGenerator()


def unique_name(base: str = "tmp") -> str:
    """Generate a unique variable name."""
    return _name_gen.next(base)


def reset_names() -> None:
    """Reset the name generator (useful between transpilations)."""
    _name_gen.reset()


# =============================================================================
# AST HELPERS
# =============================================================================

def is_constant(node: ast.AST) -> bool:
    """Check if an AST node is a constant value."""
    return isinstance(node, ast.Constant)


def is_name(node: ast.AST, name: str | None = None) -> bool:
    """
    Check if an AST node is a name reference.
    
    Args:
        node: AST node to check
        name: Optional specific name to match
    """
    if not isinstance(node, ast.Name):
        return False
    if name is not None:
        return node.id == name
    return True


def is_none(node: ast.AST) -> bool:
    """Check if an AST node is None."""
    return isinstance(node, ast.Constant) and node.value is None


def is_call_to(node: ast.AST, func_name: str) -> bool:
    """
    Check if an AST node is a call to a specific function.
    
    Example:
        is_call_to(node, "range")  # True for range(10)
    """
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id == func_name
    return False


def get_call_name(node: ast.Call) -> str | None:
    """Get the function name from a Call node."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


# =============================================================================
# PYTHON VALUE TO JAVASCRIPT LITERAL
# =============================================================================

def to_js_literal(value: Any) -> str:
    """
    Convert a Python value to a JavaScript literal.
    
    Args:
        value: Python value to convert
    
    Returns:
        JavaScript literal string
    
    Examples:
        >>> to_js_literal(5)
        '5'
        >>> to_js_literal("hello")
        '"hello"'
        >>> to_js_literal(True)
        'true'
        >>> to_js_literal(None)
        'null'
    """
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return to_js_string(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        items = ", ".join(to_js_literal(v) for v in value)
        return f"[{items}]"
    if isinstance(value, dict):
        pairs = ", ".join(f"{to_js_string(k)}: {to_js_literal(v)}" for k, v in value.items())
        return f"{{{pairs}}}"
    # Fallback
    return str(value)


# =============================================================================
# KEYWORD CHECKING
# =============================================================================

PYTHON_KEYWORDS = frozenset([
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield",
])

JS_RESERVED = frozenset([
    "break", "case", "catch", "continue", "debugger", "default", "delete",
    "do", "else", "finally", "for", "function", "if", "in", "instanceof",
    "new", "return", "switch", "this", "throw", "try", "typeof", "var",
    "void", "while", "with", "class", "const", "enum", "export", "extends",
    "import", "super", "implements", "interface", "let", "package", "private",
    "protected", "public", "static", "yield", "null", "true", "false",
    "undefined", "NaN", "Infinity",
])


def is_js_reserved(name: str) -> bool:
    """Check if a name is a JavaScript reserved word."""
    return name in JS_RESERVED


def safe_js_name(name: str) -> str:
    """
    Make a Python name safe for use in JavaScript.
    
    Handles reserved words by adding an underscore suffix.
    """
    if name in JS_RESERVED:
        return f"{name}_"
    return name
