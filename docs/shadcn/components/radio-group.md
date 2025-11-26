# RadioGroup

> **Like a multiple choice question — pick exactly one answer**

A set of mutually exclusive options where only one can be selected at a time.

---

## First Principles: What IS a RadioGroup?

### The Core Concept

A RadioGroup ensures **exactly one option is selected**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE RADIOGROUP CONCEPT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Multiple Choice Test:             RadioGroup:                               │
│  ─────────────────────             ───────────                               │
│                                                                              │
│  What color is the sky?            Choose your plan:                         │
│  ○ Red                             ○ Free                                   │
│  ○ Green                           ● Pro      ← Selected                    │
│  ● Blue  ← Selected                ○ Enterprise                              │
│  ○ Yellow                                                                    │
│                                    Only ONE can be selected                  │
│  Circle = only one answer          Click another = previous deselects        │
│                                                                              │
│  vs CHECKBOX (square):                                                       │
│  ☑ Red                                                                       │
│  ☑ Blue   ← Multiple allowed                                                │
│  ☑ Green                                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When to Use RadioGroup

```
USE RADIOGROUP:                     USE SELECT/DROPDOWN:
───────────────                     ────────────────────
• 2-5 options                       • 6+ options
• Options need explanation          • Options are simple
• Show all options at once          • Save space
• Side-by-side comparison           • Less important choice

Examples:                           Examples:
• Pricing plans                     • Country selection
• Shipping methods                  • Time zones
• Payment type                      • Font size
```

---

## Installation

```bash
pynext ui add radio-group
```

Or import directly:

```python
from pynext.shadcn import RadioGroup, RadioGroupItem, Label
```

---

## Step-by-Step Usage

### Step 1: Basic RadioGroup

```python
RadioGroup(default_value="option1")[
    div(class_="flex items-center space-x-2")[
        RadioGroupItem(value="option1", id="r1"),
        Label(html_for="r1")["Option 1"]
    ],
    div(class_="flex items-center space-x-2")[
        RadioGroupItem(value="option2", id="r2"),
        Label(html_for="r2")["Option 2"]
    ],
    div(class_="flex items-center space-x-2")[
        RadioGroupItem(value="option3", id="r3"),
        Label(html_for="r3")["Option 3"]
    ]
]
```

### Step 2: Controlled State

```python
from pynext import Signal

plan = Signal("pro")

RadioGroup(value=plan.value, on_value_change=plan.set)[
    div(class_="flex items-center space-x-2")[
        RadioGroupItem(value="free", id="free"),
        Label(html_for="free")["Free"]
    ],
    div(class_="flex items-center space-x-2")[
        RadioGroupItem(value="pro", id="pro"),
        Label(html_for="pro")["Pro"]
    ],
    div(class_="flex items-center space-x-2")[
        RadioGroupItem(value="enterprise", id="enterprise"),
        Label(html_for="enterprise")["Enterprise"]
    ]
]

# Show selected plan
p()[f"Selected: {plan.value}"]
```

### Step 3: With Descriptions

```python
RadioGroup(value=plan.value, on_value_change=plan.set, class_="space-y-4")[
    div(class_="flex items-start space-x-3")[
        RadioGroupItem(value="free", id="free", class_="mt-1"),
        div()[
            Label(html_for="free", class_="font-medium")["Free"],
            p(class_="text-sm text-muted-foreground")[
                "Basic features for personal use"
            ]
        ]
    ],
    div(class_="flex items-start space-x-3")[
        RadioGroupItem(value="pro", id="pro", class_="mt-1"),
        div()[
            Label(html_for="pro", class_="font-medium")["Pro - $9/month"],
            p(class_="text-sm text-muted-foreground")[
                "Advanced features for professionals"
            ]
        ]
    ],
]
```

---

## Common Patterns

### Pattern 1: Pricing Cards

```python
RadioGroup(value=selected_plan.value, on_value_change=selected_plan.set)[
    div(class_="grid grid-cols-3 gap-4")[
        [
            Label(
                html_for=plan["id"],
                class_=f"cursor-pointer rounded-lg border-2 p-4 {'border-primary' if selected_plan.value == plan['id'] else 'border-muted'}"
            )[
                RadioGroupItem(value=plan["id"], id=plan["id"], class_="sr-only"),
                div(class_="text-center")[
                    h3(class_="font-bold")[plan["name"]],
                    p(class_="text-2xl font-bold my-2")[f"${plan['price']}"],
                    p(class_="text-sm text-muted-foreground")[plan["description"]]
                ]
            ]
            for plan in plans
        ]
    ]
]
```

### Pattern 2: Shipping Methods

```python
RadioGroup(value=shipping.value, on_value_change=shipping.set)[
    [
        div(
            class_=f"flex items-center justify-between p-4 border rounded-lg cursor-pointer {'border-primary bg-primary/5' if shipping.value == method['id'] else ''}",
            key=method["id"]
        )[
            div(class_="flex items-center gap-3")[
                RadioGroupItem(value=method["id"], id=method["id"]),
                div()[
                    Label(html_for=method["id"], class_="font-medium cursor-pointer")[
                        method["name"]
                    ],
                    p(class_="text-sm text-muted-foreground")[method["time"]]
                ]
            ],
            span(class_="font-medium")[f"${method['price']}"]
        ]
        for method in shipping_methods
    ]
]
```

### Pattern 3: Horizontal Layout

```python
RadioGroup(
    value=size.value, 
    on_value_change=size.set,
    class_="flex gap-4"
)[
    [
        div(class_="flex items-center space-x-2", key=s)[
            RadioGroupItem(value=s, id=s),
            Label(html_for=s)[s]
        ]
        for s in ["S", "M", "L", "XL"]
    ]
]
```

---

## API Reference

### RadioGroup

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | `None` | Controlled selected value |
| `default_value` | str | `None` | Initial selected value |
| `on_value_change` | callable | `None` | Called when selection changes |
| `disabled` | bool | `False` | Disable all options |
| `required` | bool | `False` | Required for form |
| `name` | str | `None` | Form field name |
| `orientation` | str | `"vertical"` | Layout direction |

### RadioGroupItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Item's value |
| `disabled` | bool | `False` | Disable this option |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Role** | `role="radiogroup"` |
| **Arrow Keys** | Up/Down or Left/Right to navigate |
| **Focus** | Tab into group, arrows to move |
| **ARIA** | `aria-checked` on selected item |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Multiple selected | Using checkboxes | Use RadioGroupItem, not Checkbox |
| Can't deselect | Expected behavior | Radios require a selection |
| Keyboard nav broken | Wrong orientation | Match `orientation` to layout |

---

## Related Components

- **[Checkbox](./checkbox.md)** — For multiple selections
- **[Switch](./switch.md)** — For on/off toggles
- **[Select](./select.md)** — For dropdown single selection
