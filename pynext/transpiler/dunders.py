"""
PyNext Transpiler - Dunder Method Emitters

=============================================================================
WHAT THIS FILE DOES
=============================================================================
Transpiles Python dunder methods (__str__, __eq__, __iter__, etc.) to 
JavaScript equivalents, preserving Python semantics while optimizing for
performance and bundle size.

Dunder methods enable operator overloading and special behaviors in Python.
This module handles all categories of dunder methods:
- String representation (__str__, __repr__, __format__)
- Comparison (__eq__, __ne__, __lt__, __gt__, __le__, __ge__)
- Container (__len__, __bool__, __iter__, __next__, __contains__, __getitem__, etc.)
- Arithmetic (__add__, __sub__, __mul__, __truediv__, __radd__, etc.)
- Callable (__call__)
- Attribute access (__getattr__, __setattr__, __delattr__)

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================
Python's dunder methods enable operator overloading and special behaviors.
JavaScript doesn't have direct equivalents, so we need to:
1. Map dunder methods to JavaScript patterns (toString, Symbol.iterator, etc.)
2. Handle type coercion correctly
3. Optimize common cases (avoid Proxy overhead when possible)
4. Preserve Python semantics (e.g., __eq__ vs ==)

For example:
- Python: `obj1 == obj2` calls `obj1.__eq__(obj2)`
- JavaScript: `obj1 === obj2` is direct comparison
- Solution: Emit `obj1.equals(obj2)` which uses `__eq__` if defined, else `===`

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    DunderMethod IR Node
         │
         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  _emit_dunder_method(node)                              │
    │      │                                                   │
    │      ├── Check dunder_type                              │
    │      │                                                   │
    │      ├── "string" → _emit_string_dunder()              │
    │      │   - __str__ → toString()                         │
    │      │   - __repr__ → Symbol.for("repr")                │
    │      │   - __format__ → custom formatter                 │
    │      │                                                   │
    │      ├── "comparison" → _emit_comparison_dunder()       │
    │      │   - __eq__ → equals() or optimized ===           │
    │      │   - __lt__ → comparison method                   │
    │      │                                                   │
    │      ├── "container" → _emit_container_dunder()         │
    │      │   - __len__ → get length()                        │
    │      │   - __iter__ → *[Symbol.iterator]()              │
    │      │   - __getitem__ → Proxy handler                  │
    │      │                                                   │
    │      ├── "arithmetic" → _emit_arithmetic_dunder()       │
    │      │   - __add__ → __add__() method                   │
    │      │   - __radd__ → reverse operation                 │
    │      │                                                   │
    │      ├── "callable" → _emit_callable_dunder()           │
    │      │   - __call__ → callable object pattern           │
    │      │                                                   │
    │      └── "attribute" → _emit_attribute_dunder()         │
    │          - __getattr__ → Proxy get handler               │
    │          - __setattr__ → Proxy set handler               │
    └─────────────────────────────────────────────────────────┘

Optimization Strategy:
- Simple cases use native JS (e.g., __str__ → toString())
- Complex cases use runtime helpers (e.g., __eq__ → equals())
- Proxy only when necessary (e.g., __getitem__ for dynamic access)
- Tree-shakeable runtime helpers

=============================================================================
WHO USES THIS
=============================================================================
- emitter.py: Calls dunder emitters when emitting class methods
- Classes with dunder methods: Automatically use these emitters
- Runtime helpers: dunders.js provides Pythonic semantics

=============================================================================
WHEN TO USE (vs Alternatives)
=============================================================================
USE dunder emitters:
- When transpiling classes with dunder methods
- When you need Python operator overloading in JavaScript

DON'T USE directly:
- These are called automatically by the emitter
- Regular methods use MethodDef, not DunderMethod

=============================================================================
EXAMPLES
=============================================================================

String Representation:
    Python:                          JavaScript:
    def __str__(self):               toString() {
        return f"{self.x}"               return `${this.x}`;
                                    }
    
    def __repr__(self):              [Symbol.for("repr")]() {
        return f"Point({self.x})"       return `Point(${this.x})`;
                                    }

Comparison:
    Python:                          JavaScript:
    def __eq__(self, other):         equals(other) {
        return self.x == other.x         return this.x === other.x;
                                    }
    
    # Optimized case (simple types):
    def __eq__(self, other):         equals(other) {
        if not isinstance(other, Point):  if (!(other instanceof Point)) {
            return False                       return false;
        return self.x == other.x         }
                                    return this.x === other.x;
                                    }

Container:
    Python:                          JavaScript:
    def __len__(self):               get length() {
        return len(self.items)          return this.items.length;
                                    }
    
    def __iter__(self):              *[Symbol.iterator]() {
        yield self.x                    yield this.x;
        yield self.y                    yield this.y;
                                    }

Arithmetic:
    Python:                          JavaScript:
    def __add__(self, other):        __add__(other) {
        return Point(self.x + other.x,   return new Point(
                  self.y + other.y)          this.x + other.x,
                                            this.y + other.y
                                        );
                                    }

Callable:
    Python:                          JavaScript:
    def __call__(self, x):           __call__(x) {
        return self.value * x            return this.value * x;
                                    }

Attribute Access:
    Python:                          JavaScript:
    def __getattr__(self, name):     // Via Proxy wrapper
        if name == "computed":           get(target, prop) {
            return self._compute()           if (prop === "computed") {
        raise AttributeError(name)              return target._compute();
                                            }
                                            throw new AttributeError(prop);
                                        }
"""

