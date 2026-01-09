"""
PyNext Transpiler - Emitter (IR → JavaScript)

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Converts IR nodes (from parser.py) into JavaScript source code.
Each IR node type has a corresponding emit function that produces valid JS.

    IR Nodes → emit() → JavaScript Source

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

The IR is a clean intermediate representation, but we need actual JavaScript
code to run in the browser. The emitter:

1. Converts each IR node type to its JavaScript equivalent
2. Handles indentation and formatting
3. Injects runtime calls for Python semantics (__py.at, __py.slice, etc.)
4. Produces readable, debuggable JavaScript

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    IR Program
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  emit(node)                                                      │
    │      │                                                           │
    │      ├── Dictionary dispatch to type-specific emitter           │
    │      │                                                           │
    │      ├── emit_assignment(node) → "let x = 5;"                   │
    │      ├── emit_if(node) → "if (cond) { ... }"                   │
    │      ├── emit_for(node) → "for (const x of items) { ... }"     │
    │      └── ... etc                                                │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

- __init__.py: transpile() calls emit() after parse()
- Tests: Verify emitting produces correct JS

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler.emitter import emit
from pynext.transpiler.nodes import Assignment, Constant

# Emit a simple assignment
node = Assignment(target="x", value=Constant(value=5))
js = emit(node)
# → "let x = 5;"

# Emit with indentation
js = emit(node, indent=1)
# → "    let x = 5;"
```
"""

from __future__ import annotations
from typing import Optional

from .nodes import (
    JSNode, Program,
    # Statements
    Assignment, AugAssign, If, For, ForUnpack, While, FunctionDef,
    Return, Pass, Break, Continue, Delete, ExprStmt,
    # Try/Except (Phase 18.6 - critical fix)
    Try, ExceptHandler,
    # Expressions
    Name, This, Constant, BinOp, UnaryOp, Compare, BoolOp, IfExp,
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
    DunderMethod, With, WithItem, Match, AsyncFunctionDef, Yield, YieldFrom,
    # Phase 33.3: Imports
    Import, ImportFrom, ImportStar,
)
from ._internal.utils import (
    make_indent, escape_js_string, to_js_literal, safe_js_name, unique_name,
)
from ._internal.scope import ScopeTracker, get_scope, reset_scope
from ._internal.exception_context import (
    push_exception_context,
    pop_exception_context,
    get_current_exception_context,
    reset_exception_context,
)
from .optimizer.types import infer_types
from .optimizer._internal.type_env import TypeEnv, PyType

# Phase 33.1: Import emitters from separate modules
from .functions import (
    _emit_function_def,
    _emit_decorated_function,
    _emit_lambda,
    _build_params_full,
)
from .classes import (
    _emit_class_def,
    _emit_method_def,
    _emit_property_def,
    _emit_property_setter_def,
    _emit_property_deleter_def,
)
from .control_flow import (
    _emit_for,
    _emit_for_unpack,
    _emit_while,
    _emit_try,
    _emit_assert,
)
from .comprehensions import (
    _emit_list_comp,
    _emit_dict_comp,
    _emit_set_comp,
    _emit_generator_exp,
    _try_optimize_generator_call,
)
# Phase 33.2: Import advanced construct emitters
from .dunders import (
    _emit_dunder_method,
)
from .generators import (
    _emit_yield,
    _emit_yield_from,
    _emit_generator_function,
    _function_contains_yield,
)
from .context import (
    _emit_with,
)
from .pattern import (
    _emit_match,
)
from .async_support import (
    _emit_async_function_def,
    _emit_await,
    _emit_async_for,
)


# =============================================================================
# PUBLIC API
# =============================================================================

def emit(node: JSNode, indent: int = 0) -> str:
    """
    Convert an IR node to JavaScript source code.
    
    This is the main entry point for code generation.
    
    Args:
        node: IR node to emit
        indent: Indentation level (number of 4-space indents)
    
    Returns:
        JavaScript source code string
    
    Example:
        >>> emit(Assignment(target="x", value=Constant(5)))
        'let x = 5;'
    """
    emitter = _EMITTERS.get(type(node))
    if emitter is None:
        raise ValueError(f"No emitter for {type(node).__name__}")
    return emitter(node, indent)


def emit_expression(node: JSNode) -> str:
    """
    Emit an expression node (no statement terminator).
    
    Use this for expressions that don't need semicolons.
    """
    return _emit_expr(node)


# =============================================================================
# HELPERS
# =============================================================================

def _collect_named_exprs(node: JSNode) -> list[str]:
    """
    Recursively collect all variable names from NamedExpr (walrus) nodes.
    
    Used to pre-declare variables before conditions that use walrus operator.
    
    Example:
        if (x := get_value()):  → needs "let x;" before the if
    """
    result = []
    
    if isinstance(node, NamedExpr):
        result.append(node.target)
        # Also check the value for nested walrus
        result.extend(_collect_named_exprs(node.value))
    elif hasattr(node, '__dataclass_fields__'):
        # Recursively check all fields
        for field_name in node.__dataclass_fields__:
            field_value = getattr(node, field_name)
            if isinstance(field_value, JSNode):
                result.extend(_collect_named_exprs(field_value))
            elif isinstance(field_value, (list, tuple)):
                for item in field_value:
                    if isinstance(item, JSNode):
                        result.extend(_collect_named_exprs(item))
    
    return result


# =============================================================================
# STATEMENT EMITTERS
# =============================================================================

# Global type environment for type-aware optimizations
_global_type_env: Optional[TypeEnv] = None


def get_type_env() -> Optional[TypeEnv]:
    """Get the global type environment."""
    return _global_type_env


def reset_type_env() -> None:
    """Reset the global type environment."""
    global _global_type_env
    _global_type_env = None


def _emit_program(node: Program, indent: int) -> str:
    """
    Emit a program (list of statements).
    
    WHAT: Emits a complete program with imports at the top.
    WHY: ES6 imports must be at the top level, before other statements.
    HOW: Separates imports from other statements, emits imports first.
    WHO: Used by emitter when emitting Program nodes.
    WHEN: During final code generation.
    WHERE: Top-level emission function.
    
    Phase 33.3: Imports are collected and emitted at the top of the file.
    Phase 33.3 (Enhanced): Scope-aware import emission - only hoists top-level imports.
    Function-scoped imports are emitted inline as local assignments.
    """
    # Reset scope and exception context for new program
    reset_scope()
    reset_exception_context()
    
    # Run type inference for type-aware optimizations
    global _global_type_env
    _global_type_env = infer_types(node)
    
    # Phase 33.3: Scope-aware import emission
    # Only hoist top-level imports (ES6 requirement)
    # Function-scoped imports are emitted inline as local assignments
    imports = []
    other_statements = []
    
    for stmt in node.body:
        if isinstance(stmt, (Import, ImportFrom, ImportStar)):
            # Phase 33.3: Skip TYPE_CHECKING imports (stripped at runtime)
            if not getattr(stmt, 'is_type_checking', False):
                imports.append(stmt)
            # TYPE_CHECKING imports are silently skipped (not emitted)
        else:
            other_statements.append(stmt)
    
    lines = []
    
    # Phase 33.3: Emit top-level imports first (ES6 requirement)
    # Function-scoped imports are handled in _emit_function_def
    for imp in imports:
        lines.append(emit(imp, indent))
    
    # Add blank line between imports and code if both exist
    if imports and other_statements:
        lines.append("")
    
    # Emit other statements
    for stmt in other_statements:
        lines.append(emit(stmt, indent))
    
    return "\n".join(lines)


def _emit_assignment(node: Assignment, indent: int) -> str:
    """
    Emit assignment: x = value → let x = value; (first time)
                    or x = value; (reassignment)
    """
    prefix = make_indent(indent)
    target = safe_js_name(node.target)
    
    # Phase 33.2: Check if assignment value is a class instantiation with __call__
    # If so, mark the variable as a callable object
    scope = get_scope()
    is_callable = False
    
    if isinstance(node.value, Call):
        # Check if this is a class instantiation
        if isinstance(node.value.func, Name):
            class_name = node.value.func.id
            if scope.is_class_name(class_name) and scope.class_has_call(class_name):
                # This is an instantiation of a class with __call__ method
                is_callable = True
    
    # Emit the assignment
    value_js = _emit_expr(node.value)
    
    # Phase 33.2: Wrap generator function calls with wrapGenerator to add send(), throw(), close()
    # Only wrap if:
    # 1. The value is a Call (function call)
    # 2. It's a known generator function (not async, not regular)
    # 3. We're NOT inside an await expression (handled by _emit_call)
    # Note: The wrapping is handled in _emit_call, so we don't need to do it here
    # unless the call is nested in another expression. For simple assignments,
    # _emit_call will handle the wrapping.
    
    if scope.is_new_var(target):
        result = f"{prefix}let {target} = {value_js};"
    else:
        result = f"{prefix}{target} = {value_js};"
    
    # Phase 33.2: Mark as callable if it's an instance of a class with __call__
    if is_callable:
        scope.declare_callable_object(target)
    
    return result


def _emit_aug_assign(node: AugAssign, indent: int) -> str:
    """
    Emit augmented assignment with type-aware optimization.
    
    WHAT: Emits optimized JS for primitives, dunder runtime for objects.
    WHY: Performance optimization while preserving operator overloading.
    HOW: Queries type_env to determine if target is a primitive type.
    WHO: Used by emitter for all +=, -=, *=, etc. operations.
    WHEN: During code emission phase.
    WHERE: Part of emitter optimization pass.
    
    Phase 33.3: Type-aware optimization for augmented assignments.
    - Primitives (LIST, STR, INT, FLOAT): Native JS operations
    - Unknown/ANY or custom classes: Dunder runtime (preserves overloading)
    
    COMPREHENSIVE FIX: Always use dunder runtime for PyType.ANY to preserve
    operator overloading for custom classes. Only use native JS for explicitly
    known primitive types.
    
    Examples:
        items = [1, 2]           # type_env: items is LIST
        items += [3, 4]          # → items.push(...[3, 4]) (optimized)
        
        x = 5                    # type_env: x is INT
        x += 1                   # → x += 1 (native JS)
        
        s = "hello"              # type_env: s is STR
        s += " world"            # → s += " world" (native JS)
        
        obj = CustomList()       # type_env: obj is ANY
        obj += [1, 2]            # → obj = __py.dunders.iadd(obj, [1, 2]) (dunder)
        
        c = Counter(5)           # type_env: c is ANY (class instance)
        c += 10                  # → c = __py.dunders.iadd(c, 10) (dunder, preserves __iadd__)
    """
    prefix = make_indent(indent)
    target = safe_js_name(node.target)
    value_js = _emit_expr(node.value)
    
    # Phase 33.3: Type-aware optimization
    type_env = get_type_env()
    target_type = None
    if type_env:
        target_type = type_env.get_type(node.target)
    
    # COMPREHENSIVE FIX: For PyType.ANY (unknown types, custom classes), ALWAYS use dunder runtime
    # This ensures operator overloading works correctly for custom classes.
    # Even with the type inference fix above, this is a safety net that ensures
    # we never accidentally use native JS operators for custom classes.
    if target_type == PyType.ANY or target_type is None:
        # Unknown type → use dunder runtime (preserves operator overloading)
        op_map = {
            "add": "iadd",
            "sub": "isub",
            "mul": "imul",
            "div": "itruediv",
            "floordiv": "ifloordiv",
            "mod": "imod",
            "pow": "ipow",
        }
        dunder_func = op_map.get(node.op)
        if dunder_func:
            return f"{prefix}{target} = __py.dunders.{dunder_func}({target}, {value_js});"
        # Fall through for bitwise ops (they use native JS)
    
    # Optimize for known primitive types (only when type is explicitly known)
    # NOTE: We only optimize here for types we KNOW are primitives from explicit
    # assignments (x = 5, not from inference of PyType.ANY)
    if target_type:
        if node.op == "add":
            if target_type == PyType.LIST:
                # List concatenation: items += [x] → items.push(...[x])
                # This is more efficient than creating a new array
                return f"{prefix}{target}.push(...{value_js});"
            elif target_type == PyType.STR:
                # String concatenation: s += "x" → s += "x" (native JS)
                return f"{prefix}{target} += {value_js};"
            elif target_type.is_numeric():
                # Numeric addition: x += 1 → x += 1 (native JS)
                # This is safe because type inference only sets numeric types
                # for variables that were explicitly assigned numeric literals
                # (not for class instances, which are tracked separately)
                return f"{prefix}{target} += {value_js};"
        elif node.op == "sub" and target_type.is_numeric():
            # Numeric subtraction: x -= 1 → x -= 1 (native JS)
            return f"{prefix}{target} -= {value_js};"
        elif node.op == "mul" and target_type.is_numeric():
            # Numeric multiplication: x *= 2 → x *= 2 (native JS)
            return f"{prefix}{target} *= {value_js};"
        elif node.op == "div" and target_type.is_numeric():
            # Numeric division: x /= 2 → x /= 2 (native JS)
            return f"{prefix}{target} /= {value_js};"
    
    # Phase 33.3: Map operators to dunder runtime helpers (for custom classes and fallback)
    op_map = {
        "add": "iadd",
        "sub": "isub",
        "mul": "imul",
        "div": "itruediv",
        "floordiv": "ifloordiv",
        "mod": "imod",
        "pow": "ipow",
        "lshift": "<<=",  # Bitwise ops don't have in-place dunders in Python
        "rshift": ">>=",
        "bitor": "|=",
        "bitxor": "^=",
        "bitand": "&=",
    }
    
    dunder_func = op_map.get(node.op)
    
    # Use dunder runtime for arithmetic operators (preserves operator overloading)
    if dunder_func and dunder_func in ["iadd", "isub", "imul", "itruediv", "ifloordiv", "imod", "ipow"]:
        return f"{prefix}{target} = __py.dunders.{dunder_func}({target}, {value_js});"
    
    # Fallback to native JS operators for bitwise ops (they don't have in-place dunders)
    js_op_map = {
        "lshift": "<<=",
        "rshift": ">>=",
        "bitor": "|=",
        "bitxor": "^=",
        "bitand": "&=",
    }
    js_op = js_op_map.get(node.op, "+=")
    return f"{prefix}{target} {js_op} {value_js};"


