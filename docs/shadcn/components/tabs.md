# Tabs

Organize content into switchable panels.

## When to Use

Tabs are for:
- **Settings pages** - General, Security, Notifications
- **Product details** - Description, Reviews, Specs
- **Dashboard views** - Overview, Analytics, Reports
- **Profile sections** - Posts, Comments, Likes

**Don't use tabs** when content should be visible at once, or when there are more than 5-6 options (use a dropdown or sidebar instead).

## Installation

```bash
pynext ui add tabs
```

Or use directly:

```python
from pynext.shadcn import Tabs, TabsList, TabsTrigger, TabsContent
```

## Basic Usage

```python
Tabs(default_value="account")[
    TabsList()[
        TabsTrigger(value="account")["Account"],
        TabsTrigger(value="password")["Password"],
    ],
    TabsContent(value="account")[
        p()["Make changes to your account here."]
    ],
    TabsContent(value="password")[
        p()["Change your password here."]
    ]
]
```

**How it works:** 
- `Tabs` manages which tab is active via `value`
- `TabsTrigger` is what users click
- `TabsContent` is shown when its `value` matches the active tab

## Sub-Components

| Component | Purpose |
|-----------|---------|
| `Tabs` | Container, manages active state |
| `TabsList` | Container for triggers |
| `TabsTrigger` | Clickable tab button |
| `TabsContent` | Content panel for each tab |

## Examples

### Settings Tabs

```python
Tabs(default_value="general", class_="w-full")[
    TabsList(class_="grid w-full grid-cols-3")[
        TabsTrigger(value="general")["General"],
        TabsTrigger(value="security")["Security"],
        TabsTrigger(value="notifications")["Notifications"],
    ],
    
    TabsContent(value="general")[
        Card()[
            CardHeader()[
                CardTitle()["General Settings"],
                CardDescription()["Manage your account settings."]
            ],
            CardContent(class_="space-y-4")[
                div(class_="space-y-2")[
                    Label(html_for="name")["Display Name"],
                    Input(id="name", value="John Doe")
                ],
                div(class_="space-y-2")[
                    Label(html_for="email")["Email"],
                    Input(id="email", value="john@example.com")
                ]
            ]
        ]
    ],
    
    TabsContent(value="security")[
        Card()[
            CardHeader()[
                CardTitle()["Security"],
                CardDescription()["Manage your security preferences."]
            ],
            CardContent()[
                div(class_="space-y-4")[
                    div(class_="flex items-center justify-between")[
                        span()["Two-factor authentication"],
                        Switch()
                    ]
                ]
            ]
        ]
    ],
    
    TabsContent(value="notifications")[
        Card()[
            CardHeader()[
                CardTitle()["Notifications"],
                CardDescription()["Choose what you want to be notified about."]
            ],
            CardContent()[
                # Notification settings...
            ]
        ]
    ]
]
```

### Tabs with Icons

```python
TabsList()[
    TabsTrigger(value="music")[
        span(class_="flex items-center gap-2")[
            "🎵",
            "Music"
        ]
    ],
    TabsTrigger(value="podcasts")[
        span(class_="flex items-center gap-2")[
            "🎙️",
            "Podcasts"
        ]
    ],
    TabsTrigger(value="live")[
        span(class_="flex items-center gap-2")[
            "📺",
            "Live"
        ]
    ]
]
```

### Disabled Tab

```python
TabsList()[
    TabsTrigger(value="overview")["Overview"],
    TabsTrigger(value="analytics")["Analytics"],
    TabsTrigger(value="reports", disabled=True)["Reports (Coming Soon)"],
]
```

### Vertical Tabs

```python
Tabs(default_value="account", class_="flex gap-4")[
    TabsList(class_="flex flex-col h-fit")[
        TabsTrigger(value="account")["Account"],
        TabsTrigger(value="password")["Password"],
        TabsTrigger(value="team")["Team"],
    ],
    div(class_="flex-1")[
        TabsContent(value="account")[...],
        TabsContent(value="password")[...],
        TabsContent(value="team")[...],
    ]
]
```

## Controlled Tabs

```python
from pynext import Signal

active_tab = Signal("account")

def ControlledTabs():
    return Tabs(
        value=active_tab.value,
        on_value_change=active_tab.set
    )[
        TabsList()[
            TabsTrigger(value="account")["Account"],
            TabsTrigger(value="password")["Password"],
        ],
        TabsContent(value="account")["Account content"],
        TabsContent(value="password")["Password content"]
    ]

# Switch programmatically
Button(on_click=lambda: active_tab.set("password"))["Go to Password"]
```

## Styling

### Full Width Tabs

```python
TabsList(class_="w-full")[
    TabsTrigger(value="a", class_="flex-1")["Tab A"],
    TabsTrigger(value="b", class_="flex-1")["Tab B"],
    TabsTrigger(value="c", class_="flex-1")["Tab C"],
]
```

### Pill Style

```python
TabsList(class_="bg-transparent p-0 gap-2")[
    TabsTrigger(
        value="all",
        class_="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-full"
    )["All"],
    # ...
]
```

### Underline Style

```python
TabsList(class_="bg-transparent border-b rounded-none")[
    TabsTrigger(
        value="posts",
        class_="rounded-none border-b-2 border-transparent data-[state=active]:border-primary"
    )["Posts"],
    # ...
]
```

## Props Reference

### Tabs

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `default_value` | str | `""` | Initially active tab |
| `value` | str | `None` | Controlled active tab |
| `on_value_change` | callable | `None` | Called when tab changes |
| `class_` | str | `""` | Additional CSS classes |

### TabsTrigger

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Tab identifier |
| `disabled` | bool | `False` | Disable this tab |
| `class_` | str | `""` | Additional CSS classes |

### TabsContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Matches TabsTrigger value |
| `class_` | str | `""` | Additional CSS classes |

## Accessibility

- Uses proper `role="tablist"`, `role="tab"`, and `role="tabpanel"`
- Arrow keys navigate between tabs
- Tab content is linked with `aria-controls`
- Active tab indicated with `aria-selected`
- Disabled tabs have `aria-disabled`

## Related Components

- [Card](./card.md) - Often used inside TabsContent
- [Accordion](./accordion.md) - Alternative for collapsible content

