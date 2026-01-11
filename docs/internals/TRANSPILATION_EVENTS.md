# Event Transpilation Mechanism

How PyNext transpiles Python event handling code to JavaScript with zero runtime overhead.

## Overview

Event APIs use **passthrough transpilation** - the Python code transpiles to identical JavaScript without any runtime helpers.

```python
# Python
def on_click(event: MouseEvent):
    if event.ctrlKey:
        event.preventDefault()
    x = event.clientX
```

```javascript
// JavaScript (transpiled)
function on_click(event) {
    if (event.ctrlKey) {
        event.preventDefault();
    }
    let x = event.clientX;
}
```

**No `__py.*` helpers. No wrappers. Pure JavaScript.**

---

## How It Works

### DOM Registry

The transpiler maintains registries of DOM APIs that should pass through unchanged:

```python
# pynext/transpiler/dom.py

DOM_GLOBALS = frozenset({
    # Event constructors
    "Event", "MouseEvent", "KeyboardEvent", "TouchEvent",
    "FocusEvent", "InputEvent", "DragEvent", "WheelEvent",
    "CustomEvent", "PointerEvent", "AnimationEvent",
    "TransitionEvent", "SubmitEvent", "ClipboardEvent",
    
    # Supporting types
    "Touch", "TouchList", "DataTransfer",
    "DataTransferItem", "DataTransferItemList", "FileList",
    ...
})

DOM_METHODS = frozenset({
    # Event methods
    "addEventListener", "removeEventListener", "dispatchEvent",
    "preventDefault", "stopPropagation", "stopImmediatePropagation",
    "composedPath", "getModifierState",
    
    # DataTransfer methods
    "setData", "getData", "clearData", "setDragImage",
    ...
})

DOM_PROPERTIES = frozenset({
    # Event base properties
    "type", "target", "currentTarget", "eventPhase",
    "bubbles", "cancelable", "composed", "timeStamp",
    "isTrusted", "defaultPrevented",
    
    # MouseEvent properties
    "clientX", "clientY", "pageX", "pageY",
    "screenX", "screenY", "offsetX", "offsetY",
    "button", "buttons", "altKey", "ctrlKey",
    "shiftKey", "metaKey", "relatedTarget",
    
    # KeyboardEvent properties
    "key", "code", "repeat", "isComposing", "location",
    
    # TouchEvent properties
    "touches", "changedTouches", "targetTouches",
    
    # DragEvent properties
    "dataTransfer", "dropEffect", "effectAllowed",
    "files", "items", "types",
    ...
})
```

### Emitter Behavior

When the transpiler emits JavaScript, it checks each API call against these registries:

1. **Property Access**: `event.clientX`
   - Check: Is `clientX` in `DOM_PROPERTIES`? → Yes
   - Output: `event.clientX` (unchanged)

2. **Method Call**: `event.preventDefault()`
   - Check: Is `preventDefault` in `DOM_METHODS`? → Yes
   - Output: `event.preventDefault()` (unchanged)

3. **Constructor**: `CustomEvent("my-event", {...})`
   - Check: Is `CustomEvent` in `DOM_GLOBALS`? → Yes
   - Output: `new CustomEvent("my-event", {...})` (add `new` keyword)

### No Runtime Helpers

Compare with non-DOM Python operations:

```python
# Non-DOM: needs runtime helper
items[-1]  # → __py.at(items, -1)

# DOM event: pure passthrough
event.clientX  # → event.clientX
```

---

## Type Stubs

Type stubs in `pynext/client/events.py` provide IDE support without affecting transpilation:

```python
class MouseEvent(UIEvent):
    """Type stub for MouseEvent - transpiles to native browser MouseEvent."""
    
    @property
    def clientX(self) -> float:
        """X coordinate relative to viewport."""
        ...
    
    @property
    def clientY(self) -> float:
        """Y coordinate relative to viewport."""
        ...
```

These stubs:
- Provide IDE autocompletion
- Enable static type checking
- Generate documentation
- **Never affect transpiled output**

---

## Import Handling

When you import event types, they're stripped from the output:

```python
# Python
from pynext.client import MouseEvent, KeyboardEvent

def on_click(event: MouseEvent):
    pass
```

```javascript
// JavaScript
function on_click(event) {
    // Type annotations stripped - they're just for IDE
}
```

Event types are **type-only imports** - they exist only for Python's type system.

---

## Constructor Transpilation

Event constructors add the `new` keyword:

```python
# Python
event = CustomEvent("my-event", {"detail": data})
el.dispatchEvent(event)
```

```javascript
// JavaScript
let event = new CustomEvent("my-event", {"detail": data});
el.dispatchEvent(event);
```

The transpiler knows to add `new` because:
1. `CustomEvent` is in `DOM_GLOBALS`
2. It's being called as a function
3. JavaScript requires `new` for Event constructors

---

## Listener Options

Listener options pass through as JavaScript objects:

```python
# Python
el.addEventListener("click", handler, {"once": True, "capture": True})
```

```javascript
// JavaScript
el.addEventListener("click", handler, {"once": true, "capture": true});
```

Note: `True` → `true` (Python boolean to JavaScript boolean).

---

## Debugging Tips

### 1. Check Registry Membership

If a property isn't passing through:

```python
# Check if it's in the registry
from pynext.transpiler.dom import DOM_PROPERTIES
print("clientX" in DOM_PROPERTIES)  # Should be True
```

### 2. View Transpiled Output

```python
from pynext.transpiler import transpile

code = '''
def handler(event):
    x = event.clientX
'''
print(transpile(code))
```

### 3. Look for `__py.*`

If you see `__py.*` helpers in event code, something isn't registered:

```javascript
// BAD - property not in registry
let x = __py.getattr(event, "clientX");

// GOOD - passthrough
let x = event.clientX;
```

---

## Adding New Event Properties

To add support for a new event property:

1. Add to `DOM_PROPERTIES` in `pynext/transpiler/dom.py`:
   ```python
   DOM_PROPERTIES = frozenset({
       ...
       "newProperty",  # Add here
   })
   ```

2. Add type stub in `pynext/client/events.py`:
   ```python
   class SomeEvent(Event):
       @property
       def newProperty(self) -> SomeType:
           """Description."""
           ...
   ```

3. Add test in `tests/unit/client/test_344_*.py`:
   ```python
   def test_new_property_passthrough(self):
       code = '''
def handler(event):
    x = event.newProperty
'''
       result = transpile(code)
       assert 'event.newProperty' in result
       assert '__py.' not in result
   ```

---

## Performance Impact

Passthrough transpilation has **zero runtime overhead**:

| Approach | Overhead |
|----------|----------|
| PyNext Events | 0ms - native browser APIs |
| Runtime wrappers | ~0.1ms per property access |
| Type checking | 0ms - stripped in output |

The transpiled JavaScript is indistinguishable from handwritten code.

---

## See Also

- [Event API Documentation](../features/EVENTS.md) - User-facing event docs
- [DOM Transpilation](./TRANSPILATION_DOM.md) - General DOM passthrough
- [Transpiler Architecture](./TRANSPILER_ARCHITECTURE.md) - Overall transpiler design

