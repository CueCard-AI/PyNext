# Dropdown Menu

> **Like a hidden drawer that reveals options when you click a button**

A menu that appears on demand, showing a list of actions or choices.

---

## First Principles: What IS a Dropdown Menu?

### The Core Concept

A dropdown menu is a **hidden list of options** that appears on demand:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE DROPDOWN CONCEPT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BEFORE CLICK:                     AFTER CLICK:                              │
│  ─────────────                     ────────────                              │
│                                                                              │
│  ┌──────────┐                      ┌──────────┐                             │
│  │  Menu ▼  │                      │  Menu ▲  │                             │
│  └──────────┘                      └──────────┘                             │
│                                    ┌──────────┐                             │
│  (options hidden)                  │ Edit     │                             │
│                                    │ Copy     │                             │
│                                    │ Delete   │                             │
│                                    └──────────┘                             │
│                                                                              │
│  Click outside or select → Menu closes                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Dropdown Menus Exist

They solve the **"too many buttons"** problem:

```
WITHOUT DROPDOWN:                    WITH DROPDOWN:
─────────────────                    ───────────────

┌──────┐ ┌──────┐ ┌──────┐          ┌──────────┐
│ Edit │ │ Copy │ │ Paste│          │ Actions ▼│
└──────┘ └──────┘ └──────┘          └──────────┘
┌──────┐ ┌────────┐ ┌──────┐
│ Cut  │ │ Rename │ │Delete│        ↓ click
└──────┘ └────────┘ └──────┘
                                    ┌──────────┐
6 buttons visible!                  │ Edit     │
Cluttered UI                        │ Copy     │
Overwhelms user                     │ Paste    │
                                    │ Cut      │
                                    │ Rename   │
                                    │ Delete   │
                                    └──────────┘

                                    1 button visible!
                                    Clean UI
                                    Actions available on demand
```

---

## How It Works

### Component Hierarchy

```
DropdownMenu                        ← Root: manages open/close
├── DropdownMenuTrigger             ← Button that opens menu
│   └── Button()["Actions"]
└── DropdownMenuContent             ← The menu itself
    ├── DropdownMenuLabel           ← Section heading
    ├── DropdownMenuItem            ← Clickable action
    ├── DropdownMenuSeparator       ← Visual divider
    ├── DropdownMenuCheckboxItem    ← Toggle option
    ├── DropdownMenuRadioGroup      ← Single-select options
    │   └── DropdownMenuRadioItem
    └── DropdownMenuSub             ← Nested submenu
```

### The Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DROPDOWN LIFECYCLE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CLOSED STATE                                                             │
│     └── Only trigger visible                                                 │
│                                                                              │
│  2. CLICK TRIGGER                                                            │
│     └── Menu content appears                                                 │
│     └── First item focused                                                   │
│                                                                              │
│  3. NAVIGATION                                                               │
│     └── Arrow keys move focus                                                │
│     └── Enter/Space activates item                                           │
│     └── Escape closes menu                                                   │
│                                                                              │
│  4. ITEM SELECTED                                                            │
│     └── Item's action runs                                                   │
│     └── Menu closes                                                          │
│     └── Focus returns to trigger                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add dropdown-menu
```

Or import directly:

```python
from pynext.shadcn import (
    DropdownMenu, DropdownMenuTrigger, DropdownMenuContent,
    DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator,
    DropdownMenuCheckboxItem, DropdownMenuRadioGroup, DropdownMenuRadioItem,
    DropdownMenuSub, DropdownMenuSubTrigger, DropdownMenuSubContent
)
```

---

## Step-by-Step Usage

### Step 1: Basic Menu

```python
DropdownMenu()[
    DropdownMenuTrigger()[
        Button()["Open Menu"]
    ],
    DropdownMenuContent()[
        DropdownMenuItem()["Profile"],
        DropdownMenuItem()["Settings"],
        DropdownMenuItem()["Logout"],
    ]
]
```

### Step 2: Organized with Labels and Separators

```python
DropdownMenu()[
    DropdownMenuTrigger()[
        Button(variant="outline")["Actions"]
    ],
    DropdownMenuContent(class_="w-56")[
        DropdownMenuLabel()["My Account"],
        DropdownMenuSeparator(),
        
        DropdownMenuItem()[
            Icons.user(class_="mr-2 h-4 w-4"),
            "Profile",
        ],
        DropdownMenuItem()[
            Icons.settings(class_="mr-2 h-4 w-4"),
            "Settings",
        ],
        
        DropdownMenuSeparator(),
        
        DropdownMenuItem(class_="text-red-600")[
            Icons.logout(class_="mr-2 h-4 w-4"),
            "Logout",
        ],
    ]
]
```

### Step 3: With Keyboard Shortcuts

```python
DropdownMenuContent()[
    DropdownMenuItem()[
        "Cut",
        DropdownMenuShortcut()["⌘X"]
    ],
    DropdownMenuItem()[
        "Copy",
        DropdownMenuShortcut()["⌘C"]
    ],
    DropdownMenuItem()[
        "Paste",
        DropdownMenuShortcut()["⌘V"]
    ],
]
```

### Step 4: Checkbox Items

```python
from pynext import Signal

