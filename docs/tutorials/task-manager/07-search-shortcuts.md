# Part 7: Search & Keyboard Shortcuts

> **Add a command palette and power-user keyboard navigation**

In this part, we'll create a global search dialog (command palette) and add keyboard shortcuts for fast navigation using PyNext's built-in keyboard module.

---

## What We're Building

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🔍 Search tasks, projects, or type a command...          ⌘K       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  Recent                                                             │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  📋 Research streaming SSR patterns              → View Task       │   │
│  │  📋 Implement form validation                    → View Task       │   │
│  │  📋 Build component registry CLI                 → View Task       │   │
│  │                                                                     │   │
│  │  Quick Actions                                                      │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  ➕ Create new task                              N                  │   │
│  │  📋 Go to board                                  G then B           │   │
│  │  ⚙️ Open settings                                G then S           │   │
│  │  🌙 Toggle dark mode                             T then D           │   │
│  │                                                                     │   │
│  │  Projects                                                           │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  🚀 PyNext                                       → Open Project    │   │
│  │  📚 Documentation                                → Open Project    │   │
│  │  🔌 API                                          → Open Project    │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Set Up Keyboard Shortcuts

PyNext provides a `pynext.keyboard` module for registering keyboard shortcuts without writing JavaScript. Create `shortcuts.py`:

```python
"""
Global Keyboard Shortcuts

Define all keyboard shortcuts in one place using PyNext's keyboard module.
"""

from pynext.keyboard import on_keydown, on_key_sequence
from pynext.core.client import use_storage
from pynext import Signal

# =============================================================================
# State
# =============================================================================

# Command palette state (shared signal)
palette_open = Signal(False, name="palette_open")

# =============================================================================
# Global Shortcuts
# =============================================================================

@on_keydown("cmd+k")
def open_palette():
    """Open the command palette with Cmd/Ctrl+K."""
    palette_open.set(True)


@on_keydown("/", context="global")
def quick_search():
    """Open search with /."""
    palette_open.set(True)


@on_keydown("escape", context="dialog")
def close_palette():
    """Close palette with Escape."""
    palette_open.set(False)


@on_keydown("n", context="global")
def new_task():
    """Create new task with N key."""
    # Trigger new task dialog
    from pages.board import new_task_open
    new_task_open.set(True)


# =============================================================================
# Navigation Sequences
# =============================================================================

@on_key_sequence("g d")
def go_dashboard():
    """Navigate to dashboard with G then D."""
    from pynext import navigate
    navigate("/")


@on_key_sequence("g b")
def go_board():
    """Navigate to board with G then B."""
    from pynext import navigate
    navigate("/board")


@on_key_sequence("g s")
def go_settings():
    """Navigate to settings with G then S."""
    from pynext import navigate
    navigate("/settings")


@on_key_sequence("t d")
def toggle_dark_mode():
    """Toggle dark mode with T then D."""
    # Uses theme module
    from pynext.theme import use_theme
    theme = use_theme()
    current = theme()
    theme.set("dark" if current == "light" else "light")
```

**How this works:**

1. `@on_keydown("cmd+k")` registers a keyboard shortcut. PyNext automatically handles the difference between Mac (⌘) and Windows (Ctrl).

2. `@on_key_sequence("g d")` registers a multi-key sequence. Press G, then D within 1 second.

3. The `context` parameter controls when shortcuts fire:
   - `"global"`: Everywhere except input fields
   - `"dialog"`: Only when a dialog is open
   - `"always"`: Even in input fields

---

## Step 2: Create the Command Palette Component

Create `components/command_palette.py`:

