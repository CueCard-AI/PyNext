# Sheet

> **Like a drawer that slides out from the edge — more room than a dialog**

A panel that slides in from the edge of the screen, typically for detailed content or navigation.

---

## First Principles: What IS a Sheet?

### The Core Concept

A sheet is a **sliding panel** that emerges from the screen edge:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE SHEET CONCEPT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BEFORE:                          AFTER (Sheet from right):                  │
│  ───────                          ─────────────────────────                  │
│                                                                              │
│  ┌──────────────────────┐         ┌───────────────┬────────┐                │
│  │                      │         │               │ Sheet  │                │
│  │                      │         │  Dimmed       │        │                │
│  │    Your Page         │   →     │  Background   │ Content│                │
│  │                      │         │               │ Here   │                │
│  │                      │         │               │        │                │
│  └──────────────────────┘         └───────────────┴────────┘                │
│                                                                              │
│  Sheet slides in from:                                                       │
│  • Right (default)    — Settings, details                                    │
│  • Left               — Navigation, sidebar                                  │
│  • Top                — Notifications, alerts                                │
│  • Bottom             — Mobile menus, actions                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Sheet vs Dialog

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SHEET VS DIALOG                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DIALOG:                           SHEET:                                    │
│  ───────                           ──────                                    │
│                                                                              │
│  ┌──────────────────────┐         ┌──────────────────────┐                  │
│  │    ┌──────────┐      │         │              ┌──────┐│                  │
│  │    │ DIALOG   │      │         │              │SHEET ││                  │
│  │    │  Small   │      │         │              │ More ││                  │
│  │    │  Centered│      │         │              │ Room ││                  │
│  │    └──────────┘      │         │              └──────┘│                  │
│  └──────────────────────┘         └──────────────────────┘                  │
│                                                                              │
│  Use for:                          Use for:                                  │
│  • Quick confirmations             • Complex forms                           │
│  • Simple forms                    • Detail views                            │
│  • Alerts                          • Navigation menus                        │
│  • Small content                   • Settings panels                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add sheet
```

Or import directly:

```python
from pynext.shadcn import (
    Sheet, SheetTrigger, SheetContent,
    SheetHeader, SheetTitle, SheetDescription,
    SheetFooter, SheetClose
)
```

---

## Step-by-Step Usage

### Step 1: Basic Sheet

```python
Sheet()[
    SheetTrigger()[
        Button()["Open Sheet"]
    ],
    SheetContent()[
        SheetHeader()[
            SheetTitle()["Sheet Title"],
            SheetDescription()["Sheet description goes here."]
        ],
        p()["Sheet content goes here."]
    ]
]
```

### Step 2: Different Sides

```python
# Right (default)
Sheet()[
    SheetTrigger()[Button()["Right"]],
    SheetContent(side="right")[...]
]

# Left
Sheet()[
    SheetTrigger()[Button()["Left"]],
    SheetContent(side="left")[...]
]

# Top
Sheet()[
    SheetTrigger()[Button()["Top"]],
    SheetContent(side="top")[...]
]

# Bottom
Sheet()[
    SheetTrigger()[Button()["Bottom"]],
    SheetContent(side="bottom")[...]
]
```

### Step 3: With Form

```python
from pynext import server_action

@server_action
async def update_profile(data: dict):
    await db.users.update(data["id"], name=data["name"])
    return {"success": True}

