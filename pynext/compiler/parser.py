"""
PyNext Compiler - Parser (Python AST → IR)

=============================================================================
WHAT THIS FILE DOES
=============================================================================

The parser is the FIRST stage of the compiler pipeline. It takes Python
source code and extracts reactive constructs into an Intermediate 
Representation (IR) that the rest of the compiler can work with.

    Python Source → [PARSER] → IR (IslandIR)

The IR captures:
- Signal definitions: count = signal(0)
- Effect definitions: @effect def log(): ...
- Memo definitions: doubled = memo(lambda: count() * 2)
- Event handlers: onclick=lambda: count.set(count() + 1)
- DOM structure: return div()[button()[count()]]
- Source locations for error messages and source maps

=============================================================================
WHY THIS EXISTS (Problem It Solves)
=============================================================================

We can't directly convert Python AST to JavaScript because:

1. Python AST is complex and nested - hard to traverse multiple times
2. We need to identify WHICH Python constructs are compilable
3. We need source locations for error messages and debugging
4. The emitter shouldn't know about Python AST details

The IR is a CLEAN, SIMPLE representation optimized for compilation.

=============================================================================
HOW IT WORKS (Architecture)
=============================================================================

    Python Source
         │
         ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  ast.parse(source)                                          │
    │      │                                                      │
    │      ▼                                                      │
    │  find_island_function()  ─── Find @island decorated func    │
    │      │                                                      │
    │      ▼                                                      │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │ extract_signals()     ─── count = signal(0)         │   │
    │  │ extract_effects()     ─── @effect def ...           │   │
    │  │ extract_memos()       ─── doubled = memo(...)       │   │
    │  │ extract_handlers()    ─── onclick=lambda: ...       │   │
    │  │ extract_dom_tree()    ─── return div()[...]         │   │
    │  └─────────────────────────────────────────────────────┘   │
    │      │                                                      │
    │      ▼                                                      │
    │  IslandIR(signals, effects, memos, handlers, dom_tree)      │
    └─────────────────────────────────────────────────────────────┘

=============================================================================
WHO USES THIS
=============================================================================

- __init__.py: parse_island() is called first in compile_island()
- analyzer.py: Receives IslandIR and adds dependency information
- Tests: Verify parsing produces correct IR

=============================================================================
WHEN TO USE (vs Alternatives)
=============================================================================

USE parse_island():
- Single @island component from a string

USE parse_file():
- Multiple @island components in a .py file

=============================================================================
COMPILATION (Input → Output)
=============================================================================

INPUT:
```python
@island
def Counter():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
    
    return button(onclick=lambda: count.set(count() + 1))[
        "Count: ", count(), " (doubled: ", doubled(), ")"
    ]
```

OUTPUT (IslandIR):
```
IslandIR(
    name="Counter",
    signals=[
        SignalDef(name="count", initial=Constant(0), line=3)
    ],
    memos=[
        MemoDef(name="doubled", fn=Lambda(...), line=4)
    ],
    handlers=[
        HandlerDef(event="click", element="_el0", body=Lambda(...), line=6)
    ],
    dom_tree=DOMNode(
        tag="button",
        children=[
            TextNode("Count: "),
            ReactiveNode(expr=Call("count")),
            ...
        ]
    )
)
```
=============================================================================
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Union
from enum import Enum

from .errors import (
    CompileError,
    CompileWarning,
    no_island_found,
    invalid_syntax,
    class_not_compilable,
    await_not_compilable,
    import_not_compilable,
    yield_not_compilable,
    global_not_compilable,
)


# =============================================================================
# VALID HTML ELEMENT TAGS (used to distinguish elements from function calls)
# =============================================================================

# Standard HTML5 elements that can be used in PyNext components
HTML_ELEMENTS = frozenset({
    # Document structure
    "html", "head", "body", "title", "meta", "link", "script", "style",
    # Layout
    "div", "span", "section", "article", "header", "footer", "nav", "aside", "main",
    # Headings
    "h1", "h2", "h3", "h4", "h5", "h6",
    # Text
    "p", "a", "strong", "em", "b", "i", "u", "s", "code", "pre", "blockquote",
    "br", "hr", "small", "sub", "sup", "abbr", "cite", "q", "dfn", "kbd", "samp", "var",
    # Lists
    "ul", "ol", "li", "dl", "dt", "dd",
    # Forms
    "form", "input", "input_", "textarea", "button", "select", "option", "optgroup",
    "label", "fieldset", "legend", "datalist", "output",
    # Tables
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "colgroup", "col",
    # Media
    "img", "video", "audio", "source", "track", "canvas", "svg", "picture",
    "iframe", "embed", "object", "param",
    # Semantic
    "figure", "figcaption", "details", "summary", "time", "mark", "progress", "meter",
    "address", "wbr", "bdi", "bdo", "ruby", "rt", "rp",
    # Interactive
    "dialog", "menu", "menuitem",
    # Deprecated but still used
    "center", "font", "marquee",
    # SVG elements (common ones)
    "path", "circle", "rect", "line", "polygon", "polyline", "ellipse", "g", "text",
    "defs", "use", "symbol", "clipPath", "mask", "linearGradient", "radialGradient",
    "stop", "pattern", "filter", "feGaussianBlur", "feOffset", "feBlend",
})

# Python built-in functions that are NOT HTML elements
PYTHON_BUILTINS = frozenset({
    # Type conversions
    "str", "int", "float", "bool", "list", "dict", "set", "tuple", "bytes", "bytearray",
    # Sequence operations
    "len", "range", "enumerate", "zip", "map", "filter", "sorted", "reversed",
    "min", "max", "sum", "all", "any", "abs", "round", "pow", "divmod",
    # Object inspection
    "type", "isinstance", "issubclass", "id", "hash", "dir", "vars", "getattr", "setattr",
    "hasattr", "delattr", "callable", "repr", "ascii", "chr", "ord", "hex", "oct", "bin",
    # I/O
    "print", "input", "open", "format",
    # Iterators
    "iter", "next", "slice",
    # Other
    "super", "object", "staticmethod", "classmethod", "property",
    "compile", "exec", "eval", "globals", "locals", "memoryview", "complex", "frozenset",
})


# =============================================================================
# INTERMEDIATE REPRESENTATION (IR) DATA STRUCTURES
# =============================================================================

@dataclass
class SignalDef:
    """
    A signal definition: count = signal(0)
    
    Attributes:
        name: Variable name (e.g., "count")
        initial: AST node for initial value
        initial_value: Evaluated initial value if simple (int, str, etc.)
        line: Source line number
        column: Source column
        options: Signal options (name, equals, etc.)
    """
    name: str
    initial: ast.AST
    initial_value: Any = None
    line: int = 0
    column: int = 0
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EffectDef:
    """
    An effect definition: @effect def log(): ...
    
    Attributes:
        name: Function name (or auto-generated for lambdas)
        body: AST node for the effect body
        line: Source line number
        cleanup: Optional cleanup function
        dependencies: Set of signal names read (filled by analyzer)
    """
    name: str
    body: ast.AST
    line: int = 0
    column: int = 0
    cleanup: Optional[ast.AST] = None
    dependencies: List[str] = field(default_factory=list)


@dataclass
class MemoDef:
    """
    A memo definition: doubled = memo(lambda: count() * 2)
    
    Attributes:
        name: Variable name
        fn: AST node for the computation function
        line: Source line number
        dependencies: Set of signal names read (filled by analyzer)
    """
    name: str
    fn: ast.AST
    line: int = 0
    column: int = 0
    options: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class HandlerDef:
    """
    An event handler: onclick=lambda: count.set(count() + 1)
    
    Attributes:
        event: Event name (e.g., "click", "input", "submit")
        element_id: Internal element ID (e.g., "_el0")
        body: AST node for handler body
        line: Source line number
        reads: Signal names read in handler (filled by analyzer)
        writes: Signal names written in handler (filled by analyzer)
    """
    event: str
    element_id: str
    body: ast.AST
    line: int = 0
    column: int = 0
    reads: List[str] = field(default_factory=list)
    writes: List[str] = field(default_factory=list)


@dataclass
class FormDef:
    """
    A form definition: form = create_form({...}, validators={...})
    
    Attributes:
        name: Variable name (e.g., "form")
        initial: Dict of field names to initial values
        validators: Dict of field names to validator lists
        line: Source line number
        column: Source column
    """
    name: str
    initial: Dict[str, Any] = field(default_factory=dict)
    validators: Dict[str, ast.AST] = field(default_factory=dict)
    line: int = 0
    column: int = 0


class DOMNodeType(Enum):
    """Types of DOM nodes in the IR."""
    ELEMENT = "element"      # HTML element: div, button, span
    TEXT = "text"            # Static text node
    REACTIVE = "reactive"    # Reactive expression: {count()}
    CONTROL = "control"      # Control flow: Show, For, Switch
    COMPONENT = "component"  # Child island component
    FRAGMENT = "fragment"    # Fragment (no wrapper element)


@dataclass
class DOMNode:
    """
    A node in the DOM tree.
    
    Attributes:
        type: Type of node (element, text, reactive, etc.)
        tag: HTML tag name (for ELEMENT type)
        children: Child nodes
        attributes: Static attributes
        reactive_attrs: Reactive attributes (need effects)
        handlers: Event handlers on this node
        text: Text content (for TEXT type)
        expr: Expression AST (for REACTIVE type)
        control_type: Control flow type (for CONTROL type)
        control_props: Control flow props
    """
    type: DOMNodeType
    tag: str = ""
    children: List["DOMNode"] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    reactive_attrs: Dict[str, ast.AST] = field(default_factory=dict)
    handlers: List[HandlerDef] = field(default_factory=list)
    text: str = ""
    expr: Optional[ast.AST] = None
    control_type: str = ""  # "Show", "For", "Switch", etc.
    control_props: Dict[str, Any] = field(default_factory=dict)
    element_id: str = ""  # Internal ID for codegen
    line: int = 0
    column: int = 0


@dataclass
class IslandIR:
    """
    Complete Intermediate Representation of an @island component.
    
    This is the main output of the parser and the input to the analyzer.
    
    Attributes:
        name: Component function name
        params: Function parameters (props)
        signals: All signal definitions
        effects: All effect definitions
        memos: All memo definitions
        handlers: All event handlers
        forms: All form definitions
        dom_tree: Root DOM node
        filename: Source filename
        source: Original source code
        warnings: Collected warnings
    """
    name: str
    params: List[Tuple[str, Optional[ast.AST]]] = field(default_factory=list)
    signals: List[SignalDef] = field(default_factory=list)
    effects: List[EffectDef] = field(default_factory=list)
    memos: List[MemoDef] = field(default_factory=list)
    handlers: List[HandlerDef] = field(default_factory=list)
    forms: List[FormDef] = field(default_factory=list)
    dom_tree: Optional[DOMNode] = None
    filename: str = "<string>"
    source: str = ""
    warnings: List[CompileWarning] = field(default_factory=list)
    
    # Filled by analyzer
    signal_names: set = field(default_factory=set)
    memo_names: set = field(default_factory=set)
    form_names: set = field(default_factory=set)


# =============================================================================
# MAIN PARSING FUNCTIONS
# =============================================================================

def parse_island(source: str, filename: str = "<string>") -> IslandIR:
    """
    Parse a single @island component from Python source.
    
    Args:
        source: Python source code containing @island component
        filename: Source filename for error messages
    
    Returns:
        IslandIR with all reactive constructs extracted
    
    Raises:
        CompileError: If parsing fails or no @island found
    
    Example:
        >>> ir = parse_island('''
        ... @island
        ... def Counter():
        ...     count = signal(0)
        ...     return button()[count()]
        ... ''', "counter.py")
        >>> 
        >>> print(ir.name)  # "Counter"
        >>> print(ir.signals[0].name)  # "count"
    """
    # Parse Python AST
    try:
        tree = ast.parse(source, filename)
    except SyntaxError as e:
        raise invalid_syntax(filename, e.lineno or 0, str(e.msg))
    
    # Find @island decorated function
    island_func = _find_island_function(tree)
    if island_func is None:
        raise no_island_found(filename)
    
    # Extract component name and params
    name = island_func.name
    params = _extract_params(island_func)
    
    # Initialize IR
    ir = IslandIR(
        name=name,
        params=params,
        filename=filename,
        source=source,
    )
    
    # Extract reactive constructs from function body
    _extract_signals(island_func, ir)
    _extract_effects(island_func, ir)
    _extract_memos(island_func, ir)
    _extract_forms(island_func, ir)
    
    # Build signal/memo/form name sets for quick lookup
    ir.signal_names = {s.name for s in ir.signals}
    ir.memo_names = {m.name for m in ir.memos}
    ir.form_names = {f.name for f in ir.forms}
    
    # Extract DOM tree (return statement)
    ir.dom_tree = _extract_dom_tree(island_func, ir)
    
    # Validate - check for non-compilable constructs
    _validate_island(island_func, ir, filename, source)
    
    return ir


def parse_file(source: str, filename: str = "<string>") -> List[IslandIR]:
    """
    Parse all @island components in a Python file.
    
    Args:
        source: Python source code
        filename: Source filename
    
    Returns:
        List of IslandIR, one per @island component
    
    Example:
        >>> islands = parse_file('''
        ... @island
        ... def Counter(): ...
        ... 
        ... @island
        ... def Timer(): ...
        ... ''')
        >>> print(len(islands))  # 2
    """
    try:
        tree = ast.parse(source, filename)
    except SyntaxError as e:
        raise invalid_syntax(filename, e.lineno or 0, str(e.msg))
    
    islands = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and _has_island_decorator(node):
            # Get the source for just this function
            # (For now, parse the whole source - could optimize later)
            ir = IslandIR(
                name=node.name,
                params=_extract_params(node),
                filename=filename,
                source=source,
            )
            
            _extract_signals(node, ir)
            _extract_effects(node, ir)
            _extract_memos(node, ir)
            _extract_forms(node, ir)
            
            ir.signal_names = {s.name for s in ir.signals}
            ir.form_names = {f.name for f in ir.forms}
            ir.memo_names = {m.name for m in ir.memos}
            
            ir.dom_tree = _extract_dom_tree(node, ir)
            
            _validate_island(node, ir, filename, source)
            
            islands.append(ir)
    
    return islands


# =============================================================================
# HELPER FUNCTIONS - Finding @island
# =============================================================================

def _find_island_function(tree: ast.Module) -> Optional[ast.FunctionDef]:
    """Find the first @island decorated function in the AST."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and _has_island_decorator(node):
            return node
    return None


