"""
Issue Card Component (Shadcn Version)

A clean, Pythonic issue card built with shadcn components.
Compare this to the original linear/components/issue_card.py - 
no inline styles, no CSS knowledge required.

Usage:
    IssueCard(issue={"id": 1, "title": "Fix bug", "status": "todo", "priority": "high"}, all_issues=my_signal)
"""

from typing import Optional, Any
from pynext.reactive import Signal
from pynext.core import component
from pynext.core.html import Element

# Shadcn primitives
from pynext.shadcn import (
    Card, CardContent,
    Button,
    Row, Column, Text, Heading,
)

# Domain components (our custom ones)
from .status_badge import StatusBadge
from .priority_icon import PriorityIcon


@component
def IssueCard(
    issue: dict,
    all_issues: Optional[Signal] = None,
) -> Element:
    """
    Render a single issue card.
    
    Look how clean this is compared to the original!
    No inline styles, no CSS knowledge required.
    
    Args:
        issue: Dict with id, title, description, status, priority
        all_issues: Signal containing the list of all issues (for delete/status operations)
    
    Example:
        IssueCard(
            issue={"id": 1, "title": "Fix login bug", "status": "todo", "priority": "high"},
            all_issues=my_issues_signal
        )
    """
    issue_id = issue["id"]
    expanded = Signal(False, name=f"issue_{issue_id}_expanded")
    
    status = issue.get("status", "todo")
    priority = issue.get("priority", "medium")
    description = issue.get("description", "No description provided.")
    
    # Status color for left border accent
    STATUS_COLORS = {
        "backlog": "#6b7280",
        "todo": "#3b82f6",
        "in_progress": "#f59e0b",
        "done": "#10b981",
        "cancelled": "#ef4444",
    }
    border_color = STATUS_COLORS.get(status, "#6b7280")
    
    return Card(class_=f"border-l-4 my-2", style=f"border-left-color: {border_color};")[
        CardContent(class_="p-3")[
            # Main row: priority + title | status + expand button
            Row(gap="sm", justify="between", align="center")[
                # Left side: priority icon + title
                Row(gap="sm", align="center")[
                    PriorityIcon(priority, data_pynext_field="priority"),
                    Text(
                        issue.get("title", "Untitled"),
                        weight="semibold",
                        data_pynext_field="title",  # Enable reactive updates for For items
                    ),
                ],
                # Right side: status badge + expand button
                Row(gap="sm", align="center")[
                    StatusBadge(status, data_pynext_field="status"),
                    Button(
                        variant="ghost",
                        size="icon",
                        on_click=lambda: expanded.set(not expanded()),
                        class_="h-8 w-8 transition-transform",
                        data_pynext_toggle_signal=f"issue_{issue_id}_expanded",
                        data_pynext_toggle_op="truthy",
                        data_pynext_toggle_active="transform: rotate(90deg);",
                        data_pynext_toggle_inactive="transform: rotate(0deg);",
                    )["▶"],
                ],
            ],
            # Expandable details section
            Column(
                gap="md",
                class_="mt-3 pt-3 border-t",
                # Toggle visibility based on expanded signal
                data_pynext_toggle_signal=f"issue_{issue_id}_expanded",
                data_pynext_toggle_op="truthy",
                data_pynext_toggle_active="display: flex;",
                data_pynext_toggle_inactive="display: none;",
                style="display: none;",  # Initial state
            )[
                # Description - with data_pynext_field for reactive For updates
                Text(description, color="muted", size="sm", data_pynext_field="description"),
                # Action buttons - inline signal operations for proper transpilation
                # Note: all_issues must always be provided for these handlers to work
                Row(gap="sm", wrap=True)[
                    Button(
                        variant="outline",
                        size="sm",
                        on_click=lambda: all_issues.set([{**i, "status": "todo"} if i["id"] == issue_id else i for i in all_issues()]),
                    )["→ Todo"],
                    Button(
                        variant="outline",
                        size="sm",
                        on_click=lambda: all_issues.set([{**i, "status": "in_progress"} if i["id"] == issue_id else i for i in all_issues()]),
                    )["→ In Progress"],
                    Button(
                        variant="outline",
                        size="sm",
                        on_click=lambda: all_issues.set([{**i, "status": "done"} if i["id"] == issue_id else i for i in all_issues()]),
                    )["→ Done"],
                    # Spacer pushes delete to the right
                    Button(
                        variant="destructive",
                        size="sm",
                        on_click=lambda: all_issues.set([i for i in all_issues() if i["id"] != issue_id]),
                        class_="ml-auto",
                    )["Delete"],
                ],
            ],
        ],
    ]


