"""
Linear Clone - Issues Page

Demonstrates PyNext hydration with:
- Server-rendered issue list
- Client-side filtering by status
- Add/remove issues with forms
- Kanban board layout
- Full reactivity after hydration
- Form validation with create_form()
"""

from pynext import page, Signal, Store, div, span, button, input_, h1, h2, memo, self_only
from pynext.core.component import component
from pynext.core.html import Element, label, textarea, select, option, form as form_
from pynext.reactive.control_flow import Show, For
from pynext.reactive.forms import create_form
from pynext.reactive.validators import required, max_length

# Import components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from components.issue_card import IssueCard, IssueCardCompact, STATUS_LABELS


# Sample data
INITIAL_ISSUES = [
    {"id": 1, "title": "Implement user authentication", "description": "Add login/signup flow with OAuth support", "status": "in_progress", "priority": "high"},
    {"id": 2, "title": "Fix navigation bug on mobile", "description": "Menu doesn't close after selecting item", "status": "todo", "priority": "medium"},
    {"id": 3, "title": "Add dark mode support", "description": "Implement system-aware dark mode with toggle", "status": "backlog", "priority": "low"},
    {"id": 4, "title": "Performance optimization", "description": "Reduce bundle size and improve LCP", "status": "done", "priority": "high"},
    {"id": 5, "title": "Write API documentation", "description": "Document all REST endpoints with examples", "status": "todo", "priority": "medium"},
    {"id": 6, "title": "Set up CI/CD pipeline", "description": "GitHub Actions for testing and deployment", "status": "done", "priority": "urgent"},
]


