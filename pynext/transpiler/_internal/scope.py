"""
PyNext Transpiler - Scope Tracking

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Tracks variable declarations to emit correct JavaScript:
- First assignment: `let x = 5;`
- Reassignment: `x = 10;` (no let)

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

JavaScript doesn't allow redeclaring variables with `let`:
```javascript
let x = 5;
let x = 10;  // SyntaxError!
```

Python allows unlimited reassignment:
```python
x = 5
x = 10  # Fine
```

The scope tracker ensures we only emit `let` for first declaration.

=============================================================================
HOW IT WORKS
=============================================================================

Maintains a stack of scopes. Each scope is a set of declared variable names.
When entering a function/block, push a new scope. When exiting, pop it.
"""

from __future__ import annotations
from typing import Optional
from dataclasses import dataclass


# =============================================================================
# SEMANTIC CONTEXT TRACKING (Unified Context System)
# =============================================================================

@dataclass
class SemanticContext:
    """
    Base class for semantic contexts.
    
    Semantic contexts track Python's evaluation model throughout the pipeline:
    - Method context: self → this transformation
    - Class context: class-level operations
    - Guard context: pattern matching guard clauses (variables in scope)
    """
    pass


@dataclass
class MethodContext(SemanticContext):
    """
    Context: inside a method (self → this).
    
    Attributes:
        class_name: Name of the class containing this method
        method_name: Name of the method
    """
    class_name: str
    method_name: str


@dataclass
class ClassContext(SemanticContext):
    """
    Context: inside a class definition.
    
    Attributes:
        class_name: Name of the class
    """
    class_name: str


@dataclass
class GuardContext(SemanticContext):
    """
    Context: inside a pattern matching guard clause.
    
    Variables captured by the pattern are in scope for the guard.
    
    Attributes:
        pattern_vars: Set of variable names captured by the pattern
    """
    pattern_vars: set[str]