def _has_island_decorator(func: ast.FunctionDef) -> bool:
    """Check if a function has the @island decorator."""
    for decorator in func.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "island":
            return True
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name) and decorator.func.id == "island":
                return True
    return False


def _extract_params(func: ast.FunctionDef) -> List[Tuple[str, Optional[ast.AST]]]:
    """Extract function parameters (props) with their default values."""
    params = []
    
    # Regular args
    for arg in func.args.args:
        default = None
        # Find default value if any
        params.append((arg.arg, default))
    
    return params


# =============================================================================
# HELPER FUNCTIONS - Extracting Reactive Constructs
# =============================================================================

def _extract_signals(func: ast.FunctionDef, ir: IslandIR) -> None:
    """
    Extract signal definitions from function body.
    
    Looks for patterns like:
        count = signal(0)
        count = signal(0, name="count")
    """
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            # Simple assignment: count = signal(0)
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if _is_signal_call(node.value):
                    sig_def = _parse_signal_call(
                        node.targets[0].id,
                        node.value,
                        node.lineno,
                        node.col_offset
                    )
                    ir.signals.append(sig_def)


def _is_signal_call(node: ast.AST) -> bool:
    """Check if node is a call to signal()."""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "signal":
            return True
    return False


def _parse_signal_call(name: str, call: ast.Call, line: int, col: int) -> SignalDef:
    """Parse a signal() call into SignalDef."""
    initial = call.args[0] if call.args else ast.Constant(value=None)
    
    # Try to evaluate simple initial values
    initial_value = None
    if isinstance(initial, ast.Constant):
        initial_value = initial.value
    elif isinstance(initial, ast.List) and all(isinstance(e, ast.Constant) for e in initial.elts):
        initial_value = [e.value for e in initial.elts]
    elif isinstance(initial, ast.Dict):
        if all(isinstance(k, ast.Constant) for k in initial.keys if k) and \
           all(isinstance(v, ast.Constant) for v in initial.values):
            initial_value = {
                k.value: v.value 
                for k, v in zip(initial.keys, initial.values)
                if k is not None
            }
    
    # Extract options from keyword arguments
    options = {}
    for kw in call.keywords:
        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
            options["name"] = kw.value.value
        elif kw.arg == "equals":
            options["equals"] = kw.value  # Keep AST for later
    
    return SignalDef(
        name=name,
        initial=initial,
        initial_value=initial_value,
        line=line,
        column=col,
        options=options,
    )


