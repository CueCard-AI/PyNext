# State Management

> **Master signals, stores, and reactive patterns in PyNext**

Learn how PyNext's signal-based reactivity works and how to manage complex application state.

---

## What You'll Learn

- Creating and using Signals
- Computed values with Memo
- Side effects with Effect
- Stores for complex state
- State patterns for real apps

---

## Signals: The Foundation

Signals are reactive containers for values. When a signal's value changes, anything that uses it automatically updates.

```python
from pynext import Signal

# Create a signal
count = Signal(0)

# Read the value
print(count.value)  # 0

# Set a new value
count.set(5)

# Update based on current value
count.update(lambda x: x + 1)
```

### Using Signals in Components

```python
from pynext import Signal, div, button, span

count = Signal(0)

def Counter():
    return div(class_="flex items-center gap-4")[
        button(onclick=lambda: count.update(lambda x: x - 1))["-"],
        span()[count],  # Automatically updates when count changes
        button(onclick=lambda: count.update(lambda x: x + 1))["+"],
    ]
```

**How it works:**
- When `count.set()` or `count.update()` is called, PyNext tracks what parts of the UI depend on `count`
- Only those parts re-render — not the entire page

---

## Computed Values with Memo

Derive new values from signals:

```python
from pynext import Signal, Computed

# Source signals
first_name = Signal("John")
last_name = Signal("Doe")

# Computed value (automatically updates)
full_name = Computed(lambda: f"{first_name.value} {last_name.value}")

print(full_name.value)  # "John Doe"

first_name.set("Jane")
print(full_name.value)  # "Jane Doe"
```

### In Components

```python
items = Signal([
    {"name": "Apple", "price": 1.00, "qty": 3},
    {"name": "Banana", "price": 0.50, "qty": 5},
])

total = Computed(lambda: sum(
    item["price"] * item["qty"] 
    for item in items.value
))

def Cart():
    return div()[
        # Item list...
        div(class_="font-bold")[
            f"Total: ${total.value:.2f}"  # Auto-updates
        ],
    ]
```

---

## Side Effects with Effect

Run code when signals change:

```python
from pynext import Signal, Effect
from pynext.theme import use_theme

# Using PyNext's theme module (recommended)
theme = use_theme()  # Automatically handles dark mode

# For custom effects, use server-side Effects
count = Signal(0)

@Effect
def log_count_changes():
    """This runs on the server when count changes."""
    print(f"Count is now: {count.value}")
```

### Common Use Cases

```python
# Persist to localStorage using use_storage
from pynext.core.client import use_storage

# This creates a signal that automatically syncs with localStorage
settings = use_storage("settings", default={"theme": "light"})

# Fetch data when filter changes (server-side)
@Effect
async def fetch_data():
    response = await fetch(f"/api/items?filter={filter.value}")
    items.set(await response.json())

# For browser-specific listeners, use client_effect
from pynext.core.client import client_effect

@client_effect
def track_window_size():
    """
    Track window resize events.
    
    Client effects run in the browser after hydration.
    For common patterns like resize tracking, PyNext provides
    built-in hooks in future versions.
    """
    pass
```

---

## Stores for Complex State

For objects with multiple properties, use a Store:

```python
from pynext import Store

user_store = Store({
    "name": "John",
    "email": "john@example.com",
    "preferences": {
        "theme": "light",
        "notifications": True,
    }
})

# Read values
print(user_store.name)  # "John"
print(user_store.preferences.theme)  # "light"

# Update values (creates new object, triggers updates)
user_store.name = "Jane"
user_store.preferences.theme = "dark"
```

### Store vs Multiple Signals

```python
# ❌ Many related signals
user_name = Signal("")
user_email = Signal("")
user_theme = Signal("light")

# ✅ One store for related state
user = Store({
    "name": "",
    "email": "",
    "theme": "light",
})
```

---

## State Patterns

### 1. Local Component State

For state used by one component:

```python
def SearchInput():
    query = Signal("")  # Local to this component
    
    return Input(
        value=query.value,
        oninput=lambda e: query.set(e.target.value),
        placeholder="Search...",
    )
```

### 2. Shared State

For state shared between components, define at module level:

```python
# state/cart.py
from pynext import Signal, Computed

cart_items = Signal([])

cart_total = Computed(lambda: sum(
    item["price"] * item["qty"] 
    for item in cart_items.value
))

def add_to_cart(product, qty=1):
    items = cart_items.value.copy()
    existing = next((i for i in items if i["id"] == product["id"]), None)
    if existing:
        existing["qty"] += qty
    else:
        items.append({**product, "qty": qty})
    cart_items.set(items)

def remove_from_cart(product_id):
    cart_items.set([
        item for item in cart_items.value 
        if item["id"] != product_id
    ])
```

Then import where needed:

```python
from state.cart import cart_items, cart_total, add_to_cart

def CartIcon():
    count = len(cart_items.value)
    return div()[
        "🛒",
        count > 0 and Badge()[str(count)],
    ]
```

### 3. Context-Like State

Pass state down without prop drilling:

```python
# Create a context-like pattern
from pynext import Signal

class ThemeContext:
    theme = Signal("light")
    
    @classmethod
    def toggle(cls):
        cls.theme.set("dark" if cls.theme.value == "light" else "light")

# Use anywhere
def SomeDeepComponent():
    return div(class_=f"theme-{ThemeContext.theme.value}")[
        button(onclick=ThemeContext.toggle)["Toggle Theme"]
    ]
```

### 4. Form State

