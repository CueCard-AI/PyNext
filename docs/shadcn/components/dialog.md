# Dialog

> **Like a popup window that demands your attention before you can continue**

A modal window that appears over the page content, blocking interaction with the underlying page until dismissed.

---

## First Principles: What IS a Dialog?

### The Core Concept

Think of a dialog like a **conversation interruption**:

```
Normal Flow:          With Dialog:
─────────────         ─────────────
You're reading   →    WAIT!
                      ┌────────────────┐
                      │ Are you sure?  │
                      │                │
                      │ [Yes]  [No]    │
                      └────────────────┘
                      Answer first...  →    Now continue
```

A dialog is a **focused interaction point** that:
1. **Interrupts** the normal flow
2. **Focuses** attention on one task
3. **Blocks** everything else until resolved
4. **Returns control** after completion

### Why Dialogs Exist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE DIALOG PROBLEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Scenario: User clicks "Delete Account"                                      │
│                                                                              │
│  WITHOUT DIALOG:                   WITH DIALOG:                              │
│  ────────────────                  ────────────                              │
│                                                                              │
│  Click "Delete"                    Click "Delete"                            │
│      ↓                                 ↓                                     │
│  Account deleted                   "Are you SURE?"                           │
│  😱 No going back!                     ↓                                     │
│                                    User confirms → Account deleted           │
│                                    User cancels  → Nothing happens           │
│                                                                              │
│  Dialog = Safety Net + Focused Decision Point                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Mental Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DIALOG MENTAL MODEL                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Your Page (Layer 0)                                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          Header                                       │   │
│  │  ┌──────────┐  ┌──────────┐                                          │   │
│  │  │  Card 1  │  │  Card 2  │   ← User was here                        │   │
│  │  └──────────┘  └──────────┘                                          │   │
│  │                                                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Overlay (Layer 1) ← Dims the page, catches clicks                          │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│                                                                              │
│  Dialog (Layer 2) ← User's attention MUST be here                            │
│          ┌─────────────────────────────────┐                                │
│          │  ⚠️ Confirm Action              │                                │
│          │                                  │                                │
│          │  Are you sure?                   │                                │
│          │                                  │                                │
│          │     [Cancel]      [Confirm]      │                                │
│          └─────────────────────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## When to Use

✅ **Use Dialogs For:**
- **Confirmations** — "Are you sure you want to delete?"
- **Quick Forms** — Edit profile, add item
- **Details** — Show more info without leaving page
- **Alerts** — Important messages requiring acknowledgment

❌ **Don't Use Dialogs For:**
- Long forms (use a separate page)
- Complex multi-step flows
- Content users might want to reference while working
- Nested dialogs (one dialog opening another)

---

## How It Works

### The Component Hierarchy

```
Dialog                      ← Root: manages open/close state
├── DialogTrigger           ← Button/link that opens
│   └── <button>Open</button>
└── DialogContent           ← The modal window
    ├── DialogHeader        ← Title area
    │   ├── DialogTitle     ← Main heading (required for a11y)
    │   └── DialogDescription ← Supporting text
    ├── <your content>      ← Forms, text, anything
    └── DialogFooter        ← Action buttons
        ├── DialogClose     ← Closes without action
        └── Button          ← Primary action
```

### The JavaScript Magic

When you click the trigger:

```
1. Click DialogTrigger
       ↓
2. JavaScript fires: dialog.setAttribute('data-state', 'open')
       ↓
3. CSS shows the dialog: [data-state="open"] { display: flex; }
       ↓
4. Focus moves INTO dialog (focus trap activates)
       ↓
5. Escape key / outside click → closes dialog
       ↓
6. Focus returns to trigger (where you started)
```

---

## Installation

```bash
pynext ui add dialog
```

Or import directly:

```python
from pynext.shadcn import (
    Dialog, DialogTrigger, DialogContent,
    DialogHeader, DialogTitle, DialogDescription,
    DialogFooter, DialogClose
)
```

---

## Step-by-Step Usage

### Step 1: Basic Dialog

The simplest possible dialog:

```python
Dialog()[
    # The button that opens the dialog
    DialogTrigger()[
        Button()["Open"]
    ],
    
    # The dialog content
    DialogContent()[
        DialogTitle()["Hello!"],
        p()["This is a basic dialog."]
    ]
]
```

**What happens:**
- `Dialog()` creates an invisible container managing state
- `DialogTrigger()` wraps a button that opens it
- `DialogContent()` is the actual modal that appears

### Step 2: Add Structure

Use the semantic sub-components:

```python
Dialog()[
    DialogTrigger()[
        Button()["Open Dialog"]
    ],
    DialogContent()[
        # Header section
        DialogHeader()[
            DialogTitle()["Dialog Title"],
            DialogDescription()[
                "This is a description of the dialog."
            ]
        ],
        
        # Main content
        p()["Your content goes here."],
        
        # Footer with buttons
        DialogFooter()[
            Button(variant="outline")["Cancel"],
            Button()["Save"]
        ]
    ]
]
```

