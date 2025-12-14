"""
DEPRECATED: This module is deprecated. Use pynext.reactive instead.

This file exists for backward compatibility only.
All reactive primitives have been moved to pynext.reactive.

Migration:
    # OLD (deprecated):
    from pynext.core.signals import Signal, Effect, Computed, Store, batch
    
    # NEW:
    from pynext.reactive import Signal, Effect, Memo, Store, batch
"""

from __future__ import annotations

import warnings
import ast
from typing import Any, Callable, TypeVar

# Re-export everything from pynext.reactive
from pynext.reactive import (
    Signal,
    Effect,
    Memo,
    Store,
    batch,
    signal,
    effect,
    memo,
    store,
    createSignal,
    createEffect,
    createMemo,
    createStore,
    untrack,
)

# Legacy aliases
Computed = Memo
computed = memo

T = TypeVar("T")


def _emit_deprecation_warning():
    """Emit a deprecation warning once."""
    warnings.warn(
        "pynext.core.signals is deprecated. Use pynext.reactive instead.",
        DeprecationWarning,
        stacklevel=3
    )


# =============================================================================
# LEGACY TRANSPILATION (kept for backward compatibility)
# =============================================================================

def _transpile_ast(tree: ast.AST) -> str:
    """
    Transpile a Python AST to JavaScript.
    
    This is a simple transpiler for basic lambda expressions.
    Used for event handler transpilation.
    
    Args:
        tree: Python AST node
    
    Returns:
        JavaScript code string
    """
    
    class JSTranspiler(ast.NodeVisitor):
        def visit_Module(self, node):
            if node.body:
                return self.visit(node.body[0])
            return ""
        
        def visit_Expr(self, node):
            return self.visit(node.value)
        
        def visit_Lambda(self, node):
            args = ", ".join(arg.arg for arg in node.args.args)
            body = self.visit(node.body)
            if args:
                return f"({args}) => {body}"
            return f"() => {body}"
        
        def visit_BinOp(self, node):
            left = self.visit(node.left)
            right = self.visit(node.right)
            op = self._binop(node.op)
            return f"({left} {op} {right})"
        
        def visit_Compare(self, node):
            left = self.visit(node.left)
            ops = [self._cmpop(op) for op in node.ops]
            comparators = [self.visit(c) for c in node.comparators]
            
            parts = [left]
            for op, comp in zip(ops, comparators):
                parts.append(f"{op} {comp}")
            return " ".join(parts)
        
        def visit_IfExp(self, node):
            test = self.visit(node.test)
            body = self.visit(node.body)
            orelse = self.visit(node.orelse)
            return f"({test} ? {body} : {orelse})"
        
        def visit_Name(self, node):
            return node.id
        
        def visit_Constant(self, node):
            if isinstance(node.value, str):
                return f'"{node.value}"'
            return str(node.value)
        
        def visit_Num(self, node):
            return str(node.n)
        
        def visit_Str(self, node):
            return f'"{node.s}"'
        
        def visit_Call(self, node):
            func = self.visit(node.func)
            args = ", ".join(self.visit(arg) for arg in node.args)
            return f"{func}({args})"
        
        def visit_Attribute(self, node):
            value = self.visit(node.value)
            return f"{value}.{node.attr}"
        
        def visit_Subscript(self, node):
            value = self.visit(node.value)
            slice_val = self.visit(node.slice)
            return f"{value}[{slice_val}]"
        
        def visit_Index(self, node):
            return self.visit(node.value)
        
        def visit_List(self, node):
            elts = ", ".join(self.visit(e) for e in node.elts)
            return f"[{elts}]"
        
        def visit_Dict(self, node):
            pairs = []
            for k, v in zip(node.keys, node.values):
                key = self.visit(k)
                val = self.visit(v)
                pairs.append(f"{key}: {val}")
            return "{" + ", ".join(pairs) + "}"
        
        def visit_UnaryOp(self, node):
            operand = self.visit(node.operand)
            op = self._unaryop(node.op)
            return f"({op}{operand})"
        
        def visit_BoolOp(self, node):
            op = " && " if isinstance(node.op, ast.And) else " || "
            values = [self.visit(v) for v in node.values]
            return "(" + op.join(values) + ")"
        
        def _binop(self, op):
            ops = {
                ast.Add: "+",
                ast.Sub: "-",
                ast.Mult: "*",
                ast.Div: "/",
                ast.Mod: "%",
                ast.Pow: "**",
                ast.FloorDiv: "//",
            }
            return ops.get(type(op), "?")
        
        def _cmpop(self, op):
            ops = {
                ast.Eq: "===",
                ast.NotEq: "!==",
                ast.Lt: "<",
                ast.LtE: "<=",
                ast.Gt: ">",
                ast.GtE: ">=",
                ast.Is: "===",
                ast.IsNot: "!==",
                ast.In: "in",
                ast.NotIn: "not in",
            }
            return ops.get(type(op), "?")
        
        def _unaryop(self, op):
            ops = {
                ast.Not: "!",
                ast.USub: "-",
                ast.UAdd: "+",
            }
            return ops.get(type(op), "?")
        
        def generic_visit(self, node):
            return str(node)
    
    transpiler = JSTranspiler()
    return transpiler.visit(tree)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Core primitives
    "Signal",
    "Effect",
    "Memo",
    "Store",
    "batch",
    "signal",
    "effect",
    "memo",
    "store",
    "computed",
    
    # Legacy aliases
    "Computed",
    
    # SolidJS-style
    "createSignal",
    "createEffect",
    "createMemo",
    "createStore",
    "untrack",
    
    # Transpilation
    "_transpile_ast",
]
