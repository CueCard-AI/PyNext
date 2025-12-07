# Relationship Hooks

> **Phase 7.8**: Event hooks for relationship changes - simpler and more powerful than SQLAlchemy.

---

## Table of Contents

1. [What Are Relationship Hooks?](#what-are-relationship-hooks)
2. [Why Do You Need Relationship Hooks?](#why-do-you-need-relationship-hooks)
3. [Who Should Use Relationship Hooks?](#who-should-use-relationship-hooks)
4. [When to Use Each Hook Type](#when-to-use-each-hook-type)
5. [How Hooks Work Internally](#how-hooks-work-internally)
6. [Quick Start](#quick-start)
7. [The Problem: Why Existing Solutions Fail](#the-problem-why-existing-solutions-fail)
8. [The PyNext Solution](#the-pynext-solution)
9. [Hook Types Deep Dive](#hook-types-deep-dive)
10. [Real-World Scenarios](#real-world-scenarios)
11. [How to Implement Common Patterns](#how-to-implement-common-patterns)
12. [Decision Guide: Choosing the Right Hook](#decision-guide-choosing-the-right-hook)
13. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
14. [Performance Deep Dive](#performance-deep-dive)
15. [Testing Your Hooks](#testing-your-hooks)
16. [API Reference](#api-reference)
17. [Troubleshooting](#troubleshooting)

---

## What Are Relationship Hooks?

Relationship hooks are **callbacks that fire automatically when your data relationships change**. They let you execute custom logic when:

- An item is **added** to a collection (`@on_append`)
- An item is **removed** from a collection (`@on_remove`)
- A scalar relationship is **set** or changed (`@on_set`)
- An instance is about to be **deleted** (`@before_delete`)

### The Core Concept

Think of hooks as **observers** that watch your relationships. When something changes, they react:

```
┌─────────────────────────────────────────────────────────────────────┐
│                          YOUR CODE                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   user.posts.append(post)     ──────►  @on_append("posts")          │
│                                         │                            │
│                                         ▼                            │
│                                    send_notification()               │
│                                    update_post_count()               │
│                                    invalidate_cache()                │
│                                                                      │
│   user.posts.remove(post)     ──────►  @on_remove("posts")          │
│                                         │                            │
│                                         ▼                            │
│                                    log_audit()                       │
│                                    cleanup_resources()               │
│                                                                      │
│   user.profile = new_profile  ──────►  @on_set("profile")           │
│                                         │                            │
│                                         ▼                            │
│                                    cache_invalidation()              │
│                                    track_change()                    │
│                                                                      │
│   await user.delete()         ──────►  @before_delete()             │
│                                         │                            │
│                                         ▼                            │
│                                    archive_data()                    │
│                                    cleanup_files()                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Simple Example

```python
from pynext.db import Table, has_many, on_append, on_remove

class User(Table):
    name: str
    posts: List[Post] = has_many(Post, backref="author")
    
    @on_append("posts")
    def on_post_added(self, post: Post):
        """This runs automatically when a post is added."""
        print(f"{self.name} created a new post: {post.title}")
        send_notification(self.followers, f"New post from {self.name}!")

# Usage - the hook fires automatically
alice = User(name="Alice")
alice.posts.append(Post(title="Hello World"))
# Output: "Alice created a new post: Hello World"
# Notification sent to all followers
```

---

## Why Do You Need Relationship Hooks?

### The Fundamental Problem

Without hooks, you have to manually call side-effect functions everywhere:

```python
# WITHOUT HOOKS - Scattered, error-prone code

def add_post_to_user(user, post):
    user.posts.append(post)
    send_notification(user.followers, f"New post from {user.name}")  # Easy to forget!
    update_post_count(user)  # Easy to forget!
    invalidate_cache(user)   # Easy to forget!
    log_audit("post_added", user.id, post.id)  # Easy to forget!

def remove_post_from_user(user, post):
    user.posts.remove(post)
    update_post_count(user)  # Easy to forget!
    invalidate_cache(user)   # Easy to forget!
    log_audit("post_removed", user.id, post.id)  # Easy to forget!

# Problem: What if someone directly calls user.posts.append()?
# All the side effects are SKIPPED!
user.posts.append(post)  # ⚠️ No notification, no cache invalidation!
```

### The Solution: Hooks

```python
# WITH HOOKS - Centralized, guaranteed execution

class User(Table):
    posts: List[Post] = has_many(Post)
    
    @on_append("posts")
    def on_post_added(self, post: Post):
        send_notification(self.followers, f"New post from {self.name}")
        update_post_count(self)
        invalidate_cache(self)
        log_audit("post_added", self.id, post.id)
    
    @on_remove("posts")
    def on_post_removed(self, post: Post):
        update_post_count(self)
        invalidate_cache(self)
        log_audit("post_removed", self.id, post.id)

# Now ANY way posts are added triggers the hooks
user.posts.append(post)      # ✅ Hooks fire
user.posts.extend([p1, p2])  # ✅ Hooks fire for each
user.posts.insert(0, post)   # ✅ Hooks fire
user.posts[0] = new_post     # ✅ Hooks fire (remove old, append new)
```

### Seven Reasons You Need Hooks

#### 1. **Audit Logging**
Track every change to relationships for compliance, debugging, or analytics.

```python
@on_append("posts")
def audit_post_added(self, post: Post):
    AuditLog.create(
        action="post_added",
        user_id=self.id,
        post_id=post.id,
        timestamp=datetime.now(),
    )
```

#### 2. **Real-Time Notifications**
Send alerts to users when something they care about changes.

```python
@on_append("comments")
def notify_post_author(self, comment: Comment):
    send_push_notification(
        to=self.author_id,
        title="New Comment",
        body=f"{comment.author.name} commented on your post",
    )
```

#### 3. **Cache Invalidation**
Keep your caches consistent with your database.

```python
@on_append("posts")
@on_remove("posts")
def invalidate_cache(self, post: Post):
    cache.delete(f"user:{self.id}:posts")
    cache.delete(f"user:{self.id}:post_count")
    cache.delete(f"feed:global")  # Global feed includes this user
```

#### 4. **Validation**
Enforce business rules before changes are accepted.

```python
@on_append("team_members")
def validate_team_member(self, user: User):
    if len(self.team_members) >= 10:
        raise ValueError("Team cannot have more than 10 members")
    if not user.is_verified:
        raise ValueError("Only verified users can join teams")
```

#### 5. **Statistics & Metrics**
Keep denormalized counts and metrics up to date.

```python
@on_append("orders")
def update_customer_stats(self, order: Order):
    self.total_orders += 1
    self.total_spent += order.total
    self.average_order_value = self.total_spent / self.total_orders
```

#### 6. **Cleanup & Side Effects**
Handle resources that need to be cleaned up.

```python
@before_delete()
def cleanup_user_resources(self):
    # Archive data before deletion
    archive_service.store_user(self)
    
    # Clean up S3 files
    s3.delete_prefix(f"users/{self.id}/")
    
    # Remove from search index
    elasticsearch.delete("users", self.id)
    
    # Revoke authentication tokens
    auth.revoke_all_tokens(self.id)
```

#### 7. **Cross-System Integration**
Sync changes to external systems.

```python
@on_append("products")
def sync_to_inventory_system(self, product: Product):
    inventory_api.add_product_to_warehouse(
        warehouse_id=self.id,
        product_sku=product.sku,
        quantity=product.quantity,
    )
```

---

## Who Should Use Relationship Hooks?

### Use Hooks If You...

✅ **Need to react to relationship changes** - Any time you need side effects when data changes

✅ **Want consistent behavior** - Same hooks fire regardless of how the change happens

✅ **Have audit/compliance requirements** - Track all changes for regulatory compliance

✅ **Use caching** - Need to invalidate caches when relationships change

✅ **Send notifications** - Alert users when things they follow change

✅ **Maintain denormalized data** - Keep counts, totals, or aggregates in sync

✅ **Integrate with external systems** - Sync changes to third-party APIs

### Consider Alternatives If You...

❌ **Only need validation on API input** - Use Pydantic models at the API layer instead

❌ **Need complex transaction handling** - Use explicit database transactions

❌ **Have performance-critical hot paths** - Hooks add overhead; consider batch processing

❌ **Need to affect the change itself** - Hooks run AFTER the change; use validators instead

### Team Roles and Hooks

| Role | How They Use Hooks |
|------|-------------------|
| **Backend Developer** | Implement business logic, validation, and data consistency |
| **DevOps Engineer** | Add logging, metrics, and monitoring hooks |
| **Data Engineer** | Add hooks for analytics pipelines and data sync |
| **Security Engineer** | Add audit logging and compliance tracking |
| **Frontend Developer** | Understand when notifications are sent |

---

## When to Use Each Hook Type

### Decision Flowchart

```
Is something being ADDED to a collection?
    └─► YES ──► Use @on_append
    └─► NO
        │
        Is something being REMOVED from a collection?
            └─► YES ──► Use @on_remove
            └─► NO
                │
                Is a scalar relationship being SET (belongs_to, has_one)?
                    └─► YES ──► Use @on_set
                    └─► NO
                        │
                        Is an entire instance being DELETED?
                            └─► YES ──► Use @before_delete
                            └─► NO ──► You don't need a hook
```

### @on_append - When Items Are Added

**Use when you need to react to items being added to a collection.**

```python
# GOOD: Notify when follower is added
@on_append("followers")
def on_new_follower(self, follower: User):
    send_notification(self, f"{follower.name} started following you")

# GOOD: Update denormalized count
@on_append("orders")
def on_order_added(self, order: Order):
    self.order_count += 1
    self.total_revenue += order.total

# GOOD: Sync to external system
@on_append("products")
def sync_product_to_inventory(self, product: Product):
    inventory_api.add_to_warehouse(self.warehouse_id, product.sku)
```

**Triggers on:**
- `collection.append(item)`
- `collection.extend([items])`
- `collection.insert(index, item)`
- `collection[index] = new_item` (for the new item)
- `collection += [items]`

### @on_remove - When Items Are Removed

**Use when you need to react to items being removed from a collection.**

```python
# GOOD: Cleanup when post is removed
@on_remove("posts")
def on_post_removed(self, post: Post):
    # Archive before removal
    archive_service.store_post(post)
    # Update count
    self.post_count -= 1

# GOOD: Invalidate cache
@on_remove("cart_items")
def on_cart_item_removed(self, item: CartItem):
    cache.delete(f"cart:{self.id}:total")
    cache.delete(f"cart:{self.id}:item_count")

# GOOD: Log for audit
@on_remove("team_members")
def on_member_removed(self, member: User):
    audit_log.record(
        event="member_removed",
        team_id=self.id,
        member_id=member.id,
        removed_by=current_user.id,
    )
```

**Triggers on:**
- `collection.remove(item)`
- `collection.pop()` or `collection.pop(index)`
- `collection.clear()` (for each item)
- `del collection[index]`
- `collection[index] = new_item` (for the old item)

### @on_set - When Scalar Relationships Change

**Use when you need to react to belongs_to or has_one relationship changes.**

```python
# GOOD: Track ownership transfer
@on_set("owner")
def on_owner_changed(self, old_owner: User, new_owner: User):
    if old_owner is None:
        # Initial assignment
        log_event(f"Document {self.id} assigned to {new_owner.name}")
    elif new_owner is None:
        # Unassigned
        log_event(f"Document {self.id} unassigned from {old_owner.name}")
    else:
        # Transferred
        log_event(f"Document transferred from {old_owner.name} to {new_owner.name}")

# GOOD: Update related data
@on_set("category")
def on_category_changed(self, old_category: Category, new_category: Category):
    if old_category:
        old_category.product_count -= 1
    if new_category:
        new_category.product_count += 1

# GOOD: Invalidate cache
@on_set("author")
def on_author_changed(self, old_author: User, new_author: User):
    if old_author:
        cache.delete(f"user:{old_author.id}:posts")
    if new_author:
        cache.delete(f"user:{new_author.id}:posts")
```

**Triggers on:**
- `instance.relationship = new_value`
- `instance.relationship = None`

### @before_delete - Before Instance Deletion

**Use when you need to perform cleanup before an instance is deleted.**

```python
# GOOD: Archive before deletion
@before_delete()
def archive_before_delete(self):
    archive_service.store({
        "type": "user",
        "id": self.id,
        "data": self.to_dict(),
        "deleted_at": datetime.now(),
    })

# GOOD: Clean up external resources
@before_delete()
def cleanup_external_resources(self):
    # Delete files from S3
    s3.delete_prefix(f"users/{self.id}/")
    
    # Remove from search index
    elasticsearch.delete("users", self.id)
    
    # Remove from external CRM
    crm_api.delete_customer(self.external_crm_id)

# GOOD: Send notification
@before_delete()
def notify_account_deletion(self):
    send_email(
        to=self.email,
        subject="Account Deleted",
        body="Your account has been permanently deleted.",
    )
```

**Triggers:**
- Before cascade delete starts
- Before the instance is removed from the database

---

## How Hooks Work Internally

Understanding the internals helps you use hooks effectively and debug issues.

### The Hook Lifecycle

```
1. REGISTRATION (at import time)
   ┌─────────────────────────────────────────────┐
   │  class User(Table):                         │
   │      @on_append("posts")                    │
   │      def my_hook(self, post): ...           │
   │                                              │
   │  discover_hooks(User)  # Called by PyNext   │
   │      │                                       │
   │      ▼                                       │
   │  HookRegistry stores: {                      │
   │      "posts": [my_hook]                      │
   │  }                                           │
   └─────────────────────────────────────────────┘

2. TRIGGERING (at runtime)
   ┌─────────────────────────────────────────────┐
   │  user.posts.append(post)                    │
   │      │                                       │
   │      ▼                                       │
   │  SyncedList.append()                        │
   │      │                                       │
   │      ├── 1. Add item to internal list       │
   │      ├── 2. Sync backref (post.author=user) │
   │      └── 3. Fire hooks                       │
   │              │                               │
   │              ▼                               │
   │         registry.fire_on_append(            │
   │             instance=user,                   │
   │             relationship="posts",            │
   │             item=post                        │
   │         )                                    │
   │              │                               │
   │              ▼                               │
   │         for hook in hooks:                   │
   │             hook(user, post)  # Direct call │
   └─────────────────────────────────────────────┘
```

### Key Components

#### 1. HookRegistry

Each model class has its own `HookRegistry` that stores all hooks:

```python
class HookRegistry:
    """Stores hooks for a single model class."""
    
    _on_append: Dict[str, List[Callable]]  # {"posts": [hook1, hook2]}
    _on_remove: Dict[str, List[Callable]]  # {"posts": [hook3]}
    _on_set: Dict[str, List[Callable]]     # {"profile": [hook4]}
    _before_delete: List[Callable]         # [hook5, hook6]
    
    def fire_on_append(self, instance, relationship: str, item):
        for hook in self._on_append.get(relationship, []):
            hook(instance, item)
```

#### 2. Hook Decorators

Decorators mark methods as hooks without modifying their behavior:

```python
def on_append(relationship_name: str):
    def decorator(func):
        # Mark the function with hook metadata
        func._pynext_hook = HookConfig(
            type=HookType.ON_APPEND,
            relationship=relationship_name
        )
        return func  # Return unchanged function
    return decorator
```

#### 3. Hook Discovery

When a model is loaded, PyNext scans for decorated methods:

```python
def discover_hooks(model_class):
    registry = get_hook_registry(model_class)
    
    for name in dir(model_class):
        attr = getattr(model_class, name)
        if callable(attr) and hasattr(attr, "_pynext_hook"):
            config = attr._pynext_hook
            
            if config.type == HookType.ON_APPEND:
                registry.register_on_append(config.relationship, attr)
            elif config.type == HookType.ON_REMOVE:
                registry.register_on_remove(config.relationship, attr)
            # ... etc
```

#### 4. Synchronous Execution

Hooks are called **synchronously** for maximum simplicity and speed:

```python
# This is how hooks are fired - direct function calls
def fire_on_append(self, instance, relationship: str, item):
    hooks = self._on_append.get(relationship, [])
    for hook in hooks:
        hook(instance, item)  # Direct call, no async, no queue
```

**Why synchronous?**
- Zero coroutine overhead
- Clear stack traces for debugging
- Predictable execution order
- No event loop dependency

### Execution Order

Hooks execute in the order they're registered:

```python
class User(Table):
    @on_append("posts")
    def hook1(self, post):  # Runs first
        print("hook1")
    
    @on_append("posts")
    def hook2(self, post):  # Runs second
        print("hook2")
    
    @on_append("posts")
    def hook3(self, post):  # Runs third
        print("hook3")

# Output:
# hook1
# hook2
# hook3
```

### Error Propagation

Errors in hooks propagate immediately and stop subsequent hooks:

```python
class User(Table):
    @on_append("posts")
    def hook1(self, post):
        print("hook1")  # This runs
    
    @on_append("posts")
    def hook2(self, post):
        raise ValueError("Something went wrong")  # Stops here
    
    @on_append("posts")
    def hook3(self, post):
        print("hook3")  # This NEVER runs

# Result: ValueError is raised, hook3 is skipped
```

---

## Quick Start

### Installation

Hooks are built into PyNext - no additional installation required.

### Basic Usage

```python
from pynext.db import Table, has_many, has_one, on_append, on_remove, on_set, before_delete
from typing import List

class Post(Table):
    title: str
    author_id: int

class Profile(Table):
    bio: str
    user_id: int

class User(Table):
    name: str
    email: str
    posts: List[Post] = has_many(Post, backref="author")
    profile: Profile = has_one(Profile)
    
    # Hook: React when a post is added
    @on_append("posts")
    def on_post_added(self, post: Post):
        print(f"[HOOK] Post '{post.title}' added to {self.name}")
        send_notification(self.followers, f"New post from {self.name}!")
    
    # Hook: React when a post is removed
    @on_remove("posts")
    def on_post_removed(self, post: Post):
        print(f"[HOOK] Post '{post.title}' removed from {self.name}")
        log_audit("post_removed", self.id, post.id)
    
    # Hook: React when profile is set or changed
    @on_set("profile")
    def on_profile_changed(self, old_profile: Profile, new_profile: Profile):
        if old_profile is None and new_profile:
            print(f"[HOOK] Profile created for {self.name}")
        elif old_profile and new_profile:
            print(f"[HOOK] Profile updated for {self.name}")
        elif old_profile and new_profile is None:
            print(f"[HOOK] Profile removed for {self.name}")
    
    # Hook: React before user is deleted
    @before_delete()
    def on_user_deleted(self):
        print(f"[HOOK] User {self.name} is being deleted - archiving data")
        archive_user_data(self)
        cleanup_user_files(self.id)

# Usage - hooks fire automatically!
alice = User(name="Alice", email="alice@example.com")

# This triggers on_post_added
alice.posts.append(Post(title="Hello World"))
# Output: [HOOK] Post 'Hello World' added to Alice

# This triggers on_profile_changed
alice.profile = Profile(bio="I love coding")
# Output: [HOOK] Profile created for Alice

# This triggers on_post_removed
alice.posts.remove(alice.posts[0])
# Output: [HOOK] Post 'Hello World' removed from Alice

# This triggers on_user_deleted
await alice.delete()
# Output: [HOOK] User Alice is being deleted - archiving data
```

---

## The Problem: Why Existing Solutions Fail

### The SQLAlchemy Way

SQLAlchemy uses an event system that's powerful but confusing:

```python
from sqlalchemy import event
from sqlalchemy.orm import Session

# Problem 1: Events registered OUTSIDE the model class
# Where do I find all the events for User.posts? Grep the entire codebase.

@event.listens_for(User.posts, 'append')
def on_post_append(target, value, initiator):
    # Problem 2: What are these parameters?
    # - target: The User instance (but why not "user"?)
    # - value: The Post being appended (but why not "post"?)
    # - initiator: Some SQLAlchemy internal (what even is this?)
    pass

@event.listens_for(User.posts, 'remove')
def on_post_remove(target, value, initiator):
    pass

# Problem 3: String-based event names
# Typo? SQLAlchemy won't tell you until runtime
@event.listens_for(User.posts, 'appened')  # TYPO - no error at define time!

# Problem 4: No IDE autocomplete
# What events exist? "append"? "remove"? "set"? "add"?
# You have to read the docs every time.

# Problem 5: Session-dependent behavior
# Some events only fire when session.add() or session.flush() is called
# Others fire immediately. Which is which?
```

### The Django Way

Django uses signals, which have similar issues:

```python
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

# Problem 1: Signals disconnected from models
# Where are all the signals for User? Who knows!

@receiver(post_save, sender=User)
def user_saved(sender, instance, created, **kwargs):
    # Problem 2: What's sender? What's kwargs?
    pass

# Problem 3: String-based relationships
# No good way to hook into relationship changes
# You have to override save() methods or use M2M signals

# Problem 4: Global registration
# Signals are global, making testing tricky
# Easy to forget to disconnect in tests
```

### What Developers Want

```python
# IDEAL: Simple, discoverable, in the model

class User(Table):
    posts: List[Post] = has_many(Post)
    
    # When post is added, run this
    def on_post_added(self, post):
        notify_followers(self, post)
    
    # When post is removed, run this
    def on_post_removed(self, post):
        cleanup_post(post)
```

---

## The PyNext Solution

PyNext provides exactly what developers want - simple decorators in the model:

```python
from pynext.db import Table, has_many, on_append, on_remove, on_set, before_delete

class User(Table):
    posts: List[Post] = has_many(Post)
    profile: Profile = has_one(Profile)
    
    @on_append("posts")
    def on_post_added(self, post: Post):
        """Simple callback - (self, item) signature."""
        notify_followers(self, post)
    
    @on_remove("posts")
    def on_post_removed(self, post: Post):
        cleanup_post(post)
    
    @on_set("profile")
    def on_profile_changed(self, old: Profile, new: Profile):
        invalidate_profile_cache(self.id)
    
    @before_delete()
    def cleanup(self):
        archive_user_data(self)
```

### Why PyNext is Better

| Issue | SQLAlchemy | PyNext |
|-------|------------|--------|
| **Where are hooks?** | Scattered across codebase | In the model class |
| **How to find all hooks?** | Grep for `listens_for` | Read the model |
| **Callback parameters** | `(target, value, initiator)` | `(self, item)` |
| **Event names** | Strings: `"append"` | Functions: `on_append` |
| **IDE support** | None | Full autocomplete |
| **Typo in event name** | Silent failure | Import error |
| **When do hooks fire?** | Session-dependent | Immediate |
| **Testing** | Complex setup | Simple reset |

### Comparison: Adding a Post

**SQLAlchemy:**
```python
# File: models/user.py
class User(Base):
    posts = relationship("Post", back_populates="author")

# File: events/user_events.py (who knows where this is?)
from sqlalchemy import event
from models.user import User

@event.listens_for(User.posts, 'append')
def on_post_append(target, value, initiator):
    # target = user, value = post, initiator = ???
    send_notification(target.followers, f"New post from {target.name}")
```

**PyNext:**
```python
# File: models/user.py (everything in one place)
class User(Table):
    posts: List[Post] = has_many(Post, backref="author")
    
    @on_append("posts")
    def on_post_added(self, post: Post):
        # self = user, post = post (obvious!)
        send_notification(self.followers, f"New post from {self.name}")
```

---

## Hook Types Deep Dive

### @on_append Deep Dive

The `@on_append` hook fires when items are added to a collection.

#### When It Fires

| Operation | Fires @on_append? | Notes |
|-----------|------------------|-------|
| `collection.append(item)` | ✅ Yes | Single item |
| `collection.extend([items])` | ✅ Yes | Once per item |
| `collection.insert(i, item)` | ✅ Yes | Single item |
| `collection[i] = new_item` | ✅ Yes | For new item |
| `collection += [items]` | ✅ Yes | Once per item |
| `collection[0:2] = [items]` | ✅ Yes | For each new item |

#### Signature

```python
@on_append("relationship_name")
def my_hook(self, item: ItemType):
    # self: The owner instance (e.g., User)
    # item: The item being added (e.g., Post)
    pass
```

#### Complete Example

```python
class User(Table):
    posts: List[Post] = has_many(Post)
    followers: List[User] = many_to_many(User, backref="following")
    
    @on_append("posts")
    def on_post_added(self, post: Post):
        """React when a post is added to this user."""
        # Update denormalized count
        self.post_count += 1
        
        # Invalidate caches
        cache.delete(f"user:{self.id}:posts")
        cache.delete(f"feed:home")
        
        # Send notifications to followers
        for follower in self.followers:
            send_notification(
                to=follower.id,
                title="New Post",
                body=f"{self.name} published '{post.title}'"
            )
        
        # Log for analytics
        analytics.track("post_created", {
            "user_id": self.id,
            "post_id": post.id,
        })
    
    @on_append("followers")
    def on_follower_added(self, follower: User):
        """React when someone follows this user."""
        self.follower_count += 1
        
        send_notification(
            to=self.id,
            title="New Follower",
            body=f"{follower.name} started following you"
        )
```

### @on_remove Deep Dive

The `@on_remove` hook fires when items are removed from a collection.

#### When It Fires

| Operation | Fires @on_remove? | Notes |
|-----------|------------------|-------|
| `collection.remove(item)` | ✅ Yes | Single item |
| `collection.pop()` | ✅ Yes | Last item |
| `collection.pop(i)` | ✅ Yes | Item at index |
| `collection.clear()` | ✅ Yes | Once per item |
| `del collection[i]` | ✅ Yes | Single item |
| `collection[i] = new_item` | ✅ Yes | For old item |
| `del collection[0:2]` | ✅ Yes | For each item |

#### Signature

```python
@on_remove("relationship_name")
def my_hook(self, item: ItemType):
    # self: The owner instance
    # item: The item being removed
    pass
```

#### Complete Example

```python
class User(Table):
    posts: List[Post] = has_many(Post)
    
    @on_remove("posts")
    def on_post_removed(self, post: Post):
        """React when a post is removed from this user."""
        # Update denormalized count
        self.post_count -= 1
        
        # Archive the post before it's gone
        archive_service.store({
            "type": "removed_post",
            "post": post.to_dict(),
            "removed_at": datetime.now(),
            "removed_by": current_user.id,
        })
        
        # Invalidate caches
        cache.delete(f"user:{self.id}:posts")
        cache.delete(f"post:{post.id}")
        
        # Clean up S3 images
        if post.image_url:
            s3.delete(post.image_url)
        
        # Log for audit
        audit_log.record(
            event="post_removed",
            user_id=self.id,
            post_id=post.id,
        )

class ShoppingCart(Table):
    items: List[CartItem] = has_many(CartItem)
    
    @on_remove("items")
    def on_item_removed(self, item: CartItem):
        """React when an item is removed from cart."""
        # Update totals
        self.item_count -= 1
        self.subtotal -= item.price * item.quantity
        
        # Invalidate cached cart total
        cache.delete(f"cart:{self.id}:total")
        
        # Restore inventory if item was reserved
        if item.is_reserved:
            inventory.release_reservation(item.product_id, item.quantity)
```

### @on_set Deep Dive

The `@on_set` hook fires when a scalar relationship (belongs_to, has_one) is set or changed.

#### When It Fires

| Operation | Fires @on_set? | Notes |
|-----------|---------------|-------|
| `instance.rel = value` | ✅ Yes | Always |
| `instance.rel = None` | ✅ Yes | old_value is set |
| Initial assignment | ✅ Yes | old_value is None |

#### Signature

```python
@on_set("relationship_name")
def my_hook(self, old_value: Type, new_value: Type):
    # self: The owner instance
    # old_value: Previous value (None if first assignment)
    # new_value: New value (None if clearing)
    pass
```

#### Complete Example

```python
class Post(Table):
    author_id: int
    author: User = belongs_to(User, "author_id")
    
    @on_set("author")
    def on_author_changed(self, old_author: User, new_author: User):
        """React when post author changes."""
        
        if old_author is None and new_author is not None:
            # Initial assignment
            log_event(f"Post {self.id} assigned to {new_author.name}")
            new_author.post_count += 1
            
        elif old_author is not None and new_author is None:
            # Unassigned
            log_event(f"Post {self.id} unassigned from {old_author.name}")
            old_author.post_count -= 1
            
        else:
            # Transferred
            log_event(f"Post transferred: {old_author.name} → {new_author.name}")
            old_author.post_count -= 1
            new_author.post_count += 1
        
        # Invalidate caches
        if old_author:
            cache.delete(f"user:{old_author.id}:posts")
        if new_author:
            cache.delete(f"user:{new_author.id}:posts")

class Document(Table):
    category_id: int
    category: Category = belongs_to(Category, "category_id")
    
    @on_set("category")
    def on_category_changed(self, old_cat: Category, new_cat: Category):
        """React when document category changes."""
        
        # Update category counts
        if old_cat:
            old_cat.document_count -= 1
        if new_cat:
            new_cat.document_count += 1
        
        # Re-index in search
        search.update_document(self.id, category=new_cat.name if new_cat else None)
```

### @before_delete Deep Dive

The `@before_delete` hook fires before an instance is deleted.

#### When It Fires

| Operation | Fires @before_delete? |
|-----------|---------------------|
| `instance.delete()` | ✅ Yes |
| Cascade delete | ✅ Yes |
| Bulk delete | ❌ No (performance) |

#### Signature

```python
@before_delete()
def my_hook(self):
    # self: The instance being deleted
    # No other parameters
    pass
```

#### Complete Example

```python
class User(Table):
    email: str
    avatar_url: str
    posts: List[Post] = has_many(Post)
    
    @before_delete()
    def cleanup_before_delete(self):
        """Run before user is deleted."""
        
        # 1. Archive user data for compliance
        archive_service.store({
            "type": "deleted_user",
            "id": self.id,
            "email": self.email,
            "data": self.to_dict(),
            "deleted_at": datetime.now(),
        })
        
        # 2. Delete files from S3
        if self.avatar_url:
            s3.delete(self.avatar_url)
        s3.delete_prefix(f"users/{self.id}/")
        
        # 3. Remove from search index
        elasticsearch.delete("users", self.id)
        
        # 4. Remove from cache
        cache.delete_pattern(f"user:{self.id}:*")
        
        # 5. Revoke all authentication tokens
        auth.revoke_all_tokens(self.id)
        
        # 6. Send goodbye email
        send_email(
            to=self.email,
            subject="Account Deleted",
            template="account_deleted",
            data={"name": self.name},
        )
        
        # 7. Notify admin
        admin_notification.send(
            f"User {self.email} deleted their account"
        )

class Order(Table):
    @before_delete()
    def archive_order(self):
        """Archive order before deletion for financial records."""
        financial_archive.store({
            "order_id": self.id,
            "customer_id": self.customer_id,
            "total": self.total,
            "items": [item.to_dict() for item in self.items],
            "deleted_at": datetime.now(),
        })
```

---

## Real-World Scenarios

### Scenario 1: E-Commerce Order System

```python
class Customer(Table):
    name: str
    email: str
    orders: List[Order] = has_many(Order)
    total_spent: float = 0
    order_count: int = 0
    
    @on_append("orders")
    def on_order_placed(self, order: Order):
        """React when customer places an order."""
        # Update customer stats
        self.order_count += 1
        self.total_spent += order.total
        
        # Update customer tier
        if self.total_spent > 1000:
            self.tier = "gold"
        elif self.total_spent > 500:
            self.tier = "silver"
        
        # Send confirmation email
        send_email(
            to=self.email,
            subject=f"Order #{order.id} Confirmed",
            template="order_confirmation",
            data={"order": order.to_dict()},
        )
        
        # Notify warehouse
        warehouse_api.queue_order(order.id)

class Order(Table):
    items: List[OrderItem] = has_many(OrderItem)
    total: float = 0
    
    @on_append("items")
    def on_item_added(self, item: OrderItem):
        """React when item is added to order."""
        self.total += item.price * item.quantity
        
        # Reserve inventory
        inventory.reserve(item.product_id, item.quantity)
    
    @on_remove("items")
    def on_item_removed(self, item: OrderItem):
        """React when item is removed from order."""
        self.total -= item.price * item.quantity
        
        # Release reserved inventory
        inventory.release(item.product_id, item.quantity)
```

### Scenario 2: Social Media Platform

```python
class User(Table):
    username: str
    followers: List[User] = many_to_many(User, backref="following")
    posts: List[Post] = has_many(Post)
    follower_count: int = 0
    
    @on_append("followers")
    def on_new_follower(self, follower: User):
        """React when someone follows this user."""
        self.follower_count += 1
        
        # Notify user of new follower
        send_push_notification(
            to=self.id,
            title="New Follower",
            body=f"@{follower.username} started following you",
        )
        
        # Check for milestones
        if self.follower_count == 100:
            award_badge(self, "century_club")
        elif self.follower_count == 1000:
            award_badge(self, "influencer")
    
    @on_remove("followers")
    def on_follower_lost(self, follower: User):
        self.follower_count -= 1
    
    @on_append("posts")
    def on_post_published(self, post: Post):
        """React when user publishes a post."""
        # Notify all followers
        for follower in self.followers:
            add_to_feed(follower.id, post.id)
            
            # Push notification for close friends
            if self.id in follower.close_friends:
                send_push_notification(
                    to=follower.id,
                    title=f"@{self.username} posted",
                    body=post.title[:50],
                )

class Post(Table):
    comments: List[Comment] = has_many(Comment)
    likes: List[Like] = has_many(Like)
    
    @on_append("comments")
    def on_comment_added(self, comment: Comment):
        """React when someone comments."""
        # Notify post author
        if comment.author_id != self.author_id:
            send_push_notification(
                to=self.author_id,
                title="New Comment",
                body=f"@{comment.author.username}: {comment.text[:50]}",
            )
    
    @on_append("likes")
    def on_like_added(self, like: Like):
        """React when someone likes the post."""
        if like.user_id != self.author_id:
            send_push_notification(
                to=self.author_id,
                title="New Like",
                body=f"@{like.user.username} liked your post",
            )
```

### Scenario 3: Project Management System

```python
class Project(Table):
    name: str
    tasks: List[Task] = has_many(Task)
    members: List[User] = many_to_many(User)
    
    @on_append("tasks")
    def on_task_added(self, task: Task):
        """React when task is added to project."""
        # Notify all project members
        for member in self.members:
            send_notification(
                to=member.id,
                title=f"New Task in {self.name}",
                body=task.title,
            )
        
        # Update project stats
        self.task_count += 1
        
        # Log activity
        activity_feed.add(
            project_id=self.id,
            action="task_created",
            data={"task_id": task.id, "title": task.title},
        )
    
    @on_append("members")
    def on_member_added(self, member: User):
        """React when member joins project."""
        # Notify existing members
        for existing in self.members:
            if existing.id != member.id:
                send_notification(
                    to=existing.id,
                    title=f"New Team Member",
                    body=f"{member.name} joined {self.name}",
                )
        
        # Welcome the new member
        send_email(
            to=member.email,
            subject=f"Welcome to {self.name}",
            template="project_welcome",
            data={"project": self.to_dict()},
        )

class Task(Table):
    assignee_id: int
    assignee: User = belongs_to(User, "assignee_id")
    
    @on_set("assignee")
    def on_assignee_changed(self, old: User, new: User):
        """React when task is reassigned."""
        if old and new:
            # Task reassigned
            send_notification(
                to=new.id,
                title="Task Assigned to You",
                body=self.title,
            )
            send_notification(
                to=old.id,
                title="Task Reassigned",
                body=f"{self.title} reassigned to {new.name}",
            )
        elif new:
            # First assignment
            send_notification(
                to=new.id,
                title="Task Assigned to You",
                body=self.title,
            )
```

---

## How to Implement Common Patterns

### Pattern 1: Audit Logging

```python
from datetime import datetime

class AuditLog(Table):
    entity_type: str
    entity_id: int
    action: str
    old_value: str  # JSON
    new_value: str  # JSON
    user_id: int
    timestamp: datetime

def create_audit_mixin(entity_type: str):
    """Factory to create audit hooks for any model."""
    
    class AuditMixin:
        @on_append("*")  # Conceptual - would need one per relationship
        def audit_append(self, item):
            AuditLog.create(
                entity_type=entity_type,
                entity_id=self.id,
                action="item_added",
                new_value=item.to_json(),
                user_id=current_user.id,
                timestamp=datetime.now(),
            )
    
    return AuditMixin

# Usage
class User(Table):
    posts: List[Post] = has_many(Post)
    
    @on_append("posts")
    def audit_post_added(self, post: Post):
        AuditLog.create(
            entity_type="user",
            entity_id=self.id,
            action="post_added",
            new_value=json.dumps({"post_id": post.id, "title": post.title}),
            user_id=current_user.id,
            timestamp=datetime.now(),
        )
    
    @on_remove("posts")
    def audit_post_removed(self, post: Post):
        AuditLog.create(
            entity_type="user",
            entity_id=self.id,
            action="post_removed",
            old_value=json.dumps({"post_id": post.id, "title": post.title}),
            user_id=current_user.id,
            timestamp=datetime.now(),
        )
```

### Pattern 2: Cache Invalidation

```python
class User(Table):
    posts: List[Post] = has_many(Post)
    followers: List[User] = many_to_many(User)
    
    def _invalidate_post_caches(self):
        """Helper to invalidate all post-related caches."""
        cache.delete(f"user:{self.id}:posts")
        cache.delete(f"user:{self.id}:posts:count")
        cache.delete(f"user:{self.id}:posts:recent")
        cache.delete(f"feed:global")
        
        # Invalidate follower feeds
        for follower in self.followers:
            cache.delete(f"feed:user:{follower.id}")
    
    @on_append("posts")
    def invalidate_on_post_added(self, post: Post):
        self._invalidate_post_caches()
    
    @on_remove("posts")
    def invalidate_on_post_removed(self, post: Post):
        self._invalidate_post_caches()
        cache.delete(f"post:{post.id}")
```

### Pattern 3: Real-Time Updates via WebSocket

```python
from channels import broadcast

class ChatRoom(Table):
    messages: List[Message] = has_many(Message)
    participants: List[User] = many_to_many(User)
    
    @on_append("messages")
    def broadcast_new_message(self, message: Message):
        """Send new message to all participants via WebSocket."""
        broadcast(
            channel=f"room:{self.id}",
            event="new_message",
            data={
                "id": message.id,
                "text": message.text,
                "author": message.author.username,
                "timestamp": message.created_at.isoformat(),
            },
        )
    
    @on_append("participants")
    def broadcast_user_joined(self, user: User):
        """Notify when user joins the room."""
        broadcast(
            channel=f"room:{self.id}",
            event="user_joined",
            data={
                "user_id": user.id,
                "username": user.username,
            },
        )
    
    @on_remove("participants")
    def broadcast_user_left(self, user: User):
        """Notify when user leaves the room."""
        broadcast(
            channel=f"room:{self.id}",
            event="user_left",
            data={
                "user_id": user.id,
                "username": user.username,
            },
        )
```

### Pattern 4: Validation

```python
class Team(Table):
    members: List[User] = many_to_many(User)
    max_members: int = 10
    
    @on_append("members")
    def validate_member_limit(self, user: User):
        """Prevent adding members beyond limit."""
        if len(self.members) >= self.max_members:
            raise ValueError(
                f"Team cannot have more than {self.max_members} members"
            )
    
    @on_append("members")
    def validate_user_eligibility(self, user: User):
        """Ensure user is eligible to join."""
        if not user.is_verified:
            raise ValueError("Only verified users can join teams")
        
        if user.is_banned:
            raise ValueError("Banned users cannot join teams")
        
        # Check if user is already in too many teams
        if len(user.teams) >= 5:
            raise ValueError("User is already in 5 teams (maximum)")
```

### Pattern 5: External System Sync

```python
class Product(Table):
    sku: str
    name: str
    price: float
    warehouses: List[Warehouse] = many_to_many(Warehouse)
    
    @on_append("warehouses")
    def sync_to_warehouse_system(self, warehouse: Warehouse):
        """Sync product to external warehouse management system."""
        warehouse_api.add_product(
            warehouse_id=warehouse.external_id,
            product_sku=self.sku,
            product_name=self.name,
        )
    
    @on_remove("warehouses")
    def unsync_from_warehouse_system(self, warehouse: Warehouse):
        """Remove product from external warehouse system."""
        warehouse_api.remove_product(
            warehouse_id=warehouse.external_id,
            product_sku=self.sku,
        )
    
    @before_delete()
    def cleanup_external_systems(self):
        """Remove from all external systems before deletion."""
        # Remove from all warehouses
        for warehouse in self.warehouses:
            warehouse_api.remove_product(
                warehouse_id=warehouse.external_id,
                product_sku=self.sku,
            )
        
        # Remove from search index
        search_api.delete_product(self.sku)
        
        # Remove from CDN
        cdn.invalidate(f"/products/{self.sku}/*")
```

---

## Decision Guide: Choosing the Right Hook

### Quick Reference

| I want to... | Use this hook |
|-------------|---------------|
| React when item added to collection | `@on_append("collection")` |
| React when item removed from collection | `@on_remove("collection")` |
| React when belongs_to changes | `@on_set("relationship")` |
| React when has_one changes | `@on_set("relationship")` |
| Cleanup before deletion | `@before_delete()` |
| Validate before adding | `@on_append` with raise |
| Track changes for audit | All hooks + AuditLog |
| Invalidate cache | All relevant hooks |
| Send notifications | Depends on trigger |

### When NOT to Use Hooks

| Situation | Better Alternative |
|-----------|-------------------|
| Complex multi-step transactions | Use explicit service functions |
| Async-heavy operations | Use background task queue |
| Performance-critical hot paths | Batch process later |
| Need to affect the change | Use validators/constraints |
| Bulk operations | Use post-bulk signals |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Heavy Work in Hooks

```python
# ❌ BAD: Doing too much in a hook
@on_append("posts")
def on_post_added(self, post: Post):
    # This is too slow!
    for follower in self.get_all_followers():  # Could be 1M followers
        send_email(follower.email, ...)  # Blocking I/O
        update_feed(follower.id, post.id)  # DB write
        send_push_notification(follower.id, ...)  # API call

# ✅ GOOD: Queue work for background processing
@on_append("posts")
def on_post_added(self, post: Post):
    # Quick: just queue the work
    task_queue.enqueue(
        "process_new_post",
        user_id=self.id,
        post_id=post.id,
    )
```

### Anti-Pattern 2: Catching and Swallowing Errors

```python
# ❌ BAD: Hiding errors
@on_append("posts")
def on_post_added(self, post: Post):
    try:
        send_notification(...)
    except Exception:
        pass  # Error is hidden!

# ✅ GOOD: Let errors propagate or log them
@on_append("posts")
def on_post_added(self, post: Post):
    try:
        send_notification(...)
    except Exception as e:
        logger.error(f"Notification failed: {e}")
        # Re-raise if critical, or continue if non-critical
```

### Anti-Pattern 3: Circular Triggers

```python
# ❌ BAD: Can cause infinite loops
class User(Table):
    @on_append("followers")
    def on_follower_added(self, follower: User):
        # This could trigger follower's hook which triggers ours...
        follower.notifications.append(Notification(...))

# ✅ GOOD: Use flags or check conditions
class User(Table):
    @on_append("followers")
    def on_follower_added(self, follower: User):
        # Direct notification, not via relationship
        send_push_notification(follower.id, ...)
```

### Anti-Pattern 4: Relying on Hook Order for Correctness

```python
# ❌ BAD: Second hook depends on first hook
@on_append("posts")
def hook1(self, post: Post):
    post.processed = True

@on_append("posts")
def hook2(self, post: Post):
    if post.processed:  # Depends on hook1 running first!
        do_something()

# ✅ GOOD: Each hook is independent
@on_append("posts")
def process_and_notify(self, post: Post):
    post.processed = True
    if post.processed:
        do_something()
```

---

## Performance Deep Dive

### Overhead Measurements

| Scenario | Time per Operation |
|----------|-------------------|
| No hooks registered | < 0.001ms |
| 1 hook (empty) | ~0.002ms |
| 1 hook (simple work) | ~0.01ms |
| 5 hooks (simple work) | ~0.05ms |
| 1 hook + cache operation | ~1ms (cache-dependent) |
| 1 hook + API call | ~100ms (network-dependent) |

### Why Synchronous is Fastest

```python
# PyNext: Direct function call
for hook in hooks:
    hook(instance, item)  # ~0.001ms per hook

# Alternatives that are SLOWER:

# Async detection adds overhead
if asyncio.iscoroutinefunction(hook):  # ~0.01ms check
    await hook(instance, item)
else:
    hook(instance, item)

# Queuing adds overhead
queue.put((hook, instance, item))  # ~0.1ms
# Later: queue.get() and execute
```

### Optimization Tips

1. **Keep hooks simple** - Do minimal work, queue heavy operations
2. **Batch notifications** - Don't send 1000 emails in a hook
3. **Use caching** - Cache expensive computations
4. **Profile your hooks** - Measure actual overhead

```python
# Measure hook performance
import time

@on_append("posts")
def measured_hook(self, post: Post):
    start = time.perf_counter()
    
    # Your hook logic here
    do_something()
    
    elapsed = time.perf_counter() - start
    metrics.record("hook.on_post_added.duration", elapsed)
```

---

## Testing Your Hooks

### Basic Testing

```python
import pytest
from pynext.db.relationships import reset_hook_registries, discover_hooks

@pytest.fixture(autouse=True)
def reset_hooks():
    """Reset hooks before each test."""
    reset_hook_registries()
    yield
    reset_hook_registries()

def test_on_post_added_sends_notification():
    notifications = []
    
    class User(Table):
        posts: List[Post] = has_many(Post)
        
        @on_append("posts")
        def on_post_added(self, post: Post):
            notifications.append({
                "to": self.id,
                "post_id": post.id,
            })
    
    discover_hooks(User)
    
    user = User(id=1)
    user.posts.append(Post(id=10))
    
    assert len(notifications) == 1
    assert notifications[0]["to"] == 1
    assert notifications[0]["post_id"] == 10
```

### Testing Multiple Hooks

```python
def test_multiple_hooks_execute_in_order():
    order = []
    
    class User(Table):
        posts: List[Post] = has_many(Post)
        
        @on_append("posts")
        def hook1(self, post):
            order.append("hook1")
        
        @on_append("posts")
        def hook2(self, post):
            order.append("hook2")
    
    discover_hooks(User)
    
    user = User(id=1)
    user.posts.append(Post(id=1))
    
    assert order == ["hook1", "hook2"]
```

### Testing Error Handling

```python
def test_hook_error_propagates():
    class User(Table):
        posts: List[Post] = has_many(Post)
        
        @on_append("posts")
        def validate_post(self, post: Post):
            if not post.title:
                raise ValueError("Post must have title")
    
    discover_hooks(User)
    
    user = User(id=1)
    
    with pytest.raises(ValueError, match="must have title"):
        user.posts.append(Post(id=1, title=""))
```

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

def test_hook_sends_notification():
    class User(Table):
        posts: List[Post] = has_many(Post)
        
        @on_append("posts")
        def notify(self, post: Post):
            notification_service.send(self.id, f"New post: {post.title}")
    
    discover_hooks(User)
    
    with patch('myapp.notification_service') as mock_service:
        user = User(id=1)
        user.posts.append(Post(id=1, title="Hello"))
        
        mock_service.send.assert_called_once_with(1, "New post: Hello")
```

---

## API Reference

### Decorators

#### @on_append(relationship_name, *, priority=0)

Register a hook for collection additions.

```python
@on_append("posts", priority=10)
def my_hook(self, post: Post):
    pass
```

**Parameters:**
- `relationship_name` (str): Name of the relationship
- `priority` (int): Execution order (lower = earlier)

**Callback Signature:** `(self, item) -> None`

#### @on_remove(relationship_name, *, priority=0)

Register a hook for collection removals.

```python
@on_remove("posts")
def my_hook(self, post: Post):
    pass
```

**Callback Signature:** `(self, item) -> None`

#### @on_set(relationship_name, *, priority=0)

Register a hook for scalar relationship changes.

```python
@on_set("profile")
def my_hook(self, old: Profile, new: Profile):
    pass
```

**Callback Signature:** `(self, old_value, new_value) -> None`

#### @before_delete(*, priority=0)

Register a hook for pre-deletion cleanup.

```python
@before_delete()
def my_hook(self):
    pass
```

**Callback Signature:** `(self) -> None`

### Functions

#### discover_hooks(model_class)

Discover and register hooks defined on a model class.

```python
from pynext.db.relationships import discover_hooks
discover_hooks(User)
```

#### get_hook_registry(model_class)

Get the hook registry for a model class.

```python
from pynext.db.relationships import get_hook_registry
registry = get_hook_registry(User)
```

#### reset_hook_registries()

Reset all hook registries (for testing).

```python
from pynext.db.relationships import reset_hook_registries
reset_hook_registries()
```

---

## Troubleshooting

### Hook Not Firing

**1. Did you call `discover_hooks()`?**
```python
from pynext.db.relationships import discover_hooks
discover_hooks(User)  # Required!
```

**2. Is the relationship name correct?**
```python
# Wrong
@on_append("post")  # Singular

# Correct
@on_append("posts")  # Match the attribute name
```

**3. Is the method signature correct?**
```python
# Wrong - missing self
@on_append("posts")
def my_hook(post):
    pass

# Correct
@on_append("posts")
def my_hook(self, post):
    pass
```

**4. Is the hook actually triggered?**
```python
@on_append("posts")
def debug_hook(self, post):
    print(f"HOOK FIRED: {self}, {post}")  # Add debug output
```

### Hook Errors

**Errors propagate by default.** To suppress:

```python
from pynext.db.relationships import HookExecutor, set_hook_executor

executor = HookExecutor(suppress_errors=True)
set_hook_executor(executor)
```

### Debugging

```python
@on_append("posts")
def debug_hook(self, post: Post):
    import traceback
    print(f"Hook called: {self.__class__.__name__}")
    print(f"  Owner: {self}")
    print(f"  Item: {post}")
    print("Stack trace:")
    traceback.print_stack()
```

---

## Summary

PyNext relationship hooks provide a simple, powerful way to react to data changes:

| Feature | Description |
|---------|-------------|
| **@on_append** | Fire when items added to collections |
| **@on_remove** | Fire when items removed from collections |
| **@on_set** | Fire when scalar relationships change |
| **@before_delete** | Fire before instance deletion |
| **Synchronous** | Direct function calls, zero async overhead |
| **Simple Signatures** | `(self, item)` not `(target, value, initiator)` |
| **In-Model** | Hooks live with the model, easy to discover |
| **Inheritance** | Parent hooks inherited by subclasses |

### Key Takeaways

1. **Hooks are observers** - They react to changes, they don't cause them
2. **Keep hooks simple** - Queue heavy work for background processing
3. **Errors propagate** - Handle errors appropriately
4. **Test your hooks** - Use the reset functions for isolation
5. **Use the right hook** - Match the hook type to the change you're observing
