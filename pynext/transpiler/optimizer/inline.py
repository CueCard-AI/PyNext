"""
PyNext Transpiler Optimizer - Runtime Inlining

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Inlines simple __py.* runtime calls with their equivalent JavaScript code.
This reduces function call overhead for common operations.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Runtime calls have overhead:

    __py.len(arr)  →  Function call, parameter passing, return

Inlining avoids this for simple cases:

    __py.len(arr)  →  arr.length  (for known arrays)

=============================================================================
INLINABLE OPERATIONS
=============================================================================

| Call | Type Required | Inlined Form |
|------|---------------|--------------|
| __py.len(arr) | list | arr.length |
| __py.len(s) | str | s.length |
| __py.len(d) | dict | Object.keys(d).length |
| __py.bool(arr) | list | arr.length > 0 |
| __py.bool(s) | str | s.length > 0 |
| __py.bool(d) | dict | Object.keys(d).length > 0 |

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler import parse
from pynext.transpiler.optimizer.inline import inline_runtime_calls

ir = parse("n = len(items)")
# With items: list, becomes:
# n = items.length
```
"""

from __future__ import annotations
from dataclasses import replace
from typing import Optional, Dict, Callable

from pynext.transpiler.nodes import (
    JSNode, Program,
    Name, Constant, BinOp, Compare, Call, Attribute,
)
from ._internal.type_env import TypeEnv, PyType
from ._internal.visitor import IRVisitor
from .types import infer_expr_type


# =============================================================================
# PUBLIC API
# =============================================================================

def inline_runtime_calls(ir: Program, type_env: TypeEnv) -> Program:
    """
    Inline simple runtime calls.
    
    Args:
        ir: The IR to optimize
        type_env: Type environment from type inference
    
    Returns:
        Optimized IR with inlined runtime calls
    """
    optimizer = InlineOptimizer(type_env)
    return optimizer.visit(ir)


def can_inline_len(arg: JSNode, type_env: TypeEnv) -> bool:
    """Check if len() can be inlined for this argument."""
    arg_type = infer_expr_type(arg, type_env)
    return arg_type in (PyType.LIST, PyType.STR, PyType.DICT, PyType.TUPLE)


def can_inline_bool(arg: JSNode, type_env: TypeEnv) -> bool:
    """Check if bool() can be inlined for this argument."""
    arg_type = infer_expr_type(arg, type_env)
    # Only inline for types we know how to handle
    return arg_type in (PyType.LIST, PyType.STR, PyType.DICT, PyType.SET)


def inline_len(arg: JSNode, type_env: TypeEnv) -> Optional[JSNode]:
    """Inline len() call."""
    arg_type = infer_expr_type(arg, type_env)
    
    if arg_type in (PyType.LIST, PyType.STR, PyType.TUPLE):
        # arr.length or str.length
        return Attribute(value=arg, attr="length")
    elif arg_type == PyType.DICT:
        # Object.keys(d).length
        return Attribute(
            value=Call(
                func=Attribute(value=Name(id="Object"), attr="keys"),
                args=(arg,),
                keywords={},
            ),
            attr="length",
        )
    
    return None


def inline_bool(arg: JSNode, type_env: TypeEnv) -> Optional[JSNode]:
    """Inline bool() call."""
    arg_type = infer_expr_type(arg, type_env)
    
    if arg_type in (PyType.LIST, PyType.STR, PyType.TUPLE):
        # arr.length > 0 or str.length > 0
        return Compare(
            left=Attribute(value=arg, attr="length"),
            ops=(">",),
            comparators=(Constant(value=0),),
        )
    elif arg_type == PyType.DICT:
        # Object.keys(d).length > 0
        return Compare(
            left=Attribute(
                value=Call(
                    func=Attribute(value=Name(id="Object"), attr="keys"),
                    args=(arg,),
                    keywords={},
                ),
                attr="length",
            ),
            ops=(">",),
            comparators=(Constant(value=0),),
        )
    elif arg_type == PyType.SET:
        # s.size > 0
        return Compare(
            left=Attribute(value=arg, attr="size"),
            ops=(">",),
            comparators=(Constant(value=0),),
        )
    
    return None


def inline_str_methods(method: str, obj: JSNode, args: tuple,
                       type_env: TypeEnv) -> Optional[JSNode]:
    """Inline string method calls when safe."""
    obj_type = infer_expr_type(obj, type_env)
    
    if obj_type != PyType.STR:
        return None
    
    # These methods have same semantics in JS
    safe_methods = {
        "upper": "toUpperCase",
        "lower": "toLowerCase",
        "trim": "trim",
        "trimStart": "trimStart",
        "trimEnd": "trimEnd",
    }
    
    if method in safe_methods:
        return Call(
            func=Attribute(value=obj, attr=safe_methods[method]),
            args=(),
            keywords={},
        )
    
    return None


# =============================================================================
# INLINE OPTIMIZER
# =============================================================================

class InlineOptimizer(IRVisitor):
    """
    Optimizer that inlines simple runtime calls.
    """
    
    def __init__(self, type_env: TypeEnv):
        self.type_env = type_env
        self.inline_count = 0
    
    def visit_Call(self, node: Call) -> JSNode:
        """Check if this call can be inlined."""
        # First, recursively transform children
        node = self.generic_visit(node)
        
        # Check if this is a __py.* call
        if self._is_py_call(node):
            inlined = self._try_inline(node)
            if inlined is not None:
                self.inline_count += 1
                return inlined
        
        # Also check for direct builtin calls like len()
        if isinstance(node.func, Name):
            inlined = self._try_inline_builtin(node)
            if inlined is not None:
                self.inline_count += 1
                return inlined
        
        return node
    
    def _is_py_call(self, node: Call) -> bool:
        """Check if node is a __py.* call."""
        if not isinstance(node.func, Attribute):
            return False
        if not isinstance(node.func.value, Name):
            return False
        return node.func.value.id == "__py"
    
    def _try_inline(self, node: Call) -> Optional[JSNode]:
        """Try to inline a __py.* call."""
        method = node.func.attr
        
        if method == "len" and len(node.args) == 1:
            return inline_len(node.args[0], self.type_env)
        elif method == "bool" and len(node.args) == 1:
            return inline_bool(node.args[0], self.type_env)
        
        return None
    
    def _try_inline_builtin(self, node: Call) -> Optional[JSNode]:
        """Try to inline a builtin call like len()."""
        func_name = node.func.id
        
        if func_name == "len" and len(node.args) == 1:
            return inline_len(node.args[0], self.type_env)
        
        return None


# =============================================================================
# STATISTICS
# =============================================================================

def count_inlinable_calls(ir: Program, type_env: TypeEnv) -> int:
    """Count calls that could be inlined."""
    count = 0
    
    def visit(node):
        nonlocal count
        
        if isinstance(node, Call):
            # Check for __py.len, __py.bool
            if isinstance(node.func, Attribute):
                if isinstance(node.func.value, Name):
                    if node.func.value.id == "__py":
                        if node.func.attr in ("len", "bool"):
                            if len(node.args) == 1:
                                arg_type = infer_expr_type(node.args[0], type_env)
                                if arg_type.is_known():
                                    count += 1
        
        # Recurse
        for attr in ['body', 'orelse', 'args', 'left', 'right', 'value', 
                     'test', 'func', 'operand']:
            child = getattr(node, attr, None)
            if child is not None:
                if isinstance(child, (list, tuple)):
                    for c in child:
                        if isinstance(c, JSNode):
                            visit(c)
                elif isinstance(child, JSNode):
                    visit(child)
    
    for stmt in ir.body:
        visit(stmt)
    
    return count
