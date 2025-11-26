# Checkbox

A control for selecting multiple options.

## When to Use

Checkboxes are for:
- **Multi-select** - Choose multiple items from a list
- **Agreement** - Accept terms and conditions
- **Bulk actions** - Select items for deletion
- **Feature toggles** - Enable multiple features

**Switch vs Checkbox:** Use switch for immediate on/off, checkbox for form submissions.

## Installation

```bash
pynext ui add checkbox
```

Or use directly:

```python
from pynext.shadcn import Checkbox
```

## Basic Usage

```python
div(class_="flex items-center gap-2")[
    Checkbox(id="terms"),
    Label(html_for="terms")[
        "Accept terms and conditions"
    ]
]
```

## Examples

### Multi-Select List

```python
options = ["Email", "SMS", "Push notifications"]

div(class_="space-y-2")[
    [
        div(class_="flex items-center gap-2")[
            Checkbox(id=f"notify-{i}"),
            Label(html_for=f"notify-{i}")[option]
        ]
        for i, option in enumerate(options)
    ]
]
```

### With Signal State

```python
from pynext import Signal

accepted = Signal(False)

def TermsCheckbox():
    return div(class_="flex items-center gap-2")[
        Checkbox(
            checked=accepted.value,
            on_checked_change=accepted.set
        ),
        Label()["I accept the terms"],
    ]
```

### Indeterminate State

For "select all" with partial selection:

```python
Checkbox(checked="indeterminate")
```

### Disabled

```python
Checkbox(disabled=True)
Checkbox(disabled=True, checked=True)
```

## Form Integration

```python
from pynext import server_action

@server_action
async def submit_preferences(data: dict):
    # data contains checkbox values
    pass

form(action=submit_preferences)[
    div(class_="space-y-2")[
        div(class_="flex items-center gap-2")[
            Checkbox(name="newsletter", id="newsletter"),
            Label(html_for="newsletter")["Subscribe to newsletter"]
        ],
        div(class_="flex items-center gap-2")[
            Checkbox(name="updates", id="updates"),
            Label(html_for="updates")["Receive product updates"]
        ]
    ],
    Button(type="submit")["Save Preferences"]
]
```

## Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `checked` | bool/"indeterminate" | `None` | Controlled state |
| `default_checked` | bool | `False` | Initial state |
| `on_checked_change` | callable | `None` | Called on change |
| `disabled` | bool | `False` | Disable interaction |
| `required` | bool | `False` | Mark as required |
| `id` | str | `None` | HTML id |
| `name` | str | `None` | Form field name |

## Accessibility

- Uses native checkbox behavior
- Focusable via Tab
- Space toggles state
- Works with Label

## Related Components

- [Switch](./switch.md) - For immediate on/off
- [RadioGroup](./radio-group.md) - For single selection