def _emit_tuple_unpack(node: TupleUnpack, indent: int) -> str:
    """
    Emit tuple unpacking: a, b = pair → const [a, b] = pair; (first time)
                                    or [a, b] = pair; (reassignment)
    
    Phase 33.2: Supports unpacking to subscripts: arr[j], arr[j + 1] = arr[j + 1], arr[j]
    For subscript targets, we emit multiple individual assignments.
    """
    prefix = make_indent(indent)
    value_js = _emit_expr(node.value)
    
    # Phase 33.2: Check if any targets are subscripts (stored as tuples)
    has_subscripts = any(isinstance(t, tuple) and t[0] == "__subscript__" for t in node.targets)
    
    if has_subscripts:
        # Phase 33.2: Handle tuple unpacking with subscript targets
        # We need to unpack the value first, then assign to each target
        # arr[j], arr[j + 1] = arr[j + 1], arr[j]
        # → const _temp = [arr[j + 1], arr[j]]; arr[j] = _temp[0]; arr[j + 1] = _temp[1];
        
        # Create a temporary variable to hold the unpacked values
        temp_var = unique_name("unpack")
        scope = get_scope()
        scope.declare(temp_var)
        
        lines = [f"{prefix}const {temp_var} = {value_js};"]
        
        # Assign each target from the temp array
        for i, target in enumerate(node.targets):
            if isinstance(target, tuple) and target[0] == "__subscript__":
                # Subscript target - emit the subscript assignment
                subscript_ir = target[1]
                # Extract obj and key from the subscript IR node
                if isinstance(subscript_ir, Subscript):
                    obj_js = _emit_expr(subscript_ir.value)
                    idx_js = _emit_expr(subscript_ir.slice)
                    # Use __py.setitem() for subscript assignment
                    lines.append(f"{prefix}__py.setitem({obj_js}, {idx_js}, {temp_var}[{i}]);")
                else:
                    # Fallback: try to extract from emitted string
                    subscript_js = _emit_expr(subscript_ir)
                    # Extract obj and key from __py.getitem(obj, key) or __py.at(obj, key)
                    import re
                    # Handle both __py.getitem and __py.at patterns
                    match = re.match(r"__py\.(getitem|at)\(([^,]+),\s*([^)]+)\)", subscript_js)
                    if match:
                        obj_js = match.group(2).strip()
                        key_js = match.group(3).strip()
                        lines.append(f"{prefix}__py.setitem({obj_js}, {key_js}, {temp_var}[{i}]);")
                    else:
                        # Direct subscript like arr[j] - should not happen but handle it
                        lines.append(f"{prefix}{subscript_js} = {temp_var}[{i}];")
            elif isinstance(target, str) and target.startswith("*"):
                # Starred target - not supported with subscripts for now
                raise ValueError("Starred unpacking with subscript targets not supported")
            else:
                # Regular name target
                target_name = safe_js_name(target)
                if not scope.is_declared(target_name):
                    scope.declare(target_name)
                    lines.append(f"{prefix}let {target_name} = {temp_var}[{i}];")
                else:
                    lines.append(f"{prefix}{target_name} = {temp_var}[{i}];")
        
        return "\n".join(lines)
    
    # Original logic for regular tuple unpacking
    scope = get_scope()
    non_starred_targets = [t for t in node.targets if isinstance(t, str) and not t.startswith("*")]
    all_new = all(not scope.is_declared(safe_js_name(t)) for t in non_starred_targets)
    
    # Declare the variables in scope
    for t in non_starred_targets:
        scope.declare(safe_js_name(t))
    
    # Build destructuring pattern
    if node.starred_index is None:
        # Simple unpacking
        targets_js = ", ".join(safe_js_name(t) if isinstance(t, str) else str(t) for t in node.targets)
        if all_new:
            # Use 'let' instead of 'const' to allow reassignment (Python allows reassigning unpacked vars)
            return f"{prefix}let [{targets_js}] = {value_js};"
        else:
            return f"{prefix}[{targets_js}] = {value_js};"
    else:
        # Starred unpacking: a, *rest, z = items
        # This requires special handling
        parts = []
        for i, target in enumerate(node.targets):
            if i == node.starred_index:
                parts.append(f"...{safe_js_name(target)}")
            else:
                parts.append(safe_js_name(target) if isinstance(target, str) else str(target))
        
        pattern = ", ".join(parts)
        if all_new:
            # Use 'let' instead of 'const' to allow reassignment (Python allows reassigning unpacked vars)
            return f"{prefix}let [{pattern}] = {value_js};"
        else:
            return f"{prefix}[{pattern}] = {value_js};"


def _needs_bool_wrapper(node: JSNode) -> bool:
    """
    Determine if an expression needs __py.bool() wrapper for truthiness check.
    
    Returns False (no wrapper needed) for:
    - Comparisons (x > 0, a == b) - always return boolean
    - BoolOp (and, or) - already handle truthiness internally
    - UnaryOp with 'not' - already uses __py.bool
    - Literal True/False - already boolean
    - Call to bool() - already boolean
    
    Returns True (wrapper needed) for:
    - Variables (could be empty list/dict)
    - Function calls (could return empty list/dict)
    - Subscripts, attributes, etc.
    
    This prevents the Python/JS semantic difference where:
    - Python: if []: is falsy
    - JavaScript: if ([]) is truthy
    """
    # Comparisons always return boolean
    if isinstance(node, Compare):
        return False
    
    # BoolOp already handles truthiness
    if isinstance(node, BoolOp):
        return False
    
    # UnaryOp 'not' already uses __py.bool
    if isinstance(node, UnaryOp) and node.op == "not":
        return False
    
    # Literal booleans
    if isinstance(node, Constant):
        if isinstance(node.value, bool):
            return False
    
    # NamedExpr (walrus) - check the value
    if isinstance(node, NamedExpr):
        return _needs_bool_wrapper(node.value)
    
    # Everything else needs wrapper (could be empty list/dict)
    return True


def _is_type_checking_if(node: If) -> bool:
    """
    Check if an If node is a TYPE_CHECKING block.
    
    Phase 33.3: Detects if the condition is TYPE_CHECKING.
    TYPE_CHECKING blocks should be completely stripped (not emitted).
    
    Args:
        node: If IR node
    
    Returns:
        True if this is a TYPE_CHECKING block
    """
    # Check if test is a Name node with id="TYPE_CHECKING"
    if isinstance(node.test, Name):
        return node.test.id == "TYPE_CHECKING"
    return False


def _emit_truthiness(node: JSNode) -> str:
    """
    Emit an expression with proper Python truthiness semantics.
    
    Wraps in __py.bool() when needed to handle:
    - Empty list [] being falsy in Python but truthy in JS
    - Empty dict {} being falsy in Python but truthy in JS
    - Empty string being falsy
    - 0 and None being falsy
    """
    expr_js = _emit_expr(node)
    
    if _needs_bool_wrapper(node):
        return f"__py.bool({expr_js})"
    else:
        return expr_js


def _emit_if(node: If, indent: int) -> str:
    """
    Emit if/elif/else statement.
    
    Handles:
    - Walrus operator by pre-declaring variables
    - Python truthiness with __py.bool() wrapper when needed
    """
    prefix = make_indent(indent)
    lines = []
    
    # Check for walrus operator in condition and pre-declare
    walrus_vars = _collect_named_exprs(node.test)
    for var in walrus_vars:
        lines.append(f"{prefix}let {var};")
    
    # Phase 33.3: Check if this is a TYPE_CHECKING block
    # If so, skip emitting the entire block (TYPE_CHECKING is False at runtime)
    is_type_checking = _is_type_checking_if(node)
    
    if is_type_checking:
        # Skip TYPE_CHECKING blocks entirely - they're not executed at runtime
        return ""
    
    # if test { body } - wrap test in __py.bool() if needed
    test_js = _emit_truthiness(node.test)
    lines.append(f"{prefix}if ({test_js}) {{")
    for stmt in node.body:
        # Phase 33.3: Skip TYPE_CHECKING imports even if not in TYPE_CHECKING block
        if isinstance(stmt, (Import, ImportFrom, ImportStar)):
            if getattr(stmt, 'is_type_checking', False):
                continue
        lines.append(emit(stmt, indent + 1))
    
    # Handle elif/else chain
    if node.orelse:
        # Check if it's an elif (single If node)
        if len(node.orelse) == 1 and isinstance(node.orelse[0], If):
            # elif
            elif_node = node.orelse[0]
            elif_test = _emit_truthiness(elif_node.test)
            lines.append(f"{prefix}}} else if ({elif_test}) {{")
            for stmt in elif_node.body:
                lines.append(emit(stmt, indent + 1))
            
            # Recursively handle rest of elif/else chain
            if elif_node.orelse:
                rest = _emit_elif_chain(elif_node.orelse, indent)
                lines.append(rest)
            else:
                lines.append(f"{prefix}}}")
        else:
            # else block
            lines.append(f"{prefix}}} else {{")
            for stmt in node.orelse:
                lines.append(emit(stmt, indent + 1))
            lines.append(f"{prefix}}}")
    else:
        lines.append(f"{prefix}}}")
    
    return "\n".join(lines)


def _emit_elif_chain(orelse: tuple, indent: int) -> str:
    """Helper to emit elif/else chain."""
    prefix = make_indent(indent)
    lines = []
    
    if len(orelse) == 1 and isinstance(orelse[0], If):
        # Another elif - use truthiness wrapper
        elif_node = orelse[0]
        elif_test = _emit_truthiness(elif_node.test)
        lines.append(f"{prefix}}} else if ({elif_test}) {{")
        for stmt in elif_node.body:
            lines.append(emit(stmt, indent + 1))
        
        if elif_node.orelse:
            lines.append(_emit_elif_chain(elif_node.orelse, indent))
        else:
            lines.append(f"{prefix}}}")
    else:
        # Final else
        lines.append(f"{prefix}}} else {{")
        for stmt in orelse:
            lines.append(emit(stmt, indent + 1))
        lines.append(f"{prefix}}}")
    
    return "\n".join(lines)


# Control flow functions moved to control_flow.py
# Function-related functions moved to functions.py
# Class-related functions moved to classes.py
# Comprehension-related functions moved to comprehensions.py


# =============================================================================
# STATEMENT EMITTERS (remaining)
# =============================================================================

def _emit_return(node: Return, indent: int) -> str:
    """Emit return statement."""
    prefix = make_indent(indent)
    if node.value is None:
        return f"{prefix}return;"
    value_js = _emit_expr(node.value)
    return f"{prefix}return {value_js};"


def _emit_pass(node: Pass, indent: int) -> str:
    """Emit pass statement as comment."""
    prefix = make_indent(indent)
    return f"{prefix}/* pass */"


def _emit_break(node: Break, indent: int) -> str:
    """Emit break statement."""
    prefix = make_indent(indent)
    return f"{prefix}break;"


def _emit_continue(node: Continue, indent: int) -> str:
    """Emit continue statement."""
    prefix = make_indent(indent)
    return f"{prefix}continue;"


def _emit_delete(node: Delete, indent: int) -> str:
    """Emit delete statement."""
    prefix = make_indent(indent)
    target = node.target
    
    # del items[idx] → items.splice(idx, 1) for arrays, delete for objects
    if isinstance(target, Subscript):
        value_js = _emit_expr(target.value)
        idx_js = _emit_expr(target.slice)
        
        # Use splice for potential array delete (runtime can optimize)
        if isinstance(target.slice, Slice):
            # del items[1:3] - slice deletion
            return f"{prefix}__py.del_slice({value_js}, {idx_js});"
        else:
            # Simple index - use runtime helper that handles both array and object
            return f"{prefix}__py.del({value_js}, {idx_js});"
    
    if isinstance(target, Attribute):
        value_js = _emit_expr(target.value)
        attr = target.attr
        return f"{prefix}delete {value_js}.{attr};"
    
    if isinstance(target, Name):
        name = safe_js_name(target.id)
        return f"{prefix}{name} = undefined;"
    
    target_js = _emit_expr(target)
    return f"{prefix}delete {target_js};"


