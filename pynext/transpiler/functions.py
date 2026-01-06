from __future__ import annotations

"""
PyNext Transpiler - Function Emitters

Phase 33.1: Function transpilation including:
- Function definitions with *args and **kwargs
- Decorators (simple and parameterized)
- Lambda expressions
- Parameter building utilities

Phase 33.3: Scope-aware import emission for function-scoped imports.
"""

from typing import List
from .nodes import FunctionDef, DecoratedFunction, Decorator, Lambda, Import, ImportFrom, ImportStar, Assignment, Attribute, Name
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


def _is_mutable_default(node: JSNode) -> bool:
    """Check if a default argument value is mutable (list, dict, set)."""
    from .nodes import List, Dict, SetComp
    # Note: Python set literals {1, 2, 3} are parsed as SetComp in our IR
    # For now, we only handle List and Dict. Set literals are less common as defaults.
    return isinstance(node, (List, Dict))


def _is_builtin_import_assignment(node: JSNode) -> bool:
    """
    Check if an Assignment node is a built-in module import.
    
    WHAT: Detects Assignment nodes that represent built-in imports (const json = __py.json;).
    WHY: Built-in imports are parsed as Assignment nodes, not Import nodes.
    HOW: Checks if value is Attribute(value=Name(id="__py"), attr=...).
    WHO: Used to identify function-scoped built-in imports.
    WHEN: When scanning function body for imports.
    WHERE: Part of scope-aware import emission.
    
    Args:
        node: IR node to check
    
    Returns:
        True if node is a built-in import assignment
    """
    if not isinstance(node, Assignment):
        return False
    
    # Check if value is __py.module pattern
    if isinstance(node.value, Attribute):
        if isinstance(node.value.value, Name) and node.value.value.id == "__py":
            # This is __py.something - likely a built-in import
            return True
    
    return False


