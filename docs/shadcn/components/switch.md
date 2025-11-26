# Switch

> **Like a light switch — flip it on or off**

A toggle control that switches between two states (on/off, enabled/disabled).

---

## First Principles: What IS a Switch?

### The Core Concept

A switch is a **binary toggle** — it's either ON or OFF:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE SWITCH CONCEPT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Real World:                       Digital:                                  │
│  ───────────                       ────────                                  │
│                                                                              │
│  Light Switch:                     Toggle Switch:                            │
│                                                                              │
│    OFF              ON               OFF              ON                     │
│   ┌────┐          ┌────┐           ┌──────┐        ┌──────┐                │
│   │    │          │ ▓▓ │           │ ○    │        │    ● │                │
│   │ ▓▓ │   →→     │    │           └──────┘   →→   └──────┘                │
│   └────┘          └────┘                                                     │
│                                                                              │
│  Click/tap to toggle state                                                   │
│  Immediately takes effect                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Switch vs Checkbox

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SWITCH VS CHECKBOX                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SWITCH:                           CHECKBOX:                                 │
│  ───────                           ─────────                                 │
│                                                                              │
│  • Binary on/off                   • Select/deselect                         │
│  • Takes effect IMMEDIATELY        • Part of a form (submit later)           │
│  • Like a light switch             • Like a checklist                        │
│  • Single option                   • Multiple options                        │
│                                                                              │
│  Use for:                          Use for:                                  │
│  • Enable/disable features         • Accept terms                            │
│  • Dark mode toggle                • Select items from list                  │
│  • Settings that apply now         • Form options                            │
│                                                                              │
│  Example:                          Example:                                  │
│  [─────○] Enable notifications     ☐ I agree to terms                       │
│                                    ☑ Send me updates                         │
│                                    ☐ Share with partners                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add switch
```

Or import directly:

```python
from pynext.shadcn import Switch, Label
```

---

## Step-by-Step Usage

### Step 1: Basic Switch

```python
Switch()
```

### Step 2: With Label

```python
div(class_="flex items-center space-x-2")[
    Switch(id="airplane-mode"),
    Label(html_for="airplane-mode")["Airplane Mode"]
]
```

### Step 3: Controlled State

```python
from pynext import Signal

enabled = Signal(False)

div(class_="flex items-center space-x-2")[
    Switch(
        id="notifications",
        checked=enabled.value,
        on_checked_change=enabled.set
    ),
    Label(html_for="notifications")[
        "Enable notifications"
    ]
]

# Show state
p()[f"Notifications are {'enabled' if enabled.value else 'disabled'}"]
```

### Step 4: With Server Action

```python
from pynext import Signal, server_action

dark_mode = Signal(False)

@server_action
async def update_theme(enabled: bool):
    await db.users.update(user_id, dark_mode=enabled)
    return {"success": True}

Switch(
    checked=dark_mode.value,
    on_checked_change=lambda v: (dark_mode.set(v), update_theme(v))
)
```

---

## Common Patterns

### Pattern 1: Settings Toggle

```python
div(class_="space-y-4")[
    div(class_="flex items-center justify-between")[
        div()[
            Label(class_="font-medium")["Email notifications"],
            p(class_="text-sm text-muted-foreground")[
                "Receive emails about activity"
            ]
        ],
        Switch(
            checked=settings.email_notifications,
            on_checked_change=lambda v: update_setting("email_notifications", v)
        )
    ],
    Separator(),
    div(class_="flex items-center justify-between")[
        div()[
            Label(class_="font-medium")["Push notifications"],
            p(class_="text-sm text-muted-foreground")[
                "Receive push notifications on your device"
            ]
        ],
        Switch(
            checked=settings.push_notifications,
            on_checked_change=lambda v: update_setting("push_notifications", v)
        )
    ]
]
```

### Pattern 2: Feature Flag

```python
div(class_="flex items-center space-x-2 p-4 border rounded-lg")[
    Switch(
        id="beta",
        checked=beta_enabled.value,
        on_checked_change=beta_enabled.set
    ),
    div()[
        Label(html_for="beta", class_="font-medium")["Beta Features"],
        p(class_="text-sm text-muted-foreground")[
            "Try new features before they're released"
        ]
    ]
]
```

### Pattern 3: Inline Toggle

```python
Table()[
    TableBody()[
        [
            TableRow()[
                TableCell()[user.name],
                TableCell()[user.email],
                TableCell()[
                    Switch(
                        checked=user.is_active,
                        on_checked_change=lambda v, u=user: toggle_user(u.id, v)
                    )
                ]
            ]
            for user in users
        ]
    ]
]
```

---

## Styling Variants

### Sizes

```python
# Small
Switch(class_="h-4 w-8")

# Default
Switch()

# Large
Switch(class_="h-7 w-14")
```

### Colors

```python
# Default (primary when on)
Switch()

# Custom color when on
Switch(class_="data-[state=checked]:bg-green-500")

# Custom thumb
Switch(class_="[&>span]:data-[state=checked]:bg-white")
```

---

## API Reference

### Switch

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `checked` | bool | `False` | Controlled state |
| `default_checked` | bool | `False` | Initial state |
| `on_checked_change` | callable | `None` | Called when state changes |
| `disabled` | bool | `False` | Disable the switch |
| `required` | bool | `False` | Required for form submission |
| `name` | str | `None` | Form field name |
| `value` | str | `"on"` | Value when checked |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Role** | `role="switch"` |
| **State** | `aria-checked="true/false"` |
| **Keyboard** | Space to toggle |
| **Label** | Always pair with `<Label>` |

```python
# Accessible switch
div(class_="flex items-center")[
    Switch(
        id="marketing",
        aria_label="Enable marketing emails"
    ),
    Label(html_for="marketing")["Marketing emails"]
]
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| State not updating | Missing controlled props | Use `checked` + `on_checked_change` |
| No visual change | CSS not loading | Check Tailwind config |
| Not clickable | `disabled=True` | Remove disabled prop |
| Label click not working | Missing `html_for` | Add matching `id` |

---

## Related Components

- **[Checkbox](./checkbox.md)** — For form selections
- **[Toggle](./toggle.md)** — Button-style toggle
- **[RadioGroup](./radio-group.md)** — Single selection from multiple
