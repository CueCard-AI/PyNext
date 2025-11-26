# Alert

Display important messages to users.

## When to Use

Alerts are for:
- **Success messages** - "Your changes have been saved"
- **Error messages** - "Something went wrong"
- **Warnings** - "This action cannot be undone"
- **Information** - "New features are available"

Alerts are static and always visible. For dismissible notifications, consider a toast component.

## Installation

```bash
pynext ui add alert
```

Or use directly:

```python
from pynext.shadcn import Alert, AlertTitle, AlertDescription
```

## Basic Usage

```python
Alert()[
    AlertTitle()["Heads up!"],
    AlertDescription()[
        "You can add components to your app using the CLI."
    ]
]
```

**How it works:** Alert provides a styled container. AlertTitle and AlertDescription structure the content.

## Variants

### Default

```python
Alert()[
    AlertTitle()["Note"],
    AlertDescription()["This is a default alert."]
]
```

Neutral styling, for general information.

### Destructive

```python
Alert(variant="destructive")[
    AlertTitle()["Error"],
    AlertDescription()[
        "Your session has expired. Please log in again."
    ]
]
```

Red styling, for errors and dangerous actions.

## Examples

### Success Message

```python
Alert(class_="border-green-500 text-green-700 bg-green-50")[
    span(class_="text-green-500")["✓"],
    AlertTitle()["Success!"],
    AlertDescription()[
        "Your payment has been processed successfully."
    ]
]
```

### Warning Message

```python
Alert(class_="border-yellow-500 text-yellow-700 bg-yellow-50")[
    span(class_="text-yellow-500")["⚠️"],
    AlertTitle()["Warning"],
    AlertDescription()[
        "Your free trial expires in 3 days."
    ]
]
```

### With Icon

```python
Alert()[
    div(class_="flex gap-3")[
        span(class_="text-xl")["💡"],
        div()[
            AlertTitle()["Pro Tip"],
            AlertDescription()[
                "Use keyboard shortcuts to work faster."
            ]
        ]
    ]
]
```

### Dismissible Alert

```python
from pynext import Signal

show_alert = Signal(True)

def DismissibleAlert():
    if not show_alert.value:
        return None
    
    return Alert(class_="relative pr-12")[
        AlertTitle()["New Feature"],
        AlertDescription()[
            "Check out the new dashboard design."
        ],
        button(
            class_="absolute right-4 top-4 opacity-70 hover:opacity-100",
            on_click=lambda: show_alert.set(False)
        )["✕"]
    ]
```

### Alert List

```python
def AlertList(alerts: list):
    return div(class_="space-y-4")[
        [
            Alert(
                variant="destructive" if alert["type"] == "error" else "default",
                key=alert["id"]
            )[
                AlertTitle()[alert["title"]],
                AlertDescription()[alert["message"]]
            ]
            for alert in alerts
        ]
    ]
```

### Form Validation Alert

```python
errors = ["Email is required", "Password must be at least 8 characters"]

Alert(variant="destructive")[
    AlertTitle()["There were errors with your submission"],
    AlertDescription()[
        ul(class_="list-disc pl-4 mt-2")[
            [li()[error] for error in errors]
        ]
    ]
]
```

## Styling

### Custom Colors

```python
# Info (blue)
Alert(class_="border-blue-200 bg-blue-50 text-blue-800")

# Success (green)
Alert(class_="border-green-200 bg-green-50 text-green-800")

# Warning (yellow)
Alert(class_="border-yellow-200 bg-yellow-50 text-yellow-800")

# Error (red) - or use variant="destructive"
Alert(class_="border-red-200 bg-red-50 text-red-800")
```

### With Border Accent

```python
Alert(class_="border-l-4 border-l-blue-500")[
    AlertTitle()["Info"],
    AlertDescription()["Left border accent style."]
]
```

### Compact Alert

```python
Alert(class_="py-2")[
    p(class_="text-sm")["A compact inline alert message."]
]
```

## Props Reference

### Alert

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | str | `"default"` | Visual style: "default" or "destructive" |
| `class_` | str | `""` | Additional CSS classes |

### AlertTitle

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

### AlertDescription

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

## Accessibility

- Uses `role="alert"` for screen reader announcement
- Color is not the only indicator (icons, text help)
- Destructive alerts should be announced with urgency

```python
Alert(variant="destructive", role="alert", aria_live="assertive")[
    AlertTitle()["Error"],
    AlertDescription()["Critical error occurred."]
]
```

## Related Components

- [AlertDialog](./alert-dialog.md) - Modal confirmation
- [Card](./card.md) - For less urgent information
- [Badge](./badge.md) - Inline status indicators

