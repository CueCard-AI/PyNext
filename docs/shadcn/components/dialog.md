# Dialog

A modal window that appears over the page content.

## When to Use

Dialogs are for:
- **Confirmations** - "Are you sure you want to delete?"
- **Forms** - Quick edit, create new item
- **Details** - Showing more information
- **Alerts** - Important messages that need attention

**Don't use dialogs** for long forms or complex flows — use a separate page instead.

## Installation

```bash
pynext ui add dialog
```

Or use directly:

```python
from pynext.shadcn import (
    Dialog, DialogTrigger, DialogContent,
    DialogHeader, DialogTitle, DialogDescription,
    DialogFooter, DialogClose
)
```

## Basic Usage

```python
Dialog()[
    DialogTrigger()[
        Button()["Open Dialog"]
    ],
    DialogContent()[
        DialogHeader()[
            DialogTitle()["Dialog Title"],
            DialogDescription()[
                "This is a description of the dialog."
            ]
        ],
        p()["Dialog content goes here."],
        DialogFooter()[
            Button(variant="outline")["Cancel"],
            Button()["Save"]
        ]
    ]
]
```

**How it works:** `Dialog` manages open/close state. `DialogTrigger` opens it, `DialogContent` is what appears. Click outside or press Escape to close.

## Sub-Components

| Component | Purpose |
|-----------|---------|
| `Dialog` | Root container, manages state |
| `DialogTrigger` | Element that opens the dialog |
| `DialogContent` | The modal itself |
| `DialogHeader` | Container for title/description |
| `DialogTitle` | Main heading |
| `DialogDescription` | Supporting text |
| `DialogFooter` | Action buttons |
| `DialogClose` | Button that closes the dialog |

## Examples

### Edit Profile

```python
Dialog()[
    DialogTrigger()[
        Button(variant="outline")["Edit Profile"]
    ],
    DialogContent(class_="sm:max-w-md")[
        DialogHeader()[
            DialogTitle()["Edit Profile"],
            DialogDescription()[
                "Make changes to your profile here."
            ]
        ],
        div(class_="space-y-4 py-4")[
            div(class_="space-y-2")[
                Label(html_for="name")["Name"],
                Input(id="name", value="John Doe")
            ],
            div(class_="space-y-2")[
                Label(html_for="email")["Email"],
                Input(id="email", value="john@example.com")
            ]
        ],
        DialogFooter()[
            DialogClose()[
                Button(variant="outline")["Cancel"]
            ],
            Button(type="submit")["Save Changes"]
        ]
    ]
]
```

### Confirmation Dialog

```python
Dialog()[
    DialogTrigger()[
        Button(variant="destructive")["Delete Account"]
    ],
    DialogContent()[
        DialogHeader()[
            DialogTitle()["Are you absolutely sure?"],
            DialogDescription()[
                "This action cannot be undone. This will permanently delete "
                "your account and remove your data from our servers."
            ]
        ],
        DialogFooter()[
            DialogClose()[
                Button(variant="outline")["Cancel"]
            ],
            Button(variant="destructive")["Yes, delete my account"]
        ]
    ]
]
```

### Dialog with Form

```python
from pynext import server_action

@server_action
async def create_item(data: dict):
    # Save to database
    return {"success": True}

Dialog()[
    DialogTrigger()[
        Button()["+ New Item"]
    ],
    DialogContent()[
        form(action=create_item)[
            DialogHeader()[
                DialogTitle()["Create New Item"],
            ],
            div(class_="space-y-4 py-4")[
                div(class_="space-y-2")[
                    Label(html_for="title")["Title"],
                    Input(id="title", name="title", required=True)
                ],
                div(class_="space-y-2")[
                    Label(html_for="description")["Description"],
                    Textarea(id="description", name="description")
                ]
            ],
            DialogFooter()[
                DialogClose()[
                    Button(variant="outline", type="button")["Cancel"]
                ],
                Button(type="submit")["Create"]
            ]
        ]
    ]
]
```

### Scrollable Content

```python
Dialog()[
    DialogTrigger()[
        Button()["View Terms"]
    ],
    DialogContent(class_="max-h-[80vh]")[
        DialogHeader()[
            DialogTitle()["Terms of Service"],
        ],
        div(class_="overflow-y-auto max-h-[60vh] py-4")[
            # Long content here
            p()["Lorem ipsum..." * 50]
        ],
        DialogFooter()[
            DialogClose()[
                Button()["I Agree"]
            ]
        ]
    ]
]
```

## Controlled Dialog

For programmatic control:

```python
from pynext import Signal

is_open = Signal(False)

def ControlledDialog():
    return Dialog(open=is_open.value, on_open_change=is_open.set)[
        # No trigger needed when controlled
        DialogContent()[
            DialogTitle()["Controlled Dialog"],
            p()["Opened via Signal"],
        ]
    ]

# Open programmatically
Button(on_click=lambda: is_open.set(True))["Open"]
```

## Styling

### Size Variants

```python
# Small
DialogContent(class_="sm:max-w-sm")

# Medium (default)
DialogContent(class_="sm:max-w-md")

# Large
DialogContent(class_="sm:max-w-lg")

# Extra large
DialogContent(class_="sm:max-w-xl")

# Full width
DialogContent(class_="sm:max-w-full mx-4")
```

### Centering

By default, dialogs are centered. For top alignment:

```python
DialogContent(class_="top-10 translate-y-0")
```

## Props Reference

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

## Accessibility

- Focus is trapped inside the dialog when open
- Escape key closes the dialog
- Clicking overlay closes the dialog
- Uses `role="dialog"` and `aria-modal="true"`
- `DialogTitle` is announced by screen readers
- `DialogDescription` provides additional context

**Important:** Always include `DialogTitle` for screen reader users, even if visually hidden:

```python
DialogTitle(class_="sr-only")["Settings Panel"]
```

## Related Components

- [AlertDialog](./alert-dialog.md) - For confirmations requiring explicit action
- [Button](./button.md) - For dialog triggers and actions
- [Sheet](./sheet.md) - Slide-out panel alternative