def _extract_effects(func: ast.FunctionDef, ir: IslandIR) -> None:
    """
    Extract effect definitions from function body.
    
    Looks for patterns like:
        @effect
        def log():
            print(count())
    """
    for node in func.body:
        if isinstance(node, ast.FunctionDef) and _has_effect_decorator(node):
            effect_def = EffectDef(
                name=node.name,
                body=node,
                line=node.lineno,
                column=node.col_offset,
            )
            ir.effects.append(effect_def)


def _has_effect_decorator(func: ast.FunctionDef) -> bool:
    """Check if a function has the @effect decorator."""
    for decorator in func.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "effect":
            return True
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name) and decorator.func.id == "effect":
                return True
    return False


def _extract_memos(func: ast.FunctionDef, ir: IslandIR) -> None:
    """
    Extract memo definitions from function body.
    
    Looks for patterns like:
        doubled = memo(lambda: count() * 2)
    """
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if _is_memo_call(node.value):
                    memo_def = _parse_memo_call(
                        node.targets[0].id,
                        node.value,
                        node.lineno,
                        node.col_offset
                    )
                    ir.memos.append(memo_def)


def _is_memo_call(node: ast.AST) -> bool:
    """Check if node is a call to memo()."""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in ("memo", "computed"):
            return True
    return False


