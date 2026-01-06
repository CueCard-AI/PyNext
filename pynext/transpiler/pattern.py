"""
PyNext Transpiler - Pattern Matching Emitters

=============================================================================
WHAT THIS FILE DOES
=============================================================================
Transpiles Python match/case statements to optimized JavaScript switch/if chains.

Handles all pattern types:
- Literal patterns (case 1, case "hello")
- Capture patterns (case x)
- Wildcard patterns (case _)
- Sequence patterns (case [a, b, *rest])
- Mapping patterns (case {"key": value})
- Class patterns (case Point(x=1, y=2))
- OR patterns (case A | B)
- AS patterns (case x as alias)
- Guard clauses (case x if condition)
- Nested patterns

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================
Python 3.10+ match/case provides powerful pattern matching. JavaScript doesn't
have this, so we transpile to optimized switch/if chains that preserve Python
semantics.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    match value:                  →    switch (true) {
        case 1: ...                   case value === 1: ...
        case [a, b]: ...              case Array.isArray(value) && ...: ...
        case _: ...                   default: ...
                                    }

Optimization:
- Literal patterns → direct === comparison
- Sequence patterns → Array.isArray() + length checks + element matching
- Mapping patterns → typeof === "object" + key-value checks
- Early exits for performance

=============================================================================
EXAMPLES
=============================================================================

Literal Pattern:
    Python:                          JavaScript:
    match cmd:                       switch (true) {
        case "quit":                     case cmd === "quit":
            exit()                          exit();
        case "help":                         break;
            show_help()                  case cmd === "help":
                                        show_help();
                                        break;
                                    }

Sequence Pattern:
    Python:                          JavaScript:
    match cmd:                       switch (true) {
        case ["move", x, y]:              case Array.isArray(cmd) && cmd.length >= 2 && cmd[0] === "move":
            move_to(x, y)                     const x = cmd[1];
                                                const y = cmd[2];
                                                move_to(x, y);
                                                break;
                                    }
"""

from __future__ import annotations

from .nodes import (
    Match, Case, Pattern,
    LiteralPattern, CapturePattern, WildcardPattern,
    SequencePattern, MappingPattern, ClassPattern,
    OrPattern, AsPattern, GuardPattern,
)
from ._internal.utils import make_indent, safe_js_name
from ._internal.scope import get_scope


def _get_emit():
    """Lazy import to avoid circular dependency."""
    from .emitter import emit
    return emit


def _get_emit_expr():
    """Lazy import to avoid circular dependency."""
    from .emitter import _emit_expr
    return _emit_expr


