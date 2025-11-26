# Command

> **Like Spotlight or VS Code's Command Palette — press ⌘K, type, act**

A searchable command palette for fast keyboard-driven actions.

---

## First Principles: What IS a Command Palette?

### The Core Concept

A command palette is a **universal search box for actions**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE COMMAND PALETTE CONCEPT                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User presses ⌘K (or Ctrl+K):                                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  🔍 Type a command...                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  SUGGESTIONS                                                         │    │
│  │  ───────────                                                        │    │
│  │  📄 New Document                                             ⌘N     │    │
│  │  📁 Open File                                                ⌘O     │    │
│  │  💾 Save                                                     ⌘S     │    │
│  │  ⚙️ Settings                                                 ⌘,     │    │
│  │  👤 Profile                                                         │    │
│  │                                                                      │    │
│  │  RECENT                                                              │    │
│  │  ──────                                                             │    │
│  │  📄 project-plan.md                                                  │    │
│  │  📄 meeting-notes.md                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Type "set" → Shows only "Settings"                                          │
│  Press Enter → Executes action                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Command Palettes Are Powerful

```
WITHOUT COMMAND PALETTE:            WITH COMMAND PALETTE:
────────────────────────            ─────────────────────

To open settings:                   To open settings:
1. Look at menu bar                 1. Press ⌘K
2. Click "File"                     2. Type "set"
3. Scan for "Preferences"           3. Press Enter
4. Click "Settings"
                                    DONE in 2 seconds!
4 steps, 5+ seconds
Mouse required                      Keyboard only
Requires memorizing menus           Natural language search
```

---

## How It Works

### Component Hierarchy

```
Command                            ← Root container
├── CommandInput                   ← Search input
├── CommandList                    ← Scrollable results area
│   ├── CommandEmpty               ← "No results" message
│   ├── CommandGroup               ← Category heading
│   │   ├── CommandItem            ← Individual action
│   │   └── CommandItem
│   └── CommandSeparator           ← Visual divider
└── CommandShortcut                ← Keyboard hint (⌘K)
```

### The State Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMMAND PALETTE FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. ACTIVATION                                                               │
│     └── User presses ⌘K (global shortcut)                                   │
│     └── Dialog appears, input focused                                        │
│                                                                              │
│  2. SEARCH                                                                   │
│     └── User types query                                                     │
│     └── Items filtered by text match                                         │
│     └── First match auto-selected                                            │
│                                                                              │
│  3. NAVIGATION                                                               │
│     └── Arrow keys move selection                                            │
│     └── Enter executes selected item                                         │
│     └── Escape closes palette                                                │
│                                                                              │
│  4. EXECUTION                                                                │
│     └── Item's onSelect handler runs                                         │
│     └── Palette closes                                                       │
│     └── Action performed                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add command
```

Or import directly:

```python
from pynext.shadcn import (
    Command, CommandInput, CommandList, CommandEmpty,
    CommandGroup, CommandItem, CommandSeparator, CommandShortcut,
    CommandDialog
)
```

---

## Step-by-Step Usage

### Step 1: Basic Command Menu

```python
Command(class_="rounded-lg border shadow-md")[
    CommandInput(placeholder="Type a command or search..."),
    CommandList()[
        CommandEmpty()["No results found."],
        CommandGroup(heading="Suggestions")[
            CommandItem()["Calendar"],
            CommandItem()["Search Emoji"],
            CommandItem()["Calculator"],
        ],
    ]
]
```

### Step 2: With Dialog (⌘K Pattern)

```python
from pynext import Signal
from pynext.keyboard import on_keydown

is_open = Signal(False)

# Global keyboard shortcut
@on_keydown("cmd+k")
def open_command():
    is_open.set(True)

CommandDialog(open=is_open.value, on_open_change=is_open.set)[
    CommandInput(placeholder="Type a command..."),
    CommandList()[
        CommandEmpty()["No results found."],
        
        CommandGroup(heading="Actions")[
            CommandItem(on_select=lambda: navigate("/new"))[
                Icons.plus(class_="mr-2 h-4 w-4"),
                "New Document",
                CommandShortcut()["⌘N"]
            ],
            CommandItem(on_select=lambda: save())[
                Icons.save(class_="mr-2 h-4 w-4"),
                "Save",
                CommandShortcut()["⌘S"]
            ],
        ],
        
        CommandSeparator(),
        
        CommandGroup(heading="Settings")[
            CommandItem(on_select=lambda: navigate("/settings"))[
                Icons.settings(class_="mr-2 h-4 w-4"),
                "Settings",
                CommandShortcut()["⌘,"]
            ],
        ],
    ]
]
```

### Step 3: With Dynamic Data

```python
from pynext import Signal

search_results = Signal([])

