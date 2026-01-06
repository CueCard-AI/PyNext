"""
PyNext Transpiler Optimizer - Loop Variable Capture Fix

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Automatically fixes the Python closure-in-loop gotcha by wrapping lambdas
that reference loop variables with an IIFE (Immediately Invoked Function
Expression) to capture the current value.

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

Python closures capture variables by reference, not by value:

```python
# BUG: All handlers see i=4 (the final value)
for i in range(5):
    onclick = lambda: handle(i)
```

JavaScript has the same issue with `var`, but `let` fixes it.
However, our transpiled code needs to handle this explicitly for
lambdas defined inside loops.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    IR Tree with lambdas in loops
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │  LoopCaptureOptimizer.visit(ir)                                  │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  1. Find all For/While loops                                     │
    │  2. For each loop, find lambdas/functions in body                │
    │  3. Check if lambda references loop variable                     │
    │  4. If yes, wrap lambda with IIFE to capture value               │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘

=============================================================================
THE FIX
=============================================================================

Before (buggy - all see i=4):
```javascript
for (let i = 0; i < 5; i++) {
    onclick = () => handle(i);  // Captures reference to i
}
```

After (fixed - each sees its own i):
```javascript
for (let i = 0; i < 5; i++) {
    onclick = ((i) => () => handle(i))(i);  // IIFE captures value
}
```

=============================================================================
EXAMPLES
=============================================================================

```python
from pynext.transpiler import parse
from pynext.transpiler.optimizer.capture import fix_loop_captures

ir = parse('''
for i in range(5):
    handlers.append(lambda: handle(i))
''')

fixed = fix_loop_captures(ir)
# Lambda is now wrapped to capture i's value at each iteration
```
"""

from __future__ import annotations
from dataclasses import replace
from typing import Set, List as ListType, Optional

from pynext.transpiler.nodes import (
    JSNode, Program,
    Assignment, For, ForUnpack, While, FunctionDef,
    ExprStmt,
    Name, Lambda, Call, Attribute,
)
from ._internal.visitor import IRVisitor, collect_nodes, find_names


# =============================================================================
# PUBLIC API
# =============================================================================

def fix_loop_captures(ir: Program) -> Program:
    """
    Fix loop variable capture issues in lambdas.
    
    Wraps lambdas that reference loop variables with IIFEs.
    """
    optimizer = LoopCaptureOptimizer()
    return optimizer.visit(ir)


def find_lambdas_in_node(node: JSNode) -> ListType[Lambda]:
    """Find all lambda expressions within a node."""
    return collect_nodes(node, lambda n: isinstance(n, Lambda))


def find_functions_in_node(node: JSNode) -> ListType[FunctionDef]:
    """Find all function definitions within a node."""
    return collect_nodes(node, lambda n: isinstance(n, FunctionDef))


def lambda_references_var(lam: Lambda, var_name: str) -> bool:
    """Check if a lambda references a specific variable."""
    # Get all names used in the lambda body
    body_names = find_names(lam.body)
    
    # Also check default argument values
    for default in lam.defaults:
        if default is not None:
            body_names.update(find_names(default))
    
    return var_name in body_names


def function_references_var(func: FunctionDef, var_name: str) -> bool:
    """Check if a function references a specific variable."""
    # Check all statements in function body
    for stmt in func.body:
        names = find_names(stmt)
        if var_name in names:
            return True
    return False


def get_loop_variables(node: JSNode) -> Set[str]:
    """Get the loop variable(s) from a For/ForUnpack/While node."""
    if isinstance(node, For):
        return {node.target}
    elif isinstance(node, ForUnpack):
        return set(node.targets)
    elif isinstance(node, While):
        # While loops don't have explicit loop variables
        # but we could track variables modified in the loop
        return set()
    return set()


def wrap_lambda_with_capture(lam: Lambda, var_names: Set[str]) -> Call:
    """
    Wrap a lambda with an IIFE to capture loop variables.
    
    Transform:
        lambda: handle(i)
    
    Into:
        ((i) => lambda: handle(i))(i)
    
    Which evaluates to:
        ((i) => () => handle(i))(i)
    """
    # Create the outer lambda that captures the variable
    # (var) => original_lambda
    # Note: These are required parameters (no defaults) since we always pass values
    outer_lambda = Lambda(
        args=tuple(var_names),
        defaults=(),  # No defaults - these are required params
        body=lam,
        line=lam.line,
        col=lam.col,
    )
    
    # Create the IIFE call with current values
    # outer_lambda(var1, var2, ...)
    return Call(
        func=outer_lambda,
        args=tuple(Name(id=var) for var in var_names),
        keywords={},
        line=lam.line,
        col=lam.col,
    )


