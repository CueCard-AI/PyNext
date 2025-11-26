# Getting Started with PyNext UI

This guide will help you set up and use PyNext's UI components, including ShadCN-style components and Tailwind integration.

## Quick Start

### 1. Import Components

Components are available immediately from `pynext.shadcn`:

```python
from pynext.shadcn import Button, Card, Input, Dialog
```

### 2. Use in Your Pages

```python
from pynext import page
from pynext.shadcn import Button, Card, CardHeader, CardTitle, CardContent

@page
def home():
    return Card()[
        CardHeader()[CardTitle()["Welcome to PyNext"]],
        CardContent()[
            "Build beautiful UIs with Python",
            Button()["Get Started"]
        ]
    ]
```

### 3. That's It!

No npm install, no configuration, no build step. Components just work.

---

## Understanding the Component Syntax

PyNext components use a Python-friendly syntax:

```python
# Basic component
Button()["Click me"]

# With props
Button(variant="destructive", size="lg")["Delete"]

# Nested components
Card()[
    CardHeader()[CardTitle()["Title"]],
    CardContent()["Content here"]
]

# Multiple children
div()[
    Button()["One"],
    Button()["Two"],
    Button()["Three"]
]
```

### Why `[]` Instead of `()`?

The bracket syntax `Button()["text"]` separates:

- **Props** in parentheses: `Button(variant="primary")`
- **Children** in brackets: `Button()["Click me"]`

This makes it clear what's configuration vs content.

---

## Tailwind CSS Integration

PyNext includes Tailwind utilities for styling:

### The `tw` Builder

Build Tailwind classes with autocomplete:

```python
from pynext.tw import tw

# Chainable API
div(class_=tw.flex.items_center.justify_between.p(4))

# With values
div(class_=tw.bg("blue-500").text("white").hover.bg("blue-600"))

# With modifiers
div(class_=tw.md.hidden.lg.flex)
```

### The `cn` Utility

Merge classes conditionally:

```python
from pynext.tw import cn

Button(class_=cn(
    "base-class",
    is_active and "bg-blue-500",
    is_disabled and "opacity-50 cursor-not-allowed"
))
```

---

## Customizing Components

### Option 1: Use class_ Override

Add or override classes inline:

```python
Button(class_="my-custom-class")["Custom Button"]
```

### Option 2: Copy to Project

Copy a component to your project for full customization:

```bash
pynext ui add button
```

This creates `components/ui/button.py` which you can edit freely.

### Option 3: Create Your Own

Build custom components using primitives:

```python
from pynext.shadcn.primitives import Portal, FocusTrap
from pynext.tw import cn

class MyModal:
    def __init__(self, open=False):
        self.open = open
        self._children = []
    
    def __getitem__(self, children):
        self._children = children if isinstance(children, list) else [children]
        return self
    
    def render(self):
        if not self.open:
            return ""
        
        return Portal()[
            FocusTrap()[
                div(class_=cn("modal-overlay"))[
                    div(class_=cn("modal-content"))[
                        *self._children
                    ]
                ]
            ]
        ].render()
```

---

## React Escape Hatch

Need a React component that hasn't been ported yet?

```python
from pynext.react import use_react

# Wrap any npm React component
DatePicker = use_react("react-datepicker")
Carousel = use_react("embla-carousel-react", "Carousel")

# Use like any PyNext component
DatePicker(selected=date, on_change=set_date)
```

**Requirements:**

1. Add the package to `pynext.npm.txt`:
   ```
   react-datepicker@^4.0.0
   ```

2. React compatibility is auto-enabled

---

## Component Categories

### Basic Components

Simple UI elements:

- `Button` — Clickable actions
- `Input` — Text input fields
- `Label` — Form labels
- `Textarea` — Multi-line text
- `Badge` — Status indicators
- `Separator` — Visual dividers

### Card Components

Container with sections:

- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`

### Feedback Components

User notifications:

- `Alert`, `AlertTitle`, `AlertDescription`
- `AlertDialog` (confirmation modal)

### Interactive Components

Complex interactions:

- `Dialog` — Modal windows
- `DropdownMenu` — Action menus
- `Tabs` — Tabbed content
- `Accordion` — Collapsible sections

### Form Components

Form controls:

- `Toggle` — On/off button
- `Switch` — Toggle switch
- `Checkbox` — Check box
- `RadioGroup` — Radio buttons

---

## Next Steps

- [Component Reference](../shadcn/README.md) — Full component documentation
- [Tailwind Guide](./TAILWIND.md) — Advanced Tailwind usage
- [React Wrapper](./REACT_WRAPPER.md) — Using React components
- [Custom Registry](./CUSTOM_REGISTRY.md) — Creating component libraries

