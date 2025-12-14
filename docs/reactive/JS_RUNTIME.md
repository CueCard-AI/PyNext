# PyNext JavaScript Runtime

> **Version:** 1.0.0  
> **Size:** < 3KB gzipped  
> **Last Updated:** December 2024

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [API Reference](#2-api-reference)
3. [Hydration](#3-hydration)
4. [Performance Guide](#4-performance-guide)
5. [Debugging Guide](#5-debugging-guide)

---

## 1. Quick Start

### 1.1 Installation

The runtime is automatically included when using PyNext. For manual inclusion:

```html
<!-- Production (minified) -->
<script src="/_pynext/reactive.min.js"></script>

<!-- Development (with source maps) -->
<script type="module" src="/_pynext/reactive.js"></script>
```

### 1.2 Basic Usage

```javascript
import { createSignal, createEffect, createMemo } from '/_pynext/reactive.js';

// Create a reactive signal
const count = createSignal(0);

// Read the value
console.log(count());  // 0

// Update the value
count.set(5);
console.log(count());  // 5

// Create an effect that auto-tracks dependencies
createEffect(() => {
    console.log(`Count is: ${count()}`);
});

count.set(10);  // Logs: "Count is: 10"

// Create a memoized computation
const doubled = createMemo(() => count() * 2);
console.log(doubled());  // 20
```

### 1.3 API Mirrors Python Exactly

| Python | JavaScript |
|--------|------------|
| `count = signal(0)` | `const count = createSignal(0)` |
| `count()` | `count()` |
| `count.set(5)` | `count.set(5)` |
| `count.update(lambda x: x+1)` | `count.update(x => x+1)` |
| `count.peek()` | `count.peek()` |
| `@effect` | `createEffect()` |
| `memo(lambda: ...)` | `createMemo(() => ...)` |
| `store({...})` | `createStore({...})` |
| `batch(lambda: ...)` | `batch(() => ...)` |
| `untrack(lambda: ...)` | `untrack(() => ...)` |

---

## 2. API Reference

### 2.1 createSignal(initial, options?)

Create a reactive signal - a container for a value that notifies subscribers when changed.

```javascript
// Basic usage
const count = createSignal(0);

// Read value
console.log(count());  // 0

// Write value
count.set(5);

// Update with function
count.update(x => x + 1);

// Read without tracking
count.peek();

// Custom equality
const obj = createSignal(
    { id: 1, name: 'Alice' },
    { equals: (a, b) => a.id === b.id }
);
```

**Parameters:**
- `initial` - Initial value (any type)
- `options.equals` - Custom equality function `(a, b) => boolean`

**Returns:** Signal object with methods:
- `()` - Read value (tracks dependency if in reactive context)
- `.set(value)` - Write new value
- `.update(fn)` - Update value with function
- `.peek()` - Read without tracking

---

### 2.2 createEffect(fn)

Create a side effect that runs when dependencies change.

```javascript
// Basic effect
createEffect(() => {
    console.log(`Count: ${count()}`);
});

// Effect with cleanup
createEffect(() => {
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);  // Cleanup function
});

// Dispose an effect
const dispose = createEffect(() => { ... });
dispose();  // Stop the effect
```

**Parameters:**
- `fn` - Effect function. Can return a cleanup function.

**Returns:** Dispose function to stop the effect.

**Key Behaviors:**
- Runs immediately on creation
- Re-runs when any signal read inside changes
- Cleanup function runs before re-execution and on dispose
- Dependencies are automatically tracked

---

### 2.3 createMemo(fn, options?)

Create a memoized computation that caches its result.

```javascript
const count = createSignal(5);
const doubled = createMemo(() => count() * 2);

console.log(doubled());  // 10
console.log(doubled());  // 10 (cached, no recompute)

count.set(10);
console.log(doubled());  // 20 (recomputed because count changed)
```

**Parameters:**
- `fn` - Computation function
- `options.equals` - Custom equality function

**Returns:** Accessor function that returns cached value.

**Key Behaviors:**
- Lazy: Only computes when first read
- Cached: Returns cached value until dependencies change
- Tracks dependencies automatically

---

### 2.4 createStore(initialValue)

Create a deeply reactive store from an object or array.

```javascript
const store = createStore({
    user: { name: 'Alice', age: 30 },
    items: []
});

// Read
console.log(store.user.name);  // 'Alice'

// Write (triggers reactivity)
store.user.name = 'Bob';
store.items.push({ id: 1 });

// Use in effect
createEffect(() => {
    console.log(`Name: ${store.user.name}`);
});
```

**Parameters:**
- `initialValue` - Object or array

**Returns:** Proxy that intercepts all property access and mutation.

**Tracked Array Methods:**
- `push`, `pop`, `shift`, `unshift`
- `splice`, `sort`, `reverse`
- `fill`, `copyWithin`

---

### 2.5 batch(fn)

Batch multiple updates into a single notification cycle.

```javascript
const a = createSignal(0);
const b = createSignal(0);

createEffect(() => {
    console.log(`Sum: ${a() + b()}`);
});
// Logs: "Sum: 0"

batch(() => {
    a.set(1);
    b.set(1);
});
// Logs once: "Sum: 2" (not twice)
```

**Parameters:**
- `fn` - Function containing updates

---

### 2.6 untrack(fn)

Execute a function without tracking dependencies.

```javascript
createEffect(() => {
    const tracked = count();       // This is tracked
    const untracked = untrack(() => other());  // This is NOT tracked
});
```

**Parameters:**
- `fn` - Function to execute

**Returns:** Return value of fn

---

### 2.7 Control Flow Components

#### Show

Conditional rendering based on reactive condition.

```javascript
Show({
    when: () => count() > 0,
    children: () => document.createTextNode('Positive'),
    fallback: () => document.createTextNode('Zero or negative'),
    parent: container
});
```

#### For

Keyed list rendering with efficient reconciliation.

```javascript
For({
    each: () => items,
    key: item => item.id,
    children: (item, index) => {
        const li = document.createElement('li');
        li.textContent = item.name;
        return li;
    },
    fallback: () => document.createTextNode('No items'),
    parent: container
});
```

#### Switch / Match

Multi-branch conditional rendering.

```javascript
Switch({
    children: [
        Match({
            when: () => status() === 'loading',
            children: () => document.createTextNode('Loading...')
        }),
        Match({
            when: () => status() === 'error',
            children: () => document.createTextNode('Error!')
        }),
        Match({
            when: true,  // Default case
            children: () => document.createTextNode('Done')
        })
    ],
    parent: container
});
```

#### Portal

Render content to a different DOM location.

```javascript
Portal({
    mount: 'body',  // or document.body
    children: () => modalContent
});
```

#### ErrorBoundary

Catch errors and render fallback.

```javascript
ErrorBoundary({
    fallback: (error) => document.createTextNode(`Error: ${error.message}`),
    children: () => riskyContent,
    parent: container
});
```

---

## 3. Hydration

### 3.1 How Hydration Works

1. Server renders HTML with `data-pynext-*` attributes
2. Server serializes state to `<script id="__PYNEXT_DATA__">`
3. Client loads and calls `hydrate()`
4. Runtime connects signals to DOM elements

### 3.2 Server-Rendered HTML Format

```html
<!-- Component with hydration markers -->
<div data-pynext-component="Counter" data-pynext-id="c1">
    <span data-pynext-text="count">0</span>
    <button data-pynext-click="count.set(count()+1)">+</button>
</div>

<!-- Serialized state -->
<script id="__PYNEXT_DATA__" type="application/json">
{
    "components": {
        "c1": {
            "signals": { "count": 0 }
        }
    }
}
</script>
```

### 3.3 Hydration API

```javascript
// Hydrate entire page
hydrate();

// Hydrate specific root
hydrate(document.getElementById('app'));

// Hydrate single island
hydrateIsland('[data-pynext-component="Counter"]');
```

### 3.4 Supported Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `data-pynext-component` | Component name | `data-pynext-component="Counter"` |
| `data-pynext-id` | Component ID | `data-pynext-id="c1"` |
| `data-pynext-text` | Bind text content | `data-pynext-text="count"` |
| `data-pynext-click` | Click handler | `data-pynext-click="count.set(1)"` |
| `data-pynext-input` | Input handler | `data-pynext-input="text.set(e.target.value)"` |
| `data-pynext-change` | Change handler | `data-pynext-change="checked.set(e.target.checked)"` |
| `data-pynext-submit` | Form submit | `data-pynext-submit="save()"` |

---

## 4. Performance Guide

### 4.1 Performance Targets

| Metric | React | PyNext | Improvement |
|--------|-------|--------|-------------|
| Signal update | 5-10ms | < 0.1ms | 50-100x |
| List update (1 of 1000) | 10-50ms | < 1ms | 10-50x |
| Bundle size | ~40KB | < 3KB | 13x |
| Memory per signal | 200-500B | < 50B | 4-10x |

### 4.2 Why It's Fast

1. **No Virtual DOM**
   - React: Component → VDOM → Diff → DOM
   - PyNext: Signal → Direct DOM update

2. **Fine-Grained Reactivity**
   - React: Entire component re-renders
   - PyNext: Only affected expressions update

3. **O(1) Updates**
   - Changing one signal notifies only its subscribers
   - Not the entire component tree

### 4.3 Best Practices

```javascript
// GOOD: Use memos for expensive computations
const filtered = createMemo(() => 
    items().filter(x => x.active)
);

// GOOD: Batch multiple updates
batch(() => {
    count.set(1);
    name.set('Alice');
});

// GOOD: Use untrack for one-time reads
createEffect(() => {
    const initial = untrack(() => count());
    // effect only runs once
});

// GOOD: Use peek when you don't need reactivity
const currentValue = count.peek();

// BAD: Creating signals in effects
createEffect(() => {
    const temp = createSignal(0);  // Don't do this!
});

// BAD: Mutating signal values directly
const items = createSignal([1, 2]);
items().push(3);  // Won't trigger updates!
items.set([...items(), 3]);  // Do this instead
```

---

## 5. Debugging Guide

### 5.1 Common Issues

#### Effect Not Running

```javascript
// WRONG: Not calling signal
const count = createSignal(0);
createEffect(() => {
    console.log(count);  // Just the signal object, not tracked
});

// CORRECT: Call the signal
createEffect(() => {
    console.log(count());  // Reads value, creates subscription
});
```

#### Effect Runs Too Often

```javascript
// WRONG: Creating new object every time
const data = createSignal({ a: 1 });
data.set({ a: 1 });  // New object, triggers update!

// CORRECT: Use custom equality
const data = createSignal(
    { a: 1 },
    { equals: (a, b) => JSON.stringify(a) === JSON.stringify(b) }
);
```

#### Memory Leaks

```javascript
// WRONG: Not disposing effects
function MyComponent() {
    createEffect(() => { ... });  // Never cleaned up!
}

// CORRECT: Store and call dispose
function MyComponent() {
    const dispose = createEffect(() => { ... });
    return { destroy: dispose };
}
```

### 5.2 Debugging Tools

```javascript
// Log all signal reads
const count = createSignal(0);
const originalRead = count;
count = function() {
    console.log('Signal read:', originalRead());
    return originalRead();
};

// Track effect executions
let effectId = 0;
const originalEffect = createEffect;
createEffect = (fn) => {
    const id = ++effectId;
    return originalEffect(() => {
        console.log(`Effect ${id} running`);
        return fn();
    });
};
```

### 5.3 DevTools Integration

The runtime exposes debugging APIs on `window.PyNext`:

```javascript
// Access all registered signals
console.log(window.PyNext);

// In browser console
PyNext.createSignal(0);  // Create test signal
```

---

## Appendix: Complete Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>PyNext Todo App</title>
</head>
<body>
    <div id="app" data-pynext-component="TodoApp" data-pynext-id="todo">
        <input type="text" data-pynext-input="newText.set(e.target.value)">
        <button data-pynext-click="addTodo()">Add</button>
        <ul id="todo-list"></ul>
        <span data-pynext-text="remaining">0</span> items left
    </div>
    
    <script id="__PYNEXT_DATA__" type="application/json">
    {
        "components": {
            "todo": {
                "signals": { "newText": "" },
                "stores": { 
                    "todos": { "items": [] }
                }
            }
        }
    }
    </script>
    
    <script type="module">
        import { 
            createSignal, createStore, createMemo, createEffect,
            For, hydrate 
        } from '/_pynext/reactive.js';
        
        // Hydrate server-rendered content
        hydrate();
        
        // Additional client-side interactivity
        const todos = createStore({ items: [] });
        const newText = createSignal('');
        
        function addTodo() {
            if (newText()) {
                todos.items.push({
                    id: Date.now(),
                    text: newText(),
                    done: false
                });
                newText.set('');
            }
        }
        
        const remaining = createMemo(() => 
            todos.items.filter(t => !t.done).length
        );
        
        // Render list reactively
        For({
            each: () => todos.items,
            key: t => t.id,
            children: (todo) => {
                const li = document.createElement('li');
                li.textContent = todo.text;
                li.onclick = () => { todo.done = !todo.done; };
                return li;
            },
            parent: document.getElementById('todo-list')
        });
        
        // Update remaining count
        createEffect(() => {
            document.querySelector('[data-pynext-text="remaining"]')
                .textContent = remaining();
        });
        
        // Expose for hydration handlers
        window.addTodo = addTodo;
    </script>
</body>
</html>
```

---

*End of JavaScript Runtime Documentation*

