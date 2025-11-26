# Tabs

> **Like a file cabinet with labeled folders — click a tab to see its content**

Organize content into switchable panels with a row of navigation tabs.

---

## First Principles: What ARE Tabs?

### The Core Concept

Tabs let you show **one thing at a time** from a set of related options:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE TAB METAPHOR                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Physical World:                    Digital World:                           │
│  ──────────────                     ──────────────                           │
│                                                                              │
│  ┌─────┐                            ┌──────┬──────┬──────┐                  │
│  │ A │ B │ C │   ← File dividers    │ Tab1 │ Tab2 │ Tab3 │                  │
│  └───────────┘                      └──────┴──────┴──────┘                  │
│  │           │                      ┌────────────────────┐                  │
│  │  File A   │   ← One visible      │                    │                  │
│  │  Contents │     at a time        │   Tab1 Content     │                  │
│  │           │                      │                    │                  │
│  └───────────┘                      └────────────────────┘                  │
│                                                                              │
│  Click tab → See that section's content                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Tabs Exist

Tabs solve the **"too much content for one page"** problem:

```
WITHOUT TABS:                        WITH TABS:
─────────────                        ──────────

┌──────────────────┐                 ┌──────┬────────┬──────┐
│ Account Settings │                 │ Edit │ Security│ Notif│
├──────────────────┤                 └──────┴────────┴──────┘
│ Profile          │                 ┌──────────────────────┐
│ ────────         │                 │                      │
│ Name: ...        │                 │   Edit Profile       │
│ Email: ...       │                 │   (just this section)│
│                  │                 │                      │
│ Security         │  SCROLL         └──────────────────────┘
│ ────────         │  SCROLL
│ Password: ...    │  SCROLL         ✅ Focused
│ 2FA: ...         │  SCROLL         ✅ Less overwhelming
│                  │  SCROLL         ✅ Easier to find
│ Notifications    │  SCROLL
│ ─────────────    │  SCROLL
│ Email: ...       │
│ Push: ...        │
└──────────────────┘
```

---

## How It Works

### Component Hierarchy

```
Tabs                          ← Root: manages active state
├── TabsList                  ← Container for tab buttons
│   ├── TabsTrigger(value="a") ← Button that selects tab
│   └── TabsTrigger(value="b")
├── TabsContent(value="a")    ← Content shown when "a" active
└── TabsContent(value="b")    ← Content shown when "b" active
```

### The State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TAB STATE FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Click "Tab 2"                                                               │
│      ↓                                                                       │
│  JavaScript: tabs.value = "tab2"                                             │
│      ↓                                                                       │
│  All triggers: aria-selected="false"                                         │
│  Tab 2 trigger: aria-selected="true", data-state="active"                    │
│      ↓                                                                       │
│  All content: hidden                                                         │
│  Tab 2 content: visible, data-state="active"                                 │
│      ↓                                                                       │
│  CSS shows active content via [data-state="active"]                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add tabs
```

Or import directly:

```python
from pynext.shadcn import Tabs, TabsList, TabsTrigger, TabsContent
```

---

## Step-by-Step Usage

### Step 1: Basic Tabs

```python
Tabs(default_value="account")[
    # The tab buttons
    TabsList()[
        TabsTrigger(value="account")["Account"],
        TabsTrigger(value="password")["Password"],
    ],
    
    # The content panels
    TabsContent(value="account")[
        p()["Make changes to your account here."]
    ],
    TabsContent(value="password")[
        p()["Change your password here."]
    ],
]
```

**Key points:**
- `default_value` sets which tab is active initially
- Each `TabsTrigger` has a `value` that matches its `TabsContent`
- Only one content panel is visible at a time

### Step 2: Full Example with Forms

```python
Tabs(default_value="account", class_="w-[400px]")[
    TabsList(class_="grid w-full grid-cols-2")[
        TabsTrigger(value="account")["Account"],
        TabsTrigger(value="password")["Password"],
    ],
    
    TabsContent(value="account")[
        Card()[
            CardHeader()[
                CardTitle()["Account"],
                CardDescription()["Make changes to your account."]
            ],
            CardContent(class_="space-y-2")[
                div(class_="space-y-1")[
                    Label(html_for="name")["Name"],
                    Input(id="name", default_value="John Doe")
                ],
                div(class_="space-y-1")[
                    Label(html_for="username")["Username"],
                    Input(id="username", default_value="@johndoe")
                ]
            ],
            CardFooter()[
                Button()["Save changes"]
            ]
        ]
    ],
    
    TabsContent(value="password")[
        Card()[
            CardHeader()[
                CardTitle()["Password"],
                CardDescription()["Change your password here."]
            ],
            CardContent(class_="space-y-2")[
                div(class_="space-y-1")[
                    Label(html_for="current")["Current password"],
                    Input(id="current", type="password")
                ],
                div(class_="space-y-1")[
                    Label(html_for="new")["New password"],
                    Input(id="new", type="password")
                ]
            ],
            CardFooter()[
                Button()["Save password"]
            ]
        ]
    ],
]
```

### Step 3: Controlled Tabs

Control the active tab programmatically:

```python
from pynext import Signal

