# PyNext AI Assistant Guide

> **Purpose:** Help LLMs understand, assist with, and debug PyNext reactive code  
> **Version:** 1.0.0  
> **Last Updated:** December 2024

---

## Table of Contents

1. [Quick Reference](#1-quick-reference)
2. [Code Patterns](#2-code-patterns)
3. [Debugging Guide](#3-debugging-guide)
4. [Common Errors and Fixes](#4-common-errors-and-fixes)
5. [Extension Points](#5-extension-points)
6. [Prompt Templates](#6-prompt-templates)

---

## 1. Quick Reference

### 1.1 Core API Summary

```python
# SIGNALS - Reactive values
count = signal(0)           # Create with initial value
value = count()             # Read (tracks dependency)
count.set(5)               # Write (notifies subscribers)
count.update(lambda x: x+1) # Update with function
count.peek()               # Read without tracking

# EFFECTS - Side effects that auto-track
@effect
def log_count():
    print(count())         # Runs when count changes

# MEMOS - Cached computations
doubled = memo(lambda: count() * 2)  # Only recomputes when count changes

# STORES - Deep reactive objects
todos = store({"items": []})
todos.items.append({"text": "New"})  # Triggers reactivity

# CONTROL FLOW
Show(when=lambda: count() > 0)["Content"]
For(each=lambda: items, key=lambda x: x.id)[lambda item: li()[item.text]]
Switch()[Match(when=lambda: status == "loading")["Loading..."]]
```

### 1.2 Import Statement

```python
from pynext.reactive import (
    signal, effect, memo, store, batch, untrack,
    Show, For, Index, Switch, Match, Portal, ErrorBoundary,
    island, server, onMount, onCleanup
)
from pynext.core.html import div, span, button, input_, ul, li, form
```

### 1.3 Key Rules

| Rule | Correct | Incorrect |
|------|---------|-----------|
| Read signal | `count()` | `count` |
| Write signal | `count.set(5)` | `count = 5` |
| Track in effect | `@effect def fn(): print(count())` | Reads automatically tracked |
| Avoid tracking | `count.peek()` or `untrack(lambda: count())` | - |
| Mutate store | `todos.items.append(x)` | Works directly |
| Mutate signal list | `items.set([*items(), x])` | `items().append(x)` won't notify |

---

## 2. Code Patterns

### 2.1 Counter Component

```python
from pynext.reactive import signal, island
from pynext.core.html import div, button, span

@island
def Counter():
    # State
    count = signal(0)
    
    # UI
    return div(class_="counter")[
        button(onclick=lambda: count.set(count() - 1))["-"],
        span()[count()],
        button(onclick=lambda: count.set(count() + 1))["+"],
    ]
```

### 2.2 Todo List

```python
from pynext.reactive import signal, store, memo, island, Show, For
from pynext.core.html import div, input_, button, ul, li, span

@island
def TodoApp():
    # State
    todos = store({"items": [], "next_id": 1})
    new_text = signal("")
    
    # Actions
    def add_todo():
        if new_text():
            todos.items.append({
                "id": todos.next_id,
                "text": new_text(),
                "done": False
            })
            todos.next_id += 1
            new_text.set("")
    
    def toggle_todo(todo_id):
        for item in todos.items:
            if item["id"] == todo_id:
                item["done"] = not item["done"]
                break
    
    # Derived state
    remaining = memo(lambda: sum(1 for t in todos.items if not t["done"]))
    
    # UI
    return div(class_="todo-app")[
        # Input row
        div(class_="input-row")[
            input_(
                type="text",
                value=new_text(),
                oninput=lambda e: new_text.set(e.target.value),
                placeholder="What needs to be done?"
            ),
            button(onclick=add_todo)["Add"],
        ],
        
        # List
        Show(when=lambda: len(todos.items) > 0)[
            ul()[
                For(each=lambda: todos.items, key=lambda t: t["id"])[
                    lambda todo: li(
                        class_="done" if todo["done"] else "",
                        onclick=lambda: toggle_todo(todo["id"])
                    )[todo["text"]]
                ]
            ],
            div()[f"{remaining()} items left"],
        ],
    ]
```

### 2.3 Form with Validation

```python
from pynext.reactive import signal, memo, island
from pynext.core.html import form, div, input_, button, span

@island
def ContactForm():
    # Form state
    name = signal("")
    email = signal("")
    message = signal("")
    submitted = signal(False)
    
    # Validation
    is_valid = memo(lambda: (
        len(name()) >= 2 and
        "@" in email() and
        len(message()) >= 10
    ))
    
    errors = memo(lambda: {
        "name": "" if len(name()) >= 2 else "Name too short",
        "email": "" if "@" in email() else "Invalid email",
        "message": "" if len(message()) >= 10 else "Message too short",
    })
    
    # Submit handler
    def handle_submit(e):
        e.preventDefault()
        if is_valid():
            # Send to server via server action
            submitted.set(True)
    
    # UI
    return form(onsubmit=handle_submit)[
        div()[
            input_(
                type="text",
                value=name(),
                oninput=lambda e: name.set(e.target.value),
                placeholder="Name"
            ),
            Show(when=lambda: errors()["name"])[
                span(class_="error")[errors()["name"]]
            ],
        ],
        div()[
            input_(
                type="email",
                value=email(),
                oninput=lambda e: email.set(e.target.value),
                placeholder="Email"
            ),
            Show(when=lambda: errors()["email"])[
                span(class_="error")[errors()["email"]]
            ],
        ],
        div()[
            textarea(
                value=message(),
                oninput=lambda e: message.set(e.target.value),
                placeholder="Message"
            ),
            Show(when=lambda: errors()["message"])[
                span(class_="error")[errors()["message"]]
            ],
        ],
        button(type="submit", disabled=not is_valid())["Send"],
    ]
```

### 2.4 Data Fetching

```python
from pynext.reactive import signal, effect, island, Show
from pynext.core.html import div, ul, li

@island
def UserList():
    # State
    users = signal([])
    loading = signal(True)
    error = signal(None)
    
    # Fetch on mount
    @effect
    async def fetch_users():
        loading.set(True)
        error.set(None)
        try:
            response = await fetch("/api/users")
            data = await response.json()
            users.set(data)
        except Exception as e:
            error.set(str(e))
        finally:
            loading.set(False)
    
    # UI
    return div()[
        Show(when=lambda: loading())[
            div()["Loading..."]
        ],
        Show(when=lambda: error())[
            div(class_="error")[error()]
        ],
        Show(when=lambda: not loading() and not error())[
            ul()[
                For(each=users, key=lambda u: u["id"])[
                    lambda user: li()[user["name"]]
                ]
            ]
        ],
    ]
```

### 2.5 Theme Toggle

```python
from pynext.reactive import signal, effect, island
from pynext.core.html import button

@island
def ThemeToggle():
    # State
    dark = signal(False)
    
    # Sync with DOM
    @effect
    def apply_theme():
        if dark():
            document.body.classList.add("dark")
        else:
            document.body.classList.remove("dark")
    
    # UI
    return button(onclick=lambda: dark.set(not dark()))[
        "🌙" if dark() else "☀️"
    ]
```

---

## 3. Debugging Guide

### 3.1 Tracing Reactivity

```python
from pynext.reactive import signal, effect

count = signal(0)

# Add logging to trace updates
@effect
def debug_count():
    print(f"[DEBUG] count changed to: {count()}")

# Now any count.set() will log
count.set(5)  # Prints: [DEBUG] count changed to: 5
```

### 3.2 Finding Why Effect Doesn't Run

```python
# PROBLEM: Effect doesn't re-run when expected

# CHECK 1: Is the signal being read inside the effect?
count = signal(0)

@effect
def broken():
    value = count  # WRONG: Not reading, just referencing
    print(value)

@effect
def fixed():
    value = count()  # CORRECT: Calling to read
    print(value)

# CHECK 2: Is the signal read conditionally?
@effect
def conditional():
    if some_other_signal():
        print(count())  # Only subscribes when condition is True
```

### 3.3 Finding Why Effect Runs Too Often

```python
# PROBLEM: Effect runs more than expected

# CHECK 1: Are you setting same value?
count = signal(5)
count.set(5)  # Should NOT trigger (same value)

# CHECK 2: Are you creating new objects?
items = signal([1, 2, 3])
items.set([1, 2, 3])  # TRIGGERS (new list object, different reference)

# FIX: Use custom equality
items = signal([1, 2, 3], equals=lambda a, b: a == b)
items.set([1, 2, 3])  # Now won't trigger

# CHECK 3: Are you reading too many signals?
@effect
def too_broad():
    # This subscribes to ALL items, not just filtered
    filtered = [x for x in items() if x > 0]
    print(filtered)
```

### 3.4 Memory Leak Detection

```python
# PROBLEM: Effects not cleaning up

# CHECK 1: Return cleanup function
@effect
def leaky():
    interval = setInterval(tick, 1000)
    # No cleanup! Interval runs forever

@effect
def clean():
    interval = setInterval(tick, 1000)
    return lambda: clearInterval(interval)  # Proper cleanup

# CHECK 2: Dispose effects when done
dispose = effect(lambda: print(count()))
# ... later ...
dispose()  # Clean up the effect
```

---

## 4. Common Errors and Fixes

### 4.1 Signal Not Updating

```python
# ERROR: UI doesn't update when signal changes

# CAUSE 1: Not calling signal to read
div()[count]      # WRONG
div()[count()]    # CORRECT

# CAUSE 2: Mutating instead of setting
items = signal([1, 2])
items().append(3)  # WRONG: Mutates list, no notification
items.set([*items(), 3])  # CORRECT: New reference

# CAUSE 3: Using store syntax with signal
data = signal({"x": 1})
data()["x"] = 2   # WRONG: Mutating
data.set({**data(), "x": 2})  # CORRECT

# OR use store for deep reactivity
data = store({"x": 1})
data.x = 2        # CORRECT with store
```

### 4.2 Infinite Loop

```python
# ERROR: Maximum update depth exceeded

# CAUSE: Setting signal in effect that reads it
count = signal(0)

@effect
def infinite():
    print(count())
    count.set(count() + 1)  # Triggers itself!

# FIX 1: Use condition
@effect
def bounded():
    if count() < 10:
        count.set(count() + 1)

# FIX 2: Use batch
@effect
def batched():
    batch(lambda: count.set(count() + 1))

# FIX 3: Use untrack for the read
@effect
def untracked():
    val = untrack(lambda: count())  # Don't subscribe
    count.set(val + 1)              # Set doesn't re-trigger
```

### 4.3 Stale Closure

```python
# ERROR: Handler uses old value

# CAUSE: Lambda captures value at creation time
count = signal(0)

# WRONG: Captures count() at button creation
button(onclick=lambda: alert(count()))  # Always shows 0

# The above is actually CORRECT in PyNext because count() is called
# inside the lambda, not outside. But here's the anti-pattern:

current = count()  # Captured outside
button(onclick=lambda: alert(current))  # Always shows 0

# CORRECT: Read inside handler
button(onclick=lambda: alert(count()))  # Shows current value
```

### 4.4 List Key Issues

```python
# ERROR: List items re-render incorrectly

# CAUSE: No key or non-unique key
For(each=items)[
    lambda item: li()[item["text"]]  # No key!
]

# FIX: Add unique key
For(each=items, key=lambda x: x["id"])[
    lambda item: li()[item["text"]]
]

# CAUSE: Index as key (bad for reordering)
For(each=items, key=lambda x, i: i)[  # Index changes on reorder!
    lambda item: li()[item["text"]]
]
```

### 4.5 Compilation Errors

```python
# ERROR: Cannot compile to JavaScript

# CAUSE: Using non-compilable construct
@island
def Bad():
    import os  # ERROR: Can't import os in island
    
    class Foo:  # ERROR: Can't define class in island
        pass
    
    def generator():
        yield 1  # ERROR: Can't use generator in island

# FIX: Move to server
@server
def get_files():
    import os
    return os.listdir(".")

@island
def Good():
    files = signal([])
    
    @effect
    async def load():
        files.set(await get_files())  # Call server function
```

---

## 5. Extension Points

### 5.1 Custom Primitive

```python
from pynext.reactive import signal, effect

def createToggle(initial=False):
    """Custom toggle primitive with true/false only."""
    _value = signal(initial)
    
    def toggle():
        _value.set(not _value())
    
    def set_on():
        _value.set(True)
    
    def set_off():
        _value.set(False)
    
    return _value, toggle, set_on, set_off

# Usage
is_open, toggle_open, open_modal, close_modal = createToggle(False)
```

### 5.2 Custom Control Flow

```python
from pynext.reactive import signal, effect, memo

def createPagination(items, page_size=10):
    """Custom pagination primitive."""
    page = signal(0)
    
    total_pages = memo(lambda: (len(items()) + page_size - 1) // page_size)
    
    current_items = memo(lambda: 
        items()[page() * page_size : (page() + 1) * page_size]
    )
    
    def next_page():
        if page() < total_pages() - 1:
            page.set(page() + 1)
    
    def prev_page():
        if page() > 0:
            page.set(page() - 1)
    
    def go_to_page(n):
        page.set(max(0, min(n, total_pages() - 1)))
    
    return {
        "items": current_items,
        "page": page,
        "total": total_pages,
        "next": next_page,
        "prev": prev_page,
        "go_to": go_to_page,
    }
```

### 5.3 Integration with Existing Code

```python
# Wrap existing async function
async def fetch_user(user_id: int):
    """Existing async function."""
    response = await fetch(f"/api/users/{user_id}")
    return await response.json()

# Create reactive resource
from pynext.reactive import signal, effect

def createResource(fetcher, source):
    """Create reactive resource from async function."""
    data = signal(None)
    loading = signal(False)
    error = signal(None)
    
    @effect
    async def load():
        source_value = source()
        if source_value is None:
            return
        
        loading.set(True)
        error.set(None)
        try:
            result = await fetcher(source_value)
            data.set(result)
        except Exception as e:
            error.set(str(e))
        finally:
            loading.set(False)
    
    return data, loading, error

# Usage
user_id = signal(None)
user, loading, error = createResource(fetch_user, user_id)

# Trigger fetch
user_id.set(123)
```

---

## 6. Prompt Templates

### 6.1 Creating a Component

**User prompt:**
> Help me create a PyNext component that displays a sortable table with pagination

**Expected response structure:**
1. Identify state needs (items, sort column, sort direction, page)
2. Create signals/stores for state
3. Create memos for derived data (sorted items, paginated items)
4. Build UI with For and Show
5. Add event handlers for sort and pagination

### 6.2 Debugging

**User prompt:**
> My PyNext effect isn't running when the signal changes. Here's my code: [code]

**Expected debugging steps:**
1. Check if signal is read (called with parentheses)
2. Check if read is conditional
3. Check if effect is disposed
4. Add debug logging
5. Verify signal is actually changing

### 6.3 Optimization

**User prompt:**
> My PyNext list is slow when updating. How can I optimize it?

**Expected optimization steps:**
1. Ensure using `key` prop for For
2. Check if memos can reduce computation
3. Consider pagination for large lists
4. Use virtualization for very large lists
5. Profile to find bottlenecks

### 6.4 Migration

**User prompt:**
> How do I migrate this React component to PyNext? [React code]

**Expected migration steps:**
1. Map useState to signal
2. Map useEffect to @effect
3. Map useMemo to memo
4. Map useReducer to store
5. Convert JSX to PyNext HTML helpers
6. Convert event handlers

---

## Quick Answers for LLMs

### "How do I create reactive state?"
```python
count = signal(0)  # For simple values
todos = store({"items": []})  # For complex/nested data
```

### "How do I run code when state changes?"
```python
@effect
def my_effect():
    print(count())  # Runs when count changes
```

### "How do I compute derived values?"
```python
doubled = memo(lambda: count() * 2)  # Cached, only recomputes when count changes
```

### "How do I render conditionally?"
```python
Show(when=lambda: count() > 0)["Count is positive"]
```

### "How do I render a list?"
```python
For(each=items, key=lambda x: x.id)[lambda item: li()[item.name]]
```

### "How do I handle events?"
```python
button(onclick=lambda: count.set(count() + 1))["Click me"]
```

### "How do I batch updates?"
```python
batch(lambda: (count.set(1), name.set("Alice")))  # Single notification
```

### "How do I read without subscribing?"
```python
count.peek()  # or untrack(lambda: count())
```

---

*End of AI Guide*

