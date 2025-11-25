# Advanced State Patterns in PyNext

This guide covers advanced patterns for managing state in PyNext applications, including architectural patterns, async state, forms, and more.

## Table of Contents

- [Architectural Patterns](#architectural-patterns)
- [Form State Management](#form-state-management)
- [Async State (Loading, Error, Data)](#async-state-loading-error-data)
- [Optimistic Updates](#optimistic-updates)
- [State Persistence](#state-persistence)
- [State Machines](#state-machines)
- [Performance Patterns](#performance-patterns)
- [Testing State](#testing-state)
- [State Debugging](#state-debugging)

---

## Architectural Patterns

### Pattern 1: Feature-Based State Modules

Organize state by feature, not by type:

```
project/
├── features/
│   ├── auth/
│   │   ├── state.py      # Auth signals & stores
│   │   ├── actions.py    # Auth server actions
│   │   └── components.py # Auth UI components
│   ├── cart/
│   │   ├── state.py
│   │   ├── actions.py
│   │   └── components.py
│   └── products/
│       ├── state.py
│       ├── actions.py
│       └── components.py
└── pages/
    └── ...
```

**features/auth/state.py:**
```python
from pynext import Signal, Store, Computed

# State
current_user = Signal(None)
auth_loading = Signal(False)
auth_error = Signal(None)

# Derived state
is_authenticated = Computed(lambda: current_user() is not None)
user_role = Computed(lambda: current_user().role if current_user() else None)
is_admin = Computed(lambda: user_role() == "admin")

# State actions
def login(user_data):
    auth_error.set(None)
    current_user.set(user_data)

def logout():
    current_user.set(None)

def set_error(error):
    auth_error.set(error)
```

**features/auth/components.py:**
```python
from pynext import component, div, span, button
from .state import current_user, is_authenticated, logout

@component
def UserMenu():
    if not is_authenticated():
        return button(onclick=show_login)["Sign In"]
    
    return div(class_="user-menu")[
        span()[f"Hello, {current_user().name}"],
        button(onclick=logout)["Sign Out"]
    ]
```

### Pattern 2: Context-Like State Sharing

Create a context pattern for deeply nested components:

```python
from pynext import Signal, Store
from contextvars import ContextVar

# Theme context
_theme_context: ContextVar[Signal] = ContextVar('theme')

def create_theme_provider(initial_theme="light"):
    """Create a theme context for a component tree."""
    theme = Signal(initial_theme)
    _theme_context.set(theme)
    return theme

def use_theme():
    """Get the current theme signal."""
    return _theme_context.get()

# Usage
@component
def App():
    theme = create_theme_provider("dark")
    
    return div()[
        Header(),      # Can use use_theme()
        Main()[
            Sidebar(),  # Can use use_theme()
            Content(),  # Can use use_theme()
        ],
        Footer(),      # Can use use_theme()
    ]

@component
def Header():
    theme = use_theme()
    return header(class_=f"header-{theme()}")["..."]
```

### Pattern 3: State Slice Pattern

Break large stores into slices:

```python
from pynext import Store, Computed

# Master store
app_store = Store({
    "user": {
        "profile": {"name": "", "email": ""},
        "preferences": {"theme": "light", "language": "en"}
    },
    "cart": {
        "items": [],
        "coupon": None
    },
    "ui": {
        "sidebar_open": True,
        "modal": None
    }
})

# Slice selectors (computed properties)
user_profile = Computed(lambda: app_store.user.profile)
user_prefs = Computed(lambda: app_store.user.preferences)
cart_items = Computed(lambda: app_store.cart.items)
cart_coupon = Computed(lambda: app_store.cart.coupon)
ui_state = Computed(lambda: app_store.ui)

# Slice actions
class UserActions:
    @staticmethod
    def update_profile(data):
        for key, value in data.items():
            setattr(app_store.user.profile, key, value)
    
    @staticmethod
    def set_theme(theme):
        app_store.user.preferences.theme = theme

class CartActions:
    @staticmethod
    def add_item(item):
        app_store.cart.items.append(item)
    
    @staticmethod
    def remove_item(item_id):
        app_store.cart.items = [
            i for i in app_store.cart.items 
            if i["id"] != item_id
        ]
    
    @staticmethod
    def apply_coupon(code):
        app_store.cart.coupon = code

class UIActions:
    @staticmethod
    def toggle_sidebar():
        app_store.ui.sidebar_open = not app_store.ui.sidebar_open
    
    @staticmethod
    def open_modal(modal_type):
        app_store.ui.modal = modal_type
    
    @staticmethod
    def close_modal():
        app_store.ui.modal = None
```

### Pattern 4: Event Bus Pattern

Decouple state changes from UI:

```python
from pynext import Signal
from typing import Callable, Dict, List
from dataclasses import dataclass

@dataclass
class Event:
    type: str
    payload: any = None

class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event_type: str, handler: Callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        
        # Return unsubscribe function
        return lambda: self._handlers[event_type].remove(handler)
    
    def emit(self, event: Event):
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            handler(event.payload)

# Global event bus
bus = EventBus()

# State reacts to events
cart_items = Signal([])

bus.on("cart:add", lambda item: 
    cart_items.update(lambda items: items + [item])
)

bus.on("cart:remove", lambda item_id:
    cart_items.update(lambda items: [i for i in items if i["id"] != item_id])
)

bus.on("cart:clear", lambda _:
    cart_items.set([])
)

# Components emit events
@component
def ProductCard(product):
    def add_to_cart():
        bus.emit(Event("cart:add", product))
    
    return div(class_="product-card")[
        h3()[product["name"]],
        button(onclick=add_to_cart)["Add to Cart"]
    ]
```

---

## Form State Management

### Pattern 1: Simple Form State

```python
from pynext import Signal, Computed, component, div, form, input_, button, span

@component
def ContactForm():
    # Form fields
    name = Signal("")
    email = Signal("")
    message = Signal("")
    
    # Validation
    name_error = Computed(lambda: 
        "Name is required" if not name().strip() else None
    )
    email_error = Computed(lambda:
        "Invalid email" if name() and "@" not in email() else None
    )
    
    is_valid = Computed(lambda:
        name().strip() and "@" in email() and message().strip()
    )
    
    def handle_submit():
        if is_valid():
            # Submit form data
            submit_contact(name(), email(), message())
    
    return form(onsubmit=handle_submit)[
        div(class_="field")[
            input_(
                type="text",
                placeholder="Name",
                value=name,
                oninput=lambda e: name.set(e.target.value)
            ),
            name_error() and span(class_="error")[name_error()]
        ],
        div(class_="field")[
            input_(
                type="email",
                placeholder="Email",
                value=email,
                oninput=lambda e: email.set(e.target.value)
            ),
            email_error() and span(class_="error")[email_error()]
        ],
        div(class_="field")[
            textarea(
                placeholder="Message",
                value=message,
                oninput=lambda e: message.set(e.target.value)
            )
        ],
        button(type="submit", disabled=not is_valid())["Send"]
    ]
```

### Pattern 2: Form State Factory

Reusable form state management:

```python
from pynext import Signal, Computed, batch
from typing import Dict, Any, Callable, Optional

def create_form_state(
    initial_values: Dict[str, Any],
    validators: Optional[Dict[str, Callable]] = None
):
    """
    Create a form state manager.
    
    Args:
        initial_values: Initial form field values
        validators: Dict of field_name -> validator_fn
    
    Returns:
        Dict with fields, errors, is_valid, submit, reset
    """
    validators = validators or {}
    
    # Create signal for each field
    fields = {
        name: Signal(value) 
        for name, value in initial_values.items()
    }
    
    # Track touched fields
    touched = {
        name: Signal(False) 
        for name in initial_values.keys()
    }
    
    # Compute errors
    errors = {
        name: Computed(lambda n=name: 
            validators.get(n, lambda x: None)(fields[n]())
            if touched[n]() else None
        )
        for name in initial_values.keys()
    }
    
    # Overall validity
    is_valid = Computed(lambda:
        all(
            validators.get(name, lambda x: None)(fields[name]()) is None
            for name in fields.keys()
        )
    )
    
    # Is form dirty?
    is_dirty = Computed(lambda:
        any(
            fields[name]() != initial_values[name]
            for name in fields.keys()
        )
    )
    
    def set_field(name: str, value: Any):
        fields[name].set(value)
        touched[name].set(True)
    
    def get_values():
        return {name: signal() for name, signal in fields.items()}
    
    def reset():
        def do_reset():
            for name, value in initial_values.items():
                fields[name].set(value)
                touched[name].set(False)
        batch(do_reset)
    
    def validate_all():
        for name in touched.keys():
            touched[name].set(True)
        return is_valid()
    
    return {
        "fields": fields,
        "errors": errors,
        "touched": touched,
        "is_valid": is_valid,
        "is_dirty": is_dirty,
        "set_field": set_field,
        "get_values": get_values,
        "reset": reset,
        "validate_all": validate_all,
    }

# Usage
def required(value):
    return "Required" if not value else None

def min_length(n):
    return lambda value: f"Min {n} characters" if len(value) < n else None

def email(value):
    return "Invalid email" if value and "@" not in value else None

form_state = create_form_state(
    initial_values={
        "username": "",
        "email": "",
        "password": "",
    },
    validators={
        "username": required,
        "email": lambda v: required(v) or email(v),
        "password": lambda v: required(v) or min_length(8)(v),
    }
)

@component
def RegistrationForm():
    f = form_state
    
    def handle_submit():
        if f["validate_all"]():
            register_user(f["get_values"]())
    
    return form(onsubmit=handle_submit)[
        div()[
            input_(
                value=f["fields"]["username"],
                oninput=lambda e: f["set_field"]("username", e.target.value)
            ),
            f["errors"]["username"]() and span(class_="error")[f["errors"]["username"]()]
        ],
        # ... more fields
        button(type="submit", disabled=not f["is_valid"]())["Register"]
    ]
```

### Pattern 3: Field Array (Dynamic Fields)

```python
from pynext import Signal, component, div, button, input_
import uuid

def create_field_array(initial_items=None):
    """Manage an array of form fields."""
    items = Signal(initial_items or [])
    
    def append(item=None):
        new_item = item or {"id": uuid.uuid4().hex, "value": ""}
        items.update(lambda arr: arr + [new_item])
    
    def remove(item_id):
        items.update(lambda arr: [i for i in arr if i["id"] != item_id])
    
    def update_item(item_id, field, value):
        def do_update(arr):
            return [
                {**item, field: value} if item["id"] == item_id else item
                for item in arr
            ]
        items.update(do_update)
    
    def move(from_idx, to_idx):
        def do_move(arr):
            arr = list(arr)
            item = arr.pop(from_idx)
            arr.insert(to_idx, item)
            return arr
        items.update(do_move)
    
    return {
        "items": items,
        "append": append,
        "remove": remove,
        "update": update_item,
        "move": move,
    }

# Usage: Todo list with dynamic items
@component
def TodoForm():
    todos = create_field_array([
        {"id": "1", "text": "Learn PyNext", "done": False}
    ])
    
    return div()[
        div(class_="todo-list")[
            [
                div(class_="todo-item", key=todo["id"])[
                    input_(
                        type="checkbox",
                        checked=todo["done"],
                        onchange=lambda e, t=todo: 
                            todos["update"](t["id"], "done", e.target.checked)
                    ),
                    input_(
                        type="text",
                        value=todo["text"],
                        oninput=lambda e, t=todo:
                            todos["update"](t["id"], "text", e.target.value)
                    ),
                    button(onclick=lambda t=todo: todos["remove"](t["id"]))["×"]
                ]
                for todo in todos["items"]()
            ]
        ],
        button(onclick=lambda: todos["append"]())["Add Todo"]
    ]
```

---

## Async State (Loading, Error, Data)

### Pattern 1: Async State Container

```python
from pynext import Signal, Computed, Effect
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Callable
from enum import Enum

T = TypeVar('T')

class AsyncStatus(Enum):
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"

@dataclass
class AsyncState(Generic[T]):
    status: AsyncStatus = AsyncStatus.IDLE
    data: Optional[T] = None
    error: Optional[str] = None

def create_async_state():
    """Create an async state container."""
    state = Signal(AsyncState())
    
    # Derived states
    is_idle = Computed(lambda: state().status == AsyncStatus.IDLE)
    is_loading = Computed(lambda: state().status == AsyncStatus.LOADING)
    is_success = Computed(lambda: state().status == AsyncStatus.SUCCESS)
    is_error = Computed(lambda: state().status == AsyncStatus.ERROR)
    data = Computed(lambda: state().data)
    error = Computed(lambda: state().error)
    
    def set_loading():
        state.set(AsyncState(status=AsyncStatus.LOADING))
    
    def set_success(data):
        state.set(AsyncState(status=AsyncStatus.SUCCESS, data=data))
    
    def set_error(error):
        state.set(AsyncState(status=AsyncStatus.ERROR, error=str(error)))
    
    def reset():
        state.set(AsyncState())
    
    return {
        "state": state,
        "is_idle": is_idle,
        "is_loading": is_loading,
        "is_success": is_success,
        "is_error": is_error,
        "data": data,
        "error": error,
        "set_loading": set_loading,
        "set_success": set_success,
        "set_error": set_error,
        "reset": reset,
    }

# Usage
users_state = create_async_state()

@server_action
async def fetch_users():
    users_state["set_loading"]()
    try:
        users = await db.get_users()
        users_state["set_success"](users)
    except Exception as e:
        users_state["set_error"](e)

@component
def UserList():
    s = users_state
    
    if s["is_loading"]():
        return div(class_="loading")["Loading..."]
    
    if s["is_error"]():
        return div(class_="error")[
            f"Error: {s['error']()}",
            button(onclick=fetch_users)["Retry"]
        ]
    
    if s["is_success"]():
        return ul()[
            [li(key=user["id"])[user["name"]] for user in s["data"]()]
        ]
    
    return button(onclick=fetch_users)["Load Users"]
```

### Pattern 2: Query State (React Query-like)

```python
from pynext import Signal, Computed, Effect
import time
import hashlib

class QueryCache:
    """Simple query cache."""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._stale_time = 60  # seconds
    
    def get(self, key):
        if key in self._cache:
            age = time.time() - self._timestamps.get(key, 0)
            if age < self._stale_time:
                return self._cache[key], False  # data, is_stale
            return self._cache[key], True
        return None, True
    
    def set(self, key, data):
        self._cache[key] = data
        self._timestamps[key] = time.time()
    
    def invalidate(self, key=None):
        if key:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._timestamps.clear()

query_cache = QueryCache()

def create_query(key: str, fetch_fn: Callable):
    """Create a query with caching and refetching."""
    
    data = Signal(None)
    error = Signal(None)
    is_loading = Signal(False)
    is_fetching = Signal(False)  # Background refetch
    
    async def fetch(force=False):
        cache_key = key
        
        # Check cache
        if not force:
            cached, is_stale = query_cache.get(cache_key)
            if cached is not None:
                data.set(cached)
                if not is_stale:
                    return
                # Stale - refetch in background
                is_fetching.set(True)
            else:
                is_loading.set(True)
        else:
            is_loading.set(True)
        
        try:
            result = await fetch_fn()
            data.set(result)
            error.set(None)
            query_cache.set(cache_key, result)
        except Exception as e:
            error.set(str(e))
        finally:
            is_loading.set(False)
            is_fetching.set(False)
    
    def invalidate():
        query_cache.invalidate(key)
    
    def refetch():
        return fetch(force=True)
    
    return {
        "data": data,
        "error": error,
        "is_loading": is_loading,
        "is_fetching": is_fetching,
        "fetch": fetch,
        "refetch": refetch,
        "invalidate": invalidate,
    }

# Usage
users_query = create_query("users", fetch_users_from_api)

@component
def UserList():
    q = users_query
    
    # Fetch on mount
    @Effect
    def on_mount():
        q["fetch"]()
    
    return div()[
        q["is_loading"]() and div()["Loading..."],
        q["is_fetching"]() and div(class_="refetching")["Updating..."],
        q["error"]() and div(class_="error")[q["error"]()],
        q["data"]() and ul()[
            [li(key=u["id"])[u["name"]] for u in q["data"]()]
        ],
        button(onclick=q["refetch"])["Refresh"]
    ]
```

---

## Optimistic Updates

Update UI immediately, then sync with server:

```python
from pynext import Signal, server_action
import uuid

# State
todos = Signal([
    {"id": "1", "text": "Learn PyNext", "done": False},
    {"id": "2", "text": "Build app", "done": False},
])

pending_updates = Signal({})  # Track in-flight updates

@server_action
async def toggle_todo_server(todo_id: str, done: bool):
    """Server action to persist todo change."""
    await db.update_todo(todo_id, {"done": done})
    return {"success": True}

def toggle_todo_optimistic(todo_id: str):
    """Optimistically toggle todo, then sync."""
    
    # Find current state
    current_todos = todos()
    todo = next((t for t in current_todos if t["id"] == todo_id), None)
    if not todo:
        return
    
    new_done = not todo["done"]
    
    # 1. Optimistically update UI
    todos.update(lambda items: [
        {**t, "done": new_done} if t["id"] == todo_id else t
        for t in items
    ])
    
    # 2. Track pending update
    update_id = uuid.uuid4().hex
    pending_updates.update(lambda p: {**p, update_id: todo_id})
    
    # 3. Sync with server
    async def sync():
        try:
            await toggle_todo_server(todo_id, new_done)
        except Exception as e:
            # 4. Rollback on error
            todos.update(lambda items: [
                {**t, "done": not new_done} if t["id"] == todo_id else t
                for t in items
            ])
            show_error(f"Failed to update: {e}")
        finally:
            # Remove from pending
            pending_updates.update(lambda p: {
                k: v for k, v in p.items() if k != update_id
            })
    
    # Run async
    asyncio.create_task(sync())

@component
def TodoItem(todo):
    is_pending = Computed(lambda: 
        todo["id"] in pending_updates().values()
    )
    
    return li(class_=f"todo {'pending' if is_pending() else ''}")[
        input_(
            type="checkbox",
            checked=todo["done"],
            onchange=lambda: toggle_todo_optimistic(todo["id"])
        ),
        span()[todo["text"]],
        is_pending() and span(class_="syncing")["..."]
    ]
```

---

## State Persistence

### Pattern 1: LocalStorage Persistence

```python
from pynext import Signal, Effect
import json

def create_persisted_signal(key: str, initial_value, storage="localStorage"):
    """Create a signal that persists to localStorage."""
    
    # Try to load from storage
    stored = None
    try:
        # Note: This runs on server during SSR, need client-side check
        stored_json = f"window.{storage}.getItem('{key}')"
        # In real implementation, this would be handled in JS runtime
    except:
        pass
    
    signal = Signal(stored if stored is not None else initial_value)
    
    # Persist on change (client-side effect)
    @Effect
    def persist():
        value = signal()
        # This would emit JS code to persist
        # localStorage.setItem(key, JSON.stringify(value))
    
    return signal

# Usage
theme = create_persisted_signal("user_theme", "light")
recent_searches = create_persisted_signal("recent_searches", [])
```

### Pattern 2: Server State Sync

```python
from pynext import Signal, Effect, server_action
import asyncio

def create_synced_state(key: str, initial_value, sync_interval=30):
    """Create state that syncs with server periodically."""
    
    state = Signal(initial_value)
    last_synced = Signal(None)
    is_syncing = Signal(False)
    sync_error = Signal(None)
    
    @server_action
    async def save_to_server(data):
        await db.save_state(key, data)
        return {"synced_at": datetime.now().isoformat()}
    
    @server_action
    async def load_from_server():
        return await db.load_state(key)
    
    async def sync():
        is_syncing.set(True)
        try:
            result = await save_to_server(state())
            last_synced.set(result["synced_at"])
            sync_error.set(None)
        except Exception as e:
            sync_error.set(str(e))
        finally:
            is_syncing.set(False)
    
    async def load():
        try:
            data = await load_from_server()
            if data:
                state.set(data)
        except Exception as e:
            print(f"Failed to load state: {e}")
    
    # Auto-sync on change (debounced)
    @Effect
    def auto_sync():
        _ = state()  # Track dependency
        # Debounce sync
        asyncio.create_task(sync())
    
    return {
        "state": state,
        "last_synced": last_synced,
        "is_syncing": is_syncing,
        "sync_error": sync_error,
        "sync": sync,
        "load": load,
    }
```

---

## State Machines

### Pattern: Finite State Machine

```python
from pynext import Signal, Computed
from enum import Enum
from typing import Dict, Set, Callable, Any

class StateMachine:
    """Simple finite state machine with PyNext signals."""
    
    def __init__(
        self,
        initial_state: str,
        transitions: Dict[str, Dict[str, str]],
        on_enter: Dict[str, Callable] = None,
        on_exit: Dict[str, Callable] = None,
    ):
        self._transitions = transitions
        self._on_enter = on_enter or {}
        self._on_exit = on_exit or {}
        
        self.state = Signal(initial_state)
        self.context = Signal({})
        
        # Derived states
        self.can_transition = Computed(lambda: 
            list(self._transitions.get(self.state(), {}).keys())
        )
    
    def transition(self, event: str, payload: Any = None):
        current = self.state()
        transitions = self._transitions.get(current, {})
        
        if event not in transitions:
            print(f"Invalid transition: {current} + {event}")
            return False
        
        next_state = transitions[event]
        
        # Run exit callback
        if current in self._on_exit:
            self._on_exit[current](self.context())
        
        # Update state
        self.state.set(next_state)
        
        # Update context if payload provided
        if payload:
            self.context.update(lambda ctx: {**ctx, **payload})
        
        # Run enter callback
        if next_state in self._on_enter:
            self._on_enter[next_state](self.context())
        
        return True
    
    def matches(self, state: str) -> Computed:
        """Return a computed that checks if current state matches."""
        return Computed(lambda: self.state() == state)

# Usage: Checkout flow state machine
checkout_machine = StateMachine(
    initial_state="cart",
    transitions={
        "cart": {
            "proceed": "shipping",
            "clear": "cart",
        },
        "shipping": {
            "back": "cart",
            "proceed": "payment",
        },
        "payment": {
            "back": "shipping",
            "submit": "processing",
        },
        "processing": {
            "success": "confirmation",
            "error": "payment",
        },
        "confirmation": {
            "new_order": "cart",
        },
    },
    on_enter={
        "processing": lambda ctx: process_payment(ctx),
        "confirmation": lambda ctx: send_confirmation_email(ctx),
    }
)

@component
def CheckoutWizard():
    machine = checkout_machine
    
    return div(class_="checkout")[
        # Step indicators
        div(class_="steps")[
            span(class_=f"step {'active' if machine.matches('cart')() else ''}")["Cart"],
            span(class_=f"step {'active' if machine.matches('shipping')() else ''}")["Shipping"],
            span(class_=f"step {'active' if machine.matches('payment')() else ''}")["Payment"],
            span(class_=f"step {'active' if machine.matches('confirmation')() else ''}")["Done"],
        ],
        
        # Step content
        machine.matches("cart")() and CartStep(),
        machine.matches("shipping")() and ShippingStep(),
        machine.matches("payment")() and PaymentStep(),
        machine.matches("processing")() and ProcessingStep(),
        machine.matches("confirmation")() and ConfirmationStep(),
        
        # Navigation
        div(class_="actions")[
            "back" in machine.can_transition() and 
                button(onclick=lambda: machine.transition("back"))["Back"],
            "proceed" in machine.can_transition() and 
                button(onclick=lambda: machine.transition("proceed"))["Continue"],
        ]
    ]
```

---

## Performance Patterns

### Pattern 1: Memoized Components

```python
from pynext import component, Computed
from functools import lru_cache

def memo_component(fn):
    """Memoize a component based on its props."""
    cache = {}
    
    def wrapper(*args, **kwargs):
        # Create cache key from args
        key = (args, tuple(sorted(kwargs.items())))
        
        if key not in cache:
            cache[key] = fn(*args, **kwargs)
        
        return cache[key]
    
    return wrapper

@memo_component
@component
def ExpensiveList(items):
    # This won't re-render if items haven't changed
    return ul()[
        [li(key=item["id"])[item["name"]] for item in items]
    ]
```

### Pattern 2: Virtualized List State

```python
from pynext import Signal, Computed, component

def create_virtual_list_state(items_signal, item_height=50, container_height=500):
    """Manage state for a virtualized list."""
    
    scroll_top = Signal(0)
    
    visible_count = Computed(lambda: 
        (container_height // item_height) + 2  # Buffer
    )
    
    start_index = Computed(lambda:
        max(0, scroll_top() // item_height - 1)
    )
    
    end_index = Computed(lambda:
        min(len(items_signal()), start_index() + visible_count())
    )
    
    visible_items = Computed(lambda:
        items_signal()[start_index():end_index()]
    )
    
    total_height = Computed(lambda:
        len(items_signal()) * item_height
    )
    
    offset_y = Computed(lambda:
        start_index() * item_height
    )
    
    def handle_scroll(scroll_position):
        scroll_top.set(scroll_position)
    
    return {
        "visible_items": visible_items,
        "total_height": total_height,
        "offset_y": offset_y,
        "handle_scroll": handle_scroll,
    }
```

### Pattern 3: Debounced State Updates

```python
from pynext import Signal
import asyncio

def create_debounced_signal(initial_value, delay_ms=300):
    """Create a signal that debounces updates."""
    
    value = Signal(initial_value)
    debounced_value = Signal(initial_value)
    _timer = None
    
    def set_value(new_value):
        nonlocal _timer
        
        # Update immediate value
        value.set(new_value)
        
        # Cancel pending debounce
        if _timer:
            _timer.cancel()
        
        # Schedule debounced update
        async def update_debounced():
            await asyncio.sleep(delay_ms / 1000)
            debounced_value.set(new_value)
        
        _timer = asyncio.create_task(update_debounced())
    
    return {
        "value": value,              # Immediate value
        "debounced": debounced_value,  # Debounced value
        "set": set_value,
    }

# Usage: Search input
search = create_debounced_signal("", delay_ms=300)

@component
def SearchBox():
    return div()[
        input_(
            value=search["value"],
            oninput=lambda e: search["set"](e.target.value),
            placeholder="Search..."
        ),
        # Results update after debounce
        SearchResults(query=search["debounced"])
    ]
```

---

## Testing State

### Unit Testing Signals

```python
import pytest
from pynext import Signal, Computed, Effect

def test_signal_basic():
    count = Signal(0)
    
    assert count() == 0
    
    count.set(5)
    assert count() == 5
    
    count.update(lambda x: x + 1)
    assert count() == 6

def test_signal_subscription():
    count = Signal(0)
    received_values = []
    
    unsubscribe = count.subscribe(lambda v: received_values.append(v))
    
    count.set(1)
    count.set(2)
    count.set(3)
    
    assert received_values == [1, 2, 3]
    
    unsubscribe()
    count.set(4)
    
    assert received_values == [1, 2, 3]  # No more updates

def test_computed():
    a = Signal(1)
    b = Signal(2)
    
    sum_ab = Computed(lambda: a() + b())
    
    assert sum_ab() == 3
    
    a.set(10)
    assert sum_ab() == 12
    
    b.set(20)
    assert sum_ab() == 30

def test_computed_caching():
    call_count = 0
    a = Signal(1)
    
    def compute():
        nonlocal call_count
        call_count += 1
        return a() * 2
    
    doubled = Computed(compute)
    
    doubled()  # First call
    doubled()  # Cached
    doubled()  # Cached
    
    assert call_count == 1
    
    a.set(2)  # Invalidate
    doubled()  # Recompute
    
    assert call_count == 2
```

---

## State Debugging

### Debug Utilities

```python
from pynext import Signal, Effect
import json

class StateDebugger:
    """Debug utility for PyNext state."""
    
    def __init__(self):
        self._signals = {}
        self._history = []
        self._max_history = 100
    
    def track(self, name: str, signal: Signal):
        """Track a signal for debugging."""
        self._signals[name] = signal
        
        # Subscribe to changes
        def on_change(value):
            self._history.append({
                "signal": name,
                "value": value,
                "timestamp": time.time(),
            })
            if len(self._history) > self._max_history:
                self._history.pop(0)
            
            if self._log_enabled:
                print(f"[State] {name} = {value}")
        
        signal.subscribe(on_change)
    
    def snapshot(self):
        """Get current state snapshot."""
        return {
            name: signal()
            for name, signal in self._signals.items()
        }
    
    def history(self, signal_name=None):
        """Get state change history."""
        if signal_name:
            return [h for h in self._history if h["signal"] == signal_name]
        return self._history
    
    def enable_logging(self):
        self._log_enabled = True
    
    def disable_logging(self):
        self._log_enabled = False

# Global debugger instance
debugger = StateDebugger()

# Usage
count = Signal(0)
debugger.track("count", count)

user = Signal(None)
debugger.track("user", user)

# In development
debugger.enable_logging()

count.set(1)  # Prints: [State] count = 1
count.set(2)  # Prints: [State] count = 2

# Get snapshot
print(debugger.snapshot())
# {"count": 2, "user": None}

# Get history
print(debugger.history("count"))
# [{"signal": "count", "value": 1, ...}, {"signal": "count", "value": 2, ...}]
```

### Browser DevTools Integration

```javascript
// Add to signals.js for browser debugging

// Expose state to window for DevTools
window.__PYNEXT_DEVTOOLS__ = {
    getSignals: () => __pynext__.signals,
    getStores: () => __pynext__.stores,
    getSignal: (id) => __pynext__.signals[id]?.read(),
    setSignal: (id, value) => __pynext__.signals[id]?.write(value),
    
    // State snapshot
    snapshot: () => {
        const signals = {};
        for (const [id, signal] of Object.entries(__pynext__.signals)) {
            signals[id] = signal.read();
        }
        return { signals, stores: __pynext__.stores };
    },
    
    // Time travel (requires history tracking)
    history: [],
    
    trackHistory: () => {
        for (const [id, signal] of Object.entries(__pynext__.signals)) {
            const originalWrite = signal.write;
            signal.write = (value) => {
                window.__PYNEXT_DEVTOOLS__.history.push({
                    signal: id,
                    oldValue: signal.read(),
                    newValue: typeof value === 'function' ? value(signal.read()) : value,
                    timestamp: Date.now()
                });
                originalWrite(value);
            };
        }
    }
};

console.log('[PyNext] DevTools available at window.__PYNEXT_DEVTOOLS__');
```

---

## Next Steps

- See [State Management Core](STATE_MANAGEMENT.md) for fundamentals
- See [React Integration](REACT_INTEGRATION.md) for using with React components
- Check the [Example App](../example/) for real-world usage