def _emit_expr_stmt(node: ExprStmt, indent: int) -> str:
    """
    Emit expression statement.
    
    Special handling for raise statements (Phase 33.3: supports exception chaining):
    - __throw__(exc) → throw exc;
    - __throw_from__(exc, cause) → const _exc = exc; _exc.__cause__ = cause; throw _exc;
    - __raise__ (bare Name) → throw _e;  (re-raise current exception)
    
    WHAT: Emits expression statements, including raise statements with exception chaining.
    WHY: Enables proper exception handling and chaining in transpiled code.
    HOW: Detects special markers (__throw__, __throw_from__, __raise__) and emits appropriate JS.
    WHO: Used by emitter when emitting ExprStmt nodes.
    WHEN: When transpiling raise statements.
    WHERE: Part of statement emission in emitter.py.
    
    Examples:
        raise ValueError("msg")           → throw new ValueError("msg");
        raise ValueError("msg") from e    → const _exc = new ValueError("msg"); _exc.__cause__ = e; throw _exc;
        raise                             → throw _e;
    """
    prefix = make_indent(indent)
    
    # Phase 33.3: Handle __throw_from__(exc, cause) → exception chaining
    if isinstance(node.value, Call):
        if isinstance(node.value.func, Name) and node.value.func.id == "__throw_from__":
            if len(node.value.args) >= 2:
                exc_js = _emit_expr(node.value.args[0])
                cause_js = _emit_expr(node.value.args[1])
                # Emit: const _exc = exc; _exc.__cause__ = cause; throw _exc;
                return f"{prefix}const _exc = {exc_js};\n{prefix}_exc.__cause__ = {cause_js};\n{prefix}throw _exc;"
            elif node.value.args:
                # Only exception, no cause (shouldn't happen, but handle gracefully)
                exc_js = _emit_expr(node.value.args[0])
                return f"{prefix}throw {exc_js};"
            else:
                return f"{prefix}throw new Error();"
        
        # Handle __throw__(exc) → throw exc; (raise statement with exception)
        # Phase 33.3: Automatically set __context__ if inside except block
        if isinstance(node.value.func, Name) and node.value.func.id == "__throw__":
            if node.value.args:
                exc_js = _emit_expr(node.value.args[0])
                context_var = get_current_exception_context()
                
                if context_var:
                    # We're inside an except block - set __context__ automatically
                    # This matches Python's behavior: exceptions raised during handling
                    # automatically have __context__ set to the exception being handled
                    return f"{prefix}const _exc = {exc_js};\n{prefix}_exc.__context__ = {context_var};\n{prefix}throw _exc;"
                else:
                    # Not in except block - normal throw
                    return f"{prefix}throw {exc_js};"
            else:
                return f"{prefix}throw new Error();"
    
    # Handle __raise__ → throw _e; (bare raise to re-raise current exception)
    if isinstance(node.value, Name) and node.value.id == "__raise__":
        return f"{prefix}throw _e;"
    
    # Check for assignment expression (subscript/attribute assign)
    if isinstance(node.value, BinOp) and node.value.op == "assign":
        left_js = _emit_expr(node.value.left)
        right_js = _emit_expr(node.value.right)
        
        # Phase 33.2: Convert __py.getitem(obj, key) = value to __py.setitem(obj, key, value)
        if left_js.startswith("__py.getitem("):
            # Extract obj and key from __py.getitem(obj, key)
            import re
            match = re.match(r"__py\.getitem\(([^,]+),\s*([^)]+)\)", left_js)
            if match:
                obj_js = match.group(1).strip()
                key_js = match.group(2).strip()
                return f"{prefix}__py.setitem({obj_js}, {key_js}, {right_js});"
        
        # Fix: Convert __py.at(obj, key) = value to obj[key] = value for assignments
        if left_js.startswith("__py.at("):
            # Extract obj and key from __py.at(obj, key)
            import re
            match = re.match(r"__py\.at\(([^,]+),\s*([^)]+)\)", left_js)
            if match:
                obj_js = match.group(1).strip()
                key_js = match.group(2).strip()
                left_js = f"{obj_js}[{key_js}]"
        return f"{prefix}{left_js} = {right_js};"
    
    expr_js = _emit_expr(node.value)
    return f"{prefix}{expr_js};"


# =============================================================================
# EXPRESSION EMITTERS
# =============================================================================

def _emit_expr(node: JSNode) -> str:
    """Emit an expression (no trailing semicolon)."""
    emitter = _EXPR_EMITTERS.get(type(node))
    if emitter is None:
        raise ValueError(f"No expression emitter for {type(node).__name__}")
    return emitter(node)


def _emit_name(node: Name) -> str:
    """Emit variable reference."""
    # Map special Python names to JS
    # Note: "super" is preserved as-is since it's a valid JS keyword we want to use
    name_map = {
        "True": "true",
        "False": "false",
        "None": "null",
        "print": "console.log",
        "super": "super",  # Preserve super for class inheritance
        # Built-in types for isinstance() - use runtime type helpers
        "int": "__py.type(0)",  # Number type
        "str": "__py.type('')",  # String type
        "float": "__py.type(0.0)",  # Number type
        "bool": "__py.type(true)",  # Boolean type
        "list": "__py.type([])",  # Array type
        "dict": "__py.type({})",  # Object type
        "tuple": "__py.type([])",  # Array type (tuples are arrays in JS)
        "set": "__py.type(new Set())",  # Set type
    }
    return name_map.get(node.id, safe_js_name(node.id))


def _emit_this(node: This) -> str:
    """
    Emit JavaScript 'this' reference (from Python 'self').
    
    FUNDAMENTAL FIX: This node is created during parsing when 'self' is encountered
    in a method context. It directly emits to 'this' - no string replacement needed.
    
    Examples:
        self.x      → this.x  (when This is the value of Attribute)
        return self → return this
        self.foo()  → this.foo()
    """
    return "this"


def _emit_constant(node: Constant) -> str:
    """Emit literal constant."""
    return to_js_literal(node.value)


def _emit_binop(node: BinOp) -> str:
    """
    Emit binary operation (Phase 33.3: Enhanced with operator overloading).
    
    WHAT: Emits binary operators with full operator overloading support.
    WHY: Python supports operator overloading via dunder methods.
    HOW: Uses runtime helpers that check for __add__, __radd__, etc.
    WHO: Called when emitting binary operations.
    WHEN: During JavaScript emission phase.
    WHERE: Part of expression emission.
    
    Phase 33.3 Enhancements:
    - All operators use runtime helpers for dunder method support
    - Reverse operators (__radd__, __rsub__, etc.) are handled
    - Optimizations for known numeric/string literals
    """
    left_js = _emit_expr(node.left)
    right_js = _emit_expr(node.right)

    # Phase 33.3: Use operator overloading runtime helpers
    # These check for __add__, __radd__, etc. in order
    
    # Addition: __add__ → __radd__ → fallback
    if node.op == "add":
        # Optimize for known number literals (no dunder methods)
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} + {right_js})"
        # Use runtime helper for operator overloading
        return f"__py.dunders.add({left_js}, {right_js})"

    # Subtraction: __sub__ → __rsub__ → fallback
    if node.op == "sub":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} - {right_js})"
        # Use runtime helper
        return f"__py.dunders.sub({left_js}, {right_js})"

    # Multiplication: __mul__ → __rmul__ → fallback
    if node.op == "mul":
        # Known string literal - use .repeat() directly (optimization)
        if isinstance(node.left, Constant) and isinstance(node.left.value, str):
            return f"{left_js}.repeat({right_js})"
        if isinstance(node.right, Constant) and isinstance(node.right.value, str):
            return f"{right_js}.repeat({left_js})"
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} * {right_js})"
        # Use runtime helper for operator overloading
        return f"__py.dunders.mul({left_js}, {right_js})"

    # True division: __truediv__ → __rtruediv__ → fallback
    if node.op == "div":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} / {right_js})"
        # Use runtime helper
        return f"__py.dunders.truediv({left_js}, {right_js})"

    # Floor division: __floordiv__ → __rfloordiv__ → fallback
    if node.op == "floordiv":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"Math.floor({left_js} / {right_js})"
        # Use runtime helper
        return f"__py.dunders.floordiv({left_js}, {right_js})"

    # Modulo: __mod__ → __rmod__ → fallback
    if node.op == "mod":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} % {right_js})"
        # Use runtime helper
        return f"__py.dunders.mod({left_js}, {right_js})"

    # Power: __pow__ → __rpow__ → fallback
    if node.op == "pow":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} ** {right_js})"
        # Use runtime helper
        return f"__py.dunders.pow({left_js}, {right_js})"

    # Left shift: __lshift__ → __rlshift__ → fallback
    if node.op == "lshift":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} << {right_js})"
        # Use runtime helper
        return f"__py.dunders.lshift({left_js}, {right_js})"

    # Right shift: __rshift__ → __rrshift__ → fallback
    if node.op == "rshift":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} >> {right_js})"
        # Use runtime helper
        return f"__py.dunders.rshift({left_js}, {right_js})"

    # Bitwise AND: __and__ → __rand__ → fallback
    if node.op == "bitand":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} & {right_js})"
        # Use runtime helper
        return f"__py.dunders.bitand({left_js}, {right_js})"

    # Bitwise OR: __or__ → __ror__ → fallback
    if node.op == "bitor":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} | {right_js})"
        # Use runtime helper
        return f"__py.dunders.bitor({left_js}, {right_js})"

    # Bitwise XOR: __xor__ → __rxor__ → fallback
    if node.op == "bitxor":
        # Optimize for known number literals
        if _is_numeric(node.left) and _is_numeric(node.right):
            return f"({left_js} ^ {right_js})"
        # Use runtime helper
        return f"__py.dunders.bitxor({left_js}, {right_js})"
    
    # Fallback for unknown operators
    op_map = {
        "sub": "-", "div": "/",
        "lshift": "<<", "rshift": ">>",
        "bitor": "|", "bitxor": "^", "bitand": "&",
    }
    js_op = op_map.get(node.op, "+")
    return f"({left_js} {js_op} {right_js})"


def _is_numeric(node) -> bool:
    """Check if a node is a known numeric value."""
    if isinstance(node, Constant):
        return isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
    return False


def _emit_unaryop(node: UnaryOp) -> str:
    """
    Emit unary operation (Phase 33.3: Enhanced with operator overloading).
    
    WHAT: Emits unary operators with full operator overloading support.
    WHY: Python supports operator overloading via dunder methods.
    HOW: Uses runtime helpers that check for __neg__, __pos__, __abs__, etc.
    WHO: Called when emitting unary operations.
    WHEN: During JavaScript emission phase.
    WHERE: Part of expression emission.
    
    Phase 33.3 Enhancements:
    - Unary operators use runtime helpers for dunder method support
    - Optimizations for known numeric literals
    """
    operand_js = _emit_expr(node.operand)
    
    if node.op == "not":
        # Python truthiness
        return f"!__py.bool({operand_js})"
    
    # Phase 33.3: Use operator overloading runtime helpers
    # Negation: __neg__ → fallback
    if node.op == "neg":
        # Optimize for known number literals
        if _is_numeric(node.operand):
            return f"(-{operand_js})"
        # Use runtime helper
        return f"__py.dunders.neg({operand_js})"
    
    # Positive: __pos__ → fallback
    if node.op == "pos":
        # Optimize for known number literals
        if _is_numeric(node.operand):
            return f"(+{operand_js})"
        # Use runtime helper
        return f"__py.dunders.pos({operand_js})"
    
    # Invert: __invert__ → fallback (bitwise NOT)
    if node.op == "invert":
        # Optimize for known number literals
        if _is_numeric(node.operand):
            return f"(~{operand_js})"
        # Use runtime helper (if we add __invert__ support)
        # For now, just use native JS
        return f"(~{operand_js})"
    
    # Fallback
    op_map = {"neg": "-", "pos": "+", "invert": "~"}
    js_op = op_map.get(node.op, "+")
    return f"{js_op}{operand_js}"


def _emit_compare(node: Compare) -> str:
    """
    Emit comparison with proper handling of chained comparisons.
    
    CRITICAL FIX: In Python, chained comparisons like `a < f() < b` evaluate
    f() only ONCE. We use an IIFE (Immediately Invoked Function Expression)
    to cache middle operands:
    
        a < f() < b  →  (((_t) => (a < _t) && (_t < b))(f()))
    
    For simple cases (single comparison), no IIFE is needed.
    For simple variable comparisons, we also skip the IIFE.
    """
    # Single comparison - no chaining, no caching needed
    if len(node.ops) == 1:
        left_js = _emit_expr(node.left)
        right_js = _emit_expr(node.comparators[0])
        return _emit_single_compare(left_js, node.ops[0], right_js)
    
    # Chained comparison - need to cache middle operands
    # Check if middle operands are simple (Name nodes) - no caching needed
    middle_operands = node.comparators[:-1]
    all_simple = all(isinstance(c, Name) for c in middle_operands)
    
    if all_simple:
        # All middle operands are simple variables - no caching needed
        parts = []
        left_js = _emit_expr(node.left)
        for i, (op, right) in enumerate(zip(node.ops, node.comparators)):
            right_js = _emit_expr(right)
            parts.append(_emit_single_compare(left_js, op, right_js))
            left_js = right_js
        return " && ".join(parts)
    
    # Complex case: middle operands may have side effects
    # Use IIFE to cache: (((_t1, _t2) => cmp1 && cmp2 && ...)(val1, val2))
    temp_vars = []
    temp_values = []
    
    # Collect all operands that need caching (middle ones)
    for i, comp in enumerate(middle_operands):
        if isinstance(comp, Name):
            # Simple variable - use directly
            temp_vars.append(_emit_expr(comp))
        else:
            # Complex expression - cache it
            temp_name = f"_cmp{i}"
            temp_vars.append(temp_name)
            temp_values.append((temp_name, _emit_expr(comp)))
    
    # Build comparison chain
    parts = []
    left_js = _emit_expr(node.left)
    
    for i, (op, right) in enumerate(zip(node.ops, node.comparators)):
        if i < len(temp_vars):
            right_js = temp_vars[i]
        else:
            right_js = _emit_expr(right)
        
        parts.append(_emit_single_compare(left_js, op, right_js))
        left_js = right_js if i < len(temp_vars) else _emit_expr(right)
    
    comparison = " && ".join(parts)
    
    if not temp_values:
        # No caching needed after all
        return comparison
    
    # Wrap in IIFE
    params = ", ".join(name for name, _ in temp_values)
    args = ", ".join(value for _, value in temp_values)
    return f"(({params}) => {comparison})({args})"


