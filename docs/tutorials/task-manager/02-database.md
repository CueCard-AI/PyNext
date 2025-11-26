# Part 2: Database & Models

> **Set up SQLite and define our data models**

In this part, we'll create the data layer for PyTask using SQLite. We'll define models for tasks, projects, users, and labels, then seed the database with sample data.

---

## What We're Building

By the end of this part, you'll have:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Database Schema                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   users     │     │  projects   │     │   labels    │       │
│  ├─────────────┤     ├─────────────┤     ├─────────────┤       │
│  │ id          │     │ id          │     │ id          │       │
│  │ name        │     │ name        │     │ name        │       │
│  │ email       │     │ description │     │ color       │       │
│  │ avatar_url  │     │ created_at  │     │ project_id  │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                   │                   │               │
│         └─────────┬─────────┴─────────┬─────────┘               │
│                   │                   │                         │
│                   ▼                   ▼                         │
│            ┌─────────────────────────────────┐                  │
│            │            tasks                │                  │
│            ├─────────────────────────────────┤                  │
│            │ id, title, description          │                  │
│            │ status, priority                │                  │
│            │ project_id, assignee_id         │                  │
│            │ label_id, created_at            │                  │
│            └─────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create the Database Module

Create a `db/` directory for all database code:

```bash
mkdir -p db
touch db/__init__.py
```

Create `db/__init__.py`:

```python
"""
Database module for PyTask.

Provides connection management and query execution utilities.
Uses SQLite for simplicity - no external database required.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Any

# Database file location
DB_PATH = Path(__file__).parent.parent / "pytask.db"


def get_connection() -> sqlite3.Connection:
    """
    Get a database connection with row factory enabled.
    
    Row factory lets us access columns by name instead of index:
        row["title"] instead of row[0]
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """
    Context manager for database connections.
    
    Usage:
        with get_db() as db:
            db.execute("SELECT * FROM tasks")
    
    Automatically commits on success, rolls back on error,
    and closes the connection when done.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    Initialize the database schema.
    
    Creates all tables if they don't exist.
    Safe to call multiple times.
    """
    with get_db() as db:
        # Enable foreign keys
        db.execute("PRAGMA foreign_keys = ON")
        
        # Create users table
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create projects table
        db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                icon TEXT DEFAULT '📁',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create labels table
        db.execute("""
            CREATE TABLE IF NOT EXISTS labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                project_id INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # Create tasks table
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'backlog',
                priority TEXT DEFAULT 'medium',
                project_id INTEGER NOT NULL,
                assignee_id INTEGER,
                label_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (assignee_id) REFERENCES users(id),
                FOREIGN KEY (label_id) REFERENCES labels(id)
            )
        """)
        
        # Create comments table
        db.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create activity log table
        db.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        print("Database initialized successfully!")


# Initialize on import if database doesn't exist
if not DB_PATH.exists():
    init_db()
```

**What's happening here:**

1. **DB_PATH** - SQLite database file in project root
2. **get_connection()** - Creates a connection with row factory
3. **get_db()** - Context manager for safe connection handling
4. **init_db()** - Creates all tables with proper foreign keys

---

## Step 2: Create Data Models

Create `db/models.py`:

```python
"""
Data models for PyTask.

These are simple dataclasses that represent our database entities.
They provide type hints and convenient methods for serialization.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List


# Valid status values
TASK_STATUSES = ["backlog", "todo", "in_progress", "done"]

# Valid priority values
TASK_PRIORITIES = ["low", "medium", "high", "urgent"]


@dataclass
class User:
    """A team member who can be assigned tasks."""
    id: int
    name: str
    email: str
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @property
    def initials(self) -> str:
        """Get user initials (e.g., 'John Doe' -> 'JD')"""
        parts = self.name.split()
        return "".join(p[0].upper() for p in parts[:2])


@dataclass
class Project:
    """A project that contains tasks."""
    id: int
    name: str
    description: Optional[str] = None
    icon: str = "📁"
    created_at: Optional[datetime] = None
    
    # Related data (loaded separately)
    task_count: int = 0
    completed_count: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @property
    def progress(self) -> int:
        """Get completion percentage."""
        if self.task_count == 0:
            return 0
        return int((self.completed_count / self.task_count) * 100)


@dataclass
class Label:
    """A label/tag for categorizing tasks."""
    id: int
    name: str
    color: str  # Tailwind color class, e.g., "red", "blue"
    project_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @property
    def color_class(self) -> str:
        """Get Tailwind background color class."""
        colors = {
            "red": "bg-red-500",
            "orange": "bg-orange-500",
            "yellow": "bg-yellow-500",
            "green": "bg-green-500",
            "blue": "bg-blue-500",
            "purple": "bg-purple-500",
            "pink": "bg-pink-500",
            "gray": "bg-gray-500",
        }
        return colors.get(self.color, "bg-gray-500")


@dataclass
class Task:
    """A task/issue in a project."""
    id: int
    title: str
    project_id: int
    description: Optional[str] = None
    status: str = "backlog"
    priority: str = "medium"
    assignee_id: Optional[int] = None
    label_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data (loaded separately)
    assignee: Optional[User] = None
    label: Optional[Label] = None
    project: Optional[Project] = None
    comment_count: int = 0
    
    def to_dict(self) -> dict:
        data = asdict(self)
        # Remove related objects for serialization
        data.pop("assignee", None)
        data.pop("label", None)
        data.pop("project", None)
        return data
    
    @property
    def status_emoji(self) -> str:
        """Get emoji for task status."""
        emojis = {
            "backlog": "📋",
            "todo": "📝",
            "in_progress": "🔄",
            "done": "✅",
        }
        return emojis.get(self.status, "📋")
    
    @property
    def priority_emoji(self) -> str:
        """Get emoji for priority level."""
        emojis = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "urgent": "🔴",
        }
        return emojis.get(self.priority, "🟡")


@dataclass
class Comment:
    """A comment on a task."""
    id: int
    content: str
    task_id: int
    user_id: int
    created_at: Optional[datetime] = None
    
    # Related data
    user: Optional[User] = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop("user", None)
        return data


@dataclass
class Activity:
    """An activity log entry."""
    id: int
    action: str  # "created", "updated", "moved", "completed"
    entity_type: str  # "task", "project", "comment"
    entity_id: int
    user_id: int
    details: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Related data
    user: Optional[User] = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop("user", None)
        return data
    
    @property
    def action_text(self) -> str:
        """Get human-readable action text."""
        actions = {
            "created": "created",
            "updated": "updated",
            "moved": "moved",
            "completed": "completed",
            "commented": "commented on",
        }
        return actions.get(self.action, self.action)
```

**What's happening here:**

1. **Dataclasses** - Clean, typed data structures
2. **to_dict()** - Serialization for JSON/templates
3. **Properties** - Computed values like `initials`, `progress`
4. **Constants** - Valid values for status/priority

---

## Step 3: Create Query Functions

Create `db/queries.py`:

