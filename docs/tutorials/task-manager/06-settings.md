# Part 6: Project Settings & Team

> **Build settings pages for projects, labels, and team management**

In this part, we'll create settings pages with tabbed interfaces, CRUD operations for labels, and team member management.

---

## What We're Building

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Settings                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [General]  [Team]  [Labels]  [Danger Zone]                         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  Team Members                                     [+ Invite Member] │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  ┌───────────────────────────────────────────────────────────────┐ │   │
│  │  │ 👤 Jane Smith                                                 │ │   │
│  │  │    jane@example.com                              [Admin ▼]    │ │   │
│  │  └───────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  ┌───────────────────────────────────────────────────────────────┐ │   │
│  │  │ 👤 John Doe                                                   │ │   │
│  │  │    john@example.com                              [Member ▼]   │ │   │
│  │  └───────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  ┌───────────────────────────────────────────────────────────────┐ │   │
│  │  │ 👤 Alice Johnson                                              │ │   │
│  │  │    alice@example.com                             [Member ▼]   │ │   │
│  │  └───────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create the Settings Layout

Create `pages/settings/layout.py`:

```python
"""
Settings Layout

Wraps all settings pages with navigation tabs.
"""

from pynext import layout, div, h1
from pynext.tw import tw, cn
from pynext.shadcn import Tabs, TabsList, TabsTrigger


@layout
def settings_layout(children):
    """Layout for settings pages with tab navigation."""
    return div(class_=tw.p_8.max_w_4xl.mx_auto)[
        # Header
        h1(class_=tw.text_2xl.font_bold.mb_6)["Settings"],
        
        # Tab navigation
        div(class_="mb-6")[
            SettingsTabs(),
        ],
        
        # Page content
        div()[
            children
        ],
    ]


def SettingsTabs():
    """Tab navigation for settings sections."""
    # Get current path to highlight active tab
    # In a real app, you'd get this from the request
    current_path = "/settings"
    
    tabs = [
        ("/settings", "General"),
        ("/settings/team", "Team"),
        ("/settings/labels", "Labels"),
        ("/settings/danger", "Danger Zone"),
    ]
    
    return nav(class_="flex border-b border-border")[
        [
            a(
                href=path,
                class_=cn(
                    "px-4 py-2 text-sm font-medium transition-colors",
                    "border-b-2 -mb-px",
                    "border-primary text-foreground" if path == current_path 
                    else "border-transparent text-muted-foreground hover:text-foreground",
                ),
            )[label]
            for path, label in tabs
        ]
    ]
```

---

## Step 2: Create the General Settings Page

Create `pages/settings/index.py`:

```python
"""
General Settings Page

Basic workspace settings like name and preferences.
"""

from pynext import page, server_action, div, h2, p, form
from pynext.tw import tw, cn
from pynext.shadcn import (
    Button, Input, Label, Textarea,
    Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
    Switch, Separator,
)


@server_action
async def save_settings(data: dict):
    """Save general settings."""
    # In a real app, save to database
    return {"success": True, "message": "Settings saved"}


@page(title="Settings - PyTask")
def general_settings():
    """General settings page."""
    return div(class_="space-y-6")[
        # Workspace settings
        Card()[
            CardHeader()[
                CardTitle()["Workspace"],
                CardDescription()[
                    "Manage your workspace settings and preferences."
                ],
            ],
            CardContent()[
                form(action=save_settings, class_="space-y-4")[
                    div(class_="space-y-2")[
                        Label(html_for="workspace-name")["Workspace Name"],
                        Input(
                            id="workspace-name",
                            name="name",
                            value="My Workspace",
                            placeholder="Enter workspace name",
                        ),
                    ],
                    div(class_="space-y-2")[
                        Label(html_for="workspace-desc")["Description"],
                        Textarea(
                            id="workspace-desc",
                            name="description",
                            placeholder="Describe your workspace...",
                            rows=3,
                        ),
                    ],
                    Button(type="submit")["Save Changes"],
                ],
            ],
        ],
        
        # Preferences
        Card()[
            CardHeader()[
                CardTitle()["Preferences"],
                CardDescription()[
                    "Customize your experience."
                ],
            ],
            CardContent(class_="space-y-4")[
                PreferenceToggle(
                    title="Email Notifications",
                    description="Receive email updates about task changes.",
                    name="email_notifications",
                    default=True,
                ),
                Separator(),
                PreferenceToggle(
                    title="Desktop Notifications",
                    description="Show desktop notifications for mentions.",
                    name="desktop_notifications",
                    default=False,
                ),
                Separator(),
                PreferenceToggle(
                    title="Weekly Digest",
                    description="Receive a weekly summary of activity.",
                    name="weekly_digest",
                    default=True,
                ),
            ],
        ],
    ]


def PreferenceToggle(title: str, description: str, name: str, default: bool = False):
    """A toggle preference with label and description."""
    return div(class_="flex items-center justify-between")[
        div()[
            div(class_="font-medium")[title],
            p(class_="text-sm text-muted-foreground")[description],
        ],
        Switch(name=name, default_checked=default),
    ]
```

