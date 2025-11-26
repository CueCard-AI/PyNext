# Part 8: Polish & Deployment

> **Add loading states, error handling, and deploy your app**

In this final part, we'll polish the user experience with loading states and error handling, then prepare the app for production deployment.

---

## What We're Building

- Loading skeletons for smooth perceived performance
- Error boundaries for graceful failure handling
- Dark mode persistence
- Production build optimization
- Deployment to various platforms

---

## Step 1: Create Loading Skeletons

Create `components/skeletons.py`:

```python
"""
Loading Skeletons

Placeholder UI shown while content is loading.
Creates a smoother perceived loading experience.
"""

from pynext import div, span
from pynext.tw import tw, cn
from pynext.shadcn import Card, CardHeader, CardContent


def Skeleton(class_: str = ""):
    """Base skeleton element with pulse animation."""
    return div(class_=cn(
        "bg-muted rounded animate-pulse",
        class_,
    ))


def TextSkeleton(width: str = "w-full", class_: str = ""):
    """Skeleton for text lines."""
    return Skeleton(class_=cn("h-4", width, class_))


def CircleSkeleton(size: str = "h-10 w-10", class_: str = ""):
    """Skeleton for avatars/icons."""
    return Skeleton(class_=cn("rounded-full", size, class_))


# ============================================================================
# Component-specific skeletons
# ============================================================================

def StatsCardSkeleton():
    """Loading skeleton for stats card."""
    return Card()[
        CardHeader(class_="pb-2")[
            TextSkeleton(width="w-24"),
        ],
        CardContent()[
            Skeleton(class_="h-8 w-16 mb-2"),
            TextSkeleton(width="w-32"),
        ],
    ]


def TaskCardSkeleton():
    """Loading skeleton for task card."""
    return Card(class_="p-3")[
        TextSkeleton(width="w-3/4", class_="mb-3"),
        div(class_="flex items-center justify-between")[
            div(class_="flex items-center gap-2")[
                Skeleton(class_="h-5 w-16 rounded-full"),
                Skeleton(class_="h-5 w-12 rounded-full"),
            ],
            CircleSkeleton(size="h-6 w-6"),
        ],
    ]


def BoardColumnSkeleton():
    """Loading skeleton for a board column."""
    return div(class_="min-w-[280px] bg-muted/30 rounded-lg")[
        div(class_="p-3 border-b border-border")[
            div(class_="flex items-center gap-2")[
                Skeleton(class_="h-5 w-20"),
                Skeleton(class_="h-5 w-6 rounded-full"),
            ],
        ],
        div(class_="p-2 space-y-2")[
            TaskCardSkeleton(),
            TaskCardSkeleton(),
            TaskCardSkeleton(),
        ],
    ]


def BoardSkeleton():
    """Loading skeleton for the full board."""
    return div(class_="flex gap-4")[
        BoardColumnSkeleton(),
        BoardColumnSkeleton(),
        BoardColumnSkeleton(),
        BoardColumnSkeleton(),
    ]


def ActivityItemSkeleton():
    """Loading skeleton for activity item."""
    return div(class_="flex gap-3")[
        CircleSkeleton(size="h-8 w-8"),
        div(class_="flex-1 space-y-2")[
            TextSkeleton(width="w-48"),
            TextSkeleton(width="w-24"),
        ],
    ]


def ProjectCardSkeleton():
    """Loading skeleton for project card."""
    return Card()[
        CardHeader(class_="pb-2")[
            div(class_="flex items-center gap-2")[
                Skeleton(class_="h-6 w-6"),
                TextSkeleton(width="w-24"),
            ],
        ],
        CardContent()[
            div(class_="space-y-2")[
                div(class_="flex justify-between")[
                    TextSkeleton(width="w-16"),
                    TextSkeleton(width="w-8"),
                ],
                Skeleton(class_="h-2 w-full rounded-full"),
            ],
        ],
    ]


def DashboardSkeleton():
    """Loading skeleton for the entire dashboard."""
    return div(class_="p-8 max-w-7xl mx-auto")[
        # Header skeleton
        div(class_="flex justify-between items-center mb-8")[
            div(class_="space-y-2")[
                TextSkeleton(width="w-32", class_="h-8"),
                TextSkeleton(width="w-48"),
            ],
            div(class_="flex gap-2")[
                Skeleton(class_="h-10 w-24 rounded-md"),
                Skeleton(class_="h-10 w-28 rounded-md"),
            ],
        ],
        
        # Stats grid skeleton
        div(class_="grid grid-cols-4 gap-4 mb-8")[
            StatsCardSkeleton(),
            StatsCardSkeleton(),
            StatsCardSkeleton(),
            StatsCardSkeleton(),
        ],
        
        # Content grid skeleton
        div(class_="grid grid-cols-3 gap-6")[
            Card(class_="col-span-1")[
                CardHeader()[TextSkeleton(width="w-32")],
                CardContent(class_="space-y-4")[
                    ActivityItemSkeleton(),
                    ActivityItemSkeleton(),
                    ActivityItemSkeleton(),
                ],
            ],
            div(class_="col-span-2 space-y-4")[
                div(class_="flex justify-between")[
                    TextSkeleton(width="w-24", class_="h-6"),
                    TextSkeleton(width="w-16"),
                ],
                div(class_="grid grid-cols-3 gap-4")[
                    ProjectCardSkeleton(),
                    ProjectCardSkeleton(),
                    ProjectCardSkeleton(),
                ],
            ],
        ],
    ]
```

