"""
Test utilities for transpiler tests.

Provides robust helpers for checking transpiled code output.
"""

import re
from typing import Optional


def assert_has_runtime_function(
    result: str,
    function_name: str,
    *,
    runtime_type: str = "auto",  # "auto", "regular", "dunder", "both"
    old_runtime: bool = False,
    allow_native_js: bool = False,
) -> None:
    """
    Assert that transpiled code contains a runtime function call.
    
    WHAT: Flexible check for runtime functions in transpiled code
    WHY: Tests are brittle when checking exact strings - formatting varies
    HOW: Automatically detects runtime type or accepts explicit type
    WHO: Used by all transpiler tests that check for runtime functions
    
    Args:
        result: Transpiled JavaScript code
        function_name: Name of the runtime function (e.g., "mul", "add", "bool", "eq")
        runtime_type: Type of runtime function:
            - "auto": Automatically detect (default) - checks known regular functions vs dunders
            - "regular": Check __py.{function_name} (for bool, eq, in, floordiv, mod, pow)
            - "dunder": Check __py.dunders.{function_name} (for add, mul, sub, etc.)
            - "both": Check both patterns
        old_runtime: If True, also check for old runtime patterns (backwards compat)
        allow_native_js: If True, also accept native JS operators
    
    Examples:
        # Auto-detect (recommended)
        assert_has_runtime_function(result, "bool")      # Checks __py.bool
        assert_has_runtime_function(result, "add")       # Checks __py.dunders.add
        
        # Explicit type
        assert_has_runtime_function(result, "floordiv", runtime_type="regular")
        assert_has_runtime_function(result, "mul", runtime_type="dunder")
    """
    # Regular runtime functions (NOT dunders) - these stay as __py.*
    # Note: floordiv, mod, pow are actually dunders (__py.dunders.*) in Phase 33.3
    REGULAR_RUNTIME_FUNCTIONS = {
        "bool", "eq", "in",
        "abs", "str", "len", "min", "max", "print"
    }
    
    patterns = []
    
    # Determine runtime type
    if runtime_type == "auto":
        if function_name in REGULAR_RUNTIME_FUNCTIONS:
            check_regular = True
            check_dunder = False
        else:
            check_regular = False
            check_dunder = True
    elif runtime_type == "regular":
        check_regular = True
        check_dunder = False
    elif runtime_type == "dunder":
        check_regular = False
        check_dunder = True
    elif runtime_type == "both":
        check_regular = True
        check_dunder = True
    else:
        raise ValueError(f"Invalid runtime_type: {runtime_type}. Must be 'auto', 'regular', 'dunder', or 'both'")
    
    # Build patterns
    if check_regular:
        # Regular runtime: __py.{function_name}
        patterns.append(rf"__py\.{re.escape(function_name)}\s*\(")
        patterns.append(rf"__py\.{re.escape(function_name)}[^a-zA-Z0-9_]")  # Without parens
    
    if check_dunder:
        # Dunder runtime: __py.dunders.{function_name}
        patterns.append(rf"__py\.dunders\.{re.escape(function_name)}\s*\(")
        patterns.append(rf"__py\.dunders\.{re.escape(function_name)}[^a-zA-Z0-9_]")  # Without parens
    
    if old_runtime:
        # Old runtime patterns (for backwards compatibility)
        patterns.append(rf"__py\.{re.escape(function_name)}\s*\(")
        patterns.append(rf"__py\.{re.escape(function_name)}[^a-zA-Z0-9_]")
    
    if allow_native_js:
        # Native JS operators (for type-aware optimizations)
        native_ops = {
            "mul": r"\*\s",
            "add": r"\+\s",
            "sub": r"-\s",
            "div": r"/\s",
            "mod": r"%\s",
            "pow": r"\*\*\s",
        }
        if function_name in native_ops:
            patterns.append(native_ops[function_name])
    
    # Check if any pattern matches
    for pattern in patterns:
        if re.search(pattern, result):
            return
    
    # Build error message
    expected = []
    if check_regular:
        expected.append(f"__py.{function_name}")
    if check_dunder:
        expected.append(f"__py.dunders.{function_name}")
    if old_runtime:
        expected.append(f"__py.{function_name} (old)")
    if allow_native_js:
        expected.append("native JS operator")
    
    raise AssertionError(
        f"Expected one of {', '.join(expected)} in transpiled code, but found:\n{result[:200]}..."
    )


