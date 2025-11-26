# AlertDialog

> **Like a bouncer at the door — "Are you SURE you want to do this?"**

A modal dialog that requires explicit user confirmation before proceeding.

---

## First Principles: What IS an AlertDialog?

### The Core Concept

An AlertDialog is a **blocking confirmation** that requires a conscious decision:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE ALERTDIALOG CONCEPT                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User clicks "Delete Account"                                                │
│       ↓                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░┌──────────────────────────────────────┐░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░│  ⚠️ Are you absolutely sure?         │░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░│                                      │░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░│  This action cannot be undone.       │░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░│  This will permanently delete your   │░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░│  account and all associated data.    │░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░│                                      │░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░│        [Cancel]    [Delete]          │░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░└──────────────────────────────────────┘░░░░░░░░░░░░░░░░░ │    │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  KEY DIFFERENCE FROM DIALOG:                                                 │
│  • Clicking overlay does NOT close (must choose Cancel or Action)            │
│  • More urgent/warning styling                                               │
│  • For destructive/irreversible actions                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AlertDialog vs Dialog

```
DIALOG:                             ALERTDIALOG:
───────                             ────────────
• General purpose                   • Confirmations only
• Overlay click closes              • Overlay click does NOT close
• Escape key closes                 • Escape key closes
• Can be dismissed                  • Must make a choice
• For forms, content                • For "are you sure?"
```

---

## Installation

```bash
pynext ui add alert-dialog
```

Or import directly:

```python
from pynext.shadcn import (
    AlertDialog, AlertDialogTrigger, AlertDialogContent,
    AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
    AlertDialogFooter, AlertDialogCancel, AlertDialogAction
)
```

---

## Step-by-Step Usage

### Step 1: Basic Confirmation

```python
AlertDialog()[
    AlertDialogTrigger()[
        Button(variant="destructive")["Delete"]
    ],
    AlertDialogContent()[
        AlertDialogHeader()[
            AlertDialogTitle()["Are you sure?"],
            AlertDialogDescription()[
                "This action cannot be undone."
            ]
        ],
        AlertDialogFooter()[
            AlertDialogCancel()["Cancel"],
            AlertDialogAction()["Continue"]
        ]
    ]
]
```

### Step 2: With Server Action

```python
from pynext import server_action

@server_action
async def delete_account(user_id: str):
    await db.users.delete(user_id)
    redirect("/goodbye")

AlertDialog()[
    AlertDialogTrigger()[
        Button(variant="destructive")["Delete Account"]
    ],
    AlertDialogContent()[
        AlertDialogHeader()[
            AlertDialogTitle()["Delete your account?"],
            AlertDialogDescription()[
                "This will permanently delete your account and all data. "
                "This action cannot be undone."
            ]
        ],
        AlertDialogFooter()[
            AlertDialogCancel()["Cancel"],
            AlertDialogAction(
                on_click=lambda: delete_account(user.id),
                class_="bg-red-600 hover:bg-red-700"
            )["Yes, delete my account"]
        ]
    ]
]
```

---

## Common Patterns

### Pattern 1: Dangerous Action Confirmation

```python
AlertDialog()[
    AlertDialogTrigger()[
        Button(variant="outline", class_="text-red-600")[
            Icons.trash(class_="mr-2 h-4 w-4"),
            "Delete All Data"
        ]
    ],
    AlertDialogContent()[
        AlertDialogHeader()[
            AlertDialogTitle()[
                Icons.alert_triangle(class_="h-5 w-5 text-red-500 inline mr-2"),
                "Delete All Data?"
            ],
            AlertDialogDescription(class_="space-y-2")[
                p()["This will permanently delete:"],
                ul(class_="list-disc pl-4")[
                    li()["All your projects"],
                    li()["All files and assets"],
                    li()["All team memberships"],
                ],
                p(class_="font-medium text-red-600")[
                    "This action cannot be undone."
                ]
            ]
        ],
        AlertDialogFooter()[
            AlertDialogCancel()["Keep my data"],
            AlertDialogAction(class_="bg-red-600")["Delete everything"]
        ]
    ]
]
```

### Pattern 2: Save Changes Before Leaving

```python
AlertDialog(open=has_unsaved_changes.value)[
    AlertDialogContent()[
        AlertDialogHeader()[
            AlertDialogTitle()["Unsaved Changes"],
            AlertDialogDescription()[
                "You have unsaved changes. Do you want to save them before leaving?"
            ]
        ],
        AlertDialogFooter()[
            AlertDialogCancel(on_click=discard_and_leave)["Discard"],
            AlertDialogAction(on_click=save_and_leave)["Save Changes"]
        ]
    ]
]
```

---

## API Reference

### AlertDialogAction

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `on_click` | callable | `None` | Action to perform on click |

### AlertDialogCancel

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `on_click` | callable | `None` | Optional cancel handler |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Role** | `role="alertdialog"` |
| **Focus Trap** | Focus stays within dialog |
| **Escape** | Closes dialog (acts as Cancel) |
| **Initial Focus** | Cancel button by default |

---

## Troubleshooting

### AlertDialog doesn't close after action

**Problem:** User clicks the action button but the dialog stays open.

**Cause:** The action button must trigger closing. Unlike Dialog, AlertDialog is designed to require explicit action.

**Solution:**

```python
AlertDialogAction(
    on_click=lambda: (
        perform_action(),
        dialog_open.set(False)  # Explicitly close
    )
)["Delete"]
```

### Cancel button doesn't close dialog

**Problem:** Clicking Cancel does nothing.

**Solution:** Ensure `dialog_open` signal is passed correctly:

```python
# Create signal to control state
dialog_open = Signal(False)

AlertDialog(open=dialog_open)[
    AlertDialogTrigger()[...],
    AlertDialogContent()[
        AlertDialogCancel(on_click=lambda: dialog_open.set(False))["Cancel"],
        ...
    ]
]
```

### Focus goes behind dialog

**Problem:** Tab key moves focus to elements behind the dialog.

**Solution:** Make sure you're using `AlertDialogContent`, not a plain `div`. The component includes built-in focus trapping.

### Dialog opens immediately on page load

**Problem:** AlertDialog shows as soon as page renders.

**Cause:** Signal initialized to `True`.

**Solution:**

```python
# Wrong - opens immediately
dialog_open = Signal(True)

# Correct - starts closed
dialog_open = Signal(False)
```

---

## Related Components

- **[Dialog](./dialog.md)** — For general modals
- **[Button](./button.md)** — For trigger elements
