# PyNext Runtime Architecture

> **Complete guide to how PyNext's client-side JavaScript works**

This document explains the architecture of PyNext's JavaScript runtime — essential for contributors and for understanding how Python code becomes interactive browser experiences.

---

## Table of Contents

1. [The Big Picture](#the-big-picture)
2. [Module Organization](#module-organization)
3. [Core Concepts](#core-concepts)
4. [Data Flow](#data-flow)
5. [Component Initialization](#component-initialization)
6. [Signal System](#signal-system)
7. [Build System](#build-system)
8. [Adding New Features](#adding-new-features)
9. [Performance Guidelines](#performance-guidelines)

---

## The Big Picture

### What Problem Does the Runtime Solve?

Browsers only understand JavaScript. When a user clicks a button, presses a key, or toggles dark mode, the browser fires JavaScript events. PyNext lets developers write Python, but we need JavaScript to make things interactive.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           THE PYNEXT BRIDGE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PYTHON (Your Code)                    JAVASCRIPT (PyNext Runtime)         │
│   ──────────────────                    ────────────────────────────         │
│                                                                              │
│   @on_keydown("cmd+k")    ──compile──▶  keyboard.js handles keydown         │
│   def open_search():                    event, calls your handler            │
│       search.set(True)                                                       │
│                                                                              │
│   Dialog()[...]           ──render──▶   HTML with data-pynext-dialog        │
│                           ──hydrate──▶  dialog.js makes it interactive      │
│                                                                              │
│   use_visibility()        ──compile──▶  browser.js tracks visibility        │
│                           ◀──signal──   updates Signal when tab changes     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Design Philosophy

1. **SolidJS Principles**: Fine-grained reactivity, no virtual DOM, surgical updates
2. **Minimal Footprint**: Only load what's needed (< 10 KB typical)
3. **Progressive Enhancement**: Server-rendered HTML works without JS
4. **Zero Config**: Automatic initialization based on HTML attributes

---

## Module Organization

### Directory Structure

```
pynext/runtime/
├── ui/                      # UI Component Modules (loaded on-demand)
│   ├── core.js              # Shared utilities (~1.6 KB minified)
│   ├── dialog.js            # Dialog, AlertDialog
│   ├── dropdown.js          # DropdownMenu
│   ├── tabs.js              # Tabs, TabsList, TabsTrigger
│   ├── accordion.js         # Accordion, AccordionItem
│   ├── forms.js             # Switch, Checkbox, Toggle, Radio
│   ├── tooltip.js           # Tooltip
│   ├── popover.js           # Popover
│   ├── sheet.js             # Sheet/Drawer
│   ├── combobox.js          # Combobox/Autocomplete
│   ├── command.js           # Command palette
│   ├── calendar.js          # Calendar, DatePicker
│   ├── datatable.js         # DataTable
│   ├── fileupload.js        # FileUpload
│   └── loader.js            # Dynamic module loader
│
├── signals.js               # Core reactivity system
├── keyboard.js              # Keyboard shortcut handling
├── theme.js                 # Dark mode, theme management
├── storage.js               # localStorage/sessionStorage sync
├── focus.js                 # Focus traps, roving focus
├── sse.js                   # Server-Sent Events
├── browser.js               # Visibility, online status
├── toast.js                 # Toast notifications
├── navigation.js            # Client-side navigation
├── islands.js               # Island hydration
└── min/                     # Minified versions (production)
```

### Module Categories

| Category | Modules | Purpose |
|----------|---------|---------|
| **Core** | signals.js | Reactivity primitives |
| **Features** | keyboard.js, theme.js, storage.js, focus.js | Python API implementations |
| **Browser** | sse.js, browser.js | Browser API wrappers |
| **UI** | ui/*.js | Component interactivity |
| **Infrastructure** | navigation.js, islands.js | Framework plumbing |

---

## Core Concepts

### 1. The `__pynext__` Namespace

All runtime code lives under `window.__pynext__`:

```javascript
window.__pynext__ = {
    // Signals
    signals: Map,           // Signal ID → Signal instance
    setSignal: Function,    // Update a signal value
    getSignal: Function,    // Read a signal value
    
    // UI Components
    ui: {
        getFocusable: Function,
        trapFocus: Function,
        dialog: { open, close },
        dropdown: { open, close },
        // ...
    },
    
    // Features
    keyboard: { register, unregister },
    theme: { get, set, toggle },
    sse: { connect, close },
    browser: { initVisibility, initOnline },
    
    // Loader
    uiLoader: { load, scan, configure },
};
```

### 2. Data Attributes

Components communicate with JavaScript via `data-pynext-*` attributes:

```html
<!-- Dialog -->
<div data-pynext-dialog="dialog-1">
    <button data-pynext-dialog-trigger="dialog-1">Open</button>
    <div data-pynext-dialog-content>...</div>
</div>

<!-- Tabs -->
<div data-pynext-tabs>
    <div data-pynext-tabs-list>
        <button data-pynext-tab-trigger="tab1">Tab 1</button>
    </div>
    <div data-pynext-tab-content="tab1">Content</div>
</div>
```

This approach:
- Works with server rendering (no hydration mismatch)
- Enables CSS-only styling via `[data-state="open"]`
- Allows lazy loading (scan DOM for attributes)

### 3. Event Delegation

Instead of attaching listeners to each element, we use event delegation:

```javascript
// BAD: Listener per element
document.querySelectorAll('[data-pynext-dialog-trigger]').forEach(el => {
    el.addEventListener('click', handler);
});

// GOOD: Single delegated listener
document.addEventListener('click', e => {
    const trigger = e.target.closest('[data-pynext-dialog-trigger]');
    if (trigger) handleTriggerClick(trigger);
});
```

Benefits:
- Works for dynamically added elements
- Fewer listeners = less memory
- Single point of control

---

## Data Flow

### Python → JavaScript

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PYTHON → JAVASCRIPT FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. COMPILE TIME                                                             │
│     ────────────                                                             │
│     Python decorators/hooks analyzed                                         │
│     │                                                                        │
│     ▼                                                                        │
│     Hydration data generated (JSON)                                          │
│     │                                                                        │
│     ▼                                                                        │
│     Embedded in HTML as <script>__PYNEXT_DATA__ = {...}</script>            │
│                                                                              │
│  2. RENDER TIME                                                              │
│     ───────────                                                              │
│     Components render to HTML                                                │
│     │                                                                        │
│     ▼                                                                        │
│     data-pynext-* attributes added                                          │
│     │                                                                        │
│     ▼                                                                        │
│     Required runtime scripts included                                        │
│                                                                              │
│  3. HYDRATION TIME (Browser)                                                 │
│     ─────────────────────────                                               │
│     Runtime JS loads                                                         │
│     │                                                                        │
│     ▼                                                                        │
│     Reads __PYNEXT_DATA__                                                   │
│     │                                                                        │
│     ▼                                                                        │
│     Registers handlers, initializes signals                                  │
│     │                                                                        │
│     ▼                                                                        │
│     Scans DOM for data-pynext-* attributes                                  │
│     │                                                                        │
│     ▼                                                                        │
│     Attaches event listeners                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JavaScript → Python (via Server Actions)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        JAVASCRIPT → PYTHON FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User clicks button                                                          │
│  │                                                                           │
│  ▼                                                                           │
│  onclick handler (generated from Python lambda)                              │
│  │                                                                           │
│  ├──▶ Client-side only? Update Signal directly                              │
│  │                                                                           │
│  └──▶ Server action? POST to /__pynext__/action                             │
│       │                                                                      │
│       ▼                                                                      │
│       Python @server_action executes                                         │
│       │                                                                      │
│       ▼                                                                      │
│       Returns JSON response                                                  │
│       │                                                                      │
│       ▼                                                                      │
│       JavaScript updates Signal/DOM                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Initialization

### The Initialization Lifecycle

```javascript
// 1. DOM Ready or dynamic content added
document.addEventListener('DOMContentLoaded', init);
document.addEventListener('turbo:load', init);      // Turbo Drive
document.addEventListener('htmx:afterSettle', init); // HTMX

// 2. Scan and initialize
function init() {
    initDialogs();
    initDropdowns();
    initTabs();
    // ...
}

// 3. Each initializer finds its elements
function initDialogs() {
    document.querySelectorAll('[data-pynext-dialog]').forEach(dialog => {
        // Set up event listeners
        // Store state
        // Connect to triggers
    });
}
```

### Dynamic Content

When new content is added (e.g., via HTMX), the loader re-scans:

```javascript
// Automatically triggered on htmx:afterSettle
__pynext__.uiLoader.scan();

// Or manually
document.addEventListener('my-custom-event', () => {
    __pynext__.uiLoader.scan();
});
```

---

## Signal System

### How Signals Work

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SIGNAL FLOW                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Python: count = Signal(0)                                                   │
│                                                                              │
│  Compiles to:                                                                │
│  ┌─────────────────────────────────────────────────────────┐                │
│  │  __PYNEXT_DATA__.signals = [                            │                │
│  │    { id: "signal_abc123", value: 0 }                    │                │
│  │  ]                                                      │                │
│  └─────────────────────────────────────────────────────────┘                │
│                                                                              │
│  Runtime hydrates:                                                           │
│  ┌─────────────────────────────────────────────────────────┐                │
│  │  __pynext__.signals.set("signal_abc123", {              │                │
│  │    value: 0,                                            │                │
│  │    subscribers: Set(),                                  │                │
│  │  });                                                    │                │
│  └─────────────────────────────────────────────────────────┘                │
│                                                                              │
│  When value changes:                                                         │
│  ┌─────────────────────────────────────────────────────────┐                │
│  │  __pynext__.setSignal("signal_abc123", 1);              │                │
│  │  │                                                      │                │
│  │  ├──▶ Update internal value                             │                │
│  │  ├──▶ Notify subscribers                                │                │
│  │  └──▶ Subscribers update DOM                            │                │
│  └─────────────────────────────────────────────────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fine-Grained Updates (SolidJS Style)

```javascript
// React approach (BAD for us)
// - Re-render entire component
// - Diff virtual DOM
// - Apply patches

// SolidJS approach (GOOD)
// - Track exactly which DOM nodes depend on signal
// - Update ONLY those nodes
// - No diffing, no re-renders

// Example: Text content bound to signal
const textNode = document.createTextNode(signal.value);
signal.subscribe(newValue => {
    textNode.textContent = newValue;  // Direct update
});
```

---

## Build System

### Minification

```python
from pynext.build import minify_runtime

# Minify all runtime files
results = minify_runtime(strip_debug=True)

# Results show savings
# keyboard.js: 14.2 KB → 5.2 KB (64% saved)
```

### Tree Shaking

```python
from pynext.build import get_required_modules

# Analyze app to find required modules
required = get_required_modules(Path('./my-app'))
# ['signals.js', 'keyboard.js', 'ui/dialog.js']

# Bundle only what's needed
from pynext.build import bundle_runtime
bundle = bundle_runtime(required, minified=True)
```

### Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| Source | Full, commented | Minified |
| console.debug | Included | Stripped |
| Source maps | Yes | Optional |
| Bundle | All modules | Tree-shaken |

---

## Adding New Features

### Step 1: Define Python API

```python
# pynext/core/client.py

@dataclass
class MyFeatureSignal:
    id: str
    value: Any
    
    def to_dict(self):
        return {"id": self.id, "value": self.value}

def use_my_feature() -> MyFeatureSignal:
    """Hook for my feature."""
    signal = MyFeatureSignal(id=f"myfeature_{uuid4().hex[:8]}", value=None)
    
    # Register with context
    ctx = get_context()
    if ctx:
        ctx.my_feature = signal
    
    return signal
```

### Step 2: Create JavaScript Runtime

```javascript
// pynext/runtime/myfeature.js

(function(g) {
    'use strict';
    
    g.__pynext__ = g.__pynext__ || {};
    
    g.__pynext__.myFeature = {
        init: function(signalId) {
            // Set up browser listeners
            // Update signal on changes
        },
        
        getValue: function() {
            // Return current value
        }
    };
    
    // Auto-hydrate from __PYNEXT_DATA__
    var data = g.__PYNEXT_DATA__;
    if (data && data.myFeature) {
        g.__pynext__.myFeature.init(data.myFeature.id);
    }
    
})(window);
```

### Step 3: Add to Build System

```python
# pynext/build/bundle.py

FEATURE_TO_RUNTIME = {
    # ... existing ...
    'use_my_feature': 'myfeature.js',
}
```

### Step 4: Write Tests

```python
# tests/unit/test_myfeature.py

def test_use_my_feature_returns_signal():
    signal = use_my_feature()
    assert signal.id.startswith('myfeature_')

def test_js_runtime_exists():
    path = Path('pynext/runtime/myfeature.js')
    assert path.exists()
```

### Step 5: Document

Create `docs/features/MY_FEATURE.md` with:
- First principles explanation
- Architecture diagram
- Step-by-step usage
- API reference
- Common patterns
- Troubleshooting

---

## Performance Guidelines

### Do's

1. **Use event delegation** — One listener, not many
2. **Batch DOM updates** — Minimize reflows
3. **Lazy load modules** — Only load what's needed
4. **Use CSS for animations** — GPU-accelerated
5. **Minimize state** — Only track what changes

### Don'ts

1. **Don't create closures in loops** — Memory leaks
2. **Don't query DOM repeatedly** — Cache references
3. **Don't use innerHTML** — Security and performance
4. **Don't forget cleanup** — Remove listeners on unmount
5. **Don't block main thread** — Use requestIdleCallback

### Size Budgets

| Module Type | Target Size (minified) |
|-------------|----------------------|
| Core utilities | < 2 KB |
| Feature module | < 1.5 KB |
| UI component | < 1 KB |
| Total runtime | < 10 KB |

---

## Debugging Tips

### Enable Debug Mode

```javascript
// In browser console
localStorage.setItem('__pynext_debug__', 'true');
location.reload();

// Debug output will appear in console
// [PyNext] Signal updated: signal_abc123 = 42
// [PyNext] Dialog opened: dialog-1
```

### Inspect State

```javascript
// View all signals
console.table(__pynext__.signals);

// View specific signal
__pynext__.getSignal('signal_abc123');

// View UI state
__pynext__.ui.dialog.getState('dialog-1');
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Component not interactive | JS not loaded | Check script includes |
| Signal not updating | Wrong ID | Check hydration data |
| Memory leak | Missing cleanup | Add removeEventListener |
| Slow initialization | Too many DOM queries | Use delegation |

---

## Related Documentation

- [Signals Internals](./SIGNALS_INTERNALS.md)
- [UI Components Internals](./UI_COMPONENTS_INTERNALS.md)
- [Build System](./BUILD_SYSTEM.md)
- [Performance Audit](../PERFORMANCE_AUDIT.md)

