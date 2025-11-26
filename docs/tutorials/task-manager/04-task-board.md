# Part 4: Task Board (Kanban View)

> **Build an interactive Kanban board with status columns**

In this part, we'll create the main task board with columns for each status, task cards with all the details, and server actions to update task status.

---

## What We're Building

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Task Board                                    [Filter ▼] [+ New Task]      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 📋 BACKLOG  │ │ 📝 TODO     │ │ 🔄 IN PROG  │ │ ✅ DONE     │           │
│  │     (3)     │ │     (5)     │ │     (2)     │ │     (6)     │           │
│  ├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤           │
│  │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │           │
│  │ │ Research│ │ │ │ Form    │ │ │ │ Build   │ │ │ │ CI/CD   │ │           │
│  │ │ SSR     │ │ │ │ validat │ │ │ │ CLI     │ │ │ │ setup   │ │           │
│  │ │         │ │ │ │         │ │ │ │         │ │ │ │         │ │           │
│  │ │ 🟡 Med  │ │ │ │ 🟠 High │ │ │ │ 🟠 High │ │ │ │ ✓ Done  │ │           │
│  │ │ 👤 Jane │ │ │ │ 👤 John │ │ │ │ 👤 Jane │ │ │ │ 👤 Jane │ │           │
│  │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │           │
│  │             │ │             │ │             │ │             │           │
│  │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │           │
│  │ │ Edge    │ │ │ │ TypeScr │ │ │ │ Optimi  │ │ │ │ Guide   │ │           │
│  │ │ runtime │ │ │ │ -ipt    │ │ │ │ -ze     │ │ │ │ written │ │           │
│  │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │           │
│  │             │ │             │ │             │ │             │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create the Task Card Component

Create `components/task_card.py`:

```python
"""
Task Card Component

Displays a task in the Kanban board.
Shows title, priority, assignee, and labels.
"""

from pynext import div, span, a
from pynext.tw import tw, cn
from pynext.shadcn import (
    Card, Badge, Avatar, AvatarFallback,
    DropdownMenu, DropdownMenuTrigger, DropdownMenuContent,
    DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel,
    Button,
)

from db.models import Task


def TaskCard(task: Task, on_status_change=None):
    """
    A card representing a single task.
    
    Args:
        task: Task object from the database
        on_status_change: Optional callback for status changes
    """
    return a(href=f"/tasks/{task.id}")[
        Card(class_=cn(
            "p-3 cursor-pointer transition-all",
            "hover:shadow-md hover:border-primary/50",
            "group",
        ))[
            # Task header with title and menu
            div(class_="flex items-start justify-between gap-2 mb-2")[
                span(class_="text-sm font-medium leading-tight line-clamp-2")[
                    task.title
                ],
                TaskMenu(task),
            ],
            
            # Task metadata
            div(class_="flex items-center justify-between")[
                # Left side: priority and label
                div(class_="flex items-center gap-2")[
                    PriorityBadge(task.priority),
                    task.label and LabelBadge(task.label),
                ],
                
                # Right side: assignee
                task.assignee and AssigneeAvatar(task.assignee),
            ],
            
            # Comment count (if any)
            task.comment_count > 0 and div(class_="mt-2 text-xs text-muted-foreground")[
                f"💬 {task.comment_count}"
            ],
        ],
    ]


def TaskMenu(task: Task):
    """Dropdown menu for task actions."""
    return DropdownMenu()[
        DropdownMenuTrigger()[
            Button(
                variant="ghost",
                size="icon",
                class_="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity",
            )["⋮"],
        ],
        DropdownMenuContent(align="end")[
            DropdownMenuLabel()["Move to"],
            DropdownMenuSeparator(),
            StatusMenuItem("backlog", "📋 Backlog", task),
            StatusMenuItem("todo", "📝 Todo", task),
            StatusMenuItem("in_progress", "🔄 In Progress", task),
            StatusMenuItem("done", "✅ Done", task),
            DropdownMenuSeparator(),
            DropdownMenuItem(class_="text-destructive")["🗑️ Delete"],
        ],
    ]


def StatusMenuItem(status: str, label: str, task: Task):
    """Menu item for changing task status."""
    is_current = task.status == status
    return DropdownMenuItem(
        disabled=is_current,
        class_=cn("cursor-pointer", is_current and "opacity-50"),
    )[label]


def PriorityBadge(priority: str):
    """Badge showing task priority."""
    colors = {
        "low": "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
        "medium": "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
        "high": "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
        "urgent": "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
    }
    
    icons = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "urgent": "🔴",
    }
    
    return span(class_=cn(
        "text-xs px-1.5 py-0.5 rounded",
        colors.get(priority, colors["medium"]),
    ))[
        f"{icons.get(priority, '')} {priority.title()}"
    ]


def LabelBadge(label):
    """Badge showing task label."""
    return Badge(
        variant="outline",
        class_=cn("text-xs", label.color_class.replace("bg-", "border-")),
    )[label.name]


def AssigneeAvatar(user):
    """Small avatar for task assignee."""
    return Avatar(class_="h-6 w-6")[
        AvatarFallback(class_="text-xs")[user.initials]
    ]
```

