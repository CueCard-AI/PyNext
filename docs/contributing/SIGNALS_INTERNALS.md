# Signals Internals

> **The heartbeat of PyNext reactivity — how changes automatically propagate through your app**

This document explains how PyNext's signal system works under the hood, enabling fine-grained reactivity without the overhead of virtual DOM diffing.

---

## Overview

### What Problem Does This Solve?

Traditional frameworks (like React) re-render entire component trees when state changes. PyNext uses **signals** to update only the exact DOM nodes that depend on changed values.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REACT vs PYNEXT REACTIVITY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  REACT (Virtual DOM):                                                        │
│  ────────────────────                                                       │
│  1. State changes                                                            │
│  2. Re-render entire component tree                                          │
│  3. Create new virtual DOM                                                   │
│  4. Diff old vs new virtual DOM                                              │
│  5. Apply minimal patches to real DOM                                        │
│                                                                              │
│  PYNEXT (Signals):                                                           │
│  ─────────────────                                                          │
│  1. Signal value changes                                                     │
│  2. Effects that read this signal re-run                                     │
│  3. DOM updates directly (no diffing)                                        │
│                                                                              │
│  Result: Faster, more predictable, less memory                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL SYSTEM ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     subscribes      ┌──────────────┐                      │
│  │    Signal    │ ←───────────────── │    Effect    │                      │
│  │  (reactive   │                     │  (side       │                      │
│  │   value)     │ ────────────────→  │   effect)    │                      │
│  └──────────────┘     notifies        └──────────────┘                      │
│         │                                    │                               │
│         │ derived from                       │ can modify                    │
│         ▼                                    ▼                               │
│  ┌──────────────┐                     ┌──────────────┐                      │
│  │   Computed   │                     │     DOM      │                      │
│  │  (derived    │                     │   Updates    │                      │
│  │   value)     │                     │              │                      │
│  └──────────────┘                     └──────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Data Structures

```javascript
// In signals.js

// The currently executing effect (for dependency tracking)
let currentEffect = null;

// Batch updates for performance
let pendingEffects = new Set();
let isBatching = false;

// Signal class
class Signal {
  constructor(initialValue) {
    this._value = initialValue;
    this._subscribers = new Set();
  }
  
  get value() {
    // Track dependency if inside an effect
    if (currentEffect) {
      this._subscribers.add(currentEffect);
    }
    return this._value;
  }
  
  set value(newValue) {
    if (this._value !== newValue) {
      this._value = newValue;
      this._notify();
    }
  }
  
  _notify() {
    for (const effect of this._subscribers) {
      scheduleEffect(effect);
    }
  }
}
```

---

## How Dependency Tracking Works

### The Magic of Auto-Tracking

When you read a signal inside an effect, PyNext automatically tracks that dependency:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY TRACKING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Python Code:                                                                │
│  ────────────                                                               │
│  count = Signal(0)                                                           │
│                                                                              │
│  @client_effect                                                              │
│  def update_display():                                                       │
│      # Reading count.value HERE registers the dependency                     │
│      element.textContent = str(count.value)                                  │
│                                                                              │
│  Execution Flow:                                                             │
│  ───────────────                                                            │
│  1. Effect starts running                                                    │
│     currentEffect = update_display                                           │
│                                                                              │
│  2. Effect reads count.value                                                 │
│     Signal.get() sees currentEffect is set                                   │
│     Signal adds update_display to its subscribers                            │
│                                                                              │
│  3. Effect finishes                                                          │
│     currentEffect = null                                                     │
│                                                                              │
│  4. Later: count.value = 5                                                   │
│     Signal notifies all subscribers                                          │
│     update_display runs again                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JavaScript Implementation

```javascript
function createEffect(fn) {
  const effect = () => {
    // Clear old dependencies
    cleanup(effect);
    
    // Track new dependencies during execution
    currentEffect = effect;
    try {
      fn();
    } finally {
      currentEffect = null;
    }
  };
  
  // Run immediately to establish initial dependencies
  effect();
  
  return effect;
}
```

---

## Effect Scheduling

### Why Batch Updates?

Without batching, multiple signal changes would cause multiple DOM updates:

```javascript
// Without batching - BAD
count.value = 1;  // Effect runs, DOM updates
count.value = 2;  // Effect runs again, DOM updates again
count.value = 3;  // Effect runs AGAIN, DOM updates AGAIN

// With batching - GOOD
batch(() => {
  count.value = 1;  // Queued
  count.value = 2;  // Queued
  count.value = 3;  // Queued
});
// Effect runs ONCE with final value, DOM updates ONCE
```

### Implementation

```javascript
function scheduleEffect(effect) {
  pendingEffects.add(effect);
  
  if (!isBatching) {
    // Flush on next microtask (after current JS execution)
    queueMicrotask(flushEffects);
  }
}

function flushEffects() {
  const effects = [...pendingEffects];
  pendingEffects.clear();
  
  for (const effect of effects) {
    effect();
  }
}

function batch(fn) {
  isBatching = true;
  try {
    fn();
  } finally {
    isBatching = false;
    flushEffects();
  }
}
```

---

## Computed Values

### How Computed Works

A computed value is a signal that derives from other signals:

```python
# Python
count = Signal(0)
doubled = Computed(lambda: count.value * 2)
```