def wrap_function_with_capture(func: FunctionDef, var_names: Set[str]) -> Call:
    """
    Wrap a function definition with an IIFE to capture loop variables.
    
    This is more complex - we need to create a wrapper that returns
    the function with captured values.
    """
    # Create a lambda that returns a closure over the captured values
    # (var) => function(...) { body }
    # Note: These are required parameters (no defaults) since we always pass values
    outer_lambda = Lambda(
        args=tuple(var_names),
        defaults=(),  # No defaults - these are required params
        body=func,  # The function definition itself
        line=func.line,
        col=func.col,
    )
    
    # Call it immediately with current values
    return Call(
        func=outer_lambda,
        args=tuple(Name(id=var) for var in var_names),
        keywords={},
        line=func.line,
        col=func.col,
    )


# =============================================================================
# LOOP CAPTURE OPTIMIZER
# =============================================================================

class LoopCaptureOptimizer(IRVisitor):
    """
    Optimizer that fixes loop variable capture issues.
    
    When a lambda or function is defined inside a loop and references
    the loop variable, we wrap it with an IIFE to capture the current value.
    """
    
    def __init__(self):
        self.capture_count = 0
        self._current_loop_vars: Set[str] = set()
    
    def visit_For(self, node: For) -> For:
        """Handle for loop - check for lambdas that need capture."""
        # Get loop variable
        loop_var = node.target
        
        # Add to current loop vars (for nested loops)
        old_vars = self._current_loop_vars.copy()
        self._current_loop_vars.add(loop_var)
        
        # First, recursively visit nested loops in the body
        # This ensures inner loops know about outer loop vars
        visited_body = []
        for stmt in node.body:
            visited = self.visit(stmt)
            visited_body.append(visited)
        
        # Then transform the visited body for lambda capture
        # Pass ALL loop vars (including outer loops)
        new_body = []
        for stmt in visited_body:
            transformed = self._transform_statement(stmt, self._current_loop_vars)
            new_body.append(transformed)
        
        # Restore loop vars
        self._current_loop_vars = old_vars
        
        # Return transformed node (don't call generic_visit again)
        return replace(node, body=tuple(new_body))
    
    def visit_ForUnpack(self, node: ForUnpack) -> ForUnpack:
        """Handle for loop with unpacking."""
        loop_vars = set(node.targets)
        
        old_vars = self._current_loop_vars.copy()
        self._current_loop_vars.update(loop_vars)
        
        # First, recursively visit nested loops in the body
        visited_body = []
        for stmt in node.body:
            visited = self.visit(stmt)
            visited_body.append(visited)
        
        # Then transform the visited body for lambda capture
        new_body = []
        for stmt in visited_body:
            transformed = self._transform_statement(stmt, self._current_loop_vars)
            new_body.append(transformed)
        
        self._current_loop_vars = old_vars
        
        return replace(node, body=tuple(new_body))
    
    def visit_While(self, node: While) -> While:
        """
        Handle while loop - we don't auto-capture here since
        there's no explicit loop variable. Users must handle manually.
        """
        return self.generic_visit(node)
    
    def _transform_statement(self, stmt: JSNode, loop_vars: Set[str]) -> JSNode:
        """Transform a statement, wrapping lambdas that need capture."""
        if isinstance(stmt, Assignment):
            return self._transform_assignment(stmt, loop_vars)
        elif isinstance(stmt, ExprStmt):
            return self._transform_expr_stmt(stmt, loop_vars)
        else:
            # For other statements, recursively transform
            return self._transform_node(stmt, loop_vars)
    
    def _transform_assignment(self, node: Assignment, loop_vars: Set[str]) -> Assignment:
        """Transform assignment, wrapping lambda if needed."""
        if isinstance(node.value, Lambda):
            if self._lambda_needs_capture(node.value, loop_vars):
                captured_vars = self._get_captured_vars(node.value, loop_vars)
                wrapped = wrap_lambda_with_capture(node.value, captured_vars)
                self.capture_count += 1
                return replace(node, value=wrapped)
        
        # Transform nested lambdas in expression
        new_value = self._transform_node(node.value, loop_vars)
        if new_value is not node.value:
            return replace(node, value=new_value)
        
        return node
    
    def _transform_expr_stmt(self, node: ExprStmt, loop_vars: Set[str]) -> ExprStmt:
        """Transform expression statement, looking for lambdas in calls."""
        new_value = self._transform_node(node.value, loop_vars)
        if new_value is not node.value:
            return replace(node, value=new_value)
        return node
    
    def _transform_node(self, node: JSNode, loop_vars: Set[str]) -> JSNode:
        """Recursively transform a node, wrapping lambdas as needed."""
        if node is None:
            return None
        
        if isinstance(node, Lambda):
            if self._lambda_needs_capture(node, loop_vars):
                captured_vars = self._get_captured_vars(node, loop_vars)
                self.capture_count += 1
                return wrap_lambda_with_capture(node, captured_vars)
            return node
        
        if isinstance(node, Call):
            return self._transform_call(node, loop_vars)
        
        if isinstance(node, (tuple, list)):
            new_items = []
            changed = False
            for item in node:
                new_item = self._transform_node(item, loop_vars)
                if new_item is not item:
                    changed = True
                new_items.append(new_item)
            if changed:
                return tuple(new_items) if isinstance(node, tuple) else new_items
            return node
        
        # For other node types, we need to transform their children
        # This is a simplified version - full implementation would use visitor
        return node
    
    def _transform_call(self, node: Call, loop_vars: Set[str]) -> Call:
        """Transform a call, wrapping any lambda arguments."""
        new_args = []
        changed = False
        
        for arg in node.args:
            new_arg = self._transform_node(arg, loop_vars)
            if new_arg is not arg:
                changed = True
            new_args.append(new_arg)
        
        # Also transform the function if it's a lambda
        new_func = self._transform_node(node.func, loop_vars)
        if new_func is not node.func:
            changed = True
        
        if changed:
            return replace(node, func=new_func, args=tuple(new_args))
        return node
    
    def _lambda_needs_capture(self, lam: Lambda, loop_vars: Set[str]) -> bool:
        """Check if a lambda needs capture for any loop variable."""
        for var in loop_vars:
            if lambda_references_var(lam, var):
                # Don't capture if the lambda has its own parameter with same name
                if var not in lam.args:
                    return True
        return False
    
    def _get_captured_vars(self, lam: Lambda, loop_vars: Set[str]) -> Set[str]:
        """Get the set of loop variables that need to be captured."""
        captured = set()
        for var in loop_vars:
            if lambda_references_var(lam, var):
                if var not in lam.args:
                    captured.add(var)
        return captured


