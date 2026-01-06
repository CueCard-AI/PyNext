"""
PyNext Transpiler Optimizer - @js_native Escape Hatch

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides the @js_native decorator that opts out of Python semantics.
Functions decorated with @js_native are transpiled without __py.* wrappers.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

For performance-critical code, the __py.* wrappers add overhead.
The @js_native decorator lets developers say "I know this code is safe,
emit pure JavaScript."

=============================================================================
USAGE
=============================================================================

```python
from pynext import js_native

@js_native
def fast_sum(items):
    total = 0
    for x in items:
        total += x
    return total
```

Transpiles to pure JS without wrappers:

```javascript
function fast_sum(items) {
    let total = 0;
    for (const x of items) {
        total += x;
    }
    return total;
}
```

=============================================================================
CAVEATS
=============================================================================

With @js_native, the code WILL break if:
- Using negative indexing: items[-1]
- Using Python modulo with negatives: -7 % 3
- Comparing collections: [1] == [1]
- Using empty collection truthiness: if items:

Only use when you're sure your code is JS-safe!
"""

from __future__ import annotations
from dataclasses import replace
from typing import Set

from pynext.transpiler.nodes import (
    JSNode, Program, FunctionDef,
    Decorator, DecoratedFunction,
)
from ._internal.visitor import IRVisitor


# =============================================================================
# PUBLIC API
# =============================================================================

def is_js_native(node: JSNode) -> bool:
    """
    Check if a function has the @js_native decorator.
    
    Args:
        node: Function definition node (FunctionDef or DecoratedFunction)
    
    Returns:
        True if function should be transpiled without wrappers
    """
    # Check if it's a DecoratedFunction
    if isinstance(node, DecoratedFunction):
        for dec in node.decorators:
            if isinstance(dec, Decorator):
                if dec.name == "js_native":
                    return True
        return False
    
    # Plain FunctionDef cannot have decorators
    return False


def mark_native_functions(ir: Program) -> Set[str]:
    """
    Find all functions marked with @js_native.
    
    Returns set of function names that should be emitted as native JS.
    """
    native_funcs = set()
    
    for stmt in ir.body:
        if isinstance(stmt, DecoratedFunction):
            # Check decorators
            for dec in stmt.decorators:
                if isinstance(dec, Decorator) and dec.name == "js_native":
                    native_funcs.add(stmt.function.name)
                    break
    
    return native_funcs


def strip_js_native_decorator(node: JSNode) -> JSNode:
    """
    Remove the @js_native decorator from a decorated function.
    
    The decorator is only for the transpiler - it shouldn't appear in output.
    """
    if not isinstance(node, DecoratedFunction):
        return node
    
    new_decorators = []
    for dec in node.decorators:
        if isinstance(dec, Decorator):
            if dec.name != "js_native":
                new_decorators.append(dec)
    
    if not new_decorators:
        # No decorators left, return the plain function
        return node.function
    
    return replace(node, decorators=tuple(new_decorators))


# =============================================================================
# NATIVE MODE OPTIMIZER
# =============================================================================

class NativeOptimizer(IRVisitor):
    """
    Optimizer that handles @js_native functions.
    
    This visitor identifies native functions and marks them for special
    emission without __py.* wrappers.
    """
    
    def __init__(self):
        self.native_functions: Set[str] = set()
    
    def visit_DecoratedFunction(self, node: DecoratedFunction) -> JSNode:
        """Handle decorated function."""
        for dec in node.decorators:
            if isinstance(dec, Decorator) and dec.name == "js_native":
                self.native_functions.add(node.function.name)
                # Return the function without this decorator
                remaining_decorators = [
                    d for d in node.decorators
                    if not (isinstance(d, Decorator) and d.name == "js_native")
                ]
                if remaining_decorators:
                    return replace(node, decorators=tuple(remaining_decorators))
                else:
                    return node.function
        
        return self.generic_visit(node)


# =============================================================================
# STATISTICS
# =============================================================================

def count_native_functions(ir: Program) -> int:
    """Count functions marked with @js_native."""
    return len(mark_native_functions(ir))
