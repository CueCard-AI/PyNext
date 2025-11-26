# Skeleton

> **Like a placeholder shadow — shows where content will appear while loading**

A loading placeholder that mimics the shape of content before it loads.

---

## First Principles: What IS a Skeleton?

### The Core Concept

A skeleton is a **content placeholder** that reduces perceived load time:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE SKELETON CONCEPT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WITHOUT SKELETON:                 WITH SKELETON:                            │
│  ─────────────────                 ──────────────                            │
│                                                                              │
│  ┌──────────────────┐              ┌──────────────────┐                     │
│  │                  │              │  ┌──┐ ░░░░░░░░░  │                     │
│  │                  │              │  └──┘ ░░░░░      │                     │
│  │     LOADING...   │              │       ░░░░░░░░░  │                     │
│  │     (blank)      │              │       ░░░░░░░    │                     │
│  │                  │              │                  │                     │
│  └──────────────────┘              └──────────────────┘                     │
│                                                                              │
│  User sees: Nothing                User sees: Shape of content               │
│  User feels: Slow, broken          User feels: Fast, loading                 │
│                                                                              │
│  LOADING COMPLETE:                                                           │
│  ─────────────────                                                          │
│  ┌──────────────────┐                                                       │
│  │  ┌──┐ John Smith │                                                       │
│  │  └──┘ Developer  │                                                       │
│  │       Lorem ipsum│                                                       │
│  │       dolor sit  │                                                       │
│  │                  │                                                       │
│  └──────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Skeletons Beat Spinners

```
SPINNER:                            SKELETON:
────────                            ─────────
• Generic "loading"                 • Shows what's coming
• Feels like waiting                • Feels like progress
• No layout hint                    • Prevents layout shift
• Same for all content              • Matches actual content
```

---

## Installation

```bash
pynext ui add skeleton
```

Or import directly:

```python
from pynext.shadcn import Skeleton
```

---

## Step-by-Step Usage

### Step 1: Basic Skeleton

```python
Skeleton(class_="h-4 w-[200px]")  # Text line
Skeleton(class_="h-12 w-12 rounded-full")  # Circle (avatar)
Skeleton(class_="h-32 w-full")  # Large block
```

### Step 2: Card Skeleton

```python
div(class_="flex items-center space-x-4")[
    Skeleton(class_="h-12 w-12 rounded-full"),  # Avatar
    div(class_="space-y-2")[
        Skeleton(class_="h-4 w-[250px]"),  # Name
        Skeleton(class_="h-4 w-[200px]"),  # Title
    ]
]
```

### Step 3: Full Card Loading

```python
Card()[
    CardHeader()[
        Skeleton(class_="h-6 w-[200px]"),  # Title
        Skeleton(class_="h-4 w-[300px]"),  # Description
    ],
    CardContent(class_="space-y-2")[
        Skeleton(class_="h-4 w-full"),
        Skeleton(class_="h-4 w-full"),
        Skeleton(class_="h-4 w-3/4"),
    ],
    CardFooter()[
        Skeleton(class_="h-10 w-[100px]"),  # Button
    ]
]
```

---

## Common Patterns

### Pattern 1: Data Table Loading

```python
Table()[
    TableHeader()[
        TableRow()[
            [TableHead()[Skeleton(class_="h-4 w-20")] for _ in range(4)]
        ]
    ],
    TableBody()[
        [
            TableRow()[
                [TableCell()[Skeleton(class_="h-4 w-full")] for _ in range(4)]
            ]
            for _ in range(5)
        ]
    ]
]
```

### Pattern 2: List Loading

```python
div(class_="space-y-4")[
    [
        div(class_="flex items-center gap-4", key=i)[
            Skeleton(class_="h-10 w-10 rounded-full"),
            div(class_="flex-1 space-y-2")[
                Skeleton(class_="h-4 w-3/4"),
                Skeleton(class_="h-3 w-1/2")
            ]
        ]
        for i in range(5)
    ]
]
```

### Pattern 3: Conditional Loading

```python
if loading:
    # Skeleton
    div(class_="space-y-4")[
        Skeleton(class_="h-8 w-48"),
        div(class_="grid grid-cols-3 gap-4")[
            [Skeleton(class_="h-32 w-full") for _ in range(3)]
        ]
    ]
else:
    # Actual content
    div(class_="space-y-4")[
        h2()[data.title],
        div(class_="grid grid-cols-3 gap-4")[
            [Card()[...] for item in data.items]
        ]
    ]
```

### Pattern 4: Article Skeleton

```python
article(class_="space-y-6")[
    # Title
    Skeleton(class_="h-10 w-3/4"),
    
    # Meta (author, date)
    div(class_="flex items-center gap-4")[
        Skeleton(class_="h-8 w-8 rounded-full"),
        Skeleton(class_="h-4 w-32"),
        Skeleton(class_="h-4 w-24"),
    ],
    
    # Hero image
    Skeleton(class_="h-64 w-full rounded-lg"),
    
    # Paragraphs
    div(class_="space-y-4")[
        [
            div(class_="space-y-2")[
                Skeleton(class_="h-4 w-full"),
                Skeleton(class_="h-4 w-full"),
                Skeleton(class_="h-4 w-2/3"),
            ]
            for _ in range(3)
        ]
    ]
]
```

---

## API Reference

### Skeleton

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Size and shape classes |

### Common Classes

| Class | Purpose |
|-------|---------|
| `h-4` | Text line height |
| `h-12 w-12 rounded-full` | Avatar |
| `h-32 w-full` | Image/card |
| `w-[200px]` | Fixed width |
| `w-full` | Full width |
| `w-3/4` | Partial width |

---

## Animation

The Skeleton has a built-in shimmer animation:

```css
/* Default animation */
@keyframes skeleton-shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}
```

To disable animation:

```python
Skeleton(class_="h-4 w-32 animate-none")
```

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **aria-hidden** | Skeletons are decorative |
| **No focus** | Not focusable |
| **Screen readers** | Use separate "Loading" announcement |

```python
# Accessible loading state
div()[
    span(class_="sr-only")["Loading content..."],  # Screen reader only
    Skeleton(class_="h-4 w-full", aria_hidden="true")
]
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong size | Missing dimensions | Add h-* and w-* classes |
| No animation | CSS not loaded | Check Tailwind config |
| Layout shift | Skeleton != content size | Match skeleton to content dimensions |

---

## Related Components

- **[Card](./card.md)** — Often contains skeletons
- **[Spinner](./spinner.md)** — Alternative loading indicator
