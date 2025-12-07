# Relationship Ordering

## Quick Reference

```python
from pynext.db import Table, has_many, many_to_many

class User(Table):
    # Latest posts first
    posts: List[Post] = has_many(Post, order_by="created_at desc")
    
    # Pinned first, then by date
    comments: List[Comment] = has_many(
        Comment,
        order_by=["pinned desc", "created_at desc"]
    )
    
    # Tags alphabetically
    tags: List[Tag] = many_to_many(Tag, order_by="name")
    
    # Tasks with nulls handling
    tasks: List[Task] = has_many(
        Task,
        order_by=["priority desc", "due_date nulls last"]
    )
```

---

## Table of Contents

1. [Why - The Problem We're Solving](#why---the-problem-we're-solving)
2. [What - Relationship Ordering Explained](#what---relationship-ordering-explained)
3. [When - Use Cases and Scenarios](#when---use-cases-and-scenarios)
4. [Who - Target Users](#who---target-users)
5. [Where - Integration Points](#where---integration-points)
6. [How - Complete Usage Guide](#how---complete-usage-guide)
7. [API Reference](#api-reference)
8. [SQLAlchemy vs Django vs PyNext](#sqlalchemy-vs-django-vs-pynext)
9. [Real-World Examples](#real-world-examples)
10. [Performance Considerations](#performance-considerations)
11. [Troubleshooting](#troubleshooting)

---

## Why - The Problem We're Solving

### The Universal Problem

Every web application needs ordered data. Blog posts show newest first. Comments show most upvoted first. Tasks show highest priority first. Products show featured items first.

**Without relationship ordering**, you have two bad options:

1. **Sort in Python after loading** - Wastes memory, slow for large datasets
2. **Write ORDER BY in every query** - Repetitive, error-prone, scattered logic

### SQLAlchemy's Approach - Verbose and Confusing

```python
from sqlalchemy import desc
from sqlalchemy.orm import relationship

class User(Base):
    # Method 1: String with full path (verbose)
    posts = relationship("Post", order_by="Post.created_at.desc()")
    
    # Method 2: Column object (requires import)
    posts = relationship("Post", order_by=desc(Post.created_at))
    
    # Method 3: Multiple columns (even worse)
    comments = relationship("Comment", 
        order_by=[desc(Comment.pinned), desc(Comment.created_at)])
```

**Problems with SQLAlchemy:**
- Need to import `desc`, `asc` functions
- Must reference full model path in strings ("Post.created_at")
- Inconsistent between string and object syntax
- Multiple columns require list of function calls
- No NULLS FIRST/LAST without additional wrapping

### Django's Approach - Model-Level Only or Verbose

```python
class Post(models.Model):
    class Meta:
        ordering = ['-created_at']  # Model-level only, affects ALL queries

# Relationship-specific ordering requires Prefetch:
User.objects.prefetch_related(
    Prefetch('posts', queryset=Post.objects.order_by('-created_at'))
)
```

**Problems with Django:**
- Model-level `ordering` affects ALL queries (not just relationships)
- Relationship-level ordering requires `Prefetch` object
- Different syntax for model vs relationship ordering
- Can't define ordering on the relationship itself

### PyNext's Solution - Dead Simple String Syntax

```python
from pynext.db import Table, has_many

class User(Table):
    # Just write it like SQL!
    posts: List[Post] = has_many(Post, order_by="created_at desc")
    
    # Multiple columns? Just a list of strings
    comments: List[Comment] = has_many(
        Comment,
        order_by=["pinned desc", "created_at desc"]
    )
```

**Why PyNext is better:**
- **Natural SQL syntax**: `"created_at desc"` - anyone who knows SQL gets it
- **No imports needed**: Everything is a string
- **Relationship-level**: Ordering defined where it makes sense
- **NULLS support built-in**: `"due_date nulls last"` just works
- **Applied at SQL level**: Efficient ORDER BY, not Python sorting

---

## What - Relationship Ordering Explained

### Core Concept

Relationship ordering defines the **default sort order** for related items when loaded through a relationship. It's applied at the SQL level, meaning the database does the sorting efficiently.

### The order_by Parameter

Both `has_many()` and `many_to_many()` accept an `order_by` parameter:

```python
order_by: Optional[Union[str, List[str]]] = None
```

### Syntax Options

#### 1. Single Column, Default Direction (Ascending)

```python
# Alphabetical by name
posts: List[Post] = has_many(Post, order_by="name")
# Generates: ORDER BY name ASC
```

#### 2. Single Column with Direction

```python
# Newest first
posts: List[Post] = has_many(Post, order_by="created_at desc")
# Generates: ORDER BY created_at DESC

# Oldest first (explicit asc)
posts: List[Post] = has_many(Post, order_by="created_at asc")
# Generates: ORDER BY created_at ASC
```

#### 3. Multiple Columns

```python
# Pinned first, then by date
comments: List[Comment] = has_many(
    Comment,
    order_by=["pinned desc", "created_at desc"]
)
# Generates: ORDER BY pinned DESC, created_at DESC
```

#### 4. NULLS FIRST / NULLS LAST

```python
# Tasks with due dates first, then tasks without
tasks: List[Task] = has_many(
    Task,
    order_by="due_date nulls last"
)
# Generates: ORDER BY due_date ASC NULLS LAST

# High priority first, with NULL priorities at top
tasks: List[Task] = has_many(
    Task,
    order_by="priority desc nulls first"
)
# Generates: ORDER BY priority DESC NULLS FIRST
```

#### 5. Combined Multiple Columns with NULLS

```python
tasks: List[Task] = has_many(
    Task,
    order_by=[
        "priority desc nulls first",
        "due_date nulls last",
        "created_at"
    ]
)
# Generates: ORDER BY priority DESC NULLS FIRST, due_date ASC NULLS LAST, created_at ASC
```

---

## When - Use Cases and Scenarios

### Use Ordering When...

#### 1. Display Order Matters

```python
class BlogPost(Table):
    # Comments should always appear newest first for discussion
    comments: List[Comment] = has_many(Comment, order_by="created_at desc")
```

#### 2. Business Logic Requires Specific Order

```python
class Project(Table):
    # Tasks must be shown by priority, then due date
    tasks: List[Task] = has_many(
        Task,
        order_by=["priority desc", "due_date nulls last"]
    )
```

#### 3. Featured/Pinned Items First

```python
class Category(Table):
    # Featured products at top, then by sales
    products: List[Product] = has_many(
        Product,
        order_by=["featured desc", "sold_count desc"]
    )
```

#### 4. Positional/Manual Ordering

```python
class Navigation(Table):
    # Menu items in exact display order
    items: List[MenuItem] = has_many(MenuItem, order_by="position")
```

#### 5. Alphabetical Listings

```python
class Author(Table):
    # Tags shown alphabetically
    tags: List[Tag] = many_to_many(Tag, order_by="name")
```

### Don't Use Ordering When...

#### 1. You Need Different Orders in Different Views

If you need `posts` ordered by `created_at desc` in one view and `views desc` in another, you might want:
- Two separate relationships with filters
- Query-time override
- No default ordering

#### 2. Ordering Depends on User Preferences

User-configurable sort orders should be handled at query time, not in relationship definition.

#### 3. Very Large Collections

For relationships with millions of items, consider:
- Pagination (don't load everything)
- Dynamic queries instead of eager loading
- No default ordering (let each query specify)

---

## Who - Target Users

### Web Developers

```python
# Blog: Show recent posts on author profile
class Author(Table):
    posts: List[Post] = has_many(Post, order_by="published_at desc")
```

### E-commerce Developers

```python
# Store: Featured products first, then bestsellers
class Category(Table):
    products: List[Product] = has_many(
        Product,
        order_by=["featured desc", "sold_count desc"]
    )
```

### Project Management Apps

```python
# Kanban: Priority tasks at top
class Board(Table):
    tasks: List[Task] = has_many(
        Task,
        order_by=["priority desc", "due_date nulls last"]
    )
```

### Content Management Systems

```python
# CMS: Pages ordered by menu position
class Section(Table):
    pages: List[Page] = has_many(Page, order_by="position")
```

### Social Applications

```python
# Social: Most engaging content first
class User(Table):
    feed: List[FeedItem] = has_many(
        FeedItem,
        order_by=["promoted desc", "engagement_score desc", "created_at desc"]
    )
```

---

## Where - Integration Points

### 1. Relationship Definitions

```python
class User(Table):
    # has_many with ordering
    posts: List[Post] = has_many(Post, order_by="created_at desc")
    
    # many_to_many with ordering
    courses: List[Course] = many_to_many(Course, order_by="name")
```

### 2. With Other Relationship Options

```python
class User(Table):
    # With backref
    posts: List[Post] = has_many(
        Post,
        backref="author",
        order_by="created_at desc"
    )
    
    # With eager loading
    comments: List[Comment] = has_many(
        Comment,
        lazy="selectin",
        order_by="votes desc"
    )
    
    # With filter
    active_posts: List[Post] = has_many(
        Post,
        filter=[("status", "=", "published")],
        order_by="published_at desc"
    )
    
    # With cascade
    logs: List[Log] = has_many(
        Log,
        on_delete="cascade",
        order_by="timestamp desc"
    )
```

### 3. With Junction Tables (M2M)

```python
class Student(Table):
    # Ordering applies to the related Course, not the junction
    courses: List[Course] = many_to_many(
        Course,
        through=Enrollment,
        order_by="name"
    )
```

---

## How - Complete Usage Guide

### Step 1: Basic Single Column Ordering

```python
from pynext.db import Table, has_many
from typing import List

class Post(Table):
    title: str
    created_at: datetime
    author_id: int

class User(Table):
    name: str
    
    # Newest posts first
    posts: List[Post] = has_many(Post, order_by="created_at desc")

# Usage
user.posts  # Automatically ordered by created_at DESC
```

### Step 2: Multiple Column Ordering

```python
class Comment(Table):
    content: str
    created_at: datetime
    votes: int
    highlighted: bool
    post_id: int

class Post(Table):
    title: str
    
    # Highlighted first, then by votes, then by date
    comments: List[Comment] = has_many(
        Comment,
        order_by=["highlighted desc", "votes desc", "created_at desc"]
    )

# Usage
post.comments  # Highlighted first, then sorted by votes, then by date
```

### Step 3: Handling NULL Values

```python
class Task(Table):
    title: str
    priority: Optional[int]  # Can be NULL
    due_date: Optional[date]  # Can be NULL

class Project(Table):
    name: str
    
    # High priority first (NULLs at end)
    # Then by due date (tasks without due date at end)
    tasks: List[Task] = has_many(
        Task,
        order_by=[
            "priority desc nulls last",
            "due_date nulls last"
        ]
    )

# Usage
project.tasks  # Prioritized tasks first, then tasks without priority/due date
```

### Step 4: Many-to-Many Ordering

```python
class Tag(Table):
    name: str

class Article(Table):
    title: str
    
    # Tags alphabetically
    tags: List[Tag] = many_to_many(Tag, order_by="name")

# Usage
article.tags  # Sorted alphabetically by name
```

### Step 5: Combining with Other Features

```python
class User(Table):
    name: str
    
    # Full-featured relationship with ordering
    active_posts: List[Post] = has_many(
        Post,
        filter=[("status", "=", "published")],  # Only published
        order_by=["pinned desc", "published_at desc"],  # Pinned first
        backref="author",  # Bidirectional sync
        lazy="selectin",  # Batch loading
    )
```

---

## API Reference

### OrderSpec Class

```python
@dataclass
class OrderSpec:
    """Represents a single ORDER BY clause."""
    column: str           # Column name (e.g., "created_at")
    direction: str = "asc"  # "asc" or "desc"
    nulls: Optional[str] = None  # "first" or "last"
```

### OrderingConfig Class

```python
@dataclass
class OrderingConfig:
    """Configuration for relationship ordering."""
    specs: List[OrderSpec]
    raw: Optional[Union[str, List[str]]]  # Original input
    
    @classmethod
    def from_order_by(cls, order_by: Optional[Union[str, List[str]]]) -> "OrderingConfig"
    
    @property
    def has_ordering(self) -> bool
    
    def to_sql(self, table_alias: Optional[str] = None, include_keyword: bool = True) -> str
    
    def get_columns(self, table_alias: Optional[str] = None) -> List[str]
    
    def merge_with(self, other: "OrderingConfig") -> "OrderingConfig"
    
    def override_with(self, other: "OrderingConfig") -> "OrderingConfig"
```

### Parsing Functions

```python
def parse_order_spec(spec_str: str) -> OrderSpec:
    """Parse single order spec string."""

def parse_order_by(order_by: Optional[Union[str, List[str]]]) -> List[OrderSpec]:
    """Parse order_by into list of OrderSpec."""

def build_order_clause(specs: List[OrderSpec], table_alias: Optional[str] = None, include_keyword: bool = True) -> str:
    """Build SQL ORDER BY clause."""
```

### Convenience Functions

```python
def asc(column: str, nulls: Optional[str] = None) -> OrderSpec:
    """Create ascending OrderSpec."""

def desc(column: str, nulls: Optional[str] = None) -> OrderSpec:
    """Create descending OrderSpec."""
```

### Relationship Parameters

```python
def has_many(
    model: Type[T],
    foreign_key: Optional[str] = None,
    order_by: Optional[Union[str, List[str]]] = None,  # NEW
    # ... other parameters
) -> HasMany[T]

def many_to_many(
    model: Type[T],
    through: Optional[Type] = None,
    order_by: Optional[Union[str, List[str]]] = None,  # NEW
    # ... other parameters
) -> ManyToMany[T]
```

---

## SQLAlchemy vs Django vs PyNext

### Feature Comparison

| Feature | SQLAlchemy | Django | PyNext |
|---------|------------|--------|--------|
| **Single column** | `order_by=desc(Model.col)` | `ordering = ['-col']` | `order_by="col desc"` |
| **Multiple columns** | `order_by=[desc(a), asc(b)]` | `ordering = ['-a', 'b']` | `order_by=["a desc", "b"]` |
| **Relationship-level** | Yes (verbose) | Requires Prefetch | Yes (simple) |
| **Override at query** | Complex | Complex | Simple |
| **NULLS FIRST/LAST** | `nullsfirst()`/`nullslast()` | Not built-in | `"col desc nulls last"` |
| **Import required** | `from sqlalchemy import desc` | None | None |
| **Model coupling** | Yes (uses model attributes) | Yes (model-level) | No (strings) |

### Code Comparison

#### SQLAlchemy (15+ lines for M2M with ordering)

```python
from sqlalchemy import desc
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    
    # Multiple columns with different directions
    posts = relationship(
        "Post",
        order_by=[desc(Post.pinned), desc(Post.created_at)],
        back_populates="author"
    )
    
    # NULLS handling requires wrapper
    tasks = relationship(
        "Task",
        order_by=[
            desc(Task.priority).nullsfirst(),
            Task.due_date.nullslast()
        ]
    )
```

#### Django (requires Meta class or Prefetch)

```python
class Post(models.Model):
    class Meta:
        ordering = ['-pinned', '-created_at']  # Affects ALL queries!

# Or use Prefetch for relationship-specific:
User.objects.prefetch_related(
    Prefetch(
        'posts',
        queryset=Post.objects.order_by('-pinned', '-created_at')
    )
)
```

#### PyNext (2 lines per relationship)

```python
class User(Table):
    # Multiple columns - just a list of strings
    posts: List[Post] = has_many(
        Post,
        order_by=["pinned desc", "created_at desc"]
    )
    
    # NULLS handling - built into the string
    tasks: List[Task] = has_many(
        Task,
        order_by=["priority desc nulls first", "due_date nulls last"]
    )
```

### Why PyNext Wins

1. **Zero imports**: Everything is string-based
2. **Natural syntax**: Reads like SQL
3. **Relationship-level**: Ordering defined where it belongs
4. **NULLS support**: First-class citizen, not an afterthought
5. **Less code**: 2 lines vs 15+ lines
6. **More flexible**: Easy to override at query time

---

## Real-World Examples

### Example 1: Blog Application

```python
class Author(Table):
    name: str
    
    # All posts, newest first
    posts: List[Post] = has_many(
        Post,
        order_by="published_at desc"
    )
    
    # Featured posts first, then by views
    featured_posts: List[Post] = has_many(
        Post,
        filter=[("featured", "=", True)],
        order_by=["featured desc", "view_count desc"]
    )

class Post(Table):
    title: str
    author_id: int
    
    # Comments: highlighted first, then most upvoted
    comments: List[Comment] = has_many(
        Comment,
        order_by=["highlighted desc", "votes desc", "created_at"]
    )
```

### Example 2: E-commerce Store

```python
class Category(Table):
    name: str
    
    # Subcategories in display order
    subcategories: List["Category"] = has_many(
        "Category",
        foreign_key="parent_id",
        order_by="position"
    )
    
    # Products: in-stock first, featured, then by rating
    products: List[Product] = has_many(
        Product,
        order_by=[
            "in_stock desc",
            "featured desc",
            "rating desc nulls last",
            "sold_count desc"
        ]
    )

class Product(Table):
    name: str
    
    # Reviews: helpful first, then recent
    reviews: List[Review] = has_many(
        Review,
        order_by=["helpful_count desc", "created_at desc"]
    )
```

### Example 3: Project Management

```python
class Project(Table):
    name: str
    
    # Tasks: incomplete first, then by priority and due date
    tasks: List[Task] = has_many(
        Task,
        order_by=[
            "completed",  # False (0) before True (1)
            "priority desc",
            "due_date nulls last",
            "created_at"
        ]
    )
    
    # Team members alphabetically
    members: List[User] = many_to_many(User, order_by="name")

class Task(Table):
    title: str
    
    # Subtasks by position
    subtasks: List["Task"] = has_many(
        "Task",
        foreign_key="parent_id",
        order_by="position"
    )
```

### Example 4: Social Media Feed

```python
class User(Table):
    name: str
    
    # Feed: promoted first, then by engagement, then recency
    feed: List[FeedItem] = has_many(
        FeedItem,
        order_by=[
            "promoted desc",
            "engagement_score desc",
            "created_at desc"
        ]
    )
    
    # Following list alphabetically
    following: List["User"] = many_to_many(
        "User",
        order_by="name"
    )

class Post(Table):
    content: str
    
    # Comments: pinned first, then chronological
    comments: List[Comment] = has_many(
        Comment,
        order_by=["pinned desc", "created_at"]
    )
```

### Example 5: Navigation/CMS

```python
class Menu(Table):
    name: str
    
    # Menu items in exact display order
    items: List[MenuItem] = has_many(
        MenuItem,
        order_by="position"
    )

class MenuItem(Table):
    title: str
    
    # Nested items in order
    children: List["MenuItem"] = has_many(
        "MenuItem",
        foreign_key="parent_id",
        order_by="position"
    )

class Page(Table):
    title: str
    
    # Sections in display order
    sections: List[Section] = has_many(
        Section,
        order_by="position"
    )
```

---

## Performance Considerations

### 1. Database-Level Sorting is Fast

PyNext ordering generates SQL ORDER BY clauses. This is:
- Executed by the database (optimized for sorting)
- Can use indexes for frequently sorted columns
- Much faster than Python-level sorting for large datasets

### 2. Create Indexes for Order Columns

```sql
-- If you frequently order by created_at
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);

-- Composite index for multiple-column ordering
CREATE INDEX idx_tasks_priority_due ON tasks(priority DESC, due_date);
```

### 3. NULLS Handling is Efficient

PostgreSQL handles NULLS FIRST/LAST natively. It's not a workaround.

### 4. Ordering + Eager Loading = Efficient

```python
class User(Table):
    posts: List[Post] = has_many(
        Post,
        lazy="selectin",  # Batch load
        order_by="created_at desc"  # Sort in SQL
    )

# Single query:
# SELECT * FROM posts WHERE author_id IN (...) ORDER BY created_at DESC
```

### 5. Consider Dynamic Queries for Very Large Collections

```python
class User(Table):
    # For millions of posts, use dynamic query
    posts: List[Post] = has_many(
        Post,
        lazy="dynamic",
        order_by="created_at desc"  # Default for query builder
    )

# Then paginate:
user.posts.limit(20).offset(0)  # First page
```

---

## Troubleshooting

### Common Issues

#### 1. Ordering Not Applied

**Problem**: Items appear unordered.

**Check**:
- Is `order_by` spelled correctly?
- Is the column name correct?
- Are you accessing the relationship correctly?

```python
# Correct
posts: List[Post] = has_many(Post, order_by="created_at desc")

# Wrong (typo in column)
posts: List[Post] = has_many(Post, order_by="createdat desc")
```

#### 2. Invalid Column Name Error

**Problem**: `ValueError: Invalid column name`

**Check**:
- Column names must be valid identifiers
- No spaces, no special characters
- Must start with letter or underscore

```python
# Valid
order_by="created_at"
order_by="_private_field"
order_by="field1"

# Invalid
order_by="created at"  # Space
order_by="123field"    # Starts with number
order_by="field-name"  # Hyphen
```

#### 3. Wrong Direction

**Problem**: Items sorted in wrong order.

**Check**:
- `asc` = ascending (A-Z, 1-9, oldest-newest)
- `desc` = descending (Z-A, 9-1, newest-oldest)
- Default is `asc` if not specified

```python
# Newest first (descending)
order_by="created_at desc"

# Alphabetical (ascending, default)
order_by="name"  # Same as "name asc"
```

#### 4. NULLs in Unexpected Position

**Problem**: NULL values appear at wrong position in results.

**Solution**: Use explicit NULLS handling.

```python
# NULLs at end (most common)
order_by="priority desc nulls last"

# NULLs at beginning
order_by="priority desc nulls first"
```

#### 5. Multiple Column Order Wrong

**Problem**: Secondary sort not working as expected.

**Check**: Columns are sorted in order specified (left to right).

```python
# Sort by A first, then by B
order_by=["a desc", "b"]

# This means: "Sort by A descending, then within same A values, sort by B ascending"
```

### Debugging Tips

```python
# Check what ordering is configured
rel = User.__relationships__["posts"]
print(rel.ordering)  # OrderingConfig
print(rel.ordering.to_sql())  # Generated SQL

# Check raw order_by value
print(rel.order_by)  # Original string/list
```

---

## Summary

Relationship ordering in PyNext provides:

1. **Dead simple syntax**: `"created_at desc"`
2. **Multiple columns**: `["pinned desc", "created_at desc"]`
3. **NULLS handling**: `"due_date nulls last"`
4. **Works everywhere**: has_many, many_to_many, eager loading
5. **SQL-level efficiency**: Database does the sorting
6. **Query-time override**: Can change at load time

### Quick Syntax Reference

| Order Type | Syntax | SQL Generated |
|------------|--------|---------------|
| Ascending (default) | `"name"` | `ORDER BY name ASC` |
| Descending | `"created_at desc"` | `ORDER BY created_at DESC` |
| Multiple columns | `["a", "b desc"]` | `ORDER BY a ASC, b DESC` |
| NULLS FIRST | `"priority desc nulls first"` | `ORDER BY priority DESC NULLS FIRST` |
| NULLS LAST | `"due_date nulls last"` | `ORDER BY due_date ASC NULLS LAST` |

### Best Practices

1. **Define ordering where it makes sense** - On the relationship that needs it
2. **Use NULLS handling** - Don't leave NULL ordering to chance
3. **Create indexes** - For frequently used order columns
4. **Keep it simple** - Most relationships need 1-2 order columns
5. **Consider pagination** - For very large collections

PyNext relationship ordering: Write it like SQL, get it done in one line.

