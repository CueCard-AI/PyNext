# Skeleton

A loading placeholder that mimics the shape of content while it's loading.

## Installation

```python
from pynext.shadcn import Skeleton, SkeletonCard, SkeletonTable, SkeletonText
```

## Basic Usage

```python
# Simple rectangle skeleton
Skeleton(class_="h-4 w-[250px]")

# Circle skeleton (for avatars)
Skeleton(class_="h-12 w-12", variant="circle")

# Text line skeleton
Skeleton(variant="text", class_="w-3/4")
```

## Examples

### Card Skeleton

```python
div(class_="flex items-center space-x-4")[
    Skeleton(class_="h-12 w-12 rounded-full"),  # Avatar
    div(class_="space-y-2")[
        Skeleton(class_="h-4 w-[250px]"),  # Title
        Skeleton(class_="h-4 w-[200px]"),  # Subtitle
    ]
]

# Or use the pre-built component
SkeletonCard()
```

### Table Skeleton

```python
# Loading state for a table
SkeletonTable(rows=5, show_header=True)
```

### Text Skeleton

```python
# Loading state for a paragraph
SkeletonText(lines=4)
```

## API Reference

### Skeleton

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | `str` | `None` | Additional CSS classes for sizing/shaping |
| `variant` | `"default" \| "circle" \| "text"` | `"default"` | Shape variant |

### SkeletonCard

Pre-built skeleton for card layouts with avatar, title, and description.

### SkeletonTable

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `rows` | `int` | `5` | Number of rows |
| `show_header` | `bool` | `True` | Show header row |

### SkeletonText

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `lines` | `int` | `3` | Number of text lines |

## Styling

The skeleton uses a subtle pulse animation:

```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

The `bg-muted` class provides the gray background that adapts to dark mode.

