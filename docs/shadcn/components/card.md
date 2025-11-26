# Card

> **Like an index card or playing card — a self-contained container for related content**

A flexible container for grouping related content with header, body, and footer sections.

---

## First Principles: What IS a Card?

### The Core Concept

A card is a **visual container** that groups related information together:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE CARD CONCEPT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Physical Card:                    Digital Card:                             │
│  ──────────────                    ─────────────                             │
│                                                                              │
│  ┌────────────────┐                ┌──────────────────────┐                 │
│  │   RECIPE       │                │ 📧 Email Widget      │ ← Header        │
│  │   ──────       │                ├──────────────────────┤                 │
│  │   Ingredients: │                │ You have 3 unread    │                 │
│  │   • Flour      │                │ messages             │ ← Body          │
│  │   • Sugar      │                │                      │                 │
│  │   • Eggs       │                ├──────────────────────┤                 │
│  │                │                │ [View Inbox]         │ ← Footer        │
│  │   Cook at 350° │                └──────────────────────┘                 │
│  └────────────────┘                                                          │
│                                                                              │
│  Both are:                                                                   │
│  • Self-contained                                                            │
│  • Visually bounded                                                          │
│  • Hold related info                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Cards Exist

Cards create **visual hierarchy** and **scannable content**:

```
WITHOUT CARDS:                      WITH CARDS:
──────────────                      ───────────

Dashboard                           Dashboard
─────────                           ─────────

Revenue: $12,345                    ┌─────────────┐ ┌─────────────┐
Users: 1,234                        │ Revenue     │ │ Users       │
Orders: 567                         │ $12,345     │ │ 1,234       │
Sessions: 8,901                     │ ↑ 12%       │ │ ↑ 5%        │
                                    └─────────────┘ └─────────────┘
All data runs together              ┌─────────────┐ ┌─────────────┐
Hard to scan quickly                │ Orders      │ │ Sessions    │
No visual grouping                  │ 567         │ │ 8,901       │
                                    │ ↓ 3%        │ │ ↑ 8%        │
                                    └─────────────┘ └─────────────┘

                                    Each metric is distinct
                                    Easy to scan and compare
```

---

## Installation

```bash
pynext ui add card
```

Or import directly:

```python
from pynext.shadcn import (
    Card, CardHeader, CardTitle, CardDescription,
    CardContent, CardFooter
)
```

---

## Step-by-Step Usage

### Step 1: Simple Card

```python
Card()[
    CardHeader()[
        CardTitle()["Card Title"],
        CardDescription()["Card Description"]
    ],
    CardContent()[
        p()["Card Content"]
    ],
    CardFooter()[
        Button()["Action"]
    ]
]
```

### Step 2: Content-Only Card

```python
Card(class_="p-6")[
    p()["Simple content without header/footer"]
]
```

### Step 3: Interactive Card

```python
Card(class_="hover:shadow-lg transition-shadow cursor-pointer")[
    CardHeader()[
        CardTitle()["Clickable Card"]
    ],
    CardContent()[
        p()["Click anywhere on this card"]
    ]
]
```

---

## Common Patterns

### Pattern 1: Stats Card

```python
Card()[
    CardHeader(class_="flex flex-row items-center justify-between pb-2")[
        CardTitle(class_="text-sm font-medium")["Total Revenue"],
        Icons.dollar_sign(class_="h-4 w-4 text-muted-foreground")
    ],
    CardContent()[
        div(class_="text-2xl font-bold")["$45,231.89"],
        p(class_="text-xs text-muted-foreground")[
            "+20.1% from last month"
        ]
    ]
]
```

### Pattern 2: Form Card

```python
Card(class_="w-[350px]")[
    CardHeader()[
        CardTitle()["Create Account"],
        CardDescription()["Enter your email below to create your account"]
    ],
    CardContent()[
        form(class_="space-y-4")[
            div(class_="space-y-2")[
                Label(html_for="email")["Email"],
                Input(id="email", type="email", placeholder="m@example.com")
            ],
            div(class_="space-y-2")[
                Label(html_for="password")["Password"],
                Input(id="password", type="password")
            ]
        ]
    ],
    CardFooter()[
        Button(class_="w-full")["Create Account"]
    ]
]
```

