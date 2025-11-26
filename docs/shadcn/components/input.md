# Input

> **The fundamental text entry point — type here to provide information**

A single-line text input field for collecting user data.

---

## First Principles: What IS an Input?

### The Core Concept

An input is a **data entry point** — a window where users type information:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE INPUT CONCEPT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Without Input:                    With Input:                               │
│  ──────────────                    ───────────                               │
│                                                                              │
│  How do we get the                 ┌──────────────────────────┐              │
│  user's name?                      │ John Doe                 │              │
│                                    └──────────────────────────┘              │
│  🤷 No way to ask!                 User types → We capture data              │
│                                                                              │
│  The input is a BRIDGE between:                                              │
│  ────────────────────────────────                                           │
│                                                                              │
│  HUMAN                             COMPUTER                                  │
│  ─────                             ────────                                  │
│  Knows their name         →        Receives "John Doe" as text              │
│  Types on keyboard        →        Stores in form data                       │
│  Sees visual feedback     ←        Shows what was typed                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Input Types Explained

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INPUT TYPES CHEAT SHEET                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TYPE="text"        General text input (default)                             │
│  ────────────       Names, addresses, short answers                          │
│                                                                              │
│  TYPE="email"       Email validation                                         │
│  ────────────       Shows @ keyboard on mobile, validates format             │
│                                                                              │
│  TYPE="password"    Hidden text                                              │
│  ──────────────     Shows dots (•••••), secure entry                         │
│                                                                              │
│  TYPE="number"      Numeric input                                            │
│  ─────────────      Numeric keyboard on mobile, up/down arrows               │
│                                                                              │
│  TYPE="tel"         Phone number                                             │
│  ──────────         Phone keyboard on mobile                                 │
│                                                                              │
│  TYPE="url"         Website URL                                              │
│  ──────────         URL keyboard on mobile, validates format                 │
│                                                                              │
│  TYPE="search"      Search query                                             │
│  ─────────────      Clear button, search icon (browser-dependent)            │
│                                                                              │
│  TYPE="date"        Date picker                                              │
│  ────────────       Native date picker (browser-dependent)                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add input
```

Or import directly:

```python
from pynext.shadcn import Input, Label, Textarea
```

---

## Step-by-Step Usage

### Step 1: Basic Input

```python
Input(placeholder="Enter your name...")
```

### Step 2: With Label

```python
div(class_="space-y-2")[
    Label(html_for="email")["Email"],
    Input(id="email", type="email", placeholder="email@example.com")
]
```

### Step 3: In a Form

```python
from pynext import server_action

@server_action
async def submit_form(data: dict):
    return {"success": True}

form(action=submit_form, class_="space-y-4")[
    div(class_="space-y-2")[
        Label(html_for="name")["Name"],
        Input(id="name", name="name", required=True)
    ],
    div(class_="space-y-2")[
        Label(html_for="email")["Email"],
        Input(id="email", name="email", type="email", required=True)
    ],
    Button(type="submit")["Submit"]
]
```

### Step 4: Controlled Input

```python
from pynext import Signal

name = Signal("")

Input(
    value=name.value,
    on_change=lambda e: name.set(e.target.value),
    placeholder="Type something..."
)

# Display the value
p()[f"You typed: {name.value}"]
```

---

## All Variants

### Input Types

```python
# Text (default)
Input(type="text", placeholder="Regular text...")

# Email
Input(type="email", placeholder="email@example.com")

# Password
Input(type="password", placeholder="Enter password...")

# Number
Input(type="number", placeholder="0", min=0, max=100)

# Tel
Input(type="tel", placeholder="+1 (555) 000-0000")

# URL
Input(type="url", placeholder="https://example.com")

# Search
Input(type="search", placeholder="Search...")

# Date
Input(type="date")
```

### States

```python
# Disabled
Input(disabled=True, value="Can't edit this")

# Read-only
Input(read_only=True, value="Read but not edit")

# Required
Input(required=True, placeholder="Required field")

# With error
Input(class_="border-red-500 focus:ring-red-500", aria_invalid="true")
```

---

## Common Patterns

### Pattern 1: Input with Icon

```python
div(class_="relative")[
    Icons.search(class_="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"),
    Input(class_="pl-10", placeholder="Search...")
]

