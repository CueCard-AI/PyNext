# DOM Transpilation Internals

This document explains how PyNext transpiles DOM API calls to JavaScript, achieving zero runtime overhead through passthrough transpilation.

## Overview

DOM APIs are unique in the PyNext transpiler: they require **no transformation**. The Python syntax for DOM manipulation is identical to JavaScript, so the transpiler simply passes them through unchanged.

```
Python:  document.getElementById("app")
    ↓ (passthrough)
JavaScript: document.getElementById("app")
```

This is fundamentally different from other Python→JS transformations:

| Feature | Transformation |
|---------|----------------|
| `items[-1]` | `__py.at(items, -1)` |
| `items.append(x)` | `items.push(x)` |
| `document.getElementById("x")` | `document.getElementById("x")` (unchanged) |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Python Source Code                          │
│   from pynext.client import document                            │
│   el = document.getElementById("app")                           │
│   el.classList.add("active")                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Parser (AST → IR)                        │
│   Parses Python code into Intermediate Representation           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Import Handler (imports.py)                   │
│   Detects `from pynext.client import document`                  │
│   Recognizes DOM imports → returns empty (no JS import needed)  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Method Call Emitter (emitter.py)              │
│   Checks: Is this a DOM method call?                            │
│   YES → Pass through unchanged                                  │
│   NO  → Apply Python→JS transformation                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     JavaScript Output                           │
│   let el = document.getElementById("app");                      │
│   el.classList.add("active");                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. DOM Registry (`pynext/transpiler/dom.py`)

Maintains comprehensive registries of DOM APIs:

```python
# Browser globals (no import needed)
DOM_GLOBALS = frozenset({
    "document", "window", "console", "localStorage", ...
})

# DOM methods that pass through unchanged
DOM_METHODS = frozenset({
    "getElementById", "querySelector", "querySelectorAll",
    "createElement", "appendChild", "remove", "focus", ...
})

# DOM properties that pass through unchanged
DOM_PROPERTIES = frozenset({
    "innerHTML", "textContent", "classList", "dataset",
    "children", "parentElement", "hidden", ...
})
```

### 2. Import Handler (`pynext/transpiler/imports.py`)

Handles `from pynext.client import document` specially:

```python
# DOM passthrough imports - these are browser globals or type-only
dom_passthrough_names = {
    "document", "window", "Element", "Node", "NodeList", ...
}

# If ALL imports are DOM passthrough, return empty list
if all_passthrough:
    return []  # No JavaScript import generated
```

**Result:** `from pynext.client import document` generates no JavaScript code.

### 3. Method Call Emitter (`pynext/transpiler/emitter.py`)

Detects DOM method calls and passes them through:

```python
def _emit_method_call(node: Call) -> Optional[str]:
    # Check if this is a method call on a DOM object (classList, style, etc.)
    DOM_OBJECT_PROPERTIES = {"classList", "dataset", "style", "attributes"}
    
    if isinstance(node.func.value, Attribute):
        parent_attr = node.func.value.attr
        if parent_attr in DOM_OBJECT_PROPERTIES:
            # Pass through unchanged
            return f"{obj_js}.{method}({args_str})"
    
    # Check for document.* method calls
    if isinstance(node.func.value, Name) and node.func.value.id == "document":
        return f"document.{method}({args_str})"
```

## Conflict Resolution

Some DOM methods have the same name as Python methods:

| Method | Python Semantics | DOM Semantics |
|--------|------------------|---------------|
| `remove()` | `list.remove(item)` | `element.remove()` |
| `append()` | `list.append(item)` | `element.append(node, ...)` |

### Detection Strategy

The transpiler uses context and argument patterns to disambiguate:

```python
# el.remove() with no arguments → DOM remove
if method == "remove" and len(args_js) == 0:
    return f"{obj_js}.remove()"  # DOM

# el.remove(item) with 1 argument → Python list remove
if method == "remove" and len(args_js) == 1:
    return f"__py.list.remove({obj_js}, {args_js[0]})"  # Python

# el.append(a, b, c) with multiple args → DOM append
if method == "append" and len(args_js) != 1:
    return f"{obj_js}.append({args_str})"  # DOM

# el.append(item) with 1 arg → ambiguous, defaults to Python
# Use DOM-style append with multiple args if needed
```

### classList.remove() Special Case

`classList.remove()` is detected by checking the parent attribute:

```python
if isinstance(node.func.value, Attribute):
    parent_attr = node.func.value.attr
    if parent_attr == "classList" and method == "remove":
        return f"{obj_js}.remove({args_str})"  # Always DOM
```

## Type Stubs

Python type stubs provide IDE support without runtime overhead:

