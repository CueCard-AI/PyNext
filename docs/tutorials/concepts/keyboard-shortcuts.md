# Keyboard Shortcuts

> **Add power-user keyboard navigation to your app**

Learn how to implement global shortcuts, focus management, and accessible keyboard navigation using PyNext's built-in keyboard module.

---

## What You'll Learn

- Global keyboard shortcuts with `@on_keydown`
- Key sequences with `@on_key_sequence`
- Focus trapping and management
- Command palette implementation
- Platform-specific shortcuts (Mac/Windows)

---

## The PyNext Approach

PyNext provides a `pynext.keyboard` module that handles keyboard shortcuts without writing JavaScript:

```python
from pynext.keyboard import on_keydown, on_key_sequence, ShortcutHint

# Single-key shortcut
@on_keydown("cmd+k")
def open_search():
    search_open.set(True)

# Multi-key sequence
@on_key_sequence("g d")
def go_dashboard():
    navigate("/")
```

**Benefits over raw JavaScript:**
- Type-safe key definitions
- Automatic platform detection (⌘ on Mac, Ctrl on Windows)
- Context awareness (skip in inputs)
- Sequence handling with timeout
- Integration with PyNext signals

---

## Registering Shortcuts

### Using Decorators

The most common way to register shortcuts:

```python
from pynext.keyboard import on_keydown
from pynext import Signal

# State
search_open = Signal(False)
new_item_open = Signal(False)

@on_keydown("cmd+k")
def open_search():
    """Open the search dialog with Cmd/Ctrl+K."""
    search_open.set(True)

@on_keydown("escape", context="dialog")
def close_dialogs():
    """Close any open dialog with Escape."""
    search_open.set(False)
    new_item_open.set(False)

@on_keydown("n", context="global")
def create_new():
    """Create new item with N key."""
    new_item_open.set(True)

@on_keydown("?", context="global")
def show_help():
    """Show keyboard shortcuts help with ?."""
    help_open.set(True)
```

### Key Combo Syntax

PyNext understands these modifiers:

| Python | Mac | Windows/Linux |
|--------|-----|---------------|
| `cmd` | ⌘ Command | Ctrl |
| `ctrl` | ⌃ Control | Ctrl |
| `alt` | ⌥ Option | Alt |
| `shift` | ⇧ Shift | Shift |

Examples:
- `"cmd+k"` → ⌘K on Mac, Ctrl+K on Windows
- `"ctrl+shift+s"` → Ctrl+Shift+S everywhere
- `"alt+n"` → ⌥N on Mac, Alt+N on Windows
- `"escape"` → Escape key (no modifier)

### Context Options

Control when shortcuts fire:

```python
# Only fires when NOT in an input field (default)
@on_keydown("n", context="global")
def create_new():
    pass

# Only fires when a dialog is open
@on_keydown("escape", context="dialog")
def close_dialog():
    pass

# Fires even in input fields
@on_keydown("cmd+enter", context="always")
def submit_form():
    pass

# Only fires when in an input field
@on_keydown("cmd+b", context="input")
def bold_text():
    pass
```

---

## Key Sequences

For multi-key sequences like "g d" (press G, then D):

```python
from pynext.keyboard import on_key_sequence
from pynext import navigate

@on_key_sequence("g d")
def go_dashboard():
    """Navigate to dashboard with G then D."""
    navigate("/")

@on_key_sequence("g b")
def go_board():
    """Navigate to board with G then B."""
    navigate("/board")

@on_key_sequence("g s")
def go_settings():
    """Navigate to settings with G then S."""
    navigate("/settings")

@on_key_sequence("t d", timeout=500)
def toggle_dark():
    """Toggle dark mode with T then D (within 500ms)."""
    from pynext.theme import use_theme
    theme = use_theme()
    theme.set("dark" if theme() == "light" else "light")
```

**How sequences work:**
1. Press the first key (e.g., `g`)
2. Within the timeout (default 1000ms), press the next key
3. The handler fires when the full sequence is matched
4. If you don't press the next key in time, the sequence resets