def _emit_function_def(node: FunctionDef, indent: int) -> str:
    """
    Emit function definition with support for *args and **kwargs.
    
    Examples:
        def foo(a, b):           → function foo(a, b) { ... }
        def bar(*args):          → function bar(...args) { ... }
        def baz(**kwargs):       → function baz(kwargs = {}) { ... }
        def mixed(a, *args):     → function mixed(a, ...args) { ... }
        def both(*args, **kw):   → function both(...args) { const kw = args.pop() ?? {}; ... }
        def append(item, lst=[]): → const _default_lst = []; function append(item, lst = _default_lst) { ... }
    """
    prefix = make_indent(indent)
    inner_prefix = make_indent(indent + 1)
    name = safe_js_name(node.name)
    lines = []
    
    # Phase 33.1: Handle mutable defaults (lists, dicts, sets)
    # Python creates these once at function definition time, JavaScript creates them each call
    # Solution: Create constants outside the function and reference them
    mutable_defaults: list[Tuple[str, JSNode, str]] = []  # (const_name, default_node, param_name)
    all_pos_args = list(node.posonly_args) + list(node.args)
    all_defaults = list(node.posonly_defaults) + list(node.defaults)
    num_defaults = len(all_defaults)
    num_required = len(all_pos_args) - num_defaults
    
    # Check for mutable defaults in positional args
    for i, arg in enumerate(all_pos_args):
        if i >= num_required:
            default_idx = i - num_required
            default = all_defaults[default_idx]
            if default is not None and _is_mutable_default(default):
                const_name = f"_default_{safe_js_name(arg)}"
                mutable_defaults.append((const_name, default, safe_js_name(arg)))
    
    # Check for mutable defaults in keyword-only args
    for i, arg in enumerate(node.kwonly_args):
        if i < len(node.kwonly_defaults):
            default = node.kwonly_defaults[i]
            if default is not None and _is_mutable_default(default):
                const_name = f"_default_{safe_js_name(arg)}"
                mutable_defaults.append((const_name, default, safe_js_name(arg)))
    
    # Create constants for mutable defaults before the function
    _emit_expr = _get_emit_expr()
    for const_name, default_node, param_name in mutable_defaults:
        default_js = _emit_expr(default_node)
        lines.append(f"{prefix}const {const_name} = {default_js};")
    
    # Build parameter list with defaults, vararg, and kwarg
    # For mutable defaults, use the constant name instead of the literal
    params = _build_params_full(node, mutable_defaults)
    params_js = ", ".join(params)
    
    # async or regular function
    if node.is_async:
        lines.append(f"{prefix}async function {name}({params_js}) {{")
    else:
        lines.append(f"{prefix}function {name}({params_js}) {{")
    
    # Enter new ISOLATED scope for function body
    scope = get_scope()
    scope.enter_function_scope()
    
    # Declare parameters in function scope
    # Phase 33.1: Include positional-only args (they're combined with regular args in params)
    for arg in node.posonly_args:
        scope.declare(safe_js_name(arg))
    for arg in node.args:
        scope.declare(safe_js_name(arg))
    if node.vararg:
        scope.declare(safe_js_name(node.vararg))
    if node.kwarg:
        scope.declare(safe_js_name(node.kwarg))
    for arg in node.kwonly_args:
        scope.declare(safe_js_name(arg))
    
    # Handle *args with **kwargs or keyword-only args: extract kwargs from last arg
    # In JS we can't have params after rest, so kwargs is passed as last positional
    if node.vararg and (node.kwarg or node.kwonly_args):
        vararg_name = safe_js_name(node.vararg)
        kwarg_name = safe_js_name(node.kwarg) if node.kwarg else "__kwargs__"
        # Extract kwargs from last argument if it's marked as kwargs
        lines.append(f"{inner_prefix}const {kwarg_name} = ({vararg_name}.length > 0 && {vararg_name}[{vararg_name}.length - 1]?.__kw__) ? {vararg_name}.pop() : {{}};")
    
    # Handle keyword-only args when there's a vararg (they come from kwargs)
    if node.vararg and node.kwonly_args:
        kwarg_name = safe_js_name(node.kwarg) if node.kwarg else "__kwargs__"
        for i, arg in enumerate(node.kwonly_args):
            arg_name = safe_js_name(arg)
            default = node.kwonly_defaults[i] if i < len(node.kwonly_defaults) else None
            if default:
                _emit_expr = _get_emit_expr()
                default_js = _emit_expr(default)
                lines.append(f"{inner_prefix}const {arg_name} = {kwarg_name}.{arg_name} ?? {default_js};")
            else:
                lines.append(f"{inner_prefix}const {arg_name} = {kwarg_name}.{arg_name};")
    
    # Phase 33.1: Handle keyword-only args when there's NO vararg (they're in params as object destructuring)
    # No extra code needed - they're already in the parameter list as {x, y = 10} = {}
    
    # Phase 33.1: Declare positional-only args in scope (they're combined with regular args in params)
    # No extra code needed - they're already declared above with regular args
    
    # Phase 33.3: Handle function-scoped imports
    # Scan body for imports and emit them as local assignments at function start
    # This creates local bindings that shadow the hoisted global imports (matching Python semantics)
    emit = _get_emit()
    import_assignments = []
    body_statements = []
    
    for stmt in node.body:
        if isinstance(stmt, Import):
            # Function-scoped regular module import: create local binding
            # const json = json; (reference hoisted import)
            assignment = _emit_function_scoped_import(stmt, inner_prefix)
            if assignment:
                import_assignments.append(assignment)
                # Declare the variable in function scope
                scope.declare(safe_js_name(stmt.alias))
        elif isinstance(stmt, ImportFrom):
            # Function-scoped from import: create local bindings
            assignments = _emit_function_scoped_import_from(stmt, inner_prefix)
            import_assignments.extend(assignments)
            # Declare all imported names in function scope
            for original_name, alias_name in stmt.names:
                scope.declare(safe_js_name(alias_name))
        elif isinstance(stmt, ImportStar):
            # Function-scoped star import: handled specially
            assignment = _emit_function_scoped_import_star(stmt, inner_prefix)
            if assignment:
                import_assignments.append(assignment)
        elif _is_builtin_import_assignment(stmt):
            # Function-scoped built-in import (Assignment node with __py.* value)
            # Emit as const (imports are never reassigned)
            from .nodes import Assignment
            if isinstance(stmt, Assignment):
                target = safe_js_name(stmt.target)
                _emit_expr = _get_emit_expr()
                value_js = _emit_expr(stmt.value)
                import_assignments.append(f"{inner_prefix}const {target} = {value_js};")
                # Declare the variable in function scope
                scope.declare(target)
        else:
            body_statements.append(stmt)
    
    # Emit import assignments first, then other statements
    for assignment in import_assignments:
        lines.append(assignment)
    
    for stmt in body_statements:
        lines.append(emit(stmt, indent + 1))
    
    # Exit function scope
    scope.exit_scope()
    
    lines.append(f"{prefix}}}")
    return "\n".join(lines)


