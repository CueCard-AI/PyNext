# Switch

A toggle for binary settings.

## When to Use

Switches are for:
- **On/Off settings** - Enable/disable features
- **Boolean preferences** - Dark mode, notifications
- **Feature flags** - Toggle functionality

**Checkbox vs Switch:** Use checkbox for agreement/selection, switch for immediate on/off actions.

## Installation

```bash
pynext ui add switch
```

Or use directly:

```python
from pynext.shadcn import Switch
```

## Basic Usage

```python
div(class_="flex items-center gap-2")[
    Switch(id="airplane"),
    Label(html_for="airplane")["Airplane Mode"]
]
```

## Examples

### Settings List

```python
div(class_="space-y-4")[
    div(class_="flex items-center justify-between")[
        div()[
            Label()["Email Notifications"],
            p(class_="text-sm text-muted-foreground")[
                "Receive emails about account activity"
            ]
        ],
        Switch(default_checked=True)
    ],
    div(class_="flex items-center justify-between")[
        div()[
            Label()["Marketing Emails"],
            p(class_="text-sm text-muted-foreground")[
                "Receive tips and product updates"
            ]
        ],
        Switch()
    ],
]
```

### With Signal State

```python
from pynext import Signal

dark_mode = Signal(False)

def DarkModeToggle():
    return div(class_="flex items-center gap-2")[
        Switch(
            checked=dark_mode.value,
            on_checked_change=dark_mode.set
        ),
        Label()["Dark Mode"],
        span(class_="text-sm text-muted-foreground")[
            "On" if dark_mode.value else "Off"
        ]
    ]
```

### Disabled State

```python
Switch(disabled=True)
Switch(disabled=True, checked=True)
```

## Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `checked` | bool | `None` | Controlled state |
| `default_checked` | bool | `False` | Initial state |
| `on_checked_change` | callable | `None` | Called on toggle |
| `disabled` | bool | `False` | Disable interaction |
| `id` | str | `None` | HTML id for label |
| `name` | str | `None` | Form field name |

## Accessibility

- Uses `role="switch"`
- Focusable via keyboard
- Space/Enter toggles state
- `aria-checked` reflects state

## Related Components

- [Checkbox](./checkbox.md) - For multi-select options
- [Toggle](./toggle.md) - Button-style toggle