```javascript
// JavaScript equivalent
class Computed {
  constructor(fn) {
    this._fn = fn;
    this._value = undefined;
    this._dirty = true;
    this._subscribers = new Set();
    
    // Create an effect that runs the compute function
    this._effect = createEffect(() => {
      this._dirty = true;
      this._notify();
    });
  }
  
  get value() {
    // Track dependency
    if (currentEffect) {
      this._subscribers.add(currentEffect);
    }
    
    // Lazy evaluation - only compute when accessed
    if (this._dirty) {
      this._value = this._fn();
      this._dirty = false;
    }
    
    return this._value;
  }
}
```

### Lazy Evaluation

Computed values are **lazy** — they only recalculate when accessed:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LAZY EVALUATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  count = Signal(0)                                                           │
│  doubled = Computed(lambda: count.value * 2)                                 │
│  tripled = Computed(lambda: count.value * 3)                                 │
│                                                                              │
│  count.value = 5                                                             │
│  # doubled and tripled are marked dirty, but NOT recalculated yet!           │
│                                                                              │
│  print(doubled.value)  # NOW it calculates: 5 * 2 = 10                       │
│  # tripled is STILL not calculated                                           │
│                                                                              │
│  Why? Because if tripled is never read, why waste CPU calculating it?        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## DOM Updates

### How Signals Update the DOM

When PyNext renders, it creates effects that bind signals to DOM nodes:

```javascript
// Simplified hydration
function hydrateText(element, signalId) {
  const signal = __pynext__.signals[signalId];
  
  createEffect(() => {
    element.textContent = signal.value;
  });
}

function hydrateAttribute(element, attrName, signalId) {
  const signal = __pynext__.signals[signalId];
  
  createEffect(() => {
    element.setAttribute(attrName, signal.value);
  });
}
```

### Fine-Grained Updates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FINE-GRAINED DOM UPDATES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  <div>                                                                       │
│    <h1>Hello, {name}</h1>          ← Effect: update h1.textContent           │
│    <p>Count: {count}</p>           ← Effect: update p.textContent            │
│    <button class="{btnClass}">     ← Effect: update button.className         │
│      Click me                                                                │
│    </button>                                                                 │
│  </div>                                                                      │
│                                                                              │
│  When name.value changes:                                                    │
│  - ONLY h1's textContent effect runs                                         │
│  - p and button are NOT touched                                              │
│                                                                              │
│  When count.value changes:                                                   │
│  - ONLY p's textContent effect runs                                          │
│  - h1 and button are NOT touched                                             │
│                                                                              │
│  No tree diffing, no reconciliation, no wasted work!                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Comparison to React/SolidJS

### React's Virtual DOM

```javascript
// React re-renders component on ANY state change
function Counter() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState("John");
  
  // Entire function re-runs when count OR name changes
  return (
    <div>
      <h1>Hello, {name}</h1>
      <p>Count: {count}</p>
    </div>
  );
}
```

### SolidJS (PyNext's Inspiration)

```javascript
// SolidJS only updates what changed
function Counter() {
  const [count, setCount] = createSignal(0);
  const [name, setName] = createSignal("John");
  
  // Function runs ONCE at setup
  // Signals create fine-grained subscriptions
  return (
    <div>
      <h1>Hello, {name()}</h1>
      <p>Count: {count()}</p>
    </div>
  );
}
```

### PyNext

```python
# PyNext works like SolidJS but in Python
count = Signal(0)
name = Signal("John")

# Template runs once, creates subscriptions
div()[
    h1()[f"Hello, {name.value}"],
    p()[f"Count: {count.value}"]
]
```

---

## Debugging Tips

### Common Issues

#### 1. Effect Not Running

```python
# WRONG: Reading outside effect
value = signal.value  # Captured once, not reactive

def update():
    element.textContent = value  # Always shows old value

# RIGHT: Read inside effect
@client_effect
def update():
    element.textContent = signal.value  # Reactive!
```

#### 2. Infinite Loop

```python
# WRONG: Effect modifies signal it reads
count = Signal(0)

@client_effect
def bad_effect():
    count.value = count.value + 1  # Infinite loop!

# RIGHT: Use separate signals
count = Signal(0)
display = Signal("")

@client_effect  
def good_effect():
    display.value = f"Count: {count.value}"  # No loop
```

### Debug Mode

In development, enable signal debugging:

```javascript
// In browser console
__pynext__.debug = true;

// Now you'll see:
// [PyNext Signal] "count" changed: 0 → 1
// [PyNext Effect] Running effect #3
// [PyNext DOM] Updated <p> textContent
```

---

## Performance Characteristics

| Operation | Time Complexity | Notes |
|-----------|-----------------|-------|
| Signal read | O(1) | Just return value |
| Signal write | O(n) | n = number of subscribers |
| Effect registration | O(1) | Add to Set |
| Computed read (cached) | O(1) | Return cached value |
| Computed read (dirty) | O(compute) | Run compute function |
| Batch flush | O(n) | n = number of pending effects |

---

## Key Files

| File | Purpose |
|------|---------|
| `pynext/runtime/signals.js` | Core signal implementation |
| `pynext/core/signals.py` | Python Signal/Computed classes |
| `pynext/runtime/hydrate.js` | Connects signals to DOM |

---

## Further Reading

- [SolidJS Reactivity](https://www.solidjs.com/guides/reactivity) — PyNext's inspiration
- [Fine-Grained Reactivity](https://dev.to/ryansolid/a-hands-on-introduction-to-fine-grained-reactivity-3ndf) — Deep dive by SolidJS creator