def _emit_decorated_function(node: DecoratedFunction, indent: int) -> str:
    """
    Emit decorated function.
    
    Decorators are applied in reverse order (bottom-up).
    
    Examples:
        @memoize                    → const fib = __py.memoize(function fib(n) {...});
        def fib(n): ...
        
        @debounce(300)              → const search = __py.debounce(300)(function search(q) {...});
        def search(q): ...
        
        @log_calls                  → const foo = __py.log_calls(__py.memoize(function foo() {...}));
        @memoize
        def foo(): ...
    """
    prefix = make_indent(indent)
    inner_prefix = make_indent(indent + 1)
    func = node.function
    name = safe_js_name(func.name)
    
    # Build the inner function expression with full params
    params = _build_params_full(func)
    params_js = ", ".join(params)
    
    # Enter new ISOLATED scope for function body
    scope = get_scope()
    scope.enter_function_scope()
    
    # Declare parameters in function scope
    # Phase 33.1: Include positional-only args
    for arg in func.posonly_args:
        scope.declare(safe_js_name(arg))
    for arg in func.args:
        scope.declare(safe_js_name(arg))
    if func.vararg:
        scope.declare(safe_js_name(func.vararg))
    if func.kwarg:
        scope.declare(safe_js_name(func.kwarg))
    for arg in func.kwonly_args:
        scope.declare(safe_js_name(arg))
    
    # Build preamble for *args with **kwargs or keyword-only args handling
    preamble_lines = []
    if func.vararg and (func.kwarg or func.kwonly_args):
        vararg_name = safe_js_name(func.vararg)
        kwarg_name = safe_js_name(func.kwarg) if func.kwarg else "__kwargs__"
        preamble_lines.append(f"{inner_prefix}const {kwarg_name} = ({vararg_name}.length > 0 && {vararg_name}[{vararg_name}.length - 1]?.__kw__) ? {vararg_name}.pop() : {{}};")
    
    # Handle keyword-only args when there's a vararg (they come from kwargs)
    if func.vararg and func.kwonly_args:
        kwarg_name = safe_js_name(func.kwarg) if func.kwarg else "__kwargs__"
        for i, arg in enumerate(func.kwonly_args):
            arg_name = safe_js_name(arg)
            default = func.kwonly_defaults[i] if i < len(func.kwonly_defaults) else None
            if default:
                _emit_expr = _get_emit_expr()
                default_js = _emit_expr(default)
                preamble_lines.append(f"{inner_prefix}const {arg_name} = {kwarg_name}.{arg_name} ?? {default_js};")
            else:
                preamble_lines.append(f"{inner_prefix}const {arg_name} = {kwarg_name}.{arg_name};")
    
    # Phase 33.1: When there's NO vararg, keyword-only args are in params as object destructuring
    # No extra code needed - they're already in the parameter list
    
    # Phase 33.3: Handle function-scoped imports
    # Scan body for imports and emit them as local assignments at function start
    emit = _get_emit()
    import_assignments = []
    body_statements = []
    
    for stmt in func.body:
        if isinstance(stmt, Import):
            # Function-scoped regular module import: create local binding
            assignment = _emit_function_scoped_import(stmt, inner_prefix)
            if assignment:
                import_assignments.append(assignment)
                # Declare the variable in function scope
                scope.declare(safe_js_name(stmt.alias))
        elif isinstance(stmt, ImportFrom):
            # Function-scoped from import: create local bindings
            assignments = _emit_function_scoped_import_from(stmt, inner_prefix)
            import_assignments.extend(assignments)
            # Declare all imported names in function scope
            for original_name, alias_name in stmt.names:
                scope.declare(safe_js_name(alias_name))
        elif isinstance(stmt, ImportStar):
            # Function-scoped star import: handled specially
            assignment = _emit_function_scoped_import_star(stmt, inner_prefix)
            if assignment:
                import_assignments.append(assignment)
        elif _is_builtin_import_assignment(stmt):
            # Function-scoped built-in import (Assignment node with __py.* value)
            # Emit as const (imports are never reassigned)
            from .nodes import Assignment
            if isinstance(stmt, Assignment):
                target = safe_js_name(stmt.target)
                _emit_expr = _get_emit_expr()
                value_js = _emit_expr(stmt.value)
                import_assignments.append(f"{inner_prefix}const {target} = {value_js};")
                # Declare the variable in function scope
                scope.declare(target)
        else:
            body_statements.append(stmt)
    
    # Emit import assignments first, then other statements
    body_lines = []
    for assignment in import_assignments:
        body_lines.append(assignment)
    
    for stmt in body_statements:
        body_lines.append(emit(stmt, indent + 1))
    
    # Combine preamble and body
    all_body = preamble_lines + body_lines
    body_js = "\n".join(all_body)
    
    # Exit function scope
    scope.exit_scope()
    
    # Build the function expression
    # Phase 33.2+: Check if this is an async generator (async def with yield)
    # or regular async function (async def without yield)
    from .nodes import AsyncFunctionDef
    from .generators import _method_contains_yield
    
    if isinstance(func, AsyncFunctionDef):
        # Check if this async function contains yield (making it an async generator)
        is_async_generator = _method_contains_yield(func)
        if is_async_generator:
            # Async generator: emit as async function*
            # Mark in scope so calls can be wrapped with wrapAsyncGenerator
            scope = get_scope()
            scope.declare_async_generator_function(name)
            func_expr = f"async function* {name}({params_js}) {{\n{body_js}\n{prefix}}}"
        else:
            # Regular async function: emit as async function
            func_expr = f"async function {name}({params_js}) {{\n{body_js}\n{prefix}}}"
    else:
        func_expr = f"function {name}({params_js}) {{\n{body_js}\n{prefix}}}"
    
    # Apply decorators in reverse order (bottom decorator is applied first)
    result = func_expr
    for decorator in reversed(node.decorators):
        decorator_js = _emit_decorator(decorator)
        result = f"{decorator_js}({result})"
    
    # Declare the function name in scope
    scope = get_scope()
    scope.declare(name)
    
    return f"{prefix}const {name} = {result};"