### Pattern 3: Profile Card

```python
Card(class_="w-[350px]")[
    CardHeader()[
        div(class_="flex items-center gap-4")[
            Avatar(class_="h-16 w-16")[
                AvatarImage(src=user.avatar),
                AvatarFallback()[user.initials]
            ],
            div()[
                CardTitle()[user.name],
                CardDescription()[user.role]
            ]
        ]
    ],
    CardContent()[
        div(class_="space-y-2 text-sm")[
            div(class_="flex justify-between")[
                span(class_="text-muted-foreground")["Email"],
                span()[user.email]
            ],
            div(class_="flex justify-between")[
                span(class_="text-muted-foreground")["Location"],
                span()[user.location]
            ]
        ]
    ],
    CardFooter(class_="flex gap-2")[
        Button(variant="outline", class_="flex-1")["Message"],
        Button(class_="flex-1")["Follow"]
    ]
]
```

### Pattern 4: Feature Card Grid

```python
div(class_="grid gap-4 md:grid-cols-2 lg:grid-cols-3")[
    [
        Card()[
            CardHeader()[
                feature.icon(class_="h-8 w-8 text-primary"),
                CardTitle(class_="mt-4")[feature.title]
            ],
            CardContent()[
                p(class_="text-muted-foreground")[feature.description]
            ],
            CardFooter()[
                a(href=feature.link, class_="text-primary hover:underline")[
                    "Learn more →"
                ]
            ]
        ]
        for feature in features
    ]
]
```

### Pattern 5: Pricing Card

```python
Card(class_="relative overflow-hidden")[
    # Popular badge
    popular and div(
        class_="absolute top-0 right-0 bg-primary text-primary-foreground px-3 py-1 text-xs"
    )["Popular"],
    
    CardHeader()[
        CardTitle()[plan.name],
        CardDescription()[plan.description],
        div(class_="mt-4")[
            span(class_="text-4xl font-bold")[f"${plan.price}"],
            span(class_="text-muted-foreground")["/month"]
        ]
    ],
    CardContent()[
        ul(class_="space-y-2")[
            [
                li(class_="flex items-center gap-2")[
                    Icons.check(class_="h-4 w-4 text-green-500"),
                    feature
                ]
                for feature in plan.features
            ]
        ]
    ],
    CardFooter()[
        Button(class_="w-full", variant="outline" if not popular else "default")[
            "Get Started"
        ]
    ]
]
```

---

## Styling Variants

### With Border

```python
Card(class_="border-2 border-primary")  # Colored border
Card(class_="border-dashed")            # Dashed border
```

### With Shadow

```python
Card(class_="shadow-lg")                # Large shadow
Card(class_="shadow-none")              # No shadow
```

### With Background

```python
Card(class_="bg-primary text-primary-foreground")  # Colored background
Card(class_="bg-muted")                            # Muted background
```

---

## API Reference

### Card

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

### CardHeader

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

### CardTitle

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

### CardDescription

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

### CardContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

### CardFooter

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Semantic Structure** | Uses appropriate heading levels |
| **Interactive Cards** | Add `role="button"` and `tabindex="0"` |
| **Focus States** | Visible focus ring for keyboard users |

```python
# Accessible clickable card
Card(
    role="button",
    tabindex="0",
    on_click=handler,
    on_keydown=lambda e: e.key == "Enter" and handler(),
    class_="focus:ring-2 focus:ring-primary"
)[...]
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Content overflows | Fixed width | Add `overflow-hidden` or responsive classes |
| Cards not aligned | Grid issues | Use `items-stretch` on parent grid |
| Footer not at bottom | Card height varies | Use flexbox with `flex-1` on CardContent |

---

## Related Components

- **[Button](./button.md)** — For card actions
- **[Avatar](./avatar.md)** — For profile cards
- **[Badge](./badge.md)** — For card labels
