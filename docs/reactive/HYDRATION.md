# PyNext Hydration Guide

## What is Hydration?

Hydration is the process of making server-rendered HTML interactive on the client. When a PyNext page loads:

1. **Server** renders HTML with initial state embedded
2. **Browser** displays HTML immediately (fast first paint)
3. **JavaScript** loads and "hydrates" the HTML, connecting signals to DOM
4. **Page** becomes fully interactive

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PYNEXT HYDRATION FLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Server                          Network                    Client       │
│  ──────                          ───────                    ──────       │
│                                                                          │
│  1. Render component                                                     │
│     └─► Create signals                                                   │
│     └─► Generate HTML                                                    │
│     └─► Embed __PYNEXT_HYDRATION__                                       │
│                                                                          │
│                    ─────────────────────────►                            │
│                           HTML + JS                                      │
│                                                                          │
│                                              2. Display HTML (instant!)  │
│                                              3. Parse __PYNEXT_HYDRATION__│
│                                              4. Create client signals    │
│                                              5. Attach event handlers    │
│                                              6. ✨ Page is interactive    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Why Hydration?

| Approach | Initial Load | Interactivity | SEO |
|----------|-------------|---------------|-----|
| Pure SPA | Slow (wait for JS) | After JS loads | Poor |
| Pure SSR | Fast | No client interaction | Good |
| **SSR + Hydration** | **Fast** | **After hydration** | **Good** |

PyNext gives you the best of both worlds: instant content visibility AND full client-side reactivity.

## How It Works

### 1. Server-Side: Signal Registration

When you create a Signal inside a render context, it automatically registers for hydration:

```python
from pynext import page, Signal, div, span

@page(title="Counter")
def counter():
    # This signal auto-registers with the render context
    count = Signal(0, name="count")
    
    return div()[
        span()[count()],
        button(onclick=lambda: count.set(count() + 1))["Increment"]
    ]
```

### 2. Server-Side: HTML Generation

The page renders to HTML with embedded state:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Counter</title>
    <script src="/_pynext/runtime.js" defer></script>
</head>
<body>
    <div id="__pynext">
        <div>
            <span data-pynext-text="count">0</span>
            <button id="el_abc123">Increment</button>
        </div>
    </div>
    <script>
        window.__PYNEXT_HYDRATION__ = {
            "renderId": "abc123",
            "signals": {
                "count": {"id": "sig_1", "value": 0, "elementId": "sig_sig_1"}
            },
            "events": {
                "el_abc123": {"click": "__pynext__.getSignal('sig_1').update(v => v + 1)"}
            }
        };
    </script>
</body>
</html>
```

### 3. Client-Side: Hydration

The PyNext runtime (`reactive.js`) reads `__PYNEXT_HYDRATION__` and:

1. **Creates signals** with server values
2. **Binds text nodes** via `data-pynext-text` attributes
3. **Attaches event handlers** from the events map
4. **Page becomes interactive!**

```javascript
// Simplified version of what reactive.js does
function hydrate() {
    const data = window.__PYNEXT_HYDRATION__;
    
    // Create signals with server values
    for (const [name, info] of Object.entries(data.signals)) {
        const signal = createSignal(info.value);
        window.__pynext__.signals[info.id] = signal;
    }
    
    // Attach event handlers
    for (const [elementId, handlers] of Object.entries(data.events)) {
        const el = document.getElementById(elementId);
        for (const [event, code] of Object.entries(handlers)) {
            el.addEventListener(event, () => eval(code));
        }
    }
}
```

## Hydration Modes

### Islands Mode (Default)

Only `@island` components become interactive:

```python
from pynext import page, div, Signal
from pynext.core.island import island

@island
def Counter():
    count = Signal(0, name="count")
    return button(onclick=lambda: count.set(count() + 1))[
        f"Count: {count()}"
    ]

@page(title="Home", hydration="islands")  # Default
def home():
    return div()[
        "Static content (no hydration)",
        Counter(),  # This island hydrates
        "More static content"
    ]
```

Benefits:
- Minimal JavaScript bundle
- Fast hydration (only islands)
- Most content stays static

### Full Hydration Mode

Entire page becomes reactive:

```python
@page(title="App", hydration="full")
def app():
    count = Signal(0, name="count")
    
    return div()[
        button(onclick=lambda: count.set(count() + 1))["Click"],
        span()[count()]  # This updates reactively
    ]