### Step 3: Make It Interactive

Add server actions for real functionality:

```python
from pynext import server_action

@server_action
async def save_profile(data: dict):
    # Save to database
    await db.users.update(data["user_id"], name=data["name"])
    return {"success": True}

Dialog()[
    DialogTrigger()[
        Button(variant="outline")["Edit Profile"]
    ],
    DialogContent()[
        form(action=save_profile)[
            DialogHeader()[
                DialogTitle()["Edit Profile"],
            ],
            
            div(class_="space-y-4 py-4")[
                div(class_="space-y-2")[
                    Label(html_for="name")["Name"],
                    Input(id="name", name="name", value=user.name)
                ],
            ],
            
            DialogFooter()[
                DialogClose()[
                    Button(variant="outline", type="button")["Cancel"]
                ],
                Button(type="submit")["Save Changes"]
            ]
        ]
    ]
]
```

---

## Common Patterns

### Pattern 1: Confirmation Dialog

```python
Dialog()[
    DialogTrigger()[
        Button(variant="destructive")["Delete"]
    ],
    DialogContent()[
        DialogHeader()[
            DialogTitle()["Are you absolutely sure?"],
            DialogDescription()[
                "This action cannot be undone."
            ]
        ],
        DialogFooter()[
            DialogClose()[Button(variant="outline")["Cancel"]],
            Button(variant="destructive")["Yes, delete"]
        ]
    ]
]
```

### Pattern 2: Controlled Dialog (Programmatic)

Open/close from anywhere using signals:

```python
from pynext import Signal

# Create signal to control state
is_open = Signal(False)

def SettingsDialog():
    return Dialog(
        open=is_open.value, 
        on_open_change=is_open.set
    )[
        # No trigger needed when controlled externally
        DialogContent()[
            DialogTitle()["Settings"],
            p()["Your settings here..."]
        ]
    ]

# Open from anywhere
Button(on_click=lambda: is_open.set(True))["Open Settings"]
```

### Pattern 3: Scrollable Content

For long content like terms of service:

```python
Dialog()[
    DialogTrigger()[Button()["View Terms"]],
    DialogContent(class_="max-h-[80vh]")[
        DialogHeader()[
            DialogTitle()["Terms of Service"]
        ],
        # Scrollable area
        div(class_="overflow-y-auto max-h-[60vh] py-4")[
            p()["Long content here..."]
        ],
        DialogFooter()[
            DialogClose()[Button()["I Agree"]]
        ]
    ]
]
```

---

## API Reference

### Dialog

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | bool | `None` | Controlled open state |
| `on_open_change` | callable | `None` | Called when state changes |
| `default_open` | bool | `False` | Initially open |

### DialogContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |
| `close_on_overlay` | bool | `True` | Close when clicking overlay |

### DialogTitle

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Additional CSS classes |

---

## Styling

### Size Variants

```python
# Small (forms, confirmations)
DialogContent(class_="sm:max-w-sm")

# Medium (default)
DialogContent(class_="sm:max-w-md")

# Large (complex content)
DialogContent(class_="sm:max-w-lg")

# Full width (mobile-friendly)
DialogContent(class_="sm:max-w-full mx-4")
```

### Position

```python
# Top-aligned instead of centered
DialogContent(class_="top-10 translate-y-0")
```

---

## Accessibility

PyNext dialogs follow WAI-ARIA patterns automatically:

| Feature | Behavior |
|---------|----------|
| **Focus Trap** | Tab cycles within dialog only |
| **Escape to Close** | Press Escape to dismiss |
| **Click Outside** | Clicking overlay closes dialog |
| **ARIA Roles** | `role="dialog"`, `aria-modal="true"` |
| **Title Association** | Title linked via `aria-labelledby` |
| **Focus Restoration** | Returns focus to trigger on close |

**Important:** Always include `DialogTitle`, even if visually hidden:

```python
DialogTitle(class_="sr-only")["Hidden but announced"]
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Dialog doesn't open | Missing DialogTrigger | Wrap button in DialogTrigger |
| Focus escapes dialog | Tabbing outside modal | Check focus trap is working |
| No close button | Missing DialogClose | Add DialogClose or handle `on_open_change` |
| Overlay doesn't close | `close_on_overlay=False` | Remove or set to True |

---

## Related Components

- **[AlertDialog](./alert-dialog.md)** — Confirmations requiring explicit action
- **[Sheet](./sheet.md)** — Slide-out panel alternative
- **[Button](./button.md)** — For triggers and actions
- **[Input](./input.md)** — For dialog forms