---

## Step 3: Create the Team Settings Page

Create `pages/settings/team.py`:

```python
"""
Team Settings Page

Manage team members and their roles.
"""

from pynext import page, server_action, div, h2, p, form
from pynext.tw import tw, cn
from pynext.shadcn import (
    Button, Input, Label,
    Card, CardHeader, CardTitle, CardDescription, CardContent,
    Avatar, AvatarFallback, Badge,
    Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter,
    DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem,
    AlertDialog, AlertDialogTrigger, AlertDialogContent,
    AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
    AlertDialogFooter, AlertDialogAction, AlertDialogCancel,
)

from db.queries import get_users


@server_action
async def invite_member(email: str):
    """Send an invitation to a new team member."""
    if not email or "@" not in email:
        return {"success": False, "error": "Invalid email"}
    # In a real app, send invitation email
    return {"success": True, "message": f"Invitation sent to {email}"}


@server_action
async def update_role(user_id: int, role: str):
    """Update a team member's role."""
    # In a real app, update database
    return {"success": True}


@server_action
async def remove_member(user_id: int):
    """Remove a team member."""
    # In a real app, remove from team
    return {"success": True}


@page(title="Team Settings - PyTask")
def team_settings():
    """Team management page."""
    users = get_users()
    
    return div(class_="space-y-6")[
        Card()[
            CardHeader(class_="flex flex-row items-center justify-between")[
                div()[
                    CardTitle()["Team Members"],
                    CardDescription()[
                        f"{len(users)} members in your workspace"
                    ],
                ],
                InviteMemberButton(),
            ],
            CardContent(class_="space-y-4")[
                [TeamMemberRow(user, i == 0) for i, user in enumerate(users)]
            ],
        ],
        
        # Pending invitations
        Card()[
            CardHeader()[
                CardTitle(class_="text-lg")["Pending Invitations"],
            ],
            CardContent()[
                p(class_="text-sm text-muted-foreground text-center py-4")[
                    "No pending invitations"
                ],
            ],
        ],
    ]


def TeamMemberRow(user, is_admin: bool = False):
    """A row showing a team member."""
    return div(class_=cn(
        "flex items-center justify-between p-4 rounded-lg",
        "border border-border",
    ))[
        div(class_="flex items-center gap-3")[
            Avatar(class_="h-10 w-10")[
                AvatarFallback()[user.initials]
            ],
            div()[
                div(class_="font-medium")[user.name],
                div(class_="text-sm text-muted-foreground")[user.email],
            ],
        ],
        div(class_="flex items-center gap-2")[
            RoleDropdown(user, is_admin),
            not is_admin and RemoveMemberButton(user),
        ],
    ]


def RoleDropdown(user, is_admin: bool):
    """Dropdown to change member role."""
    current_role = "Admin" if is_admin else "Member"
    
    return DropdownMenu()[
        DropdownMenuTrigger()[
            Button(variant="outline", size="sm")[
                current_role, " ▼"
            ],
        ],
        DropdownMenuContent(align="end")[
            DropdownMenuItem(
                on_click=lambda: update_role(user.id, "admin"),
                disabled=is_admin,
            )["Admin"],
            DropdownMenuItem(
                on_click=lambda: update_role(user.id, "member"),
                disabled=not is_admin,
            )["Member"],
            DropdownMenuItem(
                on_click=lambda: update_role(user.id, "viewer"),
            )["Viewer"],
        ],
    ]


def RemoveMemberButton(user):
    """Button to remove a team member."""
    return AlertDialog()[
        AlertDialogTrigger()[
            Button(variant="ghost", size="icon", class_="text-muted-foreground")[
                "×"
            ],
        ],
        AlertDialogContent()[
            AlertDialogHeader()[
                AlertDialogTitle()[f"Remove {user.name}?"],
                AlertDialogDescription()[
                    "They will lose access to this workspace. "
                    "You can invite them again later."
                ],
            ],
            AlertDialogFooter()[
                AlertDialogCancel()["Cancel"],
                AlertDialogAction(
                    on_click=lambda: remove_member(user.id),
                    class_="bg-destructive",
                )["Remove"],
            ],
        ],
    ]


def InviteMemberButton():
    """Button that opens invite dialog."""
    return Dialog()[
        DialogTrigger()[
            Button()["+ Invite Member"],
        ],
        DialogContent(class_="sm:max-w-md")[
            DialogHeader()[
                DialogTitle()["Invite Team Member"],
            ],
            form(action=lambda d: invite_member(d.get("email", "")), class_="space-y-4")[
                div(class_="space-y-2")[
                    Label(html_for="invite-email")["Email Address"],
                    Input(
                        id="invite-email",
                        name="email",
                        type="email",
                        placeholder="colleague@company.com",
                        required=True,
                    ),
                ],
                DialogFooter()[
                    Button(type="submit")["Send Invitation"],
                ],
            ],
        ],
    ]
```

