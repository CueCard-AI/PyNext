# Association Proxy

Access attributes through relationships with dead-simple, Pythonic syntax.

---

## Table of Contents

1. [Why Association Proxy?](#why-association-proxy)
2. [What is Association Proxy?](#what-is-association-proxy)
3. [When to Use Association Proxy](#when-to-use-association-proxy)
4. [How It Works Internally](#how-it-works-internally)
5. [Who Should Use This](#who-should-use-this)
6. [Complete API Reference](#complete-api-reference)
7. [Real-World Examples](#real-world-examples)
8. [SQLAlchemy vs PyNext Deep Dive](#sqlalchemy-vs-pynext-deep-dive)
9. [Decision Guide](#decision-guide)
10. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
11. [Performance Deep Dive](#performance-deep-dive)
12. [Testing Your Proxies](#testing-your-proxies)
13. [Troubleshooting](#troubleshooting)

---

## Why Association Proxy?

### The Core Problem: Relationship Navigation is Tedious

When you have related models, accessing nested attributes requires verbose, repetitive code:

```python
# Your typical e-commerce setup
class Product(Table):
    id: int
    name: str
    product_tags: List[ProductTag] = has_many(ProductTag)

class ProductTag(Table):
    id: int
    product_id: int
    tag_id: int
    tag: Tag = belongs_to(Tag, "tag_id")

class Tag(Table):
    id: int
    name: str
    color: str
```

**Without association_proxy**, getting tag names is painful:

```python
# The hard way - manual navigation every single time
product = await Product.find(1)

# Option 1: Explicit loop (verbose)
tag_names = []
for product_tag in product.product_tags:
    if product_tag.tag:
        tag_names.append(product_tag.tag.name)

# Option 2: List comprehension (still awkward)
tag_names = [pt.tag.name for pt in product.product_tags if pt.tag]

# Option 3: Nested access in templates (ugly)
{% for pt in product.product_tags %}
    <span>{{ pt.tag.name }}</span>
{% endfor %}
```

### The Problems with Manual Navigation

| Problem | Impact |
|---------|--------|
| **Repetitive code** | Same navigation logic scattered everywhere |
| **Error-prone** | Forget to check for None? NullPointerException |
| **Hard to read** | `pt.tag.name` vs `product.tag_names` |
| **Not reusable** | Can't easily pass around "tag names" as a concept |
| **Breaks encapsulation** | Templates know about junction tables |
| **Difficult to change** | Rename `ProductTag`? Update 50 files |

### The Solution: Declarative Access

```python
class Product(Table):
    product_tags: List[ProductTag] = has_many(ProductTag)
    
    # Declare once, use everywhere
    tag_names: List[str] = association_proxy("product_tags", "tag.name")
    tag_colors: List[str] = association_proxy("product_tags", "tag.color")
    tags: List[Tag] = association_proxy("product_tags", "tag")

# Now everywhere in your code:
product.tag_names   # ["electronics", "sale", "featured"]
product.tag_colors  # ["blue", "red", "gold"]
product.tags        # [Tag(...), Tag(...), Tag(...)]

# In templates:
{% for name in product.tag_names %}
    <span>{{ name }}</span>
{% endfor %}
```

**One declaration replaces hundreds of navigation statements.**

---

## What is Association Proxy?

### Definition

`association_proxy` is a **descriptor** that creates a virtual attribute on your model. This attribute:

1. **Traverses** a relationship (like `has_many` or `belongs_to`)
2. **Extracts** a specific attribute from the related objects
3. **Returns** either a single value (scalar) or a collection

Think of it as a **shortcut** or **lens** that focuses on specific data through your relationships.

### Visual Representation

```
                    association_proxy("product_tags", "tag.name")
                    ================================================
                                          |
Product ──has_many──> [ProductTag] ──belongs_to──> Tag ──.name──> "electronics"
                                                            ──> "sale"
                                                            ──> "featured"
                    ================================================
                                          |
                              Returns: ["electronics", "sale", "featured"]
```

### The Three Types of Proxy

#### 1. Collection Proxy (Most Common)

When the source relationship is `has_many` or `many_to_many`, returns a list:

```python
class User(Table):
    enrollments: List[Enrollment] = has_many(Enrollment)
    
    # Returns List[str]
    course_names: List[str] = association_proxy("enrollments", "course.name")

user.course_names  # ["Math", "Physics", "Chemistry"]
```

#### 2. Scalar Proxy

When the source relationship is `belongs_to` or `has_one`, returns a single value:

```python
class Post(Table):
    author: User = belongs_to(User, "author_id")
    
    # Returns str (not List[str]!)
    author_name: str = association_proxy("author", "name")

post.author_name  # "Alice" (not ["Alice"])
```

#### 3. Object Proxy

When you want the actual related objects, not just an attribute:

```python
class Product(Table):
    product_tags: List[ProductTag] = has_many(ProductTag)
    
    # Returns List[Tag] - the actual objects
    tags: List[Tag] = association_proxy("product_tags", "tag")

product.tags  # [Tag(id=1, name="sale"), Tag(id=2, name="new")]
```

---

## When to Use Association Proxy

### Perfect Use Cases

#### ✅ Use Case 1: Simplifying Many-to-Many Access

**The Problem:**
```python
# Junction table makes access verbose
class Student(Table):
    enrollments: List[Enrollment] = has_many(Enrollment)

# Getting course names is tedious
names = [e.course.name for e in student.enrollments if e.course]
```

**The Solution:**
```python
class Student(Table):
    enrollments: List[Enrollment] = has_many(Enrollment)
    course_names: List[str] = association_proxy("enrollments", "course.name")

# Clean and simple
names = student.course_names
```

#### ✅ Use Case 2: Template Simplification

**The Problem:**
```python
<!-- Ugly template code -->
{% for enrollment in student.enrollments %}
    {% if enrollment.course %}
        <span>{{ enrollment.course.name }}</span>
    {% endif %}
{% endfor %}
```

**The Solution:**
```python
<!-- Clean template code -->
{% for name in student.course_names %}
    <span>{{ name }}</span>
{% endfor %}
```

#### ✅ Use Case 3: API Response Building

**The Problem:**
```python
def get_product(product_id: int):
    product = await Product.find(product_id)
    return {
        "id": product.id,
        "name": product.name,
        "tags": [pt.tag.name for pt in product.product_tags if pt.tag],  # Ugly
    }
```

**The Solution:**
```python
def get_product(product_id: int):
    product = await Product.find(product_id)
    return {
        "id": product.id,
        "name": product.name,
        "tags": product.tag_names,  # Clean
    }
```

#### ✅ Use Case 4: Authorization Checks

**The Problem:**
```python
def can_edit(user, resource):
    role_names = [ur.role.name for ur in user.user_roles if ur.role]
    return "admin" in role_names or "editor" in role_names
```

**The Solution:**
```python
class User(Table):
    user_roles: List[UserRole] = has_many(UserRole)
    role_names: List[str] = association_proxy("user_roles", "role.name")
    
    def has_role(self, name: str) -> bool:
        return name in self.role_names

def can_edit(user, resource):
    return user.has_role("admin") or user.has_role("editor")
```

#### ✅ Use Case 5: Denormalization Without Duplication

**The Problem:**
You want quick access to related data without storing it twice.

**The Solution:**
```python
class Order(Table):
    customer: Customer = belongs_to(Customer, "customer_id")
    
    # Quick access without storing customer_name in orders table
    customer_name: str = association_proxy("customer", "name")
    customer_email: str = association_proxy("customer", "email")

order.customer_name  # No extra database column needed
```

### When NOT to Use

#### ❌ Don't Use for Complex Filtering

```python
# BAD: Proxy then filter in Python
active_courses = [c for c in student.courses if c.active]

# GOOD: Use database query
active_courses = await Course.select().where(
    Course.id.in_(student.course_ids),
    Course.active == True
).all()
```

#### ❌ Don't Use for Aggregations

```python
# BAD: Load all data to count
total = len(student.course_names)

# GOOD: Use database count
total = await Enrollment.select().where(
    Enrollment.student_id == student.id
).count()
```

#### ❌ Don't Use When You Need the Junction Data

```python
# If you need the grade from Enrollment, don't just proxy to Course
class Student(Table):
    enrollments: List[Enrollment] = has_many(Enrollment)
    
    # This loses the grade information!
    courses: List[Course] = association_proxy("enrollments", "course")
    
    # Instead, work with enrollments directly
    def get_course_with_grade(self, course_name: str):
        for enrollment in self.enrollments:
            if enrollment.course.name == course_name:
                return (enrollment.course, enrollment.grade)
```

---

## How It Works Internally

### The Descriptor Protocol

Python descriptors are objects that customize attribute access. When you define:

```python
class Product(Table):
    tag_names: List[str] = association_proxy("product_tags", "tag.name")
```

Here's what happens:

```python
# 1. At class definition time:
#    association_proxy() creates an AttributeProxyDescriptor
descriptor = AttributeProxyDescriptor(
    target_collection="product_tags",
    attr="tag.name",
    creator=None,
    scalar=None,
    flatten=False,
)

# 2. Python calls __set_name__ with the attribute name
descriptor.__set_name__(Product, "tag_names")
# Now descriptor._name = "tag_names"
# And descriptor._owner_class = Product

# 3. When you access product.tag_names:
#    Python calls descriptor.__get__(product, Product)
result = descriptor.__get__(product, Product)
```

### Step-by-Step Execution

When you access `product.tag_names`:

```python
# Step 1: __get__ is called
def __get__(self, obj, objtype=None):
    if obj is None:
        return self  # Class-level access returns descriptor
    
    # Step 2: Get the source relationship value
    source = getattr(obj, self.target_collection)
    # source = product.product_tags (a list of ProductTag objects)
    
    # Step 3: Determine if scalar or collection
    is_scalar = self._is_scalar(source, obj)
    # is_scalar = False (because product_tags is a list)
    
    # Step 4: Return appropriate result
    if is_scalar:
        return self._get_scalar_value(source)
    else:
        return ProxyCollection(
            owner=obj,
            target_collection=self.target_collection,
            attr=self.attr,
            creator=self.creator,
            flatten=self.flatten,
        )
```

### Path Traversal: The _traverse_path Function

The magic of dot notation (`"course.name"`) happens in `_traverse_path`:

```python
def _traverse_path(obj, path: str):
    """
    Traverse a dot-notation path on an object.
    
    _traverse_path(enrollment, "course.name")
    # Equivalent to: enrollment.course.name
    """
    if obj is None:
        return None
    
    if not path:
        return obj
    
    parts = path.split(".")  # ["course", "name"]
    current = obj            # enrollment
    
    for part in parts:
        if current is None:
            return None
        current = getattr(current, part, None)
        # First iteration: current = enrollment.course (Course object)
        # Second iteration: current = course.name ("Math")
    
    return current  # "Math"
```

### ProxyCollection: The Collection Wrapper

When you access a collection proxy, you get a `ProxyCollection`:

```python
class ProxyCollection(MutableSequence, Generic[T]):
    """
    A list-like object that lazily evaluates values through a relationship.
    """
    
    def _get_values(self) -> List[T]:
        """Extract values by traversing the relationship."""
        source = getattr(self._owner, self._target_collection)
        if source is None:
            return []
        
        result = []
        for item in source:
            value = _traverse_path(item, self._attr)
            if value is not None:
                if self._flatten and isinstance(value, (list, tuple)):
                    result.extend(value)
                else:
                    result.append(value)
        
        return result
    
    def __iter__(self):
        """Iterate through proxied values."""
        return iter(self._get_values())
    
    def __len__(self):
        """Return count of proxied values."""
        return len(self._get_values())
```

### Scalar vs Collection Detection

The proxy auto-detects whether to return a single value or a collection:

```python
def _is_scalar(self, source, obj):
    # 1. If explicitly set, use that
    if self._scalar is not None:
        return self._scalar
    
    # 2. Check if source is None (might be unloaded belongs_to)
    if source is None:
        descriptor = getattr(type(obj), self.target_collection, None)
        if isinstance(descriptor, (BelongsTo, HasOne)):
            return True  # Scalar relationship
        return False
    
    # 3. Check if source is a collection
    if isinstance(source, (list, tuple)):
        return False  # Collection
    if hasattr(source, '_items'):  # SyncedList, ManyToManyCollection
        return False
    
    # 4. Check if source is a Table instance
    if hasattr(source, '_fields') and hasattr(source, '__table_name__'):
        return True  # Single model instance
    
    return True  # Default to scalar
```

### Creator Functions: How Append Works

When you add a `creator` function, you enable mutations:

```python
class Product(Table):
    product_tags: List[ProductTag] = has_many(ProductTag)
    
    tags: List[Tag] = association_proxy(
        "product_tags",
        "tag",
        creator=lambda tag: ProductTag(tag=tag)
    )

# When you call:
product.tags.append(new_tag)

# Internally:
def append(self, value):
    if self._creator is None:
        raise ValueError("No creator function - cannot append")
    
    # 1. Call the creator with the value
    new_junction = self._creator(value)
    # new_junction = ProductTag(tag=new_tag)
    
    # 2. Add to the source collection
    source = getattr(self._owner, self._target_collection)
    source.append(new_junction)
    # product.product_tags.append(ProductTag(tag=new_tag))
```

### Memory Model: No Caching

Proxies evaluate **fresh** on each access:

```python
product = await Product.find(1)

# Each access re-evaluates
names1 = list(product.tag_names)  # Traverses product_tags
names2 = list(product.tag_names)  # Traverses again (fresh)

# If you modify the source:
product.product_tags.append(ProductTag(tag=Tag(name="new")))

# The proxy sees the change:
names3 = list(product.tag_names)  # Includes "new"
```

**Why no caching?**
1. Keeps behavior predictable
2. Source modifications are immediately visible
3. No cache invalidation complexity
4. Memory efficient for large collections

**If you need caching:**
```python
# Cache manually when needed
tag_names = product.tag_names.to_list()  # Convert to regular list
# Use tag_names multiple times
```

---

## Who Should Use This

### Perfect For

| Role | Use Case |
|------|----------|
| **Backend Developers** | Simplify API response building |
| **Frontend/Template Developers** | Clean data access in templates |
| **Full-Stack Developers** | Reduce boilerplate in views |
| **API Designers** | Create intuitive model interfaces |
| **Junior Developers** | Understand relationships without junction table details |

### Prerequisites

Before using association proxies, you should understand:

1. **PyNext Relationships**: `has_many`, `belongs_to`, `has_one`, `many_to_many`
2. **Junction Tables**: Why M2M needs intermediate tables
3. **Python Descriptors**: Basic understanding helps, but not required
4. **List Operations**: Iteration, indexing, membership testing

---

## Complete API Reference

### The association_proxy() Function

```python
def association_proxy(
    target_collection: str,
    attr: str,
    *,
    creator: Optional[Callable[[Any], Any]] = None,
    scalar: Optional[bool] = None,
    flatten: bool = False,
) -> AttributeProxyDescriptor:
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target_collection` | `str` | Yes | - | Name of the relationship attribute to traverse |
| `attr` | `str` | Yes | - | Attribute path (supports dot notation) |
| `creator` | `Callable` | No | `None` | Function to create junction objects for mutations |
| `scalar` | `bool` | No | `None` | Force scalar mode (`None` = auto-detect) |
| `flatten` | `bool` | No | `False` | Flatten nested lists in results |

#### Returns

`AttributeProxyDescriptor` - A descriptor that provides proxy access.

### Parameter Deep Dive

#### target_collection

The name of an existing relationship on your model:

```python
class Product(Table):
    # These are valid target_collections:
    product_tags: List[ProductTag] = has_many(ProductTag)
    category: Category = belongs_to(Category, "category_id")
    owner: User = has_one(User)

# Using them:
tags = association_proxy("product_tags", "tag")      # ✓ Valid
cat_name = association_proxy("category", "name")     # ✓ Valid
owner_email = association_proxy("owner", "email")    # ✓ Valid
invalid = association_proxy("nonexistent", "name")   # ✗ Returns empty/None
```

#### attr

The attribute path to extract, supporting dot notation:

```python
# Single level
association_proxy("enrollments", "course")           # Returns Course objects
association_proxy("enrollments", "grade")            # Returns grade strings

# Two levels
association_proxy("enrollments", "course.name")      # Returns course names
association_proxy("enrollments", "course.credits")   # Returns credit counts

# Three+ levels
association_proxy("enrollments", "course.instructor.name")
association_proxy("items", "category.parent.name")

# Special cases
association_proxy("author", "")                      # Returns author itself
```

#### creator

A function that creates junction objects when appending:

```python
# Basic creator
association_proxy(
    "product_tags",
    "tag",
    creator=lambda tag: ProductTag(tag=tag)
)

# Creator with extra data
association_proxy(
    "product_tags",
    "tag",
    creator=lambda tag: ProductTag(
        tag=tag,
        created_at=datetime.now(),
        created_by=current_user.id,
    )
)

# Creator using factory method
association_proxy(
    "product_tags",
    "tag",
    creator=ProductTag.from_tag
)
```

#### scalar

Force scalar or collection mode:

```python
# Auto-detect (default)
association_proxy("author", "name")           # Scalar (author is belongs_to)
association_proxy("posts", "title")           # Collection (posts is has_many)

# Force scalar
association_proxy("first_item", "name", scalar=True)

# Force collection
association_proxy("single_rel", "value", scalar=False)
```

#### flatten

Flatten nested lists:

```python
class User(Table):
    roles: List[Role] = has_many(UserRole)

class Role(Table):
    permissions: List[str]  # ["read", "write", "delete"]

# Without flatten
permissions = association_proxy("roles", "permissions")
user.permissions  # [["read", "write"], ["delete", "admin"]]

# With flatten
permissions = association_proxy("roles", "permissions", flatten=True)
user.permissions  # ["read", "write", "delete", "admin"]
```

### ProxyCollection API

When you access a collection proxy, you get a `ProxyCollection` with these methods:

#### Iteration

```python
# For loop
for name in product.tag_names:
    print(name)

# List conversion
names = list(product.tag_names)
names = product.tag_names.to_list()
names = product.tag_names.copy()
```

#### Indexing and Slicing

```python
first = product.tag_names[0]       # First item
last = product.tag_names[-1]       # Last item
subset = product.tag_names[1:3]    # Slice
every_other = product.tag_names[::2]  # Step
```

#### Length and Boolean

```python
count = len(product.tag_names)     # Count
if product.tag_names:              # Truthy if not empty
    print("Has tags!")
```

#### Membership

```python
if "sale" in product.tag_names:
    print("On sale!")
if "premium" not in product.tag_names:
    print("Not premium")
```

#### Searching

```python
index = product.tag_names.index("sale")     # Find index
count = product.tag_names.count("featured")  # Count occurrences
```

#### Mutation (requires creator)

```python
# Append single item
product.tags.append(new_tag)

# Extend with multiple
product.tags.extend([tag1, tag2, tag3])

# Insert at position (adds to end of source)
product.tags.insert(0, new_tag)

# Remove by value
product.tags.remove(old_tag)

# Pop by index
removed = product.tags.pop()       # Last item
removed = product.tags.pop(0)      # First item

# Clear all
product.tags.clear()
```

#### Async Methods

```python
# Get all items
items = await product.tags.all()

# Get first item
first = await product.tags.first()

# Filter items (in-memory)
active = await product.tags.filter(active=True)
```

#### Comparison

```python
# Equality with list
product.tag_names == ["a", "b", "c"]

# Equality with another proxy
product1.tag_names == product2.tag_names

# Concatenation
all_names = product.tag_names + ["extra"]
all_names = ["prefix"] + product.tag_names
```

---

## Real-World Examples

### Example 1: E-Commerce Product Management

```python
# Models
class Category(Table):
    id: int
    name: str
    slug: str
    parent_id: Optional[int] = None
    parent: Optional["Category"] = belongs_to("Category", "parent_id")

class Tag(Table):
    id: int
    name: str
    color: str = "gray"

class ProductTag(Table):
    id: int
    product_id: int
    tag_id: int
    tag: Tag = belongs_to(Tag, "tag_id")
    added_at: datetime = Field(default_factory=datetime.now)

class ProductCategory(Table):
    id: int
    product_id: int
    category_id: int
    category: Category = belongs_to(Category, "category_id")
    is_primary: bool = False

class Product(Table):
    id: int
    name: str
    price: float
    
    # Relationships
    product_tags: List[ProductTag] = has_many(ProductTag)
    product_categories: List[ProductCategory] = has_many(ProductCategory)
    
    # Association proxies for clean access
    tag_names: List[str] = association_proxy("product_tags", "tag.name")
    tag_colors: List[str] = association_proxy("product_tags", "tag.color")
    tags: List[Tag] = association_proxy(
        "product_tags",
        "tag",
        creator=lambda tag: ProductTag(tag=tag)
    )
    
    category_names: List[str] = association_proxy("product_categories", "category.name")
    category_slugs: List[str] = association_proxy("product_categories", "category.slug")
    
    # Nested: get parent category names
    parent_category_names: List[str] = association_proxy(
        "product_categories",
        "category.parent.name"
    )


# Usage in API
async def get_product_detail(product_id: int):
    product = await Product.find(product_id)
    
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "tags": product.tag_names,
        "tag_colors": dict(zip(product.tag_names, product.tag_colors)),
        "categories": product.category_names,
        "breadcrumbs": product.parent_category_names + product.category_names,
    }


# Usage in template
"""
<div class="product-card">
    <h2>{{ product.name }}</h2>
    
    <div class="tags">
        {% for name, color in zip(product.tag_names, product.tag_colors) %}
            <span class="tag" style="background: {{ color }}">
                {{ name }}
            </span>
        {% endfor %}
    </div>
    
    <nav class="breadcrumb">
        {% for cat in product.category_names %}
            <span>{{ cat }}</span>
        {% endfor %}
    </nav>
</div>
"""


# Adding tags
async def add_tag_to_product(product_id: int, tag_name: str):
    product = await Product.find(product_id)
    tag = await Tag.find_by(name=tag_name)
    
    if tag and tag.name not in product.tag_names:
        product.tags.append(tag)
        await product.save()
```

### Example 2: User Roles and Permissions System

```python
class Permission(Table):
    id: int
    name: str
    code: str
    description: str

class RolePermission(Table):
    id: int
    role_id: int
    permission_id: int
    permission: Permission = belongs_to(Permission, "permission_id")

class Role(Table):
    id: int
    name: str
    description: str
    
    role_permissions: List[RolePermission] = has_many(RolePermission)
    
    # Get permission objects
    permissions: List[Permission] = association_proxy("role_permissions", "permission")
    
    # Get permission codes for quick checking
    permission_codes: List[str] = association_proxy("role_permissions", "permission.code")

class UserRole(Table):
    id: int
    user_id: int
    role_id: int
    role: Role = belongs_to(Role, "role_id")
    granted_at: datetime = Field(default_factory=datetime.now)
    granted_by_id: Optional[int] = None

class User(Table):
    id: int
    name: str
    email: str
    
    user_roles: List[UserRole] = has_many(UserRole)
    
    # Get role names
    role_names: List[str] = association_proxy("user_roles", "role.name")
    
    # Get role objects
    roles: List[Role] = association_proxy("user_roles", "role")
    
    # Helper methods using proxies
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return role_name in self.role_names
    
    def has_any_role(self, *role_names: str) -> bool:
        """Check if user has any of the specified roles."""
        return any(name in self.role_names for name in role_names)
    
    def has_all_roles(self, *role_names: str) -> bool:
        """Check if user has all specified roles."""
        return all(name in self.role_names for name in role_names)
    
    def has_permission(self, permission_code: str) -> bool:
        """Check if user has a permission through any role."""
        for role in self.roles:
            if permission_code in role.permission_codes:
                return True
        return False
    
    def get_all_permissions(self) -> List[str]:
        """Get all permission codes from all roles."""
        permissions = set()
        for role in self.roles:
            permissions.update(role.permission_codes)
        return list(permissions)


# Usage in authorization
def require_permission(permission_code: str):
    """Decorator for permission-based access control."""
    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.has_permission(permission_code):
                raise PermissionDenied(f"Missing permission: {permission_code}")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

@require_permission("articles.edit")
async def edit_article(request, article_id: int):
    # Only users with "articles.edit" permission can access
    pass


# Usage in templates
"""
{% if user.has_role("admin") %}
    <a href="/admin">Admin Panel</a>
{% endif %}

{% if user.has_permission("users.delete") %}
    <button class="danger">Delete User</button>
{% endif %}

<div class="user-roles">
    {% for role in user.role_names %}
        <span class="badge">{{ role }}</span>
    {% endfor %}
</div>
"""
```

### Example 3: Blog with Comments and Authors

```python
class Author(Table):
    id: int
    name: str
    email: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    
    posts: List["Post"] = has_many("Post", backref="author")

class Comment(Table):
    id: int
    post_id: int
    author_id: int
    content: str
    approved: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    
    post: "Post" = belongs_to("Post", "post_id")
    author: Author = belongs_to(Author, "author_id")

class PostTag(Table):
    id: int
    post_id: int
    tag_id: int
    tag: "Tag" = belongs_to("Tag", "tag_id")

class Tag(Table):
    id: int
    name: str
    slug: str

class Post(Table):
    id: int
    title: str
    content: str
    published: bool = False
    author_id: int
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    author: Author = belongs_to(Author, "author_id")
    comments: List[Comment] = has_many(Comment)
    post_tags: List[PostTag] = has_many(PostTag)
    
    # Scalar proxies for author info
    author_name: str = association_proxy("author", "name")
    author_email: str = association_proxy("author", "email")
    author_avatar: str = association_proxy("author", "avatar_url")
    
    # Collection proxies for comments
    commenter_names: List[str] = association_proxy("comments", "author.name")
    commenter_emails: List[str] = association_proxy("comments", "author.email")
    comment_texts: List[str] = association_proxy("comments", "content")
    
    # Collection proxies for tags
    tag_names: List[str] = association_proxy("post_tags", "tag.name")
    tag_slugs: List[str] = association_proxy("post_tags", "tag.slug")
    tags: List[Tag] = association_proxy(
        "post_tags",
        "tag",
        creator=lambda tag: PostTag(tag=tag)
    )
    
    @property
    def unique_commenters(self) -> List[str]:
        """Get unique commenter names."""
        return list(set(self.commenter_names))
    
    @property
    def comment_count(self) -> int:
        """Get number of comments."""
        return len(self.comments)


# Usage in blog view
async def get_post(slug: str):
    post = await Post.find_by(slug=slug)
    
    return {
        "title": post.title,
        "content": post.content,
        "author": {
            "name": post.author_name,
            "avatar": post.author_avatar,
        },
        "tags": post.tag_names,
        "comment_count": post.comment_count,
        "unique_commenters": post.unique_commenters,
    }


# Template example
"""
<article>
    <header>
        <h1>{{ post.title }}</h1>
        <div class="meta">
            <img src="{{ post.author_avatar }}" alt="{{ post.author_name }}">
            <span>By {{ post.author_name }}</span>
        </div>
        <div class="tags">
            {% for tag in post.tag_names %}
                <a href="/tag/{{ tag }}">{{ tag }}</a>
            {% endfor %}
        </div>
    </header>
    
    <div class="content">{{ post.content }}</div>
    
    <section class="comments">
        <h3>{{ post.comment_count }} Comments</h3>
        <p>From: {{ post.unique_commenters | join(", ") }}</p>
    </section>
</article>
"""
```

### Example 4: Order Management with Nested Data

```python
class Customer(Table):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    
    addresses: List["Address"] = has_many("Address")
    orders: List["Order"] = has_many("Order")

class Address(Table):
    id: int
    customer_id: int
    street: str
    city: str
    state: str
    country: str
    zip_code: str
    is_default: bool = False

class OrderItem(Table):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    
    product: "Product" = belongs_to("Product", "product_id")
    
    @property
    def total(self) -> float:
        return self.quantity * self.unit_price

class Product(Table):
    id: int
    name: str
    sku: str
    price: float

class Order(Table):
    id: int
    customer_id: int
    shipping_address_id: int
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    customer: Customer = belongs_to(Customer, "customer_id")
    shipping_address: Address = belongs_to(Address, "shipping_address_id")
    items: List[OrderItem] = has_many(OrderItem)
    
    # Customer info proxies
    customer_name: str = association_proxy("customer", "name")
    customer_email: str = association_proxy("customer", "email")
    customer_phone: str = association_proxy("customer", "phone")
    
    # Shipping address proxies (deeply nested)
    ship_to_city: str = association_proxy("shipping_address", "city")
    ship_to_state: str = association_proxy("shipping_address", "state")
    ship_to_country: str = association_proxy("shipping_address", "country")
    
    # Order items proxies
    product_names: List[str] = association_proxy("items", "product.name")
    product_skus: List[str] = association_proxy("items", "product.sku")
    quantities: List[int] = association_proxy("items", "quantity")
    
    @property
    def total(self) -> float:
        return sum(item.total for item in self.items)
    
    @property
    def item_count(self) -> int:
        return sum(self.quantities)


# Usage in order confirmation email
async def send_order_confirmation(order_id: int):
    order = await Order.find(order_id)
    
    email_data = {
        "to": order.customer_email,
        "subject": f"Order #{order.id} Confirmed",
        "body": f"""
        Hi {order.customer_name},
        
        Your order has been confirmed!
        
        Items:
        {', '.join(order.product_names)}
        
        Shipping to: {order.ship_to_city}, {order.ship_to_state}
        
        Total: ${order.total:.2f}
        """
    }
    
    await send_email(**email_data)
```

---

## SQLAlchemy vs PyNext Deep Dive

### Side-by-Side Comparison

#### Import and Setup

```python
# SQLAlchemy - Extra import required
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_keywords = relationship("UserKeyword", back_populates="user")
    keywords = association_proxy('user_keywords', 'keyword')

# PyNext - Built-in, no extra imports
from pynext.db import Table, has_many, association_proxy

class User(Table):
    user_keywords: List[UserKeyword] = has_many(UserKeyword)
    keywords: List[Keyword] = association_proxy("user_keywords", "keyword")
```

#### Nested Attribute Access

```python
# SQLAlchemy - Confusing 'attr' parameter
class User(Base):
    user_keywords = relationship("UserKeyword")
    
    # What does 'attr' do? Not obvious!
    keyword_names = association_proxy(
        'user_keywords',
        'keyword',
        attr='name'  # ??? Confusing
    )
    
    # Alternative syntax (also confusing)
    keyword_names = association_proxy(
        'user_keywords',
        'keyword.name'  # This works but not well documented
    )

# PyNext - Obvious dot notation
class User(Table):
    user_keywords: List[UserKeyword] = has_many(UserKeyword)
    
    # Clear: traverse user_keywords, then keyword, then name
    keyword_names: List[str] = association_proxy("user_keywords", "keyword.name")
```

#### Creator Functions

```python
# SQLAlchemy - Verbose creator
class User(Base):
    user_keywords = relationship("UserKeyword", back_populates="user")
    
    keywords = association_proxy(
        'user_keywords',
        'keyword',
        creator=lambda kw: UserKeyword(keyword=kw)
    )

# PyNext - Same pattern, cleaner integration
class User(Table):
    user_keywords: List[UserKeyword] = has_many(UserKeyword)
    
    keywords: List[Keyword] = association_proxy(
        "user_keywords",
        "keyword",
        creator=lambda kw: UserKeyword(keyword=kw)
    )
```

#### Type Hints

```python
# SQLAlchemy - No type hints on proxy
class User(Base):
    keywords = association_proxy('user_keywords', 'keyword')
    # Type: ??? (no hints)

# PyNext - Full type hints
class User(Table):
    keywords: List[Keyword] = association_proxy("user_keywords", "keyword")
    # Type: List[Keyword] ✓
    # IDE knows this returns a list of Keyword objects
```

### Feature Comparison Table

| Feature | SQLAlchemy | PyNext |
|---------|------------|--------|
| Import location | `sqlalchemy.ext.associationproxy` | Built-in |
| Syntax for nested paths | Confusing `attr` parameter | Intuitive `"a.b.c"` syntax |
| Scalar detection | Manual `scalar=True` | Auto-detected from relationship |
| Type hints | None | Full generic support |
| IDE autocomplete | Limited | Full support |
| Learning curve | Steep (read docs carefully) | Gentle (intuitive API) |
| Error messages | Generic | Helpful with suggestions |
| Documentation quality | Sparse | Comprehensive |

### Migration from SQLAlchemy

```python
# Before (SQLAlchemy)
from sqlalchemy.ext.associationproxy import association_proxy

class User(Base):
    __tablename__ = 'users'
    
    user_keywords = relationship("UserKeyword", back_populates="user")
    keywords = association_proxy('user_keywords', 'keyword')
    keyword_names = association_proxy('user_keywords', 'keyword', attr='name')

# After (PyNext)
from pynext.db import Table, has_many, association_proxy

class User(Table):
    user_keywords: List[UserKeyword] = has_many(UserKeyword)
    keywords: List[Keyword] = association_proxy("user_keywords", "keyword")
    keyword_names: List[str] = association_proxy("user_keywords", "keyword.name")
```

---

## Decision Guide

### Should I Use Association Proxy?

```
                        START
                          │
                          ▼
        ┌─────────────────────────────────┐
        │ Do you need to access data      │
        │ through a relationship?         │
        └─────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
             YES                      NO
              │                       │
              ▼                       ▼
    ┌───────────────────┐    Use direct attribute
    │ Is it read-only   │    access instead
    │ (no mutations)?   │
    └───────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
   YES                  NO
    │                   │
    ▼                   ▼
  Use proxy      ┌──────────────┐
  (no creator)   │ Do you need  │
                 │ to add items?│
                 └──────────────┘
                         │
               ┌─────────┴─────────┐
               │                   │
              YES                  NO
               │                   │
               ▼                   ▼
         Use proxy with      ┌──────────────────┐
         creator function    │ Need to modify   │
                             │ junction data?   │
                             └──────────────────┘
                                      │
                            ┌─────────┴─────────┐
                            │                   │
                           YES                  NO
                            │                   │
                            ▼                   ▼
                   Don't use proxy.        Use proxy
                   Work with junction      (no creator)
                   directly.
```

### Quick Reference Table

| Scenario | Use Proxy? | Configuration |
|----------|------------|---------------|
| Read tag names from M2M | ✅ Yes | `association_proxy("product_tags", "tag.name")` |
| Get author name from post | ✅ Yes | `association_proxy("author", "name", scalar=True)` |
| Add tags to product | ✅ Yes | Add `creator=lambda t: ProductTag(tag=t)` |
| Update enrollment grade | ❌ No | Work with `enrollments` directly |
| Count related items | ❌ No | Use database `count()` |
| Complex filtering | ❌ No | Use database queries |
| Pagination | ❌ No | Use database `limit()`/`offset()` |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Proxy to Non-Relationship

```python
# ❌ BAD: "name" is a column, not a relationship
class Product(Table):
    name: str  # This is a column!
    
    # This won't work as expected
    upper_name = association_proxy("name", "upper")

# ✅ GOOD: Access column directly
class Product(Table):
    name: str
    
    @property
    def upper_name(self):
        return self.name.upper()
```

### Anti-Pattern 2: Mutation Without Creator

```python
# ❌ BAD: No creator means no append
class Product(Table):
    product_tags: List[ProductTag] = has_many(ProductTag)
    tags = association_proxy("product_tags", "tag")  # No creator!

product.tags.append(new_tag)  # Raises ValueError!

# ✅ GOOD: Add creator for mutations
class Product(Table):
    product_tags: List[ProductTag] = has_many(ProductTag)
    tags = association_proxy(
        "product_tags",
        "tag",
        creator=lambda t: ProductTag(tag=t)
    )

product.tags.append(new_tag)  # Works!
```

### Anti-Pattern 3: Heavy Loops with Proxies

```python
# ❌ BAD: Evaluates proxy on every iteration
for i in range(100):
    if "admin" in user.role_names:  # Evaluates 100 times!
        do_something()

# ✅ GOOD: Cache the result
role_names = user.role_names.to_list()  # Evaluate once
for i in range(100):
    if "admin" in role_names:  # Use cached list
        do_something()
```

### Anti-Pattern 4: Using Proxy for Aggregations

```python
# ❌ BAD: Loads all data just to count
count = len(user.course_names)  # Fetches all courses!

# ✅ GOOD: Use database count
count = await Enrollment.select().where(
    Enrollment.student_id == user.id
).count()
```

### Anti-Pattern 5: Ignoring None Handling

```python
# ❌ BAD: Assumes all values exist
class Product(Table):
    product_tags: List[ProductTag] = has_many(ProductTag)
    tag_ids: List[int] = association_proxy("product_tags", "tag.id")

# If some ProductTags have tag=None, those are silently skipped!
# You might expect 5 IDs but get 3

# ✅ GOOD: Understand that None values are filtered out
# Or check your data integrity
assert len(product.tag_ids) == len(product.product_tags)
```

### Anti-Pattern 6: Proxy for Write-Heavy Operations

```python
# ❌ BAD: Individual appends in a loop
for tag in many_tags:
    product.tags.append(tag)  # Creates junction, triggers hooks, etc.

# ✅ GOOD: Batch operations on the source
product_tags = [ProductTag(tag=tag, product=product) for tag in many_tags]
await ProductTag.bulk_create(product_tags)
```

---

## Performance Deep Dive

### Time Complexity

| Operation | Time Complexity | Notes |
|-----------|-----------------|-------|
| `list(proxy)` | O(n) | n = items in source |
| `len(proxy)` | O(n) | Must evaluate all items |
| `item in proxy` | O(n) | Linear search |
| `proxy[0]` | O(n) | Must evaluate to create list |
| `proxy.append()` | O(1) | Just creates and appends junction |

### Memory Usage

- **ProxyCollection**: Minimal overhead (just references)
- **Iteration**: Creates temporary list of results
- **No Caching**: Each access re-evaluates (memory efficient)

### Optimization Tips

#### Tip 1: Cache When Accessing Multiple Times

```python
# ❌ Slow: Evaluates proxy 3 times
count = len(product.tag_names)
first = product.tag_names[0]
has_sale = "sale" in product.tag_names

# ✅ Fast: Evaluate once
tags = product.tag_names.to_list()
count = len(tags)
first = tags[0]
has_sale = "sale" in tags
```

#### Tip 2: Use Database Queries for Large Sets

```python
# ❌ Slow for large datasets
all_names = product.tag_names  # Loads all into memory

# ✅ Fast: Paginate at database level
names = await Tag.select().join(
    ProductTag, ProductTag.tag_id == Tag.id
).where(
    ProductTag.product_id == product.id
).limit(10).offset(page * 10).pluck("name")
```

#### Tip 3: Eager Load Related Data

```python
# ❌ Slow: N+1 queries
products = await Product.select().all()
for product in products:
    print(product.tag_names)  # Query for each product!

# ✅ Fast: Eager load
products = await Product.select().options(
    selectinload("product_tags.tag")
).all()
for product in products:
    print(product.tag_names)  # No extra queries
```

---

## Testing Your Proxies

### Basic Test Pattern

```python
import pytest
from your_app.models import Product, ProductTag, Tag

class TestProductProxy:
    def test_tag_names_returns_list(self):
        """tag_names returns a list of strings."""
        tag1 = Tag(id=1, name="sale")
        tag2 = Tag(id=2, name="new")
        
        product = Product(id=1, name="Test")
        product._product_tags = [
            ProductTag(id=1, product_id=1, tag_id=1, tag=tag1),
            ProductTag(id=2, product_id=1, tag_id=2, tag=tag2),
        ]
        
        assert list(product.tag_names) == ["sale", "new"]
    
    def test_tag_names_empty_when_no_tags(self):
        """tag_names returns empty list when no tags."""
        product = Product(id=1, name="Test")
        product._product_tags = []
        
        assert list(product.tag_names) == []
    
    def test_tag_names_skips_none_tags(self):
        """tag_names skips items where tag is None."""
        tag = Tag(id=1, name="valid")
        
        product = Product(id=1, name="Test")
        product._product_tags = [
            ProductTag(id=1, product_id=1, tag_id=1, tag=tag),
            ProductTag(id=2, product_id=1, tag_id=2, tag=None),  # None!
        ]
        
        assert list(product.tag_names) == ["valid"]
```

### Testing Mutations

```python
class TestProductProxyMutation:
    def test_append_creates_junction(self):
        """Appending tag creates ProductTag."""
        product = Product(id=1, name="Test")
        product._product_tags = []
        
        new_tag = Tag(id=1, name="added")
        product.tags.append(new_tag)
        
        assert len(product._product_tags) == 1
        assert product._product_tags[0].tag is new_tag
    
    def test_append_without_creator_raises(self):
        """Append raises when no creator defined."""
        # Assuming tag_names has no creator
        product = Product(id=1, name="Test")
        product._product_tags = []
        
        with pytest.raises(ValueError) as exc:
            product.tag_names.append("new")
        
        assert "creator function" in str(exc.value)
```

### Testing Scalar Proxies

```python
class TestPostAuthorProxy:
    def test_author_name_returns_string(self):
        """author_name returns the author's name."""
        author = Author(id=1, name="Alice")
        post = Post(id=1, title="Test", author=author)
        
        assert post.author_name == "Alice"
    
    def test_author_name_none_when_no_author(self):
        """author_name returns None when author is None."""
        post = Post(id=1, title="Test", author=None)
        
        assert post.author_name is None
```

---

## Troubleshooting

### Problem: Proxy Returns Empty When Data Exists

**Symptoms:**
```python
product.tag_names  # Returns [] but product has tags
```

**Causes & Solutions:**

1. **Relationship not loaded:**
```python
# Ensure relationships are loaded
product = await Product.find(id).options(selectinload("product_tags.tag"))
```

2. **Wrong relationship name:**
```python
# Check spelling
association_proxy("product_tagz", "tag.name")  # Typo!
association_proxy("product_tags", "tag.name")  # Correct
```

3. **None values in path:**
```python
# Some ProductTags might have tag=None
# Check data integrity
for pt in product.product_tags:
    print(pt.tag)  # Look for None values
```

### Problem: "No creator function" Error

**Symptoms:**
```python
product.tags.append(new_tag)
# ValueError: Cannot append to proxy without creator function
```

**Solution:**
```python
# Add creator to the proxy definition
tags = association_proxy(
    "product_tags",
    "tag",
    creator=lambda tag: ProductTag(tag=tag)  # Add this!
)
```

### Problem: TypeError on Access

**Symptoms:**
```python
product.tag_names
# TypeError: 'NoneType' object is not iterable
```

**Cause:**
The source relationship returns None instead of an empty list.

**Solution:**
```python
# Ensure relationship property handles None
@property
def product_tags(self):
    return self._product_tags or []  # Default to empty list
```

### Problem: Unexpected Results with Nested Paths

**Symptoms:**
```python
# Expected: ["CategoryA", "CategoryB"]
# Got: [None, None]
```

**Cause:**
Intermediate objects in the path are None.

**Solution:**
```python
# Check the full path
for item in product.product_categories:
    print(f"Category: {item.category}")
    if item.category:
        print(f"Parent: {item.category.parent}")
```

### Problem: Changes Not Reflected

**Symptoms:**
```python
product.tags.append(new_tag)
print(product.tag_names)  # Doesn't show new tag
```

**Cause:**
The new junction object wasn't set up correctly.

**Solution:**
```python
# Ensure creator sets up the relationship properly
creator=lambda tag: ProductTag(
    tag=tag,
    product_id=product.id,  # Make sure FK is set
)
```

---

## Summary

### Quick Reference Card

```python
from pynext.db import Table, has_many, belongs_to, association_proxy

# Collection proxy (has_many/many_to_many)
class Product(Table):
    product_tags: List[ProductTag] = has_many(ProductTag)
    
    # Read-only
    tag_names: List[str] = association_proxy("product_tags", "tag.name")
    
    # With mutations
    tags: List[Tag] = association_proxy(
        "product_tags",
        "tag",
        creator=lambda t: ProductTag(tag=t)
    )

# Scalar proxy (belongs_to/has_one)
class Post(Table):
    author: User = belongs_to(User, "author_id")
    author_name: str = association_proxy("author", "name")

# Nested paths
company_city: str = association_proxy("department", "company.address.city")

# Usage
product.tag_names      # ["a", "b", "c"]
product.tags.append(t) # Add tag
post.author_name       # "Alice"
```

### Key Takeaways

1. **Use for simplification**: Replace verbose navigation with clean attribute access
2. **Dot notation for nesting**: `"course.instructor.name"` is intuitive
3. **Auto-detects scalar/collection**: No manual configuration needed
4. **Add creator for mutations**: Required for append/extend/remove
5. **No caching**: Fresh evaluation on each access
6. **Handles None gracefully**: Skips None values in paths
7. **Better than SQLAlchemy**: Simpler, more Pythonic, better typed