def _emit_single_compare(left_js: str, op: str, right_js: str) -> str:
    """Emit a single comparison operation."""
    if op == "eq":
        return f"__py.eq({left_js}, {right_js})"
    elif op == "ne":
        return f"!__py.eq({left_js}, {right_js})"
    elif op == "is":
        return f"({left_js} === {right_js})"
    elif op == "isnot":
        return f"({left_js} !== {right_js})"
    elif op == "in":
        return f"__py.in({left_js}, {right_js})"
    elif op == "notin":
        return f"!__py.in({left_js}, {right_js})"
    else:
        # Simple comparisons
        op_map = {"lt": "<", "le": "<=", "gt": ">", "ge": ">="}
        js_op = op_map.get(op, "===")
        return f"({left_js} {js_op} {right_js})"


def _emit_boolop(node: BoolOp) -> str:
    """
    Emit boolean operation with Python truthiness and CORRECT short-circuit evaluation.
    
    CRITICAL: Python's `and`/`or`:
    1. Evaluate operands LEFT-TO-RIGHT
    2. Short-circuit: stop when result is determined
    3. Return the determining value (not True/False)
    
    For `a and b`:
    - If a is falsy, return a (don't evaluate b)
    - If a is truthy, return b
    
    For `a or b`:
    - If a is truthy, return a (don't evaluate b)
    - If a is falsy, return b
    
    Examples:
        get_a() and get_b()  →  ((_a) => __py.bool(_a) ? get_b() : _a)(get_a())
        get_a() or get_b()   →  ((_a) => __py.bool(_a) ? _a : get_b())(get_a())
    
    The key is: subsequent operands are NOT pre-evaluated, only the first one is cached.
    """
    if len(node.values) == 0:
        return "true"
    if len(node.values) == 1:
        return _emit_expr(node.values[0])
    
    # Check if value is simple (no side effects, can be evaluated multiple times)
    def is_simple(v):
        return isinstance(v, (Name, Constant))
    
    all_simple = all(is_simple(v) for v in node.values)
    
    if all_simple:
        # Simple case - no caching needed, direct ternaries
        parts = [_emit_expr(v) for v in node.values]
        if node.op == "and":
            result = parts[-1]
            for part in reversed(parts[:-1]):
                result = f"(__py.bool({part}) ? {result} : {part})"
            return result
        else:  # or
            result = parts[-1]
            for part in reversed(parts[:-1]):
                result = f"(__py.bool({part}) ? {part} : {result})"
            return result
    
    # Complex case - need PROPER short-circuit with lazy evaluation
    # Only cache values that are evaluated, don't pre-evaluate subsequent operands
    
    # Build the expression recursively from right to left
    def build_expr(values, op, depth=0):
        if len(values) == 1:
            return _emit_expr(values[0])
        
        first = values[0]
        rest = values[1:]
        first_js = _emit_expr(first)
        
        # Recursively build the rest (these will be lazily evaluated)
        rest_expr = build_expr(rest, op, depth + 1)
        
        if is_simple(first):
            # Simple value - no caching needed
            if op == "and":
                return f"(__py.bool({first_js}) ? {rest_expr} : {first_js})"
            else:  # or
                return f"(__py.bool({first_js}) ? {first_js} : {rest_expr})"
        else:
            # Complex value - cache in IIFE to avoid double evaluation
            temp = f"_b{depth}"
            if op == "and":
                return f"(({temp}) => __py.bool({temp}) ? {rest_expr} : {temp})({first_js})"
            else:  # or
                return f"(({temp}) => __py.bool({temp}) ? {temp} : {rest_expr})({first_js})"
    
    return build_expr(list(node.values), node.op)


def _emit_ifexp(node: IfExp) -> str:
    """
    Emit conditional expression (ternary).
    
    Uses __py.bool() wrapper for Python truthiness semantics.
    """
    test_js = _emit_truthiness(node.test)
    body_js = _emit_expr(node.body)
    orelse_js = _emit_expr(node.orelse)
    return f"({test_js} ? {body_js} : {orelse_js})"


# =============================================================================
# GENERATOR EXPRESSION OPTIMIZATION (Phase 18.5)
# =============================================================================
    
    # =========================================================================
    # sum(expr for x in items [if cond])
    # =========================================================================
    if func_name == "sum":
        # For reduce, the destructuring is the 2nd param, so no extra parens needed
        # Use __acc__ to avoid collision with destructured names
        if is_identity:
            # sum(x for x in items) → items.reduce((__acc__, x) => __acc__ + x, 0)
            return f"{base}.reduce((__acc__, {target}) => __acc__ + {target_name}, 0)"
        else:
            # sum(x*2 for x in items) → items.reduce((__acc__, x) => __acc__ + (x*2), 0)
            return f"{base}.reduce((__acc__, {target}) => __acc__ + ({element_js}), 0)"
    
    # =========================================================================
    # any(expr for x in items [if cond])
    # =========================================================================
    if func_name == "any":
        if is_identity:
            # any(x for x in items) → items.some(x => __py.bool(x))
            return f"{base}.some({arrow_target} => __py.bool({target_name}))"
        else:
            # any(x > 0 for x in items) → items.some(x => x > 0)
            return f"{base}.some({arrow_target} => {element_js})"
    
    # =========================================================================
    # all(expr for x in items [if cond])
    # =========================================================================
    if func_name == "all":
        if is_identity:
            # all(x for x in items) → items.every(x => __py.bool(x))
            return f"{base}.every({arrow_target} => __py.bool({target_name}))"
        else:
            # all(x > 0 for x in items) → items.every(x => x > 0)
            return f"{base}.every({arrow_target} => {element_js})"
    
    # =========================================================================
    # list(expr for x in items [if cond])
    # =========================================================================
    if func_name == "list":
        if is_identity:
            # list(x for x in items) → [...items]
            return base
        else:
            # list(x*2 for x in items) → items.map(x => x*2)
            return f"{base}.map({arrow_target} => {element_js})"
    
    # =========================================================================
    # set(expr for x in items [if cond])
    # =========================================================================
    if func_name == "set":
        if is_identity:
            # set(x for x in items) → new Set(items)
            return f"new Set({base})"
        else:
            # set(x*2 for x in items) → new Set(items.map(x => x*2))
            return f"new Set({base}.map({arrow_target} => {element_js}))"
    
    # =========================================================================
    # tuple(expr for x in items [if cond])
    # =========================================================================
    if func_name == "tuple":
        if is_identity:
            return f"Object.freeze({base})"
        else:
            return f"Object.freeze({base}.map({arrow_target} => {element_js}))"
    
    # =========================================================================
    # min/max(expr for x in items [if cond])
    # =========================================================================
    if func_name == "min":
        kwargs = {kw[0]: _emit_expr(kw[1]) for kw in keywords}
        key = kwargs.get("key", "null")
        if is_identity:
            return f"__py.min({base}, {key})"
        else:
            return f"__py.min({base}.map({arrow_target} => {element_js}), {key})"
    
    if func_name == "max":
        kwargs = {kw[0]: _emit_expr(kw[1]) for kw in keywords}
        key = kwargs.get("key", "null")
        if is_identity:
            return f"__py.max({base}, {key})"
        else:
            return f"__py.max({base}.map({arrow_target} => {element_js}), {key})"
    
    # =========================================================================
    # sorted(expr for x in items [if cond])
    # =========================================================================
    if func_name == "sorted":
        kwargs = {kw[0]: _emit_expr(kw[1]) for kw in keywords}
        key = kwargs.get("key", "null")
        reverse = kwargs.get("reverse", "false")
        if is_identity:
            return f"__py.sorted({base}, {key}, {reverse})"
        else:
            return f"__py.sorted({base}.map({arrow_target} => {element_js}), {key}, {reverse})"
    
    # =========================================================================
    # len(expr for x in items [if cond]) - count items
    # =========================================================================
    if func_name == "len":
        return f"{base}.length"
    
    # =========================================================================
    # dict((k, v) for k, v in items [if cond])
    # =========================================================================
    if func_name == "dict":
        # Check if element is a tuple of two elements
        if isinstance(gen.element, Tuple) and len(gen.element.elts) == 2:
            key_js = _emit_expr(gen.element.elts[0])
            val_js = _emit_expr(gen.element.elts[1])
            return f"Object.fromEntries({base}.map({arrow_target} => [{key_js}, {val_js}]))"
    
    return None


