# PyNext Hydration Protocol Specification

> **Version:** 1.0.0  
> **Status:** Draft  
> **Last Updated:** December 2024

---

## Table of Contents

1. [Overview](#1-overview)
2. [Server Rendering](#2-server-rendering)
3. [State Serialization](#3-state-serialization)
4. [Client Hydration](#4-client-hydration)
5. [Islands Mode](#5-islands-mode)
6. [Full Hydration Mode](#6-full-hydration-mode)
7. [Error Handling](#7-error-handling)
8. [Performance Optimization](#8-performance-optimization)

---

## 1. Overview

### 1.1 What is Hydration?

Hydration is the process of connecting server-rendered HTML to client-side JavaScript, making static content interactive.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HYDRATION LIFECYCLE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   SERVER                           NETWORK                CLIENT         │
│   ──────                           ───────                ──────         │
│                                                                          │
│   Python code     ───▶   HTML + JSON   ───▶   Static page (no JS)       │
│   renders page           response              displayed                 │
│                                                     │                    │
│                                                     ▼                    │
│                                               JS bundle loads            │
│                                                     │                    │
│                                                     ▼                    │
│                                               hydrate() runs             │
│                                                     │                    │
│                                                     ▼                    │
│                                               Page is interactive        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Why PyNext Hydration is Faster

| Traditional (React) | PyNext |
|---------------------|--------|
| Re-create entire VDOM | Connect existing DOM nodes |
| Diff VDOM vs real DOM | Direct signal → DOM binding |
| Re-render components | No re-rendering |
| 100-500ms hydration | < 50ms hydration |

### 1.3 Key Concepts

| Term | Definition |
|------|------------|
| **Island** | A component marked with `@island` that hydrates independently |
| **Hydration Marker** | A `data-pynext-*` attribute that identifies reactive nodes |
| **State Bundle** | JSON in `<script>` tag containing initial signal values |
| **Client Takeover** | The moment when JS connects signals to DOM |

---

## 2. Server Rendering

### 2.1 HTML Output Format

When the server renders a component, it outputs HTML with special `data-pynext-*` attributes:

```html
<!-- Component wrapper -->
<div data-pynext-component="Counter" data-pynext-id="c_1">
    <!-- Text bound to signal -->
    <span data-pynext-text="count">0</span>
    
    <!-- Button with click handler -->
    <button data-pynext-click="count.set(count()-1)">-</button>
    <button data-pynext-click="count.set(count()+1)">+</button>
</div>
```

### 2.2 Data Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `data-pynext-component` | Marks component root | `data-pynext-component="Counter"` |
| `data-pynext-id` | Unique component ID | `data-pynext-id="c_1"` |
| `data-pynext-text` | Text content bound to signal | `data-pynext-text="count"` |
| `data-pynext-html` | Inner HTML bound to signal | `data-pynext-html="content"` |
| `data-pynext-attr-*` | Attribute bound to signal | `data-pynext-attr-class="theme"` |
| `data-pynext-click` | Click event handler | `data-pynext-click="handler()"` |
| `data-pynext-input` | Input event handler | `data-pynext-input="text.set(e.target.value)"` |
| `data-pynext-change` | Change event handler | `data-pynext-change="toggle()"` |
| `data-pynext-submit` | Submit event handler | `data-pynext-submit="save()"` |
| `data-pynext-show` | Conditional visibility | `data-pynext-show="isVisible"` |
| `data-pynext-for` | List iteration marker | `data-pynext-for="items"` |
| `data-pynext-key` | List item key | `data-pynext-key="1"` |

### 2.3 Server Rendering Algorithm

```python
def render_component(component: Component) -> str:
    """
    Render a component to HTML with hydration markers.
    
    Algorithm:
    1. Create reactive context (signals, effects, memos)
    2. Execute component function to get element tree
    3. For each element:
       a. If contains signal read → add data-pynext-text/html
       b. If has event handler → add data-pynext-click/input/etc
       c. If has reactive attribute → add data-pynext-attr-*
    4. Render element tree to HTML string
    5. Generate state JSON
    6. Wrap with component markers
    
    Returns:
        HTML string with hydration markers
    """
```

### 2.4 Example: Complete Server Output

```python
# Python Component
@island
def TodoItem(todo):
    checked = signal(todo["done"])
    
    return li(
        class_="done" if checked() else "",
        onclick=lambda: checked.set(not checked())
    )[
        todo["text"]
    ]
```

```html
<!-- Server Output -->
<li 
    data-pynext-component="TodoItem"
    data-pynext-id="todo_1"
    data-pynext-attr-class="checked() ? 'done' : ''"
    data-pynext-click="checked.set(!checked())"
    class="">
    Buy groceries
</li>
```

---

## 3. State Serialization

### 3.1 JSON Format

All reactive state is serialized to JSON in a `<script>` tag:

```html
<script id="__PYNEXT_DATA__" type="application/json">
{
    "version": "1.0",
    "components": {
        "c_1": {
            "name": "Counter",
            "signals": {
                "count": 0
            }
        },
        "todo_1": {
            "name": "TodoItem",
            "signals": {
                "checked": false
            }
        }
    },
    "stores": {
        "todos": {
            "items": [
                {"id": 1, "text": "Buy groceries", "done": false},
                {"id": 2, "text": "Walk dog", "done": true}
            ]
        }
    }
}
</script>
```

### 3.2 State Types

| Python Type | JSON Representation | Notes |
|-------------|---------------------|-------|
| `int` | number | Direct mapping |
| `float` | number | Direct mapping |
| `str` | string | Direct mapping |
| `bool` | boolean | Direct mapping |
| `None` | null | Direct mapping |
| `list` | array | Recursive serialization |
| `dict` | object | Recursive serialization |
| `datetime` | string (ISO 8601) | Converted to string |
| Custom class | object | Via `__dict__` or `to_json()` |

### 3.3 Serialization Rules

```python
def serialize_state(component_id: str, signals: dict, stores: dict) -> dict:
    """
    Serialize component state to JSON-compatible format.
    
    Rules:
    1. Signals are serialized by their current value
    2. Stores are serialized as deep objects
    3. Functions are NOT serialized (they're in the JS bundle)
    4. Circular references are detected and raise an error
    5. Non-serializable values (file handles, etc.) raise an error
    """
```

### 3.4 Compression (Optional)

For large state, compression can be enabled:

```html
<!-- Compressed state -->
<script id="__PYNEXT_DATA__" type="application/json" data-compressed="lz">
eJxLTEzJSS0uLk5MTc5IzQEAAHsMAsE=
</script>
```

---

## 4. Client Hydration

### 4.1 Hydration Algorithm

```javascript
/**
 * Hydrate server-rendered HTML with reactivity.
 * 
 * Algorithm:
 * 1. Parse __PYNEXT_DATA__ JSON
 * 2. For each component:
 *    a. Find DOM element by data-pynext-id
 *    b. Create signals from serialized state
 *    c. Bind signals to DOM nodes (data-pynext-text, etc.)
 *    d. Attach event handlers (data-pynext-click, etc.)
 * 3. Initialize stores
 * 4. Run onMount callbacks
 * 5. Mark hydration complete
 */
function hydrate(root) {
    const data = JSON.parse(
        document.getElementById('__PYNEXT_DATA__').textContent
    );
    
    for (const [id, component] of Object.entries(data.components)) {
        hydrateComponent(id, component);
    }
}
```

### 4.2 Signal Binding

```javascript
function bindSignalToDOM(element, signalName, signal) {
    // Text binding: data-pynext-text="count"
    const textAttr = element.getAttribute('data-pynext-text');
    if (textAttr === signalName) {
        createEffect(() => {
            element.textContent = signal();
        });
    }
    
    // Attribute binding: data-pynext-attr-class="theme"
    for (const attr of element.attributes) {
        if (attr.name.startsWith('data-pynext-attr-')) {
            const attrName = attr.name.slice('data-pynext-attr-'.length);
            if (attr.value === signalName) {
                createEffect(() => {
                    element.setAttribute(attrName, signal());
                });
            }
        }
    }
}
```

### 4.3 Event Handler Binding

```javascript
function bindEventHandler(element, eventType, handlerCode, signals) {
    // Parse handler code and create function
    // Example: "count.set(count()+1)"
    const handler = createHandlerFunction(handlerCode, signals);
    
    element.addEventListener(eventType, (event) => {
        // Prevent default for form events
        if (eventType === 'submit') {
            event.preventDefault();
        }
        handler(event);
    });
}
```

### 4.4 DOM Traversal

```javascript
function traverseForHydration(root, signals) {
    const walker = document.createTreeWalker(
        root,
        NodeFilter.SHOW_ELEMENT,
        {
            acceptNode: (node) => {
                // Skip nested components (they hydrate independently)
                if (node !== root && node.hasAttribute('data-pynext-component')) {
                    return NodeFilter.FILTER_REJECT;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        }
    );
    
    while (walker.nextNode()) {
        const node = walker.currentNode;
        
        // Process text bindings
        if (node.hasAttribute('data-pynext-text')) {
            bindTextNode(node, signals);
        }
        
        // Process event bindings
        for (const attr of node.attributes) {
            if (attr.name.startsWith('data-pynext-') && 
                ['click', 'input', 'change', 'submit'].some(e => 
                    attr.name === `data-pynext-${e}`)) {
                bindEventHandler(node, attr.name.slice(12), attr.value, signals);
            }
        }
    }
}
```

---

## 5. Islands Mode

### 5.1 What is Islands Mode?

Islands mode (default) hydrates only components marked with `@island`. The rest of the page remains static HTML.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PAGE STRUCTURE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Static HTML (no JS)                           │   │
│   │   <header>Navigation</header>                                    │   │
│   │   <main>                                                         │   │
│   │       <h1>Welcome</h1>                                          │   │
│   │       <p>Static content...</p>                                  │   │
│   │                                                                  │   │
│   │       ┌───────────────────────┐   ┌───────────────────────┐     │   │
│   │       │    Island: Counter    │   │   Island: Comments    │     │   │
│   │       │    (hydrated, ~2KB)   │   │   (hydrated, ~5KB)    │     │   │
│   │       └───────────────────────┘   └───────────────────────┘     │   │
│   │                                                                  │   │
│   │       <p>More static content...</p>                             │   │
│   │   </main>                                                        │   │
│   │   <footer>Static footer</footer>                                │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Island Definition

```python
from pynext.reactive import island, signal

@island
def Counter():
    """This component will be hydrated on the client."""
    count = signal(0)
    
    return div()[
        button(onclick=lambda: count.set(count() - 1))["-"],
        span()[count()],
        button(onclick=lambda: count.set(count() + 1))["+"],
    ]

def StaticHeader():
    """This component stays static (no hydration)."""
    return header()[
        nav()["Home | About | Contact"]
    ]
```

### 5.3 Bundle Splitting

Each island gets its own JavaScript bundle:

```html
<!-- Only Counter island JS is loaded -->
<script type="module" src="/_pynext/islands/Counter.js" async></script>

<!-- Comments island loaded separately -->
<script type="module" src="/_pynext/islands/Comments.js" async></script>
```

### 5.4 Island Communication

Islands can communicate via:

1. **Shared stores** (defined at page level)
2. **Custom events** (DOM events)
3. **URL state** (search params)

```python
# Page level: shared store
page_store = store({"theme": "dark"})

@island
def ThemeToggle():
    # Access shared store
    return button(onclick=lambda: page_store.theme = "light" if page_store.theme == "dark" else "dark")[
        "Toggle Theme"
    ]

@island
def ThemedContent():
    # Reacts to same store
    return div(class_=page_store.theme)[
        "Content"
    ]
```

---

## 6. Full Hydration Mode

### 6.1 When to Use

Use full hydration for highly interactive applications where most of the page is dynamic:

- Dashboards
- Editors
- Games
- Real-time apps

```python
@page(hydrate="full")
def DashboardPage():
    """Entire page becomes reactive."""
    return div()[
        Sidebar(),
        MainContent(),
        Notifications(),
    ]
```

### 6.2 Trade-offs

| Aspect | Islands Mode | Full Hydration |
|--------|--------------|----------------|
| JS bundle size | Smaller (per island) | Larger (all components) |
| Initial interactivity | Faster (partial) | Slower (all at once) |
| Complexity | Simpler | More complex |
| Use case | Content sites | App-like interfaces |

### 6.3 Full Hydration Output

```html
<!-- Full page wrapped in single component -->
<div data-pynext-root="DashboardPage">
    <aside data-pynext-component="Sidebar">...</aside>
    <main data-pynext-component="MainContent">...</main>
    <div data-pynext-component="Notifications">...</div>
</div>

<!-- Single bundle for all components -->
<script type="module" src="/_pynext/page/DashboardPage.js"></script>

<!-- All state in one JSON -->
<script id="__PYNEXT_DATA__" type="application/json">
{
    "version": "1.0",
    "mode": "full",
    "components": {...}
}
</script>
```

---

## 7. Error Handling

### 7.1 Hydration Mismatch

When server HTML doesn't match client expectations:

```javascript
function hydrateComponent(id, data) {
    const element = document.querySelector(`[data-pynext-id="${id}"]`);
    
    if (!element) {
        console.error(`[PyNext] Hydration mismatch: Component ${id} not found in DOM`);
        return;
    }
    
    // Verify structure
    const textNodes = element.querySelectorAll('[data-pynext-text]');
    for (const node of textNodes) {
        const signalName = node.getAttribute('data-pynext-text');
        if (!(signalName in data.signals)) {
            console.warn(`[PyNext] Signal "${signalName}" not found in state`);
        }
    }
}
```

### 7.2 Recovery Strategies

```javascript
const HYDRATION_CONFIG = {
    // Log mismatches but continue
    onMismatch: 'warn',  // 'warn' | 'error' | 'recover'
    
    // Recover by re-rendering component
    recoverByRerender: true,
    
    // Timeout for hydration
    timeout: 5000,
};
```

### 7.3 Development Mode

In development, additional checks are enabled:

```javascript
if (__DEV__) {
    // Verify all handlers can be parsed
    validateHandlers(element);
    
    // Check for orphaned state
    checkOrphanedState(data);
    
    // Warn about large state
    if (JSON.stringify(data).length > 50000) {
        console.warn('[PyNext] Large state may slow hydration');
    }
}
```

---

## 8. Performance Optimization

### 8.1 Lazy Hydration

Islands can hydrate lazily based on visibility:

```python
@island(hydrate="visible")  # Hydrate when scrolled into view
def LazyComments():
    return div()[Comments()]

@island(hydrate="idle")  # Hydrate when browser is idle
def Analytics():
    return div()[AnalyticsWidget()]

@island(hydrate="interaction")  # Hydrate on first interaction
def SearchBox():
    return div()[SearchInput()]
```

### 8.2 Hydration Priorities

```javascript
// Priority order:
// 1. Above-the-fold interactive elements
// 2. Visible elements
// 3. Below-fold elements
// 4. Non-critical elements

function scheduleHydration(components) {
    const priorities = {
        'immediate': [],  // Buttons, inputs in viewport
        'visible': [],    // Other visible components
        'idle': [],       // Below fold
    };
    
    // Classify and schedule
    for (const comp of components) {
        const priority = classifyPriority(comp);
        priorities[priority].push(comp);
    }
    
    // Hydrate in priority order
    hydrateImmediate(priorities.immediate);
    requestIdleCallback(() => hydrateVisible(priorities.visible));
    requestIdleCallback(() => hydrateIdle(priorities.idle));
}
```

### 8.3 State Streaming

For large applications, state can be streamed:

```html
<!-- Initial critical state inline -->
<script id="__PYNEXT_DATA__" type="application/json">
{"components": {"header": {...}}}
</script>

<!-- Additional state loads async -->
<script>
fetch('/_pynext/state/dashboard.json')
    .then(r => r.json())
    .then(state => PyNext.hydrateAdditional(state));
</script>
```

### 8.4 Metrics

Track hydration performance:

```javascript
const metrics = {
    parseStart: performance.now(),
    parseEnd: 0,
    hydrateStart: 0,
    hydrateEnd: 0,
    components: 0,
    signals: 0,
};

// After hydration
console.log(`[PyNext] Hydration complete:
  Parse: ${metrics.parseEnd - metrics.parseStart}ms
  Hydrate: ${metrics.hydrateEnd - metrics.hydrateStart}ms
  Components: ${metrics.components}
  Signals: ${metrics.signals}`);
```

---

## Appendix: Complete Example

### Server-Side (Python)

```python
from pynext.reactive import island, signal, store
from pynext.core.html import div, button, span, ul, li

@island
def TodoApp():
    todos = store({"items": [
        {"id": 1, "text": "Learn PyNext", "done": False},
        {"id": 2, "text": "Build app", "done": True},
    ]})
    new_text = signal("")
    
    def add():
        if new_text():
            todos.items.append({"id": len(todos.items) + 1, "text": new_text(), "done": False})
            new_text.set("")
    
    return div(id="todo-app")[
        div()[
            input_(type="text", value=new_text(), oninput=lambda e: new_text.set(e.target.value)),
            button(onclick=add)["Add"],
        ],
        ul()[
            [li(onclick=lambda t=t: t.update(done=not t["done"]))[t["text"]] for t in todos.items]
        ],
    ]
```

### Server Output (HTML)

```html
<div id="todo-app" data-pynext-component="TodoApp" data-pynext-id="todo_app">
    <div>
        <input type="text" value="" 
               data-pynext-attr-value="new_text"
               data-pynext-input="new_text.set(e.target.value)">
        <button data-pynext-click="add()">Add</button>
    </div>
    <ul data-pynext-for="todos.items">
        <li data-pynext-key="1" data-pynext-click="todos.items[0].done=!todos.items[0].done">
            Learn PyNext
        </li>
        <li data-pynext-key="2" data-pynext-click="todos.items[1].done=!todos.items[1].done">
            Build app
        </li>
    </ul>
</div>

<script id="__PYNEXT_DATA__" type="application/json">
{
    "version": "1.0",
    "components": {
        "todo_app": {
            "name": "TodoApp",
            "signals": {
                "new_text": ""
            },
            "stores": {
                "todos": {
                    "items": [
                        {"id": 1, "text": "Learn PyNext", "done": false},
                        {"id": 2, "text": "Build app", "done": true}
                    ]
                }
            }
        }
    }
}
</script>

<script type="module" src="/_pynext/islands/TodoApp.js" async></script>
```

### Client-Side (JavaScript)

```javascript
// /_pynext/islands/TodoApp.js
import { createSignal, createStore, createEffect, hydrate } from '/_pynext/reactive.js';

function hydrateIsland(element, data) {
    // Create signals from serialized state
    const new_text = createSignal(data.signals.new_text);
    
    // Create store from serialized state
    const todos = createStore(data.stores.todos);
    
    // Bind input value
    const input = element.querySelector('input');
    createEffect(() => input.value = new_text());
    input.addEventListener('input', (e) => new_text.set(e.target.value));
    
    // Bind add button
    const addBtn = element.querySelector('button');
    addBtn.addEventListener('click', () => {
        if (new_text()) {
            todos.items.push({
                id: todos.items.length + 1,
                text: new_text(),
                done: false
            });
            new_text.set('');
        }
    });
    
    // Bind list items
    const ul = element.querySelector('ul');
    createEffect(() => {
        // Reconcile list (simplified)
        ul.innerHTML = '';
        for (const item of todos.items) {
            const li = document.createElement('li');
            li.textContent = item.text;
            li.addEventListener('click', () => item.done = !item.done);
            ul.appendChild(li);
        }
    });
}

// Auto-hydrate when DOM ready
document.querySelectorAll('[data-pynext-component="TodoApp"]').forEach(el => {
    const id = el.getAttribute('data-pynext-id');
    const data = JSON.parse(document.getElementById('__PYNEXT_DATA__').textContent);
    hydrateIsland(el, data.components[id]);
});
```

---

*End of Hydration Protocol Specification*

