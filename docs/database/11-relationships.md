# PyNext Bidirectional Relationships

Complete guide to PyNext's relationship system with automatic bidirectional sync. Define relationships once, and both sides stay in sync automatically.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [API Reference](#api-reference)
5. [Sync Behavior](#sync-behavior)
6. [Collection Operations](#collection-operations)
7. [Configuration Options](#configuration-options)
8. [Common Patterns](#common-patterns)
9. [Performance](#performance)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### What Problem Does This Solve?

Without bidirectional sync, you have to manually keep both sides of a relationship in sync:

```python
# Without backref - TEDIOUS AND ERROR-PRONE
user.posts.append(post)
post.author = user  # Must remember to do this too!
post.author_id = user.id  # And update the FK!

# Moving a post to a new user
old_user.posts.remove(post)  # Remember to remove from old
new_user.posts.append(post)  # Add to new
post.author = new_user  # Update belongs_to
post.author_id = new_user.id  # Update FK
```

### The PyNext Solution

With `backref`, one line does it all:

```python
# With backref - STUPID SIMPLE
user.posts.append(post)  # Automatically sets post.author = user

# Moving a post - just reassign
post.author = new_user  # Automatically removes from old user.posts, adds to new
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Automatic Sync** | Modify one side, the other updates automatically |
| **Loop Prevention** | Smart guards prevent infinite recursion |
| **Lazy Resolution** | Forward references work seamlessly |
| **Fine-grained** | Only affected objects are touched (SolidJS principle) |
| **AI-friendly** | Explicit, traceable behavior for easy debugging |

---

## Quick Start

### Option 1: backref (Auto-creates reverse)

The simplest approach - define on one side, get both:

```python
from pynext.db import Table, has_many
from typing import List

class User(Table):
    name: str
    posts: List["Post"] = has_many("Post", backref="author")
    # ↑ Automatically creates Post.author

class Post(Table):
    title: str
    user_id: int
    # author is auto-created by backref!

# Usage
user = User(name="John")
post = Post(title="Hello World")

# Append to has_many → sets belongs_to
user.posts.append(post)
assert post.author is user  # ✅ Auto-synced!

# Set belongs_to → adds to has_many
post2 = Post(title="Second Post")
post2.author = user
assert post2 in user.posts  # ✅ Auto-synced!
```

### Option 2: back_populates (Explicit both sides)

For more control, define both sides explicitly:

```python
from pynext.db import Table, has_many, belongs_to
from typing import List

class User(Table):
    name: str
    posts: List["Post"] = has_many("Post", back_populates="author")

class Post(Table):
    title: str
    user_id: int
    author: "User" = belongs_to("User", back_populates="posts")

# Works the same way
user.posts.append(post)
assert post.author is user  # ✅
```

---

## Core Concepts

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BIDIRECTIONAL SYNC ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐         ┌──────────────┐                          │
│  │    User      │◄───────►│    Post      │                          │
│  │              │         │              │                          │
│  │ posts: [...]────backref────►author   │                          │
│  └──────────────┘         └──────────────┘                          │
│         │                        │                                   │
│         ▼                        ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               RelationshipSyncManager                        │    │
│  │                                                              │    │
│  │  • Tracks bidirectional pairs (BackrefRegistry)              │    │
│  │  • Manages update propagation                                │    │
│  │  • Prevents infinite loops (update_guard)                    │    │
│  │  • Fine-grained: only touches affected objects               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               SyncedList (Collection)                        │    │
│  │                                                              │    │
│  │  • Wraps list operations                                     │    │
│  │  • Triggers sync on: append, remove, extend, clear, etc.     │    │
│  │  • Supports all MutableSequence methods                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### How Sync Works

1. **User calls `user.posts.append(post)`**
2. **SyncedList** receives the append
3. SyncedList adds `post` to internal list
4. SyncedList calls **RelationshipSyncManager.sync_has_many_append()**
5. Sync manager checks **update_guard** (prevents loops)
6. Sync manager sets `post.author = user`
7. **BelongsTo.__set__** is called
8. BelongsTo checks update_guard → **already guarded, skips sync**
9. Done! No infinite loop.

### The Update Guard

The guard prevents infinite recursion using a `ContextVar`:

```python
# Pseudocode of the guard logic
def sync_has_many_append(owner, attr, item):
    key = (id(owner), attr)
    
    if key in guard_set:
        return  # Already syncing this, skip!
    
    guard_set.add(key)
    try:
        # Do the sync (set item.author = owner)
        ...
    finally:
        guard_set.remove(key)
```

---

## API Reference

### Relationship Functions

#### `has_many(model, foreign_key=None, backref=None, back_populates=None)`

Define a one-to-many relationship.

```python
class User(Table):
    # Basic
    posts: List["Post"] = has_many("Post")
    
    # With auto-created reverse (recommended)
    posts: List["Post"] = has_many("Post", backref="author")
    
    # With custom foreign key
    articles: List["Article"] = has_many("Article", foreign_key="writer_id", backref="writer")
    
    # With explicit bidirectional
    comments: List["Comment"] = has_many("Comment", back_populates="user")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `str` or `Type[Table]` | Related model class or name |
| `foreign_key` | `str` | FK field on related model (auto-detected if not provided) |
| `backref` | `str` | Name for auto-created reverse relationship |
| `back_populates` | `str` | Name of existing reverse relationship |

#### `belongs_to(model, foreign_key=None, backref=None, back_populates=None)`

Define a many-to-one relationship.

```python
class Post(Table):
    user_id: int
    
    # Basic
    author: "User" = belongs_to("User")
    
    # With auto-created reverse
    author: "User" = belongs_to("User", backref="posts")
    
    # With explicit bidirectional
    author: "User" = belongs_to("User", back_populates="posts")
```

#### `has_one(model, foreign_key=None, backref=None, back_populates=None)`

Define a one-to-one relationship.

```python
class User(Table):
    # With auto-created reverse
    profile: "Profile" = has_one("Profile", backref="user")
```

### SyncedList Methods

When backref is enabled, `has_many` returns a `SyncedList` instead of a regular list. It supports all standard list operations:

| Method | Syncs? | Description |
|--------|--------|-------------|
| `append(item)` | ✅ | Add item, set belongs_to |
| `remove(item)` | ✅ | Remove item, unset belongs_to |
| `extend(items)` | ✅ | Add all items, set belongs_to on each |
| `clear()` | ✅ | Remove all, unset belongs_to on each |
| `pop(index=-1)` | ✅ | Remove and return item |
| `insert(index, item)` | ✅ | Insert at position |
| `__setitem__(i, v)` | ✅ | Replace item at index |
| `__delitem__(i)` | ✅ | Delete item at index |
| `sort()` | ❌ | Sort in place (no sync needed) |
| `reverse()` | ❌ | Reverse in place (no sync needed) |
| `copy()` | ❌ | Return regular list copy |
| `to_list()` | ❌ | Convert to regular list |

### BackrefConfig

Configuration for backref relationships:

```python
from pynext.db import BackrefConfig

config = BackrefConfig(
    name="author",                    # Reverse relationship name
    source_model=User,                # Model with has_many
    source_attr="posts",              # has_many attribute
    target_model=Post,                # Model with belongs_to
    target_attr="author",             # belongs_to attribute
    foreign_key="author_id",          # FK field
    cascade_add=True,                 # Sync on add (default: True)
    cascade_remove=True,              # Sync on remove (default: True)
)
```

---

## Sync Behavior

### has_many Operations

```python
class User(Table):
    posts: List["Post"] = has_many("Post", backref="author")

class Post(Table):
    title: str
    user_id: int

user = User(name="John")
post = Post(title="Hello")

# APPEND → sets belongs_to
user.posts.append(post)
assert post.author is user
assert post in user.posts

# REMOVE → unsets belongs_to
user.posts.remove(post)
assert post.author is None
assert post not in user.posts

# EXTEND → sets all belongs_to
posts = [Post(title=f"P{i}") for i in range(5)]
user.posts.extend(posts)
assert all(p.author is user for p in posts)

# CLEAR → unsets all belongs_to
user.posts.clear()
assert all(p.author is None for p in posts)

# POP → returns item, unsets belongs_to
user.posts.append(Post(title="Temp"))
popped = user.posts.pop()
assert popped.author is None

# INSERT → sets belongs_to
new_post = Post(title="Inserted")
user.posts.insert(0, new_post)
assert new_post.author is user
```

### belongs_to Operations

```python
# SET → adds to has_many
post.author = user
assert post in user.posts

# REPLACE → moves between collections
user2 = User(name="Jane")
post.author = user2
assert post not in user.posts   # Removed from old
assert post in user2.posts      # Added to new

# SET NONE → removes from has_many
post.author = None
assert post not in user2.posts
```

### has_one Operations

```python
class User(Table):
    profile: "Profile" = has_one("Profile", backref="user")

class Profile(Table):
    bio: str
    user_id: int

user = User(name="John")
profile = Profile(bio="Hello")

# SET → sets belongs_to
user.profile = profile
assert profile.user is user

# REPLACE → updates both old and new
profile2 = Profile(bio="New")
user.profile = profile2
assert profile.user is None      # Old unset
assert profile2.user is user     # New set

# SET NONE → unsets belongs_to
user.profile = None
assert profile2.user is None
```

---

## Collection Operations

### SyncedList is a Full List

`SyncedList` implements `MutableSequence`, so all list operations work:

```python
# Indexing
first_post = user.posts[0]
user.posts[-1] = new_post

# Slicing
recent = user.posts[-5:]
user.posts[0:3] = new_posts

# Iteration
for post in user.posts:
    print(post.title)

# Membership
if post in user.posts:
    ...

# Length
count = len(user.posts)

# Boolean
if user.posts:  # True if not empty
    ...

# Equality
if user.posts == other_posts:
    ...

# Arithmetic
combined = user.posts + other_list
user.posts += new_posts  # Same as extend

# Index lookup
idx = user.posts.index(post)
count = user.posts.count(post)

# Sorting (no sync)
user.posts.sort(key=lambda p: p.title)
user.posts.reverse()
```

### Converting to Regular List

```python
# Get a regular list (no sync)
regular_list = user.posts.to_list()
regular_list = user.posts.copy()
regular_list = list(user.posts)
```

---

## Configuration Options

### Disabling Cascade

You can disable automatic sync for specific operations:

```python
# Currently, cascade options are set at BackrefConfig level
# In future versions, you may be able to configure per-operation

# For now, if you need to bypass sync:
user.posts._items.append(post)  # Direct list access (no sync)
```

### Custom Foreign Keys

```python
class Article(Table):
    title: str
    writer_id: int  # Non-standard FK name

class Author(Table):
    name: str
    articles: List["Article"] = has_many(
        "Article", 
        foreign_key="writer_id",  # Specify FK
        backref="writer"
    )

# Now Article.writer uses writer_id
article.writer = author
assert article.writer_id == author.id  # FK updated
```

---

## Common Patterns

### Blog with Users, Posts, Comments

```python
class User(Table):
    name: str
    email: str
    posts: List["Post"] = has_many("Post", backref="author")
    comments: List["Comment"] = has_many("Comment", backref="author")

class Post(Table):
    title: str
    content: str
    author_id: int
    comments: List["Comment"] = has_many("Comment", backref="post")

class Comment(Table):
    content: str
    author_id: int
    post_id: int

# Usage
user = User(name="John", email="john@example.com")
post = Post(title="Hello", content="...")
comment = Comment(content="Great post!")

user.posts.append(post)           # post.author = user
post.comments.append(comment)     # comment.post = post
comment.author = user             # Added to user.comments
```

### E-commerce Orders

```python
class Customer(Table):
    name: str
    orders: List["Order"] = has_many("Order", backref="customer")

class Order(Table):
    total: float
    customer_id: int
    items: List["OrderItem"] = has_many("OrderItem", backref="order")

class OrderItem(Table):
    quantity: int
    price: float
    order_id: int
    product_id: int

class Product(Table):
    name: str
    price: float
    order_items: List["OrderItem"] = has_many("OrderItem", backref="product")

# Creating an order
customer = Customer(name="Jane")
order = Order(total=0)
customer.orders.append(order)

# Adding items
item1 = OrderItem(quantity=2, price=10.00, product_id=1)
item2 = OrderItem(quantity=1, price=25.00, product_id=2)
order.items.extend([item1, item2])

# All relationships are synced
assert item1.order is order
assert order in customer.orders
```

### Self-Referential (Tree Structure)

```python
class Category(Table):
    name: str
    parent_id: Optional[int] = None
    children: List["Category"] = has_many(
        "Category", 
        foreign_key="parent_id", 
        backref="parent"
    )

# Building a tree
root = Category(name="Root")
child1 = Category(name="Child 1")
child2 = Category(name="Child 2")
grandchild = Category(name="Grandchild")

root.children.extend([child1, child2])
child1.children.append(grandchild)

# Navigation
assert grandchild.parent is child1
assert child1.parent is root
assert root.parent is None
```

### Employee Manager Hierarchy

```python
class Employee(Table):
    name: str
    manager_id: Optional[int] = None
    reports: List["Employee"] = has_many(
        "Employee",
        foreign_key="manager_id",
        backref="manager"
    )

ceo = Employee(name="CEO")
vp = Employee(name="VP")
dev = Employee(name="Developer")

ceo.reports.append(vp)
vp.reports.append(dev)

assert dev.manager is vp
assert vp.manager is ceo
```

---

## Performance

### Benchmarks

| Operation | 1000 items | Notes |
|-----------|-----------|-------|
| `extend([items])` | ~50ms | Batch is faster than loop |
| `append` × 1000 | ~100ms | Avoid in hot paths |
| `clear()` | ~30ms | Single operation |
| Iteration | ~5ms | Just like regular list |

### Recommendations

1. **Use `extend()` for bulk adds**
   ```python
   # Good
   user.posts.extend(new_posts)
   
   # Slower
   for post in new_posts:
       user.posts.append(post)
   ```

2. **Use `clear()` instead of loop remove**
   ```python
   # Good
   user.posts.clear()
   
   # Slower
   while user.posts:
       user.posts.pop()
   ```

3. **Access raw list for read-only operations**
   ```python
   # If you just need to iterate without modification
   for post in user.posts._items:  # Skips SyncedList wrapper
       print(post.title)
   ```

---

## Troubleshooting

### Common Issues

#### 1. "Backref not working"

**Problem:** Setting `post.author = user` doesn't add to `user.posts`.

**Solution:** Make sure backref is defined:

```python
# Wrong - no backref
posts: List["Post"] = has_many("Post")

# Right - with backref
posts: List["Post"] = has_many("Post", backref="author")
```

#### 2. "Forward reference not resolved"

**Problem:** `"Post"` string isn't being resolved to the class.

**Solution:** Ensure the model is defined and registered:

```python
# Define both models in same file or ensure imports
class User(Table):
    posts: List["Post"] = has_many("Post", backref="author")

class Post(Table):  # Must be defined!
    user_id: int
```

#### 3. "Infinite loop / RecursionError"

**Problem:** This shouldn't happen with the guard, but if it does:

**Solution:** Check for custom `__setattr__` overrides that bypass the guard.

#### 4. "Item not removed from old collection"

**Problem:** When reassigning `post.author`, it's not removed from old user's posts.

**Solution:** This should work automatically. Check:
- Both sides have backref/back_populates
- The old user's posts was a SyncedList (not regular list)

### Debug Logging

Enable debug output:

```python
import logging
logging.getLogger("pynext.db.relationships").setLevel(logging.DEBUG)

# Now operations will log:
# DEBUG: sync_belongs_to_set: post.author = user (old=None, new=user)
# DEBUG: _add_to_collection: user.posts += post
```

### Testing Relationships

```python
import pytest
from pynext.db import reset_backref_registry, reset_sync_manager

@pytest.fixture
def clean_state():
    """Reset relationship state between tests."""
    reset_backref_registry()
    reset_sync_manager()
    yield
    reset_backref_registry()
    reset_sync_manager()

def test_backref_sync(clean_state):
    class User(Table):
        posts: List["Post"] = has_many("Post", backref="author")
    
    class Post(Table):
        user_id: int
    
    user = User(name="Test")
    post = Post(title="Test")
    
    user.posts.append(post)
    
    assert post.author is user
    assert post in user.posts
```

---

## API Quick Reference

```python
from pynext.db import (
    # Relationship functions
    has_many,
    belongs_to,
    has_one,
    
    # Descriptor classes
    HasMany,
    BelongsTo,
    HasOne,
    
    # Backref management
    BackrefConfig,
    BackrefRegistry,
    RelationshipSyncManager,
    get_backref_registry,
    get_sync_manager,
    reset_backref_registry,
    reset_sync_manager,
    
    # Collection
    SyncedList,
)
```

---

## Summary

PyNext's bidirectional relationships provide:

- **Simple API**: Just add `backref="name"` to enable sync
- **Automatic sync**: Modify one side, the other updates
- **No boilerplate**: No manual FK updates or collection management
- **Full list support**: SyncedList works like a regular Python list
- **Safe**: Update guard prevents infinite loops
- **AI-friendly**: Explicit behavior that's easy to understand and debug

For most use cases, the simple pattern is:

```python
class Parent(Table):
    children: List["Child"] = has_many("Child", backref="parent")

class Child(Table):
    parent_id: int

# Now parent.children and child.parent stay in sync automatically!
```