def _emit_call(node: Call) -> str:
    """Emit function call."""
    func_js = _emit_expr(node.func)
    
    # Phase 33.2: Handle asyncio.gather → Promise.all and asyncio.run
    if isinstance(node.func, Attribute):
        if isinstance(node.func.value, Name) and node.func.value.id == "asyncio":
            if node.func.attr == "gather":
                # asyncio.gather(*args) → Promise.all([...args])
                # Handle starred arguments - they should be spread into the array
                args_js = []
                for arg in node.args:
                    if isinstance(arg, Starred):
                        # Unpack starred argument - already spread, just add to array
                        starred_js = _emit_expr(arg.value)
                        # If it's already an array spread, don't double-spread
                        if starred_js.startswith("...") or starred_js.startswith("[..."):
                            args_js.append(starred_js)
                        else:
                            args_js.append(f"...{starred_js}")
                    else:
                        arg_js = _emit_expr(arg)
                        args_js.append(arg_js)
                # Build Promise.all array
                if len(args_js) == 1 and args_js[0].startswith("..."):
                    # Single spread argument - use directly
                    return f"Promise.all([{args_js[0]}])"
                else:
                    # Multiple args or non-spread - combine into array
                    return f"Promise.all([{', '.join(args_js)}])"
            
            if node.func.attr == "run":
                # asyncio.run(coro) → (async () => { return await coro(); })()
                # This is an IIFE that runs the async function
                if node.args:
                    coro_js = _emit_expr(node.args[0])
                    # Check if coro is already a call (e.g., asyncio.run(main()))
                    # If so, we need to await it directly
                    if isinstance(node.args[0], Call):
                        # It's already a call, so we await it directly
                        return f"(async () => {{ return await {coro_js}; }})()"
                    else:
                        # It's a function reference, so we need to call it
                        return f"(async () => {{ return await {coro_js}(); }})()"
                return "(async () => {})()"  # Empty run() call
            
            if node.func.attr == "sleep":
                # Phase 33.5: asyncio.sleep(seconds) → __py.sleep(seconds)
                # Runtime: new Promise(resolve => setTimeout(resolve, seconds * 1000))
                if node.args:
                    seconds_js = _emit_expr(node.args[0])
                    return f"__py.sleep({seconds_js})"
                return "__py.sleep(0)"  # sleep() with no args = sleep(0)
    
    # Handle special Python builtins
    if isinstance(node.func, Name):
        # Phase 33.5: Handle asyncio.sleep imported as `from asyncio import sleep`
        scope = get_scope()
        if node.func.id == "sleep" and scope.is_asyncio_import("sleep"):
            if node.args:
                seconds_js = _emit_expr(node.args[0])
                return f"__py.sleep({seconds_js})"
            return "__py.sleep(0)"
        
        builtin = _emit_builtin_call(node.func.id, node.args, node.keywords)
        if builtin is not None:
            return builtin
    
    # Handle method calls with Python→JS mapping
    if isinstance(node.func, Attribute):
        method = _emit_method_call(node)
        if method is not None:
            return method
    
    # Phase 33.1: Detect class instantiations - need 'new' keyword
    # Check if this is a class instantiation (not a function call)
    is_class_instantiation = False
    is_generator_function = False
    needs_proxy_factory = False  # Phase 33.5
    if isinstance(node.func, Name):
        # Check if the name refers to a class (registered in scope)
        scope = get_scope()
        is_class_instantiation = scope.is_class_name(node.func.id)
        # Also handle cls(...) calls in @classmethod
        if not is_class_instantiation and node.func.id == "cls":
            is_class_instantiation = True
        # Phase 33.5: Check if class needs Proxy factory for attribute access
        if is_class_instantiation and scope.needs_attribute_proxy(node.func.id):
            needs_proxy_factory = True
        # Phase 33.2: Check if this is a generator function call
        # We need to wrap it with wrapGenerator to add send(), throw(), close()
        # For now, we'll detect this at runtime by checking if the result is a generator
    
    # Regular function call
    args_js = ", ".join(_emit_expr(arg) for arg in node.args)
    
    # Check if there's a spread argument (*args)
    has_spread = any(isinstance(arg, Starred) for arg in node.args)
    
    # Phase 33.2: Handle callable objects (objects with __call__ method)
    # Only apply __call__ check when we know the object is callable (from scope tracking)
    if isinstance(node.func, Name) and not is_class_instantiation:
        func_name = node.func.id
        # Only apply __call__ check if this variable is known to be a callable object
        if scope.is_callable_object(func_name):
            # Use runtime helper: __py.call(obj, ...args) to handle __call__ method
            if node.keywords:
                kw_parts = []
                for name, value in node.keywords:
                    if name:
                        kw_parts.append(f"{name}: {_emit_expr(value)}")
                    else:
                        kw_parts.append(f"...{_emit_expr(value)}")
                if has_spread:
                    kw_parts.append("__kw__: true")
                kw_js = "{" + ", ".join(kw_parts) + "}"
                if args_js:
                    return f"__py.call({func_name}, {args_js}, {kw_js})"
                else:
                    return f"__py.call({func_name}, {kw_js})"
            else:
                return f"__py.call({func_name}, {args_js})" if args_js else f"__py.call({func_name})"
    
    # Handle keyword arguments
    if node.keywords:
        # Convert to object parameter
        kw_parts = []
        for name, value in node.keywords:
            if name:  # Named kwarg
                kw_parts.append(f"{name}: {_emit_expr(value)}")
            else:  # **kwargs spread
                kw_parts.append(f"...{_emit_expr(value)}")
        
        # If there's also a spread (*args), mark kwargs so receiver can extract it
        if has_spread:
            kw_parts.append("__kw__: true")
        
        kw_js = "{" + ", ".join(kw_parts) + "}"
        if args_js:
            call = f"{func_js}({args_js}, {kw_js})"
        else:
            call = f"{func_js}({kw_js})"
        # Phase 33.5: Use Proxy factory for classes with attribute access dunders
        if needs_proxy_factory:
            return f"__py_create_{func_js}({args_js}, {kw_js})" if args_js else f"__py_create_{func_js}({kw_js})"
        return f"new {call}" if is_class_instantiation else call
    
    # Build call expression
    call = f"{func_js}({args_js})"
    
    # ============================================================================
    # GENERATOR AND ASYNC GENERATOR CALL WRAPPING (Phase 33.2+)
    # ============================================================================
    # 
    # WHAT: Wraps generator and async generator function calls with runtime helpers
    #       to add Python protocol methods (send(), throw(), close()).
    # 
    # WHY: JavaScript generators don't have send(), throw(), close() methods.
    #      Python generators support these for advanced iteration control. This
    #      wrapping provides Python compatibility.
    # 
    # HOW:
    #     1. Check if function is a known generator or async generator (via scope)
    #     2. For regular generators: wrap with wrapGenerator()
    #     3. For async generators: wrap with wrapAsyncGenerator()
    #     4. Skip wrapping in await contexts (async functions return Promises)
    #     5. Skip wrapping for class instantiations (constructors aren't generators)
    # 
    # WHO: Called by _emit_call() when emitting function call expressions.
    # 
    # WHEN: During the emission phase, after parsing and IR transformation.
    # 
    # WHERE: Part of emitter.py, called for all Call nodes.
    # 
    # Edge Cases:
    #     - Await context: Don't wrap (async functions return Promises, not generators)
    #     - Class instantiation: Don't wrap (constructors aren't generators)
    #     - Method calls: Only wrap if function name is known (not attribute access)
    #     - Nested calls: Each call is wrapped independently
    # 
    # Examples:
    #     Regular generator:
    #         Python:                          JavaScript:
    #         def gen():                       function* gen() {
    #             yield 1                          yield 1;
    #         }                               }
    #         g = gen()                       const g = wrapGenerator(gen());
    #     
    #     Async generator:
    #         Python:                          JavaScript:
    #         async def gen():                 async function* gen() {
    #             yield 1                          yield 1;
    #         }                               }
    #         g = gen()                       const g = wrapAsyncGenerator(gen());
    #     
    #     In await context (no wrapping):
    #         Python:                          JavaScript:
    #         result = await gen()             const result = await gen();
    #                                         // Not wrapped - await expects Promise
    # 
    # Related:
    #     - scope.py: is_generator_function() - checks regular generators
    #     - scope.py: is_async_generator_function() - checks async generators
    #     - generators.js: wrapGenerator() - regular generator wrapper
    #     - generators.js: wrapAsyncGenerator() - async generator wrapper
    # ============================================================================
    
    if not is_class_instantiation and isinstance(node.func, Name):
        func_name = node.func.id
        scope = get_scope()
        
        # Skip wrapping if we're in an await context
        # Reason: await expects a Promise, not a generator. Async functions return
        # Promises, and wrapping would change the return type incorrectly.
        # 
        # Example:
        #     result = await fetch_data()  # fetch_data() returns Promise, not generator
        #     # We don't want: await wrapGenerator(fetch_data())
        if scope.is_in_await_context():
            # Phase 33.5: Use Proxy factory for classes with attribute access dunders
            if needs_proxy_factory:
                return f"__py_create_{func_js}({args_js})" if args_js else f"__py_create_{func_js}()"
            return f"new {call}" if is_class_instantiation else call
        
        # Check for async generator first (more specific)
        # Async generators need wrapAsyncGenerator() which returns Promise<IteratorResult>
        if scope.is_async_generator_function(func_name):
            # Wrap with async generator runtime helper to add send(), throw(), close()
            # All methods return Promises (async generators are async)
            # 
            # The wrapper checks:
            # 1. gen exists and is not null/undefined
            # 2. gen has next() method (is a generator)
            # 3. gen has Symbol.asyncIterator (is an async generator)
            # 4. __py.generators.wrapAsyncGenerator exists (runtime loaded)
            wrapped_call = f"((gen) => (gen && typeof gen.next === 'function' && typeof gen[Symbol.asyncIterator] === 'function') ? (__py.generators && __py.generators.wrapAsyncGenerator ? __py.generators.wrapAsyncGenerator(gen) : gen) : gen)({call})"
            return wrapped_call
        
        # Check for regular generator
        # Regular generators need wrapGenerator() which returns IteratorResult
        if scope.is_generator_function(func_name):
            # Wrap with runtime helper to add send(), throw(), close()
            # All methods return synchronous IteratorResult (regular generators are sync)
            wrapped_call = f"((gen) => (gen && typeof gen.next === 'function' && typeof gen[Symbol.iterator] === 'function') ? (__py.generators && __py.generators.wrapGenerator ? __py.generators.wrapGenerator(gen) : gen) : gen)({call})"
            return wrapped_call
    
    # Phase 33.5: Use Proxy factory for classes with attribute access dunders
    if needs_proxy_factory:
        return f"__py_create_{func_js}({args_js})" if args_js else f"__py_create_{func_js}()"
    return f"new {call}" if is_class_instantiation else call


def _emit_builtin_call(name: str, args: tuple, keywords: tuple) -> Optional[str]:
    """
    Handle Python builtin function calls.
    
    Phase 18.4: Enhanced to support keyword arguments for:
    - sorted(key=, reverse=)
    - min/max(key=)
    - filter(None, items) for truthiness filtering
    - any/all with Python truthiness
    - divmod, pow, callable
    
    Phase 18.5: Generator expression optimization for:
    - sum(x for x in items) → items.reduce((a, x) => a + x, 0)
    - any(cond for x in items) → items.some(x => cond)
    - all(cond for x in items) → items.every(x => cond)
    - list(x for x in items) → [...items] or items.map(...)
    - set(x for x in items) → new Set(items.map(...))
    - min/max(x for x in items) → __py.min/max(items.map(...))
    """
    # =========================================================================
    # GENERATOR EXPRESSION OPTIMIZATION (Phase 18.5)
    # =========================================================================
    
    # Check if first argument is a generator expression
    if len(args) == 1 and isinstance(args[0], GeneratorExp):
        gen = args[0]
        optimized = _try_optimize_generator_call(name, gen, keywords)
        if optimized is not None:
            return optimized
    
    args_js = [_emit_expr(arg) for arg in args]
    kwargs = {kw[0]: _emit_expr(kw[1]) for kw in keywords}
    
    # =========================================================================
    # BUILTINS WITH KEYWORD ARGUMENT SUPPORT
    # =========================================================================
    
    # sorted(iterable, key=None, reverse=False)
    # ALWAYS use __py.sorted for correct Python semantics (string sorting, type checking)
    if name == "sorted":
        key = kwargs.get("key", "null")
        reverse = kwargs.get("reverse", "false")
        return f"__py.sorted({args_js[0]}, {key}, {reverse})"
    
    # min/max - ALWAYS use __py.min/__py.max for type checking and correct semantics
    if name == "min":
        if len(args_js) == 1:
            key = kwargs.get("key", "null")
            return f"__py.min({args_js[0]}, {key})"
        # Multiple args: min(a, b, c, ...)
        key = kwargs.get("key", "null")
        return f"__py.min([{', '.join(args_js)}], {key})"
    
    if name == "max":
        if len(args_js) == 1:
            key = kwargs.get("key", "null")
            return f"__py.max({args_js[0]}, {key})"
        # Multiple args: max(a, b, c, ...)
        key = kwargs.get("key", "null")
        return f"__py.max([{', '.join(args_js)}], {key})"
    
    # filter - use __py.filter for proper None/truthiness handling
    if name == "filter":
        if len(args_js) >= 2:
            func = args_js[0]
            iterable = args_js[1]
            return f"__py.filter({func}, {iterable})"
        return None
    
    # map with multiple iterables support
    if name == "map":
        if len(args_js) >= 2:
            func = args_js[0]
            if len(args_js) == 2:
                return f"[...{args_js[1]}].map({func})"
            # Multiple iterables - use __py.map
            return f"__py.map({func}, {', '.join(args_js[1:])})"
        return None
    
    # =========================================================================
    # NEW BUILTINS (Phase 18.4)
    # =========================================================================
    
    # any/all with Python truthiness
    if name == "any":
        return f"__py.any({args_js[0]})"
    
    if name == "all":
        return f"__py.all({args_js[0]})"
    
    # divmod returns [floordiv, mod]
    if name == "divmod":
        return f"__py.divmod({args_js[0]}, {args_js[1]})"
    
    # pow with optional modulus
    if name == "pow":
        if len(args_js) == 3:
            return f"__py.pow({args_js[0]}, {args_js[1]}, {args_js[2]})"
        # Phase 33.2: Optimize for numeric literals (use native Math.pow)
        # Use runtime helper for objects that might have __pow__ dunder method
        if len(args) >= 2 and _is_numeric(args[0]) and _is_numeric(args[1]):
            return f"Math.pow({args_js[0]}, {args_js[1]})"
        # Use runtime helper to check for __pow__ dunder method
        return f"__py.pow({args_js[0]}, {args_js[1]})"
    
    # callable
    if name == "callable":
        return f"(typeof {args_js[0]} === 'function')"
    
    # repr with Python semantics
    if name == "repr":
        return f"__py.repr({args_js[0]})"
    
    # abs - Phase 33.2: Optimize for numeric literals (use native Math.abs)
    # Use runtime helper for objects that might have __abs__ dunder method
    if name == "abs":
        if len(args) >= 1 and _is_numeric(args[0]):
            return f"Math.abs({args_js[0]})"
        # Use runtime helper to check for __abs__ dunder method
        return f"__py.abs({args_js[0]})"
    
    # =========================================================================
    # SIMPLE BUILTINS (direct mappings)
    # =========================================================================
    
    simple_builtins = {
        "len": lambda a: f"__py.len({a[0]})" if a else "0",
        "str": lambda a: f"__py.str({a[0]})" if a else "''",
        "int": lambda a: f"parseInt({a[0]})" if a else "0",
        "float": lambda a: f"parseFloat({a[0]})" if a else "0.0",
        "bool": lambda a: f"__py.bool({a[0]})" if a else "false",
        "list": lambda a: f"[...{a[0]}]" if a else "[]",
        "dict": lambda a: f"Object.fromEntries({a[0]})" if a else "{}",
        "tuple": lambda a: f"Object.freeze([...{a[0]}])" if a else "Object.freeze([])",
        "set": lambda a: f"new Set({a[0]})" if a else "new Set()",
        "frozenset": lambda a: f"Object.freeze(new Set({a[0]}))" if a else "Object.freeze(new Set())",
        "sum": lambda a: f"__py.sum({a[0]})" if len(a) == 1 else f"__py.sum({a[0]}, {a[1]})",
        "reversed": lambda a: f"[...{a[0]}].reverse()",
        "enumerate": lambda a: f"__py.enumerate({a[0]})" if len(a) == 1 else f"__py.enumerate({a[0]}, {a[1]})",
        "zip": lambda a: f"__py.zip({', '.join(a)})",
        "range": lambda a: _emit_range_call(a),
        "isinstance": lambda a: _emit_isinstance_call(a),
        "type": lambda a: f"__py.type({a[0]})",
        "hasattr": lambda a: f"({a[1]} in {a[0]})",
        "getattr": lambda a: f"({a[0]}[{a[1]}])" if len(a) == 2 else f"({a[1]} in {a[0]} ? {a[0]}[{a[1]}] : {a[2]})",
        "setattr": lambda a: f"({a[0]}[{a[1]}] = {a[2]})",
        "delattr": lambda a: f"(delete {a[0]}[{a[1]}])",
        "round": lambda a: f"Math.round({a[0]})" if len(a) == 1 else f"__py.round({a[0]}, {a[1]})",
        "ord": lambda a: f"{a[0]}.charCodeAt(0)",
        "chr": lambda a: f"String.fromCharCode({a[0]})",
        "print": lambda a: f"__py.print({', '.join(a)})" if a else "__py.print()",
        "input": lambda a: f"prompt({a[0]})" if a else 'prompt("")',
        "id": lambda a: f"(typeof {a[0]} === 'object' ? {a[0]}.__id__ ?? ({a[0]}.__id__ = Math.random()) : {a[0]})",
        "hash": lambda a: f"JSON.stringify({a[0]}).split('').reduce((a,b)=>((a<<5)-a)+b.charCodeAt(0),0)",
        "hex": lambda a: f"'0x' + {a[0]}.toString(16)",
        "oct": lambda a: f"'0o' + {a[0]}.toString(8)",
        "bin": lambda a: f"'0b' + {a[0]}.toString(2)",
        "ascii": lambda a: f"__py.ascii({a[0]})",
        "iter": lambda a: f"__py.iter({a[0]})",
        # Phase 33.2: next() works with both generators and arrays/iterables
        # Generator expressions are materialized as arrays, so we need to handle both cases
        "next": lambda a: f"__py.next({a[0]})" if len(a) == 1 else f"__py.next({a[0]}, {a[1]})",
        "slice": lambda a: f"{{start: {a[0] if len(a) > 0 else 'null'}, stop: {a[1] if len(a) > 1 else 'null'}, step: {a[2] if len(a) > 2 else 'null'}}}",
        "vars": lambda a: f"Object.entries({a[0]})" if a else "{}",
        "dir": lambda a: f"Object.keys({a[0]})" if a else "[]",
    }
    
    handler = simple_builtins.get(name)
    if handler:
        return handler(args_js)
    
    return None


