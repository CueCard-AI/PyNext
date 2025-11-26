# Tailwind CSS Integration

> **Type-safe Tailwind classes in Python with autocomplete support**

PyNext provides a Pythonic API for working with Tailwind CSS that gives you the power of utility-first styling with the safety of Python.

---

## Why Tailwind in PyNext?

Tailwind CSS is the most popular utility-first CSS framework. But using it in Python templates traditionally means:

- No autocomplete
- No type safety
- Easy to make typos
- Hard to do conditional classes

**PyNext solves all of these** with the `tw` class builder and `cn()` utility.

---

## Quick Start

```python
from pynext.tw import tw, cn
from pynext.core.html import div, button

# Method 1: tw class builder (chainable)
div(class_=tw.flex.items_center.gap_4)[
    "Flexbox with centered items and gap"
]

# Method 2: cn() utility (conditional classes)
button(class_=cn(
    "px-4 py-2 rounded",           # Always applied
    "bg-blue-500" if primary else "bg-gray-200",  # Conditional
    {"font-bold": is_active},      # Object syntax
))[
    "Click me"
]
```

---

## The `tw` Class Builder

The `tw` object provides a chainable, type-safe way to build Tailwind classes.

### Basic Usage

```python
from pynext.tw import tw

# Chain properties with dots
tw.flex.items_center.justify_between
# → "flex items-center justify-between"

# Use underscores for hyphens
tw.bg_blue_500.text_white
# → "bg-blue-500 text-white"
```

### With Values

```python
# Padding with value
tw.p(4)           # → "p-4"
tw.px(8)          # → "px-8"

# Spacing
tw.gap(2)         # → "gap-2"
tw.space_x(4)     # → "space-x-4"

# Sizing
tw.w(64)          # → "w-64"
tw.h("full")      # → "h-full"
tw.max_w("screen_lg")  # → "max-w-screen-lg"

# Colors
tw.bg("blue", 500)     # → "bg-blue-500"
tw.text("gray", 700)   # → "text-gray-700"
```

### Responsive Modifiers

```python
# Responsive prefixes
tw.md.flex.lg.hidden
# → "md:flex lg:hidden"

tw.sm.text_sm.md.text_base.lg.text_lg
# → "sm:text-sm md:text-base lg:text-lg"
```

### State Modifiers

```python
# Hover, focus, etc.
tw.hover.bg_blue_600.focus.ring_2
# → "hover:bg-blue-600 focus:ring-2"

tw.disabled.opacity_50.disabled.cursor_not_allowed
# → "disabled:opacity-50 disabled:cursor-not-allowed"
```

### Dark Mode

```python
tw.bg_white.dark.bg_gray_900
# → "bg-white dark:bg-gray-900"

tw.text_gray_900.dark.text_gray_100
# → "text-gray-900 dark:text-gray-100"
```

### Combining Modifiers

```python
tw.md.hover.bg_blue_600
# → "md:hover:bg-blue-600"

tw.dark.hover.text_white
# → "dark:hover:text-white"
```

---

## The `cn()` Utility

The `cn()` function merges class names intelligently, handling:

- Conditional classes
- Array of classes
- Object syntax (`{class: condition}`)
- Tailwind class conflict resolution

### Basic Usage

```python
from pynext.tw import cn

# Simple merge
cn("px-4", "py-2", "rounded")
# → "px-4 py-2 rounded"

# Conditional (falsy values are filtered)
cn("base-class", None, "", False, "active-class")
# → "base-class active-class"
```

### Conditional Classes

```python
# Ternary expressions
cn(
    "btn",
    "btn-primary" if is_primary else "btn-secondary"
)

# Object syntax (dict)
cn(
    "btn",
    {
        "btn-primary": is_primary,
        "btn-disabled": is_disabled,
        "btn-loading": is_loading,
    }
)
```

### Arrays

```python
cn(
    "base",
    ["conditional-a", "conditional-b"] if condition else [],
    "always"
)
```

### Tailwind Conflict Resolution

`cn()` intelligently resolves conflicting Tailwind classes:

```python
# Later classes override earlier ones
cn("p-4", "p-8")        # → "p-8"
cn("bg-red-500", "bg-blue-500")  # → "bg-blue-500"

# This is crucial for component variants
def Button(variant="default", class_=""):
    base = "px-4 py-2 rounded font-medium"
    variants = {
        "default": "bg-blue-500 text-white",
        "outline": "border border-blue-500 text-blue-500 bg-transparent",
    }
    
    return button(class_=cn(base, variants[variant], class_))[...]
    
# User can override
Button(class_="bg-red-500")  # Their bg-red-500 wins!
```

---

## Real-World Patterns

### Component Variants