def _emit_decorator(decorator: Decorator) -> str:
    """
    Emit a single decorator call.
    
    Examples:
        @memoize       → __py.memoize
        @debounce(300) → __py.debounce(300)
        @log_calls     → __py.log_calls
    """
    name = decorator.name
    
    # Check if it's a known PyNext decorator
    BUILTIN_DECORATORS = {
        "memoize", "debounce", "throttle", "once", "retry",
        "deprecated", "log_calls", "timed", "cached_property",
        "validate", "lock", "compose"
    }
    
    if name in BUILTIN_DECORATORS:
        prefix = "__py."
    elif "." in name:
        # Module-qualified decorator
        prefix = ""
    else:
        # Custom decorator
        prefix = ""
    
    has_args = decorator.args or decorator.kwargs or decorator.starred_args or decorator.double_starred_kwargs
    
    if has_args:
        # Decorator with arguments: @debounce(300), @validate(*rules), @config(**settings)
        parts = []
        
        _emit_expr = _get_emit_expr()
        # Regular positional args
        parts.extend(_emit_expr(arg) for arg in decorator.args)
        
        # Starred args (*items)
        parts.extend(f"...{_emit_expr(arg)}" for arg in decorator.starred_args)
        
        # Named kwargs (key=value)
        parts.extend(f"{k}: {_emit_expr(v)}" for k, v in decorator.kwargs)
        
        # Double-starred kwargs (**settings) - spread into a single object if present
        if decorator.double_starred_kwargs:
            spreads = [f"...{_emit_expr(kw)}" for kw in decorator.double_starred_kwargs]
            if decorator.kwargs:
                # Mix kwargs with spread: {key: val, ...settings}
                kwargs_parts = [f"{k}: {_emit_expr(v)}" for k, v in decorator.kwargs]
                parts = parts[:-len(decorator.kwargs)]  # Remove named kwargs, will add as object
                parts.append("{" + ", ".join(kwargs_parts + spreads) + "}")
            else:
                # Just spreads: {...settings}
                parts.append("{" + ", ".join(spreads) + "}")
        
        return f"{prefix}{name}({', '.join(parts)})"
    else:
        # Simple decorator: @memoize
        return f"{prefix}{name}"


