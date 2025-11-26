# Part 5: Task Detail & Forms

> **Build the task detail view with editing and comments**

In this part, we'll create the task detail page with a full edit form, validation, and a comments section.

---

## What We're Building

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Board                                           [Edit] [Delete] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📋 Research streaming SSR patterns                                 │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Status: 📋 Backlog          Priority: 🟡 Medium                   │   │
│  │  Project: 🚀 PyNext          Assignee: 👤 Jane Smith               │   │
│  │  Label: 🟢 Feature           Created: Nov 15, 2024                 │   │
│  │                                                                     │   │
│  │  ───────────────────────────────────────────────────────────────── │   │
│  │                                                                     │   │
│  │  Description                                                        │   │
│  │  Investigate how to implement streaming SSR similar to React 18    │   │
│  │  Suspense boundaries. Look at prior art from Next.js and Remix.    │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Comments (2)                                                       │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  👤 John Doe • 2 hours ago                                          │   │
│  │  I found some useful resources on streaming. Will share links.     │   │
│  │                                                                     │   │
│  │  👤 Jane Smith • 1 hour ago                                         │   │
│  │  Thanks! Let's discuss in our next sync.                           │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Add a comment...                                            │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                    [Post Comment]   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create the Task Detail Page

Create `pages/tasks/[id].py`:

```python
"""
Task Detail Page

Shows full task details with edit capability and comments.
Dynamic route: /tasks/123 extracts id=123
"""

from pynext import page, server_action, div, h1, p, a, span, form
from pynext.tw import tw, cn
from pynext.shadcn import (
    Button, Card, CardHeader, CardTitle, CardContent,
    Badge, Avatar, AvatarFallback, Separator,
    Dialog, DialogTrigger, DialogContent, DialogHeader,
    DialogTitle, DialogFooter,
    AlertDialog, AlertDialogTrigger, AlertDialogContent,
    AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
    AlertDialogFooter, AlertDialogAction, AlertDialogCancel,
)

from db.queries import get_task, get_users, get_labels, get_projects, update_task, delete_task
from db.models import Task
from components.task_form import TaskEditForm
from components.comments import CommentSection


@page(title="Task - PyTask")
def task_detail(id: str):
    """
    Task detail page.
    
    The `id` parameter comes from the [id].py filename.
    """
    task_id = int(id)
    task = get_task(task_id)
    
    if not task:
        return NotFoundState()
    
    return div(class_=tw.p_8.max_w_4xl.mx_auto)[
        # Back navigation
        BackButton(),
        
        # Main task card
        TaskDetailCard(task),
        
        # Comments section
        div(class_="mt-6")[
            CommentSection(task_id=task.id),
        ],
    ]


def BackButton():
    """Navigation back to the board."""
    return a(
        href="/board",
        class_=cn(
            "inline-flex items-center gap-2 text-sm text-muted-foreground",
            "hover:text-foreground mb-4",
        ),
    )[
        "← Back to Board"
    ]


def TaskDetailCard(task: Task):
    """Main card showing task details."""
    return Card()[
        CardHeader(class_="flex flex-row items-start justify-between")[
            div()[
                div(class_="flex items-center gap-2 mb-2")[
                    span(class_="text-xl")[task.status_emoji],
                    CardTitle(class_="text-xl")[task.title],
                ],
                TaskMetadata(task),
            ],
            div(class_="flex gap-2")[
                EditTaskButton(task),
                DeleteTaskButton(task),
            ],
        ],
        
        Separator(),
        
        CardContent(class_="pt-6")[
            # Description
            div()[
                h3(class_="font-medium mb-2")["Description"],
                task.description and p(class_="text-muted-foreground whitespace-pre-wrap")[
                    task.description
                ] or p(class_="text-muted-foreground italic")[
                    "No description provided"
                ],
            ],
        ],
    ]


def TaskMetadata(task: Task):
    """Grid of task metadata."""
    return div(class_="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4")[
        MetadataItem(
            label="Status",
            value=f"{task.status_emoji} {task.status.replace('_', ' ').title()}",
        ),
        MetadataItem(
            label="Priority",
            value=f"{task.priority_emoji} {task.priority.title()}",
        ),
        MetadataItem(
            label="Project",
            value=task.project.name if task.project else "—",
            icon=task.project.icon if task.project else None,
        ),
        MetadataItem(
            label="Assignee",
            value=task.assignee.name if task.assignee else "Unassigned",
            avatar=task.assignee,
        ),
        task.label and MetadataItem(
            label="Label",
            value=task.label.name,
            badge_color=task.label.color,
        ),
        MetadataItem(
            label="Created",
            value=format_date(task.created_at),
        ),
    ]


def MetadataItem(label: str, value: str, icon: str = None, avatar=None, badge_color: str = None):
    """A single metadata field."""
    return div(class_="space-y-1")[
        span(class_="text-xs text-muted-foreground")[label],
        div(class_="flex items-center gap-2")[
            icon and span()[icon],
            avatar and Avatar(class_="h-5 w-5")[
                AvatarFallback(class_="text-xs")[avatar.initials]
            ],
            badge_color and Badge(
                variant="outline",
                class_=f"border-{badge_color}-500 text-{badge_color}-500",
            )[value] or span(class_="text-sm font-medium")[value],
        ],
    ]


def EditTaskButton(task: Task):
    """Button that opens edit dialog."""
    return Dialog()[
        DialogTrigger()[
            Button(variant="outline", size="sm")["Edit"]
        ],
        DialogContent(class_="sm:max-w-lg")[
            DialogHeader()[
                DialogTitle()["Edit Task"],
            ],
            TaskEditForm(task),
        ],
    ]


def DeleteTaskButton(task: Task):
    """Button that opens delete confirmation."""
    return AlertDialog()[
        AlertDialogTrigger()[
            Button(variant="destructive", size="sm")["Delete"]
        ],
        AlertDialogContent()[
            AlertDialogHeader()[
                AlertDialogTitle()["Delete this task?"],
                AlertDialogDescription()[
                    f'This will permanently delete "{task.title}". '
                    "This action cannot be undone."
                ],
            ],
            AlertDialogFooter()[
                AlertDialogCancel()["Cancel"],
                AlertDialogAction(
                    on_click=lambda: handle_delete(task.id),
                    class_="bg-destructive text-destructive-foreground",
                )["Delete"],
            ],
        ],
    ]


def NotFoundState():
    """Shown when task doesn't exist."""
    return div(class_="text-center py-12")[
        div(class_="text-4xl mb-4")["🔍"],
        h1(class_="text-xl font-bold mb-2")["Task not found"],
        p(class_="text-muted-foreground mb-4")[
            "This task may have been deleted."
        ],
        Button()[
            a(href="/board")["Back to Board"]
        ],
    ]


def format_date(dt) -> str:
    """Format a datetime for display."""
    if not dt:
        return "—"
    if isinstance(dt, str):
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt
    return dt.strftime("%b %d, %Y")


# Server action for deletion
@server_action
async def handle_delete(task_id: int):
    """Delete a task and redirect to board."""
    delete_task(task_id)
    # In a real app, this would redirect
    return {"success": True, "redirect": "/board"}
```

---

## Step 2: Create the Task Edit Form

Create `components/task_form.py`:

```python
"""
Task Form Component

Form for creating and editing tasks with validation.
"""

from pynext import div, form, span, server_action
from pynext.tw import tw, cn
from pynext.shadcn import (
    Button, Input, Label, Textarea,
    DialogFooter, DialogClose,
)

from db.queries import get_users, get_labels, get_projects, update_task, create_task
from db.models import Task, TASK_STATUSES, TASK_PRIORITIES
from typing import Optional


@server_action
async def save_task(data: dict):
    """
    Server action to save task changes.
    
    Handles both creating and updating tasks.
    """
    task_id = data.get("task_id")
    
    # Validate required fields
    if not data.get("title"):
        return {"success": False, "error": "Title is required"}
    
    if not data.get("project_id"):
        return {"success": False, "error": "Project is required"}
    
    # Prepare data
    task_data = {
        "title": data["title"].strip(),
        "description": data.get("description", "").strip() or None,
        "status": data.get("status", "backlog"),
        "priority": data.get("priority", "medium"),
        "project_id": int(data["project_id"]),
        "assignee_id": int(data["assignee_id"]) if data.get("assignee_id") else None,
        "label_id": int(data["label_id"]) if data.get("label_id") else None,
    }
    
    if task_id:
        # Update existing task
        update_task(int(task_id), **task_data)
        return {"success": True, "message": "Task updated"}
    else:
        # Create new task
        new_id = create_task(**task_data)
        return {"success": True, "message": "Task created", "id": new_id}


def TaskEditForm(task: Optional[Task] = None):
    """
    Form for editing or creating a task.
    
    Args:
        task: Existing task to edit, or None for new task
    """
    users = get_users()
    labels = get_labels()
    projects = get_projects()
    
    return form(action=save_task, class_="space-y-4")[
        # Hidden task ID for updates
        task and input(type="hidden", name="task_id", value=str(task.id)),
        
        # Title
        FormField(
            name="title",
            label="Title",
            required=True,
            value=task.title if task else "",
            placeholder="What needs to be done?",
        ),
        
        # Description
        FormTextarea(
            name="description",
            label="Description",
            value=task.description if task else "",
            placeholder="Add more details...",
            rows=3,
        ),
        
        # Two-column layout for dropdowns
        div(class_="grid grid-cols-2 gap-4")[
            # Status
            FormSelect(
                name="status",
                label="Status",
                options=[(s, s.replace("_", " ").title()) for s in TASK_STATUSES],
                value=task.status if task else "backlog",
            ),
            
            # Priority
            FormSelect(
                name="priority",
                label="Priority",
                options=[(p, p.title()) for p in TASK_PRIORITIES],
                value=task.priority if task else "medium",
            ),
        ],
        
        div(class_="grid grid-cols-2 gap-4")[
            # Project
            FormSelect(
                name="project_id",
                label="Project",
                options=[(p.id, f"{p.icon} {p.name}") for p in projects],
                value=task.project_id if task else None,
                required=True,
            ),
            
            # Assignee
            FormSelect(
                name="assignee_id",
                label="Assignee",
                options=[(u.id, u.name) for u in users],
                value=task.assignee_id if task else None,
                placeholder="Unassigned",
            ),
        ],
        
        # Label
        FormSelect(
            name="label_id",
            label="Label",
            options=[(l.id, l.name) for l in labels],
            value=task.label_id if task else None,
            placeholder="No label",
        ),
        
        # Submit buttons
        DialogFooter(class_="mt-6")[
            DialogClose()[
                Button(variant="outline", type="button")["Cancel"]
            ],
            Button(type="submit")[
                "Update Task" if task else "Create Task"
            ],
        ],
    ]


def FormField(
    name: str,
    label: str,
    type: str = "text",
    value: str = "",
    placeholder: str = "",
    required: bool = False,
    error: str = None,
):
    """A form field with label and optional error."""
    return div(class_="space-y-2")[
        Label(html_for=name)[
            label,
            required and span(class_="text-destructive ml-1")["*"],
        ],
        Input(
            id=name,
            name=name,
            type=type,
            value=value,
            placeholder=placeholder,
            required=required,
            class_=cn(error and "border-destructive"),
        ),
        error and span(class_="text-sm text-destructive")[error],
    ]


def FormTextarea(
    name: str,
    label: str,
    value: str = "",
    placeholder: str = "",
    rows: int = 3,
    error: str = None,
):
    """A textarea field with label."""
    return div(class_="space-y-2")[
        Label(html_for=name)[label],
        Textarea(
            id=name,
            name=name,
            value=value,
            placeholder=placeholder,
            rows=rows,
            class_=cn(error and "border-destructive"),
        ),
        error and span(class_="text-sm text-destructive")[error],
    ]


def FormSelect(
    name: str,
    label: str,
    options: list,
    value=None,
    placeholder: str = None,
    required: bool = False,
    error: str = None,
):
    """A select dropdown with label."""
    return div(class_="space-y-2")[
        Label(html_for=name)[
            label,
            required and span(class_="text-destructive ml-1")["*"],
        ],
        select(
            id=name,
            name=name,
            required=required,
            class_=cn(
                "w-full h-10 rounded-md border border-input bg-background",
                "px-3 py-2 text-sm ring-offset-background",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
                error and "border-destructive",
            ),
        )[
            placeholder and option(value="")[placeholder],
            [
                option(
                    value=str(opt_value),
                    selected=str(opt_value) == str(value) if value else False,
                )[opt_label]
                for opt_value, opt_label in options
            ],
        ],
        error and span(class_="text-sm text-destructive")[error],
    ]
```