---

## Step 2: Create the Board Column Component

Create `components/board_column.py`:

```python
"""
Board Column Component

A column in the Kanban board containing tasks of a specific status.
"""

from pynext import div, span
from pynext.tw import tw, cn
from pynext.shadcn import Button

from db.models import Task
from components.task_card import TaskCard
from typing import List


# Column configuration
COLUMNS = {
    "backlog": {
        "title": "Backlog",
        "icon": "📋",
        "color": "border-t-slate-500",
    },
    "todo": {
        "title": "Todo",
        "icon": "📝",
        "color": "border-t-blue-500",
    },
    "in_progress": {
        "title": "In Progress",
        "icon": "🔄",
        "color": "border-t-yellow-500",
    },
    "done": {
        "title": "Done",
        "icon": "✅",
        "color": "border-t-green-500",
    },
}


def BoardColumn(status: str, tasks: List[Task], class_: str = ""):
    """
    A column in the Kanban board.
    
    Args:
        status: The status this column represents
        tasks: List of tasks to display
        class_: Additional CSS classes
    """
    config = COLUMNS.get(status, COLUMNS["backlog"])
    
    return div(class_=cn(
        "flex flex-col min-w-[280px] max-w-[320px]",
        "bg-muted/30 rounded-lg",
        "border-t-4",
        config["color"],
        class_,
    ))[
        # Column header
        ColumnHeader(
            title=config["title"],
            icon=config["icon"],
            count=len(tasks),
            status=status,
        ),
        
        # Task list
        div(class_="flex-1 overflow-y-auto p-2 space-y-2")[
            [TaskCard(task) for task in tasks]
            if tasks else EmptyColumn(status),
        ],
    ]


def ColumnHeader(title: str, icon: str, count: int, status: str):
    """Header for a board column."""
    return div(class_="flex items-center justify-between p-3 border-b border-border")[
        div(class_="flex items-center gap-2")[
            span()[icon],
            span(class_="font-medium")[title],
            span(class_=cn(
                "text-xs bg-muted px-2 py-0.5 rounded-full",
                "text-muted-foreground",
            ))[str(count)],
        ],
        Button(
            variant="ghost",
            size="icon",
            class_="h-6 w-6 opacity-60 hover:opacity-100",
        )["+"],
    ]


def EmptyColumn(status: str):
    """Empty state for a column with no tasks."""
    messages = {
        "backlog": "No tasks in backlog",
        "todo": "Nothing to do!",
        "in_progress": "Nothing in progress",
        "done": "No completed tasks",
    }
    
    return div(class_="text-center py-8 text-muted-foreground text-sm")[
        messages.get(status, "No tasks"),
    ]


def Board(tasks: List[Task], class_: str = ""):
    """
    Complete Kanban board with all columns.
    
    Args:
        tasks: All tasks (will be sorted into columns)
    """
    # Group tasks by status
    tasks_by_status = {
        "backlog": [],
        "todo": [],
        "in_progress": [],
        "done": [],
    }
    
    for task in tasks:
        if task.status in tasks_by_status:
            tasks_by_status[task.status].append(task)
    
    return div(class_=cn(
        "flex gap-4 overflow-x-auto pb-4",
        "min-h-[calc(100vh-200px)]",
        class_,
    ))[
        [
            BoardColumn(status, column_tasks)
            for status, column_tasks in tasks_by_status.items()
        ]
    ]
```

---

## Step 3: Create Filter Component

Create `components/board_filters.py`:

