# Tooltip

> **Like a helpful whisper — hover over something to learn what it does**

A small popup that appears on hover or focus to provide additional context.

---

## First Principles: What IS a Tooltip?

### The Core Concept

A tooltip is a **contextual hint** that appears on demand:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE TOOLTIP CONCEPT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WITHOUT TOOLTIP:                  WITH TOOLTIP:                             │
│  ────────────────                  ──────────────                            │
│                                                                              │
│  ┌───┐                             ┌───┐                                    │
│  │ ? │  What does this mean?       │ ? │                                    │
│  └───┘                             └───┘                                    │
│                                      ↑                                       │
│                                    ┌───────────────┐                        │
│                                    │ Click for help│ ← Tooltip              │
│                                    └───────────────┘                        │
│                                                                              │
│  User hovers/focuses → Tooltip appears → User understands                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tooltip vs Popover vs Dialog

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHOOSING THE RIGHT COMPONENT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TOOLTIP:           POPOVER:              DIALOG:                            │
│  ────────           ────────              ───────                            │
│  • Text only        • Rich content        • Complex content                  │
│  • On hover/focus   • On click            • On action                        │
│  • Informational    • Interactive         • Requires decision                │
│  • Brief delay      • Stays until close   • Blocks interaction               │
│                                                                              │
│  "What is this?"    "Show me more"        "Confirm this action"              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add tooltip
```

Or import directly:

```python
from pynext.shadcn import Tooltip, TooltipTrigger, TooltipContent, TooltipProvider
```

---

## Step-by-Step Usage

### Step 1: Basic Tooltip

```python
TooltipProvider()[
    Tooltip()[
        TooltipTrigger()[
            Button(variant="outline")["Hover me"]
        ],
        TooltipContent()[
            p()["This is a tooltip"]
        ]
    ]
]
```

### Step 2: On Icon Buttons

```python
TooltipProvider()[
    Tooltip()[
        TooltipTrigger()[
            Button(variant="ghost", size="icon")[
                Icons.settings(class_="h-4 w-4")
            ]
        ],
        TooltipContent()["Settings"]
    ]
]
```

### Step 3: Custom Positioning

```python
# Position options: top, right, bottom, left
Tooltip()[
    TooltipTrigger()[Button()["Top"]],
    TooltipContent(side="top")["Appears above"]
]

Tooltip()[
    TooltipTrigger()[Button()["Right"]],
    TooltipContent(side="right")["Appears right"]
]
```

---

## Common Patterns

### Pattern 1: Icon Button Toolbar

```python
TooltipProvider()[
    div(class_="flex gap-1")[
        Tooltip()[
            TooltipTrigger()[
                Button(variant="ghost", size="icon")[Icons.bold()]
            ],
            TooltipContent()["Bold (⌘B)"]
        ],
        Tooltip()[
            TooltipTrigger()[
                Button(variant="ghost", size="icon")[Icons.italic()]
            ],
            TooltipContent()["Italic (⌘I)"]
        ],
        Tooltip()[
            TooltipTrigger()[
                Button(variant="ghost", size="icon")[Icons.underline()]
            ],
            TooltipContent()["Underline (⌘U)"]
        ],
    ]
]
```

### Pattern 2: Truncated Text

```python
Tooltip()[
    TooltipTrigger()[
        p(class_="max-w-[200px] truncate")[
            "This is a very long text that gets truncated..."
        ]
    ],
    TooltipContent()[
        p(class_="max-w-[300px]")[
            "This is a very long text that gets truncated but you can read it all in the tooltip"
        ]
    ]
]
```

---

## API Reference

### TooltipProvider

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `delay_duration` | int | `200` | Delay before showing (ms) |
| `skip_delay_duration` | int | `300` | Skip delay when moving between tooltips |

### TooltipContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `side` | str | `"top"` | `"top"`, `"right"`, `"bottom"`, `"left"` |
| `side_offset` | int | `4` | Distance from trigger |
| `align` | str | `"center"` | `"start"`, `"center"`, `"end"` |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Role** | `role="tooltip"` |
| **Keyboard** | Shows on focus |
| **Escape** | Hides tooltip |
| **Screen readers** | Content announced |

---

## Troubleshooting

### Tooltip doesn't appear

**Problem:** Hovering over trigger shows nothing.

**Cause:** Missing `TooltipProvider` wrapper.

**Solution:** Wrap your app or component tree:

```python
TooltipProvider()[  # Required!
    Tooltip()[
        TooltipTrigger()[Button()["Hover me"]],
        TooltipContent()["Tooltip text"]
    ]
]
```

### Tooltip appears instantly without delay

**Problem:** Tooltip shows immediately on hover, feels jarring.

**Solution:** Add delay via provider:

```python
TooltipProvider(delay_duration=300)[  # 300ms delay
    Tooltip()[...]
]
```

### Tooltip position is wrong

**Problem:** Tooltip appears on wrong side.

**Solution:** Set explicit side:

```python
TooltipContent(side="bottom")[  # top, right, bottom, left
    "This appears below"
]
```

### Tooltip gets cut off at edges

**Problem:** Tooltip clipped at screen/container edge.

**Solution:** Tooltip auto-flips by default. If still clipped:

```python
TooltipContent(
    side="top",
    side_offset=4,
    avoid_collisions=True  # Enable collision detection
)[...]
```

### Tooltip not showing on disabled button

**Problem:** Tooltip doesn't work on `disabled` elements.

**Cause:** Disabled elements don't receive mouse events.

**Solution:** Wrap in a span:

```python
Tooltip()[
    TooltipTrigger(as_child=True)[
        Span(class_="inline-block")[  # Wrapper receives events
            Button(disabled=True)["Disabled"]
        ]
    ],
    TooltipContent()["This feature is coming soon"]
]
```

### Tooltip flickers on quick mouse movements

**Problem:** Tooltip appears/disappears rapidly.

**Solution:** Increase delay and skip delay on immediate re-hover:

```python
TooltipProvider(
    delay_duration=200,
    skip_delay_duration=100  # Quick re-hover shows immediately
)[...]
```

### Screen reader not announcing tooltip

**Problem:** Tooltip content not read by screen readers.

**Solution:** Tooltip uses `aria-describedby` automatically. Ensure trigger has accessible label:

```python
Tooltip()[
    TooltipTrigger()[
        Button(aria_label="Settings")[Icon()]  # Has accessible name
    ],
    TooltipContent()["Adjust your preferences"]
]
```

---

## Related Components

- **[Popover](./popover.md)** — For interactive content
- **[Button](./button.md)** — Common trigger element