```python
from pynext.tw import tw, cn
from pynext.core.html import button

def Button(
    variant: str = "default",
    size: str = "md",
    disabled: bool = False,
    class_: str = "",
    children = None
):
    # Base styles always applied
    base = "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2"
    
    # Variant styles
    variants = {
        "default": "bg-primary text-primary-foreground hover:bg-primary/90",
        "destructive": "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        "outline": "border border-input bg-background hover:bg-accent",
        "ghost": "hover:bg-accent hover:text-accent-foreground",
    }
    
    # Size styles
    sizes = {
        "sm": "h-9 px-3 text-sm",
        "md": "h-10 px-4 py-2",
        "lg": "h-11 px-8 text-lg",
    }
    
    return button(
        class_=cn(
            base,
            variants.get(variant, variants["default"]),
            sizes.get(size, sizes["md"]),
            {"opacity-50 cursor-not-allowed": disabled},
            class_,  # User overrides come last
        ),
        disabled=disabled,
    )[children]
```

### Responsive Card Layout

```python
def CardGrid(cards):
    return div(class_=tw.grid.gap_6.sm.grid_cols_2.lg.grid_cols_3.xl.grid_cols_4)[
        [Card(card) for card in cards]
    ]

def Card(data):
    return div(class_=cn(
        tw.rounded_lg.border.bg_card.p_6,
        tw.transition_shadow.hover.shadow_lg,
    ))[
        h3(class_=tw.font_semibold.text_lg.mb_2)[data["title"]],
        p(class_=tw.text_muted_foreground.text_sm)[data["description"]],
    ]
```

### Dark Mode Toggle

```python
def ThemeAwareComponent():
    return div(class_=cn(
        # Light mode
        "bg-white text-gray-900 border-gray-200",
        # Dark mode
        "dark:bg-gray-900 dark:text-gray-100 dark:border-gray-700",
        # Shared
        "rounded-lg border p-4",
    ))[
        "This adapts to light/dark mode"
    ]
```

### Form Styling

```python
def FormField(label: str, error: str = None):
    return div(class_=tw.space_y_2)[
        Label(class_=tw.text_sm.font_medium)[label],
        Input(class_=cn(
            tw.w_full.rounded_md.border.px_3.py_2,
            tw.focus.ring_2.focus.ring_primary.focus.border_transparent,
            {"border-red-500 focus:ring-red-500": error},
        )),
        error and p(class_=tw.text_sm.text_red_500)[error],
    ]
```

---

## Setup

### 1. Install Tailwind CSS

Add Tailwind to your project's `pynext.npm.txt`:

```
tailwindcss
@tailwindcss/forms
@tailwindcss/typography
```

### 2. Create Tailwind Config

Create `tailwind.config.js` in your project root:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.py",
    "./components/**/*.py",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... ShadCN color tokens
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
}
```

### 3. Add CSS File

Create `public/styles.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    /* ... more CSS variables */
  }
  
  .dark {
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
  }
}
```

---

## Tips & Best Practices

### 1. Use `tw` for Static Classes

```python
# Good - clear, type-safe
div(class_=tw.flex.items_center.gap_4)

# Avoid for static - no benefit
div(class_=cn("flex items-center gap-4"))
```

### 2. Use `cn()` for Dynamic/Conditional

```python
# Good - clear intent
cn("base", {"active": is_active})

# Avoid - harder to read
f"base {'active' if is_active else ''}"
```

### 3. Extract Common Patterns

```python
# Create reusable style constants
CARD_STYLES = tw.rounded_lg.border.bg_card.p_6.shadow_sm
INPUT_STYLES = tw.w_full.rounded_md.border.px_3.py_2.text_sm

# Use them
div(class_=CARD_STYLES)[...]
Input(class_=INPUT_STYLES)
```

### 4. Let Users Override

```python
def MyComponent(class_: str = "", **props):
    # Always put user's class_ last
    return div(class_=cn(
        "my-default-styles",
        class_,  # User overrides win
    ))[...]
```

---

## API Reference

### `tw` Builder

| Method | Example | Result |
|--------|---------|--------|
| Property access | `tw.flex` | `"flex"` |
| Underscore → hyphen | `tw.bg_blue_500` | `"bg-blue-500"` |
| With value | `tw.p(4)` | `"p-4"` |
| With tuple | `tw.bg("blue", 500)` | `"bg-blue-500"` |
| Chaining | `tw.flex.gap_4` | `"flex gap-4"` |
| Modifiers | `tw.hover.bg_blue` | `"hover:bg-blue"` |
| Responsive | `tw.md.flex` | `"md:flex"` |

### `cn()` Function

| Input | Example | Result |
|-------|---------|--------|
| Strings | `cn("a", "b")` | `"a b"` |
| Falsy filtered | `cn("a", None, "b")` | `"a b"` |
| Dict conditions | `cn({"a": True, "b": False})` | `"a"` |
| Arrays | `cn(["a", "b"])` | `"a b"` |
| Mixed | `cn("a", {"b": True}, ["c"])` | `"a b c"` |
| Conflicts | `cn("p-2", "p-4")` | `"p-4"` |

---

## Related

- [ShadCN Components](../shadcn/README.md) - Pre-built components using these utilities
- [Getting Started with UI](./GETTING_STARTED.md) - Overview of the UI system

