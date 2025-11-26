# Radio Group

Select one option from a list.

## When to Use

Radio groups are for:
- **Single selection** - Choose one plan, one size
- **Settings** - Theme, language preference
- **Forms** - Gender, payment method
- **Mutually exclusive options** - Yes/No, On/Off

**Checkbox vs Radio:** Use checkbox for multiple selections, radio for single selection.

## Installation

```bash
pynext ui add radio-group
```

Or use directly:

```python
from pynext.shadcn import RadioGroup, RadioGroupItem
```

## Basic Usage

```python
RadioGroup(default_value="option-1")[
    div(class_="flex items-center gap-2")[
        RadioGroupItem(value="option-1", id="r1"),
        Label(html_for="r1")["Option 1"]
    ],
    div(class_="flex items-center gap-2")[
        RadioGroupItem(value="option-2", id="r2"),
        Label(html_for="r2")["Option 2"]
    ]
]
```

## Examples

### Plan Selection

```python
RadioGroup(default_value="free", class_="space-y-3")[
    div(class_="flex items-start gap-3")[
        RadioGroupItem(value="free", id="free"),
        div()[
            Label(html_for="free")["Free"],
            p(class_="text-sm text-muted-foreground")[
                "Basic features, forever free"
            ]
        ]
    ],
    div(class_="flex items-start gap-3")[
        RadioGroupItem(value="pro", id="pro"),
        div()[
            Label(html_for="pro")["Pro - $10/month"],
            p(class_="text-sm text-muted-foreground")[
                "Advanced features for professionals"
            ]
        ]
    ],
    div(class_="flex items-start gap-3")[
        RadioGroupItem(value="enterprise", id="enterprise"),
        div()[
            Label(html_for="enterprise")["Enterprise"],
            p(class_="text-sm text-muted-foreground")[
                "Custom solutions for teams"
            ]
        ]
    ]
]
```

### Horizontal Layout

```python
RadioGroup(default_value="light", class_="flex gap-4")[
    div(class_="flex items-center gap-2")[
        RadioGroupItem(value="light", id="light"),
        Label(html_for="light")["Light"]
    ],
    div(class_="flex items-center gap-2")[
        RadioGroupItem(value="dark", id="dark"),
        Label(html_for="dark")["Dark"]
    ],
    div(class_="flex items-center gap-2")[
        RadioGroupItem(value="system", id="system"),
        Label(html_for="system")["System"]
    ]
]
```

### With Signal State

```python
from pynext import Signal

selected_size = Signal("medium")

def SizeSelector():
    return RadioGroup(
        value=selected_size.value,
        on_value_change=selected_size.set
    )[
        [
            div(class_="flex items-center gap-2")[
                RadioGroupItem(value=size, id=size),
                Label(html_for=size)[size.title()]
            ]
            for size in ["small", "medium", "large"]
        ]
    ]
```

### Card Style Options

```python
RadioGroup(default_value="card", class_="grid grid-cols-3 gap-4")[
    Label(
        html_for="card",
        class_="flex flex-col items-center p-4 border rounded-lg cursor-pointer hover:border-primary [&:has(:checked)]:border-primary"
    )[
        RadioGroupItem(value="card", id="card", class_="sr-only"),
        "💳",
        span(class_="text-sm")["Card"]
    ],
    Label(
        html_for="paypal",
        class_="flex flex-col items-center p-4 border rounded-lg cursor-pointer hover:border-primary [&:has(:checked)]:border-primary"
    )[
        RadioGroupItem(value="paypal", id="paypal", class_="sr-only"),
        "🅿️",
        span(class_="text-sm")["PayPal"]
    ],
    Label(
        html_for="apple",
        class_="flex flex-col items-center p-4 border rounded-lg cursor-pointer hover:border-primary [&:has(:checked)]:border-primary"
    )[
        RadioGroupItem(value="apple", id="apple", class_="sr-only"),
        "🍎",
        span(class_="text-sm")["Apple Pay"]
    ]
]
```

### Disabled Option

```python
RadioGroup()[
    div(class_="flex items-center gap-2")[
        RadioGroupItem(value="available", id="av"),
        Label(html_for="av")["Available"]
    ],
    div(class_="flex items-center gap-2 opacity-50")[
        RadioGroupItem(value="sold-out", id="so", disabled=True),
        Label(html_for="so")["Sold Out"]
    ]
]
```

## Props Reference

### RadioGroup

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `default_value` | str | `None` | Initially selected value |
| `value` | str | `None` | Controlled selection |
| `on_value_change` | callable | `None` | Called when selection changes |
| `name` | str | `None` | Form field name |
| `disabled` | bool | `False` | Disable all options |

### RadioGroupItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Option value |
| `id` | str | `None` | HTML id for label |
| `disabled` | bool | `False` | Disable this option |

## Accessibility

- Uses native radio behavior
- Arrow keys navigate between options
- Space selects focused option
- Labels are properly associated
- `aria-checked` indicates selection

## Related Components

- [Checkbox](./checkbox.md) - For multiple selection
- [Switch](./switch.md) - For binary toggle
- [Toggle](./toggle.md) - Button-style selection

