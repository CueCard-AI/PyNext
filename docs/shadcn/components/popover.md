# Popover

A floating panel with rich content that appears on click.

## Installation

```python
from pynext.shadcn import (
    Popover, PopoverTrigger, PopoverContent,
    PopoverAnchor, PopoverClose
)
```

## Basic Usage

```python
Popover()[
    PopoverTrigger()[
        Button(variant="outline")["Open popover"]
    ],
    PopoverContent()[
        div(class_="space-y-2")[
            h4(class_="font-medium")["Dimensions"],
            p(class_="text-sm text-muted-foreground")[
                "Set the dimensions for the layer."
            ],
        ]
    ]
]
```

## Examples

### With Form Content

```python
Popover()[
    PopoverTrigger()[
        Button()["Edit settings"]
    ],
    PopoverContent(class_="w-80")[
        div(class_="grid gap-4")[
            div(class_="space-y-2")[
                h4(class_="font-medium")["Settings"],
            ],
            div(class_="grid gap-2")[
                Label(for_="width")["Width"],
                Input(id="width", placeholder="100%"),
            ],
            div(class_="grid gap-2")[
                Label(for_="height")["Height"],
                Input(id="height", placeholder="auto"),
            ],
        ]
    ]
]
```

### With Placement

```python
# Bottom (default)
Popover()[
    PopoverTrigger()[Button()["Bottom"]],
    PopoverContent(side="bottom")["Content below"]
]

# Right
Popover()[
    PopoverTrigger()[Button()["Right"]],
    PopoverContent(side="right")["Content right"]
]
```

### With Close Button

```python
Popover()[
    PopoverTrigger()[Button()["Open"]],
    PopoverContent()[
        div(class_="flex justify-between items-center")[
            span()["Content"],
            PopoverClose()[
                Button(variant="ghost", size="sm")["×"]
            ]
        ]
    ]
]
```

### Modal Mode

```python
# Blocks interaction with outside elements
Popover(modal=True)[
    PopoverTrigger()[Button()["Open modal"]],
    PopoverContent()[
        "Click outside is disabled"
    ]
]
```

## API Reference

### Popover

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | `bool` | `None` | Controlled open state |
| `default_open` | `bool` | `False` | Initial open state |
| `modal` | `bool` | `False` | Block outside interaction |

### PopoverContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `side` | `"top" \| "bottom" \| "left" \| "right"` | `"bottom"` | Placement |
| `side_offset` | `int` | `4` | Distance from trigger (px) |
| `align` | `"start" \| "center" \| "end"` | `"center"` | Alignment |
| `trap_focus` | `bool` | `True` | Trap focus inside |
| `close_on_escape` | `bool` | `True` | Close on Escape key |
| `close_on_outside_click` | `bool` | `True` | Close on outside click |

## Accessibility

- Focus is trapped inside the popover when open
- Closes on Escape key
- Supports click outside to close
- Uses `role="dialog"` for screen readers

## Difference from Tooltip

- **Tooltip**: Shows on hover, simple text content
- **Popover**: Shows on click, rich interactive content