```python
"""
Database query functions for PyTask.

Provides functions to read and write data.
Each function handles its own database connection.
"""

from typing import List, Optional
from db import get_db
from db.models import User, Project, Label, Task, Comment, Activity


# ============================================================================
# USER QUERIES
# ============================================================================

def get_users() -> List[User]:
    """Get all users."""
    with get_db() as db:
        rows = db.execute("SELECT * FROM users ORDER BY name").fetchall()
        return [User(**dict(row)) for row in rows]


def get_user(user_id: int) -> Optional[User]:
    """Get a user by ID."""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return User(**dict(row)) if row else None


# ============================================================================
# PROJECT QUERIES
# ============================================================================

def get_projects() -> List[Project]:
    """Get all projects with task counts."""
    with get_db() as db:
        rows = db.execute("""
            SELECT 
                p.*,
                COUNT(t.id) as task_count,
                SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) as completed_count
            FROM projects p
            LEFT JOIN tasks t ON t.project_id = p.id
            GROUP BY p.id
            ORDER BY p.name
        """).fetchall()
        return [Project(**dict(row)) for row in rows]


def get_project(project_id: int) -> Optional[Project]:
    """Get a project by ID with task counts."""
    with get_db() as db:
        row = db.execute("""
            SELECT 
                p.*,
                COUNT(t.id) as task_count,
                SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) as completed_count
            FROM projects p
            LEFT JOIN tasks t ON t.project_id = p.id
            WHERE p.id = ?
            GROUP BY p.id
        """, (project_id,)).fetchone()
        return Project(**dict(row)) if row else None


def create_project(name: str, description: str = None, icon: str = "📁") -> int:
    """Create a new project and return its ID."""
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO projects (name, description, icon) VALUES (?, ?, ?)",
            (name, description, icon)
        )
        return cursor.lastrowid


# ============================================================================
# LABEL QUERIES
# ============================================================================

def get_labels(project_id: int = None) -> List[Label]:
    """Get labels, optionally filtered by project."""
    with get_db() as db:
        if project_id:
            rows = db.execute(
                "SELECT * FROM labels WHERE project_id = ? OR project_id IS NULL",
                (project_id,)
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM labels").fetchall()
        return [Label(**dict(row)) for row in rows]


def create_label(name: str, color: str, project_id: int = None) -> int:
    """Create a new label and return its ID."""
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO labels (name, color, project_id) VALUES (?, ?, ?)",
            (name, color, project_id)
        )
        return cursor.lastrowid


# ============================================================================
# TASK QUERIES
# ============================================================================

def get_tasks(
    project_id: int = None,
    status: str = None,
    assignee_id: int = None,
    label_id: int = None,
) -> List[Task]:
    """
    Get tasks with optional filters.
    
    Includes related user, label, and project data.
    """
    with get_db() as db:
        query = """
            SELECT 
                t.*,
                u.name as assignee_name,
                u.email as assignee_email,
                u.avatar_url as assignee_avatar,
                l.name as label_name,
                l.color as label_color,
                p.name as project_name,
                (SELECT COUNT(*) FROM comments c WHERE c.task_id = t.id) as comment_count
            FROM tasks t
            LEFT JOIN users u ON u.id = t.assignee_id
            LEFT JOIN labels l ON l.id = t.label_id
            LEFT JOIN projects p ON p.id = t.project_id
            WHERE 1=1
        """
        params = []
        
        if project_id:
            query += " AND t.project_id = ?"
            params.append(project_id)
        
        if status:
            query += " AND t.status = ?"
            params.append(status)
        
        if assignee_id:
            query += " AND t.assignee_id = ?"
            params.append(assignee_id)
        
        if label_id:
            query += " AND t.label_id = ?"
            params.append(label_id)
        
        query += " ORDER BY t.updated_at DESC"
        
        rows = db.execute(query, params).fetchall()
        
        tasks = []
        for row in rows:
            row_dict = dict(row)
            
            # Build Task with related objects
            task = Task(
                id=row_dict["id"],
                title=row_dict["title"],
                description=row_dict["description"],
                status=row_dict["status"],
                priority=row_dict["priority"],
                project_id=row_dict["project_id"],
                assignee_id=row_dict["assignee_id"],
                label_id=row_dict["label_id"],
                created_at=row_dict["created_at"],
                updated_at=row_dict["updated_at"],
                comment_count=row_dict["comment_count"],
            )
            
            # Attach related user
            if row_dict.get("assignee_name"):
                task.assignee = User(
                    id=row_dict["assignee_id"],
                    name=row_dict["assignee_name"],
                    email=row_dict["assignee_email"],
                    avatar_url=row_dict["assignee_avatar"],
                )
            
            # Attach related label
            if row_dict.get("label_name"):
                task.label = Label(
                    id=row_dict["label_id"],
                    name=row_dict["label_name"],
                    color=row_dict["label_color"],
                )
            
            tasks.append(task)
        
        return tasks


def get_task(task_id: int) -> Optional[Task]:
    """Get a single task by ID with all related data."""
    with get_db() as db:
        row = db.execute("""
            SELECT 
                t.*,
                u.name as assignee_name,
                u.email as assignee_email,
                u.avatar_url as assignee_avatar,
                l.name as label_name,
                l.color as label_color,
                p.name as project_name,
                (SELECT COUNT(*) FROM comments c WHERE c.task_id = t.id) as comment_count
            FROM tasks t
            LEFT JOIN users u ON u.id = t.assignee_id
            LEFT JOIN labels l ON l.id = t.label_id
            LEFT JOIN projects p ON p.id = t.project_id
            WHERE t.id = ?
        """, (task_id,)).fetchone()
        
        if not row:
            return None
        
        row_dict = dict(row)
        task = Task(
            id=row_dict["id"],
            title=row_dict["title"],
            description=row_dict["description"],
            status=row_dict["status"],
            priority=row_dict["priority"],
            project_id=row_dict["project_id"],
            assignee_id=row_dict["assignee_id"],
            label_id=row_dict["label_id"],
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
            comment_count=row_dict["comment_count"],
        )
        
        if row_dict.get("assignee_name"):
            task.assignee = User(
                id=row_dict["assignee_id"],
                name=row_dict["assignee_name"],
                email=row_dict["assignee_email"],
                avatar_url=row_dict["assignee_avatar"],
            )
        
        if row_dict.get("label_name"):
            task.label = Label(
                id=row_dict["label_id"],
                name=row_dict["label_name"],
                color=row_dict["label_color"],
            )
        
        return task


def create_task(
    title: str,
    project_id: int,
    description: str = None,
    status: str = "backlog",
    priority: str = "medium",
    assignee_id: int = None,
    label_id: int = None,
) -> int:
    """Create a new task and return its ID."""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO tasks 
            (title, description, status, priority, project_id, assignee_id, label_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, description, status, priority, project_id, assignee_id, label_id))
        return cursor.lastrowid


def update_task(task_id: int, **fields) -> bool:
    """
    Update a task's fields.
    
    Usage:
        update_task(1, status="done", priority="high")
    """
    if not fields:
        return False
    
    with get_db() as db:
        # Build SET clause dynamically
        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [task_id]
        
        db.execute(f"""
            UPDATE tasks 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        
        return True


def delete_task(task_id: int) -> bool:
    """Delete a task by ID."""
    with get_db() as db:
        db.execute("DELETE FROM comments WHERE task_id = ?", (task_id,))
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return True


# ============================================================================
# STATS QUERIES
# ============================================================================

def get_dashboard_stats() -> dict:
    """Get statistics for the dashboard."""
    with get_db() as db:
        # Task counts by status
        status_counts = {}
        for status in ["backlog", "todo", "in_progress", "done"]:
            row = db.execute(
                "SELECT COUNT(*) as count FROM tasks WHERE status = ?",
                (status,)
            ).fetchone()
            status_counts[status] = row["count"]
        
        # Total tasks
        total = sum(status_counts.values())
        
        return {
            "total": total,
            "backlog": status_counts["backlog"],
            "todo": status_counts["todo"],
            "in_progress": status_counts["in_progress"],
            "done": status_counts["done"],
            "active": total - status_counts["done"],
        }


# ============================================================================
# ACTIVITY QUERIES
# ============================================================================

def get_recent_activity(limit: int = 10) -> List[Activity]:
    """Get recent activity entries."""
    with get_db() as db:
        rows = db.execute("""
            SELECT 
                a.*,
                u.name as user_name,
                u.avatar_url as user_avatar
            FROM activity a
            LEFT JOIN users u ON u.id = a.user_id
            ORDER BY a.created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
        activities = []
        for row in rows:
            row_dict = dict(row)
            activity = Activity(
                id=row_dict["id"],
                action=row_dict["action"],
                entity_type=row_dict["entity_type"],
                entity_id=row_dict["entity_id"],
                user_id=row_dict["user_id"],
                details=row_dict["details"],
                created_at=row_dict["created_at"],
            )
            if row_dict.get("user_name"):
                activity.user = User(
                    id=row_dict["user_id"],
                    name=row_dict["user_name"],
                    email="",
                    avatar_url=row_dict["user_avatar"],
                )
            activities.append(activity)
        
        return activities


def log_activity(
    action: str,
    entity_type: str,
    entity_id: int,
    user_id: int,
    details: str = None,
) -> int:
    """Log an activity entry."""
    with get_db() as db:
        cursor = db.execute("""
            INSERT INTO activity (action, entity_type, entity_id, user_id, details)
            VALUES (?, ?, ?, ?, ?)
        """, (action, entity_type, entity_id, user_id, details))
        return cursor.lastrowid
```