---

## Step 2: Create Error Boundaries

Create `components/error_boundary.py`:

```python
"""
Error Boundary Components

Handle errors gracefully in the UI.
"""

from pynext import div, h1, h2, p, pre, code, a
from pynext.tw import tw, cn
from pynext.shadcn import Button, Card, CardHeader, CardTitle, CardContent


def ErrorPage(
    status: int = 500,
    title: str = "Something went wrong",
    message: str = None,
    details: str = None,
    show_retry: bool = True,
):
    """
    Full-page error display.
    
    Args:
        status: HTTP status code
        title: Error title
        message: User-friendly message
        details: Technical details (dev only)
        show_retry: Show retry button
    """
    return div(class_="min-h-screen flex items-center justify-center p-4")[
        div(class_="text-center max-w-md")[
            # Status code
            div(class_="text-6xl font-bold text-muted-foreground mb-4")[
                str(status)
            ],
            
            # Title
            h1(class_="text-2xl font-bold mb-2")[title],
            
            # Message
            message and p(class_="text-muted-foreground mb-6")[message],
            
            # Actions
            div(class_="flex gap-3 justify-center")[
                show_retry and Button(onclick=lambda: navigate(current_path(), refresh=True))[
                    "Try Again"
                ],
                Button(variant="outline")[
                    a(href="/")["Go Home"]
                ],
            ],
            
            # Technical details (collapsible)
            details and div(class_="mt-8 text-left")[
                details_tag(class_="text-sm")[
                    summary(class_="cursor-pointer text-muted-foreground hover:text-foreground")[
                        "Technical Details"
                    ],
                    pre(class_="mt-2 p-4 bg-muted rounded-lg overflow-x-auto text-xs")[
                        code()[details]
                    ],
                ],
            ],
        ],
    ]


def NotFoundPage():
    """404 Not Found page."""
    return ErrorPage(
        status=404,
        title="Page not found",
        message="The page you're looking for doesn't exist or has been moved.",
        show_retry=False,
    )


def ServerErrorPage(error: str = None):
    """500 Server Error page."""
    return ErrorPage(
        status=500,
        title="Server error",
        message="We're having trouble processing your request. Please try again.",
        details=error,
    )


def ErrorCard(title: str, message: str, on_retry=None):
    """
    Inline error card for component-level errors.
    """
    return Card(class_="border-destructive/50")[
        CardHeader()[
            CardTitle(class_="text-destructive flex items-center gap-2")[
                "⚠️",
                title,
            ],
        ],
        CardContent()[
            p(class_="text-sm text-muted-foreground mb-4")[message],
            on_retry and Button(variant="outline", size="sm", onclick=on_retry)[
                "Retry"
            ],
        ],
    ]


def EmptyState(
    icon: str = "📭",
    title: str = "Nothing here",
    message: str = None,
    action_label: str = None,
    action_href: str = None,
):
    """
    Empty state placeholder.
    """
    return div(class_="text-center py-12")[
        div(class_="text-4xl mb-3")[icon],
        h2(class_="text-lg font-medium mb-1")[title],
        message and p(class_="text-sm text-muted-foreground mb-4")[message],
        action_label and action_href and Button(variant="outline")[
            a(href=action_href)[action_label]
        ],
    ]
```

