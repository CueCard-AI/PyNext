# Advanced State Patterns in PyNext

> **Battle-tested patterns for managing complex application state—with detailed explanations.**

This guide covers advanced patterns for managing state in PyNext applications, including architectural patterns, async state, forms, and more. Each pattern includes a detailed explanation of **what** it does and **why** it works.

---

## Table of Contents

- [Understanding State Patterns](#understanding-state-patterns)
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

## Understanding State Patterns

### What Are State Patterns?

State patterns are **reusable solutions** to common state management problems. Think of them like recipes—you don't reinvent cooking from scratch every meal; you follow proven recipes and adapt them to your needs.

### When to Use These Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PATTERN SELECTION GUIDE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PROBLEM                           PATTERN TO USE                          │
│   ───────                           ──────────────                          │
│                                                                              │
│   "My state is scattered           → Feature-Based Modules                  │
│    across too many files"            (organize by feature, not type)        │
│                                                                              │
│   "Deep components can't            → Context-Like State Sharing            │
│    access shared state"              (pass state down the tree)             │
│                                                                              │
│   "My store is getting huge"        → State Slice Pattern                   │
│                                       (break into focused pieces)           │
│                                                                              │
│   "Components are too coupled       → Event Bus Pattern                     │
│    to state implementation"          (decouple via events)                  │
│                                                                              │
│   "Forms are messy"                 → Form State Factory                    │
│                                       (reusable form handling)              │
│                                                                              │
│   "Loading/error states are         → Async State Container                 │
│    inconsistent"                     (standardize async state)              │
│                                                                              │
│   "UI feels slow on save"           → Optimistic Updates                    │
│                                       (update UI first, sync later)         │
│                                                                              │
│   "State resets on refresh"         → State Persistence                     │
│                                       (save to localStorage/server)         │
│                                                                              │
│   "Complex multi-step flows"        → State Machines                        │
│                                       (explicit states & transitions)       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architectural Patterns

### Pattern 1: Feature-Based State Modules

#### The Problem

As your app grows, you end up with state scattered everywhere:

```
# BAD: State organized by TYPE (hard to find related code)
project/
├── signals/           # All signals in one place
│   ├── auth.py       # Auth signals
│   ├── cart.py       # Cart signals
│   └── products.py   # Product signals
├── actions/           # All actions in another place
│   ├── auth.py       # Auth actions
│   └── cart.py       # Cart actions
└── components/        # Components are separate
    ├── login.py
    └── cart.py
```

When you need to modify the cart feature, you're jumping between 3+ directories. This is called "feature scatter."

#### The Solution: Organize by Feature

```
# GOOD: State organized by FEATURE (related code together)
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

Now everything related to "auth" is in ONE folder. This is called "feature cohesion."

#### How It Works

**features/auth/state.py** - All auth-related state in one place:

```python
from pynext import Signal, Store, Computed

# =============================================================================
# STATE: The raw data containers
# =============================================================================

# The currently logged-in user (None if not logged in)
current_user = Signal(None)

# Is an auth operation in progress? (login, logout, etc.)
auth_loading = Signal(False)

# Did an auth operation fail? Contains the error message.
auth_error = Signal(None)


# =============================================================================
# DERIVED STATE: Computed values that automatically update
# =============================================================================

# Boolean: Is anyone logged in?
# This is COMPUTED - it automatically updates when current_user changes!
is_authenticated = Computed(lambda: current_user() is not None)

# What role does the current user have? (or None if not logged in)
# The "if current_user() else None" prevents errors when no one is logged in.
user_role = Computed(lambda: current_user().role if current_user() else None)

# Is the current user an admin?
is_admin = Computed(lambda: user_role() == "admin")


# =============================================================================
# STATE ACTIONS: Functions that modify state
# =============================================================================

def login(user_data):
    """
    Call this after successful login API response.
    Clears any previous error and sets the current user.
    """
    auth_error.set(None)  # Clear previous errors
    current_user.set(user_data)  # Store the user

def logout():
    """
    Clear the current user. The Computed values will automatically
    update - is_authenticated becomes False, user_role becomes None, etc.
    """
    current_user.set(None)

def set_error(error):
    """Store an authentication error message."""
    auth_error.set(error)
```

**Why this works:**

1. **Single Source of Truth**: All auth state is in ONE file
2. **Derived State**: `is_authenticated` automatically updates when `current_user` changes
3. **Encapsulation**: Other parts of the app don't need to know HOW auth works, just use `is_authenticated()`

**features/auth/components.py** - Components that use the state:

```python
from pynext import component, div, span, button
from .state import current_user, is_authenticated, logout

@component
def UserMenu():
    """
    This component READS from auth state.
    It doesn't need to know how auth works - it just uses the signals.
    """
    # Check if user is logged in
    if not is_authenticated():
        return button(onclick=show_login)["Sign In"]
    
    # User is logged in - show their name and logout button
    return div(class_="user-menu")[
        span()[f"Hello, {current_user().name}"],
        button(onclick=logout)["Sign Out"]  # logout is imported from state.py
    ]
```

**Why this works:**

1. **Separation of Concerns**: Components don't manage state, they just render it
2. **Reactivity**: When `current_user` changes, this component automatically re-renders
3. **Reusability**: `UserMenu` can be used anywhere without passing props

---

### Pattern 2: Context-Like State Sharing

#### The Problem

You need to pass state to deeply nested components:

```python
# BAD: "Prop drilling" - passing theme through every level
def App():
    theme = Signal("dark")
    return Layout(theme=theme)[
        Header(theme=theme)[
            Navigation(theme=theme)[
                NavItem(theme=theme)["Home"]  # 4 levels deep!
            ]
        ]
    ]
```

This is called "prop drilling" and it's tedious and error-prone.

#### The Solution: Context Pattern

Create a "global variable" that any component can access, without passing it through every level:

```python
from pynext import Signal, Store
from contextvars import ContextVar

# =============================================================================
# STEP 1: Create a Context Variable
# =============================================================================

# ContextVar is Python's way of having "thread-local" or "context-local" variables
# It means each component tree can have its own theme value
_theme_context: ContextVar[Signal] = ContextVar('theme')


# =============================================================================
# STEP 2: Create a Provider function (sets the value)
# =============================================================================

def create_theme_provider(initial_theme="light"):
    """
    Create a theme context for a component tree.
    
    This is like saying: "Everything inside this tree can access this theme"
    
    Returns the theme signal so the parent can also modify it.
    """
    theme = Signal(initial_theme)
    _theme_context.set(theme)  # Store it in the context
    return theme


# =============================================================================
# STEP 3: Create a Consumer function (gets the value)
# =============================================================================

def use_theme():
    """
    Get the current theme signal.
    
    Any component can call this to get the theme,
    no matter how deeply nested it is!
    """
    return _theme_context.get()
```

**Using it in practice:**

```python
@component
def App():
    # Create the theme at the TOP of the tree
    theme = create_theme_provider("dark")
    
    return div()[
        Header(),      # Can use use_theme() inside
        Main()[
            Sidebar(),  # Can use use_theme() inside
            Content(),  # Can use use_theme() inside
        ],
        Footer(),      # Can use use_theme() inside
    ]

# A deeply nested component - NO PROPS NEEDED!
@component
def NavItem(label):
    # Get the theme without any prop drilling
    theme = use_theme()
    
    # Use it
    return a(
        class_=f"nav-item nav-item-{theme()}"  # "nav-item nav-item-dark"
    )[label]
```

**Why this works:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CONTEXT FLOW                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   App                                                                       │
│   │ create_theme_provider("dark")  ← Sets the context value                │
│   │                                                                         │
│   ├── Header                                                                │
│   │   │ theme = use_theme()  ← Gets "dark" from context                    │
│   │   └── Navigation                                                        │
│   │       │ theme = use_theme()  ← Also gets "dark"                        │
│   │       └── NavItem                                                       │
│   │           │ theme = use_theme()  ← Still gets "dark"!                  │
│   │                                                                         │
│   └── Footer                                                                │
│       │ theme = use_theme()  ← Gets the same "dark"                        │
│                                                                              │
│   NO PROP DRILLING! Every component accesses the same shared value.        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Pattern 3: State Slice Pattern

#### The Problem

Your store has grown into a massive object that's hard to work with:

```python
# BAD: One giant store
app_store = Store({
    "user": {...},
    "cart": {...},
    "products": {...},
    "orders": {...},
    "notifications": {...},
    "ui": {...},
    # ... 500 lines later
})
```

Every component imports this one store, and it's hard to know what affects what.

#### The Solution: Slice the Store

Keep ONE master store for structure, but create "slices" for focused access:

```python
from pynext import Store, Computed

# =============================================================================
# MASTER STORE: The single source of truth
# =============================================================================

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

# =============================================================================
# SLICE SELECTORS: Computed properties for focused access
# =============================================================================

# Instead of: app_store.user.profile everywhere
# Use: user_profile() - shorter and more semantic

user_profile = Computed(lambda: app_store.user.profile)
user_prefs = Computed(lambda: app_store.user.preferences)
cart_items = Computed(lambda: app_store.cart.items)
cart_coupon = Computed(lambda: app_store.cart.coupon)
ui_state = Computed(lambda: app_store.ui)
```

**Why use Computed for slices?**

1. **Caching**: The value is only recalculated when the underlying data changes
2. **Reactivity**: Components using `cart_items()` automatically update when cart changes
3. **Abstraction**: If you restructure the store, you only change the selector, not every component

**Slice Actions - Organized Mutations:**

```python
# =============================================================================
# SLICE ACTIONS: Grouped mutations for each slice
# =============================================================================

class UserActions:
    """All actions that modify user state."""
    
    @staticmethod
    def update_profile(data):
        """
        Update user profile fields.
        
        Example: UserActions.update_profile({"name": "Alice", "email": "a@b.com"})
        """
        for key, value in data.items():
            setattr(app_store.user.profile, key, value)
    
    @staticmethod
    def set_theme(theme):
        """Change the user's preferred theme."""
        app_store.user.preferences.theme = theme


class CartActions:
    """All actions that modify cart state."""
    
    @staticmethod
    def add_item(item):
        """Add an item to the cart."""
        app_store.cart.items.append(item)
    
    @staticmethod
    def remove_item(item_id):
        """Remove an item by ID."""
        app_store.cart.items = [
            i for i in app_store.cart.items 
            if i["id"] != item_id
        ]
    
    @staticmethod
    def apply_coupon(code):
        """Apply a coupon code."""
        app_store.cart.coupon = code


class UIActions:
    """All actions that modify UI state."""
    
    @staticmethod
    def toggle_sidebar():
        """Toggle sidebar open/closed."""
        app_store.ui.sidebar_open = not app_store.ui.sidebar_open
    
    @staticmethod
    def open_modal(modal_type):
        """Open a modal by type (e.g., "login", "confirm", "settings")."""
        app_store.ui.modal = modal_type
    
    @staticmethod
    def close_modal():
        """Close any open modal."""
        app_store.ui.modal = None
```

**Why this works:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SLICE PATTERN BENEFITS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   BEFORE (Chaos):                    AFTER (Organized):                     │
│   ───────────────                    ──────────────────                     │
│                                                                              │
│   # Scattered mutations              # Grouped by domain                    │
│   app_store.cart.items.append(x)     CartActions.add_item(x)               │
│   app_store.ui.modal = "login"       UIActions.open_modal("login")         │
│                                                                              │
│   # Direct property access           # Semantic selectors                   │
│   app_store.user.preferences.theme   user_prefs().theme                    │
│                                                                              │
│   BENEFITS:                                                                 │
│   ─────────                                                                 │
│   ✓ Clear ownership - CartActions owns cart mutations                      │
│   ✓ Easy to find - "Where do I add to cart?" → CartActions                │
│   ✓ Testable - Test CartActions in isolation                              │
│   ✓ Refactorable - Change store structure, update selectors, done         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Pattern 4: Event Bus Pattern

#### The Problem

Your components are directly calling state mutations, creating tight coupling:

```python
# BAD: Component directly knows about cart state implementation
@component
def ProductCard(product):
    def add_to_cart():
        # This component KNOWS about cart_items signal
        cart_items.update(lambda items: items + [product])
    
    return button(onclick=add_to_cart)["Add"]
```

If you change how cart works, you have to update every component that touches it.

#### The Solution: Event Bus

Components emit events, and state reacts to events. They don't know about each other.

```python
from pynext import Signal
from typing import Callable, Dict, List
from dataclasses import dataclass

# =============================================================================
# THE EVENT BUS: A simple publish-subscribe system
# =============================================================================

@dataclass
class Event:
    """An event with a type and optional payload."""
    type: str           # e.g., "cart:add", "user:login"
    payload: any = None # e.g., the product to add, the user data


class EventBus:
    """
    A central hub where events are published and handlers react.
    
    Think of it like a message board:
    - Publishers post messages: bus.emit(Event("cart:add", product))
    - Subscribers read messages: bus.on("cart:add", handle_add)
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event_type: str, handler: Callable):
        """
        Subscribe to an event type.
        
        Args:
            event_type: The type of event to listen for
            handler: Function to call when event is emitted
        
        Returns:
            A function to unsubscribe
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        
        # Return unsubscribe function
        return lambda: self._handlers[event_type].remove(handler)
    
    def emit(self, event: Event):
        """
        Emit an event. All subscribed handlers will be called.
        """
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            handler(event.payload)


# Global event bus (singleton)
bus = EventBus()
```

**Setting up state to react to events:**

```python
# =============================================================================
# STATE REACTS TO EVENTS (not direct mutations)
# =============================================================================

cart_items = Signal([])

# When "cart:add" event is emitted, add the item to cart
bus.on("cart:add", lambda item: 
    cart_items.update(lambda items: items + [item])
)

# When "cart:remove" event is emitted, remove the item
bus.on("cart:remove", lambda item_id:
    cart_items.update(lambda items: [i for i in items if i["id"] != item_id])
)

# When "cart:clear" event is emitted, empty the cart
bus.on("cart:clear", lambda _:
    cart_items.set([])
)
```

**Components emit events instead of mutating state:**

```python
@component
def ProductCard(product):
    def add_to_cart():
        # Component doesn't know about cart_items signal
        # It just emits an event - someone else handles it
        bus.emit(Event("cart:add", product))
    
    return div(class_="product-card")[
        h3()[product["name"]],
        button(onclick=add_to_cart)["Add to Cart"]
    ]
```

**Why this works:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EVENT BUS FLOW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   DECOUPLED:                                                                │
│   ──────────                                                                │
│                                                                              │
│   ProductCard                      EventBus                 CartState       │
│   ────────────                     ────────                 ─────────       │
│        │                              │                          │          │
│        │ emit("cart:add", product)    │                          │          │
│        │─────────────────────────────►│                          │          │
│        │                              │                          │          │
│        │                              │ call handler(product)    │          │
│        │                              │─────────────────────────►│          │
│        │                              │                          │          │
│        │                              │                 update items        │
│        │                              │                          │          │
│                                                                              │
│   - ProductCard doesn't import cart_items                                   │
│   - CartState doesn't know about ProductCard                                │
│   - They communicate through events only                                    │
│                                                                              │
│                                                                              │
│   BENEFITS:                                                                 │
│   ─────────                                                                 │
│   ✓ Loose coupling - components don't know about each other               │
│   ✓ Easy to add features - new handlers don't affect existing code        │
│   ✓ Testable - emit events in tests, verify state changed                 │
│   ✓ Debuggable - log all events to see what's happening                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Form State Management

### Pattern 1: Simple Form State

#### The Problem

Forms need to track values, validate inputs, and handle submission. Without a pattern, you end up with messy state spread everywhere.

#### The Solution: Structured Form State

```python
from pynext import Signal, Computed, component, div, form, input_, button, span

@component
def ContactForm():
    # =========================================================================
    # FORM FIELDS: Each input has its own signal
    # =========================================================================
    
    name = Signal("")      # User's name
    email = Signal("")     # User's email
    message = Signal("")   # The message content
    
    # =========================================================================
    # VALIDATION: Computed values that automatically update on input change
    # =========================================================================
    
    # Name error: Required field
    name_error = Computed(lambda: 
        "Name is required" if not name().strip() else None
    )
    # ↑ This automatically recalculates whenever name() changes!
    
    # Email error: Must contain @
    email_error = Computed(lambda:
        "Invalid email" if name() and "@" not in email() else None
    )
    # ↑ Why check `name()` first? To only show email error after user starts typing
    
    # Is the entire form valid?
    is_valid = Computed(lambda:
        name().strip() and "@" in email() and message().strip()
    )
    # ↑ All three conditions must be true
    
    # =========================================================================
    # SUBMISSION HANDLER
    # =========================================================================
    
    def handle_submit():
        if is_valid():
            # All validation passed - submit the form
            submit_contact(name(), email(), message())
    
    # =========================================================================
    # THE FORM UI
    # =========================================================================
    
    return form(onsubmit=handle_submit)[
        # Name field with error display
        div(class_="field")[
            input_(
                type="text",
                placeholder="Name",
                value=name,                              # Two-way binding
                oninput=lambda e: name.set(e.target.value)  # Update on type
            ),
            # Show error only if there is one (conditional rendering)
            name_error() and span(class_="error")[name_error()]
        ],
        
        # Email field with error display
        div(class_="field")[
            input_(
                type="email",
                placeholder="Email",
                value=email,
                oninput=lambda e: email.set(e.target.value)
            ),
            email_error() and span(class_="error")[email_error()]
        ],
        
        # Message field
        div(class_="field")[
            textarea(
                placeholder="Message",
                value=message,
                oninput=lambda e: message.set(e.target.value)
            )
        ],
        
        # Submit button - disabled when form is invalid
        button(type="submit", disabled=not is_valid())["Send"]
    ]
```

**How the reactivity flows:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FORM REACTIVITY FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   User types "hello" in name field                                          │
│        │                                                                     │
│        ▼                                                                     │
│   oninput fires → name.set("hello")                                         │
│        │                                                                     │
│        ▼                                                                     │
│   name() now returns "hello"                                                │
│        │                                                                     │
│        ├──► name_error recalculates → returns None (no error)               │
│        │                                                                     │
│        └──► is_valid recalculates → checks all conditions                  │
│                   │                                                          │
│                   ▼                                                          │
│   Button's disabled attribute updates automatically!                        │
│                                                                              │
│   ALL OF THIS HAPPENS AUTOMATICALLY - no manual orchestration needed.       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Pattern 2: Form State Factory

#### The Problem

You're writing the same form state logic over and over for different forms. DRY (Don't Repeat Yourself) violation!

#### The Solution: A Reusable Form State Factory

This factory function creates all the signals, validation, and helpers for ANY form:

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
            Example: {"username": "", "email": "", "password": ""}
        
        validators: Dict mapping field names to validator functions
            Each validator receives a value and returns an error string (or None)
            Example: {"email": lambda v: "Invalid" if "@" not in v else None}
    
    Returns:
        Dict with fields, errors, is_valid, submit, reset, etc.
    """
    validators = validators or {}
    
    # =========================================================================
    # CREATE SIGNALS FOR EACH FIELD
    # =========================================================================
    
    fields = {
        name: Signal(value) 
        for name, value in initial_values.items()
    }
    # ↑ Creates: {"username": Signal(""), "email": Signal(""), ...}
    
    # =========================================================================
    # TRACK WHICH FIELDS HAVE BEEN TOUCHED
    # =========================================================================
    
    # "Touched" means the user has interacted with the field
    # We don't show errors until a field is touched (better UX)
    touched = {
        name: Signal(False) 
        for name in initial_values.keys()
    }
    
    # =========================================================================
    # COMPUTE ERRORS FOR EACH FIELD
    # =========================================================================
    
    errors = {
        name: Computed(lambda n=name: 
            # Only validate if field has been touched
            validators.get(n, lambda x: None)(fields[n]())
            if touched[n]() else None
        )
        for name in initial_values.keys()
    }
    # ↑ The `n=name` is a Python trick to capture the loop variable correctly
    
    # =========================================================================
    # OVERALL FORM VALIDITY
    # =========================================================================
    
    is_valid = Computed(lambda:
        all(
            # Run every validator and check they all return None
            validators.get(name, lambda x: None)(fields[name]()) is None
            for name in fields.keys()
        )
    )
    
    # =========================================================================
    # IS THE FORM DIRTY? (Has anything changed from initial values)
    # =========================================================================
    
    is_dirty = Computed(lambda:
        any(
            fields[name]() != initial_values[name]
            for name in fields.keys()
        )
    )
    # ↑ Useful for "Are you sure you want to leave?" prompts
    
    # =========================================================================
    # HELPER FUNCTIONS
    # =========================================================================
    
    def set_field(name: str, value: Any):
        """Update a field value and mark it as touched."""
        fields[name].set(value)
        touched[name].set(True)
    
    def get_values():
        """Get all current field values as a dict."""
        return {name: signal() for name, signal in fields.items()}
    
    def reset():
        """Reset all fields to initial values and clear touched state."""
        def do_reset():
            for name, value in initial_values.items():
                fields[name].set(value)
                touched[name].set(False)
        batch(do_reset)  # Batch to avoid multiple re-renders
    
    def validate_all():
        """Mark all fields as touched and return overall validity."""
        for name in touched.keys():
            touched[name].set(True)
        return is_valid()
    
    # =========================================================================
    # RETURN THE FORM STATE API
    # =========================================================================
    
    return {
        "fields": fields,           # The field signals
        "errors": errors,           # Computed error messages
        "touched": touched,         # Which fields have been touched
        "is_valid": is_valid,       # Computed: is everything valid?
        "is_dirty": is_dirty,       # Computed: has anything changed?
        "set_field": set_field,     # Update a field
        "get_values": get_values,   # Get all values as dict
        "reset": reset,             # Reset to initial state
        "validate_all": validate_all,  # Touch all fields and validate
    }
```

**Using the factory:**

```python
# =============================================================================
# DEFINE VALIDATORS (reusable across forms)
# =============================================================================

def required(value):
    """Value must not be empty."""
    return "Required" if not value else None

def min_length(n):
    """Value must be at least n characters."""
    return lambda value: f"Min {n} characters" if len(value) < n else None

def email(value):
    """Value must be a valid email."""
    return "Invalid email" if value and "@" not in value else None


# =============================================================================
# CREATE A FORM USING THE FACTORY
# =============================================================================

form_state = create_form_state(
    initial_values={
        "username": "",
        "email": "",
        "password": "",
    },
    validators={
        "username": required,
        # Chain validators: first check required, then check email format
        "email": lambda v: required(v) or email(v),
        # Chain validators: first check required, then check min length
        "password": lambda v: required(v) or min_length(8)(v),
    }
)


# =============================================================================
# USE IN A COMPONENT
# =============================================================================

@component
def RegistrationForm():
    f = form_state  # Short alias
    
    def handle_submit():
        if f["validate_all"]():  # Validate everything first
            register_user(f["get_values"]())  # Submit if valid
    
    return form(onsubmit=handle_submit)[
        div()[
            input_(
                value=f["fields"]["username"],
                oninput=lambda e: f["set_field"]("username", e.target.value)
            ),
            # Show error only if field has one
            f["errors"]["username"]() and span(class_="error")[f["errors"]["username"]()]
        ],
        # ... more fields ...
        button(type="submit", disabled=not f["is_valid"]())["Register"]
    ]
```

**Why this works:**

1. **DRY**: Define the form pattern once, use it everywhere
2. **Consistent**: Every form has the same API
3. **Validated**: Errors are computed automatically
4. **UX-friendly**: Errors only show after user interaction (touched)

---

### Pattern 3: Field Array (Dynamic Fields)

#### The Problem

You need a form with a dynamic number of fields—like a todo list or a list of addresses.

#### The Solution: Field Array Manager

```python
from pynext import Signal, component, div, button, input_
import uuid

def create_field_array(initial_items=None):
    """
    Manage an array of form fields that can grow/shrink.
    
    Each item has a unique ID for stable rendering (React key equivalent).
    """
    items = Signal(initial_items or [])
    
    def append(item=None):
        """Add a new item to the array."""
        new_item = item or {"id": uuid.uuid4().hex, "value": ""}
        items.update(lambda arr: arr + [new_item])
    
    def remove(item_id):
        """Remove an item by ID."""
        items.update(lambda arr: [i for i in arr if i["id"] != item_id])
    
    def update_item(item_id, field, value):
        """Update a specific field of a specific item."""
        def do_update(arr):
            return [
                {**item, field: value} if item["id"] == item_id else item
                for item in arr
            ]
        items.update(do_update)
    
    def move(from_idx, to_idx):
        """Reorder items (for drag-and-drop)."""
        def do_move(arr):
            arr = list(arr)  # Copy to avoid mutation
            item = arr.pop(from_idx)
            arr.insert(to_idx, item)
            return arr
        items.update(do_move)
    
    return {
        "items": items,      # Signal containing the array
        "append": append,    # Add new item
        "remove": remove,    # Remove by ID
        "update": update_item,  # Update field in item
        "move": move,        # Reorder items
    }
```

**Usage: Dynamic Todo List:**

```python
@component
def TodoForm():
    # Create a field array with one initial todo
    todos = create_field_array([
        {"id": "1", "text": "Learn PyNext", "done": False}
    ])
    
    return div()[
        div(class_="todo-list")[
            [
                # Each todo item in the array
                div(class_="todo-item", key=todo["id"])[
                    # Checkbox
                    input_(
                        type="checkbox",
                        checked=todo["done"],
                        onchange=lambda e, t=todo: 
                            todos["update"](t["id"], "done", e.target.checked)
                    ),
                    # Text input
                    input_(
                        type="text",
                        value=todo["text"],
                        oninput=lambda e, t=todo:
                            todos["update"](t["id"], "text", e.target.value)
                    ),
                    # Delete button
                    button(onclick=lambda t=todo: todos["remove"](t["id"]))["×"]
                ]
                for todo in todos["items"]()  # Iterate over the signal's value
            ]
        ],
        # Add new todo button
        button(onclick=lambda: todos["append"]())["Add Todo"]
    ]
```

**Why the `t=todo` trick?**

```python
# This is a Python closure gotcha!

# BAD: All lambdas capture the same 'todo' variable
for todo in todos:
    button(onclick=lambda: remove(todo["id"]))  # WRONG! All use last todo

# GOOD: Capture the current value with default argument
for todo in todos:
    button(onclick=lambda t=todo: remove(t["id"]))  # RIGHT! Each captures its own
```

---

## Async State (Loading, Error, Data)

### Pattern 1: Async State Container

#### The Problem

You're repeating the same loading/error/data pattern everywhere:

```python
# BAD: Repeating this pattern for every async operation
loading = Signal(False)
error = Signal(None)
data = Signal(None)

async def fetch():
    loading.set(True)
    try:
        result = await api_call()
        data.set(result)
    except Exception as e:
        error.set(str(e))
    finally:
        loading.set(False)
```

#### The Solution: Standardized Async State

```python
from pynext import Signal, Computed, Effect
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional
from enum import Enum

T = TypeVar('T')

class AsyncStatus(Enum):
    """The possible states of an async operation."""
    IDLE = "idle"        # Not started
    LOADING = "loading"  # In progress
    SUCCESS = "success"  # Completed successfully
    ERROR = "error"      # Failed


@dataclass
class AsyncState(Generic[T]):
    """Container for async operation state."""
    status: AsyncStatus = AsyncStatus.IDLE
    data: Optional[T] = None
    error: Optional[str] = None


def create_async_state():
    """
    Create an async state container.
    
    Returns an object with:
    - State signals (is_loading, is_success, etc.)
    - State setters (set_loading, set_success, set_error)
    """
    # The main state container
    state = Signal(AsyncState())
    
    # =========================================================================
    # DERIVED STATES: Boolean checks for each status
    # =========================================================================
    
    is_idle = Computed(lambda: state().status == AsyncStatus.IDLE)
    is_loading = Computed(lambda: state().status == AsyncStatus.LOADING)
    is_success = Computed(lambda: state().status == AsyncStatus.SUCCESS)
    is_error = Computed(lambda: state().status == AsyncStatus.ERROR)
    
    # Convenience accessors
    data = Computed(lambda: state().data)
    error = Computed(lambda: state().error)
    
    # =========================================================================
    # STATE TRANSITIONS
    # =========================================================================
    
    def set_loading():
        """Transition to loading state (clears previous data/error)."""
        state.set(AsyncState(status=AsyncStatus.LOADING))
    
    def set_success(data):
        """Transition to success state with data."""
        state.set(AsyncState(status=AsyncStatus.SUCCESS, data=data))
    
    def set_error(error):
        """Transition to error state with message."""
        state.set(AsyncState(status=AsyncStatus.ERROR, error=str(error)))
    
    def reset():
        """Reset to idle state."""
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
```

**Using it:**

```python
# Create async state for users
users_state = create_async_state()

@server_action
async def fetch_users():
    """Fetch users with proper state management."""
    users_state["set_loading"]()
    try:
        users = await db.get_users()
        users_state["set_success"](users)
    except Exception as e:
        users_state["set_error"](e)


@component
def UserList():
    """Component that renders based on async state."""
    s = users_state
    
    # IDLE: Show fetch button
    if s["is_idle"]():
        return button(onclick=fetch_users)["Load Users"]
    
    # LOADING: Show spinner
    if s["is_loading"]():
        return div(class_="loading")["Loading..."]
    
    # ERROR: Show error with retry
    if s["is_error"]():
        return div(class_="error")[
            f"Error: {s['error']()}",
            button(onclick=fetch_users)["Retry"]
        ]
    
    # SUCCESS: Show data
    if s["is_success"]():
        return ul()[
            [li(key=user["id"])[user["name"]] for user in s["data"]()]
        ]
```

**The state machine visualization:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ASYNC STATE MACHINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                    ┌───────────────┐                                        │
│                    │     IDLE      │                                        │
│                    │  (not started)│                                        │
│                    └───────┬───────┘                                        │
│                            │ fetch()                                        │
│                            ▼                                                │
│                    ┌───────────────┐                                        │
│                    │    LOADING    │                                        │
│                    │ (in progress) │                                        │
│                    └───────┬───────┘                                        │
│                     ┌──────┴──────┐                                         │
│                     │             │                                         │
│                success           error                                      │
│                     │             │                                         │
│                     ▼             ▼                                         │
│            ┌───────────────┐  ┌───────────────┐                            │
│            │    SUCCESS    │  │     ERROR     │                            │
│            │  (has data)   │  │ (has message) │                            │
│            └───────────────┘  └───────┬───────┘                            │
│                                       │ retry()                            │
│                                       └──────► LOADING                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Optimistic Updates

### The Problem

When you save data, the user has to wait for the server response:

```
User clicks "Like" → Wait 500ms → UI updates → User sees result

The 500ms feels SLOW and unresponsive.
```

### The Solution: Update UI First, Sync Later

```
User clicks "Like" → UI updates IMMEDIATELY → Server syncs in background

The UI feels INSTANT!
```

```python
from pynext import Signal, server_action
import uuid
import asyncio

# =============================================================================
# STATE
# =============================================================================

todos = Signal([
    {"id": "1", "text": "Learn PyNext", "done": False},
    {"id": "2", "text": "Build app", "done": False},
])

# Track which updates are still syncing with server
pending_updates = Signal({})  # {update_id: todo_id}


# =============================================================================
# SERVER ACTION: The actual persistence
# =============================================================================

@server_action
async def toggle_todo_server(todo_id: str, done: bool):
    """Server action to persist todo change."""
    await db.update_todo(todo_id, {"done": done})
    return {"success": True}


# =============================================================================
# OPTIMISTIC UPDATE: Update UI first, then sync
# =============================================================================

def toggle_todo_optimistic(todo_id: str):
    """
    Optimistically toggle a todo:
    1. Update UI immediately
    2. Sync with server in background
    3. Rollback if server fails
    """
    
    # Find current state
    current_todos = todos()
    todo = next((t for t in current_todos if t["id"] == todo_id), None)
    if not todo:
        return
    
    new_done = not todo["done"]
    
    # =========================================================================
    # STEP 1: Update UI IMMEDIATELY (optimistic)
    # =========================================================================
    
    todos.update(lambda items: [
        {**t, "done": new_done} if t["id"] == todo_id else t
        for t in items
    ])
    # ↑ User sees the change RIGHT NOW!
    
    # =========================================================================
    # STEP 2: Track this as a pending update
    # =========================================================================
    
    update_id = uuid.uuid4().hex
    pending_updates.update(lambda p: {**p, update_id: todo_id})
    # ↑ We track pending updates so we can show a "syncing" indicator
    
    # =========================================================================
    # STEP 3: Sync with server in background
    # =========================================================================
    
    async def sync():
        try:
            await toggle_todo_server(todo_id, new_done)
            # Success! The optimistic update was correct.
            
        except Exception as e:
            # =========================================================
            # STEP 4: ROLLBACK on error
            # =========================================================
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
    
    # Run the sync in background (don't await - we want to return immediately)
    asyncio.create_task(sync())


# =============================================================================
# COMPONENT: Shows pending state
# =============================================================================

@component
def TodoItem(todo):
    # Is this todo currently syncing?
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
        # Show syncing indicator
        is_pending() and span(class_="syncing")["..."]
    ]
```

**The timeline:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OPTIMISTIC UPDATE TIMELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Time: 0ms                                                                 │
│   ─────────                                                                 │
│   User clicks checkbox                                                      │
│        │                                                                     │
│        ▼                                                                     │
│   UI updates IMMEDIATELY (done: false → true)                               │
│   User sees: ☑ (checked)                                                    │
│   "Syncing..." indicator appears                                            │
│        │                                                                     │
│        ▼                                                                     │
│   (Background: HTTP request sent to server)                                 │
│                                                                              │
│                                                                              │
│   Time: 300ms                                                               │
│   ───────────                                                               │
│   Server responds: Success!                                                 │
│   "Syncing..." indicator disappears                                         │
│   UI remains: ☑ (checked)                                                   │
│                                                                              │
│                                                                              │
│   ALTERNATE: Time: 300ms (Error case)                                       │
│   ───────────────────────────────────                                       │
│   Server responds: Error!                                                   │
│   ROLLBACK: UI reverts to ☐ (unchecked)                                     │
│   Error message: "Failed to update"                                         │
│                                                                              │
│                                                                              │
│   USER EXPERIENCE:                                                          │
│   ────────────────                                                          │
│   Without optimistic: User waits 300ms before seeing any change            │
│   With optimistic: User sees change in <1ms, background sync transparent   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## State Machines

### The Problem

Complex multi-step flows (checkout, onboarding, wizards) are hard to manage with simple signals. You end up with:

```python
# BAD: Spaghetti state
step = Signal("cart")
can_go_next = Signal(True)
can_go_back = Signal(False)
is_processing = Signal(False)
# ... 20 more signals to track all the conditions
```

### The Solution: Finite State Machine

A state machine has:
1. **States**: The possible situations (cart, shipping, payment, etc.)
2. **Transitions**: What events can move you from one state to another
3. **Guards**: Conditions that must be true for a transition to happen

```python
from pynext import Signal, Computed
from typing import Dict, Callable, Any

class StateMachine:
    """
    A finite state machine with PyNext signals.
    
    The key insight: Instead of tracking "can I go to shipping?", 
    you ask "what transitions are valid from my current state?"
    """
    
    def __init__(
        self,
        initial_state: str,
        transitions: Dict[str, Dict[str, str]],
        on_enter: Dict[str, Callable] = None,
        on_exit: Dict[str, Callable] = None,
    ):
        """
        Args:
            initial_state: Starting state
            transitions: Dict mapping state → {event → next_state}
            on_enter: Callbacks when entering a state
            on_exit: Callbacks when leaving a state
        """
        self._transitions = transitions
        self._on_enter = on_enter or {}
        self._on_exit = on_exit or {}
        
        # Current state (reactive)
        self.state = Signal(initial_state)
        
        # Context for passing data between states
        self.context = Signal({})
        
        # What transitions are valid right now?
        self.can_transition = Computed(lambda: 
            list(self._transitions.get(self.state(), {}).keys())
        )
    
    def transition(self, event: str, payload: Any = None):
        """
        Attempt to transition to a new state.
        
        Returns True if transition was valid, False otherwise.
        """
        current = self.state()
        transitions = self._transitions.get(current, {})
        
        # Is this transition valid?
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
```

**Example: Checkout Flow**

```python
checkout_machine = StateMachine(
    initial_state="cart",
    
    # Define all valid transitions
    transitions={
        "cart": {
            "proceed": "shipping",  # "proceed" event → go to "shipping"
            "clear": "cart",        # "clear" event → stay in "cart"
        },
        "shipping": {
            "back": "cart",         # Can go back to cart
            "proceed": "payment",   # Or proceed to payment
        },
        "payment": {
            "back": "shipping",
            "submit": "processing",
        },
        "processing": {
            "success": "confirmation",
            "error": "payment",     # Go back to payment on error
        },
        "confirmation": {
            "new_order": "cart",    # Start a new order
        },
    },
    
    # Callbacks when entering states
    on_enter={
        "processing": lambda ctx: process_payment(ctx),
        "confirmation": lambda ctx: send_confirmation_email(ctx),
    }
)
```

**Using in a component:**

```python
@component
def CheckoutWizard():
    machine = checkout_machine
    
    return div(class_="checkout")[
        # =====================================================================
        # STEP INDICATORS
        # =====================================================================
        div(class_="steps")[
            span(class_=f"step {'active' if machine.matches('cart')() else ''}")["Cart"],
            span(class_=f"step {'active' if machine.matches('shipping')() else ''}")["Shipping"],
            span(class_=f"step {'active' if machine.matches('payment')() else ''}")["Payment"],
            span(class_=f"step {'active' if machine.matches('confirmation')() else ''}")["Done"],
        ],
        
        # =====================================================================
        # STEP CONTENT (only one shows at a time)
        # =====================================================================
        machine.matches("cart")() and CartStep(),
        machine.matches("shipping")() and ShippingStep(),
        machine.matches("payment")() and PaymentStep(),
        machine.matches("processing")() and ProcessingStep(),
        machine.matches("confirmation")() and ConfirmationStep(),
        
        # =====================================================================
        # NAVIGATION (buttons based on valid transitions)
        # =====================================================================
        div(class_="actions")[
            # Show "Back" only if "back" is a valid transition
            "back" in machine.can_transition() and 
                button(onclick=lambda: machine.transition("back"))["Back"],
            
            # Show "Continue" only if "proceed" is a valid transition
            "proceed" in machine.can_transition() and 
                button(onclick=lambda: machine.transition("proceed"))["Continue"],
        ]
    ]
```

**Why state machines work:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STATE MACHINE BENEFITS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. IMPOSSIBLE STATES ARE IMPOSSIBLE                                       │
│   ──────────────────────────────────────                                    │
│   You can't be in "payment" and "shipping" at the same time.               │
│   The state is ALWAYS one of the defined states.                            │
│                                                                              │
│   2. TRANSITIONS ARE EXPLICIT                                               │
│   ───────────────────────────                                               │
│   From "cart", you can ONLY "proceed" or "clear".                          │
│   You can't accidentally jump to "confirmation" from "cart".                │
│                                                                              │
│   3. EASY TO VISUALIZE                                                      │
│   ─────────────────────                                                     │
│                                                                              │
│   cart ──proceed──► shipping ──proceed──► payment                           │
│     │                  │                    │                               │
│     │                  │                    │                               │
│     └──clear──┐        └──back──► cart      └──submit──► processing         │
│               │                                           │    │            │
│               ▼                                           │    │            │
│             cart                            success ◄─────┘    │            │
│                                               │                │            │
│                                               ▼                │            │
│                                         confirmation           │            │
│                                               │                │            │
│                                               └──new_order──► cart          │
│                                                                │            │
│                                         payment ◄──error───────┘            │
│                                                                              │
│   4. DEBUGGING IS EASY                                                      │
│   ─────────────────────                                                     │
│   "What state are we in?" → machine.state()                                │
│   "What can we do?" → machine.can_transition()                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Performance Patterns

### Pattern 1: Debounced State Updates

#### The Problem

User types in a search box, and you fetch results on every keystroke:

```
User types "hello"
→ Fetch "h"
→ Fetch "he"
→ Fetch "hel"
→ Fetch "hell"
→ Fetch "hello"

5 API calls! Most are wasted because user was still typing.
```

#### The Solution: Debounce

Wait until user stops typing, then fetch:

```python
from pynext import Signal
import asyncio

def create_debounced_signal(initial_value, delay_ms=300):
    """
    Create a signal that debounces updates.
    
    The 'value' updates immediately (for UI responsiveness).
    The 'debounced' updates after user stops changing for delay_ms.
    """
    
    value = Signal(initial_value)           # Immediate value
    debounced_value = Signal(initial_value)  # Debounced value
    _timer = None
    
    def set_value(new_value):
        nonlocal _timer
        
        # Update immediate value (so input feels responsive)
        value.set(new_value)
        
        # Cancel any pending debounce
        if _timer:
            _timer.cancel()
        
        # Schedule debounced update
        async def update_debounced():
            await asyncio.sleep(delay_ms / 1000)
            debounced_value.set(new_value)
        
        _timer = asyncio.create_task(update_debounced())
    
    return {
        "value": value,              # Use for input display
        "debounced": debounced_value,  # Use for expensive operations
        "set": set_value,
    }


# =============================================================================
# USAGE
# =============================================================================

search = create_debounced_signal("", delay_ms=300)

@component
def SearchBox():
    return div()[
        # Input uses immediate value (responsive)
        input_(
            value=search["value"],
            oninput=lambda e: search["set"](e.target.value),
            placeholder="Search..."
        ),
        # Results use debounced value (efficient)
        SearchResults(query=search["debounced"])
    ]
```

**The timeline:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEBOUNCE TIMELINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   User types: "h" "e" "l" "l" "o"                                          │
│   Time:       0   50  100 150 200  (ms)                                    │
│                                                                              │
│                                                                              │
│   WITHOUT DEBOUNCE:                                                         │
│   ─────────────────                                                         │
│   0ms:   search("h") → API call                                            │
│   50ms:  search("he") → API call                                           │
│   100ms: search("hel") → API call                                          │
│   150ms: search("hell") → API call                                         │
│   200ms: search("hello") → API call                                        │
│                                                                              │
│   5 API calls! 🔥                                                           │
│                                                                              │
│                                                                              │
│   WITH DEBOUNCE (300ms delay):                                              │
│   ────────────────────────────                                              │
│   0ms:   value = "h" (immediate, UI updates)                               │
│   50ms:  value = "he" (immediate, timer resets)                            │
│   100ms: value = "hel" (immediate, timer resets)                           │
│   150ms: value = "hell" (immediate, timer resets)                          │
│   200ms: value = "hello" (immediate, timer resets)                         │
│   ...user stops typing...                                                   │
│   500ms: debounced = "hello" → API call                                    │
│                                                                              │
│   1 API call! ✓                                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Testing State

### Unit Testing Signals

Testing signals is straightforward because they're just values with subscriptions:

```python
import pytest
from pynext import Signal, Computed, Effect

def test_signal_basic():
    """Test basic signal operations."""
    count = Signal(0)
    
    # Reading
    assert count() == 0
    
    # Setting
    count.set(5)
    assert count() == 5
    
    # Updating with function
    count.update(lambda x: x + 1)
    assert count() == 6


def test_signal_subscription():
    """Test that subscribers are notified of changes."""
    count = Signal(0)
    received_values = []
    
    # Subscribe to changes
    unsubscribe = count.subscribe(lambda v: received_values.append(v))
    
    # Make changes
    count.set(1)
    count.set(2)
    count.set(3)
    
    # All values should have been received
    assert received_values == [1, 2, 3]
    
    # Unsubscribe
    unsubscribe()
    count.set(4)
    
    # Should NOT receive 4
    assert received_values == [1, 2, 3]


def test_computed():
    """Test that computed values update when dependencies change."""
    a = Signal(1)
    b = Signal(2)
    
    # Computed that depends on a and b
    sum_ab = Computed(lambda: a() + b())
    
    assert sum_ab() == 3
    
    # Change a
    a.set(10)
    assert sum_ab() == 12  # Automatically updated!
    
    # Change b
    b.set(20)
    assert sum_ab() == 30  # Automatically updated!


def test_computed_caching():
    """Test that computed values are cached (not recomputed unnecessarily)."""
    call_count = 0
    a = Signal(1)
    
    def compute():
        nonlocal call_count
        call_count += 1  # Count how many times we compute
        return a() * 2
    
    doubled = Computed(compute)
    
    # First access - should compute
    doubled()
    assert call_count == 1
    
    # Second access - should use cache
    doubled()
    doubled()
    assert call_count == 1  # Still 1! Cached.
    
    # Change dependency - should invalidate cache
    a.set(2)
    doubled()  # This should recompute
    assert call_count == 2
```

---

## State Debugging

### Debug Utilities

When something goes wrong, you need to know what state changed and when:

```python
from pynext import Signal, Effect
import json
import time

class StateDebugger:
    """
    Debug utility for PyNext state.
    
    Tracks all signal changes with timestamps.
    """
    
    def __init__(self):
        self._signals = {}      # name → signal
        self._history = []      # List of {signal, value, timestamp}
        self._max_history = 100
        self._log_enabled = False
    
    def track(self, name: str, signal: Signal):
        """
        Track a signal for debugging.
        
        Every time the signal changes, we record it.
        """
        self._signals[name] = signal
        
        def on_change(value):
            # Record the change
            self._history.append({
                "signal": name,
                "value": value,
                "timestamp": time.time(),
            })
            
            # Trim old history
            if len(self._history) > self._max_history:
                self._history.pop(0)
            
            # Log if enabled
            if self._log_enabled:
                print(f"[State] {name} = {value}")
        
        signal.subscribe(on_change)
    
    def snapshot(self):
        """Get current values of all tracked signals."""
        return {
            name: signal()
            for name, signal in self._signals.items()
        }
    
    def history(self, signal_name=None):
        """
        Get change history.
        
        Args:
            signal_name: Filter to specific signal (optional)
        """
        if signal_name:
            return [h for h in self._history if h["signal"] == signal_name]
        return self._history
    
    def enable_logging(self):
        """Enable console logging of all state changes."""
        self._log_enabled = True
    
    def disable_logging(self):
        """Disable console logging."""
        self._log_enabled = False


# =============================================================================
# USAGE
# =============================================================================

# Create debugger
debugger = StateDebugger()

# Track signals
count = Signal(0)
debugger.track("count", count)

user = Signal(None)
debugger.track("user", user)

# Enable logging during development
debugger.enable_logging()

# Now every change is logged
count.set(1)  # Prints: [State] count = 1
count.set(2)  # Prints: [State] count = 2

# Get snapshot of current state
print(debugger.snapshot())
# {"count": 2, "user": None}

# Get history of changes
print(debugger.history("count"))
# [
#   {"signal": "count", "value": 1, "timestamp": 1234567890.123},
#   {"signal": "count", "value": 2, "timestamp": 1234567890.456}
# ]
```

**Why debugging tools matter:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEBUGGING WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PROBLEM: "Why is my cart empty after checkout?"                           │
│                                                                              │
│   1. Check current state:                                                   │
│      debugger.snapshot()                                                    │
│      → {"cart_items": [], "checkout_step": "confirmation"}                  │
│                                                                              │
│   2. Check history:                                                         │
│      debugger.history("cart_items")                                         │
│      → [                                                                    │
│          {"value": [{id: 1, name: "Widget"}], timestamp: 1000},            │
│          {"value": [], timestamp: 1500}  ← Here's when it emptied!         │
│        ]                                                                    │
│                                                                              │
│   3. The 500ms gap between checkout step change and cart clear              │
│      tells you the cart was cleared AFTER moving to confirmation.           │
│                                                                              │
│   4. Search code for where cart is cleared → find the bug!                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

- See [State Management Core](STATE_MANAGEMENT.md) for fundamentals
- See [Server Actions](SERVER_ACTIONS.md) for async operations
- Check the [Example App](../example/) for real-world usage