def _emit_range_call(args: list[str]) -> str:
    """Emit range() call as array."""
    if len(args) == 1:
        return f"__py.range(0, {args[0]})"
    elif len(args) == 2:
        return f"__py.range({args[0]}, {args[1]})"
    else:
        return f"__py.range({args[0]}, {args[1]}, {args[2]})"


def _emit_isinstance_call(args: list[str]) -> str:
    """Emit isinstance() call, converting builtin type names to string literals."""
    if len(args) < 2:
        return f"__py.isinstance({args[0] if args else 'null'}, null)"
    
    # Check if the second argument is a builtin type name converted to __py.type(...)
    # If so, extract the type name and use it as a string literal
    type_arg = args[1]
    
    # Builtin type names that get converted to __py.type(...) in _emit_name
    builtin_types = {
        "__py.type(0)": "int",
        "__py.type('')": "str",
        "__py.type(0.0)": "float",
        "__py.type(true)": "bool",
        "__py.type([])": "list",
        "__py.type({})": "dict",
        "__py.type(new Set())": "set",
    }
    
    # Also check for bare type names (in case they weren't converted)
    bare_type_names = {
        "int": "int",
        "str": "str",
        "float": "float",
        "bool": "bool",
        "list": "list",
        "dict": "dict",
        "set": "set",
        "tuple": "tuple",
    }
    
    # If it's a builtin type conversion, use the string literal
    if type_arg in builtin_types:
        type_name = builtin_types[type_arg]
        return f"__py.isinstance({args[0]}, '{type_name}')"
    
    # If it's a bare type name, use string literal (runtime expects string or type object)
    if type_arg in bare_type_names:
        return f"__py.isinstance({args[0]}, '{type_arg}')"
    
    # Otherwise, use as-is
    return f"__py.isinstance({args[0]}, {type_arg})"


def _emit_method_call(node: Call) -> Optional[str]:
    """
    Handle Python method calls with JS mapping.
    
    Phase 18.3: Comprehensive type method dispatch with:
    - Direct mappings (same semantics)
    - Runtime helpers (different semantics)
    - Special handling (complex transformations)
    
    Phase 18.4: Standard library module.function() calls
    Phase 34.1: DOM API passthrough
    """
    if not isinstance(node.func, Attribute):
        return None
    
    obj_js = _emit_expr(node.func.value)
    method = node.func.attr
    args_js = [_emit_expr(arg) for arg in node.args]
    
    # Get keyword arguments
    kwargs = {kw[0]: _emit_expr(kw[1]) for kw in node.keywords}
    
    # =========================================================================
    # DOM API PASSTHROUGH (Phase 34.1)
    # =========================================================================
    # DOM APIs should pass through unchanged. We detect DOM calls by:
    # 1. Calls on known DOM objects (classList, dataset, style, attributes)
    # 2. Calls where the method name is a known DOM method
    # 3. Chained calls on document (document.*)
    
    # Import DOM method registry
    from pynext.transpiler.dom import is_dom_method
    
    # Check if this is a method call on a DOM object property
    # e.g., el.classList.add() or el.dataset.* or el.style.setProperty()
    DOM_OBJECT_PROPERTIES = {"classList", "dataset", "style", "attributes"}
    DOM_OBJECT_METHODS = {
        # DOMTokenList (classList) methods
        "add", "contains", "toggle", "replace", "supports", "item",
        # CSSStyleDeclaration methods
        "getPropertyValue", "setProperty", "removeProperty", "getPropertyPriority",
        # NamedNodeMap methods
        "getNamedItem", "setNamedItem", "removeNamedItem",
        # ForEach and iterator methods (also valid on NodeList, HTMLCollection)
        "forEach", "entries", "keys", "values",
    }
    
    # Element DOM methods that conflict with Python list/string methods
    # These need special detection to pass through correctly
    DOM_ELEMENT_METHODS_CONFLICTING = {
        "remove",       # el.remove() vs list.remove(item)
        "append",       # el.append(child) vs list.append(item)
        "prepend",      # el.prepend(child)
        "after",        # el.after(sibling)
        "before",       # el.before(sibling)
        "replaceWith",  # el.replaceWith(new)
        "replaceChildren",  # el.replaceChildren(...)
    }
    
    # Detect if we're calling a method on a DOM object (like classList, style, etc.)
    if isinstance(node.func.value, Attribute):
        parent_attr = node.func.value.attr
        if parent_attr in DOM_OBJECT_PROPERTIES and method in DOM_OBJECT_METHODS:
            # This is a DOM method call - pass through unchanged
            args_str = ", ".join(args_js)
            return f"{obj_js}.{method}({args_str})"
        # Also handle .classList.remove() specifically - "remove" is not in DOM_OBJECT_METHODS
        # because it conflicts with Python list.remove(), but for classList it should pass through
        if parent_attr == "classList" and method == "remove":
            args_str = ", ".join(args_js)
            return f"{obj_js}.remove({args_str})"
    
    # Check for document.* method calls (should always pass through)
    if isinstance(node.func.value, Name) and node.func.value.id == "document":
        # document.getElementById, document.querySelector, etc.
        args_str = ", ".join(args_js)
        return f"document.{method}({args_str})"
    
    # Check for window.* method calls (Phase 34.2 - should always pass through)
    if isinstance(node.func.value, Name) and node.func.value.id == "window":
        # window.getComputedStyle, window.matchMedia, etc.
        args_str = ", ".join(args_js)
        return f"window.{method}({args_str})"
    
    # Check for DOM element methods that conflict with Python list/string methods
    # We detect these by checking if:
    # 1. The method is in the conflicting set
    # 2. The method is called with arguments that don't match Python list/string patterns
    if method in DOM_ELEMENT_METHODS_CONFLICTING:
        # el.remove() with no arguments is DOM remove (vs list.remove(item) which requires an argument)
        if method == "remove" and len(args_js) == 0:
            return f"{obj_js}.remove()"
        # el.append(node) or el.append(node1, node2) - DOM append can take multiple args
        # Python list.append only takes 1 argument
        if method == "append" and len(args_js) != 1:
            args_str = ", ".join(args_js)
            return f"{obj_js}.append({args_str})"
        # For other methods in this set (prepend, after, before, etc.), pass through
        if method in {"prepend", "after", "before", "replaceWith", "replaceChildren"}:
            args_str = ", ".join(args_js)
            return f"{obj_js}.{method}({args_str})"
    
    # =========================================================================
    # STANDARD LIBRARY MODULES (Phase 18.4)
    # =========================================================================
    
    # Check if this is a stdlib module call (json.loads, math.sqrt, etc.)
    if isinstance(node.func.value, Name):
        module = node.func.value.id
        func = method
        
        # json module
        if module == "json":
            if func == "loads":
                return f"JSON.parse({args_js[0]})"
            if func == "dumps":
                indent = kwargs.get("indent", "null")
                sort_keys = kwargs.get("sort_keys", "false")
                if sort_keys != "false":
                    return f"__py.json.dumps({args_js[0]}, {indent}, {sort_keys})"
                return f"JSON.stringify({args_js[0]}, null, {indent})"
            if func in ("load", "dump"):
                return f"__py.json.{func}({', '.join(args_js)})"
        
        # math module
        if module == "math":
            # Direct Math.* mappings
            MATH_DIRECT = {
                "floor", "ceil", "trunc", "sqrt", "abs", "pow", "exp",
                "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
                "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
                "log10", "log2", "hypot", "sign"
            }
            if func in MATH_DIRECT:
                return f"Math.{func}({', '.join(args_js)})"
            
            # Constants
            MATH_CONSTANTS = {
                "pi": "Math.PI",
                "e": "Math.E",
                "tau": "(2 * Math.PI)",
                "inf": "Infinity",
                "nan": "NaN",
            }
            if func in MATH_CONSTANTS:
                return MATH_CONSTANTS[func]
            
            # Special handling
            if func == "log":
                if len(args_js) == 1:
                    return f"Math.log({args_js[0]})"
                return f"(Math.log({args_js[0]}) / Math.log({args_js[1]}))"
            if func == "fabs":
                return f"Math.abs({args_js[0]})"
            if func == "isnan":
                return f"Number.isNaN({args_js[0]})"
            if func == "isinf":
                return f"(!Number.isFinite({args_js[0]}) && !Number.isNaN({args_js[0]}))"
            if func == "isfinite":
                return f"Number.isFinite({args_js[0]})"
            if func == "degrees":
                return f"({args_js[0]} * (180 / Math.PI))"
            if func == "radians":
                return f"({args_js[0]} * (Math.PI / 180))"
            
            # Runtime helpers for complex functions
            if func in ("factorial", "gcd", "lcm", "modf", "frexp", "ldexp", "fsum", "prod", "copysign"):
                return f"__py.math.{func}({', '.join(args_js)})"
        
        # re module
        if module == "re":
            # All re functions use runtime helpers
            if func in ("match", "search", "findall", "finditer", "sub", "subn", "split", "escape", "compile", "fullmatch"):
                return f"__py.re.{func}({', '.join(args_js)})"
            # Constants
            if func in ("IGNORECASE", "I", "MULTILINE", "M", "DOTALL", "S"):
                return f"__py.re.{func}"
        
        # random module
        if module == "random":
            # Direct mappings
            if func == "random":
                return "Math.random()"
            if func == "randint":
                return f"__py.random.randint({args_js[0]}, {args_js[1]})"
            if func == "randrange":
                return f"__py.random.randrange({', '.join(args_js)})"
            if func == "choice":
                return f"__py.random.choice({args_js[0]})"
            if func == "choices":
                k = args_js[1] if len(args_js) > 1 else "1"
                weights = kwargs.get("weights", "null")
                return f"__py.random.choices({args_js[0]}, {k}, {weights})"
            if func == "sample":
                return f"__py.random.sample({args_js[0]}, {args_js[1]})"
            if func == "shuffle":
                return f"__py.random.shuffle({args_js[0]})"
            if func == "uniform":
                return f"__py.random.uniform({args_js[0]}, {args_js[1]})"
            if func in ("gauss", "normalvariate"):
                return f"__py.random.gauss({args_js[0]}, {args_js[1]})"
            if func == "seed":
                return f"__py.random.seed({args_js[0] if args_js else 'null'})"
            # Other random functions
            if func in ("expovariate", "triangular", "betavariate", "gammavariate"):
                return f"__py.random.{func}({', '.join(args_js)})"
    
    # =========================================================================
    # STRING METHODS
    # =========================================================================
    
    # Direct mappings (same semantics)
    STRING_DIRECT = {
        "lower": "toLowerCase",
        "upper": "toUpperCase",
        "startswith": "startsWith",
        "endswith": "endsWith",
        "find": "indexOf",
        "rfind": "lastIndexOf",
    }
    
    if method in STRING_DIRECT:
        return f"{obj_js}.{STRING_DIRECT[method]}({', '.join(args_js)})"
    
    # Runtime helpers (different semantics)
    STRING_RUNTIME = {
        "split": "__py.str.split",
        "rsplit": "__py.str.rsplit",
        "index": "__py.str.index",
        "rindex": "__py.str.rindex",
        "count": "__py.str.count",
        "title": "__py.str.title",
        "capitalize": "__py.str.capitalize",
        "swapcase": "__py.str.swapcase",
        "center": "__py.str.center",
        "ljust": "__py.str.ljust",
        "rjust": "__py.str.rjust",
        "zfill": "__py.str.zfill",
        "partition": "__py.str.partition",
        "rpartition": "__py.str.rpartition",
        "splitlines": "__py.str.splitlines",
        "expandtabs": "__py.str.expandtabs",
        "isdigit": "__py.str.isdigit",
        "isalpha": "__py.str.isalpha",
        "isalnum": "__py.str.isalnum",
        "isspace": "__py.str.isspace",
        "isupper": "__py.str.isupper",
        "islower": "__py.str.islower",
        "istitle": "__py.str.istitle",
        "isnumeric": "__py.str.isnumeric",
        "isdecimal": "__py.str.isdecimal",
        "isidentifier": "__py.str.isidentifier",
        "encode": "__py.str.encode",
    }
    
    if method in STRING_RUNTIME:
        all_args = [obj_js] + args_js
        return f"{STRING_RUNTIME[method]}({', '.join(all_args)})"
    
    # Special string methods
    if method == "strip":
        if args_js:
            return f"__py.str.strip({obj_js}, {args_js[0]})"
        return f"{obj_js}.trim()"
    
    if method == "lstrip":
        if args_js:
            return f"__py.str.lstrip({obj_js}, {args_js[0]})"
        return f"{obj_js}.trimStart()"
    
    if method == "rstrip":
        if args_js:
            return f"__py.str.rstrip({obj_js}, {args_js[0]})"
        return f"{obj_js}.trimEnd()"
    
    if method == "join":
        return f"{args_js[0]}.join({obj_js})"
    
    if method == "replace":
        if len(args_js) >= 3:
            # With count limit - use runtime
            return f"__py.str.replace({obj_js}, {', '.join(args_js)})"
        # Without count - use replaceAll
        return f"{obj_js}.replaceAll({', '.join(args_js)})"
    
    if method == "format":
        return f"__py.format({obj_js}, {', '.join(args_js)})"
    
    # =========================================================================
    # LIST METHODS
    # =========================================================================
    
    # Direct mappings
    LIST_DIRECT = {
        "reverse": "reverse",
    }
    
    if method in LIST_DIRECT:
        return f"{obj_js}.{LIST_DIRECT[method]}()"
    
    # Runtime helpers
    LIST_RUNTIME = {
        "remove": "__py.list.remove",
        "index": "__py.list.index",
        "count": "__py.list.count",
    }
    
    if method in LIST_RUNTIME:
        all_args = [obj_js] + args_js
        return f"{LIST_RUNTIME[method]}({', '.join(all_args)})"
    
    # Special list methods
    if method == "append":
        return f"{obj_js}.push({args_js[0]})"
    
    if method == "extend":
        return f"{obj_js}.push(...{args_js[0]})"
    
    if method == "insert":
        return f"__py.list.insert({obj_js}, {args_js[0]}, {args_js[1]})"
    
    if method == "pop":
        if args_js:
            return f"__py.list.pop({obj_js}, {args_js[0]})"
        return f"{obj_js}.pop()"
    
    if method == "copy":
        return f"[...{obj_js}]"
    
    if method == "clear":
        return f"({obj_js}.length = 0)"
    
    if method == "sort":
        # Handle key= and reverse= kwargs
        key_arg = kwargs.get("key", "null")
        reverse_arg = kwargs.get("reverse", "false")
        if key_arg != "null" or reverse_arg != "false":
            return f"__py.list.sort({obj_js}, {key_arg}, {reverse_arg})"
        # Simple sort - numeric by default
        return f"__py.list.sort({obj_js})"
    
    # =========================================================================
    # DICT METHODS
    # =========================================================================
    
    DICT_METHODS = {
        "keys": lambda: f"Object.keys({obj_js})",
        "values": lambda: f"Object.values({obj_js})",
        "items": lambda: f"__py.dict.items({obj_js})",  # Use runtime helper to preserve key types
        "copy": lambda: f"({{...{obj_js}}})",
    }
    
    if method in DICT_METHODS:
        return DICT_METHODS[method]()
    
    # dict.get(key) vs api.get() - need to check for args
    # dict.get() requires at least 1 argument (the key)
    # If no args, it's probably an HTTP .get() or similar passthrough
    if method == "get":
        if len(args_js) >= 1:
            default = args_js[1] if len(args_js) > 1 else "null"
            return f"__py.dict.get({obj_js}, {args_js[0]}, {default})"
        # No args - passthrough (e.g., api.get(), http.get())
        return None
    
    # dict.pop(key) requires at least 1 argument
    if method == "pop":
        if len(args_js) >= 1:
            if len(args_js) > 1:
                return f"__py.dict.pop({obj_js}, {args_js[0]}, {args_js[1]})"
            return f"__py.dict.pop({obj_js}, {args_js[0]})"
        # No args - passthrough (e.g., list.pop() with no args)
        return None
    
    if method == "setdefault":
        if len(args_js) >= 1:
            default = args_js[1] if len(args_js) > 1 else "null"
            return f"__py.dict.setdefault({obj_js}, {args_js[0]}, {default})"
        return None
    
    # =========================================================================
    # UPDATE METHOD - SMART DISPATCH
    # =========================================================================
    # 
    # CRITICAL: .update() is used by both dicts/sets AND signals:
    # 
    # - dict.update(other_dict)    → __py.dict.update(d, other)
    # - set.update(other_set)      → __py.set.update(s, other)
    # - signal.update(lambda x: x+1) → signal.update(x => x + 1)
    # 
    # The key insight is that signal.update() takes a FUNCTION argument,
    # while dict/set.update() takes a collection argument.
    # 
    # Heuristic:
    # 1. If argument is a lambda/function → it's signal.update()
    # 2. If object looks like a dict (literal, naming convention) → dict.update()
    # 3. If object looks like a set (naming convention) → set.update()
    # 4. Otherwise, use dict.update() as fallback (most common Python use)
    # 
    # =========================================================================
    
    if method == "update":
        # Check if the first argument is a lambda/function → signal.update()
        if node.args and _is_function_arg(node.args[0]):
            return f"{obj_js}.{method}({', '.join(args_js)})"
        
        # Check if this is clearly a set update
        if _might_be_set(node.func.value):
            all_args = [obj_js] + args_js
            return f"__py.set.update({', '.join(all_args)})"
        
        # Default to dict.update() for dict-like objects or any collection argument
        # This handles: d.update(other), config.update(new_config), etc.
        if args_js:
            return f"__py.dict.update({obj_js}, {args_js[0]})"
        return f"__py.dict.update({obj_js})"
    
    # =========================================================================
    # SET/PEEK METHODS (signal-only, not ambiguous)
    # =========================================================================
    
    if method in ("set", "peek"):
        return f"{obj_js}.{method}({', '.join(args_js)})"
    
    # =========================================================================
    # DICT-ONLY METHODS (methods that are unambiguously dict operations)
    # =========================================================================
    
    if method == "popitem":
        return f"__py.dict.popitem({obj_js})"
    
    if method == "clear" and _might_be_dict(node.func.value):
        return f"__py.dict.clear({obj_js})"
    
    # =========================================================================
    # SET METHODS (excluding 'update' which is handled above)
    # =========================================================================
    
    SET_RUNTIME = {
        "remove": "__py.set.remove",
        "discard": "__py.set.discard",
        "pop": "__py.set.pop",
        "union": "__py.set.union",
        "intersection": "__py.set.intersection",
        "difference": "__py.set.difference",
        "symmetric_difference": "__py.set.symmetric_difference",
        "intersection_update": "__py.set.intersection_update",
        "difference_update": "__py.set.difference_update",
        "symmetric_difference_update": "__py.set.symmetric_difference_update",
        "issubset": "__py.set.issubset",
        "issuperset": "__py.set.issuperset",
        "isdisjoint": "__py.set.isdisjoint",
        "copy": "__py.set.copy",
    }
    
    if method in SET_RUNTIME:
        all_args = [obj_js] + args_js
        return f"{SET_RUNTIME[method]}({', '.join(all_args)})"
    
    # Only treat "add" as set method if we're certain it's a set
    # Otherwise, let it pass through as a regular method call
    if method == "add" and _might_be_set(node.func.value):
        return f"{obj_js}.add({args_js[0]})"
    
    if method == "clear" and _might_be_set(node.func.value):
        return f"{obj_js}.clear()"
    
    # Default: pass through as-is (regular method call)
    return None


