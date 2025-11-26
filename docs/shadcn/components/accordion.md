# Accordion

> **Like a folding paper menu — click a section to expand it, others collapse**

A vertically stacked set of collapsible sections, each with a header that reveals content.

---

## First Principles: What IS an Accordion?

### The Core Concept

An accordion **hides content until needed**, showing one (or multiple) sections at a time:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE ACCORDION CONCEPT                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  COLLAPSED STATE:                  EXPANDED STATE:                           │
│  ────────────────                  ───────────────                           │
│                                                                              │
│  ┌────────────────────┐            ┌────────────────────┐                   │
│  │ ▶ Section 1        │            │ ▼ Section 1        │                   │
│  ├────────────────────┤            ├────────────────────┤                   │
│  │ ▶ Section 2        │            │ Content for        │                   │
│  ├────────────────────┤            │ section 1 is       │                   │
│  │ ▶ Section 3        │            │ now visible!       │                   │
│  └────────────────────┘            ├────────────────────┤                   │
│                                    │ ▶ Section 2        │                   │
│  All content hidden                ├────────────────────┤                   │
│  Page looks clean                  │ ▶ Section 3        │                   │
│                                    └────────────────────┘                   │
│                                                                              │
│                                    Click another section →                   │
│                                    Section 1 closes, new one opens           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Accordions Exist

Accordions solve the **"information overload"** problem:

```
WITHOUT ACCORDION:                  WITH ACCORDION:
──────────────────                  ────────────────

┌────────────────────┐              ┌────────────────────┐
│ FAQ                │              │ FAQ                │
├────────────────────┤              ├────────────────────┤
│ Q: How do I...?    │              │ ▶ How do I...?     │
│ A: You can do it   │              │ ▶ What is...?      │
│ by following these │              │ ▼ Where can I...?  │ ← Expanded
│ detailed steps...  │              │   You can find it  │
│                    │              │   at our website.  │
│ Q: What is...?     │              │ ▶ Can I...?        │
│ A: This is a long  │              │ ▶ Why does...?     │
│ explanation that   │              └────────────────────┘
│ goes on and on...  │
│                    │              Only 1 answer visible
│ Q: Where can I...? │              User scans questions quickly
│ A: You can find... │              Clicks what interests them
│ ...                │
│ [scroll scroll]    │
│ [scroll scroll]    │
└────────────────────┘
```

---

## How It Works

### Component Hierarchy

```
Accordion                          ← Root: manages open state
├── AccordionItem                  ← Container for one section
│   ├── AccordionTrigger           ← Clickable header
│   │   └── "Section Title"
│   └── AccordionContent           ← Hidden/shown content
│       └── <your content>
├── AccordionItem
│   ├── AccordionTrigger
│   └── AccordionContent
└── ...
```

### The State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACCORDION STATE FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TYPE: "single" (default)                                                    │
│  ─────────────────────────                                                  │
│                                                                              │
│  Click Section 1:                                                            │
│  └── Section 1 opens                                                         │
│  └── All others close                                                        │
│                                                                              │
│  Click Section 1 again:                                                      │
│  └── Section 1 closes (if collapsible=True)                                  │
│  └── Section 1 stays open (if collapsible=False)                             │
│                                                                              │
│  TYPE: "multiple"                                                            │
│  ────────────────                                                           │
│                                                                              │
│  Click Section 1: Section 1 opens                                            │
│  Click Section 2: Section 2 opens (Section 1 stays open)                     │
│  Click Section 1: Section 1 closes                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add accordion
```

Or import directly:

```python
from pynext.shadcn import (
    Accordion, AccordionItem, AccordionTrigger, AccordionContent
)
```

---

## Step-by-Step Usage

### Step 1: Basic Accordion

```python
Accordion(type="single", collapsible=True)[
    AccordionItem(value="item-1")[
        AccordionTrigger()["Is it accessible?"],
        AccordionContent()[
            "Yes. It adheres to the WAI-ARIA design pattern."
        ]
    ],
    AccordionItem(value="item-2")[
        AccordionTrigger()["Is it styled?"],
        AccordionContent()[
            "Yes. It comes with default styles that matches the other components."
        ]
    ],
    AccordionItem(value="item-3")[
        AccordionTrigger()["Is it animated?"],
        AccordionContent()[
            "Yes. It's animated by default, but you can disable it if you prefer."
        ]
    ]
]
```

### Step 2: Multiple Items Open

```python
Accordion(type="multiple", default_value=["item-1"])[
    AccordionItem(value="item-1")[
        AccordionTrigger()["Section 1"],
        AccordionContent()["Content 1"]
    ],
    AccordionItem(value="item-2")[
        AccordionTrigger()["Section 2"],
        AccordionContent()["Content 2"]
    ],
]
```

### Step 3: Controlled State

```python
from pynext import Signal

open_items = Signal(["faq-1"])

