# Keyboard Shortcuts Guide

> **Complete guide to keyboard shortcuts in PyNext**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding Keyboard Events](#understanding-keyboard-events)
3. [Single-Key Shortcuts](#single-key-shortcuts)
4. [Key Sequences](#key-sequences)
5. [Context System](#context-system)
6. [Platform Detection](#platform-detection)
7. [Displaying Shortcuts](#displaying-shortcuts)
8. [Advanced Patterns](#advanced-patterns)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

```python
from pynext.keyboard import on_keydown, on_key_sequence
from pynext import Signal

search_open = Signal(False)

@on_keydown("cmd+k")
def open_search():
    search_open.set(True)

@on_key_sequence("g d")
def go_dashboard():
    from pynext import navigate
    navigate("/")
```

That's it! No JavaScript required.

---

## Understanding Keyboard Events

### First Principles: How Keyboards Work in Browsers

When you press a key, the browser fires events:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Key Press Lifecycle                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Physical Action              Browser Events              Your Code         │
│  ───────────────              ──────────────              ─────────         │
│                                                                             │
│  Press key down      ───▶     keydown event       ───▶    @on_keydown      │
│       │                            │                                        │
│       │                            ▼                                        │
│       │                       (key repeats if held)                         │
│       │                                                                     │
│       ▼                                                                     │
│  Release key         ───▶     keyup event         ───▶    (not used)       │
│                                                                             │
│  Why keydown?                                                               │
│  ────────────                                                               │
│  - Fires immediately when pressed                                           │
│  - Can prevent default (stop browser action)                                │
│  - Repeats if held (good for navigation)                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The KeyboardEvent Object

When a key is pressed, the browser creates an event object:

```javascript
// When user presses ⌘K on Mac:
{
  key: "k",           // The key pressed
  code: "KeyK",       // Physical key location
  metaKey: true,      // ⌘ (Command) is held
  ctrlKey: false,     // Ctrl is NOT held
  altKey: false,      // Alt/Option is NOT held
  shiftKey: false,    // Shift is NOT held
  repeat: false,      // First press, not repeat
  target: <input>     // Element that has focus
}
```

PyNext abstracts this away — you just write `"cmd+k"`.

---

## Single-Key Shortcuts

### Basic Syntax

```python
@on_keydown("key_combo")
def handler():
    pass
```

### Key Combo Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Key Combo Syntax                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Format: "modifier+modifier+key"                                            │
│                                                                             │
│  Modifiers (optional, can combine):                                         │
│  ──────────────────────────────────                                         │
│  cmd    → Command (Mac) / Ctrl (Windows)                                    │
│  ctrl   → Control key (both platforms)                                      │
│  alt    → Option (Mac) / Alt (Windows)                                      │
│  shift  → Shift key                                                         │
│                                                                             │
│  Keys:                                                                      │
│  ─────                                                                      │
│  a-z      → Letter keys (lowercase)                                         │
│  0-9      → Number keys                                                     │
│  escape   → Escape key                                                      │
│  enter    → Enter/Return key                                                │
│  space    → Space bar                                                       │
│  tab      → Tab key                                                         │
│  backspace→ Backspace/Delete                                                │
│  /        → Forward slash                                                   │
│  ?        → Question mark (shift+/)                                         │
│  [        → Left bracket                                                    │
│  ]        → Right bracket                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Examples

```python
# Single keys (no modifier)
@on_keydown("n")
def new_item(): pass

@on_keydown("escape")
def close_dialog(): pass

@on_keydown("/")
def open_search(): pass

@on_keydown("?")
def show_help(): pass

# With cmd/ctrl
@on_keydown("cmd+k")        # ⌘K / Ctrl+K
def command_palette(): pass

@on_keydown("cmd+s")        # ⌘S / Ctrl+S
def save(): pass

@on_keydown("cmd+z")        # ⌘Z / Ctrl+Z
def undo(): pass

# With other modifiers
@on_keydown("ctrl+shift+p")  # Ctrl+Shift+P
def command_palette_vscode(): pass

@on_keydown("alt+n")        # ⌥N / Alt+N
def new_window(): pass

# Multiple modifiers
@on_keydown("cmd+shift+s")  # ⌘⇧S / Ctrl+Shift+S
def save_as(): pass

@on_keydown("cmd+alt+i")    # ⌘⌥I / Ctrl+Alt+I
def dev_tools(): pass
```

### What Each Decorator Does

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  @on_keydown("cmd+k") Breakdown                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: Parse                                                              │
│  ─────────────                                                              │
│  "cmd+k" → { key: "k", modifiers: ["meta"] }                                │
│                                                                             │
│  Step 2: Create Shortcut Record                                             │
│  ─────────────────────────────────                                          │
│  {                                                                          │
│    id: "shortcut_a1b2c3d4",                                                 │
│    key: "k",                                                                │
│    modifiers: ["meta"],                                                     │
│    handlerId: "handler_e5f6g7h8",                                           │
│    context: "global",                                                       │
│    preventDefault: true                                                     │
│  }                                                                          │
│                                                                             │
│  Step 3: Register Handler                                                   │
│  ────────────────────────                                                   │
│  Python function stored with handlerId                                      │
│                                                                             │
│  Step 4: Hydrate (when page loads)                                          │
│  ─────────────────────────────────                                          │
│  Shortcut config injected into page as JSON                                 │
│  keyboard.js parses and registers listener                                  │
│                                                                             │
│  Step 5: Match (when key pressed)                                           │
│  ──────────────────────────────────                                         │
│  Event: { key: "k", metaKey: true, ctrlKey: false, ... }                    │
│  Check: key matches? ✓  meta matches? ✓  context ok? ✓                      │
│  Result: Execute handler!                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Sequences

### What Are Key Sequences?

Instead of pressing keys simultaneously (⌘K), sequences require pressing keys one after another (G then D):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Simultaneous vs Sequential                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Simultaneous (cmd+k):                                                      │
│  ─────────────────────                                                      │
│                                                                             │
│  Time: ├───────────────────────────────────────────────────▶               │
│                                                                             │
│  ⌘ key: ██████████████████████████████████████                              │
│  K key:     ████████████████                                                │
│                  │                                                          │
│                  └── Both pressed at same time = fires!                     │
│                                                                             │
│                                                                             │
│  Sequential (g d):                                                          │
│  ─────────────────                                                          │
│                                                                             │
│  Time: ├───────────────────────────────────────────────────▶               │
│                                                                             │
│  G key: ████                                                                │
│  D key:              ████                                                   │
│              │        │                                                     │
│              │        └── D pressed within timeout = fires!                 │
│              │                                                              │
│              └── G pressed first, starts timer                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Basic Usage

```python
@on_key_sequence("g d")
def go_dashboard():
    navigate("/")

@on_key_sequence("g b")
def go_board():
    navigate("/board")

@on_key_sequence("g s")
def go_settings():
    navigate("/settings")
```

### How the Buffer Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Sequence Buffer State Machine                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  State: IDLE                                                                │
│  Buffer: []                                                                 │
│       │                                                                     │
│       │ User presses "g"                                                    │
│       ▼                                                                     │
│  State: BUFFERING                                                           │
│  Buffer: ["g"]                                                              │
│  Timer: 1000ms countdown started                                            │
│       │                                                                     │
│       ├──────────────────────────────────────────────┐                     │
│       │                                              │                     │
│       │ User presses "d"                             │ Timer expires       │
│       │ (within 1000ms)                              │ (no "d" pressed)    │
│       ▼                                              ▼                     │
│  State: MATCHED!                                State: TIMEOUT             │
│  Buffer: ["g", "d"]                             Buffer: []                 │
│  Action: Execute go_dashboard()                 Action: Reset to IDLE     │
│  Then: Reset to IDLE                                                       │
│                                                                             │
│                                                                             │
│  What if user presses wrong key?                                            │
│  ────────────────────────────────                                           │
│  Buffer: ["g"]                                                              │
│       │                                                                     │
│       │ User presses "x" (not "d")                                          │
│       ▼                                                                     │
│  No sequence starts with "g x"                                              │
│  Buffer: [] (reset)                                                         │
│  State: IDLE                                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Custom Timeout

```python
# Default: 1000ms (1 second)
@on_key_sequence("g d")
def normal_sequence(): pass

# Shorter timeout: 500ms
@on_key_sequence("t d", timeout=500)
def quick_sequence(): pass

# Longer timeout: 2000ms
@on_key_sequence("x y z", timeout=2000)
def three_key_sequence(): pass
```

### Three+ Key Sequences

```python
@on_key_sequence("g p r")  # g → p → r
def go_to_pr():
    navigate("/pulls")

# User must press all three within timeout
# Timer resets after each key
```

---

## Context System

### Why Contexts?

Not all shortcuts should fire everywhere:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  The Problem                                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Without context:                                                           │
│                                                                             │
│  @on_keydown("n")                                                           │
│  def new_task(): ...                                                        │
│                                                                             │
│  User is typing in search: "planning" ← Contains 'n'!                       │
│                                                                             │
│  Every time they type 'n', new task dialog opens! 😫                        │
│                                                                             │
│                                                                             │
│  With context:                                                              │
│                                                                             │
│  @on_keydown("n", context="global")                                         │
│  def new_task(): ...                                                        │
│                                                                             │
│  User is typing in search: "planning"                                       │
│                                                                             │
│  Shortcut detects input field, doesn't fire. 🎉                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Available Contexts

```python
# "global" (default)
# Fires everywhere EXCEPT input fields
@on_keydown("n", context="global")
def new_item():
    """
    Will NOT fire when user is:
    - Typing in <input>
    - Typing in <textarea>
    - Typing in <select>
    - Typing in contenteditable
    
    WILL fire when user is:
    - On the page body
    - Focused on a button
    - Focused on a link
    """
    pass


# "dialog"
# Only fires when a dialog/modal is open
@on_keydown("escape", context="dialog")
def close_dialog():
    """
    Only fires when:
    - Inside element with [role="dialog"]
    - Inside element with [data-pynext-dialog]
    - Inside element with [data-state="open"]
    
    Perfect for Escape key in modals!
    """
    pass


# "always"
# Fires everywhere, including in inputs
@on_keydown("cmd+enter", context="always")
def submit():
    """
    Fires even when typing in textarea.
    
    Use sparingly! Only for shortcuts that
    make sense inside text fields.
    
    Good: cmd+enter to submit
    Bad: 'n' to create new item
    """
    pass


# "input"
# Only fires INSIDE input fields
@on_keydown("cmd+b", context="input")
def bold():
    """
    Only fires when user is in input/textarea.
    
    Good for text formatting shortcuts.
    """
    pass
```

### Context Detection Logic

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  How Context Is Checked                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  When keydown fires:                                                        │
│                                                                             │
│  1. Get event.target (focused element)                                      │
│                                                                             │
│  2. Check if target is input:                                               │
│     isInput = target.matches('input, textarea, select, [contenteditable]')  │
│                                                                             │
│  3. Check if in dialog:                                                     │
│     isInDialog = target.closest('[role="dialog"], [data-pynext-dialog]')    │
│                                                                             │
│  4. Apply context rules:                                                    │
│                                                                             │
│     ┌──────────────┬───────────────────────────────────────────────────┐   │
│     │ Context      │ Logic                                              │   │
│     ├──────────────┼───────────────────────────────────────────────────┤   │
│     │ "global"     │ Fire if NOT isInput (unless special key)          │   │
│     │ "dialog"     │ Fire if isInDialog                                │   │
│     │ "always"     │ Always fire                                       │   │
│     │ "input"      │ Fire if isInput                                   │   │
│     └──────────────┴───────────────────────────────────────────────────┘   │
│                                                                             │
│  Special keys (escape, enter, tab) fire in "global" even in some inputs    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Platform Detection

### The Problem

Mac uses ⌘ (Command), Windows uses Ctrl:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Platform Keyboard Differences                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Action          Mac             Windows/Linux                              │
│  ──────          ───             ─────────────                              │
│  Copy            ⌘C              Ctrl+C                                     │
│  Paste           ⌘V              Ctrl+V                                     │
│  Save            ⌘S              Ctrl+S                                     │
│  Undo            ⌘Z              Ctrl+Z                                     │
│  Find            ⌘F              Ctrl+F                                     │
│                                                                             │
│  Users expect platform-native shortcuts!                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PyNext's Solution

Use `cmd` and it works on both:

```python
@on_keydown("cmd+k")  # ⌘K on Mac, Ctrl+K on Windows
def open_search(): pass
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Platform Detection Flow                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. keyboard.js detects platform on load:                                   │
│     const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform)           │
│                                                                             │
│  2. When checking "cmd" modifier:                                           │
│                                                                             │
│     if (isMac) {                                                            │
│       // Check event.metaKey (⌘)                                            │
│       return event.metaKey === needsMeta;                                   │
│     } else {                                                                │
│       // Check event.ctrlKey                                                │
│       return event.ctrlKey === needsMeta;                                   │
│     }                                                                       │
│                                                                             │
│  3. Result:                                                                 │
│                                                                             │
│     Mac user presses ⌘K:     event.metaKey = true  → Match!                │
│     Windows user presses Ctrl+K: event.ctrlKey = true → Match!             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When to Use `cmd` vs `ctrl`

```python
# Use "cmd" for common shortcuts (recommended)
# These feel native on both platforms
@on_keydown("cmd+k")    # Command palette
@on_keydown("cmd+s")    # Save
@on_keydown("cmd+z")    # Undo

# Use "ctrl" only when you specifically need Control key
# (rarely needed in web apps)
@on_keydown("ctrl+c")   # Force Ctrl on all platforms
```

---

## Displaying Shortcuts

### ShortcutHint Component

```python
from pynext.keyboard import ShortcutHint

# In a button
Button()[
    "Save",
    ShortcutHint("cmd+s", class_="ml-2"),
]

# Displays: "Save ⌘S" on Mac, "Save Ctrl+S" on Windows
```

### How ShortcutHint Renders

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ShortcutHint Rendering                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Input: ShortcutHint("cmd+shift+k")                                         │
│                                                                             │
│  On Mac:                                                                    │
│  ────────                                                                   │
│  <kbd class="...">                                                          │
│    <span>⌘</span>                                                           │
│    <span>⇧</span>                                                           │
│    <span>K</span>                                                           │
│  </kbd>                                                                     │
│                                                                             │
│  Renders as: ⌘⇧K                                                            │
│                                                                             │
│                                                                             │
│  On Windows:                                                                │
│  ────────────                                                               │
│  <kbd class="...">                                                          │
│    <span>Ctrl</span>                                                        │
│    <span>+</span>                                                           │
│    <span>Shift</span>                                                       │
│    <span>+</span>                                                           │
│    <span>K</span>                                                           │
│  </kbd>                                                                     │
│                                                                             │
│  Renders as: Ctrl+Shift+K                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ShortcutsHelpDialog

```python
from pynext.keyboard import ShortcutsHelpDialog
from pynext.shadcn import Button

# Add to your layout
ShortcutsHelpDialog(
    trigger=Button(variant="ghost")["?"],
)
```

This automatically shows all registered shortcuts!

---

## Advanced Patterns

### Prevent Default Browser Behavior

By default, PyNext prevents the browser's default action:

```python
@on_keydown("cmd+s")  # Prevents browser "Save Page" dialog
def save():
    save_document()

# To allow default behavior:
@on_keydown("cmd+s", prevent_default=False)
def save_with_default():
    # Browser's "Save Page" will also show
    save_document()
```

### Programmatic Registration

```python
from pynext.keyboard import register_shortcut, unregister_shortcut

# Register at runtime
shortcut_id = register_shortcut(
    "cmd+shift+n",
    handler=create_project,
    context="global",
)

# Later, remove it
unregister_shortcut(shortcut_id)
```

### Conditional Shortcuts

```python
from pynext import Signal

editing_mode = Signal(False)

@on_keydown("e", context="global")
def toggle_edit():
    editing_mode.set(not editing_mode())

# These only make sense in edit mode
@on_keydown("cmd+b", context="always")
def bold():
    if editing_mode():
        apply_bold()

@on_keydown("cmd+i", context="always")
def italic():
    if editing_mode():
        apply_italic()
```

---

## Troubleshooting

### Shortcut Not Firing?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Debugging Checklist                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Is ShortcutProvider in layout?                                          │
│     ─────────────────────────────                                           │
│     @layout                                                                 │
│     def root_layout(children):                                              │
│       return ShortcutProvider()[children]  # ← Need this!                   │
│                                                                             │
│  2. Is focus in an input field?                                             │
│     ──────────────────────────                                              │
│     context="global" doesn't fire in inputs.                                │
│     Try context="always" if that's intended.                                │
│                                                                             │
│  3. Is another shortcut conflicting?                                        │
│     ────────────────────────────────                                        │
│     Browser shortcuts take precedence.                                      │
│     Can't override Cmd+W, Cmd+Q, etc.                                       │
│                                                                             │
│  4. Check the console                                                       │
│     ──────────────────                                                      │
│     window.__PYNEXT_DEBUG__ = true                                          │
│     Then press keys to see debug output.                                    │
│                                                                             │
│  5. Is the import working?                                                  │
│     ──────────────────────                                                  │
│     Make sure shortcuts.py is imported somewhere!                           │
│     Just defining @on_keydown isn't enough.                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Common Mistakes

```python
# ❌ Wrong: Uppercase key
@on_keydown("cmd+K")  # Should be lowercase
def bad(): pass

# ✅ Correct: Lowercase key
@on_keydown("cmd+k")
def good(): pass


# ❌ Wrong: Space in key combo
@on_keydown("cmd + k")  # No spaces!
def bad(): pass

# ✅ Correct: No spaces
@on_keydown("cmd+k")
def good(): pass


# ❌ Wrong: Using 'command' instead of 'cmd'
@on_keydown("command+k")
def bad(): pass

# ✅ Correct: Use 'cmd'
@on_keydown("cmd+k")
def good(): pass
```

---

## Summary

| Feature | Syntax | Example |
|---------|--------|---------|
| Single shortcut | `@on_keydown("combo")` | `@on_keydown("cmd+k")` |
| Key sequence | `@on_key_sequence("keys")` | `@on_key_sequence("g d")` |
| With context | `context="..."` | `context="dialog"` |
| Custom timeout | `timeout=ms` | `timeout=500` |
| Display hint | `ShortcutHint("combo")` | `ShortcutHint("cmd+k")` |
| Help dialog | `ShortcutsHelpDialog()` | Shows all shortcuts |

**Remember:**
- Use `cmd` for cross-platform ⌘/Ctrl
- Use `context="global"` to skip input fields
- Import your shortcuts file so decorators run!