active_tab = Signal("account")

Tabs(
    value=active_tab.value,
    on_value_change=active_tab.set
)[
    TabsList()[
        TabsTrigger(value="account")["Account"],
        TabsTrigger(value="password")["Password"],
    ],
    TabsContent(value="account")[...],
    TabsContent(value="password")[...],
]

# Switch programmatically
Button(on_click=lambda: active_tab.set("password"))["Go to Password"]
```

---

## Styling Variants

### Underline Style

```python
TabsList(class_="bg-transparent border-b rounded-none")[
    TabsTrigger(
        value="tab1",
        class_="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none"
    )["Tab 1"],
    TabsTrigger(
        value="tab2",
        class_="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none"
    )["Tab 2"],
]
```

### Pill Style

```python
TabsList(class_="bg-muted p-1 rounded-full")[
    TabsTrigger(value="tab1", class_="rounded-full")["Tab 1"],
    TabsTrigger(value="tab2", class_="rounded-full")["Tab 2"],
]
```

### Vertical Tabs

```python
div(class_="flex gap-4")[
    TabsList(class_="flex-col h-auto")[
        TabsTrigger(value="general")["General"],
        TabsTrigger(value="security")["Security"],
        TabsTrigger(value="billing")["Billing"],
    ],
    div(class_="flex-1")[
        TabsContent(value="general")[...],
        TabsContent(value="security")[...],
        TabsContent(value="billing")[...],
    ]
]
```

---

## API Reference

### Tabs

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `default_value` | str | `None` | Initially active tab |
| `value` | str | `None` | Controlled active tab |
| `on_value_change` | callable | `None` | Called when tab changes |
| `orientation` | str | `"horizontal"` | `"horizontal"` or `"vertical"` |

### TabsTrigger

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Unique identifier for this tab |
| `disabled` | bool | `False` | Disable this tab |

### TabsContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Matches TabsTrigger value |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **ARIA Roles** | `role="tablist"`, `role="tab"`, `role="tabpanel"` |
| **Arrow Keys** | Left/Right to navigate tabs |
| **Home/End** | Jump to first/last tab |
| **Selection** | `aria-selected="true"` on active tab |
| **Panel Link** | Tab linked to panel via `aria-controls` |

---

## Common Patterns

### Pattern 1: Dynamic Tabs

```python
tabs = [
    {"id": "tab1", "label": "First", "content": "Content 1"},
    {"id": "tab2", "label": "Second", "content": "Content 2"},
]

Tabs(default_value=tabs[0]["id"])[
    TabsList()[
        [TabsTrigger(value=t["id"])[t["label"]] for t in tabs]
    ],
    [TabsContent(value=t["id"])[p()[t["content"]]] for t in tabs]
]
```

### Pattern 2: Tabs with Icons

```python
TabsTrigger(value="music", class_="flex items-center gap-2")[
    Icons.music(class_="h-4 w-4"),
    "Music"
]
```

### Pattern 3: Tabs with Badges

```python
TabsTrigger(value="notifications")[
    "Notifications",
    Badge(class_="ml-2")["3"]
]
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Content not showing | Mismatched values | Ensure trigger and content `value` match |
| Multiple tabs active | Duplicate values | Each value must be unique |
| Keyboard nav broken | Wrong orientation | Set `orientation` prop correctly |
| Styling not applied | Missing data-state | Check CSS targets `[data-state="active"]` |

---

## Related Components

- **[Card](./card.md)** — Often used inside TabsContent
- **[Button](./button.md)** — For actions within tabs
