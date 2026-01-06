"""
PyNext Transpiler - Parser (Python AST → IR)

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Converts Python source code (or AST) into our Intermediate Representation (IR).
The IR is a simplified tree of nodes that maps cleanly to JavaScript constructs.

    Python Source → ast.parse() → Python AST → parse() → IR Nodes

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Python's AST is complex and contains many constructs that don't exist in
JavaScript. The parser:

1. Filters out unsupported constructs (with helpful errors)
2. Normalizes patterns (e.g., chained comparisons → multiple comparisons)
3. Creates a clean IR that the emitter can easily convert to JS
4. Preserves source location for error messages

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    Python Source
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  parse(source)                                                   │
    │      │                                                           │
    │      ├── ast.parse(source) → Python AST                         │
    │      │                                                           │
    │      └── parse_module(ast) → IR                                 │
    │              │                                                   │
    │              ├── For each statement:                             │
    │              │       parse_statement(stmt) → IR node             │
    │              │                                                   │
    │              └── Returns Program(body=[...])                    │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

- __init__.py: transpile() calls parse() first
- Tests: Verify parsing produces correct IR

=============================================================================
WHEN TO USE (vs Alternatives)
=============================================================================

USE parse():
- When you have Python source code as a string

USE parse_function():
- When you have an already-parsed function AST node

USE parse_statements():
- When you have a list of AST statement nodes

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler.parser import parse

# Parse a simple assignment
ir = parse("x = 5")
# → Program(body=[Assignment(target="x", value=Constant(5))])

# Parse a function
ir = parse('''
def foo(a, b):
    return a + b
''')
# → Program(body=[FunctionDef(name="foo", args=("a", "b"), ...)])
```
"""

from __future__ import annotations
import ast
from typing import Optional, Sequence

from .nodes import (
    JSNode, Program,
    # Statements
    Assignment, AugAssign, If, For, ForUnpack, While, FunctionDef,
    Return, Pass, Break, Continue, Delete, ExprStmt,
    # Expressions
    Name, Constant, BinOp, UnaryOp, Compare, BoolOp, IfExp,
    Call, Attribute, Subscript, Slice, List, Dict, Tuple,
    Lambda, Await, Starred, DictSpread, TupleUnpack,
    # Decorators (Phase 18.5)
    Decorator, DecoratedFunction,
    # F-strings and Comprehensions
    FString, FormattedValue, Comprehension,
    ListComp, DictComp, SetComp, GeneratorExp,
    # Classes (Phase 18.8)
    ClassDef, MethodDef, PropertyDef, PropertySetterDef, PropertyDeleterDef,
    # Assert and Walrus (Phase 18.8)
    Assert, NamedExpr,
    # Phase 33.2: Advanced Constructs
    DunderMethod, Yield, YieldFrom, With, WithItem,
    Match, Case, Pattern, LiteralPattern, CapturePattern, WildcardPattern,
    SequencePattern, MappingPattern, ClassPattern, OrPattern, AsPattern, GuardPattern,
    AsyncFunctionDef,
    # Phase 33.3: Import System
    Import, ImportFrom, ImportStar,
)
from .errors import TranspileError, UnsupportedSyntax, unsupported, get_suggestion
from ._internal.utils import get_binop, get_unaryop, get_cmpop, get_augop, is_call_to
from ._internal.scope import get_scope, MethodContext, ClassContext, GuardContext


# =============================================================================
# ASYNC CONTEXT TRACKING (Phase 18 Fix)
# =============================================================================

# Track whether we're inside an async function for await validation
_async_context_depth = 0


def _enter_async_context():
    """Enter an async function context."""
    global _async_context_depth
    _async_context_depth += 1


def _exit_async_context():
    """Exit an async function context."""
    global _async_context_depth
    _async_context_depth -= 1


def _is_in_async_context() -> bool:
    """Check if we're currently parsing inside an async function."""
    return _async_context_depth > 0


def _reset_async_context():
    """Reset async context (for new parse)."""
    global _async_context_depth
    _async_context_depth = 0


# =============================================================================
# PUBLIC API
# =============================================================================

def parse(source: str, filename: str = "<string>") -> Program:
    """
    Parse Python source code into IR.
    
    This is the main entry point for parsing.
    
    Args:
        source: Python source code
        filename: Optional filename for error messages
    
    Returns:
        Program node containing the parsed IR
    
    Raises:
        TranspileError: If the code contains unsupported syntax
    
    Example:
        >>> ir = parse("x = 5")
        >>> ir.body[0]
        Assignment(target='x', value=Constant(value=5))
    """
    # Phase 33.3: Reset TYPE_CHECKING context for new program
    from ._internal.type_checking_context import reset_type_checking_context
    reset_type_checking_context()
    
    # Reset async context for fresh parse
    _reset_async_context()
    
    try:
        tree = ast.parse(source, filename=filename, mode="exec")
    except SyntaxError as e:
        raise TranspileError(
            message=f"Python syntax error: {e.msg}",
            line=e.lineno or 0,
            col=e.offset or 0,
            source=source,
            filename=filename,
        )
    
    # Phase 33.3: Create module resolver for import path resolution
    from ._internal.module_resolver import ModuleResolver
    resolver = ModuleResolver(current_file=filename)
    
    return parse_module(tree, source=source, resolver=resolver)


def parse_function(node: ast.FunctionDef, source: Optional[str] = None) -> FunctionDef:
    """
    Parse a function definition AST node into IR.
    
    Args:
        node: Python AST FunctionDef node
        source: Optional source code for error messages
    
    Returns:
        FunctionDef IR node
    """
    # Phase 33.3: Create resolver for backward compatibility
    from ._internal.module_resolver import ModuleResolver
    resolver = ModuleResolver(current_file="<string>")
    return _parse_function_def(node, source, resolver=resolver)


def parse_statements(
    stmts: Sequence[ast.stmt],
    source: Optional[str] = None,
    resolver: Optional["ModuleResolver"] = None
) -> tuple[JSNode, ...]:
    """
    Parse a sequence of statements into IR.
    
    WHAT: Parses multiple statements into IR nodes.
    WHY: Convenience function for parsing statement sequences.
    HOW: Calls _parse_statement for each statement.
    WHO: Used when parsing function bodies or other statement sequences.
    WHEN: During parsing phase.
    WHERE: Part of parsing pipeline.
    
    Args:
        stmts: List of Python AST statement nodes
        source: Optional source code for error messages
        resolver: Optional ModuleResolver for imports (Phase 33.3)
    
    Returns:
        Tuple of IR nodes
    """
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    results = []
    for stmt in stmts:
        parsed = _parse_statement(stmt, source, resolver=resolver)
        if isinstance(parsed, list):
            results.extend(parsed)
        else:
            results.append(parsed)
    return tuple(results)


# =============================================================================
# MODULE PARSING
# =============================================================================

def parse_module(
    tree: ast.Module,
    source: Optional[str] = None,
    resolver: Optional["ModuleResolver"] = None
) -> Program:
    """
    Parse a module AST into a Program IR node.
    
    WHAT: Converts Python module AST to Program IR node.
    WHY: Modules are the top-level container for Python code.
    HOW: Parses each statement and collects into Program body.
    WHO: Used by parse() after AST parsing.
    WHEN: During module-level parsing.
    WHERE: Part of parsing pipeline.
    
    Args:
        tree: Python AST Module node
        source: Optional source code for error messages
        resolver: Optional ModuleResolver for import resolution (Phase 33.3)
    
    Returns:
        Program IR node with parsed statements
    """
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    body_parts = []
    for stmt in tree.body:
        parsed = _parse_statement(stmt, source, resolver=resolver)
        # Handle parsers that return multiple nodes (e.g., import statements)
        if isinstance(parsed, list):
            body_parts.extend(parsed)
        else:
            body_parts.append(parsed)
    return Program(body=tuple(body_parts))


# =============================================================================
# STATEMENT PARSING
# =============================================================================

def _parse_statement(
    node: ast.stmt,
    source: Optional[str] = None,
    resolver: Optional["ModuleResolver"] = None
) -> JSNode | list[JSNode]:
    """
    Parse a single statement AST node into IR.
    
    WHAT: Dispatches AST statement nodes to appropriate parsers.
    WHY: Centralizes statement parsing logic.
    HOW: Uses dictionary dispatch to map AST types to parser functions.
    WHO: Used by parse_module() for each statement.
    WHEN: During module parsing.
    WHERE: Part of parsing pipeline.
    
    Args:
        node: AST statement node
        source: Optional source code for error messages
        resolver: Optional ModuleResolver for imports (Phase 33.3)
    
    Returns:
        IR node or list of IR nodes
    """
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    # Map AST types to parser functions
    parsers = {
        ast.Assign: _parse_assign,
        ast.AugAssign: _parse_aug_assign,
        ast.AnnAssign: _parse_ann_assign,
        ast.If: lambda n, s: _parse_if(n, s, resolver),  # Phase 33.3: Pass resolver for TYPE_CHECKING
        ast.For: lambda n, s: _parse_for(n, s, resolver),  # Phase 33.3: Pass resolver for imports in loops
        ast.While: lambda n, s: _parse_while(n, s, resolver),  # Phase 33.3: Pass resolver for imports in loops
        ast.FunctionDef: lambda n, s: _parse_function_def(n, s, resolver),  # Phase 33.3: Pass resolver for imports in functions
        ast.AsyncFunctionDef: lambda n, s: _parse_async_function_def(n, s, resolver),  # Phase 33.3: Pass resolver for imports in async functions
        ast.Return: _parse_return,
        ast.Pass: _parse_pass,
        ast.Break: _parse_break,
        ast.Continue: _parse_continue,
        ast.Delete: _parse_delete,
        ast.Expr: _parse_expr_stmt,
        # Phase 33.2: Context managers
        ast.With: lambda n, s: _parse_with(n, s, resolver),  # Phase 33.3: Pass resolver for imports in with blocks
        ast.AsyncWith: lambda n, s: _parse_async_with(n, s, resolver),  # Phase 33.3: Pass resolver for imports in async with blocks
        # Phase 33.2: Async
        ast.AsyncFor: lambda n, s: _parse_async_for(n, s, resolver),  # Phase 33.3: Pass resolver for imports in async for loops
        ast.Try: lambda n, s: _parse_try(n, s, resolver),  # Phase 33.3: Pass resolver for imports in try blocks
        ast.Raise: _parse_raise,  # Stub for 18.4
        ast.Assert: _parse_assert,  # Stub
        ast.Import: lambda n, s: _parse_import(n, resolver, s),  # Phase 33.3: Pass resolver
        ast.ImportFrom: lambda n, s: _parse_import_from(n, resolver, s),  # Phase 33.3: Pass resolver
        ast.Global: _unsupported_global,
        ast.Nonlocal: _unsupported_nonlocal,
        ast.ClassDef: lambda n, s: _parse_class_def(n, s, resolver),  # Phase 33.3: Pass resolver for imports in classes
    }
    
    # Phase 33.2: Handle Match separately (Python 3.10+)
    if hasattr(ast, "Match") and isinstance(node, ast.Match):
        return _parse_match(node, source, resolver=resolver)
    
    parser = parsers.get(type(node))
    if parser is None:
        raise unsupported(f"{type(node).__name__} statements", node, source)
    
    return parser(node, source)


