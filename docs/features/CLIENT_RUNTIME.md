# PyNext Client Runtime

> **Write Python, get browser interactivity — no JavaScript required**

The PyNext Client Runtime provides Python APIs for common browser interactions. You write Python decorators and functions; PyNext compiles them to efficient JavaScript that runs in the browser.

---

## Table of Contents

1. [The Big Picture](#the-big-picture)
2. [First Principles](#first-principles)
3. [Keyboard Shortcuts](#keyboard-shortcuts)
4. [Theme Management](#theme-management)
5. [Focus Management](#focus-management)
6. [Storage](#storage)
7. [Refs](#refs)
8. [Client Effects](#client-effects)
9. [How It All Works Together](#how-it-all-works-together)

---

## The Big Picture

### The Problem

Traditional web frameworks require you to write JavaScript for browser interactions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Traditional Approach                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Python (Server)              JavaScript (Browser)                         │
│   ┌─────────────┐             ┌─────────────────────────────────┐          │
│   │ def page(): │             │ document.addEventListener(...)   │          │
│   │   return    │             │ localStorage.getItem(...)        │          │
│   │   html(...) │             │ element.classList.toggle(...)    │          │
│   └─────────────┘             │ window.matchMedia(...)           │          │
│                               └─────────────────────────────────┘          │
│                                                                             │
│   You write BOTH languages and manually connect them                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The PyNext Solution

PyNext lets you write everything in Python:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PyNext Approach                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Python (You write)          JavaScript (PyNext generates)                 │
│   ┌─────────────────────┐     ┌─────────────────────────────────┐          │
│   │ @on_keydown("cmd+k")│     │                                 │          │
│   │ def open_search():  │ ──▶ │  // Auto-generated, optimized   │          │
│   │     search.set(True)│     │  // ~5KB total runtime          │          │
│   │                     │     │                                 │          │
│   │ theme = use_theme() │     │                                 │          │
│   └─────────────────────┘     └─────────────────────────────────┘          │
│                                                                             │
│   You write ONLY Python — PyNext handles the browser                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## First Principles

### Why Does This Exist?

Browsers only understand JavaScript. When you press a key, scroll the page, or toggle dark mode, the browser fires JavaScript events. Traditionally, you'd write JavaScript to handle these.

PyNext's insight: **Most browser interactions follow predictable patterns.**

- Keyboard shortcuts? Same pattern every time.
- Dark mode? Same localStorage + CSS class every time.
- Focus trapping? Same Tab key handling every time.

PyNext provides Python APIs for these patterns and generates the JavaScript for you.

### The Two-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                           Your Application                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Tier 1: Client Runtime (~5KB)                     │   │
│  │                                                                      │   │
│  │   Python API              Compiles To              Browser           │   │
│  │   ──────────              ──────────               ───────           │   │
│  │   @on_keydown    ───▶     keyboard.js    ───▶     Key events        │   │
│  │   use_theme()    ───▶     theme.js       ───▶     Dark mode         │   │
│  │   FocusTrap      ───▶     focus.js       ───▶     Tab handling      │   │
│  │   use_storage()  ───▶     storage.js     ───▶     localStorage      │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Tier 2: Server Actions                            │   │
│  │                                                                      │   │
│  │   For complex logic that should run on the server:                   │   │
│  │   - Database queries                                                 │   │
│  │   - Authentication                                                   │   │
│  │   - Business logic                                                   │   │
│  │                                                                      │   │
│  │   @server_action                                                     │   │
│  │   async def save_task(data):                                         │   │
│  │       # Runs on server, not in browser                               │   │
│  │       await db.insert(data)                                          │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tier 1 (Client Runtime)**: Instant browser interactions — no server round-trip.
**Tier 2 (Server Actions)**: Complex logic that needs Python packages, databases, etc.

---

## Keyboard Shortcuts

### The Concept

Keyboard shortcuts make power users happy. They need:
1. **Registration**: Tell the browser "when user presses ⌘K, do this"
2. **Context awareness**: Don't fire when user is typing in an input
3. **Platform detection**: Use ⌘ on Mac, Ctrl on Windows
4. **Sequences**: Support multi-key combos like "g then d"

### Basic Usage

```python
from pynext.keyboard import on_keydown, on_key_sequence
from pynext import Signal

# State
search_open = Signal(False)

# Single-key shortcut
@on_keydown("cmd+k")
def open_search():
    """
    Opens the search dialog.
    
    - On Mac: ⌘K
    - On Windows/Linux: Ctrl+K
    
    PyNext automatically handles platform detection!
    """
    search_open.set(True)
```

### Step-by-Step Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  What happens when you write @on_keydown("cmd+k")                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: PARSE                                                              │
│  ─────────────────────────────────────────────────────                      │
│  "cmd+k" is parsed into:                                                    │
│    - key: "k"                                                               │
│    - modifiers: ["meta"]  (cmd = meta on web)                               │
│                                                                             │
│  Step 2: REGISTER                                                           │
│  ─────────────────────────────────────────────────────                      │
│  A shortcut object is created:                                              │
│    {                                                                        │
│      id: "shortcut_a1b2c3d4",                                               │
│      key: "k",                                                              │
│      modifiers: ["meta"],                                                   │
│      handler_id: "handler_e5f6g7h8",                                        │
│      context: "global"                                                      │
│    }                                                                        │
│                                                                             │
│  Step 3: HYDRATE                                                            │
│  ─────────────────────────────────────────────────────                      │
│  When the page loads, PyNext injects:                                       │
│    - The shortcut config as JSON                                            │
│    - keyboard.js runtime (~2KB)                                             │
│                                                                             │
│  Step 4: LISTEN                                                             │
│  ─────────────────────────────────────────────────────                      │
│  keyboard.js adds: document.addEventListener('keydown', ...)                │
│                                                                             │
│  Step 5: MATCH                                                              │
│  ─────────────────────────────────────────────────────                      │
│  When user presses ⌘K:                                                      │
│    1. keydown event fires                                                   │
│    2. keyboard.js checks: key="k", metaKey=true ✓                           │
│    3. Context check: not in input field ✓                                   │
│    4. Handler executes: search_open.set(True)                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Combination Syntax

```python
# Modifier keys
@on_keydown("cmd+k")      # ⌘K on Mac, Ctrl+K on Windows
@on_keydown("ctrl+s")     # Ctrl+S everywhere
@on_keydown("alt+n")      # ⌥N on Mac, Alt+N on Windows  
@on_keydown("shift+?")    # Shift+? (shows as ?)

# Multiple modifiers
@on_keydown("cmd+shift+p")   # ⌘⇧P
@on_keydown("ctrl+alt+del")  # Ctrl+Alt+Del

# No modifier
@on_keydown("escape")     # Escape key
@on_keydown("enter")      # Enter key
@on_keydown("n")          # Just the N key
```

### Context Options

```python
# "global" (default) - Fires everywhere EXCEPT input fields
@on_keydown("n", context="global")
def new_item():
    # Won't fire if user is typing in a text field
    pass

# "dialog" - Only fires when a dialog is open
@on_keydown("escape", context="dialog")
def close_dialog():
    # Only fires inside [role="dialog"] or data-pynext-dialog
    pass

# "always" - Fires even in input fields
@on_keydown("cmd+enter", context="always")
def submit_form():
    # Fires everywhere, including textareas
    pass

# "input" - Only fires IN input fields
@on_keydown("cmd+b", context="input")
def bold_text():
    # Only fires when focused on input/textarea
    pass
```

### Key Sequences

For vim-style navigation (press G, then D):

```python
@on_key_sequence("g d")
def go_dashboard():
    """
    Navigate to dashboard.
    
    User presses G, then D within 1 second.
    If they wait too long, the sequence resets.
    """
    from pynext import navigate
    navigate("/")

@on_key_sequence("g b")
def go_board():
    navigate("/board")

@on_key_sequence("g s")
def go_settings():
    navigate("/settings")

# Custom timeout
@on_key_sequence("t d", timeout=500)  # 500ms instead of 1000ms
def toggle_dark():
    pass
```

### How Sequences Work

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Key Sequence: "g d" with 1000ms timeout                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Timeline:                                                                  │
│                                                                             │
│  0ms        500ms       1000ms      1500ms                                  │
│  │           │           │           │                                      │
│  ▼           ▼           ▼           ▼                                      │
│  ┌─────────────────────────────────────────────────────┐                   │
│  │  Press G                                             │                   │
│  │    ↓                                                 │                   │
│  │  Buffer: ["g"]                                       │                   │
│  │  Start timer: 1000ms                                 │                   │
│  │    ↓                                                 │                   │
│  │  Press D (within timeout)                            │                   │
│  │    ↓                                                 │                   │
│  │  Buffer: ["g", "d"]                                  │                   │
│  │  Match found! Execute handler.                       │                   │
│  │  Clear buffer.                                       │                   │
│  └─────────────────────────────────────────────────────┘                   │
│                                                                             │
│  If D not pressed within 1000ms:                                            │
│  ┌─────────────────────────────────────────────────────┐                   │
│  │  Timer expires                                       │                   │
│  │    ↓                                                 │                   │
│  │  Buffer cleared: []                                  │                   │
│  │  User must start over.                               │                   │
│  └─────────────────────────────────────────────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Example

```python
# shortcuts.py
"""
Application keyboard shortcuts.

Centralize all shortcuts in one file for maintainability.
"""

from pynext.keyboard import on_keydown, on_key_sequence
from pynext import Signal, navigate

# =============================================================================
# State
# =============================================================================

search_open = Signal(False, name="search_open")
new_task_open = Signal(False, name="new_task_open")
help_open = Signal(False, name="help_open")

# =============================================================================
# Global Shortcuts
# =============================================================================

@on_keydown("cmd+k")
def open_search():
    """Open command palette with ⌘K."""
    search_open.set(True)

@on_keydown("/", context="global")
def quick_search():
    """Open search with / key."""
    search_open.set(True)

@on_keydown("n", context="global")
def new_task():
    """Create new task with N key."""
    new_task_open.set(True)

@on_keydown("?", context="global")
def show_help():
    """Show keyboard shortcuts with ?."""
    help_open.set(True)

# =============================================================================
# Dialog Shortcuts
# =============================================================================

@on_keydown("escape", context="dialog")
def close_dialogs():
    """Close any open dialog with Escape."""
    search_open.set(False)
    new_task_open.set(False)
    help_open.set(False)

# =============================================================================
# Navigation Sequences
# =============================================================================

@on_key_sequence("g d")
def go_dashboard():
    """Go to dashboard with G then D."""
    navigate("/")

@on_key_sequence("g b")
def go_board():
    """Go to board with G then B."""
    navigate("/board")

@on_key_sequence("g s")
def go_settings():
    """Go to settings with G then S."""
    navigate("/settings")

# =============================================================================
# Theme
# =============================================================================

@on_key_sequence("t d")
def toggle_dark():
    """Toggle dark mode with T then D."""
    from pynext.theme import use_theme
    theme = use_theme()
    theme.set("dark" if theme() == "light" else "light")
```

---

## Theme Management

### The Concept

Dark mode needs:
1. **Flash prevention**: Page shouldn't flash white before applying dark theme
2. **System preference**: Respect `prefers-color-scheme`
3. **Persistence**: Remember user's choice
4. **Toggle**: Let users switch manually

### The Flash Problem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  WITHOUT flash prevention:                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Time: 0ms        50ms        100ms       150ms       200ms                 │
│        │           │           │           │           │                    │
│        ▼           ▼           ▼           ▼           ▼                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ ░░░░░░░ │ │ ░░░░░░░ │ │ ░░░░░░░ │ │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │               │
│  │ ░WHITE░ │ │ ░WHITE░ │ │ ░WHITE░ │ │ ▓DARK▓▓ │ │ ▓DARK▓▓ │               │
│  │ ░░░░░░░ │ │ ░░░░░░░ │ │ ░░░░░░░ │ │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
│       │           │           │           │                                 │
│       │           │           │           └── JS finally runs,              │
│       │           │           │               adds .dark class              │
│       │           │           │                                             │
│       └───────────┴───────────┴── User sees WHITE flash! 😫                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  WITH PyNext's ThemeScript:                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Time: 0ms        50ms        100ms       150ms       200ms                 │
│        │           │           │           │           │                    │
│        ▼           ▼           ▼           ▼           ▼                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │               │
│  │ ▓DARK▓▓ │ │ ▓DARK▓▓ │ │ ▓DARK▓▓ │ │ ▓DARK▓▓ │ │ ▓DARK▓▓ │               │
│  │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │ │ ▓▓▓▓▓▓▓ │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
│       │                                                                     │
│       └── Inline script in <head> runs IMMEDIATELY,                         │
│           before any content renders. No flash! 🎉                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Basic Usage

```python
from pynext.theme import ThemeScript, ThemeProvider, ThemeToggle

@layout
def root_layout(children):
    return html()[
        head()[
            # Step 1: Add ThemeScript FIRST in head
            # This prevents the white flash
            ThemeScript(),
            
            link(rel="stylesheet", href="/styles.css"),
        ],
        body()[
            # Step 2: Wrap app in ThemeProvider
            ThemeProvider()[
                header()[
                    Logo(),
                    # Step 3: Add toggle button
                    ThemeToggle(),
                ],
                main()[
                    children
                ],
            ],
        ],
    ]
```

### Step-by-Step Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  How PyNext Theme System Works                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ThemeScript() in <head>                                                 │
│     ────────────────────────                                                │
│     Generates inline JavaScript that runs IMMEDIATELY:                      │
│                                                                             │
│     <script>                                                                │
│       (function() {                                                         │
│         var stored = localStorage.getItem('theme');                         │
│         var prefersDark = matchMedia('(prefers-color-scheme: dark)').matches│
│         if (stored === 'dark' || (!stored && prefersDark)) {                │
│           document.documentElement.classList.add('dark');                   │
│         }                                                                   │
│       })();                                                                  │
│     </script>                                                               │
│                                                                             │
│     This runs BEFORE any CSS or content loads!                              │
│                                                                             │
│  2. ThemeProvider wraps app                                                 │
│     ───────────────────────                                                 │
│     - Creates theme signal                                                  │
│     - Hydrates theme.js runtime                                             │
│     - Listens for system preference changes                                 │
│                                                                             │
│  3. ThemeToggle button                                                      │
│     ────────────────────                                                    │
│     - Shows ☀️ in dark mode, 🌙 in light mode                               │
│     - Clicking calls: __pynext__.theme.cycle()                              │
│     - Cycles: light → dark → system → light                                 │
│                                                                             │
│  4. CSS uses .dark class                                                    │
│     ─────────────────────                                                   │
│     .dark {                                                                 │
│       --background: 222.2 84% 4.9%;  /* Dark background */                  │
│       --foreground: 210 40% 98%;     /* Light text */                       │
│     }                                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Programmatic Theme Control

```python
from pynext.theme import use_theme

# Get the theme signal
theme = use_theme()

# Read current mode
def get_current():
    mode = theme()  # Returns: "light", "dark", or "system"
    return mode

# Set mode directly
def set_dark():
    theme.set("dark")

def set_light():
    theme.set("light")

def set_system():
    theme.set("system")  # Follow OS preference

# Toggle between light and dark
def toggle():
    current = theme()
    theme.set("dark" if current == "light" else "light")

# Cycle through all modes
def cycle():
    modes = ["light", "dark", "system"]
    current = theme()
    idx = modes.index(current)
    theme.set(modes[(idx + 1) % len(modes)])
```

### Theme-Aware Components

```python
from pynext.theme import use_theme
from pynext import div, Show

def ThemedCard():
    """A card that shows different content based on theme."""
    theme = use_theme()
    
    return div(class_="p-4 rounded-lg bg-card")[
        # Show different icons
        Show(when=lambda: theme() == "dark")[
            "🌙 Dark mode active"
        ],
        Show(when=lambda: theme() == "light")[
            "☀️ Light mode active"
        ],
        Show(when=lambda: theme() == "system")[
            "💻 Following system preference"
        ],
    ]
```

---

## Focus Management

### The Concept

Focus management ensures keyboard users can navigate your app:
1. **Focus Trap**: Keep focus inside modals/dialogs
2. **Focus Restoration**: Return focus when closing dialogs
3. **Roving Focus**: Arrow key navigation in menus
4. **Skip Links**: Jump to main content

### Focus Trap

When a modal opens, Tab should cycle within it, not escape to the page behind:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  WITHOUT Focus Trap:                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────┐                 │
│  │ Page Content                                           │                 │
│  │                                                        │                 │
│  │     ┌─────────────────────────────────┐               │                 │
│  │     │ Modal                           │               │                 │
│  │     │                                 │               │                 │
│  │     │  [Input 1] ◀── Focus here       │               │                 │
│  │     │  [Input 2]                      │               │                 │
│  │     │  [Submit]                       │               │                 │
│  │     │                                 │               │                 │
│  │     └─────────────────────────────────┘               │                 │
│  │                                                        │                 │
│  │  [Some Link] ◀── Tab escapes to here! BAD! 😫         │                 │
│  │  [Another Link]                                        │                 │
│  └───────────────────────────────────────────────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  WITH Focus Trap:                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│     ┌─────────────────────────────────┐                                    │
│     │ Modal (Focus Trap Active)        │                                    │
│     │                                  │                                    │
│     │  [Input 1] ◀── Tab cycles here   │                                    │
│     │       │                          │                                    │
│     │       ▼                          │                                    │
│     │  [Input 2]                       │                                    │
│     │       │                          │                                    │
│     │       ▼                          │                                    │
│     │  [Submit] ─── Tab wraps back ────┘                                    │
│     │                                  │                                    │
│     └──────────────────────────────────┘                                    │
│                                                                             │
│  Focus CANNOT escape the modal! 🎉                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Using FocusTrap

```python
from pynext.focus import FocusTrap
from pynext.shadcn import Dialog, DialogContent, Input, Button

def LoginModal():
    return Dialog()[
        DialogContent()[
            # Wrap content in FocusTrap
            FocusTrap(
                auto_focus=True,      # Focus first element when opened
                restore_focus=True,   # Return focus when closed
            )[
                h2()["Login"],
                
                Input(placeholder="Email", type="email"),
                Input(placeholder="Password", type="password"),
                
                div(class_="flex gap-2")[
                    Button(variant="outline")["Cancel"],
                    Button()["Login"],
                ],
            ]
        ]
    ]
```

### How FocusTrap Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FocusTrap Internal Logic                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. On Mount:                                                               │
│     ─────────                                                               │
│     - Find all focusable elements inside container                          │
│     - Store reference to previously focused element                         │
│     - If auto_focus=True, focus first element                               │
│                                                                             │
│  2. Tab Key Handler:                                                        │
│     ────────────────                                                        │
│     document.addEventListener('keydown', (e) => {                           │
│       if (e.key !== 'Tab') return;                                          │
│                                                                             │
│       const focusable = getFocusableElements(container);                    │
│       const first = focusable[0];                                           │
│       const last = focusable[focusable.length - 1];                         │
│                                                                             │
│       if (e.shiftKey && document.activeElement === first) {                 │
│         e.preventDefault();                                                 │
│         last.focus();  // Wrap to end                                       │
│       }                                                                     │
│                                                                             │
│       if (!e.shiftKey && document.activeElement === last) {                 │
│         e.preventDefault();                                                 │
│         first.focus();  // Wrap to start                                    │
│       }                                                                     │
│     });                                                                     │
│                                                                             │
│  3. On Unmount:                                                             │
│     ──────────                                                              │
│     - If restore_focus=True, focus previous element                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Roving Focus

For menus and lists, arrow keys should move between items:

```python
from pynext.focus import RovingFocus, RovingFocusItem
from pynext.shadcn import Button

def NavigationMenu():
    """Menu with arrow key navigation."""
    return nav()[
        RovingFocus(
            orientation="horizontal",  # ←→ keys
            loop=True,                 # Wrap at ends
        )[
            RovingFocusItem()[
                Button(variant="ghost")["Home"]
            ],
            RovingFocusItem()[
                Button(variant="ghost")["Products"]
            ],
            RovingFocusItem()[
                Button(variant="ghost")["About"]
            ],
            RovingFocusItem()[
                Button(variant="ghost")["Contact"]
            ],
        ]
    ]

def VerticalList():
    """List with up/down navigation."""
    items = ["Item 1", "Item 2", "Item 3"]
    
    return div()[
        RovingFocus(
            orientation="vertical",  # ↑↓ keys
            loop=True,
        )[
            [
                RovingFocusItem()[
                    Button(class_="w-full text-left")[item]
                ]
                for item in items
            ]
        ]
    ]
```

### Skip Links

Help keyboard users skip repetitive navigation:

```python
from pynext.focus import SkipLinks

@layout
def root_layout(children):
    return html()[
        body()[
            # Skip links (hidden until focused)
            SkipLinks(links=[
                ("main-content", "Skip to main content"),
                ("navigation", "Skip to navigation"),
            ]),
            
            nav(id="navigation")[
                # Long navigation menu...
            ],
            
            main(id="main-content")[
                children
            ],
        ]
    ]
```

---

## Storage

### The Concept

`use_storage` creates a Signal that automatically syncs with localStorage or sessionStorage:

```python
from pynext.core.client import use_storage

# This creates a signal AND persists to localStorage
theme = use_storage("theme", default="light")

# Read like a normal signal
current = theme()  # "light"

# Write like a normal signal — automatically persists!
theme.set("dark")  # Also saves to localStorage
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  use_storage Flow                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Python:                            Browser:                                │
│  ────────                           ────────                                │
│                                                                             │
│  theme = use_storage(               On page load:                           │
│    "theme",                         ─────────────                           │
│    default="light"                  1. Check localStorage.getItem("theme")  │
│  )                                  2. If found → use it                    │
│       │                             3. If not → use "light"                 │
│       │                                                                     │
│       ▼                                                                     │
│  theme.set("dark")  ──────────────▶ 1. Update signal value                  │
│                                     2. localStorage.setItem("theme","dark") │
│                                     3. Update any bound DOM                 │
│                                     4. Notify other tabs (storage event)   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Session vs Local Storage

```python
# localStorage — persists forever (until cleared)
theme = use_storage("theme", default="light", storage="local")

# sessionStorage — cleared when tab closes
temp_data = use_storage("draft", default={}, storage="session")
```

### Cross-Tab Sync

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Cross-Tab Synchronization                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Tab 1                              Tab 2                                   │
│  ─────                              ─────                                   │
│                                                                             │
│  theme.set("dark")                                                          │
│       │                                                                     │
│       ▼                                                                     │
│  localStorage.setItem(              window 'storage' event fires            │
│    "theme", "dark"                         │                                │
│  )  ───────────────────────────────────────┘                                │
│                                            │                                │
│                                            ▼                                │
│                                     storage.js detects change               │
│                                            │                                │
│                                            ▼                                │
│                                     theme signal updates                    │
│                                            │                                │
│                                            ▼                                │
│                                     UI updates to dark mode                 │
│                                                                             │
│  Both tabs now show dark mode! 🎉                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Refs

### The Concept

Refs give you access to DOM elements after they render:

```python
from pynext.core.client import use_ref
from pynext import input_

# Create a ref
search_input = use_ref("search")

# Attach to element
Input(ref=search_input, placeholder="Search...")

# Later, access the DOM element
# search_input.current is the <input> element
```

### Common Use Cases

```python
# 1. Focus an input programmatically
@on_keydown("/")
def focus_search():
    search_input.current.focus()

# 2. Scroll to element
@on_keydown("cmd+end")
def scroll_to_bottom():
    bottom_ref.current.scrollIntoView()

# 3. Read input value
def get_search_value():
    return search_input.current.value
```

---

## Client Effects

### The Concept

`@client_effect` runs code in the browser after hydration:

```python
from pynext.core.client import client_effect

@client_effect
def setup_analytics():
    """
    This code runs in the browser, not on the server.
    Use for browser-specific APIs.
    """
    # Track page view
    pass

@client_effect(dependencies=["theme"])
def apply_theme():
    """
    Re-runs when 'theme' signal changes.
    """
    pass
```

### When to Use

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Use client_effect for:                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✅ Browser-specific APIs                                                   │
│     - window.addEventListener                                               │
│     - Intersection Observer                                                 │
│     - Geolocation                                                           │
│                                                                             │
│  ✅ Third-party integrations                                                │
│     - Analytics (Google Analytics, Mixpanel)                                │
│     - Chat widgets                                                          │
│     - A/B testing                                                           │
│                                                                             │
│  ✅ DOM measurements                                                        │
│     - Get element dimensions                                                │
│     - Scroll position                                                       │
│                                                                             │
│  ❌ DON'T use for things PyNext already provides:                           │
│     - Keyboard shortcuts → use @on_keydown                                  │
│     - Dark mode → use use_theme()                                           │
│     - localStorage → use use_storage()                                      │
│     - Focus trap → use FocusTrap                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## How It All Works Together

### Complete Layout Example

```python
"""
Complete layout using all client runtime features.
"""

from pynext import html, head, body, div, nav, main
from pynext.theme import ThemeScript, ThemeProvider, ThemeToggle
from pynext.keyboard import ShortcutProvider
from pynext.focus import SkipLinks

# Import your shortcuts (registers them)
import shortcuts

@layout
def root_layout(children):
    return html(class_="h-full")[
        head()[
            title()["My App"],
            
            # 1. Theme flash prevention (MUST be first)
            ThemeScript(),
            
            link(rel="stylesheet", href="/styles.css"),
        ],
        body(class_="h-full bg-background text-foreground")[
            # 2. Skip links for accessibility
            SkipLinks(links=[
                ("main", "Skip to content"),
                ("nav", "Skip to navigation"),
            ]),
            
            # 3. Theme provider for dark mode
            ThemeProvider()[
                # 4. Shortcut provider for keyboard
                ShortcutProvider()[
                    
                    # Navigation
                    nav(id="nav", class_="border-b px-4 py-3")[
                        div(class_="flex items-center justify-between")[
                            Logo(),
                            div(class_="flex items-center gap-4")[
                                SearchTrigger(),
                                ThemeToggle(),
                            ],
                        ],
                    ],
                    
                    # Main content
                    main(id="main", class_="p-6")[
                        children
                    ],
                    
                    # Command palette (uses shortcuts + focus)
                    CommandPalette(),
                ],
            ],
        ],
    ]
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Complete Data Flow                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Server (Python)                    Browser (JavaScript)                    │
│  ────────────────                   ─────────────────────                   │
│                                                                             │
│  1. Render Phase                                                            │
│     ────────────                                                            │
│     - Execute page function                                                 │
│     - Collect shortcuts, theme config                                       │
│     - Generate HTML + hydration data                                        │
│                                                                             │
│  2. Send to Browser                                                         │
│     ────────────────                                                        │
│     HTML includes:                                                          │
│     - <script>ThemeScript</script>   ───▶  Runs immediately                │
│     - __PYNEXT_HYDRATION__ JSON      ───▶  Stored for hydration            │
│     - Runtime JS (signals.js, etc)   ───▶  Loads and parses                │
│                                                                             │
│  3. Hydration                                                               │
│     ──────────                                                              │
│                                      - keyboard.js registers shortcuts      │
│                                      - theme.js connects to signal          │
│                                      - focus.js initializes traps           │
│                                      - storage.js syncs with localStorage   │
│                                                                             │
│  4. User Interaction                                                        │
│     ────────────────                                                        │
│                                      User presses ⌘K:                       │
│                                      - keyboard.js catches event            │
│                                      - Finds matching shortcut              │
│                                      - Executes: search_open.set(True)      │
│                                      - Signal updates DOM                   │
│                                      - Command palette appears              │
│                                                                             │
│  5. Server Action (if needed)                                               │
│     ─────────────────────────                                               │
│                                      User submits form:                     │
│     @server_action           ◀────── fetch('/_pynext/action', ...)         │
│     async def save(data):                                                   │
│       await db.insert(data)  ──────▶ Response with new data                │
│                                      UI updates                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

| Module | Purpose | Key APIs |
|--------|---------|----------|
| `pynext.keyboard` | Keyboard shortcuts | `@on_keydown`, `@on_key_sequence`, `ShortcutHint` |
| `pynext.theme` | Dark mode | `ThemeScript`, `ThemeProvider`, `ThemeToggle`, `use_theme` |
| `pynext.focus` | Accessibility | `FocusTrap`, `RovingFocus`, `SkipLinks` |
| `pynext.core.client` | Primitives | `use_storage`, `use_ref`, `@client_effect` |

**Total runtime size: ~5KB** — smaller than a single React component!

---

## Next Steps

- [Keyboard Shortcuts Guide](./KEYBOARD.md) - Deep dive on shortcuts
- [Theme Guide](./THEME.md) - Complete theming system
- [Focus Guide](./FOCUS.md) - Accessibility patterns
- [Tutorial: Task Manager](../tutorials/task-manager/) - Build a complete app

