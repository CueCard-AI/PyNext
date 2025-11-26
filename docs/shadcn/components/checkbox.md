# Checkbox

> **Like a paper checklist box — tick it to select an option**

A control that allows users to select one or more options from a set.

---

## First Principles: What IS a Checkbox?

### The Core Concept

A checkbox is a **multi-select toggle** — you can have many checked at once:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE CHECKBOX CONCEPT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CHECKBOX (multi-select):          RADIO (single-select):                   │
│  ────────────────────────          ─────────────────────                    │
│                                                                              │
│  Which toppings?                   Pizza size?                               │
│  ☑ Pepperoni                       ○ Small                                  │
│  ☐ Mushrooms                       ● Medium  ← Only one                     │
│  ☑ Olives                          ○ Large                                  │
│  ☑ Extra cheese                                                             │
│     ↑                                                                        │
│  Multiple OK!                      Must pick exactly one                     │
│                                                                              │
│  CHECKBOX:                         SWITCH:                                   │
│  ─────────                         ───────                                   │
│  Part of a form                    Immediate effect                          │
│  Submit later                      Takes effect NOW                          │
│  ☑ I agree to terms               [─────○] Enable feature                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Checkbox States

```
UNCHECKED:     ☐    (default)
CHECKED:       ☑    (selected)
INDETERMINATE: ▣    (some children selected)
DISABLED:      ☐̲    (can't interact)
```

---

## Installation

```bash
pynext ui add checkbox
```

Or import directly:

```python
from pynext.shadcn import Checkbox, Label
```

---

## Step-by-Step Usage

### Step 1: Basic Checkbox

```python
div(class_="flex items-center space-x-2")[
    Checkbox(id="terms"),
    Label(html_for="terms")["Accept terms and conditions"]
]
```

### Step 2: Controlled State

```python
from pynext import Signal

agreed = Signal(False)

div(class_="flex items-center space-x-2")[
    Checkbox(
        id="terms",
        checked=agreed.value,
        on_checked_change=agreed.set
    ),
    Label(html_for="terms")["Accept terms and conditions"]
]

# Submit button disabled until checked
Button(disabled=not agreed.value)["Continue"]
```

### Step 3: In a Form

```python
form(action=submit_form, class_="space-y-4")[
    div(class_="space-y-2")[
        p(class_="font-medium")["Select your interests:"],
        
        div(class_="flex items-center space-x-2")[
            Checkbox(id="tech", name="interests", value="tech"),
            Label(html_for="tech")["Technology"]
        ],
        div(class_="flex items-center space-x-2")[
            Checkbox(id="design", name="interests", value="design"),
            Label(html_for="design")["Design"]
        ],
        div(class_="flex items-center space-x-2")[
            Checkbox(id="business", name="interests", value="business"),
            Label(html_for="business")["Business"]
        ]
    ],
    Button(type="submit")["Submit"]
]
```

---

## Common Patterns

### Pattern 1: Select All

```python
from pynext import Signal

items = [
    {"id": "1", "name": "Item 1"},
    {"id": "2", "name": "Item 2"},
    {"id": "3", "name": "Item 3"},
]
selected = Signal([])

all_selected = len(selected.value) == len(items)
some_selected = len(selected.value) > 0 and not all_selected

div(class_="space-y-2")[
    # Select all checkbox
    div(class_="flex items-center space-x-2")[
        Checkbox(
            id="select-all",
            checked=all_selected,
            indeterminate=some_selected,
            on_checked_change=lambda v: selected.set(
                [i["id"] for i in items] if v else []
            )
        ),
        Label(html_for="select-all", class_="font-medium")["Select all"]
    ],
    
    # Individual items
    [
        div(class_="flex items-center space-x-2 pl-6", key=item["id"])[
            Checkbox(
                id=item["id"],
                checked=item["id"] in selected.value,
                on_checked_change=lambda v, id=item["id"]: selected.set(
                    [*selected.value, id] if v else [x for x in selected.value if x != id]
                )
            ),
            Label(html_for=item["id"])[item["name"]]
        ]
        for item in items
    ]
]
```

### Pattern 2: Terms Checkbox

```python
div(class_="flex items-start space-x-2")[
    Checkbox(id="terms", class_="mt-1"),
    Label(html_for="terms", class_="text-sm leading-relaxed")[
        "I agree to the ",
        a(href="/terms", class_="underline")["Terms of Service"],
        " and ",
        a(href="/privacy", class_="underline")["Privacy Policy"]
    ]
]
```

### Pattern 3: With Description

```python
div(class_="flex items-start space-x-2")[
    Checkbox(id="marketing"),
    div()[
        Label(html_for="marketing")["Marketing emails"],
        p(class_="text-sm text-muted-foreground")[
            "Receive emails about new products and features."
        ]
    ]
]
```

---

## API Reference

### Checkbox

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `checked` | bool | `False` | Controlled checked state |
| `default_checked` | bool | `False` | Initial state |
| `on_checked_change` | callable | `None` | Called when state changes |
| `disabled` | bool | `False` | Disable checkbox |
| `required` | bool | `False` | Required for form |
| `name` | str | `None` | Form field name |
| `value` | str | `"on"` | Value when checked |
| `indeterminate` | bool | `False` | Mixed/partial state |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Label** | Always pair with Label component |
| **Keyboard** | Space to toggle |
| **ARIA** | Uses native checkbox behavior |
| **Focus** | Visible focus ring |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Not toggling | Missing controlled props | Add `checked` and `on_checked_change` |
| Label click not working | Missing `html_for` | Add matching `id` |
| Value not in form | Missing `name` | Add `name` prop |

---

## Related Components

- **[Switch](./switch.md)** — For immediate on/off
- **[RadioGroup](./radio-group.md)** — For single selection
- **[Label](./input.md#label)** — Always pair with checkbox