from __future__ import annotations

from .nodes import DunderMethod
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


def _emit_dunder_method(node: DunderMethod, indent: int) -> str:
    """
    Emit a dunder method to JavaScript.
    
    Routes to specific emitter based on dunder_type for optimization.
    
    Args:
        node: DunderMethod IR node
        indent: Indentation level
    
    Returns:
        JavaScript source code
    """
    # Enter function scope for proper variable tracking
    from ._internal.scope import get_scope
    scope = get_scope()
    scope.enter_scope()
    
    try:
        dunder_type = node.dunder_type
        
        if dunder_type == "string":
            return _emit_string_dunder(node, indent)
        elif dunder_type == "comparison":
            return _emit_comparison_dunder(node, indent)
        elif dunder_type == "container":
            return _emit_container_dunder(node, indent)
        elif dunder_type == "arithmetic":
            return _emit_arithmetic_dunder(node, indent)
        elif dunder_type == "callable":
            return _emit_callable_dunder(node, indent)
        elif dunder_type == "attribute":
            return _emit_attribute_dunder(node, indent)
        elif dunder_type == "context":
            # Context manager dunders (__enter__, __exit__, __aenter__, __aexit__)
            # Emit as regular methods with self → this replacement
            return _emit_generic_dunder(node, indent)
        else:
            # Fallback: emit as regular method
            return _emit_generic_dunder(node, indent)
    finally:
        # Exit function scope
        scope.exit_scope()