def _build_params(args: tuple, defaults: tuple) -> list[str]:
    """Build parameter list with defaults."""
    params = []
    # defaults are aligned to the end of args
    num_defaults = len(defaults)
    num_required = len(args) - num_defaults
    
    for i, arg in enumerate(args):
        arg_name = safe_js_name(arg)
        if i >= num_required:
            # Has default
            default_idx = i - num_required
            _emit_expr = _get_emit_expr()
            default_js = _emit_expr(defaults[default_idx])
            params.append(f"{arg_name} = {default_js}")
        else:
            params.append(arg_name)
    
    return params


def _build_params_full(node, mutable_defaults: Optional[list[Tuple[str, JSNode, str]]] = None) -> list[str]:
    """
    Build full parameter list including positional-only, *args, **kwargs, and keyword-only.
    
    Phase 33.1: Enhanced to handle positional-only args and proper keyword-only args.
    
    Examples:
        def foo(a, b):              → ['a', 'b']
        def bar(*args):             → ['...args']
        def baz(**kwargs):          → ['kwargs = {}']
        def mixed(a, *args):        → ['a', '...args']
        def posonly(x, y, /, z):    → ['x', 'y', 'z'] (posonly combined with regular)
        def kwonly(*, x, y=10):     → ['{x, y = 10} = {}'] (object destructuring)
        def full(a, *args, **kw):   → ['a', '...args'] (kw extracted in body)
    """
    params = []
    
    # Combine positional-only and regular positional args for JavaScript
    # JavaScript doesn't distinguish, but we track them separately for documentation
    all_pos_args = list(node.posonly_args) + list(node.args)
    
    # Combine defaults: positional-only defaults (padded with None) + regular defaults (padded with None)
    # Both are already padded to match their respective arg lists
    posonly_defaults = getattr(node, 'posonly_defaults', ())
    regular_defaults = getattr(node, 'defaults', ())
    all_defaults = list(posonly_defaults) + list(regular_defaults)
    
    # Build params with defaults
    # Defaults are aligned to the END, so we need to match them correctly
    num_defaults = len(all_defaults)
    num_required = len(all_pos_args) - num_defaults
    
    # Build a lookup map for mutable defaults
    mutable_map = {}
    if mutable_defaults:
        for const_name, default_node, param_name in mutable_defaults:
            mutable_map[param_name] = const_name
    
    for i, arg in enumerate(all_pos_args):
        arg_name = safe_js_name(arg)
        # Check if this arg has a default (defaults are aligned to the end)
        if i >= num_required:
            default_idx = i - num_required
            default = all_defaults[default_idx]
            # Only add default if it's not None (None means no default was provided)
            if default is not None:
                # If this is a mutable default, use the constant name
                if arg_name in mutable_map:
                    params.append(f"{arg_name} = {mutable_map[arg_name]}")
                else:
                    _emit_expr = _get_emit_expr()
                    default_js = _emit_expr(default)
                    params.append(f"{arg_name} = {default_js}")
            else:
                params.append(arg_name)
        else:
            params.append(arg_name)
    
    # *args → ...args (rest parameter)
    if node.vararg:
        vararg_name = safe_js_name(node.vararg)
        params.append(f"...{vararg_name}")
        # When there's a vararg, kwonly_args and kwargs are handled in function body
        # They are extracted from the vararg array or passed as marked kwargs object
    else:
        # Keyword-only args (come after bare * in Python 3)
        # Without vararg, use object destructuring for keyword-only args
        if node.kwonly_args:
            kwonly_parts = []
            for i, arg in enumerate(node.kwonly_args):
                arg_name = safe_js_name(arg)
                default = node.kwonly_defaults[i] if i < len(node.kwonly_defaults) else None
                if default is not None:
                    # If this is a mutable default, use the constant name
                    if arg_name in mutable_map:
                        kwonly_parts.append(f"{arg_name} = {mutable_map[arg_name]}")
                    else:
                        _emit_expr = _get_emit_expr()
                        default_js = _emit_expr(default)
                        kwonly_parts.append(f"{arg_name} = {default_js}")
                else:
                    kwonly_parts.append(arg_name)
            
            # Use object destructuring: {x, y = 10} = {}
            params.append("{" + ", ".join(kwonly_parts) + "} = {}")
        
        # **kwargs → kwargs = {} (default to empty object)
        if node.kwarg:
            kwarg_name = safe_js_name(node.kwarg)
            params.append(f"{kwarg_name} = {{}}")
    
    return params


