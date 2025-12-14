# PyNext Unified Reactive System Specification

> **Version:** 1.0.0  
> **Status:** Draft  
> **Last Updated:** December 2024

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Design Principles](#2-design-principles)
3. [Core Primitives](#3-core-primitives)
4. [Control Flow Components](#4-control-flow-components)
5. [Hydration Protocol](#5-hydration-protocol)
6. [Compilation Boundaries](#6-compilation-boundaries)
7. [API Reference](#7-api-reference)
8. [Examples](#8-examples)
9. [Performance Guarantees](#9-performance-guarantees)
10. [Error Handling](#10-error-handling)

---

## 1. Executive Summary

### 1.1 What is PyNext Reactive?

PyNext Reactive is a **fine-grained reactivity system** for Python web applications that achieves performance faster than both React.js and Next.js by using SolidJS optimization principles:

- **No Virtual DOM** - Updates happen directly on the DOM nodes that changed
- **Fine-grained tracking** - Only the exact expressions that depend on changed data re-run
- **Compile-time optimization** - Python reactive code compiles to minimal JavaScript
- **O(1) updates** - Updating one item in a 10,000-item list takes constant time

### 1.2 Why Does It Exist?

| Problem with React/Next.js | PyNext Solution |
|---------------------------|-----------------|
| Virtual DOM diffing is O(n) | Direct DOM updates are O(1) |
| Component re-renders cascade | Only affected expressions update |
| 40KB+ runtime | < 5KB runtime |
| Hydration mismatch errors | Unified server/client model |
| Complex hooks rules | Simple read/write API |
| JavaScript-only | Write Python, runs everywhere |

### 1.3 Who Is It For?

**Primary Audience:**
- Python developers building web applications
- Teams wanting React-like DX without JavaScript complexity
- Applications requiring high performance (dashboards, real-time apps)

**Prerequisites:**
- Basic Python knowledge (functions, classes, decorators)
- Basic HTML/CSS understanding
- No JavaScript knowledge required (framework handles compilation)

### 1.4 Performance Targets

| Metric | React/Next.js | PyNext Target | Improvement |
|--------|---------------|---------------|-------------|
| Initial render | 50-100ms | < 20ms | 2.5-5x faster |
| Update 1 item in 1000-item list | 10-50ms | < 1ms | 10-50x faster |
| Memory per component | 1-2KB | < 200 bytes | 5-10x smaller |
| Runtime bundle | ~40KB | < 5KB | 8x smaller |
| Hydration time | 100-500ms | < 50ms | 2-10x faster |

---

## 2. Design Principles

### 2.1 SolidJS Optimization Principles

PyNext adopts the core innovations from SolidJS that make it faster than React:

#### 2.1.1 Fine-Grained Reactivity

```
React (Virtual DOM):
┌─────────────────────────────────────────────────────────┐
│  User clicks button                                      │
│           ↓                                              │
│  setState({count: 1})                                    │
│           ↓                                              │
│  Entire component re-renders                             │
│           ↓                                              │
│  Virtual DOM diff (compare old tree vs new tree)         │
│           ↓                                              │
│  Patch real DOM with differences                         │
│                                                          │
│  Time: O(n) where n = component tree size                │
└─────────────────────────────────────────────────────────┘

PyNext (Fine-Grained):
┌─────────────────────────────────────────────────────────┐
│  User clicks button                                      │
│           ↓                                              │
│  count.set(1)                                            │
│           ↓                                              │
│  Signal notifies only subscribed DOM nodes               │
│           ↓                                              │
│  Exact text node updates: "0" → "1"                      │
│                                                          │
│  Time: O(1) constant time                                │
└─────────────────────────────────────────────────────────┘
```

#### 2.1.2 No Virtual DOM

React creates a virtual representation of the DOM and diffs it on every update. PyNext skips this entirely:

- **React:** Component → Virtual DOM → Diff → Real DOM
- **PyNext:** Signal change → Direct DOM update

#### 2.1.3 Compile-Time Optimization

PyNext compiles Python reactive code to optimized JavaScript at build time:

```python
# Python (what you write)
count = signal(0)
button(onclick=lambda: count.set(count() + 1))[count()]
```

```javascript
// JavaScript (what runs in browser)
const count = createSignal(0);
const _btn = document.createElement("button");
_btn.addEventListener("click", () => count.set(count() + 1));
createEffect(() => _btn.textContent = count());
```

### 2.2 Pythonic API Design

The API is designed to feel natural to Python developers:

#### 2.2.1 Objects, Not Tuples

```python
# SolidJS pattern (tuple unpacking - feels foreign in Python)
count, setCount = createSignal(0)
setCount(5)

# PyNext pattern (object with methods - feels Pythonic)
count = signal(0)
count.set(5)
```

#### 2.2.2 Decorators for Effects

```python
# Natural Python pattern using decorators
@effect
def log_changes():
    print(f"Count changed to: {count()}")
```

#### 2.2.3 Callable for Reading

```python
# Reading a signal uses function call syntax
current_value = count()  # Parentheses = "get current value"
```

### 2.3 AI-Friendly Code Patterns

The codebase is designed to be easily understood by LLMs:

#### 2.3.1 Explicit Over Implicit

```python
# GOOD: Explicit and clear
count = signal(0)           # Create a signal with initial value 0
current = count()           # Read the current value
count.set(5)               # Set to a new value
count.set(count() + 1)     # Update based on current value

# AVOIDED: Magic or implicit behavior
count += 1                  # This does NOT work - no operator overloading
```

#### 2.3.2 Consistent Naming

| Concept | Name | Why |
|---------|------|-----|
| Reactive value | `signal` | Signals changes to subscribers |
| Side effect | `effect` | Causes effects when dependencies change |
| Cached value | `memo` | Memoizes (caches) computation |
| Deep reactive | `store` | Stores complex state |

#### 2.3.3 Predictable Behavior

- Reading a signal always returns the current value
- Setting a signal always notifies subscribers (unless value unchanged)
- Effects always run after all signals in a batch are updated
- Memos always cache until a dependency changes

---

## 3. Core Primitives

### 3.1 signal(initial) - Reactive Values

#### What

A `signal` is a container for a reactive value. When the value changes, all code that reads the signal automatically re-runs.

#### When to Use

Use `signal` when you have a value that:
- Changes over time
- Should trigger UI updates when it changes
- Needs to be read from multiple places

#### Why It's Fast

- Signals use **fine-grained subscriptions** - only code that actually reads the signal subscribes
- Updates are **O(1)** - changing a signal only notifies its direct subscribers
- No diffing or reconciliation needed

#### How to Use

```python
from pynext.reactive import signal

# ═══════════════════════════════════════════════════════════════════════════
# CREATION
# ═══════════════════════════════════════════════════════════════════════════

# Create a signal with an initial value
count = signal(0)           # Integer
name = signal("Alice")      # String
items = signal([1, 2, 3])   # List (reference - use store for deep reactivity)
user = signal(None)         # None (will be set later)

# ═══════════════════════════════════════════════════════════════════════════
# READING
# ═══════════════════════════════════════════════════════════════════════════

# Call the signal to read its current value
current_count = count()     # Returns: 0
current_name = name()       # Returns: "Alice"

# Reading in an effect/memo automatically subscribes
@effect
def log_count():
    print(count())          # Automatically re-runs when count changes

# ═══════════════════════════════════════════════════════════════════════════
# WRITING
# ═══════════════════════════════════════════════════════════════════════════

# Set a new value directly
count.set(5)                # count() is now 5

# Set based on current value
count.set(count() + 1)      # Increment

# Functional update (safer for async)
count.update(lambda x: x + 1)

# ═══════════════════════════════════════════════════════════════════════════
# READING WITHOUT SUBSCRIBING
# ═══════════════════════════════════════════════════════════════════════════

# peek() reads without creating a subscription
@effect
def conditional_effect():
    if should_track():
        print(count())      # Subscribes to count
    else:
        print(count.peek()) # Does NOT subscribe to count
```

#### Complete API

```python
class Signal[T]:
    """A reactive value container with automatic dependency tracking."""
    
    def __init__(self, initial: T, *, equals: Callable[[T, T], bool] = None):
        """
        Create a new signal.
        
        Args:
            initial: The initial value
            equals: Optional custom equality function. If provided, subscribers
                   are only notified when equals(old, new) returns False.
                   Default: operator.eq (==)
        
        Examples:
            count = signal(0)
            name = signal("Alice")
            
            # Custom equality (e.g., for objects)
            user = signal(User("Alice"), equals=lambda a, b: a.id == b.id)
        """
    
    def __call__(self) -> T:
        """
        Read the current value and subscribe to changes.
        
        When called inside an effect or memo, creates a subscription.
        When the signal's value changes, the effect/memo will re-run.
        
        Returns:
            The current value
        
        Examples:
            count = signal(0)
            value = count()  # Returns 0, subscribes if in reactive context
        """
    
    def set(self, value: T) -> None:
        """
        Set a new value and notify subscribers.
        
        Subscribers are only notified if the new value differs from
        the current value (according to the equals function).
        
        Args:
            value: The new value to set
        
        Examples:
            count.set(5)           # Set to 5
            count.set(count() + 1) # Increment
        """
    
    def update(self, fn: Callable[[T], T]) -> None:
        """
        Update the value using a function.
        
        This is safer than set(signal() + 1) in async contexts because
        it always operates on the current value at update time.
        
        Args:
            fn: A function that receives the current value and returns the new value
        
        Examples:
            count.update(lambda x: x + 1)  # Increment
            count.update(lambda x: x * 2)  # Double
        """
    
    def peek(self) -> T:
        """
        Read the current value WITHOUT subscribing.
        
        Use this when you need the current value but don't want
        the enclosing effect/memo to re-run when this signal changes.
        
        Returns:
            The current value
        
        Examples:
            @effect
            def log_when_enabled():
                if is_enabled():
                    # Only rerun when is_enabled changes, not when count changes
                    print(f"Count is {count.peek()}")
        """
```

#### Edge Cases and Gotchas

```python
# ═══════════════════════════════════════════════════════════════════════════
# GOTCHA 1: Signals contain references, not deep copies
# ═══════════════════════════════════════════════════════════════════════════

items = signal([1, 2, 3])
items().append(4)          # WRONG! Mutates the list but doesn't notify
items.set([1, 2, 3, 4])    # CORRECT! Creates new reference, notifies

# For deep reactivity, use store instead:
items = store({"list": [1, 2, 3]})
items.list.append(4)       # Works! Store tracks deep mutations

# ═══════════════════════════════════════════════════════════════════════════
# GOTCHA 2: Reading in a loop creates one subscription, not N
# ═══════════════════════════════════════════════════════════════════════════

@effect
def log_many():
    for i in range(10):
        print(count())     # Only ONE subscription created, not 10

# ═══════════════════════════════════════════════════════════════════════════
# GOTCHA 3: Conditionally reading may not subscribe
# ═══════════════════════════════════════════════════════════════════════════

@effect
def conditional():
    if show_count():
        print(count())     # Only subscribes to count when show_count() is True
    # If show_count() returns False, count is never read, no subscription

# ═══════════════════════════════════════════════════════════════════════════
# GOTCHA 4: Setting same value doesn't notify
# ═══════════════════════════════════════════════════════════════════════════

count = signal(5)
count.set(5)               # No notification - value unchanged

# Custom equality changes this behavior:
count = signal(5, equals=lambda a, b: False)  # Always notify
count.set(5)               # Now notifies even though value is "same"
```

---

### 3.2 effect(fn) - Side Effects

#### What

An `effect` is a function that runs whenever its dependencies change. Dependencies are automatically tracked - any signal read inside the effect body becomes a dependency.

#### When to Use

Use `effect` when you need to:
- Update the DOM based on signal changes
- Log or debug signal values
- Sync state to external systems (localStorage, APIs)
- Trigger side effects (network requests, timers)

#### Why It's Fast

- **Auto-tracking** - No manual dependency arrays like React's useEffect
- **Glitch-free** - Effects run after all signals in a batch are updated
- **Efficient cleanup** - Old effects are disposed before new ones run

#### How to Use

```python
from pynext.reactive import signal, effect

count = signal(0)

# ═══════════════════════════════════════════════════════════════════════════
# BASIC EFFECT
# ═══════════════════════════════════════════════════════════════════════════

# Decorator syntax (preferred)
@effect
def log_count():
    print(f"Count is: {count()}")

# Runs immediately with: "Count is: 0"
count.set(5)  # Runs again: "Count is: 5"

# ═══════════════════════════════════════════════════════════════════════════
# EFFECT WITH CLEANUP
# ═══════════════════════════════════════════════════════════════════════════

@effect
def setup_timer():
    interval = setInterval(lambda: print(f"Tick: {count()}"), 1000)
    
    # Return a cleanup function - runs before next execution or on disposal
    def cleanup():
        clearInterval(interval)
    return cleanup

# ═══════════════════════════════════════════════════════════════════════════
# INLINE EFFECT
# ═══════════════════════════════════════════════════════════════════════════

# Function syntax (for simple cases)
dispose = effect(lambda: print(f"Count: {count()}"))

# Later: manually dispose if needed
dispose()

# ═══════════════════════════════════════════════════════════════════════════
# EFFECT WITH MULTIPLE DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════

first_name = signal("John")
last_name = signal("Doe")

@effect
def log_full_name():
    # Automatically tracks both first_name and last_name
    print(f"Full name: {first_name()} {last_name()}")

first_name.set("Jane")  # Triggers effect
last_name.set("Smith")  # Triggers effect again
```

#### Complete API

```python
def effect(fn: Callable[[], Optional[Callable[[], None]]]) -> Callable[[], None]:
    """
    Create a reactive effect that re-runs when dependencies change.
    
    Args:
        fn: A function to run. The function is called immediately and then
            re-called whenever any signal it reads changes. If the function
            returns a cleanup function, that cleanup is called before the
            next execution and when the effect is disposed.
    
    Returns:
        A dispose function that stops the effect from running.
    
    Examples:
        # Basic effect
        @effect
        def log():
            print(count())
        
        # Effect with cleanup
        @effect
        def timer():
            id = setInterval(tick, 1000)
            return lambda: clearInterval(id)
        
        # Inline effect
        dispose = effect(lambda: print(count()))
        dispose()  # Stop the effect
    """

# Can also be used as a decorator
@effect
def my_effect():
    # effect body
    pass
```

#### Cleanup Patterns

```python
# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 1: Timer cleanup
# ═══════════════════════════════════════════════════════════════════════════

@effect
def polling():
    interval_id = setInterval(fetch_data, delay())
    return lambda: clearInterval(interval_id)

# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 2: Event listener cleanup
# ═══════════════════════════════════════════════════════════════════════════

@effect
def resize_handler():
    def on_resize():
        width.set(window.innerWidth)
    
    window.addEventListener("resize", on_resize)
    return lambda: window.removeEventListener("resize", on_resize)

# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 3: Subscription cleanup
# ═══════════════════════════════════════════════════════════════════════════

@effect
def websocket():
    ws = WebSocket(url())
    ws.onmessage = lambda msg: messages.update(lambda m: m + [msg])
    return lambda: ws.close()

# ═══════════════════════════════════════════════════════════════════════════
# PATTERN 4: Abort controller for fetch
# ═══════════════════════════════════════════════════════════════════════════

@effect
async def fetch_user():
    controller = AbortController()
    try:
        response = await fetch(f"/api/users/{user_id()}", signal=controller.signal)
        data.set(await response.json())
    except AbortError:
        pass  # Request was cancelled
    return lambda: controller.abort()
```

---

### 3.3 memo(fn) - Computed Values

#### What

A `memo` is a cached computation that only re-runs when its dependencies change. Unlike effects, memos are **lazy** - they don't compute until read.

#### When to Use

Use `memo` when you have a computation that:
- Derives from one or more signals
- Is expensive to compute
- Is read from multiple places
- Should be cached until dependencies change

#### Why It's Fast

- **Lazy evaluation** - Doesn't compute until first read
- **Caching** - Returns cached value if dependencies unchanged
- **Fine-grained** - Only recomputes when direct dependencies change

#### How to Use

```python
from pynext.reactive import signal, memo

# ═══════════════════════════════════════════════════════════════════════════
# BASIC MEMO
# ═══════════════════════════════════════════════════════════════════════════

count = signal(0)

# Create a memoized computation
doubled = memo(lambda: count() * 2)

# Read the memoized value (computes on first read)
print(doubled())  # Output: 0

count.set(5)
print(doubled())  # Output: 10 (recomputed because count changed)
print(doubled())  # Output: 10 (cached - count hasn't changed)

# ═══════════════════════════════════════════════════════════════════════════
# EXPENSIVE COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════

items = signal([1, 2, 3, 4, 5, ..., 10000])
filter_text = signal("")

# This expensive filter only runs when items or filter_text changes
filtered = memo(lambda: [
    item for item in items()
    if filter_text().lower() in item.name.lower()
])

# ═══════════════════════════════════════════════════════════════════════════
# CHAINED MEMOS
# ═══════════════════════════════════════════════════════════════════════════

count = signal(0)
doubled = memo(lambda: count() * 2)
quadrupled = memo(lambda: doubled() * 2)  # Depends on doubled memo

print(quadrupled())  # 0
count.set(5)
print(quadrupled())  # 20

# ═══════════════════════════════════════════════════════════════════════════
# MEMO VS EFFECT
# ═══════════════════════════════════════════════════════════════════════════

# MEMO: For computed values (lazy, cached, returns value)
total = memo(lambda: sum(prices()))

# EFFECT: For side effects (eager, no caching, no return value)
@effect
def update_title():
    document.title = f"Total: {total()}"
```

#### Complete API

```python
def memo(
    fn: Callable[[], T],
    *,
    equals: Callable[[T, T], bool] = None
) -> Callable[[], T]:
    """
    Create a memoized computation that caches its result.
    
    The computation function is called lazily (on first read) and then
    only re-called when one of its dependencies changes. Results are
    cached between calls.
    
    Args:
        fn: A function that computes and returns a value. Any signals
            read inside this function become dependencies.
        equals: Optional custom equality function. If provided, downstream
                subscribers are only notified when equals(old, new) is False.
                Default: operator.eq (==)
    
    Returns:
        A function that returns the memoized value.
    
    Examples:
        doubled = memo(lambda: count() * 2)
        print(doubled())  # Computes and caches
        print(doubled())  # Returns cached value
    """
```

---

### 3.4 store(obj) - Deep Reactive Objects

#### What

A `store` is a deeply reactive object that tracks changes at any level of nesting. Unlike signals (which only track the top-level reference), stores track property access and mutation at every depth.

#### When to Use

Use `store` when you have:
- Nested objects or arrays
- Complex state that needs deep tracking
- Lists that need add/remove/reorder operations
- State that should update when any nested property changes

#### Why It's Fast

- **Proxy-based** - Uses JavaScript Proxy for efficient interception
- **Path tracking** - Only notifies listeners subscribed to changed paths
- **Batched mutations** - Multiple mutations in one tick are batched

#### How to Use

```python
from pynext.reactive import store

# ═══════════════════════════════════════════════════════════════════════════
# BASIC STORE
# ═══════════════════════════════════════════════════════════════════════════

# Create a store with nested data
todos = store({
    "items": [
        {"id": 1, "text": "Learn PyNext", "done": False},
        {"id": 2, "text": "Build app", "done": False},
    ],
    "filter": "all"
})

# ═══════════════════════════════════════════════════════════════════════════
# READING
# ═══════════════════════════════════════════════════════════════════════════

# Access properties directly (subscribes to that path)
print(todos.filter)           # "all"
print(todos.items[0].text)    # "Learn PyNext"
print(len(todos.items))       # 2

# ═══════════════════════════════════════════════════════════════════════════
# WRITING
# ═══════════════════════════════════════════════════════════════════════════

# Set properties directly (notifies subscribers)
todos.filter = "active"
todos.items[0].done = True

# Array mutations work naturally
todos.items.append({"id": 3, "text": "Deploy", "done": False})
todos.items.pop()
del todos.items[0]

# ═══════════════════════════════════════════════════════════════════════════
# EFFECTS WITH STORES
# ═══════════════════════════════════════════════════════════════════════════

@effect
def log_filter():
    print(f"Filter: {todos.filter}")  # Only runs when filter changes

@effect
def log_first_item():
    print(f"First: {todos.items[0].text}")  # Only runs when first item's text changes

@effect
def log_count():
    print(f"Count: {len(todos.items)}")  # Runs when items added/removed
```

#### Complete API

```python
def store(initial: dict | list) -> StoreProxy:
    """
    Create a deeply reactive store from an object or array.
    
    The returned proxy intercepts all property access and mutation,
    enabling fine-grained reactivity at any depth.
    
    Args:
        initial: The initial data structure (dict or list)
    
    Returns:
        A reactive proxy that tracks access and mutation
    
    Examples:
        todos = store({"items": [], "filter": "all"})
        todos.items.append({"text": "New todo"})
        todos.filter = "active"
    """

class StoreProxy:
    """A proxy wrapper that enables deep reactivity."""
    
    def __getattr__(self, key: str) -> Any:
        """Get a property, creating subscription to that path."""
    
    def __setattr__(self, key: str, value: Any) -> None:
        """Set a property, notifying subscribers to that path."""
    
    def __getitem__(self, index: int) -> Any:
        """Get an array item, creating subscription."""
    
    def __setitem__(self, index: int, value: Any) -> None:
        """Set an array item, notifying subscribers."""
    
    def __delitem__(self, index: int) -> None:
        """Delete an array item, notifying subscribers."""
    
    def __len__(self) -> int:
        """Get length, creating subscription to length changes."""
    
    def __iter__(self) -> Iterator:
        """Iterate over items, creating subscription."""
```

#### Store vs Signal

```python
# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL: For simple values or immutable updates
# ═══════════════════════════════════════════════════════════════════════════

count = signal(0)
count.set(count() + 1)  # Simple value

items = signal([1, 2, 3])
items.set([*items(), 4])  # Immutable update (creates new list)

# ═══════════════════════════════════════════════════════════════════════════
# STORE: For mutable nested data
# ═══════════════════════════════════════════════════════════════════════════

todos = store({"items": []})
todos.items.append({"text": "New"})  # Mutable update (modifies in place)
todos.items[0].done = True           # Deep update
```

---

## 4. Control Flow Components

Control flow components enable conditional and list rendering with optimal performance.

### 4.1 Show(when, fallback) - Conditional Rendering

```python
from pynext.reactive import signal, Show

is_logged_in = signal(False)

# Render content conditionally
Show(when=lambda: is_logged_in())[
    "Welcome back!"
]

# With fallback content
Show(when=lambda: is_logged_in(), fallback="Please log in")[
    "Welcome back!"
]
```

### 4.2 For(each, key) - List Rendering

```python
from pynext.reactive import store, For
from pynext.core.html import div, li

todos = store({"items": [
    {"id": 1, "text": "Learn PyNext"},
    {"id": 2, "text": "Build app"},
]})

# Render a list with keyed reconciliation
For(each=lambda: todos.items, key=lambda item: item["id"])[
    lambda item: li()[item["text"]]
]
```

### 4.3 Index(each) - Index-Based Lists

```python
from pynext.reactive import signal, Index

numbers = signal([1, 2, 3, 4, 5])

# When you need the index and don't have unique keys
Index(each=lambda: numbers())[
    lambda item, index: div()[f"{index}: {item}"]
]
```

### 4.4 Switch/Match - Multi-Branch Conditionals

```python
from pynext.reactive import signal, Switch, Match

status = signal("loading")

Switch()[
    Match(when=lambda: status() == "loading")[
        "Loading..."
    ],
    Match(when=lambda: status() == "error")[
        "Error occurred"
    ],
    Match(when=lambda: status() == "success")[
        "Data loaded!"
    ],
]
```

### 4.5 Portal(mount) - Render Outside Tree

```python
from pynext.reactive import Portal

# Render modal content into document.body
Portal(mount="body")[
    div(class_="modal")[
        "Modal content"
    ]
]
```

### 4.6 ErrorBoundary(fallback) - Error Handling

```python
from pynext.reactive import ErrorBoundary

ErrorBoundary(fallback=lambda error: div()[f"Error: {error}"])[
    RiskyComponent()
]
```

---

## 5. Hydration Protocol

See [HYDRATION_PROTOCOL.md](./HYDRATION_PROTOCOL.md) for the complete specification.

### 5.1 Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HYDRATION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   SERVER                              CLIENT                             │
│   ──────                              ──────                             │
│                                                                          │
│   1. Python renders                                                      │
│      component tree                                                      │
│            ↓                                                             │
│   2. Generate HTML with                                                  │
│      data-pynext-* attrs     ──────────────────▶  4. Parse HTML         │
│            ↓                                             ↓               │
│   3. Serialize state to                          5. Load JS runtime     │
│      JSON in <script>        ──────────────────▶        ↓               │
│                                                  6. hydrate() connects   │
│                                                     signals to DOM       │
│                                                          ↓               │
│                                                  7. Attach event         │
│                                                     handlers             │
│                                                          ↓               │
│                                                  8. Interactive!         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Server Output Format

```html
<!-- Server-rendered HTML -->
<div data-pynext-component="Counter">
  <span data-pynext-text="count">0</span>
  <button data-pynext-click="count.set(count()+1)">+</button>
</div>

<script id="__PYNEXT_DATA__" type="application/json">
{
  "signals": {
    "count": 0
  }
}
</script>
```

### 5.3 Client Hydration

```javascript
// Client-side hydration (runtime does this automatically)
import { hydrate } from '/_pynext/reactive.js';

hydrate(document.querySelector('[data-pynext-component]'));
```

---

## 6. Compilation Boundaries

See [COMPILATION_GUIDE.md](./COMPILATION_GUIDE.md) for the complete specification.

### 6.1 What Compiles to JavaScript

| Python Code | Compiles? | JavaScript Output |
|-------------|-----------|-------------------|
| `count()` | Yes | `count()` |
| `count.set(5)` | Yes | `count.set(5)` |
| `count() + 1` | Yes | `count() + 1` |
| `f"Value: {count()}"` | Yes | `` `Value: ${count()}` `` |
| `lambda: count.set(0)` | Yes | `() => count.set(0)` |
| `if count() > 0:` | Yes | `if (count() > 0)` |
| `[x * 2 for x in items()]` | Yes | `items().map(x => x * 2)` |

### 6.2 What Stays Server-Only

| Python Code | Why Server-Only |
|-------------|-----------------|
| Database queries | Requires server access |
| File I/O | No filesystem in browser |
| `import os` | System access |
| Custom classes | Complex compilation |
| Generators | No direct JS equivalent |

### 6.3 Compilation Markers

```python
from pynext.reactive import island, server

# This component compiles to JavaScript
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))[count()]

# This code runs only on the server
@server
def fetch_user(user_id: int):
    return db.query(User).get(user_id)
```

---

## 7. API Reference

### 7.1 Core Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `signal` | `signal(initial: T) -> Signal[T]` | Create a reactive value |
| `effect` | `effect(fn: () -> None) -> () -> None` | Create a side effect |
| `memo` | `memo(fn: () -> T) -> () -> T` | Create a memoized value |
| `store` | `store(initial: dict) -> StoreProxy` | Create a deep reactive store |
| `batch` | `batch(fn: () -> None) -> None` | Batch multiple updates |
| `untrack` | `untrack(fn: () -> T) -> T` | Read without subscribing |

### 7.2 Control Flow

| Component | Props | Description |
|-----------|-------|-------------|
| `Show` | `when`, `fallback` | Conditional rendering |
| `For` | `each`, `key`, `fallback` | Keyed list rendering |
| `Index` | `each`, `fallback` | Index-based list rendering |
| `Switch` | children: `Match[]` | Multi-branch conditional |
| `Match` | `when` | Branch of Switch |
| `Portal` | `mount` | Render to different target |
| `ErrorBoundary` | `fallback` | Catch rendering errors |

### 7.3 Lifecycle

| Function | Signature | Description |
|----------|-----------|-------------|
| `onMount` | `onMount(fn: () -> None)` | Run after DOM insertion |
| `onCleanup` | `onCleanup(fn: () -> None)` | Run before disposal |

---

## 8. Examples

### 8.1 Counter (Minimal)

```python
from pynext.reactive import signal, island
from pynext.core.html import div, button, span

@island
def Counter():
    count = signal(0)
    
    return div(class_="counter")[
        button(onclick=lambda: count.set(count() - 1))["-"],
        span()[count()],
        button(onclick=lambda: count.set(count() + 1))["+"],
    ]
```

### 8.2 Todo List

```python
from pynext.reactive import signal, store, memo, island, Show, For
from pynext.core.html import div, input_, button, ul, li, span

@island
def TodoApp():
    todos = store({"items": [], "next_id": 1})
    new_text = signal("")
    
    def add_todo():
        if new_text():
            todos.items.append({
                "id": todos.next_id,
                "text": new_text(),
                "done": False
            })
            todos.next_id += 1
            new_text.set("")
    
    def toggle(todo_id):
        for item in todos.items:
            if item["id"] == todo_id:
                item["done"] = not item["done"]
                break
    
    remaining = memo(lambda: sum(1 for t in todos.items if not t["done"]))
    
    return div(class_="todo-app")[
        div(class_="input-row")[
            input_(
                type="text",
                value=new_text(),
                oninput=lambda e: new_text.set(e.target.value),
                placeholder="What needs to be done?"
            ),
            button(onclick=add_todo)["Add"],
        ],
        
        Show(when=lambda: len(todos.items) > 0)[
            ul(class_="todo-list")[
                For(each=lambda: todos.items, key=lambda t: t["id"])[
                    lambda todo: li(class_="done" if todo["done"] else "")[
                        input_(
                            type="checkbox",
                            checked=todo["done"],
                            onchange=lambda: toggle(todo["id"])
                        ),
                        span()[todo["text"]],
                    ]
                ]
            ],
            div(class_="footer")[
                f"{remaining()} items remaining"
            ]
        ],
    ]
```

### 8.3 Dashboard (Complex State)

```python
from pynext.reactive import signal, store, memo, effect, island, Show, For
from pynext.core.html import div, h1, h2, section

@island
def Dashboard():
    # Multiple signals for different UI concerns
    theme = signal("dark")
    sidebar_open = signal(True)
    
    # Store for complex nested data
    data = store({
        "users": [],
        "stats": {"total": 0, "active": 0},
        "loading": True,
        "error": None,
    })
    
    # Derived values
    active_users = memo(lambda: [u for u in data.users if u["active"]])
    
    # Side effect for data fetching
    @effect
    async def fetch_data():
        data.loading = True
        try:
            response = await fetch("/api/dashboard")
            result = await response.json()
            data.users = result["users"]
            data.stats = result["stats"]
        except Exception as e:
            data.error = str(e)
        finally:
            data.loading = False
    
    return div(class_=f"dashboard {theme()}")[
        section(class_="sidebar" if sidebar_open() else "sidebar collapsed")[
            # Sidebar content
        ],
        
        section(class_="main")[
            h1()["Dashboard"],
            
            Show(when=lambda: data.loading, fallback=
                Show(when=lambda: data.error, fallback=
                    div()[
                        h2()[f"Active Users: {len(active_users())}"],
                        For(each=active_users, key=lambda u: u["id"])[
                            lambda user: UserCard(user=user)
                        ]
                    ]
                )[
                    div(class_="error")[data.error]
                ]
            )[
                div(class_="loading")["Loading..."]
            ],
        ],
    ]
```

---

## 9. Performance Guarantees

### 9.1 Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Signal read | O(1) | Direct value access |
| Signal write | O(k) | k = number of subscribers |
| Effect execution | O(1) | Per effect, not per signal |
| Memo cache hit | O(1) | Direct value return |
| Memo recompute | O(f) | f = computation cost |
| Store property access | O(1) | Proxy interception |
| Store deep update | O(k) | k = path subscribers |
| For reconciliation | O(n) | n = list length, with LIS optimization |

### 9.2 Memory Usage

| Primitive | Memory | Notes |
|-----------|--------|-------|
| Signal | ~100 bytes | Value + subscriber set |
| Effect | ~200 bytes | Function + dependency set |
| Memo | ~200 bytes | Function + cached value + deps |
| Store (per path) | ~50 bytes | Proxy overhead per path |

### 9.3 Bundle Size

| Component | Size (gzipped) |
|-----------|---------------|
| Core runtime | ~2KB |
| Control flow | ~1KB |
| Hydration | ~1KB |
| Router | ~1KB |
| **Total** | **< 5KB** |

---

## 10. Error Handling

### 10.1 Signal Errors

```python
count = signal(0)

# Error: Setting wrong type (optional type checking)
count.set("not a number")  # TypeError if type hints enabled

# Error: Reading disposed signal
del count
count()  # SignalDisposedError
```

### 10.2 Effect Errors

```python
@effect
def faulty():
    if count() > 10:
        raise ValueError("Count too high")

# Errors in effects propagate to ErrorBoundary or global handler
```

### 10.3 Store Errors

```python
todos = store({"items": []})

# Error: Accessing non-existent path
todos.nonexistent.property  # KeyError

# Error: Mutating after disposal
del todos
todos.items.append({})  # StoreDisposedError
```

### 10.4 Compilation Errors

```python
@island
def Invalid():
    import os  # CompilationError: Cannot import 'os' in island
    
    class Foo:  # CompilationError: Cannot define class in island
        pass
```

---

## Appendix A: Comparison with React

| Concept | React | PyNext |
|---------|-------|--------|
| State | `useState(0)` | `signal(0)` |
| Side effects | `useEffect(() => {}, [deps])` | `@effect` (auto-tracked) |
| Memoization | `useMemo(() => val, [deps])` | `memo(lambda: val)` (auto-tracked) |
| Complex state | `useReducer` / Redux / Zustand | `store({...})` |
| Conditional | `{condition && <Comp />}` | `Show(when=condition)[Comp()]` |
| Lists | `{items.map(item => ...)}` | `For(each=items)[lambda item: ...]` |
| Context | `createContext` + `useContext` | `createContext` + `useContext` |

---

## Appendix B: Comparison with SolidJS

| Concept | SolidJS | PyNext |
|---------|---------|--------|
| State | `createSignal(0)` → `[get, set]` | `signal(0)` → object with `.set()` |
| Effects | `createEffect(() => ...)` | `@effect` decorator |
| Memos | `createMemo(() => ...)` | `memo(lambda: ...)` |
| Stores | `createStore({...})` | `store({...})` |
| Show | `<Show when={...}>` | `Show(when=...)[]` |
| For | `<For each={...}>` | `For(each=...)[]` |
| Compilation | Babel plugin | Python AST → JS |

---

*End of Specification*