---

## Step 4: Create the Labels Settings Page

Create `pages/settings/labels.py`:

```python
"""
Labels Settings Page

Manage labels for categorizing tasks.
"""

from pynext import page, server_action, div, span, form
from pynext.tw import tw, cn
from pynext.shadcn import (
    Button, Input, Label as FormLabel,
    Card, CardHeader, CardTitle, CardDescription, CardContent,
    Badge,
    Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter,
    AlertDialog, AlertDialogTrigger, AlertDialogContent,
    AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
    AlertDialogFooter, AlertDialogAction, AlertDialogCancel,
)

from db.queries import get_labels, create_label
from db import get_db


LABEL_COLORS = [
    ("red", "Red", "bg-red-500"),
    ("orange", "Orange", "bg-orange-500"),
    ("yellow", "Yellow", "bg-yellow-500"),
    ("green", "Green", "bg-green-500"),
    ("blue", "Blue", "bg-blue-500"),
    ("purple", "Purple", "bg-purple-500"),
    ("pink", "Pink", "bg-pink-500"),
    ("gray", "Gray", "bg-gray-500"),
]


@server_action
async def add_label(name: str, color: str):
    """Create a new label."""
    if not name or not name.strip():
        return {"success": False, "error": "Name is required"}
    
    create_label(name.strip(), color)
    return {"success": True, "message": "Label created"}


@server_action
async def delete_label(label_id: int):
    """Delete a label."""
    with get_db() as db:
        # Remove label from tasks first
        db.execute("UPDATE tasks SET label_id = NULL WHERE label_id = ?", (label_id,))
        db.execute("DELETE FROM labels WHERE id = ?", (label_id,))
    return {"success": True}


@page(title="Labels - PyTask")
def labels_settings():
    """Labels management page."""
    labels = get_labels()
    
    return div(class_="space-y-6")[
        Card()[
            CardHeader(class_="flex flex-row items-center justify-between")[
                div()[
                    CardTitle()["Labels"],
                    CardDescription()[
                        "Create and manage labels for organizing tasks."
                    ],
                ],
                CreateLabelButton(),
            ],
            CardContent()[
                labels and div(class_="space-y-2")[
                    [LabelRow(label) for label in labels]
                ] or EmptyLabels(),
            ],
        ],
    ]


def LabelRow(label):
    """A row showing a label with edit/delete options."""
    color_class = f"bg-{label.color}-500"
    
    return div(class_=cn(
        "flex items-center justify-between p-3 rounded-lg",
        "border border-border",
    ))[
        div(class_="flex items-center gap-3")[
            span(class_=cn("w-4 h-4 rounded-full", color_class)),
            span(class_="font-medium")[label.name],
        ],
        div(class_="flex items-center gap-2")[
            Button(variant="ghost", size="sm")["Edit"],
            DeleteLabelButton(label),
        ],
    ]


def DeleteLabelButton(label):
    """Button to delete a label with confirmation."""
    return AlertDialog()[
        AlertDialogTrigger()[
            Button(variant="ghost", size="sm", class_="text-destructive")[
                "Delete"
            ],
        ],
        AlertDialogContent()[
            AlertDialogHeader()[
                AlertDialogTitle()[f'Delete "{label.name}"?'],
                AlertDialogDescription()[
                    "Tasks with this label will be updated to have no label. "
                    "This action cannot be undone."
                ],
            ],
            AlertDialogFooter()[
                AlertDialogCancel()["Cancel"],
                AlertDialogAction(
                    on_click=lambda: delete_label(label.id),
                    class_="bg-destructive",
                )["Delete"],
            ],
        ],
    ]


def CreateLabelButton():
    """Button that opens create label dialog."""
    return Dialog()[
        DialogTrigger()[
            Button()["+ New Label"],
        ],
        DialogContent(class_="sm:max-w-md")[
            DialogHeader()[
                DialogTitle()["Create Label"],
            ],
            form(action=lambda d: add_label(d.get("name", ""), d.get("color", "gray")), class_="space-y-4")[
                div(class_="space-y-2")[
                    FormLabel(html_for="label-name")["Name"],
                    Input(
                        id="label-name",
                        name="name",
                        placeholder="e.g., Bug, Feature, Docs",
                        required=True,
                    ),
                ],
                div(class_="space-y-2")[
                    FormLabel()["Color"],
                    ColorPicker(),
                ],
                DialogFooter()[
                    Button(type="submit")["Create Label"],
                ],
            ],
        ],
    ]


def ColorPicker():
    """Grid of color options for labels."""
    return div(class_="grid grid-cols-4 gap-2")[
        [
            label(class_="cursor-pointer")[
                input(
                    type="radio",
                    name="color",
                    value=value,
                    class_="sr-only peer",
                    checked=value == "gray",
                ),
                span(class_=cn(
                    "block w-8 h-8 rounded-full",
                    color_class,
                    "ring-2 ring-transparent",
                    "peer-checked:ring-offset-2 peer-checked:ring-primary",
                )),
            ]
            for value, name, color_class in LABEL_COLORS
        ]
    ]


def EmptyLabels():
    """Empty state for no labels."""
    return div(class_="text-center py-8 text-muted-foreground")[
        span(class_="text-3xl block mb-2")["🏷️"],
        span(class_="text-sm")[
            "No labels yet. Create one to organize your tasks."
        ],
    ]
```

