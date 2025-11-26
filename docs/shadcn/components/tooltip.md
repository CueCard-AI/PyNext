# Tooltip

A popup that displays information when hovering over or focusing on an element.

## Installation

```python
from pynext.shadcn import Tooltip, TooltipTrigger, TooltipContent, TooltipProvider
```

## Basic Usage

```python
Tooltip()[
    TooltipTrigger()[
        Button(variant="outline")["Hover me"]
    ],
    TooltipContent()["This is the tooltip content"]
]
```

## Examples

### With Placement

```python
# Top (default)
Tooltip()[
    TooltipTrigger()[Button()["Top"]],
    TooltipContent(side="top")["Appears above"]
]

# Bottom
Tooltip()[
    TooltipTrigger()[Button()["Bottom"]],
    TooltipContent(side="bottom")["Appears below"]
]

# Left
Tooltip()[
    TooltipTrigger()[Button()["Left"]],
    TooltipContent(side="left")["Appears left"]
]

# Right
Tooltip()[
    TooltipTrigger()[Button()["Right"]],
    TooltipContent(side="right")["Appears right"]
]
```

### With Custom Delay

```python
Tooltip(delay=1000)[  # 1 second delay
    TooltipTrigger()[Button()["Slow tooltip"]],
    TooltipContent()["I take a second to appear"]
]
```

### With Alignment

```python
Tooltip()[
    TooltipTrigger()[Button()["Start aligned"]],
    TooltipContent(side="bottom", align="start")[
        "Aligned to the start"
    ]
]
```

### With Arrow

```python
Tooltip()[
    TooltipTrigger()[Button()["With arrow"]],
    TooltipContent(arrow=True)["Points to trigger"]
]
```

## API Reference

### Tooltip

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `delay` | `int` | `700` | Delay before showing (ms) |
| `open` | `bool` | `None` | Controlled open state |
| `default_open` | `bool` | `False` | Initial open state |

### TooltipTrigger

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `as_child` | `bool` | `True` | Merge props onto child element |

### TooltipContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `side` | `"top" \| "bottom" \| "left" \| "right"` | `"top"` | Placement |
| `side_offset` | `int` | `4` | Distance from trigger (px) |
| `align` | `"start" \| "center" \| "end"` | `"center"` | Alignment |
| `arrow` | `bool` | `False` | Show pointing arrow |

## Accessibility

- Tooltip appears on both hover and focus for keyboard users
- Closes on Escape key press
- Uses appropriate ARIA roles

## Styling

The tooltip uses the following CSS classes by default:

- `bg-popover` - Background color
- `text-popover-foreground` - Text color
- `animate-in fade-in-0 zoom-in-95` - Enter animation
- `animate-out fade-out-0 zoom-out-95` - Exit animation