def _parse_memo_call(name: str, call: ast.Call, line: int, col: int) -> MemoDef:
    """Parse a memo() call into MemoDef."""
    fn = call.args[0] if call.args else None
    
    options = {}
    for kw in call.keywords:
        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
            options["name"] = kw.value.value
        elif kw.arg == "equals":
            options["equals"] = kw.value
    
    return MemoDef(
        name=name,
        fn=fn,
        line=line,
        column=col,
        options=options,
    )


# =============================================================================
# HELPER FUNCTIONS - Extracting Forms
# =============================================================================

def _extract_forms(func: ast.FunctionDef, ir: IslandIR) -> None:
    """
    Extract form definitions from function body.
    
    Looks for patterns like:
        form = create_form(initial={...}, validators={...})
        form = create_form({...}, {...})
    """
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if _is_form_call(node.value):
                    form_def = _parse_form_call(
                        node.targets[0].id,
                        node.value,
                        node.lineno,
                        node.col_offset
                    )
                    ir.forms.append(form_def)


def _is_form_call(node: ast.AST) -> bool:
    """Check if node is a call to create_form()."""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "create_form":
            return True
    return False


def _parse_form_call(name: str, call: ast.Call, line: int, col: int) -> FormDef:
    """Parse a create_form() call into FormDef."""
    initial = {}
    validators = {}
    
    # Parse positional arguments
    if call.args:
        # First arg is initial values
        if isinstance(call.args[0], ast.Dict):
            initial = _parse_dict_literal(call.args[0])
        # Second arg (if present) is validators
        if len(call.args) > 1 and isinstance(call.args[1], ast.Dict):
            validators = call.args[1]  # Keep as AST for later
    
    # Parse keyword arguments
    for kw in call.keywords:
        if kw.arg == "initial" and isinstance(kw.value, ast.Dict):
            initial = _parse_dict_literal(kw.value)
        elif kw.arg == "validators":
            validators = kw.value  # Keep as AST
    
    return FormDef(
        name=name,
        initial=initial,
        validators=validators,
        line=line,
        column=col,
    )


