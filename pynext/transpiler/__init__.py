"""
PyNext Transpiler - Python to JavaScript

=============================================================================
WHAT THIS FILE DOES
=============================================================================

This is the public API for the PyNext transpiler. It provides simple functions
to convert Python code to JavaScript, suitable for client-side execution.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

PyNext allows developers to write Python code that runs in the browser.
Event handlers, reactive computations, and interactive logic written in
Python need to be converted to JavaScript that browsers can execute.

The transpiler bridges this gap by:
1. Parsing Python source code
2. Converting to an intermediate representation (IR)
3. Emitting optimized JavaScript
4. Preserving Python semantics where they differ from JS

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    Python Source Code
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                        transpile()                               │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
    │  │   Parser    │ ─▶ │     IR      │ ─▶ │   Emitter   │         │
    │  │ (parser.py) │    │  (nodes.py) │    │ (emitter.py)│         │
    │  └─────────────┘    └─────────────┘    └─────────────┘         │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
           │
           ▼
    JavaScript Source Code

=============================================================================
WHO USES THIS
=============================================================================

- pynext/core/html.py: Transpiles onclick, onsubmit handlers
- pynext/reactive/: Transpiles reactive computations
- pynext/compiler/: Uses for @island component compilation
- Developers: Can use directly for custom transpilation needs

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler import transpile, transpile_handler

# Transpile a simple expression
js = transpile("x = items[-1]")
# → "let x = __py.at(items, -1);"

# Transpile an event handler function
js = transpile_handler('''
def handle_click():
    count.set(count() + 1)
''')
# → "function handle_click() { count.set(count() + 1); }"

# Transpile with error context
try:
    js = transpile("yield 1")
except TranspileError as e:
    print(e)
    # → TranspileError at line 1: Generator functions are not supported
```
"""

from __future__ import annotations
from typing import Optional

from .parser import parse, parse_function, parse_statements
from .emitter import emit, emit_expression
from .nodes import (
    # Re-export all node types for advanced usage
    JSNode, Program,
    Assignment, AugAssign, If, For, While, FunctionDef,
    Return, Pass, Break, Continue, Delete, ExprStmt,
    Name, Constant, BinOp, UnaryOp, Compare, BoolOp, IfExp,
    Call, Attribute, Subscript, Slice, List, Dict, Tuple,
    Lambda, Starred, DictSpread, TupleUnpack,
    # Classes (Phase 18.8)
    ClassDef, MethodDef, PropertyDef, PropertySetterDef,
    # Assert and Walrus (Phase 18.8)
    Assert, NamedExpr,
)
from .errors import (
    TranspileError,
    UnsupportedSyntax,
    SemanticError,
    InternalError,
    unsupported,
)


__all__ = [
    # Main API
    "transpile",
    "transpile_handler",
    "transpile_expression",
    # Error types
    "TranspileError",
    "UnsupportedSyntax",
    "SemanticError",
    "InternalError",
    # Advanced API
    "parse",
    "emit",
    # Optimizer (Phase 18.7)
    "optimize",
    "OptimizeOptions",
    # PyNext Integration (Phase 18.6)
    "ReactiveContext",
    "analyze_handler",
    "transpile_for_hydration",
    "PyNextTransformer",
    # Node types (for advanced usage)
    "JSNode",
    "Program",
    "Assignment",
    "AugAssign",
    "If",
    "For",
    "While",
    "FunctionDef",
    "Return",
    "Pass",
    "Break",
    "Continue",
    "Delete",
    "ExprStmt",
    "Name",
    "Constant",
    "BinOp",
    "UnaryOp",
    "Compare",
    "BoolOp",
    "IfExp",
    "Call",
    "Attribute",
    "Subscript",
    "Slice",
    "List",
    "Dict",
    "Tuple",
    "Lambda",
    "Starred",
    "DictSpread",
    "TupleUnpack",
    # Classes (Phase 18.8)
    "ClassDef",
    "MethodDef",
    "PropertyDef",
    "PropertySetterDef",
    # Assert and Walrus (Phase 18.8)
    "Assert",
    "NamedExpr",
]

# Phase 18.6: PyNext Integration exports
from .reactive import ReactiveContext, analyze_handler, create_context
from .hydration import transpile_for_hydration, transpile_inline_handler
from .pynext import PyNextTransformer, transpile_handler_source, transpile_handler_body

# Phase 18.7: Optimizer exports
from .optimizer import optimize as optimize_ir, OptimizeOptions


# =============================================================================
# PUBLIC API
# =============================================================================

