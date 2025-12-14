"""
PyNext Compiler - Emitter (IR → JavaScript)

=============================================================================
WHAT THIS FILE DOES
=============================================================================

The emitter is the FINAL stage of the compiler pipeline. It takes the analyzed
IR and generates optimized JavaScript that uses the PyNext reactive runtime.

    IR (with dependencies) → [EMITTER] → JavaScript

The generated JavaScript:
1. Creates signals using createSignal() from reactive.js
2. Creates DOM elements directly (no Virtual DOM)
3. Attaches event handlers with addEventListener()
4. Uses createEffect() for reactive bindings (surgical updates)
5. Registers the island in window.__PYNEXT_ISLANDS__

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

React generates code that:
- Creates a Virtual DOM tree
- Diffs it against the previous tree
- Patches the real DOM

This is SLOW because:
- Every update rebuilds the entire component's VDOM
- Diffing is O(n) at best
- Many DOM operations even for small changes

PyNext generates code that:
- Creates real DOM elements once at component mount
- Uses createEffect() to update ONLY the specific DOM nodes that changed
- Achieves O(1) updates regardless of component size

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    IslandIR (with dependencies from analyzer)
         │
         ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                                                                        │
    │  emit_javascript(ir) → str                                             │
    │      │                                                                 │
    │      ├── emit_function_header()   → "function Counter() {"            │
    │      │                                                                 │
    │      ├── emit_signals()           → "const count = createSignal(0);"  │
    │      │                                                                 │
    │      ├── emit_memos()             → "const doubled = createMemo(...);"│
    │      │                                                                 │
    │      ├── emit_dom_tree()          → DOM element creation               │
    │      │                                                                 │
    │      ├── emit_handlers()          → addEventListener() calls           │
    │      │                                                                 │
    │      ├── emit_effects()           → createEffect() for reactive bindings│
    │      │                                                                 │
    │      └── emit_registration()      → window.__PYNEXT_ISLANDS__         │
    │                                                                        │
    └───────────────────────────────────────────────────────────────────────┘
         │
         ▼
    Complete JavaScript string

=============================================================================
WHO USES THIS
=============================================================================

- __init__.py: Called after analyze_dependencies()
- Build system: Writes emitted JS to files
- Dev server: Returns emitted JS for hot reload

=============================================================================
WHEN TO USE (vs Alternatives)
=============================================================================

Always called as part of compile_island(). You typically don't call
emit_javascript() directly unless debugging or customizing output.

=============================================================================
COMPILATION (Input → Output)
=============================================================================

INPUT (IslandIR):
```
IslandIR(
    name="Counter",
    signals=[SignalDef(name="count", initial_value=0)],
    handlers=[HandlerDef(event="click", body=..., reads=["count"], writes=["count"])],
    dom_tree=DOMNode(tag="button", children=[ReactiveNode(expr=count())])
)
```

OUTPUT (JavaScript):
```javascript
function Counter() {
    const count = createSignal(0);
    
    const _el0 = document.createElement("button");
    _el0.addEventListener("click", () => count.set(count() + 1));
    
    createEffect(() => _el0.textContent = count());
    
    return _el0;
}

window.__PYNEXT_ISLANDS__ = window.__PYNEXT_ISLANDS__ || {};
window.__PYNEXT_ISLANDS__.Counter = Counter;
```
=============================================================================
"""

from __future__ import annotations

import ast
import json
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field

from .parser import IslandIR, DOMNode, DOMNodeType, HandlerDef, SignalDef, MemoDef, EffectDef, FormDef


# =============================================================================
# PYTHON → JAVASCRIPT METHOD/FUNCTION TRANSLATIONS
# =============================================================================

# Python string methods → JavaScript equivalents
PYTHON_STRING_METHODS = {
    "upper": "toUpperCase",
    "lower": "toLowerCase",
    "strip": "trim",
    "lstrip": "trimStart",
    "rstrip": "trimEnd",
    "startswith": "startsWith",
    "endswith": "endsWith",
    "replace": "replace",
    "split": "split",
    "join": "join",
    "find": "indexOf",
    "rfind": "lastIndexOf",
    "index": "indexOf",
    "rindex": "lastIndexOf",
    "count": "split",  # Note: Python count != JS - needs special handling
    "capitalize": None,  # No direct equivalent
    "title": None,  # No direct equivalent
    "isdigit": None,  # No direct equivalent
    "isalpha": None,  # No direct equivalent
    "isalnum": None,  # No direct equivalent
}

# Python list methods → JavaScript equivalents
PYTHON_LIST_METHODS = {
    "append": "push",
    "pop": "pop",
    "insert": "splice",  # Needs special handling
    "remove": None,  # Needs special handling
    "reverse": "reverse",
    "sort": "sort",
    "clear": "length = 0",  # Needs special handling
    "copy": "slice",
    "extend": "push",  # Needs spread: push(...arr)
    "index": "indexOf",
}