show_panel = Signal(True)

DropdownMenuContent()[
    DropdownMenuCheckboxItem(
        checked=show_panel.value,
        on_checked_change=show_panel.set
    )["Show Panel"],
    DropdownMenuCheckboxItem(checked=True)["Show Sidebar"],
]
```

### Step 5: Radio Group

```python
from pynext import Signal

theme = Signal("system")

DropdownMenuContent()[
    DropdownMenuLabel()["Theme"],
    DropdownMenuSeparator(),
    DropdownMenuRadioGroup(value=theme.value, on_value_change=theme.set)[
        DropdownMenuRadioItem(value="light")["Light"],
        DropdownMenuRadioItem(value="dark")["Dark"],
        DropdownMenuRadioItem(value="system")["System"],
    ]
]
```

### Step 6: Submenus

```python
DropdownMenuContent()[
    DropdownMenuItem()["New Tab"],
    DropdownMenuSub()[
        DropdownMenuSubTrigger()["Share"],
        DropdownMenuSubContent()[
            DropdownMenuItem()["Email"],
            DropdownMenuItem()["Twitter"],
            DropdownMenuItem()["Facebook"],
        ]
    ],
    DropdownMenuSeparator(),
    DropdownMenuItem()["Settings"],
]
```

---

## Common Patterns

### Pattern 1: Row Actions (Tables)

```python
# In a DataTable cell
DropdownMenu()[
    DropdownMenuTrigger()[
        Button(variant="ghost", size="icon")[
            Icons.more_horizontal(class_="h-4 w-4")
        ]
    ],
    DropdownMenuContent(align="end")[
        DropdownMenuItem(on_click=lambda: edit(row["id"]))["Edit"],
        DropdownMenuItem(on_click=lambda: duplicate(row["id"]))["Duplicate"],
        DropdownMenuSeparator(),
        DropdownMenuItem(
            class_="text-red-600",
            on_click=lambda: delete(row["id"])
        )["Delete"],
    ]
]
```

### Pattern 2: User Menu

```python
DropdownMenu()[
    DropdownMenuTrigger()[
        Avatar()[
            AvatarImage(src=user.avatar),
            AvatarFallback()[user.initials]
        ]
    ],
    DropdownMenuContent(class_="w-56", align="end")[
        DropdownMenuLabel()[
            div(class_="flex flex-col")[
                span(class_="font-medium")[user.name],
                span(class_="text-xs text-muted-foreground")[user.email]
            ]
        ],
        DropdownMenuSeparator(),
        DropdownMenuItem()["Profile"],
        DropdownMenuItem()["Billing"],
        DropdownMenuItem()["Settings"],
        DropdownMenuSeparator(),
        DropdownMenuItem()["Logout"],
    ]
]
```

### Pattern 3: Context Menu (Right-Click)

```python
# Wrap content to add right-click menu
ContextMenu()[
    ContextMenuTrigger()[
        div(class_="border rounded p-10")["Right-click me"]
    ],
    ContextMenuContent()[
        ContextMenuItem()["Back"],
        ContextMenuItem()["Forward"],
        ContextMenuItem()["Refresh"],
    ]
]
```

---

## API Reference

### DropdownMenu

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | bool | `None` | Controlled open state |
| `on_open_change` | callable | `None` | Called when state changes |
| `modal` | bool | `True` | Trap focus when open |

### DropdownMenuContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `align` | str | `"center"` | `"start"`, `"center"`, `"end"` |
| `side` | str | `"bottom"` | `"top"`, `"right"`, `"bottom"`, `"left"` |
| `side_offset` | int | `4` | Distance from trigger |

### DropdownMenuItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `disabled` | bool | `False` | Disable item |
| `on_select` | callable | `None` | Called when selected |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **ARIA Roles** | `role="menu"`, `role="menuitem"` |
| **Arrow Keys** | Up/Down to navigate items |
| **Home/End** | Jump to first/last item |
| **Escape** | Close menu, return focus to trigger |
| **Type-ahead** | Type to jump to matching item |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Menu not opening | Missing DropdownMenuTrigger | Wrap trigger in component |
| Wrong position | Default alignment | Use `align` and `side` props |
| Focus issues | Modal mode | Set `modal={False}` if needed |
| Click not registering | Nested buttons | Use `as_child` on trigger |

---

## Related Components

- **[Button](./button.md)** — Common trigger element
- **[Dialog](./dialog.md)** — For more complex interactions
- **[Command](./command.md)** — For searchable actions