# Right icon
div(class_="relative")[
    Input(class_="pr-10", type="email", placeholder="Email"),
    Icons.mail(class_="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground")
]
```

### Pattern 2: Input with Button

```python
div(class_="flex gap-2")[
    Input(placeholder="Enter email...", class_="flex-1"),
    Button()["Subscribe"]
]
```

### Pattern 3: Input with Validation Error

```python
from pynext import Signal

email = Signal("")
error = Signal("")

def validate(value):
    if not "@" in value:
        error.set("Please enter a valid email")
    else:
        error.set("")

div(class_="space-y-2")[
    Label(html_for="email")["Email"],
    Input(
        id="email",
        type="email",
        value=email.value,
        on_change=lambda e: (email.set(e.target.value), validate(e.target.value)),
        class_=error.value and "border-red-500 focus:ring-red-500" or "",
        aria_invalid=bool(error.value)
    ),
    error.value and p(class_="text-sm text-red-500")[error.value]
]
```

### Pattern 4: Password with Toggle

```python
from pynext import Signal

show_password = Signal(False)

div(class_="relative")[
    Input(
        type="text" if show_password.value else "password",
        placeholder="Password"
    ),
    Button(
        type="button",
        variant="ghost",
        size="icon",
        class_="absolute right-0 top-0",
        on_click=lambda: show_password.set(not show_password.value)
    )[
        show_password.value and Icons.eye_off() or Icons.eye()
    ]
]
```

### Pattern 5: Character Counter

```python
from pynext import Signal

bio = Signal("")
max_length = 280

div(class_="space-y-2")[
    Label()["Bio"],
    Textarea(
        value=bio.value,
        on_change=lambda e: bio.set(e.target.value[:max_length]),
        placeholder="Tell us about yourself..."
    ),
    p(class_="text-sm text-muted-foreground text-right")[
        f"{len(bio.value)}/{max_length}"
    ]
]
```

---

## Textarea

For multi-line text input:

```python
Textarea(
    placeholder="Enter your message...",
    rows=4
)
```

### Auto-resize Textarea

```python
Textarea(
    placeholder="This grows as you type...",
    class_="min-h-[80px] resize-none",
    on_input="this.style.height='auto';this.style.height=this.scrollHeight+'px'"
)
```

---

## API Reference

### Input

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | str | `"text"` | Input type |
| `placeholder` | str | `""` | Placeholder text |
| `value` | str | `None` | Controlled value |
| `default_value` | str | `None` | Initial value |
| `disabled` | bool | `False` | Disable input |
| `required` | bool | `False` | Mark as required |
| `read_only` | bool | `False` | Read-only mode |
| `min` | int | `None` | Minimum value (number) |
| `max` | int | `None` | Maximum value (number) |
| `min_length` | int | `None` | Minimum characters |
| `max_length` | int | `None` | Maximum characters |
| `pattern` | str | `None` | Regex validation pattern |

### Label

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `html_for` | str | `None` | ID of associated input |

### Textarea

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `rows` | int | `3` | Number of visible rows |
| `cols` | int | `None` | Number of visible columns |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Label Association** | Use `html_for` to link Label to Input |
| **Required State** | `aria-required="true"` |
| **Invalid State** | `aria-invalid="true"` + `aria-describedby` |
| **Disabled State** | `disabled` attribute |

```python
# Accessible input with error
div()[
    Label(html_for="email")["Email"],
    Input(
        id="email",
        aria_invalid=True,
        aria_describedby="email-error"
    ),
    p(id="email-error", class_="text-sm text-red-500")[
        "Please enter a valid email"
    ]
]
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Value not updating | Missing controlled state | Use Signal with on_change |
| Validation not working | Using text type | Use correct type (email, url, etc.) |
| Label click not focusing | Missing html_for | Add matching id |
| Mobile keyboard wrong | Wrong input type | Use type="tel", "email", etc. |

---

## Related Components

- **[Label](./input.md#label)** — Always pair with inputs
- **[Button](./button.md)** — For form submission
- **[Form](./form.md)** — For complete form handling
- **[Textarea](./input.md#textarea)** — For multi-line input