---

## Programmatic Registration

For dynamic shortcuts:

```python
from pynext.keyboard import register_shortcut, unregister_shortcut

# Register at runtime
shortcut_id = register_shortcut(
    "cmd+shift+n",
    handler=create_new_project,
    context="global",
)

# Later, unregister
unregister_shortcut(shortcut_id)
```

---

## Focus Management

### Focus Trap

Keep focus inside a dialog or modal:

```python
from pynext.focus import FocusTrap

def Modal():
    return div(class_="modal")[
        FocusTrap(auto_focus=True, restore_focus=True)[
            div(class_="modal-content")[
                Input(placeholder="Name"),
                Input(placeholder="Email"),
                Button()["Submit"],
                Button(variant="ghost")["Cancel"],
            ]
        ]
    ]
```

**What FocusTrap does:**
- Traps Tab/Shift+Tab within the container
- Auto-focuses the first focusable element
- Restores focus to the previous element when closed

### Roving Focus

For arrow key navigation in lists:

```python
from pynext.focus import RovingFocus, RovingFocusItem

def CommandList(items):
    return RovingFocus(orientation="vertical", loop=True)[
        [
            RovingFocusItem()[
                Button(class_="w-full text-left")[item.label]
            ]
            for item in items
        ]
    ]
```

**How RovingFocus works:**
- Arrow keys move focus between items
- Only one item is tabbable at a time
- Home/End jump to first/last item
- Works with `orientation="vertical"` (↑↓) or `"horizontal"` (←→)

---

## Command Palette

