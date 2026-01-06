from __future__ import annotations

"""
PyNext Transpiler - Comprehension Emitters

Phase 33.1: Comprehension transpilation including:
- List comprehensions
- Dict comprehensions
- Set comprehensions
- Generator expressions
- Generator expression optimization
"""
from typing import Optional

from .nodes import ListComp, DictComp, SetComp, GeneratorExp, Name, Dict
from ._internal.utils import safe_js_name


def _get_emit_expr():
    """Lazy import to avoid circular dependency."""
    from .emitter import _emit_expr
    return _emit_expr


def _get_type_env():
    """Lazy import to avoid circular dependency."""
    from .emitter import get_type_env
    return get_type_env()


def _get_pytype():
    """Lazy import to avoid circular dependency."""
    from .optimizer._internal.type_env import PyType
    return PyType


def _is_likely_dict(iter_node) -> bool:
    """
    Detect if an iterable is likely a dict using type inference.
    
    Returns True if:
    - iter_node is a Dict literal
    - iter_node is a DictComp
    - iter_node is a Name and type_env says it's a DICT
    
    This is used to prevent unsafe optimizations like [...dict_var]
    which would fail in JavaScript.
    """
    PyType = _get_pytype()
    
    # Dict literal - definitely a dict
    if isinstance(iter_node, Dict):
        return True
    
    # Dict comprehension - definitely a dict
    if isinstance(iter_node, DictComp):
        return True
    
    # Check type environment for variable types
    if isinstance(iter_node, Name):
        type_env = _get_type_env()
        if type_env:
            iter_type = type_env.get_type(iter_node.id)
            if iter_type == PyType.DICT:
                return True
    
    return False


def _try_optimize_generator_call(func_name: str, gen: GeneratorExp, keywords: tuple) -> Optional[str]:
    """
    Try to optimize builtin(generator_expression) patterns.
    
    Transforms common patterns to more efficient JavaScript:
    
    | Python | JavaScript |
    |--------|------------|
    | sum(x for x in items) | items.reduce((a, x) => a + x, 0) |
    | sum(x*2 for x in items) | items.reduce((a, x) => a + x*2, 0) |
    | any(x > 0 for x in items) | items.some(x => x > 0) |
    | all(x > 0 for x in items) | items.every(x => x > 0) |
    | list(x for x in items) | [...items] |
    | list(x*2 for x in items) | items.map(x => x*2) |
    | set(x for x in items) | new Set(items) |
    | min(x for x in items) | __py.min(items, null) |
    | max(x for x in items) | __py.max(items, null) |
    | sum(a*b for a, b in pairs) | pairs.reduce((acc, ([a, b])) => acc + a*b, 0) |
    
    Returns None if optimization not applicable.
    """
    if len(gen.generators) == 0:
        return None
    
    # Get the first generator clause
    g = gen.generators[0]
    
    # Build target pattern - handle both simple and tuple unpacking
    if g.target:
        target = g.target
        arrow_target = target  # Simple name doesn't need parens
        is_tuple = False
    else:
        # Tuple unpacking: [a, b] needs to be ([a, b]) in arrow function
        target = f"[{', '.join(g.targets)}]"
        arrow_target = f"({target})"
        is_tuple = True
    
    _emit_expr = _get_emit_expr()
    iter_js = _emit_expr(g.iter)
    element_js = _emit_expr(gen.element)
    
    # Check if element is identity (just the target)
    target_name = g.target if g.target else (g.targets[0] if len(g.targets) == 1 else None)
    is_identity = isinstance(gen.element, Name) and target_name and gen.element.id == target_name
    
    # Build the base iterable (with filters if present)
    if g.ifs:
        # Add filter stage
        filters = [_emit_expr(cond) for cond in g.ifs]
        filter_cond = " && ".join(filters)
        base = f"__py.iter({iter_js}).filter({arrow_target} => {filter_cond})"
    else:
        base = f"__py.iter({iter_js})"
    
    # Optimize based on function name
    if func_name == "sum":
        # Use __acc__ to avoid collision with destructured names
        if is_identity:
            return f"{base}.reduce((__acc__, {arrow_target}) => __acc__ + {target_name}, 0)"
        else:
            return f"{base}.reduce((__acc__, {arrow_target}) => __acc__ + ({element_js}), 0)"
    
    if func_name == "any":
        if is_identity:
            # any(x for x in items) → items.some(x => __py.bool(x))
            return f"{base}.some({arrow_target} => __py.bool({target_name}))"
        else:
            return f"{base}.some({arrow_target} => {element_js})"
    
    if func_name == "all":
        if is_identity:
            # all(x for x in items) → items.every(x => __py.bool(x))
            return f"{base}.every({arrow_target} => __py.bool({target_name}))"
        else:
            return f"{base}.every({arrow_target} => {element_js})"
    
    if func_name == "list":
        if is_identity:
            # list(x for x in items) → [...items] (optimize away __py.iter for simple case)
            # But we need __py.iter for dicts, so check if iter is a simple name
            # CRITICAL: If there are filters, we must use base (which includes .filter())
            # CRITICAL: If iter is a dict, we must use __py.iter (can't spread plain objects)
            if isinstance(g.iter, Name) and not g.ifs and not _is_likely_dict(g.iter):
                # Simple name with no filters and NOT a dict - can use directly
                return f"[...{iter_js}]"
            else:
                # Complex expression, has filters, or is a dict - use base with __py.iter and filters
                return f"[...{base}]"
        else:
            return f"[...{base}.map({arrow_target} => {element_js})]"
    
    if func_name == "set":
        if is_identity:
            return f"new Set({base})"
        else:
            return f"new Set([...{base}.map({arrow_target} => {element_js})])"
    
    if func_name == "min":
        # Check for key parameter
        key = None
        for kw in keywords:
            if kw[0] == "key" and kw[1]:
                key = _emit_expr(kw[1])
                break
        
        if key:
            if is_identity:
                return f"__py.min([...{base}], {key})"
            else:
                mapped = f"[...{base}.map({arrow_target} => {element_js})]"
                return f"__py.min({mapped}, {key})"
        else:
            if is_identity:
                return f"__py.min([...{base}], null)"
            else:
                mapped = f"[...{base}.map({arrow_target} => {element_js})]"
                return f"__py.min({mapped}, null)"
    
    if func_name == "max":
        # Check for key parameter
        key = None
        for kw in keywords:
            if kw[0] == "key" and kw[1]:
                key = _emit_expr(kw[1])
                break
        
        if key:
            if is_identity:
                return f"__py.max([...{base}], {key})"
            else:
                mapped = f"[...{base}.map({arrow_target} => {element_js})]"
                return f"__py.max({mapped}, {key})"
        else:
            if is_identity:
                return f"__py.max([...{base}], null)"
            else:
                mapped = f"[...{base}.map({arrow_target} => {element_js})]"
                return f"__py.max({mapped}, null)"
    
    # No optimization available
    return None


