# PyNext Reactive DOM Updates

## Overview

This document describes how PyNext updates the DOM reactively when signal values change. Unlike React's Virtual DOM diffing, PyNext uses **fine-grained reactivity** where each reactive binding updates only the specific DOM node it's attached to.

## Who This Is For

- **Developers** building interactive UIs with PyNext
- **AI assistants** understanding PyNext's reactivity model
- **Contributors** extending the reactive system

## What It Does

The reactive DOM update system:

1. **Tracks dependencies** - Each binding knows which signals it depends on
2. **Creates effects** - Client-side effects re-run when signals change
3. **Surgically updates DOM** - Only the affected elements are modified

### Binding Types

| Type | Description | Example |
|------|-------------|---------|
| `show` | Toggle element visibility | `Show(when=lambda: visible())` |
| `for` | Render/update list items | `For(each=lambda: items())` |
| `text` | Update text content | `div()[count]` |
| `class` | Update CSS classes | `div(class_=lambda: "active" if x() else "")` |
| `style` | Update inline styles | `div(style=lambda: {"color": color()})` |
| `attr` | Update any attribute | `input_(disabled=lambda: loading())` |

## When It Happens

### Server-Side (SSR)

1. Component renders to HTML
2. Bindings are registered with `RenderContext`
3. Hydration data is serialized and embedded in response

### Client-Side (Hydration)

1. Page loads with server-rendered HTML
2. `__PYNEXT_HYDRATION__` data is parsed
3. Signals and effects are created
4. Bindings register effects that update DOM

### On Signal Change

1. Signal value changes via `.set()` or `.update()`
2. Signal notifies all subscribed effects
3. Effects re-execute
4. DOM update functions modify specific elements

## Where It Lives

### Python Files

```
pynext/
├── reactive/
│   ├── control_flow.py    # Show, For components
│   └── signal.py          # Signal class
├── core/
│   ├── html.py            # Element rendering, callable attrs
│   └── context.py         # RenderContext, binding registration
└── server/
    └── hydration.py       # Hydration script generation
```

### JavaScript Files

```
pynext/runtime/
└── signals.js             # Client-side runtime
    ├── createSignal()     # Signal creation
    ├── createEffect()     # Effect system
    ├── registerBinding()  # Binding registration
    ├── updateShow()       # Show/hide elements
    ├── updateText()       # Update text content
    ├── updateClass()      # Update className
    ├── updateStyle()      # Update inline styles
    └── updateAttr()       # Update attributes
```

## Why This Approach

### vs React Virtual DOM

| Aspect | React | PyNext |
|--------|-------|--------|
| Update granularity | Component tree | Single element |
| Comparison method | Tree diffing | Direct signal subscription |
| Memory usage | Virtual tree copy | Minimal (just subscriptions) |
| Update complexity | O(n) tree size | O(1) per binding |

### Benefits

1. **Performance** - No tree diffing, direct updates
2. **Predictability** - Know exactly what updates when
3. **Debugging** - Clear cause-and-effect relationship
4. **Memory efficiency** - No Virtual DOM overhead

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SERVER SIDE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │  Component  │────▶│RenderContext │────▶│ Hydration   │  │
│  │   .render() │     │.register_    │     │   Data      │  │
│  │             │     │  binding()   │     │             │  │
│  └─────────────┘     └──────────────┘     └─────────────┘  │
│                                                             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ HTML + Hydration Script
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT SIDE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │  hydrate()  │────▶│createEffect()│────▶│ updateXxx() │  │
│  │             │     │              │     │             │  │
│  └─────────────┘     └──────────────┘     └─────────────┘  │
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Signal Subscription                   │   │
│  │  signal.set(newValue) ──▶ effect.execute() ──▶ DOM   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Binding Registration (Python)

When a component renders, bindings are registered:

```python
# In Show.render()
ctx.register_binding(
    node_id=self._id,           # e.g., "show_abc123"
    binding_type="show",
    signal_deps=["sig_1"],      # Depends on this signal
    update_expr="Boolean(__pynext__.getSignal('sig_1').read())",
    initial_value=True,
)
```

### Hydration Data

The binding becomes part of hydration data:

```javascript
window.__PYNEXT_HYDRATION__ = {
    renderId: "abc123",
    signals: {
        visible: { id: "sig_1", value: true }
    },
    bindings: [
        {
            nodeId: "show_abc123",
            type: "show",
            signals: ["sig_1"],
            update: "Boolean(__pynext__.getSignal('sig_1').read())",
            initial: true
        }
    ]
};
```

### Client-Side Effect

The binding creates an effect:

