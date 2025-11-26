# Badge

> **Like a label sticker — a small visual tag that categorizes or highlights**

A compact element for displaying status, categories, or counts.

---

## First Principles: What IS a Badge?

### The Core Concept

A badge is a **small visual label** that provides quick context:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE BADGE CONCEPT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WITHOUT BADGES:                   WITH BADGES:                              │
│  ───────────────                   ────────────                              │
│                                                                              │
│  Task List:                        Task List:                                │
│  • Fix bug                         • Fix bug [Critical]                      │
│  • Add feature                     • Add feature [In Progress]               │
│  • Update docs                     • Update docs [Done]                      │
│                                                                              │
│  Hard to scan status!              Status visible at a glance!               │
│                                                                              │
│  Badge Types:                                                                │
│  ─────────────                                                              │
│  [Default]  [Secondary]  [Destructive]  [Outline]                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Common Badge Uses

```
STATUS:     [Active]  [Pending]  [Closed]
CATEGORY:   [Bug]  [Feature]  [Documentation]
COUNT:      Inbox [3]  Notifications [12]
NEW:        Feature [New]  [Beta]
```

---

## Installation

```bash
pynext ui add badge
```

Or import directly:

```python
from pynext.shadcn import Badge
```

---

## Step-by-Step Usage

### Step 1: Basic Badge

```python
Badge()["Badge"]
```

### Step 2: Variants

```python
Badge()["Default"]
Badge(variant="secondary")["Secondary"]
Badge(variant="outline")["Outline"]
Badge(variant="destructive")["Destructive"]
```

### Step 3: In Context

```python
# Next to text
h3(class_="flex items-center gap-2")[
    "Feature Name",
    Badge(variant="secondary")["Beta"]
]

# In a list item
div(class_="flex items-center justify-between")[
    span()["Task title"],
    Badge()["In Progress"]
]
```

---

## Common Patterns

### Pattern 1: Status Badge

```python
def status_badge(status: str):
    variants = {
        "active": ("default", "Active"),
        "pending": ("secondary", "Pending"),
        "completed": ("outline", "Completed"),
        "cancelled": ("destructive", "Cancelled"),
    }
    variant, label = variants.get(status, ("secondary", status))
    return Badge(variant=variant)[label]

# Usage
status_badge(task.status)
```

### Pattern 2: Notification Count

```python
Button(variant="ghost", class_="relative")[
    Icons.bell(class_="h-5 w-5"),
    unread_count > 0 and Badge(
        class_="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0",
        variant="destructive"
    )[unread_count if unread_count < 100 else "99+"]
]
```

### Pattern 3: Tag List

```python
div(class_="flex flex-wrap gap-2")[
    [
        Badge(variant="outline", class_="cursor-pointer hover:bg-muted", key=tag)[
            tag,
            Button(
                variant="ghost",
                size="icon",
                class_="h-4 w-4 ml-1 p-0",
                on_click=lambda t=tag: remove_tag(t)
            )[Icons.x(class_="h-3 w-3")]
        ]
        for tag in tags
    ]
]
```

### Pattern 4: Priority Indicator

```python
def priority_badge(priority: str):
    colors = {
        "critical": "bg-red-500 text-white",
        "high": "bg-orange-500 text-white",
        "medium": "bg-yellow-500 text-black",
        "low": "bg-green-500 text-white",
    }
    return Badge(class_=colors.get(priority, ""))[priority.capitalize()]
```

---

## API Reference

### Badge

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | str | `"default"` | Visual style |

### Variants

| Variant | Appearance |
|---------|------------|
| `default` | Primary color, filled |
| `secondary` | Muted color, filled |
| `outline` | Border only, transparent |
| `destructive` | Red/danger color |

---

## Styling

### Custom Colors

```python
# Success
Badge(class_="bg-green-500 text-white")["Success"]

# Warning
Badge(class_="bg-yellow-500 text-black")["Warning"]

# Info
Badge(class_="bg-blue-500 text-white")["Info"]
```

### Sizes

```python
# Small
Badge(class_="text-xs px-1.5 py-0.5")["Small"]

# Default
Badge()["Default"]

# Large
Badge(class_="text-sm px-3 py-1")["Large"]
```

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Semantics** | Purely decorative, use with context |
| **Color Contrast** | Ensure text is readable |
| **Screen Readers** | Badge text is announced |

---

## Troubleshooting

### Badge not displaying correct color

**Problem:** Badge shows default color instead of variant color.

**Cause:** CSS variables not defined.

**Solution:** Ensure your theme includes:

```css
:root {
  --primary: 222.2 47.4% 11.2%;
  --secondary: 210 40% 96.1%;
  --destructive: 0 84.2% 60.2%;
}
```

### Badge text overflows

**Problem:** Long text causes badge to stretch or overflow.

**Solution:** Use truncation or max-width:

```python
Badge(class_="max-w-[100px] truncate")["Very long status text"]
```

### Badge not aligned with other elements

**Problem:** Badge appears above or below inline text.

**Solution:** Use proper alignment:

```python
Span(class_="inline-flex items-center gap-1")[
    "Status:",
    Badge(class_="align-middle")["Active"]
]
```

### Notification badge not positioned correctly

**Problem:** Badge on avatar or icon not in corner.

**Solution:** Use relative/absolute positioning:

```python
Div(class_="relative inline-block")[
    Avatar()[...],
    Badge(
        class_="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center"
    )["3"]
]
```

### Badge color contrast issues

**Problem:** Badge text is hard to read.

**Solution:** Ensure sufficient contrast:

```python
# Use dark text on light backgrounds
Badge(class_="bg-yellow-200 text-yellow-900")["Warning"]

# Use light text on dark backgrounds
Badge(class_="bg-blue-700 text-white")["Info"]
```

---

## Related Components

- **[Avatar](./avatar.md)** — Often paired with badges
- **[Button](./button.md)** — For actionable badges
