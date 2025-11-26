# Input

Text input fields for collecting user data.

## When to Use

Inputs are for collecting:
- **Text data** - Names, emails, search queries
- **Passwords** - With appropriate masking
- **Numbers** - Quantities, amounts
- **Dates** - When a picker isn't needed

For longer text, use [Textarea](./textarea.md). For selecting from options, use [Select](./select.md).

## Installation

```bash
pynext ui add input
```

Or use directly:

```python
from pynext.shadcn import Input, Label, Textarea
```

## Basic Usage

```python
Input(placeholder="Enter your name")
```

**How it works:** Input wraps a native `<input>` element with consistent styling and focus states.

## With Label

Always pair inputs with labels for accessibility:

```python
div(class_="space-y-2")[
    Label(html_for="email")["Email"],
    Input(id="email", type="email", placeholder="m@example.com")
]
```

## Input Types

```python
# Email with validation
Input(type="email", placeholder="Email address")

# Password (masked)
Input(type="password", placeholder="Password")

# Number
Input(type="number", min=0, max=100)

# Search
Input(type="search", placeholder="Search...")

# URL
Input(type="url", placeholder="https://example.com")

# Phone
Input(type="tel", placeholder="+1 (555) 000-0000")
```

## States

### Disabled

```python
Input(disabled=True, placeholder="Can't edit this")
```

### Required

```python
Input(required=True, placeholder="Required field")
```

### With Error

```python
div(class_="space-y-2")[
    Label(html_for="email")["Email"],
    Input(
        id="email",
        class_="border-red-500 focus:ring-red-500",
        aria_invalid="true",
    ),
    p(class_="text-sm text-red-500")["Please enter a valid email"]
]
```

### With Helper Text

```python
div(class_="space-y-2")[
    Label(html_for="username")["Username"],
    Input(id="username", placeholder="johndoe"),
    p(class_="text-sm text-muted-foreground")[
        "This will be your public display name."
    ]
]
```

## With Icons

### Left Icon

```python
div(class_="relative")[
    span(class_="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground")[
        "🔍"  # Or use an icon component
    ],
    Input(class_="pl-10", placeholder="Search...")
]
```

### Right Icon

```python
div(class_="relative")[
    Input(type="password", class_="pr-10"),
    button(
        class_="absolute right-3 top-1/2 -translate-y-1/2",
        type="button",
    )["👁️"]
]
```

## Form Integration

### With Server Actions

```python
from pynext import server_action

@server_action
async def submit_form(data: dict):
    email = data["email"]
    # Process form...

def SignupForm():
    return form(action=submit_form)[
        div(class_="space-y-4")[
            div(class_="space-y-2")[
                Label(html_for="email")["Email"],
                Input(id="email", name="email", type="email", required=True)
            ],
            Button(type="submit")["Sign Up"]
        ]
    ]
```

### With Signals

```python
from pynext import Signal

email = Signal("")

def EmailInput():
    return Input(
        value=email.value,
        on_input=lambda e: email.set(e.target.value),
        placeholder="Enter email"
    )
```

## Textarea

For multi-line text input:

```python
from pynext.shadcn import Textarea

Textarea(placeholder="Tell us about yourself...", rows=4)
```

### Textarea Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `rows` | int | `3` | Number of visible rows |
| `placeholder` | str | `""` | Placeholder text |
| `disabled` | bool | `False` | Disable input |
| `required` | bool | `False` | Mark as required |

## Props Reference

### Input

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | str | `"text"` | Input type (text, email, password, number, etc.) |
| `placeholder` | str | `""` | Placeholder text |
| `disabled` | bool | `False` | Disable the input |
| `required` | bool | `False` | Mark as required |
| `id` | str | `None` | HTML id for label association |
| `name` | str | `None` | Form field name |
| `value` | any | `None` | Controlled value |
| `class_` | str | `""` | Additional CSS classes |

### Label

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `html_for` | str | `None` | ID of the associated input |
| `class_` | str | `""` | Additional CSS classes |

## Accessibility

- Always use `Label` with `html_for` matching the input's `id`
- Set `aria-invalid="true"` for error states
- Provide error messages linked with `aria-describedby`
- Use `required` attribute for required fields

## Related Components

- [Label](./label.md) - Input labels
- [Textarea](./textarea.md) - Multi-line input
- [Button](./button.md) - Form submission

