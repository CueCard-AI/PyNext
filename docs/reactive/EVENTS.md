# PyNext Event Modifiers

## Who

**For PyNext developers** building interactive UIs that need to control event behavior—modals, forms, dropdowns, nested clickables.

## What

Event modifiers are **wrapper functions** that add behavior control to event handlers:

| Modifier | What It Does |
|----------|--------------|
| `stop()` | Calls `event.stopPropagation()` |
| `prevent()` | Calls `event.preventDefault()` |
| `self_only()` | Only fires if `event.target === event.currentTarget` |
| `once()` | Handler fires once, then removes itself |
| `capture()` | Use capture phase instead of bubble phase |

## When

Use event modifiers when you need to:
- **Modals**: Close when clicking overlay but not content (`self_only`)
- **Forms**: Handle submission without page reload (`prevent`)
- **Nested buttons**: Prevent click from bubbling to parent (`stop`)
- **First-time actions**: Show intro tooltip once (`once`)
- **Event interception**: Catch events before they reach targets (`capture`)

## Where

```python
from pynext import div, button, stop, prevent, self_only, once, capture
```

## Why

### The Problem

PyNext renders HTML on the server and hydrates on the client. Event handlers are serialized to JavaScript. But you can't serialize:

```python
# ❌ This doesn't work - Python code can't serialize
onclick=lambda e: e.stopPropagation()
```

### The Solution

Wrap handlers in modifiers that PyNext understands:

```python
# ✅ This works - modifier metadata is serialized
onclick=stop(lambda: do_action())
```

## How

### Basic Usage

```python
from pynext import div, button, stop, prevent, self_only

# Stop propagation
button(onclick=stop(lambda: handle_click()))["Click Me"]

# Prevent default
form(onsubmit=prevent(lambda: handle_submit()))["..."]

# Only fire on self (not children)
div(onclick=self_only(lambda: close_modal()))["..."]
```

### Compose Modifiers

Modifiers can be composed by nesting:

```python
# Both stop propagation AND prevent default
button(onclick=stop(prevent(lambda: handle())))["Submit"]

# All modifiers together
div(onclick=capture(once(stop(prevent(self_only(lambda: init()))))))["..."]
```

### Real Example: Modal

```python
from pynext import div, button, Signal, Show, self_only

show_modal = Signal(False)

# Modal overlay
Show(when=lambda: show_modal())[
    div(
        class_="overlay",
        style="position: fixed; inset: 0; background: rgba(0,0,0,0.5);",
        # Only close when clicking the overlay itself, not its children
        onclick=self_only(lambda: show_modal.set(False)),
    )[
        div(class_="modal-content")[
            "Modal content here",
            button(onclick=lambda: show_modal.set(False))["Close"],
        ]
    ]
]
```

### Real Example: Form

```python
from pynext import form, button, input_, prevent

def handle_submit():
    # Process form data
    print("Form submitted!")

form(onsubmit=prevent(handle_submit))[
    input_(type="text", name="username"),
    button(type="submit")["Submit"],
]
```

### Real Example: Nested Buttons

```python
from pynext import div, button, stop

div(onclick=lambda: print("outer clicked"))[
    button(onclick=stop(lambda: print("inner clicked")))["Inner"]
]
# Clicking "Inner" only prints "inner clicked", not "outer clicked"
```

## First Principles

### Event Flow in DOM

```
                    ┌─────────────┐
                    │   Window    │
                    └─────────────┘
                          │
         Capture Phase ↓  │  ↑ Bubble Phase
                          │
                    ┌─────────────┐
                    │   Document  │
                    └─────────────┘
                          │
                    ┌─────────────┐
                    │   <body>    │
                    └─────────────┘
                          │
                    ┌─────────────┐
                    │   <div>     │  ← overlay (self_only handler)
                    └─────────────┘
                          │
                    ┌─────────────┐
                    │   <div>     │  ← modal content
                    └─────────────┘
                          │
                    ┌─────────────┐
                    │  <button>   │  ← click target
                    └─────────────┘
```

When you click the button:
1. **Capture phase**: Events travel DOWN from window to target
2. **Target phase**: Event reaches the clicked element
3. **Bubble phase**: Events travel UP from target to window

### How Modifiers Work

```python
# Python
div(onclick=self_only(lambda: close()))
```

Serializes to:

```javascript
// Generated JavaScript
element.addEventListener('click', (event) => {
    // self_only check
    if (event.target !== event.currentTarget) return;
    
    // Handler code
    pynext_debug.signals['show_modal'].set(false);
});
```

## API Reference

### EventHandler

```python
@dataclass
class EventHandler:
    fn: Callable          # The handler function
    stop: bool = False    # Call stopPropagation()
    prevent: bool = False # Call preventDefault()
    self_only: bool = False # Only fire if target === currentTarget
    once: bool = False    # Fire only once
    capture: bool = False # Use capture phase
```

### stop(handler)

Wraps handler to call `event.stopPropagation()` before execution.

```python
stop(lambda: action())
# or
stop(existing_event_handler)
```

### prevent(handler)

Wraps handler to call `event.preventDefault()` before execution.

```python
prevent(lambda: action())
```

### self_only(handler)

Only fires handler if `event.target === event.currentTarget`.

```python
self_only(lambda: action())
```

### once(handler)

Handler fires only once, then the listener is removed.

```python
once(lambda: init())
```

### capture(handler)

Uses capture phase instead of bubble phase.

```python
capture(lambda: intercept())
```

## Comparison

### vs SolidJS

SolidJS uses inline JavaScript:

```jsx
// SolidJS
<div onClick={(e) => { e.stopPropagation(); action(); }}>
```

PyNext uses declarative wrappers:

```python
# PyNext
div(onclick=stop(action))
```

### vs Vue

Vue uses modifier syntax:

```vue
<!-- Vue -->
<div @click.stop="action">
```

PyNext uses function composition:

```python
# PyNext
div(onclick=stop(action))
```

### vs React

React requires manual event handling:

```jsx
// React
<div onClick={(e) => { e.stopPropagation(); action(); }}>
```

PyNext abstracts this:

```python
# PyNext
div(onclick=stop(action))
```

## Performance

Modifiers add minimal overhead:
- **Compile time**: O(1) wrapper detection
- **Hydration**: O(1) modifier application
- **Runtime**: Single conditional checks before handler

## Files

| File | Purpose |
|------|---------|
| `pynext/events.py` | Event handler wrappers |
| `pynext/core/html.py` | Serialization logic |
| `pynext/runtime/signals.js` | Client-side modifier application |
| `tests/unit/events/test_event_handlers.py` | 50 tests |

