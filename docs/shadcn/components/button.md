# Button

> **The fundamental unit of user interaction — "click here to make something happen"**

A versatile button component with multiple variants, sizes, and states.

---

## First Principles: What IS a Button?

### The Core Concept

A button is a **promise of action**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        THE BUTTON CONTRACT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   User sees:              User clicks:           Something happens:          │
│   ──────────              ────────────           ──────────────────          │
│                                                                              │
│   ┌─────────┐                 👆                 Form submits                │
│   │  Save   │     ───────────────────────▶       Dialog opens                │
│   └─────────┘                                    Data updates                │
│                                                  Navigation occurs           │
│                                                                              │
│   The button SHOWS what will happen                                          │
│   The button DOES what it promised                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Button Variants Exist

Different actions need different visual weights:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VISUAL HIERARCHY                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PRIMARY (default)     "This is THE action to take"                        │
│   █████████████████     Save, Submit, Confirm, Create                        │
│                                                                              │
│   SECONDARY             "Alternative action, less important"                 │
│   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓     Cancel, Close, Back                                 │
│                                                                              │
│   OUTLINE               "Neutral, doesn't push you either way"              │
│   ┌───────────────┐     Edit, View, Open                                    │
│   └───────────────┘                                                         │
│                                                                              │
│   GHOST                 "Minimal, let content shine"                        │
│   (barely visible)      Icon buttons, inline actions                        │
│                                                                              │
│   DESTRUCTIVE           "DANGER! This can't be undone"                      │
│   🔴🔴🔴🔴🔴🔴🔴🔴🔴       Delete, Remove, Disconnect                          │
│                                                                              │
│   LINK                  "This goes somewhere else"                          │
│   text underlined       Navigation, external links                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add button
```

Or import directly:

```python
from pynext.shadcn import Button
```

---

## Step-by-Step Usage

### Step 1: Basic Button

```python
Button()["Click me"]
```

This renders a primary button with default styling.

### Step 2: Choose a Variant

```python
# Primary action (default)
Button()["Save"]

# Secondary action
Button(variant="secondary")["Cancel"]

# Outline style
Button(variant="outline")["Edit"]

# Minimal/ghost
Button(variant="ghost")["···"]

# Dangerous action
Button(variant="destructive")["Delete"]

# Link style
Button(variant="link")["Learn more"]
```

### Step 3: Add an Action

```python
from pynext import server_action

@server_action
async def save_data(data: dict):
    await db.save(data)
    return {"success": True}

# Submit a form
form(action=save_data)[
    Input(name="title"),
    Button(type="submit")["Save"]
]

# Or use onclick for client-side actions
Button(on_click=lambda: modal.set(True))["Open Modal"]
```

### Step 4: Add Icons

```python
from pynext.shadcn import Icons

# Icon before text
Button()[
    Icons.plus(class_="mr-2 h-4 w-4"),
    "Add Item"
]

# Icon after text
Button(variant="outline")[
    "Next",
    Icons.arrow_right(class_="ml-2 h-4 w-4")
]

# Icon only
Button(variant="ghost", size="icon")[
    Icons.settings(class_="h-4 w-4")
]
```

---

## All Variants

```python
from pynext.shadcn import Button

def AllButtons():
    return div(class_="flex flex-wrap gap-4")[
        Button()["Default"],
        Button(variant="secondary")["Secondary"],
        Button(variant="outline")["Outline"],
        Button(variant="ghost")["Ghost"],
        Button(variant="link")["Link"],
        Button(variant="destructive")["Destructive"],
    ]
```

---

## All Sizes

```python
Button(size="sm")["Small"]
Button(size="default")["Default"]
Button(size="lg")["Large"]
Button(size="icon")["🔔"]  # Square, for icons only
```

| Size | Height | Padding | Use Case |
|------|--------|---------|----------|
| `sm` | 32px | Compact | Toolbars, dense UIs |
| `default` | 40px | Normal | Most buttons |
| `lg` | 44px | Spacious | CTAs, hero sections |
| `icon` | 40×40px | Square | Icon-only buttons |

---

## Common Patterns

### Pattern 1: Loading State

```python
from pynext import Signal

is_loading = Signal(False)

Button(disabled=is_loading.value)[
    is_loading.value and Icons.loader(class_="mr-2 h-4 w-4 animate-spin"),
    "Save" if not is_loading.value else "Saving..."
]
```

### Pattern 2: Button as Link

```python
from pynext.html import a

# Navigate to another page
Button(as_child=True)[
    a(href="/dashboard")["Go to Dashboard"]
]
```

### Pattern 3: Button Group

```python
div(class_="flex rounded-md shadow-sm")[
    Button(class_="rounded-r-none")["Left"],
    Button(class_="rounded-none border-x-0")["Center"],
    Button(class_="rounded-l-none")["Right"],
]
```

### Pattern 4: Full Width

```python
Button(class_="w-full")["Sign Up"]
```

---

## API Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | str | `"default"` | Visual style |
| `size` | str | `"default"` | Button size |
| `disabled` | bool | `False` | Disable interaction |
| `type` | str | `"button"` | HTML button type |
| `as_child` | bool | `False` | Render as child element |
| `class_` | str | `""` | Additional CSS classes |

### Variants

| Value | Description |
|-------|-------------|
| `default` | Primary action, solid background |
| `secondary` | Secondary action, muted background |
| `outline` | Border only, transparent background |
| `ghost` | Minimal, transparent until hover |
| `link` | Text-only, underlined on hover |
| `destructive` | Dangerous action, red styling |

---

## Accessibility

PyNext buttons are accessible by default:

| Feature | Behavior |
|---------|----------|
| **Focus Ring** | Visible focus state for keyboard users |
| **Disabled State** | `disabled` attribute + `aria-disabled` |
| **Loading State** | Add `aria-busy="true"` when loading |
| **Icon Buttons** | Include `aria-label` for screen readers |

```python
# Icon button with screen reader text
Button(variant="ghost", size="icon", aria_label="Open settings")[
    Icons.settings(class_="h-4 w-4")
]
```

---

## Styling Tips

### Custom Colors

```python
# Override with Tailwind classes
Button(class_="bg-purple-600 hover:bg-purple-700")["Custom"]
```

### With Tailwind Utilities

```python
Button(class_="shadow-lg hover:shadow-xl transition-shadow")[
    "Elevated"
]
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Button not clickable | `disabled=True` | Check condition |
| Form not submitting | Missing `type="submit"` | Add type attribute |
| No hover effect | CSS not loading | Check Tailwind setup |
| Icon misaligned | Missing margin | Add `mr-2` or `ml-2` |

---

## Related Components

- **[Input](./input.md)** — Text inputs for forms
- **[Dialog](./dialog.md)** — Modals triggered by buttons
- **[DropdownMenu](./dropdown-menu.md)** — Menu triggered by button