Sheet()[
    SheetTrigger()[
        Button(variant="outline")["Edit Profile"]
    ],
    SheetContent()[
        SheetHeader()[
            SheetTitle()["Edit Profile"],
            SheetDescription()[
                "Make changes to your profile here."
            ]
        ],
        form(action=update_profile, class_="space-y-4 py-4")[
            div(class_="space-y-2")[
                Label(html_for="name")["Name"],
                Input(id="name", name="name", value=user.name)
            ],
            div(class_="space-y-2")[
                Label(html_for="email")["Email"],
                Input(id="email", name="email", value=user.email)
            ],
            SheetFooter()[
                SheetClose()[
                    Button(variant="outline", type="button")["Cancel"]
                ],
                Button(type="submit")["Save"]
            ]
        ]
    ]
]
```

### Step 4: Swipe to Close (Mobile)

```python
Sheet()[
    SheetTrigger()[Button()["Open"]],
    SheetContent(
        side="bottom",
        swipe_to_close=True  # Enable swipe gesture
    )[
        # Drag indicator for mobile
        div(class_="mx-auto w-12 h-1.5 bg-muted rounded-full mb-4"),
        SheetTitle()["Mobile Menu"],
        # Content...
    ]
]
```

---

## Common Patterns

### Pattern 1: Mobile Navigation

```python
Sheet()[
    SheetTrigger()[
        Button(variant="ghost", size="icon", class_="md:hidden")[
            Icons.menu(class_="h-6 w-6")
        ]
    ],
    SheetContent(side="left", class_="w-64")[
        SheetHeader()[
            SheetTitle()["Navigation"]
        ],
        nav(class_="flex flex-col gap-2 py-4")[
            [
                a(
                    href=item.href,
                    class_="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-muted"
                )[
                    item.icon(class_="h-4 w-4"),
                    item.label
                ]
                for item in nav_items
            ]
        ]
    ]
]
```

### Pattern 2: Settings Panel

```python
Sheet()[
    SheetTrigger()[
        Button(variant="outline")[
            Icons.settings(class_="mr-2 h-4 w-4"),
            "Settings"
        ]
    ],
    SheetContent(class_="w-[400px] sm:max-w-[540px]")[
        SheetHeader()[
            SheetTitle()["Settings"],
            SheetDescription()["Configure your preferences"]
        ],
        
        Tabs(default_value="general", class_="mt-4")[
            TabsList()[
                TabsTrigger(value="general")["General"],
                TabsTrigger(value="notifications")["Notifications"],
                TabsTrigger(value="privacy")["Privacy"]
            ],
            TabsContent(value="general")[
                # General settings...
            ],
            TabsContent(value="notifications")[
                # Notification settings...
            ],
            TabsContent(value="privacy")[
                # Privacy settings...
            ]
        ]
    ]
]
```

### Pattern 3: Detail View

```python
# Click on table row to open detail sheet
Sheet()[
    SheetTrigger()[
        TableRow(class_="cursor-pointer hover:bg-muted")[
            TableCell()[order.id],
            TableCell()[order.customer],
            TableCell()[f"${order.total}"]
        ]
    ],
    SheetContent()[
        SheetHeader()[
            SheetTitle()[f"Order #{order.id}"],
            SheetDescription()[f"Placed on {order.date}"]
        ],
        
        div(class_="space-y-6 py-4")[
            # Customer info
            div()[
                h3(class_="font-medium")["Customer"],
                p(class_="text-muted-foreground")[order.customer]
            ],
            
            # Items
            div()[
                h3(class_="font-medium")["Items"],
                [
                    div(class_="flex justify-between py-2")[
                        span()[item.name],
                        span()[f"${item.price}"]
                    ]
                    for item in order.items
                ]
            ],
            
            # Total
            div(class_="flex justify-between font-medium pt-4 border-t")[
                span()["Total"],
                span()[f"${order.total}"]
            ]
        ],
        
        SheetFooter()[
            Button(variant="outline")["Print"],
            Button()["Process"]
        ]
    ]
]
```

### Pattern 4: Controlled Sheet

```python
from pynext import Signal

is_open = Signal(False)

Sheet(open=is_open.value, on_open_change=is_open.set)[
    # No trigger needed when controlled
    SheetContent()[
        SheetTitle()["Controlled Sheet"],
        p()["Opened programmatically"]
    ]
]

# Open from anywhere
Button(on_click=lambda: is_open.set(True))["Open Sheet"]
```

---

## Styling

### Custom Width

```python
# Narrow
SheetContent(class_="w-[300px]")

# Wide
SheetContent(class_="w-[600px] sm:max-w-[600px]")

# Full width (mobile)
SheetContent(class_="w-full sm:max-w-md")
```

### Custom Height (for top/bottom)

```python
SheetContent(side="bottom", class_="h-[50vh]")
```

---

## API Reference

### Sheet

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | bool | `None` | Controlled open state |
| `on_open_change` | callable | `None` | Called when state changes |

### SheetContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `side` | str | `"right"` | `"top"`, `"right"`, `"bottom"`, `"left"` |
| `swipe_to_close` | bool | `False` | Enable swipe to dismiss (mobile) |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Focus Trap** | Focus stays within sheet |
| **Escape Key** | Closes sheet |
| **ARIA** | `role="dialog"`, `aria-modal="true"` |
| **Focus Return** | Returns to trigger on close |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Sheet not closing | Missing close button | Add SheetClose or use controlled state |
| Wrong side | Default is right | Set `side` prop |
| Content cut off | Fixed width | Use responsive classes |
| No overlay click close | Nested clickable | Check event propagation |

---

## Related Components

- **[Dialog](./dialog.md)** — Centered modal for quick interactions
- **[DropdownMenu](./dropdown-menu.md)** — Quick actions menu
- **[Tabs](./tabs.md)** — Often used inside sheets