@page(title="Issues - Linear Clone", hydration="full")
def issues():
    """
    Main issues page with filtering and Kanban view.
    
    This page demonstrates:
    1. Signal-based state management
    2. Memo for derived/filtered data
    3. Server-side rendering with hydration
    4. Event handlers that become interactive on client
    """
    
    # ==========================================================================
    # STATE
    # ==========================================================================
    
    # All issues stored in a signal
    all_issues = Signal(INITIAL_ISSUES.copy(), name="all_issues")
    
    # Current filter (all, backlog, todo, in_progress, done)
    filter_status = Signal("all", name="filter_status")
    
    # View mode (list or kanban)
    view_mode = Signal("list", name="view_mode")
    
    # Show/hide modal state
    show_add_form = Signal(False, name="show_add_form")
    
    # Create issue form with validation
    issue_form = create_form(
        initial={
            "title": "",
            "description": "",
            "priority": "medium",
            "status": "backlog",
        },
        validators={
            "title": [required("Title is required"), max_length(100, "Title too long")],
            "description": [max_length(500, "Description too long")],
        }
    )
    
    # Counter for generating unique IDs
    next_id = Signal(len(INITIAL_ISSUES) + 1, name="next_id")
    
    # ==========================================================================
    # DERIVED STATE (Memos)
    # ==========================================================================
    
    # Filtered issues based on current filter
    filtered_issues = memo(
        lambda: [
            issue for issue in all_issues()
            if filter_status() == "all" or issue["status"] == filter_status()
        ],
        name="filtered_issues"
    )
    
    # Issue counts by status
    status_counts = memo(
        lambda: {
            status: len([i for i in all_issues() if i["status"] == status])
            for status in STATUS_LABELS.keys()
        },
        name="status_counts"
    )
    
    # Issues grouped by status for Kanban view
    issues_by_status = memo(
        lambda: {
            status: [i for i in all_issues() if i["status"] == status]
            for status in ["backlog", "todo", "in_progress", "done"]
        },
        name="issues_by_status"
    )
    
    # ==========================================================================
    # HANDLERS
    # ==========================================================================
    
    def handle_status_change(issue_id: int, new_status: str):
        """Change an issue's status."""
        all_issues.set([
            {**issue, "status": new_status} if issue["id"] == issue_id else issue
            for issue in all_issues()
        ])
    
    def handle_delete(issue_id: int):
        """Delete an issue."""
        all_issues.set([
            issue for issue in all_issues()
            if issue["id"] != issue_id
        ])
    
    def handle_add_issue():
        """Add a new issue using the form."""
        if issue_form.validate():
            values = issue_form.values
            new_issue = {
                "id": next_id(),
                "title": values["title"],
                "description": values["description"],
                "status": values["status"],
                "priority": values["priority"],
            }
            all_issues.set([*all_issues(), new_issue])
            next_id.set(next_id() + 1)
            issue_form.reset()
            show_add_form.set(False)
    
    # ==========================================================================
    # RENDER
    # ==========================================================================
    
    return div(class_="issues-page", style="max-width: 1200px; margin: 0 auto; padding: 24px;")[
        # Header
        div(class_="header", style="margin-bottom: 24px;")[
            h1(style="font-size: 24px; font-weight: 700; color: #111827; margin: 0;")[
                "Issues"
            ],
            div(style="display: flex; gap: 12px; margin-top: 16px;")[
                # View toggle
                div(class_="view-toggle", style="display: flex; gap: 4px; background: #f3f4f6; padding: 4px; border-radius: 8px;")[
                    button(
                        style=f"padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; {'background: white; box-shadow: 0 1px 2px rgba(0,0,0,0.1);' if view_mode() == 'list' else 'background: transparent;'}",
                        onclick=lambda: view_mode.set("list"),
                    )["List"],
                    button(
                        style=f"padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; {'background: white; box-shadow: 0 1px 2px rgba(0,0,0,0.1);' if view_mode() == 'kanban' else 'background: transparent;'}",
                        onclick=lambda: view_mode.set("kanban"),
                    )["Kanban"],
                ],
                # Add issue button
                button(
                    style="padding: 8px 16px; background: #5046e5; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 500;",
                    onclick=lambda: show_add_form.set(True),
                )["+ New Issue"],
            ],
        ],
        
        # Add issue form modal (shown conditionally)
        Show(when=lambda: show_add_form())[
            # Modal overlay - self_only means only close when clicking overlay itself, not children
            div(
                class_="modal-overlay",
                style="position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 50;",
                onclick=self_only(lambda: show_add_form.set(False)),
            )[
                # Modal content - no onclick needed, self_only on overlay handles it
                div(
                    class_="modal-content",
                    style="background: white; padding: 24px; border-radius: 12px; box-shadow: 0 25px 50px rgba(0,0,0,0.25); max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto;",
                )[
                    # Header
                    div(style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;")[
                        h2(style="font-size: 18px; font-weight: 600; margin: 0;")["Create New Issue"],
                        button(
                            style="background: none; border: none; font-size: 20px; cursor: pointer; color: #6b7280;",
                            onclick=lambda: show_add_form.set(False),
                        )["×"],
                    ],
                    
                    # Form fields
                    div(style="display: flex; flex-direction: column; gap: 16px;")[
                        # Title field
                        div(class_="form-field")[
                            label(style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px; color: #374151;")["Title *"],
                            input_(
                                type="text",
                                placeholder="What needs to be done?",
                                style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; box-sizing: border-box;",
                                bind=issue_form.title,
                            ),
                            issue_form.error_for("title"),
                        ],
                        
                        # Description field
                        div(class_="form-field")[
                            label(style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px; color: #374151;")["Description"],
                            textarea(
                                placeholder="Add more details...",
                                style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; min-height: 80px; resize: vertical; box-sizing: border-box;",
                                bind=issue_form.description,
                            ),
                            issue_form.error_for("description"),
                        ],
                        
                        # Priority & Status row
                        div(style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;")[
                            # Priority
                            div(class_="form-field")[
                                label(style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px; color: #374151;")["Priority"],
                                select(
                                    style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; background: white; box-sizing: border-box;",
                                    bind=issue_form.priority,
                                )[
                                    option(value="low")["Low"],
                                    option(value="medium")["Medium"],
                                    option(value="high")["High"],
                                    option(value="urgent")["Urgent"],
                                ],
                            ],
                            # Status
                            div(class_="form-field")[
                                label(style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px; color: #374151;")["Status"],
                                select(
                                    style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; background: white; box-sizing: border-box;",
                                    bind=issue_form.status,
                                )[
                                    option(value="backlog")["Backlog"],
                                    option(value="todo")["Todo"],
                                    option(value="in_progress")["In Progress"],
                                    option(value="done")["Done"],
                                ],
                            ],
                        ],
                    ],
                    
                    # Form actions
                    div(style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;")[
                        button(
                            style="padding: 10px 20px; background: #f3f4f6; color: #374151; border: none; border-radius: 8px; cursor: pointer; font-weight: 500;",
                            onclick=lambda: show_add_form.set(False),
                        )["Cancel"],
                        button(
                            style="padding: 10px 20px; background: #5046e5; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 500;",
                            onclick=handle_add_issue,
                        )["Create Issue"],
                    ],
                ],
            ],
        ],
        
        # Filter tabs (only in list view)
        Show(when=lambda: view_mode() == "list")[
            div(class_="filters", style="display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap;")[
                # All filter
                button(
                    style=f"padding: 6px 12px; border: 1px solid {'#5046e5' if filter_status() == 'all' else '#d1d5db'}; border-radius: 6px; cursor: pointer; background: {'#eef2ff' if filter_status() == 'all' else 'white'};",
                    onclick=lambda: filter_status.set("all"),
                )[f"All ({len(all_issues())})"],
                # Status filters
                button(
                    style=f"padding: 6px 12px; border: 1px solid {'#5046e5' if filter_status() == 'backlog' else '#d1d5db'}; border-radius: 6px; cursor: pointer; background: {'#eef2ff' if filter_status() == 'backlog' else 'white'};",
                    onclick=lambda: filter_status.set("backlog"),
                )[f"Backlog ({status_counts().get('backlog', 0)})"],
                button(
                    style=f"padding: 6px 12px; border: 1px solid {'#5046e5' if filter_status() == 'todo' else '#d1d5db'}; border-radius: 6px; cursor: pointer; background: {'#eef2ff' if filter_status() == 'todo' else 'white'};",
                    onclick=lambda: filter_status.set("todo"),
                )[f"Todo ({status_counts().get('todo', 0)})"],
                button(
                    style=f"padding: 6px 12px; border: 1px solid {'#5046e5' if filter_status() == 'in_progress' else '#d1d5db'}; border-radius: 6px; cursor: pointer; background: {'#eef2ff' if filter_status() == 'in_progress' else 'white'};",
                    onclick=lambda: filter_status.set("in_progress"),
                )[f"In Progress ({status_counts().get('in_progress', 0)})"],
                button(
                    style=f"padding: 6px 12px; border: 1px solid {'#5046e5' if filter_status() == 'done' else '#d1d5db'}; border-radius: 6px; cursor: pointer; background: {'#eef2ff' if filter_status() == 'done' else 'white'};",
                    onclick=lambda: filter_status.set("done"),
                )[f"Done ({status_counts().get('done', 0)})"],
            ],
        ],
        
        # List View
        Show(when=lambda: view_mode() == "list")[
            div(class_="issue-list")[
                For(each=lambda: filtered_issues(), key_fn=lambda x: x["id"])[
                    lambda issue, index: IssueCard(
                        issue=issue,
                        on_status_change=handle_status_change,
                        on_delete=handle_delete,
                    )
                ],
                # Empty state
                Show(when=lambda: len(filtered_issues()) == 0)[
                    div(style="text-align: center; padding: 48px; color: #6b7280;")[
                        "No issues found. Create one to get started!"
                    ],
                ],
            ],
        ],
        
        # Kanban View
        Show(when=lambda: view_mode() == "kanban")[
            div(
                class_="kanban-board",
                style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;",
            )[
                # Backlog column
                KanbanColumn(
                    title="Backlog",
                    issues=issues_by_status().get("backlog", []),
                    color="#6b7280",
                ),
                # Todo column
                KanbanColumn(
                    title="Todo",
                    issues=issues_by_status().get("todo", []),
                    color="#3b82f6",
                ),
                # In Progress column
                KanbanColumn(
                    title="In Progress",
                    issues=issues_by_status().get("in_progress", []),
                    color="#f59e0b",
                ),
                # Done column
                KanbanColumn(
                    title="Done",
                    issues=issues_by_status().get("done", []),
                    color="#10b981",
                ),
            ],
        ],
    ]


@component
def KanbanColumn(title: str, issues: list, color: str) -> Element:
    """
    A single Kanban column with header and issue cards.
    """
    return div(
        class_="kanban-column",
        style=f"background: #f9fafb; border-radius: 12px; padding: 12px; min-height: 400px;",
    )[
        # Column header
        div(
            class_="column-header",
            style=f"display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 2px solid {color};",
        )[
            span(
                class_="column-dot",
                style=f"width: 8px; height: 8px; border-radius: 50%; background: {color};",
            ),
            span(style="font-weight: 600; color: #374151;")[title],
            span(
                class_="count",
                style="background: #e5e7eb; padding: 2px 8px; border-radius: 4px; font-size: 12px; color: #6b7280;",
            )[str(len(issues))],
        ],
        # Issue cards
        div(class_="column-issues")[
            For(each=lambda: issues, key_fn=lambda x: x["id"])[
                lambda issue, index: IssueCardCompact(issue=issue)
            ],
            # Empty state
            Show(when=lambda: len(issues) == 0)[
                div(style="text-align: center; padding: 24px; color: #9ca3af; font-size: 14px;")[
                    "No issues"
                ],
            ],
        ],
    ]

