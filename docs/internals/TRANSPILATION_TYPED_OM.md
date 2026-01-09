# CSS Typed OM Transpilation Mechanism (Phase 34.3)

This document explains how PyNext transpiles CSS Typed OM code from Python to JavaScript.

## Overview

CSS Typed OM uses **zero-runtime passthrough** — Python code transpiles 1:1 to identical JavaScript without any runtime helpers or wrappers.

```
Python: CSS.px(100)
   ↓
JavaScript: CSS.px(100)
```

This is possible because CSS Typed OM is a browser-native API with identical syntax in both languages.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Python Source                          │
├─────────────────────────────────────────────────────────────┤
│  width = CSS.px(100)                                        │
│  el.attributeStyleMap.set("width", width)                   │
│  transform = CSSTransformValue([CSS.rotate(CSS.deg(45))])   │
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
│  - DOM_GLOBALS: CSS, CSSUnitValue, CSSTransformValue, ...   │
│  - DOM_METHODS: px, percent, add, mul, set, get, ...        │
│  - DOM_PROPERTIES: attributeStyleMap, value, unit, ...      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Emitter                              │
│  pynext/transpiler/emitter.py                               │
│  Generates JavaScript from AST                              │
│  CSS.* detected as DOM global → passthrough                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    JavaScript Output                        │
├─────────────────────────────────────────────────────────────┤
│  const width = CSS.px(100);                                 │
│  el.attributeStyleMap.set("width", width);                  │
│  const transform = new CSSTransformValue([                  │
│      CSS.rotate(CSS.deg(45))                                │
│  ]);                                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## DOM Registry Configuration

### Global Names

The following are registered as browser globals in `pynext/transpiler/dom.py`:

```python
DOM_GLOBALS = frozenset({
    # CSS Typed OM namespace
    "CSS",
    
    # Value types
    "CSSStyleValue",
    "CSSNumericValue",
    "CSSUnitValue",
    "CSSKeywordValue",
    
    # Math types
    "CSSMathValue",
    "CSSMathSum",
    "CSSMathProduct",
    "CSSMathMin",
    "CSSMathMax",
    "CSSMathClamp",
    
    # Transform types
    "CSSTransformValue",
    "CSSTransformComponent",
    "CSSTranslate",
    "CSSRotate",
    "CSSScale",
    "CSSSkew",
    "CSSPerspective",
    "CSSMatrixComponent",
    
    # Support types
    "StylePropertyMap",
    "DOMMatrix",
})
```

### Method Names

CSS factory and value methods registered for passthrough:

```python
DOM_METHODS = frozenset({
    # Length factories
    "px", "percent", "em", "rem", "vw", "vh", "vmin", "vmax",
    "cm", "mm", "pt", "pc", "ch", "ex", "fr",
    
    # Angle factories
    "deg", "rad", "turn", "grad",
    
    # Time factories
    "ms",  # "s" handled specially
    
    # Resolution factories
    "dpi", "dpcm", "dppx",
    
    # Other factories
    "number", "calc", "keyword",
    
    # Arithmetic methods
    "add", "sub", "mul", "div",
    "equals", "to", "toSum", "negate", "invert",
    
    # Transform factories
    "translate", "translateX", "translateY", "translateZ", "translate3d",
    "rotateX", "rotateY", "rotateZ", "rotate3d",
    "scaleX", "scaleY", "scaleZ", "scale3d",
    "skewX", "skewY",
    "toMatrix",
    
    # Color factories
    "rgb", "hsl", "hwb", "oklch", "oklab", "lab", "lch",
    "lighten", "darken", "saturate", "desaturate",
    "fadeIn", "fadeOut", "toRGB", "toHSL", "toOKLCH", "toHex",
    
    # StylePropertyMap methods
    "set", "get", "getAll", "has", "delete", "clear",
    "keys", "values", "entries", "forEach",
    "computedStyleMap",
})
```

### Property Names

Properties that pass through unchanged:

```python
DOM_PROPERTIES = frozenset({
    # StylePropertyMap access
    "attributeStyleMap",
    
    # CSSUnitValue properties
    "value",
    "unit",
    
    # StylePropertyMap size
    "size",
    
    # CSSTransformValue
    "length",
    "is2D",
})
```

---

## Transpilation Examples

### Basic Factory Calls

```python
# Python
width = CSS.px(100)
height = CSS.percent(50)
angle = CSS.deg(45)
```

```javascript
// JavaScript (identical)
const width = CSS.px(100);
const height = CSS.percent(50);
const angle = CSS.deg(45);
```

### Arithmetic Operations

```python
# Python
base = CSS.px(100)
doubled = base.mul(2)
half = base.div(2)
added = base.add(CSS.px(50))
```

```javascript
// JavaScript (identical)
const base = CSS.px(100);
const doubled = base.mul(2);
const half = base.div(2);
const added = base.add(CSS.px(50));
```

### Property Access

```python
# Python
width = CSS.px(100)
v = width.value  # 100
u = width.unit   # "px"
```

```javascript
// JavaScript (identical)
const width = CSS.px(100);
const v = width.value;  // 100
const u = width.unit;   // "px"
```

### StylePropertyMap

