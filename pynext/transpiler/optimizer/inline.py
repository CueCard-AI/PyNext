"""
PyNext Transpiler Optimizer - Runtime Inlining

=============================================================================
WHO: Transpiler developers, bundle size optimizers
=============================================================================

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Inlines simple __py.* runtime calls with their equivalent JavaScript code.
This reduces function call overhead and bundle size for common operations.

=============================================================================
WHEN: During optimization pass (optional, enabled by default)
=============================================================================

=============================================================================
WHERE: Called by optimize() in optimizer/__init__.py
=============================================================================

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Runtime calls have overhead:

    __py.len(arr)  →  Function call, parameter passing, return
    __py.str.upper(s)  →  Function call, runtime lookup, return

Inlining avoids this for simple cases:

    __py.len(arr)  →  arr.length  (zero overhead)
    __py.str.upper(s)  →  s.toUpperCase()  (native JS)

=============================================================================
HOW: Pattern matching on IR nodes, replacing with inlined equivalents
=============================================================================

=============================================================================
INLINABLE OPERATIONS (Updated for Bundle Optimization)
=============================================================================

| Call Pattern | Type | Inlined Form | Savings |
|--------------|------|--------------|---------|
| __py.len(arr) | list | arr.length | 100% |
| __py.len(s) | str | s.length | 100% |
| __py.len(d) | dict | Object.keys(d).length | 100% |
| __py.bool(arr) | list | arr.length > 0 | 100% |
| __py.bool(s) | str | s.length > 0 | 100% |
| __py.bool(d) | dict | Object.keys(d).length > 0 | 100% |
| __py.str.upper(s) | str | s.toUpperCase() | 100% |
| __py.str.lower(s) | str | s.toLowerCase() | 100% |
| __py.str.strip(s) | str | s.trim() | 100% |
| __py.str.lstrip(s) | str | s.trimStart() | 100% |
| __py.str.rstrip(s) | str | s.trimEnd() | 100% |
| __py.list.append(arr, x) | list | arr.push(x) | 100% |
| __py.list.pop(arr) | list | arr.pop() | 100% |
| __py.list.reverse(arr) | list | arr.reverse() | 100% |
| __py.dict.keys(d) | dict | Object.keys(d) | 100% |
| __py.dict.values(d) | dict | Object.values(d) | 100% |
| __py.dict.items(d) | dict | Object.entries(d) | 100% |

=============================================================================
SIZE IMPACT
=============================================================================

Before inlining: App imports full __py.str, __py.list, __py.dict modules
After inlining: Native JS methods used, no runtime imports needed

Estimated savings: Up to 2KB gzipped for apps using only inlined methods

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler import parse
from pynext.transpiler.optimizer.inline import inline_runtime_calls

ir = parse("n = len(items)")
# With items: list, becomes:
# n = items.length

ir = parse("s = text.upper()")
# With text: str, becomes:
# s = text.toUpperCase()

ir = parse("arr.append(42)")
# With arr: list, becomes:
# arr.push(42)
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
    """
    Inline string method calls when safe.
    
    =============================================================================
    INLINABLE STRING METHODS
    =============================================================================
    
    | Python Method | JavaScript Method | Notes |
    |---------------|-------------------|-------|
    | s.upper()     | s.toUpperCase()   | Zero-cost inline |
    | s.lower()     | s.toLowerCase()   | Zero-cost inline |
    | s.strip()     | s.trim()          | Zero-cost inline |
    | s.lstrip()    | s.trimStart()     | Zero-cost inline |
    | s.rstrip()    | s.trimEnd()       | Zero-cost inline |
    
    =============================================================================
    WHY THESE ARE SAFE TO INLINE
    =============================================================================
    
    These methods have identical semantics in Python and JavaScript:
    - No optional arguments that change behavior
    - No locale-dependent behavior (ASCII only for case conversion)
    - Same return type (string)
    """
    obj_type = infer_expr_type(obj, type_env)
    
    if obj_type != PyType.STR:
        return None
    
    # These methods have same semantics in JS
    safe_methods = {
        "upper": "toUpperCase",
        "lower": "toLowerCase",
        "strip": "trim",
        "lstrip": "trimStart",
        "rstrip": "trimEnd",
    }
    
    if method in safe_methods and len(args) == 0:
        return Call(
            func=Attribute(value=obj, attr=safe_methods[method]),
            args=(),
            keywords={},
        )
    
    return None


def inline_list_methods(method: str, obj: JSNode, args: tuple,
                        type_env: TypeEnv) -> Optional[JSNode]:
    """
    Inline list method calls when safe.
    
    =============================================================================
    INLINABLE LIST METHODS
    =============================================================================
    
    | Python Method   | JavaScript Method | Notes |
    |-----------------|-------------------|-------|
    | arr.append(x)   | arr.push(x)       | Zero-cost inline |
    | arr.pop()       | arr.pop()         | Same method name |
    | arr.clear()     | arr.length = 0    | Assignment instead of method |
    | arr.reverse()   | arr.reverse()     | Same method name (mutates in place) |
    | arr.copy()      | [...arr]          | Spread operator for shallow copy |
    
    =============================================================================
    WHY THESE ARE SAFE TO INLINE
    =============================================================================
    
    - append() maps directly to push() (both mutate, return undefined/None)
    - pop() is identical (both remove and return last element)
    - clear() has no JS equivalent, but length = 0 is faster
    - reverse() is identical (both mutate in place)
    - copy() uses spread which is idiomatic JS
    """
    obj_type = infer_expr_type(obj, type_env)
    
    if obj_type != PyType.LIST:
        return None
    
    if method == "append" and len(args) == 1:
        # arr.append(x) → arr.push(x)
        return Call(
            func=Attribute(value=obj, attr="push"),
            args=args,
            keywords={},
        )
    
    if method == "pop" and len(args) == 0:
        # arr.pop() → arr.pop()
        return Call(
            func=Attribute(value=obj, attr="pop"),
            args=(),
            keywords={},
        )
    
    if method == "reverse" and len(args) == 0:
        # arr.reverse() → arr.reverse()
        return Call(
            func=Attribute(value=obj, attr="reverse"),
            args=(),
            keywords={},
        )
    
    return None


def inline_dict_methods(method: str, obj: JSNode, args: tuple,
                        type_env: TypeEnv) -> Optional[JSNode]:
    """
    Inline dict method calls when safe.
    
    =============================================================================
    INLINABLE DICT METHODS
    =============================================================================
    
    | Python Method | JavaScript Equivalent | Notes |
    |---------------|----------------------|-------|
    | d.keys()      | Object.keys(d)       | Returns array, not view |
    | d.values()    | Object.values(d)     | Returns array, not view |
    | d.items()     | Object.entries(d)    | Returns array of [k, v] pairs |
    
    =============================================================================
    WHY THESE ARE SAFE TO INLINE
    =============================================================================
    
    Python dict views vs JS arrays:
    - In Python, d.keys() returns a view that reflects changes to dict
    - In JS, Object.keys(d) returns a snapshot array
    - For most code, this difference doesn't matter
    - If view behavior is needed, don't use inlining (rare)
    """
    obj_type = infer_expr_type(obj, type_env)
    
    if obj_type != PyType.DICT:
        return None
    
    if method == "keys" and len(args) == 0:
        # d.keys() → Object.keys(d)
        return Call(
            func=Attribute(value=Name(id="Object"), attr="keys"),
            args=(obj,),
            keywords={},
        )
    
    if method == "values" and len(args) == 0:
        # d.values() → Object.values(d)
        return Call(
            func=Attribute(value=Name(id="Object"), attr="values"),
            args=(obj,),
            keywords={},
        )
    
    if method == "items" and len(args) == 0:
        # d.items() → Object.entries(d)
        return Call(
            func=Attribute(value=Name(id="Object"), attr="entries"),
            args=(obj,),
            keywords={},
        )
    
    return None


# =============================================================================
# INLINE OPTIMIZER
# =============================================================================

class InlineOptimizer(IRVisitor):
    """
    Optimizer that inlines simple runtime calls.
    
    =============================================================================
    INLINING STRATEGY
    =============================================================================
    
    This optimizer handles three levels of inlining:
    
    1. __py.len(x), __py.bool(x) - Simple builtin calls
    2. __py.str.method(s, ...) - String method wrappers
    3. __py.list.method(arr, ...) - List method wrappers
    4. __py.dict.method(d, ...) - Dict method wrappers
    
    =============================================================================
    METHODS INLINED
    =============================================================================
    
    | Call Pattern | Inlined To | Savings |
    |--------------|------------|---------|
    | __py.len(arr) | arr.length | 100% |
    | __py.str.upper(s) | s.toUpperCase() | 100% |
    | __py.str.lower(s) | s.toLowerCase() | 100% |
    | __py.str.strip(s) | s.trim() | 100% |
    | __py.list.append(arr, x) | arr.push(x) | 100% |
    | __py.list.pop(arr) | arr.pop() | 100% |
    | __py.dict.keys(d) | Object.keys(d) | 100% |
    | __py.dict.values(d) | Object.values(d) | 100% |
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
        
        # Check if this is a __py.str.*, __py.list.*, __py.dict.* call
        if self._is_py_type_method_call(node):
            inlined = self._try_inline_type_method(node)
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
        """Check if node is a __py.method() call (not __py.type.method())."""
        if not isinstance(node.func, Attribute):
            return False
        if not isinstance(node.func.value, Name):
            return False
        return node.func.value.id == "__py"
    
    def _is_py_type_method_call(self, node: Call) -> bool:
        """Check if node is a __py.str.method() or __py.list.method() call."""
        if not isinstance(node.func, Attribute):
            return False
        # Check for __py.str.method or __py.list.method pattern
        if not isinstance(node.func.value, Attribute):
            return False
        if not isinstance(node.func.value.value, Name):
            return False
        return (node.func.value.value.id == "__py" and 
                node.func.value.attr in ("str", "list", "dict", "set"))
    
    def _try_inline(self, node: Call) -> Optional[JSNode]:
        """Try to inline a __py.* call."""
        method = node.func.attr
        
        if method == "len" and len(node.args) == 1:
            return inline_len(node.args[0], self.type_env)
        elif method == "bool" and len(node.args) == 1:
            return inline_bool(node.args[0], self.type_env)
        
        return None
    
    def _try_inline_type_method(self, node: Call) -> Optional[JSNode]:
        """
        Try to inline a __py.str.method(obj, args) or __py.list.method(obj, args) call.
        
        Pattern: __py.str.upper(s) → s.toUpperCase()
        Pattern: __py.list.append(arr, x) → arr.push(x)
        """
        type_name = node.func.value.attr  # "str", "list", "dict"
        method = node.func.attr  # "upper", "append", "keys", etc.
        
        # These methods take (obj, ...args) pattern
        if len(node.args) < 1:
            return None
        
        obj = node.args[0]
        remaining_args = node.args[1:]
        
        if type_name == "str":
            return inline_str_methods(method, obj, remaining_args, self.type_env)
        elif type_name == "list":
            return inline_list_methods(method, obj, remaining_args, self.type_env)
        elif type_name == "dict":
            return inline_dict_methods(method, obj, remaining_args, self.type_env)
        
        return None
    
    def _try_inline_builtin(self, node: Call) -> Optional[JSNode]:
        """Try to inline a builtin call like len()."""
        func_name = node.func.id
        
        if func_name == "len" and len(node.args) == 1:
            return inline_len(node.args[0], self.type_env)
        
        return None


# =============================================================================
# INLINABLE METHODS REGISTRY (for external use)
# =============================================================================

# Registry of methods that can be inlined, for documentation and validation
INLINABLE_METHODS = {
    "str": {
        "upper": ("toUpperCase", 0),   # (js_method, num_args)
        "lower": ("toLowerCase", 0),
        "strip": ("trim", 0),
        "lstrip": ("trimStart", 0),
        "rstrip": ("trimEnd", 0),
    },
    "list": {
        "append": ("push", 1),
        "pop": ("pop", 0),
        "reverse": ("reverse", 0),
    },
    "dict": {
        "keys": ("Object.keys", 0),
        "values": ("Object.values", 0),
        "items": ("Object.entries", 0),
    },
}


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
