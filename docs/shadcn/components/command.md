# Command

A fast, composable command menu with fuzzy search. Similar to cmdk.

## Installation

```python
from pynext.shadcn import (
    Command, CommandDialog, CommandInput, CommandList,
    CommandEmpty, CommandGroup, CommandItem,
    CommandSeparator, CommandShortcut
)
```

## Basic Usage

```python
Command()[
    CommandInput(placeholder="Type a command or search..."),
    CommandList()[
        CommandEmpty()["No results found."],
        CommandGroup(heading="Suggestions")[
            CommandItem(value="calendar")["Calendar"],
            CommandItem(value="search")["Search Emoji"],
            CommandItem(value="calculator")["Calculator"],
        ],
    ]
]
```

## Examples

### Command Dialog (⌘K)

```python
# Triggered with Cmd+K (or Ctrl+K on Windows)
CommandDialog(open=is_open, on_open_change=set_open)[
    CommandInput(placeholder="Search..."),
    CommandList()[
        CommandEmpty()["No results found."],
        CommandGroup(heading="Actions")[
            CommandItem(value="new", on_select=create_new)[
                "Create New Document",
                CommandShortcut()["⌘N"]
            ],
            CommandItem(value="save", on_select=save)[
                "Save",
                CommandShortcut()["⌘S"]
            ],
        ],
        CommandSeparator(),
        CommandGroup(heading="Navigation")[
            CommandItem(value="home")["Home"],
            CommandItem(value="settings")["Settings"],
        ],
    ]
]
```

### With Icons

```python
CommandItem(value="settings")[
    span(class_="flex items-center gap-2")[
        "⚙️",
        "Settings"
    ],
    CommandShortcut()["⌘,"]
]
```

### Nested Groups

```python
CommandList()[
    CommandGroup(heading="Pages")[
        CommandItem(value="home")["Home"],
        CommandItem(value="about")["About"],
    ],
    CommandSeparator(),
    CommandGroup(heading="Settings")[
        CommandItem(value="profile")["Profile"],
        CommandItem(value="billing")["Billing"],
        CommandItem(value="notifications")["Notifications"],
    ],
]
```

### With Disabled Items

```python
CommandItem(value="premium", disabled=True)[
    "Premium Feature"
]
```

## API Reference

### Command

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `str` | `None` | Selected value |
| `on_value_change` | `Callable` | `None` | Selection callback |
| `loop` | `bool` | `False` | Loop keyboard navigation |

### CommandDialog

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | `bool` | `None` | Controlled open state |
| `on_open_change` | `Callable` | `None` | State change callback |

### CommandInput

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `placeholder` | `str` | `"Search..."` | Placeholder text |

### CommandItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `str` | required | Search/select value |
| `on_select` | `Callable` | `None` | Selection callback |
| `disabled` | `bool` | `False` | Disable selection |

### CommandShortcut

Displays keyboard shortcut hints (e.g., "⌘K").

## Keyboard Navigation

- `↓/↑` - Navigate items
- `Enter` - Select highlighted item
- `Escape` - Close dialog
- Type to filter items

## Integration with @on_keydown

```python
from pynext import on_keydown

@on_keydown("cmd+k")
def open_command_palette():
    command_open.set(True)
```