---

## Step 3: Add Dark Mode Persistence

PyNext provides a built-in theme module that handles dark mode with zero JavaScript. Use the components from `pynext.theme`:

```python
"""
Theme Setup

Using PyNext's built-in theme module for dark mode.
No custom JavaScript required!
"""

from pynext.theme import (
    ThemeProvider,     # Wraps app with theme context
    ThemeScript,       # Prevents flash on page load
    ThemeToggle,       # Ready-to-use toggle button
    ThemeSwitcher,     # Dropdown with light/dark/system options
    use_theme,         # Hook to access theme state
)

# In your layout's head, add the flash prevention script
head()[
    ThemeScript(),  # Prevents theme flash before hydration
    # ... other head elements
]

# Wrap your app with ThemeProvider
body()[
    ThemeProvider()[  # Handles theme state and persistence
        # Your app content
        children
    ],
]
```

### Using the Theme Toggle

Add the toggle button to your sidebar or header:

```python
from pynext.theme import ThemeToggle, ThemeSwitcher

def Sidebar():
    return nav(class_="...")[
        # ... sidebar content
        
        # Simple toggle (light ↔ dark)
        div(class_="mt-auto p-4 border-t")[
            ThemeToggle()
        ],
    ]

# Or use the full dropdown with system option
def Header():
    return header(class_="...")[
        # ... header content
        ThemeSwitcher()  # Shows light/dark/system options
    ]
```

### Accessing Theme State

You can also access the theme state programmatically:

```python
from pynext.theme import use_theme

# Get the theme signal
theme = use_theme()

# Read current mode
current_mode = theme()  # "light", "dark", or "system"

# Set mode
theme.set("dark")

# Toggle
def toggle_theme():
    theme.set("dark" if theme() == "light" else "light")
```

### How It Works

PyNext's theme module automatically handles:

1. **Flash Prevention**: The `ThemeScript` component adds inline JS to `<head>` that runs before any content renders, preventing the white flash.

2. **System Preference**: Respects `prefers-color-scheme` media query when set to "system".

3. **Persistence**: Stores preference in localStorage automatically.

4. **Cross-Tab Sync**: Changes in one tab are reflected in other tabs.

5. **No JavaScript Required**: You write Python, PyNext generates the minimal JS needed.

---

## Step 4: Optimize for Production

Create `pynext.config.py` with production settings:

```python
"""
PyNext Configuration

Production-ready settings for PyTask.
"""

# Build options
build = {
    "output": ".pynext/build",
    "minify": True,
    "sourcemaps": False,  # Disable in production
}

# Development options
dev = {
    "port": 3000,
    "host": "127.0.0.1",
    "hot_reload": True,
}

# Production options
production = {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4,  # Adjust based on CPU cores
}

# Static file caching
static = {
    "max_age": 31536000,  # 1 year for hashed assets
    "immutable": True,
}

# Security headers
security = {
    "csp": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
    },
    "hsts": True,
    "x_frame_options": "DENY",
}
```

---

## Step 5: Build for Production

Run the production build:

```bash
pynext build
```