def _emit_match(node: Match, indent: int) -> str:
    """
    Emit match statement to optimized switch/if chains.
    
    FUNDAMENTAL FIX: Use if/else chains when guards are present to match Python's
    evaluation order (pattern first → variables in scope → guard evaluated).
    
    Examples:
        match value:              → switch (true) {
        case 1: ...                   case value === 1: ...
        case _: ...                   default: ...
                                    }
        
        match value:              → if (true) {
        case x if x > 0: ...          const x = value;
                                        if (x > 0) { ... }
                                    }
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    emit_expr = _get_emit_expr()
    from .nodes import WildcardPattern, CapturePattern, AsPattern
    from ._internal.scope import get_scope, GuardContext
    
    subject_js = emit_expr(node.subject)
    
    # Check if any case has a guard - if so, use if/else chains (matches Python evaluation order)
    has_guards = any(case.guard for case in node.cases)
    
    if has_guards:
        # Use if/else chains for guards (matches Python evaluation order)
        return _emit_match_if_else(node, subject_js, indent)
    else:
        # Use switch for performance when no guards
        return _emit_match_switch(node, subject_js, indent)


def _emit_match_if_else(node: Match, subject_js: str, indent: int) -> str:
    """
    Emit match as if/else chain - matches Python evaluation order:
    1. Pattern matches (variables captured)
    2. Guard evaluated (can use captured variables)
    3. Body executed
    
    This is the fundamental fix for guard variable scope issues.
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    emit_expr = _get_emit_expr()
    from .nodes import WildcardPattern
    from ._internal.scope import get_scope, GuardContext
    from ._internal.utils import safe_js_name
    
    lines = []
    
    for i, case in enumerate(node.cases):
        is_wildcard = isinstance(case.pattern, WildcardPattern)
        is_last = (i == len(node.cases) - 1)
        
        if is_wildcard:
            # Wildcard becomes else clause
            lines.append(f"{prefix}else {{")
            body_indent = indent + 1
            # Emit body for wildcard case
            for stmt in case.body:
                lines.append(emit(stmt, body_indent))
            lines.append(f"{prefix}}}")
        else:
            # Get pattern condition and variable declarations
            pattern_result = _emit_pattern_with_vars(case.pattern, subject_js, indent + 1)
            pattern_condition = pattern_result["condition"]
            var_decls = pattern_result["vars"]
            
            # Collect pattern variable names for guard context
            pattern_vars = set()
            for var_decl in var_decls:
                # Extract variable name from "const x = value;"
                if var_decl.startswith("const "):
                    var_name = var_decl.split("=")[0].replace("const", "").strip()
                    pattern_vars.add(var_name)
            
            # FUNDAMENTAL FIX: For guards with capture patterns, we need to declare variables
            # in an IIFE so they're available for the guard condition, and make guard part of if condition.
            # This ensures that if guard fails, we don't enter the block and fall through to next case.
            if case.guard:
                # Track guard context
                scope = get_scope()
                scope.enter_context(GuardContext(pattern_vars=pattern_vars))
                try:
                    guard_expr_js = emit_expr(case.guard)
                finally:
                    scope.exit_context()
                
                # For capture patterns, variables need to be in scope for guard
                # Use IIFE to declare vars and evaluate guard as part of condition
                if var_decls:
                    # Extract variable names and values
                    var_parts = []
                    for var_decl in var_decls:
                        if var_decl.startswith("const "):
                            # Extract "const x = value;" → ("x", "value")
                            parts = var_decl.replace("const", "").strip().split("=")
                            if len(parts) == 2:
                                var_name = parts[0].strip()
                                var_value = parts[1].strip().rstrip(";")
                                var_parts.append((var_name, var_value))
                    
                    if var_parts:
                        # Build IIFE: ((vars...) => { return guard; })(values...)
                        params = ", ".join(name for name, _ in var_parts)
                        args = ", ".join(value for _, value in var_parts)
                        iife_body = f"{{ return {guard_expr_js}; }}"
                        guard_condition = f"(({params}) => {iife_body})({args})"
                    else:
                        guard_condition = guard_expr_js
                else:
                    guard_condition = guard_expr_js
                
                # Combine pattern and guard in condition
                combined_condition = f"{pattern_condition} && {guard_condition}"
                
                if i == 0:
                    lines.append(f"{prefix}if ({combined_condition}) {{")
                else:
                    lines.append(f"{prefix}else if ({combined_condition}) {{")
                
                # Declare variables in the block (for use in body)
                for var_decl in var_decls:
                    lines.append(f"{make_indent(indent + 1)}{var_decl}")
                
                body_indent = indent + 1
            else:
                # No guard - simple pattern match
                if i == 0:
                    lines.append(f"{prefix}if ({pattern_condition}) {{")
                else:
                    lines.append(f"{prefix}else if ({pattern_condition}) {{")
                
                # Declare variables
                for var_decl in var_decls:
                    lines.append(f"{make_indent(indent + 1)}{var_decl}")
                
                body_indent = indent + 1
            
            # Emit body
            for stmt in case.body:
                lines.append(emit(stmt, body_indent))
            
            # Close pattern if block
            lines.append(f"{prefix}}}")
    
    return "\n".join(lines)