def _parse_dict_literal(node: ast.Dict) -> Dict[str, Any]:
    """Parse a dict literal AST node into a Python dict."""
    result = {}
    for key, value in zip(node.keys, node.values):
        if isinstance(key, ast.Constant):
            key_str = str(key.value)
            if isinstance(value, ast.Constant):
                result[key_str] = value.value
            elif isinstance(value, ast.List):
                result[key_str] = [
                    c.value if isinstance(c, ast.Constant) else None
                    for c in value.elts
                ]
            else:
                result[key_str] = None  # Non-constant value
    return result


# =============================================================================
# HELPER FUNCTIONS - Extracting DOM Tree
# =============================================================================

_element_counter = 0


def _reset_element_counter():
    """Reset element ID counter (for testing)."""
    global _element_counter
    _element_counter = 0


def _next_element_id() -> str:
    """Generate unique element ID."""
    global _element_counter
    eid = f"_el{_element_counter}"
    _element_counter += 1
    return eid


def _extract_dom_tree(func: ast.FunctionDef, ir: IslandIR) -> Optional[DOMNode]:
    """
    Extract DOM tree from function's return statement.
    
    Looks for patterns like:
        return div(class_="container")[
            h1()["Title"],
            button(onclick=lambda: ...)[count()]
        ]
    """
    _reset_element_counter()
    
    # Find return statement
    for node in func.body:
        if isinstance(node, ast.Return) and node.value:
            return _parse_dom_node(node.value, ir)
    
    return None


