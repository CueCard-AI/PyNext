# Badge

Small status indicator for labeling items.

## When to Use

Badges are for:
- **Status indicators** - Active, Pending, Closed
- **Counts** - Notifications, unread messages
- **Categories** - Tags, labels
- **New/Updated** - Feature highlights

## Installation

```bash
pynext ui add badge
```

Or use directly:

```python
from pynext.shadcn import Badge
```

## Basic Usage

```python
Badge()["Badge"]
```

## Variants

```python
Badge(variant="default")["Default"]
Badge(variant="secondary")["Secondary"]
Badge(variant="destructive")["Destructive"]
Badge(variant="outline")["Outline"]
```

| Variant | Use Case |
|---------|----------|
| `default` | Primary status, active states |
| `secondary` | Neutral information |
| `destructive` | Errors, warnings |
| `outline` | Subtle, less emphasis |

## Examples

### Status Badges

```python
Badge(variant="default")["Active"]
Badge(variant="secondary")["Pending"]
Badge(variant="destructive")["Rejected"]
Badge(class_="bg-green-500")["Approved"]
```

### With Icons

```python
Badge()[
    span(class_="mr-1")["✓"],
    "Verified"
]
```

### Notification Count

```python
Button(class_="relative")[
    "Inbox",
    Badge(class_="absolute -top-2 -right-2 h-5 w-5 p-0 justify-center")[
        "3"
    ]
]
```

### In Cards/Lists

```python
div(class_="flex items-center justify-between")[
    span()["Premium Plan"],
    Badge(variant="secondary")["Current"]
]
```

## Custom Colors

```python
Badge(class_="bg-blue-500 hover:bg-blue-600")["Info"]
Badge(class_="bg-yellow-500 text-yellow-950")["Warning"]
Badge(class_="bg-green-500")["Success"]
Badge(class_="bg-purple-500")["Premium"]
```

## Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | str | `"default"` | Visual style |
| `class_` | str | `""` | Additional CSS classes |

## Related Components

- [Button](./button.md) - For actions
- [Card](./card.md) - Often contains badges