def transpile(
    source: str,
    *,
    filename: str = "<string>",
    indent: int = 0,
    minify: bool = False,
    optimize: bool = False,
) -> str:
    """
    Transpile Python source code to JavaScript.
    
    This is the main entry point for the transpiler.
    
    Args:
        source: Python source code as a string
        filename: Optional filename for error messages
        indent: Base indentation level (number of 4-space indents)
        minify: If True, produce minified output (future)
        optimize: If True, run optimization passes (wrapper elision, etc.)
    
    Returns:
        JavaScript source code
    
    Raises:
        TranspileError: If the code contains unsupported syntax
    
    Examples:
        >>> transpile("x = 5")
        'let x = 5;'
        
        >>> transpile("items[-1]")
        '__py.at(items, -1)'
        
        >>> transpile('''
        ... def greet(name):
        ...     return "Hello, " + name
        ... ''')
        'function greet(name) {
            return "Hello, " + name;
        }'
        
        >>> transpile("x = 5 + 3", optimize=True)
        'let x = 8;'  # Constant folding
    
    Notes:
        - Type annotations are preserved but ignored
        - Comments are not preserved (Python AST drops them)
        - Unsupported constructs raise UnsupportedSyntax errors
    """
    from .optimizer import optimize as run_optimizer
    
    ir = parse(source, filename=filename)
    
    if optimize:
        ir = run_optimizer(ir)
    
    return emit(ir, indent=indent)


def transpile_handler(
    source: str,
    *,
    filename: str = "<handler>",
    extract_body: bool = True,
) -> str:
    """
    Transpile a Python event handler to JavaScript.
    
    Optimized for PyNext event handlers (onclick, onsubmit, etc.).
    Can extract just the function body if desired.
    
    Args:
        source: Python function source code
        filename: Optional filename for error messages
        extract_body: If True, return only the function body (no wrapper)
    
    Returns:
        JavaScript source code
    
    Raises:
        TranspileError: If the code contains unsupported syntax
    
    Examples:
        >>> transpile_handler('''
        ... def handle_click():
        ...     count.set(count() + 1)
        ... ''')
        'function handle_click() {
            count.set(count() + 1);
        }'
        
        >>> transpile_handler('''
        ... def handle_submit():
        ...     if form.validate():
        ...         submit_data(form.values)
        ... ''', extract_body=True)
        'if (form.validate()) {
            submit_data(form.values);
        }'
    """
    import ast
    
    # Parse the source
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        raise TranspileError(
            message=f"Python syntax error: {e.msg}",
            line=e.lineno or 0,
            col=e.offset or 0,
            source=source,
            filename=filename,
        )
    
    # Find the function definition
    func_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_node = node
            break
    
    if func_node is None:
        raise TranspileError(
            message="No function definition found in handler",
            source=source,
            filename=filename,
        )
    
    # Parse to IR
    ir = parse_function(func_node, source=source)
    
    if extract_body:
        # Return only the body statements
        lines = []
        for stmt in ir.body:
            lines.append(emit(stmt, indent=0))
        return "\n".join(lines)
    
    # Return the full function
    return emit(ir, indent=0)


def transpile_expression(
    source: str,
    *,
    filename: str = "<expr>",
) -> str:
    """
    Transpile a single Python expression to JavaScript.
    
    Use this for simple expressions that don't need statement handling.
    
    Args:
        source: Python expression as a string
        filename: Optional filename for error messages
    
    Returns:
        JavaScript expression (no semicolon)
    
    Raises:
        TranspileError: If the code is not a valid expression
    
    Examples:
        >>> transpile_expression("x + 1")
        '(x + 1)'
        
        >>> transpile_expression("items[-1]")
        '__py.at(items, -1)'
        
        >>> transpile_expression("lambda x: x * 2")
        '(x) => x * 2'
    """
    import ast
    
    try:
        tree = ast.parse(source, filename=filename, mode="eval")
    except SyntaxError as e:
        raise TranspileError(
            message=f"Invalid expression: {e.msg}",
            line=e.lineno or 0,
            col=e.offset or 0,
            source=source,
            filename=filename,
        )
    
    from .parser import _parse_expression
    ir = _parse_expression(tree.body, source=source)
    return emit_expression(ir)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def is_supported(source: str) -> bool:
    """
    Check if Python source code can be transpiled.
    
    Useful for feature detection before attempting transpilation.
    
    Args:
        source: Python source code
    
    Returns:
        True if the code can be transpiled, False otherwise
    
    Examples:
        >>> is_supported("x = 5")
        True
        
        >>> is_supported("yield 1")
        False
    """
    try:
        transpile(source)
        return True
    except (TranspileError, Exception):
        return False


def get_unsupported_features(source: str) -> list[str]:
    """
    Get a list of unsupported features in Python source code.
    
    Args:
        source: Python source code
    
    Returns:
        List of unsupported feature descriptions
    
    Examples:
        >>> get_unsupported_features("yield 1")
        ['Generator functions are not supported']
    """
    import ast
    
    unsupported_features = []
    
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ["Invalid Python syntax"]
    
    # Walk the AST looking for unsupported constructs
    for node in ast.walk(tree):
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            unsupported_features.append("Generator functions (yield)")
        if isinstance(node, ast.AsyncWith):
            unsupported_features.append("Async context managers (async with)")
        if isinstance(node, ast.AsyncFor):
            unsupported_features.append("Async iteration (async for)")
        if hasattr(ast, "Match") and isinstance(node, ast.Match):
            unsupported_features.append("Pattern matching (match/case)")
        if hasattr(ast, "NamedExpr") and isinstance(node, ast.NamedExpr):
            unsupported_features.append("Walrus operator (:=)")
        if isinstance(node, ast.Global):
            unsupported_features.append("Global statement")
        if isinstance(node, ast.Nonlocal):
            unsupported_features.append("Nonlocal statement")
    
    return list(set(unsupported_features))  # Deduplicate
