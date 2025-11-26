# Separator

> **Like a horizontal line on paper — visually divides content into sections**

A simple line that separates content into distinct groups.

---

## First Principles: What IS a Separator?

### The Core Concept

A separator creates **visual boundaries** between content:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE SEPARATOR CONCEPT                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WITHOUT SEPARATOR:                WITH SEPARATOR:                           │
│  ──────────────────                ───────────────                           │
│                                                                              │
│  Profile Settings                  Profile Settings                          │
│  Name: John Doe                    Name: John Doe                            │
│  Email: john@example.com           Email: john@example.com                   │
│  Account Settings                  ────────────────────── ← Separator        │
│  Password                          Account Settings                          │
│  Two-factor auth                   Password                                  │
│  Delete account                    Two-factor auth                           │
│                                    Delete account                            │
│  Sections blur together!           Clear sections!                           │
│                                                                              │
│  Separator Types:                                                            │
│  ────────────────                                                           │
│  HORIZONTAL: ────────────────────                                           │
│                                                                              │
│  VERTICAL:   │                                                               │
│              │                                                               │
│              │                                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When to Use Separators

```
USE SEPARATOR:                      USE SPACING/CARDS INSTEAD:
──────────────                      ──────────────────────────
• Between menu sections             • Between major page sections
• In dropdown menus                 • Between unrelated content
• Between form groups               • When cards make more sense
• In toolbars                       • When border adds clarity
```

---

## Installation

```bash
pynext ui add separator
```

Or import directly:

```python
from pynext.shadcn import Separator
```

---

## Step-by-Step Usage

### Step 1: Horizontal Separator

```python
div()[
    h2()["Section One"],
    p()["Content for section one"],
    
    Separator(class_="my-4"),
    
    h2()["Section Two"],
    p()["Content for section two"],
]
```

### Step 2: Vertical Separator

```python
div(class_="flex h-5 items-center space-x-4 text-sm")[
    span()["Blog"],
    Separator(orientation="vertical"),
    span()["Docs"],
    Separator(orientation="vertical"),
    span()["Source"],
]
```

### Step 3: With Label

```python
div(class_="relative")[
    Separator(),
    span(class_="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background px-2 text-xs text-muted-foreground")[
        "OR"
    ]
]
```

---

## Common Patterns

### Pattern 1: In Dropdown Menu

```python
DropdownMenuContent()[
    DropdownMenuItem()["Profile"],
    DropdownMenuItem()["Settings"],
    Separator(),  # ← Divides sections
    DropdownMenuItem()["Logout"],
]
```

### Pattern 2: Form Sections

```python
form(class_="space-y-6")[
    # Personal Info
    div(class_="space-y-4")[
        h3(class_="font-medium")["Personal Information"],
        Input(placeholder="Name"),
        Input(placeholder="Email"),
    ],
    
    Separator(),
    
    # Address
    div(class_="space-y-4")[
        h3(class_="font-medium")["Address"],
        Input(placeholder="Street"),
        Input(placeholder="City"),
    ],
]
```

### Pattern 3: Breadcrumb-style Navigation

```python
nav(class_="flex items-center space-x-2 text-sm")[
    a(href="/")["Home"],
    Separator(orientation="vertical", class_="h-4"),
    a(href="/products")["Products"],
    Separator(orientation="vertical", class_="h-4"),
    span(class_="text-muted-foreground")["Widget"],
]
```

### Pattern 4: In Card Footer

```python
Card()[
    CardContent()[
        # Card content
    ],
    Separator(),
    CardFooter(class_="flex justify-between")[
        Button(variant="ghost")["Cancel"],
        Button()["Save"],
    ]
]
```

---

## API Reference

### Separator

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `orientation` | str | `"horizontal"` | `"horizontal"` or `"vertical"` |
| `decorative` | bool | `True` | If true, `aria-hidden="true"` |
| `class_` | str | `""` | Additional styling |

---

## Styling

### Custom Colors

```python
Separator(class_="bg-red-500")  # Colored separator
```

### Thickness

```python
Separator(class_="h-[2px]")  # Thicker horizontal
Separator(orientation="vertical", class_="w-[2px]")  # Thicker vertical
```

### Dashed/Dotted

```python
Separator(class_="border-t border-dashed bg-transparent")
```

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Role** | `role="separator"` (when not decorative) |
| **Decorative** | `aria-hidden="true"` by default |
| **Orientation** | `aria-orientation` when vertical |

For meaningful separators (not just visual):

```python
Separator(decorative=False)  # Announces to screen readers
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Vertical separator invisible | Missing height | Add container height or explicit `h-*` |
| Too much spacing | Default margins | Adjust with margin classes |
| Not visible | Color too light | Check against background color |

---

## Related Components

- **[Card](./card.md)** — For grouped content sections
- **[DropdownMenu](./dropdown-menu.md)** — Common use case
