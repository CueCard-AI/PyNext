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

## See Also

- [DOM API Reference](../features/DOM_API.md) - User-facing documentation
- [Phase 34.1 Test Overview](../test-case-tracking/phase-34/phase-34-1/TEST_OVERVIEW.md) - Test coverage details