def _emit_string_dunder(node: DunderMethod, indent: int) -> str:
    """
    Emit string representation dunders (__str__, __repr__, __format__).
    
    Examples:
        __str__ → toString()
        __repr__ → [Symbol.for("repr")]()
        __format__ → [Symbol.for("format")](format_spec)
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    emit_expr = _get_emit_expr()
    
    method_name = node.name
    
    if method_name == "__str__":
        # __str__ → toString()
        js_method = "toString"
    elif method_name == "__repr__":
        # __repr__ → Symbol.for("repr")
        js_method = '[Symbol.for("repr")]'
    elif method_name == "__format__":
        # __format__ → [Symbol.for("format")](format_spec)
        js_method = '[Symbol.for("format")]'
    else:
        # Unknown string dunder, emit as-is
        js_method = safe_js_name(method_name)
    
    # Emit method signature
    if node.args:
        params = ", ".join(safe_js_name(arg) for arg in node.args)
        signature = f"{js_method}({params})"
    else:
        signature = f"{js_method}()"
    
    # Emit body - replace self with this (same as regular methods)
    from .classes import _replace_self_with_this
    body_lines = []
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Replace self. with this. (avoiding string literals)
        emitted = _replace_self_with_this(emitted)
        body_lines.append(emitted)
    
    if not body_lines:
        body_lines.append(f"{prefix}    /* pass */")
    
    body = "\n".join(body_lines)
    
    return f"{prefix}{signature} {{\n{body}\n{prefix}}}"


def _emit_comparison_dunder(node: DunderMethod, indent: int) -> str:
    """
    Emit comparison dunders (__eq__, __ne__, __lt__, __gt__, __le__, __ge__).
    
    Examples:
        __eq__ → equals(other) or optimized ===
        __lt__ → __lt__(other)
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    
    method_name = node.name
    
    if method_name == "__eq__":
        # __eq__ → equals(other)
        js_method = "equals"
    elif method_name == "__ne__":
        # __ne__ → notEquals(other) or !equals(other)
        js_method = "notEquals"
    else:
        # __lt__, __gt__, __le__, __ge__ → __lt__(other), etc.
        js_method = safe_js_name(method_name)
    
    # Emit method signature
    if node.args:
        params = ", ".join(safe_js_name(arg) for arg in node.args)
        signature = f"{js_method}({params})"
    else:
        signature = f"{js_method}()"
    
    # Emit body - replace self with this (same as regular methods)
    from .classes import _replace_self_with_this
    body_lines = []
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Replace self. with this. (avoiding string literals)
        emitted = _replace_self_with_this(emitted)
        body_lines.append(emitted)
    
    if not body_lines:
        body_lines.append(f"{prefix}    /* pass */")
    
    body = "\n".join(body_lines)
    
    return f"{prefix}{signature} {{\n{body}\n{prefix}}}"


def _emit_container_dunder(node: DunderMethod, indent: int) -> str:
    """
    Emit container dunders (__len__, __bool__, __iter__, __next__, __contains__, __getitem__, etc.).
    
    Examples:
        __len__ → get length()
        __bool__ → [Symbol.toPrimitive]("boolean")
        __iter__ → *[Symbol.iterator]()
        __getitem__ → (handled by Proxy wrapper)
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    
    method_name = node.name
    
    if method_name == "__len__":
        # __len__ → get length()
        js_method = "get length"
        signature = "()"  # Getters have no parameters
    elif method_name == "__bool__":
        # __bool__ → [Symbol.toPrimitive](hint) with boolean check
        js_method = '[Symbol.toPrimitive]'
        signature = '(hint)'
    elif method_name == "__iter__":
        # __iter__ → *[Symbol.iterator]()
        js_method = "*[Symbol.iterator]"
        signature = "()"
    elif method_name == "__next__":
        # __next__ → next()
        js_method = "next"
        signature = "()"
    elif method_name == "__contains__":
        # __contains__ → has(item) or includes(item)
        js_method = "has"
        if node.args:
            params = ", ".join(safe_js_name(arg) for arg in node.args)
            signature = f"({params})"
        else:
            signature = "()"
    elif method_name in ("__getitem__", "__setitem__", "__delitem__"):
        # These are handled by Proxy wrappers, but we still emit the method
        # for the Proxy to call
        js_method = safe_js_name(method_name)
        if node.args:
            params = ", ".join(safe_js_name(arg) for arg in node.args)
            signature = f"({params})"
        else:
            signature = "()"
    else:
        # Unknown container dunder
        js_method = safe_js_name(method_name)
        if node.args:
            params = ", ".join(safe_js_name(arg) for arg in node.args)
            signature = f"({params})"
        else:
            signature = "()"
    
    # Emit body - replace self with this (same as regular methods)
    from .classes import _replace_self_with_this
    body_lines = []
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Replace self. with this. (avoiding string literals)
        emitted = _replace_self_with_this(emitted)
        body_lines.append(emitted)
    
    if not body_lines:
        body_lines.append(f"{prefix}    /* pass */")
    
    body = "\n".join(body_lines)
    
    return f"{prefix}{js_method}{signature} {{\n{body}\n{prefix}}}"


def _emit_arithmetic_dunder(node: DunderMethod, indent: int) -> str:
    """
    Emit arithmetic dunders (__add__, __sub__, __mul__, __truediv__, __radd__, etc.).
    
    Examples:
        __add__ → __add__(other)
        __radd__ → __radd__(other) (reverse operation)
        __iadd__ → __iadd__(other) (in-place operation)
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    
    # Arithmetic dunders keep their Python names (__add__, __sub__, etc.)
    js_method = safe_js_name(node.name)
    
    # Emit method signature
    if node.args:
        params = ", ".join(safe_js_name(arg) for arg in node.args)
        signature = f"{js_method}({params})"
    else:
        signature = f"{js_method}()"
    
    # Emit body - replace self with this (same as regular methods)
    from .classes import _replace_self_with_this
    body_lines = []
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Replace self. with this. (avoiding string literals)
        emitted = _replace_self_with_this(emitted)
        body_lines.append(emitted)
    
    if not body_lines:
        body_lines.append(f"{prefix}    /* pass */")
    
    body = "\n".join(body_lines)
    
    return f"{prefix}{signature} {{\n{body}\n{prefix}}}"