# Python built-in functions → JavaScript equivalents
PYTHON_BUILTINS_TO_JS = {
    "len": lambda args: f"{args[0]}.length",
    "str": lambda args: f"String({args[0]})",
    "int": lambda args: f"parseInt({args[0]})",
    "float": lambda args: f"parseFloat({args[0]})",
    "bool": lambda args: f"Boolean({args[0]})",
    "abs": lambda args: f"Math.abs({args[0]})",
    "min": lambda args: f"Math.min({', '.join(args)})",
    "max": lambda args: f"Math.max({', '.join(args)})",
    "round": lambda args: f"Math.round({args[0]})" if len(args) == 1 else f"parseFloat({args[0]}.toFixed({args[1]}))",
    "pow": lambda args: f"Math.pow({', '.join(args)})",
    "sum": lambda args: f"{args[0]}.reduce((a, b) => a + b, 0)",
    "range": lambda args: _emit_range(args),
    "list": lambda args: f"[...{args[0]}]" if args else "[]",
    "dict": lambda args: f"Object.fromEntries({args[0]})" if args else "{}",
    "sorted": lambda args: f"[...{args[0]}].sort()" if len(args) == 1 else f"[...{args[0]}].sort({args[1]})",
    "reversed": lambda args: f"[...{args[0]}].reverse()",
    "enumerate": lambda args: f"{args[0]}.map((item, index) => [index, item])",
    "zip": lambda args: _emit_zip(args),
    "map": lambda args: f"{args[1]}.map({args[0]})",
    "filter": lambda args: f"{args[1]}.filter({args[0]})",
    "any": lambda args: f"{args[0]}.some(x => x)",
    "all": lambda args: f"{args[0]}.every(x => x)",
    "print": lambda args: f"console.log({', '.join(args)})",
    "type": lambda args: f"typeof {args[0]}",
    "isinstance": lambda args: _emit_isinstance(args),
}


def _emit_range(args: List[str]) -> str:
    """Emit JavaScript equivalent of Python range()."""
    if len(args) == 1:
        return f"Array.from({{length: {args[0]}}}, (_, i) => i)"
    elif len(args) == 2:
        return f"Array.from({{length: {args[1]} - {args[0]}}}, (_, i) => i + {args[0]})"
    else:
        return f"Array.from({{length: Math.ceil(({args[1]} - {args[0]}) / {args[2]})}}, (_, i) => {args[0]} + i * {args[2]})"


def _emit_zip(args: List[str]) -> str:
    """Emit JavaScript equivalent of Python zip()."""
    return f"{args[0]}.map((_, i) => [{', '.join(f'{a}[i]' for a in args)}])"


def _emit_isinstance(args: List[str]) -> str:
    """Emit JavaScript equivalent of Python isinstance()."""
    # Simplified - just checks type
    type_map = {
        "str": "string",
        "int": "number",
        "float": "number",
        "bool": "boolean",
        "list": "object",
        "dict": "object",
    }
    return f"typeof {args[0]} === '{type_map.get(args[1], 'object')}'"


# =============================================================================
# MAIN EMIT FUNCTION
# =============================================================================

def emit_javascript(ir: IslandIR) -> str:
    """
    Emit JavaScript code from the analyzed IR.
    
    This is the main entry point for code generation. It produces a complete
    JavaScript function that creates and manages a reactive component.
    
    Args:
        ir: IslandIR with dependency information from analyzer
    
    Returns:
        Complete JavaScript code string
    
    Example:
        >>> ir = parse_island(source, "counter.py")
        >>> ir = analyze_dependencies(ir)
        >>> js = emit_javascript(ir)
        >>> print(js)
    """
    emitter = JSEmitter(ir)
    return emitter.emit()


