# CSS Styling Transpilation Mechanism (Phase 34.2)

This document explains how PyNext transpiles CSS styling code from Python to JavaScript.

## Overview

CSS styling in PyNext uses a **zero-runtime passthrough** design for core APIs:

```
Python                    →  JavaScript
el.style.display = "flex" →  el.style.display = "flex"
```

Higher-level helpers compile down to DOM API calls:

```
Python                                    →  JavaScript
set_css_var("primary", "blue")           →  document.documentElement.style.setProperty("--primary", "blue")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Python Source                          │
├─────────────────────────────────────────────────────────────┤
│  el.style.backgroundColor = "red"                           │
│  window.getComputedStyle(el).width                          │
│  el.animate([{...}], duration=300)                          │
│  set_css_var("primary", "#3b82f6")                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       AST Parser                            │
│  Parses Python into Abstract Syntax Tree                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Passthrough Detector                       │
│  pynext/transpiler/dom.py                                   │
│  - DOM_GLOBALS: document, window, Element, ...              │
│  - DOM_METHODS: getComputedStyle, animate, ...              │
│  - DOM_PROPERTIES: style, classList, cssText, ...           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Emitter                              │
│  pynext/transpiler/emitter.py                               │
│  Generates JavaScript from AST                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    JavaScript Output                        │
├─────────────────────────────────────────────────────────────┤
│  el.style.backgroundColor = "red";                          │
│  window.getComputedStyle(el).width;                         │
│  el.animate([{...}], {duration: 300});                      │
│  document.documentElement.style.setProperty("--primary",    │
│      "#3b82f6");                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Passthrough Detection

### DOM Registry (pynext/transpiler/dom.py)

The DOM registry defines what passes through unchanged:

```python
# Globals that are always passthrough
DOM_GLOBALS: FrozenSet[str] = frozenset({
    "document",
    "window",
    "Element",
    "CSSStyleDeclaration",
    # ...
})

# Methods that pass through unchanged  
DOM_METHODS: FrozenSet[str] = frozenset({
    # CSSStyleDeclaration methods
    "getPropertyValue",
    "setProperty",
    "removeProperty",
    "getPropertyPriority",
    
    # Window methods (Phase 34.2)
    "getComputedStyle",
    "matchMedia",
    
    # Web Animations API (Phase 34.2)
    "animate",
    "getAnimations",
    "pause",
    "play",
    "cancel",
    "reverse",
    # ...
})

# Properties that pass through unchanged
DOM_PROPERTIES: FrozenSet[str] = frozenset({
    "style",
    "classList",
    "cssText",
    "display",
    "visibility",
    # All 200+ CSS properties...
})
```

### Emitter Logic (pynext/transpiler/emitter.py)

The emitter checks for passthrough patterns:

```python
def emit_Call(self, node: Call) -> str:
    # Check for document.* method calls
    if isinstance(node.func.value, Name) and node.func.value.id == "document":
        args_str = ", ".join(args_js)
        return f"document.{method}({args_str})"
    
    # Check for window.* method calls (Phase 34.2)
    if isinstance(node.func.value, Name) and node.func.value.id == "window":
        args_str = ", ".join(args_js)
        return f"window.{method}({args_str})"
    
    # Check for DOM object properties (.style, .classList)
    DOM_OBJECT_PROPERTIES = {"classList", "dataset", "style", "attributes"}
    DOM_OBJECT_METHODS = {
        "getPropertyValue", "setProperty", "removeProperty",
        "add", "remove", "toggle", "contains", "replace",
        "animate", "getAnimations",
        # ...
    }
    
    if isinstance(node.func.value, Attribute):
        parent_attr = node.func.value.attr
        if parent_attr in DOM_OBJECT_PROPERTIES and method in DOM_OBJECT_METHODS:
            args_str = ", ".join(args_js)
            return f"{obj_js}.{method}({args_str})"