async def search(query: str):
    results = await api.search(query)
    search_results.set(results)

Command()[
    CommandInput(
        placeholder="Search...",
        on_value_change=lambda v: search(v)
    ),
    CommandList()[
        CommandEmpty()["No results found."],
        
        search_results.value and CommandGroup(heading="Results")[
            [
                CommandItem(
                    value=r["id"],
                    on_select=lambda: navigate(f"/item/{r['id']}")
                )[
                    r["title"]
                ]
                for r in search_results.value
            ]
        ]
    ]
]
```

---

## Common Patterns

### Pattern 1: Application Command Palette

```python
CommandDialog(open=is_open.value, on_open_change=is_open.set)[
    CommandInput(placeholder="What do you need?"),
    CommandList()[
        CommandEmpty()["No results. Try a different search."],
        
        # Quick Actions
        CommandGroup(heading="Quick Actions")[
            CommandItem()[Icons.plus(), "Create Project"],
            CommandItem()[Icons.upload(), "Upload File"],
            CommandItem()[Icons.users(), "Invite Team Member"],
        ],
        
        CommandSeparator(),
        
        # Navigation  
        CommandGroup(heading="Go To")[
            CommandItem()[Icons.home(), "Dashboard", CommandShortcut()["G D"]],
            CommandItem()[Icons.folder(), "Projects", CommandShortcut()["G P"]],
            CommandItem()[Icons.settings(), "Settings", CommandShortcut()["G S"]],
        ],
        
        CommandSeparator(),
        
        # Theme
        CommandGroup(heading="Theme")[
            CommandItem(on_select=lambda: set_theme("light"))[Icons.sun(), "Light Mode"],
            CommandItem(on_select=lambda: set_theme("dark"))[Icons.moon(), "Dark Mode"],
            CommandItem(on_select=lambda: set_theme("system"))[Icons.monitor(), "System"],
        ],
    ]
]
```

### Pattern 2: Search with Categories

```python
Command()[
    CommandInput(placeholder="Search everything..."),
    CommandList()[
        # Files
        files and CommandGroup(heading="Files")[
            [CommandItem(value=f["id"])[Icons.file(), f["name"]] for f in files]
        ],
        
        # Users
        users and CommandGroup(heading="People")[
            [
                CommandItem(value=u["id"])[
                    Avatar(class_="h-6 w-6 mr-2")[AvatarImage(src=u["avatar"])],
                    u["name"]
                ]
                for u in users
            ]
        ],
        
        # Commands
        CommandGroup(heading="Commands")[
            CommandItem()["Create new file"],
            CommandItem()["Open settings"],
        ],
    ]
]
```

### Pattern 3: Nested Commands

```python
# State to track current "page"
page = Signal("root")

Command()[
    CommandInput(placeholder="Search..."),
    CommandList()[
        # Root level
        page.value == "root" and CommandGroup()[
            CommandItem(on_select=lambda: page.set("projects"))[
                "Projects", Icons.chevron_right()
            ],
            CommandItem(on_select=lambda: page.set("team"))[
                "Team", Icons.chevron_right()
            ],
        ],
        
        # Projects submenu
        page.value == "projects" and [
            CommandItem(on_select=lambda: page.set("root"))[
                Icons.arrow_left(), "Back"
            ],
            CommandGroup(heading="Projects")[
                CommandItem()["Project Alpha"],
                CommandItem()["Project Beta"],
            ]
        ],
    ]
]
```

---

## API Reference

### Command

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | `""` | Search value |
| `on_value_change` | callable | `None` | Called when search changes |

### CommandDialog

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | bool | `False` | Whether dialog is open |
| `on_open_change` | callable | `None` | Called when open state changes |

### CommandItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | `None` | Search value (defaults to text) |
| `disabled` | bool | `False` | Disable this item |
| `on_select` | callable | `None` | Called when selected |
| `keywords` | str | `""` | Additional search keywords |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate items |
| `Enter` | Select item |
| `Escape` | Close palette |
| `⌘K` | Open palette (with global shortcut) |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **ARIA Roles** | `role="combobox"`, `role="listbox"` |
| **Live Region** | Results announced to screen readers |
| **Focus Management** | Focus trapped in dialog |
| **Keyboard Only** | Fully usable without mouse |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| ⌘K not working | Missing global shortcut | Add `@on_keydown("cmd+k")` |
| Items not filtering | No value prop | Ensure text content is searchable |
| Dialog not closing | Missing on_open_change | Add handler to close |
| Slow with many items | Too many DOM nodes | Virtualize the list |

---

## Related Components

- **[Dialog](./dialog.md)** — Used internally for CommandDialog
- **[Combobox](./combobox.md)** — For single selections with search
- **[DropdownMenu](./dropdown-menu.md)** — For simple action menus