def _emit_list_comp(node: ListComp) -> str:
    """
    Emit list comprehension as map/filter chains.
    
    Examples:
        [x*2 for x in items]           → items.map(x => x*2)
        [x for x in items if x > 0]    → items.filter(x => x > 0)
        [x*2 for x in items if x > 0]  → items.filter(x => x > 0).map(x => x*2)
    """
    if len(node.generators) == 0:
        return "[]"
    
    _emit_expr = _get_emit_expr()
    gen = node.generators[0]
    target = gen.target if gen.target else f"[{', '.join(gen.targets)}]"
    iter_js = _emit_expr(gen.iter)
    element_js = _emit_expr(node.element)
    
    # Start with the iterable
    result = f"__py.iter({iter_js})"
    
    # Add filters
    for cond in gen.ifs:
        cond_js = _emit_expr(cond)
        result = f"{result}.filter({target} => {cond_js})"
    
    # Check if element is just the target (identity map)
    target_name = target if gen.target else gen.targets[0] if len(gen.targets) == 1 else None
    if isinstance(node.element, Name) and node.element.id == target_name:
        # [x for x in items if ...] - no map needed
        result = f"[...{result}]"
    else:
        # [x*2 for x in items] - need map
        result = f"[...{result}.map({target} => {element_js})]"
    
    # Handle nested generators
    for gen in node.generators[1:]:
        target2 = gen.target if gen.target else f"[{', '.join(gen.targets)}]"
        iter_js2 = _emit_expr(gen.iter)
        
        # Wrap with flatMap for nested comprehension
        inner = f"__py.iter({iter_js2})"
        for cond in gen.ifs:
            cond_js = _emit_expr(cond)
            inner = f"{inner}.filter({target2} => {cond_js})"
        inner = f"{inner}.map({target2} => {element_js})"
        
        result = f"{result}.flatMap({target} => [...{inner}])"
    
    return result


