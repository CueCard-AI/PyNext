# PyNext Tutorials

> **Learn by building real applications**

These tutorials take you from zero to a complete, production-ready application. Each one teaches PyNext concepts through hands-on coding.

---

## Main Tutorial: Build a Task Manager

A comprehensive 8-part tutorial building a **Linear-style project management app** with:

- Dashboard with analytics
- Kanban task board
- Real-time updates
- Team collaboration
- Keyboard shortcuts
- Dark mode

**Time:** ~4-6 hours total | **Difficulty:** Intermediate

```
┌─────────────────────────────────────────────────────────────────────┐
│  PyTask - Your Projects                                    [+ New] │
├──────────┬──────────────────────────────────────────────────────────┤
│          │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│ Projects │  │ BACKLOG │ │  TODO   │ │ IN PROG │ │  DONE   │        │
│          │  ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤        │
│ • PyNext │  │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │        │
│ • Docs   │  │ │Task1│ │ │ │Task3│ │ │ │Task5│ │ │ │Task7│ │        │
│ • API    │  │ └─────┘ │ │ └─────┘ │ │ └─────┘ │ │ └─────┘ │        │
│          │  │ ┌─────┐ │ │ ┌─────┐ │ │         │ │ ┌─────┐ │        │
│ ──────── │  │ │Task2│ │ │ │Task4│ │ │         │ │ │Task8│ │        │
│ Settings │  │ └─────┘ │ │ └─────┘ │ │         │ │ └─────┘ │        │
│          │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
└──────────┴──────────────────────────────────────────────────────────┘
```

### Tutorial Parts

| Part | Title | What You'll Build |
|------|-------|-------------------|
| 1 | [Project Setup](./task-manager/01-setup.md) | Tailwind, layout, routing |
| 2 | [Database & Models](./task-manager/02-database.md) | SQLite, models, seed data |
| 3 | [Dashboard](./task-manager/03-dashboard.md) | Stats cards, activity feed |
| 4 | [Task Board](./task-manager/04-task-board.md) | Kanban columns, drag & drop |
| 5 | [Task Detail](./task-manager/05-task-detail.md) | Forms, validation, comments |
| 6 | [Settings & Team](./task-manager/06-settings.md) | Tabs, team management |
| 7 | [Search & Shortcuts](./task-manager/07-search-shortcuts.md) | Command palette, keyboard nav |
| 8 | [Polish & Deploy](./task-manager/08-polish-deploy.md) | Loading states, deployment |

[**Start the Tutorial →**](./task-manager/README.md)

---

## Concept Tutorials

Focused tutorials on specific PyNext features. Each takes 15-30 minutes.

### Forms & Data

| Tutorial | Description |
|----------|-------------|
| [Forms & Validation](./concepts/forms-and-validation.md) | Server actions, validation, error handling |
| [Data Tables](./concepts/data-tables.md) | Sorting, filtering, pagination |
| [State Management](./concepts/state-management.md) | Signals, stores, reactive patterns |

### Features

| Tutorial | Description |
|----------|-------------|
| [Authentication](./concepts/authentication.md) | Login, sessions, protected routes |
| [Real-time Updates](./concepts/real-time-updates.md) | Polling, SSE, optimistic updates |
| [Keyboard Shortcuts](./concepts/keyboard-shortcuts.md) | Global shortcuts, focus management |

### UI & Styling

| Tutorial | Description |
|----------|-------------|
| [Theming](./concepts/theming.md) | Custom themes, dark mode, CSS variables |
| [Component Patterns](./concepts/component-patterns.md) | Composition, variants, extending ShadCN |

---

## Prerequisites

Before starting tutorials, you should:

1. **Have Python 3.9+** installed
2. **Understand Python basics** (functions, classes, decorators)
3. **Have PyNext installed**: `pip install git+https://github.com/CueCard-AI/PyNext.git`
4. **Basic HTML/CSS knowledge** (helpful but not required)

No prior React, Next.js, or frontend framework experience needed!

---

## How to Use These Tutorials

### For the Main Tutorial

Work through parts 1-8 in order. Each part builds on the previous one.

```bash
# Create a fresh project for the tutorial
mkdir pytask && cd pytask
pynext init .
```

### For Concept Tutorials

Pick any topic you want to learn. They're self-contained.

```bash
# Each concept tutorial has its own starter
pynext init concept-demo
```

---

## Getting Help

- **Stuck?** Check the "Troubleshooting" section at the end of each part
- **Found an issue?** Open a GitHub issue
- **Want to contribute?** PRs welcome for typos, improvements, and translations

---

## What's Next?

Ready to build something real? 

[**Start Building: Task Manager Tutorial →**](./task-manager/README.md)