```python
"""
Command Palette Component

A searchable command palette (like VS Code's Cmd+K or Linear's Cmd+K).
Uses PyNext's reactive system instead of raw JavaScript.
"""

from pynext import div, span, input_, a, Show, For
from pynext.tw import tw, cn
from pynext.shadcn import Dialog, DialogContent, Separator
from pynext.focus import FocusTrap, RovingFocus, RovingFocusItem
from pynext.keyboard import on_keydown, ShortcutHint

from shortcuts import palette_open
from db.queries import get_tasks, get_projects
from typing import List, Dict


def CommandPalette():
    """
    Global command palette triggered by Cmd/Ctrl+K.
    
    Features:
    - Search tasks, projects, and commands
    - Quick actions (new task, navigation)
    - Keyboard navigation with arrow keys
    
    No JavaScript required - uses PyNext's built-in focus management.
    """
    tasks = get_tasks()[:5]  # Recent tasks
    projects = get_projects()
    
    return Show(when=palette_open)[
        div(
            class_=cn(
                "fixed inset-0 z-50 flex items-start justify-center pt-20",
                "bg-background/80 backdrop-blur-sm",
            ),
            onclick=lambda: palette_open.set(False),  # Click outside to close
        )[
            # Stop propagation on the palette itself
            div(
                class_=cn(
                    "w-full max-w-2xl bg-card border border-border",
                    "rounded-lg shadow-lg overflow-hidden",
                ),
                onclick=lambda e: e.stopPropagation(),
            )[
                FocusTrap(auto_focus=True, restore_focus=True)[
                    # Search input
                    SearchInput(),
                    
                    Separator(),
                    
                    # Results with roving focus for keyboard navigation
                    RovingFocus(orientation="vertical", loop=True)[
                        div(class_="max-h-80 overflow-y-auto p-2")[
                            # Recent Tasks
                            CommandGroup(title="Recent")[
                                [
                                    CommandItem(
                                        icon="📋",
                                        label=task.title,
                                        href=f"/tasks/{task.id}",
                                        meta=task.project.name if task.project else None,
                                    )
                                    for task in tasks
                                ]
                            ],
                            
                            # Quick Actions
                            CommandGroup(title="Quick Actions")[
                                CommandItem(
                                    icon="➕",
                                    label="Create new task",
                                    action="new_task",
                                    shortcut="N",
                                ),
                                CommandItem(
                                    icon="📋",
                                    label="Go to board",
                                    href="/board",
                                    shortcut="G B",
                                ),
                                CommandItem(
                                    icon="⚙️",
                                    label="Open settings",
                                    href="/settings",
                                    shortcut="G S",
                                ),
                                CommandItem(
                                    icon="🌙",
                                    label="Toggle dark mode",
                                    action="toggle_theme",
                                    shortcut="T D",
                                ),
                            ],
                            
                            # Projects
                            CommandGroup(title="Projects")[
                                [
                                    CommandItem(
                                        icon=project.emoji or "📁",
                                        label=project.name,
                                        href=f"/projects/{project.id}",
                                    )
                                    for project in projects
                                ]
                            ],
                        ],
                    ],
                ],
            ],
        ],
    ]


def SearchInput():
    """The search input at the top of the palette."""
    from pynext.core.client import use_ref
    
    input_ref = use_ref("search")
    
    return div(class_="flex items-center gap-3 px-4 py-3")[
        span(class_="text-muted-foreground")["🔍"],
        input_(
            ref=input_ref,
            type="text",
            placeholder="Search tasks, projects, or type a command...",
            class_=cn(
                "flex-1 bg-transparent border-0 outline-none",
                "text-sm placeholder:text-muted-foreground",
            ),
            # Real-time filtering is handled by PyNext signals
            oninput=lambda e: filter_results(e.target.value),
        ),
        ShortcutHint("cmd+k"),
    ]


def CommandGroup(title: str, children=None):
    """A group of related commands."""
    return div(class_="mb-4")[
        span(class_="text-xs font-semibold text-muted-foreground px-2 mb-2 block")[
            title
        ],
        div(class_="space-y-1")[
            children
        ],
    ]


def CommandItem(
    icon: str,
    label: str,
    href: str = None,
    action: str = None,
    shortcut: str = None,
    meta: str = None,
):
    """A single command item with RovingFocusItem for keyboard nav."""
    
    # Handle action execution
    def handle_action():
        if action == "new_task":
            from pages.board import new_task_open
            new_task_open.set(True)
        elif action == "toggle_theme":
            from pynext.theme import use_theme
            theme = use_theme()
            theme.set("dark" if theme() == "light" else "light")
        palette_open.set(False)
    
    return RovingFocusItem()[
        a(
            href=href,
            onclick=handle_action if action else None,
            class_=cn(
                "flex items-center justify-between px-2 py-2 rounded-md",
                "cursor-pointer",
                "hover:bg-accent focus:bg-accent",
                "outline-none",
            ),
        )[
            div(class_="flex items-center gap-3")[
                span(class_="text-base")[icon],
                span(class_="text-sm")[label],
                meta and span(class_="text-xs text-muted-foreground")[f"• {meta}"],
            ],
            shortcut and ShortcutHint(shortcut),
        ],
    ]


# Filter function (uses PyNext signals)
filter_query = Signal("", name="filter_query")

def filter_results(query: str):
    """Update the filter query signal."""
    filter_query.set(query.lower())
```

