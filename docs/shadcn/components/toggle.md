# Toggle

> **Like a pressed/unpressed button — click to activate, click again to deactivate**

A button that can be toggled between on and off states.

---

## First Principles: What IS a Toggle?

### The Core Concept

A toggle is a **button with memory** — it stays pressed until you click it again:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE TOGGLE CONCEPT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  REGULAR BUTTON:                   TOGGLE:                                   │
│  ───────────────                   ───────                                   │
│                                                                              │
│  Click → Action happens            Click → Turns ON (pressed)                │
│  Release → Button returns          Click again → Turns OFF                   │
│                                                                              │
│  [  Bold  ]  →  Makes text bold    [  Bold  ]  →  Bold mode ON              │
│                 immediately                       ↓                          │
│                                    [ ▣Bold▣ ]  ←  Stays pressed              │
│                                                   ↓                          │
│                                    [  Bold  ]  ←  Click to turn OFF          │
│                                                                              │
│  Use for:                                                                    │
│  • Text formatting (Bold, Italic, Underline)                                │
│  • View modes (Grid/List)                                                    │
│  • Filters (Show completed)                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Toggle vs Switch vs Checkbox

```
TOGGLE:                  SWITCH:                 CHECKBOX:
───────                  ───────                 ─────────
• Button appearance      • Slider appearance     • Box with checkmark
• In toolbars           • In settings           • In forms
• Multiple allowed      • Binary on/off         • Multiple allowed
• Visual pressed state  • Visual on/off state   • Checked state
```

---

## Installation

```bash
pynext ui add toggle
```

Or import directly:

```python
from pynext.shadcn import Toggle, ToggleGroup, ToggleGroupItem
```

---

## Step-by-Step Usage

### Step 1: Basic Toggle

```python
Toggle()[
    Icons.bold(class_="h-4 w-4")
]
```

### Step 2: With Text

```python
Toggle()[
    Icons.italic(class_="h-4 w-4 mr-2"),
    "Italic"
]
```

### Step 3: Controlled State

```python
from pynext import Signal

is_bold = Signal(False)

Toggle(
    pressed=is_bold.value,
    on_pressed_change=is_bold.set
)[
    Icons.bold(class_="h-4 w-4")
]
```

### Step 4: Toggle Group

```python
from pynext import Signal

alignment = Signal("left")

ToggleGroup(
    type="single",
    value=alignment.value,
    on_value_change=alignment.set
)[
    ToggleGroupItem(value="left")[Icons.align_left()],
    ToggleGroupItem(value="center")[Icons.align_center()],
    ToggleGroupItem(value="right")[Icons.align_right()],
]
```

---

## Common Patterns

### Pattern 1: Text Formatting Toolbar

```python
from pynext import Signal

formatting = Signal({"bold": False, "italic": False, "underline": False})

div(class_="flex border rounded-lg p-1 gap-1")[
    Toggle(
        pressed=formatting.value["bold"],
        on_pressed_change=lambda v: formatting.set({**formatting.value, "bold": v})
    )[Icons.bold(class_="h-4 w-4")],
    
    Toggle(
        pressed=formatting.value["italic"],
        on_pressed_change=lambda v: formatting.set({**formatting.value, "italic": v})
    )[Icons.italic(class_="h-4 w-4")],
    
    Toggle(
        pressed=formatting.value["underline"],
        on_pressed_change=lambda v: formatting.set({**formatting.value, "underline": v})
    )[Icons.underline(class_="h-4 w-4")],
]
```

### Pattern 2: View Mode Toggle

```python
view_mode = Signal("grid")

ToggleGroup(type="single", value=view_mode.value, on_value_change=view_mode.set)[
    ToggleGroupItem(value="grid", aria_label="Grid view")[
        Icons.grid(class_="h-4 w-4")
    ],
    ToggleGroupItem(value="list", aria_label="List view")[
        Icons.list(class_="h-4 w-4")
    ],
]
```

### Pattern 3: Filter Toggle

```python
show_completed = Signal(False)

Toggle(
    variant="outline",
    pressed=show_completed.value,
    on_pressed_change=show_completed.set
)[
    Icons.check(class_="h-4 w-4 mr-2"),
    "Show Completed"
]
```

### Pattern 4: Multi-Select Toggle Group

```python
selected_tags = Signal([])

ToggleGroup(
    type="multiple",
    value=selected_tags.value,
    on_value_change=selected_tags.set
)[
    ToggleGroupItem(value="bug")["Bug"],
    ToggleGroupItem(value="feature")["Feature"],
    ToggleGroupItem(value="docs")["Docs"],
]
```

---

## Variants

### Default

```python
Toggle()[Icons.bold()]  # Subtle background when pressed
```

### Outline

```python
Toggle(variant="outline")[Icons.bold()]  # Border, no background
```

### Sizes

```python
Toggle(size="sm")[Icons.bold(class_="h-3 w-3")]
Toggle(size="default")[Icons.bold(class_="h-4 w-4")]
Toggle(size="lg")[Icons.bold(class_="h-5 w-5")]
```

---

## API Reference

### Toggle

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `pressed` | bool | `False` | Controlled pressed state |
| `default_pressed` | bool | `False` | Initial pressed state |
| `on_pressed_change` | callable | `None` | Called when state changes |
| `disabled` | bool | `False` | Disable toggle |
| `variant` | str | `"default"` | Visual style |
| `size` | str | `"default"` | Size variant |

### ToggleGroup

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | str | `"single"` | `"single"` or `"multiple"` |
| `value` | str/list | `None` | Selected value(s) |
| `on_value_change` | callable | `None` | Called when selection changes |
| `disabled` | bool | `False` | Disable all items |

### ToggleGroupItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Item's value |
| `disabled` | bool | `False` | Disable this item |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Role** | `role="button"` with `aria-pressed` |
| **Keyboard** | Space/Enter to toggle |
| **Group** | `role="group"` with `aria-label` |
| **Label** | Use `aria-label` for icon-only toggles |

```python
# Accessible icon toggle
Toggle(aria_label="Bold")[
    Icons.bold(class_="h-4 w-4")
]
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| State not updating | Missing controlled props | Add `pressed` and `on_pressed_change` |
| Multiple items in single group | Wrong type | Use `type="single"` |
| Can't deselect in group | Expected for single | Use toggle (not group) if deselect needed |

---

## Related Components

- **[Button](./button.md)** — For one-time actions
- **[Switch](./switch.md)** — For settings on/off
- **[Checkbox](./checkbox.md)** — For form selections