```python
# pynext/client/dom.py

class Element(Node):
    """DOM Element interface."""
    
    @property
    def innerHTML(self) -> str: ...
    
    @innerHTML.setter
    def innerHTML(self, value: str) -> None: ...
    
    def getAttribute(self, name: str) -> Optional[str]: ...
    def setAttribute(self, name: str, value: str) -> None: ...
    # ... 50+ more methods
```

The `document` global is a placeholder instance:

```python
class _DocumentStub(Document):
    def __getattr__(self, name: str) -> Any:
        raise RuntimeError(
            "document is a client-side object. This code should be "
            "transpiled to JavaScript and run in a browser."
        )

document: Document = _DocumentStub()
```

## Output Comparison

### Pure DOM Code

**Input (Python):**
```python
from pynext.client import document

el = document.getElementById("app")
el.innerHTML = "<h1>Hello</h1>"
el.classList.add("active")
el.dataset.loaded = "true"
```

**Output (JavaScript):**
```javascript
let el = document.getElementById("app");
el.innerHTML = "<h1>Hello</h1>";
el.classList.add("active");
el.dataset.loaded = "true";
```

**Observations:**
- No imports generated
- No `__py.*` runtime helpers
- Identical to hand-written JavaScript

### Mixed Code

**Input (Python):**
```python
from pynext.client import document

items = ["Apple", "Banana", "Cherry"]  # Python list
for item in items:
    li = document.createElement("li")
    li.textContent = item
    document.body.appendChild(li)
```

**Output (JavaScript):**
```javascript
let items = ["Apple", "Banana", "Cherry"];
for (let item of items) {
    let li = document.createElement("li");
    li.textContent = item;
    document.body.appendChild(li);
}
```

**Observations:**
- Python list syntax → JavaScript array syntax
- DOM calls pass through unchanged
- `for...of` used for iteration

## Performance

### Bundle Size Impact

| DOM Usage | Bundle Overhead |
|-----------|-----------------|
| DOM only | **0 KB** |
| DOM + Python lists | ~1 KB (list helpers) |
| DOM + full Python | ~5 KB (full runtime) |

### Runtime Performance

DOM passthrough means:
- **No function call overhead** - direct DOM access
- **No proxy wrappers** - native objects
- **No type coercion** - values used as-is

## Testing

The DOM transpilation is tested in:

| Test File | Coverage |
|-----------|----------|
| `tests/unit/client/test_341_document.py` | Document queries, creation, properties |
| `tests/unit/client/test_341_element_attrs.py` | Attributes, dataset, classList |
| `tests/unit/client/test_341_element_content.py` | innerHTML, textContent, value |
| `tests/unit/client/test_341_traversal.py` | Parent/child/sibling navigation |
| `tests/unit/client/test_341_manipulation.py` | appendChild, remove, cloneNode |
| `tests/integration/transpiler/test_341_dom_parity.py` | Mini-app integration tests |

**Total: 125 tests**

## Adding New DOM APIs

To add support for a new DOM API:

1. **Add to registry** (`pynext/transpiler/dom.py`):
   ```python
   DOM_METHODS.add("newMethod")
   # or
   DOM_PROPERTIES.add("newProperty")
   ```

2. **Add type stub** (`pynext/client/dom.py`):
   ```python
   class Element:
       def newMethod(self, arg: str) -> None:
           """Documentation."""
           ...
   ```

3. **Add tests** (`tests/unit/client/test_341_*.py`):
   ```python
   def test_new_method(self):
       code = 'el.newMethod("value")'
       result = transpile(code)
       assert 'el.newMethod("value")' in result
   ```

## Type-Aware Method Dispatch (Phase 34.5+)

A more advanced passthrough mechanism tracks variable types from constructor assignments:

### The Problem

Some DOM methods have the same name as Python methods:

| Method | Python Usage | DOM Usage |
|--------|--------------|-----------|
| `encode()` | `"text".encode("utf-8")` | `encoder.encode("text")` |
| `get()` | `dict.get("key")` | `params.get("key")` |
| `sort()` | `list.sort()` | `params.sort()` |
| `keys()` | `dict.keys()` | `params.keys()` |

Without type information, the transpiler couldn't distinguish between:
```python
encoder.encode("Hello")  # Should be: encoder.encode("Hello")
s.encode("utf-8")        # Should be: __py.str.encode(s, "utf-8")
```

### The Solution

Track variable types from constructor assignments:

