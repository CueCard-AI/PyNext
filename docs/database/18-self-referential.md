# Self-Referential Relationships

Self-referential relationships allow a model to reference itself, creating hierarchical tree structures. This is one of the most powerful patterns in database design, used for:

- **Category Taxonomies**: Electronics → Computers → Laptops → Gaming Laptops
- **Comment Threads**: Original post → Reply → Reply to reply
- **Organizational Charts**: CEO → VPs → Managers → Employees
- **File Systems**: / → home → user → documents
- **Menu Structures**: Main Menu → Products → Electronics → Phones
- **Geographic Hierarchies**: Country → State → City → Neighborhood

**PyNext makes self-referential relationships dramatically simpler than SQLAlchemy** — no confusing `remote_side` parameter, just intuitive Python code.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [The Problem with SQLAlchemy](#the-problem-with-sqlalchemy)
3. [PyNext Solution](#pynext-solution)
4. [TreeMixin Complete Reference](#treemixin-complete-reference)
5. [Real-World Examples](#real-world-examples)
6. [Configuration Options](#configuration-options)
7. [Performance: CTE vs App-Level](#performance-cte-vs-app-level)
8. [Common Patterns](#common-patterns)
9. [Edge Cases](#edge-cases)
10. [SQLAlchemy Comparison](#sqlalchemy-comparison)
11. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Step 1: Define Your Model

```python
from pynext.db import Table, TreeMixin
from typing import Optional

class Category(Table, TreeMixin):
    """Product category with parent-child hierarchy."""
    name: str
    parent_id: Optional[int]  # This is all you need!
```

That's it! PyNext automatically:
- Detects `parent_id` as self-referential
- Creates `parent` and `children` relationships
- Adds all tree traversal methods via `TreeMixin`

### Step 2: Create Your Tree

```python
# Create root categories
electronics = await Category.create(name="Electronics")
clothing = await Category.create(name="Clothing")

# Create subcategories
computers = await Category.create(name="Computers", parent_id=electronics.id)
phones = await Category.create(name="Phones", parent_id=electronics.id)

# Create sub-subcategories
laptops = await Category.create(name="Laptops", parent_id=computers.id)
desktops = await Category.create(name="Desktops", parent_id=computers.id)
gaming_laptops = await Category.create(name="Gaming Laptops", parent_id=laptops.id)
```

This creates:
```
Electronics
├── Computers
│   ├── Laptops
│   │   └── Gaming Laptops
│   └── Desktops
└── Phones

Clothing
```

### Step 3: Navigate the Tree

```python
# Get the gaming laptops category
gaming = await Category.get(gaming_laptops.id)

# Check if it's a root
print(gaming.is_root)  # False

# Get all ancestors (parent → grandparent → root)
ancestors = await gaming.ancestors()
# [Laptops, Computers, Electronics]

# Get the full path
await gaming.ancestors()  # Populates cache
print(gaming.path)  # "Electronics/Computers/Laptops/Gaming Laptops"

# Get depth level (root = 0)
depth = await gaming.depth()
print(depth)  # 3

# Find the root of this tree
root = await gaming.root()
print(root.name)  # "Electronics"

# Check if it's a leaf (no children)
is_leaf = await gaming.is_leaf()
print(is_leaf)  # True

# Get siblings (same level, same parent)
siblings = await laptops.siblings()
# [Desktops]

# Get all descendants from electronics
all_under_electronics = await electronics.descendants()
# [Computers, Phones, Laptops, Desktops, Gaming Laptops]
```

---

## The Problem with SQLAlchemy

SQLAlchemy's self-referential relationships are notoriously confusing:

```python
# SQLAlchemy - Good luck understanding this!
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

class Node(Base):
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('nodes.id'))
    name = Column(String)
    
    # WTF is remote_side?!
    children = relationship(
        "Node",
        backref=backref("parent", remote_side=[id])
    )
```

### Problems with SQLAlchemy:

1. **`remote_side` is cryptic** — What does it mean? Why is it needed? Even experienced developers get confused.

2. **No built-in tree traversal** — Want ancestors? Descendants? Path? Write your own recursive queries.

3. **Manual CTE writing** — PostgreSQL has efficient recursive CTEs, but you have to write raw SQL.

4. **Easy to create infinite loops** — Get the backref wrong and your app hangs.

5. **No move validation** — Moving a node to its own descendant creates a cycle. SQLAlchemy won't stop you.

---

## PyNext Solution

### Basic Self-Referential (Auto-Detected)

PyNext automatically detects self-referential patterns:

```python
from pynext.db import Table
from typing import Optional, List

class Category(Table):
    name: str
    parent_id: Optional[int]  # Auto-detected as self-ref to Category!
    
    # These are auto-created for you:
    # parent: Optional[Category]
    # children: List[Category]
```

**Detection patterns:**
- `parent_id` on any model → Always self-referential
- `reply_to_id` on any model → Self-referential (for comments)
- `reports_to_id` on any model → Self-referential (for org charts)
- `category_id` on Category → Self-referential
- `comment_id` on Comment → Self-referential

### Explicit Relationships (Optional)

You can also define relationships explicitly:

```python
from pynext.db import Table, belongs_to, has_many
from typing import Optional, List

class Category(Table):
    name: str
    parent_id: Optional[int]
    
    # Explicit definitions (optional)
    parent: Optional["Category"] = belongs_to("Category")
    children: List["Category"] = has_many("Category", foreign_key="parent_id")
```

### TreeMixin for Full Power

Add `TreeMixin` to get all tree traversal methods:

```python
from pynext.db import Table, TreeMixin
from typing import Optional

class Category(Table, TreeMixin):
    name: str
    parent_id: Optional[int]
    slug: str  # URL-friendly name

# Now Category has 15+ tree methods!
```

---

## TreeMixin Complete Reference

### Sync Properties (No Database Call)

These properties work instantly without hitting the database:

#### `is_root: bool`

Check if this node is a root (has no parent).

```python
root = Category(name="Electronics", parent_id=None)
child = Category(name="Computers", parent_id=1)

print(root.is_root)   # True
print(child.is_root)  # False
```

**Use cases:**
- Conditional rendering (show different UI for root vs child)
- Validation (some operations only allowed on roots)
- Building breadcrumbs

#### `path: str`

Get the full path from root to this node.

```python
# First, populate the ancestor cache
await gaming_laptops.ancestors()

# Now path is available
print(gaming_laptops.path)
# "Electronics/Computers/Laptops/Gaming Laptops"
```

**Important:** Call `ancestors()` first to populate the cache. Without cache, `path` returns just the node's name.

**Customization:**
```python
class Category(Table, TreeMixin):
    name: str
    parent_id: Optional[int]
    
    _tree_separator = " > "  # Custom separator

# Result: "Electronics > Computers > Laptops"
```

#### `path_ids: List[int]`

Get list of IDs from root to this node.

```python
await gaming_laptops.ancestors()
print(gaming_laptops.path_ids)
# [1, 5, 12, 47]  (Electronics.id, Computers.id, Laptops.id, Gaming Laptops.id)
```

**Use cases:**
- Building URL paths: `/categories/1/5/12/47`
- Checking if a category is in a specific branch
- Efficient ancestor checks

---

### Async Methods (Database Calls)

These methods query the database and must be awaited:

#### `ancestors(include_self=False, use_cte=None) → List[Self]`

Get all ancestors from immediate parent up to the root.

```python
# Basic usage
ancestors = await gaming_laptops.ancestors()
# [Laptops, Computers, Electronics]
# (Parent first, root last)

# Include self in the result
all_nodes = await gaming_laptops.ancestors(include_self=True)
# [Gaming Laptops, Laptops, Computers, Electronics]

# Force app-level traversal (works on all databases)
ancestors = await gaming_laptops.ancestors(use_cte=False)

# Force CTE (PostgreSQL only, faster)
ancestors = await gaming_laptops.ancestors(use_cte=True)
```

**Performance:**
- **PostgreSQL:** Single recursive CTE query (O(1) queries)
- **Other DBs:** One query per level (O(depth) queries)

**Use cases:**
- Building breadcrumb navigation
- Checking permissions up the hierarchy
- Computing inherited settings

---

#### `descendants(include_self=False, use_cte=None, max_depth=None) → List[Self]`

Get all descendants recursively (breadth-first order).

```python
# Get all descendants
all_children = await electronics.descendants()
# [Computers, Phones, Laptops, Desktops, Gaming Laptops]

# Include self
subtree = await electronics.descendants(include_self=True)
# [Electronics, Computers, Phones, Laptops, Desktops, Gaming Laptops]

# Limit depth (1 = direct children only)
direct_children = await electronics.descendants(max_depth=1)
# [Computers, Phones]

# Two levels deep
two_levels = await electronics.descendants(max_depth=2)
# [Computers, Phones, Laptops, Desktops]
```

**Performance:**
- **PostgreSQL:** Single recursive CTE query
- **Other DBs:** One query per level

**Use cases:**
- Displaying category trees
- Counting all items in a category and subcategories
- Bulk operations on entire subtrees

---

#### `root() → Self`

Get the root ancestor of this tree.

```python
gaming = await Category.get(gaming_laptops_id)
root = await gaming.root()
print(root.name)  # "Electronics"

# Root of a root is itself
electronics = await Category.get(electronics_id)
root = await electronics.root()
print(root.name)  # "Electronics"
```

**Use cases:**
- Finding the top-level category for a product
- Grouping items by their root category
- Navigation to the top of a tree

---

#### `depth() → int`

Get the depth level (root = 0).

```python
print(await electronics.depth())      # 0 (root)
print(await computers.depth())        # 1
print(await laptops.depth())          # 2
print(await gaming_laptops.depth())   # 3
```

**Use cases:**
- Indentation in tree views
- Limiting nesting depth
- Computing relative depths

---

#### `is_leaf() → bool`

Check if this node has no children.

```python
print(await electronics.is_leaf())     # False (has Computers, Phones)
print(await gaming_laptops.is_leaf())  # True (no children)
```

**Use cases:**
- Determining if products can be assigned (only to leaves)
- Conditional rendering (expandable vs non-expandable nodes)
- Validation rules

---

#### `siblings(include_self=False) → List[Self]`

Get nodes with the same parent.

```python
# Laptops and Desktops are siblings (both under Computers)
laptops_siblings = await laptops.siblings()
# [Desktops]

# Include self
all_under_computers = await laptops.siblings(include_self=True)
# [Laptops, Desktops]

# Root-level siblings
electronics_siblings = await electronics.siblings()
# [Clothing]
```

**Use cases:**
- "See also" recommendations
- Navigation between peer categories
- Reordering items at the same level

---

#### `subtree(include_self=True, max_depth=None) → List[Self]`

Get this node and all its descendants. Alias for `descendants(include_self=True)`.

```python
# Get entire subtree
full_subtree = await computers.subtree()
# [Computers, Laptops, Desktops, Gaming Laptops]

# Exclude self
just_descendants = await computers.subtree(include_self=False)
# [Laptops, Desktops, Gaming Laptops]
```

---

#### `children() → List[Self]`

Get direct children only (not recursive).

```python
direct_children = await electronics.children()
# [Computers, Phones]
# Does NOT include Laptops, Desktops, Gaming Laptops
```

**Difference from `descendants(max_depth=1)`:** Same result, but `children()` is more semantic and readable.

---

#### `parent() → Optional[Self]`

Get the parent node (or None for root).

```python
parent = await laptops.parent()
print(parent.name)  # "Computers"

root_parent = await electronics.parent()
print(root_parent)  # None
```

---

### Tree Modification Methods

#### `move_to(new_parent: Optional[Self]) → None`

Move this node to a new parent.

```python
# Move Laptops from Computers to Phones
laptops = await Category.get(laptops_id)
phones = await Category.get(phones_id)

await laptops.move_to(phones)

# Before: Electronics > Computers > Laptops
# After:  Electronics > Phones > Laptops
```

**Make it a root:**
```python
await laptops.move_to(None)
# Now Laptops is a root-level category
```

**Validation (automatic):**
```python
# Cannot move to self
await laptops.move_to(laptops)
# Raises: ValueError("Cannot move a node to itself")

# Cannot move to a descendant (would create cycle)
await electronics.move_to(gaming_laptops)
# Raises: ValueError("Cannot move a node to one of its descendants")
```

**Side effects:**
- Clears cached ancestors (path needs to be recalculated)
- Automatically saves the node

---

#### `make_root() → None`

Make this node a root (remove parent). Shortcut for `move_to(None)`.

```python
await computers.make_root()

# Before: Electronics > Computers > Laptops
# After:  Computers > Laptops (Computers is now a root)
```

---

## Real-World Examples

### E-Commerce Product Categories

```python
from pynext.db import Table, TreeMixin
from typing import Optional

class Category(Table, TreeMixin):
    """Product category with full tree support."""
    name: str
    slug: str
    parent_id: Optional[int]
    description: Optional[str]
    image_url: Optional[str]
    is_active: bool = True


# === Creating Categories ===

async def setup_categories():
    """Set up initial category tree."""
    # Root categories
    electronics = await Category.create(
        name="Electronics",
        slug="electronics",
        description="Electronic devices and accessories"
    )
    
    # Subcategories
    computers = await Category.create(
        name="Computers",
        slug="computers",
        parent_id=electronics.id
    )
    
    phones = await Category.create(
        name="Phones",
        slug="phones",
        parent_id=electronics.id
    )
    
    # Sub-subcategories
    laptops = await Category.create(
        name="Laptops",
        slug="laptops",
        parent_id=computers.id
    )
    
    return electronics, computers, phones, laptops


# === Building Breadcrumbs ===

async def get_breadcrumbs(category_id: int) -> list:
    """Build breadcrumb navigation for a category."""
    category = await Category.get(category_id)
    await category.ancestors()  # Populate cache
    
    # Build breadcrumb list
    breadcrumbs = []
    for node_id in category.path_ids:
        node = await Category.get(node_id)
        breadcrumbs.append({
            "name": node.name,
            "slug": node.slug,
            "url": f"/categories/{node.slug}"
        })
    
    return breadcrumbs

# Result: [
#   {"name": "Electronics", "slug": "electronics", "url": "/categories/electronics"},
#   {"name": "Computers", "slug": "computers", "url": "/categories/computers"},
#   {"name": "Laptops", "slug": "laptops", "url": "/categories/laptops"}
# ]


# === Category Tree for Sidebar ===

async def get_category_tree(max_depth: int = 3) -> list:
    """Build category tree for navigation sidebar."""
    # Get all root categories
    roots = await Category.select().where_null("parent_id")
    
    async def build_node(category, current_depth):
        node = {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "children": []
        }
        
        if current_depth < max_depth:
            children = await category.children()
            for child in children:
                child_node = await build_node(child, current_depth + 1)
                node["children"].append(child_node)
        
        return node
    
    tree = []
    for root in roots:
        tree.append(await build_node(root, 0))
    
    return tree


# === Product Count with Subcategories ===

async def count_products_in_category(category_id: int) -> int:
    """Count products in a category and all subcategories."""
    category = await Category.get(category_id)
    
    # Get all category IDs (this category + all descendants)
    subtree = await category.subtree()
    category_ids = [c.id for c in subtree]
    
    # Count products in all these categories
    count = await Product.select().where_in(category_id=category_ids).count()
    return count


# === Moving Categories ===

async def move_category(category_id: int, new_parent_id: Optional[int]):
    """Move a category to a new parent (with validation)."""
    category = await Category.get(category_id)
    
    if new_parent_id is None:
        await category.make_root()
    else:
        new_parent = await Category.get(new_parent_id)
        if new_parent is None:
            raise ValueError("Parent category not found")
        await category.move_to(new_parent)
    
    return category
```

---

### Comment Thread System

```python
from pynext.db import Table, TreeMixin
from typing import Optional
from datetime import datetime

class Comment(Table, TreeMixin):
    """Comment with nested replies support."""
    content: str
    author_id: int
    post_id: int
    parent_id: Optional[int]  # For replies
    created_at: datetime
    is_deleted: bool = False
    
    _tree_name_field = "content"  # Use content for path (if needed)


# === Creating Comments ===

async def create_comment(post_id: int, author_id: int, content: str, 
                         reply_to_id: Optional[int] = None) -> Comment:
    """Create a comment or reply."""
    return await Comment.create(
        content=content,
        author_id=author_id,
        post_id=post_id,
        parent_id=reply_to_id,
        created_at=datetime.utcnow()
    )


# === Loading Comment Thread ===

async def get_comment_thread(post_id: int) -> list:
    """Get all comments for a post as a threaded structure."""
    # Get root-level comments
    root_comments = await Comment.select().where(
        post_id=post_id,
        parent_id=None,
        is_deleted=False
    ).order_by("created_at")
    
    async def build_thread(comment):
        """Recursively build comment thread."""
        replies = await comment.children()
        return {
            "id": comment.id,
            "content": comment.content,
            "author_id": comment.author_id,
            "created_at": comment.created_at.isoformat(),
            "depth": await comment.depth(),
            "replies": [
                await build_thread(reply) 
                for reply in replies 
                if not reply.is_deleted
            ]
        }
    
    return [await build_thread(c) for c in root_comments]


# === Get Reply Context ===

async def get_reply_context(comment_id: int) -> dict:
    """Get context for replying to a comment."""
    comment = await Comment.get(comment_id)
    ancestors = await comment.ancestors()
    
    return {
        "replying_to": comment.content[:100],
        "thread_depth": await comment.depth(),
        "thread_root_id": (await comment.root()).id,
        "ancestor_authors": [a.author_id for a in ancestors]
    }


# === Collapse Deep Threads ===

async def get_comments_with_collapse(post_id: int, max_depth: int = 3) -> list:
    """Get comments, collapsing threads deeper than max_depth."""
    root_comments = await Comment.select().where(
        post_id=post_id,
        parent_id=None
    )
    
    async def build_with_collapse(comment, current_depth):
        children = await comment.children()
        
        if current_depth >= max_depth and children:
            # Collapse: just show count
            total_replies = len(await comment.descendants())
            return {
                "id": comment.id,
                "content": comment.content,
                "collapsed": True,
                "hidden_replies": total_replies
            }
        
        return {
            "id": comment.id,
            "content": comment.content,
            "collapsed": False,
            "replies": [
                await build_with_collapse(c, current_depth + 1)
                for c in children
            ]
        }
    
    return [await build_with_collapse(c, 0) for c in root_comments]
```

---

### Organizational Chart

```python
from pynext.db import Table, TreeMixin
from typing import Optional

class Employee(Table, TreeMixin):
    """Employee with reporting hierarchy."""
    name: str
    email: str
    title: str
    department: str
    manager_id: Optional[int]  # Reports to
    
    # Custom configuration
    _tree_parent_field = "manager_id"
    _tree_separator = " → "


# === Org Chart Queries ===

async def get_reporting_chain(employee_id: int) -> list:
    """Get the management chain above an employee."""
    employee = await Employee.get(employee_id)
    chain = await employee.ancestors()
    
    return [
        {"name": e.name, "title": e.title}
        for e in chain
    ]
    # [
    #   {"name": "Carol", "title": "Engineering Manager"},
    #   {"name": "Bob", "title": "VP Engineering"},
    #   {"name": "Alice", "title": "CEO"}
    # ]


async def get_all_reports(manager_id: int, direct_only: bool = False) -> list:
    """Get all employees reporting to a manager."""
    manager = await Employee.get(manager_id)
    
    if direct_only:
        reports = await manager.children()
    else:
        reports = await manager.descendants()
    
    return [
        {"id": e.id, "name": e.name, "title": e.title}
        for e in reports
    ]


async def get_org_level(employee_id: int) -> int:
    """Get organizational level (CEO = 0)."""
    employee = await Employee.get(employee_id)
    return await employee.depth()


async def get_team_size(manager_id: int) -> int:
    """Count all employees under a manager."""
    manager = await Employee.get(manager_id)
    return len(await manager.descendants())


async def can_approve(approver_id: int, requestor_id: int) -> bool:
    """Check if approver is in requestor's management chain."""
    requestor = await Employee.get(requestor_id)
    ancestors = await requestor.ancestors()
    ancestor_ids = {a.id for a in ancestors}
    return approver_id in ancestor_ids


async def transfer_employee(employee_id: int, new_manager_id: int):
    """Transfer an employee to a new manager."""
    employee = await Employee.get(employee_id)
    new_manager = await Employee.get(new_manager_id)
    
    await employee.move_to(new_manager)
    
    # Log the transfer
    print(f"{employee.name} now reports to {new_manager.name}")
```

---

### File/Folder System

```python
from pynext.db import Table, TreeMixin
from typing import Optional
from datetime import datetime

class Folder(Table, TreeMixin):
    """Folder with hierarchical structure."""
    name: str
    parent_id: Optional[int]
    created_at: datetime
    owner_id: int
    
    _tree_separator = "/"  # Unix-style paths


# === Path Operations ===

async def get_full_path(folder_id: int) -> str:
    """Get the full path to a folder."""
    folder = await Folder.get(folder_id)
    await folder.ancestors()
    return "/" + folder.path  # Prepend root slash


async def find_by_path(path: str) -> Optional[Folder]:
    """Find a folder by its path."""
    parts = path.strip("/").split("/")
    
    current = None
    for part in parts:
        if current is None:
            # Find root folder
            folders = await Folder.select().where(name=part, parent_id=None)
            current = folders[0] if folders else None
        else:
            # Find child folder
            children = await current.children()
            current = next((c for c in children if c.name == part), None)
        
        if current is None:
            return None
    
    return current


async def list_folder_contents(folder_id: int) -> dict:
    """List contents of a folder with metadata."""
    folder = await Folder.get(folder_id)
    children = await folder.children()
    
    return {
        "folder": folder.name,
        "path": await get_full_path(folder_id),
        "subfolders": [
            {
                "id": c.id,
                "name": c.name,
                "has_children": not await c.is_leaf()
            }
            for c in children
        ]
    }


async def move_folder(folder_id: int, new_parent_id: Optional[int]):
    """Move a folder to a new location."""
    folder = await Folder.get(folder_id)
    
    if new_parent_id is None:
        await folder.make_root()
    else:
        new_parent = await Folder.get(new_parent_id)
        await folder.move_to(new_parent)
    
    # Return new path
    await folder.ancestors()
    return "/" + folder.path


async def delete_folder_recursive(folder_id: int):
    """Delete a folder and all its contents."""
    folder = await Folder.get(folder_id)
    
    # Get all descendants (deepest first for deletion order)
    descendants = await folder.descendants()
    descendants.reverse()  # Delete children before parents
    
    # Delete all descendants
    for child in descendants:
        await child.delete()
    
    # Delete the folder itself
    await folder.delete()
```

---

## Configuration Options

### Custom Parent Field

```python
class Employee(Table, TreeMixin):
    name: str
    manager_id: Optional[int]  # Not parent_id
    
    _tree_parent_field = "manager_id"  # Tell TreeMixin which field to use
```

### Custom Name Field

```python
class Page(Table, TreeMixin):
    title: str
    slug: str
    parent_id: Optional[int]
    
    _tree_name_field = "title"  # Use title for path instead of name
```

Result: `"Home/Products/Electronics"` instead of using IDs

### Custom Path Separator

```python
class Namespace(Table, TreeMixin):
    name: str
    parent_id: Optional[int]
    
    _tree_separator = "::"  # C++-style namespaces
```

Result: `"std::string::npos"`

### All Options Together

```python
class OrgUnit(Table, TreeMixin):
    full_name: str
    code: str
    reports_to_id: Optional[int]
    
    _tree_parent_field = "reports_to_id"
    _tree_name_field = "code"
    _tree_separator = " > "
```

Result: `"CORP > TECH > ENG > FRONTEND"`

---

## Performance: CTE vs App-Level

PyNext uses a **hybrid strategy** for tree traversal:

### PostgreSQL: Recursive CTEs (Fast!)

When using PostgreSQL, PyNext generates efficient recursive Common Table Expressions:

```sql
-- Generated for ancestors()
WITH RECURSIVE ancestors AS (
    SELECT t.*, 1 as _depth
    FROM categories t
    WHERE t.id = (SELECT parent_id FROM categories WHERE id = $1)
    
    UNION ALL
    
    SELECT t.*, a._depth + 1
    FROM categories t
    JOIN ancestors a ON t.id = a.parent_id
)
SELECT * FROM ancestors ORDER BY _depth ASC
```

**Performance:** Single query, regardless of tree depth. O(1) queries.

### Other Databases: App-Level Traversal

For SQLite, MySQL without CTE support, etc.:

```python
# PyNext walks the tree level by level
async def _ancestors_app_level(self):
    ancestors = []
    current_parent_id = self.parent_id
    
    while current_parent_id is not None:
        parent = await Model.get(current_parent_id)
        ancestors.append(parent)
        current_parent_id = parent.parent_id
    
    return ancestors
```

**Performance:** One query per level. O(depth) queries.

### Force a Specific Strategy

```python
# Force CTE (fails on databases without CTE support)
ancestors = await node.ancestors(use_cte=True)

# Force app-level (works everywhere, slower on deep trees)
ancestors = await node.ancestors(use_cte=False)

# Auto-detect (default) - uses CTE if available
ancestors = await node.ancestors()
```

---

## Common Patterns

### Breadcrumb Navigation

```python
async def breadcrumbs(category_id: int):
    category = await Category.get(category_id)
    ancestors = await category.ancestors()
    
    # Build breadcrumb (root first)
    crumbs = [{"name": a.name, "url": f"/c/{a.slug}"} for a in reversed(ancestors)]
    crumbs.append({"name": category.name, "url": None})  # Current page
    
    return crumbs
```

### Tree Dropdown

```python
async def category_options():
    """Build <select> options with indentation."""
    options = []
    
    async def add_node(node, depth):
        indent = "—" * depth
        options.append({
            "value": node.id,
            "label": f"{indent} {node.name}" if indent else node.name
        })
        
        for child in await node.children():
            await add_node(child, depth + 1)
    
    roots = await Category.select().where_null("parent_id")
    for root in roots:
        await add_node(root, 0)
    
    return options
    # [
    #   {"value": 1, "label": "Electronics"},
    #   {"value": 2, "label": "— Computers"},
    #   {"value": 3, "label": "—— Laptops"},
    #   {"value": 4, "label": "— Phones"},
    # ]
```

### Inherited Settings

```python
async def get_setting(category_id: int, setting_name: str):
    """Get a setting, inheriting from ancestors if not set."""
    category = await Category.get(category_id)
    
    # Check this category
    value = getattr(category, setting_name, None)
    if value is not None:
        return value
    
    # Check ancestors
    for ancestor in await category.ancestors():
        value = getattr(ancestor, setting_name, None)
        if value is not None:
            return value
    
    return None  # No value found
```

### Permission Check

```python
async def has_access(user_id: int, category_id: int) -> bool:
    """Check if user has access to category or any parent."""
    category = await Category.get(category_id)
    
    # Get all category IDs to check (this + ancestors)
    all_ids = category.path_ids
    
    # Check if user has permission to any of these
    permission = await Permission.select().where(
        user_id=user_id
    ).where_in(category_id=all_ids).first()
    
    return permission is not None
```

---

## Edge Cases

### Orphan Nodes

If a node's parent doesn't exist (data integrity issue):

```python
orphan = Category(id=5, name="Orphan", parent_id=999)

# ancestors() handles this gracefully
ancestors = await orphan.ancestors()
# Returns: [] (empty, because parent 999 doesn't exist)

# depth() returns 0
depth = await orphan.depth()
# Returns: 0

# root() returns self
root = await orphan.root()
# Returns: orphan (itself)
```

### Deep Trees (100+ Levels)

PyNext handles deep trees efficiently:

```python
# 100 levels deep
for i in range(100):
    await Category.create(name=f"Level {i}", parent_id=i if i > 0 else None)

deepest = await Category.get(100)
ancestors = await deepest.ancestors()
# Returns all 99 ancestors
# PostgreSQL: 1 query (CTE)
# Other DBs: 99 queries (app-level)
```

### Wide Trees (1000+ Siblings)

```python
# 1000 children under one parent
root = await Category.create(name="Root")
for i in range(1000):
    await Category.create(name=f"Child {i}", parent_id=root.id)

# descendants() handles this
all_children = await root.descendants()
# Returns all 1000 children
```

### Multiple Independent Trees

```python
# Two separate category trees
electronics = await Category.create(name="Electronics")
clothing = await Category.create(name="Clothing")

# Each tree is independent
electronics_tree = await electronics.subtree()
clothing_tree = await clothing.subtree()
# No overlap
```

### Node with ID = 0

```python
# ID 0 is valid!
root = Category(id=0, name="Root")
child = Category(id=1, name="Child", parent_id=0)

# Works correctly
print(child.is_root)  # False (not None)
parent = await child.parent()
print(parent.id)  # 0
```

---

## SQLAlchemy Comparison

| Feature | SQLAlchemy | PyNext |
|---------|------------|--------|
| **Basic Setup** | `backref=backref("parent", remote_side=[id])` 😵 | `parent_id: Optional[int]` ✅ |
| **Get Ancestors** | Write your own CTE | `await node.ancestors()` |
| **Get Descendants** | Write your own CTE | `await node.descendants()` |
| **Get Path** | Not built-in | `node.path` |
| **Get Depth** | Not built-in | `await node.depth()` |
| **Check if Root** | `node.parent_id is None` | `node.is_root` |
| **Check if Leaf** | Query children | `await node.is_leaf()` |
| **Get Siblings** | Query + filter | `await node.siblings()` |
| **Move Node** | Manual, no validation | `await node.move_to(parent)` |
| **Cycle Prevention** | None (you crash) | Automatic validation |
| **CTE Support** | Manual SQL | Automatic |
| **Learning Curve** | High 📈 | Low 📉 |

---

## Troubleshooting

### "Path shows only node name"

**Problem:** `category.path` returns just `"Laptops"` instead of `"Electronics/Computers/Laptops"`.

**Solution:** Call `ancestors()` first to populate the cache:

```python
await category.ancestors()  # Populates cache
print(category.path)  # Now shows full path
```

### "Cannot move a node to one of its descendants"

**Problem:** `ValueError` when calling `move_to()`.

**Solution:** This is intentional! Moving a node to its own descendant would create a cycle. Check your logic:

```python
# This would create: A > B > A (cycle!)
await a.move_to(b)  # If B is a descendant of A
```

### "Ancestors returns empty for non-root"

**Problem:** Node has `parent_id` set but `ancestors()` returns `[]`.

**Cause:** The parent doesn't exist in the database (orphan node).

**Solution:** Fix your data integrity or handle gracefully:

```python
ancestors = await node.ancestors()
if not ancestors and not node.is_root:
    print(f"Warning: Orphan node {node.id}")
```

### "CTE queries not working"

**Problem:** Always using app-level traversal even on PostgreSQL.

**Solution:** Check that `supports_cte` is correctly detected. You can force CTE:

```python
ancestors = await node.ancestors(use_cte=True)
```

### "Performance is slow on deep trees"

**Problem:** Slow performance with 100+ level deep trees on non-PostgreSQL.

**Solution:** 
1. Use PostgreSQL for CTE support
2. Cache results when possible
3. Consider denormalizing (storing depth, path as columns)