```python
"""
Board Filters Component

Filters for the task board: by assignee, label, priority.
"""

from pynext import div, span, select, option
from pynext.tw import tw, cn
from pynext.shadcn import Button, Badge

from db.models import User, Label
from typing import List, Optional


def BoardFilters(
    users: List[User],
    labels: List[Label],
    current_assignee: Optional[int] = None,
    current_label: Optional[int] = None,
    current_priority: Optional[str] = None,
    class_: str = "",
):
    """
    Filter controls for the task board.
    """
    return div(class_=cn("flex flex-wrap items-center gap-3", class_))[
        # Assignee filter
        FilterSelect(
            name="assignee",
            placeholder="All Members",
            options=[(u.id, u.name) for u in users],
            value=current_assignee,
        ),
        
        # Label filter
        FilterSelect(
            name="label",
            placeholder="All Labels",
            options=[(l.id, l.name) for l in labels],
            value=current_label,
        ),
        
        # Priority filter
        FilterSelect(
            name="priority",
            placeholder="All Priorities",
            options=[
                ("urgent", "🔴 Urgent"),
                ("high", "🟠 High"),
                ("medium", "🟡 Medium"),
                ("low", "🟢 Low"),
            ],
            value=current_priority,
        ),
        
        # Clear filters button
        (current_assignee or current_label or current_priority) and Button(
            variant="ghost",
            size="sm",
            class_="text-muted-foreground",
        )["Clear filters"],
    ]


def FilterSelect(
    name: str,
    placeholder: str,
    options: list,
    value=None,
):
    """A filter dropdown."""
    return select(
        name=name,
        class_=cn(
            "h-9 rounded-md border border-input bg-background px-3",
            "text-sm ring-offset-background",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        ),
    )[
        option(value="", selected=value is None)[placeholder],
        [
            option(
                value=str(opt_value),
                selected=str(opt_value) == str(value),
            )[opt_label]
            for opt_value, opt_label in options
        ],
    ]


def ActiveFilters(filters: dict, class_: str = ""):
    """Display active filters as badges."""
    if not any(filters.values()):
        return None
    
    return div(class_=cn("flex items-center gap-2", class_))[
        span(class_="text-sm text-muted-foreground")["Filters:"],
        [
            Badge(variant="secondary", class_="gap-1")[
                f"{key}: {value}",
                Button(variant="ghost", size="icon", class_="h-4 w-4 ml-1")["×"],
            ]
            for key, value in filters.items()
            if value
        ],
    ]
```

---

## Step 4: Create Server Actions for Task Updates

Create `pages/api/tasks.py` for API routes, or use server actions directly.

Let's add server actions to `pages/board.py`:

```python
"""
Task Board Page

Kanban-style board for managing tasks.
"""

from pynext import page, server_action, div, h1, p
from pynext.tw import tw, cn
from pynext.shadcn import Button

from db.queries import get_tasks, get_users, get_labels, update_task, log_activity
from components.board_column import Board
from components.board_filters import BoardFilters
from components.quick_task import QuickTaskButton


@server_action
async def change_task_status(task_id: int, new_status: str, user_id: int = 1):
    """
    Server action to update a task's status.
    
    This runs on the server and can access the database directly.
    """
    # Validate status
    valid_statuses = ["backlog", "todo", "in_progress", "done"]
    if new_status not in valid_statuses:
        return {"success": False, "error": "Invalid status"}
    
    # Update the task
    update_task(task_id, status=new_status)
    
    # Log the activity
    log_activity(
        action="moved",
        entity_type="task",
        entity_id=task_id,
        user_id=user_id,
        details=f"Moved to {new_status.replace('_', ' ').title()}",
    )
    
    return {"success": True, "status": new_status}


@server_action
async def change_task_priority(task_id: int, new_priority: str, user_id: int = 1):
    """Server action to update a task's priority."""
    valid_priorities = ["low", "medium", "high", "urgent"]
    if new_priority not in valid_priorities:
        return {"success": False, "error": "Invalid priority"}
    
    update_task(task_id, priority=new_priority)
    
    log_activity(
        action="updated",
        entity_type="task",
        entity_id=task_id,
        user_id=user_id,
        details=f"Priority changed to {new_priority}",
    )
    
    return {"success": True, "priority": new_priority}


@page(title="Task Board - PyTask")
def board():
    """
    Kanban task board page.
    
    Displays tasks in columns by status.
    """
    # Get query parameters for filters
    # In a real app, you'd parse these from the request
    filter_assignee = None
    filter_label = None
    filter_priority = None
    
    # Fetch data
    tasks = get_tasks(
        assignee_id=filter_assignee,
        label_id=filter_label,
    )
    
    # Filter by priority if specified
    if filter_priority:
        tasks = [t for t in tasks if t.priority == filter_priority]
    
    users = get_users()
    labels = get_labels()
    
    return div(class_=tw.p_6.h_full.flex.flex_col)[
        # Header
        div(class_=cn(
            "flex flex-col sm:flex-row sm:items-center sm:justify-between",
            "gap-4 mb-6",
        ))[
            div()[
                h1(class_=tw.text_2xl.font_bold)["Task Board"],
                p(class_=tw.text_muted_foreground.text_sm)[
                    f"Showing {len(tasks)} tasks"
                ],
            ],
            div(class_="flex items-center gap-3")[
                BoardFilters(
                    users=users,
                    labels=labels,
                    current_assignee=filter_assignee,
                    current_label=filter_label,
                    current_priority=filter_priority,
                ),
                QuickTaskButton(),
            ],
        ],
        
        # Board
        div(class_="flex-1 overflow-hidden")[
            Board(tasks),
        ],
    ]
```

