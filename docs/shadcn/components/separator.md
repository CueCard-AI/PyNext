# Separator

Visual divider between content sections.

## When to Use

Separators are for:
- **Dividing sections** - Between groups of content
- **Menu dividers** - Between menu item groups
- **Card sections** - Between header, content, footer
- **List breaks** - Between categories

## Installation

```bash
pynext ui add separator
```

Or use directly:

```python
from pynext.shadcn import Separator
```

## Basic Usage

```python
Separator()  # Horizontal line
```

## Orientation

```python
# Horizontal (default)
Separator()

# Vertical
Separator(orientation="vertical", class_="h-4")
```

## Examples

### Between Content

```python
div()[
    h2()["Section One"],
    p()["Content for section one..."],
    Separator(class_="my-4"),
    h2()["Section Two"],
    p()["Content for section two..."]
]
```

### In Navigation

```python
nav(class_="flex items-center gap-2")[
    a(href="/")["Home"],
    Separator(orientation="vertical", class_="h-4"),
    a(href="/products")["Products"],
    Separator(orientation="vertical", class_="h-4"),
    a(href="/about")["About"]
]
```

### Decorative

```python
# Separator is decorative by default (aria-hidden)
# For semantic breaks, use decorative=False
Separator(decorative=False)
```

## Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `orientation` | str | `"horizontal"` | "horizontal" or "vertical" |
| `decorative` | bool | `True` | If true, adds aria-hidden |
| `class_` | str | `""` | Additional CSS classes |

## Styling

```python
# Thicker
Separator(class_="h-[2px]")

# Different color
Separator(class_="bg-primary")

# With margin
Separator(class_="my-8")
```

## Related Components

- [Card](./card.md) - Often uses separators
- [DropdownMenu](./dropdown-menu.md) - Menu separators