```

Benefits:
- SPA-like experience
- All state is reactive
- Good for highly interactive pages

## API Reference

### Signal Methods for Hydration

```python
from pynext.reactive import Signal

# Create a signal with a name (for hydration)
count = Signal(0, name="count")

# Serialize for __PYNEXT_HYDRATION__
count.to_hydration_state()  # → {"count": 0}

# Serialize to JSON-compatible dict
count.to_json()  # → {"id": "sig_1", "name": "count", "value": 0}

# Generate JS initialization code
count.get_js_init()  # → "const sig_1 = __pynext__.createSignal(0)"

# Render as HTML with hydration marker
count.render_value()  # → '<span data-pynext-text="count">0</span>'
```

### Store Methods for Hydration

```python
from pynext.reactive import Store

# Create a store with a name (for hydration)
state = Store({"items": [], "count": 0}, name="state")

# Serialize for __PYNEXT_HYDRATION__
state.to_hydration_state()  
# → {"state": {"items": [], "count": 0}}

# Generate JS initialization code
state.get_js_init()
# → "const store_1 = __pynext__.createStore({items: [], count: 0})"
```

### Memo Methods for Hydration

```python
from pynext.reactive import Signal, Memo

count = Signal(5)
doubled = Memo(lambda: count() * 2, name="doubled")

# Serialize for __PYNEXT_HYDRATION__
doubled.to_hydration_state()  # → {"doubled": 10}

# Render as HTML with hydration marker
doubled.render_value()  # → '<span data-pynext-memo="doubled">10</span>'
```

### Render Context

```python
from pynext.core.context import render_context, get_context

# Create a render context for SSR
with render_context() as ctx:
    # Signals created here auto-register
    count = Signal(0, name="count")
    
    # Get hydration data
    data = ctx.get_hydration_data()
    # → {
    #     "renderId": "abc123",
    #     "signals": {"count": {...}},
    #     "events": {...},
    #     ...
    # }
```

### Server Hydration Utilities

```python
from pynext.server.hydration import (
    HydrationData,
    collect_hydration_data,
    inject_hydration_script,
    render_with_hydration,
)

# Render a component with full hydration support
html = render_with_hydration(my_page)

# Or manually inject hydration data
with render_context() as ctx:
    html = my_component.render()
    data = collect_hydration_data(ctx)
    html = inject_hydration_script(html, data)
```

## Performance Considerations

### Bundle Size

The PyNext hydration runtime is minimal:
- Core reactive primitives: ~2.3KB gzipped
- Hydration code: ~500 bytes
- Total: < 3KB

### Real Browser Hydration Time

> ⚠️ **Important**: Hydration performance depends on actual DOM operations,
> not in-memory signal creation. DOM operations are **100-1000x slower** than
> memory operations.

Run real browser benchmarks with: `pytest tests/e2e/bench_hydration_real.py -v -s`

**Realistic expectations for actual browser hydration:**

| Scenario | Hydration Time | Time to Interactive |
|----------|----------------|---------------------|
| 10 signals + 10 handlers | 10-30ms | < 50ms |
| 100 signals + 100 handlers | 30-80ms | < 100ms |
| 500 signals + 500 handlers | 100-300ms | < 500ms |
| Linear clone (104 signals + 305 handlers) | 50-100ms | < 150ms |

**Why these numbers matter:**
- 60fps = 16.67ms per frame
- Hydration < 100ms feels instant to users
- Hydration > 300ms may feel sluggish
- Use Islands mode to hydrate only interactive parts

### Synthetic Benchmarks (In-Memory Only)

The following are **NOT representative of real performance** - they measure
in-memory signal creation without DOM operations:

| Scenario | In-Memory Time | ⚠️ Real Browser |
|----------|----------------|-----------------|
| 10 signals | 3.3 µs | **~20ms** (6000x slower) |
| 100 signals | 37.5 µs | **~60ms** (1600x slower) |
| Linear clone | 242 µs | **~80ms** (330x slower) |

### What Causes Real-World Slowdown?

| Operation | In-Memory | Real DOM |
|-----------|-----------|----------|
| Create signal | ~0.5 µs | ~0.5 µs |
| `document.getElementById()` | N/A | ~1-10 µs |
| `addEventListener()` | N/A | ~1-5 µs |
| `element.textContent = x` | N/A | ~10-50 µs |
| Layout recalculation | N/A | ~1-10 ms |

**Per hydrated element total: ~50-100 µs** (not ~0.5 µs)

### Server-Side Serialization (Python)

Server-side is very fast since it's just JSON serialization:

| Scenario | Measured |
|----------|----------|
| Simple page (1 signal) | ~12 µs |
| 100 signals | ~84 µs |
| Complex page | ~91 µs |

### Memory

| Item | Measured |
|------|----------|
| Per hydrated signal (browser) | ~500-1000 bytes |
| Per store | ~1KB base + data |

### Performance Tips

1. **Use Islands mode** - Only hydrate interactive components
2. **Defer non-critical hydration** - Use `priority="low"` for below-fold content
3. **Keep signal count reasonable** - < 100 signals per page is ideal
4. **Batch initial state** - Reduce `__PYNEXT_HYDRATION__` size

## Debugging Hydration

### Check if Hydration Data Exists

Open browser DevTools Console:

```javascript
console.log(window.__PYNEXT_HYDRATION__);
// Should show: {renderId: ..., signals: {...}, events: {...}}
```

### Verify Signal Values

```javascript
// Get a signal by ID
const count = window.__pynext__.getSignal('sig_1');
console.log(count());  // Current value