class ScopeTracker:
    """
    Tracks variable declarations across scopes.
    
    Usage:
        scope = ScopeTracker()
        scope.is_new_var("x")  # True, first time
        scope.is_new_var("x")  # False, already declared
        
        scope.enter_function_scope()  # New isolated scope (function)
        scope.is_new_var("x")  # True, isolated from outer scope
        scope.is_new_var("y")  # True, new in this scope
        scope.exit_scope()
    
    Function scopes are isolated - assignments create local variables,
    just like in Python (without global/nonlocal).
    """
    
    def __init__(self):
        # Stack of scopes, each scope is a set of variable names
        self._scopes: list[set[str]] = [set()]
        # Track which scopes are function scopes (isolated)
        self._is_function_scope: list[bool] = [False]
        # Track class names (for proper 'new' keyword emission)
        self._class_names: set[str] = set()
        # Phase 33.2: Track callable objects (instances of classes with __call__)
        self._callable_objects: set[str] = set()
        # Phase 33.2: Track classes that have __call__ method
        self._classes_with_call: set[str] = set()
        # Phase 33.2: Track generator functions (functions with yield)
        self._generator_functions: set[str] = set()
        # Phase 33.2+: Track async generator functions (async def with yield)
        # Separate from regular generators because:
        # 1. They emit as async function* (different JavaScript syntax)
        # 2. They need wrapAsyncGenerator() instead of wrapGenerator() (different runtime)
        # 3. They return Promise<IteratorResult> instead of IteratorResult (different types)
        self._async_generator_functions: set[str] = set()
        # Phase 33.2: Track await context depth (to skip generator wrapping in await expressions)
        self._await_context_depth: int = 0
        # Unified semantic context tracking
        self._context_stack: list[SemanticContext] = []
    
    def enter_scope(self) -> None:
        """Enter a new block scope (if, for, while)."""
        self._scopes.append(set())
        self._is_function_scope.append(False)
    
    def enter_function_scope(self) -> None:
        """Enter a new function scope (isolated from outer scopes)."""
        self._scopes.append(set())
        self._is_function_scope.append(True)
    
    def exit_scope(self) -> None:
        """Exit the current scope."""
        if len(self._scopes) > 1:
            self._scopes.pop()
            self._is_function_scope.pop()
    
    def is_new_var(self, name: str) -> bool:
        """
        Check if this is the first declaration of a variable.
        
        Returns True if this is a new variable (needs `let`),
        False if it's a reassignment (no `let`).
        
        For function scopes: only checks current scope (isolated).
        For block scopes: checks current and outer scopes.
        
        Also registers the variable as declared.
        """
        # If we're in a function scope, only check current scope
        if self._is_function_scope[-1]:
            if name in self._scopes[-1]:
                return False  # Already declared in this function
            self._scopes[-1].add(name)
            return True
        
        # For block scopes, check all scopes up to the nearest function scope
        for i in range(len(self._scopes) - 1, -1, -1):
            if name in self._scopes[i]:
                return False  # Already declared
            # Stop at function boundary
            if self._is_function_scope[i]:
                break
        
        # First time - declare it in current scope
        self._scopes[-1].add(name)
        return True
    
    def is_declared(self, name: str) -> bool:
        """Check if a variable is declared (without declaring it)."""
        for scope in self._scopes:
            if name in scope:
                return True
        return False
    
    def declare(self, name: str) -> None:
        """Explicitly declare a variable in current scope."""
        self._scopes[-1].add(name)
    
    def declare_class(self, name: str) -> None:
        """Declare a class name (for detecting class instantiations)."""
        self._class_names.add(name)
    
    def is_class_name(self, name: str) -> bool:
        """Check if a name refers to a class (needs 'new' keyword)."""
        return name in self._class_names
    
    def declare_class_with_call(self, class_name: str) -> None:
        """Mark a class as having __call__ method (Phase 33.2)."""
        self._classes_with_call.add(class_name)
    
    def class_has_call(self, class_name: str) -> bool:
        """Check if a class has __call__ method (Phase 33.2)."""
        return class_name in self._classes_with_call
    
    def declare_callable_object(self, name: str) -> None:
        """Mark a variable as a callable object (has __call__ method) (Phase 33.2)."""
        self._callable_objects.add(name)
    
    def is_callable_object(self, name: str) -> bool:
        """Check if a variable is a known callable object (Phase 33.2)."""
        return name in self._callable_objects
    
    def declare_generator_function(self, name: str) -> None:
        """Mark a function as a generator function (has yield) (Phase 33.2)."""
        self._generator_functions.add(name)
    
    def is_generator_function(self, name: str) -> bool:
        """Check if a function is a known generator function (Phase 33.2)."""
        return name in self._generator_functions
    
    def declare_async_generator_function(self, name: str) -> None:
        """
        Mark a function as an async generator function (async def with yield).
        
        WHAT: Declares that a function is an async generator, meaning it contains
              yield/yield from and should be transpiled as `async function*`.
        
        WHY: Async generators need special handling:
             1. Emit as `async function*` instead of `async function`
             2. Wrap calls with `wrapAsyncGenerator()` instead of `wrapGenerator()`
             3. Return `Promise<IteratorResult>` instead of `IteratorResult`
        
        HOW: Called by the emitter when it detects yield/yield from in an
             AsyncFunctionDef. The function name is stored in a set for later
             lookup during call emission.
        
        WHO: Called by async_support.py: _emit_async_function_def() when it
             detects that an AsyncFunctionDef contains yield/yield from.
        
        WHEN: During the emission phase, after parsing but before final JavaScript
              output. The function must have already been parsed as AsyncFunctionDef.
        
        WHERE: Part of scope tracking, used by emitter.py to determine how to
               wrap function calls.
        
        Args:
            name: The JavaScript-safe name of the async generator function.
                 This is the name after safe_js_name() transformation.
        
        Examples:
            # In async_support.py:
            if _contains_yield(node):
                scope.declare_async_generator_function("fetch_pages")
                # Later, in emitter.py:
                if scope.is_async_generator_function("fetch_pages"):
                    # Wrap with wrapAsyncGenerator()
        
        Related:
            - async_support.py: _emit_async_function_def() - calls this
            - emitter.py: _emit_call() - checks this to wrap calls
            - generators.js: wrapAsyncGenerator() - runtime wrapper
        """
        self._async_generator_functions.add(name)
    
    def is_async_generator_function(self, name: str) -> bool:
        """
        Check if a function is a known async generator function.
        
        WHAT: Checks if a function name has been declared as an async generator.
        
        WHY: Used during call emission to determine if a function call should be
             wrapped with `wrapAsyncGenerator()` instead of `wrapGenerator()`.
        
        HOW: Looks up the function name in the `_async_generator_functions` set.
             Returns True if found, False otherwise.
        
        WHO: Called by emitter.py: _emit_call() when emitting function calls.
        
        WHEN: During the emission phase, when emitting a Call node that references
              a function name.
        
        WHERE: Part of scope tracking, used by emitter.py for call wrapping.
        
        Args:
            name: The JavaScript-safe name of the function to check.
                 This should match the name used in declare_async_generator_function().
        
        Returns:
            True if the function is a known async generator, False otherwise.
        
        Examples:
            # In emitter.py:
            if scope.is_async_generator_function("fetch_pages"):
                # This is an async generator call - wrap with wrapAsyncGenerator()
                return f"wrapAsyncGenerator({call})"
            elif scope.is_generator_function("fetch_pages"):
                # This is a regular generator call - wrap with wrapGenerator()
                return f"wrapGenerator({call})"
        
        Related:
            - declare_async_generator_function() - sets this flag
            - emitter.py: _emit_call() - uses this for call wrapping
        """
        return name in self._async_generator_functions
    
    def enter_await_context(self) -> None:
        """Enter an await expression context (Phase 33.2)."""
        self._await_context_depth += 1
    
    def exit_await_context(self) -> None:
        """Exit an await expression context (Phase 33.2)."""
        if self._await_context_depth > 0:
            self._await_context_depth -= 1
    
    def is_in_await_context(self) -> bool:
        """Check if we're currently inside an await expression (Phase 33.2)."""
        return self._await_context_depth > 0
    
    def reset(self) -> None:
        """Reset all scopes (for new transpilation)."""
        self._scopes = [set()]
        self._is_function_scope = [False]
        self._class_names = set()
        self._callable_objects = set()
        self._classes_with_call = set()
        self._generator_functions = set()
        self._async_generator_functions = set()
        self._await_context_depth = 0
        self._context_stack = []
    
    # =============================================================================
    # SEMANTIC CONTEXT TRACKING (Unified Context System)
    # =============================================================================
    
    def enter_context(self, context: SemanticContext) -> None:
        """
        Enter a semantic context (method, class, guard clause, etc.).
        
        Contexts are tracked in a stack to handle nested contexts.
        
        Examples:
            scope.enter_context(MethodContext(class_name="Vector", method_name="__str__"))
            scope.enter_context(GuardContext(pattern_vars={"x"}))
        """
        self._context_stack.append(context)
    
    def exit_context(self) -> None:
        """Exit the current semantic context."""
        if self._context_stack:
            self._context_stack.pop()
    
    def get_current_context(self) -> Optional[SemanticContext]:
        """Get the current semantic context (most recent)."""
        return self._context_stack[-1] if self._context_stack else None
    
    def is_in_method_context(self) -> bool:
        """
        Check if we're currently in a method context.
        
        Returns True if any context in the stack is a MethodContext.
        This is used to transform 'self' → 'this' during parsing.
        """
        return any(isinstance(ctx, MethodContext) for ctx in self._context_stack)
    
    def is_in_class_context(self) -> bool:
        """
        Check if we're currently in a class context.
        
        Returns True if any context in the stack is a ClassContext.
        """
        return any(isinstance(ctx, ClassContext) for ctx in self._context_stack)
    
    def is_in_guard_context(self) -> bool:
        """
        Check if we're currently in a pattern matching guard clause context.
        
        Returns True if any context in the stack is a GuardContext.
        This is used to ensure pattern variables are in scope for guards.
        """
        return any(isinstance(ctx, GuardContext) for ctx in self._context_stack)
    
    def get_method_context(self) -> Optional[MethodContext]:
        """Get the current method context, if any."""
        for ctx in reversed(self._context_stack):
            if isinstance(ctx, MethodContext):
                return ctx
        return None
    
    def get_guard_context(self) -> Optional[GuardContext]:
        """Get the current guard context, if any."""
        for ctx in reversed(self._context_stack):
            if isinstance(ctx, GuardContext):
                return ctx
        return None
    
    def get_current_scope_depth(self) -> int:
        """Get current scope nesting depth."""
        return len(self._scopes)
    
    def is_in_function_scope(self) -> bool:
        """Check if we're currently inside a function scope."""
        return any(self._is_function_scope)
    
    def get_outer_variable(self, name: str) -> bool:
        """
        Check if a variable exists in an outer scope (for shadowing detection).
        
        Returns True if the variable is declared in an outer scope (not current).
        This is useful for detecting variable shadowing in nested functions.
        """
        # Check all scopes except current
        for i in range(len(self._scopes) - 2, -1, -1):
            if name in self._scopes[i]:
                return True
        return False
    
    def declare_in_current_only(self, name: str) -> bool:
        """
        Declare a variable in current scope only, regardless of outer scopes.
        
        Used for loop variables in comprehensions that should be local.
        Returns True if this is a new declaration in current scope.
        """
        is_new = name not in self._scopes[-1]
        self._scopes[-1].add(name)
        return is_new


# Global instance for convenience
_global_scope = ScopeTracker()


def get_scope() -> ScopeTracker:
    """Get the global scope tracker."""
    return _global_scope


def reset_scope() -> None:
    """Reset the global scope tracker."""
    _global_scope.reset()