```python
def create_form_state(initial: dict):
    """Factory for form state management."""
    values = Store(initial)
    errors = Signal({})
    touched = Signal(set())
    
    def set_field(name, value):
        setattr(values, name, value)
    
    def set_error(name, error):
        errs = errors.value.copy()
        if error:
            errs[name] = error
        else:
            errs.pop(name, None)
        errors.set(errs)
    
    def touch(name):
        touched.set(touched.value | {name})
    
    def reset():
        for key, value in initial.items():
            setattr(values, key, value)
        errors.set({})
        touched.set(set())
    
    return {
        "values": values,
        "errors": errors,
        "touched": touched,
        "set_field": set_field,
        "set_error": set_error,
        "touch": touch,
        "reset": reset,
    }
```

### 5. Async State

```python
from pynext import Signal

def create_async_state():
    """State for async operations."""
    data = Signal(None)
    loading = Signal(False)
    error = Signal(None)
    
    async def fetch(fetcher):
        loading.set(True)
        error.set(None)
        try:
            result = await fetcher()
            data.set(result)
        except Exception as e:
            error.set(str(e))
        finally:
            loading.set(False)
    
    return {
        "data": data,
        "loading": loading,
        "error": error,
        "fetch": fetch,
    }

# Usage
users_state = create_async_state()

async def load_users():
    await users_state["fetch"](
        lambda: fetch("/api/users").then(r => r.json())
    )
```

---

## Best Practices

### Do's

```python
# ✅ Keep signals granular
first_name = Signal("")
last_name = Signal("")

# ✅ Use computed for derived values
full_name = Computed(lambda: f"{first_name.value} {last_name.value}")

# ✅ Update immutably
items.set([*items.value, new_item])  # New array

# ✅ Co-locate related state
# state/user.py has all user-related signals
```

### Don'ts

```python
# ❌ Mutating signal value directly
items.value.append(new_item)  # Won't trigger updates!

# ❌ Too many signals for one thing
user_name = Signal("")
user_email = Signal("")
user_avatar = Signal("")
# Use a Store instead

# ❌ Putting everything in one global store
app_state = Store({...everything...})  # Hard to maintain
```

---

## Debugging State

```python
from pynext import Effect

# Log all changes to a signal
@Effect
def debug_count():
    print(f"Count changed to: {count.value}")

# Track all state changes
def create_tracked_signal(name, initial):
    signal = Signal(initial)
    original_set = signal.set
    
    def tracked_set(value):
        print(f"[{name}] {signal.value} -> {value}")
        original_set(value)
    
    signal.set = tracked_set
    return signal

count = create_tracked_signal("count", 0)
```

---

## Complete Example

```python
from pynext import page, Signal, Computed, Store

# State
todos = Signal([
    {"id": 1, "text": "Learn PyNext", "done": True},
    {"id": 2, "text": "Build an app", "done": False},
])

filter_mode = Signal("all")  # "all", "active", "completed"

# Computed
filtered_todos = Computed(lambda: [
    todo for todo in todos.value
    if filter_mode.value == "all"
    or (filter_mode.value == "active" and not todo["done"])
    or (filter_mode.value == "completed" and todo["done"])
])

active_count = Computed(lambda: sum(
    1 for todo in todos.value if not todo["done"]
))

# Actions
def add_todo(text):
    todos.set([
        *todos.value,
        {"id": len(todos.value) + 1, "text": text, "done": False}
    ])

def toggle_todo(id):
    todos.set([
        {**t, "done": not t["done"]} if t["id"] == id else t
        for t in todos.value
    ])

def clear_completed():
    todos.set([t for t in todos.value if not t["done"]])


@page(title="Todos")
def todo_page():
    new_text = Signal("")
    
    return div(class_="max-w-md mx-auto p-8")[
        h1(class_="text-2xl font-bold mb-4")["Todos"],
        
        # Add form
        form(
            onsubmit=lambda e: (
                e.preventDefault(),
                add_todo(new_text.value),
                new_text.set(""),
            )
        )[
            div(class_="flex gap-2")[
                Input(
                    value=new_text.value,
                    oninput=lambda e: new_text.set(e.target.value),
                    placeholder="What needs to be done?",
                ),
                Button(type="submit")["Add"],
            ],
        ],
        
        # Todo list
        ul(class_="mt-4 space-y-2")[
            [
                li(class_="flex items-center gap-2")[
                    Checkbox(
                        checked=todo["done"],
                        onchange=lambda t=todo: toggle_todo(t["id"]),
                    ),
                    span(class_="line-through" if todo["done"] else "")[
                        todo["text"]
                    ],
                ]
                for todo in filtered_todos.value
            ]
        ],
        
        # Footer
        div(class_="mt-4 flex justify-between text-sm text-muted-foreground")[
            span()[f"{active_count.value} items left"],
            div(class_="flex gap-2")[
                button(onclick=lambda: filter_mode.set("all"))["All"],
                button(onclick=lambda: filter_mode.set("active"))["Active"],
                button(onclick=lambda: filter_mode.set("completed"))["Completed"],
            ],
            button(onclick=clear_completed)["Clear completed"],
        ],
    ]
```

---

## Key Takeaways

1. **Signals are reactive** — UI updates automatically
2. **Use Computed for derived values** — Don't compute in render
3. **Update immutably** — Always create new objects/arrays
4. **Keep state granular** — But group related state in Stores
5. **Effects for side effects** — Sync with external systems

---

## Related Tutorials

- [Forms & Validation](./forms-and-validation.md) - Form state patterns
- [Real-time Updates](./real-time-updates.md) - Syncing state with server

