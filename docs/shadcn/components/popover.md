# Popover

> **Like a speech bubble — click something to reveal more content**

A floating panel that appears near a trigger element for additional content or actions.

---

## First Principles: What IS a Popover?

### The Core Concept

A popover is a **floating content panel** anchored to a trigger:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE POPOVER CONCEPT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CLOSED:                           OPEN:                                     │
│  ───────                           ─────                                     │
│                                                                              │
│  ┌──────────────┐                  ┌──────────────┐                         │
│  │ Click to     │                  │ Click to     │                         │
│  │ open         │                  │ open         │                         │
│  └──────────────┘                  └──────────────┘                         │
│                                          ↓                                   │
│                                    ┌──────────────────┐                     │
│                                    │ Popover Content  │                     │
│                                    │                  │                     │
│                                    │ ┌────────────┐   │                     │
│                                    │ │ Form Input │   │                     │
│                                    │ └────────────┘   │                     │
│                                    │ [Submit]         │                     │
│                                    └──────────────────┘                     │
│                                                                              │
│  Click outside → Closes                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When to Use Popover

```
USE POPOVER:                        USE DIALOG:
────────────                        ───────────
• Quick forms                       • Complex forms
• Small content                     • Important decisions
• Contextual actions                • Full-page focus needed
• Stay near trigger                 • Center of screen
```

---

## Installation

```bash
pynext ui add popover
```

Or import directly:

```python
from pynext.shadcn import Popover, PopoverTrigger, PopoverContent
```

---

## Step-by-Step Usage

### Step 1: Basic Popover

```python
Popover()[
    PopoverTrigger()[
        Button(variant="outline")["Open Popover"]
    ],
    PopoverContent()[
        p()["This is popover content"]
    ]
]
```

### Step 2: With Form

```python
Popover()[
    PopoverTrigger()[
        Button()["Set Dimensions"]
    ],
    PopoverContent(class_="w-80")[
        div(class_="space-y-4")[
            h4(class_="font-medium")["Dimensions"],
            div(class_="grid gap-2")[
                div(class_="grid grid-cols-3 items-center gap-4")[
                    Label(html_for="width")["Width"],
                    Input(id="width", default_value="100%", class_="col-span-2 h-8")
                ],
                div(class_="grid grid-cols-3 items-center gap-4")[
                    Label(html_for="height")["Height"],
                    Input(id="height", default_value="25px", class_="col-span-2 h-8")
                ]
            ]
        ]
    ]
]
```

### Step 3: Positioning

```python
# Default: bottom
Popover()[
    PopoverTrigger()[Button()["Bottom"]],
    PopoverContent()["Appears below"]
]

# Top
Popover()[
    PopoverTrigger()[Button()["Top"]],
    PopoverContent(side="top")["Appears above"]
]

# Right aligned
Popover()[
    PopoverTrigger()[Button()["Right Aligned"]],
    PopoverContent(align="end")["Aligned to right edge"]
]
```

---

## Common Patterns

### Pattern 1: Color Picker

```python
Popover()[
    PopoverTrigger()[
        Button(variant="outline", class_="w-[220px] justify-start")[
            div(class_="w-4 h-4 rounded mr-2", style=f"background:{color.value}"),
            color.value or "Pick a color"
        ]
    ],
    PopoverContent(class_="w-64")[
        div(class_="grid grid-cols-5 gap-2")[
            [
                button(
                    class_="w-8 h-8 rounded",
                    style=f"background:{c}",
                    on_click=lambda c=c: color.set(c)
                )
                for c in ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6"]
            ]
        ]
    ]
]
```

### Pattern 2: Share Menu

```python
Popover()[
    PopoverTrigger()[
        Button(variant="outline")[
            Icons.share(class_="mr-2 h-4 w-4"),
            "Share"
        ]
    ],
    PopoverContent(class_="w-72")[
        div(class_="space-y-4")[
            h4(class_="font-medium")["Share this link"],
            div(class_="flex gap-2")[
                Input(value=share_url, read_only=True),
                Button(size="icon", on_click=copy_to_clipboard)[
                    Icons.copy()
                ]
            ],
            div(class_="flex gap-2")[
                Button(variant="outline", size="icon")[Icons.twitter()],
                Button(variant="outline", size="icon")[Icons.facebook()],
                Button(variant="outline", size="icon")[Icons.linkedin()],
            ]
        ]
    ]
]
```

---

## API Reference

### Popover

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | bool | `None` | Controlled open state |
| `on_open_change` | callable | `None` | Called when state changes |

### PopoverContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `side` | str | `"bottom"` | `"top"`, `"right"`, `"bottom"`, `"left"` |
| `align` | str | `"center"` | `"start"`, `"center"`, `"end"` |
| `side_offset` | int | `4` | Distance from trigger |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Focus** | Focus moves into popover on open |
| **Escape** | Closes popover |
| **Click Outside** | Closes popover |

---

## Troubleshooting

### Popover doesn't open

**Problem:** Clicking trigger does nothing.

**Cause:** Missing JavaScript runtime or incorrect structure.

**Solution:** Ensure proper component nesting:

```python
Popover()[
    PopoverTrigger()[
        Button()["Click me"]  # Must have a clickable child
    ],
    PopoverContent()[
        "Content here"
    ]
]
```

### Popover appears in wrong position

**Problem:** Popover shows on wrong side of trigger.

**Solution:** Adjust `side` and `align` props:

```python
PopoverContent(
    side="top",      # top, right, bottom, left
    align="start",   # start, center, end
    side_offset=8    # Distance from trigger
)[...]
```

### Popover gets cut off by container

**Problem:** Popover content clipped by parent with `overflow: hidden`.

**Solution:** Popover uses a portal by default. If still clipped, check:

```python
# Ensure content uses portal
PopoverContent()[  # Portal is automatic
    "This should not be clipped"
]
```

### Click outside doesn't close popover

**Problem:** Popover stays open when clicking outside.

**Cause:** Click handler not reaching popover overlay.

**Solution:** Ensure no elements are stopping event propagation:

```python
# Wrong - stops propagation
Div(onclick="event.stopPropagation()")[
    Popover()[...]
]

# Correct - let events bubble
Div()[
    Popover()[...]
]
```

### Form inside popover submits and closes immediately

**Problem:** Submitting form in popover closes it before action completes.

**Solution:** Prevent default and handle manually:

```python
PopoverContent()[
    Form(
        on_submit=lambda e: (
            e.preventDefault(),
            handle_submit()
            # Don't close - let user see result
        )
    )[
        Input(name="value"),
        Button(type="submit")["Submit"]
    ]
]
```

### Popover arrow not visible

**Problem:** No arrow/pointer on popover.

**Solution:** Add arrow styling:

```python
PopoverContent(class_="relative")[
    # Arrow (requires custom CSS)
    Div(class_="absolute -top-2 left-1/2 -translate-x-1/2 w-0 h-0 border-l-8 border-r-8 border-b-8 border-transparent border-b-white"),
    "Content"
]
```

---

## Related Components

- **[Tooltip](./tooltip.md)** — For simple text hints
- **[Dialog](./dialog.md)** — For complex interactions
- **[DropdownMenu](./dropdown-menu.md)** — For action menus
