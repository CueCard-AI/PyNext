# State Management in PyNext

PyNext uses **SolidJS-inspired fine-grained reactivity** for state management. Unlike React's component-level re-renders, PyNext updates only the specific DOM nodes that depend on changed data.

## Table of Contents

- [Introduction to Fine-Grained Reactivity](#introduction-to-fine-grained-reactivity)
- [Signal - The Core Primitive](#signal---the-core-primitive)
- [Store - Nested Reactive State](#store---nested-reactive-state)
- [Computed/Memo - Derived State](#computedmemo---derived-state)
- [Effect - Side Effects](#effect---side-effects)
- [Batching Updates](#batching-updates)
- [Server-to-Client State Flow](#server-to-client-state-flow)
- [State Patterns](#state-patterns)
- [Comparison with Other Frameworks](#comparison-with-other-frameworks)
- [Performance Characteristics](#performance-characteristics)
- [API Reference](#api-reference)

---

## Introduction to Fine-Grained Reactivity

### What is Fine-Grained Reactivity?

Traditional frameworks like React use **coarse-grained reactivity**:
- State changes trigger component re-renders
- Virtual DOM diffing determines what changed
- Batched updates to the real DOM

PyNext uses **fine-grained reactivity** (like SolidJS):
- State changes notify only subscribed consumers
- Direct DOM updates without diffing
- Surgical precision updates

### Visual Comparison

```
COARSE-GRAINED (React)                 FINE-GRAINED (PyNext)
─────────────────────                  ─────────────────────

     State Change                           State Change
          │                                      │
          ▼                                      ▼
   ┌─────────────┐                      ┌─────────────────┐
   │ Re-render   │                      │ Signal notifies │
   │ Component   │                      │ subscribers     │
   └─────────────┘                      └─────────────────┘
          │                                      │
          ▼                                      │
   ┌─────────────┐                               │
   │ Create new  │                               │
   │ Virtual DOM │                               │
   └─────────────┘                               │
          │                                      │
          ▼                                      │
   ┌─────────────┐                               │
   │ Diff old vs │                               │
   │ new VDOM    │                               │
   └─────────────┘                               │
          │                                      │
          ▼                                      ▼
   ┌─────────────┐                      ┌─────────────────┐
   │ Patch real  │                      │ Update specific │
   │ DOM         │                      │ DOM node        │
   └─────────────┘                      └─────────────────┘

   Time: ~5-10ms                        Time: ~0.1-0.5ms
```

### Why Fine-Grained?

| Benefit | Description |
|---------|-------------|
| **Performance** | No virtual DOM overhead, direct updates |
| **Predictability** | Clear cause → effect relationship |
| **Scalability** | Performance doesn't degrade with component size |
| **Memory** | No virtual DOM tree in memory |
| **Debugging** | Easy to trace what caused an update |

---

## Signal - The Core Primitive

A **Signal** is a reactive container that holds a value and notifies subscribers when that value changes.

### Creating Signals

```python
from pynext import Signal

# Basic signal with initial value
count = Signal(0)
name = Signal("Alice")
is_active = Signal(True)
items = Signal([1, 2, 3])
user = Signal({"name": "Bob", "age": 30})

# Signal with explicit name (for debugging)
from pynext.core.signals import signal
temperature = signal(72.5, name="room_temperature")
```

### Reading Signal Values

```python
count = Signal(10)

# Call the signal to read its value
current_value = count()  # Returns: 10

# In templates/components
div()[
    span()[count],           # Renders: <span>10</span>
    span()[f"Count: {count()}"],  # Renders: <span>Count: 10</span>
]
```

### Writing Signal Values

```python
count = Signal(0)

# Direct set
count.set(5)

# Update based on current value
count.update(lambda x: x + 1)

# Multiple updates
count.set(10)
count.update(lambda x: x * 2)  # Now 20
```

### How Signals Work Internally

```
┌─────────────────────────────────────────────────────────────────┐
│                         Signal Internal                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   class Signal:                                                  │
│       _value: T              # Current value                     │
│       _id: str               # Unique identifier                 │
│       _subscribers: list     # Functions to call on change       │
│       _attribute_bindings    # DOM attributes bound to signal    │
│                                                                  │
│   ┌─────────────┐                                               │
│   │  count()    │ ──► Returns _value                            │
│   └─────────────┘                                               │
│                                                                  │
│   ┌─────────────┐     ┌──────────────────┐                     │
│   │ count.set() │ ──► │ _value = new     │                     │
│   └─────────────┘     │ _notify()        │                     │
│                       └────────┬─────────┘                     │
│                                │                                │
│                                ▼                                │
│                       ┌──────────────────┐                     │
│                       │ For each         │                     │
│                       │ subscriber:      │                     │
│                       │   subscriber()   │                     │
│                       └──────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Subscription System

```python
count = Signal(0)

# Manual subscription (rarely needed)
def on_count_change(new_value):
    print(f"Count changed to: {new_value}")

unsubscribe = count.subscribe(on_count_change)

count.set(5)   # Prints: "Count changed to: 5"
count.set(10)  # Prints: "Count changed to: 10"

# Unsubscribe when done
unsubscribe()
count.set(15)  # Nothing printed
```

### DOM Binding

When a signal is rendered in HTML, PyNext creates a binding:

```python
count = Signal(42)

# Python template
span()[count]

# Renders to HTML:
# <span data-signal="sig_abc123" id="sig_sig_abc123">42</span>

# When count.set(100) is called:
# JavaScript runtime finds element by data-signal attribute
# Updates textContent directly: element.textContent = "100"
```

### Signal in Attributes

```python
is_visible = Signal(True)
class_name = Signal("active")

div(
    class_=class_name,           # Reactive class
    hidden=is_visible,           # Reactive attribute  
)
```

### Memory Management

Signals are garbage collected when:
1. No more references in Python code
2. No DOM elements bound to them
3. No active subscriptions

```python
def create_counter():
    count = Signal(0)  # Created
    return div()[count]
    # Signal stays alive because DOM references it

# When component unmounts, signal can be GC'd
```

---

## Store - Nested Reactive State

A **Store** provides reactive access to nested objects with automatic tracking.

### Creating Stores

```python
from pynext import Store

# Simple store
user = Store({
    "name": "Alice",
    "email": "alice@example.com"
})

# Nested store
app_state = Store({
    "user": {
        "profile": {
            "name": "Bob",
            "avatar": "/img/bob.png"
        },
        "settings": {
            "theme": "dark",
            "notifications": True
        }
    },
    "cart": {
        "items": [],
        "total": 0
    }
})
```

### Reading Store Values

```python
user = Store({
    "name": "Alice",
    "settings": {"theme": "dark"}
})

# Dot notation (preferred)
user.name                  # "Alice"
user.settings.theme        # "dark"

# Bracket notation
user["name"]               # "Alice"
user["settings"]["theme"]  # "dark"

# Get entire store value
user()                     # {"name": "Alice", "settings": {"theme": "dark"}}
```

### Updating Store Values

```python
user = Store({
    "name": "Alice",
    "age": 25,
    "settings": {"theme": "dark"}
})

# Direct property assignment
user.name = "Bob"
user.age = 26
user.settings.theme = "light"

# Bracket notation
user["name"] = "Charlie"

# Update multiple properties
user.update({
    "name": "Diana",
    "age": 28
})
```

### How Stores Work (Proxy Chain)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Store Proxy Chain                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   app_state = Store({                                           │
│       "user": {                                                  │
│           "profile": { "name": "Alice" }                        │
│       }                                                          │
│   })                                                             │
│                                                                  │
│   app_state.user.profile.name                                   │
│        │      │       │     │                                   │
│        │      │       │     └── Read "name" from profile proxy  │
│        │      │       │                                         │
│        │      │       └── Returns Proxy wrapping profile object │
│        │      │                                                 │
│        │      └── Returns Proxy wrapping user object            │
│        │                                                        │
│        └── Root Store Proxy                                     │
│                                                                  │
│                                                                  │
│   Each level returns a Proxy that:                              │
│   • Tracks read access (for dependency tracking)                │
│   • Intercepts writes (for notification)                        │
│   • Wraps nested objects in new Proxies                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Array Handling in Stores

```python
todos = Store({
    "items": [
        {"id": 1, "text": "Learn PyNext", "done": False},
        {"id": 2, "text": "Build app", "done": False}
    ]
})

# Read array
todos.items              # List of todo objects
todos.items[0].text      # "Learn PyNext"
len(todos.items)         # 2

# Modify array items
todos.items[0].done = True

# Add to array
todos.items.append({"id": 3, "text": "Deploy", "done": False})

# Remove from array
todos.items.pop()

# Note: For complex array operations, consider
# wrapping the array in a Signal instead
items = Signal([...])
items.update(lambda arr: arr + [new_item])
```

### Store vs Signal: When to Use Which

| Use Case | Signal | Store |
|----------|--------|-------|
| Single value (number, string, bool) | ✅ | ❌ |
| Simple object | ✅ | ✅ |
| Deeply nested object | ❌ | ✅ |
| Array with frequent updates | ✅ | ⚠️ |
| Form with many fields | ⚠️ | ✅ |
| Configuration/settings | ⚠️ | ✅ |

---

## Computed/Memo - Derived State

**Computed** (also called **Memo**) creates a derived value that automatically updates when its dependencies change.

### Creating Computed Values

```python
from pynext import Signal, Computed, Memo

price = Signal(100)
quantity = Signal(2)
tax_rate = Signal(0.1)

# Using Computed
subtotal = Computed(lambda: price() * quantity())
tax = Computed(lambda: subtotal() * tax_rate())
total = Computed(lambda: subtotal() + tax())

# Using Memo (alias for Computed)
total_memo = Memo(lambda: price() * quantity() * (1 + tax_rate()))
```

### Automatic Dependency Tracking

```python
first_name = Signal("John")
last_name = Signal("Doe")
show_full = Signal(True)

# Dependencies are tracked automatically
display_name = Computed(lambda: 
    f"{first_name()} {last_name()}" if show_full() 
    else first_name()
)

# When show_full is True:
#   Dependencies: [first_name, last_name, show_full]
#   Changes to any will recompute

# When show_full is False:
#   Dependencies: [first_name, show_full]
#   last_name changes won't trigger recompute!
```

### Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    Computed Dependency Graph                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────┐   ┌──────────┐   ┌──────────┐                    │
│   │  price  │   │ quantity │   │ tax_rate │                    │
│   │ Signal  │   │  Signal  │   │  Signal  │                    │
│   └────┬────┘   └────┬─────┘   └────┬─────┘                    │
│        │             │              │                           │
│        └──────┬──────┘              │                           │
│               │                     │                           │
│               ▼                     │                           │
│        ┌────────────┐               │                           │
│        │  subtotal  │               │                           │
│        │  Computed  │◄──────────────┘                           │
│        │            │                                           │
│        │ price() *  │                                           │
│        │ quantity() │                                           │
│        └─────┬──────┘                                           │
│              │                                                   │
│              │      ┌──────────┐                                │
│              │      │ tax_rate │                                │
│              │      │  Signal  │                                │
│              │      └────┬─────┘                                │
│              │           │                                       │
│              ▼           ▼                                       │
│        ┌────────────────────┐                                   │
│        │        tax         │                                   │
│        │      Computed      │                                   │
│        │                    │                                   │
│        │ subtotal() *       │                                   │
│        │ tax_rate()         │                                   │
│        └─────────┬──────────┘                                   │
│                  │                                               │
│                  ▼                                               │
│        ┌────────────────────┐                                   │
│        │       total        │                                   │
│        │      Computed      │                                   │
│        │                    │                                   │
│        │ subtotal() + tax() │                                   │
│        └────────────────────┘                                   │
│                                                                  │
│   When price.set(200):                                          │
│   1. subtotal recomputes → 400                                  │
│   2. tax recomputes → 40                                        │
│   3. total recomputes → 440                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Lazy Evaluation

Computed values are **lazy** - they only compute when read:

```python
expensive = Computed(lambda: some_expensive_operation())

# Not computed yet!

value = expensive()  # NOW it computes

value2 = expensive()  # Returns cached value (no recompute)

dependency.set(new_value)  # Marks as dirty

value3 = expensive()  # Recomputes because dirty
```

### Caching Behavior

```python
call_count = 0

def compute_value():
    global call_count
    call_count += 1
    return a() + b()

result = Computed(compute_value)

result()  # call_count = 1
result()  # call_count = 1 (cached)
result()  # call_count = 1 (cached)

a.set(10)  # Invalidates cache

result()  # call_count = 2 (recomputes)
result()  # call_count = 2 (cached again)
```

---

## Effect - Side Effects

**Effects** run code in response to signal changes, with automatic dependency tracking.

### Creating Effects

```python
from pynext import Signal, Effect

count = Signal(0)

# Decorator style
@Effect
def log_count():
    print(f"Count is: {count()}")

# Runs immediately with count = 0
# Runs again whenever count changes
```

### Effect Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                       Effect Lifecycle                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   @Effect                                                        │
│   def my_effect():                                              │
│       # ... use signals ...                                     │
│       return cleanup_fn  # Optional                             │
│                                                                  │
│                                                                  │
│   ┌───────────────────────────────────────────────────────┐    │
│   │                   INITIAL RUN                          │    │
│   │                                                        │    │
│   │  1. Effect function executes                          │    │
│   │  2. Signal reads are tracked as dependencies          │    │
│   │  3. Optional cleanup function stored                  │    │
│   └───────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│   ┌───────────────────────────────────────────────────────┐    │
│   │                  DEPENDENCY CHANGE                     │    │
│   │                                                        │    │
│   │  1. If cleanup exists, run it                         │    │
│   │  2. Clear old dependencies                            │    │
│   │  3. Re-run effect function                            │    │
│   │  4. Track new dependencies                            │    │
│   │  5. Store new cleanup (if returned)                   │    │
│   └───────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│   ┌───────────────────────────────────────────────────────┐    │
│   │                     DISPOSAL                           │    │
│   │                                                        │    │
│   │  1. Run cleanup if exists                             │    │
│   │  2. Remove from all dependency subscription lists     │    │
│   │  3. Mark effect as disposed                           │    │
│   └───────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cleanup Functions

```python
from pynext import Signal, Effect

interval_ms = Signal(1000)

@Effect
def setup_timer():
    ms = interval_ms()
    
    # Setup
    timer_id = set_interval(tick, ms)
    print(f"Timer started with {ms}ms interval")
    
    # Return cleanup function
    def cleanup():
        clear_interval(timer_id)
        print("Timer stopped")
    
    return cleanup

# When interval_ms changes:
# 1. cleanup() called (stops old timer)
# 2. Effect re-runs (starts new timer)
```

### Dependency Tracking in Effects

```python
show_details = Signal(False)
user_id = Signal(1)
user_data = Signal(None)

@Effect
def fetch_user():
    if show_details():
        # Only tracks user_id when show_details is True
        uid = user_id()
        # fetch user data...
        user_data.set(fetched_data)

# When show_details is False:
#   Effect only depends on: [show_details]
#   Changes to user_id don't trigger re-run

# When show_details is True:
#   Effect depends on: [show_details, user_id]
#   Changes to either trigger re-run
```

### Effect vs Computed

| Aspect | Effect | Computed |
|--------|--------|----------|
| **Purpose** | Side effects (API calls, DOM manipulation) | Derived values |
| **Return value** | Optional cleanup function | Computed value |
| **When runs** | Immediately + on changes | Lazily, when read |
| **Caching** | No | Yes |
| **Use case** | Logging, fetching, subscriptions | Transforming data |

---

## Batching Updates

Multiple signal updates can be batched to prevent intermediate re-renders.

### Using batch()

```python
from pynext import Signal, batch

first_name = Signal("John")
last_name = Signal("Doe")
age = Signal(25)

# Without batching: 3 separate updates, 3 re-renders
first_name.set("Jane")
last_name.set("Smith")
age.set(30)

# With batching: 1 re-render after all updates
def update_user():
    first_name.set("Jane")
    last_name.set("Smith")
    age.set(30)

batch(update_user)
```

### How Batching Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Without Batching                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   first_name.set("Jane")                                        │
│        │                                                         │
│        └──► Notify subscribers ──► DOM Update 1                 │
│                                                                  │
│   last_name.set("Smith")                                        │
│        │                                                         │
│        └──► Notify subscribers ──► DOM Update 2                 │
│                                                                  │
│   age.set(30)                                                   │
│        │                                                         │
│        └──► Notify subscribers ──► DOM Update 3                 │
│                                                                  │
│   Total: 3 notification cycles, 3 DOM updates                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      With Batching                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   batch(lambda: (                                               │
│       first_name.set("Jane"),                                   │
│       last_name.set("Smith"),  ──► Queue notifications         │
│       age.set(30)                                               │
│   ))                                                             │
│        │                                                         │
│        └──► Process queue ──► Single DOM Update                 │
│                                                                  │
│   Total: 1 notification cycle, 1 DOM update                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Server-to-Client State Flow

Understanding how state moves from Python to the browser is crucial.

### The Hydration Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. SERVER RENDER (Python)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   count = Signal(0)                                             │
│   name = Signal("Alice")                                        │
│                                                                  │
│   @page                                                          │
│   def my_page():                                                │
│       return div()[                                              │
│           span()[count],                                        │
│           span()[name],                                         │
│           button(onclick=lambda: count.update(x: x+1))["+"]    │
│       ]                                                          │
│                                                                  │
│   # RenderContext tracks:                                       │
│   # - signals: {id, value, element_id}                          │
│   # - events: {element_id: {event_type: handler_code}}         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. HTML OUTPUT                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   <div id="__pynext">                                           │
│     <span data-signal="sig_001" id="sig_sig_001">0</span>       │
│     <span data-signal="sig_002" id="sig_sig_002">Alice</span>   │
│     <button id="el_btn_001">+</button>                          │
│   </div>                                                        │
│                                                                  │
│   <script>                                                       │
│   window.__PYNEXT_HYDRATION__ = {                               │
│     "renderId": "abc123",                                       │
│     "signals": {                                                │
│       "sig_001": {"id": "sig_001", "value": 0, "elementId": "sig_sig_001"},
│       "sig_002": {"id": "sig_002", "value": "Alice", "elementId": "sig_sig_002"}
│     },                                                          │
│     "events": {                                                 │
│       "el_btn_001": {                                           │
│         "click": "__pynext__.getSignal('sig_001').update(v => v + 1)"
│       }                                                         │
│     }                                                           │
│   };                                                            │
│   </script>                                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 3. CLIENT HYDRATION (JavaScript)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   // signals.js runs on page load                               │
│                                                                  │
│   function hydrate() {                                          │
│     const data = window.__PYNEXT_HYDRATION__;                   │
│                                                                  │
│     // Recreate signals                                         │
│     for (const [id, info] of Object.entries(data.signals)) {   │
│       createSignal(id, info.value);                             │
│     }                                                           │
│                                                                  │
│     // Attach event handlers                                    │
│     for (const [elemId, handlers] of Object.entries(data.events)) {
│       const el = document.getElementById(elemId);               │
│       for (const [event, code] of Object.entries(handlers)) {  │
│         el.addEventListener(event, new Function('event', code));│
│       }                                                         │
│     }                                                           │
│   }                                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. INTERACTIVE (Runtime)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   // User clicks button                                         │
│   // Handler runs: __pynext__.getSignal('sig_001').update(...)  │
│                                                                  │
│   // Signal updates value: 0 → 1                                │
│   // Signal notifies subscribers                                │
│   // DOM binding updates:                                       │
│   //   document.querySelector('[data-signal="sig_001"]')        │
│   //     .textContent = '1';                                    │
│                                                                  │
│   // Result: <span data-signal="sig_001">1</span>               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### SSR Considerations

**Signal values are serialized at render time:**
```python
count = Signal(0)

@page
def my_page():
    # count() returns 0 during SSR
    # This value is embedded in HTML
    return div()[count]

# If count.set(5) happens after render starts,
# HTML will still show 0, but hydration data has 5
```

**Best Practice: Initialize signals before render:**
```python
# Good - signal value is stable during render
count = Signal(initial_value)

@page
def my_page():
    return div()[count]
```

---

## State Patterns

### Pattern 1: Local Component State

State that belongs to a single component:

```python
@component
def Counter():
    # Local state - created fresh each time component renders
    count = Signal(0)
    
    return div()[
        span()[count],
        button(onclick=lambda: count.update(lambda x: x + 1))["+"]
    ]

# Each Counter instance has its own count
div()[
    Counter(),  # count = 0
    Counter(),  # count = 0 (separate signal)
]
```

### Pattern 2: Module-Level Shared State

State shared across components:

```python
# state.py
from pynext import Signal, Store

# Shared across all components that import this
current_user = Signal(None)
theme = Signal("light")
notifications = Signal([])

app_config = Store({
    "api_url": "https://api.example.com",
    "features": {
        "dark_mode": True,
        "beta": False
    }
})
```

```python
# components/header.py
from state import current_user, theme

@component
def Header():
    return header()[
        span()[f"Welcome, {current_user().name if current_user() else 'Guest'}"],
        button(onclick=lambda: theme.set("dark" if theme() == "light" else "light"))[
            "Toggle Theme"
        ]
    ]
```

```python
# pages/profile.py
from state import current_user

@page
def profile():
    return div()[
        h1()[current_user().name],
        # Changes here update Header too!
    ]
```

### Pattern 3: State Factory

Create isolated state instances:

```python
def create_counter_state(initial=0):
    count = Signal(initial)
    
    def increment():
        count.update(lambda x: x + 1)
    
    def decrement():
        count.update(lambda x: x - 1)
    
    def reset():
        count.set(initial)
    
    return {
        "count": count,
        "increment": increment,
        "decrement": decrement,
        "reset": reset,
    }

# Usage
counter1 = create_counter_state(0)
counter2 = create_counter_state(100)

@component
def DualCounter():
    return div()[
        div()[
            span()[counter1["count"]],
            button(onclick=counter1["increment"])["+"]
        ],
        div()[
            span()[counter2["count"]],
            button(onclick=counter2["increment"])["+"]
        ]
    ]
```

### Pattern 4: Derived State Composition

```python
# Base state
cart_items = Signal([
    {"id": 1, "name": "Widget", "price": 10, "qty": 2},
    {"id": 2, "name": "Gadget", "price": 25, "qty": 1},
])

discount_percent = Signal(10)
tax_rate = Signal(0.08)

# Derived state (auto-updates)
subtotal = Computed(lambda: 
    sum(item["price"] * item["qty"] for item in cart_items())
)

discount = Computed(lambda: 
    subtotal() * (discount_percent() / 100)
)

subtotal_after_discount = Computed(lambda: 
    subtotal() - discount()
)

tax = Computed(lambda: 
    subtotal_after_discount() * tax_rate()
)

total = Computed(lambda: 
    subtotal_after_discount() + tax()
)

# Usage
@component
def CartSummary():
    return div(class_="cart-summary")[
        div()[f"Subtotal: ${subtotal():.2f}"],
        div()[f"Discount ({discount_percent()}%): -${discount():.2f}"],
        div()[f"Tax: ${tax():.2f}"],
        div(class_="total")[f"Total: ${total():.2f}"],
    ]
```

---

## Comparison with Other Frameworks

### PyNext vs React

| Aspect | React | PyNext |
|--------|-------|--------|
| State unit | `useState` hook | `Signal` |
| Updates trigger | Component re-render | DOM node update |
| Derived state | `useMemo` with deps | `Computed` (auto-deps) |
| Side effects | `useEffect` with deps | `Effect` (auto-deps) |
| Nested state | Spread operators / Immer | `Store` with Proxy |
| Batching | Automatic in event handlers | Explicit `batch()` |
| Memory | Virtual DOM overhead | Direct references |

### PyNext vs Vue 3

| Aspect | Vue 3 | PyNext |
|--------|-------|--------|
| Reactivity | `ref()`, `reactive()` | `Signal`, `Store` |
| Auto-unwrap | In templates | Call signal: `count()` |
| Computed | `computed()` | `Computed()` |
| Watch | `watch()`, `watchEffect()` | `Effect` |
| Template syntax | Vue SFC | Python functions |

### PyNext vs Svelte

| Aspect | Svelte | PyNext |
|--------|--------|--------|
| Reactivity | `$:` statements | Explicit signals |
| State | `let x = 0` | `x = Signal(0)` |
| Derived | `$: doubled = x * 2` | `doubled = Computed(...)` |
| Stores | `writable()` | `Signal`, `Store` |
| Compilation | Compiler transforms | Runtime system |

---

## Performance Characteristics

### Update Timing

| Operation | Typical Time |
|-----------|-------------|
| Signal read | ~0.01ms |
| Signal write | ~0.05ms |
| DOM update (single node) | ~0.1ms |
| Computed recalc (simple) | ~0.02ms |
| Effect run | ~0.1-1ms |
| React component re-render | ~5-50ms |

### Memory Usage

```
Signal:
  ~100 bytes base
  + value size
  + 50 bytes per subscriber

Store:
  ~200 bytes base
  + object size
  + Proxy overhead (~50 bytes per nested level)

Computed:
  ~150 bytes base
  + cached value size
  + dependency tracking (~20 bytes per dep)
```

### Scaling Characteristics

```
┌─────────────────────────────────────────────────────────────────┐
│                    Update Time vs Component Size                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Time                                                            │
│   ▲                                                              │
│   │                                           React              │
│   │                                        .-·´                  │
│   │                                    .-·´                      │
│   │                                .-·´                          │
│   │                            .-·´                              │
│   │                        .-·´                                  │
│   │                    .-·´                                      │
│   │       ─────────────────────────────────────── PyNext        │
│   │                                                              │
│   └────────────────────────────────────────────────────►        │
│                    Component Size (DOM nodes)                    │
│                                                                  │
│   PyNext: O(1) - Only affected nodes update                     │
│   React:  O(n) - Virtual DOM diff scales with size              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Signal

```python
class Signal(Generic[T]):
    def __init__(self, initial_value: T, name: Optional[str] = None)
    def __call__(self) -> T                    # Read value
    def set(self, value: T) -> None            # Set value
    def update(self, fn: Callable[[T], T]) -> None  # Update via function
    def subscribe(self, fn: Callable[[T], None]) -> Callable[[], None]  # Returns unsubscribe
```

### Store

```python
class Store(Generic[T]):
    def __init__(self, initial_value: T, name: Optional[str] = None)
    def __call__(self) -> T                    # Get entire value
    def __getattr__(self, name: str) -> Any    # Dot access
    def __setattr__(self, name: str, value: Any) -> None
    def __getitem__(self, key: str) -> Any     # Bracket access
    def __setitem__(self, key: str, value: Any) -> None
    def update(self, updates: dict) -> None    # Batch update
    def subscribe(self, fn: Callable[[T], None]) -> Callable[[], None]
```

### Computed / Memo

```python
class Computed(Generic[T]):
    def __init__(self, fn: Callable[[], T], name: Optional[str] = None)
    def __call__(self) -> T                    # Get computed value
    def invalidate(self) -> None               # Force recalculation

Memo = Computed  # Alias
```

### Effect

```python
class Effect:
    def __init__(
        self, 
        fn: Optional[Callable[[], Optional[Callable[[], None]]]] = None,
        *, 
        js_code: Optional[str] = None
    )
    def __call__(self, fn) -> "Effect"         # Use as decorator
    def dispose(self) -> None                  # Clean up effect
```

### batch

```python
def batch(fn: Callable[[], None]) -> None
```

### Helper Functions

```python
def signal(value: T, name: Optional[str] = None) -> Signal[T]
def computed(fn: Callable[[], T], name: Optional[str] = None) -> Computed[T]
def effect(fn: Callable[[], Optional[Callable[[], None]]]) -> Effect
def store(value: T, name: Optional[str] = None) -> Store[T]
```

---

## Next Steps

- **[State + Data Integration](STATE_DATA_INTEGRATION.md)** - How Signals work with Server Actions & API Routes
- [State Patterns](STATE_PATTERNS.md) for advanced patterns
- [React Integration](REACT_INTEGRATION.md) for using React components
- See the [Example App](../example/) for complete usage examples