# =============================================================================
# SIMPLE STATEMENTS
# =============================================================================

def _parse_assign(node: ast.Assign, source: Optional[str] = None) -> JSNode:
    """
    Parse assignment: x = value or a, b = value (tuple unpacking)
    """
    # Handle multiple targets: a = b = 5 (not common, but valid)
    if len(node.targets) > 1:
        # For now, treat as simple assignment to first target
        # Could expand to multiple assignments if needed
        pass
    
    target = node.targets[0]
    value = _parse_expression(node.value, source)
    
    # Tuple unpacking: a, b = pair
    if isinstance(target, ast.Tuple):
        targets, starred_idx = _parse_unpack_targets(target, source)
        return TupleUnpack(
            targets=targets,
            starred_index=starred_idx,
            value=value,
            line=node.lineno,
            col=node.col_offset,
        )
    
    # Simple assignment: x = value
    if isinstance(target, ast.Name):
        return Assignment(
            target=target.id,
            value=value,
            line=node.lineno,
            col=node.col_offset,
        )
    
    # Subscript assignment: items[0] = value
    if isinstance(target, ast.Subscript):
        # This becomes: items[0] = value; (same in JS)
        # We'll handle this as an ExprStmt with a special assignment node
        return ExprStmt(
            value=_parse_subscript_assign(target, value, source),
            line=node.lineno,
            col=node.col_offset,
        )
    
    # Attribute assignment: obj.attr = value
    if isinstance(target, ast.Attribute):
        return ExprStmt(
            value=_parse_attribute_assign(target, value, source),
            line=node.lineno,
            col=node.col_offset,
        )
    
    raise unsupported(f"Assignment to {type(target).__name__}", node, source)


def _parse_unpack_targets(node: ast.Tuple, source: Optional[str] = None) -> tuple[tuple[str, ...], Optional[int]]:
    """
    Extract target names from a tuple unpacking pattern.
    
    Phase 33.2: Supports unpacking to subscripts: arr[j], arr[j + 1] = arr[j + 1], arr[j]
    For subscript targets, we create a special marker that the emitter will handle.
    """
    from .nodes import Subscript
    
    names = []
    starred_index = None
    has_subscripts = False
    
    for i, elt in enumerate(node.elts):
        if isinstance(elt, ast.Name):
            names.append(elt.id)
        elif isinstance(elt, ast.Starred):
            if isinstance(elt.value, ast.Name):
                names.append(elt.value.id)
                starred_index = i
            else:
                raise unsupported("Complex starred target", elt, source)
        elif isinstance(elt, ast.Subscript):
            # Phase 33.2: Support unpacking to subscripts
            # Create a special marker: "__subscript__<index>" that the emitter will handle
            subscript_ir = _parse_expression(elt, source)
            # Store as a tuple (marker, subscript_ir) so emitter can identify it
            names.append(("__subscript__", subscript_ir))
            has_subscripts = True
        else:
            raise unsupported(f"Unpacking to {type(elt).__name__}", elt, source)
    
    # If we have subscripts, we need to handle this specially in the emitter
    # For now, return the names with the subscript markers
    return tuple(names), starred_index


def _parse_subscript_assign(target: ast.Subscript, value: JSNode, source: Optional[str]) -> JSNode:
    """Parse subscript assignment: items[0] = value"""
    # For now, return a BinOp with "assign" operator as placeholder
    # The emitter will handle this specially
    return BinOp(
        left=_parse_expression(target, source),
        op="assign",
        right=value,
        line=target.lineno,
        col=target.col_offset,
    )


def _parse_attribute_assign(target: ast.Attribute, value: JSNode, source: Optional[str]) -> JSNode:
    """Parse attribute assignment: obj.attr = value"""
    return BinOp(
        left=_parse_expression(target, source),
        op="assign",
        right=value,
        line=target.lineno,
        col=target.col_offset,
    )


def _parse_aug_assign(node: ast.AugAssign, source: Optional[str] = None) -> JSNode:
    """
    Parse augmented assignment: x += 1, self.x += 1, etc.
    
    For simple names (x += 1): returns AugAssign node
    For attributes (self.x += 1): transforms to BinOp(self.x, "assign", BinOp(self.x, op, value))
    For subscripts (items[0] += 1): same transformation
    
    Examples:
        x += 1          → AugAssign(target="x", op="add", value=1)
        self.x += 1     → self.x = self.x + 1 (as BinOp with op="assign")
        items[0] += 1   → items[0] = items[0] + 1 (as BinOp with op="assign")
    """
    op_name = type(node.op).__name__
    # Map to our internal op names
    op_map = {
        "Add": "add", "Sub": "sub", "Mult": "mul", "Div": "div",
        "FloorDiv": "floordiv", "Mod": "mod", "Pow": "pow",
        "LShift": "lshift", "RShift": "rshift",
        "BitOr": "bitor", "BitXor": "bitxor", "BitAnd": "bitand",
    }
    op = op_map.get(op_name, "add")
    
    # Simple name: x += 1 → AugAssign
    if isinstance(node.target, ast.Name):
        return AugAssign(
            target=node.target.id,
            op=op,
            value=_parse_expression(node.value, source),
            line=node.lineno,
            col=node.col_offset,
        )
    
    # Attribute: self.x += 1 → self.x = self.x + value
    # Subscript: items[0] += 1 → items[0] = items[0] + value
    if isinstance(node.target, (ast.Attribute, ast.Subscript)):
        target_ir = _parse_expression(node.target, source)
        value_ir = _parse_expression(node.value, source)
        
        # Create BinOp: target op value
        binop = BinOp(
            left=target_ir,
            op=op,
            right=value_ir,
            line=node.lineno,
            col=node.col_offset,
        )
        
        # Create assignment as BinOp with op="assign" (same as attribute assignment)
        assign_binop = BinOp(
            left=target_ir,
            op="assign",
            right=binop,
            line=node.lineno,
            col=node.col_offset,
        )
        
        # Wrap in ExprStmt since it's used as a statement
        return ExprStmt(
            value=assign_binop,
            line=node.lineno,
            col=node.col_offset,
        )
    
    raise unsupported("Augmented assignment to unsupported target", node, source)


def _parse_ann_assign(node: ast.AnnAssign, source: Optional[str] = None) -> JSNode:
    """Parse annotated assignment: x: int = 5"""
    # Type annotations are ignored, just parse as regular assignment
    if node.value is None:
        # Just a type annotation without value: x: int
        return Pass(line=node.lineno, col=node.col_offset)
    
    if isinstance(node.target, ast.Name):
        return Assignment(
            target=node.target.id,
            value=_parse_expression(node.value, source),
            line=node.lineno,
            col=node.col_offset,
        )
    
    raise unsupported("Complex annotated assignment", node, source)