Accordion(
    type="multiple",
    value=open_items.value,
    on_value_change=open_items.set
)[
    AccordionItem(value="faq-1")[
        AccordionTrigger()["Question 1"],
        AccordionContent()["Answer 1"]
    ],
    AccordionItem(value="faq-2")[
        AccordionTrigger()["Question 2"],
        AccordionContent()["Answer 2"]
    ],
]

# Programmatically expand all
Button(on_click=lambda: open_items.set(["faq-1", "faq-2"]))["Expand All"]
```

---

## Common Patterns

### Pattern 1: FAQ Section

```python
faqs = [
    {
        "question": "How do I create an account?",
        "answer": "Click the 'Sign Up' button in the top right corner..."
    },
    {
        "question": "What payment methods do you accept?",
        "answer": "We accept all major credit cards, PayPal, and bank transfers."
    },
    {
        "question": "How can I contact support?",
        "answer": "You can reach us at support@example.com or use the chat widget."
    },
]

Accordion(type="single", collapsible=True, class_="w-full")[
    [
        AccordionItem(value=f"faq-{i}")[
            AccordionTrigger()[faq["question"]],
            AccordionContent()[faq["answer"]]
        ]
        for i, faq in enumerate(faqs)
    ]
]
```

### Pattern 2: Settings Sections

```python
Accordion(type="multiple", default_value=["general"])[
    AccordionItem(value="general")[
        AccordionTrigger()[
            div(class_="flex items-center gap-2")[
                Icons.settings(class_="h-4 w-4"),
                "General Settings"
            ]
        ],
        AccordionContent()[
            div(class_="space-y-4")[
                # General settings form
                div()[
                    Label()["Site Name"],
                    Input(default_value="My Site")
                ],
                div()[
                    Label()["Timezone"],
                    Select()[...]
                ]
            ]
        ]
    ],
    AccordionItem(value="security")[
        AccordionTrigger()[
            div(class_="flex items-center gap-2")[
                Icons.shield(class_="h-4 w-4"),
                "Security"
            ]
        ],
        AccordionContent()[
            # Security settings
        ]
    ],
    AccordionItem(value="notifications")[
        AccordionTrigger()[
            div(class_="flex items-center gap-2")[
                Icons.bell(class_="h-4 w-4"),
                "Notifications"
            ]
        ],
        AccordionContent()[
            # Notification settings
        ]
    ]
]
```

### Pattern 3: Nested Content

```python
AccordionItem(value="item-1")[
    AccordionTrigger()["Product Features"],
    AccordionContent()[
        div(class_="space-y-4")[
            p()["Our product includes these amazing features:"],
            ul(class_="list-disc pl-6 space-y-2")[
                li()["Real-time collaboration"],
                li()["Advanced analytics"],
                li()["Custom integrations"],
            ],
            Button(variant="outline")["Learn More"]
        ]
    ]
]
```

---

## Styling Variants

### Bordered Style

```python
Accordion(class_="divide-y divide-border rounded-lg border")[
    AccordionItem(value="item-1", class_="px-4")[
        AccordionTrigger()["Section 1"],
        AccordionContent()["Content 1"]
    ],
    AccordionItem(value="item-2", class_="px-4")[
        AccordionTrigger()["Section 2"],
        AccordionContent()["Content 2"]
    ],
]
```

### Card Style

```python
div(class_="space-y-2")[
    [
        Card()[
            AccordionItem(value=f"item-{i}")[
                CardHeader(class_="p-0")[
                    AccordionTrigger(class_="px-4")["Section {i}"]
                ],
                AccordionContent(class_="px-4 pb-4")[
                    "Content for section {i}"
                ]
            ]
        ]
        for i in range(1, 4)
    ]
]
```

---

## API Reference

### Accordion

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | str | `"single"` | `"single"` or `"multiple"` |
| `collapsible` | bool | `False` | Allow all items to close |
| `value` | str/list | `None` | Controlled open item(s) |
| `default_value` | str/list | `None` | Initially open item(s) |
| `on_value_change` | callable | `None` | Called when state changes |
| `disabled` | bool | `False` | Disable all items |

### AccordionItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Unique identifier |
| `disabled` | bool | `False` | Disable this item |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **ARIA Expanded** | `aria-expanded` on trigger |
| **ARIA Controls** | Links trigger to content |
| **Keyboard** | Enter/Space to toggle |
| **Focus** | Tab through triggers |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| All items stay open | `type="multiple"` | Change to `type="single"` |
| Can't close item | `collapsible=False` | Add `collapsible=True` |
| Wrong item open | `value` mismatch | Check `value` prop matches item |
| No animation | CSS missing | Check Tailwind animate classes |

---

## Related Components

- **[Tabs](./tabs.md)** — Horizontal content switching
- **[Collapsible](./collapsible.md)** — Single collapsible section
- **[Card](./card.md)** — Often used inside accordion content


