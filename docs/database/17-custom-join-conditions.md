# Custom Join Conditions & Filtered Relationships

> Build-in filters for relationships - dramatically simpler than SQLAlchemy's string-based expressions.

---

## Table of Contents

1. [What Are Filtered Relationships and Why Use Them?](#what-are-filtered-relationships-and-why-use-them)
2. [The Problem: "I Only Want SOME Related Records"](#the-problem-i-only-want-some-related-records)
3. [Quick Start](#quick-start)
4. [Understanding When to Use Filtered Relationships](#understanding-when-to-use-filtered-relationships)
5. [Condition Functions](#condition-functions)
6. [Tuple Syntax](#tuple-syntax)
7. [Date/Time Helpers](#datetime-helpers)
8. [Real-World Scenarios](#real-world-scenarios)
9. [Decision Guide: Filter vs Dynamic vs Query](#decision-guide-filter-vs-dynamic-vs-query)
10. [PyNext vs SQLAlchemy](#pynext-vs-sqlalchemy)
11. [All Relationship Types](#all-relationship-types)
12. [Combining with Other Features](#combining-with-other-features)
13. [Anti-Patterns and What NOT to Do](#anti-patterns-and-what-not-to-do)
14. [Performance Considerations](#performance-considerations)
15. [API Reference](#api-reference)

---

## What Are Filtered Relationships and Why Use Them?

### The Core Concept

A **filtered relationship** is a relationship that automatically includes a WHERE clause when loaded. Instead of loading ALL related records, it only loads those matching specific conditions.

```python
class User(Table):
    # Unfiltered: loads ALL posts
    posts: List[Post] = has_many(Post)
    
    # Filtered: loads ONLY active, non-deleted posts
    active_posts: List[Post] = has_many(Post, filter=[
        eq("is_active", True),
        is_null("deleted_at")
    ])
```

**What happens in the database:**

```sql
-- Unfiltered relationship
SELECT * FROM posts WHERE author_id = 5;
-- Returns ALL 150 posts

-- Filtered relationship  
SELECT * FROM posts 
WHERE author_id = 5 
  AND is_active = TRUE 
  AND deleted_at IS NULL;
-- Returns only the 42 active, non-deleted posts
```

### Why This Matters

Without filtered relationships, you'd filter everywhere you load:

```python
# WITHOUT filtered relationships - repetitive and error-prone
def get_user_feed(user_id):
    posts = user.posts  # All 150 posts
    active = [p for p in posts if p.is_active and p.deleted_at is None]  # Filter in Python
    return active

def show_profile(user_id):
    posts = user.posts  # All 150 posts again
    active = [p for p in posts if p.is_active and p.deleted_at is None]  # Same filter
    return active

def get_post_count(user_id):
    posts = user.posts  # All 150 posts
    active = [p for p in posts if p.is_active and p.deleted_at is None]  # Same filter
    return len(active)
```

With filtered relationships, the filter is defined ONCE:

```python
# WITH filtered relationships - clean and consistent
class User(Table):
    active_posts: List[Post] = has_many(Post, filter=[
        eq("is_active", True),
        is_null("deleted_at")
    ])

def get_user_feed(user_id):
    return user.active_posts  # Always filtered correctly

def show_profile(user_id):
    return user.active_posts  # Same filter automatically

def get_post_count(user_id):
    return len(user.active_posts)  # Same filter
```

### Benefits

| Benefit | Description |
|---------|-------------|
| **DRY** | Define filter once, use everywhere |
| **Performance** | Filter at SQL level, not in Python |
| **Consistency** | Same filter applied everywhere |
| **Readability** | Relationship name describes what you get |
| **Less Bugs** | Can't forget to filter |

---

## The Problem: "I Only Want SOME Related Records"

### Real Questions You'll Face

When building any application, you'll encounter these patterns:

**Scenario 1: Content Visibility**
- User has posts → But only show PUBLISHED ones
- User has comments → But only show APPROVED ones
- User has photos → But only show PUBLIC ones

**Scenario 2: Soft Deletes**
- User has orders → But exclude DELETED ones
- Product has reviews → But exclude HIDDEN ones
- Thread has messages → But exclude REMOVED ones

**Scenario 3: Time-Based Filtering**
- User has notifications → But only from last 30 days
- User has sessions → But only ACTIVE ones
- Product has offers → But only CURRENT ones (not expired)

**Scenario 4: Status Filtering**
- User has orders → But only PENDING ones for dashboard
- User has orders → But only COMPLETED ones for history
- Project has tasks → But only OPEN ones for kanban

### The Common (Wrong) Solutions

**Wrong Solution 1: Filter in Python**

```python
# ❌ BAD: Loads ALL 1000 orders, then filters to 5
def get_pending_orders(user):
    orders = user.orders  # 1000 orders loaded from DB
    return [o for o in orders if o.status == "pending"]  # Only 5 are pending
```

**Wrong Solution 2: Multiple Queries**

```python
# ❌ BAD: Separate query, not using relationship benefits
def get_pending_orders(user):
    return await Order.select().where(user_id=user.id, status="pending")
```

**Wrong Solution 3: Check Everywhere**

```python
# ❌ BAD: Scattered filter logic
# In view 1:
active = [p for p in user.posts if p.is_active and not p.deleted_at]
# In view 2:
active = [p for p in user.posts if p.is_active and p.deleted_at is None]  # Slightly different!
# In view 3:
active = [p for p in user.posts if p.status == "active"]  # Wrong check!
```

### The Right Solution: Filtered Relationships

```python
class User(Table):
    # Define once, use everywhere
    pending_orders: List[Order] = has_many(Order, filter=[
        eq("status", "pending")
    ])
    
    active_posts: List[Post] = has_many(Post, filter=[
        eq("is_active", True),
        is_null("deleted_at")
    ])
    
    recent_notifications: List[Notification] = has_many(Notification, filter=[
        gte("created_at", days_ago(30))
    ])
```

---

## Quick Start

### Step 1: Import Condition Functions

```python
from pynext.db import Table, has_many, eq, gte, is_null
from typing import List
```

### Step 2: Define Filtered Relationships

```python
class User(Table):
    name: str
    
    # Only published posts
    published_posts: List[Post] = has_many(Post, filter=[
        eq("status", "published")
    ])
    
    # Only recent activity (last 7 days)
    recent_activity: List[Activity] = has_many(Activity, filter=[
        gte("created_at", days_ago(7))
    ])
```

### Step 3: Use Like Normal Relationships

```python
user = await User.get(1)

# Automatically filtered!
for post in user.published_posts:
    print(post.title)  # Only published posts

for activity in user.recent_activity:
    print(activity.action)  # Only last 7 days
```

---

## Understanding When to Use Filtered Relationships

### Use Filtered Relationships When...

#### 1. The Filter is Part of Your Business Logic

If you **always** want a specific subset of records, make it a filtered relationship:

```python
# ✅ GOOD: You ALWAYS want active posts on a profile
class User(Table):
    active_posts: List[Post] = has_many(Post, filter=[eq("is_active", True)])

# Use case: Profile page shows only active posts
# Use case: Post count shows only active posts  
# Use case: API returns only active posts
```

#### 2. You Want Multiple "Views" of the Same Data

Define multiple relationships with different filters:

```python
# ✅ GOOD: Different views for different purposes
class User(Table):
    # Dashboard shows pending
    pending_orders: List[Order] = has_many(Order, filter=[
        eq("status", "pending")
    ])
    
    # History shows completed
    completed_orders: List[Order] = has_many(Order, filter=[
        eq("status", "completed")
    ])
    
    # Admin sees all
    all_orders: List[Order] = has_many(Order)
```

#### 3. Soft Deletes

Always filter out deleted records:

```python
# ✅ GOOD: Soft delete pattern
class User(Table):
    # Only non-deleted
    posts: List[Post] = has_many(Post, filter=[is_null("deleted_at")])
    
    # Also non-deleted
    comments: List[Comment] = has_many(Comment, filter=[is_null("deleted_at")])
```

#### 4. Time-Based Windows

Common for notifications, activity, etc.:

```python
# ✅ GOOD: Time-based views
class User(Table):
    recent_notifications: List[Notification] = has_many(Notification, filter=[
        gte("created_at", days_ago(30))
    ])
    
    this_week_activity: List[Activity] = has_many(Activity, filter=[
        gte("created_at", start_of_week())
    ])
```

### DON'T Use Filtered Relationships When...

#### 1. Filter Varies at Runtime

If the filter depends on user input or context, use query-level filtering:

```python
# ❌ BAD: Category changes per request
class User(Table):
    # Can't put runtime value in relationship definition!
    posts_in_category: List[Post] = has_many(Post, filter=[
        eq("category_id", ???)  # Where does this come from?
    ])

# ✅ GOOD: Query-level filtering for runtime values
posts = await user.posts.where(category_id=request.category_id)
```

#### 2. Complex Conditional Logic

For complex OR conditions or nested logic:

```python
# ❌ BAD: Complex conditions
class User(Table):
    weird_posts: List[Post] = has_many(Post, filter=[
        # This is getting messy...
    ])

# ✅ GOOD: Use dynamic relationship or query
all_posts = await user.posts  # Use dynamic relationship
filtered = await all_posts.filter(complex_logic)
```

#### 3. You Need ALL Records Sometimes

Don't replace the unfiltered relationship:

```python
# ❌ BAD: Lost access to all posts
class User(Table):
    posts: List[Post] = has_many(Post, filter=[eq("published", True)])
    # Now you can never get drafts!

# ✅ GOOD: Keep both
class User(Table):
    all_posts: List[Post] = has_many(Post)  # Access to everything
    published_posts: List[Post] = has_many(Post, filter=[eq("published", True)])
```

---

## Condition Functions

### Available Conditions

| Function | SQL Equivalent | Example |
|----------|----------------|---------|
| `eq(field, value)` | `field = value` | `eq("status", "active")` |
| `ne(field, value)` | `field != value` | `ne("status", "deleted")` |
| `gt(field, value)` | `field > value` | `gt("age", 18)` |
| `gte(field, value)` | `field >= value` | `gte("views", 100)` |
| `lt(field, value)` | `field < value` | `lt("price", 50)` |
| `lte(field, value)` | `field <= value` | `lte("quantity", 10)` |
| `like(field, pattern)` | `LIKE pattern` | `like("name", "%john%")` |
| `ilike(field, pattern)` | `ILIKE pattern` | `ilike("email", "%@GMAIL%")` |
| `is_in(field, values)` | `IN (...)` | `is_in("status", ["a", "b"])` |
| `not_in(field, values)` | `NOT IN (...)` | `not_in("type", ["x", "y"])` |
| `is_null(field)` | `IS NULL` | `is_null("deleted_at")` |
| `is_null(field, False)` | `IS NOT NULL` | `is_null("email", False)` |

### Full Aliases for Readability

```python
from pynext.db import (
    equals,                # Same as eq
    not_equals,           # Same as ne
    greater_than,         # Same as gt
    greater_than_or_equal, # Same as gte
    less_than,            # Same as lt
    less_than_or_equal,   # Same as lte
    contains,             # Same as like
)
```

### Multiple Conditions (AND)

All conditions in a filter list are combined with AND:

```python
class User(Table):
    # Must satisfy ALL conditions
    premium_active_posts: List[Post] = has_many(Post, filter=[
        eq("is_active", True),           # AND
        gte("views", 1000),              # AND
        eq("is_premium", True)
    ])
```

**Generated SQL:**
```sql
SELECT * FROM posts 
WHERE author_id = ? 
  AND is_active = TRUE 
  AND views >= 1000 
  AND is_premium = TRUE;
```

---

## Tuple Syntax

For those who prefer SQL-like syntax:

```python
class User(Table):
    # Tuple syntax: (field, operator, value)
    active_posts: List[Post] = has_many(Post, filter=[
        ("is_active", "=", True),
        ("views", ">=", 100),
        ("status", "IN", ["published", "featured"])
    ])
```

### Supported Operators

| Operator | Description |
|----------|-------------|
| `=` | Equal |
| `!=` or `<>` | Not equal |
| `>` | Greater than |
| `>=` | Greater than or equal |
| `<` | Less than |
| `<=` | Less than or equal |
| `LIKE` | Pattern match (case-sensitive) |
| `ILIKE` | Pattern match (case-insensitive) |
| `NOT LIKE` | Negative pattern |
| `IN` | In list |
| `NOT IN` | Not in list |
| `IS NULL` | Is null |
| `IS NOT NULL` | Is not null |

### Mix Both Syntaxes

```python
class User(Table):
    posts: List[Post] = has_many(Post, filter=[
        eq("is_active", True),           # Function style
        ("views", ">=", 100),             # Tuple style
        is_null("deleted_at"),            # Function style
        ("status", "IN", ["a", "b"])      # Tuple style
    ])
```

---

## Date/Time Helpers

PyNext provides convenient helpers for date-based filters:

### Past Time Helpers

```python
from pynext.db import (
    days_ago,      # N days ago
    hours_ago,     # N hours ago
    minutes_ago,   # N minutes ago
    seconds_ago,   # N seconds ago
    weeks_ago,     # N weeks ago
    months_ago,    # N months ago (~30 days each)
    years_ago,     # N years ago (~365 days each)
)

class User(Table):
    # Posts from last 24 hours
    todays_posts: List[Post] = has_many(Post, filter=[
        gte("created_at", hours_ago(24))
    ])
    
    # Posts from last 30 days
    monthly_posts: List[Post] = has_many(Post, filter=[
        gte("created_at", days_ago(30))
    ])
    
    # Posts from last year
    yearly_posts: List[Post] = has_many(Post, filter=[
        gte("created_at", years_ago(1))
    ])
```

### Future Time Helpers

```python
from pynext.db import (
    days_from_now,
    hours_from_now,
    minutes_from_now,
)

class Product(Table):
    # Sales expiring within 7 days
    expiring_sales: List[Sale] = has_many(Sale, filter=[
        lte("expires_at", days_from_now(7)),
        gte("expires_at", now())
    ])
```

### Boundary Helpers

```python
from pynext.db import (
    today,         # Today's date
    yesterday,     # Yesterday's date  
    tomorrow,      # Tomorrow's date
    start_of_today,    # Midnight today
    end_of_today,      # 23:59:59 today
    start_of_week,     # Monday 00:00
    start_of_month,    # 1st of month 00:00
    start_of_year,     # Jan 1 00:00
    now,           # Current datetime
    utc_now,       # Current UTC datetime
)

class User(Table):
    # Posts from this week
    weekly_posts: List[Post] = has_many(Post, filter=[
        gte("created_at", start_of_week())
    ])
    
    # Posts from this month
    monthly_posts: List[Post] = has_many(Post, filter=[
        gte("created_at", start_of_month())
    ])
    
    # Posts from today
    todays_posts: List[Post] = has_many(Post, filter=[
        gte("created_at", start_of_today())
    ])
```

---

## Real-World Scenarios

### Scenario 1: Content Management System

```python
class User(Table):
    name: str
    role: str
    
    # Public profile shows published only
    published_articles: List[Article] = has_many(Article, filter=[
        eq("status", "published")
    ])
    
    # Dashboard shows drafts
    draft_articles: List[Article] = has_many(Article, filter=[
        eq("status", "draft")
    ])
    
    # Scheduled posts for calendar
    scheduled_articles: List[Article] = has_many(Article, filter=[
        eq("status", "scheduled"),
        gte("publish_at", now())
    ])
    
    # All articles for admin
    all_articles: List[Article] = has_many(Article)
    
    # Non-deleted comments (soft delete)
    visible_comments: List[Comment] = has_many(Comment, filter=[
        is_null("deleted_at")
    ])

class Article(Table):
    author_id: int
    title: str
    status: str  # draft, published, scheduled, archived
    
    # Only approved comments
    approved_comments: List[Comment] = has_many(Comment, filter=[
        eq("approved", True),
        is_null("deleted_at")
    ])
```

**Why these filters?**
- `published_articles`: Public-facing, only show what readers should see
- `draft_articles`: Author's dashboard, shows work in progress
- `scheduled_articles`: Calendar view, shows future publications
- `approved_comments`: Spam filtering, only show moderated content

---

### Scenario 2: E-Commerce Platform

```python
class Customer(Table):
    name: str
    email: str
    
    # Dashboard shows active orders
    pending_orders: List[Order] = has_many(Order, filter=[
        is_in("status", ["pending", "processing", "shipped"])
    ])
    
    # Order history shows completed
    completed_orders: List[Order] = has_many(Order, filter=[
        eq("status", "completed")
    ])
    
    # High-value orders for VIP detection
    premium_orders: List[Order] = has_many(Order, filter=[
        gte("total", 500)
    ])
    
    # Recent purchases for recommendations
    recent_orders: List[Order] = has_many(Order, filter=[
        gte("created_at", days_ago(90))
    ])

class Product(Table):
    name: str
    price: float
    
    # Only in-stock variants on product page
    available_variants: List[Variant] = has_many(Variant, filter=[
        gt("stock_quantity", 0),
        eq("is_active", True)
    ])
    
    # Only approved reviews
    approved_reviews: List[Review] = has_many(Review, filter=[
        eq("status", "approved"),
        is_null("deleted_at")
    ])
    
    # Recent reviews for "latest" section
    recent_reviews: List[Review] = has_many(Review, filter=[
        eq("status", "approved"),
        gte("created_at", days_ago(30))
    ])
    
    # Current promotions
    active_promotions: List[Promotion] = has_many(Promotion, filter=[
        lte("start_date", now()),
        gte("end_date", now())
    ])
```

**Why these filters?**
- `available_variants`: Don't show out-of-stock options
- `approved_reviews`: Quality control, no spam
- `active_promotions`: Only currently valid deals

---

### Scenario 3: Social Media Platform

```python
class User(Table):
    username: str
    
    # Only active followers (not banned/deleted)
    active_followers: List["User"] = many_to_many(
        "User",
        through="Follow",
        filter=[eq("is_active", True)]
    )
    
    # Verified accounts they follow
    verified_following: List["User"] = many_to_many(
        "User",
        through="Follow", 
        filter=[eq("is_verified", True)]
    )
    
    # Public posts only
    public_posts: List[Post] = has_many(Post, filter=[
        eq("visibility", "public"),
        is_null("deleted_at")
    ])
    
    # Recent activity (last 7 days)
    recent_activity: List[Activity] = has_many(Activity, filter=[
        gte("created_at", days_ago(7))
    ])
    
    # Unread notifications
    unread_notifications: List[Notification] = has_many(Notification, filter=[
        eq("read", False)
    ])
    
    # Recent notifications (last 30 days)
    recent_notifications: List[Notification] = has_many(Notification, filter=[
        gte("created_at", days_ago(30))
    ])
```

**Why these filters?**
- `active_followers`: Exclude banned/deleted accounts
- `public_posts`: Privacy settings enforced at relationship level
- `unread_notifications`: Notification badge count

---

### Scenario 4: Project Management

```python
class Project(Table):
    name: str
    
    # Kanban board: open tasks only
    open_tasks: List[Task] = has_many(Task, filter=[
        is_in("status", ["todo", "in_progress", "review"])
    ])
    
    # Overdue tasks for alerts
    overdue_tasks: List[Task] = has_many(Task, filter=[
        lt("due_date", today()),
        ne("status", "completed")
    ])
    
    # Tasks due this week
    this_week_tasks: List[Task] = has_many(Task, filter=[
        gte("due_date", start_of_week()),
        lte("due_date", days_from_now(7))
    ])
    
    # Active milestones
    active_milestones: List[Milestone] = has_many(Milestone, filter=[
        eq("status", "active"),
        gte("due_date", today())
    ])

class Team(Table):
    name: str
    
    # Only active members
    active_members: List[User] = many_to_many(User, filter=[
        eq("is_active", True)
    ])
```

---

## Decision Guide: Filter vs Dynamic vs Query

### Quick Decision Tree

```
Is the filter always the same?
├── YES: Is it a common use case?
│   ├── YES → Filtered relationship
│   └── NO → Consider if it's worth a relationship
│
└── NO: Does the filter depend on runtime values?
    ├── YES → Query-level filtering
    └── NO: Is the logic complex (OR, nested)?
        ├── YES → Dynamic relationship + query
        └── NO → Filtered relationship might still work
```

### Comparison

| Approach | When to Use | Example |
|----------|-------------|---------|
| **Filtered Relationship** | Static, always-needed filters | `active_posts`, `pending_orders` |
| **Dynamic Relationship** | Large collections, complex queries | `user.posts.where(status=x)` |
| **Query-Level** | Runtime filters, user input | `Post.where(author_id=user.id, category=request.cat)` |

### Examples

**Use Filtered Relationship:**
```python
# Always want published posts
class User(Table):
    published_posts: List[Post] = has_many(Post, filter=[
        eq("status", "published")
    ])

# Usage: Simple access
posts = user.published_posts
```

**Use Dynamic Relationship:**
```python
# Need to query/filter further
class User(Table):
    posts: DynamicRelationship[Post] = has_many(Post, lazy="dynamic")

# Usage: Complex queries
posts = await user.posts.where(category=cat).order_by("views").limit(10)
```

**Use Query-Level:**
```python
# Filter depends on request context
posts = await Post.select().where(
    author_id=user.id,
    category_id=request.query.category,  # Runtime value
    created_at__gte=request.query.since   # Runtime value
)
```

---

## PyNext vs SQLAlchemy

### The SQLAlchemy Problem

```python
# SQLAlchemy - String-based, cryptic, error-prone
class User(Base):
    __tablename__ = 'users'
    
    active_posts = relationship(
        "Post",
        primaryjoin="and_(User.id == Post.author_id, Post.is_active == true())",
        foreign_keys="[Post.author_id]"
    )
    
    recent_posts = relationship(
        "Post",
        primaryjoin="and_(User.id == Post.author_id, "
                    "Post.created_at >= func.now() - timedelta(days=30))",
        foreign_keys="[Post.author_id]",
        viewonly=True
    )
```

**Problems:**
- `primaryjoin="and_(User.id == Post.author_id, ..."` - String inside string!
- No IDE autocomplete
- Typos (`is_active` vs `isActive`) cause runtime errors
- `foreign_keys="[Post.author_id]"` - More strings!
- `viewonly=True` - Easy to forget
- Hard for AI/LLMs to understand and generate

### The PyNext Solution

```python
from pynext.db import Table, has_many, eq, gte, days_ago

class User(Table):
    # Clear and simple
    active_posts: List[Post] = has_many(Post, filter=[
        eq("is_active", True)
    ])
    
    # Date filtering with helper
    recent_posts: List[Post] = has_many(Post, filter=[
        gte("created_at", days_ago(30))
    ])
```

### Comparison Table

| Feature | SQLAlchemy | PyNext |
|---------|------------|--------|
| Syntax | `primaryjoin="and_(...)"` strings | `filter=[eq(...)]` objects |
| IDE Support | ❌ None (strings) | ✅ Full autocomplete |
| Type Hints | ❌ None | ✅ Complete |
| Typo Detection | ❌ Runtime error | ✅ IDE warning |
| Date Helpers | ❌ Write SQL functions | ✅ `days_ago()`, `start_of_week()` |
| AI/LLM Friendly | ❌ Hard to parse | ✅ Easy to understand |
| Error Messages | ❌ Cryptic SQL errors | ✅ Clear Python errors |

---

## All Relationship Types

Filters work with ALL relationship types:

### has_many

```python
class User(Table):
    active_posts: List[Post] = has_many(Post, filter=[
        eq("is_active", True)
    ])
```

### has_one

```python
class User(Table):
    active_profile: Profile = has_one(Profile, filter=[
        eq("is_active", True)
    ])
```

### belongs_to

```python
class Post(Table):
    author_id: int
    
    # Only load if author is active
    active_author: User = belongs_to(User, filter=[
        eq("is_active", True)
    ])
```

### many_to_many

```python
class Student(Table):
    # Only active courses
    active_courses: List[Course] = many_to_many(Course, filter=[
        eq("is_active", True)
    ])
```

---

## Combining with Other Features

### With Loading Strategies

```python
class User(Table):
    # Selectin loading with filter
    active_posts: List[Post] = has_many(
        Post,
        lazy="selectin",
        filter=[eq("is_active", True)]
    )
    
    # Raise loading with filter (N+1 prevention)
    protected_posts: List[Post] = has_many(
        Post,
        lazy="raise",
        filter=[eq("is_active", True)]
    )
```

### With Cascades

```python
class User(Table):
    # Filter + cascade
    active_posts: List[Post] = has_many(
        Post,
        on_delete="cascade",
        filter=[eq("is_active", True)]
    )
```

### With Backref

```python
class User(Table):
    # Filter + backref
    published_posts: List[Post] = has_many(
        Post,
        backref="author",
        filter=[eq("status", "published")]
    )
```

---

## Anti-Patterns and What NOT to Do

### Anti-Pattern 1: Replacing Unfiltered with Filtered

```python
# ❌ BAD: Lost access to all posts
class User(Table):
    posts: List[Post] = has_many(Post, filter=[eq("published", True)])
    # Now you can never get drafts!

# ✅ GOOD: Keep both
class User(Table):
    all_posts: List[Post] = has_many(Post)
    published_posts: List[Post] = has_many(Post, filter=[eq("published", True)])
```

### Anti-Pattern 2: Runtime Values in Filters

```python
# ❌ BAD: Where does category_id come from?
class User(Table):
    category_posts: List[Post] = has_many(Post, filter=[
        eq("category_id", some_variable)  # Not available at class definition!
    ])

# ✅ GOOD: Query-level for runtime values
posts = await Post.where(user_id=user.id, category_id=request.category)
```

### Anti-Pattern 3: Too Many Similar Relationships

```python
# ❌ BAD: Explosion of relationships
class User(Table):
    posts_from_jan: List[Post] = has_many(Post, filter=[...])
    posts_from_feb: List[Post] = has_many(Post, filter=[...])
    posts_from_mar: List[Post] = has_many(Post, filter=[...])
    # ... 12 more ...

# ✅ GOOD: Dynamic relationship with query
class User(Table):
    posts: DynamicRelationship[Post] = has_many(Post, lazy="dynamic")

# Usage
jan_posts = await user.posts.where(
    created_at__gte=datetime(2024, 1, 1),
    created_at__lt=datetime(2024, 2, 1)
)
```

### Anti-Pattern 4: Complex Logic in Filters

```python
# ❌ BAD: Logic too complex
class User(Table):
    weird_posts: List[Post] = has_many(Post, filter=[
        eq("is_active", True),
        eq("is_featured", True),
        gte("views", 100),
        is_null("deleted_at"),
        is_in("category", ["tech", "science"]),
        # ... more conditions ...
    ])

# ✅ GOOD: Use dynamic relationship for complex logic
class User(Table):
    posts: DynamicRelationship[Post] = has_many(Post, lazy="dynamic")

# Complex logic in method
async def get_featured_tech_posts(user):
    return await user.posts.where(
        is_active=True,
        is_featured=True
    ).where_gte(views=100).where_in(
        category=["tech", "science"]
    ).where_null("deleted_at")
```

---

## Performance Considerations

### SQL is Better Than Python

```python
# ✅ GOOD: Filter at SQL level
active_posts: List[Post] = has_many(Post, filter=[eq("is_active", True)])
# SQL: SELECT * FROM posts WHERE author_id = 5 AND is_active = TRUE
# Returns 42 rows

# ❌ BAD: Filter in Python
all_posts = user.posts  # SQL returns all 150 rows
active = [p for p in all_posts if p.is_active]  # Filter 150 in Python
```

### Use Selectin for Batch Loading

```python
class User(Table):
    active_posts: List[Post] = has_many(
        Post,
        lazy="selectin",  # Batch load for multiple users
        filter=[eq("is_active", True)]
    )

# Loading 10 users
users = await User.select().limit(10)
# 1 query for users
# 1 query for ALL active posts (batch)
# NOT 10 separate queries
```

### Index Filtered Columns

```sql
-- Create indexes for filtered columns
CREATE INDEX idx_posts_is_active ON posts(is_active);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_created_at ON posts(created_at);

-- Composite index for common filter combinations
CREATE INDEX idx_posts_active_created ON posts(is_active, created_at);
```

---

## API Reference

### Condition Functions

```python
eq(field, value)         # field = value
ne(field, value)         # field != value
gt(field, value)         # field > value
gte(field, value)        # field >= value
lt(field, value)         # field < value
lte(field, value)        # field <= value
like(field, pattern)     # field LIKE pattern
ilike(field, pattern)    # field ILIKE pattern (case-insensitive)
not_like(field, pattern) # field NOT LIKE pattern
is_in(field, values)     # field IN (values)
not_in(field, values)    # field NOT IN (values)
is_null(field)           # field IS NULL
is_null(field, False)    # field IS NOT NULL
```

### Date/Time Helpers

```python
# Past
days_ago(n), hours_ago(n), minutes_ago(n), seconds_ago(n)
weeks_ago(n), months_ago(n), years_ago(n)

# Future
days_from_now(n), hours_from_now(n), minutes_from_now(n)

# Boundaries
today(), yesterday(), tomorrow()
start_of_today(), end_of_today()
start_of_week(), start_of_month(), start_of_year()
now(), utc_now()
```

### Filter Parameter

```python
# Accepts list of:
filter=[
    eq("field", value),           # Condition function
    ("field", "=", value),        # 3-tuple
    gte("date", days_ago(30)),    # With date helper
    ("status", "IN", ["a", "b"]), # Tuple with list
]
```

---

## Summary

| Question | Answer |
|----------|--------|
| "Always want this subset?" | Use filtered relationship |
| "Filter varies by request?" | Use query-level filtering |
| "Need complex queries?" | Use dynamic relationship |
| "Multiple views of same data?" | Define multiple filtered relationships |

**Key Principles:**
1. **Filter at SQL level** - not in Python
2. **Define once, use everywhere** - DRY principle
3. **Name relationships by what they return** - `active_posts` not `posts`
4. **Keep both filtered and unfiltered** - don't lose access to all data
5. **Use date helpers** - `days_ago(30)` is clearer than manual datetime math