---

## Step 4: Create Seed Data

Create `db/seed.py`:

```python
"""
Seed data for PyTask.

Run this script to populate the database with sample data:
    python -m db.seed
"""

from db import get_db, init_db
from db.queries import (
    create_project, create_label, create_task, log_activity
)


def seed_database():
    """Populate database with sample data."""
    
    # Initialize schema first
    init_db()
    
    with get_db() as db:
        # Clear existing data
        db.execute("DELETE FROM activity")
        db.execute("DELETE FROM comments")
        db.execute("DELETE FROM tasks")
        db.execute("DELETE FROM labels")
        db.execute("DELETE FROM projects")
        db.execute("DELETE FROM users")
        
        # Reset auto-increment
        db.execute("DELETE FROM sqlite_sequence")
    
    print("Seeding users...")
    with get_db() as db:
        db.execute("""
            INSERT INTO users (name, email, avatar_url) VALUES
            ('Jane Smith', 'jane@example.com', NULL),
            ('John Doe', 'john@example.com', NULL),
            ('Alice Johnson', 'alice@example.com', NULL)
        """)
    
    print("Seeding projects...")
    proj_pynext = create_project("PyNext", "The PyNext framework", "🚀")
    proj_docs = create_project("Documentation", "Docs and tutorials", "📚")
    proj_api = create_project("API", "Backend API development", "🔌")
    
    print("Seeding labels...")
    # Global labels
    label_bug = create_label("Bug", "red")
    label_feature = create_label("Feature", "green")
    label_docs = create_label("Docs", "yellow")
    label_enhancement = create_label("Enhancement", "blue")
    label_urgent = create_label("Urgent", "orange")
    
    print("Seeding tasks...")
    # PyNext project tasks
    tasks = [
        # Backlog
        ("Research streaming SSR patterns", proj_pynext, "backlog", "medium", 1, label_feature),
        ("Investigate edge runtime support", proj_pynext, "backlog", "low", None, label_feature),
        ("Review community feedback", proj_pynext, "backlog", "low", None, None),
        
        # Todo
        ("Implement form validation helpers", proj_pynext, "todo", "high", 2, label_feature),
        ("Add TypeScript definitions", proj_pynext, "todo", "medium", 1, label_enhancement),
        ("Create migration guide", proj_pynext, "todo", "medium", 3, label_docs),
        ("Fix hydration mismatch warning", proj_pynext, "todo", "high", 2, label_bug),
        
        # In Progress
        ("Build component registry CLI", proj_pynext, "in_progress", "high", 1, label_feature),
        ("Optimize bundle size", proj_pynext, "in_progress", "medium", 2, label_enhancement),
        
        # Done
        ("Set up CI/CD pipeline", proj_pynext, "done", "high", 1, None),
        ("Write getting started guide", proj_pynext, "done", "medium", 3, label_docs),
        ("Implement dark mode", proj_pynext, "done", "low", 2, label_feature),
        
        # Docs project
        ("Write API reference", proj_docs, "todo", "high", 3, label_docs),
        ("Create video tutorials", proj_docs, "backlog", "medium", None, label_docs),
        ("Update changelog", proj_docs, "done", "low", 3, label_docs),
        
        # API project
        ("Design REST endpoints", proj_api, "in_progress", "high", 2, label_feature),
        ("Implement authentication", proj_api, "todo", "urgent", 1, label_feature),
        ("Add rate limiting", proj_api, "backlog", "medium", None, label_enhancement),
        ("Fix CORS issues", proj_api, "done", "high", 2, label_bug),
    ]
    
    for title, project_id, status, priority, assignee_id, label_id in tasks:
        task_id = create_task(
            title=title,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            label_id=label_id,
        )
    
    print("Seeding activity...")
    activities = [
        ("completed", "task", 10, 1, "Set up CI/CD pipeline"),
        ("moved", "task", 8, 1, "Moved to In Progress"),
        ("created", "task", 7, 2, "Fix hydration mismatch warning"),
        ("completed", "task", 11, 3, "Write getting started guide"),
        ("commented", "task", 8, 2, "Added component list"),
        ("updated", "task", 4, 2, "Updated priority to high"),
        ("completed", "task", 12, 2, "Implement dark mode"),
    ]
    
    for action, entity_type, entity_id, user_id, details in activities:
        log_activity(action, entity_type, entity_id, user_id, details)
    
    print("\n✅ Database seeded successfully!")
    print("   - 3 users")
    print("   - 3 projects")
    print("   - 5 labels")
    print("   - 19 tasks")
    print("   - 7 activity entries")


if __name__ == "__main__":
    seed_database()
```