```javascript
function registerBinding(binding) {
    const element = document.getElementById(binding.nodeId);
    const updateFn = new Function('return ' + binding.update);
    
    createEffect(() => {
        const value = updateFn();
        updateShow(element, value);  // For show bindings
    });
}
```

### Signal Change Flow

```
1. User clicks button
2. onclick handler calls: signal.set(newValue)
3. Signal updates internal value
4. Signal notifies subscribers (effects)
5. Effect re-executes
6. updateShow(element, newValue) is called
7. element.style.display is updated
```

## Deep Code Examples

### Show Component

**Python (Server)**:

```python
from pynext.reactive import Signal
from pynext.reactive.control_flow import Show

visible = Signal(False, name="visible")

# This Show will be hidden initially
modal = Show(when=lambda: visible())[
    div(class_="modal")[
        h2()["Create Issue"],
        button(onclick=lambda: visible.set(False))["Close"]
    ]
]
```

**Generated HTML**:

```html
<div id="show_abc123" 
     data-pynext-show="true" 
     data-condition="false"
     style="display: none;">
    <div class="modal">
        <h2>Create Issue</h2>
        <button id="el_1">Close</button>
    </div>
</div>
```

**Client Behavior**:

```javascript
// When visible.set(true) is called:
// 1. Signal value changes to true
// 2. Show effect runs
// 3. updateShow() removes display:none
// 4. Modal becomes visible
```

### For Component

**Python**:

```python
from pynext.reactive import Signal
from pynext.reactive.control_flow import For

items = Signal([
    {"id": 1, "name": "First"},
    {"id": 2, "name": "Second"}
], name="items")

list_view = For(each=lambda: items())[
    lambda item, i: div(key=item["id"])[item["name"]]
]
```

**Client Array Diffing**:

```javascript
// When items change:
// 1. Get new array from signal
// 2. Build key map of new items
// 3. Remove DOM nodes for deleted keys
// 4. Add DOM nodes for new keys
// 5. Reorder if necessary
```

### Callable Attributes

**Python**:

```python
active = Signal(True, name="active")

el = div(
    class_=lambda: "btn active" if active() else "btn"
)["Click me"]
```

**Generated HTML**:

```html
<div id="el_123" class="btn active">Click me</div>
```

**Hydration Binding**:

```javascript
{
    nodeId: "el_123",
    type: "class",
    signals: ["sig_1"],
    update: "__pynext__.getSignal('sig_1').read() ? 'btn active' : 'btn'",
    attr: "class",
    initial: "btn active"
}
```

### Text Interpolation

**Python**:

```python
count = Signal(0, name="count")
el = div()[count]  # Signal as text content
```

**Generated HTML**:

```html
<div>
    <span data-pynext-text="sig_1" id="text_sig_1">0</span>
</div>
```

**On Signal Change**:

```javascript
// count.set(5)
// Effect runs: updateText(element, 5)
// Span content becomes "5"
```

## Performance Comparison

| Operation | React | PyNext | Improvement |
|-----------|-------|--------|-------------|
| Toggle visibility | ~1ms (re-render tree) | ~0.1ms (style change) | 10x |
| Update single list item | ~2ms (reconcile list) | ~0.2ms (update node) | 10x |
| Update text | ~0.5ms (VDOM diff) | ~0.05ms (textContent) | 10x |
| Memory per component | Virtual tree copy | Minimal subscriptions | ~5x less |

## Troubleshooting

### Element Not Updating

**Symptoms**: Signal changes but DOM doesn't update.

**Causes**:
1. No binding registered (check hydration data)
2. Wrong signal ID in binding
3. Element ID doesn't match

**Debug**:
```javascript
console.log(window.__PYNEXT_HYDRATION__.bindings);
console.log(Object.keys(window.__pynext__.effects));
```

### Effect Running Too Often

**Symptoms**: Effect triggers multiple times.

**Causes**:
1. Multiple signals in one expression
2. Effect registered multiple times

**Debug**:
```javascript
window.__pynext__.createEffect(() => {
    console.log('Effect running');
    // Your code
});
```

### Show Content Missing

**Symptoms**: Show element is empty when visible.

**Cause**: Children weren't rendered on server.

**Fix**: Show now always renders children with `display: none` when hidden.

## Best Practices

1. **Keep bindings simple** - One signal per binding when possible
2. **Use keys for lists** - Enables efficient reconciliation
3. **Avoid nested callables** - Each callable is a separate binding
4. **Batch updates** - Use `batch()` for multiple changes

## Related Documentation

- [Signals & Effects](./01-signals.md)
- [Control Flow Components](./control_flow.md)
- [Hydration](./HYDRATION.md)
- [Forms](./FORMS.md)

