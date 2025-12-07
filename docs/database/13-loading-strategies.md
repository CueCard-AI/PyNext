# Loading Strategies

Complete control over how and when relationships are loaded with dead-simple, AI-friendly APIs.

## Table of Contents

1. [Introduction](#introduction)
2. [The N+1 Problem Explained](#the-n1-problem-explained)
3. [Quick Start Guide](#quick-start-guide)
4. [Loading Strategies Deep Dive](#loading-strategies-deep-dive)
5. [Model-Level Configuration](#model-level-configuration)
6. [Query-Level Overrides](#query-level-overrides)
7. [Nested Loading Patterns](#nested-loading-patterns)
8. [Dynamic Relationships](#dynamic-relationships)
9. [N+1 Prevention System](#n1-prevention-system)
10. [Performance Optimization](#performance-optimization)
11. [Real-World Examples](#real-world-examples)
12. [Common Patterns](#common-patterns)
13. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
14. [Testing Strategies](#testing-strategies)
15. [Debugging Guide](#debugging-guide)
16. [Migration Guide](#migration-guide)
17. [Troubleshooting](#troubleshooting)
18. [Architecture Overview](#architecture-overview)
19. [Complete API Reference](#complete-api-reference)
20. [FAQ](#faq)

---

## Introduction

### What Are Loading Strategies?

Loading strategies control **when** and **how** related data is fetched from the database. When you have a `User` with `posts`, the loading strategy determines:

- **When**: Is the data loaded immediately with the user, or when you first access `user.posts`?
- **How**: Is it loaded via a JOIN, a separate query, or not at all?

### Why Do Loading Strategies Matter?

Without proper loading strategies, your application can suffer from:

1. **N+1 Query Problem**: Executing hundreds of queries instead of 2
2. **Over-fetching**: Loading data you don't need
3. **Under-fetching**: Making users wait for lazy loads
4. **Memory Issues**: Loading millions of rows accidentally

### Design Philosophy

PyNext's loading strategies follow these principles:

```
1. SIMPLE        - One parameter (lazy=) controls everything
2. EXPLICIT      - You always know when queries happen
3. FLEXIBLE      - Override at any level (model or query)
4. AI-FRIENDLY   - Clear names, predictable behavior
5. SAFE          - Easy to prevent N+1 with lazy="raise"
```

### Available Strategies

| Strategy | Description | Queries | Best For |
|----------|-------------|---------|----------|
| `select` | Load on access | 1 per access | Rarely accessed |
| `joined` | LEFT JOIN | 1 total | Single objects |
| `selectin` | SELECT WHERE IN | 2 total | Collections |
| `subquery` | Subquery IN | 2 total | Complex queries |
| `raise` | Raise error | 0 | N+1 prevention |
| `dynamic` | Query builder | On demand | Large collections |

---

## The N+1 Problem Explained

### What Is the N+1 Problem?

The N+1 query problem is the most common performance issue in ORM-based applications. It occurs when:

1. You load N records from the database (1 query)
2. For each record, you access a relationship (N queries)

**Total: N+1 queries instead of 2**

### Concrete Example

```python
# THE PROBLEM: N+1 Queries

class User(Table):
    name: str
    posts: List["Post"] = has_many("Post")  # Default lazy="select"

class Post(Table):
    title: str
    user_id: int

# This innocent-looking code causes N+1 queries:
users = await User.select()  # Query 1: SELECT * FROM users

for user in users:  # If 100 users...
    print(user.posts)  # ...executes 100 more queries!
    # Query 2: SELECT * FROM posts WHERE user_id = 1
    # Query 3: SELECT * FROM posts WHERE user_id = 2
    # Query 4: SELECT * FROM posts WHERE user_id = 3
    # ... 97 more queries ...

# Total: 101 queries for what should be 2!
```

### Why Is It So Bad?

```
With 100 users:
- N+1 approach: 101 queries × 10ms = 1,010ms (1+ second!)
- Optimized:    2 queries × 10ms = 20ms

With 1000 users:
- N+1 approach: 1,001 queries × 10ms = 10,010ms (10+ seconds!)
- Optimized:    2 queries × 10ms = 20ms
```

### The Solution

```python
# SOLUTION: Use selectinload

users = await User.select().options(
    selectinload("posts")  # Load all posts in ONE extra query
)

for user in users:  # Now safe!
    print(user.posts)  # No additional queries - already loaded!

# Total: 2 queries
# Query 1: SELECT * FROM users
# Query 2: SELECT * FROM posts WHERE user_id IN (1, 2, 3, ... 100)
```

---

## Quick Start Guide

### Step 1: Install and Import

```python
from pynext.db import (
    Table,
    has_many,
    has_one,
    belongs_to,
    # Loading option functions
    joinedload,
    selectinload,
    subqueryload,
    raiseload,
    noload,
)
from typing import List, Optional
```

### Step 2: Define Models with Loading Strategies

```python
class User(Table):
    name: str
    email: str
    
    # SELECTIN for collections - loads all posts in one extra query
    posts: List["Post"] = has_many("Post", lazy="selectin")
    
    # JOINED for single objects - loads profile in same query
    profile: Optional["Profile"] = has_one("Profile", lazy="joined")
    
    # DYNAMIC for huge collections - returns query builder
    audit_logs: List["AuditLog"] = has_many("AuditLog", lazy="dynamic")
    
    # RAISE for forbidden lazy loads - prevents N+1 in production
    sensitive_data: List["SensitiveData"] = has_many("SensitiveData", lazy="raise")


class Post(Table):
    title: str
    content: str
    user_id: int
    
    # JOINED for belongs_to - single FK lookup
    author: "User" = belongs_to("User", lazy="joined")
    
    # SELECTIN for comments collection
    comments: List["Comment"] = has_many("Comment", lazy="selectin")


class Profile(Table):
    bio: str
    avatar_url: str
    user_id: int


class Comment(Table):
    text: str
    post_id: int
    user_id: int
    
    # Load comment author with JOIN
    author: "User" = belongs_to("User", lazy="joined")


class AuditLog(Table):
    action: str
    timestamp: str
    user_id: int
```

### Step 3: Query with Eager Loading

```python
# Basic query - uses model defaults
users = await User.select().where(active=True)

# Override at query time
users = await User.select().options(
    selectinload("posts"),       # Eager load posts
    joinedload("profile"),       # JOIN profile
).where(active=True)

# Nested loading
users = await User.select().options(
    selectinload("posts")
        .joinedload("author")
        .selectinload("comments")
).where(active=True)

# Access loaded data - NO extra queries!
for user in users:
    print(f"User: {user.name}")
    print(f"Profile: {user.profile.bio if user.profile else 'No profile'}")
    print(f"Posts: {len(user.posts)}")
    
    for post in user.posts:
        print(f"  - {post.title} ({len(post.comments)} comments)")
```

### Step 4: Handle Dynamic Relationships

```python
user = await User.get(1)

# audit_logs is a DynamicRelationship, not a list!
# Use query methods:
recent_logs = await user.audit_logs.order_by("-timestamp").limit(10)
error_count = await user.audit_logs.filter(level="error").count()
has_warnings = await user.audit_logs.filter(level="warning").exists()

# Or await directly for all items (use cautiously!)
all_logs = await user.audit_logs  # Same as await user.audit_logs.all()
```

---

## Loading Strategies Deep Dive

### Strategy 1: SELECT (Default)

**What It Does**: Executes a separate query when you first access the relationship.

**SQL Pattern**:
```sql
-- Initial query
SELECT * FROM users WHERE id = 1

-- When you access user.posts
SELECT * FROM posts WHERE user_id = 1
```

**Code Example**:
```python
class User(Table):
    posts: List[Post] = has_many(Post, lazy="select")  # Default

# Usage
user = await User.get(1)  # 1 query
posts = user.posts        # 1 more query (lazy load triggered)
```

**When to Use**:
- Relationship is rarely accessed
- Single object queries (not loops)
- When you're certain about access patterns

**When NOT to Use**:
- In loops (causes N+1)
- When you usually need the related data
- In performance-critical code

**Pros**:
- Simple default behavior
- Only loads what you access
- No upfront overhead

**Cons**:
- N+1 prone in loops
- Unpredictable query timing
- Hard to optimize

---

### Strategy 2: JOINED

**What It Does**: Loads the relationship using a LEFT JOIN in the same query.

**SQL Pattern**:
```sql
SELECT users.*, profiles.*
FROM users
LEFT JOIN profiles ON users.id = profiles.user_id
WHERE users.id = 1
```

**Code Example**:
```python
class User(Table):
    profile: Profile = has_one(Profile, lazy="joined")

class Post(Table):
    author: User = belongs_to(User, lazy="joined")

# Usage
user = await User.get(1)        # Profile loaded in same query!
print(user.profile.bio)         # No extra query

posts = await Post.select()     # Authors loaded via JOIN
for post in posts:
    print(post.author.name)     # No extra queries!
```

**When to Use**:
- `belongs_to` relationships (single FK lookup)
- `has_one` relationships (single related object)
- Always need the related data
- Related table is small

**When NOT to Use**:
- `has_many` with large collections (creates row explosion)
- Optional relationships you usually don't need
- Deep nesting (multiple JOINs become expensive)

**Pros**:
- Single query (best performance for single objects)
- Data always available
- No N+1 risk

**Cons**:
- Returns duplicate rows for has_many (row explosion)
- Loads data even if unused
- Memory overhead for large JOINs

**Row Explosion Example** (why not to use joined for has_many):
```
User 1 has 100 posts
User 2 has 50 posts
User 3 has 200 posts

With joined loading:
- Without JOIN: 3 rows returned
- With JOIN: 350 rows returned (1*100 + 1*50 + 1*200)

The same user data is duplicated for each post!
```

---

### Strategy 3: SELECTIN

**What It Does**: Collects all parent IDs, then loads children with `SELECT WHERE IN`.

**SQL Pattern**:
```sql
-- Query 1: Load users
SELECT * FROM users WHERE active = true

-- Query 2: Load all posts for those users
SELECT * FROM posts WHERE user_id IN (1, 2, 3, 4, 5, ...)
```

**Code Example**:
```python
class User(Table):
    posts: List[Post] = has_many(Post, lazy="selectin")

# Usage
users = await User.select().where(active=True)  # Query 1
# Query 2 automatically executes: SELECT * FROM posts WHERE user_id IN (...)

for user in users:
    print(user.posts)  # Already loaded, no query!
```

**When to Use**:
- `has_many` relationships (most common choice)
- Loading multiple parent objects
- Collection sizes are reasonable (< 10,000)
- Need all items in the collection

**When NOT to Use**:
- Very large IN clauses (> 10,000 IDs)
- Need filtering/pagination on the collection
- Complex parent queries with pagination

**Pros**:
- Only 2 queries regardless of parent count
- No row duplication
- Efficient for batches

**Cons**:
- 2 queries minimum
- Large IN clauses can be slow
- Loads entire collection

---

### Strategy 4: SUBQUERY

**What It Does**: Uses a subquery to fetch related IDs instead of passing them directly.

**SQL Pattern**:
```sql
-- Query 1: Load users
SELECT * FROM users WHERE email LIKE '%@company.com%' LIMIT 100

-- Query 2: Load posts using subquery
SELECT * FROM posts 
WHERE user_id IN (
    SELECT id FROM users WHERE email LIKE '%@company.com%' LIMIT 100
)
```

**Code Example**:
```python
class User(Table):
    posts: List[Post] = has_many(Post, lazy="subquery")

# Usage - great for complex queries
users = await User.select().where_like(
    email="%@company.com%"
).order_by("-created_at").limit(100)

for user in users:
    print(user.posts)  # Loaded via subquery
```

**When to Use**:
- Complex parent queries with LIMIT/OFFSET
- Deep nesting where IDs might be duplicated
- Parent query is hard to replicate for IN clause
- Very large number of parent IDs

**When NOT to Use**:
- Simple queries (selectin is simpler)
- Small result sets
- When IN clause is more efficient

**Pros**:
- Handles complex parent queries
- No need to collect IDs in application
- Works well with pagination

**Cons**:
- Slightly more complex SQL
- May be slower for simple cases
- Database needs to execute subquery

---

### Strategy 5: RAISE

**What It Does**: Raises `LazyLoadError` if the relationship is accessed without explicit loading.

**SQL Pattern**:
```sql
-- No query executed - raises exception instead!
```

**Code Example**:
```python
class User(Table):
    sensitive_data: List[SensitiveData] = has_many(SensitiveData, lazy="raise")

# This WILL raise an error:
user = await User.get(1)
user.sensitive_data  # LazyLoadError!

# This works - explicitly loaded:
user = await User.select().options(
    selectinload("sensitive_data")
).where(id=1).first()
user.sensitive_data  # Works! Explicitly loaded.
```

**Error Message**:
```
LazyLoadError: Accessing 'sensitive_data' on User would trigger a lazy load.
This relationship has lazy='raise' to prevent N+1 queries.
Use .options(selectinload('sensitive_data')) or .with_related('sensitive_data') to eager load.
```

**When to Use**:
- Preventing N+1 queries in production
- Performance-critical endpoints
- Relationships that should always be explicitly loaded
- During development to catch N+1 early

**When NOT to Use**:
- When lazy loading is acceptable
- Relationships you always access (use joined/selectin instead)
- Prototyping/rapid development

**Pros**:
- Prevents N+1 completely
- Forces explicit loading decisions
- Great for production safety
- Catches issues during development

**Cons**:
- Requires explicit loading everywhere
- More verbose code
- Can be annoying during development

---

### Strategy 6: DYNAMIC

**What It Does**: Returns a query builder instead of loading all results.

**SQL Pattern**:
```sql
-- No query until you execute it!
-- Then whatever query you build:
SELECT * FROM audit_logs WHERE user_id = 1 ORDER BY timestamp DESC LIMIT 10
```

**Code Example**:
```python
class User(Table):
    # Could have millions of audit logs!
    audit_logs: List[AuditLog] = has_many(AuditLog, lazy="dynamic")

# Usage
user = await User.get(1)

# audit_logs is NOT a list - it's a DynamicRelationship!
print(type(user.audit_logs))  # <class 'DynamicRelationship'>

# Query methods available:
recent = await user.audit_logs.order_by("-timestamp").limit(10)
errors = await user.audit_logs.filter(level="error")
count = await user.audit_logs.count()  # COUNT(*) query
exists = await user.audit_logs.filter(level="critical").exists()
first = await user.audit_logs.order_by("-timestamp").first()

# Pagination
page_2 = await user.audit_logs.order_by("-timestamp").offset(20).limit(10)

# Chained filters
recent_errors = await (
    user.audit_logs
    .filter(level="error")
    .order_by("-timestamp")
    .limit(5)
)
```

**When to Use**:
- Collections with potentially millions of items
- Need filtering/pagination on the collection
- Don't want to load all items at once
- Analytics/reporting scenarios

**When NOT to Use**:
- Small collections (< 1000 items)
- Always need all items
- Need bidirectional sync (backref)

**Pros**:
- Never loads too much data
- Full query builder flexibility
- COUNT/EXISTS without loading
- Memory efficient

**Cons**:
- Can't iterate directly (must await)
- No backref synchronization
- More verbose for simple access

---

## Model-Level Configuration

### Setting Defaults on Relationships

Configure loading strategy when defining your models:

```python
class User(Table):
    name: str
    email: str
    
    # Always eager load profile with JOIN
    profile: Profile = has_one(Profile, lazy="joined")
    
    # Batch load posts when user is loaded
    posts: List[Post] = has_many(Post, lazy="selectin")
    
    # Never auto-load audit logs
    audit_logs: List[AuditLog] = has_many(AuditLog, lazy="raise")
    
    # Return query builder for notifications
    notifications: List[Notification] = has_many(Notification, lazy="dynamic")
    
    # Default lazy loading for rarely accessed data
    preferences: List[Preference] = has_many(Preference, lazy="select")
```

### Combining lazy with backref

Loading strategies work alongside bidirectional relationships:

```python
class User(Table):
    # Selectin loading + backref
    posts: List[Post] = has_many(Post, backref="author", lazy="selectin")

class Post(Table):
    user_id: int
    # author: User is auto-created via backref
    # backref gets default lazy="select"
    
    # Explicit belongs_to with joined loading
    category: Category = belongs_to(Category, lazy="joined")
```

### Combining lazy with back_populates

```python
class User(Table):
    posts: List[Post] = has_many(Post, back_populates="author", lazy="selectin")

class Post(Table):
    user_id: int
    author: User = belongs_to(User, back_populates="posts", lazy="joined")
```

### Strategy Recommendations by Relationship Type

| Relationship Type | Recommended Strategy | Why |
|-------------------|---------------------|-----|
| `belongs_to` | `joined` | Single FK lookup, nearly always needed |
| `has_one` | `joined` | Single object, efficient with JOIN |
| `has_many` (small) | `selectin` | Batch loading without duplicates |
| `has_many` (large) | `dynamic` | Don't load millions at once |
| `has_many` (forbidden) | `raise` | Prevent N+1 in critical paths |
| Rarely accessed | `select` | Only load when needed |

---

## Query-Level Overrides

### The options() Method

Override model defaults at query time:

```python
# Model default is lazy="select", but we want eager loading here
users = await User.select().options(
    selectinload("posts"),
    joinedload("profile"),
)
```

### Available Loading Functions

```python
from pynext.db import (
    joinedload,      # Load with LEFT JOIN
    selectinload,    # Load with SELECT WHERE id IN
    subqueryload,    # Load with subquery
    raiseload,       # Raise error if accessed
    noload,          # Don't load (explicit ignore)
    lazyload,        # Use default lazy loading
    immediateload,   # Alias for selectinload
    eagerload,       # Alias for selectinload
)
```

### Function Details

#### joinedload(relationship)

```python
# Load author with LEFT JOIN
posts = await Post.select().options(
    joinedload("author")
)

# SQL:
# SELECT posts.*, users.*
# FROM posts
# LEFT JOIN users ON posts.user_id = users.id
```

#### selectinload(relationship)

```python
# Load posts with SELECT IN
users = await User.select().options(
    selectinload("posts")
)

# SQL:
# SELECT * FROM users
# SELECT * FROM posts WHERE user_id IN (1, 2, 3, ...)
```

#### subqueryload(relationship)

```python
# Load with subquery (good for complex parent queries)
users = await User.select().options(
    subqueryload("posts")
).where_like(email="%@company.com%").limit(100)

# SQL:
# SELECT * FROM users WHERE email LIKE '%@company.com%' LIMIT 100
# SELECT * FROM posts WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@company.com%' LIMIT 100)
```

#### raiseload(relationship)

```python
# Block lazy loading at query time
users = await User.select().options(
    selectinload("posts"),
    raiseload("audit_logs"),  # Will raise if accessed
)

users[0].posts       # Works - explicitly loaded
users[0].audit_logs  # Raises LazyLoadError!
```

#### noload(relationship)

```python
# Explicitly don't load (override model default)
users = await User.select().options(
    noload("posts"),  # Even if model has lazy="selectin"
)

users[0].posts  # Returns empty list, no query
```

### Multiple Options

```python
users = await User.select().options(
    selectinload("posts"),
    joinedload("profile"),
    selectinload("comments"),
    raiseload("audit_logs"),
    noload("preferences"),
)
```

### Options Order

Options are processed in order, but later options for the same relationship override earlier ones:

```python
# Last one wins
users = await User.select().options(
    selectinload("posts"),  # This is overridden
    joinedload("posts"),    # This takes effect
)
```

### Options with Query Methods

Options work with all query methods:

```python
users = await User.select().options(
    selectinload("posts")
).where(
    active=True
).where_not(
    role="admin"
).order_by(
    "-created_at"
).limit(
    50
).offset(
    0
)
```

---

## Nested Loading Patterns

### Basic Nested Loading

Load relationships of relationships:

```python
# User -> Posts -> Comments
users = await User.select().options(
    selectinload("posts").selectinload("comments")
)

# Access nested data without queries
for user in users:
    for post in user.posts:
        for comment in post.comments:
            print(comment.text)
```

### Deep Nesting

```python
# User -> Posts -> Comments -> Author -> Profile
users = await User.select().options(
    selectinload("posts")
        .selectinload("comments")
        .joinedload("author")
        .joinedload("profile")
)
```

### Multiple Branches

Load multiple relationships at the same level:

```python
# Load posts with BOTH author AND comments
opt = selectinload("posts")
opt.joinedload("author")        # posts -> author
opt.selectinload("comments")    # posts -> comments

users = await User.select().options(opt)

# Or inline:
users = await User.select().options(
    selectinload("posts").joinedload("author"),
    selectinload("posts").selectinload("comments"),
)
```

### Mixed Strategies in Chain

```python
users = await User.select().options(
    selectinload("posts")           # Batch load posts
        .joinedload("author")       # JOIN author (single object)
        .selectinload("comments")   # Batch load comments
        .joinedload("commenter")    # JOIN commenter (single object)
)
```

### Complex Graph Example

```python
# E-commerce: Load order with all related data
orders = await Order.select().options(
    # Order -> Customer with profile
    joinedload("customer").joinedload("profile"),
    
    # Order -> Items with product and category
    selectinload("items")
        .joinedload("product")
        .joinedload("category"),
    
    # Order -> Shipping address
    joinedload("shipping_address"),
    
    # Order -> Payment with method
    joinedload("payment").joinedload("payment_method"),
).where(status="pending")
```

---

## Dynamic Relationships

### When to Use Dynamic

Use `lazy="dynamic"` when:

1. Collection could have thousands/millions of items
2. You need filtering/pagination
3. You want COUNT without loading
4. Memory is a concern

### Creating Dynamic Relationships

```python
class User(Table):
    # Could have millions of audit logs
    audit_logs: List[AuditLog] = has_many(AuditLog, lazy="dynamic")
    
    # Could have thousands of notifications
    notifications: List[Notification] = has_many(Notification, lazy="dynamic")
```

### DynamicRelationship API

```python
user = await User.get(1)

# user.audit_logs is a DynamicRelationship, NOT a list!

# Get all (returns Query, must await)
all_logs = await user.audit_logs.all()

# Filter
errors = await user.audit_logs.filter(level="error")
logins = await user.audit_logs.where(action="login")

# Compound filters
recent_errors = await (
    user.audit_logs
    .filter(level="error")
    .where(action="login")
)

# IN clause filter
specific = await user.audit_logs.where_in(id=[1, 2, 3])

# NOT filter
non_errors = await user.audit_logs.where_not(level="error")

# Ordering
recent = await user.audit_logs.order_by("-timestamp")
oldest = await user.audit_logs.order_by("timestamp")
multi_sort = await user.audit_logs.order_by("-level", "timestamp")

# Limiting
top_10 = await user.audit_logs.limit(10)

# Pagination
page_2 = await user.audit_logs.offset(20).limit(10)

# Count (doesn't load all records)
total = await user.audit_logs.count()
error_count = await user.audit_logs.filter(level="error").count()

# Exists (efficient check)
has_errors = await user.audit_logs.filter(level="error").exists()

# First item
latest = await user.audit_logs.order_by("-timestamp").first()

# One item (raises if not found)
specific = await user.audit_logs.filter(id=123).one()
```

### Awaiting Dynamic Relationships

```python
# Direct await gets all items
logs = await user.audit_logs  # Same as await user.audit_logs.all()

# Async iteration
async for log in user.audit_logs:
    print(log.action)
```

### Dynamic vs Selectin Comparison

```python
# SELECTIN: Loads ALL posts immediately
class UserWithSelectin(Table):
    posts: List[Post] = has_many(Post, lazy="selectin")

user = await UserWithSelectin.get(1)
user.posts  # Already loaded - it's a list of 10,000 posts in memory!

# DYNAMIC: Loads on demand
class UserWithDynamic(Table):
    posts: List[Post] = has_many(Post, lazy="dynamic")

user = await UserWithDynamic.get(1)
user.posts  # It's a DynamicRelationship, NOT a list

# Only load what you need:
recent = await user.posts.order_by("-created_at").limit(10)  # Only 10 in memory
count = await user.posts.count()  # No posts loaded, just COUNT(*)
```

---

## N+1 Prevention System

### Using lazy="raise"

The most aggressive N+1 prevention:

```python
class User(Table):
    posts: List[Post] = has_many(Post, lazy="raise")

# This WILL raise!
user = await User.get(1)
user.posts  # LazyLoadError!

# Must explicitly load:
user = await User.select().options(
    selectinload("posts")
).where(id=1).first()
user.posts  # Works!
```

### Using raiseload() in Options

Block specific relationships at query time:

```python
# Load profile but block everything else
users = await User.select().options(
    joinedload("profile"),
    raiseload("posts"),
    raiseload("comments"),
    raiseload("audit_logs"),
)

users[0].profile     # Works
users[0].posts       # LazyLoadError!
users[0].comments    # LazyLoadError!
users[0].audit_logs  # LazyLoadError!
```

### LazyLoadError Details

```python
class LazyLoadError(Exception):
    """Raised when accessing a relationship with lazy='raise'."""
    
    relationship: str       # e.g., "posts"
    model: Optional[str]    # e.g., "User"
```

**Error Message Format**:
```
LazyLoadError: Accessing 'posts' on User would trigger a lazy load.
This relationship has lazy='raise' to prevent N+1 queries.
Use .options(selectinload('posts')) or .with_related('posts') to eager load.
```

### Development vs Production Strategy

```python
# In development - catch N+1 early
class User(Table):
    posts: List[Post] = has_many(Post, lazy="raise")

# In production - same protection

# For specific endpoints where you know you need data:
async def get_user_with_posts(user_id: int):
    return await User.select().options(
        selectinload("posts")
    ).where(id=user_id).first()

# For endpoints where you DON'T need posts:
async def get_user_basic(user_id: int):
    return await User.get(user_id)
    # Accessing .posts would raise - that's good!
    # It means we're protected from accidental N+1
```

### Catching LazyLoadError

```python
try:
    users = await User.select()
    for user in users:
        print(user.posts)  # Might raise!
except LazyLoadError as e:
    print(f"Need to eager load: {e.relationship}")
    # Fix: Add selectinload("posts") to your query
```

---

## Performance Optimization

### Query Count by Strategy

| Scenario | select | joined | selectin | subquery | raise | dynamic |
|----------|--------|--------|----------|----------|-------|---------|
| 1 user, access posts | 2 | 1 | 2 | 2 | 0* | 1** |
| 100 users, access posts | 101 | 1 | 2 | 2 | 0* | 100** |
| 100 users, no access | 1 | 1 | 2 | 2 | 1 | 1 |

\* raises error, ** on-demand queries

### Memory Usage by Strategy

| Strategy | Memory Pattern |
|----------|---------------|
| select | Loads on demand, can accumulate |
| joined | All in memory from start |
| selectin | All in memory from start |
| subquery | All in memory from start |
| raise | Zero until explicit load |
| dynamic | Only loaded items in memory |

### Choosing the Right Strategy

**Decision Tree**:

```
Is it a belongs_to or has_one?
├─ Yes → Use joined
└─ No (has_many) →
    Is the collection huge (>10k items)?
    ├─ Yes → Use dynamic
    └─ No →
        Do you always need this data?
        ├─ Yes → Use selectin
        └─ No →
            Is N+1 a concern?
            ├─ Yes → Use raise
            └─ No → Use select (default)
```

### Benchmarking Example

```python
import time

# BAD: N+1 pattern
start = time.time()
users = await User.select().limit(100)  # 1 query
for user in users:
    _ = user.posts  # 100 queries!
print(f"N+1: {time.time() - start:.2f}s")  # ~1-2 seconds

# GOOD: Eager loading
start = time.time()
users = await User.select().options(
    selectinload("posts")
).limit(100)  # 2 queries
for user in users:
    _ = user.posts  # No queries!
print(f"Eager: {time.time() - start:.2f}s")  # ~0.02 seconds
```

### Optimization Tips

1. **Always eager load in loops**:
```python
# BAD
users = await User.select()
for user in users:
    print(user.posts)  # N+1!

# GOOD
users = await User.select().options(selectinload("posts"))
for user in users:
    print(user.posts)  # No N+1
```

2. **Use dynamic for huge collections**:
```python
# BAD - might load millions
audit_logs: List[AuditLog] = has_many(AuditLog)  # lazy="select"
logs = user.audit_logs  # Loads ALL logs!

# GOOD - load on demand
audit_logs: List[AuditLog] = has_many(AuditLog, lazy="dynamic")
recent = await user.audit_logs.limit(10)  # Only 10 loaded
```

3. **Use raise in production**:
```python
# Development will catch N+1 issues early
sensitive_data: List[Data] = has_many(Data, lazy="raise")
```

4. **Minimize JOINs for has_many**:
```python
# BAD - row explosion
posts: List[Post] = has_many(Post, lazy="joined")  # Don't do this!

# GOOD - no duplicates
posts: List[Post] = has_many(Post, lazy="selectin")
```

---

## Real-World Examples

### Example 1: Blog Platform

```python
class Author(Table):
    name: str
    bio: str
    
    # Selectin for posts (usually need all)
    posts: List["BlogPost"] = has_many("BlogPost", lazy="selectin")
    
    # Dynamic for comments (could be thousands)
    all_comments: List["Comment"] = has_many("Comment", lazy="dynamic")


class BlogPost(Table):
    title: str
    content: str
    author_id: int
    category_id: int
    
    # Joined for author (always show)
    author: Author = belongs_to(Author, lazy="joined")
    
    # Joined for category (always show)
    category: "Category" = belongs_to("Category", lazy="joined")
    
    # Selectin for comments (show on post page)
    comments: List["Comment"] = has_many("Comment", lazy="selectin")
    
    # Dynamic for views (analytics only)
    views: List["PageView"] = has_many("PageView", lazy="dynamic")


class Comment(Table):
    text: str
    post_id: int
    author_id: int
    
    # Joined for author (always show commenter)
    author: Author = belongs_to(Author, lazy="joined")


# Query for blog homepage
posts = await BlogPost.select().options(
    joinedload("author"),
    joinedload("category"),
).order_by("-created_at").limit(10)

# Query for single post page
post = await BlogPost.select().options(
    joinedload("author").joinedload("profile"),
    joinedload("category"),
    selectinload("comments").joinedload("author"),
).where(slug=slug).first()

# Query for author page
author = await Author.select().options(
    selectinload("posts").joinedload("category"),
).where(username=username).first()
```

### Example 2: E-commerce Platform

```python
class Customer(Table):
    name: str
    email: str
    
    # Selectin for recent orders
    orders: List["Order"] = has_many("Order", lazy="selectin")
    
    # Dynamic for all-time order history
    order_history: List["Order"] = has_many("Order", lazy="dynamic")
    
    # Raise for sensitive payment methods
    payment_methods: List["PaymentMethod"] = has_many("PaymentMethod", lazy="raise")


class Order(Table):
    status: str
    total: float
    customer_id: int
    
    customer: Customer = belongs_to(Customer, lazy="joined")
    items: List["OrderItem"] = has_many("OrderItem", lazy="selectin")
    shipping: "ShippingInfo" = has_one("ShippingInfo", lazy="joined")


class OrderItem(Table):
    quantity: int
    price: float
    order_id: int
    product_id: int
    
    product: "Product" = belongs_to("Product", lazy="joined")


class Product(Table):
    name: str
    price: float
    category_id: int
    
    category: "Category" = belongs_to("Category", lazy="joined")
    reviews: List["Review"] = has_many("Review", lazy="dynamic")


# Order confirmation page
order = await Order.select().options(
    joinedload("customer"),
    joinedload("shipping"),
    selectinload("items").joinedload("product").joinedload("category"),
).where(id=order_id).first()

# Customer dashboard
customer = await Customer.select().options(
    selectinload("orders")
        .joinedload("shipping")
        .selectinload("items"),
).where(id=customer_id).first()

# Product page with recent reviews
product = await Product.get(product_id)
recent_reviews = await product.reviews.order_by("-created_at").limit(5)
review_count = await product.reviews.count()
avg_rating = await product.reviews.avg("rating")  # If implemented
```

### Example 3: Social Network

```python
class User(Table):
    username: str
    
    # Joined for profile (always show)
    profile: "Profile" = has_one("Profile", lazy="joined")
    
    # Dynamic for posts (could be thousands)
    posts: List["Post"] = has_many("Post", lazy="dynamic")
    
    # Dynamic for followers/following (could be millions)
    followers: List["Follow"] = has_many("Follow", lazy="dynamic")
    following: List["Follow"] = has_many("Follow", lazy="dynamic")
    
    # Raise for DMs (sensitive, explicit load only)
    messages: List["Message"] = has_many("Message", lazy="raise")


class Post(Table):
    content: str
    user_id: int
    
    author: User = belongs_to(User, lazy="joined")
    likes: List["Like"] = has_many("Like", lazy="dynamic")
    comments: List["Comment"] = has_many("Comment", lazy="selectin")


# User profile page
user = await User.select().options(
    joinedload("profile"),
).where(username=username).first()

recent_posts = await user.posts.order_by("-created_at").limit(20)
follower_count = await user.followers.count()
following_count = await user.following.count()

# Feed generation
feed_posts = await Post.select().options(
    joinedload("author").joinedload("profile"),
    selectinload("comments").joinedload("author"),
).where_in(
    user_id=following_user_ids
).order_by("-created_at").limit(50)

# Get like counts efficiently (dynamic)
for post in feed_posts:
    post.like_count = await post.likes.count()  # Single COUNT query each
```

---

## Common Patterns

### Pattern 1: Dashboard Loading

Load multiple relationships for a dashboard:

```python
async def get_dashboard(user_id: int):
    user = await User.select().options(
        joinedload("profile"),
        selectinload("recent_orders").joinedload("items"),
        selectinload("notifications"),
    ).where(id=user_id).first()
    
    # Dynamic queries for counts
    unread_count = await user.notifications.filter(read=False).count()
    order_count = await user.order_history.count()
    
    return {
        "user": user,
        "unread_notifications": unread_count,
        "total_orders": order_count,
    }
```

### Pattern 2: List vs Detail Views

Different loading for list and detail:

```python
# List view - minimal loading
async def list_posts():
    return await Post.select().options(
        joinedload("author"),  # Just author name
        joinedload("category"),
    ).order_by("-created_at").limit(20)

# Detail view - full loading
async def get_post(post_id: int):
    return await Post.select().options(
        joinedload("author").joinedload("profile"),
        joinedload("category"),
        selectinload("comments")
            .joinedload("author")
            .selectinload("replies"),
        selectinload("tags"),
    ).where(id=post_id).first()
```

### Pattern 3: Paginated Collections

Use dynamic for paginated data:

```python
class User(Table):
    orders: List[Order] = has_many(Order, lazy="dynamic")

async def get_user_orders(user_id: int, page: int = 1, per_page: int = 20):
    user = await User.get(user_id)
    
    orders = await (
        user.orders
        .order_by("-created_at")
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    
    total = await user.orders.count()
    
    return {
        "orders": orders,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
    }
```

### Pattern 4: Conditional Loading

Load based on conditions:

```python
async def get_user(user_id: int, include_posts: bool = False):
    options = [joinedload("profile")]
    
    if include_posts:
        options.append(selectinload("posts"))
    
    return await User.select().options(*options).where(id=user_id).first()
```

### Pattern 5: Prefetching for API

Prefetch all needed data for API response:

```python
async def get_user_api(user_id: int):
    user = await User.select().options(
        joinedload("profile"),
        selectinload("posts")
            .joinedload("category")
            .selectinload("tags"),
        selectinload("followers"),
    ).where(id=user_id).first()
    
    # All data is loaded - serialize without N+1
    return {
        "id": user.id,
        "name": user.name,
        "profile": {
            "bio": user.profile.bio,
            "avatar": user.profile.avatar_url,
        } if user.profile else None,
        "posts": [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category.name,
                "tags": [t.name for t in p.tags],
            }
            for p in user.posts
        ],
        "follower_count": len(user.followers),
    }
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: N+1 in Loops

```python
# ❌ BAD: N+1 queries
users = await User.select()
for user in users:
    print(user.posts)  # Query per user!

# ✅ GOOD: Eager load
users = await User.select().options(selectinload("posts"))
for user in users:
    print(user.posts)  # No extra queries
```

### Anti-Pattern 2: Joined for has_many

```python
# ❌ BAD: Row explosion
class User(Table):
    posts: List[Post] = has_many(Post, lazy="joined")
    # 100 users × 100 posts = 10,000 rows returned!

# ✅ GOOD: Use selectin
class User(Table):
    posts: List[Post] = has_many(Post, lazy="selectin")
    # 100 users + 10,000 posts = 2 queries, no duplication
```

### Anti-Pattern 3: Loading Everything

```python
# ❌ BAD: Over-fetching
users = await User.select().options(
    selectinload("posts"),
    selectinload("comments"),
    selectinload("likes"),
    selectinload("followers"),
    selectinload("following"),
    selectinload("notifications"),
    selectinload("audit_logs"),
)  # Loading tons of data you might not need!

# ✅ GOOD: Load only what you need
users = await User.select().options(
    joinedload("profile"),  # For display
)
# Access other data only when needed, or use dynamic
```

### Anti-Pattern 4: Ignoring Large Collections

```python
# ❌ BAD: Could load millions
class User(Table):
    audit_logs: List[AuditLog] = has_many(AuditLog)  # Default select

user = await User.get(1)
logs = user.audit_logs  # Loads ALL audit logs!

# ✅ GOOD: Use dynamic
class User(Table):
    audit_logs: List[AuditLog] = has_many(AuditLog, lazy="dynamic")

user = await User.get(1)
recent = await user.audit_logs.limit(10)  # Only 10 loaded
```

### Anti-Pattern 5: Mixing with_related and options

```python
# ❌ CONFUSING: Mixed approaches
users = await User.select().with_related(
    "posts"
).options(
    selectinload("posts"),  # Redundant!
)

# ✅ CLEAR: Use one approach
users = await User.select().options(
    selectinload("posts"),
)
```

---

## Testing Strategies

### Testing Eager Loading

```python
import pytest

@pytest.mark.asyncio
async def test_user_posts_eager_loaded():
    """Test that posts are eager loaded."""
    user = await User.select().options(
        selectinload("posts")
    ).where(id=1).first()
    
    # Posts should be loaded
    assert user._cached_posts is not None
    assert len(user.posts) > 0

@pytest.mark.asyncio
async def test_no_extra_queries_after_eager_load(query_counter):
    """Test that accessing eager-loaded data doesn't query."""
    user = await User.select().options(
        selectinload("posts")
    ).where(id=1).first()
    
    initial_count = query_counter.count
    
    # Access posts multiple times
    _ = user.posts
    _ = user.posts
    _ = len(user.posts)
    
    # No additional queries should have been made
    assert query_counter.count == initial_count
```

### Testing Raise Strategy

```python
@pytest.mark.asyncio
async def test_raise_strategy_raises():
    """Test that raise strategy raises LazyLoadError."""
    from pynext.db import LazyLoadError
    
    class TestUser(Table):
        posts: List[Post] = has_many(Post, lazy="raise")
    
    user = TestUser()
    
    with pytest.raises(LazyLoadError) as exc_info:
        _ = user.posts
    
    assert "posts" in str(exc_info.value)

@pytest.mark.asyncio
async def test_raise_works_when_loaded():
    """Test that raise strategy works when explicitly loaded."""
    user = await User.select().options(
        selectinload("posts")
    ).where(id=1).first()
    
    # Should not raise - explicitly loaded
    posts = user.posts
    assert isinstance(posts, list)
```

### Testing Dynamic Relationships

```python
@pytest.mark.asyncio
async def test_dynamic_returns_query():
    """Test that dynamic returns DynamicRelationship."""
    from pynext.db import DynamicRelationship
    
    class TestUser(Table):
        logs: List[Log] = has_many(Log, lazy="dynamic")
    
    user = TestUser()
    user.id = 1
    
    result = user.logs
    assert isinstance(result, DynamicRelationship)

@pytest.mark.asyncio
async def test_dynamic_filter():
    """Test dynamic relationship filtering."""
    user = await User.get(1)
    
    errors = await user.audit_logs.filter(level="error")
    
    assert all(log.level == "error" for log in errors)

@pytest.mark.asyncio
async def test_dynamic_count():
    """Test dynamic relationship counting."""
    user = await User.get(1)
    
    count = await user.audit_logs.count()
    
    assert isinstance(count, int)
    assert count >= 0
```

### Testing Nested Loading

```python
@pytest.mark.asyncio
async def test_nested_loading():
    """Test nested relationship loading."""
    users = await User.select().options(
        selectinload("posts").selectinload("comments")
    )
    
    for user in users:
        for post in user.posts:
            # Comments should be loaded
            assert post._cached_comments is not None
```

---

## Debugging Guide

### Identifying N+1 Queries

**Symptom**: Slow page loads, many similar queries in logs.

**Diagnosis**:
```python
# Enable query logging
import logging
logging.getLogger("pynext.db").setLevel(logging.DEBUG)

# Look for patterns like:
# DEBUG: SELECT * FROM posts WHERE user_id = 1
# DEBUG: SELECT * FROM posts WHERE user_id = 2
# DEBUG: SELECT * FROM posts WHERE user_id = 3
# ... (repeated many times)
```

**Fix**:
```python
# Before: N+1
users = await User.select()
for user in users:
    print(user.posts)

# After: 2 queries
users = await User.select().options(selectinload("posts"))
for user in users:
    print(user.posts)
```

### Debugging LazyLoadError

**Symptom**: `LazyLoadError: Accessing 'posts' on User would trigger lazy load`

**Diagnosis**: The relationship has `lazy="raise"` and you're trying to access it without loading.

**Fix**:
```python
# Add eager loading
users = await User.select().options(
    selectinload("posts")  # Add this!
)
```

### Debugging Empty Collections

**Symptom**: Relationship returns empty list but data exists.

**Diagnosis**: Check if relationship is loaded:
```python
user = await User.get(1)
print(f"Cache attr exists: {hasattr(user, '_cached_posts')}")
print(f"Cache value: {getattr(user, '_cached_posts', 'NOT SET')}")
```

**Fix**:
```python
# Ensure eager loading
user = await User.select().options(
    selectinload("posts")
).where(id=1).first()
```

### Debugging Dynamic Relationships

**Symptom**: Expected list but got `DynamicRelationship`.

**Diagnosis**: Relationship has `lazy="dynamic"`.

**Fix**:
```python
# Await the query
logs = await user.audit_logs  # Now it's a list

# Or use query methods
recent = await user.audit_logs.limit(10)
```

### Query Inspection

```python
# Inspect what options are set
query = User.select().options(selectinload("posts"))
print(f"Load options: {query._load_options}")

# Check if relationship has cache
user = await User.get(1)
print(f"Posts cached: {hasattr(user, '_cached_posts')}")
print(f"Posts value: {getattr(user, '_cached_posts', None)}")
```

---

## Migration Guide

### From with_related()

The `with_related()` method still works but `options()` provides more control:

```python
# OLD: with_related (still works)
users = await User.select().with_related("posts", "profile")

# NEW: options (more control)
users = await User.select().options(
    selectinload("posts"),   # Choose strategy
    joinedload("profile"),   # Choose strategy
)

# NEW: Nested loading (not possible with with_related)
users = await User.select().options(
    selectinload("posts").joinedload("author"),
)
```

### From No Loading Strategy

If your models don't specify `lazy`, they default to `lazy="select"`:

```python
# BEFORE: Default lazy loading
class User(Table):
    posts: List[Post] = has_many(Post)  # lazy="select" (default)

# AFTER: Explicit strategy
class User(Table):
    posts: List[Post] = has_many(Post, lazy="selectin")  # Better!
```

### From SQLAlchemy

| SQLAlchemy | PyNext |
|------------|--------|
| `relationship(lazy="select")` | `has_many(Model, lazy="select")` |
| `relationship(lazy="joined")` | `has_many(Model, lazy="joined")` |
| `relationship(lazy="subquery")` | `has_many(Model, lazy="subquery")` |
| `relationship(lazy="selectin")` | `has_many(Model, lazy="selectin")` |
| `relationship(lazy="raise")` | `has_many(Model, lazy="raise")` |
| `relationship(lazy="dynamic")` | `has_many(Model, lazy="dynamic")` |
| `joinedload(User.posts)` | `joinedload("posts")` |
| `selectinload(User.posts)` | `selectinload("posts")` |
| `subqueryload(User.posts)` | `subqueryload("posts")` |
| `raiseload(User.posts)` | `raiseload("posts")` |
| `noload(User.posts)` | `noload("posts")` |

---

## Troubleshooting

### Problem: LazyLoadError When Accessing Relationship

**Error**:
```
LazyLoadError: Accessing 'posts' on User would trigger a lazy load.
```

**Cause**: Relationship has `lazy="raise"` or `raiseload()` applied.

**Solution**:
```python
# Add explicit loading
users = await User.select().options(
    selectinload("posts")
)
```

### Problem: Empty List But Data Exists

**Symptom**: `user.posts` returns `[]` but posts exist in database.

**Cause**: Relationship not loaded and returns default empty value.

**Solution**:
```python
# Ensure eager loading
users = await User.select().options(
    selectinload("posts")
)
```

### Problem: DynamicRelationship Instead of List

**Symptom**: Expected `list` but got `DynamicRelationship`.

**Cause**: Relationship has `lazy="dynamic"`.

**Solution**:
```python
# Await to get list
logs = await user.audit_logs  # Now it's a list

# Or use query methods
recent = await user.audit_logs.limit(10)
```

### Problem: Too Many Queries (N+1)

**Symptom**: Slow page, many queries in logs.

**Cause**: Accessing relationship in loop without eager loading.

**Solution**:
```python
# Add eager loading BEFORE the loop
users = await User.select().options(
    selectinload("posts")
)
for user in users:
    print(user.posts)  # No N+1!
```

### Problem: Too Much Data Loaded

**Symptom**: High memory usage, slow initial query.

**Cause**: Eager loading too much data.

**Solution**:
```python
# Use dynamic for large collections
class User(Table):
    audit_logs: List[AuditLog] = has_many(AuditLog, lazy="dynamic")

# Or be selective about what you load
users = await User.select().options(
    joinedload("profile"),  # Only what you need
)
```

### Problem: Relationship Not Found Error

**Error**: `RelationshipError: Unknown relationship: posts`

**Cause**: Typo in relationship name or relationship not defined.

**Solution**: Check the relationship name matches exactly:
```python
class User(Table):
    posts: List[Post] = has_many(Post)  # Name is "posts"

# Must match exactly
users = await User.select().options(
    selectinload("posts"),  # Correct
    # selectinload("post"),  # Wrong! (singular)
)
```

---

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Your Application                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User.select().options(selectinload("posts"))               │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                      Query                             │  │
│  │  - _load_options: List[LoadOption]                    │  │
│  │  - options(*opts) → Query                             │  │
│  │  - _apply_load_options(instances)                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 RelationshipLoader                     │  │
│  │  - load(instances, options, model)                    │  │
│  │  - _load_selectin(...)                                │  │
│  │  - _load_subquery(...)                                │  │
│  │  - _mark_raise(...)                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               Relationship Descriptors                 │  │
│  │  - HasMany.__get__()  → List or DynamicRelationship   │  │
│  │  - BelongsTo.__get__() → Model or None                │  │
│  │  - HasOne.__get__()   → Model or None                 │  │
│  │                                                        │  │
│  │  Checks:                                               │  │
│  │  - lazy="raise" → raise LazyLoadError                 │  │
│  │  - lazy="dynamic" → return DynamicRelationship        │  │
│  │  - cached → return cached value                       │  │
│  │  - else → return default (None or [])                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Query Creation
   User.select()
   └─> Creates Query with _load_options = []

2. Options Applied
   .options(selectinload("posts"))
   └─> Clones Query, adds LoadOption to _load_options

3. Query Execution
   await query.all()
   └─> Executes main SELECT
   └─> Calls _apply_load_options(instances)

4. Options Processing
   _apply_load_options(instances)
   └─> For each LoadOption:
       ├─ JOINED: Already handled in main query
       ├─ SELECTIN: Execute SELECT WHERE id IN (...)
       ├─ SUBQUERY: Execute SELECT WHERE id IN (subquery)
       ├─ RAISE: Mark instances to raise on access
       └─ SELECT/DYNAMIC: No action (lazy or on-demand)

5. Result Access
   user.posts
   └─> HasMany.__get__() checks:
       ├─ _raise_on_posts? → raise LazyLoadError
       ├─ lazy="dynamic"? → return DynamicRelationship
       ├─ _cached_posts exists? → return cached
       └─> return [] (not loaded)
```

### Key Classes

| Class | File | Purpose |
|-------|------|---------|
| `LoadStrategy` | `loading.py` | Enum of all strategies |
| `LoadOption` | `loading.py` | Configuration for a loading option |
| `LazyLoadError` | `loading.py` | Exception for raise strategy |
| `RelationshipLoader` | `loading.py` | Executes loading strategies |
| `JoinBuilder` | `loading.py` | Builds JOIN SQL clauses |
| `DynamicRelationship` | `dynamic.py` | Query builder for dynamic |
| `joinedload()` | `options.py` | Creates joined LoadOption |
| `selectinload()` | `options.py` | Creates selectin LoadOption |

---

## Complete API Reference

### LoadStrategy Enum

```python
class LoadStrategy(Enum):
    """Loading strategies for relationships."""
    
    SELECT = "select"      # Lazy load on access (default)
    JOINED = "joined"      # LEFT JOIN in same query
    SUBQUERY = "subquery"  # Subquery for IN clause
    SELECTIN = "selectin"  # SELECT WHERE id IN (...)
    RAISE = "raise"        # Raise error on access
    DYNAMIC = "dynamic"    # Return query builder
    
    @classmethod
    def from_string(cls, value: str) -> "LoadStrategy":
        """Convert string to LoadStrategy (case-insensitive)."""
```

### LoadOption Class

```python
@dataclass
class LoadOption:
    """Configuration for a loading option."""
    
    relationship: str                         # Relationship name
    strategy: LoadStrategy                    # Loading strategy
    inner_options: List["LoadOption"] = []    # Nested options
    
    # Chaining methods (return inner LoadOption)
    def joinedload(self, rel: str) -> "LoadOption"
    def selectinload(self, rel: str) -> "LoadOption"
    def subqueryload(self, rel: str) -> "LoadOption"
    def raiseload(self, rel: str) -> "LoadOption"
    def noload(self, rel: str) -> "LoadOption"
    
    # Utilities
    def to_dict(self) -> Dict[str, Any]
    def __repr__(self) -> str
```

### LazyLoadError Exception

```python
class LazyLoadError(Exception):
    """Raised when accessing a relationship with lazy='raise'."""
    
    relationship: str           # Relationship name (e.g., "posts")
    model: Optional[str]        # Model name (e.g., "User")
    
    def __init__(
        self,
        relationship: str,
        model: Optional[str] = None,
        message: Optional[str] = None,
    )
```

### Loading Functions

```python
def joinedload(relationship: str) -> LoadOption:
    """Load relationship with LEFT JOIN."""

def selectinload(relationship: str) -> LoadOption:
    """Load relationship with SELECT WHERE id IN."""

def subqueryload(relationship: str) -> LoadOption:
    """Load relationship with subquery."""

def raiseload(relationship: str) -> LoadOption:
    """Raise error if relationship is accessed."""

def noload(relationship: str) -> LoadOption:
    """Don't load relationship at all."""

def lazyload(relationship: str) -> LoadOption:
    """Use default lazy loading."""

def immediateload(relationship: str) -> LoadOption:
    """Alias for selectinload."""

def eagerload(relationship: str) -> LoadOption:
    """Alias for selectinload."""
```

### DynamicRelationship Class

```python
class DynamicRelationship(Generic[T]):
    """Query builder for dynamic relationships."""
    
    # Query building methods (return Query)
    def all(self) -> Query[T]
    def filter(self, **kwargs) -> Query[T]
    def where(self, **kwargs) -> Query[T]
    def where_in(self, **kwargs) -> Query[T]
    def where_not(self, **kwargs) -> Query[T]
    def order_by(self, *fields: str) -> Query[T]
    def limit(self, n: int) -> Query[T]
    def offset(self, n: int) -> Query[T]
    
    # Async execution methods
    async def count(self) -> int
    async def exists(self) -> bool
    async def first(self) -> Optional[T]
    async def one(self) -> T
    
    # Async iteration
    def __await__(self)          # await user.posts
    async def __aiter__(self)    # async for post in user.posts
    
    # Properties
    def __bool__(self) -> bool   # Always True
    def __repr__(self) -> str
```

### Query.options() Method

```python
class Query(Generic[T]):
    def options(self, *load_options: LoadOption) -> "Query[T]":
        """
        Apply loading options to control how relationships are loaded.
        
        Args:
            *load_options: LoadOption objects from joinedload(), etc.
        
        Returns:
            Query with loading options applied (cloned)
        
        Example:
            users = await User.select().options(
                selectinload("posts"),
                joinedload("profile"),
            )
        """
```

### Relationship Functions (with lazy parameter)

```python
def has_many(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
    lazy: str = "select",  # NEW
) -> HasMany[T]:
    """
    Define a has_many relationship.
    
    Args:
        model: Related model class or string name
        foreign_key: FK field on related model
        backref: Auto-create reverse belongs_to
        back_populates: Link to existing reverse relationship
        lazy: Loading strategy (select|joined|selectin|subquery|raise|dynamic)
    """

def belongs_to(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
    lazy: str = "select",  # NEW
) -> BelongsTo[T]:
    """
    Define a belongs_to relationship.
    
    Args:
        model: Related model class or string name
        foreign_key: FK field on this model
        backref: Auto-create reverse has_many
        back_populates: Link to existing reverse relationship
        lazy: Loading strategy (select|joined|raise)
    """

def has_one(
    model: Union[Type[T], str],
    foreign_key: Optional[str] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
    lazy: str = "select",  # NEW
) -> HasOne[T]:
    """
    Define a has_one relationship.
    
    Args:
        model: Related model class or string name
        foreign_key: FK field on related model
        backref: Auto-create reverse belongs_to
        back_populates: Link to existing reverse relationship
        lazy: Loading strategy (select|joined|selectin|raise)
    """
```

---

## FAQ

### Q: What's the default loading strategy?

A: `lazy="select"` (lazy loading on first access). This is the simplest but can cause N+1 problems in loops.

### Q: Which strategy should I use for belongs_to?

A: Use `lazy="joined"`. It's a single FK lookup and you almost always need the parent object.

### Q: Which strategy should I use for has_many?

A: Use `lazy="selectin"` for most cases. Use `lazy="dynamic"` for huge collections (thousands of items).

### Q: How do I prevent N+1 completely?

A: Use `lazy="raise"` on relationships. This forces you to explicitly load everything you need.

### Q: Can I mix strategies on the same model?

A: Yes! Each relationship can have a different strategy:
```python
class User(Table):
    profile: Profile = has_one(Profile, lazy="joined")
    posts: List[Post] = has_many(Post, lazy="selectin")
    audit: List[Audit] = has_many(Audit, lazy="raise")
    logs: List[Log] = has_many(Log, lazy="dynamic")
```

### Q: Does options() override model-level lazy?

A: Yes! Query-level options take precedence over model-level lazy settings.

### Q: Can I nest loading options?

A: Yes! Chain methods to load nested relationships:
```python
selectinload("posts").joinedload("author").selectinload("profile")
```

### Q: What happens if I don't load a relationship?

A: Depends on the strategy:
- `select`: Triggers a query on access
- `joined/selectin/subquery`: Returns empty (not loaded)
- `raise`: Raises LazyLoadError
- `dynamic`: Returns DynamicRelationship

### Q: Is dynamic compatible with backref?

A: Dynamic relationships don't support automatic backref synchronization. Use for read-only large collections.

### Q: How do I test loading strategies?

A: Check the cache attribute:
```python
user = await User.select().options(selectinload("posts")).first()
assert hasattr(user, "_cached_posts")
assert user._cached_posts is not None
```

---

## Summary

Loading strategies give you complete control over relationship loading:

| Goal | Strategy | How |
|------|----------|-----|
| Load single related object | `joined` | `lazy="joined"` or `joinedload()` |
| Load collection efficiently | `selectin` | `lazy="selectin"` or `selectinload()` |
| Handle huge collections | `dynamic` | `lazy="dynamic"` |
| Prevent N+1 errors | `raise` | `lazy="raise"` or `raiseload()` |
| Complex parent queries | `subquery` | `lazy="subquery"` or `subqueryload()` |

**Key Principles**:
1. Set sensible defaults at model level with `lazy=`
2. Override at query level with `.options()`
3. Use `raise` in production to catch N+1
4. Use `dynamic` for large collections
5. Always eager load in loops

**The API is designed to be**:
- Simple: One parameter controls everything
- Explicit: You know when queries happen
- Flexible: Override at any level
- Safe: Easy to prevent N+1
- AI-Friendly: Clear names, predictable behavior
