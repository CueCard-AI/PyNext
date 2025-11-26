# Dropdown Menu

A menu triggered by a button click.

## When to Use

Dropdown menus are for:
- **Actions** - Edit, Delete, Share
- **Navigation** - Sub-menus, category lists
- **Options** - View settings, sort options
- **User menu** - Profile, settings, logout

## Installation

```bash
pynext ui add dropdown-menu
```

Or use directly:

```python
from pynext.shadcn import (
    DropdownMenu, DropdownMenuTrigger, DropdownMenuContent,
    DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel
)
```

## Basic Usage

```python
DropdownMenu()[
    DropdownMenuTrigger()[
        Button(variant="outline")["Open Menu"]
    ],
    DropdownMenuContent()[
        DropdownMenuItem()["Profile"],
        DropdownMenuItem()["Settings"],
        DropdownMenuSeparator(),
        DropdownMenuItem()["Logout"]
    ]
]
```

## Sub-Components

| Component | Purpose |
|-----------|---------|
| `DropdownMenu` | Container, manages state |
| `DropdownMenuTrigger` | Element that opens menu |
| `DropdownMenuContent` | The dropdown panel |
| `DropdownMenuItem` | Clickable item |
| `DropdownMenuSeparator` | Visual divider |
| `DropdownMenuLabel` | Non-interactive header |

## Examples

### User Menu

```python
DropdownMenu()[
    DropdownMenuTrigger()[
        Button(variant="ghost", size="icon")[
            Avatar(class_="h-8 w-8")[
                AvatarImage(src="/avatar.jpg"),
                AvatarFallback()["JD"]
            ]
        ]
    ],
    DropdownMenuContent(align="end")[
        DropdownMenuLabel()["My Account"],
        DropdownMenuSeparator(),
        DropdownMenuItem()[
            span(class_="mr-2")["👤"],
            "Profile"
        ],
        DropdownMenuItem()[
            span(class_="mr-2")["⚙️"],
            "Settings"
        ],
        DropdownMenuSeparator(),
        DropdownMenuItem(class_="text-red-600")[
            span(class_="mr-2")["🚪"],
            "Log out"
        ]
    ]
]
```

### With Actions

```python
DropdownMenu()[
    DropdownMenuTrigger()[
        Button(variant="ghost", size="icon")["⋮"]
    ],
    DropdownMenuContent()[
        DropdownMenuItem(on_click=handle_edit)["Edit"],
        DropdownMenuItem(on_click=handle_duplicate)["Duplicate"],
        DropdownMenuSeparator(),
        DropdownMenuItem(
            on_click=handle_delete,
            class_="text-destructive"
        )["Delete"]
    ]
]
```

### Keyboard Shortcuts

```python
DropdownMenuContent()[
    DropdownMenuItem()[
        span(class_="flex-1")["Cut"],
        span(class_="text-xs text-muted-foreground")["⌘X"]
    ],
    DropdownMenuItem()[
        span(class_="flex-1")["Copy"],
        span(class_="text-xs text-muted-foreground")["⌘C"]
    ],
    DropdownMenuItem()[
        span(class_="flex-1")["Paste"],
        span(class_="text-xs text-muted-foreground")["⌘V"]
    ]
]
```

### Disabled Items

```python
DropdownMenuItem(disabled=True)["Can't click this"]
```

## Alignment

```python
# Align to end of trigger
DropdownMenuContent(align="end")

# Align to start (default)
DropdownMenuContent(align="start")

# Align to center
DropdownMenuContent(align="center")
```

## Props Reference

### DropdownMenuContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `align` | str | `"start"` | Alignment: "start", "center", "end" |
| `side` | str | `"bottom"` | Position: "top", "bottom", "left", "right" |
| `class_` | str | `""` | Additional CSS classes |

### DropdownMenuItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `disabled` | bool | `False` | Disable item |
| `on_click` | callable | `None` | Click handler |
| `class_` | str | `""` | Additional CSS classes |

## Accessibility

- Opens with Enter/Space on trigger
- Arrow keys navigate items
- Escape closes menu
- Items are focusable
- Screen reader announces menu items

## Related Components

- [Button](./button.md) - Menu trigger
- [Dialog](./dialog.md) - For complex actions