def _parse_return(node: ast.Return, source: Optional[str] = None) -> Return:
    """Parse return statement."""
    value = None
    if node.value is not None:
        value = _parse_expression(node.value, source)
    
    return Return(
        value=value,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_pass(node: ast.Pass, source: Optional[str] = None) -> Pass:
    """Parse pass statement."""
    return Pass(line=node.lineno, col=node.col_offset)


def _parse_break(node: ast.Break, source: Optional[str] = None) -> Break:
    """Parse break statement."""
    return Break(line=node.lineno, col=node.col_offset)


def _parse_continue(node: ast.Continue, source: Optional[str] = None) -> Continue:
    """Parse continue statement."""
    return Continue(line=node.lineno, col=node.col_offset)


def _parse_delete(node: ast.Delete, source: Optional[str] = None) -> Delete:
    """Parse delete statement: del x, del items[0]"""
    # Handle single target for now
    if len(node.targets) != 1:
        raise unsupported("Multiple delete targets", node, source)
    
    target = _parse_expression(node.targets[0], source)
    return Delete(
        target=target,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_expr_stmt(node: ast.Expr, source: Optional[str] = None) -> ExprStmt:
    """Parse expression statement: foo(), print(x)"""
    return ExprStmt(
        value=_parse_expression(node.value, source),
        line=node.lineno,
        col=node.col_offset,
    )


# =============================================================================
# CONTROL FLOW
# =============================================================================

def _parse_if(
    node: ast.If,
    source: Optional[str] = None,
    resolver: Optional["ModuleResolver"] = None
) -> If:
    """
    Parse if/elif/else statement (Phase 33.3: TYPE_CHECKING detection).
    
    WHAT: Parses Python if statements, detecting TYPE_CHECKING blocks.
    WHY: Imports inside `if TYPE_CHECKING:` should be stripped at runtime.
    HOW: Checks if condition is TYPE_CHECKING, marks imports in body.
    WHO: Used by parser when encountering if statements.
    WHEN: During AST parsing phase.
    WHERE: Part of statement parsing.
    
    Args:
        node: AST If node
        source: Optional source code for error messages
        resolver: Optional ModuleResolver for imports (Phase 33.3)
    
    Returns:
        If IR node
    """
    # Phase 33.3: Detect TYPE_CHECKING blocks
    is_type_checking = _is_type_checking_condition(node.test)
    
    # Parse body - mark imports as TYPE_CHECKING if inside TYPE_CHECKING block
    body_statements = []
    for stmt in node.body:
        parsed = _parse_statement(stmt, source, resolver=resolver)
        if isinstance(parsed, list):
            # Multiple nodes (e.g., import statements)
            for p in parsed:
                if isinstance(p, (Import, ImportFrom, ImportStar)) and is_type_checking:
                    # Mark as TYPE_CHECKING import
                    from dataclasses import replace
                    if isinstance(p, Import):
                        p = replace(p, is_type_checking=True)
                    elif isinstance(p, ImportFrom):
                        p = replace(p, is_type_checking=True)
                    elif isinstance(p, ImportStar):
                        p = replace(p, is_type_checking=True)
                body_statements.append(p)
        else:
            if isinstance(parsed, (Import, ImportFrom, ImportStar)) and is_type_checking:
                from dataclasses import replace
                if isinstance(parsed, Import):
                    parsed = replace(parsed, is_type_checking=True)
                elif isinstance(parsed, ImportFrom):
                    parsed = replace(parsed, is_type_checking=True)
                elif isinstance(parsed, ImportStar):
                    parsed = replace(parsed, is_type_checking=True)
            body_statements.append(parsed)
    
    # Parse orelse (elif/else)
    orelse_statements = []
    for stmt in node.orelse:
        parsed = _parse_statement(stmt, source, resolver=resolver)
        if isinstance(parsed, list):
            orelse_statements.extend(parsed)
        else:
            orelse_statements.append(parsed)
    
    return If(
        test=_parse_expression(node.test, source),
        body=tuple(body_statements),
        orelse=tuple(orelse_statements),
        line=node.lineno,
        col=node.col_offset,
    )


def _is_type_checking_condition(node: ast.expr) -> bool:
    """
    Check if an expression is a TYPE_CHECKING condition.
    
    WHAT: Detects `if TYPE_CHECKING:` conditions, including complex expressions.
    WHY: Imports inside TYPE_CHECKING blocks should be stripped at runtime.
    HOW: Recursively checks if expression involves TYPE_CHECKING.
    WHO: Used by _parse_if to detect TYPE_CHECKING blocks.
    WHEN: During if statement parsing.
    WHERE: Part of TYPE_CHECKING detection.
    
    Args:
        node: AST expression node (the if condition)
    
    Returns:
        True if this is a TYPE_CHECKING condition
    
    Examples:
        TYPE_CHECKING → True
        TYPE_CHECKING and True → True
        TYPE_CHECKING or False → True
        not TYPE_CHECKING → False
    """
    if isinstance(node, ast.Name):
        return node.id == "TYPE_CHECKING"
    
    # Handle complex conditions: TYPE_CHECKING and True, TYPE_CHECKING or False, etc.
    if isinstance(node, ast.BoolOp):
        # For AND: if any operand is TYPE_CHECKING, the whole condition is TYPE_CHECKING
        # For OR: if any operand is TYPE_CHECKING, the whole condition is TYPE_CHECKING (short-circuit)
        if isinstance(node.op, ast.And):
            # TYPE_CHECKING and True → TYPE_CHECKING block
            return any(_is_type_checking_condition(value) for value in node.values)
        elif isinstance(node.op, ast.Or):
            # TYPE_CHECKING or False → TYPE_CHECKING block (short-circuit)
            return any(_is_type_checking_condition(value) for value in node.values)
    
    # not TYPE_CHECKING → not a TYPE_CHECKING block
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return False
    
    # Could also check for: from typing import TYPE_CHECKING
    # But for now, just check direct name reference
    return False


def _parse_for(node: ast.For, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> JSNode:
    """Parse for loop."""
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    # Check for range() iteration
    if is_call_to(node.iter, "range"):
        return _parse_for_range(node, source, resolver=resolver)

    # Check for tuple unpacking: for a, b in items
    if isinstance(node.target, ast.Tuple):
        return _parse_for_unpack(node, source, resolver=resolver)

    # Regular for-in loop
    if not isinstance(node.target, ast.Name):
        raise unsupported("Complex for loop target", node, source)

    return For(
        target=node.target.id,
        iter=_parse_expression(node.iter, source),
        body=parse_statements(node.body, source, resolver=resolver),
        orelse=parse_statements(node.orelse, source, resolver=resolver),  # Phase 33.1: for...else
        is_range=False,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_for_unpack(node: ast.For, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> ForUnpack:
    """Parse for loop with tuple unpacking: for a, b in items"""
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    if not isinstance(node.target, ast.Tuple):
        raise unsupported("Expected tuple target for unpacking", node, source)
    
    # Extract target names
    targets = []
    for elt in node.target.elts:
        if isinstance(elt, ast.Name):
            targets.append(elt.id)
        elif isinstance(elt, ast.Starred) and isinstance(elt.value, ast.Name):
            targets.append(f"*{elt.value.id}")
        else:
            raise unsupported("Complex unpack target in for loop", elt, source)
    
    return ForUnpack(
        targets=tuple(targets),
        iter=_parse_expression(node.iter, source),
        body=parse_statements(node.body, source, resolver=resolver),
        orelse=parse_statements(node.orelse, source, resolver=resolver),  # Phase 33.1: for...else
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_for_range(node: ast.For, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> For:
    """Parse for i in range(...) loop."""
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    if not isinstance(node.target, ast.Name):
        raise unsupported("Complex for loop target", node, source)
    
    call = node.iter
    if not isinstance(call, ast.Call):
        raise unsupported("Invalid range call", node, source)
    
    # Parse range arguments
    range_args = tuple(_parse_expression(arg, source) for arg in call.args)
    
    return For(
        target=node.target.id,
        iter=_parse_expression(node.iter, source),
        body=parse_statements(node.body, source, resolver=resolver),
        orelse=parse_statements(node.orelse, source, resolver=resolver),  # Phase 33.1: for...else
        is_range=True,
        range_args=range_args,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_while(node: ast.While, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> While:
    """Parse while loop."""
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    return While(
        test=_parse_expression(node.test, source),
        body=parse_statements(node.body, source, resolver=resolver),
        orelse=parse_statements(node.orelse, source, resolver=resolver),  # Phase 33.1: while...else
        line=node.lineno,
        col=node.col_offset,
    )


# =============================================================================
# FUNCTIONS
# =============================================================================

def _parse_function_def(node: ast.FunctionDef, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> JSNode:
    """
    Parse function definition, optionally with decorators.
    
    Examples:
        def foo(): pass           → FunctionDef
        @memoize                  → DecoratedFunction
        def fib(n): ...
        def varargs(*args): ...   → FunctionDef with vararg
    """
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    parsed_args = _parse_function_args(node.args, source)
    
    func = FunctionDef(
        name=node.name,
        posonly_args=parsed_args['posonly_args'],
        posonly_defaults=parsed_args['posonly_defaults'],
        args=parsed_args['args'],
        defaults=parsed_args['defaults'],
        vararg=parsed_args['vararg'],
        kwarg=parsed_args['kwarg'],
        kwonly_args=parsed_args['kwonly_args'],
        kwonly_defaults=parsed_args['kwonly_defaults'],
        body=parse_statements(node.body, source, resolver=resolver),
        is_async=False,
        line=node.lineno,
        col=node.col_offset,
    )
    
    # Handle decorators if present
    if node.decorator_list:
        decorators = tuple(_parse_decorator(d, source) for d in node.decorator_list)
        return DecoratedFunction(
            decorators=decorators,
            function=func,
            line=node.lineno,
            col=node.col_offset,
        )
    
    return func


def _parse_async_function_def(node: ast.AsyncFunctionDef, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> JSNode:
    """
    Parse async function definition, optionally with decorators (Phase 33.2+).
    
    WHAT: Parses Python async function definitions (async def) into AsyncFunctionDef
          IR nodes. Supports both regular async functions and async generators
          (async def with yield).
    
    WHY: Async functions are a core Python feature for asynchronous programming.
         Async generators enable progressive data loading, real-time streams, and
         chunked processing patterns in client-side code. This function enables
         transpilation of both patterns.
    
    HOW: 
        1. Parses function arguments (including *args, **kwargs, positional-only)
        2. Enters async context for await validation
        3. Parses function body statements
        4. Creates AsyncFunctionDef IR node
        5. Handles decorators if present
    
    WHO: Called by _parse_statement() when it encounters an ast.AsyncFunctionDef
         node in the Python AST.
    
    WHEN: Runs during the parsing phase, before IR transformation and emission.
         This is the first step in transpiling async functions to JavaScript.
    
    WHERE: Part of the parser module, called during AST → IR conversion.
    
    Examples:
        Regular async function:
            Python:                          IR:
            async def fetch():               AsyncFunctionDef(
                return await get_data()          name="fetch",
            )                                   body=(Return(...),)
                                            )
        
        Async generator:
            Python:                          IR:
            async def gen():                 AsyncFunctionDef(
                yield 1                          name="gen",
            )                                   body=(Yield(...),)
                                            )
        
        With decorators:
            Python:                          IR:
            @memoize                         DecoratedFunction(
            async def fetch():                   decorators=(Decorator(...),),
                ...                               function=AsyncFunctionDef(...)
            )                               )
    
    Edge Cases:
        - Nested functions: Yield in nested functions doesn't make the outer
          async function an async generator (handled correctly)
        - Decorators: Multiple decorators are supported
        - Complex arguments: *args, **kwargs, positional-only, keyword-only
        - Empty body: Handled gracefully
    
    Related:
        - async_support.py: _emit_async_function_def() - emits async function*
        - scope.py: declare_async_generator_function() - tracks async generators
        - generators.js: wrapAsyncGenerator() - runtime protocol support
    """
    
    # Parse function arguments (including *args, **kwargs, positional-only, keyword-only)
    parsed_args = _parse_function_args(node.args, source)
    
    # Enter async context for await validation
    # This ensures that 'await' expressions inside the function body are validated
    # correctly (await can only be used inside async functions)
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    _enter_async_context()
    try:
        # Parse all statements in the function body
        # This includes yield/yield from expressions, which are now supported
        # for async generators (async def with yield)
        body = parse_statements(node.body, source, resolver=resolver)
    finally:
        # Always exit async context, even if there's an error
        _exit_async_context()
    
    func = AsyncFunctionDef(
        name=node.name,
        posonly_args=parsed_args.get('posonly_args', ()),
        posonly_defaults=parsed_args.get('posonly_defaults', ()),
        args=parsed_args['args'],
        defaults=parsed_args['defaults'],
        vararg=parsed_args['vararg'],
        kwarg=parsed_args['kwarg'],
        kwonly_args=parsed_args['kwonly_args'],
        kwonly_defaults=parsed_args['kwonly_defaults'],
        body=body,
        decorators=tuple(),
        returns=None,
        line=node.lineno,
        col=node.col_offset,
    )
    
    # Handle decorators if present
    if node.decorator_list:
        decorators = tuple(_parse_decorator(d, source) for d in node.decorator_list)
        return DecoratedFunction(
            decorators=decorators,
            function=func,
            line=node.lineno,
            col=node.col_offset,
        )
    
    return func


def _parse_decorator(node: ast.expr, source: Optional[str] = None) -> Decorator:
    """
    Parse a single decorator.
    
    Examples:
        @memoize           → Decorator(name="memoize", args=())
        @debounce(300)     → Decorator(name="debounce", args=(Constant(300),))
        @log_calls         → Decorator(name="log_calls", args=())
    """
    if isinstance(node, ast.Name):
        # Simple decorator: @memoize
        return Decorator(
            name=node.id,
            args=(),
            kwargs=(),
            line=node.lineno,
            col=node.col_offset,
        )
    elif isinstance(node, ast.Call):
        # Decorator with args: @debounce(300)
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Handle @module.decorator
            name = _get_attribute_chain(node.func)
        else:
            raise unsupported("Complex decorator expression", node, source)
        
        # Parse regular positional args (not starred)
        args = tuple(
            _parse_expression(arg, source) 
            for arg in node.args 
            if not isinstance(arg, ast.Starred)
        )
        
        # Parse starred args (*items)
        starred_args = tuple(
            _parse_expression(arg.value, source)
            for arg in node.args
            if isinstance(arg, ast.Starred)
        )
        
        # Parse named keyword args (key=value)
        kwargs = tuple(
            (kw.arg, _parse_expression(kw.value, source))
            for kw in node.keywords if kw.arg
        )
        
        # Parse double-starred kwargs (**settings)
        double_starred_kwargs = tuple(
            _parse_expression(kw.value, source)
            for kw in node.keywords if kw.arg is None
        )
        
        return Decorator(
            name=name,
            args=args,
            kwargs=kwargs,
            starred_args=starred_args,
            double_starred_kwargs=double_starred_kwargs,
            line=node.lineno,
            col=node.col_offset,
        )
    elif isinstance(node, ast.Attribute):
        # Decorator with attribute: @module.decorator
        name = _get_attribute_chain(node)
        return Decorator(
            name=name,
            args=(),
            kwargs=(),
            line=node.lineno,
            col=node.col_offset,
        )
    else:
        raise unsupported(f"Decorator type {type(node).__name__}", node, source)


def _get_attribute_chain(node: ast.Attribute) -> str:
    """Get dotted name from attribute chain: a.b.c"""
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _parse_function_args(args: ast.arguments, source: Optional[str] = None) -> dict:
    """
    Parse function arguments including *args, **kwargs, and positional-only (Phase 33.1).
    
    Returns a dict with:
        posonly_args: tuple of positional-only arg names (before /)
        posonly_defaults: tuple of positional-only defaults (None for required)
        args: tuple of regular positional arg names (after / but before *)
        defaults: tuple of default values for regular positional args (aligned to end)
        vararg: *args name or None
        kwarg: **kwargs name or None
        kwonly_args: tuple of keyword-only arg names
        kwonly_defaults: tuple of keyword-only defaults (None for required)
    
    Phase 33.1: Properly separate positional-only args from regular positional args.
    JavaScript doesn't have positional-only args, but we track them for:
    1. Runtime validation (optional, can be added later)
    2. Better error messages
    3. Documentation purposes
    """
    # Positional-only args (Python 3.8+, before the /)
    posonly_names = tuple(arg.arg for arg in getattr(args, 'posonlyargs', []))
    
    # Regular positional args (after / but before *)
    regular_names = tuple(arg.arg for arg in args.args)
    
    # Parse defaults - Python's AST stores defaults aligned to the END of all positional args
    # (both positional-only and regular combined)
    # We need to split them between positional-only and regular positional
    all_defaults = tuple(_parse_expression(d, source) for d in args.defaults)
    
    # Combine all positional args to figure out default alignment
    all_pos_args = list(posonly_names) + list(regular_names)
    total_pos_args = len(all_pos_args)
    num_defaults = len(all_defaults)
    num_required = total_pos_args - num_defaults
    
    # Defaults are aligned to the END, so:
    # - defaults[0] belongs to all_pos_args[num_required]
    # - defaults[1] belongs to all_pos_args[num_required + 1]
    # - etc.
    
    # Split defaults into positional-only and regular
    # Defaults are aligned to the END, so we need to figure out which belong to which
    posonly_defaults_list = []
    regular_defaults_list = []
    
    for i, default in enumerate(all_defaults):
        arg_idx = num_required + i  # Index in combined [posonly..., regular...] list
        if arg_idx < len(posonly_names):
            # This default belongs to a positional-only arg
            posonly_defaults_list.append((arg_idx, default))
        else:
            # This default belongs to a regular positional arg
            regular_arg_idx = arg_idx - len(posonly_names)
            regular_defaults_list.append((regular_arg_idx, default))
    
    # Build padded lists: pad with None at the beginning (defaults are at the end)
    posonly_defaults_padded = [None] * len(posonly_names)
    for idx, default in posonly_defaults_list:
        posonly_defaults_padded[idx] = default
    
    regular_defaults_padded = [None] * len(regular_names)
    for idx, default in regular_defaults_list:
        regular_defaults_padded[idx] = default
    
    # *args
    vararg = args.vararg.arg if args.vararg else None
    
    # **kwargs
    kwarg = args.kwarg.arg if args.kwarg else None
    
    # Keyword-only args (after *args or bare *)
    kwonly_args = tuple(arg.arg for arg in args.kwonlyargs)
    
    # Keyword-only defaults (may contain None for required args)
    kwonly_defaults = tuple(
        _parse_expression(d, source) if d else None
        for d in args.kw_defaults
    )
    
    return {
        'posonly_args': posonly_names,
        'posonly_defaults': tuple(posonly_defaults_padded),
        'args': regular_names,
        'defaults': tuple(regular_defaults_padded),
        'vararg': vararg,
        'kwarg': kwarg,
        'kwonly_args': kwonly_args,
        'kwonly_defaults': kwonly_defaults,
    }


# =============================================================================
# EXPRESSIONS
# =============================================================================

def _parse_expression(node: ast.expr, source: Optional[str] = None) -> JSNode:
    """Parse an expression AST node into IR."""
    parsers = {
        ast.Name: _parse_name,
        ast.Constant: _parse_constant,
        ast.Num: _parse_num,  # Python 3.7 compatibility
        ast.Str: _parse_str,  # Python 3.7 compatibility
        ast.NameConstant: _parse_name_constant,  # Python 3.7 compatibility
        ast.BinOp: _parse_binop,
        ast.UnaryOp: _parse_unaryop,
        ast.Compare: _parse_compare,
        ast.BoolOp: _parse_boolop,
        ast.IfExp: _parse_ifexp,
        ast.Call: _parse_call,
        ast.Attribute: _parse_attribute,
        ast.Subscript: _parse_subscript,
        ast.List: _parse_list,
        ast.Dict: _parse_dict,
        ast.Tuple: _parse_tuple,
        ast.Lambda: _parse_lambda,
        ast.Await: _parse_await,
        ast.Starred: _parse_starred,
        # F-strings and Comprehensions
        ast.JoinedStr: _parse_fstring,
        ast.ListComp: _parse_list_comp,
        ast.DictComp: _parse_dict_comp,
        ast.SetComp: _parse_set_comp,
        ast.GeneratorExp: _parse_generator_exp,
        # Walrus operator (Phase 18.8)
        ast.NamedExpr: _parse_named_expr,
        # Phase 33.2: Generators
        ast.Yield: _parse_yield,
        ast.YieldFrom: _parse_yield_from,
    }

    parser = parsers.get(type(node))
    if parser is None:
        raise unsupported(f"{type(node).__name__} expressions", node, source)

    return parser(node, source)


def _parse_name(node: ast.Name, source: Optional[str] = None) -> JSNode:
    """
    Parse variable reference.
    
    FUNDAMENTAL FIX: Transform 'self' → This node when in method context.
    This is the unified semantic context tracking approach - no string replacement needed.
    """
    from .nodes import This
    
    # Check if this is 'self' and we're in a method context
    if node.id == "self":
        scope = get_scope()
        if scope.is_in_method_context():
            return This(line=node.lineno, col=node.col_offset)
    
    return Name(id=node.id, line=node.lineno, col=node.col_offset)


def _parse_constant(node: ast.Constant, source: Optional[str] = None) -> Constant:
    """Parse literal constant."""
    return Constant(value=node.value, line=node.lineno, col=node.col_offset)


# Python 3.7 compatibility
def _parse_num(node, source: Optional[str] = None) -> Constant:
    return Constant(value=node.n, line=node.lineno, col=node.col_offset)

def _parse_str(node, source: Optional[str] = None) -> Constant:
    return Constant(value=node.s, line=node.lineno, col=node.col_offset)

def _parse_name_constant(node, source: Optional[str] = None) -> Constant:
    return Constant(value=node.value, line=node.lineno, col=node.col_offset)


def _parse_binop(node: ast.BinOp, source: Optional[str] = None) -> BinOp:
    """Parse binary operation."""
    op_name = type(node.op).__name__
    op_map = {
        "Add": "add", "Sub": "sub", "Mult": "mul", "Div": "div",
        "FloorDiv": "floordiv", "Mod": "mod", "Pow": "pow",
        "LShift": "lshift", "RShift": "rshift",
        "BitOr": "bitor", "BitXor": "bitxor", "BitAnd": "bitand",
    }
    
    return BinOp(
        left=_parse_expression(node.left, source),
        op=op_map.get(op_name, "add"),
        right=_parse_expression(node.right, source),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_unaryop(node: ast.UnaryOp, source: Optional[str] = None) -> UnaryOp:
    """Parse unary operation."""
    op_name = type(node.op).__name__
    op_map = {"UAdd": "pos", "USub": "neg", "Not": "not", "Invert": "invert"}
    
    return UnaryOp(
        op=op_map.get(op_name, "pos"),
        operand=_parse_expression(node.operand, source),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_compare(node: ast.Compare, source: Optional[str] = None) -> Compare:
    """Parse comparison."""
    op_map = {
        "Eq": "eq", "NotEq": "ne", "Lt": "lt", "LtE": "le",
        "Gt": "gt", "GtE": "ge", "Is": "is", "IsNot": "isnot",
        "In": "in", "NotIn": "notin",
    }
    
    ops = tuple(op_map.get(type(op).__name__, "eq") for op in node.ops)
    comparators = tuple(_parse_expression(c, source) for c in node.comparators)
    
    return Compare(
        left=_parse_expression(node.left, source),
        ops=ops,
        comparators=comparators,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_boolop(node: ast.BoolOp, source: Optional[str] = None) -> BoolOp:
    """Parse boolean operation (and/or)."""
    op = "and" if isinstance(node.op, ast.And) else "or"
    values = tuple(_parse_expression(v, source) for v in node.values)
    
    return BoolOp(
        op=op,
        values=values,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_ifexp(node: ast.IfExp, source: Optional[str] = None) -> IfExp:
    """Parse conditional expression (ternary)."""
    return IfExp(
        test=_parse_expression(node.test, source),
        body=_parse_expression(node.body, source),
        orelse=_parse_expression(node.orelse, source),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_call(node: ast.Call, source: Optional[str] = None) -> Call:
    """Parse function call."""
    args = tuple(_parse_expression(arg, source) for arg in node.args)
    keywords = tuple((kw.arg or "", _parse_expression(kw.value, source)) for kw in node.keywords)
    
    return Call(
        func=_parse_expression(node.func, source),
        args=args,
        keywords=keywords,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_attribute(node: ast.Attribute, source: Optional[str] = None) -> Attribute:
    """Parse attribute access."""
    return Attribute(
        value=_parse_expression(node.value, source),
        attr=node.attr,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_subscript(node: ast.Subscript, source: Optional[str] = None) -> Subscript:
    """Parse subscript access."""
    slice_node = node.slice
    
    # Handle slice vs index
    if isinstance(slice_node, ast.Slice):
        slice_ir = _parse_slice(slice_node, source)
    else:
        slice_ir = _parse_expression(slice_node, source)
    
    # Check if index might be negative (for runtime call)
    is_negative = _might_be_negative(slice_node)
    
    return Subscript(
        value=_parse_expression(node.value, source),
        slice=slice_ir,
        is_negative=is_negative,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_slice(node: ast.Slice, source: Optional[str] = None) -> Slice:
    """Parse slice specification."""
    lower = _parse_expression(node.lower, source) if node.lower else None
    upper = _parse_expression(node.upper, source) if node.upper else None
    step = _parse_expression(node.step, source) if node.step else None
    
    return Slice(
        lower=lower,
        upper=upper,
        step=step,
        line=getattr(node, "lineno", 0),
        col=getattr(node, "col_offset", 0),
    )


def _might_be_negative(node) -> bool:
    """
    Check if an index expression might be negative.
    
    Returns True if the expression could evaluate to a negative number,
    which means we need to use __py.at() for Python negative indexing.
    
    Examples:
        items[0]        → False (known positive)
        items[-1]       → True (known negative)
        items[i]        → True (variable, could be negative)
        items[len(x)-1] → True (expression, could be negative)
        items[func()]   → True (function call, could return negative)
    """
    # Known positive literal
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value < 0
    
    # Unary minus: -x
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return True
    
    # Variables: could be negative
    if isinstance(node, ast.Name):
        return True
    
    # Binary operations: a + b, len(x) - 1, etc.
    if isinstance(node, ast.BinOp):
        return True
    
    # Function calls: func() could return any value
    if isinstance(node, ast.Call):
        return True
    
    # Subscript: items[i][j] - inner index result could be negative
    if isinstance(node, ast.Subscript):
        return True
    
    # Attribute access: obj.index - could be negative
    if isinstance(node, ast.Attribute):
        return True
    
    # Default: assume could be negative (safe)
    return True


def _parse_list(node: ast.List, source: Optional[str] = None) -> List:
    """Parse list literal."""
    elts = tuple(_parse_expression(elt, source) for elt in node.elts)
    return List(elts=elts, line=node.lineno, col=node.col_offset)


def _parse_dict(node: ast.Dict, source: Optional[str] = None) -> Dict:
    """Parse dict literal."""
    keys = tuple(
        _parse_expression(k, source) if k is not None else None
        for k in node.keys
    )
    values = tuple(_parse_expression(v, source) for v in node.values)
    return Dict(keys=keys, values=values, line=node.lineno, col=node.col_offset)


def _parse_tuple(node: ast.Tuple, source: Optional[str] = None) -> Tuple:
    """Parse tuple literal."""
    elts = tuple(_parse_expression(elt, source) for elt in node.elts)
    return Tuple(elts=elts, line=node.lineno, col=node.col_offset)


def _parse_lambda(node: ast.Lambda, source: Optional[str] = None) -> Lambda:
    """
    Parse lambda expression.
    
    Phase 33.1: Enhanced to support *args, **kwargs, and default arguments.
    Note: Lambdas don't support positional-only or keyword-only args in Python.
    """
    # Regular positional args
    args = tuple(arg.arg for arg in node.args.args)
    defaults = tuple(_parse_expression(d, source) for d in node.args.defaults)
    
    # *args
    vararg = node.args.vararg.arg if node.args.vararg else None
    
    # **kwargs
    kwarg = node.args.kwarg.arg if node.args.kwarg else None
    
    # Note: Lambdas don't support posonlyargs or kwonlyargs in Python
    
    return Lambda(
        args=args,
        defaults=defaults,
        vararg=vararg,
        kwarg=kwarg,
        body=_parse_expression(node.body, source),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_await(node: ast.Await, source: Optional[str] = None) -> Await:
    """
    Parse await expression: await expr
    
    Validates that await is only used inside async functions.
    
    Examples:
        await fetch(url)        → Await(value=Call(...))
        await response.json()   → Await(value=Call(Attribute(...)))
    
    Raises:
        UnsupportedSyntax: If await is used outside an async function
    """
    if not _is_in_async_context():
        raise unsupported(
            "'await' outside async function",
            node,
            source,
            "The 'await' keyword can only be used inside an 'async def' function.\n\n"
            "Change your function to async:\n"
            "    async def handle_click():\n"
            "        result = await fetch_data()\n\n"
            "Or use a callback pattern instead."
        )
    
    return Await(
        value=_parse_expression(node.value, source),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_starred(node: ast.Starred, source: Optional[str] = None) -> Starred:
    """Parse starred expression."""
    return Starred(
        value=_parse_expression(node.value, source),
        line=node.lineno,
        col=node.col_offset,
    )


# =============================================================================
# F-STRINGS
# =============================================================================

def _parse_fstring(node: ast.JoinedStr, source: Optional[str] = None) -> FString:
    """
    Parse f-string: f"Hello {name}" or f"{x:.2f}" or f"{obj!r}"
    
    Python AST represents f-strings as JoinedStr with values being:
    - ast.Constant for literal string parts
    - ast.FormattedValue for {expr} parts
    
    Conversion characters (!s, !r, !a):
    - !s = str() - convert to string
    - !r = repr() - convert to repr
    - !a = ascii() - convert to ASCII repr
    """
    parts = []
    format_specs = []
    conversions = []
    
    for value in node.values:
        if isinstance(value, ast.Constant):
            # Literal string part
            parts.append(str(value.value))
        elif isinstance(value, ast.FormattedValue):
            # {expr} or {expr:spec} part
            expr = _parse_expression(value.value, source)
            parts.append(expr)
            
            # Get format spec if present
            if value.format_spec is not None and isinstance(value.format_spec, ast.JoinedStr):
                # Format spec is also a JoinedStr (can contain expressions)
                spec_parts = []
                for spec_val in value.format_spec.values:
                    if isinstance(spec_val, ast.Constant):
                        spec_parts.append(str(spec_val.value))
                    else:
                        # Dynamic format spec - emit the expression
                        spec_parts.append(f"${{{_parse_expression(spec_val, source)}}}")
                format_specs.append("".join(spec_parts))
            else:
                format_specs.append("")
            
            # Handle conversion (!s, !r, !a)
            # value.conversion: -1 = none, 115 = s, 114 = r, 97 = a
            if value.conversion == 115:  # ord('s')
                conversions.append('s')
            elif value.conversion == 114:  # ord('r')
                conversions.append('r')
            elif value.conversion == 97:  # ord('a')
                conversions.append('a')
            else:
                conversions.append('')
        else:
            # Fallback
            parts.append("")
    
    return FString(
        parts=tuple(parts),
        format_specs=tuple(format_specs),
        conversions=tuple(conversions),
        line=node.lineno,
        col=node.col_offset,
    )


# =============================================================================
# COMPREHENSIONS
# =============================================================================

def _parse_comprehension(comp: ast.comprehension, source: Optional[str] = None) -> Comprehension:
    """Parse a single comprehension clause: for x in items if cond"""
    # Handle simple target (single variable)
    if isinstance(comp.target, ast.Name):
        target = comp.target.id
        targets = ()
    elif isinstance(comp.target, ast.Tuple):
        # Tuple unpacking: for k, v in items
        target = ""
        targets = tuple(
            elt.id if isinstance(elt, ast.Name) else "_"
            for elt in comp.target.elts
        )
    else:
        target = "_"
        targets = ()
    
    # Parse conditions
    ifs = tuple(_parse_expression(if_clause, source) for if_clause in comp.ifs)
    
    return Comprehension(
        target=target,
        targets=targets,
        iter=_parse_expression(comp.iter, source),
        ifs=ifs,
    )


def _parse_list_comp(node: ast.ListComp, source: Optional[str] = None) -> ListComp:
    """
    Parse list comprehension: [x*2 for x in items if x > 0]
    """
    return ListComp(
        element=_parse_expression(node.elt, source),
        generators=tuple(_parse_comprehension(gen, source) for gen in node.generators),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_dict_comp(node: ast.DictComp, source: Optional[str] = None) -> DictComp:
    """
    Parse dict comprehension: {k: v for k, v in items}
    """
    return DictComp(
        key=_parse_expression(node.key, source),
        value=_parse_expression(node.value, source),
        generators=tuple(_parse_comprehension(gen, source) for gen in node.generators),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_set_comp(node: ast.SetComp, source: Optional[str] = None) -> SetComp:
    """
    Parse set comprehension: {x for x in items}
    """
    return SetComp(
        element=_parse_expression(node.elt, source),
        generators=tuple(_parse_comprehension(gen, source) for gen in node.generators),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_generator_exp(node: ast.GeneratorExp, source: Optional[str] = None) -> GeneratorExp:
    """
    Parse generator expression: (x for x in items)
    """
    return GeneratorExp(
        element=_parse_expression(node.elt, source),
        generators=tuple(_parse_comprehension(gen, source) for gen in node.generators),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_named_expr(node: ast.NamedExpr, source: Optional[str] = None) -> NamedExpr:
    """
    Parse walrus operator: (x := value)
    
    The walrus operator allows assignment as an expression.
    
    Examples:
        if (x := get_value()):      → NamedExpr(target="x", value=Call(...))
        while (line := read()):     → NamedExpr(target="line", value=Call(...))
        [y for x in items if (y := f(x))]
    
    The emitter will pre-declare the variable and use assignment expression.
    """
    return NamedExpr(
        target=node.target.id,
        value=_parse_expression(node.value, source),
        line=node.lineno,
        col=node.col_offset,
    )


# =============================================================================
# STUBS AND UNSUPPORTED
# =============================================================================

def _parse_try(node: ast.Try, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> "Try":
    """
    Parse try/except/else/finally statement.
    
    Examples:
        try:
            risky()
        except ValueError as e:
            handle(e)
        else:
            success()
        finally:
            cleanup()
    
    JavaScript output:
        try {
            risky();
        } catch (_e) {
            if (_e instanceof ValueError) { let e = _e; handle(e); }
        } finally {
            cleanup();
        }
    """
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    from .nodes import Try, ExceptHandler
    
    # Parse try body
    body = parse_statements(node.body, source, resolver=resolver)
    
    # Parse exception handlers
    handlers = []
    for handler in node.handlers:
        handler_type = None
        if handler.type:
            if isinstance(handler.type, ast.Name):
                handler_type = handler.type.id
            elif isinstance(handler.type, ast.Attribute):
                # Module.Exception pattern
                parts = []
                curr = handler.type
                while isinstance(curr, ast.Attribute):
                    parts.append(curr.attr)
                    curr = curr.value
                if isinstance(curr, ast.Name):
                    parts.append(curr.id)
                handler_type = ".".join(reversed(parts))
        
        handler_body = parse_statements(handler.body, source, resolver=resolver)
        
        handlers.append(ExceptHandler(
            type=handler_type,
            name=handler.name,
            body=handler_body,
            line=handler.lineno if hasattr(handler, 'lineno') else node.lineno,
            col=handler.col_offset if hasattr(handler, 'col_offset') else node.col_offset,
        ))
    
    # Parse else block (runs if no exception)
    orelse = parse_statements(node.orelse, source, resolver=resolver)
    
    # Parse finally block
    finalbody = parse_statements(node.finalbody, source, resolver=resolver)
    
    return Try(
        body=body,
        handlers=tuple(handlers),
        orelse=orelse,
        finalbody=finalbody,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_raise(node: ast.Raise, source: Optional[str] = None) -> "ExprStmt":
    """
    Parse raise statement (Phase 33.3: supports exception chaining).
    
    WHAT: Parses Python raise statements, including exception chaining.
    WHY: Enables proper exception handling and chaining in transpiled code.
    HOW: Creates ExprStmt with __throw__ call, including cause if present.
    WHO: Used by transpiler when parsing raise statements.
    WHEN: When Python code contains raise statements.
    WHERE: Part of statement parsing in parser.py.
    
    Examples:
        raise ValueError("msg")           → throw new ValueError("msg");
        raise e                            → throw e;
        raise                              → throw _e;  (re-raise current exception)
        raise ValueError("msg") from e    → const _exc = new ValueError("msg"); _exc.__cause__ = e; throw _exc;
    """
    from .nodes import ExprStmt, Call, Name, Attribute, Constant
    
    if node.exc is None:
        # Bare raise - re-raise current exception
        # This only makes sense inside an except handler
        # We'll emit: throw _e; (the caught exception variable)
        return ExprStmt(
            value=Name(id="__raise__"),  # Special marker for re-raise
            line=node.lineno,
            col=node.col_offset,
        )
    
    exc = _parse_expression(node.exc, source)
    
    # Phase 33.3: Handle exception chaining (raise ... from ...)
    if node.cause is not None:
        # raise ValueError("msg") from e
        # We need to:
        # 1. Create the exception
        # 2. Set __cause__ attribute
        # 3. Throw it
        # Emitter will handle this as: const _exc = ...; _exc.__cause__ = ...; throw _exc;
        cause = _parse_expression(node.cause, source)
        return ExprStmt(
            value=Call(
                func=Name(id="__throw_from__"),  # Special marker for raise ... from ...
                args=(exc, cause),
            ),
            line=node.lineno,
            col=node.col_offset,
        )
    
    # Regular raise without chaining
    # Wrap in a "throw" marker - emitter will handle this
    return ExprStmt(
        value=Call(
            func=Name(id="__throw__"),
            args=(exc,),
        ),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_assert(node: ast.Assert, source: Optional[str] = None) -> Assert:
    """
    Parse assert statement: assert condition, message
    
    Examples:
        assert x > 0              → Assert(test=Compare(...), msg=None)
        assert x > 0, "message"   → Assert(test=Compare(...), msg=Constant("message"))
    """
    return Assert(
        test=_parse_expression(node.test, source),
        msg=_parse_expression(node.msg, source) if node.msg else None,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_class_def(node: ast.ClassDef, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> ClassDef:
    """
    Parse class definition into ClassDef IR node.
    
    Supports:
    - Single inheritance (one base class)
    - __init__ → constructor
    - Instance methods (strips 'self')
    - @property → getters
    - @staticmethod → static methods
    - async methods
    
    Rejects with helpful errors:
    - Multiple inheritance
    - @classmethod
    - Metaclasses
    - __slots__
    """
    # Phase 33.1: Support multiple inheritance via mixin pattern
    # First base is the primary (extends), rest are mixins whose methods are copied
    # JavaScript only supports single inheritance, so we use a runtime mixin helper
    
    # Check for metaclass
    for keyword in node.keywords:
        if keyword.arg == "metaclass":
            raise UnsupportedSyntax(
                message="Metaclasses are not supported for client-side classes.",
                line=node.lineno,
                col=node.col_offset,
                source=source,
                suggestion="Use @server_action for complex class patterns that require metaclasses.",
            )
    
    # Phase 33.1: Parse base classes - first is primary (extends), rest are mixins
    bases = []
    mixins = []
    for base in node.bases:
        base_name = base.id if isinstance(base, ast.Name) else str(ast.dump(base))
        if len(bases) == 0:
            # First base is the primary (extends)
            bases.append(base_name)
        else:
            # Additional bases are mixins
            mixins.append(base_name)
    
    bases = tuple(bases)
    mixins = tuple(mixins)
    
    # Parse class decorators (limited support)
    decorators = tuple(_parse_decorator(d, source) for d in node.decorator_list)
    
    # Phase 33.1: Detect @dataclass decorator
    is_dataclass = False
    for d in node.decorator_list:
        if isinstance(d, ast.Name) and d.id == "dataclass":
            is_dataclass = True
            break
        elif isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass":
            # @dataclass() or @dataclass(frozen=True) etc.
            is_dataclass = True
            break
    
    # Phase 33.1: Detect ABC base class (abstract class)
    is_abstract = "ABC" in bases or "ABC" in mixins
    
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    # FUNDAMENTAL FIX: Track class context for semantic context tracking
    scope = get_scope()
    scope.enter_context(ClassContext(class_name=node.name))
    try:
        # Parse class body
        body = []
        dataclass_fields = []
        abstract_methods = []
        
        for stmt in node.body:
            # Phase 33.1: Parse annotated assignments as dataclass fields
            if is_dataclass and isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                type_hint = ast.unparse(stmt.annotation) if stmt.annotation else "Any"
                default_value = _parse_expression(stmt.value, source) if stmt.value else None
                dataclass_fields.append((field_name, type_hint, default_value))
                continue
            
            parsed = _parse_class_body_item(stmt, source, class_name=node.name, resolver=resolver)
            if parsed is not None:
                body.append(parsed)
                # Phase 33.1: Collect abstract method names
                if isinstance(parsed, MethodDef) and parsed.is_abstract:
                    abstract_methods.append(parsed.name)
    finally:
        scope.exit_context()
    
    # Phase 33.2: Check if class has __call__ method
    has_call_method = any(
        isinstance(item, DunderMethod) and item.name == "__call__"
        for item in body
    )
    
    return ClassDef(
        name=node.name,
        bases=bases,
        mixins=mixins,  # Phase 33.1
        body=tuple(body),
        decorators=decorators,
        is_dataclass=is_dataclass,
        dataclass_fields=tuple(dataclass_fields),
        is_abstract=is_abstract,
        abstract_methods=tuple(abstract_methods),  # Phase 33.1
        has_call_method=has_call_method,  # Phase 33.2
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_class_body_item(node: ast.stmt, source: Optional[str] = None, class_name: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> Optional[JSNode]:
    """
    Parse a single item in a class body.
    
    Returns MethodDef, PropertyDef, or None for docstrings/pass.
    
    Args:
        class_name: Name of the class (for context tracking)
        resolver: ModuleResolver for imports (Phase 33.3)
    """
    # Skip docstrings
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        return None
    
    # Skip pass statements
    if isinstance(node, ast.Pass):
        return None
    
    # Check for __slots__ (not supported)
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__slots__":
                raise UnsupportedSyntax(
                    message="__slots__ is not supported for client-side classes.",
                    line=node.lineno,
                    col=node.col_offset,
                    source=source,
                    suggestion="Remove __slots__. JavaScript classes don't have this optimization.",
                )
        # Skip class-level assignments (class variables)
        # Could emit as static properties in future
        return None
    
    # Function definition (method, property, staticmethod)
    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        # Phase 33.2: Check if this is a dunder method
        dunder_type = _get_dunder_type(node.name)
        if dunder_type is not None:
            return _parse_dunder_method(node, dunder_type, source, class_name=class_name, resolver=resolver)
        return _parse_method_def(node, source, class_name=class_name, resolver=resolver)
    
    # Skip other statements with warning
    return None


def _get_dunder_type(method_name: str) -> Optional[str]:
    """
    Determine the type of dunder method for optimization purposes.
    
    Returns:
        - "string" for __str__, __repr__, __format__
        - "comparison" for __eq__, __ne__, __lt__, __gt__, __le__, __ge__
        - "container" for __len__, __bool__, __iter__, __next__, __contains__, __getitem__, __setitem__, __delitem__
        - "arithmetic" for __add__, __sub__, __mul__, __truediv__, __radd__, etc.
        - "callable" for __call__
        - "attribute" for __getattr__, __setattr__, __delattr__
        - None if not a dunder method
    """
    # Phase 33.2: Dunder method detection
    if not (method_name.startswith("__") and method_name.endswith("__")):
        return None
    
    string_dunders = {"__str__", "__repr__", "__format__"}
    comparison_dunders = {"__eq__", "__ne__", "__lt__", "__gt__", "__le__", "__ge__"}
    container_dunders = {"__len__", "__bool__", "__iter__", "__next__", "__contains__", 
                         "__getitem__", "__setitem__", "__delitem__"}
    arithmetic_dunders = {"__add__", "__sub__", "__mul__", "__truediv__", "__floordiv__", "__mod__", "__pow__",
                          "__radd__", "__rsub__", "__rmul__", "__rtruediv__", "__rfloordiv__", "__rmod__", "__rpow__",
                          "__iadd__", "__isub__", "__imul__", "__itruediv__", "__ifloordiv__", "__imod__", "__ipow__",
                          "__neg__", "__pos__", "__abs__", "__invert__"}
    callable_dunders = {"__call__"}
    attribute_dunders = {"__getattr__", "__setattr__", "__delattr__"}
    # Phase 33.2: Context manager dunders
    context_dunders = {"__enter__", "__exit__", "__aenter__", "__aexit__"}
    
    if method_name in string_dunders:
        return "string"
    elif method_name in comparison_dunders:
        return "comparison"
    elif method_name in container_dunders:
        return "container"
    elif method_name in arithmetic_dunders:
        return "arithmetic"
    elif method_name in callable_dunders:
        return "callable"
    elif method_name in attribute_dunders:
        return "attribute"
    elif method_name in context_dunders:
        # Context manager dunders are treated as generic dunder methods
        # They need self → this replacement but no special transpilation
        return "context"
    
    return None


def _parse_method_def(node, source: Optional[str] = None, class_name: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> JSNode:
    """
    Parse a method definition within a class.
    
    Handles:
    - Regular methods (strips 'self')
    - @staticmethod
    - @property
    - @classmethod (error with suggestion)
    - async methods
    - Phase 33.2: Dunder methods (__str__, __eq__, etc.)
    
    Args:
        class_name: Name of the class (for context tracking)
    """
    is_async = isinstance(node, ast.AsyncFunctionDef)
    is_static = False
    is_classmethod = False  # Phase 33.1
    is_abstract = False  # Phase 33.1
    is_property = False
    
    # Check decorators
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name):
            if decorator.id == "staticmethod":
                is_static = True
            elif decorator.id == "property":
                is_property = True
            elif decorator.id == "classmethod":
                # Phase 33.1: Support @classmethod
                # In JS, classmethod is emitted as static with 'cls' bound to constructor
                is_classmethod = True
            elif decorator.id == "abstractmethod":
                # Phase 33.1: Support @abstractmethod
                is_abstract = True
        elif isinstance(decorator, ast.Attribute):
            # Check for @property_name.setter
            if isinstance(decorator.value, ast.Name) and decorator.attr == "setter":
                # This is a property setter
                return _parse_property_setter(node, decorator.value.id, source, class_name=class_name, resolver=resolver)
            # Phase 33.1: Check for @property_name.deleter
            elif isinstance(decorator.value, ast.Name) and decorator.attr == "deleter":
                # This is a property deleter
                return _parse_property_deleter(node, decorator.value.id, source, class_name=class_name, resolver=resolver)
    
    # Phase 33.2: Check if this is a dunder method
    dunder_type = _get_dunder_type(node.name)
    if dunder_type is not None:
        # Parse as dunder method
        return _parse_dunder_method(node, dunder_type, source, class_name=class_name, resolver=resolver)
    
    # Get method name (convert __init__ to constructor)
    method_name = node.name
    if method_name == "__init__":
        method_name = "constructor"
    
    # Phase 33.1: Detect private methods and name mangling
    is_private = method_name.startswith("_") and not method_name.startswith("__")
    is_mangled = method_name.startswith("__") and not method_name.endswith("__") and method_name != "__init__"
    
    # Parse arguments using the same logic as functions (Phase 33.1: support *args, **kwargs)
    parsed_args = _parse_function_args(node.args, source)
    
    # Strip 'self' or 'cls' from regular args for instance/class methods
    args = []
    defaults = []
    all_pos_args = list(parsed_args['posonly_args']) + list(parsed_args['args'])
    
    for i, arg in enumerate(all_pos_args):
        # Skip 'self' or 'cls' for instance/class methods (only first arg)
        if i == 0 and arg in ("self", "cls") and not is_static:
            continue
        args.append(arg)
    
    # Adjust defaults to match stripped args
    # Defaults are aligned to the end, so we need to figure out which ones to keep
    all_defaults = list(parsed_args['posonly_defaults']) + list(parsed_args['defaults'])
    num_stripped = len(all_pos_args) - len(args)  # Usually 1 if we stripped self/cls
    
    if num_stripped > 0 and all_defaults:
        # If we stripped self/cls from the beginning, we need to remove the corresponding defaults
        # Defaults are aligned to the end, so we remove from the beginning
        defaults = all_defaults[num_stripped:]
    else:
        defaults = all_defaults
    
    # Filter out None padding - only keep actual default values
    # Defaults are aligned to the end, so None values at the start are padding
    # We should only include defaults that are not None
    actual_defaults = [d for d in defaults if d is not None]
    defaults = tuple(actual_defaults) if actual_defaults else ()
    
    # FUNDAMENTAL FIX: Track method context for self → this transformation
    scope = get_scope()
    if class_name and not is_static:
        # Only track method context for instance methods (not static methods)
        scope.enter_context(MethodContext(class_name=class_name, method_name=node.name))
    try:
        # Phase 33.3: Create resolver if not provided (for backward compatibility)
        if resolver is None:
            from ._internal.module_resolver import ModuleResolver
            resolver = ModuleResolver(current_file="<string>")
        
        # Parse body - enter async context if async method
        if is_async:
            _enter_async_context()
        try:
            body = parse_statements(node.body, source, resolver=resolver)
        finally:
            if is_async:
                _exit_async_context()
    finally:
        if class_name and not is_static:
            scope.exit_context()
    
    # Return PropertyDef for @property
    if is_property:
        return PropertyDef(
            name=node.name,
            body=body,
            line=node.lineno,
            col=node.col_offset,
        )
    
    # Return MethodDef for methods
    return MethodDef(
        name=method_name,
        args=tuple(args),
        defaults=tuple(defaults),
        vararg=parsed_args['vararg'],  # Phase 33.1: *args support
        kwarg=parsed_args['kwarg'],  # Phase 33.1: **kwargs support
        kwonly_args=parsed_args['kwonly_args'],  # Phase 33.1: Keyword-only args
        kwonly_defaults=parsed_args['kwonly_defaults'],  # Phase 33.1: Keyword-only defaults
        body=body,
        is_static=is_static,
        is_classmethod=is_classmethod,  # Phase 33.1
        is_abstract=is_abstract,  # Phase 33.1
        is_async=is_async,
        is_private=is_private,  # Phase 33.1
        is_mangled=is_mangled,  # Phase 33.1
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_dunder_method(node, dunder_type: str, source: Optional[str] = None, class_name: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> DunderMethod:
    """
    Parse a dunder method definition (Phase 33.2).
    
    Dunder methods are special methods like __str__, __eq__, __iter__, etc.
    They are parsed separately from regular methods to enable special transpilation.
    
    Args:
        node: AST function definition node (FunctionDef or AsyncFunctionDef)
        dunder_type: Type of dunder method ("string", "comparison", "container", "arithmetic", "callable", "attribute", "context")
        source: Optional source code for error messages
        class_name: Name of the class (for context tracking)
    
    Returns:
        DunderMethod IR node
    """
    # Phase 33.2: Handle async dunder methods (e.g., __aenter__, __aexit__)
    is_async = isinstance(node, ast.AsyncFunctionDef)
    
    # Parse arguments (dunder methods typically have 'self' and sometimes one other arg)
    parsed_args = _parse_function_args(node.args, source)
    
    # Strip 'self' from args (dunder methods are instance methods)
    args = []
    defaults = []
    all_pos_args = list(parsed_args['posonly_args']) + list(parsed_args['args'])
    
    for i, arg in enumerate(all_pos_args):
        # Skip 'self' (first arg for instance methods)
        if i == 0 and arg == "self":
            continue
        args.append(arg)
    
    # Adjust defaults to match stripped args
    all_defaults = list(parsed_args['posonly_defaults']) + list(parsed_args['defaults'])
    num_stripped = len(all_pos_args) - len(args)  # Usually 1 if we stripped self
    
    if num_stripped > 0 and all_defaults:
        defaults = all_defaults[num_stripped:]
    else:
        defaults = all_defaults
    
    # Filter out None padding
    actual_defaults = [d for d in defaults if d is not None]
    defaults = tuple(actual_defaults) if actual_defaults else ()
    
    # FUNDAMENTAL FIX: Track method context for self → this transformation
    scope = get_scope()
    if class_name:
        scope.enter_context(MethodContext(class_name=class_name, method_name=node.name))
    try:
        # Phase 33.3: Create resolver if not provided (for backward compatibility)
        if resolver is None:
            from ._internal.module_resolver import ModuleResolver
            resolver = ModuleResolver(current_file="<string>")
        
        # Parse body - enter async context if async dunder method
        if is_async:
            _enter_async_context()
        try:
            body = parse_statements(node.body, source, resolver=resolver)
        finally:
            if is_async:
                _exit_async_context()
    finally:
        if class_name:
            scope.exit_context()
    
    return DunderMethod(
        name=node.name,  # Keep original name (e.g., "__str__")
        args=tuple(args),
        defaults=defaults,
        body=body,
        dunder_type=dunder_type,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_property_deleter(node, property_name: str, source: Optional[str] = None, class_name: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> "PropertyDeleterDef":
    """
    Parse a property deleter definition - Phase 33.1.
    
    Example:
        @value.deleter
        def value(self):
            del self._value
    
    Returns PropertyDeleterDef node.
    
    Args:
        class_name: Name of the class (for context tracking)
    """
    from .nodes import PropertyDeleterDef
    
    # FUNDAMENTAL FIX: Track method context for self → this transformation
    scope = get_scope()
    if class_name:
        scope.enter_context(MethodContext(class_name=class_name, method_name=property_name))
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    try:
        # Parse body (strip 'self' parameter)
        body = parse_statements(node.body, source, resolver=resolver)
    finally:
        if class_name:
            scope.exit_context()
    
    return PropertyDeleterDef(
        name=property_name,
        body=body,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_property_setter(node, property_name: str, source: Optional[str] = None, class_name: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> PropertySetterDef:
    """
    Parse a property setter definition.
    
    Example:
        @value.setter
        def value(self, val):
            self._value = val
    
    Returns PropertySetterDef node.
    
    Args:
        class_name: Name of the class (for context tracking)
    """
    # Get the setter argument (second parameter after self)
    all_args = node.args.args
    if len(all_args) < 2:
        raise UnsupportedSyntax(
            message="Property setter must have exactly one argument (besides self).",
            line=node.lineno,
            col=node.col_offset,
            source=source,
        )
    
    # First arg is self, second is the value arg
    setter_arg = all_args[1].arg
    
    # FUNDAMENTAL FIX: Track method context for self → this transformation
    scope = get_scope()
    if class_name:
        scope.enter_context(MethodContext(class_name=class_name, method_name=property_name))
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    try:
        # Parse body
        body = parse_statements(node.body, source, resolver=resolver)
    finally:
        if class_name:
            scope.exit_context()
    
    return PropertySetterDef(
        name=property_name,
        arg=setter_arg,
        body=body,
        line=node.lineno,
        col=node.col_offset,
    )


def _unsupported_with(node, source: Optional[str] = None):
    raise unsupported("with statements", node, source, 
                      "Use @server_action for context managers")


def _unsupported_async_with(node, source: Optional[str] = None):
    raise unsupported("async with statements", node, source,
                      get_suggestion("async_with"))


# =============================================================================
# PHASE 33.2: GENERATORS
# =============================================================================

def _parse_yield(node: ast.Yield, source: Optional[str] = None) -> Yield:
    """
    Parse yield expression (Phase 33.2).
    
    Examples:
        yield value     → Yield(value=...)
        yield           → Yield(value=None)
    """
    value = None
    if node.value is not None:
        value = _parse_expression(node.value, source)
    
    return Yield(
        value=value,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_yield_from(node: ast.YieldFrom, source: Optional[str] = None) -> YieldFrom:
    """
    Parse yield from expression (Phase 33.2).
    
    Examples:
        yield from gen  → YieldFrom(value=...)
    """
    return YieldFrom(
        value=_parse_expression(node.value, source),
        line=node.lineno,
        col=node.col_offset,
    )


# =============================================================================
# PHASE 33.2: CONTEXT MANAGERS
# =============================================================================

def _parse_with(node: ast.With, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> With:
    """
    Parse with statement (Phase 33.2).
    
    Examples:
        with resource() as r:     → With(items=[WithItem(...)], body=[...])
            use(r)
        
        with r1() as a, r2() as b: → With(items=[WithItem(...), WithItem(...)], body=[...])
            process(a, b)
    """
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    items = []
    for item in node.items:
        context_expr = _parse_expression(item.context_expr, source)
        optional_vars = None
        
        if item.optional_vars:
            if isinstance(item.optional_vars, ast.Name):
                optional_vars = item.optional_vars.id
            elif isinstance(item.optional_vars, ast.Tuple):
                # Multiple variables: with ctx() as (a, b):
                optional_vars = tuple(name.id for name in item.optional_vars.elts if isinstance(name, ast.Name))
        
        items.append(WithItem(
            context_expr=context_expr,
            optional_vars=optional_vars,
            is_async=False,
            line=item.lineno if hasattr(item, 'lineno') else node.lineno,
            col=item.col_offset if hasattr(item, 'col_offset') else node.col_offset,
        ))
    
    body = parse_statements(node.body, source, resolver=resolver)
    orelse = parse_statements(node.orelse, source, resolver=resolver) if hasattr(node, 'orelse') and node.orelse else tuple()
    
    return With(
        items=tuple(items),
        body=body,
        orelse=orelse,
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_async_with(node: ast.AsyncWith, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> With:
    """
    Parse async with statement (Phase 33.2).
    
    Examples:
        async with resource() as r:  → With(items=[WithItem(..., is_async=True)], body=[...])
            await use(r)
    """
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    items = []
    for item in node.items:
        context_expr = _parse_expression(item.context_expr, source)
        optional_vars = None
        
        if item.optional_vars:
            if isinstance(item.optional_vars, ast.Name):
                optional_vars = item.optional_vars.id
            elif isinstance(item.optional_vars, ast.Tuple):
                optional_vars = tuple(name.id for name in item.optional_vars.elts if isinstance(name, ast.Name))
        
        items.append(WithItem(
            context_expr=context_expr,
            optional_vars=optional_vars,
            is_async=True,
            line=item.lineno if hasattr(item, 'lineno') else node.lineno,
            col=item.col_offset if hasattr(item, 'col_offset') else node.col_offset,
        ))
    
    body = parse_statements(node.body, source, resolver=resolver)
    orelse = parse_statements(node.orelse, source, resolver=resolver) if hasattr(node, 'orelse') and node.orelse else tuple()
    
    return With(
        items=tuple(items),
        body=body,
        orelse=orelse,
        line=node.lineno,
        col=node.col_offset,
    )


# =============================================================================
# PHASE 33.2: ASYNC FOR
# =============================================================================

def _parse_async_for(node: ast.AsyncFor, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> For:
    """
    Parse async for statement (Phase 33.2).
    
    Examples:
        async for item in async_iter():  → For(target="item", iter=..., is_async=True, body=[...])
            await process(item)
    """
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    # Parse target
    if isinstance(node.target, ast.Name):
        target = node.target.id
    elif isinstance(node.target, ast.Tuple):
        targets, _ = _parse_unpack_targets(node.target, source)
        # For simplicity, use first target (full unpacking would need ForUnpack with is_async)
        target = targets[0] if targets else "item"
    else:
        target = "item"
    
    iter_expr = _parse_expression(node.iter, source)
    body = parse_statements(node.body, source, resolver=resolver)
    orelse = parse_statements(node.orelse, source, resolver=resolver) if node.orelse else tuple()
    
    return For(
        target=target,
        iter=iter_expr,
        body=body,
        orelse=orelse,
        is_async=True,  # Phase 33.2: Mark as async
        line=node.lineno,
        col=node.col_offset,
    )


# =============================================================================
# PHASE 33.2: PATTERN MATCHING
# =============================================================================

def _parse_match(node: ast.Match, source: Optional[str] = None, resolver: Optional["ModuleResolver"] = None) -> Match:
    """
    Parse match statement (Phase 33.2).
    
    Examples:
        match value:              → Match(subject=..., cases=[...])
            case 1: ...
            case _: ...
    """
    # Phase 33.3: Create resolver if not provided (for backward compatibility)
    if resolver is None:
        from ._internal.module_resolver import ModuleResolver
        resolver = ModuleResolver(current_file="<string>")
    
    subject = _parse_expression(node.subject, source)
    cases = []
    
    for case in node.cases:
        pattern = _parse_pattern(case.pattern, source)
        guard = None
        if case.guard:
            guard = _parse_expression(case.guard, source)
        
        body = parse_statements(case.body, source, resolver=resolver)
        
        cases.append(Case(
            pattern=pattern,
            guard=guard,
            body=body,
            line=case.pattern.lineno if hasattr(case.pattern, 'lineno') else node.lineno,
            col=case.pattern.col_offset if hasattr(case.pattern, 'col_offset') else node.col_offset,
        ))
    
    return Match(
        subject=subject,
        cases=tuple(cases),
        line=node.lineno,
        col=node.col_offset,
    )


def _parse_pattern(node: ast.pattern, source: Optional[str] = None) -> Pattern:
    """
    Parse a pattern AST node into Pattern IR (Phase 33.2).
    
    Handles: MatchValue, MatchSingleton, MatchSequence, MatchMapping, 
             MatchClass, MatchStar, MatchAs, MatchOr
    """
    # MatchValue: case 1, case "hello"
    if isinstance(node, ast.MatchValue):
        value = _parse_expression(node.value, source)
        return LiteralPattern(
            value=value,
            line=node.lineno,
            col=node.col_offset,
        )
    
    # MatchSingleton: case True, case False, case None
    if isinstance(node, ast.MatchSingleton):
        value = Constant(value=node.value, line=node.lineno, col=node.col_offset)
        return LiteralPattern(
            value=value,
            line=node.lineno,
            col=node.col_offset,
        )
    
    # MatchAs: case x, case x as alias
    if isinstance(node, ast.MatchAs):
        if node.name:
            return CapturePattern(
                name=node.name,
                line=node.lineno,
                col=node.col_offset,
            )
        else:
            return WildcardPattern(
                line=node.lineno,
                col=node.col_offset,
            )
    
    # MatchStar: case *rest (in sequences)
    if isinstance(node, ast.MatchStar):
        if node.name:
            # This is handled in SequencePattern
            return CapturePattern(
                name=node.name,
                line=node.lineno,
                col=node.col_offset,
            )
        else:
            return WildcardPattern(
                line=node.lineno,
                col=node.col_offset,
            )
    
    # MatchSequence: case [a, b, *rest]
    if isinstance(node, ast.MatchSequence):
        patterns = []
        starred = None
        for i, pat in enumerate(node.patterns):
            if isinstance(pat, ast.MatchStar):
                starred = pat.name if pat.name else None
                # Skip the MatchStar itself, it's handled by starred field
            else:
                patterns.append(_parse_pattern(pat, source))
        
        return SequencePattern(
            patterns=tuple(patterns),
            starred=starred,
            line=node.lineno,
            col=node.col_offset,
        )
    
    # MatchMapping: case {"key": value}
    if isinstance(node, ast.MatchMapping):
        keys = []
        values = []
        rest = None
        
        for key, value in zip(node.keys, node.patterns):
            if key is None:
                # **rest pattern
                if isinstance(value, ast.MatchAs):
                    rest = value.name
            else:
                # Create MatchValue node with lineno/col_offset from parent
                match_value = ast.MatchValue(value=key)
                match_value.lineno = getattr(node, 'lineno', 0)
                match_value.col_offset = getattr(node, 'col_offset', 0)
                key_pattern = _parse_pattern(match_value, source)
                value_pattern = _parse_pattern(value, source)
                keys.append(key_pattern)
                values.append(value_pattern)
        
        return MappingPattern(
            keys=tuple(keys),
            values=tuple(values),
            rest=rest,
            line=node.lineno,
            col=node.col_offset,
        )
    
    # MatchClass: case Point(x=1, y=2)
    if isinstance(node, ast.MatchClass):
        keyword_patterns = []
        # kwd_attrs and kwd_patterns are separate lists that need to be zipped
        for attr, pattern_node in zip(node.kwd_attrs, node.kwd_patterns):
            pattern = _parse_pattern(pattern_node, source)
            keyword_patterns.append((attr, pattern))
        
        return ClassPattern(
            class_name=_parse_expression(node.cls, source) if hasattr(node.cls, 'id') else Name(id=str(node.cls), line=node.lineno, col=node.col_offset),
            keyword_patterns=tuple(keyword_patterns),
            line=node.lineno,
            col=node.col_offset,
        )
    
    # MatchOr: case A | B
    if isinstance(node, ast.MatchOr):
        patterns = tuple(_parse_pattern(pat, source) for pat in node.patterns)
        return OrPattern(
            patterns=patterns,
            line=node.lineno,
            col=node.col_offset,
        )
    
    # Fallback: wildcard
    return WildcardPattern(
        line=node.lineno if hasattr(node, 'lineno') else 0,
        col=node.col_offset if hasattr(node, 'col_offset') else 0,
    )


def _parse_import(
    node: ast.Import,
    resolver: "ModuleResolver",
    source: Optional[str] = None
) -> list[JSNode]:
    """
    Parse import statement (Phase 33.3: Full import system).
    
    WHAT: Parses Python 'import module' statements using the new import system.
    WHY: Enables full import support with path resolution and circular detection.
    HOW: Delegates to imports.parse_import().
    WHO: Used by parser when encountering ast.Import.
    WHEN: During AST parsing phase.
    WHERE: Part of import system integration.
    
    Args:
        node: AST Import node
        resolver: ModuleResolver for path resolution
        source: Optional source code for error messages
    
    Returns:
        List of IR nodes (Import or Assignment for built-ins)
    """
    from .imports import parse_import
    return parse_import(node, resolver, source)


def _parse_import_from(
    node: ast.ImportFrom,
    resolver: "ModuleResolver",
    source: Optional[str] = None
) -> list[JSNode]:
    """
    Parse from import statement (Phase 33.3: Full import system).
    
    WHAT: Parses Python 'from module import ...' statements using the new import system.
    WHY: Enables full from import support with relative imports and path resolution.
    HOW: Delegates to imports.parse_import_from().
    WHO: Used by parser when encountering ast.ImportFrom.
    WHEN: During AST parsing phase.
    WHERE: Part of import system integration.
    
    Args:
        node: AST ImportFrom node
        resolver: ModuleResolver for path resolution
        source: Optional source code for error messages
    
    Returns:
        List of IR nodes (ImportFrom or ImportStar)
    """
    from .imports import parse_import_from
    return parse_import_from(node, resolver, source)


def _unsupported_import(node, source: Optional[str] = None):
    raise unsupported("import statements", node, source,
                      get_suggestion("import"))


def _unsupported_global(node: ast.Global, source: Optional[str] = None) -> Pass:
    """
    Handle global statement with warning (Phase 18.8 - limited support).
    
    JavaScript doesn't have Python's global/nonlocal semantics.
    We emit a warning comment but continue transpilation.
    Variables will be treated as regular assignments (let-scoped).
    """
    import warnings
    var_names = ", ".join(node.names)
    warnings.warn(
        f"'global {var_names}' at line {node.lineno} - JavaScript doesn't have "
        f"Python's global semantics. Variable will be function-scoped.",
        stacklevel=4,
    )
    # Return Pass - the variable will be handled as a normal assignment
    return Pass(line=node.lineno, col=node.col_offset)


def _unsupported_nonlocal(node: ast.Nonlocal, source: Optional[str] = None) -> Pass:
    """
    Handle nonlocal statement with warning (Phase 18.8 - limited support).
    
    JavaScript closures automatically capture outer variables by reference,
    so nonlocal is actually the default behavior in JS.
    We emit a warning comment but continue transpilation.
    """
    import warnings
    var_names = ", ".join(node.names)
    warnings.warn(
        f"'nonlocal {var_names}' at line {node.lineno} - JavaScript closures "
        f"automatically capture outer scope, so this behaves correctly.",
        stacklevel=4,
    )
    # Return Pass - JS closures already have the desired behavior
    return Pass(line=node.lineno, col=node.col_offset)
