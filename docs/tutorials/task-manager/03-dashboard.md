# Part 3: Building the Dashboard

> **Create an informative dashboard with real data**

In this part, we'll build the main dashboard with stats cards, an activity feed, and project overview — all powered by the database we set up in Part 2.

---

## What We're Building

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Dashboard                                                  + New Task      │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │     19       │ │      5       │ │      3       │ │      6       │       │
│  │  Total Tasks │ │     Todo     │ │  In Progress │ │   Completed  │       │
│  │   ────────   │ │   ────────   │ │   ────────   │ │   ────────   │       │
│  │  All tasks   │ │  Ready to    │ │  Being       │ │  Done this   │       │
│  │              │ │  start       │ │  worked on   │ │  week        │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
│                                                                             │
│  ┌─────────────────────────────────────┐ ┌─────────────────────────────┐   │
│  │ Recent Activity                     │ │ Projects Overview           │   │
│  ├─────────────────────────────────────┤ ├─────────────────────────────┤   │
│  │ 👤 Jane completed "Set up CI/CD"    │ │ 🚀 PyNext                   │   │
│  │    2 minutes ago                    │ │    ████████░░ 12 tasks      │   │
│  │                                     │ │                             │   │
│  │ 👤 John moved task to In Progress  │ │ 📚 Documentation            │   │
│  │    15 minutes ago                   │ │    ██████░░░░ 3 tasks       │   │
│  │                                     │ │                             │   │
│  │ 👤 Alice created "Write guide"     │ │ 🔌 API                      │   │
│  │    1 hour ago                       │ │    ████░░░░░░ 4 tasks       │   │
│  └─────────────────────────────────────┘ └─────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create Dashboard Components

First, let's create reusable components for the dashboard.

### Stats Card Component

Create `components/stats_card.py`:

```python
"""
Stats Card Component

Displays a metric with label and optional trend indicator.
Used on the dashboard for task statistics.
"""

from pynext import div, span
from pynext.tw import tw, cn
from pynext.shadcn import Card, CardHeader, CardTitle, CardContent


def StatsCard(
    title: str,
    value: str | int,
    description: str = "",
    icon: str = None,
    trend: str = None,  # "up", "down", or None
    trend_value: str = None,  # e.g., "+12%"
    class_: str = "",
):
    """
    A card displaying a statistic with optional trend.
    
    Args:
        title: Label for the stat (e.g., "Total Tasks")
        value: The main number to display
        description: Helper text below the value
        icon: Optional emoji/icon
        trend: Direction of change ("up" or "down")
        trend_value: Text showing change (e.g., "+12%")
    """
    trend_colors = {
        "up": "text-green-600",
        "down": "text-red-600",
    }
    
    trend_icons = {
        "up": "↑",
        "down": "↓",
    }
    
    return Card(class_=cn("relative overflow-hidden", class_))[
        CardHeader(class_="flex flex-row items-center justify-between pb-2")[
            CardTitle(class_="text-sm font-medium text-muted-foreground")[
                title
            ],
            icon and span(class_="text-2xl opacity-80")[icon],
        ],
        CardContent()[
            div(class_="flex items-baseline gap-2")[
                # Main value
                span(class_="text-3xl font-bold")[str(value)],
                
                # Trend indicator
                trend and trend_value and span(class_=cn(
                    "text-sm font-medium",
                    trend_colors.get(trend, ""),
                ))[
                    f"{trend_icons.get(trend, '')} {trend_value}"
                ],
            ],
            
            # Description
            description and div(class_="text-xs text-muted-foreground mt-1")[
                description
            ],
        ],
        
        # Decorative gradient
        div(class_=cn(
            "absolute inset-0 bg-gradient-to-br opacity-5",
            "from-primary to-transparent",
        )),
    ]
```

### Activity Feed Component

Create `components/activity_feed.py`:

```python
"""
Activity Feed Component

Shows recent actions in the system.
Used on the dashboard to show team activity.
"""

from pynext import div, span, a
from pynext.tw import tw, cn
from pynext.shadcn import Card, CardHeader, CardTitle, CardContent, Avatar, AvatarFallback

from db.models import Activity
from typing import List


def ActivityFeed(activities: List[Activity], class_: str = ""):
    """
    Display a list of recent activities.
    
    Args:
        activities: List of Activity objects from the database
        class_: Additional CSS classes
    """
    return Card(class_=class_)[
        CardHeader()[
            CardTitle(class_="text-lg")["Recent Activity"],
        ],
        CardContent()[
            div(class_="space-y-4")[
                [ActivityItem(activity) for activity in activities]
            ] if activities else EmptyState(),
        ],
    ]


def ActivityItem(activity: Activity):
    """A single activity entry."""
    # Get user info
    user_name = activity.user.name if activity.user else "Unknown"
    user_initials = activity.user.initials if activity.user else "?"
    
    # Format time (in a real app, use a proper time formatting library)
    time_ago = format_time_ago(activity.created_at)
    
    return div(class_="flex gap-3")[
        # User avatar
        Avatar(class_="h-8 w-8 flex-shrink-0")[
            AvatarFallback(class_="text-xs")[user_initials]
        ],
        
        # Activity details
        div(class_="flex-1 min-w-0")[
            div(class_="text-sm")[
                span(class_="font-medium")[user_name],
                span(class_="text-muted-foreground")[
                    f" {activity.action_text} "
                ],
                activity.details and span(class_="font-medium")[
                    f'"{activity.details}"'
                ],
            ],
            div(class_="text-xs text-muted-foreground mt-0.5")[
                time_ago
            ],
        ],
    ]


def EmptyState():
    """Shown when there's no activity."""
    return div(class_="text-center py-8 text-muted-foreground")[
        div(class_="text-3xl mb-2")["📭"],
        div(class_="text-sm")["No recent activity"],
    ]


def format_time_ago(timestamp) -> str:
    """
    Format a timestamp as relative time.
    
    In production, use a library like `humanize` or `timeago`.
    This is a simplified version for the tutorial.
    """
    if not timestamp:
        return "Just now"
    
    from datetime import datetime
    
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except:
            return "Recently"
    
    now = datetime.now()
    if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo:
        now = datetime.now(timestamp.tzinfo)
    
    diff = now - timestamp
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return timestamp.strftime("%b %d, %Y")
```

### Project Card Component

Create `components/project_card.py`:

```python
"""
Project Card Component

Shows a project with progress bar and task count.
Used on the dashboard for project overview.
"""

from pynext import div, span, a
from pynext.tw import tw, cn
from pynext.shadcn import Card, CardHeader, CardTitle, CardContent

from db.models import Project


def ProjectCard(project: Project, class_: str = ""):
    """
    Display a project with progress indicator.
    
    Args:
        project: Project object from the database
        class_: Additional CSS classes
    """
    return a(href=f"/projects/{project.id}")[
        Card(class_=cn(
            "hover:shadow-md transition-shadow cursor-pointer",
            class_,
        ))[
            CardHeader(class_="pb-2")[
                div(class_="flex items-center gap-2")[
                    span(class_="text-xl")[project.icon],
                    CardTitle(class_="text-base")[project.name],
                ],
            ],
            CardContent()[
                # Progress bar
                div(class_="space-y-2")[
                    div(class_="flex justify-between text-sm")[
                        span(class_="text-muted-foreground")[
                            f"{project.task_count} tasks"
                        ],
                        span(class_="font-medium")[
                            f"{project.progress}%"
                        ],
                    ],
                    ProgressBar(value=project.progress),
                ],
                
                # Task breakdown
                project.task_count > 0 and div(class_="flex gap-4 mt-3 text-xs text-muted-foreground")[
                    span()[f"✅ {project.completed_count} done"],
                    span()[f"📋 {project.task_count - project.completed_count} remaining"],
                ],
            ],
        ],
    ]


def ProgressBar(value: int, class_: str = ""):
    """
    A simple progress bar.
    
    Args:
        value: Percentage (0-100)
    """
    # Clamp value between 0 and 100
    value = max(0, min(100, value))
    
    return div(class_=cn("h-2 bg-muted rounded-full overflow-hidden", class_))[
        div(
            class_="h-full bg-primary transition-all duration-300",
            style=f"width: {value}%",
        ),
    ]


def ProjectGrid(projects: list, class_: str = ""):
    """
    Grid of project cards.
    
    Args:
        projects: List of Project objects
    """
    return div(class_=cn("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4", class_))[
        [ProjectCard(project) for project in projects]
    ] if projects else EmptyState()


def EmptyState():
    """Shown when there are no projects."""
    return div(class_="text-center py-12 text-muted-foreground")[
        div(class_="text-4xl mb-3")["📁"],
        div(class_="text-lg font-medium mb-1")["No projects yet"],
        div(class_="text-sm")["Create your first project to get started"],
    ]
```