def _emit_dict_comp(node: DictComp) -> str:
    """
    Emit dict comprehension as Object.fromEntries.
    
    Examples:
        {k: v for k, v in items}     → Object.fromEntries([...items])
        {k: v*2 for k, v in d.items() if v > 0}
            → Object.fromEntries([...Object.entries(d)].filter(([k, v]) => v > 0).map(([k, v]) => [k, v*2]))
    """
    if len(node.generators) == 0:
        return "{}"
    
    _emit_expr = _get_emit_expr()
    gen = node.generators[0]
    
    # Build target pattern
    if gen.targets:
        # Multiple targets: wrap in parentheses for arrow function
        target = f"([{', '.join(gen.targets)}])"
    else:
        target = gen.target
    
    iter_js = _emit_expr(gen.iter)
    key_js = _emit_expr(node.key)
    value_js = _emit_expr(node.value)
    
    # Start with iterable
    result = f"[...__py.iter({iter_js})]"
    
    # Add filters
    for cond in gen.ifs:
        cond_js = _emit_expr(cond)
        result = f"{result}.filter({target} => {cond_js})"
    
    # Map to [key, value] pairs
    result = f"{result}.map({target} => [{key_js}, {value_js}])"
    
    return f"Object.fromEntries({result})"


def _emit_set_comp(node: SetComp) -> str:
    """
    Emit set comprehension as new Set().
    
    Examples:
        {x for x in items}           → new Set(items)
        {x*2 for x in items if x}    → new Set([...items].filter(x => x).map(x => x*2))
    """
    if len(node.generators) == 0:
        return "new Set()"
    
    _emit_expr = _get_emit_expr()
    gen = node.generators[0]
    target = gen.target if gen.target else f"[{', '.join(gen.targets)}]"
    iter_js = _emit_expr(gen.iter)
    element_js = _emit_expr(node.element)
    
    # Check for simple case: {x for x in items}
    target_name = target if gen.target else gen.targets[0] if len(gen.targets) == 1 else None
    is_identity = isinstance(node.element, Name) and node.element.id == target_name
    has_filter = len(gen.ifs) > 0
    
    if is_identity and not has_filter:
        # Simple case: new Set(items)
        return f"new Set(__py.iter({iter_js}))"
    
    # Complex case: need filter/map
    result = f"[...__py.iter({iter_js})]"
    
    for cond in gen.ifs:
        cond_js = _emit_expr(cond)
        result = f"{result}.filter({target} => {cond_js})"
    
    if not is_identity:
        result = f"{result}.map({target} => {element_js})"
    
    return f"new Set({result})"


def _emit_generator_exp(node: GeneratorExp) -> str:
    """
    Emit generator expression.
    
    Usually appears in function calls like sum(), any(), all().
    We emit as an array (materialize the generator) since JS doesn't have
    lazy generators in the same way.
    
    Examples:
        (x for x in items)      → [...items]
        (x*2 for x in items)    → items.map(x => x*2)
        (a*b for a, b in pairs) → pairs.map(([a, b]) => a*b)
    """
    if len(node.generators) == 0:
        return "[]"
    
    _emit_expr = _get_emit_expr()
    gen = node.generators[0]
    
    # Build target pattern - wrap in parens if destructuring (tuple unpacking)
    if gen.target:
        target = gen.target
        arrow_target = target  # Simple name doesn't need parens
    else:
        # Tuple unpacking: [a, b] needs to be ([a, b]) in arrow function
        target = f"[{', '.join(gen.targets)}]"
        arrow_target = f"({target})"  # Wrap destructuring in parens for arrow
    
    iter_js = _emit_expr(gen.iter)
    element_js = _emit_expr(node.element)
    
    # Start with iterable
    result = f"__py.iter({iter_js})"
    
    # Add filters
    for cond in gen.ifs:
        cond_js = _emit_expr(cond)
        result = f"{result}.filter({arrow_target} => {cond_js})"
    
    # Check if element is just the target (identity map)
    target_name = target if gen.target else gen.targets[0] if len(gen.targets) == 1 else None
    if isinstance(node.element, Name) and node.element.id == target_name:
        # (x for x in items) - spread to array
        result = f"[...{result}]"
    else:
        # (x*2 for x in items) - map
        result = f"[...{result}.map({arrow_target} => {element_js})]"
    
    return result

