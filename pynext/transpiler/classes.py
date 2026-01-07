from __future__ import annotations

"""
PyNext Transpiler - Class Emitters

Phase 33.1: Class transpilation including:
- Class definitions with inheritance
- Method definitions (instance, static, class methods)
- Property getters, setters, deleters
- Multiple inheritance via mixins
- Abstract base classes
- Dataclasses
"""

from .nodes import (
    ClassDef, MethodDef, PropertyDef, PropertySetterDef, PropertyDeleterDef,
    DunderMethod,  # Phase 33.2
    ExprStmt, Call, Name
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


def _get_build_params_full():
    """Lazy import to avoid circular dependency."""
    from .functions import _build_params_full
    return _build_params_full


def _constructor_calls_super(method: MethodDef) -> bool:
    """
    Check if constructor method calls super() or super().__init__().
    
    Properly detects:
    - super() 
    - super().__init__()
    - super().__init__(args)
    """
    from .nodes import ExprStmt, Call, Name, Attribute
    
    def _is_super_call(node) -> bool:
        """Recursively check if a node is a super() call."""
        if isinstance(node, Call):
            # Direct super() call: super()
            if isinstance(node.func, Name) and node.func.id == "super":
                return True
            # super().__init__() call: Attribute(value=Call(super()), attr='__init__')
            if isinstance(node.func, Attribute):
                if isinstance(node.func.value, Call):
                    if isinstance(node.func.value.func, Name) and node.func.value.func.id == "super":
                        return True
        return False
    
    for stmt in method.body:
        if isinstance(stmt, ExprStmt):
            if _is_super_call(stmt.value):
                return True
    return False


def _find_matching_paren(s: str, start: int) -> int:
    """
    Find the matching closing parenthesis for an opening paren.
    
    Handles nested parentheses correctly.
    
    Args:
        s: The string to search
        start: Index of the opening parenthesis
        
    Returns:
        Index of the matching closing paren, or -1 if not found
    """
    if start >= len(s) or s[start] != '(':
        return -1
    
    depth = 1
    i = start + 1
    in_string = None  # Track if we're inside a string
    
    while i < len(s) and depth > 0:
        char = s[i]
        
        # Handle string literals
        if in_string:
            if char == in_string and (i == 0 or s[i-1] != '\\'):
                in_string = None
        elif char in ('"', "'", '`'):
            in_string = char
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        
        i += 1
    
    return i - 1 if depth == 0 else -1


def _replace_self_with_this(js_code: str) -> str:
    """
    Replace 'self.' with 'this.' in JavaScript code, avoiding string literals.
    
    FUNDAMENTAL: Uses proper string literal detection - not simple replace.
    
    This correctly handles:
    - self.name → this.name
    - "self.name" → "self.name" (unchanged - it's a string)
    - 'self.value' → 'self.value' (unchanged - it's a string)
    - `text ${self.name} text` → `text ${this.name} text` (replace inside ${})
    """
    result = []
    i = 0
    in_string = None  # Track if we're inside a string literal ('"` or None)
    in_template_expr = False  # Track if we're inside ${} in a template literal
    
    while i < len(js_code):
        char = js_code[i]
        
        # Handle string literal boundaries
        if in_string:
            # Inside a regular string (not template literal)
            if in_string in ('"', "'"):
                result.append(char)
                if char == in_string and (i == 0 or js_code[i-1] != '\\'):
                    in_string = None
                i += 1
                continue
            else:  # Template literal (backtick)
                # Check for closing backtick FIRST (end of template literal)
                if char == '`':
                    in_string = None
                    in_template_expr = False  # Reset template expr state
                    result.append(char)
                    i += 1
                    continue
                # Check for ${} start
                if char == '$' and i + 1 < len(js_code) and js_code[i+1] == '{':
                    in_template_expr = True
                    result.append(char)
                    result.append(js_code[i+1])
                    i += 2
                    continue
                # Check for } end of template expression
                if char == '}' and in_template_expr:
                    in_template_expr = False
                    result.append(char)
                    i += 1
                    continue
                # Check for 'self.' pattern inside ${} expressions
                if in_template_expr and js_code[i:i+5] == 'self.':
                    # Make sure it's not part of a larger identifier
                    if i == 0 or not (js_code[i-1].isalnum() or js_code[i-1] == '_'):
                        result.append('this.')
                        i += 5
                        continue
                # Inside template literal but outside ${} - don't replace self.
                result.append(char)
                i += 1
                continue
        
        # Check for string literal start
        if char in ('"', "'", '`'):
            in_string = char
            result.append(char)
            i += 1
            continue
        
        # Check for 'self.' pattern (only outside strings, or inside ${} in template literals)
        if js_code[i:i+5] == 'self.':
            # Make sure it's not part of a larger identifier (e.g., 'myself.')
            # Check character before 'self' is not alphanumeric or underscore
            if i == 0 or not (js_code[i-1].isalnum() or js_code[i-1] == '_'):
                # Replace if we're not in a string, or if we're in a template expression
                # Note: in_template_expr is only True when we're inside ${} in a template literal
                if in_string is None or (in_string == '`' and in_template_expr):
                    result.append('this.')
                    i += 5
                    continue
        
        # Check for standalone 'self' (not 'self.' and not part of larger identifier)
        # This handles: return self;  →  return this;
        if js_code[i:i+4] == 'self' and (i + 4 >= len(js_code) or js_code[i+4] != '.'):
            # Make sure it's not part of a larger identifier (e.g., 'myself', 'selfish')
            # Check character before 'self' is not alphanumeric or underscore
            # Check character after 'self' is not alphanumeric or underscore
            before_ok = (i == 0 or not (js_code[i-1].isalnum() or js_code[i-1] == '_'))
            after_ok = (i + 4 >= len(js_code) or not (js_code[i+4].isalnum() or js_code[i+4] == '_'))
            if before_ok and after_ok:
                # Replace if we're not in a string, or if we're in a template expression
                if in_string is None or (in_string == '`' and in_template_expr):
                    result.append('this')
                    i += 4
                    continue
        
        result.append(char)
        i += 1
    
    return ''.join(result)


def _transform_super_calls(js_code: str, is_constructor: bool) -> str:
    """
    Transform Python super() calls to JavaScript super calls.
    
    FUNDAMENTAL: Uses proper parenthesis matching - no brittle regex.
    
    In constructor:
        super().__init__(args)  →  super(args)
        super().__init__()      →  super()
    
    In other methods:
        super().method(args)    →  super.method(args)
        super().method()        →  super.method()
    """
    result = []
    i = 0
    
    while i < len(js_code):
        # Look for "super()" pattern
        if js_code[i:i+7] == 'super()':
            if is_constructor:
                # Check for "super().__init__(" - 17 characters
                if js_code[i:i+17] == 'super().__init__(':
                    # Find matching closing paren using proper matching
                    args_start = i + 17  # Position after the opening (
                    args_end = _find_matching_paren(js_code, args_start - 1)
                    if args_end != -1:
                        args = js_code[args_start:args_end]
                        result.append(f'super({args})')
                        i = args_end + 1
                        continue
                # Handle "super().__init__()" - empty args case (18 chars)
                elif js_code[i:i+18] == 'super().__init__()':
                    result.append('super()')
                    i += 18
                    continue
                # Handle "super().__init__" without parens (rare)
                elif js_code[i:i+16] == 'super().__init__' and (i + 16 >= len(js_code) or js_code[i+16] not in '('):
                    result.append('super')
                    i += 16
                    continue
            else:
                # Check for "super().method(" pattern
                if js_code[i+7:i+8] == '.':
                    # Find method name
                    method_start = i + 8
                    method_end = method_start
                    while method_end < len(js_code) and (js_code[method_end].isalnum() or js_code[method_end] == '_'):
                        method_end += 1
                    
                    if method_end > method_start and method_end < len(js_code) and js_code[method_end] == '(':
                        method_name = js_code[method_start:method_end]
                        # Replace super().method( with super.method(
                        result.append(f'super.{method_name}(')
                        i = method_end + 1
                        continue
        
        result.append(js_code[i])
        i += 1
    
    return ''.join(result)


def _emit_class_def(node: ClassDef, indent: int) -> str:
    """
    Emit a class definition.
    
    Examples:
        class Todo:                     → class Todo {
            def __init__(self, title):  →     constructor(title) {
                self.title = title      →         this.title = title;
                                        →     }
                                        → }
        
        class Child(Parent):            → class Child extends Parent {
            ...                         →     ...
                                        → }
        
        @dataclass                      → class Point {
        class Point:                    →     constructor(x = 0, y = 0) {
            x: int = 0                  →         this.x = x;
            y: int = 0                  →         this.y = y;
                                        →     }
                                        →     equals(other) { ... }
                                        →     toString() { ... }
                                        → }
    """
    ind = make_indent(indent)
    inner_ind = make_indent(indent + 1)
    body_ind = make_indent(indent + 2)
    parts = []
    emit = _get_emit()
    _emit_expr = _get_emit_expr()
    _build_params_full = _get_build_params_full()
    
    # Class decorators (limited support - just emit the class, ignore decorators for now)
    # Future: could support specific decorators
    
    # Phase 33.1: Multiple inheritance via mixin pattern
    # First base is primary (extends), additional bases are mixins
    mixins = node.mixins  # Phase 33.1: Use separate mixins field
    
    # Phase 33.1: Register class name in scope BEFORE emitting body
    # This ensures class instantiations in methods (including dunder methods) get 'new' keyword
    scope = get_scope()
    scope.declare_class(node.name)
    
    # Phase 33.2: Register if class has __call__ method
    if node.has_call_method:
        scope.declare_class_with_call(node.name)
    
    # Phase 33.5: Register if class needs Proxy for attribute access
    if node.has_attribute_proxy:
        scope.declare_class_with_attribute_proxy(node.name)
    
    # Class header
    if node.bases:
        parts.append(f"{ind}class {node.name} extends {node.bases[0]} {{")
    else:
        parts.append(f"{ind}class {node.name} {{")
    
    # Phase 33.1: Add abstract class check
    # If class extends ABC, add static _abstract flag and check in constructor
    if node.is_abstract:
        # Check if there's an explicit constructor in the body
        has_explicit_constructor = any(
            isinstance(item, MethodDef) and item.name == "constructor"
            for item in node.body
        )
        if not has_explicit_constructor:
            # Generate a constructor with abstract check
            parts.append(f"{inner_ind}constructor() {{")
            parts.append(f"{body_ind}if (new.target === {node.name}) {{")
            parts.append(f'{body_ind}    throw new Error("TypeError: Cannot instantiate abstract class {node.name}");')
            parts.append(f"{body_ind}}}")
            parts.append(f"{inner_ind}}}")
    
    # Phase 33.1: Auto-generate dataclass methods
    if node.is_dataclass and node.dataclass_fields:
        # Auto-generate constructor
        params = []
        assignments = []
        for field_name, _type_hint, default in node.dataclass_fields:
            if default is not None:
                default_js = _emit_expr(default)
                params.append(f"{field_name} = {default_js}")
            else:
                params.append(field_name)
            assignments.append(f"{body_ind}this.{field_name} = {field_name};")
        
        parts.append(f"{inner_ind}constructor({', '.join(params)}) {{")
        parts.extend(assignments)
        parts.append(f"{inner_ind}}}")
        
        # Auto-generate equals() method (__eq__)
        field_names = [f[0] for f in node.dataclass_fields]
        eq_checks = " && ".join(f"this.{f} === other.{f}" for f in field_names)
        parts.append(f"{inner_ind}equals(other) {{")
        parts.append(f"{body_ind}return other instanceof {node.name} && {eq_checks};")
        parts.append(f"{inner_ind}}}")
        
        # Auto-generate toString() method (__repr__)
        field_strs = ", ".join(f"{f}=${{this.{f}}}" for f in field_names)
        parts.append(f"{inner_ind}toString() {{")
        parts.append(f"{body_ind}return `{node.name}({field_strs})`;")
        parts.append(f"{inner_ind}}}")
    
    # Class body (explicit methods)
    has_explicit_constructor = False
    for item in node.body:
        if isinstance(item, MethodDef):
            if item.name == "constructor":
                has_explicit_constructor = True
                # Phase 33.1: If class extends another and constructor doesn't call super(), add it
                if node.bases and not _constructor_calls_super(item):
                    # Prepend super() call to constructor
                    method_js = _emit_method_def(item, indent + 1)
                    # Insert super() after the opening brace
                    inner_ind = make_indent(indent + 1)
                    method_js = method_js.replace(
                        f"{inner_ind}constructor(",
                        f"{inner_ind}constructor("
                    ).replace(
                        ") {",
                        ") {\n" + inner_ind + "super();"
                    )
                    parts.append(method_js)
                else:
                    parts.append(_emit_method_def(item, indent + 1))
            else:
                parts.append(_emit_method_def(item, indent + 1))
        elif isinstance(item, PropertyDef):
            parts.append(_emit_property_def(item, indent + 1))
        elif isinstance(item, PropertySetterDef):
            parts.append(_emit_property_setter_def(item, indent + 1))
        elif isinstance(item, PropertyDeleterDef):
            parts.append(_emit_property_deleter_def(item, indent + 1))  # Phase 33.1
        elif isinstance(item, DunderMethod):
            # Phase 33.2: Emit dunder methods
            from .dunders import _emit_dunder_method
            parts.append(_emit_dunder_method(item, indent + 1))
        # Skip other items (already filtered by parser)
    
    # Phase 33.1: If class extends another but has no constructor, add one with super()
    if node.bases and not has_explicit_constructor and not node.is_dataclass:
        parts.append(f"{inner_ind}constructor() {{")
        parts.append(f"{body_ind}super();")
        parts.append(f"{inner_ind}}}")
    
    parts.append(f"{ind}}}")
    
    # Phase 33.1: Apply mixins for multiple inheritance
    # Use runtime helper for proper property descriptor copying
    if mixins:
        parts.append("")  # Blank line before mixin code
        for mixin in mixins:
            parts.append(f"{ind}__py_classes.applyMixins({node.name}, [{mixin}]);")
    
    # Phase 33.5: Emit Proxy factory function for classes with attribute access dunders
    # This wraps new instances with Proxy to intercept __getattr__/__setattr__/__delattr__
    if node.has_attribute_proxy:
        parts.append("")  # Blank line before factory
        parts.append(f"{ind}function __py_create_{node.name}(...args) {{")
        parts.append(f"{inner_ind}const instance = new {node.name}(...args);")
        parts.append(f"{inner_ind}return new Proxy(instance, __py.proxy.createAttributeProxy(instance));")
        parts.append(f"{ind}}}")
    
    return "\n".join(parts)


def _emit_method_def(node: MethodDef, indent: int) -> str:
    """
    Emit a method definition within a class.
    
    Examples:
        def toggle(self):               → toggle() {
            self.done = not self.done   →     this.done = !this.done;
                                        → }
        
        @staticmethod                   → static validate(title) {
        def validate(title):            →     return title.length > 0;
            return len(title) > 0       → }
        
        @classmethod                    → static from_dict(data) {
        def from_dict(cls, data):       →     const cls = this.constructor ?? this;
            return cls(**data)          →     return new cls(data);
                                        → }
        
        def __init__(self, name):       → constructor(name) {
            super().__init__(name)      →     super(name);
                                        → }
        
        def process(self):              → process() {
            super().process()           →     super.process();
                                        → }
        
        def items(self):                → *items() {  (Phase 33.2: generator method)
            yield item                  →     yield item;
                                        → }
    """
    # Phase 33.2: Check if this is a generator method
    from .generators import _method_contains_yield
    is_generator = _method_contains_yield(node)
    
    if is_generator:
        # Emit as generator method
        from .generators import _emit_generator_method
        return _emit_generator_method(node, indent)
    
    ind = make_indent(indent)
    inner_ind = make_indent(indent + 1)
    parts = []
    emit = _get_emit()
    _emit_expr = _get_emit_expr()
    _build_params_full = _get_build_params_full()
    
    # Build method signature
    prefix = ""
    if node.is_async:
        prefix += "async "
    if node.is_static or node.is_classmethod:
        # Both @staticmethod and @classmethod are static in JS
        prefix += "static "
    
    # Build full parameter list (methods can have *args and **kwargs too) - Phase 33.1
    # Convert MethodDef to FunctionDef-like structure for parameter building
    class MethodParams:
        posonly_args = ()
        posonly_defaults = ()
        args = node.args
        defaults = node.defaults
        vararg = getattr(node, 'vararg', None)
        kwarg = getattr(node, 'kwarg', None)
        kwonly_args = getattr(node, 'kwonly_args', ())
        kwonly_defaults = getattr(node, 'kwonly_defaults', ())
    
    method_params = MethodParams()
    params_list = _build_params_full(method_params)
    params = ", ".join(params_list) if params_list else ""
    
    # Phase 33.1: Handle private methods and name mangling
    method_name = node.name
    if node.is_mangled:
        # Name mangling: __method → #method (ES2022 private fields)
        # Remove leading __ and use # prefix
        method_name = "#" + node.name[2:] if node.name.startswith("__") else node.name
    elif node.is_private:
        # Private method: _method → keep as _method (convention, not enforced)
        # JavaScript doesn't enforce private methods, but we keep the underscore
        method_name = node.name
    
    parts.append(f"{ind}{prefix}{method_name}({params}) {{")
    
    # Phase 33.1: Handle @abstractmethod - emit NotImplementedError
    if node.is_abstract:
        parts.append(f'{inner_ind}throw new Error("NotImplementedError: {node.name} must be implemented by subclass");')
        parts.append(f"{ind}}}")
        return "\n".join(parts)
    
    # Enter function scope for method body (isolated from class scope)
    # This ensures variables declared in one method don't conflict with another
    scope = get_scope()
    scope.enter_function_scope()
    
    # Declare method parameters in function scope - Phase 33.1: include vararg/kwarg
    for arg in node.args:
        scope.declare(safe_js_name(arg))
    if getattr(node, 'vararg', None):
        scope.declare(safe_js_name(node.vararg))
    if getattr(node, 'kwarg', None):
        scope.declare(safe_js_name(node.kwarg))
    for arg in getattr(node, 'kwonly_args', ()):
        scope.declare(safe_js_name(arg))
    
    try:
        # For @classmethod, inject 'const cls = this.constructor ?? this;' at start
        # This binds 'cls' to the class constructor for use in method body
        if node.is_classmethod:
            parts.append(f"{inner_ind}const cls = this.constructor ?? this;")
        
        # Phase 33.1: Handle *args with **kwargs or keyword-only args (same as functions)
        vararg = getattr(node, 'vararg', None)
        kwarg = getattr(node, 'kwarg', None)
        kwonly_args = getattr(node, 'kwonly_args', ())
        kwonly_defaults = getattr(node, 'kwonly_defaults', ())
        
        if vararg and (kwarg or kwonly_args):
            vararg_name = safe_js_name(vararg)
            kwarg_name = safe_js_name(kwarg) if kwarg else "__kwargs__"
            parts.append(f"{inner_ind}const {kwarg_name} = ({vararg_name}.length > 0 && {vararg_name}[{vararg_name}.length - 1]?.__kw__) ? {vararg_name}.pop() : {{}};")
        
        # Handle keyword-only args when there's a vararg
        if vararg and kwonly_args:
            kwarg_name = safe_js_name(kwarg) if kwarg else "__kwargs__"
            for i, arg in enumerate(kwonly_args):
                arg_name = safe_js_name(arg)
                default = kwonly_defaults[i] if i < len(kwonly_defaults) else None
                if default:
                    default_js = _emit_expr(default)
                    parts.append(f"{inner_ind}const {arg_name} = {kwarg_name}.{arg_name} ?? {default_js};")
                else:
                    parts.append(f"{inner_ind}const {arg_name} = {kwarg_name}.{arg_name};")
        
        # Method body - replace 'self' with 'this' and transform super() calls
        is_constructor = node.name == "constructor"
        for stmt in node.body:
            emitted = emit(stmt, indent + 1)
            # Replace self. with this. (avoiding string literals)
            emitted = _replace_self_with_this(emitted)
            # Transform super() calls
            emitted = _transform_super_calls(emitted, is_constructor)
            parts.append(emitted)
    finally:
        # Exit function scope
        scope.exit_scope()
    
    parts.append(f"{ind}}}")
    
    return "\n".join(parts)


def _emit_property_def(node: PropertyDef, indent: int) -> str:
    """
    Emit a property getter.
    
    Examples:
        @property                       → get status() {
        def status(self):               →     return this.done ? "Done" : "Pending";
            return "Done" if self.done  → }
                   else "Pending"
    """
    ind = make_indent(indent)
    parts = []
    emit = _get_emit()
    
    parts.append(f"{ind}get {node.name}() {{")
    
    # Property body - replace 'self' with 'this' (avoiding string literals)
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        emitted = _replace_self_with_this(emitted)
        parts.append(emitted)
    
    parts.append(f"{ind}}}")
    
    return "\n".join(parts)


def _emit_property_setter_def(node: PropertySetterDef, indent: int) -> str:
    """
    Emit a property setter.
    
    Examples:
        @value.setter                   → set value(val) {
        def value(self, val):           →     this._value = val;
            self._value = val           → }
    """
    ind = make_indent(indent)
    parts = []
    emit = _get_emit()
    
    parts.append(f"{ind}set {node.name}({node.arg}) {{")
    
    # Setter body - replace 'self' with 'this' (avoiding string literals)
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        emitted = _replace_self_with_this(emitted)
        parts.append(emitted)
    
    parts.append(f"{ind}}}")
    
    return "\n".join(parts)


def _emit_property_deleter_def(node: PropertyDeleterDef, indent: int) -> str:
    """
    Emit a property deleter - Phase 33.1.
    
    Examples:
        @value.deleter                  → delete value() {
        def value(self):                →     delete this._value;
            del self._value             → }
    
    Note: JavaScript doesn't have a delete operator for properties like Python's del.
    We use a custom delete descriptor pattern or just emit the body.
    """
    ind = make_indent(indent)
    parts = []
    emit = _get_emit()
    
    # Phase 33.1: Property deleter - use a custom pattern
    # We'll create a delete method that can be called
    parts.append(f"{ind}delete {node.name}() {{")
    
    # Deleter body - replace 'self' with 'this'
    for stmt in node.body:
        emitted = emit(stmt, indent + 1)
        emitted = _replace_self_with_this(emitted)
        parts.append(emitted)
    
    parts.append(f"{ind}}}")
    
    return "\n".join(parts)