def _emit_match_switch(node: Match, subject_js: str, indent: int) -> str:
    """
    Emit match as switch statement (when no guards are present).
    
    This is optimized for performance when guards aren't needed.
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    emit_expr = _get_emit_expr()
    from .nodes import WildcardPattern
    
    lines = [f"{prefix}switch (true) {{"]
    
    for case in node.cases:
        # Check if this is a wildcard pattern (should be default)
        is_wildcard = isinstance(case.pattern, WildcardPattern)
        
        if is_wildcard:
            # Wildcard becomes default case
            lines.append(f"{make_indent(indent + 1)}default:")
            # Wrap in block scope for consistency
            lines.append(f"{make_indent(indent + 2)}{{")
            case_indent = indent + 3
            var_decls = []
        else:
            # Get pattern condition and variable declarations
            pattern_result = _emit_pattern_with_vars(case.pattern, subject_js, indent + 1)
            pattern_condition = pattern_result["condition"]
            var_decls = pattern_result["vars"]
            
            case_condition = pattern_condition
            lines.append(f"{make_indent(indent + 1)}case {case_condition}:")
            # Phase 33.2: Wrap case in block scope to isolate variable declarations
            lines.append(f"{make_indent(indent + 2)}{{")
            case_indent = indent + 3
        
        # Emit variable declarations if any
        for var_decl in var_decls:
            lines.append(f"{make_indent(case_indent)}{var_decl}")
        
        # Emit case body
        for stmt in case.body:
            lines.append(emit(stmt, case_indent))
        
        lines.append(f"{make_indent(case_indent)}break;")
        lines.append(f"{make_indent(indent + 2)}}}")  # Close block scope
    
    lines.append(f"{prefix}}}")
    
    return "\n".join(lines)


def _emit_pattern_with_vars(pattern: Pattern, subject: str, indent: int) -> dict:
    """
    Emit a pattern matching condition and variable declarations.
    
    Returns dict with:
        - "condition": JavaScript expression that evaluates to true if pattern matches
        - "vars": List of variable declaration strings (e.g., "const x = value;")
    """
    from .nodes import WildcardPattern, CapturePattern, AsPattern, SequencePattern
    from ._internal.utils import safe_js_name
    
    emit_expr = _get_emit_expr()
    
    if isinstance(pattern, LiteralPattern):
        # Literal: case 1, case "hello"
        value_js = emit_expr(pattern.value)
        return {
            "condition": f"{subject} === {value_js}",
            "vars": []
        }
    
    elif isinstance(pattern, CapturePattern):
        # Capture: case x (always matches, declares variable)
        return {
            "condition": "true",
            "vars": [f"const {safe_js_name(pattern.name)} = {subject};"]
        }
    
    elif isinstance(pattern, WildcardPattern):
        # Wildcard: case _ (always matches, no variable)
        return {
            "condition": "true",
            "vars": []
        }
    
    elif isinstance(pattern, SequencePattern):
        # Sequence: case [a, b, *rest]
        conditions = [f"Array.isArray({subject})"]
        vars = []
        
        if pattern.patterns:
            conditions.append(f"{subject}.length >= {len(pattern.patterns)}")
            
            # Match each element
            for i, pat in enumerate(pattern.patterns):
                elem_js = f"{subject}[{i}]"
                elem_result = _emit_pattern_with_vars(pat, elem_js, indent)
                conditions.append(f"({elem_result['condition']})")
                vars.extend(elem_result['vars'])
        
        if pattern.starred:
            # Starred pattern (rest elements)
            rest_js = f"{subject}.slice({len(pattern.patterns)})"
            vars.append(f"const {safe_js_name(pattern.starred)} = {rest_js};")
        
        return {
            "condition": " && ".join(conditions),
            "vars": vars
        }
    
    elif isinstance(pattern, MappingPattern):
        # Mapping: case {"key": value}
        conditions = [f"typeof {subject} === 'object'", f"{subject} !== null"]
        vars = []
        
        for key_pattern, value_pattern in zip(pattern.keys, pattern.values):
            # Extract key from key pattern (should be literal)
            if isinstance(key_pattern, LiteralPattern):
                key_js = emit_expr(key_pattern.value)
                
                # Check key exists and value matches
                value_result = _emit_pattern_with_vars(value_pattern, f"{subject}[{key_js}]", indent)
                conditions.append(f"({key_js} in {subject}) && ({value_result['condition']})")
                vars.extend(value_result['vars'])
        
        if pattern.rest:
            # **rest pattern
            rest_obj = f"Object.fromEntries(Object.entries({subject}).filter(([k]) => ![{', '.join([emit_expr(kp.value) for kp in pattern.keys if isinstance(kp, LiteralPattern)])}].includes(k)))"
            vars.append(f"const {safe_js_name(pattern.rest)} = {rest_obj};")
        
        return {
            "condition": " && ".join(conditions),
            "vars": vars
        }
    
    elif isinstance(pattern, ClassPattern):
        # Class: case Point(x=1, y=2)
        conditions = [f"{subject} instanceof {pattern.class_name}"]
        vars = []
        
        for attr_name, attr_pattern in pattern.keyword_patterns:
            attr_js = f"{subject}.{safe_js_name(attr_name)}"
            attr_result = _emit_pattern_with_vars(attr_pattern, attr_js, indent)
            conditions.append(f"({attr_result['condition']})")
            vars.extend(attr_result['vars'])
        
        return {
            "condition": " && ".join(conditions),
            "vars": vars
        }
    
    elif isinstance(pattern, OrPattern):
        # OR: case A | B
        conditions = []
        vars = []
        for pat in pattern.patterns:
            pat_result = _emit_pattern_with_vars(pat, subject, indent)
            conditions.append(f"({pat_result['condition']})")
            # Note: OR patterns don't declare vars (only first matching pattern would)
        
        return {
            "condition": " || ".join(conditions),
            "vars": vars
        }
    
    elif isinstance(pattern, AsPattern):
        # AS: case x as alias
        inner_result = _emit_pattern_with_vars(pattern.pattern, subject, indent)
        # Add alias variable
        inner_result["vars"].append(f"const {safe_js_name(pattern.alias)} = {subject};")
        return inner_result
    
    elif isinstance(pattern, GuardPattern):
        # Guard: case x if condition
        return _emit_pattern_with_vars(pattern.pattern, subject, indent)
    
    else:
        # Unknown pattern type
        return {
            "condition": "true",
            "vars": []
        }

