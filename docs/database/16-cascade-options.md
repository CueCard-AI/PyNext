# Cascade Options

> Complete control over what happens when records are deleted, saved, or orphaned.

---

## Table of Contents

1. [What Are Cascades and Why Do They Matter?](#what-are-cascades-and-why-do-they-matter)
2. [The Problem: "What Happens to Related Records?"](#the-problem-what-happens-to-related-records)
3. [Quick Start](#quick-start)
4. [Understanding When to Use Each Cascade](#understanding-when-to-use-each-cascade)
5. [Decision Guide: Choosing the Right Cascade](#decision-guide-choosing-the-right-cascade)
6. [Simple Presets (on_delete)](#simple-presets-on_delete)
7. [Fine-Grained Control (CascadeOptions)](#fine-grained-control-cascadeoptions)
8. [Real-World Scenarios](#real-world-scenarios)
9. [PyNext vs SQLAlchemy](#pynext-vs-sqlalchemy)
10. [Database-Level Cascade Integration](#database-level-cascade-integration)
11. [Performance Considerations](#performance-considerations)
12. [Anti-Patterns and What NOT to Do](#anti-patterns-and-what-not-to-do)
13. [Migration Guide](#migration-guide)
14. [Troubleshooting](#troubleshooting)
15. [API Reference](#api-reference)

---

## What Are Cascades and Why Do They Matter?

### The Core Concept

**Cascades** define what happens to related records when you perform an operation on a parent record. When you delete a User, what happens to their Posts? Their Comments? Their Orders?

```
User (deleted)
├── Posts → Should they be deleted too?
├── Comments → Should they become "anonymous"?
├── Orders → Should deletion be blocked?
└── Profile → Should it be deleted?
```

**Without cascades**, you must handle every scenario manually:

```python
# WITHOUT cascades - you forget something, data becomes orphaned
async def delete_user(user_id):
    user = await User.get(user_id)
    
    # Did you remember all of these?
    for post in user.posts:
        for comment in post.comments:  # Comments on posts?
            await comment.delete()
        await post.delete()
    
    for comment in user.comments:  # User's own comments?
        await comment.delete()
    
    if user.profile:  # Profile?
        await user.profile.delete()
    
    # What about notifications? Activity logs? Subscriptions?
    # Easy to forget something...
    
    await user.delete()
```

**With cascades**, behavior is defined once and enforced automatically:

```python
# WITH cascades - clean, complete, automatic
class User(Table):
    posts: List[Post] = has_many(Post, on_delete="cascade")
    comments: List[Comment] = has_many(Comment, on_delete="nullify")  
    orders: List[Order] = has_many(Order, on_delete="protect")
    profile: Profile = has_one(Profile, on_delete="cascade")

# Now this handles EVERYTHING correctly:
await user.delete()
```

### Why Cascades Are Critical

| Scenario | Without Cascades | With Cascades |
|----------|------------------|---------------|
| Delete user with 100 posts | 100+ manual deletes, easy to forget | One `await user.delete()` |
| Orphaned records | FK pointing to deleted parent | Never happens |
| Data integrity | Hope you remembered everything | Guaranteed |
| Code maintenance | Update every delete location | Update model once |
| Bug potential | High | Low |

---

## The Problem: "What Happens to Related Records?"

### Real Questions You'll Face

When building any application, you'll encounter these questions:

**Scenario 1: Blog Platform**
- User deletes their account → What about their published posts?
- User deletes a post → What about the comments on it?
- User deletes a comment → What about replies to that comment?

**Scenario 2: E-Commerce**
- Customer deletes account → What about their order history?
- Order is cancelled → What about the order items?
- Product is discontinued → What about orders containing it?

**Scenario 3: Social Media**
- User deactivates account → What about their likes, follows, messages?
- Post is deleted → What about shares, reactions, mentions?

### The Four Fundamental Choices

When a parent record is deleted, you have exactly four options for child records:

| Option | What Happens | When to Use |
|--------|--------------|-------------|
| **CASCADE** | Delete children too | Children have no meaning without parent |
| **NULLIFY** | Set FK to NULL | Preserve children as "orphans" |
| **PROTECT** | Block the deletion | Children are too important to lose |
| **NONE** | Do nothing (let DB decide) | Database constraints handle it |

Understanding WHEN to use each is the key to data modeling.

---

## Quick Start

### 1. Basic Cascade Delete

```python
from pynext.db import Table, has_many
from typing import List

class Comment(Table):
    content: str
    post_id: int

class Post(Table):
    title: str
    # When post deleted, delete all comments
    comments: List[Comment] = has_many(Comment, on_delete="cascade")

# Usage
post = await Post.get(1)
await post.delete()  # Automatically deletes all 50 comments
```

### 2. Protect Critical Data

```python
class Order(Table):
    total: float
    user_id: int

class User(Table):
    name: str
    # Cannot delete user if they have orders
    orders: List[Order] = has_many(Order, on_delete="protect")

# Usage
user = await User.get(1)
await user.delete()  # Raises ProtectedDeleteError if orders exist!
```

### 3. Preserve but Unlink

```python
class Post(Table):
    title: str
    author_id: Optional[int]  # Must be Optional for nullify!

class User(Table):
    name: str
    # When user deleted, posts become "anonymous"
    posts: List[Post] = has_many(Post, on_delete="nullify")

# Usage
await user.delete()
# Posts now have author_id = None
# They're preserved as anonymous content
```

---

## Understanding When to Use Each Cascade

### CASCADE: "Children Die With Parent"

**Use `on_delete="cascade"` when:**
- Children have no meaning without the parent
- Children are "owned" by the parent
- You want complete cleanup

**Examples:**

```python
# ✅ GOOD: Comments on a post (no post = no comments)
class Post(Table):
    comments: List[Comment] = has_many(Comment, on_delete="cascade")

# ✅ GOOD: Items in a shopping cart
class Cart(Table):
    items: List[CartItem] = has_many(CartItem, on_delete="cascade")

# ✅ GOOD: User's profile
class User(Table):
    profile: Profile = has_one(Profile, on_delete="cascade")

# ✅ GOOD: Form fields
class Form(Table):
    fields: List[FormField] = has_many(FormField, on_delete="cascade")

# ✅ GOOD: Thread messages
class Thread(Table):
    messages: List[Message] = has_many(Message, on_delete="cascade")
```

**Decision Question:** "Do the children make sense if the parent is deleted?"
- If NO → Use `cascade`

---

### NULLIFY: "Children Survive but Become Orphans"

**Use `on_delete="nullify"` when:**
- Children should be preserved even without parent
- The relationship is optional (author left, but content remains)
- Historical/archival purposes

**Examples:**

```python
# ✅ GOOD: Blog posts when author deletes account
class User(Table):
    # Posts become "anonymous" but content is preserved
    posts: List[Post] = has_many(Post, on_delete="nullify")

# ✅ GOOD: Comments from deleted users
class User(Table):
    comments: List[Comment] = has_many(Comment, on_delete="nullify")

# ✅ GOOD: Wiki articles from former editors
class Editor(Table):
    articles: List[Article] = has_many(Article, on_delete="nullify")

# ✅ GOOD: Products created by deleted admin
class Admin(Table):
    products: List[Product] = has_many(Product, on_delete="nullify")
```

**Important:** The FK column MUST be `Optional[int]` for nullify to work!

```python
class Post(Table):
    title: str
    author_id: Optional[int]  # ✅ Must be Optional for nullify
    # NOT: author_id: int  # ❌ Can't be nullified
```

**Decision Question:** "Should the content survive if the creator is gone?"
- If YES → Use `nullify`

---

### PROTECT: "Cannot Delete If Children Exist"

**Use `on_delete="protect"` when:**
- Children are critical records that must not be lost
- Business rules require the parent to exist
- Legal/compliance requires maintaining records
- Accidental deletion would be catastrophic

**Examples:**

```python
# ✅ GOOD: Orders (financial records)
class User(Table):
    orders: List[Order] = has_many(Order, on_delete="protect")
    # Cannot delete user with existing orders

# ✅ GOOD: Payments (legal requirement)
class Invoice(Table):
    payments: List[Payment] = has_many(Payment, on_delete="protect")
    # Cannot delete invoice with payments

# ✅ GOOD: Employee with active projects
class Employee(Table):
    projects: List[Project] = has_many(Project, on_delete="protect")
    # Cannot delete employee managing projects

# ✅ GOOD: Category with products
class Category(Table):
    products: List[Product] = has_many(Product, on_delete="protect")
    # Must reassign products before deleting category
```

**Handling Protected Errors:**

```python
from pynext.db.relationships import ProtectedDeleteError

try:
    await user.delete()
except ProtectedDeleteError as e:
    print(f"Cannot delete: user has {e.related_count} {e.relationship}")
    # "Cannot delete: user has 5 orders"
    
    # Offer alternatives:
    # 1. Reassign the orders to another user
    # 2. Cancel/refund the orders first
    # 3. Archive the user instead of deleting
```

**Decision Question:** "Would deleting the parent cause unacceptable data loss?"
- If YES → Use `protect`

---

### NONE: "Let Database Handle It"

**Use `on_delete="none"` when:**
- Database FK constraints should decide
- You're not sure yet (development)
- Performance is critical (millions of records)
- Using database-level triggers

**Examples:**

```python
# ✅ GOOD: Log entries (let DB constraint decide)
class User(Table):
    logs: List[Log] = has_many(Log, on_delete="none")

# ✅ GOOD: Analytics events (millions of records)
class Session(Table):
    events: List[Event] = has_many(Event, on_delete="none")
    # DB constraint: ON DELETE CASCADE for performance
```

**Warning:** With `none`, you MUST have database constraints or you'll get orphaned records!

---

## Decision Guide: Choosing the Right Cascade

### Quick Decision Tree

```
When parent is deleted, should children be deleted?
├── YES, children have no meaning without parent
│   └── CASCADE
│
├── NO, but children should be preserved
│   ├── Can the FK be NULL?
│   │   ├── YES → NULLIFY
│   │   └── NO → Need to change schema or use PROTECT
│
├── NO, and deletion should be blocked
│   └── PROTECT
│
└── Let the database decide
    └── NONE (ensure DB constraints exist!)
```

### Decision Matrix by Relationship Type

| Relationship | Typical Cascade | Why |
|--------------|-----------------|-----|
| User → Profile | CASCADE | Profile is part of user |
| User → Posts | NULLIFY or CASCADE | Depends on content policy |
| User → Comments | NULLIFY | Preserve discussion |
| User → Orders | PROTECT | Financial records |
| User → Cart | CASCADE | Cart is user's |
| User → Sessions | CASCADE | Session is meaningless without user |
| Post → Comments | CASCADE | Comments are on the post |
| Post → Likes | CASCADE | Likes are for the post |
| Order → Items | CASCADE | Items are part of order |
| Category → Products | PROTECT | Must reassign products |
| Department → Employees | PROTECT or NULLIFY | Depends on business rules |

### By Industry/Domain

**E-Commerce:**
```python
class User(Table):
    cart: Cart = has_one(Cart, on_delete="cascade")              # Cart dies with user
    orders: List[Order] = has_many(Order, on_delete="protect")   # Orders are sacred
    reviews: List[Review] = has_many(Review, on_delete="nullify") # Preserve reviews
    wishlist: Wishlist = has_one(Wishlist, on_delete="cascade")  # Wishlist dies
```

**Social Media:**
```python
class User(Table):
    posts: List[Post] = has_many(Post, on_delete="cascade")     # Delete all content
    # OR
    posts: List[Post] = has_many(Post, on_delete="nullify")     # Preserve as anonymous
    
    likes: List[Like] = has_many(Like, on_delete="cascade")      # Likes disappear
    followers: List[Follow] = has_many(Follow, on_delete="cascade")
    messages: List[Message] = has_many(Message, on_delete="nullify")  # Preserve history
```

**SaaS/B2B:**
```python
class Organization(Table):
    users: List[User] = has_many(User, on_delete="cascade")      # Delete all users
    invoices: List[Invoice] = has_many(Invoice, on_delete="protect")  # Keep records
    subscriptions: List[Sub] = has_many(Sub, on_delete="cascade")
```

**Content Platform:**
```python
class Author(Table):
    articles: List[Article] = has_many(Article, on_delete="nullify")  # Preserve content
    drafts: List[Draft] = has_many(Draft, on_delete="cascade")       # Delete drafts
```

---

## Simple Presets (on_delete)

For 90% of use cases, use the simple `on_delete` parameter:

### cascade

```python
class Post(Table):
    comments: List[Comment] = has_many(Comment, on_delete="cascade")

await post.delete()
# Post deleted
# All comments deleted automatically
```

### nullify

```python
class User(Table):
    posts: List[Post] = has_many(Post, on_delete="nullify")

await user.delete()
# User deleted
# All posts now have author_id = NULL
```

### protect

```python
class User(Table):
    orders: List[Order] = has_many(Order, on_delete="protect")

await user.delete()  # Raises ProtectedDeleteError if orders exist
```

### none

```python
class User(Table):
    logs: List[Log] = has_many(Log, on_delete="none")

await user.delete()
# Database FK constraint determines behavior
```

---

## Fine-Grained Control (CascadeOptions)

For advanced use cases, `CascadeOptions` gives you precise control:

```python
from pynext.db import CascadeOptions

class Order(Table):
    items: List[OrderItem] = has_many(
        OrderItem,
        cascade=CascadeOptions(
            on_save=True,     # Save items when order.save()
            on_delete=True,   # Delete items when order.delete()
            on_orphan=True,   # Delete item when removed from collection
        )
    )
```

### When You Need Fine-Grained Control

**Scenario: Aggregate Root Pattern**

In Domain-Driven Design, an Order "owns" its Items completely:

```python
class Order(Table):
    items: List[OrderItem] = has_many(
        OrderItem,
        cascade=CascadeOptions(
            on_save=True,    # Changes save together
            on_delete=True,  # Delete together
            on_orphan=True,  # Removing from list = delete
        )
    )

# Adding items
order.items.append(OrderItem(product_id=1, qty=2))
order.items.append(OrderItem(product_id=2, qty=1))
await order.save()  # Saves order AND both items

# Removing items
order.items.pop(0)  # Schedules item for deletion
await order.save()  # Item is deleted from database

# Deleting order
await order.delete()  # Order AND all items deleted
```

**Scenario: Form Builder**

Form fields exist only as part of the form:

```python
class Form(Table):
    fields: List[FormField] = has_many(
        FormField,
        cascade=CascadeOptions.all()  # Full ownership
    )

# Building a form
form.fields.append(FormField(type="text", label="Name"))
form.fields.append(FormField(type="email", label="Email"))
await form.save()  # Form and fields saved together

# Removing a field
form.fields.remove(email_field)  # Field will be deleted
await form.save()
```

### CascadeOptions Presets

```python
# All cascades enabled (full ownership)
CascadeOptions.all()
# Same as: CascadeOptions(on_save=True, on_delete=True, on_orphan=True, on_merge=True)

# Only cascade deletes
CascadeOptions.delete_only()
# Same as: CascadeOptions(on_delete=True)

# Delete + orphan handling (common pattern)
CascadeOptions.delete_orphan()
# Same as: CascadeOptions(on_delete=True, on_orphan=True)

# Only cascade saves
CascadeOptions.save_only()
# Same as: CascadeOptions(on_save=True)

# No cascades
CascadeOptions.none()
```

---

## Real-World Scenarios

### Scenario 1: User Account Deletion (GDPR Compliance)

```python
class User(Table):
    # Personal data - must be deleted
    profile: Profile = has_one(Profile, on_delete="cascade")
    addresses: List[Address] = has_many(Address, on_delete="cascade")
    payment_methods: List[PaymentMethod] = has_many(PaymentMethod, on_delete="cascade")
    
    # Content - preserve as anonymous
    posts: List[Post] = has_many(Post, on_delete="nullify")
    comments: List[Comment] = has_many(Comment, on_delete="nullify")
    
    # Financial records - must keep for legal
    orders: List[Order] = has_many(Order, on_delete="protect")
    invoices: List[Invoice] = has_many(Invoice, on_delete="protect")
    
    # Activity - can delete
    sessions: List[Session] = has_many(Session, on_delete="cascade")
    notifications: List[Notification] = has_many(Notification, on_delete="cascade")

# GDPR deletion flow
async def handle_gdpr_deletion(user_id):
    user = await User.get(user_id)
    
    try:
        await user.delete()
    except ProtectedDeleteError as e:
        # User has orders - can't fully delete
        # Option 1: Anonymize instead
        await anonymize_user(user)
        # Option 2: Inform user
        raise Exception("Cannot delete account: you have active orders")
```

### Scenario 2: E-Commerce Product Management

```python
class Category(Table):
    name: str
    # Cannot delete category with products
    products: List[Product] = has_many(Product, on_delete="protect")

class Product(Table):
    name: str
    category_id: Optional[int]  # Can be uncategorized
    
    # Delete variants with product
    variants: List[ProductVariant] = has_many(ProductVariant, on_delete="cascade")
    # Delete images with product
    images: List[ProductImage] = has_many(ProductImage, on_delete="cascade")
    # Preserve reviews as historical
    reviews: List[Review] = has_many(Review, on_delete="nullify")

# Safe category deletion
async def delete_category(category_id):
    category = await Category.get(category_id)
    
    if category.products:
        # First reassign products
        uncategorized = await Category.find_by(name="Uncategorized")
        for product in category.products:
            product.category_id = uncategorized.id
            await product.save()
    
    await category.delete()  # Now safe
```

### Scenario 3: Project Management

```python
class Project(Table):
    name: str
    owner_id: int
    
    # Tasks are part of project
    tasks: List[Task] = has_many(Task, on_delete="cascade")
    # Keep documents for audit
    documents: List[Document] = has_many(Document, on_delete="nullify")
    # Team membership
    members: List[ProjectMember] = has_many(ProjectMember, on_delete="cascade")

class Task(Table):
    title: str
    project_id: int
    assignee_id: Optional[int]
    
    # Comments on task
    comments: List[TaskComment] = has_many(TaskComment, on_delete="cascade")
    # Time entries for billing
    time_entries: List[TimeEntry] = has_many(TimeEntry, on_delete="protect")

class Employee(Table):
    name: str
    
    # Cannot delete employee with active projects
    projects: List[Project] = has_many(Project, on_delete="protect")
    # Tasks become unassigned
    tasks: List[Task] = has_many(Task, foreign_key="assignee_id", on_delete="nullify")
```

---

## PyNext vs SQLAlchemy

### The SQLAlchemy Problem

```python
# SQLAlchemy - Confusing string-based syntax
class User(Base):
    posts = relationship(
        "Post", 
        cascade="all, delete-orphan",  # What's in "all"?
        passive_deletes=True,           # What does this do?
    )

# Questions developers ask:
# - What's in "all"? (save-update, merge, refresh-expire, expunge)
# - What's "delete-orphan" vs "delete"?
# - What if I typo "casade" instead of "cascade"?
# - What combinations are valid?
# - What does passive_deletes actually do?
```

### The PyNext Solution

```python
# PyNext - Clear, type-safe, self-documenting
class User(Table):
    posts: List[Post] = has_many(Post, on_delete="cascade")
    
# For fine control:
class User(Table):
    posts: List[Post] = has_many(Post, cascade=CascadeOptions(
        on_save=True,     # Clear!
        on_delete=True,   # Clear!
        on_orphan=True,   # Clear!
    ))
```

### Comparison

| Feature | SQLAlchemy | PyNext |
|---------|------------|--------|
| **Syntax** | `cascade="all, delete-orphan"` | `on_delete="cascade"` |
| **Type Safety** | String (typos silently fail) | Enum (IDE autocomplete) |
| **Discoverability** | Read docs | IDE shows options |
| **Clarity** | Cryptic ("passive_deletes"?) | Self-documenting |
| **Fine Control** | Same confusing string | Separate `CascadeOptions` |
| **Default** | Implicit behaviors | Explicit `"none"` |

---

## Database-Level Cascade Integration

PyNext automatically generates PostgreSQL FK constraints with `ON DELETE` clauses for maximum performance:

```python
# You write this:
class User(Table):
    posts: List[Post] = has_many(Post, on_delete="cascade")

# PyNext generates this SQL:
# CREATE TABLE posts (
#     id SERIAL PRIMARY KEY,
#     user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
# )
```

### PostgreSQL Mapping

| PyNext | PostgreSQL | Behavior |
|--------|------------|----------|
| `"cascade"` | `ON DELETE CASCADE` | DB handles deletion |
| `"nullify"` | `ON DELETE SET NULL` | DB sets to NULL |
| `"protect"` | `ON DELETE RESTRICT` | DB blocks deletion |
| `"none"` | `ON DELETE NO ACTION` | No automatic action |

### Why This Matters

**Performance:**
```python
# Without DB cascades: N+1 deletes
await user.delete()
# Python: SELECT * FROM posts WHERE user_id = 1
# Python: DELETE FROM posts WHERE id = 1
# Python: DELETE FROM posts WHERE id = 2
# ... 100 more queries
# Python: DELETE FROM users WHERE id = 1

# With DB cascades: 1 delete
await user.delete()
# SQL: DELETE FROM users WHERE id = 1
# PostgreSQL handles cascade in single atomic operation
```

---

## Performance Considerations

### When to Use App-Level vs DB-Level Cascades

| Use App-Level When | Use DB-Level When |
|--------------------|-------------------|
| Need to trigger Python hooks | Maximum performance needed |
| Complex business logic | Simple delete cascades |
| Audit logging required | Millions of records |
| Validation before delete | No Python logic needed |

### Batch Deletion

```python
# For very large collections, consider DB-level:
class Analytics(Table):
    # Millions of events - let DB handle
    events: List[Event] = has_many(Event, on_delete="none")
    # FK constraint: ON DELETE CASCADE
```

---

## Anti-Patterns and What NOT to Do

### Anti-Pattern 1: No Cascade Strategy

```python
# ❌ BAD: No explicit cascade - unclear what happens
class User(Table):
    posts: List[Post] = has_many(Post)  # on_delete="none" by default

# What happens when you delete user? Unknown!
```

```python
# ✅ GOOD: Always be explicit
class User(Table):
    posts: List[Post] = has_many(Post, on_delete="cascade")
```

### Anti-Pattern 2: Nullify Without Optional FK

```python
# ❌ BAD: Nullify but FK is required
class Post(Table):
    author_id: int  # NOT Optional!

class User(Table):
    posts: List[Post] = has_many(Post, on_delete="nullify")  # Will fail!
```

```python
# ✅ GOOD: FK must be Optional for nullify
class Post(Table):
    author_id: Optional[int]  # Can be NULL

class User(Table):
    posts: List[Post] = has_many(Post, on_delete="nullify")
```

### Anti-Pattern 3: Cascade Everything

```python
# ❌ BAD: Cascade on financial records
class User(Table):
    orders: List[Order] = has_many(Order, on_delete="cascade")  # Losing money!
    payments: List[Payment] = has_many(Payment, on_delete="cascade")  # Audit trail gone!
```

```python
# ✅ GOOD: Protect critical data
class User(Table):
    orders: List[Order] = has_many(Order, on_delete="protect")
    payments: List[Payment] = has_many(Payment, on_delete="protect")
```

### Anti-Pattern 4: Protect Non-Critical Data

```python
# ❌ BAD: Protect makes deletion impossible
class User(Table):
    notifications: List[Notification] = has_many(Notification, on_delete="protect")
    sessions: List[Session] = has_many(Session, on_delete="protect")
    # Can never delete a user!
```

```python
# ✅ GOOD: Cascade non-critical data
class User(Table):
    notifications: List[Notification] = has_many(Notification, on_delete="cascade")
    sessions: List[Session] = has_many(Session, on_delete="cascade")
```

---

## Migration Guide

### From SQLAlchemy

| SQLAlchemy | PyNext |
|------------|--------|
| `cascade="delete"` | `on_delete="cascade"` |
| `cascade="delete-orphan"` | `cascade=CascadeOptions.delete_orphan()` |
| `cascade="all"` | `cascade=CascadeOptions.all()` |
| `cascade="save-update"` | `cascade=CascadeOptions(on_save=True)` |
| `passive_deletes=True` | `on_delete="none"` (let DB handle) |

### Example Migration

**SQLAlchemy:**
```python
class User(Base):
    posts = relationship(
        "Post",
        cascade="all, delete-orphan",
        backref="author"
    )
```

**PyNext:**
```python
class User(Table):
    posts: List[Post] = has_many(
        Post,
        backref="author",
        cascade=CascadeOptions.all()
    )
```

---

## Troubleshooting

### ProtectedDeleteError

**Problem:** Trying to delete a record with protected relationships.

```python
try:
    await user.delete()
except ProtectedDeleteError as e:
    print(f"Cannot delete: has {e.related_count} {e.relationship}")
```

**Solutions:**
1. Reassign children to another parent
2. Delete/cancel children first
3. Archive instead of delete
4. Change cascade to `"cascade"` or `"nullify"`

### Orphaned Records

**Problem:** Records with FK pointing to deleted parent.

**Cause:** Using `on_delete="none"` without database constraints.

**Solution:** Either add DB-level cascade or use explicit cascade:

```python
# Option 1: App-level
posts: List[Post] = has_many(Post, on_delete="cascade")

# Option 2: DB-level
# ALTER TABLE posts ADD CONSTRAINT ... ON DELETE CASCADE
```

### Nullify Failing

**Problem:** "Cannot set NULL on non-optional column"

**Cause:** FK column is not Optional.

**Solution:**
```python
# Change from
author_id: int

# To
author_id: Optional[int]
```

---

## API Reference

### OnDeleteAction Values

| Value | Description |
|-------|-------------|
| `"cascade"` | Delete related records |
| `"nullify"` | Set FK to NULL |
| `"protect"` | Block deletion if related exist |
| `"none"` | Do nothing (default) |

### CascadeOptions

```python
@dataclass
class CascadeOptions:
    on_save: bool = False    # Cascade save operations
    on_delete: bool = False  # Cascade delete operations
    on_orphan: bool = False  # Delete when removed from collection
    on_merge: bool = False   # Cascade merge operations
    
    @classmethod
    def all(cls): ...           # All cascades enabled
    @classmethod
    def delete_only(cls): ...   # Only on_delete
    @classmethod
    def delete_orphan(cls): ... # on_delete + on_orphan
    @classmethod
    def save_only(cls): ...     # Only on_save
    @classmethod
    def none(cls): ...          # No cascades
```

### Relationship Parameters

```python
has_many(
    model: Type[T],
    foreign_key: str = None,
    backref: str = None,
    on_delete: str = "none",              # Simple preset
    cascade: CascadeOptions = None,        # Fine-grained control
)

has_one(
    model: Type[T],
    foreign_key: str = None,
    backref: str = None,
    on_delete: str = "none",
    cascade: CascadeOptions = None,
)
```

---

## Summary

| Question | Cascade Type |
|----------|--------------|
| "Children meaningless without parent?" | `cascade` |
| "Preserve children as anonymous?" | `nullify` |
| "Must prevent accidental data loss?" | `protect` |
| "Let database decide?" | `none` |

**Key Principles:**
1. **Always be explicit** - don't rely on defaults
2. **Think about data value** - financial records need protection
3. **Consider user expectations** - content platforms often preserve content
4. **Use DB-level cascades** for performance with large datasets
5. **Test deletion scenarios** - verify cascades work as expected
