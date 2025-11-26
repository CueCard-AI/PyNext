# Card

A container for grouping related content with optional header and footer.

## When to Use

Cards are perfect for:
- **Dashboard widgets** - Metrics, charts, summaries
- **List items** - Blog posts, products, user profiles
- **Forms** - Settings panels, signup forms
- **Content sections** - Feature highlights, testimonials

Cards create visual hierarchy by grouping related information together.

## Installation

```bash
pynext ui add card
```

Or use directly:

```python
from pynext.shadcn import Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
```

## Basic Usage

```python
Card()[
    CardHeader()[
        CardTitle()["Card Title"],
        CardDescription()["Card description goes here"]
    ],
    CardContent()[
        p()["Your main content here."]
    ],
    CardFooter()[
        Button()["Action"]
    ]
]
```

**How it works:** Cards are built from composable parts. Use only what you need — a simple card might just have `CardContent`.

## Sub-Components

| Component | Purpose |
|-----------|---------|
| `Card` | The container |
| `CardHeader` | Top section with title/description |
| `CardTitle` | Main heading |
| `CardDescription` | Subtitle or summary |
| `CardContent` | Main content area |
| `CardFooter` | Bottom section for actions |

## Examples

### Simple Card

```python
Card(class_="max-w-sm")[
    CardContent(class_="pt-6")[
        p()["A simple card with just content."]
    ]
]
```

### Profile Card

```python
Card(class_="w-80")[
    CardHeader(class_="text-center")[
        Avatar(class_="w-20 h-20 mx-auto")[
            AvatarImage(src="/avatar.jpg"),
            AvatarFallback()["JD"]
        ],
        CardTitle(class_="mt-4")["Jane Doe"],
        CardDescription()["Software Engineer"]
    ],
    CardContent()[
        p(class_="text-sm text-center")[
            "Building the future of web development."
        ]
    ],
    CardFooter(class_="justify-center gap-2")[
        Button(variant="outline", size="sm")["Follow"],
        Button(size="sm")["Message"]
    ]
]
```

### Stats Card

```python
Card()[
    CardHeader(class_="flex flex-row items-center justify-between pb-2")[
        CardTitle(class_="text-sm font-medium")["Total Revenue"],
        span(class_="text-muted-foreground")["$"]
    ],
    CardContent()[
        div(class_="text-2xl font-bold")["$45,231.89"],
        p(class_="text-xs text-muted-foreground")[
            "+20.1% from last month"
        ]
    ]
]
```

### Form Card

```python
Card(class_="max-w-md")[
    CardHeader()[
        CardTitle()["Create Account"],
        CardDescription()["Enter your email below to create your account."]
    ],
    CardContent()[
        div(class_="space-y-4")[
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

### Interactive Card

```python
Card(class_="hover:shadow-lg transition-shadow cursor-pointer")[
    CardHeader()[
        CardTitle()["Clickable Card"],
    ],
    CardContent()[
        p()["This card has hover effects."]
    ]
]
```

## Styling

### Custom Width

```python
Card(class_="w-full max-w-lg")  # Responsive width
Card(class_="w-96")              # Fixed width
```

### Custom Background

```python
Card(class_="bg-gradient-to-br from-purple-500 to-pink-500 text-white")
```

### Removing Border

```python
Card(class_="border-0 shadow-lg")
```

### Horizontal Layout

```python
Card(class_="flex flex-row")[
    CardContent(class_="flex-1")[...],
    CardFooter(class_="flex-col justify-center")[...]
]
```

## Props Reference

### Card

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

All sub-components accept `class_` for customization.

## Accessibility

- Cards are semantic containers using `<div>` with appropriate roles
- Use proper heading hierarchy inside `CardTitle`
- Ensure interactive cards have keyboard access
- For clickable cards, consider using `<a>` or `<button>` wrappers

## Related Components

- [Button](./button.md) - For card actions
- [Avatar](./avatar.md) - For profile cards
- [Badge](./badge.md) - For status indicators