---

## Step 3: Create the Comments Component

Create `components/comments.py`:

```python
"""
Comments Component

Display and add comments on a task.
"""

from pynext import div, form, span, server_action, Signal
from pynext.tw import tw, cn
from pynext.shadcn import (
    Button, Textarea, Card, CardHeader, CardTitle, CardContent,
    Avatar, AvatarFallback, Separator,
)

from db import get_db
from db.models import Comment, User
from typing import List


@server_action
async def add_comment(task_id: int, content: str, user_id: int = 1):
    """Add a comment to a task."""
    if not content or not content.strip():
        return {"success": False, "error": "Comment cannot be empty"}
    
    with get_db() as db:
        db.execute(
            "INSERT INTO comments (content, task_id, user_id) VALUES (?, ?, ?)",
            (content.strip(), task_id, user_id)
        )
    
    return {"success": True, "message": "Comment added"}


def get_comments(task_id: int) -> List[Comment]:
    """Get all comments for a task."""
    with get_db() as db:
        rows = db.execute("""
            SELECT c.*, u.name as user_name, u.avatar_url
            FROM comments c
            LEFT JOIN users u ON u.id = c.user_id
            WHERE c.task_id = ?
            ORDER BY c.created_at ASC
        """, (task_id,)).fetchall()
        
        comments = []
        for row in rows:
            row_dict = dict(row)
            comment = Comment(
                id=row_dict["id"],
                content=row_dict["content"],
                task_id=row_dict["task_id"],
                user_id=row_dict["user_id"],
                created_at=row_dict["created_at"],
            )
            comment.user = User(
                id=row_dict["user_id"],
                name=row_dict["user_name"] or "Unknown",
                email="",
                avatar_url=row_dict.get("avatar_url"),
            )
            comments.append(comment)
        
        return comments


def CommentSection(task_id: int):
    """Complete comments section with list and form."""
    comments = get_comments(task_id)
    
    return Card()[
        CardHeader()[
            CardTitle(class_="text-lg")[
                f"Comments ({len(comments)})"
            ],
        ],
        CardContent(class_="space-y-4")[
            # Comment list
            comments and div(class_="space-y-4")[
                [CommentItem(comment) for comment in comments]
            ] or EmptyComments(),
            
            Separator(class_="my-4"),
            
            # New comment form
            CommentForm(task_id),
        ],
    ]


def CommentItem(comment: Comment):
    """A single comment."""
    return div(class_="flex gap-3")[
        Avatar(class_="h-8 w-8 flex-shrink-0")[
            AvatarFallback(class_="text-xs")[
                comment.user.initials if comment.user else "?"
            ]
        ],
        div(class_="flex-1")[
            div(class_="flex items-center gap-2 mb-1")[
                span(class_="font-medium text-sm")[
                    comment.user.name if comment.user else "Unknown"
                ],
                span(class_="text-xs text-muted-foreground")[
                    format_time_ago(comment.created_at)
                ],
            ],
            p(class_="text-sm text-muted-foreground whitespace-pre-wrap")[
                comment.content
            ],
        ],
    ]


def CommentForm(task_id: int):
    """Form to add a new comment."""
    return form(action=lambda data: add_comment(task_id, data.get("content", "")))[
        div(class_="space-y-3")[
            Textarea(
                name="content",
                placeholder="Add a comment...",
                rows=2,
                class_="resize-none",
            ),
            div(class_="flex justify-end")[
                Button(type="submit", size="sm")["Post Comment"],
            ],
        ],
    ]


def EmptyComments():
    """Shown when there are no comments."""
    return div(class_="text-center py-6 text-muted-foreground")[
        span(class_="text-2xl block mb-2")["💬"],
        span(class_="text-sm")["No comments yet"],
    ]


def format_time_ago(timestamp) -> str:
    """Format timestamp as relative time."""
    if not timestamp:
        return "Just now"
    
    from datetime import datetime
    
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return "Recently"
    
    now = datetime.now()
    diff = now - timestamp
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    else:
        days = int(seconds / 86400)
        return f"{days}d ago"
```