---

## Step 2: Update the Dashboard Page

Now let's update `pages/index.py` to use real data:

```python
"""
Dashboard Page

The main page showing task statistics, recent activity,
and project overview.
"""

from pynext import page, div, h1, h2, p, a
from pynext.tw import tw, cn
from pynext.shadcn import Button

# Import database queries
from db.queries import get_dashboard_stats, get_recent_activity, get_projects

# Import our components
from components.stats_card import StatsCard
from components.activity_feed import ActivityFeed
from components.project_card import ProjectGrid


@page(title="Dashboard - PyTask")
def dashboard():
    """
    Main dashboard page.
    
    Displays:
    - Task statistics
    - Recent activity
    - Project overview
    """
    # Fetch data from database
    stats = get_dashboard_stats()
    activities = get_recent_activity(limit=5)
    projects = get_projects()
    
    return div(class_=tw.p_8.max_w_7xl.mx_auto)[
        # Page header
        DashboardHeader(),
        
        # Stats row
        div(class_=tw.grid.grid_cols_1.sm.grid_cols_2.lg.grid_cols_4.gap_4.mb_8)[
            StatsCard(
                title="Total Tasks",
                value=stats["total"],
                description="Across all projects",
                icon="📋",
            ),
            StatsCard(
                title="Todo",
                value=stats["todo"],
                description="Ready to start",
                icon="📝",
            ),
            StatsCard(
                title="In Progress",
                value=stats["in_progress"],
                description="Being worked on",
                icon="🔄",
            ),
            StatsCard(
                title="Completed",
                value=stats["done"],
                description="Done this week",
                icon="✅",
                trend="up",
                trend_value="+3",
            ),
        ],
        
        # Main content grid
        div(class_="grid grid-cols-1 lg:grid-cols-3 gap-6")[
            # Activity feed (takes 1 column on lg)
            div(class_="lg:col-span-1")[
                ActivityFeed(activities),
            ],
            
            # Projects overview (takes 2 columns on lg)
            div(class_="lg:col-span-2")[
                div(class_="flex items-center justify-between mb-4")[
                    h2(class_="text-lg font-semibold")["Projects"],
                    a(href="/projects", class_="text-sm text-primary hover:underline")[
                        "View all →"
                    ],
                ],
                ProjectGrid(projects),
            ],
        ],
    ]


def DashboardHeader():
    """Header with title and action buttons."""
    return div(class_=cn(
        "flex flex-col sm:flex-row sm:items-center sm:justify-between",
        "gap-4 mb-8",
    ))[
        div()[
            h1(class_=tw.text_3xl.font_bold.mb_1)["Dashboard"],
            p(class_=tw.text_muted_foreground)[
                "Welcome back! Here's what's happening."
            ],
        ],
        div(class_="flex gap-2")[
            Button(variant="outline")[
                a(href="/board")["View Board"]
            ],
            Button()[
                "+ New Task"
            ],
        ],
    ]
```

---

## Step 3: Create a Quick Task Component

Let's add a "New Task" dialog. Create `components/quick_task.py`:

```python
"""
Quick Task Dialog

A dialog for quickly creating a new task.
"""

from pynext import div, form
from pynext.tw import tw, cn
from pynext.shadcn import (
    Button, Input, Label, Textarea,
    Dialog, DialogTrigger, DialogContent,
    DialogHeader, DialogTitle, DialogDescription,
    DialogFooter,
)


def QuickTaskButton():
    """
    Button that opens a dialog to create a new task.
    """
    return Dialog()[
        DialogTrigger()[
            Button()["+ New Task"]
        ],
        DialogContent(class_="sm:max-w-md")[
            form(action="/api/tasks", method="POST")[
                DialogHeader()[
                    DialogTitle()["Create Task"],
                    DialogDescription()[
                        "Add a new task to your project."
                    ],
                ],
                
                div(class_="space-y-4 py-4")[
                    # Title
                    div(class_="space-y-2")[
                        Label(html_for="title")["Title"],
                        Input(
                            id="title",
                            name="title",
                            placeholder="What needs to be done?",
                            required=True,
                        ),
                    ],
                    
                    # Description
                    div(class_="space-y-2")[
                        Label(html_for="description")["Description"],
                        Textarea(
                            id="description",
                            name="description",
                            placeholder="Add more details...",
                            rows=3,
                        ),
                    ],
                    
                    # Project selection (simplified)
                    div(class_="space-y-2")[
                        Label(html_for="project")["Project"],
                        select(
                            id="project",
                            name="project_id",
                            class_=cn(
                                "w-full rounded-md border border-input bg-background",
                                "px-3 py-2 text-sm ring-offset-background",
                                "focus:outline-none focus:ring-2 focus:ring-ring",
                            ),
                        )[
                            option(value="1")["🚀 PyNext"],
                            option(value="2")["📚 Documentation"],
                            option(value="3")["🔌 API"],
                        ],
                    ],
                ],
                
                DialogFooter()[
                    Button(type="submit")["Create Task"],
                ],
            ],
        ],
    ]
```

---

## Step 4: Add Empty States

Good dashboards handle empty states gracefully. Update the components to show helpful messages when there's no data.

We've already added `EmptyState` functions in our components. Here's how they look:

```
┌─────────────────────────────────┐
│                                 │
│           📭                    │
│                                 │
│    No recent activity           │
│                                 │
└─────────────────────────────────┘
```

---

## Step 5: Add Loading States (Preview)

In a real app, you'd want loading states. Here's a preview of what we'll add in Part 8:

```python
def StatsCardSkeleton():
    """Loading skeleton for stats card."""
    return Card()[
        CardHeader(class_="pb-2")[
            div(class_="h-4 w-20 bg-muted rounded animate-pulse"),
        ],
        CardContent()[
            div(class_="h-8 w-16 bg-muted rounded animate-pulse mb-2"),
            div(class_="h-3 w-24 bg-muted rounded animate-pulse"),
        ],
    ]
```

---

## Step 6: Test the Dashboard

Make sure your database is seeded:

```bash
python -m db.seed
```

Start the dev server:

```bash
pynext dev
```

Visit `http://localhost:3000` and you should see:

1. **Stats Cards** showing real task counts
2. **Activity Feed** with recent team actions
3. **Project Grid** with progress bars

---

## What We Built

In this part, we:

- Created reusable dashboard components
- Connected the UI to real database data
- Built stats cards with trend indicators
- Made an activity feed with relative timestamps
- Added project cards with progress bars
- Implemented empty states

### Component Summary

| Component | Purpose |
|-----------|---------|
| `StatsCard` | Display a metric with optional trend |
| `ActivityFeed` | Show recent team actions |
| `ActivityItem` | Single activity entry |
| `ProjectCard` | Project with progress bar |
| `ProjectGrid` | Grid layout for projects |
| `ProgressBar` | Simple progress indicator |

### Key Patterns Learned

| Pattern | Example |
|---------|---------|
| **Data Fetching** | Call `get_*()` functions in page |
| **Component Composition** | `StatsCard` used inside grid |
| **Conditional Rendering** | `activities if activities else EmptyState()` |
| **Props Passing** | `StatsCard(title="...", value=...)` |

---

## Next Up

In **Part 4**, we'll build the Kanban task board with columns for each status.

[**Continue to Part 4: Task Board →**](./04-task-board.md)

---

## Troubleshooting

### "No module named 'components'" error?

Make sure you have `components/__init__.py`:
```bash
touch components/__init__.py
```

### Stats showing zeros?

Make sure you've seeded the database:
```bash
python -m db.seed
```

### Activity timestamps wrong?

The `format_time_ago` function is simplified. In production, use a library like `humanize` or `python-dateutil`.

