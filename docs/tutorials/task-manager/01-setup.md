# Part 1: Project Setup & First Pages

> **Set up the foundation for our task manager**

In this part, you'll initialize a new PyNext project, configure Tailwind CSS with a custom theme, and build the main layout with sidebar navigation.

---

## What We're Building

By the end of this part, you'll have:

```
┌─────────────────────────────────────────────────────────────────┐
│  🚀 PyTask                                         [🌙] [JD]    │
├────────────┬────────────────────────────────────────────────────┤
│            │                                                    │
│  PROJECTS  │  Welcome to PyTask                                 │
│            │                                                    │
│  ◉ All     │  Your task management dashboard                    │
│            │                                                    │
│  ────────  │  [Go to Board]                                     │
│            │                                                    │
│  SETTINGS  │                                                    │
│            │                                                    │
│  ⚙ General │                                                    │
│  👥 Team   │                                                    │
│            │                                                    │
└────────────┴────────────────────────────────────────────────────┘
```

---

## Step 1: Initialize the Project

Create a new directory and initialize a PyNext project:

```bash
mkdir pytask
cd pytask
pynext init .
```

This creates the basic structure:

```
pytask/
├── pages/
│   ├── index.py
│   └── about.py
├── public/
│   └── styles.css
├── components/
├── pynext.config.py
├── pynext.requirements.txt
└── pynext.npm.txt
```

Test that it works:

```bash
pynext dev
```

Visit `http://localhost:3000` — you should see the default welcome page.

---

## Step 2: Set Up Tailwind CSS

### Install Tailwind

Add these to `pynext.npm.txt`:

```
tailwindcss
autoprefixer
postcss
@tailwindcss/forms
```

Install the dependencies:

```bash
pynext deps install
```

### Create Tailwind Config

Create `tailwind.config.js` in your project root:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.py",
    "./components/**/*.py",
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors
        brand: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
        },
        // Semantic colors using CSS variables
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
  ],
}
```

### Create Theme CSS

Replace `public/styles.css` with our theme:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 199 89% 48%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 199 89% 48%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --primary: 199 89% 48%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 199 89% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  @apply bg-muted;
}

::-webkit-scrollbar-thumb {
  @apply bg-muted-foreground/20 rounded-full;
}

::-webkit-scrollbar-thumb:hover {
  @apply bg-muted-foreground/40;
}
```

---

## Step 3: Add ShadCN Components

Copy the components we'll need:

```bash
pynext ui add button card badge avatar separator
```

This creates editable copies in `components/ui/`.

---

## Step 4: Create the Root Layout

The layout wraps every page with the sidebar navigation.

Create `pages/layout.py`:

```python
"""
Root Layout - Sidebar navigation wrapper for all pages.
"""

from pynext import layout, html, head, body, link, script, div
from pynext.tw import tw, cn

# Import our sidebar component (we'll create this next)
from components.sidebar import Sidebar


@layout
def root_layout(children):
    """
    Root layout with sidebar navigation.
    
    Every page in our app will be wrapped in this layout,
    giving us consistent navigation and styling.
    """
    from pynext.theme import ThemeScript, ThemeProvider
    
    return html(class_="h-full")[
        head()[
            # Page metadata
            link(rel="stylesheet", href="/styles.css"),
            link(rel="icon", href="/favicon.ico"),
            
            # Prevent flash of wrong theme (PyNext handles this!)
            ThemeScript(),
        ],
        body(class_="h-full")[
            # ThemeProvider enables theme management
            ThemeProvider()[
                div(class_=tw.flex.h_full)[
                    # Sidebar navigation (fixed width)
                    Sidebar(),
                    
                    # Main content area (fills remaining space)
                    main(class_=tw.flex_1.overflow_auto.bg_background)[
                        children
                    ],
                ],
            ],
        ],
    ]
```

**What's happening here:**

1. `@layout` decorator marks this as a layout component
2. The layout receives `children` — the page content to wrap
3. We use `tw` for Tailwind classes (type-safe!)
4. The sidebar is fixed, content scrolls independently
5. `ThemeScript()` prevents dark mode flash without writing JavaScript
6. `ThemeProvider` enables theme toggling throughout the app

---

## Step 5: Build the Sidebar Component

Create `components/sidebar.py`:

```python
"""
Sidebar Navigation Component

The main navigation for our task manager.
Shows projects, labels, and settings links.
"""

from pynext import div, nav, a, span, button, Signal
from pynext.tw import tw, cn
from pynext.shadcn import Button, Avatar, AvatarFallback, Separator


def Sidebar():
    """
    Left sidebar with navigation links.
    
    Structure:
    - Logo/brand
    - Projects list
    - Labels
    - Settings
    - User menu
    """
    return div(class_=cn(
        "w-64 h-full flex flex-col",
        "bg-card border-r border-border",
    ))[
        # Header with logo
        SidebarHeader(),
        
        # Navigation sections
        div(class_="flex-1 overflow-y-auto py-4")[
            # Projects section
            NavSection(title="Projects")[
                NavItem(href="/", icon="📋", label="All Tasks", active=True),
                NavItem(href="/projects/pynext", icon="🚀", label="PyNext"),
                NavItem(href="/projects/docs", icon="📚", label="Documentation"),
                NavItem(href="/projects/api", icon="🔌", label="API"),
            ],
            
            Separator(class_="my-4"),
            
            # Quick filters
            NavSection(title="Labels")[
                NavItem(href="/labels/bug", icon="🔴", label="Bug"),
                NavItem(href="/labels/feature", icon="🟢", label="Feature"),
                NavItem(href="/labels/docs", icon="🟡", label="Docs"),
            ],
            
            Separator(class_="my-4"),
            
            # Settings section
            NavSection(title="Settings")[
                NavItem(href="/settings", icon="⚙️", label="General"),
                NavItem(href="/settings/team", icon="👥", label="Team"),
            ],
        ],
        
        # User section at bottom
        SidebarFooter(),
    ]


def SidebarHeader():
    """Logo and brand header."""
    return div(class_="h-16 flex items-center px-4 border-b border-border")[
        a(href="/", class_="flex items-center gap-2")[
            span(class_="text-2xl")["🚀"],
            span(class_="font-bold text-lg")["PyTask"],
        ],
    ]


def NavSection(title: str, children=None):
    """A section of navigation items with a title."""
    return div(class_="px-3")[
        span(class_=cn(
            "text-xs font-semibold uppercase tracking-wider",
            "text-muted-foreground px-3 mb-2 block",
        ))[title],
        nav(class_="space-y-1")[
            children
        ],
    ]


def NavItem(
    href: str,
    icon: str,
    label: str,
    active: bool = False,
    count: int = None,
):
    """A single navigation item."""
    return a(
        href=href,
        class_=cn(
            "flex items-center gap-3 px-3 py-2 rounded-md text-sm",
            "transition-colors",
            # Active state
            "bg-accent text-accent-foreground" if active else "",
            # Hover state (when not active)
            "" if active else "hover:bg-accent/50 text-muted-foreground hover:text-foreground",
        ),
    )[
        span(class_="text-base")[icon],
        span(class_="flex-1")[label],
        count is not None and span(class_=cn(
            "text-xs bg-muted px-2 py-0.5 rounded-full",
        ))[str(count)],
    ]


def SidebarFooter():
    """User section at the bottom of sidebar."""
    return div(class_="p-4 border-t border-border")[
        div(class_="flex items-center gap-3")[
            Avatar(class_="h-8 w-8")[
                AvatarFallback()["JD"]
            ],
            div(class_="flex-1 min-w-0")[
                div(class_="text-sm font-medium truncate")["John Doe"],
                div(class_="text-xs text-muted-foreground truncate")[
                    "john@example.com"
                ],
            ],
            Button(variant="ghost", size="icon", class_="h-8 w-8")[
                "⚙️"
            ],
        ],
    ]
```

**What's happening here:**

1. **Sidebar()** - Main component that composes all sections
2. **SidebarHeader()** - Logo at the top
3. **NavSection()** - Groups nav items with a title
4. **NavItem()** - Individual links with icon, label, and optional count
5. **SidebarFooter()** - User avatar and settings at bottom

Notice how we:
- Use `cn()` for conditional classes
- Keep components small and focused
- Pass data as props (`href`, `icon`, `label`, etc.)

---

## Step 6: Create the Home Page

Replace `pages/index.py`:

```python
"""
Dashboard - The main page of our task manager.

For now, we'll show a simple welcome message.
We'll build the full dashboard in Part 3.
"""

from pynext import page, div, h1, p, a
from pynext.tw import tw
from pynext.shadcn import Button, Card, CardHeader, CardTitle, CardContent


@page(title="Dashboard - PyTask")
def dashboard():
    """
    Main dashboard page.
    
    This will eventually show:
    - Task statistics
    - Recent activity
    - Project overview
    """
    return div(class_=tw.p_8.max_w_6xl.mx_auto)[
        # Page header
        div(class_=tw.mb_8)[
            h1(class_=tw.text_3xl.font_bold.mb_2)[
                "Welcome to PyTask"
            ],
            p(class_=tw.text_muted_foreground)[
                "Your task management dashboard"
            ],
        ],
        
        # Quick actions
        div(class_=tw.flex.gap_4)[
            Button(variant="default")[
                a(href="/board")["Go to Board"]
            ],
            Button(variant="outline")[
                a(href="/settings")["Settings"]
            ],
        ],
        
        # Placeholder cards (we'll replace these in Part 3)
        div(class_=tw.grid.grid_cols_1.md.grid_cols_3.gap_4.mt_8)[
            StatsCard(
                title="Total Tasks",
                value="24",
                description="Across all projects",
            ),
            StatsCard(
                title="In Progress",
                value="5",
                description="Currently being worked on",
            ),
            StatsCard(
                title="Completed",
                value="12",
                description="This week",
            ),
        ],
    ]


def StatsCard(title: str, value: str, description: str):
    """A simple stats card component."""
    return Card()[
        CardHeader(class_="pb-2")[
            CardTitle(class_="text-sm font-medium text-muted-foreground")[
                title
            ],
        ],
        CardContent()[
            div(class_="text-3xl font-bold")[value],
            p(class_="text-xs text-muted-foreground mt-1")[description],
        ],
    ]
```

---

## Step 7: Create the Board Page

Create `pages/board.py`:

```python
"""
Task Board - Kanban-style task management.

We'll build the full board in Part 4.
For now, just a placeholder.
"""

from pynext import page, div, h1, p
from pynext.tw import tw
from pynext.shadcn import Button


@page(title="Board - PyTask")
def board():
    """Kanban task board page."""
    return div(class_=tw.p_8)[
        # Header
        div(class_=tw.flex.items_center.justify_between.mb_8)[
            div()[
                h1(class_=tw.text_2xl.font_bold)["Task Board"],
                p(class_=tw.text_muted_foreground)[
                    "Drag and drop to update task status"
                ],
            ],
            Button()["+ New Task"],
        ],
        
        # Board columns placeholder
        div(class_=tw.grid.grid_cols_4.gap_4)[
            BoardColumn(title="Backlog", count=3),
            BoardColumn(title="Todo", count=5),
            BoardColumn(title="In Progress", count=2),
            BoardColumn(title="Done", count=8),
        ],
    ]


def BoardColumn(title: str, count: int):
    """A single column in the kanban board."""
    return div(class_="bg-muted/50 rounded-lg p-4 min-h-[500px]")[
        div(class_="flex items-center justify-between mb-4")[
            div(class_="flex items-center gap-2")[
                span(class_="font-medium")[title],
                span(class_="text-xs bg-muted px-2 py-0.5 rounded-full")[
                    str(count)
                ],
            ],
        ],
        # Task cards will go here
        div(class_="space-y-2")[
            p(class_="text-sm text-muted-foreground text-center py-8")[
                "Tasks coming in Part 4..."
            ],
        ],
    ]
```

---

## Step 8: Test Everything

Start the dev server:

```bash
pynext dev
```

You should now see:

1. **Sidebar** on the left with navigation
2. **Dashboard** as the home page with stats cards
3. **Board** page at `/board` with column layout

Try clicking around — the navigation should work!

---

## What We Built

In this part, we:

- Initialized a PyNext project
- Configured Tailwind CSS with a custom theme
- Added ShadCN components
- Created a root layout with sidebar
- Built reusable navigation components
- Made placeholder pages for dashboard and board

### Key Concepts Learned

| Concept | What We Learned |
|---------|-----------------|
| **Layouts** | Wrap pages with shared UI (sidebar) |
| **Components** | Break UI into reusable pieces |
| **`tw` builder** | Type-safe Tailwind classes |
| **`cn()` utility** | Conditional class merging |
| **ShadCN** | Pre-built, customizable components |

---

## Next Up

In **Part 2**, we'll set up the database and create models for our tasks, projects, and users.

[**Continue to Part 2: Database & Models →**](./02-database.md)

---

## Troubleshooting

### Tailwind styles not working?

1. Make sure `pynext.npm.txt` includes `tailwindcss`
2. Run `pynext deps install`
3. Check that `tailwind.config.js` exists
4. Verify `public/styles.css` has the `@tailwind` directives

### Import errors?

Make sure you've copied the ShadCN components:
```bash
pynext ui add button card badge avatar separator
```

### Sidebar not showing?

Check that `pages/layout.py` exists and has the `@layout` decorator.