@dataclass
class JSEmitter:
    """
    JavaScript code emitter for PyNext islands.
    
    This class holds state during emission and provides methods for
    emitting different parts of the component.
    """
    ir: IslandIR
    lines: List[str] = field(default_factory=list)
    indent: int = 0
    element_vars: Dict[str, str] = field(default_factory=dict)  # element_id -> var name
    _counter: int = 0  # Global counter for unique variable names
    
    def _next_id(self) -> int:
        """Get next unique ID for variable naming."""
        self._counter += 1
        return self._counter
    
    def emit(self) -> str:
        """Generate complete JavaScript for the island."""
        self.lines = []
        
        # Function header
        self._emit_function_header()
        
        # Signals
        self._emit_signals()
        
        # Memos
        self._emit_memos()
        
        # Forms
        self._emit_forms()
        
        # DOM tree
        if self.ir.dom_tree:
            root_var = self._emit_dom_node(self.ir.dom_tree)
        else:
            root_var = "null"
        
        # Effects for reactive bindings
        self._emit_reactive_bindings()
        
        # Effects from @effect decorators
        self._emit_effects()
        
        # Return statement
        self._line(f"return {root_var};")
        
        # Close function
        self.indent -= 1
        self._line("}")
        
        # Island registration
        self._emit_registration()
        
        return "\n".join(self.lines)
    
    def _line(self, code: str) -> None:
        """Add a line of code with current indentation."""
        indent_str = "    " * self.indent
        self.lines.append(f"{indent_str}{code}")
    
    def _blank(self) -> None:
        """Add a blank line."""
        self.lines.append("")
    
    # =========================================================================
    # FUNCTION HEADER
    # =========================================================================
    
    def _emit_function_header(self) -> None:
        """Emit function declaration."""
        params = ", ".join(p[0] for p in self.ir.params)
        self._line(f"function {self.ir.name}({params}) {{")
        self.indent += 1
    
    # =========================================================================
    # SIGNALS
    # =========================================================================
    
    def _emit_signals(self) -> None:
        """Emit signal declarations."""
        if not self.ir.signals:
            return
        
        for sig in self.ir.signals:
            initial = self._emit_value(sig.initial, sig.initial_value)
            self._line(f"const {sig.name} = createSignal({initial});")
        
        self._blank()
    
    # =========================================================================
    # MEMOS
    # =========================================================================
    
    def _emit_memos(self) -> None:
        """Emit memo declarations."""
        if not self.ir.memos:
            return
        
        for memo in self.ir.memos:
            fn_code = self._emit_lambda(memo.fn) if memo.fn else "() => null"
            self._line(f"const {memo.name} = createMemo({fn_code});")
        
        self._blank()
    
    # =========================================================================
    # FORMS
    # =========================================================================
    
    def _emit_forms(self) -> None:
        """Emit form declarations."""
        if not hasattr(self.ir, 'forms') or not self.ir.forms:
            return
        
        for form in self.ir.forms:
            initial_js = json.dumps(form.initial)
            validators_js = self._emit_form_validators(form.validators)
            self._line(f"const {form.name} = createForm({initial_js}, {validators_js});")
        
        self._blank()
    
    def _emit_form_validators(self, validators_ast) -> str:
        """
        Emit validators dict for a form.
        
        Converts Python AST validators to JavaScript.
        """
        if validators_ast is None:
            return "{}"
        
        if not isinstance(validators_ast, ast.Dict):
            return "{}"
        
        parts = []
        for key, value in zip(validators_ast.keys, validators_ast.values):
            if not isinstance(key, ast.Constant):
                continue
            
            field_name = str(key.value)
            
            # Convert validator list/single validator to JS
            if isinstance(value, ast.List):
                validator_strs = []
                for v in value.elts:
                    validator_strs.append(self._emit_validator(v))
                validators_js = "[" + ", ".join(validator_strs) + "]"
            else:
                validators_js = self._emit_validator(value)
            
            parts.append(f"{json.dumps(field_name)}: {validators_js}")
        
        return "{" + ", ".join(parts) + "}"
    
    def _emit_validator(self, node: ast.AST) -> str:
        """Emit a single validator call."""
        if isinstance(node, ast.Call):
            # e.g., required("message") or min_length(5)
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            # Map Python validator names to JS
            validator_map = {
                "required": "required",
                "min_length": "minLength",
                "max_length": "maxLength",
                "email": "email",
                "pattern": "pattern",
                "min_value": "minValue",
                "max_value": "maxValue",
                "one_of": "oneOf",
                "url": "url",
                "integer": "integer",
                "number": "number",
            }
            
            js_name = validator_map.get(func_name, func_name)
            
            # Emit arguments
            args = []
            for arg in node.args:
                args.append(self._emit_value(arg, None))
            for kw in node.keywords:
                if kw.arg:
                    args.append(self._emit_value(kw.value, None))
            
            args_js = ", ".join(args)
            return f"{js_name}({args_js})"
        
        return "() => null"
    
    # =========================================================================
    # DOM TREE
    # =========================================================================
    
    def _emit_dom_node(self, node: DOMNode, parent_var: Optional[str] = None) -> str:
        """
        Emit JavaScript for a DOM node.
        
        Returns the variable name holding the DOM element.
        """
        if node.type == DOMNodeType.ELEMENT:
            return self._emit_element(node, parent_var)
        elif node.type == DOMNodeType.TEXT:
            return self._emit_text_node(node, parent_var)
        elif node.type == DOMNodeType.REACTIVE:
            return self._emit_reactive_node(node, parent_var)
        elif node.type == DOMNodeType.CONTROL:
            return self._emit_control_flow(node, parent_var)
        elif node.type == DOMNodeType.FRAGMENT:
            return self._emit_fragment(node, parent_var)
        else:
            return "null"
    
    def _emit_element(self, node: DOMNode, parent_var: Optional[str]) -> str:
        """Emit an HTML element."""
        var_id = self._next_id()
        var_name = f"_el{var_id}"
        if node.element_id:
            self.element_vars[node.element_id] = var_name
        
        # Create element
        self._line(f"const {var_name} = document.createElement(\"{node.tag}\");")
        
        # Static attributes
        for attr_name, attr_value in node.attributes.items():
            if attr_name == "class":
                self._line(f"{var_name}.className = {json.dumps(attr_value)};")
            elif attr_name == "style" and isinstance(attr_value, str):
                self._line(f"{var_name}.style.cssText = {json.dumps(attr_value)};")
            else:
                self._line(f"{var_name}.setAttribute({json.dumps(attr_name)}, {json.dumps(attr_value)});")
        
        # Event handlers
        for handler in node.handlers:
            handler_code = self._emit_handler(handler)
            self._line(f"{var_name}.addEventListener(\"{handler.event}\", {handler_code});")
        
        # Children - pass parent so they can append themselves
        for child in node.children:
            child_var = self._emit_dom_node(child, var_name)
        
        # Append to parent if provided
        if parent_var:
            self._line(f"{parent_var}.appendChild({var_name});")
        
        return var_name
    
    def _emit_text_node(self, node: DOMNode, parent_var: Optional[str]) -> str:
        """Emit a static text node."""
        var_id = self._next_id()
        var_name = f"_text{var_id}"
        self._line(f"const {var_name} = document.createTextNode({json.dumps(node.text)});")
        
        if parent_var:
            self._line(f"{parent_var}.appendChild({var_name});")
        
        return var_name
    
    def _emit_reactive_node(self, node: DOMNode, parent_var: Optional[str]) -> str:
        """Emit a reactive text node with createEffect for updates."""
        var_id = self._next_id()
        var_name = f"_text{var_id}"
        
        # Create initial text node
        self._line(f"const {var_name} = document.createTextNode(\"\");")
        
        if parent_var:
            self._line(f"{parent_var}.appendChild({var_name});")
        
        # Create effect for reactive updates
        if node.expr:
            expr_code = self._emit_expr(node.expr)
            self._line(f"createEffect(() => {{ {var_name}.textContent = {expr_code}; }});")
        
        return var_name
    
    def _emit_control_flow(self, node: DOMNode, parent_var: Optional[str]) -> str:
        """Emit control flow (Show, For, etc.)."""
        control_type = node.control_type
        
        if control_type == "Show":
            return self._emit_show(node, parent_var)
        elif control_type == "For":
            return self._emit_for(node, parent_var)
        elif control_type == "Switch":
            return self._emit_switch(node, parent_var)
        else:
            # Generic control flow
            return self._emit_generic_control(node, parent_var)
    
    def _emit_show(self, node: DOMNode, parent_var: Optional[str]) -> str:
        """
        Emit Show control flow with proper cleanup.
        
        Uses a factory pattern so that nested effects can be disposed when
        the content is hidden. The runtime Show() function handles this.
        """
        show_id = self._next_id()
        
        when_expr = node.control_props.get("when")
        # If when is a lambda, emit it directly; otherwise wrap
        if isinstance(when_expr, ast.Lambda):
            when_code = self._emit_lambda(when_expr)
        elif when_expr:
            when_code = f"() => {self._emit_expr(when_expr)}"
        else:
            when_code = "() => true"
        
        # Generate children factory
        if node.children:
            children_code = self._emit_children_factory(node.children)
        else:
            children_code = "() => null"
        
        # Generate fallback if present
        fallback_expr = node.control_props.get("fallback")
        if fallback_expr:
            if isinstance(fallback_expr, ast.AST):
                fallback_code = self._emit_lambda(fallback_expr)
            else:
                fallback_code = "null"
        else:
            fallback_code = "null"
        
        # Use runtime Show function which handles disposal properly
        self._line(f"Show({{")
        self.indent += 1
        self._line(f"when: {when_code},")
        self._line(f"children: {children_code},")
        if fallback_code != "null":
            self._line(f"fallback: {fallback_code},")
        if parent_var:
            self._line(f"parent: {parent_var}")
        self.indent -= 1
        self._line("});")
        
        return f"_show{show_id}"
    
    def _emit_for(self, node: DOMNode, parent_var: Optional[str]) -> str:
        """
        Emit For control flow.
        
        For loops need special handling because the children template
        is typically a lambda that receives (item, index). We need to
        detect this pattern and compile the lambda body properly.
        """
        for_id = self._next_id()
        
        each_expr = node.control_props.get("each")
        each_code = self._emit_lambda(each_expr) if each_expr else "() => []"
        
        key_expr = node.control_props.get("key")
        key_code = self._emit_lambda(key_expr) if key_expr else "(item, i) => i"
        
        # Handle children - could be a lambda or direct nodes
        children_code = "(item, index) => null"
        if node.children:
            # Check if the first child is a lambda (common pattern: For()[lambda item: ...])
            if len(node.children) == 1:
                child = node.children[0]
                if child.type == DOMNodeType.REACTIVE and child.expr:
                    if isinstance(child.expr, ast.Lambda):
                        # This is the pattern: For()[lambda item: div()[item]]
                        children_code = self._emit_for_children_lambda(child.expr)
                    else:
                        # Direct expression using item
                        children_code = self._emit_children_factory(node.children, item_param=True)
                else:
                    children_code = self._emit_children_factory(node.children, item_param=True)
            else:
                children_code = self._emit_children_factory(node.children, item_param=True)
        
        # Fallback
        fallback_expr = node.control_props.get("fallback")
        fallback_code = self._emit_lambda(fallback_expr) if fallback_expr else "null"
        
        self._line(f"For({{")
        self.indent += 1
        self._line(f"each: {each_code},")
        self._line(f"key: {key_code},")
        self._line(f"children: {children_code},")
        if fallback_code != "null":
            self._line(f"fallback: {fallback_code},")
        if parent_var:
            self._line(f"parent: {parent_var}")
        self.indent -= 1
        self._line("});")
        
        return f"_for{for_id}"
    
    def _emit_for_children_lambda(self, lambda_node: ast.Lambda) -> str:
        """
        Emit a For children lambda: lambda item: div()[item["name"]]
        
        This compiles the lambda body as DOM creation code.
        """
        # Get parameter names
        params = []
        for arg in lambda_node.args.args:
            params.append(arg.arg)
        
        params_str = ", ".join(params) if params else "item"
        if len(params) < 2:
            params_str = f"({params_str}, _index)"
        else:
            params_str = f"({params_str})"
        
        # The body should be a DOM expression - compile it
        body = lambda_node.body
        
        # Save state
        saved_lines = self.lines
        saved_indent = self.indent
        
        self.lines = []
        self.indent = 0
        
        # Parse the body as a DOM node
        # We need to create a temporary DOMNode from the AST
        body_var = self._emit_for_body(body)
        
        body_code = "\n".join(self.lines)
        
        # Restore state
        self.lines = saved_lines
        self.indent = saved_indent
        
        if body_code.strip():
            return f"{params_str} => {{\n{self._indent_code(body_code, 2)}\n        return {body_var};\n    }}"
        else:
            return f"{params_str} => {self._emit_expr(body)}"
    
    def _emit_for_body(self, node: ast.AST) -> str:
        """Emit the body of a For children lambda."""
        # Handle subscript (element with children)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Call):
            # This is like div()[item["name"]]
            return self._emit_for_body_element(node)
        
        # Handle plain call (element without children)
        if isinstance(node, ast.Call):
            return self._emit_for_body_element(node)
        
        # For other expressions, just emit as reactive text
        var_id = self._next_id()
        var_name = f"_text{var_id}"
        expr_code = self._emit_expr(node)
        self._line(f"const {var_name} = document.createTextNode({expr_code});")
        return var_name
    
    def _emit_for_body_element(self, node: ast.AST) -> str:
        """Emit an element from For body."""
        var_id = self._next_id()
        
        # Get tag and children
        if isinstance(node, ast.Subscript):
            call_node = node.value
            children_ast = node.slice
        else:
            call_node = node
            children_ast = None
        
        # Get tag name
        tag = "div"
        if isinstance(call_node, ast.Call) and isinstance(call_node.func, ast.Name):
            tag = call_node.func.id
        
        var_name = f"_el{var_id}"
        self._line(f"const {var_name} = document.createElement(\"{tag}\");")
        
        # Attributes
        if isinstance(call_node, ast.Call):
            for kw in call_node.keywords:
                if kw.arg is None:
                    continue
                attr_name = kw.arg
                if attr_name == "class_":
                    attr_name = "class"
                    if isinstance(kw.value, ast.Constant):
                        self._line(f"{var_name}.className = {json.dumps(kw.value.value)};")
                    else:
                        expr = self._emit_expr(kw.value)
                        self._line(f"{var_name}.className = {expr};")
                elif attr_name.startswith("on"):
                    event = attr_name[2:].lower()
                    handler = self._emit_lambda(kw.value)
                    self._line(f"{var_name}.addEventListener(\"{event}\", {handler});")
                elif isinstance(kw.value, ast.Constant):
                    self._line(f"{var_name}.setAttribute(\"{attr_name}\", {json.dumps(kw.value.value)});")
                else:
                    expr = self._emit_expr(kw.value)
                    self._line(f"{var_name}.setAttribute(\"{attr_name}\", {expr});")
        
        # Children
        if children_ast:
            self._emit_for_body_children(children_ast, var_name)
        
        return var_name
    
    def _emit_for_body_children(self, node: ast.AST, parent_var: str) -> None:
        """Emit children for a For body element."""
        if isinstance(node, ast.Tuple):
            for child in node.elts:
                self._emit_for_body_child(child, parent_var)
        else:
            self._emit_for_body_child(node, parent_var)
    
    def _emit_for_body_child(self, node: ast.AST, parent_var: str) -> None:
        """Emit a single child in For body."""
        var_id = self._next_id()
        
        if isinstance(node, ast.Constant):
            # Static text
            var_name = f"_text{var_id}"
            self._line(f"const {var_name} = document.createTextNode({json.dumps(node.value)});")
            self._line(f"{parent_var}.appendChild({var_name});")
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Call):
            # Nested element
            child_var = self._emit_for_body_element(node)
            self._line(f"{parent_var}.appendChild({child_var});")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            # Nested element without children
            child_var = self._emit_for_body_element(node)
            self._line(f"{parent_var}.appendChild({child_var});")
        else:
            # Reactive expression (like item["name"])
            var_name = f"_text{var_id}"
            expr_code = self._emit_expr(node)
            self._line(f"const {var_name} = document.createTextNode({expr_code});")
            self._line(f"{parent_var}.appendChild({var_name});")
    
    def _emit_switch(self, node: DOMNode, parent_var: Optional[str]) -> str:
        """Emit Switch control flow."""
        var_name = f"_switch{len(self.element_vars)}"
        
        self._line(f"Switch({{")
        self.indent += 1
        
        if node.children:
            self._line("children: [")
            self.indent += 1
            for child in node.children:
                if child.type == DOMNodeType.CONTROL and child.control_type == "Match":
                    self._emit_match(child)
            self.indent -= 1
            self._line("],")
        
        if parent_var:
            self._line(f"parent: {parent_var}")
        
        self.indent -= 1
        self._line("});")
        
        return var_name
    
    def _emit_match(self, node: DOMNode) -> None:
        """Emit a Match case inside Switch."""
        when_expr = node.control_props.get("when")
        when_code = self._emit_lambda(when_expr) if when_expr else "() => true"
        
        self._line(f"Match({{")
        self.indent += 1
        self._line(f"when: {when_code},")
        
        if node.children:
            children_code = self._emit_children_factory(node.children)
            self._line(f"children: {children_code}")
        
        self.indent -= 1
        self._line("}),")
    
    def _emit_generic_control(self, node: DOMNode, parent_var: Optional[str]) -> str:
        """Emit generic control flow component."""
        var_name = f"_ctrl{len(self.element_vars)}"
        
        self._line(f"{node.control_type}({{")
        self.indent += 1
        
        for prop_name, prop_value in node.control_props.items():
            if prop_name.endswith("_deps"):
                continue  # Skip analyzer metadata
            
            if isinstance(prop_value, ast.AST):
                code = self._emit_lambda(prop_value)
            elif isinstance(prop_value, (list, dict)):
                continue  # Skip complex values for now
            else:
                code = json.dumps(prop_value)
            
            self._line(f"{prop_name}: {code},")
        
        if parent_var:
            self._line(f"parent: {parent_var}")
        
        self.indent -= 1
        self._line("});")
        
        return var_name
    
    def _emit_fragment(self, node: DOMNode, parent_var: Optional[str]) -> str:
        """Emit a document fragment."""
        var_name = f"_frag{len(self.element_vars)}"
        self._line(f"const {var_name} = document.createDocumentFragment();")
        
        for child in node.children:
            child_var = self._emit_dom_node(child, var_name)
        
        if parent_var:
            self._line(f"{parent_var}.appendChild({var_name});")
        
        return var_name
    
    def _emit_children_factory(self, children: List[DOMNode], item_param: bool = False) -> str:
        """
        Emit a factory function for children.
        
        For control flow like For/Switch, we need to generate a function that
        creates DOM nodes when called. This is tricky because we need to:
        1. Generate the DOM creation code
        2. Wrap it in a function
        3. Return the root element(s)
        """
        # Save current state
        saved_lines = self.lines
        saved_indent = self.indent
        
        # Generate children into a temporary buffer
        self.lines = []
        self.indent = 0
        
        child_vars = []
        for child in children:
            child_var = self._emit_dom_node(child, None)
            child_vars.append(child_var)
        
        child_code = "\n".join(self.lines)
        
        # Restore state
        self.lines = saved_lines
        self.indent = saved_indent
        
        # Build the factory function
        if item_param:
            params = "(item, index)"
        else:
            params = "()"
        
        # Determine what to return
        if len(child_vars) == 0:
            return f"{params} => null"
        elif len(child_vars) == 1:
            # Single child - return it directly
            # Inline the code if it's short
            if child_code.count('\n') <= 3:
                return f"{params} => {{ {child_code.strip()}; return {child_vars[0]}; }}"
            else:
                return f"{params} => {{\n{self._indent_code(child_code, 2)}\n        return {child_vars[0]};\n    }}"
        else:
            # Multiple children - return array or fragment
            vars_list = ", ".join(child_vars)
            return f"{params} => {{\n{self._indent_code(child_code, 2)}\n        return [{vars_list}];\n    }}"
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by given number of spaces."""
        indent = "    " * spaces
        return "\n".join(indent + line for line in code.split("\n") if line.strip())
    
    # =========================================================================
    # REACTIVE BINDINGS
    # =========================================================================
    
    def _emit_reactive_bindings(self) -> None:
        """Emit createEffect() calls for reactive attributes."""
        if not self.ir.dom_tree:
            return
        
        self._emit_node_reactive_attrs(self.ir.dom_tree)
    
    def _emit_node_reactive_attrs(self, node: DOMNode) -> None:
        """Emit effects for reactive attributes on a node."""
        var_name = self.element_vars.get(node.element_id, node.element_id)
        
        for attr_name, attr_expr in node.reactive_attrs.items():
            expr_code = self._emit_expr(attr_expr)
            
            if attr_name == "class":
                self._line(f"createEffect(() => {{ {var_name}.className = {expr_code}; }});")
            elif attr_name == "style":
                self._line(f"createEffect(() => {{ {var_name}.style.cssText = {expr_code}; }});")
            elif attr_name == "value":
                self._line(f"createEffect(() => {{ {var_name}.value = {expr_code}; }});")
            else:
                self._line(f"createEffect(() => {{ {var_name}.setAttribute(\"{attr_name}\", {expr_code}); }});")
        
        for child in node.children:
            self._emit_node_reactive_attrs(child)
    
    # =========================================================================
    # EFFECTS
    # =========================================================================
    
    def _emit_effects(self) -> None:
        """Emit @effect decorated functions."""
        if not self.ir.effects:
            return
        
        self._blank()
        
        for effect in self.ir.effects:
            body_code = self._emit_function_body(effect.body)
            self._line(f"createEffect(() => {{ {body_code} }});")
    
    # =========================================================================
    # HANDLERS
    # =========================================================================
    
    def _emit_handler(self, handler: HandlerDef) -> str:
        """Emit an event handler function."""
        return self._emit_lambda(handler.body)
    
    # =========================================================================
    # REGISTRATION
    # =========================================================================
    
    def _emit_registration(self) -> None:
        """Emit island registration for hydration."""
        self._blank()
        self._line("// Register island for hydration")
        self._line("window.__PYNEXT_ISLANDS__ = window.__PYNEXT_ISLANDS__ || {};")
        self._line(f"window.__PYNEXT_ISLANDS__.{self.ir.name} = {self.ir.name};")
    
    # =========================================================================
    # EXPRESSION EMITTERS
    # =========================================================================
    
    def _emit_value(self, ast_node: ast.AST, evaluated: Any = None) -> str:
        """Emit a value (for signal initialization, etc.)."""
        if evaluated is not None:
            return json.dumps(evaluated)
        return self._emit_expr(ast_node)
    
    def _emit_expr(self, node: ast.AST) -> str:
        """Emit a JavaScript expression from Python AST."""
        if isinstance(node, ast.Constant):
            return json.dumps(node.value)
        
        if isinstance(node, ast.Name):
            return node.id
        
        if isinstance(node, ast.Call):
            return self._emit_call(node)
        
        if isinstance(node, ast.Lambda):
            return self._emit_lambda(node)
        
        if isinstance(node, ast.BinOp):
            return self._emit_binop(node)
        
        if isinstance(node, ast.Compare):
            return self._emit_compare(node)
        
        if isinstance(node, ast.UnaryOp):
            return self._emit_unaryop(node)
        
        if isinstance(node, ast.BoolOp):
            return self._emit_boolop(node)
        
        if isinstance(node, ast.IfExp):
            return self._emit_ifexp(node)
        
        if isinstance(node, ast.Attribute):
            return self._emit_attribute(node)
        
        if isinstance(node, ast.Subscript):
            return self._emit_subscript(node)
        
        if isinstance(node, ast.List):
            elements = ", ".join(self._emit_expr(e) for e in node.elts)
            return f"[{elements}]"
        
        if isinstance(node, ast.Dict):
            pairs = []
            for k, v in zip(node.keys, node.values):
                if k is None:
                    continue
                key = self._emit_expr(k)
                val = self._emit_expr(v)
                pairs.append(f"{key}: {val}")
            return f"{{{', '.join(pairs)}}}"
        
        if isinstance(node, ast.Tuple):
            elements = ", ".join(self._emit_expr(e) for e in node.elts)
            return f"[{elements}]"
        
        if isinstance(node, ast.JoinedStr):
            return self._emit_fstring(node)
        
        # Fallback
        return "null"
    
    def _emit_call(self, node: ast.Call) -> str:
        """
        Emit a function call, translating Python methods/functions to JavaScript.
        
        Handles:
        - Method calls: obj.method(args) → obj.jsMethod(args)
        - Built-in functions: len(x) → x.length, str(x) → String(x)
        - Regular function calls: func(args) → func(args)
        """
        # Method call: obj.method(args)
        if isinstance(node.func, ast.Attribute):
            obj = self._emit_expr(node.func.value)
            method = node.func.attr
            args_list = [self._emit_expr(a) for a in node.args]
            args = ", ".join(args_list)
            
            # Translate Python string methods to JavaScript
            if method in PYTHON_STRING_METHODS:
                js_method = PYTHON_STRING_METHODS[method]
                if js_method is None:
                    # No direct equivalent - keep as is (may fail at runtime)
                    return f"{obj}.{method}({args})"
                return f"{obj}.{js_method}({args})"
            
            # Translate Python list methods to JavaScript
            if method in PYTHON_LIST_METHODS:
                js_method = PYTHON_LIST_METHODS[method]
                if js_method is None:
                    # Special handling needed
                    if method == "remove":
                        # arr.remove(x) → arr.splice(arr.indexOf(x), 1)
                        return f"{obj}.splice({obj}.indexOf({args}), 1)"
                    if method == "clear":
                        return f"{obj}.length = 0"
                    return f"{obj}.{method}({args})"
                
                if method == "insert":
                    # arr.insert(i, x) → arr.splice(i, 0, x)
                    return f"{obj}.splice({args_list[0]}, 0, {args_list[1]})"
                if method == "extend":
                    # arr.extend(other) → arr.push(...other)
                    return f"{obj}.push(...{args_list[0]})"
                
                return f"{obj}.{js_method}({args})"
            
            # Default: keep the method name as-is
            return f"{obj}.{method}({args})"
        
        # Function call: func(args)
        if isinstance(node.func, ast.Name):
            func = node.func.id
            args_list = [self._emit_expr(a) for a in node.args]
            
            # Translate Python built-in functions to JavaScript
            if func in PYTHON_BUILTINS_TO_JS:
                translator = PYTHON_BUILTINS_TO_JS[func]
                return translator(args_list)
            
            # Regular function call
            args = ", ".join(args_list)
            return f"{func}({args})"
        
        return "null"
    
    def _emit_lambda(self, node: ast.AST) -> str:
        """Emit a lambda as an arrow function."""
        if not isinstance(node, ast.Lambda):
            # If it's not a lambda, wrap it
            expr = self._emit_expr(node)
            return f"() => {expr}"
        
        # Get parameters
        params = []
        for arg in node.args.args:
            params.append(arg.arg)
        
        params_str = ", ".join(params)
        body = self._emit_expr(node.body)
        
        # Handle tuple body (multiple statements)
        if isinstance(node.body, ast.Tuple):
            stmts = [self._emit_expr(e) for e in node.body.elts]
            body = "; ".join(stmts)
            return f"({params_str}) => {{ {body}; }}"
        
        return f"({params_str}) => {body}"
    
    def _emit_binop(self, node: ast.BinOp) -> str:
        """Emit a binary operation."""
        left = self._emit_expr(node.left)
        right = self._emit_expr(node.right)
        
        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
            ast.Pow: "**",
            ast.FloorDiv: "Math.floor({left} / {right})",
            ast.BitAnd: "&",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.LShift: "<<",
            ast.RShift: ">>",
        }
        
        op = op_map.get(type(node.op), "+")
        
        if "{left}" in op:
            return op.format(left=left, right=right)
        
        return f"({left} {op} {right})"
    
    def _emit_compare(self, node: ast.Compare) -> str:
        """
        Emit a comparison.
        
        Special handling for:
        - `x is None` → `x === null`
        - `x is not None` → `x !== null`
        - `x in list` → `list.includes(x)`
        - `x in dict` → `x in dict` (JS object property check)
        """
        left = self._emit_expr(node.left)
        
        for op, comparator in zip(node.ops, node.comparators):
            comp = self._emit_expr(comparator)
            
            # Handle 'is None' and 'is not None' specially
            if isinstance(op, ast.Is):
                if isinstance(comparator, ast.Constant) and comparator.value is None:
                    left = f"({left} === null)"
                else:
                    # For non-None identity, warn this might not work as expected
                    # but use === as best approximation
                    left = f"({left} === {comp})"
            
            elif isinstance(op, ast.IsNot):
                if isinstance(comparator, ast.Constant) and comparator.value is None:
                    left = f"({left} !== null)"
                else:
                    left = f"({left} !== {comp})"
            
            # Handle 'in' operator - works for both arrays and objects
            elif isinstance(op, ast.In):
                # Use Array.isArray to determine which check to use
                left = f"(Array.isArray({comp}) ? {comp}.includes({left}) : ({left} in {comp}))"
            
            elif isinstance(op, ast.NotIn):
                left = f"(Array.isArray({comp}) ? !{comp}.includes({left}) : !({left} in {comp}))"
            
            # Standard comparisons
            elif isinstance(op, ast.Eq):
                left = f"({left} === {comp})"
            elif isinstance(op, ast.NotEq):
                left = f"({left} !== {comp})"
            elif isinstance(op, ast.Lt):
                left = f"({left} < {comp})"
            elif isinstance(op, ast.LtE):
                left = f"({left} <= {comp})"
            elif isinstance(op, ast.Gt):
                left = f"({left} > {comp})"
            elif isinstance(op, ast.GtE):
                left = f"({left} >= {comp})"
            else:
                # Default fallback
                left = f"({left} === {comp})"
        
        return left
    
    def _emit_unaryop(self, node: ast.UnaryOp) -> str:
        """Emit a unary operation."""
        operand = self._emit_expr(node.operand)
        
        op_map = {
            ast.Not: "!",
            ast.USub: "-",
            ast.UAdd: "+",
            ast.Invert: "~",
        }
        
        op = op_map.get(type(node.op), "")
        return f"{op}{operand}"
    
    def _emit_boolop(self, node: ast.BoolOp) -> str:
        """Emit a boolean operation."""
        op = "&&" if isinstance(node.op, ast.And) else "||"
        values = [self._emit_expr(v) for v in node.values]
        return f"({f' {op} '.join(values)})"
    
    def _emit_ifexp(self, node: ast.IfExp) -> str:
        """Emit a ternary expression."""
        test = self._emit_expr(node.test)
        body = self._emit_expr(node.body)
        orelse = self._emit_expr(node.orelse)
        return f"({test} ? {body} : {orelse})"
    
    def _emit_attribute(self, node: ast.Attribute) -> str:
        """Emit an attribute access."""
        value = self._emit_expr(node.value)
        return f"{value}.{node.attr}"
    
    def _emit_subscript(self, node: ast.Subscript) -> str:
        """Emit a subscript access."""
        value = self._emit_expr(node.value)
        
        if isinstance(node.slice, ast.Constant):
            key = json.dumps(node.slice.value)
        else:
            key = self._emit_expr(node.slice)
        
        return f"{value}[{key}]"
    
    def _emit_fstring(self, node: ast.JoinedStr) -> str:
        """Emit an f-string as template literal."""
        parts = []
        
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                expr = self._emit_expr(value.value)
                parts.append(f"${{{expr}}}")
        
        return f"`{''.join(parts)}`"
    
    def _emit_function_body(self, node: ast.AST) -> str:
        """Emit a function body (statements)."""
        if isinstance(node, ast.FunctionDef):
            # Extract statements from function body
            stmts = []
            for stmt in node.body:
                stmts.append(self._emit_statement(stmt))
            return " ".join(stmts)
        
        return self._emit_expr(node)
    
    def _emit_statement(self, node: ast.AST) -> str:
        """Emit a single statement."""
        if isinstance(node, ast.Expr):
            return f"{self._emit_expr(node.value)};"
        
        if isinstance(node, ast.Assign):
            targets = [self._emit_expr(t) for t in node.targets]
            value = self._emit_expr(node.value)
            return f"{targets[0]} = {value};"
        
        if isinstance(node, ast.Return):
            if node.value:
                return f"return {self._emit_expr(node.value)};"
            return "return;"
        
        if isinstance(node, ast.If):
            test = self._emit_expr(node.test)
            body = " ".join(self._emit_statement(s) for s in node.body)
            result = f"if ({test}) {{ {body} }}"
            if node.orelse:
                orelse = " ".join(self._emit_statement(s) for s in node.orelse)
                result += f" else {{ {orelse} }}"
            return result
        
        return self._emit_expr(node) + ";"

