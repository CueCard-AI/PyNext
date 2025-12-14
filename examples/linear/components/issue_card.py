"""
Linear Clone - Issue Card Component

A reusable component for displaying a single issue with:
- Title and status
- Priority indicator
- Expand/collapse functionality
- Status toggle
"""

from pynext import Signal, div, span, button, component
from pynext.core.html import Element


# Status configuration
STATUS_COLORS = {
    "backlog": "#6b7280",      # Gray
    "todo": "#3b82f6",         # Blue
    "in_progress": "#f59e0b",  # Amber
    "done": "#10b981",         # Green
    "cancelled": "#ef4444",    # Red
}

STATUS_LABELS = {
    "backlog": "Backlog",
    "todo": "Todo",
    "in_progress": "In Progress",
    "done": "Done",
    "cancelled": "Cancelled",
}

PRIORITY_ICONS = {
    "urgent": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
    "none": "⚪",
}


@component
def IssueCard(
    issue: dict,
    on_status_change=None,
    on_delete=None,
) -> Element:
    """
    Render a single issue card.
    
    Args:
        issue: Dict with id, title, description, status, priority
        on_status_change: Callback when status changes
        on_delete: Callback when issue is deleted
    """
    # Local state for expand/collapse
    expanded = Signal(False, name=f"issue_{issue['id']}_expanded")
    
    status = issue.get("status", "todo")
    priority = issue.get("priority", "medium")
    status_color = STATUS_COLORS.get(status, "#6b7280")
    status_label = STATUS_LABELS.get(status, status)
    priority_icon = PRIORITY_ICONS.get(priority, "⚪")
    
    return div(
        class_="issue-card",
        style=f"border-left: 4px solid {status_color}; padding: 12px; margin: 8px 0; background: #f9fafb; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);",
        data_issue_id=str(issue["id"]),
    )[
        # Header row
        div(
            class_="issue-header",
            style="display: flex; align-items: center; justify-content: space-between;",
        )[
            # Left side: priority + title
            div(style="display: flex; align-items: center; gap: 8px;")[
                span(class_="priority-icon")[priority_icon],
                span(
                    class_="issue-title",
                    style="font-weight: 600; color: #111827;",
                )[issue.get("title", "Untitled")],
            ],
            # Right side: status + actions
            div(style="display: flex; align-items: center; gap: 8px;")[
                span(
                    class_="status-badge",
                    style=f"background: {status_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;",
                )[status_label],
                button(
                    class_="expand-btn",
                    style="background: none; border: none; cursor: pointer; font-size: 16px;",
                    onclick=lambda: expanded.set(not expanded()),
                )["▼" if not expanded() else "▲"],
            ],
        ],
        # Expandable details section
        div(
            class_="issue-details",
            style=f"margin-top: {'12px' if expanded() else '0'}; overflow: hidden; max-height: {'200px' if expanded() else '0'}; transition: max-height 0.3s;",
        )[
            div(style="padding-top: 8px; border-top: 1px solid #e5e7eb;")[
                # Description
                div(style="color: #6b7280; margin-bottom: 12px;")[
                    issue.get("description", "No description provided.")
                ],
                # Actions
                div(style="display: flex; gap: 8px;")[
                    button(
                        class_="action-btn",
                        style="padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer;",
                        onclick=lambda: on_status_change(issue["id"], "todo") if on_status_change else None,
                    )["→ Todo"],
                    button(
                        class_="action-btn",
                        style="padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer;",
                        onclick=lambda: on_status_change(issue["id"], "in_progress") if on_status_change else None,
                    )["→ In Progress"],
                    button(
                        class_="action-btn",
                        style="padding: 4px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer;",
                        onclick=lambda: on_status_change(issue["id"], "done") if on_status_change else None,
                    )["→ Done"],
                    button(
                        class_="delete-btn",
                        style="padding: 4px 12px; border: 1px solid #ef4444; border-radius: 4px; background: #fef2f2; color: #ef4444; cursor: pointer; margin-left: auto;",
                        onclick=lambda: on_delete(issue["id"]) if on_delete else None,
                    )["Delete"],
                ],
            ],
        ] if expanded() else "",
    ]


@component  
def IssueCardCompact(issue: dict) -> Element:
    """
    Compact issue card for Kanban columns.
    
    Shows just the title and priority, suitable for dense lists.
    """
    status = issue.get("status", "todo")
    priority = issue.get("priority", "medium")
    priority_icon = PRIORITY_ICONS.get(priority, "⚪")
    
    return div(
        class_="issue-card-compact",
        style="padding: 8px 12px; margin: 4px 0; background: white; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: pointer;",
        draggable="true",
        data_issue_id=str(issue["id"]),
    )[
        div(style="display: flex; align-items: center; gap: 8px;")[
            span(class_="priority-icon", style="font-size: 12px;")[priority_icon],
            span(
                class_="issue-title",
                style="font-size: 14px; color: #374151; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;",
            )[issue.get("title", "Untitled")],
        ],
    ]