def _emit_lambda(node: Lambda) -> str:
    """
    Emit lambda expression.
    
    Phase 33.1: Enhanced to support *args, **kwargs, and default arguments.
    
    Examples:
        lambda x: x * 2           → (x) => x * 2
        lambda x, y=10: x + y     → (x, y = 10) => x + y
        lambda *args: len(args)  → (...args) => args.length
        lambda **kw: len(kw)      → (kw = {}) => Object.keys(kw).length
    """
    params = []
    
    # Regular positional args with defaults
    num_defaults = len(node.defaults)
    num_required = len(node.args) - num_defaults
    
    for i, arg in enumerate(node.args):
        arg_name = safe_js_name(arg)
        if i >= num_required:
            default_idx = i - num_required
            _emit_expr = _get_emit_expr()
            default_js = _emit_expr(node.defaults[default_idx])
            params.append(f"{arg_name} = {default_js}")
        else:
            params.append(arg_name)
    
    # *args → ...args
    if node.vararg:
        vararg_name = safe_js_name(node.vararg)
        params.append(f"...{vararg_name}")
    
    # **kwargs → kwargs = {}
    if node.kwarg:
        kwarg_name = safe_js_name(node.kwarg)
        params.append(f"{kwarg_name} = {{}}")
    
    params_js = ", ".join(params)
    _emit_expr = _get_emit_expr()
    body_js = _emit_expr(node.body)
    return f"({params_js}) => {body_js}"


# =============================================================================
# FUNCTION-SCOPED IMPORT EMISSION (Phase 33.3)
# =============================================================================

def _emit_function_scoped_import(node: Import, prefix: str) -> str:
    """
    Emit function-scoped import as local assignment.
    
    WHAT: Emits local variable assignment for imports inside functions.
    WHY: Python imports create local bindings that shadow globals.
    HOW: For built-ins: const json = __py.json; For regular: const json = json;
    WHO: Used when emitting function bodies with imports.
    WHEN: When import is inside a function body.
    WHERE: Part of scope-aware import emission.
    
    Phase 33.3: Scope-aware import emission.
    All imports are hoisted to top level (ES6 requirement), but function-scoped
    imports create local bindings that shadow the global imports, matching Python semantics.
    
    Args:
        node: Import IR node
        prefix: Indentation prefix
    
    Returns:
        JavaScript assignment statement or empty string
    """
    BUILTIN_MODULES = {"json", "math", "re", "random", "asyncio"}
    alias = safe_js_name(node.alias)
    module_base = node.module.split('.')[0]
    
    if module_base in BUILTIN_MODULES:
        # Built-in module: const json = __py.json;
        return f"{prefix}const {alias} = __py.{module_base};"
    else:
        # Regular module: const json = json; (reference hoisted import)
        # The import was hoisted to top, so we just create a local binding
        return f"{prefix}const {alias} = {alias};"