**Key improvements:**

1. **No JavaScript**: Uses PyNext's `Show` component for conditional rendering
2. **FocusTrap**: Automatically traps focus inside the dialog
3. **RovingFocus**: Enables arrow key navigation between items
4. **ShortcutHint**: Built-in component to display shortcuts

---

## Step 3: Add Command Palette to Layout

Update `pages/layout.py`:

```python
from components.command_palette import CommandPalette
from pynext.keyboard import ShortcutProvider
from pynext.theme import ThemeProvider, ThemeScript

@layout
def root_layout(children):
    return html(class_="h-full")[
        head()[
            title()["TaskFlow"],
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            
            # Prevent theme flash (before any other scripts)
            ThemeScript(),
            
            link(rel="stylesheet", href="/styles/globals.css"),
        ],
        body(class_="h-full")[
            # Providers wrap the entire app
            ThemeProvider()[
                ShortcutProvider()[
                    div(class_=tw.flex.h_full)[
                        Sidebar(),
                        main(class_=tw.flex_1.overflow_auto.bg_background, id="main-content")[
                            children
                        ],
                    ],
                    
                    # Command palette (renders when open)
                    CommandPalette(),
                ],
            ],
        ],
    ]
```

---

## Step 4: Add Search Trigger to Header

Create a button that opens the command palette:

```python
from pynext.keyboard import ShortcutHint
from shortcuts import palette_open

def SearchTrigger():
    """Button that opens the command palette."""
    return button(
        class_=cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-md",
            "border border-input bg-background",
            "text-sm text-muted-foreground",
            "hover:bg-accent hover:text-foreground",
            "transition-colors",
        ),
        onclick=lambda: palette_open.set(True),
    )[
        span()["🔍"],
        span(class_="hidden md:inline")["Search..."],
        ShortcutHint("cmd+k", class_="ml-2"),
    ]
```

---

## Step 5: Implement Vim-style Navigation on Board

For vim-style navigation, we use PyNext's keyboard module with context-aware shortcuts:

```python
# Add to pages/board.py

from pynext import Signal
from pynext.keyboard import on_keydown
from pynext.focus import RovingFocus, RovingFocusItem

# Board navigation state
current_column = Signal(0)
current_task = Signal(0)

# =============================================================================
# Board Navigation Shortcuts
# =============================================================================

@on_keydown("j", context="global")
def move_down():
    """Move to next task in column."""
    current_task.update(lambda x: x + 1)


@on_keydown("k", context="global")
def move_up():
    """Move to previous task in column."""
    current_task.update(lambda x: max(0, x - 1))


@on_keydown("h", context="global")
def move_left():
    """Move to previous column."""
    current_column.update(lambda x: max(0, x - 1))
    current_task.set(0)  # Reset task position


@on_keydown("l", context="global")
def move_right():
    """Move to next column."""
    current_column.update(lambda x: x + 1)
    current_task.set(0)  # Reset task position


@on_keydown("enter", context="global")
def open_selected_task():
    """Open the currently selected task."""
    # Will be implemented with server action
    pass


# =============================================================================
# Board Component with Keyboard Support
# =============================================================================

def TaskBoard():
    """Kanban board with vim-style keyboard navigation."""
    columns = ["Backlog", "Todo", "In Progress", "Done"]
    
    return div(class_="flex gap-4 p-4 overflow-x-auto")[
        [
            TaskColumn(
                name=col,
                index=i,
                is_active=current_column() == i,
            )
            for i, col in enumerate(columns)
        ]
    ]


def TaskColumn(name: str, index: int, is_active: bool):
    """A column in the Kanban board."""
    tasks = get_tasks_by_status(name.lower().replace(" ", "_"))
    
    return div(
        class_=cn(
            "w-72 shrink-0 bg-muted/50 rounded-lg p-3",
            "ring-2 ring-primary" if is_active else "",
        ),
        data_column=index,
    )[
        # Column header
        div(class_="flex items-center justify-between mb-3")[
            span(class_="font-medium text-sm")[name],
            span(class_="text-xs text-muted-foreground bg-background px-1.5 py-0.5 rounded")[
                len(tasks)
            ],
        ],
        
        # Tasks with RovingFocus for keyboard navigation
        RovingFocus(orientation="vertical")[
            [
                TaskCard(
                    task=task,
                    is_selected=is_active and current_task() == i,
                )
                for i, task in enumerate(tasks)
            ]
        ],
    ]


def TaskCard(task, is_selected: bool):
    """A task card in the Kanban column."""
    return RovingFocusItem()[
        a(
            href=f"/tasks/{task.id}",
            class_=cn(
                "block p-3 bg-card rounded-md border mb-2",
                "hover:border-primary transition-colors",
                "ring-2 ring-primary" if is_selected else "",
                "focus:outline-none focus:ring-2 focus:ring-primary",
            ),
            data_task=task.id,
        )[
            span(class_="text-sm font-medium block mb-1")[task.title],
            div(class_="flex items-center gap-2")[
                task.priority and PriorityBadge(task.priority),
                task.due_date and span(class_="text-xs text-muted-foreground")[
                    format_date(task.due_date)
                ],
            ],
        ],
    ]
```

