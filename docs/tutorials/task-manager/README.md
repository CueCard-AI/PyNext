# Build a Linear-Style Task Manager

> **A complete project management app in pure Python**

In this tutorial, you'll build **PyTask** — a full-featured task management application inspired by [Linear](https://linear.app). By the end, you'll have a production-ready app and deep understanding of PyNext.

---

## What We're Building

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🚀 PyTask                                              [⌘K] [🌙] [JD ▼]   │
├────────────┬────────────────────────────────────────────────────────────────┤
│            │                                                                │
│  PROJECTS  │  Dashboard                                    + New Task       │
│            │  ───────────────────────────────────────────────────────────   │
│  ◉ PyNext  │                                                                │
│  ○ Docs    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  ○ API     │  │    12    │ │    5     │ │    3     │ │    24    │          │
│            │  │  Active  │ │ In Prog  │ │ Blocked  │ │ Complete │          │
│  ────────  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│            │                                                                │
│  LABELS    │  Recent Activity                                               │
│            │  ───────────────────────────────────────────────────────────   │
│  🔴 Bug    │  • Jane completed "Fix auth bug"           2 min ago          │
│  🟢 Feat   │  • John moved "Add dashboard" to In Prog   15 min ago         │
│  🟡 Docs   │  • Jane created "Update API docs"          1 hour ago         │
│            │                                                                │
│  ────────  │  Projects Overview                                             │
│            │  ───────────────────────────────────────────────────────────   │
│  TEAM      │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│            │  │ PyNext          │ │ Documentation   │ │ API             │  │
│  👤 Jane   │  │ ████████░░ 80%  │ │ ██████░░░░ 60%  │ │ ████░░░░░░ 40%  │  │
│  👤 John   │  │ 8 tasks         │ │ 12 tasks        │ │ 6 tasks         │  │
│            │  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
│            │                                                                │
└────────────┴────────────────────────────────────────────────────────────────┘
```

### Features You'll Implement

- **Dashboard** with stats, charts, and activity feed
- **Kanban Board** with drag-and-drop task management
- **Task Detail** with comments and history
- **Project Management** with team collaboration
- **Global Search** with command palette (⌘K)
- **Keyboard Shortcuts** for power users
- **Dark Mode** with theme persistence
- **Real-time Updates** across tabs

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | PyNext |
| UI Components | pynext.shadcn |
| Styling | Tailwind CSS |
| Database | SQLite (via Python's sqlite3) |
| State | PyNext Signals |
| Server Logic | Server Actions |

**No JavaScript written** — everything is Python!

---

## Prerequisites

Before starting, make sure you have:

```bash
# Python 3.9 or higher
python --version  # Should be 3.9+

# PyNext installed
pip install pynext

# Node.js (for Tailwind CSS)
node --version  # Should be 18+
```

---

## Tutorial Parts

### Part 1: Project Setup & First Pages
*~45 minutes*

Set up the project structure, configure Tailwind CSS, and build the layout with sidebar navigation.

**You'll learn:**
- Project initialization
- Tailwind + ShadCN theming
- Layouts and routing
- Sidebar navigation component

[**Start Part 1 →**](./01-setup.md)

---

### Part 2: Database & Models
*~30 minutes*

Create the data layer with SQLite, define models, and seed initial data.

**You'll learn:**
- SQLite setup in Python
- Model definitions
- Database utilities
- Seeding data

[**Start Part 2 →**](./02-database.md)

---

### Part 3: Building the Dashboard
*~45 minutes*

Build the main dashboard with stats cards, activity feed, and project overview.

**You'll learn:**
- Data fetching patterns
- Card and Badge components
- Activity timeline
- Responsive grid layouts

[**Start Part 3 →**](./03-dashboard.md)

---

### Part 4: Task Board (Kanban View)
*~60 minutes*

Create the kanban board with columns, task cards, and status updates.

**You'll learn:**
- Column layouts
- Task cards
- Server actions for updates
- Filtering and sorting

[**Start Part 4 →**](./04-task-board.md)

---

### Part 5: Task Detail & Forms
*~45 minutes*

Build the task detail view with edit form, validation, and comments.

**You'll learn:**
- Dialog/Modal patterns
- Form handling
- Validation
- Comments system

[**Start Part 5 →**](./05-task-detail.md)

---

### Part 6: Project Settings & Team
*~30 minutes*

Create settings pages for projects, labels, and team management.

**You'll learn:**
- Tabbed interfaces
- CRUD operations
- Team member management
- Confirmation dialogs

[**Start Part 6 →**](./06-settings.md)

---

### Part 7: Search & Keyboard Shortcuts
*~45 minutes*

Add global search with command palette and keyboard navigation.

**You'll learn:**
- Command palette UI
- Keyboard event handling
- Quick actions
- Focus management

[**Start Part 7 →**](./07-search-shortcuts.md)

---

### Part 8: Polish & Deployment
*~30 minutes*

Add loading states, error handling, and prepare for deployment.

**You'll learn:**
- Loading skeletons
- Error boundaries
- Performance optimization
- Deployment options

[**Start Part 8 →**](./08-polish-deploy.md)

---

## Project Structure

By the end of this tutorial, your project will look like:

```
pytask/
├── pages/
│   ├── layout.py              # Root layout with sidebar
│   ├── index.py               # Dashboard
│   ├── board.py               # Kanban board
│   ├── tasks/
│   │   └── [id].py            # Task detail
│   ├── projects/
│   │   ├── index.py           # Projects list
│   │   └── [id]/
│   │       ├── index.py       # Project board
│   │       └── settings.py    # Project settings
│   └── settings/
│       ├── index.py           # General settings
│       └── team.py            # Team management
├── components/
│   ├── ui/                    # Copied ShadCN components
│   ├── sidebar.py             # Navigation sidebar
│   ├── task_card.py           # Task card component
│   ├── stats_card.py          # Dashboard stat card
│   ├── command_palette.py     # Search dialog
│   └── activity_feed.py       # Activity timeline
├── db/
│   ├── __init__.py            # Database connection
│   ├── models.py              # Data models
│   ├── queries.py             # Query functions
│   └── seed.py                # Seed data
├── public/
│   └── globals.css            # Tailwind + theme
├── pynext.config.py
├── pynext.requirements.txt
├── pynext.npm.txt
└── tailwind.config.js
```

---

## Let's Build!

Ready to start? 

[**Begin Part 1: Project Setup →**](./01-setup.md)

