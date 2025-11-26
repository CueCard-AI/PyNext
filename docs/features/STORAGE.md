# Storage Guide

> **Complete guide to persistent state with localStorage and sessionStorage**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding Browser Storage](#understanding-browser-storage)
3. [use_storage API](#use_storage-api)
4. [Local vs Session Storage](#local-vs-session-storage)
5. [Complex Data Types](#complex-data-types)
6. [Cross-Tab Synchronization](#cross-tab-synchronization)
7. [Server-Side Considerations](#server-side-considerations)
8. [Common Patterns](#common-patterns)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

```python
from pynext.core.client import use_storage

# Create a persistent signal
sidebar_collapsed = use_storage("sidebar_collapsed", default=False)

# Read it (like a normal signal)
is_collapsed = sidebar_collapsed()

# Write it (automatically saves to localStorage!)
sidebar_collapsed.set(True)
```

The value persists across page refreshes and browser sessions!

---

## Understanding Browser Storage

### First Principles: What Is Storage?

Browsers provide two storage APIs that persist data on the user's device:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Browser Storage Types                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  localStorage                          sessionStorage                       │
│  ────────────                          ──────────────                       │
│                                                                             │
│  Persists forever                      Cleared when tab closes              │
│  (until user clears)                                                        │
│                                                                             │
│  Shared across tabs                    Isolated to each tab                 │
│  (same origin)                         (even same URL)                      │
│                                                                             │
│  Good for:                             Good for:                            │
│  - Theme preference                    - Form draft data                    │
│  - User settings                       - Shopping cart (temporary)          │
│  - "Remember me" states                - Page-specific state                │
│                                                                             │
│  Capacity: ~5-10MB                     Capacity: ~5-10MB                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Raw JavaScript API

```javascript
// localStorage
localStorage.setItem("key", "value");
const value = localStorage.getItem("key");  // "value"
localStorage.removeItem("key");

// Only stores strings! Objects must be serialized:
localStorage.setItem("user", JSON.stringify({ name: "Alice" }));
const user = JSON.parse(localStorage.getItem("user"));
```

PyNext handles all of this for you!

---

## use_storage API

### Basic Syntax

```python
from pynext.core.client import use_storage

# Basic usage
my_signal = use_storage("key", default=initial_value)

# With options
my_signal = use_storage(
    "key",                    # Storage key
    default=initial_value,    # Default if not in storage
    storage="local",          # "local" or "session"
)
```

### What It Returns

`use_storage` returns a Signal with superpowers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  use_storage Return Value                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  signal = use_storage("key", default="value")                               │
│                                                                             │
│  Methods (inherited from Signal):                                           │
│  ─────────────────────────────────                                          │
│  signal()           → Read current value                                    │
│  signal.set(value)  → Set new value (saves to storage!)                     │
│  signal.update(fn)  → Update with function (saves to storage!)              │
│                                                                             │
│  Automatic Behaviors:                                                       │
│  ────────────────────                                                       │
│  - On mount: Reads from storage, uses default if missing                    │
│  - On set/update: Automatically writes to storage                           │
│  - Cross-tab: Syncs with other tabs (localStorage only)                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Example

```python
from pynext.core.client import use_storage
from pynext import div, button
from pynext.tw import cn

# User preferences (persist forever)
dark_mode = use_storage("dark_mode", default=False)
sidebar_width = use_storage("sidebar_width", default=240)
recent_searches = use_storage("recent_searches", default=[])

def Sidebar():
    return div(
        class_=cn(
            "h-screen bg-card border-r transition-all",
        ),
        style=f"width: {sidebar_width()}px",
    )[
        # Sidebar content
    ]

def SearchHistory():
    searches = recent_searches()
    
    return div()[
        h3()["Recent Searches"],
        [
            button(onclick=lambda s=s: do_search(s))[s]
            for s in searches[:5]
        ],
        button(onclick=lambda: recent_searches.set([]))[
            "Clear History"
        ],
    ]

def add_search(query):
    # Update with function to prepend new search
    recent_searches.update(lambda searches: [query] + searches[:9])
```

---

## Local vs Session Storage

### When to Use Which

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  localStorage vs sessionStorage                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Use localStorage for:                 Use sessionStorage for:              │
│  ─────────────────────                 ───────────────────────              │
│                                                                             │
│  ✅ Theme/dark mode                    ✅ Unsaved form data                 │
│  ✅ Language preference                ✅ Page scroll position              │
│  ✅ UI preferences                     ✅ Temporary wizard state            │
│     (sidebar state, view mode)                                              │
│  ✅ Recently viewed items              ✅ Tab-specific data                 │
│  ✅ User settings                                                           │
│  ✅ Persistent filters                 ✅ Multi-step form progress          │
│                                                                             │
│                                                                             │
│  Lifetime Comparison:                                                       │
│  ────────────────────                                                       │
│                                                                             │
│  localStorage:                                                              │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │ Tab 1 opens │ Tab 1 closes │ Browser closes │ Day later │ ...  │        │
│  │    value    │    value     │     value      │   value   │ ...  │        │
│  └────────────────────────────────────────────────────────────────┘        │
│  Data survives everything!                                                  │
│                                                                             │
│  sessionStorage:                                                            │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │ Tab 1 opens │ Tab 1 closes │                                   │        │
│  │    value    │    GONE      │                                   │        │
│  └────────────────────────────────────────────────────────────────┘        │
│  Data cleared when tab closes!                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Code Examples

```python
# Theme: Should persist forever
theme = use_storage("theme", default="light", storage="local")

# Draft email: Lose it when tab closes
draft = use_storage("email_draft", default="", storage="session")

# Wizard progress: Lose if they leave
wizard_step = use_storage("wizard_step", default=0, storage="session")

# View preference: Remember forever
list_view = use_storage("list_view", default="grid", storage="local")
```

---

## Complex Data Types

### Storing Objects

```python
# Objects work automatically!
user_prefs = use_storage("user_prefs", default={
    "notifications": True,
    "emailFrequency": "daily",
    "timezone": "UTC",
})

# Read nested values
if user_prefs()["notifications"]:
    send_notification()

# Update nested values (immutably!)
user_prefs.update(lambda prefs: {
    **prefs,
    "notifications": False,
})
```

### Storing Lists

```python
favorites = use_storage("favorites", default=[])

# Add item
def add_favorite(item):
    favorites.update(lambda items: [*items, item])

# Remove item
def remove_favorite(item_id):
    favorites.update(lambda items: [
        i for i in items if i["id"] != item_id
    ])

# Check if favorited
def is_favorite(item_id):
    return any(i["id"] == item_id for i in favorites())
```

### How Serialization Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Storage Serialization Flow                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Python Value                   localStorage                   Python Value │
│  ────────────                   ────────────                   ──────────── │
│                                                                             │
│  {"name": "Alice"}  ──JSON.stringify──▶  '{"name":"Alice"}'                 │
│                                                    │                        │
│                                                    │                        │
│                     ◀──JSON.parse────  '{"name":"Alice"}'                  │
│  {"name": "Alice"}                                                          │
│                                                                             │
│                                                                             │
│  Supported Types:                                                           │
│  ────────────────                                                           │
│  ✅ Strings:   "hello"                                                      │
│  ✅ Numbers:   42, 3.14                                                     │
│  ✅ Booleans:  True, False                                                  │
│  ✅ Lists:     [1, 2, 3]                                                    │
│  ✅ Dicts:     {"key": "value"}                                             │
│  ✅ None:      null                                                         │
│                                                                             │
│  NOT Supported:                                                             │
│  ──────────────                                                             │
│  ❌ Functions                                                               │
│  ❌ Classes                                                                 │
│  ❌ Dates (store as ISO string instead)                                     │
│  ❌ Sets (convert to list)                                                  │
│  ❌ Circular references                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dates Example

```python
# Store date as ISO string
last_visit = use_storage("last_visit", default=None)

def record_visit():
    from datetime import datetime
    last_visit.set(datetime.now().isoformat())

def get_last_visit():
    value = last_visit()
    if value:
        from datetime import datetime
        return datetime.fromisoformat(value)
    return None
```

---

## Cross-Tab Synchronization

### How It Works

localStorage automatically syncs across tabs (same origin):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Cross-Tab Sync Flow                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Tab 1                                   Tab 2                              │
│  ─────                                   ─────                              │
│                                                                             │
│  User clicks "Dark Mode"                                                    │
│       │                                                                     │
│       ▼                                                                     │
│  theme.set("dark")                                                          │
│       │                                                                     │
│       ▼                                                                     │
│  localStorage.setItem(                   Browser fires                      │
│    "theme", "dark"                       'storage' event ────────┐          │
│  )                                                               │          │
│                                                                  ▼          │
│                                          storage.js detects                 │
│                                               │                             │
│                                               ▼                             │
│                                          theme signal updates               │
│                                               │                             │
│                                               ▼                             │
│                                          UI re-renders                      │
│                                          with dark mode                     │
│                                                                             │
│  Both tabs now show dark mode! 🎉                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Code Example

```python
# In any component
theme = use_storage("theme", default="light")

# When user changes theme in Tab 1...
theme.set("dark")

# Tab 2 automatically updates!
# No extra code needed.
```

### Session Storage Doesn't Sync

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  sessionStorage is Tab-Isolated                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Tab 1                                   Tab 2                              │
│  ─────                                   ─────                              │
│                                                                             │
│  sessionStorage:                         sessionStorage:                    │
│    cart = ["item1"]                        cart = []                        │
│                                                                             │
│  These are COMPLETELY SEPARATE!                                             │
│  Changes in Tab 1 don't affect Tab 2.                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Server-Side Considerations

### The SSR Problem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SSR vs Client Storage                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Server:                             Client:                                │
│  ───────                             ───────                                │
│                                                                             │
│  No localStorage!                    Has localStorage!                      │
│  No sessionStorage!                  Has sessionStorage!                    │
│                                                                             │
│  What happens:                                                              │
│  ─────────────                                                              │
│                                                                             │
│  1. Server renders with DEFAULT value                                       │
│  2. HTML sent to browser                                                    │
│  3. Client hydrates                                                         │
│  4. Storage is read                                                         │
│  5. If different, UI updates                                                │
│                                                                             │
│  This means there might be a brief flash if stored value                    │
│  differs from default!                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Handling the Mismatch

```python
# For theme, use ThemeScript to prevent flash
from pynext.theme import ThemeScript

# For other values, consider:
# 1. Accept the brief update (usually fine)
# 2. Hide content until hydrated
# 3. Use CSS to handle both states

def Sidebar():
    collapsed = use_storage("sidebar", default=False)
    
    # The server renders with collapsed=False
    # If user had it collapsed, it briefly shows expanded
    # Then collapses after hydration
    
    return div(
        class_=cn(
            "transition-all duration-200",  # Smooth transition
            "w-16" if collapsed() else "w-64",
        ),
    )[...]
```

---

## Common Patterns

### User Preferences Object

```python
# Single storage key for all preferences
prefs = use_storage("preferences", default={
    "theme": "system",
    "sidebarCollapsed": False,
    "listView": "grid",
    "itemsPerPage": 20,
    "notifications": True,
})

def get_pref(key):
    return prefs()[key]

def set_pref(key, value):
    prefs.update(lambda p: {**p, key: value})

# Usage
set_pref("theme", "dark")
items_per_page = get_pref("itemsPerPage")
```

### Recent Items List

```python
MAX_RECENT = 10
recent_items = use_storage("recent", default=[])

def add_to_recent(item):
    recent_items.update(lambda items: [
        item,
        *[i for i in items if i["id"] != item["id"]]  # Remove if exists
    ][:MAX_RECENT])  # Keep max

def clear_recent():
    recent_items.set([])

# Display
def RecentItemsList():
    items = recent_items()
    if not items:
        return p()["No recent items"]
    
    return ul()[
        [li()[item["name"]] for item in items]
    ]
```

### Draft Auto-Save

```python
# Save draft every few seconds
draft = use_storage("post_draft", default="", storage="session")

@island
def Editor():
    content = Signal("")
    
    # Initialize from storage
    @client_effect()
    def load_draft():
        saved = draft()
        if saved:
            content.set(saved)
    
    # Auto-save every 3 seconds
    @client_effect(dependencies=[content])
    def auto_save():
        timer = None
        def save():
            draft.set(content())
        timer = set_timeout(save, 3000)
        return lambda: clear_timeout(timer)
    
    return textarea(
        value=content(),
        oninput=lambda e: content.set(e.target.value),
    )
```

### Feature Flags

```python
# Dev/testing feature flags
flags = use_storage("feature_flags", default={})

def is_enabled(flag):
    return flags().get(flag, False)

def enable_flag(flag):
    flags.update(lambda f: {**f, flag: True})

def disable_flag(flag):
    flags.update(lambda f: {**f, flag: False})

# Usage
if is_enabled("new_dashboard"):
    return NewDashboard()
else:
    return OldDashboard()
```

---

## Troubleshooting

### Value Not Persisting?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Debugging Persistence Issues                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Check DevTools → Application → Local Storage                            │
│     ─────────────────────────────────────────────                           │
│     Is your key there?                                                      │
│     Is the value correct?                                                   │
│                                                                             │
│  2. Is storage full?                                                        │
│     ────────────────                                                        │
│     localStorage has a limit (~5MB)                                         │
│     Check: Object.keys(localStorage).forEach(k =>                           │
│              console.log(k, localStorage[k].length))                        │
│                                                                             │
│  3. Private/Incognito mode?                                                 │
│     ─────────────────────────                                               │
│     Some browsers disable storage in private mode                           │
│                                                                             │
│  4. Using session storage?                                                  │
│     ─────────────────────────                                               │
│     sessionStorage clears when tab closes!                                  │
│     Switch to storage="local" if you need persistence.                      │
│                                                                             │
│  5. Key typo?                                                               │
│     ────────────                                                            │
│     use_storage("theme")  vs  use_storage("Theme")                          │
│     Keys are case-sensitive!                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Storage Quota Exceeded?

```python
# Catch and handle storage errors
def safe_storage_set(key, value):
    try:
        storage.set(value)
    except Exception as e:
        # Storage might be full
        # Clear old data or notify user
        print(f"Storage error: {e}")
```

### Cross-Tab Not Syncing?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Cross-Tab Sync Troubleshooting                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Are you using localStorage? (not session)                               │
│     sessionStorage doesn't sync!                                            │
│                                                                             │
│  2. Are tabs on the same origin?                                            │
│     localhost:3000 ≠ localhost:3001                                         │
│     http://mysite.com ≠ https://mysite.com                                  │
│                                                                             │
│  3. Is the storage event firing?                                            │
│     window.addEventListener('storage', e => console.log(e))                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

| Feature | `localStorage` | `sessionStorage` |
|---------|----------------|------------------|
| Persistence | Forever | Until tab closes |
| Tab sync | ✅ Yes | ❌ No |
| Use for | Preferences, settings | Drafts, temp state |

**Key APIs:**
```python
# Create storage signal
signal = use_storage("key", default=value)
signal = use_storage("key", default=value, storage="session")

# Read
value = signal()

# Write (auto-saves!)
signal.set(new_value)
signal.update(lambda v: transform(v))
```

**Remember:**
- Values must be JSON-serializable
- Server renders with default (no storage access)
- localStorage syncs across tabs automatically
- sessionStorage is tab-isolated