---

## Step 6: Create Shortcuts Help Dialog

Use the built-in `ShortcutsHelpDialog` component:

```python
from pynext.keyboard import ShortcutsHelpDialog, ShortcutHint
from pynext.shadcn import Button

def HelpButton():
    """Button that opens the shortcuts help dialog."""
    return ShortcutsHelpDialog(
        trigger=Button(variant="ghost", size="icon")["?"],
    )


# Or create a custom shortcuts list
def ShortcutsHelp():
    """Full list of keyboard shortcuts."""
    shortcuts = [
        ("Navigation", [
            ("G D", "Go to dashboard"),
            ("G B", "Go to board"),
            ("G S", "Go to settings"),
        ]),
        ("Actions", [
            ("N", "New task"),
            ("⌘ K", "Open command palette"),
            ("/", "Quick search"),
        ]),
        ("Task Board", [
            ("J", "Move down"),
            ("K", "Move up"),
            ("H", "Move left"),
            ("L", "Move right"),
            ("Enter", "Open task"),
        ]),
        ("General", [
            ("T D", "Toggle dark mode"),
            ("?", "Show shortcuts"),
            ("Esc", "Close dialog"),
        ]),
    ]
    
    return div(class_="space-y-6")[
        [
            div()[
                span(class_="text-sm font-semibold mb-2 block")[category],
                div(class_="space-y-2")[
                    [
                        div(class_="flex items-center justify-between")[
                            span(class_="text-sm text-muted-foreground")[desc],
                            ShortcutHint(keys),
                        ]
                        for keys, desc in items
                    ]
                ],
            ]
            for category, items in shortcuts
        ]
    ]
```

---

## Step 7: Test Keyboard Navigation

1. Start the dev server:
   ```bash
   pynext dev
   ```

2. Test the shortcuts:
   - Press `⌘K` (or `Ctrl+K`) to open command palette
   - Type to search tasks and projects
   - Use `↑↓` to navigate, `Enter` to select
   - Press `Esc` to close
   - Press `N` to create a new task
   - Press `G` then `D` to go to dashboard
   - Press `G` then `B` to go to board
   - Press `T` then `D` to toggle dark mode
   - On the board, use `j/k/h/l` to navigate

---

## What We Built

In this part, we:

- **Registered keyboard shortcuts** using `@on_keydown`
- **Created key sequences** using `@on_key_sequence`  
- **Built a command palette** with focus trapping
- **Implemented vim-style navigation** on the task board
- **Used RovingFocus** for accessible keyboard navigation

### Key PyNext Features Used

| Feature | Purpose |
|---------|---------|
| `@on_keydown` | Register single-key shortcuts |
| `@on_key_sequence` | Register multi-key sequences |
| `FocusTrap` | Keep focus inside dialogs |
| `RovingFocus` | Arrow key navigation in lists |
| `ShortcutHint` | Display shortcut keys |
| `ShortcutProvider` | Inject keyboard runtime |

### Zero JavaScript Required

Notice that we didn't write any JavaScript! PyNext's keyboard module handles:
- Platform detection (⌘ vs Ctrl)
- Context awareness (skip in inputs)
- Sequence timing
- Focus management

### Keyboard Shortcuts Summary

| Shortcut | Action |
|----------|--------|
| `⌘K` | Open command palette |
| `/` | Quick search |
| `N` | New task |
| `G D` | Go to dashboard |
| `G B` | Go to board |
| `G S` | Go to settings |
| `T D` | Toggle dark mode |
| `j/k` | Move down/up (on board) |
| `h/l` | Move left/right (on board) |
| `Enter` | Open selected item |
| `Esc` | Close dialog |

---

## Next Up

In **Part 8**, we'll add loading states, error handling, and prepare for deployment.

[**Continue to Part 8: Polish & Deploy →**](./08-polish-deploy.md)