Run the seed script:

```bash
python -m db.seed
```

---

## Step 5: Test the Database

Let's verify everything works. Create a quick test:

```bash
python -c "
from db.queries import get_projects, get_tasks, get_dashboard_stats

print('Projects:')
for p in get_projects():
    print(f'  - {p.name}: {p.task_count} tasks, {p.progress}% complete')

print()
print('Dashboard Stats:')
stats = get_dashboard_stats()
for k, v in stats.items():
    print(f'  - {k}: {v}')

print()
print('Recent Tasks:')
for t in get_tasks()[:5]:
    assignee = t.assignee.name if t.assignee else 'Unassigned'
    print(f'  - [{t.status}] {t.title} ({assignee})')
"
```

You should see output like:

```
Projects:
  - API: 4 tasks, 25% complete
  - Documentation: 3 tasks, 33% complete
  - PyNext: 12 tasks, 25% complete

Dashboard Stats:
  - total: 19
  - backlog: 5
  - todo: 5
  - in_progress: 3
  - done: 6
  - active: 13

Recent Tasks:
  - [done] Fix CORS issues (John Doe)
  - [backlog] Add rate limiting (Unassigned)
  - [todo] Implement authentication (Jane Smith)
  - [in_progress] Design REST endpoints (John Doe)
  - [done] Update changelog (Alice Johnson)
```