def _emit_callable_dunder(node: DunderMethod, indent: int) -> str:
    """
    Emit callable dunder (__call__).
    
    Examples:
        __call__ → __call__(...args)
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    
    # __call__ → __call__(...args)
    js_method = "__call__"
    
    # Emit method signature
    if node.args:
        params = ", ".join(safe_js_name(arg) for arg in node.args)
        signature = f"{js_method}({params})"
    else:
        signature = f"{js_method}()"
    
    # Emit body - replace self with this (same as regular methods)
    from .classes import _replace_self_with_this
    body_lines = []
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Replace self. with this. (avoiding string literals)
        emitted = _replace_self_with_this(emitted)
        body_lines.append(emitted)
    
    if not body_lines:
        body_lines.append(f"{prefix}    /* pass */")
    
    body = "\n".join(body_lines)
    
    return f"{prefix}{signature} {{\n{body}\n{prefix}}}"


def _emit_attribute_dunder(node: DunderMethod, indent: int) -> str:
    """
    Emit attribute access dunders (__getattr__, __setattr__, __delattr__).
    
    These are typically handled by Proxy wrappers, but we emit the methods
    for the Proxy to call.
    
    Examples:
        __getattr__ → __getattr__(name)
        __setattr__ → __setattr__(name, value)
        __delattr__ → __delattr__(name)
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    
    # Attribute dunders keep their Python names
    js_method = safe_js_name(node.name)
    
    # Emit method signature
    if node.args:
        params = ", ".join(safe_js_name(arg) for arg in node.args)
        signature = f"{js_method}({params})"
    else:
        signature = f"{js_method}()"
    
    # Emit body - replace self with this (same as regular methods)
    from .classes import _replace_self_with_this
    body_lines = []
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Replace self. with this. (avoiding string literals)
        emitted = _replace_self_with_this(emitted)
        body_lines.append(emitted)
    
    if not body_lines:
        body_lines.append(f"{prefix}    /* pass */")
    
    body = "\n".join(body_lines)
    
    return f"{prefix}{signature} {{\n{body}\n{prefix}}}"


def _emit_generic_dunder(node: DunderMethod, indent: int) -> str:
    """
    Fallback emitter for unknown dunder methods.
    
    Emits as a regular method with the original dunder name.
    """
    prefix = make_indent(indent)
    emit = _get_emit()
    
    js_method = safe_js_name(node.name)
    
    # Emit method signature
    if node.args:
        params = ", ".join(safe_js_name(arg) for arg in node.args)
        signature = f"{js_method}({params})"
    else:
        signature = f"{js_method}()"
    
    # Emit body - replace self with this (same as regular methods)
    from .classes import _replace_self_with_this
    body_lines = []
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        # Replace self. with this. (avoiding string literals)
        emitted = _replace_self_with_this(emitted)
        body_lines.append(emitted)
    
    if not body_lines:
        body_lines.append(f"{prefix}    /* pass */")
    
    body = "\n".join(body_lines)
    
    return f"{prefix}{signature} {{\n{body}\n{prefix}}}"