---

## Step 4: Add Form Validation

Let's enhance the form with client-side validation hints:

```python
# Add to components/task_form.py

def ValidatedInput(
    name: str,
    label: str,
    value: str = "",
    placeholder: str = "",
    required: bool = False,
    min_length: int = None,
    max_length: int = None,
    pattern: str = None,
    help_text: str = None,
):
    """
    Input with validation attributes.
    
    Uses HTML5 validation for immediate feedback.
    """
    return div(class_="space-y-2")[
        Label(html_for=name)[
            label,
            required and span(class_="text-destructive ml-1")["*"],
        ],
        Input(
            id=name,
            name=name,
            value=value,
            placeholder=placeholder,
            required=required,
            minlength=min_length,
            maxlength=max_length,
            pattern=pattern,
            class_="peer",
        ),
        # Validation messages
        help_text and span(class_="text-xs text-muted-foreground")[
            help_text
        ],
        # Error shown when invalid
        span(class_=cn(
            "text-xs text-destructive hidden",
            "peer-invalid:peer-focus:block",
        ))[
            "Please fill out this field correctly"
        ],
    ]
```

---

## Step 5: Test the Task Detail

1. Make sure your database has tasks:
   ```bash
   python -m db.seed
   ```

2. Start the dev server:
   ```bash
   pynext dev
   ```

3. Go to `/board` and click on a task card

4. You should see:
   - Task details with all metadata
   - Edit button that opens a form dialog
   - Delete button with confirmation
   - Comments section with add form

---

## What We Built

In this part, we:

- Created a dynamic route for task details (`[id].py`)
- Built a comprehensive task detail view
- Made an edit form with all task fields
- Added form validation
- Created a comments section with add functionality
- Implemented delete with confirmation

### Component Summary

| Component | Purpose |
|-----------|---------|
| `TaskDetailCard` | Main task information |
| `TaskMetadata` | Grid of task properties |
| `TaskEditForm` | Form for editing tasks |
| `CommentSection` | List and form for comments |
| `FormField` / `FormSelect` | Reusable form components |

### Key Patterns Learned

| Pattern | Example |
|---------|---------|
| **Dynamic Routes** | `[id].py` captures URL parameter |
| **Server Actions** | `@server_action` for form handling |
| **Form Validation** | HTML5 attributes + server validation |
| **Dialogs** | `Dialog` for edit, `AlertDialog` for delete |

---

## Next Up

In **Part 6**, we'll build the settings pages for projects, labels, and team management.

[**Continue to Part 6: Project Settings →**](./06-settings.md)

---

## Troubleshooting

### "Task not found" on all tasks?

Make sure the URL parameter is being parsed correctly. Check that you're visiting `/tasks/1` (not `/tasks/`).

### Form not submitting?

Check that `@server_action` decorator is on the handler function and it's `async`.

### Comments not saving?

Verify the database has the `comments` table:
```bash
python -c "from db import init_db; init_db()"
```