def _might_be_dict(node) -> bool:
    """Heuristic: check if node might be a dict."""
    if isinstance(node, Dict):
        return True
    if isinstance(node, Name) and node.id.endswith(('_dict', 'Dict', 'config', 'options', 'settings')):
        return True
    return False


def _might_be_set(node) -> bool:
    """Heuristic: check if node might be a set."""
    if isinstance(node, Name) and node.id.endswith(('_set', 'Set', 'seen', 'visited', 'unique')):
        return True
    return False


def _is_function_arg(node) -> bool:
    """
    Check if an IR node represents a function/lambda argument.
    
    This is used to distinguish between:
    - signal.update(lambda x: x + 1)  → function argument
    - dict.update(other_dict)         → non-function argument
    
    Returns True if the node is:
    - A Lambda node
    - A FunctionDef node (unlikely as argument)
    - A Name that looks like a function reference (ends in _fn, _func, etc.)
    """
    from .nodes import Lambda, FunctionDef, Name
    
    if isinstance(node, Lambda):
        return True
    
    if isinstance(node, FunctionDef):
        return True
    
    # Heuristic for function references
    if isinstance(node, Name):
        name = node.id
        # Common patterns for function variables
        if name.endswith(('_fn', '_func', '_callback', 'Handler', 'Callback')):
            return True
        # Common functional names
        if name in ('fn', 'func', 'callback', 'handler'):
            return True
    
    return False


def _emit_attribute(node: Attribute) -> str:
    """
    Emit attribute access.
    
    Handles special cases for stdlib module constants:
    - math.pi → Math.PI
    - math.e → Math.E
    - math.inf → Infinity
    - math.nan → NaN
    """
    # Check for stdlib module constants
    if isinstance(node.value, Name):
        module = node.value.id
        attr = node.attr
        
        # math module constants
        if module == "math":
            MATH_CONSTANTS = {
                "pi": "Math.PI",
                "e": "Math.E",
                "tau": "(2 * Math.PI)",
                "inf": "Infinity",
                "nan": "NaN",
            }
            if attr in MATH_CONSTANTS:
                return MATH_CONSTANTS[attr]
        
        # random module (less common as constants)
        # re module flags
        if module == "re":
            RE_FLAGS = {
                "IGNORECASE": "'i'",
                "I": "'i'",
                "MULTILINE": "'m'",
                "M": "'m'",
                "DOTALL": "'s'",
                "S": "'s'",
            }
            if attr in RE_FLAGS:
                return RE_FLAGS[attr]
    
    value_js = _emit_expr(node.value)
    return f"{value_js}.{node.attr}"


def _emit_subscript(node: Subscript) -> str:
    """Emit subscript access."""
    value_js = _emit_expr(node.value)
    
    # Handle slicing
    if isinstance(node.slice, Slice):
        return _emit_slice_access(value_js, node.slice)
    
    idx_js = _emit_expr(node.slice)
    
    # Use runtime for potential negative indexing
    # Always use __py.at() when is_negative is True to handle Python negative indexing semantics
    if node.is_negative:
        return f"__py.at({value_js}, {idx_js})"
    
    # Phase 33.2: Use runtime helper to check for __getitem__ dunder method
    # This handles objects with custom subscript access
    # TODO: Optimize to use direct [] for known arrays/dicts
    return f"__py.getitem({value_js}, {idx_js})"


def _emit_slice_access(value_js: str, slice_node: Slice) -> str:
    """Emit slice access: items[1:3:1]"""
    lower = "null" if slice_node.lower is None else _emit_expr(slice_node.lower)
    upper = "null" if slice_node.upper is None else _emit_expr(slice_node.upper)
    
    if slice_node.step is None:
        return f"__py.slice({value_js}, {lower}, {upper})"
    
    step = _emit_expr(slice_node.step)
    return f"__py.slice({value_js}, {lower}, {upper}, {step})"


def _emit_slice(node: Slice) -> str:
    """Emit slice node (used in delete operations)."""
    lower = "null" if node.lower is None else _emit_expr(node.lower)
    upper = "null" if node.upper is None else _emit_expr(node.upper)
    step = "null" if node.step is None else _emit_expr(node.step)
    return f"[{lower}, {upper}, {step}]"


def _emit_list(node: List) -> str:
    """Emit list literal."""
    elts_js = ", ".join(_emit_expr(elt) for elt in node.elts)
    return f"[{elts_js}]"


def _emit_dict(node: Dict) -> str:
    """Emit dict literal."""
    pairs = []
    for key, value in zip(node.keys, node.values):
        value_js = _emit_expr(value)
        if key is None:
            # Spread: **d → ...d
            pairs.append(f"...{value_js}")
        else:
            key_js = _emit_expr(key)
            # Use computed property if key isn't a simple string
            if isinstance(key, Constant) and isinstance(key.value, str):
                pairs.append(f"{key_js}: {value_js}")
            else:
                pairs.append(f"[{key_js}]: {value_js}")
    return "{" + ", ".join(pairs) + "}"


def _emit_tuple(node: Tuple) -> str:
    """Emit tuple as array."""
    elts_js = ", ".join(_emit_expr(elt) for elt in node.elts)
    return f"[{elts_js}]"


# Removed - using async_support._emit_await instead


def _emit_starred(node: Starred) -> str:
    """Emit starred (spread) expression."""
    value_js = _emit_expr(node.value)
    return f"...{value_js}"


def _emit_dict_spread(node: DictSpread) -> str:
    """Emit dict spread expression."""
    value_js = _emit_expr(node.value)
    return f"...{value_js}"


# =============================================================================
# F-STRINGS
# =============================================================================