---

## Step 5: Add Click-to-Move Functionality

Update `components/task_card.py` to use the server action:

```python
# Add to task_card.py

from pynext import server_action

@server_action
async def move_task(task_id: int, status: str):
    """Move a task to a new status."""
    from db.queries import update_task, log_activity
    
    update_task(task_id, status=status)
    log_activity(
        action="moved",
        entity_type="task",
        entity_id=task_id,
        user_id=1,  # TODO: get current user
        details=f"Moved to {status.replace('_', ' ').title()}",
    )
    
    return {"success": True}


def StatusMenuItem(status: str, label: str, task: Task):
    """Menu item for changing task status."""
    is_current = task.status == status
    
    return DropdownMenuItem(
        disabled=is_current,
        class_=cn("cursor-pointer", is_current and "opacity-50"),
        on_click=lambda: move_task(task.id, status) if not is_current else None,
    )[label]
```

---

## Step 6: Add Keyboard Navigation

Let's add basic keyboard navigation for power users using PyNext's keyboard module. Create `shortcuts.py`:

```python
"""
Keyboard Shortcuts

Define keyboard shortcuts using PyNext's built-in keyboard module.
No JavaScript required!
"""

from pynext.keyboard import on_keydown
from pynext import Signal


# State for new task dialog
new_task_open = Signal(False)


@on_keydown("n", context="global")
def open_new_task():
    """
    Open new task dialog with N key.
    
    The `context="global"` means this won't fire when typing in inputs.
    """
    new_task_open.set(True)


@on_keydown("/", context="global")
def focus_search():
    """
    Focus search input with / key.
    
    PyNext handles preventDefault automatically.
    """
    # This will be handled by the command palette in Part 7
    from shortcuts import palette_open
    palette_open.set(True)


@on_keydown("escape", context="dialog")
def close_dialogs():
    """Close any open dialogs with Escape."""
    new_task_open.set(False)
```

Then include the `ShortcutProvider` in your layout (we'll do this fully in Part 7):

```python
from pynext.keyboard import ShortcutProvider

@layout
def board_layout(children):
    return ShortcutProvider()[
        children
    ]
```

**Why this is better:**
- No raw JavaScript to maintain
- Automatic `context="global"` skips input fields  
- Type-safe shortcut definitions
- Integration with PyNext's signal system

---

## Step 7: Test the Board

Make sure your database is seeded:

```bash
python -m db.seed
```

Start the dev server:

```bash
pynext dev
```

Visit `http://localhost:3000/board` and you should see:

1. **Four columns** (Backlog, Todo, In Progress, Done)
2. **Task cards** with title, priority, assignee
3. **Filter dropdowns** for assignee, label, priority
4. **"+ New Task"** button

Try:
- Clicking on a task card (opens task detail - we'll build in Part 5)
- Using the dropdown menu on a task to change status
- Filtering by assignee or label

---

## What We Built

In this part, we:

- Created task cards with priority badges and assignee avatars
- Built Kanban columns that group tasks by status
- Added filter components for assignee, label, and priority
- Implemented server actions for updating task status
- Added keyboard navigation basics

### Component Summary

| Component | Purpose |
|-----------|---------|
| `TaskCard` | Single task with all metadata |
| `TaskMenu` | Dropdown for task actions |
| `PriorityBadge` | Colored priority indicator |
| `BoardColumn` | Column for a status |
| `Board` | Complete Kanban board |
| `BoardFilters` | Filter dropdowns |

### Key Patterns Learned

| Pattern | Example |
|---------|---------|
| **Server Actions** | `@server_action` for database updates |
| **Grouping Data** | Sorting tasks into columns by status |
| **Conditional Styling** | Different colors for priorities |
| **Empty States** | Friendly messages when no tasks |
| **Keyboard Shortcuts** | `@on_keydown` for power-user navigation |

---

## Next Up

In **Part 5**, we'll build the task detail page with edit form, validation, and comments.

[**Continue to Part 5: Task Detail & Forms →**](./05-task-detail.md)

---

## Troubleshooting

### Tasks not showing in columns?

Check that tasks have valid status values (`backlog`, `todo`, `in_progress`, `done`).

### Server action not working?

Make sure you're using `@server_action` decorator and the function is `async`.

### Filter dropdowns not updating?

Filters need JavaScript to submit. We'll add this properly in Part 7.