# =============================================================================
# STATISTICS
# =============================================================================

def count_loop_lambdas(ir: Program) -> int:
    """Count lambdas defined inside loops."""
    count = 0
    
    def visit(node, in_loop=False):
        nonlocal count
        
        if isinstance(node, (For, ForUnpack, While)):
            # Mark that we're in a loop
            for stmt in getattr(node, 'body', []):
                visit(stmt, in_loop=True)
            return
        
        if isinstance(node, Lambda) and in_loop:
            count += 1
        
        # Recurse into children
        for attr in ['body', 'orelse', 'args', 'left', 'right', 'value', 
                     'test', 'comparators', 'values', 'iter', 'target',
                     'func', 'operand', 'elts', 'keys']:
            child = getattr(node, attr, None)
            if child is not None:
                if isinstance(child, (list, tuple)):
                    for c in child:
                        if isinstance(c, JSNode):
                            visit(c, in_loop)
                elif isinstance(child, JSNode):
                    visit(child, in_loop)
    
    for stmt in ir.body:
        visit(stmt)
    
    return count


def needs_capture_fix(ir: Program) -> bool:
    """Check if the IR has any lambdas that need capture fixes."""
    optimizer = LoopCaptureOptimizer()
    
    def check(node):
        if isinstance(node, For):
            loop_var = {node.target}
            for stmt in node.body:
                lambdas = find_lambdas_in_node(stmt)
                for lam in lambdas:
                    if optimizer._lambda_needs_capture(lam, loop_var):
                        return True
        elif isinstance(node, ForUnpack):
            loop_vars = set(node.targets)
            for stmt in node.body:
                lambdas = find_lambdas_in_node(stmt)
                for lam in lambdas:
                    if optimizer._lambda_needs_capture(lam, loop_vars):
                        return True
        
        # Recurse
        for attr in ['body', 'orelse']:
            child = getattr(node, attr, None)
            if child is not None:
                for c in child:
                    if check(c):
                        return True
        return False
    
    for stmt in ir.body:
        if check(stmt):
            return True
    return False
