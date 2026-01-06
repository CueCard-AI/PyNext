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
    issues_signal=None,
    on_status_change=None,
    on_delete=None,
) -> Element:
    """
    Render a single issue card.
    
    Args:
        issue: Dict with id, title, description, status, priority
        issues_signal: The Signal containing all issues (for direct manipulation)
        on_status_change: Callback when status changes (legacy, prefer issues_signal)
        on_delete: Callback when issue is deleted (legacy, prefer issues_signal)
    """
    # Store issue ID for use in handlers
    issue_id = issue["id"]
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
                # FUNDAMENTAL: Reactive priority updates with field mapping
                span(
                    class_="priority-icon",
                    data_pynext_field="priority",
                    data_pynext_field_map='{"low":"🟢","medium":"🟡","high":"🟠","urgent":"🔴"}',
                )[priority_icon],
                span(
                    class_="issue-title",
                    style="font-weight: 600; color: #111827;",
                    data_pynext_field="title",
                )[issue.get("title", "Untitled")],
            ],
            # Right side: status + actions
            div(style="display: flex; align-items: center; gap: 8px;")[
                # FUNDAMENTAL: Reactive status updates with field mapping
                # data_pynext_field_map defines value→label transformation
                # data_pynext_style_map defines value→style transformation
                span(
                    class_="status-badge",
                    style=f"background: {status_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;",
                    data_pynext_field="status",
                    data_pynext_field_map='{"backlog":"Backlog","todo":"Todo","in_progress":"In Progress","done":"Done","cancelled":"Cancelled"}',
                    data_pynext_style_map='{"backlog":{"background":"#6b7280"},"todo":{"background":"#3b82f6"},"in_progress":{"background":"#f59e0b"},"done":{"background":"#10b981"},"cancelled":{"background":"#ef4444"}}',
                )[status_label],
                button(
                    class_="expand-btn",
                    style="background: none; border: none; cursor: pointer; font-size: 16px; transition: transform 0.2s;",
                    onclick=lambda: expanded.set(not expanded()),
                    data_pynext_toggle_signal=f"issue_{issue['id']}_expanded",
                    data_pynext_toggle_op="truthy",
                    data_pynext_toggle_active="transform: rotate(90deg);",
                    data_pynext_toggle_inactive="transform: rotate(0deg);",
                )["▶"],
            ],
        ],
        # Expandable details section - uses toggle binding for reactive visibility
        # Initially hidden (display: none), shown when expanded signal is truthy
        div(
            class_="issue-details",
            style="margin-top: 12px; display: none;",
            data_pynext_toggle_signal=f"issue_{issue['id']}_expanded",
            data_pynext_toggle_op="truthy",
            data_pynext_toggle_active="display: block;",
            data_pynext_toggle_inactive="display: none;",
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
                        # Use declarative action pattern - runtime will handle the delete
                        data_pynext_action="delete",
                        data_pynext_action_signal="all_issues",
                        data_pynext_action_key="id",
                        data_pynext_action_value=str(issue_id),
                    )["Delete"],
                ],
            ],
        ],
    ]


@component  
def IssueCardCompact(issue: dict, draggable: bool = False, ondragstart=None) -> Element:
    """
    Compact issue card for Kanban columns.
    
    Shows just the title and priority, suitable for dense lists.
    
    Args:
        issue: Dict with id, title, priority, etc.
        draggable: Whether the card can be dragged
        ondragstart: Handler called when drag starts
    """
    priority = issue.get("priority", "medium")
    priority_icon = PRIORITY_ICONS.get(priority, "⚪")
    
    return div(
        class_="issue-card-compact",
        style="padding: 8px 12px; margin: 4px 0; background: white; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: grab;" if draggable else "padding: 8px 12px; margin: 4px 0; background: white; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: pointer;",
        draggable="true" if draggable else None,
        data_issue_id=str(issue["id"]),
        ondragstart=ondragstart,
    )[
        div(style="display: flex; align-items: center; gap: 8px;")[
            # FUNDAMENTAL: Reactive priority updates with field mapping
            span(
                class_="priority-icon",
                style="font-size: 12px;",
                data_pynext_field="priority",
                data_pynext_field_map='{"low":"🟢","medium":"🟡","high":"🟠","urgent":"🔴"}',
            )[priority_icon],
            span(
                class_="issue-title",
                style="font-size: 14px; color: #374151; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;",
                data_pynext_field="title",
            )[issue.get("title", "Untitled")],
        ],
    ]