Build a command palette (like VS Code's Cmd+K):

```python
from pynext import div, input_, Signal, Show
from pynext.keyboard import on_keydown, ShortcutHint
from pynext.focus import FocusTrap, RovingFocus, RovingFocusItem
from pynext.tw import cn

# State
palette_open = Signal(False)
search_query = Signal("")

@on_keydown("cmd+k")
def toggle_palette():
    palette_open.set(not palette_open())

@on_keydown("escape", context="dialog")
def close_palette():
    palette_open.set(False)


def CommandPalette():
    """Global command palette."""
    commands = [
        {"icon": "🏠", "label": "Go to Dashboard", "shortcut": "G D", "action": "/"},
        {"icon": "📋", "label": "Go to Board", "shortcut": "G B", "action": "/board"},
        {"icon": "➕", "label": "New Task", "shortcut": "N", "action": "new_task"},
        {"icon": "⚙️", "label": "Settings", "shortcut": "G S", "action": "/settings"},
        {"icon": "🌙", "label": "Toggle Dark Mode", "shortcut": "T D", "action": "toggle_theme"},
    ]
    
    return Show(when=palette_open)[
        div(
            class_="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm",
            onclick=lambda: palette_open.set(False),
        )[
            div(
                class_=cn(
                    "fixed left-1/2 top-20 -translate-x-1/2",
                    "w-full max-w-lg bg-card border rounded-lg shadow-lg",
                ),
                onclick=lambda e: e.stopPropagation(),
            )[
                FocusTrap(auto_focus=True)[
                    # Search input
                    div(class_="flex items-center gap-2 p-4 border-b")[
                        "🔍",
                        input_(
                            placeholder="Search commands...",
                            class_="flex-1 bg-transparent outline-none",
                            oninput=lambda e: search_query.set(e.target.value),
                        ),
                        ShortcutHint("cmd+k"),
                    ],
                    
                    # Results
                    RovingFocus(orientation="vertical")[
                        div(class_="p-2 max-h-80 overflow-y-auto")[
                            [
                                CommandItem(cmd)
                                for cmd in commands
                                if search_query().lower() in cmd["label"].lower()
                            ]
                        ]
                    ],
                ]
            ]
        ]
    ]


def CommandItem(cmd):
    return RovingFocusItem()[
        div(
            class_=cn(
                "flex items-center justify-between p-2 rounded",
                "cursor-pointer hover:bg-accent focus:bg-accent outline-none",
            ),
            onclick=lambda: execute_command(cmd["action"]),
            tabindex="0",
        )[
            div(class_="flex items-center gap-3")[
                cmd["icon"],
                cmd["label"],
            ],
            ShortcutHint(cmd["shortcut"]),
        ]
    ]


def execute_command(action):
    palette_open.set(False)
    
    if action.startswith("/"):
        from pynext import navigate
        navigate(action)
    elif action == "new_task":
        # Trigger new task dialog
        new_task_open.set(True)
    elif action == "toggle_theme":
        from pynext.theme import use_theme
        theme = use_theme()
        theme.set("dark" if theme() == "light" else "light")
```

---

## Displaying Shortcuts

### ShortcutHint Component

Display keyboard shortcuts with platform-aware formatting:

```python
from pynext.keyboard import ShortcutHint

# Displays "⌘K" on Mac, "Ctrl+K" on Windows
ShortcutHint("cmd+k")

# Multiple keys
ShortcutHint("cmd+shift+p")

# In a button
Button()[
    "Search",
    ShortcutHint("cmd+k", class_="ml-2"),
]
```

### Shortcuts Help Dialog

Show all available shortcuts:

```python
from pynext.keyboard import ShortcutsHelpDialog

# Add to your layout
ShortcutsHelpDialog(
    trigger=Button(variant="ghost")["?"]
)
```

Or build a custom list:

```python
def ShortcutsHelp():
    shortcuts = [
        ("Navigation", [
            ("G D", "Go to dashboard"),
            ("G B", "Go to board"),
            ("G S", "Go to settings"),
        ]),
        ("Actions", [
            ("N", "New item"),
            ("⌘ K", "Open search"),
            ("/", "Quick search"),
        ]),
        ("General", [
            ("T D", "Toggle dark mode"),
            ("?", "Show this help"),
            ("Esc", "Close dialog"),
        ]),
    ]
    
    return div(class_="space-y-6")[
        [
            div()[
                h3(class_="font-semibold mb-2")[category],
                div(class_="space-y-1")[
                    [
                        div(class_="flex justify-between")[
                            span(class_="text-muted-foreground")[desc],
                            ShortcutHint(keys),
                        ]
                        for keys, desc in items
                    ]
                ]
            ]
            for category, items in shortcuts
        ]
    ]
```

---

## Provider Setup

Include the keyboard provider in your layout:

```python
from pynext.keyboard import ShortcutProvider

@layout
def root_layout(children):
    return html()[
        head()[...],
        body()[
            ShortcutProvider()[
                # Your app content
                children,
                
                # Command palette (renders when open)
                CommandPalette(),
            ]
        ],
    ]
```

---

## Best Practices

### 1. Use Consistent Patterns

Follow established conventions:
- `⌘K` / `Ctrl+K` for search/command palette
- `N` for new items
- `Escape` for closing dialogs
- `?` for help
- `G + letter` for navigation

### 2. Make Shortcuts Discoverable

- Show shortcut hints in UI
- Provide a help dialog (`?`)
- Add tooltips to buttons

### 3. Context Awareness

Use the `context` parameter to prevent conflicts:
- `"global"` - Skip in input fields
- `"dialog"` - Only in dialogs
- `"always"` - Even in inputs

### 4. Accessibility

- All shortcuts should have mouse alternatives
- Focus management for keyboard users
- Use `FocusTrap` for modals
- Test with keyboard-only navigation

---

## Summary

| Module | Purpose |
|--------|---------|
| `@on_keydown` | Register single-key shortcuts |
| `@on_key_sequence` | Register multi-key sequences |
| `FocusTrap` | Keep focus inside a container |
| `RovingFocus` | Arrow key navigation in lists |
| `ShortcutHint` | Display shortcut key |
| `ShortcutProvider` | Inject keyboard runtime |

---

## Next Steps

- [Theming](./theming.md) - Add dark mode support
- [Component Patterns](./component-patterns.md) - Build reusable components
- [Forms & Validation](./forms-and-validation.md) - Handle user input
