# PyNext ShadCN

**Beautiful, accessible components for PyNext** — A full port of [ShadCN/ui](https://ui.shadcn.com/) to Python.

## What is ShadCN?

ShadCN/ui is the most popular React component library, known for:

- **Beautiful defaults** — Modern, polished styling with Tailwind CSS
- **Fully accessible** — Built on Radix UI primitives with proper ARIA
- **Copy-paste customizable** — Components live in your codebase, not hidden in node_modules
- **Production-ready** — Used by Vercel, Cal.com, and thousands of projects

PyNext ShadCN brings this same experience to Python.

## Quick Start

### Using Built-in Components

Components are available immediately, no installation needed:

```python
from pynext.shadcn import Button, Card, CardHeader, CardTitle, CardContent

Card()[
    CardHeader()[CardTitle()["Welcome"]],
    CardContent()[
        "Get started with PyNext ShadCN",
        Button()["Learn More"]
    ]
]
```

### Customizing Components

To customize a component, copy it to your project:

```bash
pynext ui add button
```

This creates `components/ui/button.py` which you can edit freely.

## Available Components

### Basic
- [Button](./components/button.md) — Clickable actions
- [Input](./components/input.md) — Text input fields
- [Label](./components/label.md) — Form labels
- [Textarea](./components/textarea.md) — Multi-line text
- [Badge](./components/badge.md) — Status indicators
- [Avatar](./components/avatar.md) — User images
- [Separator](./components/separator.md) — Visual dividers

### Card
- [Card](./components/card.md) — Container with sections

### Feedback
- [Alert](./components/alert.md) — Important messages
- [AlertDialog](./components/alert-dialog.md) — Confirmation dialogs

### Interactive
- [Dialog](./components/dialog.md) — Modal windows
- [DropdownMenu](./components/dropdown-menu.md) — Action menus
- [Tabs](./components/tabs.md) — Tabbed content
- [Accordion](./components/accordion.md) — Collapsible sections

### Form
- [Toggle](./components/toggle.md) — On/off buttons
- [Switch](./components/switch.md) — Toggle switches
- [Checkbox](./components/checkbox.md) — Check boxes
- [RadioGroup](./components/radio-group.md) — Radio selections

## Tailwind Integration

ShadCN components use Tailwind CSS. PyNext provides utilities for working with Tailwind:

```python
from pynext.tw import tw, cn

# Build classes with type safety
div(class_=tw.flex.items_center.gap(4).p(4))

# Conditional classes
Button(class_=cn(
    "base-styles",
    is_primary and "bg-blue-500",
    is_disabled and "opacity-50"
))
```

## Theming

ShadCN uses CSS variables for theming. Add these to your CSS:

```css
:root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    /* ... more variables */
}

.dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark mode variables */
}
```

See [Theming Guide](./theming.md) for full variable list.

## React Escape Hatch

Need a complex React component that hasn't been ported yet?

```python
from pynext.react import use_react

DatePicker = use_react("react-datepicker")
DatePicker(selected=date, on_change=set_date)
```

See [React Wrapper](../ui/REACT_WRAPPER.md) for details.

