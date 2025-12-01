# PyNext Database Layer

## Table of Contents

1. [Introduction: Why Databases?](#introduction-why-databases)
2. [Chapter 1: How Computers Remember Things](#chapter-1-how-computers-remember-things)
3. [Chapter 2: What is a Database?](#chapter-2-what-is-a-database)
4. [Chapter 3: The Impedance Mismatch Problem](#chapter-3-the-impedance-mismatch-problem)
5. [Chapter 4: ORMs - The Translator](#chapter-4-orms---the-translator)
6. [Chapter 5: PyNext Tables - Python Objects as Database Rows](#chapter-5-pynext-tables---python-objects-as-database-rows)
7. [Chapter 6: CRUD Operations - Create, Read, Update, Delete](#chapter-6-crud-operations---create-read-update-delete)
8. [Chapter 7: Querying Data - Finding What You Need](#chapter-7-querying-data---finding-what-you-need)
9. [Chapter 8: Relationships - Connecting Tables](#chapter-8-relationships---connecting-tables)
10. [Chapter 9: Validation - Ensuring Data Quality](#chapter-9-validation---ensuring-data-quality)
11. [Chapter 10: Transactions - All or Nothing](#chapter-10-transactions---all-or-nothing)
12. [Chapter 11: Raw SQL - The Escape Hatch](#chapter-11-raw-sql---the-escape-hatch)
13. [Chapter 12: Adapters - Connecting to Different Databases](#chapter-12-adapters---connecting-to-different-databases)
14. [API Reference](#api-reference)
15. [Troubleshooting](#troubleshooting)

---

## Introduction: Why Databases?

### The Fundamental Question

Every application needs to **remember things**. Think about it:

- A todo app needs to remember your tasks
- Twitter needs to remember your tweets
- A bank needs to remember your balance
- A game needs to remember your high score

Without memory, every time you close an app, everything would disappear. You'd have to re-enter your password, re-create your profile, re-add your friends—every single time.

**Databases are how applications remember.**

### What This Guide Teaches

By the end of this guide, you'll understand:

1. **What databases are** and why we need them
2. **How PyNext simplifies** database interaction
3. **How to model your data** as Python classes
4. **How to perform operations** (create, read, update, delete)
5. **How to query efficiently** (find exactly what you need)
6. **How to maintain data quality** (validation, relationships)

We'll start from absolute basics and build up to production patterns.

---

## Chapter 1: How Computers Remember Things

### The Memory Hierarchy

Computers have different types of memory, each with trade-offs:

```
┌────────────────────────────────────────────────────────────────────┐
│                     Computer Memory Hierarchy                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐                                               │
│  │    CPU Cache    │  ← Super fast, tiny (KB)                      │
│  └────────┬────────┘    Lost when program ends                     │
│           ↓                                                         │
│  ┌─────────────────┐                                               │
│  │       RAM       │  ← Very fast, small (GB)                      │
│  └────────┬────────┘    Lost when computer turns off               │
│           ↓                                                         │
│  ┌─────────────────┐                                               │
│  │    SSD/HDD      │  ← Slower, large (TB)                        │
│  └────────┬────────┘    Survives restarts! ← THIS IS WHERE         │
│           ↓                                    DATABASES LIVE      │
│  ┌─────────────────┐                                               │
│  │  Cloud Storage  │  ← Slowest, unlimited                        │
│  └─────────────────┘    Survives anything                          │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Variables Don't Persist

In Python, when you create a variable, it lives in RAM:

```python
# This variable exists only while the program runs
user_name = "Alice"
user_age = 25

# When you close Python... *poof* it's gone forever
```

### Files Are Simple But Limited

You could save data to a file:

```python
# Save to a file
with open("users.txt", "w") as f:
    f.write("Alice,25\n")
    f.write("Bob,30\n")

# Read from a file
with open("users.txt", "r") as f:
    for line in f:
        name, age = line.strip().split(",")
        print(f"{name} is {age} years old")
```

**But files have problems:**

| Problem | Example |
|---------|---------|
| **No structure** | Is it CSV? JSON? Custom format? |
| **No querying** | How do you find users over 25? Read entire file! |
| **No concurrency** | Two users editing at once? Corruption! |
| **No relationships** | How do you link users to their posts? |
| **No validation** | What if someone writes "twenty-five" instead of 25? |

This is where databases come in.

---

## Chapter 2: What is a Database?

### The Simple Definition

A **database** is organized, structured storage that:

1. **Persists** - Data survives restarts
2. **Structures** - Data follows a defined format
3. **Queries** - You can ask questions about your data
4. **Validates** - Enforces rules about what data can be stored
5. **Handles concurrency** - Multiple users can access simultaneously

### The Spreadsheet Analogy

Think of a database like a collection of spreadsheets:

```
┌─────────────────────────────────────────────────────────────────────┐
│                           DATABASE                                   │
│  (like an Excel workbook with multiple sheets)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────┐                    │
│  │  TABLE: users (like a spreadsheet)           │                    │
│  ├──────┬────────────┬──────────────────────┬──┤                    │
│  │  id  │   name     │       email          │age│ ← COLUMNS         │
│  ├──────┼────────────┼──────────────────────┼──┤                    │
│  │  1   │  Alice     │  alice@example.com   │25 │ ← ROW (record)    │
│  │  2   │  Bob       │  bob@example.com     │30 │ ← ROW (record)    │
│  │  3   │  Carol     │  carol@example.com   │28 │ ← ROW (record)    │
│  └──────┴────────────┴──────────────────────┴──┘                    │
│                                                                      │
│  ┌─────────────────────────────────────────────┐                    │
│  │  TABLE: posts                                │                    │
│  ├──────┬────────────────────┬──────────┬──────┤                    │
│  │  id  │      title         │ content  │user_id│                   │
│  ├──────┼────────────────────┼──────────┼──────┤                    │
│  │  1   │  Hello World       │  ...     │  1   │ ← Links to Alice  │
│  │  2   │  My Second Post    │  ...     │  1   │ ← Links to Alice  │
│  │  3   │  Bob's First Post  │  ...     │  2   │ ← Links to Bob    │
│  └──────┴────────────────────┴──────────┴──────┘                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Terminology

| Term | Spreadsheet Equivalent | Meaning |
|------|------------------------|---------|
| **Database** | Workbook | Collection of related tables |
| **Table** | Spreadsheet/Sheet | Collection of similar records |
| **Row** | Row | One record (one user, one post) |
| **Column** | Column | One attribute (name, email, age) |
| **Primary Key** | Row number | Unique identifier for each row |
| **Foreign Key** | Reference to another row | Links tables together |

### SQL: The Language of Databases

Databases speak a language called **SQL** (Structured Query Language):

```sql
-- Create a table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    age INTEGER
);

-- Insert data
INSERT INTO users (name, email, age) VALUES ('Alice', 'alice@example.com', 25);

-- Query data
SELECT * FROM users WHERE age > 20;

-- Update data
UPDATE users SET age = 26 WHERE name = 'Alice';

-- Delete data
DELETE FROM users WHERE name = 'Alice';
```

SQL is powerful, but it's **a different language from Python**. This creates a problem...

---

## Chapter 3: The Impedance Mismatch Problem

### Two Different Worlds

Python and SQL think about data differently:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    THE IMPEDANCE MISMATCH                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    Python World                        SQL World                     │
│    ────────────                        ─────────                     │
│                                                                      │
│    Objects with methods                Tables with rows              │
│    user.name                           SELECT name FROM users        │
│                                                                      │
│    Classes                             Table definitions            │
│    class User:                         CREATE TABLE users (...)      │
│                                                                      │
│    Types (str, int, bool)              Types (TEXT, INTEGER, BOOL)  │
│    datetime.now()                      CURRENT_TIMESTAMP             │
│                                                                      │
│    Lists and dicts                     JOINs and subqueries          │
│    user.posts                          SELECT ... JOIN ...           │
│                                                                      │
│    Exceptions                          Error codes                   │
│    try/except                          SQLSTATE                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### The Raw SQL Approach (Painful)

Without any help, you'd have to manually translate between worlds:

```python
import sqlite3

# Connect to database
conn = sqlite3.connect("myapp.db")
cursor = conn.cursor()

# Create a user - lots of manual work!
name = "Alice"
email = "alice@example.com"
age = 25

# Write SQL (different language!)
cursor.execute(
    "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
    (name, email, age)
)
conn.commit()

# Get the ID
user_id = cursor.lastrowid

# Query the user - more SQL!
cursor.execute("SELECT id, name, email, age FROM users WHERE id = ?", (user_id,))
row = cursor.fetchone()

# Manually convert to a Python dict
user = {
    "id": row[0],
    "name": row[1],
    "email": row[2],
    "age": row[3]
}

print(user["name"])  # "Alice"
```

**Problems with this approach:**

1. **Two languages** - You're constantly switching between Python and SQL
2. **Manual mapping** - You have to track column positions (row[0], row[1]...)
3. **No type safety** - Nothing stops you from setting age = "twenty-five"
4. **Repetitive** - Same boilerplate for every table
5. **Error-prone** - Typos in SQL, wrong column order, SQL injection risks
6. **No IDE help** - Your editor can't autocomplete SQL strings

### What We Need

We need a way to:
- Write Python, not SQL
- Have Python objects represent database rows
- Get type safety and IDE autocomplete
- Avoid repetitive boilerplate

This is what an **ORM** does.

---

## Chapter 4: ORMs - The Translator

### What is an ORM?

**ORM** stands for **Object-Relational Mapper**. It's a translator between Python objects and database rows:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         How an ORM Works                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│     Python Code              ORM              Database               │
│     ───────────              ───              ────────               │
│                                                                      │
│   user = User(                               INSERT INTO users      │
│     name="Alice",       ───────────▶         (name, email, age)     │
│     email="a@b.com",                         VALUES ('Alice',       │
│     age=25                                   'a@b.com', 25);        │
│   )                                                                  │
│   await user.insert()                                                │
│                                                                      │
│                                                                      │
│   users = await User      ◀───────────       SELECT * FROM users    │
│     .where(age > 20)                         WHERE age > 20;        │
│     .all()                                                           │
│                              ORM converts                            │
│                              rows → objects                          │
│                                                                      │
│   print(users[0].name)   # "Alice"                                  │
│                          # ↑ Python object!                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### The Translation Table

| Python | ORM Generates | SQL |
|--------|--------------|-----|
| `class User(Table)` | → | `CREATE TABLE users (...)` |
| `User.insert(name="Alice")` | → | `INSERT INTO users (name) VALUES ('Alice')` |
| `User.get(1)` | → | `SELECT * FROM users WHERE id = 1` |
| `User.where(age > 20).all()` | → | `SELECT * FROM users WHERE age > 20` |
| `user.update(age=26)` | → | `UPDATE users SET age = 26 WHERE id = 1` |
| `user.delete()` | → | `DELETE FROM users WHERE id = 1` |

### Why PyNext's ORM is Different

**Most ORMs are complicated:**

```python
# SQLAlchemy - lots of boilerplate
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True)
    age = Column(Integer, default=0)

engine = create_engine('sqlite:///myapp.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Finally use it
user = User(name="Alice", email="alice@example.com", age=25)
session.add(user)
session.commit()
```

**PyNext - just Python types:**

```python
from pynext.db import Table

class User(Table):
    name: str
    email: str
    age: int = 0

# Use it
user = await User.insert(name="Alice", email="alice@example.com", age=25)
```

**That's 5 lines vs 20+ lines!**

### PyNext Design Principles

| Principle | What It Means |
|-----------|---------------|
| **Type hints ARE the schema** | `name: str` means VARCHAR/TEXT column |
| **No special Column types** | Just use `str`, `int`, `float`, `bool`, `datetime` |
| **Automatic common fields** | `id`, `created_at`, `updated_at` added automatically |
| **Async by default** | All database operations are `await`-able |
| **Python first** | If you know Python, you know PyNext |

---

## Chapter 5: PyNext Tables - Python Objects as Database Rows

### Your First Table

Let's create a table step by step:

```python
from pynext.db import Table

class User(Table):
    name: str
    email: str
    age: int = 0
```

**What you wrote:**
- A class called `User` that inherits from `Table`
- Three fields: `name` (required), `email` (required), `age` (optional, defaults to 0)

**What PyNext creates:**

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    age INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields you get automatically:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Auto-incrementing primary key |
| `created_at` | `datetime` | Set when row is created |
| `updated_at` | `datetime` | Updated on every change |

### Type Mapping

PyNext maps Python types to database types:

| Python Type | SQL Type | Example |
|-------------|----------|---------|
| `str` | TEXT/VARCHAR | `"Alice"` |
| `int` | INTEGER | `25` |
| `float` | REAL/DOUBLE | `3.14` |
| `bool` | BOOLEAN | `True` |
| `datetime` | TIMESTAMP | `datetime.now()` |
| `date` | DATE | `date.today()` |
| `bytes` | BLOB | `b"binary data"` |
| `dict` | JSON | `{"key": "value"}` |
| `list` | JSON | `[1, 2, 3]` |
| `Optional[T]` | T (nullable) | `None` or value |

### Field Options

You can customize fields:

```python
from pynext.db import Table, Field
from typing import Optional

class User(Table):
    # Required field (no default)
    name: str
    
    # Optional field (can be None)
    email: Optional[str] = None
    
    # Field with default value
    age: int = 0
    
    # Field with constraints
    username: str = Field(unique=True, min_length=3, max_length=50)
    
    # Computed default (called on each insert)
    api_key: str = Field(default_factory=lambda: generate_random_key())
```

### More Examples

**A Blog Post:**

```python
from pynext.db import Table
from typing import Optional
from datetime import datetime

class Post(Table):
    title: str
    content: str
    published: bool = False
    published_at: Optional[datetime] = None
    view_count: int = 0
    author_id: int  # Foreign key to User
```

**A Product:**

```python
from pynext.db import Table
from decimal import Decimal

class Product(Table):
    name: str
    description: str
    price: Decimal
    stock: int = 0
    is_active: bool = True
    category: str
    tags: list = []  # Stored as JSON
    metadata: dict = {}  # Stored as JSON
```

**A Game Score:**

```python
from pynext.db import Table

class Score(Table):
    player_name: str
    game: str
    points: int
    level: int = 1
    achievements: list = []
```

---

## Chapter 6: CRUD Operations - Create, Read, Update, Delete

### The CRUD Acronym

**CRUD** represents the four basic operations on data:

| Letter | Operation | Description |
|--------|-----------|-------------|
| **C** | Create | Add new records |
| **R** | Read | Get existing records |
| **U** | Update | Modify existing records |
| **D** | Delete | Remove records |

Every database application uses these operations. Let's learn each one.

### Setup

First, configure your database:

```python
from pynext.db import configure_db, MemoryAdapter, Table

# Create an in-memory database (great for learning!)
adapter = MemoryAdapter()
await adapter.connect()
configure_db(adapter)

# Define your model
class User(Table):
    name: str
    email: str
    age: int = 0
```

### Create: Adding New Records

```python
# Method 1: Insert with keyword arguments
user = await User.insert(
    name="Alice",
    email="alice@example.com",
    age=25
)

print(user.id)   # 1 (auto-generated)
print(user.name) # "Alice"

# Method 2: Create object, then insert
user = User(name="Bob", email="bob@example.com", age=30)
await user.insert()

# Method 3: Bulk insert (more efficient for many records)
users = await User.insert_many([
    {"name": "Carol", "email": "carol@example.com", "age": 28},
    {"name": "Dave", "email": "dave@example.com", "age": 35},
    {"name": "Eve", "email": "eve@example.com", "age": 22},
])
```

**What happens under the hood:**

```
User.insert(name="Alice", email="alice@example.com", age=25)
                              ↓
         PyNext validates the data (types match)
                              ↓
         PyNext generates SQL:
         INSERT INTO users (name, email, age) VALUES ('Alice', 'alice@example.com', 25)
                              ↓
         Database executes and returns new ID
                              ↓
         PyNext creates User object with id=1
```

### Read: Getting Records

```python
# Get one by ID
user = await User.get(1)
print(user.name)  # "Alice"

# Get one by ID (returns None if not found)
user = await User.get_or_none(999)
print(user)  # None

# Get all records
all_users = await User.all()
for user in all_users:
    print(f"{user.name}: {user.age} years old")

# Get first matching record
adult = await User.where(User.age >= 18).first()

# Check if records exist
has_users = await User.exists()
has_alice = await User.where(User.name == "Alice").exists()

# Count records
total = await User.count()
adults = await User.where(User.age >= 18).count()
```

### Update: Modifying Records

```python
# Method 1: Update single record
user = await User.get(1)
await user.update(age=26)

# Method 2: Update with dict
await user.update({"age": 27, "name": "Alice Smith"})

# Method 3: Modify and save
user.age = 28
user.name = "Alice Johnson"
await user.save()

# Method 4: Bulk update (many records at once)
await User.where(User.age < 18).update_many(is_minor=True)
```

**What happens under the hood:**

```
user.update(age=26)
       ↓
PyNext validates new age (is it an int?)
       ↓
PyNext generates SQL:
UPDATE users SET age = 26, updated_at = '...' WHERE id = 1
       ↓
Database executes
       ↓
user object is updated in memory
```

### Delete: Removing Records

```python
# Method 1: Delete single record
user = await User.get(1)
await user.delete()

# Method 2: Delete by ID
await User.delete(1)

# Method 3: Bulk delete
await User.where(User.age < 0).delete_many()  # Delete invalid records

# Method 4: Delete all (careful!)
await User.delete_all()  # Removes all users!
```

### Upsert: Insert or Update

Sometimes you want to insert a new record OR update if it exists:

```python
# Upsert by unique field
user = await User.upsert(
    {"email": "alice@example.com"},  # Find by this
    {"name": "Alice", "age": 25}     # Set these values
)

# If email exists: updates name and age
# If email doesn't exist: inserts new record
```

### Complete CRUD Example

```python
from pynext.db import configure_db, MemoryAdapter, Table

# Setup
adapter = MemoryAdapter()
await adapter.connect()
configure_db(adapter)

class Task(Table):
    title: str
    completed: bool = False

# CREATE
task1 = await Task.insert(title="Learn PyNext")
task2 = await Task.insert(title="Build an app")
task3 = await Task.insert(title="Deploy to production")

print(f"Created {await Task.count()} tasks")

# READ
all_tasks = await Task.all()
for task in all_tasks:
    status = "✓" if task.completed else "○"
    print(f"{status} {task.title}")

# UPDATE
task1 = await Task.get(1)
await task1.update(completed=True)
print(f"\nCompleted: {task1.title}")

# READ (filtered)
pending = await Task.where(Task.completed == False).all()
print(f"\n{len(pending)} tasks remaining")

# DELETE
await task3.delete()
print(f"\nDeleted task: {task3.title}")
print(f"{await Task.count()} tasks left")
```

Output:
```
Created 3 tasks
○ Learn PyNext
○ Build an app
○ Deploy to production

Completed: Learn PyNext

2 tasks remaining

Deleted task: Deploy to production
2 tasks left
```

---

## Chapter 7: Querying Data - Finding What You Need

### Why Querying Matters

Imagine you have 1 million users. You don't want to load all of them into memory just to find users from New York. You want the database to do the filtering and send you only the matching records.

```
Without querying:                    With querying:
─────────────────                    ──────────────
Load 1M users → Filter in Python    Ask database: "Find NYC users"
1M rows transferred                  1K rows transferred
Slow and memory-hungry!              Fast and efficient!
```

### The Query Builder

PyNext provides a fluent query builder:

```python
# Start with the table
User.where(...)      # Add conditions
    .order_by(...)   # Sort results
    .limit(...)      # Limit count
    .offset(...)     # Skip records
    .all()           # Execute and get results
```

### Basic Conditions

```python
# Equality
users = await User.where(User.name == "Alice").all()

# Comparison
adults = await User.where(User.age >= 18).all()
young = await User.where(User.age < 30).all()

# Not equal
non_admins = await User.where(User.role != "admin").all()

# IN list
specific = await User.where(User.id.in_([1, 2, 3])).all()

# NOT IN list
others = await User.where(User.id.not_in([1, 2, 3])).all()

# NULL checks
with_email = await User.where(User.email != None).all()
no_email = await User.where(User.email == None).all()

# LIKE patterns
gmail = await User.where(User.email.like("%@gmail.com")).all()
starts_a = await User.where(User.name.like("A%")).all()

# BETWEEN
middle_aged = await User.where(User.age.between(30, 50)).all()
```

### Combining Conditions

```python
# AND (multiple where clauses)
adult_alices = await User.where(
    User.name == "Alice",
    User.age >= 18
).all()

# OR (using |)
from pynext.db import or_

young_or_admin = await User.where(
    or_(User.age < 18, User.role == "admin")
).all()

# Complex combinations
complex_query = await User.where(
    User.is_active == True,
    or_(
        User.role == "admin",
        User.age >= 18
    )
).all()
```

### Sorting Results

```python
# Ascending (default)
oldest_first = await User.order_by(User.age).all()

# Descending
youngest_first = await User.order_by(User.age.desc()).all()

# Multiple columns
sorted_users = await User.order_by(User.age.desc(), User.name).all()
```

### Pagination

```python
# Limit results
top_10 = await User.order_by(User.age.desc()).limit(10).all()

# Skip and take (for pagination)
page_size = 20
page_number = 3

page_3 = await User.order_by(User.id).offset(page_size * (page_number - 1)).limit(page_size).all()

# Built-in pagination helper
page = await User.order_by(User.id).page(page=3, per_page=20)
# page.items - list of users
# page.total - total count
# page.pages - total pages
# page.has_next - boolean
# page.has_prev - boolean
```

### Selecting Specific Columns

```python
# Select only certain fields (more efficient)
names = await User.select(User.name, User.email).all()
# Returns list of tuples: [("Alice", "alice@example.com"), ...]

# With where clause
admin_names = await User.select(User.name).where(User.role == "admin").all()
```

### Aggregations

```python
# Count
total_users = await User.count()
active_users = await User.where(User.is_active == True).count()

# Sum, Avg, Min, Max
from pynext.db import func

total_age = await User.select(func.sum(User.age)).scalar()
average_age = await User.select(func.avg(User.age)).scalar()
oldest_age = await User.select(func.max(User.age)).scalar()
youngest_age = await User.select(func.min(User.age)).scalar()

# Group by
age_counts = await User.select(
    User.age,
    func.count(User.id)
).group_by(User.age).all()
# [(25, 10), (30, 15), (35, 8)]  - age and count
```

### Query Execution Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `.all()` | `list[Model]` | All matching records |
| `.first()` | `Model` or `None` | First matching record |
| `.one()` | `Model` | Exactly one (raises if 0 or 2+) |
| `.count()` | `int` | Number of matches |
| `.exists()` | `bool` | True if any match |
| `.scalar()` | `Any` | Single value (for aggregations) |

### Complete Query Example

```python
from pynext.db import Table, or_

class Product(Table):
    name: str
    price: float
    category: str
    in_stock: bool = True

# Insert sample data
await Product.insert_many([
    {"name": "Laptop", "price": 999.99, "category": "Electronics", "in_stock": True},
    {"name": "Mouse", "price": 29.99, "category": "Electronics", "in_stock": True},
    {"name": "Keyboard", "price": 79.99, "category": "Electronics", "in_stock": False},
    {"name": "Coffee Mug", "price": 12.99, "category": "Kitchen", "in_stock": True},
    {"name": "Water Bottle", "price": 24.99, "category": "Kitchen", "in_stock": True},
])

# Query 1: In-stock electronics under $100
affordable_tech = await Product.where(
    Product.category == "Electronics",
    Product.price < 100,
    Product.in_stock == True
).all()
# Returns: [Mouse]

# Query 2: Kitchen items or items over $500
kitchen_or_expensive = await Product.where(
    or_(
        Product.category == "Kitchen",
        Product.price > 500
    )
).order_by(Product.price.desc()).all()
# Returns: [Laptop, Water Bottle, Coffee Mug]

# Query 3: Average price by category
from pynext.db import func

avg_by_category = await Product.select(
    Product.category,
    func.avg(Product.price)
).group_by(Product.category).all()
# Returns: [("Electronics", 369.99), ("Kitchen", 18.99)]
```

---

## Chapter 8: Relationships - Connecting Tables

### The Relationship Analogy

Think about real-world relationships:

- A **person** has one **passport** (one-to-one)
- A **person** has many **posts** (one-to-many)
- A **student** takes many **courses**, and a **course** has many **students** (many-to-many)

Databases model these same relationships.

### One-to-Many: The Most Common

```
┌─────────────────┐         ┌─────────────────┐
│      User       │         │      Post       │
├─────────────────┤         ├─────────────────┤
│ id: 1           │◄───────┐│ id: 1           │
│ name: "Alice"   │        ││ title: "Hello"  │
└─────────────────┘        ││ user_id: 1 ─────┘
                           │└─────────────────┘
                           │
                           │┌─────────────────┐
                           ││ id: 2           │
                           └│ title: "World"  │
                            │ user_id: 1 ─────┘
                            └─────────────────┘

One User has Many Posts
```

**Implementation:**

```python
from pynext.db import Table, ForeignKey

class User(Table):
    name: str
    email: str

class Post(Table):
    title: str
    content: str
    user_id: int = ForeignKey(User)  # Links to User

# Create user with posts
user = await User.insert(name="Alice", email="alice@example.com")

post1 = await Post.insert(title="My First Post", content="Hello!", user_id=user.id)
post2 = await Post.insert(title="Second Post", content="World!", user_id=user.id)

# Query: Get all posts for a user
alice_posts = await Post.where(Post.user_id == user.id).all()

# Or with eager loading (one query instead of two)
user = await User.get(1).load(User.posts)
for post in user.posts:
    print(post.title)
```

### One-to-One

```
┌─────────────────┐         ┌─────────────────┐
│      User       │         │     Profile     │
├─────────────────┤         ├─────────────────┤
│ id: 1           │◄───────┐│ id: 1           │
│ name: "Alice"   │        ││ bio: "..."      │
└─────────────────┘        └│ user_id: 1 ─────┘
                            └─────────────────┘

One User has One Profile
```

**Implementation:**

```python
class User(Table):
    name: str
    email: str

class Profile(Table):
    bio: str
    avatar_url: str
    user_id: int = ForeignKey(User, unique=True)  # unique=True makes it one-to-one

# Create
user = await User.insert(name="Alice", email="alice@example.com")
profile = await Profile.insert(bio="Python developer", avatar_url="...", user_id=user.id)

# Query
profile = await Profile.where(Profile.user_id == user.id).first()
```

### Many-to-Many

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│     Student     │         │  Enrollment     │         │     Course      │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id: 1           │◄───────┐│ student_id: 1   │┌───────►│ id: 1           │
│ name: "Alice"   │        ││ course_id: 1  ──┘        │ name: "Math"    │
└─────────────────┘        │└─────────────────┘         └─────────────────┘
                           │┌─────────────────┐         
                           ││ student_id: 1   │┌───────►┌─────────────────┐
                           └│ course_id: 2  ──┘        │ id: 2           │
                            └─────────────────┘         │ name: "Physics" │
                                                        └─────────────────┘

One Student takes Many Courses
One Course has Many Students
→ Need a "junction table" (Enrollment) in the middle
```

**Implementation:**

```python
class Student(Table):
    name: str

class Course(Table):
    name: str
    instructor: str

class Enrollment(Table):
    student_id: int = ForeignKey(Student)
    course_id: int = ForeignKey(Course)
    enrolled_at: datetime
    grade: Optional[str] = None

# Enroll a student in courses
alice = await Student.insert(name="Alice")
math = await Course.insert(name="Math", instructor="Dr. Smith")
physics = await Course.insert(name="Physics", instructor="Dr. Jones")

await Enrollment.insert(student_id=alice.id, course_id=math.id, enrolled_at=datetime.now())
await Enrollment.insert(student_id=alice.id, course_id=physics.id, enrolled_at=datetime.now())

# Get all courses for a student
alice_enrollments = await Enrollment.where(Enrollment.student_id == alice.id).all()
alice_course_ids = [e.course_id for e in alice_enrollments]
alice_courses = await Course.where(Course.id.in_(alice_course_ids)).all()

# Or with a join (more efficient)
alice_courses = await Course.join(Enrollment).where(
    Enrollment.student_id == alice.id
).all()
```

### Eager Loading (Avoiding N+1 Problem)

The **N+1 problem** is a common performance issue:

```python
# BAD: N+1 queries (1 for users + N for posts)
users = await User.all()  # 1 query
for user in users:
    posts = await Post.where(Post.user_id == user.id).all()  # N queries!
    print(f"{user.name} has {len(posts)} posts")

# If you have 100 users, that's 101 database queries!
```

**Solution: Eager loading**

```python
# GOOD: 2 queries total (1 for users + 1 for all related posts)
users = await User.all().load(User.posts)
for user in users:
    print(f"{user.name} has {len(user.posts)} posts")

# Only 2 queries, no matter how many users!
```

---

## Chapter 9: Validation - Ensuring Data Quality

### Why Validate?

Bad data is worse than no data. Consider:

```python
# Without validation, anything goes:
user = User(name="", email="not-an-email", age=-5)
await user.insert()  # This would succeed! 😱

# Now you have garbage in your database:
# - Empty name
# - Invalid email
# - Negative age
```

Validation prevents bad data from entering your database.

### Automatic Type Validation

PyNext validates types automatically:

```python
class User(Table):
    name: str
    age: int

# This works
user = await User.insert(name="Alice", age=25)

# This raises TypeError
user = await User.insert(name=123, age="twenty-five")
# TypeError: name must be str, got int
```

### Built-in Validators

```python
from pynext.db import Table, Field

class User(Table):
    # String length constraints
    name: str = Field(min_length=2, max_length=100)
    
    # Regex pattern
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    
    # Numeric ranges
    age: int = Field(ge=0, le=150)  # ge = greater/equal, le = less/equal
    
    # Choices/enum
    role: str = Field(choices=["user", "admin", "moderator"])
    
    # Required vs optional
    bio: Optional[str] = None  # Optional (can be None)
    password: str = Field(required=True)  # Required (cannot be None)
    
    # Unique constraint
    username: str = Field(unique=True)
```

### Validation Error Messages

```python
try:
    user = await User.insert(
        name="A",           # Too short! (min_length=2)
        email="not-email",  # Invalid pattern
        age=-5,             # Below minimum
        role="superadmin",  # Not in choices
    )
except ValidationError as e:
    print(e.errors)
    # {
    #     "name": ["String must be at least 2 characters"],
    #     "email": ["Value does not match pattern"],
    #     "age": ["Value must be >= 0"],
    #     "role": ["Value must be one of: user, admin, moderator"]
    # }
```

### Custom Validators

```python
from pynext.db import Table, Field, validator

class User(Table):
    name: str
    email: str
    password: str
    confirm_password: str
    
    @validator("email")
    def validate_email(cls, value):
        if "@" not in value:
            raise ValueError("Must contain @")
        if value.endswith("@tempmail.com"):
            raise ValueError("Temporary emails not allowed")
        return value.lower()  # Can also transform value
    
    @validator("confirm_password")
    def passwords_match(cls, value, values):
        if value != values.get("password"):
            raise ValueError("Passwords do not match")
        return value
    
    @validator("name")
    def clean_name(cls, value):
        # Strip whitespace and capitalize
        return value.strip().title()
```

### Model-Level Validation

```python
from pynext.db import Table, model_validator

class DateRange(Table):
    name: str
    start_date: date
    end_date: date
    
    @model_validator
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")

# This raises ValueError
await DateRange.insert(
    name="Invalid Range",
    start_date=date(2024, 12, 31),
    end_date=date(2024, 1, 1)  # Before start!
)
```

### Validation Summary

| Type | Example | Validates |
|------|---------|-----------|
| Type hints | `age: int` | Must be an integer |
| Required | `Field(required=True)` | Cannot be None |
| Min/max length | `Field(min_length=2)` | String length |
| Numeric range | `Field(ge=0, le=100)` | Number bounds |
| Pattern | `Field(pattern=r'...')` | Regex match |
| Choices | `Field(choices=[...])` | Value in list |
| Custom | `@validator` | Any Python logic |
| Model-level | `@model_validator` | Cross-field logic |

---

## Chapter 10: Transactions - All or Nothing

### The Bank Transfer Problem

Imagine transferring $100 from Alice to Bob:

```python
# Without transactions - DANGEROUS!
alice = await Account.get(alice_id)
bob = await Account.get(bob_id)

alice.balance -= 100  # Step 1: Take from Alice
await alice.save()

# What if the server crashes HERE? 💥
# Alice lost $100, Bob got nothing!

bob.balance += 100    # Step 2: Give to Bob
await bob.save()
```

If anything fails between Step 1 and Step 2, the money disappears!

### What is a Transaction?

A **transaction** is a group of operations that either **all succeed** or **all fail**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TRANSACTION                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                      │
│  │ Op 1     │───►│ Op 2     │───►│ Op 3     │                      │
│  │ -$100    │    │ +$100    │    │ Log it   │                      │
│  └──────────┘    └──────────┘    └──────────┘                      │
│                                                                      │
│  If ALL succeed → COMMIT (make permanent)                           │
│  If ANY fails   → ROLLBACK (undo everything)                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Basic Transactions in PyNext

```python
from pynext.db import transaction

async def transfer_money(from_id: int, to_id: int, amount: float):
    async with transaction():
        # All operations inside this block are atomic
        from_account = await Account.get(from_id)
        to_account = await Account.get(to_id)
        
        if from_account.balance < amount:
            raise ValueError("Insufficient funds")
        
        from_account.balance -= amount
        to_account.balance += amount
        
        await from_account.save()
        await to_account.save()
        
        # Log the transfer
        await TransferLog.insert(
            from_account=from_id,
            to_account=to_id,
            amount=amount
        )
    
    # If we get here, transaction committed successfully
    print(f"Transferred ${amount}")

# Usage
try:
    await transfer_money(alice_id, bob_id, 100)
except Exception as e:
    # If anything fails, ALL changes are rolled back
    print(f"Transfer failed: {e}")
```

### Automatic Rollback

```python
async with transaction():
    await User.insert(name="Alice")  # Success
    await User.insert(name="Bob")    # Success
    raise Exception("Oops!")         # Error!
    await User.insert(name="Carol")  # Never runs

# After the exception:
# - Alice was NOT inserted (rolled back)
# - Bob was NOT inserted (rolled back)
# - Database is exactly as before the transaction
```

### Savepoints (Nested Transactions)

Sometimes you want to rollback part of a transaction:

```python
async with transaction():
    await Order.insert(customer_id=1, total=100)
    
    try:
        async with transaction():  # This creates a savepoint
            await Inventory.update(product_id=1, quantity=-1)
            if inventory_check_failed:
                raise InventoryError("Out of stock")
    except InventoryError:
        # Inner transaction rolled back
        # But outer transaction continues!
        pass
    
    await Order.insert(customer_id=1, total=50)  # Different order
    
# Outer transaction commits
# Inner transaction was rolled back but didn't affect outer
```

### Transaction Isolation Levels

Different isolation levels control what other transactions can see:

```python
from pynext.db import transaction, IsolationLevel

# Read Committed (default) - see only committed data
async with transaction(isolation=IsolationLevel.READ_COMMITTED):
    ...

# Repeatable Read - consistent view throughout transaction
async with transaction(isolation=IsolationLevel.REPEATABLE_READ):
    ...

# Serializable - strongest isolation, transactions appear sequential
async with transaction(isolation=IsolationLevel.SERIALIZABLE):
    ...
```

### When to Use Transactions

| Scenario | Use Transaction? |
|----------|------------------|
| Single insert/update | Usually no (auto-committed) |
| Multiple related changes | Yes |
| Money/inventory operations | Always yes |
| Any "all or nothing" logic | Yes |
| Read-only queries | Usually no |

---

## Chapter 11: Raw SQL - The Escape Hatch

### When ORM Isn't Enough

PyNext's ORM covers 95% of use cases. But sometimes you need raw SQL:

- **Complex queries** - Window functions, CTEs, advanced joins
- **Performance** - Hand-optimized queries for hot paths
- **Database features** - Specific PostgreSQL/SQLite features
- **Migrations** - Schema modifications

### Executing Raw SQL

```python
from pynext.db import sql

# Simple query
users = await sql("SELECT * FROM users WHERE age > $1", 18)

# Returns list of dicts
for user in users:
    print(user["name"], user["email"])

# Insert with returning
result = await sql(
    "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
    "Alice", "alice@example.com"
)
user_id = result[0]["id"]

# Update/Delete (returns affected count)
affected = await sql("DELETE FROM users WHERE last_login < $1", old_date)
print(f"Deleted {affected} inactive users")
```

### Getting Single Values

```python
from pynext.db import sql_one, sql_val

# Get one row (raises if not exactly 1)
user = await sql_one("SELECT * FROM users WHERE id = $1", 1)

# Get single value
count = await sql_val("SELECT COUNT(*) FROM users")
max_age = await sql_val("SELECT MAX(age) FROM users")
```

### Complex Queries

```python
# Window functions
rankings = await sql("""
    SELECT 
        name,
        score,
        RANK() OVER (ORDER BY score DESC) as rank
    FROM players
    WHERE game = $1
""", "chess")

# CTEs (Common Table Expressions)
results = await sql("""
    WITH active_users AS (
        SELECT * FROM users WHERE last_login > NOW() - INTERVAL '30 days'
    ),
    user_orders AS (
        SELECT user_id, SUM(total) as total_spent
        FROM orders
        WHERE user_id IN (SELECT id FROM active_users)
        GROUP BY user_id
    )
    SELECT u.name, COALESCE(o.total_spent, 0) as total_spent
    FROM active_users u
    LEFT JOIN user_orders o ON u.id = o.user_id
    ORDER BY total_spent DESC
""")

# Full text search (PostgreSQL)
posts = await sql("""
    SELECT *, ts_rank(search_vector, query) as rank
    FROM posts, plainto_tsquery('english', $1) query
    WHERE search_vector @@ query
    ORDER BY rank DESC
    LIMIT 20
""", "python web framework")
```

### SQL Builder (Type-Safe Raw SQL)

For complex queries with type safety:

```python
from pynext.db import SQL, Select, Insert

# Build SELECT
query = (
    Select("users")
    .columns("id", "name", "email")
    .where("age > $1", 18)
    .order_by("name")
    .limit(10)
)

users = await query.execute()

# Build INSERT
query = (
    Insert("users")
    .values(name="Alice", email="alice@example.com", age=25)
    .returning("id")
)

result = await query.execute()
```

### When to Use What

| Situation | Use |
|-----------|-----|
| Standard CRUD | PyNext ORM (`User.insert()`, `User.get()`) |
| Complex conditions | Query builder (`.where()`, `.join()`) |
| Very complex queries | Raw SQL (`sql()`, `sql_one()`) |
| Performance-critical | Raw SQL or SQL builder |
| Database-specific features | Raw SQL |

---

## Chapter 12: Adapters - Connecting to Different Databases

### What is an Adapter?

An **adapter** translates between PyNext and a specific database:

```
┌─────────────────────────────────────────────────────────────────────┐
│                           PyNext ORM                                 │
│                                                                      │
│  User.insert(name="Alice")                                          │
│               ↓                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                           ADAPTER                                    │
│                    (translates to database)                         │
├──────────────────┬──────────────────┬───────────────────────────────┤
│   MemoryAdapter  │  PostgresAdapter │   (Future adapters...)        │
│   (SQLite)       │  (PostgreSQL)    │                               │
└────────┬─────────┴────────┬─────────┴───────────────────────────────┘
         ↓                  ↓
    SQLite DB         PostgreSQL DB
```

### MemoryAdapter (Development/Testing)

Perfect for learning and testing - no setup required:

```python
from pynext.db import configure_db, MemoryAdapter

# Create in-memory database
adapter = MemoryAdapter()
await adapter.connect()
configure_db(adapter)

# Use it (data disappears when program ends)
await User.insert(name="Alice")
```

**Pros:**
- Zero setup
- Fast (runs in memory)
- Great for tests

**Cons:**
- Data doesn't persist
- Not for production

### MockAdapter (Pure Testing)

For unit tests without even SQLite:

```python
from pynext.db import configure_db, MockAdapter

# Completely fake database
adapter = MockAdapter()
configure_db(adapter)

# You can pre-populate mock data
adapter.set_data("users", [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
])

# Queries return mock data
users = await User.all()  # Returns the mock data
```

### PostgresAdapter (Production)

For real applications:

```python
from pynext.db import configure_db
from pynext.db.adapters import PostgresAdapter

# Connect to PostgreSQL
adapter = PostgresAdapter("postgresql://user:pass@localhost:5432/mydb")
await adapter.connect()
configure_db(adapter)

# Now using real PostgreSQL!
await User.insert(name="Alice")  # Persisted to PostgreSQL
```

See [POSTGRES.md](./POSTGRES.md) for complete PostgreSQL documentation.

### Choosing an Adapter

| Scenario | Recommended Adapter |
|----------|---------------------|
| Learning PyNext | `MemoryAdapter` |
| Unit tests | `MockAdapter` |
| Integration tests | `MemoryAdapter` or test PostgreSQL |
| Development | `MemoryAdapter` or local PostgreSQL |
| Production | `PostgresAdapter` |

### Switching Adapters

The beauty of adapters - your model code never changes:

```python
class User(Table):
    name: str
    email: str

# Development
if os.getenv("ENV") == "development":
    adapter = MemoryAdapter()
else:
    adapter = PostgresAdapter(os.getenv("DATABASE_URL"))

await adapter.connect()
configure_db(adapter)

# Same code works with any adapter!
await User.insert(name="Alice")
```

---

## API Reference

### Table Base Class

```python
class Table:
    # Auto-generated fields
    id: int                    # Primary key
    created_at: datetime       # Set on insert
    updated_at: datetime       # Updated on save
    
    # Class methods
    @classmethod
    async def insert(**fields) -> Self
    @classmethod
    async def insert_many(records: list[dict]) -> list[Self]
    @classmethod
    async def get(id: int) -> Self
    @classmethod
    async def get_or_none(id: int) -> Optional[Self]
    @classmethod
    async def all() -> list[Self]
    @classmethod
    def where(*conditions) -> Query
    @classmethod
    async def count() -> int
    @classmethod
    async def exists() -> bool
    @classmethod
    async def upsert(match: dict, data: dict) -> Self
    @classmethod
    async def delete(id: int) -> None
    @classmethod
    async def delete_all() -> int
    
    # Instance methods
    async def save() -> None
    async def update(**fields) -> None
    async def delete() -> None
    async def refresh() -> None
```

### Query Builder

```python
class Query:
    def where(*conditions) -> Query
    def order_by(*fields) -> Query
    def limit(n: int) -> Query
    def offset(n: int) -> Query
    def select(*fields) -> Query
    def join(table: type[Table]) -> Query
    def group_by(*fields) -> Query
    def load(*relationships) -> Query
    
    async def all() -> list[Table]
    async def first() -> Optional[Table]
    async def one() -> Table
    async def count() -> int
    async def exists() -> bool
    async def scalar() -> Any
    async def page(page: int, per_page: int) -> Page
    
    async def update_many(**fields) -> int
    async def delete_many() -> int
```

### Field Options

```python
Field(
    # Value constraints
    required: bool = False,
    default: Any = None,
    default_factory: Callable = None,
    
    # String constraints
    min_length: int = None,
    max_length: int = None,
    pattern: str = None,  # Regex
    
    # Numeric constraints
    gt: Number = None,   # Greater than
    ge: Number = None,   # Greater or equal
    lt: Number = None,   # Less than
    le: Number = None,   # Less or equal
    
    # Database constraints
    unique: bool = False,
    index: bool = False,
    
    # Enum
    choices: list = None,
)
```

### Adapters

```python
# Memory (SQLite in-memory)
adapter = MemoryAdapter(echo: bool = False)

# Mock (fake data for tests)
adapter = MockAdapter()
adapter.set_data(table: str, records: list[dict])

# PostgreSQL
adapter = PostgresAdapter(
    url: str = None,
    host: str = "localhost",
    port: int = 5432,
    database: str = None,
    user: str = "postgres",
    password: str = None,
    ssl: bool = False,
)
```

---

## Troubleshooting

### Common Errors

**"No adapter configured"**

```python
# Problem
await User.insert(name="Alice")
# Error: No adapter configured

# Solution
from pynext.db import configure_db, MemoryAdapter

adapter = MemoryAdapter()
await adapter.connect()
configure_db(adapter)  # ← You forgot this!
```

**"ValidationError: name must be str"**

```python
# Problem
await User.insert(name=123)
# Error: ValidationError: name must be str

# Solution: Pass correct types
await User.insert(name="123")  # String, not int
```

**"RecordNotFound"**

```python
# Problem
user = await User.get(9999)
# Error: RecordNotFound

# Solution: Use get_or_none for optional lookups
user = await User.get_or_none(9999)
if user is None:
    print("User not found")
```

**"UniqueViolation"**

```python
# Problem
await User.insert(email="alice@example.com")
await User.insert(email="alice@example.com")  # Duplicate!
# Error: UniqueViolation

# Solution: Check first or use upsert
existing = await User.where(User.email == email).first()
if not existing:
    await User.insert(email=email)

# Or use upsert
await User.upsert(
    {"email": "alice@example.com"},
    {"name": "Alice"}
)
```

### Performance Tips

1. **Use pagination** for large result sets:
   ```python
   # Instead of: await User.all()
   page = await User.page(page=1, per_page=100)
   ```

2. **Select only needed columns**:
   ```python
   # Instead of: await User.all()
   names = await User.select(User.name).all()
   ```

3. **Use eager loading** to avoid N+1:
   ```python
   users = await User.all().load(User.posts)
   ```

4. **Use bulk operations**:
   ```python
   # Instead of loop with single inserts
   await User.insert_many([...])
   ```

5. **Add indexes** for frequently queried columns:
   ```python
   email: str = Field(index=True)
   ```

---

## Summary

You've learned the PyNext database layer from first principles:

1. **Databases** store data persistently and support queries
2. **Tables** are defined as Python classes with type hints
3. **CRUD** operations create, read, update, and delete records
4. **Queries** filter and sort data efficiently
5. **Relationships** connect tables together
6. **Validation** ensures data quality
7. **Transactions** provide atomic operations
8. **Raw SQL** is available when needed
9. **Adapters** connect to different databases

PyNext makes database operations feel like native Python, while giving you the full power of SQL when you need it.

**Next steps:**
- [POSTGRES.md](./POSTGRES.md) - Production PostgreSQL setup
- [MIGRATIONS.md](./MIGRATIONS.md) - Schema changes and versioning
- [POOLING.md](./POOLING.md) - Connection management
- [RELIABILITY.md](./RELIABILITY.md) - Fault tolerance
- [HIGH_LOAD.md](./HIGH_LOAD.md) - Performance optimization