```
┌──────────────────────────────────────────────────────────────────┐
│  Python Source                                                    │
│  encoder = TextEncoder()   ─────────────────────────────────────┐│
│  bytes = encoder.encode("Hello")                                ││
└─────────────────────────────────────────────────────────────────┘│
                                                                   │
                  ┌────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  ScopeTracker records:                                           │
│  _dom_types = { "encoder": "TextEncoder" }                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  DOM_TYPE_METHODS registry:                                      │
│  {                                                               │
│    "TextEncoder": {"encode", "encodeInto"},                      │
│    "URLSearchParams": {"get", "set", "sort", "keys", ...},       │
│    "Blob": {"text", "arrayBuffer", "slice", "stream"},           │
│    ...                                                           │
│  }                                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Method Dispatch Decision:                                       │
│  1. encoder is known type "TextEncoder"                          │
│  2. "encode" is in DOM_TYPE_METHODS["TextEncoder"]               │
│  3. Result: passthrough → encoder.encode("Hello")                │
└─────────────────────────────────────────────────────────────────┘
```

### Components

#### 1. DOM Type Registry (`pynext/transpiler/dom.py`)

Maps constructor names to their method sets:

```python
DOM_TYPE_METHODS: dict[str, FrozenSet[str]] = {
    "TextEncoder": frozenset({"encode", "encodeInto"}),
    "TextDecoder": frozenset({"decode"}),
    "URLSearchParams": frozenset({
        "get", "getAll", "set", "append", "delete", "has",
        "sort", "keys", "values", "entries", "forEach", "toString"
    }),
    "Blob": frozenset({"slice", "text", "arrayBuffer", "stream"}),
    "DataView": frozenset({
        "getInt8", "setInt8", "getUint8", "setUint8", ...
    }),
    # TypedArrays, FormData, Headers, WebSocket, etc.
}
```

#### 2. Scope Tracking (`pynext/transpiler/_internal/scope.py`)

Tracks variable→constructor mappings:

```python
class ScopeTracker:
    def __init__(self):
        self._dom_types: dict[str, str] = {}
    
    def declare_dom_type(self, var_name: str, constructor: str) -> None:
        """Record that var_name was constructed from constructor."""
        self._dom_types[var_name] = constructor
    
    def get_dom_type(self, var_name: str) -> Optional[str]:
        """Get the DOM constructor type for a variable."""
        return self._dom_types.get(var_name)
```

#### 3. Assignment Recording (`pynext/transpiler/emitter.py`)

When emitting assignments, record DOM types:

```python
def _emit_assignment(node: Assignment, indent: int) -> str:
    if isinstance(node.value, Call):
        if isinstance(node.value.func, Name):
            class_name = node.value.func.id
            if class_name in DOM_TYPE_METHODS:
                scope.declare_dom_type(target, class_name)
```

#### 4. Type-Aware Method Dispatch (`pynext/transpiler/emitter.py`)

Check type before Python method mappings:

```python
def _emit_method_call(node: Call) -> Optional[str]:
    # Check if object is a known DOM type
    if isinstance(node.func.value, Name):
        obj_name = node.func.value.id
        dom_type = scope.get_dom_type(obj_name)
        
        if dom_type and is_dom_type_method(dom_type, method):
            # Passthrough - emit direct method call
            return f"{obj_js}.{method}({args_str})"
    
    # ... fall through to Python method mappings
```

### Example Transformations

| Python Code | Without Type Tracking | With Type Tracking |
|-------------|----------------------|-------------------|
| `encoder.encode("Hi")` | `__py.str.encode(encoder, "Hi")` | `encoder.encode("Hi")` |
| `params.get("key")` | `__py.dict.get(params, "key", null)` | `params.get("key")` |
| `params.sort()` | `__py.list.sort(params)` | `params.sort()` |
| `params.keys()` | `Object.keys(params)` | `params.keys()` |
| `d.get("key")` (dict) | `__py.dict.get(d, "key", null)` | `__py.dict.get(d, "key", null)` |

### Benefits

1. **Zero runtime overhead** - Direct method calls, no wrappers
2. **Smaller bundle size** - No `__py.*` helpers for DOM code
3. **Correct semantics** - DOM and Python methods behave correctly
4. **Scalable** - Add new types to registry only

### Adding New DOM Types

To add type-aware passthrough for a new constructor:

1. **Add to DOM_TYPE_METHODS** (`pynext/transpiler/dom.py`):
   ```python
   DOM_TYPE_METHODS["MyConstructor"] = frozenset({
       "method1", "method2", "method3"
   })
   ```

2. **Add tests** (`tests/unit/transpiler/test_dom_type_tracking.py`):
   ```python
   def test_myconstructor_method1_passthrough(self):
       code = '''
   obj = MyConstructor()
   result = obj.method1("arg")
   '''
       result = transpile(code)
       assert 'obj.method1("arg")' in result
   ```

No changes needed to scope tracking or emitter logic.

## See Also

- [DOM API Reference](../features/DOM_API.md) - User-facing documentation
- [Phase 34.1 Test Overview](../test-case-tracking/phase-34/phase-34-1/TEST_OVERVIEW.md) - Test coverage details
- [URL Encoding API](../features/URL_ENCODING.md) - URL, Encoding & Binary Data APIs

