# Many-to-Many Relationships

The most powerful, yet dead-simple many-to-many relationship system in Python. This guide covers everything from basic usage to advanced patterns.

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [What is Many-to-Many?](#what-is-many-to-many)
   - [The Junction Table Problem](#the-junction-table-problem)
   - [Why PyNext is Revolutionary](#why-pynext-is-revolutionary)
   
2. [SQLAlchemy vs PyNext: The Complete Comparison](#2-sqlalchemy-vs-pynext-the-complete-comparison)
   - [Basic M2M: 20 Lines vs 2 Lines](#basic-m2m-20-lines-vs-2-lines)
   - [Extra Columns: 40 Lines vs 5 Lines](#extra-columns-40-lines-vs-5-lines)
   - [Feature-by-Feature Comparison](#feature-by-feature-comparison)
   
3. [Quick Start Guide](#3-quick-start-guide)
   - [Your First M2M (2 Lines!)](#your-first-m2m-2-lines)
   - [Adding and Removing Items](#adding-and-removing-items)
   - [Bidirectional Access](#bidirectional-access)
   
4. [Junction Tables Deep Dive](#4-junction-tables-deep-dive)
   - [Auto-Created Junction Tables](#auto-created-junction-tables)
   - [Naming Conventions](#naming-conventions)
   - [Explicit Junction Tables](#explicit-junction-tables)
   - [Junction Table Factory](#junction-table-factory)
   
5. [Extra Columns on Junction](#5-extra-columns-on-junction)
   - [The `through=` Parameter](#the-through-parameter)
   - [Adding Data with `add()`](#adding-data-with-add)
   - [Accessing Junction Data](#accessing-junction-data)
   - [Updating Junction Data](#updating-junction-data)
   - [Real-World Examples](#real-world-examples)
   
6. [Bidirectional Relationships](#6-bidirectional-relationships)
   - [Using `backref=`](#using-backref)
   - [Using `back_populates=`](#using-back_populates)
   - [Automatic Sync Behavior](#automatic-sync-behavior)
   - [Understanding the Sync Mechanism](#understanding-the-sync-mechanism)
   
7. [Loading Strategies](#7-loading-strategies)
   - [lazy="select" (Default)](#lazyselect-default)
   - [lazy="selectin" (Best for Batches)](#lazyselectin-best-for-batches)
   - [lazy="subquery"](#lazysubquery)
   - [lazy="raise" (N+1 Prevention)](#lazyraise-n1-prevention)
   - [lazy="dynamic" (Query Builder)](#lazydynamic-query-builder)
   - [Choosing the Right Strategy](#choosing-the-right-strategy)
   
8. [Dynamic Relationships](#8-dynamic-relationships)
   - [When to Use Dynamic](#when-to-use-dynamic)
   - [Query Building Methods](#query-building-methods)
   - [Filtering](#filtering)
   - [Ordering](#ordering)
   - [Pagination](#pagination)
   - [Counting and Existence](#counting-and-existence)
   
9. [Collection Operations](#9-collection-operations)
   - [Adding Items](#adding-items)
   - [Removing Items](#removing-items)
   - [Bulk Operations](#bulk-operations)
   - [Checking Membership](#checking-membership)
   - [Iteration](#iteration)
   - [Indexing and Slicing](#indexing-and-slicing)
   - [Sorting](#sorting)
   
10. [Common Patterns](#10-common-patterns)
    - [Tags System](#tags-system)
    - [Permissions and Roles](#permissions-and-roles)
    - [Friends and Followers](#friends-and-followers)
    - [Categories](#categories)
    - [Course Enrollment](#course-enrollment)
    - [Wishlist/Favorites](#wishlistfavorites)
    
11. [Self-Referential Relationships](#11-self-referential-relationships)
    - [Friends Pattern](#friends-pattern)
    - [Followers Pattern](#followers-pattern)
    - [Tree Structures](#tree-structures)
    
12. [Performance Optimization](#12-performance-optimization)
    - [The N+1 Problem](#the-n1-problem)
    - [Eager Loading](#eager-loading)
    - [Batch Loading](#batch-loading)
    - [Query Optimization](#query-optimization)
    - [When to Use Dynamic](#when-to-use-dynamic-1)
    
13. [Error Handling](#13-error-handling)
    - [LazyLoadError](#lazyloaderror)
    - [Common Errors](#common-errors)
    - [Debugging Tips](#debugging-tips)
    
14. [Testing M2M Relationships](#14-testing-m2m-relationships)
    - [Unit Testing](#unit-testing)
    - [Integration Testing](#integration-testing)
    - [Mocking Strategies](#mocking-strategies)
    
15. [Migration Guide](#15-migration-guide)
    - [From SQLAlchemy](#from-sqlalchemy)
    - [From Django](#from-django)
    
16. [API Reference](#16-api-reference)
    - [many_to_many() Function](#many_to_many-function)
    - [ManyToMany Descriptor](#manytomany-descriptor)
    - [ManyToManyCollection](#manytomanycollection)
    - [DynamicManyToMany](#dynamicmanytomany)
    - [JunctionConfig](#junctionconfig)
    - [JunctionManager](#junctionmanager)

17. [New Simplifications (Phase 7.3 Enhancements)](#17-new-simplifications-phase-73-enhancements)
    - [Auto-Backref Naming](#auto-backref-naming)
    - [Backref Opt-Out](#backref-opt-out)
    - [Type-Hint Auto-Detection](#type-hint-auto-detection)
    - [Inline Extra Columns](#inline-extra-columns)
    - [Tuple Syntax for Data](#tuple-syntax-for-data)
    - [Property-Style Junction Access](#property-style-junction-access)

18. [Phase History](#18-phase-history)
    - [Phase 7.1: Bidirectional Relationships](#phase-71-bidirectional-relationships)
    - [Phase 7.2: Loading Strategies](#phase-72-loading-strategies)
    - [Phase 7.3: Many-to-Many](#phase-73-many-to-many)

---

## 1. Introduction

### What is Many-to-Many?

A many-to-many (M2M) relationship is a type of database relationship where:
- Multiple records in Table A can be associated with multiple records in Table B
- AND vice versa

**Real-world examples:**
- **Students ↔ Courses**: A student enrolls in many courses; a course has many students
- **Articles ↔ Tags**: An article has many tags; a tag is on many articles
- **Users ↔ Roles**: A user has many roles; a role belongs to many users
- **Products ↔ Categories**: A product is in many categories; a category has many products

### The Junction Table Problem

Unlike one-to-one or one-to-many relationships, M2M relationships **cannot be represented with just a foreign key**. They require a third table called a:
- **Junction table** (most common term)
- **Association table**
- **Join table**
- **Link table**
- **Bridge table**
- **Cross-reference table**

This junction table stores pairs of foreign keys:

```
students          enrollments (junction)      courses
+----+------+     +------------+----------+   +----+--------+
| id | name |     | student_id | course_id|   | id | name   |
+----+------+     +------------+----------+   +----+--------+
| 1  | John |     | 1          | 1        |   | 1  | Math   |
| 2  | Jane |     | 1          | 2        |   | 2  | Science|
+----+------+     | 2          | 1        |   +----+--------+
                  +------------+----------+
```

**This creates complexity:**
1. You must define the junction table
2. You must manage inserts/deletes to it
3. You must join through it for queries
4. If you want extra data (like `grade`), it gets even more complex

### Why PyNext is Revolutionary

PyNext eliminates this complexity entirely:

```python
# This is ALL you need:
class Student(Table):
    courses: List[Course] = many_to_many(Course, backref="students")

# Junction table? Auto-created.
# Bidirectional access? Automatic.
# Managing junction rows? Handled for you.
```

**The magic:**
1. **2 lines** instead of 20+
2. **No junction table definition** - auto-created
3. **No manual SQL** - just use Python lists
4. **Bidirectional** - `backref=` creates both sides
5. **Extra columns supported** - use `through=` when needed

---

## 2. SQLAlchemy vs PyNext: The Complete Comparison

### Basic M2M: 20 Lines vs 2 Lines

**SQLAlchemy (The Verbose Way):**

```python
from sqlalchemy import Table, Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

Base = declarative_base()

# Step 1: Define the junction table explicitly (6 lines)
student_courses = Table(
    'student_courses',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)

# Step 2: Define the Student model (6 lines)
class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    courses = relationship('Course', secondary=student_courses, 
                          back_populates='students')

# Step 3: Define the Course model (6 lines)
class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    students = relationship('Student', secondary=student_courses,
                           back_populates='courses')

# Step 4: Create engine, session, tables (4 lines)
engine = create_engine('sqlite:///school.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Total: 22+ lines before you can even use it!
```

**PyNext (The Simple Way):**

```python
from pynext.db import Table, many_to_many
from typing import List

class Student(Table):
    name: str
    courses: List["Course"] = many_to_many("Course", backref="students")

class Course(Table):
    name: str
    # students: List[Student] is auto-created via backref!

# Total: 6 lines including imports. Done!
```

**Result: 73% less code, 100% less confusion.**

### Extra Columns: 40 Lines vs 5 Lines

What if you need extra data on the junction? Like a grade for an enrollment?

**SQLAlchemy (The Nightmare):**

```python
from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# You need the "Association Object" pattern - extremely complex
class Enrollment(Base):
    __tablename__ = 'enrollments'
    student_id = Column(Integer, ForeignKey('students.id'), primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)
    grade = Column(String(2))
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    
    # Need explicit relationships to both sides
    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    
    # Direct access to enrollments
    enrollments = relationship("Enrollment", back_populates="student")
    
    # If you ALSO want direct access to courses, need association_proxy
    # This is where it gets really messy
    
class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    enrollments = relationship("Enrollment", back_populates="course")

# Usage is awkward:
enrollment = Enrollment(student=student, course=course, grade="A")
session.add(enrollment)
session.commit()

# To get courses for a student:
for enrollment in student.enrollments:
    print(f"{enrollment.course.name}: {enrollment.grade}")
```

**PyNext (The Dream):**

```python
from pynext.db import Table, many_to_many
from typing import List, Optional
from datetime import datetime

class Enrollment(Table):
    student_id: int
    course_id: int
    grade: Optional[str] = None
    enrolled_at: Optional[datetime] = None

class Student(Table):
    name: str
    courses: List["Course"] = many_to_many("Course", through=Enrollment, backref="students")

class Course(Table):
    name: str

# Usage is beautiful:
student.courses.add(course, grade="A", enrolled_at=datetime.now())

# Direct access to courses:
for course in student.courses:
    print(course.name)

# Need the grade? Get the junction:
enrollment = await student.courses.get_junction(course)
print(f"Grade: {enrollment.grade}")
```

### Feature-by-Feature Comparison

| Feature | SQLAlchemy | PyNext | Winner |
|---------|------------|--------|--------|
| **Basic M2M definition** | 20+ lines | 2 lines | PyNext by 10x |
| **Junction table** | Manual definition required | Auto-created | PyNext |
| **Bidirectional access** | Define on BOTH models | `backref=` on one | PyNext |
| **Extra columns** | Complex association pattern | Simple `through=` | PyNext |
| **Add with extra data** | Create association object | `add(item, grade="A")` | PyNext |
| **Access extra data** | Navigate through association | `get_junction()` | PyNext |
| **Type hints** | Optional, often ignored | First-class support | PyNext |
| **Learning curve** | Steep (weeks) | Flat (minutes) | PyNext |
| **Documentation needed** | Extensive | Minimal | PyNext |
| **AI friendliness** | Complex patterns confuse LLMs | Simple, explicit | PyNext |
| **Debugging** | Stack traces through ORM | Clear Python errors | PyNext |

---

## 3. Quick Start Guide

### Your First M2M (2 Lines!)

```python
from pynext.db import Table, many_to_many
from typing import List

class Article(Table):
    title: str
    tags: List["Tag"] = many_to_many("Tag", backref="articles")

class Tag(Table):
    name: str
    # articles: List[Article] is auto-created via backref!
```

That's it. You now have:
- ✅ Articles that can have many tags
- ✅ Tags that can be on many articles  
- ✅ A junction table (auto-created as `articles_tags`)
- ✅ Bidirectional access from both sides

### Adding and Removing Items

```python
# Create instances
article = Article(title="Python Tutorial")
python_tag = Tag(name="python")
tutorial_tag = Tag(name="tutorial")

# Add tags to article
article.tags.append(python_tag)
article.tags.append(tutorial_tag)

# Or add multiple at once
article.tags.extend([python_tag, tutorial_tag])

# Check what's there
print(f"Tags: {len(article.tags)}")  # Tags: 2

# Remove a tag
article.tags.remove(tutorial_tag)

# Clear all tags
article.tags.clear()
```

### Bidirectional Access

The `backref="articles"` parameter creates automatic access from both sides:

```python
# Access from Article side
article = Article(title="Python Tutorial")
article.tags.append(python_tag)

# Access from Tag side - it's there automatically!
print(python_tag.articles)  # Contains the article!

# Works both ways
python_tag.articles.append(another_article)
# Now another_article.tags contains python_tag!
```

**The sync is automatic:**
- Add to `article.tags` → appears in `tag.articles`
- Remove from `article.tags` → removed from `tag.articles`
- No manual sync needed!

---

## 4. Junction Tables Deep Dive

### Auto-Created Junction Tables

When you don't specify `through=`, PyNext creates a junction table automatically:

```python
class Student(Table):
    courses: List[Course] = many_to_many(Course)

# PyNext auto-creates a junction table with:
# - Name: "courses_students" (alphabetically sorted)
# - Columns: student_id, course_id
```

**The auto-created junction is:**
- Registered in the model registry
- Available for queries if needed
- Managed automatically on append/remove

### Naming Conventions

Junction table names follow a consistent convention:

```
{table1}_{table2}  (alphabetically sorted)
```

**Examples:**
| Model A | Model B | Junction Table Name |
|---------|---------|-------------------|
| Student | Course | `courses_students` |
| Article | Tag | `articles_tags` |
| User | Role | `roles_users` |
| Product | Category | `categories_products` |

**Why alphabetical?** So the same name is generated regardless of which model defines the relationship first.

### Explicit Junction Tables

Use `through=` when you need extra columns:

```python
class Enrollment(Table):
    """Junction table with extra data."""
    student_id: int
    course_id: int
    grade: Optional[str] = None
    enrolled_at: Optional[datetime] = None
    semester: str = ""
    credits: int = 3
    notes: str = ""

class Student(Table):
    name: str
    courses: List[Course] = many_to_many(
        Course,
        through=Enrollment,  # Use our explicit junction
        backref="students"
    )

class Course(Table):
    name: str
```

**Benefits of explicit junction:**
- Store additional data (grades, timestamps, metadata)
- Query the junction directly when needed
- Full control over column types and defaults

### Junction Table Factory

PyNext uses a `JunctionTableFactory` to manage junction tables:

```python
from pynext.db.relationships.junction import get_junction_factory

factory = get_junction_factory()

# Generate a junction name
name = factory.generate_junction_name(Student, Course)
print(name)  # "courses_students"

# Create an implicit junction
junction_class = factory.create_implicit_junction(Student, Course)
print(junction_class.__table_name__)  # "courses_students"

# Get cached junction
same_class = factory.create_implicit_junction(Student, Course)
assert junction_class is same_class  # True - cached!
```

---

## 5. Extra Columns on Junction

### The `through=` Parameter

The `through=` parameter specifies an explicit junction table model:

```python
class Enrollment(Table):
    """Explicit junction with extra columns."""
    student_id: int
    course_id: int
    
    # Extra columns!
    grade: Optional[str] = None
    enrolled_at: Optional[datetime] = None
    dropped_at: Optional[datetime] = None
    semester: str = ""
    year: int = 2024
    status: str = "active"  # active, completed, dropped

class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, through=Enrollment)
```

### Adding Data with `add()`

Use `add()` instead of `append()` to include extra data:

```python
# Simple append (no extra data)
student.courses.append(course)

# Add with extra data
student.courses.add(
    course,
    grade="A",
    enrolled_at=datetime.now(),
    semester="Fall",
    year=2024,
    status="active"
)

# Add multiple with same extra data
for course in required_courses:
    student.courses.add(course, semester="Fall", year=2024)
```

### Accessing Junction Data

Get the junction row to access extra columns:

```python
# Get junction row for specific course
enrollment = await student.courses.get_junction(math_course)

if enrollment:
    print(f"Grade: {enrollment.grade}")
    print(f"Enrolled: {enrollment.enrolled_at}")
    print(f"Semester: {enrollment.semester} {enrollment.year}")
    print(f"Status: {enrollment.status}")
else:
    print("Not enrolled in this course")
```

### Updating Junction Data

Update extra columns on the junction:

```python
# Update a single field
await student.courses.update_junction(math_course, grade="A+")

# Update multiple fields
await student.courses.update_junction(
    math_course,
    grade="A+",
    status="completed"
)
```

### Real-World Examples

**1. Course Enrollment System:**

```python
class Enrollment(Table):
    student_id: int
    course_id: int
    grade: Optional[str] = None
    enrolled_at: datetime = datetime.now()
    completed_at: Optional[datetime] = None
    attendance_rate: float = 0.0
    final_score: Optional[float] = None

class Student(Table):
    name: str
    email: str
    courses: List[Course] = many_to_many(Course, through=Enrollment, backref="students")

# Enroll with initial data
student.courses.add(math, enrolled_at=datetime.now())

# Update as course progresses
await student.courses.update_junction(math, attendance_rate=0.95)

# Complete the course
await student.courses.update_junction(
    math,
    grade="A",
    final_score=95.5,
    completed_at=datetime.now()
)

# Get transcript
for course in student.courses:
    enrollment = await student.courses.get_junction(course)
    print(f"{course.name}: {enrollment.grade} ({enrollment.final_score})")
```

**2. Team Membership with Roles:**

```python
class TeamMembership(Table):
    user_id: int
    team_id: int
    role: str = "member"  # member, admin, owner
    joined_at: datetime = datetime.now()
    invited_by: Optional[int] = None

class User(Table):
    name: str
    teams: List[Team] = many_to_many(Team, through=TeamMembership, backref="members")

class Team(Table):
    name: str

# Add user to team with role
user.teams.add(engineering, role="admin", invited_by=owner.id)

# Check role
membership = await user.teams.get_junction(engineering)
if membership.role == "admin":
    print("User is an admin!")

# Promote to owner
await user.teams.update_junction(engineering, role="owner")
```

**3. Order Line Items:**

```python
class OrderItem(Table):
    order_id: int
    product_id: int
    quantity: int = 1
    unit_price: float = 0.0
    discount: float = 0.0
    notes: str = ""

class Order(Table):
    customer_id: int
    status: str = "pending"
    products: List[Product] = many_to_many(Product, through=OrderItem)

class Product(Table):
    name: str
    price: float

# Add products to order
order.products.add(iphone, quantity=2, unit_price=999.99)
order.products.add(case, quantity=1, unit_price=49.99, discount=10.0)

# Calculate total
total = 0.0
for product in order.products:
    item = await order.products.get_junction(product)
    subtotal = item.quantity * item.unit_price * (1 - item.discount / 100)
    total += subtotal
```

---

## 6. Bidirectional Relationships

### Using `backref=`

The `backref=` parameter auto-creates the reverse relationship:

```python
class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, backref="students")
    #                                           ↑
    #                        This creates Course.students automatically!

class Course(Table):
    name: str
    # students: List[Student] is auto-created by backref!
```

**Usage:**

```python
student = Student(name="John")
math = Course(name="Math")

# Add from student side
student.courses.append(math)

# Access from course side - it's there!
assert student in math.students

# Works the other way too
physics = Course(name="Physics")
physics.students.append(student)
assert physics in student.courses
```

### Using `back_populates=`

For explicit bidirectional definition on both models:

```python
class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, back_populates="students")

class Course(Table):
    name: str
    students: List[Student] = many_to_many(Student, back_populates="courses")
```

**When to use which:**

| Scenario | Use |
|----------|-----|
| One model owns the relationship | `backref=` |
| Both models are equal peers | `back_populates=` |
| You want explicit definition | `back_populates=` |
| You want less code | `backref=` |

### Automatic Sync Behavior

When you modify one side, the other updates automatically:

```python
# Adding
student.courses.append(math)
# Now: math.students contains student ✓

# Removing
student.courses.remove(math)
# Now: math.students no longer contains student ✓

# Clearing
student.courses.clear()
# Now: all courses' students lists no longer contain student ✓

# Extending
student.courses.extend([math, physics, chemistry])
# Now: all three courses' students lists contain student ✓
```

### Understanding the Sync Mechanism

PyNext uses a `ManyToManyCollection` that syncs on mutation:

```python
# When you call:
student.courses.append(course)

# Internally it:
# 1. Adds course to student._cached_courses._items
# 2. Marks (course, {}) as pending addition for junction row
# 3. Looks up course._cached_students (if exists)
# 4. Adds student to that collection (without recursion)
```

**Loop prevention:**

Internal methods prevent infinite recursion:

```python
# These are internal - used by sync system
collection._append_without_sync(item)   # Doesn't trigger reverse sync
collection._remove_without_sync(item)   # Doesn't trigger reverse sync
```

---

## 7. Loading Strategies

### lazy="select" (Default)

Loads related items on first access with a separate SELECT query:

```python
class Student(Table):
    courses: List[Course] = many_to_many(Course, lazy="select")

# Usage
student = await Student.get(1)
# No query yet...

for course in student.courses:  # Query happens HERE
    print(course.name)
```

**Pros:**
- Simple, intuitive behavior
- No unnecessary loading

**Cons:**
- Can cause N+1 problem with loops

### lazy="selectin" (Best for Batches)

Loads all related items with SELECT WHERE id IN (...):

```python
class Student(Table):
    courses: List[Course] = many_to_many(Course, lazy="selectin")

# When loading multiple students, courses loaded efficiently:
students = await Student.select()  # Query 1: get students
for student in students:
    print(student.courses)  # Query 2: SELECT WHERE student_id IN (1,2,3...)
```

**Pros:**
- Efficient for batch loading
- Only 2 queries total

**Cons:**
- Loads all items (memory for large collections)

### lazy="subquery"

Loads with a subquery (useful for complex filters):

```python
class Student(Table):
    courses: List[Course] = many_to_many(Course, lazy="subquery")
```

**Generated SQL:**

```sql
SELECT * FROM courses WHERE id IN (
    SELECT course_id FROM enrollments WHERE student_id IN (
        SELECT id FROM students WHERE ...
    )
)
```

### lazy="raise" (N+1 Prevention)

Raises an error if accessed without eager loading:

```python
class Student(Table):
    courses: List[Course] = many_to_many(Course, lazy="raise")

student = await Student.get(1)

# This RAISES an error!
for course in student.courses:  # LazyLoadError!
    print(course.name)

# Must eager load:
students = await Student.select().options(
    selectinload("courses")
)
for student in students:
    for course in student.courses:  # Works - already loaded
        print(course.name)
```

**Use this when:**
- You want to enforce eager loading patterns
- You want to catch N+1 bugs at development time
- You have strict performance requirements

### lazy="dynamic" (Query Builder)

Returns a query builder instead of loading items:

```python
class Student(Table):
    # Could have thousands of courses over their lifetime
    all_courses: List[Course] = many_to_many(Course, lazy="dynamic")

student = await Student.get(1)

# student.all_courses is a DynamicManyToMany, NOT a list!

# Filter
active = await student.all_courses.filter(active=True)

# Order and limit
recent = await student.all_courses.order_by("-enrolled_at").limit(10)

# Count (efficient - no loading)
total = await student.all_courses.count()

# Check existence
has_math = await student.all_courses.filter(name="Math").exists()
```

### Choosing the Right Strategy

| Scenario | Strategy | Why |
|----------|----------|-----|
| Small collections, simple access | `select` | Simple, intuitive |
| Loading multiple parents | `selectin` | Efficient batch loading |
| Complex query filters | `subquery` | Better query optimization |
| Performance-critical code | `raise` | Forces explicit loading |
| Large collections | `dynamic` | Never loads all items |
| Pagination needed | `dynamic` | Built-in limit/offset |

**Decision flow:**

```
Is the collection potentially large (>100 items)?
├─ Yes → Use lazy="dynamic"
└─ No → Will you always access it?
         ├─ Yes → Use lazy="selectin"
         └─ No → Will you load multiple parents?
                 ├─ Yes → Use lazy="selectin" or lazy="raise"
                 └─ No → Use lazy="select" (default)
```

---

## 8. Dynamic Relationships

### When to Use Dynamic

Use `lazy="dynamic"` when:
- Collections can be large (100+ items)
- You need filtering/sorting on the collection
- You need pagination
- You want efficient counting without loading
- You want to build custom queries

### Query Building Methods

`DynamicManyToMany` provides a fluent query builder:

```python
class User(Table):
    purchases: List[Product] = many_to_many(Product, lazy="dynamic")

user = await User.get(1)

# user.purchases is a DynamicManyToMany with these methods:

# Filtering
user.purchases.filter(category="electronics")
user.purchases.where(active=True)  # alias for filter
user.purchases.where_in(id=[1, 2, 3])
user.purchases.where_not(archived=True)

# Ordering
user.purchases.order_by("name")
user.purchases.order_by("-price")  # descending
user.purchases.order_by("-created_at", "name")  # multiple

# Pagination
user.purchases.limit(10)
user.purchases.offset(20)
user.purchases.offset(20).limit(10)  # page 3

# Execution (all async)
await user.purchases.all()      # List of all
await user.purchases.count()    # Just the count
await user.purchases.exists()   # True/False
await user.purchases.first()    # First item or None
await user.purchases.one()      # Exactly one (raises if not)
```

### Filtering

```python
# Simple equality
electronics = await user.purchases.filter(category="electronics")

# Multiple conditions (AND)
expensive_electronics = await user.purchases.filter(
    category="electronics",
    price_gte=1000
)

# IN clause
specific = await user.purchases.where_in(id=[1, 2, 3, 4, 5])

# NOT
not_archived = await user.purchases.where_not(archived=True)

# Chaining (all are AND)
result = await (
    user.purchases
    .filter(category="electronics")
    .filter(active=True)
    .where_not(out_of_stock=True)
)
```

### Ordering

```python
# Ascending (default)
by_name = await user.purchases.order_by("name")

# Descending (prefix with -)
newest = await user.purchases.order_by("-created_at")

# Multiple fields
sorted_purchases = await user.purchases.order_by("-created_at", "name")
```

### Pagination

```python
# Limit
top_10 = await user.purchases.limit(10)

# Offset + Limit (pagination)
page_size = 20

# Page 1
page1 = await user.purchases.order_by("-created_at").limit(page_size)

# Page 2
page2 = await user.purchases.order_by("-created_at").offset(20).limit(page_size)

# Page 3
page3 = await user.purchases.order_by("-created_at").offset(40).limit(page_size)
```

### Counting and Existence

```python
# Count - efficient COUNT(*) query
total = await user.purchases.count()
print(f"Total purchases: {total}")

# Filtered count
electronics_count = await user.purchases.filter(category="electronics").count()

# Existence check - even more efficient
has_purchases = await user.purchases.exists()
if has_purchases:
    print("User has made purchases")

# Filtered existence
has_expensive = await user.purchases.filter(price_gte=1000).exists()
```

---

## 9. Collection Operations

### Adding Items

```python
# Single item
student.courses.append(math)

# With extra junction data
student.courses.add(math, grade="A", enrolled_at=datetime.now())

# Multiple items
student.courses.extend([math, physics, chemistry])

# Insert at position
student.courses.insert(0, priority_course)  # At beginning
student.courses.insert(2, course)  # At index 2
```

### Removing Items

```python
# Remove specific item
student.courses.remove(math)  # Raises ValueError if not found

# Remove without error if missing
student.courses.discard(math)  # No error if not found

# Remove by index
dropped = student.courses.pop()     # Remove and return last
dropped = student.courses.pop(0)    # Remove and return first
dropped = student.courses.pop(2)    # Remove and return index 2

# Clear all
student.courses.clear()

# Delete by slice
del student.courses[0]      # Delete first
del student.courses[-1]     # Delete last
del student.courses[1:3]    # Delete range
```

### Bulk Operations

```python
# Extend with multiple
student.courses.extend([math, physics, chemistry])

# Replace all
student.courses = [new_math, new_physics]

# Set by slice
student.courses[1:3] = [replacement1, replacement2]

# Clear and add (efficient replacement)
student.courses.clear()
student.courses.extend(new_courses)
```

### Checking Membership

```python
# Check if item is in collection
if math in student.courses:
    print("Enrolled in math!")

# Check if item is NOT in collection
if physics not in student.courses:
    print("Not enrolled in physics")

# Check if empty
if not student.courses:
    print("Not enrolled in any courses")

# Check if non-empty
if student.courses:
    print(f"Enrolled in {len(student.courses)} courses")
```

### Iteration

```python
# Standard iteration
for course in student.courses:
    print(course.name)

# With index
for i, course in enumerate(student.courses):
    print(f"{i + 1}. {course.name}")

# Reversed
for course in reversed(student.courses):
    print(course.name)

# List comprehension
names = [course.name for course in student.courses]

# Filter comprehension
hard_courses = [c for c in student.courses if c.difficulty > 8]
```

### Indexing and Slicing

```python
# Get by index
first = student.courses[0]
last = student.courses[-1]
third = student.courses[2]

# Slice
first_three = student.courses[:3]
last_two = student.courses[-2:]
middle = student.courses[1:4]
every_other = student.courses[::2]

# Set by index
student.courses[0] = new_course

# Set by slice
student.courses[1:3] = [course_a, course_b]
```

### Sorting

```python
# Sort in place (requires __lt__ or key)
student.courses.sort()

# Sort with key function
student.courses.sort(key=lambda c: c.name)
student.courses.sort(key=lambda c: c.difficulty)

# Sort descending
student.courses.sort(reverse=True)
student.courses.sort(key=lambda c: c.name, reverse=True)

# Reverse in place
student.courses.reverse()

# Get sorted copy (without modifying)
sorted_courses = sorted(student.courses, key=lambda c: c.name)
```

---

## 10. Common Patterns

### Tags System

```python
class Tag(Table):
    name: str
    slug: str
    color: str = "#808080"

class Article(Table):
    title: str
    content: str
    tags: List[Tag] = many_to_many(Tag, backref="articles")

# Usage
article = Article(title="Python Tutorial", content="...")
python = Tag(name="Python", slug="python", color="#3776AB")
tutorial = Tag(name="Tutorial", slug="tutorial", color="#4CAF50")

# Add tags
article.tags.extend([python, tutorial])

# Find articles by tag
python_articles = python.articles  # All articles tagged with python

# Check if tagged
if python in article.tags:
    print("This is a Python article")

# Remove tag
article.tags.remove(obsolete_tag)
```

### Permissions and Roles

```python
class Permission(Table):
    name: str  # e.g., "users:read", "users:write", "admin:*"
    description: str

class Role(Table):
    name: str
    permissions: List[Permission] = many_to_many(Permission, backref="roles")

class User(Table):
    name: str
    email: str
    roles: List[Role] = many_to_many(Role, backref="users")

# Setup
admin_role = Role(name="admin")
admin_role.permissions.extend([read_perm, write_perm, delete_perm])

editor_role = Role(name="editor")
editor_role.permissions.extend([read_perm, write_perm])

# Assign roles
user.roles.append(editor_role)

# Check permissions
def has_permission(user: User, perm_name: str) -> bool:
    for role in user.roles:
        for perm in role.permissions:
            if perm.name == perm_name or perm.name.endswith(":*"):
                return True
    return False

if has_permission(user, "users:write"):
    print("Can write users!")
```

### Friends and Followers

```python
# Symmetric friendship (both must add each other)
class User(Table):
    name: str
    friends: List["User"] = many_to_many("User")

# Add friend (need both to add)
alice.friends.append(bob)
bob.friends.append(alice)  # Now they're mutual friends

# Asymmetric following (Twitter-style)
class User(Table):
    name: str
    following: List["User"] = many_to_many("User", backref="followers")

# Follow someone
fan.following.append(celebrity)

# Check followers
for follower in celebrity.followers:
    print(f"{follower.name} follows {celebrity.name}")

# Check if following
if celebrity in fan.following:
    print("Fan follows celebrity")
```

### Categories

```python
class Category(Table):
    name: str
    parent_id: Optional[int] = None  # For hierarchy

class Product(Table):
    name: str
    price: float
    categories: List[Category] = many_to_many(Category, backref="products")

# Multi-category product
laptop = Product(name="MacBook Pro", price=2499.99)
laptop.categories.extend([
    electronics,
    computers,
    apple_products,
    premium_items
])

# Find products in category
for product in electronics.products:
    print(f"{product.name}: ${product.price}")
```

### Course Enrollment

```python
class Enrollment(Table):
    student_id: int
    course_id: int
    grade: Optional[str] = None
    enrolled_at: datetime = datetime.now()
    status: str = "active"

class Student(Table):
    name: str
    email: str
    courses: List[Course] = many_to_many(
        Course,
        through=Enrollment,
        backref="students"
    )

class Course(Table):
    name: str
    credits: int
    instructor: str

# Enroll student
student.courses.add(
    math_101,
    enrolled_at=datetime.now(),
    status="active"
)

# Drop course
student.courses.remove(math_101)

# Update grade
await student.courses.update_junction(math_101, grade="A")

# Get transcript
for course in student.courses:
    enrollment = await student.courses.get_junction(course)
    print(f"{course.name}: {enrollment.grade or 'In Progress'}")
```

### Wishlist/Favorites

```python
class WishlistItem(Table):
    user_id: int
    product_id: int
    added_at: datetime = datetime.now()
    priority: int = 0  # Higher = more wanted
    notes: str = ""

class User(Table):
    name: str
    wishlist: List[Product] = many_to_many(
        Product,
        through=WishlistItem,
        backref="wishlisted_by"
    )

class Product(Table):
    name: str
    price: float

# Add to wishlist with priority
user.wishlist.add(
    iphone,
    priority=10,
    notes="Want the Pro Max version"
)

# Get wishlist sorted by priority
items = []
for product in user.wishlist:
    item = await user.wishlist.get_junction(product)
    items.append((product, item.priority))

sorted_wishlist = sorted(items, key=lambda x: -x[1])  # High priority first
```

---

## 11. Self-Referential Relationships

### Friends Pattern

```python
class Person(Table):
    name: str
    # Self-referential M2M
    friends: List["Person"] = many_to_many("Person")

alice = Person(name="Alice")
bob = Person(name="Bob")
carol = Person(name="Carol")

# Add friends
alice.friends.append(bob)
alice.friends.append(carol)

# Check friends
print(f"Alice's friends: {[f.name for f in alice.friends]}")
# Output: Alice's friends: ['Bob', 'Carol']

# Note: This is one-way! Bob doesn't automatically have Alice as friend
# For mutual friendship, add both ways:
bob.friends.append(alice)
```

### Followers Pattern

```python
class User(Table):
    username: str
    # Following/followers pattern
    following: List["User"] = many_to_many("User", backref="followers")

john = User(username="john")
celebrity = User(username="celebrity")

# John follows celebrity
john.following.append(celebrity)

# Check
assert celebrity in john.following      # John follows celebrity
assert john in celebrity.followers      # Celebrity has John as follower
assert celebrity not in john.followers  # Celebrity doesn't follow John
```

### Tree Structures

```python
class Category(Table):
    name: str
    # Many-to-many for flexible trees (allows multiple parents)
    parents: List["Category"] = many_to_many("Category", backref="children")

# Create hierarchy
electronics = Category(name="Electronics")
computers = Category(name="Computers")
laptops = Category(name="Laptops")
gaming = Category(name="Gaming")
gaming_laptops = Category(name="Gaming Laptops")

# Gaming Laptops has multiple parents!
gaming_laptops.parents.extend([laptops, gaming])

# Access children
for child in laptops.children:
    print(child.name)  # Gaming Laptops
```

---

## 12. Performance Optimization

### The N+1 Problem

The N+1 problem occurs when you load N items and then make a separate query for each one's relationships:

```python
# BAD: N+1 queries!
students = await Student.select()  # 1 query
for student in students:           # N more queries!
    print(student.courses)         # Each access = 1 query

# If you have 100 students, that's 101 queries!
```

### Eager Loading

Use `selectinload()` to load relationships efficiently:

```python
from pynext.db import selectinload

# GOOD: Only 2 queries total
students = await Student.select().options(
    selectinload("courses")
)
for student in students:
    print(student.courses)  # Already loaded!
```

### Batch Loading

For loading multiple related collections:

```python
from pynext.db import selectinload

students = await Student.select().options(
    selectinload("courses"),
    selectinload("clubs"),
    selectinload("grades"),
)

# Only 4 queries total:
# 1. SELECT * FROM students
# 2. SELECT * FROM courses WHERE id IN (...)
# 3. SELECT * FROM clubs WHERE id IN (...)
# 4. SELECT * FROM grades WHERE student_id IN (...)
```

### Query Optimization

For complex scenarios:

```python
# Use lazy="raise" to catch N+1 bugs
class Student(Table):
    courses: List[Course] = many_to_many(Course, lazy="raise")

# Now this will ERROR, forcing you to fix it:
students = await Student.select()
for student in students:
    print(student.courses)  # LazyLoadError! Must eager load!
```

### When to Use Dynamic

For large collections, use `lazy="dynamic"` to never load all items:

```python
class User(Table):
    # Could have thousands of purchases
    purchases: List[Product] = many_to_many(Product, lazy="dynamic")

# Efficient - never loads all
count = await user.purchases.count()  # SELECT COUNT(*)
recent = await user.purchases.order_by("-date").limit(10)  # Only 10 items
```

---

## 13. Error Handling

### LazyLoadError

Raised when accessing a relationship with `lazy="raise"` that wasn't eager loaded:

```python
from pynext.db import LazyLoadError

class Student(Table):
    courses: List[Course] = many_to_many(Course, lazy="raise")

try:
    student = await Student.get(1)
    courses = student.courses  # Raises!
except LazyLoadError as e:
    print(f"Relationship: {e.relationship}")  # "courses"
    print(f"Model: {e.model}")                 # "Student"
    print("Must use options(selectinload('courses'))")
```

### Common Errors

**ValueError on remove:**
```python
try:
    student.courses.remove(course_not_enrolled)
except ValueError:
    print("Student not enrolled in this course")
```

**IndexError on access:**
```python
try:
    first = student.courses[0]
except IndexError:
    print("No courses enrolled")
```

### Debugging Tips

**1. Print collection state:**
```python
print(f"Collection: {student.courses}")
print(f"Items: {student.courses._items}")
print(f"Pending adds: {student.courses.get_pending_additions()}")
print(f"Pending removes: {student.courses.get_pending_removals()}")
```

**2. Check if loaded:**
```python
if student._cached_courses is not None:
    print("Courses are loaded")
else:
    print("Courses not yet loaded")
```

**3. Check relationship descriptor:**
```python
descriptor = Student.__dict__["courses"]
print(f"Lazy: {descriptor.lazy}")
print(f"Backref: {descriptor.backref}")
print(f"Through: {descriptor.through}")
```

---

## 14. Testing M2M Relationships

### Unit Testing

```python
import pytest
from pynext.db import Table, many_to_many, reset_backref_registry
from pynext.db.relationships.junction import reset_junction_factory

@pytest.fixture(autouse=True)
def clean_state():
    """Reset state before each test."""
    reset_backref_registry()
    reset_junction_factory()
    yield
    reset_backref_registry()
    reset_junction_factory()


class TestTagging:
    def test_add_tag(self, clean_state):
        class Tag(Table):
            name: str = ""
        
        class Article(Table):
            title: str = ""
            tags: List[Tag] = many_to_many(Tag)
        
        article = Article(title="Test")
        tag = Tag(name="python")
        
        article.tags.append(tag)
        
        assert tag in article.tags
        assert len(article.tags) == 1
    
    def test_remove_tag(self, clean_state):
        class Tag(Table):
            name: str = ""
        
        class Article(Table):
            title: str = ""
            tags: List[Tag] = many_to_many(Tag)
        
        article = Article(title="Test")
        tag = Tag(name="python")
        
        article.tags.append(tag)
        article.tags.remove(tag)
        
        assert tag not in article.tags
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_m2m_with_database(clean_state, db_adapter):
    """Test M2M with actual database."""
    configure_db(db_adapter)
    
    # Create and save
    student = await Student.insert(name="John")
    course = await Course.insert(name="Math")
    
    # Add relationship
    student.courses.append(course)
    await student.courses.sync_junction_rows()
    
    # Reload and verify
    loaded = await Student.get(student.id)
    # ... verify courses are loaded
```

### Mocking Strategies

```python
from unittest.mock import MagicMock, AsyncMock

def test_with_mock_collection():
    student = Student(name="John")
    
    # Create mock collection
    mock_collection = MagicMock()
    mock_collection.__contains__ = MagicMock(return_value=True)
    mock_collection.__len__ = MagicMock(return_value=5)
    
    student._cached_courses = mock_collection
    
    assert len(student.courses) == 5
```

---

## 15. Migration Guide

### From SQLAlchemy

**SQLAlchemy:**
```python
# Association table
student_courses = Table('student_courses', Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id')),
    Column('course_id', Integer, ForeignKey('courses.id'))
)

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    courses = relationship('Course', secondary=student_courses,
                          back_populates='students')

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    students = relationship('Student', secondary=student_courses,
                           back_populates='courses')
```

**PyNext:**
```python
class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, backref="students")

class Course(Table):
    name: str
```

**Migration steps:**
1. Remove the association table definition
2. Replace `relationship()` with `many_to_many()`
3. Use `backref=` instead of defining both sides
4. Remove `__tablename__` (auto-generated)
5. Use type hints instead of `Column()`

### From Django

**Django:**
```python
class Student(models.Model):
    name = models.CharField(max_length=100)
    courses = models.ManyToManyField('Course', related_name='students')

class Course(models.Model):
    name = models.CharField(max_length=100)
```

**PyNext:**
```python
class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, backref="students")

class Course(Table):
    name: str
```

**Migration steps:**
1. Replace `ManyToManyField` with `many_to_many()`
2. Replace `related_name=` with `backref=`
3. Use type hints

---

## 16. API Reference

### many_to_many() Function

```python
def many_to_many(
    model: Union[Type[Table], str],
    through: Optional[Union[Type[Table], str]] = None,
    backref: Optional[str] = None,
    back_populates: Optional[str] = None,
    lazy: str = "select",
) -> ManyToMany:
    """
    Define a many-to-many relationship.
    
    Args:
        model: Target model class or string name for forward reference.
        through: Junction table model. If None, auto-created.
        backref: Name for auto-created reverse relationship.
        back_populates: Name of existing reverse relationship to sync.
        lazy: Loading strategy. One of:
            - "select": Load on first access (default)
            - "selectin": Load with SELECT WHERE id IN (...)
            - "subquery": Load with subquery
            - "raise": Raise error if not eager loaded
            - "dynamic": Return query builder instead of loading
    
    Returns:
        ManyToMany descriptor.
    
    Examples:
        # Simple
        tags: List[Tag] = many_to_many(Tag)
        
        # With backref
        tags: List[Tag] = many_to_many(Tag, backref="articles")
        
        # With explicit junction
        courses: List[Course] = many_to_many(Course, through=Enrollment)
        
        # With loading strategy
        courses: List[Course] = many_to_many(Course, lazy="selectin")
    """
```

### ManyToMany Descriptor

```python
class ManyToMany(Generic[T]):
    """
    Descriptor for many-to-many relationships.
    
    Attributes:
        rel_name: str - Relationship name (e.g., "courses")
        _model: Type[Table] | str - Target model
        through: Type[Table] | str | None - Junction table
        backref: str | None - Auto-created reverse relationship name
        back_populates: str | None - Existing reverse relationship name
        lazy: str - Loading strategy
    
    Class access:
        Student.courses  # Returns ManyToMany descriptor
    
    Instance access:
        student.courses  # Returns ManyToManyCollection
    """
```

### ManyToManyCollection

```python
class ManyToManyCollection(MutableSequence, Generic[T]):
    """
    Collection for managing M2M relationships.
    
    Properties:
        owner: Table - The instance owning this collection
        attr_name: str - Attribute name on owner
        config: JunctionConfig - Junction table configuration
        has_pending_changes: bool - Whether there are unsaved changes
    
    Methods - Adding:
        append(item) -> None
        add(item, **extra) -> None  # With junction data
        extend(items) -> None
        insert(index, item) -> None
    
    Methods - Removing:
        remove(item) -> None  # Raises ValueError if not found
        discard(item) -> None  # No error if not found
        pop(index=-1) -> T
        clear() -> None
    
    Methods - Access:
        __getitem__(index) -> T
        __getitem__(slice) -> List[T]
        __contains__(item) -> bool
        __len__() -> int
        __iter__() -> Iterator[T]
        index(item) -> int
        count(item) -> int
    
    Methods - Junction:
        await get_junction(item) -> Table | None
        await update_junction(item, **updates) -> Table | None
        await sync_junction_rows() -> None
    
    Methods - Conversion:
        to_list() -> List[T]
        copy() -> List[T]
    
    Methods - Sorting:
        sort(key=None, reverse=False) -> None
        reverse() -> None
    
    Internal Methods (used by sync system):
        _append_without_sync(item) -> None
        _remove_without_sync(item) -> None
        _set_items_without_sync(items) -> None
    """
```

### DynamicManyToMany

```python
class DynamicManyToMany(Generic[T]):
    """
    Query builder for dynamic M2M relationships.
    
    Returned when lazy="dynamic".
    
    Methods - Query Building (return new DynamicManyToMany):
        filter(**kwargs) -> DynamicManyToMany
        where(**kwargs) -> DynamicManyToMany  # Alias for filter
        where_in(**kwargs) -> DynamicManyToMany
        where_not(**kwargs) -> DynamicManyToMany
        order_by(*fields) -> DynamicManyToMany
        limit(n) -> DynamicManyToMany
        offset(n) -> DynamicManyToMany
    
    Methods - Execution (async):
        await all() -> List[T]
        await count() -> int
        await exists() -> bool
        await first() -> T | None
        await one() -> T  # Raises if not exactly one
    
    Examples:
        # Get all
        items = await user.purchases.all()
        
        # Filtered
        electronics = await user.purchases.filter(category="electronics")
        
        # Paginated
        page = await user.purchases.order_by("-date").offset(20).limit(10)
        
        # Count
        total = await user.purchases.count()
    """
```

### JunctionConfig

```python
@dataclass
class JunctionConfig:
    """
    Configuration for a junction table.
    
    Attributes:
        name: str - Junction table name
        source_model: Type[Table] | str - Source model
        target_model: Type[Table] | str - Target model
        source_fk: str - Source foreign key column name
        target_fk: str - Target foreign key column name
        through_model: Type[Table] | str | None - Explicit junction model
        source_attr: str - Attribute name on source
        target_attr: str - Attribute name on target
    
    Properties:
        is_explicit: bool - Whether using explicit through model
    
    Methods:
        to_dict() -> dict
    """
```

### JunctionManager

```python
class JunctionManager:
    """
    Manages junction table rows.
    
    Methods (all async):
        await create_row(source, target, **extra) -> Table
        await delete_row(source, target) -> bool
        await get_row(source, target) -> Table | None
        await exists(source, target) -> bool
        await get_all_for_source(source) -> List[Table]
        await get_all_for_target(target) -> List[Table]
        await delete_all_for_source(source) -> int
        await delete_all_for_target(target) -> int
        await update_row(source, target, **updates) -> Table | None
    """
```

---

## Summary

PyNext's many-to-many relationships are:

1. **Simple**: 2 lines vs SQLAlchemy's 20+
2. **Automatic**: Junction tables created for you
3. **Powerful**: Extra columns, loading strategies, dynamic queries
4. **Bidirectional**: `backref=` syncs both sides
5. **Type-safe**: Full type hints and IDE support
6. **Performant**: Multiple loading strategies for any use case
7. **AI-Friendly**: Clear, explicit, easy to understand

```python
# The complete M2M experience in PyNext:

class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, backref="students")

# That's it. Everything else just works:
student.courses.append(course)    # Junction row created
course.students                   # Bidirectional access
student.courses.remove(course)    # Junction row deleted
```

**Welcome to the future of Python ORMs.**

---

## 17. New Simplifications (Phase 7.3 Enhancements)

These enhancements make M2M relationships even simpler than before.

### Auto-Backref Naming

**Before:** You had to specify the backref name manually.

```python
# Old way - explicit backref required
class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, backref="students")
```

**After:** Backref is auto-generated from the class name.

```python
# New way - backref auto-generated as "students" (Student → students)
class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course)  # backref="students" implied!
```

**How it works:**
- `Student` class → `"students"` backref (lowercase + "s")
- `ShoppingCart` → `"shoppingcarts"`
- `Person` → `"persons"` (simple pluralization)

For complex pluralization, use explicit backref:

```python
courses: List[Course] = many_to_many(Course, backref="people")  # Custom name
```

### Backref Opt-Out

**New feature:** Explicitly disable backref with `backref=False`.

```python
# One-way relationship - no reverse relationship created
class Logger(Table):
    name: str
    # Users can see their logs, but Log doesn't need to link back
    logs: List[Log] = many_to_many(Log, backref=False)

# Log has no "loggers" attribute
```

**When to use `backref=False`:**
- One-way relationships where reverse isn't needed
- Performance optimization (less memory/sync overhead)
- Cleaner API when reverse doesn't make sense

**Backref behavior summary:**
| Value | Behavior |
|-------|----------|
| `None` (default) | Auto-generate from class name |
| `"name"` | Use provided name |
| `False` | Explicitly disable (no reverse) |

### Type-Hint Auto-Detection

**New feature:** Bare `List[Model]` type hints are auto-detected as M2M.

```python
# Simplest possible M2M definition!
class Student(Table):
    name: str
    courses: List[Course]  # Auto-detected as M2M! No many_to_many() needed!

# Equivalent to:
# courses: List[Course] = many_to_many(Course)
```

**Detection logic:**
1. Field is `List[SomeTable]`
2. No explicit `many_to_many()` or `has_many()` assigned
3. The inner type is a Table subclass
4. → Automatically create as M2M with auto-backref

**When NOT auto-detected:**
- `List[str]`, `List[int]` - primitives
- Explicit `has_many(...)` - stays as has_many
- Explicit `many_to_many(...)` - uses provided config

### Inline Extra Columns

**New feature:** Define junction columns inline with `extra={}`.

**Before:** Needed separate junction model.

```python
# Old way - separate model required
class Enrollment(Table):
    student_id: int
    course_id: int
    grade: Optional[str]
    enrolled_at: datetime

class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, through=Enrollment)
```

**After:** Define inline with `extra=` parameter.

```python
# New way - inline definition!
class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, extra={
        "grade": Optional[str],
        "enrolled_at": datetime,
    })
```

**Benefits:**
- No separate model file needed
- Junction columns defined right where the relationship is
- Still supports all junction operations

**When to still use `through=`:**
- Complex junction with methods
- Shared junction across multiple M2M
- Need custom table name

### Tuple Syntax for Data

**New feature:** Add junction data using tuple syntax.

```python
# Method 1: add() with kwargs (existing)
student.courses.add(math, grade="A", enrolled_at=now)

# Method 2: append() with tuple (new!)
student.courses.append((math, {"grade": "A", "enrolled_at": now}))

# Method 3: extend() with tuples (new!)
student.courses.extend([
    (math, {"grade": "A"}),
    (science, {"grade": "B+"}),
    (english, {"grade": "A-"}),
])
```

**Mixed syntax also works:**

```python
student.courses.extend([
    biology,  # Simple add, no extra data
    (chemistry, {"grade": "A"}),  # With data
    physics,  # Simple add
])
```

### Property-Style Junction Access

**New feature:** Access junction rows using `collection[item]` syntax.

```python
# Get junction row for a specific relationship
enrollment = student.courses[math_course]

# Access extra columns
print(enrollment.grade)  # "A"
print(enrollment.enrolled_at)  # datetime

# Modify and save
enrollment.grade = "A+"
await enrollment.save()
```

**Note:** This returns cached junction data. For guaranteed database access, use:

```python
enrollment = await student.courses.get_junction(math_course)
```

---

## 18. Phase History

PyNext's relationship system was built in phases:

### Phase 7.1: Bidirectional Relationships

**Features introduced:**
- `backref=` parameter for auto-created reverse relationships
- `back_populates=` for explicit bidirectional linking
- `SyncedList` for automatic sync on mutations
- Backref registry for deferred resolution

**Key files:**
- `pynext/db/relationships/backref.py`
- `pynext/db/relationships/collections.py`

**Example:**
```python
class User(Table):
    posts: List[Post] = has_many(Post, backref="author")

# Automatic sync:
user.posts.append(post)  # Sets post.author = user
post.author = other      # Updates user.posts
```

### Phase 7.2: Loading Strategies

**Features introduced:**
- `lazy=` parameter on all relationships
- `selectinload()`, `joinedload()`, `subqueryload()`, `raiseload()`
- `LazyLoadError` for N+1 prevention
- `DynamicRelationship` for query building
- `.options()` method for query-time overrides

**Key files:**
- `pynext/db/relationships/loading.py`
- `pynext/db/relationships/options.py`
- `pynext/db/relationships/dynamic.py`

**Example:**
```python
class Author(Table):
    books: List[Book] = has_many(Book, lazy="selectin")

# N+1 prevention:
class StrictModel(Table):
    items: List[Item] = has_many(Item, lazy="raise")

# Query-time override:
authors = await Author.select().options(
    selectinload(Author.books)
).all()
```

### Phase 7.3: Many-to-Many

**Features introduced:**
- `many_to_many()` function
- `through=` for explicit junction tables
- `ManyToManyCollection` for collection operations
- `JunctionConfig` and `JunctionManager`
- `AssociationProxy` for direct access
- `DynamicManyToMany` for query building
- All loading strategies for M2M
- Auto-backref naming
- `backref=False` opt-out
- Type-hint auto-detection
- `extra={}` inline columns
- Tuple syntax for data

**Key files:**
- `pynext/db/relationships/junction.py`
- `pynext/db/relationships/m2m_collection.py`
- `pynext/db/relationships/m2m_dynamic.py`
- `pynext/db/relationships/proxy.py`

**Example:**
```python
# Zero-config M2M (Phase 7.3 final form):
class Student(Table):
    name: str
    courses: List[Course]  # Auto M2M, auto backref!

# With inline extra columns:
class Student(Table):
    name: str
    courses: List[Course] = many_to_many(Course, extra={
        "grade": Optional[str]
    })

# Adding with data:
student.courses.append((math, {"grade": "A"}))
```

---

## Complete Simplification Summary

| Feature | SQLAlchemy | PyNext 7.3 Original | PyNext 7.3 Enhanced |
|---------|------------|---------------------|---------------------|
| Basic M2M | 20+ lines | 2 lines | **1 line** (`List[Model]`) |
| Backref | Both sides required | `backref="x"` | **Auto-generated** |
| No backref | Complex | Not easy | **`backref=False`** |
| Extra columns | 40+ lines | `through=Model` | **`extra={...}`** |
| Add with data | Manual association | `add(item, **kw)` | **`append((item, data))`** |
| Access junction | Navigate association | `get_junction()` | **`collection[item]`** |

**PyNext: Making M2M relationships stupid simple since Phase 7.3.**