This will:
1. Bundle all JavaScript
2. Process and optimize images
3. Generate static pages where possible
4. Create a production-ready output in `.pynext/build/`

---

## Step 6: Deployment Options

### Option A: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyNext
RUN pip install pynext

# Copy application
COPY . .

# Install npm dependencies and build
RUN pynext deps install
RUN pynext build

# Expose port
EXPOSE 8000

# Run production server
CMD ["pynext", "start", "--production"]
```

Build and run:

```bash
docker build -t pytask .
docker run -p 8000:8000 pytask
```

### Option B: Railway/Render

Create `railway.json` or use the dashboard:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "pynext start --production",
    "healthcheckPath": "/",
    "healthcheckTimeout": 300
  }
}
```

### Option C: VPS with systemd

Create `/etc/systemd/system/pytask.service`:

```ini
[Unit]
Description=PyTask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/pytask
ExecStart=/usr/local/bin/pynext start --production
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl enable pytask
sudo systemctl start pytask
```

---

## Step 7: Final Checklist

### Pre-deployment Checklist

- [ ] All tests passing
- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] Error tracking set up (e.g., Sentry)
- [ ] Logging configured
- [ ] Security headers enabled
- [ ] HTTPS configured
- [ ] Backups scheduled

### Performance Checklist

- [ ] Static assets cached
- [ ] Images optimized
- [ ] JavaScript minified
- [ ] Database indexes added
- [ ] Query performance checked

### Security Checklist

- [ ] No hardcoded secrets
- [ ] CSRF protection enabled
- [ ] Input validation on all forms
- [ ] SQL injection prevention
- [ ] XSS prevention

---

## What We Built

Congratulations! You've built a complete task management application with:

- **Dashboard** with real-time stats
- **Kanban Board** for task management
- **Task Detail** with editing and comments
- **Settings** for team and labels
- **Command Palette** for power users
- **Dark Mode** with persistence
- **Loading States** for smooth UX
- **Error Handling** for reliability
- **Production Deployment** ready

### Final Project Structure

```
pytask/
├── pages/
│   ├── layout.py
│   ├── index.py          # Dashboard
│   ├── board.py          # Kanban board
│   ├── tasks/
│   │   └── [id].py       # Task detail
│   ├── projects/
│   │   └── [id]/
│   │       ├── index.py
│   │       └── settings.py
│   └── settings/
│       ├── layout.py
│       ├── index.py
│       ├── team.py
│       └── labels.py
├── components/
│   ├── ui/               # ShadCN components
│   ├── sidebar.py
│   ├── task_card.py
│   ├── board_column.py
│   ├── stats_card.py
│   ├── activity_feed.py
│   ├── project_card.py
│   ├── task_form.py
│   ├── comments.py
│   ├── command_palette.py
│   ├── skeletons.py
│   ├── error_boundary.py
│   └── theme_toggle.py
├── db/
│   ├── __init__.py
│   ├── models.py
│   ├── queries.py
│   └── seed.py
├── public/
│   └── styles.css
├── pynext.config.py
├── tailwind.config.js
├── Dockerfile
└── README.md
```

---

## What's Next?

You now have a solid foundation. Here are ideas for extending PyTask:

1. **Authentication** - Add login/signup with sessions
2. **Real-time Updates** - Use WebSockets for live collaboration
3. **File Attachments** - Upload files to tasks
4. **Time Tracking** - Log time spent on tasks
5. **Notifications** - Email and push notifications
6. **Mobile App** - Build a mobile version
7. **API** - Create a REST/GraphQL API

---

## Resources

- [PyNext Documentation](/)
- [Concept Tutorials](../concepts/)
- [ShadCN Components](../../shadcn/)
- [Tailwind CSS](https://tailwindcss.com)

---

## Thank You!

You've completed the PyTask tutorial. You now have the skills to build production-ready web applications with PyNext.

If you found this helpful, consider:
- Starring the PyNext repo on GitHub
- Sharing your projects built with PyNext
- Contributing to the documentation

Happy coding! 🚀

