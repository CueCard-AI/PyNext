# Accordion

Collapsible content sections for organizing information.

## When to Use

Accordions are for:
- **FAQs** - Questions and answers
- **Settings** - Grouped preferences
- **Navigation** - Category menus
- **Long content** - Breaking up text sections

Use accordions when users don't need to see all content at once.

## Installation

```bash
pynext ui add accordion
```

Or use directly:

```python
from pynext.shadcn import Accordion, AccordionItem, AccordionTrigger, AccordionContent
```

## Basic Usage

```python
Accordion(type="single", collapsible=True)[
    AccordionItem(value="item-1")[
        AccordionTrigger()["Is it accessible?"],
        AccordionContent()[
            "Yes. It follows WAI-ARIA design patterns."
        ]
    ],
    AccordionItem(value="item-2")[
        AccordionTrigger()["Is it styled?"],
        AccordionContent()[
            "Yes. It comes with default styles that match your theme."
        ]
    ]
]
```

## Sub-Components

| Component | Purpose |
|-----------|---------|
| `Accordion` | Container, manages open state |
| `AccordionItem` | Individual section wrapper |
| `AccordionTrigger` | Clickable header |
| `AccordionContent` | Collapsible content |

## Types

### Single (only one open)

```python
Accordion(type="single", default_value="item-1")[
    AccordionItem(value="item-1")[...],
    AccordionItem(value="item-2")[...],
]
```

### Multiple (any number open)

```python
Accordion(type="multiple", default_value=["item-1", "item-2"])[
    AccordionItem(value="item-1")[...],
    AccordionItem(value="item-2")[...],
]
```

## Examples

### FAQ Section

```python
faq_items = [
    {"q": "How do I get started?", "a": "Install PyNext with pip install pynext, then run pynext init my-app."},
    {"q": "Is it free?", "a": "Yes, PyNext is open source and free to use."},
    {"q": "Can I use it in production?", "a": "Absolutely! PyNext is production-ready."},
]

Accordion(type="single", collapsible=True, class_="w-full")[
    [
        AccordionItem(value=f"faq-{i}")[
            AccordionTrigger()[item["q"]],
            AccordionContent()[item["a"]]
        ]
        for i, item in enumerate(faq_items)
    ]
]
```

### Settings Accordion

```python
Accordion(type="multiple", class_="w-full")[
    AccordionItem(value="account")[
        AccordionTrigger()[
            div(class_="flex items-center gap-2")[
                "👤",
                "Account Settings"
            ]
        ],
        AccordionContent()[
            div(class_="space-y-4")[
                div(class_="flex justify-between")[
                    span()["Email Notifications"],
                    Switch()
                ],
                div(class_="flex justify-between")[
                    span()["Two-Factor Auth"],
                    Switch()
                ]
            ]
        ]
    ],
    AccordionItem(value="appearance")[
        AccordionTrigger()[
            div(class_="flex items-center gap-2")[
                "🎨",
                "Appearance"
            ]
        ],
        AccordionContent()[
            # Theme settings...
        ]
    ]
]
```

### Nested Accordion

```python
Accordion(type="single")[
    AccordionItem(value="getting-started")[
        AccordionTrigger()["Getting Started"],
        AccordionContent()[
            Accordion(type="single", class_="pl-4")[
                AccordionItem(value="installation")[
                    AccordionTrigger()["Installation"],
                    AccordionContent()["pip install pynext"]
                ],
                AccordionItem(value="first-app")[
                    AccordionTrigger()["Your First App"],
                    AccordionContent()["pynext init my-app"]
                ]
            ]
        ]
    ]
]
```

## Controlled Accordion

```python
from pynext import Signal

open_item = Signal("item-1")

Accordion(
    type="single",
    value=open_item.value,
    on_value_change=open_item.set
)[
    AccordionItem(value="item-1")[
        AccordionTrigger()["Section 1"],
        AccordionContent()["Content 1"]
    ],
    AccordionItem(value="item-2")[
        AccordionTrigger()["Section 2"],
        AccordionContent()["Content 2"]
    ]
]
```

## Styling

### Without Border

```python
AccordionItem(value="item-1", class_="border-0")[...]
```

### Custom Trigger Arrow

```python
AccordionTrigger(class_="[&>svg]:hidden")[
    div(class_="flex justify-between w-full")[
        "Section Title",
        span(class_="transition-transform group-data-[state=open]:rotate-180")[
            "▼"
        ]
    ]
]
```

### Filled Background

```python
AccordionItem(
    value="item-1",
    class_="bg-muted rounded-lg mb-2 px-4"
)[...]
```

## Props Reference

### Accordion

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | str | `"single"` | "single" or "multiple" |
| `collapsible` | bool | `False` | Allow closing all items (single type) |
| `default_value` | str/list | `None` | Initially open item(s) |
| `value` | str/list | `None` | Controlled open state |
| `on_value_change` | callable | `None` | Called when state changes |

### AccordionItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Unique identifier |
| `disabled` | bool | `False` | Disable this item |

## Accessibility

- Uses `aria-expanded` to indicate state
- Arrow keys navigate between items
- Enter/Space toggles items
- Proper heading levels in triggers

## Related Components

- [Tabs](./tabs.md) - Side-by-side content switching
- [Collapsible](./collapsible.md) - Single collapsible section