```

---

## Transpilation Examples

### 1. Inline Style Assignment

```python
# Python
el.style.backgroundColor = "red"
```

```javascript
// JavaScript (unchanged)
el.style.backgroundColor = "red";
```

**How it works:**
1. Parser creates `Assign` node with `Attribute` target
2. Emitter detects `style` in attribute chain
3. Emits as-is: property assignment on style object

### 2. setProperty Method

```python
# Python
el.style.setProperty("--primary", "#3b82f6")
```

```javascript
// JavaScript (unchanged)
el.style.setProperty("--primary", "#3b82f6");
```

**How it works:**
1. Parser creates `Call` node with `Attribute` func
2. Emitter detects `.style.` parent and `setProperty` method
3. Passes through unchanged with same arguments

### 3. window.getComputedStyle

```python
# Python
computed = window.getComputedStyle(el)
width = computed.width
```

```javascript
// JavaScript (unchanged)
const computed = window.getComputedStyle(el);
const width = computed.width;
```

**How it works:**
1. `window.getComputedStyle` is detected as window.* call
2. Passes through with same arguments
3. Property access on result also passes through

### 4. Web Animations API

```python
# Python
anim = el.animate([
    {"opacity": "0"},
    {"opacity": "1"},
], duration=300, easing="ease-out")
```

```javascript
// JavaScript
const anim = el.animate([
    {opacity: "0"},
    {opacity: "1"},
], {duration: 300, easing: "ease-out"});
```

**How it works:**
1. `animate` detected in DOM_METHODS
2. Keyframe list transpiles as array of objects
3. Keyword args converted to options object

### 5. CSS Variable Helpers

```python
# Python
from pynext.client.css_vars import set_css_var
set_css_var("primary", "#3b82f6")
```

```javascript
// JavaScript (expanded)
const target = document.documentElement;
const var_name = "--primary";
target.style.setProperty(var_name, "#3b82f6");
```

**How it works:**
1. Helper function is included in transpiled output
2. Function body uses DOM passthrough internally
3. No runtime overhead - just function call inlining

### 6. classList Operations

```python
# Python
el.classList.add("active", "visible")
el.classList.toggle("selected", is_active)
```

```javascript
// JavaScript (unchanged)
el.classList.add("active", "visible");
el.classList.toggle("selected", is_active);
```

**How it works:**
1. `classList` detected as DOM_OBJECT_PROPERTY
2. `add`, `toggle` detected in DOM_OBJECT_METHODS
3. Passes through with all arguments

---

## Special Cases

### Python's `float` Property

Python's `float` is a reserved word, but CSS `float` exists. We use `cssFloat`:

```python
# Python
el.style.cssFloat = "left"  # Not el.style.float
```

```javascript
// JavaScript
el.style.cssFloat = "left";  // Standard DOM property
```

### Infinity for Iterations

Python's `float("inf")` transpiles to JavaScript's `Infinity`:

```python
# Python
el.animate([...], iterations=float("inf"))
```

```javascript
// JavaScript
el.animate([...], {iterations: Infinity});
```

### Keyword Arguments to Options Object

Python keyword arguments become JavaScript options object:

```python
# Python
el.animate(keyframes, duration=300, easing="ease-out", fill="forwards")
```

```javascript
// JavaScript
el.animate(keyframes, {duration: 300, easing: "ease-out", fill: "forwards"});
```

---

## Why Zero Runtime?

1. **Performance**: No wrapper overhead
2. **Bundle size**: No extra runtime code
3. **Debugging**: JavaScript matches source 1:1
4. **Predictability**: Same behavior as native APIs

The passthrough approach means:
- No abstraction leaks
- No performance surprises
- Easy to debug in browser dev tools
- Compatible with all CSS features

---

## Files Involved

| File | Purpose |
|------|---------|
| `pynext/transpiler/dom.py` | DOM passthrough registry |
| `pynext/transpiler/emitter.py` | JavaScript emission logic |
| `pynext/client/dom.py` | Python type stubs |
| `pynext/client/window.py` | Window type stubs |
| `pynext/client/animation.py` | Animation type stubs |
| `pynext/client/styles.py` | StylesProxy helper |
| `pynext/client/css_vars.py` | CSS variable helpers |
| `pynext/client/style_utils.py` | Style utility helpers |

