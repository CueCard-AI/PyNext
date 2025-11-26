# Alert Dialog

A modal dialog for confirmations requiring explicit action.

## When to Use

Alert dialogs are for:
- **Destructive actions** - Delete, remove, clear
- **Important confirmations** - Submit payment, accept terms
- **Irreversible changes** - Data loss warnings
- **Critical decisions** - Logout, cancel subscription

**Dialog vs AlertDialog:** Use AlertDialog when users MUST make a choice (no clicking outside to dismiss).

## Installation

```bash
pynext ui add alert-dialog
```

Or use directly:

```python
from pynext.shadcn import (
    AlertDialog, AlertDialogTrigger, AlertDialogContent,
    AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
    AlertDialogFooter, AlertDialogAction, AlertDialogCancel
)
```

## Basic Usage

```python
AlertDialog()[
    AlertDialogTrigger()[
        Button(variant="destructive")["Delete Account"]
    ],
    AlertDialogContent()[
        AlertDialogHeader()[
            AlertDialogTitle()["Are you absolutely sure?"],
            AlertDialogDescription()[
                "This action cannot be undone. This will permanently "
                "delete your account and remove your data."
            ]
        ],
        AlertDialogFooter()[
            AlertDialogCancel()["Cancel"],
            AlertDialogAction()["Yes, delete"]
        ]
    ]
]
```

**How it works:** AlertDialog requires explicit action (Cancel or Action button). Clicking outside or pressing Escape doesn't close it.

## Sub-Components

| Component | Purpose |
|-----------|---------|
| `AlertDialog` | Container |
| `AlertDialogTrigger` | Opens the dialog |
| `AlertDialogContent` | The modal |
| `AlertDialogHeader` | Title/description container |
| `AlertDialogTitle` | Main heading |
| `AlertDialogDescription` | Explanation text |
| `AlertDialogFooter` | Action buttons |
| `AlertDialogAction` | Confirms action |
| `AlertDialogCancel` | Dismisses dialog |

## Examples

### Delete Confirmation

```python
AlertDialog()[
    AlertDialogTrigger()[
        Button(variant="destructive", size="sm")["🗑️ Delete"]
    ],
    AlertDialogContent()[
        AlertDialogHeader()[
            AlertDialogTitle()["Delete this item?"],
            AlertDialogDescription()[
                "This will permanently delete the item. "
                "This action cannot be undone."
            ]
        ],
        AlertDialogFooter()[
            AlertDialogCancel()["Keep it"],
            AlertDialogAction(on_click=delete_item)[
                "Delete"
            ]
        ]
    ]
]
```

### Logout Confirmation

```python
AlertDialog()[
    AlertDialogTrigger()[
        DropdownMenuItem()["Log out"]
    ],
    AlertDialogContent()[
        AlertDialogHeader()[
            AlertDialogTitle()["Log out of your account?"],
            AlertDialogDescription()[
                "You'll need to sign in again to access your account."
            ]
        ],
        AlertDialogFooter()[
            AlertDialogCancel()["Stay signed in"],
            AlertDialogAction(on_click=handle_logout)[
                "Log out"
            ]
        ]
    ]
]
```

### With Warning Icon

```python
AlertDialogContent()[
    AlertDialogHeader()[
        div(class_="flex items-center gap-4")[
            span(class_="text-4xl")["⚠️"],
            div()[
                AlertDialogTitle()["Unsaved changes"],
                AlertDialogDescription()[
                    "You have unsaved changes. Do you want to save before leaving?"
                ]
            ]
        ]
    ],
    AlertDialogFooter()[
        AlertDialogCancel()["Cancel"],
        Button(variant="outline", on_click=discard)["Don't save"],
        AlertDialogAction(on_click=save)["Save changes"]
    ]
]
```

## Controlled AlertDialog

```python
from pynext import Signal

show_dialog = Signal(False)

def ControlledAlertDialog():
    return AlertDialog(
        open=show_dialog.value,
        on_open_change=show_dialog.set
    )[
        AlertDialogContent()[
            AlertDialogTitle()["Controlled Dialog"],
            AlertDialogDescription()["Opened via Signal"],
            AlertDialogFooter()[
                AlertDialogCancel()["Close"]
            ]
        ]
    ]
```

## Styling Action Buttons

```python
AlertDialogFooter()[
    AlertDialogCancel()["Cancel"],
    AlertDialogAction(class_="bg-destructive text-destructive-foreground")[
        "Delete"
    ]
]
```

## Props Reference

### AlertDialog

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | bool | `None` | Controlled open state |
| `on_open_change` | callable | `None` | Called when state changes |

### AlertDialogAction / AlertDialogCancel

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `on_click` | callable | `None` | Click handler |
| `class_` | str | `""` | Additional CSS classes |

## Accessibility

- Focus is trapped inside the dialog
- Escape key does NOT close (must click Cancel)
- Uses `role="alertdialog"` for urgency
- Screen readers announce as alert
- Focus moves to dialog on open

## Related Components

- [Dialog](./dialog.md) - For non-critical modals
- [Button](./button.md) - Trigger styling