def _emit_function_scoped_import_from(node: ImportFrom, prefix: str) -> List[str]:
    """
    Emit function-scoped from import as local assignments.
    
    WHAT: Emits local variable assignments for from imports inside functions.
    WHY: Python from imports create local bindings that shadow globals.
    HOW: For built-ins: const loads = __py.json.loads; For regular: const x = x;
    WHO: Used when emitting function bodies with from imports.
    WHEN: When from import is inside a function body.
    WHERE: Part of scope-aware import emission.
    
    Args:
        node: ImportFrom IR node
        prefix: Indentation prefix
    
    Returns:
        List of JavaScript assignment statements
    """
    BUILTIN_MODULES = {"json", "math", "re", "random", "asyncio"}
    assignments = []
    
    # Check if this is a built-in module
    if node.module:
        module_base = node.module.split('.')[0]
        is_builtin = module_base in BUILTIN_MODULES
    else:
        # Relative import - not a built-in
        is_builtin = False
    
    for original_name, alias_name in node.names:
        alias_safe = safe_js_name(alias_name)
        
        if is_builtin:
            # Built-in module: const loads = __py.json.loads;
            module_base = node.module.split('.')[0]
            assignments.append(f"{prefix}const {alias_safe} = __py.{module_base}.{original_name};")
        else:
            # Regular module: const x = x; (reference hoisted import)
            # The import was hoisted to top, so we just create a local binding
            assignments.append(f"{prefix}const {alias_safe} = {alias_safe};")
    
    return assignments


def _emit_function_scoped_import_star(node: ImportStar, prefix: str) -> str:
    """
    Emit function-scoped star import.
    
    WHAT: Emits star import inside function as local property copying.
    WHY: Python star imports create local bindings in function scope.
    HOW: Uses __py.star_import() for built-ins, __py.star_import_esm() for regular modules.
    WHO: Used when emitting function bodies with star imports.
    WHEN: When star import is inside a function body.
    WHERE: Part of scope-aware import emission.
    
    Args:
        node: ImportStar IR node
        prefix: Indentation prefix
    
    Returns:
        JavaScript statement for function-scoped star import
    """
    BUILTIN_MODULES = {"json", "math", "re", "random", "asyncio"}
    
    if node.module:
        module_base = node.module.split('.')[0]
        if module_base in BUILTIN_MODULES:
            # Built-in module: __py.star_import(__py.json, localScope);
            # Use IIFE to get function's local scope
            return f"{prefix}__py.star_import(__py.{module_base}, (function() {{ return this; }})());"
        else:
            # Regular module: Need to import namespace first, then copy
            # For function-scoped imports, the namespace should already be hoisted
            # at module level, so we can reference it here
            # Note: This requires the namespace to be available in function scope
            # The namespace import is hoisted to module level by _emit_program
            from .emitter import safe_js_name
            namespace = safe_js_name(f"_{module_base}")
            # Use IIFE to get function's local scope
            return f"{prefix}__py.star_import_esm({namespace}, (function() {{ return this; }})(), {namespace}.__all__);"
    else:
        # Relative import - same as regular module
        # Note: Relative imports in function scope are complex
        # For now, emit a comment indicating this needs the namespace to be hoisted
        from .emitter import safe_js_name
        namespace = safe_js_name("_module")
        return f"{prefix}__py.star_import_esm({namespace}, (function() {{ return this; }})(), {namespace}.__all__);"