def assert_has_operator_pattern(
    result: str,
    operator: str,
    *,
    prefer_dunders: bool = True,
) -> None:
    """
    Assert that code contains an operator (flexible check).
    
    For operator tests, checks for either runtime function or native JS.
    
    Args:
        result: Transpiled JavaScript code
        operator: Operator name ("mul", "add", "sub", "div", "mod", "pow")
        prefer_dunders: If True, prefer __py.dunders.* over native JS
    """
    # Map operator names to patterns
    operator_patterns = {
        "mul": (r"\*\s", "__py.dunders.mul"),
        "add": (r"\+\s", "__py.dunders.add"),
        "sub": (r"-\s", "__py.dunders.sub"),
        "div": (r"/\s", "__py.dunders.truediv"),
        "mod": (r"%\s", "__py.dunders.mod"),
        "pow": (r"\*\*\s", "__py.dunders.pow"),
    }
    
    if operator not in operator_patterns:
        raise ValueError(f"Unknown operator: {operator}")
    
    native_pattern, dunder_name = operator_patterns[operator]
    
    # Check for dunder runtime (preferred)
    dunder_func_name = dunder_name.split('.')[-1]
    if prefer_dunders and re.search(rf"__py\.dunders\.{re.escape(dunder_func_name)}", result):
        return
    
    # Check for native JS
    if re.search(native_pattern, result):
        return
    
    # If prefer_dunders, we should have found dunders
    if prefer_dunders:
        raise AssertionError(
            f"Expected {dunder_name} in transpiled code, but found:\n{result[:200]}..."
        )
    else:
        raise AssertionError(
            f"Expected {operator} operator or {dunder_name} in:\n{result[:200]}..."
        )


def assert_has_function_call_with_args(
    result: str,
    func_name: str,
    *args,
    allow_parentheses_around_negative_literals: bool = True,
) -> None:
    """
    Assert that transpiled code contains a function call with specific arguments.
    
    WHAT: Flexible check for function calls with arguments, handling parentheses around negative literals
    WHY: Emitter wraps negative number literals in parentheses for precedence, but tests expect them without
    HOW: Uses regex to match function calls, allowing optional parentheses ONLY around negative number literals
    WHO: Used by tests checking for __py.at(), __py.slice(), etc.
    
    Args:
        result: Transpiled JavaScript code
        func_name: Function name (e.g., "at", "slice")
        *args: Expected argument patterns (strings like "items", "-1", "null", "i")
        allow_parentheses_around_negative_literals: If True, allow parentheses around negative number literals
    
    Examples:
        # Check for __py.at(items, -1) or __py.at(items, (-1))
        assert_has_function_call_with_args(result, "at", "items", "-1")
        
        # Check for __py.slice(items, null, null, -1) or __py.slice(items, null, null, (-1))
        assert_has_function_call_with_args(result, "slice", "items", "null", "null", "-1")
        
        # Variables never have parentheses: __py.at(items, i)
        assert_has_function_call_with_args(result, "at", "items", "i")
    """
    # Build regex pattern for each argument
    arg_patterns = []
    for arg in args:
        # Check if this is a negative number literal (e.g., "-1", "-2", "-10")
        # Pattern: starts with "-", followed by digits only
        is_negative_literal = arg.startswith("-") and len(arg) > 1 and arg[1:].isdigit()
        
        if is_negative_literal and allow_parentheses_around_negative_literals:
            # Negative literal: allow with or without parentheses
            # Pattern matches: "-1" or "(-1)"
            # Escape the minus sign and digits, but allow optional parentheses
            digits = arg[1:]  # Everything after the minus sign
            arg_patterns.append(rf"\s*(-{re.escape(digits)}|\(-{re.escape(digits)}\))")
        else:
            # Non-negative literal or variable: match exactly (no parentheses)
            # Escape the argument but allow whitespace
            arg_patterns.append(rf"\s*{re.escape(arg)}")
    
    # Join argument patterns with comma and optional whitespace
    args_pattern = r",".join(arg_patterns)
    
    # Build full pattern: __py.{func_name}(args)
    pattern = rf"__py\.{re.escape(func_name)}\s*\(\s*{args_pattern}\s*\)"
    
    if not re.search(pattern, result):
        # Build expected string for error message
        expected_args = ", ".join(args)
        expected = f"__py.{func_name}({expected_args})"
        if allow_parentheses_around_negative_literals:
            expected += " (with optional parentheses around negative literals)"
        
        raise AssertionError(
            f"Expected {expected} in transpiled code, but found:\n{result[:200]}..."
        )


