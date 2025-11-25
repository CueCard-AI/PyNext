# PyNext Hydration System

> How PyNext transfers reactive state from server to client

## Table of Contents

1. [Overview](#overview)
2. [How Hydration Works](#how-hydration-works)
3. [Hydration Primitives](#hydration-primitives)
4. [Signal Hydration](#signal-hydration)
5. [Resource Hydration](#resource-hydration)
6. [Store Hydration](#store-hydration)
7. [Payload Size Analysis](#payload-size-analysis)
8. [Performance Optimization](#performance-optimization)
9. [Debugging Hydration](#debugging-hydration)
10. [Best Practices](#best-practices)

---

## Overview

**Hydration** is the process of making server-rendered HTML interactive by attaching JavaScript event handlers and reactive state. PyNext's hydration system is inspired by SolidJS's fine-grained reactivity, ensuring only the necessary parts of the DOM are hydrated.

### Key Principles

1. **Server-First**: Data is fetched and resolved on the server
2. **No Double-Fetch**: Hydrated data doesn't refetch on client
3. **Fine-Grained**: Only reactive parts get JavaScript
4. **Minimal Payload**: Efficient serialization format

### The Hydration Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SERVER SIDE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Request arrives → Route matched via trie (O(1))                 │
│                                                                      │
│  2. Component renders                                                │
│     └─> Signals created with initial values                        │
│     └─> Resources fetch data (await)                                │
│     └─> Stores initialized                                          │
│                                                                      │
│  3. HTML generated                                                   │
│     └─> Elements rendered with data-pynext-* attributes             │
│     └─> Reactive values wrapped in markers                          │
│                                                                      │
│  4. Hydration script generated                                       │
│     └─> __pynext__.createSignal(...) calls                          │
│     └─> __pynext__.createResource(...) calls                        │
│     └─> __pynext__.createStore(...) calls                           │
│                                                                      │
│  5. Response sent (HTML + embedded script)                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │  HTML + Hydration Data
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT SIDE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Browser receives HTML                                            │
│     └─> Renders immediately (fast First Paint)                      │
│                                                                      │
│  2. signals.js loads                                                 │
│     └─> Reactive runtime initialized                                │
│     └─> createSignal, createEffect, etc. available                  │
│                                                                      │
│  3. resource.js loads                                                │
│     └─> Resource primitive available                                │
│     └─> Async data fetching ready                                   │
│                                                                      │
│  4. Hydration script executes                                        │
│     └─> Signals created with server values                          │
│     └─> Resources hydrated (state = READY, no refetch!)             │
│     └─> DOM nodes connected to signals                              │
│                                                                      │
│  5. Page is interactive!                                             │
│     └─> Signal updates trigger DOM updates                          │
│     └─> Events work (onclick, onsubmit, etc.)                       │
│     └─> Resources can refetch, mutate                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## How Hydration Works

### Step 1: Server Renders HTML with Markers

When a component with reactive state renders, PyNext embeds special markers:

```python
# Python component
@page
def Counter():
    count = Signal(0, name="count")
    return div()[
        span(data_pynext_signal="count")[count],
        button(onclick="__pynext__.getSignal('count')[1](c => c + 1)")["Increment"]
    ]
```

Generates:

```html
<div>
  <span data-pynext-signal="count">0</span>
  <button onclick="__pynext__.getSignal('count')[1](c => c + 1)">Increment</button>
</div>
```

### Step 2: Hydration Script is Embedded

At the end of the HTML, PyNext injects the hydration data:

```html
<script>
  // Runtime first
  // ... signals.js content ...
  // ... resource.js content ...
  
  // Then hydration data
  __pynext__.createSignal('count', 0);
  __pynext__.createResource('users', { state: 'ready', data: [...] });
</script>
```

### Step 3: Client Connects DOM to State

When the script executes:

1. `createSignal('count', 0)` creates a reactive signal
2. The runtime finds `[data-pynext-signal="count"]` elements
3. Updates to the signal automatically update those DOM nodes

```javascript
// After hydration
const [count, setCount] = __pynext__.getSignal('count');
setCount(5);  // DOM automatically updates to show "5"
```

---

## Hydration Primitives

### Signal

The basic reactive primitive. Holds a single value and notifies subscribers on change.

**Server (Python):**
```python
count = Signal(0, name="count")
```

**Hydration Output:**
```javascript
__pynext__.createSignal('sig_abc123', 0);
```

**Payload:** ~40-60 bytes per signal

---

### Resource

Async data with loading/error states. The key benefit: **server-resolved data doesn't refetch on client**.

**Server (Python):**
```python
async def fetch_users():
    return await db.get_users()

users = Resource(fetch_users, name="users")
await users.fetch()  # Resolved on server
```

**Hydration Output:**
```javascript
__pynext__.createResource("resource_def456", {
  state: "ready",
  data: [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
  error: null,
  fetchedAt: 1764059713.898508
});
```

**Payload:** ~100-200 bytes + data size

---

### Store

Nested reactive objects. Each property is independently reactive.

**Server (Python):**
```python
user = Store({"name": "Alice", "settings": {"theme": "dark"}})
```

**Hydration Output:**
```javascript
__pynext__.createStore('store_ghi789', {
  name: "Alice",
  settings: { theme: "dark" }
});
```

**Payload:** ~50 bytes + data size

---

## Signal Hydration

### Basic Signal

```python
# Python
count = Signal(42, name="counter")
```

```javascript
// Generated JS
__pynext__.createSignal('counter', 42);
```

### Signal with DOM Binding

```python
# Python
name = Signal("World", name="name")
return h1()[f"Hello, {name}"]
```

```html
<!-- Generated HTML -->
<h1>Hello, <span data-pynext-signal="name">World</span></h1>

<script>
__pynext__.createSignal('name', 'World');
</script>
```

### Signal in Attributes

```python
# Python
is_active = Signal(True, name="active")
return div(class_=lambda: "active" if is_active() else "inactive")
```

```html
<!-- Generated HTML -->
<div class="active" data-pynext-attr='{"class": "active"}'>...</div>
```

---

## Resource Hydration

### Resource States

Resources can be in one of five states:

| State | Description | Client Behavior |
|-------|-------------|-----------------|
| `unresolved` | Not yet fetched | Will fetch on access |
| `pending` | Currently fetching | Shows loading state |
| `ready` | Data available | Uses cached data |
| `refreshing` | Refetching | Shows stale data + loading |
| `errored` | Fetch failed | Shows error state |

### Ready State (Most Common)

When the server resolves a resource, it's hydrated as `ready`:

```python
# Server
users = Resource(fetch_users)
await users.fetch()  # Fetched on server
```

```javascript
// Client - NO REFETCH NEEDED!
__pynext__.createResource("users", {
  state: "ready",
  data: [{"id": 1, "name": "Alice"}],
  error: null,
  fetchedAt: 1764059713
});

// Client can immediately use the data
const users = __pynext__.getResource("users");
console.log(users());  // [{"id": 1, "name": "Alice"}]
console.log(users.loading);  // false
```

### Error State

Errors are also serialized:

```python
# Server - fetch failed
try:
    await users.fetch()
except Exception:
    pass  # Error captured in resource
```

```javascript
// Client receives error state
__pynext__.createResource("users", {
  state: "errored",
  data: null,
  error: "Connection refused",
  fetchedAt: null
});

// Client can retry
const users = __pynext__.getResource("users");
console.log(users.error);  // "Connection refused"
await users.refetch();  // Try again
```

### Resource with Reactive Source

When a resource depends on a signal:

```python
# Server
user_id = Signal(42, name="user_id")
user = Resource(fetch_user, source=user_id, name="user")
await user.fetch()
```

```javascript
// Client
__pynext__.createSignal('user_id', 42);
__pynext__.createResource("user", {
  state: "ready",
  data: {"id": 42, "name": "Alice"},
  error: null,
  fetchedAt: 1764059713
});

// When user_id changes, resource refetches
const [userId, setUserId] = __pynext__.getSignal('user_id');
setUserId(123);  // Triggers user.refetch()
```

---

## Store Hydration

### Basic Store

```python
# Server
settings = Store({
    "theme": "dark",
    "fontSize": 14,
    "notifications": {"email": True, "push": False}
})
```

```javascript
// Client
__pynext__.createStore('settings', {
  theme: "dark",
  fontSize: 14,
  notifications: { email: true, push: false }
});

// Granular updates
const settings = __pynext__.getStore('settings');
settings.theme = "light";  // Only theme subscribers notified
```

### Nested Reactivity

Stores support deep reactivity:

```javascript
// This works!
settings.notifications.email = false;
// Only components using notifications.email update
```

---

## Payload Size Analysis

### Typical Page Scenarios

| Scenario | Hydration Size | With Gzip |
|----------|----------------|-----------|
| Simple page (2 signals) | ~200 bytes | ~80 bytes |
| Form page (5 signals, 1 store) | ~500 bytes | ~150 bytes |
| Dashboard (3 resources, 5 signals) | ~2 KB | ~400 bytes |
| Data table (1 resource, 100 rows) | ~18 KB | ~1.5 KB |

### Signal vs Resource Overhead

```
Data: {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

Signal:   106 bytes  → Just the data
Resource: 183 bytes  → Data + state management
─────────────────────
Overhead: +77 bytes  → For loading, error, refetch, mutate
```

### What the Overhead Buys You

| Feature | Signal | Resource |
|---------|--------|----------|
| Data storage | ✓ | ✓ |
| Reactivity | ✓ | ✓ |
| Loading state | ✗ | ✓ |
| Error handling | ✗ | ✓ |
| Refetch capability | ✗ | ✓ |
| Optimistic updates | ✗ | ✓ |
| Cache invalidation | ✗ | ✓ |

### Compression Impact

PyNext uses gzip compression by default:

```
Uncompressed:  17.71 KB (100 products)
Compressed:     1.35 KB
Ratio:          92% reduction!
```

---

## Performance Optimization

### 1. Minimize Serialized Data

```python
# ❌ Bad: Serialize entire user object
user = Resource(lambda: fetch_user_full())  # 50 fields

# ✓ Good: Only serialize what's needed
user = Resource(lambda: fetch_user_summary())  # 5 fields
```

### 2. Use Stores for Complex Objects

```python
# ❌ Bad: Many separate signals
name = Signal("Alice")
email = Signal("alice@example.com")
avatar = Signal("/avatar.jpg")

# ✓ Good: One store
user = Store({"name": "Alice", "email": "...", "avatar": "..."})
```

### 3. Avoid Redundant Resources

```python
# ❌ Bad: Same data fetched twice
users_list = Resource(fetch_users)
users_count = Resource(lambda: len(fetch_users()))

# ✓ Good: Derive from single resource
users = Resource(fetch_users)
# Use users()[:5] for list, len(users()) for count
```

### 4. Enable Compression

Compression is enabled by default in production. Verify in config:

```python
# pynext.config.py
config = {
    "compression": True,  # Default
    "compression_min_size": 500,  # Bytes
}
```

### 5. Use Resource Caching

```python
# Resource with TTL (won't refetch if fresh)
users = Resource(fetch_users, cache_ttl=300)  # 5 minutes
```

---

## Debugging Hydration

### View Hydration Data

In browser DevTools, access the PyNext runtime:

```javascript
// View all signals
console.log(__pynext__.signals);

// View all resources
console.log(__pynext__.resources);

// View all stores
console.log(__pynext__.stores);

// Check specific resource state
const users = __pynext__.getResource('users');
console.log({
  data: users(),
  loading: users.loading,
  error: users.error,
  state: users.state
});
```

### Debug Mode

Enable debug mode for verbose logging:

```python
# pynext.config.py
config = {
    "debug": True,
}
```

This adds:
- `Server-Timing` header with render times
- Detailed hydration logs in console
- `/__pynext__/debug/hydration` endpoint

### Hydration Mismatch

If the client state doesn't match server:

```javascript
// Check for mismatches
__pynext__.debug.checkHydration();
// Logs any differences between server HTML and client state
```

### Network Tab

In Chrome DevTools Network tab:
1. Find the initial HTML request
2. Look for the `<script>` containing `__pynext__`
3. View the hydration payload size

---

## Best Practices

### 1. Name Your Signals

```python
# ❌ Anonymous signal (auto-generated ID)
count = Signal(0)

# ✓ Named signal (predictable, debuggable)
count = Signal(0, name="item_count")
```

### 2. Fetch on Server When Possible

```python
# ✓ Server fetch - no client waterfall
@page
async def UserProfile():
    user = Resource(fetch_user)
    await user.fetch()  # Resolved before HTML sent
    return div()[user()["name"]]
```

### 3. Handle Loading States

```python
# ✓ Always provide fallbacks
@page
async def Dashboard():
    data = Resource(fetch_data)
    
    if data.loading():
        return Loading()
    if data.error():
        return Error(data.error())
    return DataTable(data())
```

### 4. Use Optimistic Updates

```python
# Client-side optimistic update
@server_action
async def save_user(user):
    return await db.save(user)

# In component
async def handle_save():
    # Optimistic update (instant UI)
    user.mutate(new_data)
    
    # Then sync with server
    try:
        await save_user(new_data)
    except:
        user.refetch()  # Revert on error
```

### 5. Group Related Data

```python
# ✓ Single resource for related data
page_data = Resource(lambda: {
    "user": fetch_user(),
    "posts": fetch_posts(),
    "comments": fetch_comments()
})

# Instead of 3 separate resources with 3x overhead
```

---

## Related Documentation

- [State Management](./STATE_MANAGEMENT.md) - Signals, Stores, Computed
- [Server Actions](./SERVER_ACTIONS.md) - Server-side functions
- [API Routes](./API_ROUTES.md) - REST endpoints
- [State & Data Integration](./STATE_DATA_INTEGRATION.md) - Full data flow

---

## Demo Script

Run the hydration impact demo:

```bash
python tests/demos/demo_resource_hydration.py
```

This shows:
- Payload sizes for different scenarios
- Compression ratios
- Signal vs Resource comparison
- Timeline visualization