---

## Step 5: Test the Settings Pages

1. Start the dev server:
   ```bash
   pynext dev
   ```

2. Navigate to `/settings`

3. Test each tab:
   - **General**: Save workspace settings
   - **Team**: View members, change roles
   - **Labels**: Create and delete labels

---

## What We Built

In this part, we:

- Created a settings layout with tab navigation
- Built a general settings page with preferences
- Made a team management page with roles
- Created a label management page with color picker
- Implemented CRUD operations for labels

### Component Summary

| Component | Purpose |
|-----------|---------|
| `SettingsTabs` | Tab navigation for settings |
| `PreferenceToggle` | Toggle with description |
| `TeamMemberRow` | Team member with role dropdown |
| `LabelRow` | Label with edit/delete |
| `ColorPicker` | Color selection for labels |

### Key Patterns Learned

| Pattern | Example |
|---------|---------|
| **Nested Layouts** | Settings layout wraps settings pages |
| **Tab Navigation** | Manual tab links with active state |
| **Role Management** | Dropdown for changing roles |
| **Color Picker** | Radio buttons styled as color swatches |

---

## Next Up

In **Part 7**, we'll add global search with a command palette and keyboard shortcuts.

[**Continue to Part 7: Search & Shortcuts →**](./07-search-shortcuts.md)