def _parse_dom_node(node: ast.AST, ir: IslandIR) -> DOMNode:
    """Parse an AST node into a DOMNode."""
    
    # Case 1: Subscript - could be element[children] OR data["key"] OR signal()["key"]
    if isinstance(node, ast.Subscript):
        # Check if this is an element with children (value is a Call to HTML element)
        # vs a data access expression
        if isinstance(node.value, ast.Call):
            # Check if it's a signal/memo read followed by subscript: signal()["key"]
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                if func_name in ir.signal_names or func_name in ir.memo_names:
                    # This is signal()["key"] - treat as reactive expression
                    return DOMNode(
                        type=DOMNodeType.REACTIVE,
                        expr=node,
                        line=getattr(node, 'lineno', 0),
                    )
            # This looks like element()[children] - treat as DOM
            return _parse_element_with_children(node, ir)
        else:
            # This looks like data["key"] or obj.attr - treat as reactive expression
            return DOMNode(
                type=DOMNodeType.REACTIVE,
                expr=node,
                line=getattr(node, 'lineno', 0),
            )
    
    # Case 2: Call - Check in priority order: control flow, signals, elements, builtins
    if isinstance(node, ast.Call):
        # Case 2a: Method call on an object, e.g., text().upper(), items().append(x)
        # This is NEVER an HTML element!
        if isinstance(node.func, ast.Attribute):
            # This is a method call like:
            #   - text().upper()  → func.value is Call(Name("text")), func.attr is "upper"
            #   - obj.method()    → func.value is Name("obj"), func.attr is "method"
            # These are always expressions, NOT HTML elements
            return DOMNode(
                type=DOMNodeType.REACTIVE,
                expr=node,
                line=node.lineno,
            )
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Priority 1: Control flow components - always process first
            if func_name in ("Show", "For", "Index", "Switch", "Match", "Portal", "ErrorBoundary"):
                return _parse_control_flow(node, ir)
            
            # Priority 2: Signal/memo read - this is reactive content, not an element!
            if func_name in ir.signal_names or func_name in ir.memo_names:
                return DOMNode(
                    type=DOMNodeType.REACTIVE,
                    expr=node,
                    line=node.lineno,
                )
            
            # Priority 3: HTML elements (checked BEFORE builtins!)
            # This is important because 'input' is both an HTML element and a Python builtin
            # In a component context, we want to treat it as an HTML element
            if func_name in HTML_ELEMENTS:
                return _parse_element_call(node, ir)
            
            # Priority 4: Python built-in functions like len(), str(), int() - NOT elements!
            if func_name in PYTHON_BUILTINS:
                return DOMNode(
                    type=DOMNodeType.REACTIVE,
                    expr=node,
                    line=node.lineno,
                )
            
            # Priority 5: Unknown function - treat as reactive expression
            # Could be a helper function or custom component
            return DOMNode(
                type=DOMNodeType.REACTIVE,
                expr=node,
                line=node.lineno,
            )
        
        # Fallback: parse as element call
        return _parse_element_call(node, ir)
    
    # Case 3: Constant - static text
    if isinstance(node, ast.Constant):
        return DOMNode(
            type=DOMNodeType.TEXT,
            text=str(node.value),
            line=getattr(node, 'lineno', 0),
        )
    
    # Case 4: Name - variable reference (might be signal or param)
    if isinstance(node, ast.Name):
        if node.id in ir.signal_names or node.id in ir.memo_names:
            # It's a signal/memo being displayed (need to call it)
            return DOMNode(
                type=DOMNodeType.REACTIVE,
                expr=ast.Call(func=node, args=[], keywords=[]),
                line=node.lineno,
            )
        else:
            # It's a prop or other variable
            return DOMNode(
                type=DOMNodeType.REACTIVE,
                expr=node,
                line=node.lineno,
            )
    
    # Case 5: JoinedStr - f-string
    if isinstance(node, ast.JoinedStr):
        return DOMNode(
            type=DOMNodeType.REACTIVE,
            expr=node,
            line=node.lineno,
        )
    
    # Case 6: BinOp, Compare, etc. - expressions
    if isinstance(node, (ast.BinOp, ast.Compare, ast.BoolOp, ast.UnaryOp)):
        return DOMNode(
            type=DOMNodeType.REACTIVE,
            expr=node,
            line=getattr(node, 'lineno', 0),
        )
    
    # Default: treat as reactive expression
    return DOMNode(
        type=DOMNodeType.REACTIVE,
        expr=node,
        line=getattr(node, 'lineno', 0),
    )