def assert_has_assignment_with_operation(
    result: str,
    target: str,
    operator: str,
    *,
    allow_native_js: bool = True,
    allow_old_runtime: bool = False,
) -> None:
    """
    Assert that transpiled code contains an assignment with a specific operation.
    
    WHAT: Flexible check for assignment patterns like "target = target op value"
    WHY: Tests for attribute augmented assignments are brittle - they check exact strings
         but implementation uses different runtime patterns based on operand types
    HOW: Checks for assignment pattern, then flexibly matches the RHS operation
    WHO: Used by tests checking augmented assignment to attributes (Segment 8)
    
    Args:
        result: Transpiled JavaScript code
        target: Assignment target (e.g., "this.count", "this.value")
        operator: Operation name ("add", "sub", "mul", "div", "floordiv", "mod", "pow")
        allow_native_js: If True, accept native JS operators (default: True)
        allow_old_runtime: If True, also check for old runtime patterns (default: False)
    
    Examples:
        # Check for: this.count = __py.dunders.add(this.count, 1) OR this.count = (this.count + 1)
        assert_has_assignment_with_operation(result, "this.count", "add")
        
        # Check for: this.value = __py.dunders.sub(this.value, 5) OR this.value = (this.value - 5)
        assert_has_assignment_with_operation(result, "this.value", "sub")
    """
    # Map operator names to JS operators and runtime function names
    operator_info = {
        "add": ("+", "add"),
        "sub": ("-", "sub"),
        "mul": ("*", "mul"),
        "div": ("/", "truediv"),
        "floordiv": ("//", "floordiv"),
        "mod": ("%", "mod"),
        "pow": ("**", "pow"),
    }
    
    if operator not in operator_info:
        raise ValueError(f"Unknown operator: {operator}")
    
    js_op, runtime_name = operator_info[operator]
    
    # Escape target for regex
    target_pattern = re.escape(target)
    
    # Build patterns for the RHS (right-hand side of assignment)
    rhs_patterns = []
    
    # Pattern 1: Dunder runtime (current implementation) - regular ops
    # this.count = __py.dunders.add(this.count, ...)
    rhs_patterns.append(
        rf"__py\.dunders\.{re.escape(runtime_name)}\s*\(\s*{target_pattern}\s*,"
    )
    
    # Pattern 1b: Dunder runtime - in-place operators (iadd, imul, etc.)
    # total = __py.dunders.iadd(total, item)
    inplace_name = f"i{runtime_name}" if not runtime_name.startswith("i") else runtime_name
    rhs_patterns.append(
        rf"__py\.dunders\.{re.escape(inplace_name)}\s*\(\s*{target_pattern}\s*,"
    )
    
    # Pattern 2: Native JS operator (when both operands are numeric)
    # this.value = (this.value - 5)
    if allow_native_js:
        # Match: (target op value) or target op value (with or without parens)
        if operator == "floordiv":
            # Floor div uses Math.floor, not native operator
            rhs_patterns.append(rf"Math\.floor\s*\(\s*{target_pattern}\s*/\s*")
        elif operator == "pow":
            rhs_patterns.append(rf"\({target_pattern}\s*\*\*\s*")
        else:
            # Escape JS operator (handle * specially)
            js_op_escaped = re.escape(js_op) if js_op != "*" else r"\*"
            rhs_patterns.append(rf"\({target_pattern}\s*{js_op_escaped}\s*")
    
    # Pattern 3: Old runtime (for backward compatibility)
    if allow_old_runtime:
        # this.count = __py.add(this.count, ...)
        rhs_patterns.append(
            rf"__py\.{re.escape(runtime_name)}\s*\(\s*{target_pattern}\s*,"
        )
    
    # Build full assignment pattern: target = <any of the RHS patterns>
    assignment_pattern = rf"{target_pattern}\s*=\s*(?:{'|'.join(rhs_patterns)})"
    
    if not re.search(assignment_pattern, result):
        expected = []
        expected.append(f"__py.dunders.{runtime_name}")
        if allow_native_js:
            expected.append(f"native JS operator ({js_op})")
        if allow_old_runtime:
            expected.append(f"__py.{runtime_name} (old)")
        
        raise AssertionError(
            f"Expected assignment '{target} = <operation>' with one of {', '.join(expected)} "
            f"in transpiled code, but found:\n{result[:300]}..."
        )

