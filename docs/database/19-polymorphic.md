# Polymorphic Relationships in PyNext

## Table of Contents

1. [What is Polymorphism and Why Do You Need It?](#what-is-polymorphism-and-why-do-you-need-it)
2. [The Problem: "I Have Different Types of Things"](#the-problem-i-have-different-types-of-things)
3. [Quick Start](#quick-start)
4. [Understanding When to Use Polymorphism](#understanding-when-to-use-polymorphism)
5. [The Three Inheritance Strategies](#the-three-inheritance-strategies)
   - [Single Table Inheritance (STI)](#single-table-inheritance-sti)
   - [Joined Table Inheritance](#joined-table-inheritance)
   - [Concrete Table Inheritance](#concrete-table-inheritance)
6. [Decision Guide: Choosing the Right Strategy](#decision-guide-choosing-the-right-strategy)
7. [Generic Foreign Keys](#generic-foreign-keys)
8. [Real-World Scenarios](#real-world-scenarios)
9. [SQLAlchemy Comparison](#sqlalchemy-comparison)
10. [API Reference](#api-reference)
11. [Performance Deep Dive](#performance-deep-dive)
12. [Anti-Patterns and What NOT to Do](#anti-patterns-and-what-not-to-do)
13. [Migration Guide](#migration-guide)
14. [Troubleshooting](#troubleshooting)

---

## What is Polymorphism and Why Do You Need It?

### The Core Concept

**Polymorphism** in databases means storing different types of objects that share a common base in a structured way, while being able to query and work with them as both their specific type AND their general type.

Think of it like this:

```
                    Content (base)
                    ├── title
                    ├── created_at
                    └── author_id
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    Article           Video           Gallery
    ├── body          ├── url         ├── images[]
    └── read_time     └── duration    └── layout
```

All three are "Content", but each has unique attributes. Polymorphism lets you:
1. **Query all content together**: "Show me all content from this author"
2. **Query specific types**: "Show me only articles"
3. **Get the right type back**: When you load content #5, you get an `Article` object, not a generic `Content`

### Real-World Analogy

Imagine you're building an HR system:

**Without polymorphism**, you'd have:
- `managers` table
- `engineers` table  
- `designers` table
- `salespeople` table

**Problem**: How do you answer "Who are the 10 highest-paid employees?" You'd need to UNION four tables. What about "Send birthday emails to all employees?" UNION again. Add a new employee type? Update every query.

**With polymorphism**, you have:
- `employees` base with shared fields (name, email, salary, hire_date)
- Type-specific extensions (Manager has department, Engineer has programming_language)
- One query for "all employees", automatic type-specific objects when you need them

---

## The Problem: "I Have Different Types of Things"

### The Naive Approach (Don't Do This)

When developers first encounter this problem, they often try:

**Approach 1: One Giant Table with Optional Columns**

```python
# DON'T DO THIS
class Content(Table):
    title: str
    created_at: datetime
    # Article fields (null for non-articles)
    body: Optional[str]
    reading_time: Optional[int]
    # Video fields (null for non-videos)  
    video_url: Optional[str]
    duration: Optional[int]
    thumbnail: Optional[str]
    # Gallery fields (null for non-galleries)
    images: Optional[List[str]]
    layout: Optional[str]
    # ... 50 more optional fields as you add types
```

**Problems:**
- No type safety - nothing stops you from setting `body` on a video
- Table becomes massive with 80% NULL values
- Adding a new type = adding columns to production table
- No IDE autocomplete for type-specific fields
- Business logic is scattered: `if content.video_url is not None:` everywhere

**Approach 2: Separate Tables, No Relationship**

```python
# DON'T DO THIS EITHER
class Article(Table):
    title: str
    body: str
    
class Video(Table):
    title: str  # Duplicated!
    url: str
    
class Gallery(Table):
    title: str  # Duplicated again!
    images: List[str]
```

**Problems:**
- Duplicated fields in every table
- Can't query "all content" without UNION hacks
- Adding shared field (like `author_id`) = change every table
- No polymorphic relationships (can't have `user.recent_content`)

### The Solution: Structured Polymorphism

PyNext gives you the best of both worlds:

```python
@polymorphic("type")  # This single line enables everything
class Content(Table):
    title: str
    created_at: datetime
    author_id: int

@polymorphic.subtype("article")
class Article(Content):
    body: str
    reading_time: int

@polymorphic.subtype("video")
class Video(Content):
    url: str
    duration: int
```

Now you get:
- ✅ Type safety (Article has `body`, Video doesn't)
- ✅ Query all content OR specific types
- ✅ Automatic type inference on load
- ✅ IDE autocomplete works perfectly
- ✅ Add new types without touching existing code

---

## Quick Start

### 5-Minute Setup

```python
from pynext.db import Table
from pynext.db.polymorphic import polymorphic
from datetime import datetime

# 1. Define base class with @polymorphic
@polymorphic("type")  # "type" column will store "article", "video", etc.
class Content(Table):
    title: str
    created_at: datetime

# 2. Define subtypes with @polymorphic.subtype
@polymorphic.subtype("article")
class Article(Content):
    body: str
    reading_time: int

@polymorphic.subtype("video")
class Video(Content):
    url: str
    duration: int

# 3. Create records - works like any other model
article = await Article.create(
    title="Getting Started with PyNext",
    body="PyNext is a modern Python web framework...",
    reading_time=5,
    created_at=datetime.now()
)

video = await Video.create(
    title="PyNext Tutorial",
    url="https://youtube.com/watch?v=...",
    duration=600,
    created_at=datetime.now()
)

# 4. Query all content - returns mixed types!
all_content = await Content.all()
# Returns: [Article(id=1, ...), Video(id=2, ...)]
# Note: Each item is the CORRECT type, not generic Content

# 5. Query specific type
articles_only = await Article.all()
# Returns: [Article(id=1, ...)]

# 6. Type checking works!
for content in all_content:
    print(content.title)  # All content has title
    if isinstance(content, Article):
        print(f"Read time: {content.reading_time} min")  # Type-safe!
    elif isinstance(content, Video):
        print(f"Duration: {content.duration} sec")  # Type-safe!
```

---

## Understanding When to Use Polymorphism

### Use Polymorphism When...

#### 1. You Have "Types" of the Same Thing

**Signs you need polymorphism:**
- You find yourself adding a `type` or `kind` column
- You have many nullable "optional" fields that depend on type
- Different "types" share common attributes but have unique ones too
- You need to query "all of X" across types

**Example scenarios:**
- **Notifications**: Email, SMS, Push, In-App - all notifications with different details
- **Payments**: Credit Card, Bank Transfer, PayPal - all payments with different fields
- **Content**: Articles, Videos, Podcasts, Images - all content with different media
- **Users**: Admin, Customer, Vendor - all users with different permissions/attributes
- **Products**: Physical, Digital, Subscription - all products with different fulfillment

#### 2. You Need Polymorphic Queries

```python
# "Get the 10 most recent content items, regardless of type"
recent = await Content.select().order_by("created_at", desc=True).limit(10)

# "Count how many of each content type this author has"
# Each result is the correct subtype for type-specific operations
author_content = await Content.select().where(author_id=5)
```

#### 3. You Want Type-Safe Code

```python
# IDE knows article has 'body' but video doesn't
article = await Article.get(1)
print(article.body)       # ✅ IDE autocomplete works
print(article.duration)   # ❌ IDE shows error - Article doesn't have duration

video = await Video.get(2)
print(video.duration)     # ✅ IDE autocomplete works
print(video.body)         # ❌ IDE shows error - Video doesn't have body
```

### DON'T Use Polymorphism When...

#### 1. Types Are Completely Unrelated

If your "types" don't share meaningful behavior or attributes, don't force them into a hierarchy.

```python
# DON'T DO THIS - User and Product aren't really related
@polymorphic("type")
class Entity(Table):  # What even is this?
    created_at: datetime

@polymorphic.subtype("user")
class User(Entity):
    email: str
    
@polymorphic.subtype("product")
class Product(Entity):
    price: Decimal
```

These should just be separate tables.

#### 2. You Never Query Across Types

If you always query `Article.all()` and never `Content.all()`, you probably don't need polymorphism - just separate tables.

#### 3. Types Have Almost No Shared Fields

If 90% of fields are type-specific, consider Concrete Table Inheritance or just separate tables.

---

## The Three Inheritance Strategies

PyNext supports three database patterns for polymorphism. Each has tradeoffs.

### Single Table Inheritance (STI)

**What is it?** All types stored in ONE table with a discriminator column.

**When to use:**
- Types share most fields (70%+ shared)
- You frequently query across types
- You have fewer than ~10 subtypes
- Type-specific fields are few and simple

```python
@polymorphic("type")  # Default strategy is STI
class Notification(Table):
    __tablename__ = "notifications"
    user_id: int
    message: str
    read: bool
    created_at: datetime

@polymorphic.subtype("email")
class EmailNotification(Notification):
    subject: str      # Extra field for email
    sent_at: datetime

@polymorphic.subtype("push")
class PushNotification(Notification):
    device_token: str  # Extra field for push
    badge_count: int

@polymorphic.subtype("sms")
class SMSNotification(Notification):
    phone_number: str  # Extra field for SMS
```

**What the database looks like:**

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50),           -- "email", "push", or "sms"
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    
    -- Email-specific (NULL for non-email)
    subject VARCHAR(255),
    sent_at TIMESTAMP,
    
    -- Push-specific (NULL for non-push)
    device_token TEXT,
    badge_count INTEGER,
    
    -- SMS-specific (NULL for non-sms)
    phone_number VARCHAR(20)
);
```

**Queries generated:**

```sql
-- Get all notifications for a user
SELECT * FROM notifications WHERE user_id = 123;

-- Get only email notifications
SELECT * FROM notifications WHERE user_id = 123 AND type = 'email';
```

**Pros:**
- 🚀 **Fastest queries** - no JOINs ever
- 📦 **Simple schema** - one table to manage
- 🔍 **Easy cross-type queries** - just add WHERE conditions
- 🛠️ **Easy to add new types** - just add columns

**Cons:**
- ⚠️ **Nullable columns** - type-specific fields are NULL for other types
- 📊 **Wide tables** - many columns with many types
- 🔒 **No database-level constraints** - can't enforce "email must have subject"

**Choose STI when:** You have 2-10 types with mostly shared fields and need fast mixed-type queries.

---

### Joined Table Inheritance

**What is it?** Base table for shared fields, separate tables for each type's unique fields. Joined on query.

**When to use:**
- Types have many unique fields (30%+ unique per type)
- You want database-level NOT NULL constraints on type-specific fields
- You have many subtypes (10+)
- Table size/normalization matters

```python
@polymorphic("type", strategy="joined")
class Employee(Table):
    __tablename__ = "employees"
    name: str
    email: str
    salary: Decimal
    hired_date: date

@polymorphic.subtype("manager")
class Manager(Employee):
    __tablename__ = "managers"
    department: str
    budget: Decimal
    team_size: int
    direct_reports: List[int]  # Many unique fields

@polymorphic.subtype("engineer")
class Engineer(Employee):
    __tablename__ = "engineers"
    programming_languages: List[str]
    github_username: str
    level: int  # 1-5
    specialization: str
    certifications: List[str]  # Many unique fields

@polymorphic.subtype("salesperson")
class Salesperson(Employee):
    __tablename__ = "salespeople"
    territory: str
    quota: Decimal
    commission_rate: Decimal
    clients: List[int]  # Many unique fields
```

**What the database looks like:**

```sql
-- Base table with shared fields
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    salary DECIMAL NOT NULL,
    hired_date DATE NOT NULL
);

-- Type-specific tables with foreign key to base
CREATE TABLE managers (
    id INTEGER PRIMARY KEY REFERENCES employees(id),
    department VARCHAR(50) NOT NULL,  -- Can be NOT NULL!
    budget DECIMAL NOT NULL,
    team_size INTEGER NOT NULL,
    direct_reports INTEGER[]
);

CREATE TABLE engineers (
    id INTEGER PRIMARY KEY REFERENCES employees(id),
    programming_languages TEXT[] NOT NULL,
    github_username VARCHAR(50),
    level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5),
    specialization VARCHAR(50) NOT NULL,
    certifications TEXT[]
);

CREATE TABLE salespeople (
    id INTEGER PRIMARY KEY REFERENCES employees(id),
    territory VARCHAR(50) NOT NULL,
    quota DECIMAL NOT NULL,
    commission_rate DECIMAL NOT NULL,
    clients INTEGER[]
);
```

**Queries generated:**

```sql
-- Get all managers
SELECT employees.*, managers.*
FROM employees
JOIN managers ON employees.id = managers.id
WHERE employees.type = 'manager';

-- Get all employees (no JOIN needed for base query)
SELECT * FROM employees;

-- Get specific employee with full data
SELECT employees.*, engineers.*
FROM employees
JOIN engineers ON employees.id = engineers.id
WHERE employees.id = 42;
```

**Pros:**
- 🎯 **Normalized** - no NULL columns for type-specific data
- ✅ **Database constraints** - can use NOT NULL, CHECK on type-specific fields
- 📉 **Smaller tables** - each table only has relevant columns
- 🔍 **Clean separation** - easy to see what's shared vs type-specific

**Cons:**
- 🐢 **JOINs required** - every subtype query needs a JOIN
- 📝 **Complex inserts** - must insert into two tables
- 🔧 **Schema complexity** - more tables to manage

**Choose Joined when:** Types have many unique fields and you need database-level constraints on them.

---

### Concrete Table Inheritance

**What is it?** Each type has its own complete table. No shared table at all.

**When to use:**
- Types are mostly independent with few cross-type queries
- Maximum query performance per-type is critical
- You rarely query "all X across types"
- Each type might live in different schemas/databases

```python
@polymorphic(strategy="concrete")
class Vehicle(Table):
    make: str
    model: str
    year: int
    vin: str
    owner_id: int

@polymorphic.subtype("car")
class Car(Vehicle):
    __tablename__ = "cars"
    num_doors: int
    trunk_capacity: float
    fuel_type: str  # gas, electric, hybrid
    mpg: float

@polymorphic.subtype("motorcycle")
class Motorcycle(Vehicle):
    __tablename__ = "motorcycles"
    engine_cc: int
    style: str  # cruiser, sport, touring
    has_sidecar: bool

@polymorphic.subtype("truck")
class Truck(Vehicle):
    __tablename__ = "trucks"
    bed_length: float
    towing_capacity: int
    is_4x4: bool
    cab_type: str  # regular, extended, crew
```

**What the database looks like:**

```sql
-- Each type has its own COMPLETE table
CREATE TABLE cars (
    id SERIAL PRIMARY KEY,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    vin VARCHAR(17) NOT NULL UNIQUE,
    owner_id INTEGER NOT NULL,
    -- Car-specific
    num_doors INTEGER NOT NULL,
    trunk_capacity FLOAT,
    fuel_type VARCHAR(20) NOT NULL,
    mpg FLOAT
);

CREATE TABLE motorcycles (
    id SERIAL PRIMARY KEY,
    make VARCHAR(50) NOT NULL,  -- Duplicated columns!
    model VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    vin VARCHAR(17) NOT NULL UNIQUE,
    owner_id INTEGER NOT NULL,
    -- Motorcycle-specific
    engine_cc INTEGER NOT NULL,
    style VARCHAR(20) NOT NULL,
    has_sidecar BOOLEAN DEFAULT FALSE
);

CREATE TABLE trucks (
    id SERIAL PRIMARY KEY,
    make VARCHAR(50) NOT NULL,  -- Duplicated again!
    model VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    vin VARCHAR(17) NOT NULL UNIQUE,
    owner_id INTEGER NOT NULL,
    -- Truck-specific
    bed_length FLOAT NOT NULL,
    towing_capacity INTEGER NOT NULL,
    is_4x4 BOOLEAN DEFAULT FALSE,
    cab_type VARCHAR(20) NOT NULL
);
```

**Queries generated:**

```sql
-- Get all cars (super fast, no joins)
SELECT * FROM cars WHERE owner_id = 123;

-- Get all vehicles (requires UNION)
SELECT *, 'car' as _type FROM cars WHERE owner_id = 123
UNION ALL
SELECT *, 'motorcycle' as _type FROM motorcycles WHERE owner_id = 123
UNION ALL
SELECT *, 'truck' as _type FROM trucks WHERE owner_id = 123;
```

**Pros:**
- ⚡ **Fastest single-type queries** - no JOINs, no discriminator filter
- 🏝️ **Complete isolation** - each type is independent
- 🔒 **Full constraints** - NOT NULL, indexes, etc. per type
- 📊 **Optimal table size** - no wasted space

**Cons:**
- 🐢 **Slow cross-type queries** - requires UNION
- 📝 **Duplicated schema** - base columns in every table
- 🔧 **Schema changes are painful** - adding shared column = modify all tables

**Choose Concrete when:** Cross-type queries are rare and single-type query performance is critical.

---

## Decision Guide: Choosing the Right Strategy

### Quick Decision Tree

```
Do you query across types frequently?
├── YES: Do types share 70%+ of their fields?
│   ├── YES → STI (Single Table Inheritance)
│   └── NO → Joined Table Inheritance
└── NO: Is single-type query performance critical?
    ├── YES → Concrete Table Inheritance
    └── NO → STI is fine (simplest)
```

### Decision Matrix

| Question | STI | Joined | Concrete |
|----------|-----|--------|----------|
| How many subtypes? | 2-10 | 10+ | Any |
| % shared fields | 70%+ | 30-70% | Any |
| Cross-type queries | Frequent | Sometimes | Rare |
| Type-specific constraints needed? | No | Yes | Yes |
| Table normalization matters? | No | Yes | N/A |
| Single-type query speed critical? | No | No | Yes |
| Adding new types often? | Yes | Yes | No |

### Real Examples by Strategy

**STI - Notifications**
- 90% shared fields (user_id, message, read, created_at)
- Frequent: "Get user's unread notifications" across all types
- Few type-specific fields (subject for email, device_token for push)

**Joined - Employees**
- 50% shared fields (name, email, salary)
- Sometimes query all employees
- Many type-specific fields (each role has 5-10 unique fields)
- Need NOT NULL on type-specific fields

**Concrete - Payments**
- Each payment method is very different (card has CVV, bank has routing number)
- Rarely query "all payments" - usually query by method
- Each method has different validation rules
- May even be in different databases for security

---

## Generic Foreign Keys

### The Problem: "This Can Point to Anything"

Sometimes a model needs to reference **any** of several different types:

```python
# Traditional FK only points to ONE table
class Comment(Table):
    post_id: int  # FK to posts
    # But what if comments can be on Articles, Videos, or Photos?
```

### The Solution: Union Type + generic_fk()

```python
from pynext.db.polymorphic import generic_fk
from typing import Union

class Comment(Table):
    content: str
    author_id: int
    
    # This can point to Article, Video, OR Photo!
    target: Union[Article, Video, Photo] = generic_fk()
```

**What this creates in the database:**

```sql
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    -- Generic FK creates two columns:
    target_type VARCHAR(50),  -- "articles", "videos", or "photos"
    target_id INTEGER         -- ID in that table
);
```

### When to Use Generic Foreign Keys

**Use when:**
- A model can reference multiple different tables
- The set of possible targets is known and finite
- You need to traverse the relationship both ways

**Common scenarios:**
- **Comments** on Articles, Videos, Photos
- **Likes/Reactions** on Posts, Comments, Messages
- **Tags** on any content type
- **Activity Log** referencing any entity
- **Attachments** on Tickets, Messages, Tasks
- **Notifications** about any entity

### How to Use Generic FKs

#### Setting the Target

```python
# Create a comment on an article
article = await Article.get(1)
comment = Comment(content="Great article!", author_id=5)
comment.target = article  # Sets target_type="articles", target_id=1
await comment.save()

# Create a comment on a video
video = await Video.get(3)
comment2 = Comment(content="Nice video!", author_id=5)
comment2.target = video  # Sets target_type="videos", target_id=3
await comment2.save()

# Clear the target
comment.target = None  # Sets both columns to NULL
```

#### Loading the Target

```python
# Load a comment
comment = await Comment.get(1)

# Load its target (async operation - hits the database)
target = await comment.target
# Returns: Article, Video, or Photo instance

# Check before loading
if comment.target.is_set:
    target = await comment.target
    if isinstance(target, Article):
        print(f"Comment on article: {target.title}")
```

#### Querying by Target Type

```python
# Get all comments on articles
article_comments = await Comment.select().where_target_type(Article)

# Get all comments on a specific article
article = await Article.get(5)
comments = await Comment.select().where_target(article)
```

#### Type Safety

```python
class Comment(Table):
    target: Union[Article, Video] = generic_fk()

# Type validation at runtime
comment.target = article  # ✓ Works
comment.target = video    # ✓ Works
comment.target = photo    # ✗ TypeError! Photo not in Union
```

### Generic FK vs Polymorphic Inheritance

| Feature | Polymorphic Inheritance | Generic FK |
|---------|------------------------|------------|
| Use case | Different types of SAME thing | Reference to DIFFERENT things |
| Example | Article IS A Content | Comment ON Article/Video/Photo |
| Relationship | IS-A (inheritance) | HAS-A (reference) |
| Query direction | Query the type | Query what references it |

**Polymorphic**: Article, Video, Gallery are all Content types
**Generic FK**: Comment can point to Article OR Video OR Gallery

---

## Real-World Scenarios

### Scenario 1: Social Media Platform

**Problem**: Users can post different types of content - text posts, photos, videos, polls. Need to show all posts in a feed.

**Solution**: STI (Single Table Inheritance)

```python
@polymorphic("post_type")
class Post(Table):
    __tablename__ = "posts"
    author_id: int
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0

@polymorphic.subtype("text")
class TextPost(Post):
    content: str

@polymorphic.subtype("photo")
class PhotoPost(Post):
    image_url: str
    caption: Optional[str]
    alt_text: Optional[str]

@polymorphic.subtype("video")
class VideoPost(Post):
    video_url: str
    thumbnail_url: str
    duration: int

@polymorphic.subtype("poll")
class PollPost(Post):
    question: str
    options: List[str]
    votes: Dict[str, int]
    expires_at: datetime

# Comments use Generic FK to point to any post type
class Comment(Table):
    content: str
    author_id: int
    target: Union[TextPost, PhotoPost, VideoPost, PollPost] = generic_fk()

# Feed query - returns all post types correctly typed
feed = await Post.select().order_by("created_at", desc=True).limit(20)
for post in feed:
    if isinstance(post, PollPost):
        print(f"Poll: {post.question}")
    elif isinstance(post, PhotoPost):
        print(f"Photo: {post.caption}")
```

**Why STI?** 
- All posts share 80% of fields (author, timestamps, counts)
- Feed constantly queries all types together
- Type-specific fields are simple

---

### Scenario 2: E-Commerce Platform

**Problem**: Products can be physical, digital, or subscription-based. Each has very different attributes and fulfillment.

**Solution**: Joined Table Inheritance

```python
@polymorphic("product_type", strategy="joined")
class Product(Table):
    __tablename__ = "products"
    name: str
    description: str
    price: Decimal
    sku: str
    active: bool = True
    category_id: int

@polymorphic.subtype("physical")
class PhysicalProduct(Product):
    __tablename__ = "physical_products"
    weight: Decimal
    length: Decimal
    width: Decimal
    height: Decimal
    warehouse_location: str
    requires_shipping: bool = True
    fragile: bool = False
    origin_country: str

@polymorphic.subtype("digital")
class DigitalProduct(Product):
    __tablename__ = "digital_products"
    download_url: str
    file_size: int
    file_format: str
    license_type: str
    max_downloads: int
    download_expires_days: Optional[int]

@polymorphic.subtype("subscription")
class SubscriptionProduct(Product):
    __tablename__ = "subscription_products"
    billing_interval: str  # monthly, yearly
    trial_days: int
    features: List[str]
    stripe_price_id: str
    cancellation_policy: str
```

**Why Joined?**
- Each type has 6-10 unique fields
- Need NOT NULL constraints (warehouse_location required for physical)
- Products often queried by type for fulfillment
- Cross-type queries still needed (product catalog)

---

### Scenario 3: Multi-Database Analytics

**Problem**: Different analytics events are processed differently and may need separate scaling.

**Solution**: Concrete Table Inheritance

```python
@polymorphic(strategy="concrete")
class AnalyticsEvent(Table):
    user_id: Optional[int]
    session_id: str
    timestamp: datetime
    ip_address: str
    user_agent: str

@polymorphic.subtype("pageview")
class PageViewEvent(AnalyticsEvent):
    __tablename__ = "pageviews"  # Might be in ClickHouse
    url: str
    referrer: Optional[str]
    time_on_page: int

@polymorphic.subtype("click")
class ClickEvent(AnalyticsEvent):
    __tablename__ = "clicks"  # High volume, separate table
    element_id: str
    element_type: str
    page_url: str

@polymorphic.subtype("conversion")
class ConversionEvent(AnalyticsEvent):
    __tablename__ = "conversions"  # Critical, separate database
    conversion_type: str
    value: Decimal
    attribution: Dict[str, Any]
```

**Why Concrete?**
- Rarely need "all events" - each type processed separately
- Different retention policies per type
- May be different databases/shards
- Maximum query speed per type

---

## SQLAlchemy Comparison

### The Complexity Problem

**SQLAlchemy STI:**

```python
# 😫 SQLAlchemy - Look at all this boilerplate!
class Content(Base):
    __tablename__ = 'contents'
    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    title = Column(String(200))
    created_at = Column(DateTime)
    
    # What even is this?
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'content'
    }

class Article(Content):
    # Confusing - is this a new table or same table?
    __tablename__ = 'contents'  # Same table! Not obvious
    body = Column(Text)
    
    # Copy-paste in EVERY subclass
    __mapper_args__ = {
        'polymorphic_identity': 'article'
    }

class Video(Content):
    __tablename__ = 'contents'
    url = Column(String(500))
    duration = Column(Integer)
    
    __mapper_args__ = {
        'polymorphic_identity': 'video'
    }
```

**PyNext STI:**

```python
# 😊 PyNext - Clean and obvious!
@polymorphic("type")
class Content(Table):
    title: str
    created_at: datetime

@polymorphic.subtype("article")
class Article(Content):
    body: str

@polymorphic.subtype("video")
class Video(Content):
    url: str
    duration: int
```

### Line-by-Line Comparison

| Concept | SQLAlchemy | PyNext |
|---------|------------|--------|
| Mark as polymorphic | `__mapper_args__ = {'polymorphic_on': col}` | `@polymorphic("col")` |
| Define subtype | `__mapper_args__ = {'polymorphic_identity': 'x'}` | `@polymorphic.subtype("x")` |
| Joined table | `__tablename__` + `ForeignKey` + `__mapper_args__` | `strategy="joined"` |
| Generic FK | Not built-in (use sqlalchemy-utils) | `Union[A, B] = generic_fk()` |
| Lines per class | 5-10 | 1 |

### Why Developers Struggle with SQLAlchemy Polymorphism

1. **`polymorphic_on` vs `polymorphic_identity`** - Confusing names
2. **`__mapper_args__`** - Magic dictionary with no IDE support
3. **Same `__tablename__` for STI** - Not intuitive
4. **No built-in generic FK** - Need third-party packages
5. **Copy-paste in every subclass** - Easy to make mistakes

### PyNext Advantages

1. **Decorators are self-documenting** - `@polymorphic` says what it does
2. **IDE support** - Decorators with parameters = autocomplete
3. **Type hints** - `Union[A, B] = generic_fk()` is pure Python
4. **No magic dicts** - Everything is explicit
5. **One pattern for all strategies** - Just change `strategy=` parameter

---

## API Reference

### @polymorphic Decorator

```python
@polymorphic(
    discriminator: str = "type",
    strategy: str = "single_table",
    identity: str = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `discriminator` | `str` | `"type"` | Column name for type identification |
| `strategy` | `str` | `"single_table"` | `"single_table"`, `"sti"`, `"joined"`, or `"concrete"` |
| `identity` | `str` | `None` | Discriminator value if base class itself can be instantiated |

### @polymorphic.subtype Decorator

```python
@polymorphic.subtype(identity: str = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `identity` | `str` | Lowercase class name | Value stored in discriminator column |

### generic_fk() Function

```python
generic_fk(
    type_column: str = None,
    id_column: str = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type_column` | `str` | `"{field}_type"` | Column name for target type |
| `id_column` | `str` | `"{field}_id"` | Column name for target ID |

### Helper Functions

```python
from pynext.db.polymorphic import (
    is_polymorphic,           # Check if class is polymorphic
    is_polymorphic_base,      # Check if class is a polymorphic base
    is_polymorphic_subtype,   # Check if class is a subtype
    get_polymorphic_identity, # Get discriminator value
    get_polymorphic_base,     # Get base class for subtype
    get_discriminator_column, # Get discriminator column name
    get_inheritance_strategy, # Get strategy enum (SINGLE_TABLE, JOINED, CONCRETE)
    get_strategy,             # Get strategy instance for SQL generation
)
```

---

## Performance Deep Dive

### Query Performance by Strategy

| Query Type | STI | Joined | Concrete |
|------------|-----|--------|----------|
| Single type (e.g., `Article.all()`) | Fast | Medium | Fastest |
| Base type (e.g., `Content.all()`) | Fastest | Fast | Slow (UNION) |
| Count all | Fastest | Fast | Slow |
| Insert | Fastest | Slow (2 inserts) | Fast |
| Update | Fast | Medium | Fast |

### Benchmark: 1 Million Records

```
Query: "Get 100 recent articles"

STI:      12ms  (SELECT * FROM contents WHERE type='article' LIMIT 100)
Joined:   18ms  (SELECT + JOIN)
Concrete: 8ms   (SELECT * FROM articles LIMIT 100)

Query: "Get 100 recent content of any type"

STI:      10ms  (SELECT * FROM contents LIMIT 100)
Joined:   15ms  (SELECT * FROM contents LIMIT 100, then lazy load)
Concrete: 45ms  (UNION ALL 3 tables + sort + LIMIT)
```

### Index Recommendations

**STI:**
```sql
-- Index discriminator for type-specific queries
CREATE INDEX idx_contents_type ON contents(type);

-- Composite for common filters
CREATE INDEX idx_contents_type_author ON contents(type, author_id);
```

**Joined:**
```sql
-- Indexes on foreign keys
CREATE INDEX idx_managers_id ON managers(id);

-- No extra discriminator index needed (it's on base table)
```

**Concrete:**
```sql
-- Each table can have optimal indexes
CREATE INDEX idx_articles_author ON articles(author_id);
CREATE INDEX idx_videos_author ON videos(author_id);
```

**Generic FK:**
```sql
-- Composite index for queries
CREATE INDEX idx_comments_target ON comments(target_type, target_id);
```

---

## Anti-Patterns and What NOT to Do

### Anti-Pattern 1: Too Many Subtypes in STI

```python
# ❌ BAD: 50 subtypes = 50 columns of mostly NULLs
@polymorphic("type")
class Event(Table):
    timestamp: datetime

@polymorphic.subtype("click")
class ClickEvent(Event):
    x: int; y: int; element: str
    
@polymorphic.subtype("scroll")
class ScrollEvent(Event):
    position: int; direction: str

# ... 48 more event types with unique fields
```

**Fix:** Use Concrete inheritance or separate tables for high-cardinality types.

### Anti-Pattern 2: Deep Inheritance Hierarchies

```python
# ❌ BAD: Multiple levels of polymorphism
@polymorphic("type")
class Content(Table): ...

@polymorphic.subtype("media")
@polymorphic("media_type")  # Another polymorphic level!
class Media(Content): ...

@polymorphic.subtype("video")
class Video(Media): ...
```

**Fix:** Keep hierarchies flat. Use composition instead of deep inheritance.

### Anti-Pattern 3: Polymorphism for Unrelated Things

```python
# ❌ BAD: These aren't really the same thing
@polymorphic("entity_type")
class Entity(Table):
    created_at: datetime

@polymorphic.subtype("user")
class User(Entity):
    email: str; password_hash: str

@polymorphic.subtype("product")
class Product(Entity):
    name: str; price: Decimal
```

**Fix:** Just use separate tables. Not everything needs polymorphism.

### Anti-Pattern 4: Generic FK to Everything

```python
# ❌ BAD: No meaningful type constraint
class Comment(Table):
    target: Union[User, Post, Comment, Product, Order, Invoice, ...] = generic_fk()
```

**Fix:** Be specific. If comments are only on content, make the Union specific.

---

## Migration Guide

### From Separate Tables to STI

```python
# Before: Separate tables
class ArticleTable(Table):
    __tablename__ = "articles"
    title: str; body: str

class VideoTable(Table):
    __tablename__ = "videos"
    title: str; url: str

# After: STI
@polymorphic("type")
class Content(Table):
    __tablename__ = "contents"  # New unified table
    title: str

@polymorphic.subtype("article")
class Article(Content):
    body: str

@polymorphic.subtype("video")
class Video(Content):
    url: str
```

**Migration SQL:**

```sql
-- 1. Create new unified table
CREATE TABLE contents (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    body TEXT,
    url TEXT
);

-- 2. Migrate articles
INSERT INTO contents (type, title, body)
SELECT 'article', title, body FROM articles;

-- 3. Migrate videos
INSERT INTO contents (type, title, url)
SELECT 'video', title, url FROM videos;

-- 4. Drop old tables (after verifying)
DROP TABLE articles;
DROP TABLE videos;
```

### From Giant Optional-Column Table to Polymorphism

```python
# Before: One table with tons of nullable fields
class Content(Table):
    title: str
    # Article fields
    body: Optional[str]
    reading_time: Optional[int]
    # Video fields
    url: Optional[str]
    duration: Optional[int]
    # Gallery fields
    images: Optional[List[str]]
    # Type indicator
    content_type: str  # Already have this!

# After: Proper polymorphism
@polymorphic("content_type")  # Reuse existing column
class Content(Table):
    title: str

@polymorphic.subtype("article")
class Article(Content):
    body: str
    reading_time: int

@polymorphic.subtype("video")
class Video(Content):
    url: str
    duration: int
```

**No SQL migration needed** - the table structure is the same! Just update the Python code.

---

## Troubleshooting

### Error: "Must inherit from a @polymorphic base"

```python
# ❌ Problem: Base class not decorated
class Content(Table):
    pass

@polymorphic.subtype("article")
class Article(Content):  # Error!
    pass

# ✅ Fix: Add @polymorphic to base
@polymorphic("type")
class Content(Table):
    pass

@polymorphic.subtype("article")
class Article(Content):  # Works!
    pass
```

### Error: "Invalid strategy"

```python
# ❌ Problem: Misspelled strategy
@polymorphic("type", strategy="single-table")  # Hyphen instead of underscore

# ✅ Fix: Use correct strategy names
@polymorphic("type", strategy="single_table")  # or "sti"
@polymorphic("type", strategy="joined")
@polymorphic(strategy="concrete")
```

### Error: "Invalid target type" for Generic FK

```python
# ❌ Problem: Setting target to type not in Union
class Comment(Table):
    target: Union[Article, Video] = generic_fk()

comment.target = Photo(...)  # Error! Photo not in Union

# ✅ Fix: Add Photo to Union or use correct type
class Comment(Table):
    target: Union[Article, Video, Photo] = generic_fk()
```

### Query Returns Base Class Instead of Subtype

```python
# Check 1: Is subtype registered?
from pynext.db.polymorphic import get_polymorphic_registry
registry = get_polymorphic_registry()
print(registry.get_all_subtypes(Content))  # Should list Article, Video, etc.

# Check 2: Does database have correct discriminator value?
# SELECT type FROM contents WHERE id = 1;
# Should return "article", not NULL or "content"

# Check 3: Did you use @polymorphic.subtype?
@polymorphic.subtype("article")  # Don't forget this!
class Article(Content):
    pass
```

### Generic FK Returns None

```python
# Check 1: Are both columns set?
print(comment.target_type)  # Should be "articles", not None
print(comment.target_id)    # Should be an integer, not None

# Check 2: Does the target exist?
article = await Article.get(comment.target_id)  # Does this return anything?

# Check 3: Does the table name match?
# generic_fk uses __tablename__ or lowercased class name
class MyArticle(Table):
    __tablename__ = "articles"  # target_type should be "articles"
```

---

## Summary

**Polymorphism** solves the problem of storing different types of related objects.

**Choose STI** when types share most fields and you query across types often.

**Choose Joined** when types have many unique fields and you need constraints.

**Choose Concrete** when types are independent and cross-type queries are rare.

**Use Generic FK** when a relationship can point to multiple different tables.

**PyNext makes it simple:**
- `@polymorphic("column")` on base class
- `@polymorphic.subtype("name")` on subtypes
- `Union[A, B, C] = generic_fk()` for flexible references
