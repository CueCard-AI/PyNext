# Focus Management Guide

> **Complete guide to keyboard accessibility and focus management in PyNext**

---

## Table of Contents

1. [Why Focus Matters](#why-focus-matters)
2. [Focus Trap](#focus-trap)
3. [Focus Restoration](#focus-restoration)
4. [Roving Focus](#roving-focus)
5. [Skip Links](#skip-links)
6. [Visually Hidden](#visually-hidden)
7. [Testing Focus](#testing-focus)
8. [Common Patterns](#common-patterns)

---

## Why Focus Matters

### The Keyboard Navigation Problem

Not everyone uses a mouse. People navigate with:
- **Keyboard** (Tab, Shift+Tab, arrows)
- **Screen readers** (JAWS, NVDA, VoiceOver)
- **Switch devices** (accessibility hardware)

If focus isn't managed properly:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Without Proper Focus Management                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User clicks "Edit" button                                                  │
│       │                                                                     │
│       ▼                                                                     │
│  Modal opens                                                                │
│       │                                                                     │
│       ▼                                                                     │
│  User presses Tab...                                                        │
│       │                                                                     │
│       ▼                                                                     │
│  Focus goes to element BEHIND the modal! 😫                                 │
│                                                                             │
│  User can't see where focus is.                                             │
│  User is confused and frustrated.                                           │
│  User might give up.                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  With Proper Focus Management                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User clicks "Edit" button                                                  │
│       │                                                                     │
│       ▼                                                                     │
│  Modal opens                                                                │
│  Focus moves to modal title or first input                                  │
│       │                                                                     │
│       ▼                                                                     │
│  User presses Tab...                                                        │
│       │                                                                     │
│       ▼                                                                     │
│  Focus moves to next element IN the modal                                   │
│  Tab wraps around at the end                                                │
│       │                                                                     │
│       ▼                                                                     │
│  User presses Escape                                                        │
│  Modal closes                                                               │
│  Focus returns to "Edit" button 🎉                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Focus Trap

### What Is Focus Trapping?

A focus trap keeps keyboard focus inside a container:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Focus Trap Visualization                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Page (behind modal, unfocusable)                                           │
│  ┌───────────────────────────────────────────────────────────────┐         │
│  │  [Header Link 1]  [Header Link 2]  [Logo]                     │         │
│  │                                                               │         │
│  │       ┌─────────────────────────────────────────┐            │         │
│  │       │  Modal (focus trap active)               │            │         │
│  │       │                                          │            │         │
│  │       │  ┌──────────────────────────────────┐   │            │         │
│  │       │  │ [Close Button] ◀──────────────┐  │   │            │         │
│  │       │  └──────────────────────────────────┘   │            │         │
│  │       │         │                          │    │            │         │
│  │       │         │ Tab                      │    │            │         │
│  │       │         ▼                          │    │            │         │
│  │       │  ┌──────────────────────────────────┐   │            │         │
│  │       │  │ [Input Field]                    │   │            │         │
│  │       │  └──────────────────────────────────┘   │            │         │
│  │       │         │                          │    │            │         │
│  │       │         │ Tab                      │    │            │         │
│  │       │         ▼                          │    │            │         │
│  │       │  ┌──────────────────────────────────┐   │            │         │
│  │       │  │ [Cancel]    [Submit] ───────────┼───┘            │         │
│  │       │  └──────────────────────────────────┘                │         │
│  │       │                                          │            │         │
│  │       │  Tab from Submit wraps back to Close!    │            │         │
│  │       └─────────────────────────────────────────┘            │         │
│  │                                                               │         │
│  │  [Footer Link 1]  [Footer Link 2]  (can't reach these)       │         │
│  └───────────────────────────────────────────────────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Using FocusTrap

```python
from pynext.focus import FocusTrap
from pynext import div, button, input_

def Modal(children):
    return div(class_="fixed inset-0 bg-black/50")[
        FocusTrap(
            active=True,       # Trap is on
            auto_focus=True,   # Focus first element
            restore_focus=True # Return focus on close
        )[
            div(class_="modal-content")[
                children
            ]
        ]
    ]
```

### FocusTrap Options

```python
FocusTrap(
    # Is the trap active?
    active=True,
    
    # Auto-focus first focusable element when mounted?
    auto_focus=True,
    
    # Return focus to trigger element when unmounted?
    restore_focus=True,
    
    # Initial focus selector (instead of first element)
    initial_focus="[data-focus-initial]",
    
    # Which element to return focus to (if not trigger)
    return_focus_ref=some_ref,
)[
    children
]
```

### How FocusTrap Works Internally

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FocusTrap Implementation                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Find Focusable Elements                                                 │
│     ────────────────────────                                                │
│     Query: 'a[href], button, input, select, textarea,                       │
│             [tabindex]:not([tabindex="-1"]), [contenteditable]'             │
│                                                                             │
│  2. Identify Boundaries                                                     │
│     ─────────────────────                                                   │
│     first = focusable[0]                                                    │
│     last = focusable[focusable.length - 1]                                  │
│                                                                             │
│  3. Keydown Handler                                                         │
│     ───────────────────                                                     │
│     container.addEventListener('keydown', (e) => {                          │
│       if (e.key !== 'Tab') return;                                          │
│                                                                             │
│       if (e.shiftKey && document.activeElement === first) {                 │
│         // Shift+Tab from first → go to last                                │
│         e.preventDefault();                                                 │
│         last.focus();                                                       │
│       }                                                                     │
│                                                                             │
│       if (!e.shiftKey && document.activeElement === last) {                 │
│         // Tab from last → go to first                                      │
│         e.preventDefault();                                                 │
│         first.focus();                                                      │
│       }                                                                     │
│     });                                                                     │
│                                                                             │
│  4. Cleanup on Unmount                                                      │
│     ────────────────────                                                    │
│     Remove event listener                                                   │
│     Restore focus if restore_focus=True                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Focus Restoration

### Why Restore Focus?

When a modal closes, users expect to return to where they were:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Focus Restoration Flow                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. User clicks "Edit Task"                                                 │
│     Focus is on: [Edit Task] button                                         │
│                                                                             │
│  2. Modal opens                                                             │
│     Save reference: previousFocus = [Edit Task]                             │
│     Move focus to: [Modal Title] or first input                             │
│                                                                             │
│  3. User makes edits...                                                     │
│     Focus moves around inside modal                                         │
│                                                                             │
│  4. User clicks "Save" or presses Escape                                    │
│     Modal closes                                                            │
│                                                                             │
│  5. Focus returns to: [Edit Task] button                                    │
│     ───────────────────────────────────────                                 │
│     User is exactly where they left off! 🎉                                 │
│                                                                             │
│  Without restoration:                                                       │
│  ────────────────────                                                       │
│  5. Focus goes to: <body> (or nowhere)                                      │
│     User has to Tab many times to get back 😫                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Using Focus Restoration

```python
from pynext.focus import FocusTrap, use_focus_restore

# Automatic (with FocusTrap)
FocusTrap(restore_focus=True)[...]

# Manual control
focus_state = use_focus_restore()

def open_modal():
    focus_state.save()  # Remember current focus
    show_modal()

def close_modal():
    hide_modal()
    focus_state.restore()  # Go back
```

---

## Roving Focus

### What Is Roving Focus?

For grouped elements (menus, tabs, toolbars), arrow keys should navigate:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Roving Focus Pattern                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Tab Bar:                                                                   │
│                                                                             │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐                                 │
│  │ Tab1 │   │ Tab2 │   │ Tab3 │   │ Tab4 │                                 │
│  │tabidx│   │tabidx│   │tabidx│   │tabidx│                                 │
│  │ =0   │   │ =-1  │   │ =-1  │   │ =-1  │                                 │
│  └──┬───┘   └──────┘   └──────┘   └──────┘                                 │
│     │                                                                       │
│     └── Only ONE tab is in the tab order!                                   │
│                                                                             │
│                                                                             │
│  Navigation:                                                                │
│                                                                             │
│  Tab key:       Enter group (focus Tab1)                                    │
│  → / ↓ key:     Move to Tab2 (tabindex=0 moves, Tab1 becomes -1)           │
│  → / ↓ key:     Move to Tab3                                                │
│  → / ↓ key:     Move to Tab4                                                │
│  → / ↓ key:     Wrap to Tab1 (if loop=true)                                 │
│  Tab key:       Exit group (move to next section)                           │
│                                                                             │
│                                                                             │
│  Why this pattern?                                                          │
│  ──────────────────                                                         │
│  - Tab key: Navigate between page sections                                  │
│  - Arrow keys: Navigate within a section                                    │
│  - Reduces number of Tab presses to navigate page                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Using RovingFocus

```python
from pynext.focus import RovingFocus

# Horizontal (← →)
def TabList():
    return RovingFocus(orientation="horizontal", loop=True)[
        button(role="tab")["Tab 1"],
        button(role="tab")["Tab 2"],
        button(role="tab")["Tab 3"],
    ]

# Vertical (↑ ↓)
def MenuList():
    return RovingFocus(orientation="vertical", loop=True)[
        button(role="menuitem")["Item 1"],
        button(role="menuitem")["Item 2"],
        button(role="menuitem")["Item 3"],
    ]

# Both directions
def Grid():
    return RovingFocus(orientation="both")[
        # Arrow keys work in all directions
        ...
    ]
```

### RovingFocus Options

```python
RovingFocus(
    # Direction: "horizontal", "vertical", or "both"
    orientation="horizontal",
    
    # Wrap at ends?
    loop=True,
    
    # Which child is initially focusable?
    default_index=0,
)[
    children
]
```

### How Roving Focus Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  RovingFocus Implementation                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  State:                                                                     │
│  ──────                                                                     │
│  activeIndex = 0  // Currently focusable item                               │
│                                                                             │
│  Initial Setup:                                                             │
│  ──────────────                                                             │
│  items.forEach((item, i) => {                                               │
│    item.tabIndex = i === activeIndex ? 0 : -1;                              │
│  });                                                                        │
│                                                                             │
│  Keydown Handler:                                                           │
│  ────────────────                                                           │
│  container.addEventListener('keydown', (e) => {                             │
│    let newIndex = activeIndex;                                              │
│                                                                             │
│    if (orientation === 'horizontal' || orientation === 'both') {            │
│      if (e.key === 'ArrowRight') newIndex++;                                │
│      if (e.key === 'ArrowLeft') newIndex--;                                 │
│    }                                                                        │
│    if (orientation === 'vertical' || orientation === 'both') {              │
│      if (e.key === 'ArrowDown') newIndex++;                                 │
│      if (e.key === 'ArrowUp') newIndex--;                                   │
│    }                                                                        │
│                                                                             │
│    // Handle wrapping                                                       │
│    if (loop) {                                                              │
│      newIndex = (newIndex + items.length) % items.length;                   │
│    } else {                                                                 │
│      newIndex = Math.max(0, Math.min(items.length - 1, newIndex));          │
│    }                                                                        │
│                                                                             │
│    // Update tabindex                                                       │
│    items[activeIndex].tabIndex = -1;                                        │
│    items[newIndex].tabIndex = 0;                                            │
│    items[newIndex].focus();                                                 │
│    activeIndex = newIndex;                                                  │
│  });                                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Skip Links

### What Are Skip Links?

Links that let users skip repetitive content:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Skip Links Usage                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Page Structure:                                                            │
│  ───────────────                                                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────┐               │
│  │ [Skip to main content] ◀── Hidden until focused         │               │
│  ├─────────────────────────────────────────────────────────┤               │
│  │ Header                                                   │               │
│  │   Logo  [Nav1] [Nav2] [Nav3] [Nav4] [Search] [Profile]  │               │
│  ├─────────────────────────────────────────────────────────┤               │
│  │                                                          │               │
│  │ Main Content  ◀── Skip link jumps here                  │               │
│  │                                                          │               │
│  └─────────────────────────────────────────────────────────┘               │
│                                                                             │
│  Without skip links:                                                        │
│  ───────────────────                                                        │
│  User must Tab through ALL header links to reach content.                   │
│  On every single page!                                                      │
│                                                                             │
│  With skip links:                                                           │
│  ────────────────                                                           │
│  User presses Tab once → "Skip to main" appears                             │
│  User presses Enter → Focus jumps to main content                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Using SkipLinks

```python
from pynext.focus import SkipLinks

@layout
def root_layout(children):
    return html()[
        body()[
            # Place at the very start of body
            SkipLinks(links=[
                {"href": "#main-content", "label": "Skip to main content"},
                {"href": "#navigation", "label": "Skip to navigation"},
                {"href": "#footer", "label": "Skip to footer"},
            ]),
            
            header(id="navigation")[...],
            
            main(id="main-content")[
                children
            ],
            
            footer(id="footer")[...],
        ]
    ]
```

### SkipLinks CSS

```css
/* Hidden by default */
.skip-links {
  position: absolute;
  top: -40px;
  left: 0;
  z-index: 9999;
  background: white;
  padding: 8px;
}

/* Visible when focused */
.skip-links:focus-within {
  top: 0;
}

/* Or use Tailwind's sr-only */
.sr-only:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

---

## Visually Hidden

### What Is Visually Hidden?

Content that's invisible but accessible to screen readers:

```python
from pynext.focus import VisuallyHidden

# Screen reader only hears "Close dialog"
button(class_="p-2")[
    VisuallyHidden()["Close dialog"],
    span(aria_hidden="true")["×"],  # Visual X
]
```

### When to Use

```python
# Icon buttons need labels
button()[
    VisuallyHidden()["Delete item"],
    DeleteIcon(),
]

# Form field hints
label()[
    "Email",
    VisuallyHidden()[" (required)"],
]

# Status announcements
div(role="status")[
    VisuallyHidden()["Loading complete. 5 items found."],
]
```

### CSS for VisuallyHidden

```css
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Tailwind: Use sr-only class */
```

---

## Testing Focus

### Manual Testing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Focus Testing Checklist                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Tab Through Page                                                        │
│     ────────────────                                                        │
│     - Put down your mouse                                                   │
│     - Press Tab repeatedly                                                  │
│     - Can you reach all interactive elements?                               │
│     - Is the focus order logical?                                           │
│     - Is focus visible on every element?                                    │
│                                                                             │
│  2. Modal Focus                                                             │
│     ───────────                                                             │
│     - Open a modal                                                          │
│     - Tab through it                                                        │
│     - Does focus stay inside?                                               │
│     - Close modal - does focus return?                                      │
│                                                                             │
│  3. Arrow Key Navigation                                                    │
│     ─────────────────────                                                   │
│     - Tab to a menu/tab list                                                │
│     - Do arrow keys move between items?                                     │
│     - Does Tab exit the group?                                              │
│                                                                             │
│  4. Skip Links                                                              │
│     ──────────                                                              │
│     - Refresh page                                                          │
│     - Press Tab once                                                        │
│     - Does "Skip to content" appear?                                        │
│     - Press Enter - does focus move?                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Debugging Focus

```javascript
// In browser console

// See what's focused
document.activeElement

// Log focus changes
document.addEventListener('focusin', (e) => {
  console.log('Focus:', e.target);
});

// Highlight focus
document.addEventListener('focusin', (e) => {
  document.querySelectorAll('.debug-focus').forEach(el => {
    el.classList.remove('debug-focus');
  });
  e.target.classList.add('debug-focus');
});

// Add this CSS
.debug-focus { outline: 3px solid red !important; }
```

---

## Common Patterns

### Dialog/Modal

```python
from pynext.focus import FocusTrap

@island
def Dialog(open, on_close, children):
    if not open():
        return None
    
    return div(
        class_="fixed inset-0 z-50",
        role="dialog",
        aria_modal="true",
    )[
        # Backdrop
        div(
            class_="fixed inset-0 bg-black/50",
            onclick=on_close,
        ),
        
        # Content with focus trap
        FocusTrap(
            active=True,
            auto_focus=True,
            restore_focus=True,
        )[
            div(class_="relative bg-white p-6 rounded-lg")[
                children
            ]
        ]
    ]
```

### Dropdown Menu

```python
from pynext.focus import FocusTrap, RovingFocus

@island  
def DropdownMenu(trigger, items):
    open = Signal(False)
    
    return div(class_="relative")[
        # Trigger
        button(onclick=lambda: open.set(not open()))[
            trigger
        ],
        
        # Menu
        Show(when=open)[
            FocusTrap(active=open())[
                RovingFocus(orientation="vertical", loop=True)[
                    div(class_="absolute mt-2 bg-white shadow-lg rounded")[
                        [
                            button(
                                class_="block w-full text-left px-4 py-2 hover:bg-gray-100",
                                role="menuitem",
                                onclick=lambda i=item: select_item(i),
                            )[item["label"]]
                            for item in items
                        ]
                    ]
                ]
            ]
        ]
    ]
```

### Tab Panel

```python
from pynext.focus import RovingFocus

@island
def Tabs(tabs, default=0):
    active = Signal(default)
    
    return div()[
        # Tab list with roving focus
        div(role="tablist")[
            RovingFocus(orientation="horizontal", loop=True)[
                [
                    button(
                        role="tab",
                        aria_selected="true" if active() == i else "false",
                        onclick=lambda i=i: active.set(i),
                    )[tab["label"]]
                    for i, tab in enumerate(tabs)
                ]
            ]
        ],
        
        # Tab panels
        [
            div(
                role="tabpanel",
                hidden=active() != i,
            )[tab["content"]]
            for i, tab in enumerate(tabs)
        ]
    ]
```

---

## Summary

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `FocusTrap` | Keep focus inside | Modals, dialogs, drawers |
| `RovingFocus` | Arrow key navigation | Tabs, menus, toolbars |
| `SkipLinks` | Jump past navigation | Every page layout |
| `VisuallyHidden` | Screen reader text | Icon buttons, announcements |

**Key Principles:**
1. **All interactive elements must be focusable**
2. **Focus order should be logical** (usually visual order)
3. **Focus must be visible** (outline or ring)
4. **Modals must trap focus**
5. **Focus must be restored** when dialogs close
6. **Skip links help navigation** on every page

**Testing:**
- Put down your mouse
- Tab through the entire page
- Open modals and verify trapping
- Use a screen reader (VoiceOver, NVDA)