def _parse_element_with_children(node: ast.Subscript, ir: IslandIR) -> DOMNode:
    """Parse element[children] syntax."""
    
    # Get the element part (before [])
    element_node = _parse_element_call(node.value, ir) if isinstance(node.value, ast.Call) else _parse_dom_node(node.value, ir)
    
    # Parse children inside []
    children = _parse_children(node.slice, ir)
    element_node.children = children
    
    return element_node


def _parse_element_call(node: ast.Call, ir: IslandIR) -> DOMNode:
    """Parse element() or element(attrs) call."""
    
    # Get tag name
    tag = ""
    if isinstance(node.func, ast.Name):
        tag = node.func.id
    elif isinstance(node.func, ast.Attribute):
        tag = node.func.attr
    
    # Check for control flow
    if tag in ("Show", "For", "Index", "Switch", "Match", "Portal", "ErrorBoundary"):
        return _parse_control_flow(node, ir)
    
    element_id = _next_element_id()
    
    dom_node = DOMNode(
        type=DOMNodeType.ELEMENT,
        tag=tag,
        element_id=element_id,
        line=node.lineno,
        column=node.col_offset,
    )
    
    # Parse attributes
    for kw in node.keywords:
        attr_name = kw.arg
        attr_value = kw.value
        
        if attr_name is None:
            continue
        
        # Event handlers: onclick, oninput, etc.
        if attr_name.startswith("on"):
            event_name = attr_name[2:].lower()  # onclick -> click
            handler = HandlerDef(
                event=event_name,
                element_id=element_id,
                body=attr_value,
                line=node.lineno,
            )
            dom_node.handlers.append(handler)
            ir.handlers.append(handler)
        
        # class_ -> class (Python keyword workaround)
        elif attr_name == "class_":
            if isinstance(attr_value, ast.Constant):
                dom_node.attributes["class"] = attr_value.value
            else:
                dom_node.reactive_attrs["class"] = attr_value
        
        # Static attribute
        elif isinstance(attr_value, ast.Constant):
            dom_node.attributes[attr_name] = attr_value.value
        
        # Reactive attribute
        else:
            dom_node.reactive_attrs[attr_name] = attr_value
    
    return dom_node