```python
# Python
el.attributeStyleMap.set("width", CSS.px(200))
width = el.attributeStyleMap.get("width")
el.attributeStyleMap.delete("margin")
el.attributeStyleMap.clear()
```

```javascript
// JavaScript (identical)
el.attributeStyleMap.set("width", CSS.px(200));
const width = el.attributeStyleMap.get("width");
el.attributeStyleMap.delete("margin");
el.attributeStyleMap.clear();
```

### Transforms

```python
# Python
from pynext.client import CSS, CSSTransformValue

transform = CSSTransformValue([
    CSS.translate(CSS.px(100), CSS.px(50)),
    CSS.rotate(CSS.deg(45)),
    CSS.scale(2),
])
el.attributeStyleMap.set("transform", transform)
```

```javascript
// JavaScript
const transform = new CSSTransformValue([
    CSS.translate(CSS.px(100), CSS.px(50)),
    CSS.rotate(CSS.deg(45)),
    CSS.scale(2),
]);
el.attributeStyleMap.set("transform", transform);
```

### Math Functions

```python
# Python
width = CSS.calc("100% - 20px")
min_w = CSS.min(CSS.px(300), CSS.percent(100))
clamped = CSS.clamp(CSS.px(12), CSS.vw(2), CSS.px(24))
```

```javascript
// JavaScript
const width = CSS.calc("100% - 20px");
const min_w = CSS.min(CSS.px(300), CSS.percent(100));
const clamped = CSS.clamp(CSS.px(12), CSS.vw(2), CSS.px(24));
```

### Computed Styles

```python
# Python
computed = el.computedStyleMap()
width = computed.get("width")
if computed.has("transform"):
    transform = computed.get("transform")
```

```javascript
// JavaScript (identical)
const computed = el.computedStyleMap();
const width = computed.get("width");
if (computed.has("transform")) {
    const transform = computed.get("transform");
}
```

---

## Emitter Logic

The emitter in `pynext/transpiler/emitter.py` handles CSS Typed OM through the standard DOM passthrough mechanism:

1. **Global Detection**: When the emitter sees `CSS.*`, it checks if `CSS` is in `DOM_GLOBALS`
2. **Method Detection**: Method calls like `.px()`, `.add()`, `.set()` are checked against `DOM_METHODS`
3. **Property Detection**: Property accesses like `.value`, `.unit`, `.attributeStyleMap` are checked against `DOM_PROPERTIES`
4. **Passthrough**: If detected, the code is emitted unchanged; no `__py.*` wrappers are added

### Key Code Path

```python
# In emitter.py

def _emit_method_call(node: Call) -> Optional[str]:
    # ...
    
    # Check if this is a method call on a DOM object
    from pynext.transpiler.dom import is_dom_method
    
    if is_dom_method(method):
        # Pass through unchanged
        args_str = ", ".join(args_js)
        return f"{obj_js}.{method}({args_str})"
    
    # Otherwise, may need transformation
    # ...
```

---

## Type Stubs

Python type stubs provide IDE autocompletion without runtime overhead:

### Location

`pynext/client/typed_om.py`

### Purpose

- IDE autocompletion (VS Code, PyCharm)
- Static type checking (mypy, pyright)
- Documentation for LLMs and developers
- No runtime code — just type annotations

### Example Stub

```python
class CSS:
    @staticmethod
    def px(value: float) -> CSSUnitValue:
        """Create a pixel value."""
        ...
    
    @staticmethod
    def percent(value: float) -> CSSUnitValue:
        """Create a percentage value."""
        ...
```

The `...` (ellipsis) indicates these are stubs — the actual implementation is in the browser.

---

## Debugging Tips

### Check Transpiled Output

```python
from pynext.transpiler import transpile

code = 'width = CSS.px(100)'
js = transpile(code)
print(js)
# Should output: const width = CSS.px(100);
```

### Verify No Runtime Helpers

Good transpilation has no `__py.*` calls:

```python
assert "__py." not in transpile('CSS.px(100)')
```

### Browser DevTools

In browser console, verify typed values:

```javascript
const val = CSS.px(100);
console.log(val);           // CSSUnitValue {value: 100, unit: "px"}
console.log(val.value);     // 100
console.log(val.unit);      // "px"
console.log(val.toString());// "100px"
```

---

## Performance Considerations

CSS Typed OM provides performance benefits:

1. **No String Parsing**: Browser doesn't need to parse CSS strings
2. **Direct Manipulation**: Values are already in the format the browser uses
3. **Batched Updates**: StylePropertyMap can batch multiple property changes
4. **Cached Computation**: Computed style map caches resolved values

PyNext's zero-runtime passthrough ensures no additional overhead from the transpiler.

---

## Browser Compatibility Notes

If targeting browsers without full CSS Typed OM support:

1. **Feature Detection**:
```python
has_typed_om = hasattr(window, "CSS") and hasattr(CSS, "px")
```

2. **Fallback Pattern**:
```python
def set_width(el, value):
    if hasattr(el, "attributeStyleMap"):
        el.attributeStyleMap.set("width", CSS.px(value))
    else:
        el.style.width = f"{value}px"
```

3. **Polyfills**: Consider [css-typed-om](https://github.com/nicolo-ribaudo/css-typed-om-polyfill) polyfill for older browsers