def _needs_repr_in_fstring(expr: JSNode) -> bool:
    """
    Determine if an expression in an f-string needs __py.repr() for Python-compatible representation.
    
    Python's f-strings use str() for objects, which for collections is the same as repr():
    - Lists: ['a', 'b'] not "a,b"
    - Tuples: ('a', 'b') not "a,b"  
    - Dicts: {'a': 1} not "[object Object]"
    
    However, for primitives (int, str, bool), Python uses str() not repr():
    - f"{'hello'}" → "hello" (not "'hello'")
    - f"{42}" → "42" (same as repr, but conceptually str())
    
    FUNDAMENTAL FIX: Only use __py.repr() for collections, not primitives.
    For unknown types (PyType.ANY), we can't be sure, but we err on the side
    of using repr() since it's safer for collections (the main issue we're fixing).
    
    Returns True if the expression should use __py.repr() in f-strings.
    """
    # Direct list/tuple/dict literals - always use repr()
    if isinstance(expr, (List, Tuple, Dict)):
        return True
    
    # List comprehensions produce lists
    if isinstance(expr, ListComp):
        return True
    
    # Dict comprehensions produce dicts
    if isinstance(expr, DictComp):
        return True
    
    # For variables, check type inference
    if isinstance(expr, Name):
        type_env = get_type_env()
        if type_env is not None:
            var_type = type_env.get_type(expr.id)
            # Known collections: use repr()
            if var_type in (PyType.LIST, PyType.TUPLE, PyType.DICT):
                return True
            # Known primitives: don't use repr() (Python uses str() for primitives)
            if var_type in (PyType.INT, PyType.FLOAT, PyType.BOOL, PyType.STR, PyType.NONE, PyType.NUMBER):
                return False
            # Unknown type (PyType.ANY): use repr() to be safe for collections
            # This handles function parameters and variables where type is unknown
            # We prioritize fixing collection representation over potential string quoting
            if var_type == PyType.ANY:
                return True
    
    # For string constants, don't use repr() (Python uses str())
    if isinstance(expr, Constant) and isinstance(expr.value, str):
        return False
    
    # For other expressions (calls, attributes, etc.), be conservative
    # If we can't determine the type, use repr() to match Python's behavior for collections
    return False


def _emit_fstring(node: FString) -> str:
    """
    Emit f-string as JavaScript template literal.

    Examples:
        f"Hello {name}"    → `Hello ${name}`
        f"{x:.2f}"         → `${__py.format(x, '.2f')}`
        f"{obj!r}"         → `${__py.repr(obj)}`
        f"{val!s}"         → `${String(val)}`
        f"{items}"         → `${__py.repr(items)}`  (if items is a list/tuple/dict)
    
    Conversion characters:
        !s → String(val)
        !r → __py.repr(val) (Python repr)
        !a → __py.ascii(val) (ASCII repr)
    
    FUNDAMENTAL: Arrays/lists/tuples/dicts in f-strings use __py.repr() to match
    Python's behavior (repr() not toString()). This ensures Python-compatible
    string representation for collections.
    """
    js_parts = []
    expr_idx = 0

    for part in node.parts:
        if isinstance(part, str):
            # Literal string part - escape backticks and ${
            escaped = part.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
            js_parts.append(escaped)
        else:
            # Expression part
            expr_js = _emit_expr(part)
            
            # Get conversion and format spec
            conversion = node.conversions[expr_idx] if expr_idx < len(node.conversions) else ''
            spec = node.format_specs[expr_idx] if expr_idx < len(node.format_specs) else ''
            expr_idx += 1
            
            # Apply conversion first (before format spec)
            if conversion == 's':
                # !s → String(val)
                converted = f"String({expr_js})"
            elif conversion == 'r':
                # !r → __py.repr(val)
                converted = f"__py.repr({expr_js})"
            elif conversion == 'a':
                # !a → __py.ascii(val)
                converted = f"__py.ascii({expr_js})"
            else:
                # No explicit conversion
                # FUNDAMENTAL FIX: Use __py.fstr() for collections and unknown types
                # Python's f-strings use str() which for collections is same as repr(),
                # but for strings is different (no quotes). __py.fstr() mimics this behavior.
                # NOTE: Only apply fstr() if there's no format spec - format specs handle conversion
                if spec:
                    # Format spec will handle the conversion, so use direct expression
                    converted = expr_js
                elif _needs_repr_in_fstring(part):
                    converted = f"__py.fstr({expr_js})"
                else:
                    converted = expr_js
            
            # Apply format spec
            if spec:
                # Check for dynamic format spec (contains ${...})
                if '${' in spec:
                    # Dynamic format spec - need special handling
                    js_parts.append(f"${{__py.format({converted}, `{spec}`)}}")
                else:
                    # Static format spec
                    js_parts.append(f"${{__py.format({converted}, '{spec}')}}")
            else:
                js_parts.append(f"${{{converted}}}")

    return f"`{''.join(js_parts)}`"


# =============================================================================
# COMPREHENSIONS
# =============================================================================

# =============================================================================
# TRY/EXCEPT SUPPORT (Phase 18.6 - Critical Fix)
# =============================================================================

# =============================================================================
# CLASS EMITTERS (Phase 18.8)
# =============================================================================

def _build_params_with_defaults(args: tuple, defaults: tuple) -> str:
    """Build parameter list with default values."""
    if not args:
        return ""
    
    params = []
    num_defaults = len(defaults)
    num_args = len(args)
    
    for i, arg in enumerate(args):
        # Check if this arg has a default
        default_idx = i - (num_args - num_defaults)
        if default_idx >= 0 and default_idx < num_defaults:
            default_val = _emit_expr(defaults[default_idx])
            params.append(f"{arg} = {default_val}")
        else:
            params.append(arg)
    
    return ", ".join(params)


# =============================================================================
# ASSERT AND WALRUS EMITTERS (Phase 18.8)
# =============================================================================

def _emit_named_expr(node: NamedExpr) -> str:
    """
    Emit a walrus operator (named expression).
    
    The walrus operator is emitted as an assignment expression.
    The variable must be pre-declared by the enclosing statement emitter.
    
    Examples:
        (x := get_value())  → (x = get_value())
    
    Note: The enclosing if/while statement is responsible for
    emitting the variable declaration.
    """
    target = node.target
    value = _emit_expr(node.value)
    return f"({target} = {value})"


# =============================================================================
# IMPORT EMITTERS (Phase 33.3)
# =============================================================================

def _emit_import(node: Import, indent: int) -> str:
    """
    Emit import statement: import module [as alias]
    
    WHAT: Emits ES6 import statement for Python 'import module'.
    WHY: Converts Python imports to JavaScript ES6 imports.
    HOW: Emits 'import * as alias from path'.
    WHO: Used by emitter when emitting Import IR nodes.
    WHEN: During code generation phase.
    WHERE: Part of import system emission.
    
    Examples:
        import json → import * as json from './json.js';
        import json as j → import * as j from './json.js';
    
    Args:
        node: Import IR node
        indent: Indentation level
    
    Returns:
        JavaScript import statement
    """
    prefix = make_indent(indent)
    alias = safe_js_name(node.alias)
    path = node.path
    
    # Escape path if needed (though paths shouldn't need escaping)
    return f"{prefix}import * as {alias} from {to_js_literal(path)};"


def _emit_import_from(node: ImportFrom, indent: int) -> str:
    """
    Emit from import statement: from module import x, y [as alias]
    
    WHAT: Emits ES6 named import statement for Python 'from module import ...'.
    WHY: Converts Python from imports to JavaScript ES6 named imports.
    HOW: Emits 'import { names } from path'.
    WHO: Used by emitter when emitting ImportFrom IR nodes.
    WHEN: During code generation phase.
    WHERE: Part of import system emission.
    
    Phase 33.3: Strips 'from typing import TYPE_CHECKING' imports entirely.
    TYPE_CHECKING is a compile-time constant (False at runtime), so the import
    is not needed in JavaScript.
    
    Examples:
        from module import x, y → import { x, y } from './module.js';
        from . import utils → import { utils } from './utils.js';
        from module import x as alias → import { x as alias } from './module.js';
        from typing import TYPE_CHECKING → (stripped, not emitted)
    
    Args:
        node: ImportFrom IR node
        indent: Indentation level
    
    Returns:
        JavaScript import statement (or empty string if TYPE_CHECKING import)
    """
    # Phase 33.3: Strip 'from typing import ...' imports entirely
    # The typing module is only for type hints, which are not used at runtime
    # All typing imports should be stripped (they're compile-time only)
    if node.module == "typing":
        return ""  # Strip all typing imports (type hints only)
    
    prefix = make_indent(indent)
    path = node.path
    
    # Build named imports: { name1, name2 as alias2, ... }
    imports = []
    for original_name, alias_name in node.names:
        original_safe = safe_js_name(original_name)
        alias_safe = safe_js_name(alias_name)
        
        if original_safe == alias_safe:
            # No alias: import { x }
            imports.append(original_safe)
        else:
            # With alias: import { x as alias }
            imports.append(f"{original_safe} as {alias_safe}")
    
    imports_str = ", ".join(imports)
    return f"{prefix}import {{ {imports_str} }} from {to_js_literal(path)};"


def _emit_import_star(node: ImportStar, indent: int) -> str:
    """
    Emit star import statement: from module import *
    
    WHAT: Emits ES6 namespace import + property copying for Python 'from module import *'.
    WHY: Converts Python star imports to JavaScript namespace imports + property copying.
    HOW: Emits namespace import, then calls runtime helper to copy properties.
    WHO: Used by emitter when emitting ImportStar IR nodes.
    WHEN: During code generation phase.
    WHERE: Part of import system emission.
    
    Examples:
        from module import * → 
            import * as _module from './module.js';
            __py.star_import_esm(_module, globalThis, _module.__all__);
    
    Note: __all__ is checked at runtime. The emitter creates the namespace import
    and calls the runtime helper which respects __all__ if defined.
    
    Args:
        node: ImportStar IR node
        indent: Indentation level
    
    Returns:
        JavaScript code (import statement + property copying)
    """
    prefix = make_indent(indent)
    path = node.path
    
    # Generate a safe namespace name
    if node.module:
        module_name = node.module.split('.')[-1]  # Get last part of module name
    else:
        module_name = "module"  # Default for relative imports
    
    namespace = safe_js_name(f"_{module_name}")
    
    # Emit namespace import
    import_stmt = f"{prefix}import * as {namespace} from {to_js_literal(path)};"
    
    # Emit property copying (respects __all__ at runtime)
    # The runtime helper will check namespace.__all__ if it exists
    copy_stmt = f"{prefix}__py.star_import_esm({namespace}, globalThis, {namespace}.__all__);"
    
    return f"{import_stmt}\n{copy_stmt}"


# =============================================================================
# EMITTER DISPATCH TABLES
# =============================================================================

_EMITTERS: dict = {
    Program: _emit_program,
    Assignment: _emit_assignment,
    AugAssign: _emit_aug_assign,
    TupleUnpack: _emit_tuple_unpack,
    If: _emit_if,
    For: lambda node, indent: _emit_async_for(node, indent) if getattr(node, 'is_async', False) else _emit_for(node, indent),
    ForUnpack: _emit_for_unpack,
    While: _emit_while,
    FunctionDef: lambda node, indent: _emit_generator_function(node, indent) if _function_contains_yield(node) else _emit_function_def(node, indent),
    DecoratedFunction: _emit_decorated_function,
    Return: _emit_return,
    Pass: _emit_pass,
    Break: _emit_break,
    Continue: _emit_continue,
    Delete: _emit_delete,
    ExprStmt: _emit_expr_stmt,
    Try: _emit_try,
    # Classes (Phase 18.8)
    ClassDef: _emit_class_def,
    MethodDef: _emit_method_def,
    PropertyDef: _emit_property_def,
    PropertySetterDef: _emit_property_setter_def,
    PropertyDeleterDef: _emit_property_deleter_def,  # Phase 33.1
    # Assert (Phase 18.8)
    Assert: _emit_assert,
    # Phase 33.2: Advanced Constructs
    DunderMethod: _emit_dunder_method,
    With: _emit_with,
    Match: _emit_match,
    AsyncFunctionDef: _emit_async_function_def,
    Yield: _emit_yield,
    YieldFrom: _emit_yield_from,
    # Phase 33.3: Imports
    Import: lambda node, indent: _emit_import(node, indent),
    ImportFrom: lambda node, indent: _emit_import_from(node, indent),
    ImportStar: lambda node, indent: _emit_import_star(node, indent),
}

_EXPR_EMITTERS: dict = {
    Name: _emit_name,
    This: _emit_this,
    Constant: _emit_constant,
    BinOp: _emit_binop,
    UnaryOp: _emit_unaryop,
    Compare: _emit_compare,
    BoolOp: _emit_boolop,
    IfExp: _emit_ifexp,
    Call: _emit_call,
    Attribute: _emit_attribute,
    Subscript: _emit_subscript,
    Slice: _emit_slice,
    List: _emit_list,
    Dict: _emit_dict,
    Tuple: _emit_tuple,
    Lambda: _emit_lambda,
    Await: _emit_await,  # Phase 33.2: Updated to use async_support
    Starred: _emit_starred,
    DictSpread: _emit_dict_spread,
    # F-strings and Comprehensions
    FString: _emit_fstring,
    ListComp: _emit_list_comp,
    DictComp: _emit_dict_comp,
    SetComp: _emit_set_comp,
    GeneratorExp: _emit_generator_exp,
    # Walrus operator (Phase 18.8)
    NamedExpr: _emit_named_expr,
    # Phase 33.2: Generators
    Yield: lambda node: _emit_yield(node, 0),
    YieldFrom: lambda node: _emit_yield_from(node, 0),
}
