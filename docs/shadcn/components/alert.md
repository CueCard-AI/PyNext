# Alert

> **Like a sticky note on your monitor — persistent, important information**

A highlighted message that stays visible on the page to convey important information.

---

## First Principles: What IS an Alert?

### The Core Concept

An alert is a **persistent in-page notification** that draws attention:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE ALERT CONCEPT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TOAST (temporary):                ALERT (persistent):                       │
│  ──────────────────                ───────────────────                       │
│                                                                              │
│  ┌─────────────────┐               ┌──────────────────────────────────────┐ │
│  │                 │               │                                      │ │
│  │  Page Content   │               │  ⚠️ ALERT: Your trial expires in 3   │ │
│  │                 │               │     days. Upgrade now to continue.   │ │
│  │         ┌─────┐ │               │                                      │ │
│  │         │Saved│ │               └──────────────────────────────────────┘ │
│  │         └─────┘ │               │                                      │ │
│  │           ↑     │               │  Page Content                        │ │
│  │       Disappears│               │                                      │ │
│  │       after 3s  │               │  Alert stays until dismissed or      │ │
│  │                 │               │  condition changes                   │ │
│  └─────────────────┘               └──────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Alert Variants

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ALERT TYPES                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DEFAULT:          Neutral information                                       │
│  ├────────────────────────────────────────┐                                 │
│  │ ℹ️ Note: This feature is in beta       │                                 │
│  └────────────────────────────────────────┘                                 │
│                                                                              │
│  DESTRUCTIVE:      Error or danger                                           │
│  ├────────────────────────────────────────┐                                 │
│  │ ⚠️ Error: Could not save changes       │                                 │
│  └────────────────────────────────────────┘                                 │
│                                                                              │
│  (Custom):         Success, warning, info                                    │
│  ├────────────────────────────────────────┐                                 │
│  │ ✓ Success: Your changes have been saved│                                 │
│  └────────────────────────────────────────┘                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add alert
```

Or import directly:

```python
from pynext.shadcn import Alert, AlertTitle, AlertDescription
```

---

## Step-by-Step Usage

### Step 1: Basic Alert

```python
Alert()[
    AlertTitle()["Heads up!"],
    AlertDescription()[
        "You can add components to your app using the CLI."
    ]
]
```

### Step 2: Destructive Alert

```python
Alert(variant="destructive")[
    Icons.alert_circle(class_="h-4 w-4"),
    AlertTitle()["Error"],
    AlertDescription()[
        "Your session has expired. Please log in again."
    ]
]
```

### Step 3: With Icon

```python
Alert()[
    Icons.terminal(class_="h-4 w-4"),
    AlertTitle()["Terminal"],
    AlertDescription()[
        "Run `pynext init` to create a new project."
    ]
]
```

---

## Common Patterns

### Pattern 1: Form Validation Error

```python
errors and Alert(variant="destructive")[
    Icons.alert_circle(class_="h-4 w-4"),
    AlertTitle()["There were errors with your submission"],
    AlertDescription()[
        ul(class_="list-disc pl-4")[
            [li()[error] for error in errors]
        ]
    ]
]
```

### Pattern 2: Feature Announcement

```python
Alert(class_="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-200")[
    Icons.sparkles(class_="h-4 w-4 text-purple-500"),
    AlertTitle()["New Feature!"],
    AlertDescription()[
        "Dark mode is now available. ",
        a(href="/settings", class_="underline")["Enable it in settings."]
    ]
]
```

### Pattern 3: Dismissible Alert

```python
from pynext import Signal

show_alert = Signal(True)

show_alert.value and Alert(class_="relative")[
    Icons.info(class_="h-4 w-4"),
    AlertTitle()["Update Available"],
    AlertDescription()["A new version is ready to install."],
    Button(
        variant="ghost",
        size="icon",
        class_="absolute top-2 right-2",
        on_click=lambda: show_alert.set(False)
    )[Icons.x(class_="h-4 w-4")]
]
```

---

## API Reference

### Alert

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | str | `"default"` | `"default"` or `"destructive"` |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Role** | `role="alert"` for important messages |
| **Icons** | Include `aria-hidden="true"` on decorative icons |
| **Dismissible** | Include accessible close button |

---

## Troubleshooting

### Alert not visible or wrong styling

**Problem:** Alert renders but looks plain/unstyled.

**Cause:** Missing Tailwind classes or CSS.

**Solution:** Ensure Tailwind is configured and pynext styles are imported:

```python
# Check that Alert is imported from shadcn
from pynext.shadcn import Alert, AlertTitle, AlertDescription
```

### Icon doesn't align with text

**Problem:** Icon appears misaligned with alert content.

**Solution:** Use proper flex alignment:

```python
Alert()[
    Div(class_="flex items-start gap-3")[
        Icon(class_="h-4 w-4 mt-0.5"),  # Add margin-top for alignment
        Div()[
            AlertTitle()["Title"],
            AlertDescription()["Description"]
        ]
    ]
]
```

### Destructive variant not showing red

**Problem:** `variant="destructive"` shows default styling.

**Cause:** CSS variables not defined or Tailwind not processing the classes.

**Solution:** Verify your `globals.css` includes:

```css
:root {
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 0 0% 98%;
}
```

### Screen reader not announcing alert

**Problem:** Screen readers skip over the alert.

**Solution:** Add `role="alert"` for important messages:

```python
Alert(role="alert")[
    AlertTitle()["Error"],
    AlertDescription()["Something went wrong."]
]
```

---

## Related Components

- **[Toast](./toast.md)** — For temporary notifications
- **[AlertDialog](./alert-dialog.md)** — For confirmations