// Update it manually
count.set(10);
```

### Check Event Bindings

```javascript
// See all registered events
console.log(window.__PYNEXT_HYDRATION__.events);
```

### Common Issues

1. **Signal not reactive after hydration**
   - Check if signal has a `name` parameter
   - Verify signal appears in `__PYNEXT_HYDRATION__.signals`

2. **Event handler not working**
   - Check element has correct ID
   - Verify event in `__PYNEXT_HYDRATION__.events`
   - Check console for JavaScript errors

3. **Hydration mismatch (value differs)**
   - Ensure server and client render same data
   - Check for race conditions with async data

## Advanced: Custom Hydration

### Manual Signal Hydration

```javascript
// On the client, if you need to manually hydrate:
import { createSignal, hydrate } from '/_pynext/reactive.js';

// Create signals from server data
const data = window.__PYNEXT_HYDRATION__;
const signals = {};

for (const [name, info] of Object.entries(data.signals)) {
    signals[name] = createSignal(info.value);
    
    // Bind to existing DOM element
    const el = document.querySelector(`[data-pynext-text="${name}"]`);
    if (el) {
        createEffect(() => {
            el.textContent = signals[name]();
        });
    }
}
```

### Progressive Hydration

For large pages, hydrate critical components first:

```python
@page(title="Dashboard", hydration="islands")
def dashboard():
    return div()[
        # Critical: hydrates immediately
        island(priority="high")[
            SearchBar()
        ],
        # Deferred: hydrates when visible
        island(priority="low", when="visible")[
            ActivityFeed()  # Large, below fold
        ],
    ]
```

## AI Guide: Extending Hydration

### Adding New Primitive Support

1. **Add serialization methods** to the primitive class:
   - `to_hydration_state()` → `{name: value}`
   - `to_json()` → `{id, name, value, ...}`
   - `get_js_init()` → JavaScript code

2. **Register with context** in `__init__`:
```python
def __init__(self, ...):
    # ... initialization ...
    self._register_with_context()

def _register_with_context(self):
    from pynext.core.context import get_context
    ctx = get_context()
    if ctx:
        ctx.register_my_primitive(self)
```

3. **Update RenderContext** to handle the new type

4. **Update reactive.js** to hydrate the new type

### Adding New Event Types

1. **Server side**: Extract handler code in `html.py`
2. **Generate JS**: Add to `events` in hydration data
3. **Client side**: Bind in `hydrate()` function

## Summary

PyNext hydration enables:
- ⚡ **Fast initial load** via SSR
- 🔄 **Full reactivity** after hydration
- 🎯 **SEO friendly** with real HTML content
- 📦 **Tiny bundle** (~3KB)
- 🏝️ **Islands or full** hydration modes

For most apps, the default Islands mode is recommended. Use Full hydration for highly interactive SPAs.