def _parse_children(node: ast.AST, ir: IslandIR) -> List[DOMNode]:
    """Parse children from subscript slice."""
    children = []
    
    # Tuple of children: div()[child1, child2, child3]
    if isinstance(node, ast.Tuple):
        for elt in node.elts:
            children.append(_parse_dom_node(elt, ir))
    
    # Single child: div()[child]
    else:
        children.append(_parse_dom_node(node, ir))
    
    return children


def _parse_control_flow(node: ast.Call, ir: IslandIR) -> DOMNode:
    """Parse control flow components (Show, For, etc.)."""
    
    control_type = ""
    if isinstance(node.func, ast.Name):
        control_type = node.func.id
    
    control_props = {}
    
    for kw in node.keywords:
        if kw.arg:
            control_props[kw.arg] = kw.value
    
    return DOMNode(
        type=DOMNodeType.CONTROL,
        control_type=control_type,
        control_props=control_props,
        element_id=_next_element_id(),
        line=node.lineno,
    )


# =============================================================================
# VALIDATION
# =============================================================================

def _validate_island(func: ast.FunctionDef, ir: IslandIR, filename: str, source: str) -> None:
    """
    Validate that the island contains only compilable constructs.
    
    Raises CompileError for non-compilable patterns.
    """
    source_lines = source.split("\n")
    
    for node in ast.walk(func):
        # Classes not allowed
        if isinstance(node, ast.ClassDef):
            line = node.lineno
            source_line = source_lines[line - 1] if line <= len(source_lines) else ""
            raise class_not_compilable(filename, line, source_line, node.name)
        
        # Await not allowed
        if isinstance(node, ast.Await):
            line = node.lineno
            source_line = source_lines[line - 1] if line <= len(source_lines) else ""
            raise await_not_compilable(filename, line, source_line)
        
        # Yield not allowed
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            line = node.lineno
            source_line = source_lines[line - 1] if line <= len(source_lines) else ""
            raise yield_not_compilable(filename, line, source_line)
        
        # Global/nonlocal not allowed
        if isinstance(node, ast.Global):
            line = node.lineno
            source_line = source_lines[line - 1] if line <= len(source_lines) else ""
            raise global_not_compilable(filename, line, source_line, node.names[0])
        
        if isinstance(node, ast.Nonlocal):
            line = node.lineno
            source_line = source_lines[line - 1] if line <= len(source_lines) else ""
            raise global_not_compilable(filename, line, source_line, node.names[0])
        
        # Import inside function not allowed
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            line = node.lineno
            source_line = source_lines[line - 1] if line <= len(source_lines) else ""
            module = ""
            if isinstance(node, ast.Import) and node.names:
                module = node.names[0].name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
            raise import_not_compilable(filename, line, source_line, module)