---

## What We Built

In this part, we:

- Set up SQLite with proper connection management
- Created models for Users, Projects, Labels, Tasks, Comments, and Activity
- Built query functions with filtering and related data loading
- Seeded the database with realistic sample data

### Key Concepts Learned

| Concept | What We Learned |
|---------|-----------------|
| **Context Managers** | Safe database connection handling |
| **Dataclasses** | Clean, typed data structures |
| **SQL Joins** | Loading related data efficiently |
| **Computed Properties** | Deriving values like `initials`, `progress` |

### Database Schema

```
users (id, name, email, avatar_url)
projects (id, name, description, icon)
labels (id, name, color, project_id)
tasks (id, title, description, status, priority, project_id, assignee_id, label_id)
comments (id, content, task_id, user_id)
activity (id, action, entity_type, entity_id, user_id, details)
```

---

## Next Up

In **Part 3**, we'll build the dashboard using this data, creating stats cards, an activity feed, and project overview.

[**Continue to Part 3: Building the Dashboard →**](./03-dashboard.md)

---

## Troubleshooting

### "No module named 'db'" error?

Make sure you have `db/__init__.py` file created.

### Database not found?

Run the seed script:
```bash
python -m db.seed
```

### Foreign key errors?

SQLite has foreign keys disabled by default. We enable them in `get_db()`:
```python
db.execute("PRAGMA foreign_keys = ON")
```

