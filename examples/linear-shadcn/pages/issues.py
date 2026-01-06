"""
Issues Page (Shadcn Version)

A clean, Pythonic issues page built with shadcn components.
Uses PyNext's form system for proper Pythonic issue creation.
"""

from pynext import page
from pynext.reactive import Signal, Memo
from pynext.core.html import Element, div, style, raw_html, label, input_, textarea, select, option, span
from pynext.reactive.forms import create_form
from pynext.reactive.validators import required, max_length
from pynext.reactive.control_flow import For, Show

# Shadcn components
from pynext.shadcn import (
    Button,
    Card, CardHeader, CardTitle, CardContent,
    Row, Column, Text, Heading,
    Badge,
    Tabs, TabsList, TabsTrigger, TabsContent,
)

# Domain components - use sys.path manipulation for standalone page loading
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from components import IssueCard, StatusBadge


# Sample data
SAMPLE_ISSUES = [
    {"id": 1, "title": "Fix authentication bug", "description": "Users can't log in with SSO", "status": "in_progress", "priority": "high"},
    {"id": 2, "title": "Add dark mode", "description": "Implement dark mode toggle", "status": "todo", "priority": "medium"},
    {"id": 3, "title": "Update documentation", "description": "Add API reference docs", "status": "backlog", "priority": "low"},
    {"id": 4, "title": "Performance optimization", "description": "Reduce bundle size by 50%", "status": "done", "priority": "high"},
    {"id": 5, "title": "Mobile responsive", "description": "Fix layout on mobile devices", "status": "todo", "priority": "medium"},
]


@page(title="Issues - Linear Clone (Shadcn)", hydration="full")
def issues() -> Element:
    """
    Issues page - the main issue tracker view.
    
    Notice how much cleaner this is compared to the original!
    No inline styles, semantic component names, clear structure.
    """
    # Reactive state
    all_issues = Signal(SAMPLE_ISSUES.copy(), name="all_issues")
    filter_status = Signal("all", name="filter_status")
    view_mode = Signal("list", name="view_mode")  # "list" or "kanban"
    show_new_issue_modal = Signal(False, name="show_new_issue_modal")
    next_id = Signal(len(SAMPLE_ISSUES) + 1, name="next_id")
    
    # Form for creating new issues (PyNext's proper form system)
    issue_form = create_form(
        initial={
            "title": "",
            "description": "",
            "priority": "medium",
            "status": "todo",
        },
        validators={
            "title": [required("Title is required"), max_length(100, "Title too long")],
            "description": [max_length(500, "Description too long")],
        }
    )
    
    # Computed counts
    total_count = Memo(lambda: len(all_issues()), name="total_count")
    
    def count_by_status(status: str) -> Memo:
        return Memo(
            lambda: len([i for i in all_issues() if i["status"] == status]),
            name=f"{status}_count"
        )
    
    backlog_count = count_by_status("backlog")
    todo_count = count_by_status("todo")
    in_progress_count = count_by_status("in_progress")
    done_count = count_by_status("done")
    
    # Memos for Kanban columns - each filters all_issues by a specific status
    # Using explicit Memos so the For component can properly transpile them
    backlog_issues = Memo(
        lambda: [i for i in all_issues() if i["status"] == "backlog"],
        name="backlog_issues"
    )
    todo_issues = Memo(
        lambda: [i for i in all_issues() if i["status"] == "todo"],
        name="todo_issues"
    )
    in_progress_issues = Memo(
        lambda: [i for i in all_issues() if i["status"] == "in_progress"],
        name="in_progress_issues"
    )
    done_issues = Memo(
        lambda: [i for i in all_issues() if i["status"] == "done"],
        name="done_issues"
    )
    
    # Filtered issues
    filtered_issues = Memo(
        lambda: [i for i in all_issues() if filter_status() == "all" or i["status"] == filter_status()],
        name="filtered_issues"
    )
    
    # Event handlers
    def handle_status_change(issue_id: int, new_status: str):
        issues = all_issues()
        for issue in issues:
            if issue["id"] == issue_id:
                issue["status"] = new_status
                break
        all_issues.set(issues.copy())
    
    def handle_delete(issue_id: int):
        issues = [i for i in all_issues() if i["id"] != issue_id]
        all_issues.set(issues)
    
    def handle_add_issue():
        """Add a new issue using the form - Pythonic handler transpiled to JS."""
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
            show_new_issue_modal.set(False)
    
    return div()[
        # Shadcn Theme Variables (Tailwind is loaded in PyNext's base template)
        style()["""
            :root {
                --background: 0 0% 100%;
                --foreground: 222.2 84% 4.9%;
                --card: 0 0% 100%;
                --card-foreground: 222.2 84% 4.9%;
                --primary: 221.2 83.2% 53.3%;
                --primary-foreground: 210 40% 98%;
                --secondary: 210 40% 96%;
                --secondary-foreground: 222.2 47.4% 11.2%;
                --muted: 210 40% 96%;
                --muted-foreground: 215.4 16.3% 46.9%;
                --destructive: 0 84.2% 60.2%;
                --destructive-foreground: 210 40% 98%;
                --border: 214.3 31.8% 91.4%;
            }
            body { 
                background: hsl(var(--background)); 
                color: hsl(var(--foreground)); 
                font-family: system-ui, -apple-system, sans-serif;
            }
            /* Toast notification */
            .toast-success {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #22c55e;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 100;
                animation: slideIn 0.3s ease;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .bg-primary { background-color: hsl(var(--primary)); }
            .text-primary-foreground { color: hsl(var(--primary-foreground)); }
            .bg-secondary { background-color: hsl(var(--secondary)); }
            .text-secondary-foreground { color: hsl(var(--secondary-foreground)); }
            .bg-destructive { background-color: hsl(var(--destructive)); }
            .text-destructive-foreground { color: hsl(var(--destructive-foreground)); }
            .text-muted-foreground { color: hsl(var(--muted-foreground)); }
            .bg-card { background-color: hsl(var(--card)); }
            .text-card-foreground { color: hsl(var(--card-foreground)); }
            .text-foreground { color: hsl(var(--foreground)); }
            .border-input { border-color: hsl(var(--border)); }
            .hover\\:bg-primary\\/90:hover { background-color: hsl(221.2 83.2% 53.3% / 0.9); }
            .hover\\:bg-destructive\\/90:hover { background-color: hsl(0 84.2% 60.2% / 0.9); }
        """],
        # Kanban drag-drop helper script
        raw_html("""<script>
            window.handleKanbanDrop = function(event, newStatus) {
                event.preventDefault();
                event.currentTarget.classList.remove('ring-2', 'ring-primary');
                
                var issueId = parseInt(event.dataTransfer.getData('text/plain'));
                if (isNaN(issueId)) return;
                
                var allIssues = __pynext__.getSignal('all_issues').read();
                var currentIssue = allIssues.find(function(i) { return i.id === issueId; });
                if (!currentIssue || currentIssue.status === newStatus) return;
                
                // Update the issue status
                var updated = allIssues.map(function(i) {
                    return i.id === issueId ? Object.assign({}, i, {status: newStatus}) : i;
                });
                __pynext__.getSignal('all_issues').set(updated);
                
                // Priority colors map
                var priorityColors = {low: '#22c55e', medium: '#eab308', high: '#f97316', urgent: '#ef4444'};
                
                // Move the card element
                var card = document.querySelector('[data-issue-id="' + issueId + '"]');
                if (card) {
                    var cardWrapper = card.closest('[data-for-item]');
                    var targetFor = event.currentTarget.querySelector('[id^="for_"]');
                    if (cardWrapper && targetFor) {
                        // Update the for-item key
                        cardWrapper.setAttribute('data-for-item', String(issueId));
                        // Move to target column
                        targetFor.appendChild(cardWrapper);
                        
                        // Fix priority dot color - For component may have corrupted it
                        var priorityDot = card.querySelector('span[style*="border-radius"]');
                        if (priorityDot && currentIssue.priority) {
                            var correctColor = priorityColors[currentIssue.priority] || '#eab308';
                            priorityDot.style.background = correctColor;
                        }
                    }
                }
                
                // Update count displays
                var counts = {
                    backlog: updated.filter(function(i) { return i.status === 'backlog'; }).length,
                    todo: updated.filter(function(i) { return i.status === 'todo'; }).length,
                    in_progress: updated.filter(function(i) { return i.status === 'in_progress'; }).length,
                    done: updated.filter(function(i) { return i.status === 'done'; }).length
                };
                
                document.querySelectorAll('[data-pynext-text="total_count"]').forEach(function(el) { el.textContent = updated.length; });
                document.querySelectorAll('[data-pynext-text="backlog_count"]').forEach(function(el) { el.textContent = counts.backlog; });
                document.querySelectorAll('[data-pynext-text="todo_count"]').forEach(function(el) { el.textContent = counts.todo; });
                document.querySelectorAll('[data-pynext-text="in_progress_count"]').forEach(function(el) { el.textContent = counts.in_progress; });
                document.querySelectorAll('[data-pynext-text="done_count"]').forEach(function(el) { el.textContent = counts.done; });
            };
        </script>"""),
        # Main content
        Column(gap="lg", padding="lg", class_="max-w-4xl mx-auto")[
        # Header with view toggle
        Row(justify="between", align="center")[
            Heading(level=1)["Issues"],
            Row(gap="sm", align="center")[
                # View toggle buttons
                Row(gap="none", class_="bg-gray-100 rounded-lg p-1")[
                    view_toggle_button("list", "List", view_mode),
                    view_toggle_button("kanban", "Kanban", view_mode),
                ],
                Button(
                    variant="default",
                    data_pynext_on_click="return __pynext__.getSignal('show_new_issue_modal').set(true);",
                )["+ New Issue"],
            ],
        ],
        
        # Filter tabs - using reactive text binding for counts
        Row(gap="sm", wrap=True)[
            filter_button("all", "All", "total_count", total_count(), filter_status),
            filter_button("backlog", "Backlog", "backlog_count", backlog_count(), filter_status),
            filter_button("todo", "Todo", "todo_count", todo_count(), filter_status),
            filter_button("in_progress", "In Progress", "in_progress_count", in_progress_count(), filter_status),
            filter_button("done", "Done", "done_count", done_count(), filter_status),
        ],
        
        # List View (shown when view_mode == "list")
        # Using For component for reactive list rendering
        div(
            id="issues-list-container",
            data_pynext_toggle_signal="view_mode",
            data_pynext_toggle_value="list",
            data_pynext_toggle_active="display: block;",
            data_pynext_toggle_inactive="display: none;",
        )[
            Column(gap="sm")[
                For(each=lambda: filtered_issues(), key_fn=lambda x: x["id"])[
                    lambda issue, index: IssueCard(
                        issue=issue,
                        all_issues=all_issues,
                    )
                ],
            ],
        ],
        
        # Kanban View (shown when view_mode == "kanban")
        # Uses dedicated Memos for each status to enable reactive updates
        div(
            data_pynext_toggle_signal="view_mode",
            data_pynext_toggle_value="kanban",
            data_pynext_toggle_active="display: block;",
            data_pynext_toggle_inactive="display: none;",
            style="display: none;",  # Initially hidden
        )[
            Row(gap="md", class_="overflow-x-auto")[
                kanban_column_reactive("Backlog", "backlog", backlog_issues),
                kanban_column_reactive("Todo", "todo", todo_issues),
                kanban_column_reactive("In Progress", "in_progress", in_progress_issues),
                kanban_column_reactive("Done", "done", done_issues),
            ],
        ],
        
        # Empty state
        div(
            data_pynext_toggle_signal="filtered_issues",
            data_pynext_toggle_op="falsy",
            data_pynext_toggle_active="display: block;",
            data_pynext_toggle_inactive="display: none;",
            style="display: none;",
        )[
            Card(class_="text-center p-8")[
                CardContent()[
                    Column(gap="sm", align="center")[
                        Text("??", size="4xl"),
                        Text("No issues found", size="lg", weight="medium"),
                        Text("Create a new issue or adjust your filters.", color="muted"),
                    ],
                ],
            ],
        ],
        
        # New Issue Modal - Using PyNext's form system (Pythonic approach)
        div(
            data_pynext_toggle_signal="show_new_issue_modal",
            data_pynext_toggle_op="truthy",
            data_pynext_toggle_active="display: flex;",
            data_pynext_toggle_inactive="display: none;",
            style="display: none;",
            class_="fixed inset-0 bg-black/50 items-center justify-center z-50",
        )[
            Card(class_="w-full max-w-md mx-4")[
                CardHeader()[
                    CardTitle()["Create New Issue"],
                ],
                CardContent()[
                    Column(gap="md")[
                        # Title field with form binding
                        Column(gap="xs")[
                            label(style="font-weight: 500; font-size: 14px;")["Title"],
                            input_(
                                type="text",
                                placeholder="Issue title...",
                                style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px;",
                                bind=issue_form.title,
                            ),
                            issue_form.error_for("title"),
                        ],
                        # Description field with form binding
                        Column(gap="xs")[
                            label(style="font-weight: 500; font-size: 14px;")["Description"],
                            textarea(
                                placeholder="Describe the issue...",
                                rows="3",
                                style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px;",
                                bind=issue_form.description,
                            ),
                        ],
                        # Status and Priority row
                        Row(gap="md")[
                            Column(gap="xs", class_="flex-1")[
                                label(style="font-weight: 500; font-size: 14px;")["Status"],
                                select(
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: white;",
                                    bind=issue_form.status,
                                )[
                                    option(value="backlog")["Backlog"],
                                    option(value="todo")["Todo"],
                                    option(value="in_progress")["In Progress"],
                                    option(value="done")["Done"],
                                ],
                            ],
                            Column(gap="xs", class_="flex-1")[
                                label(style="font-weight: 500; font-size: 14px;")["Priority"],
                                select(
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: white;",
                                    bind=issue_form.priority,
                                )[
                                    option(value="low")["Low"],
                                    option(value="medium")["Medium"],
                                    option(value="high")["High"],
                                    option(value="urgent")["Urgent"],
                                ],
                            ],
                        ],
                        # Action buttons
                        Row(gap="sm", justify="end")[
                            Button(
                                variant="outline",
                                on_click=lambda: show_new_issue_modal.set(False),
                            )["Cancel"],
                            Button(
                                variant="default",
                                on_click=handle_add_issue,
                            )["Create Issue"],
                        ],
                    ],
                ],
            ],
        ],
    ],  # Close Column
    ]  # Close outer div


def filter_button(value: str, label: str, count_memo_name: str, initial_count: int, signal: Signal) -> Element:
    """
    A filter button that toggles active state based on the filter signal.
    
    Uses reactive text binding for the count so it updates when issues change.
    """
    return Button(
        variant="outline",
        size="sm",
        # Use single quotes in JS to avoid breaking HTML attribute
        data_pynext_on_click=f"return __pynext__.getSignal('filter_status').set('{value}');",
        # Reactive styling via toggle binding
        data_pynext_toggle_signal="filter_status",
        data_pynext_toggle_value=value,
        data_pynext_toggle_active="border-color: #5046e5; background: #eef2ff;",
        data_pynext_toggle_inactive="border-color: #d1d5db; background: white;",
    )[
        label,
        " (",
        span(data_pynext_text=count_memo_name)[str(initial_count)],
        ")",
    ]


def view_toggle_button(value: str, label: str, signal: Signal) -> Element:
    """Toggle button for switching between List and Kanban views."""
    return Button(
        variant="ghost",
        size="sm",
        # Use single quotes in JS to avoid breaking HTML attribute
        data_pynext_on_click=f"return __pynext__.getSignal('view_mode').set('{value}');",
        data_pynext_toggle_signal="view_mode",
        data_pynext_toggle_value=value,
        data_pynext_toggle_active="background: white; box-shadow: 0 1px 2px rgba(0,0,0,0.1);",
        data_pynext_toggle_inactive="background: transparent;",
    )[label]


def kanban_column_reactive(title: str, status: str, issues_memo: Memo) -> Element:
    """A reactive Kanban column that uses For component with a Memo.
    
    This version uses a Memo that's defined at the page level, which allows
    the For component's transpiler to properly generate JavaScript for
    reactive updates.
    
    Supports drag-and-drop to move issues between columns.
    
    Args:
        title: Column title (e.g., "Backlog", "Todo")
        status: The status value for this column (e.g., "backlog", "todo")
        issues_memo: A Memo that returns filtered issues for this column
    """
    PRIORITY_COLORS = {"low": "#22c55e", "medium": "#eab308", "high": "#f97316", "urgent": "#ef4444"}
    
    # Get initial issues for template rendering
    initial_issues = issues_memo()
    
    def render_kanban_card(issue: dict, index: int) -> Element:
        priority = issue.get("priority", "medium")
        color = PRIORITY_COLORS.get(priority, "#eab308")
        desc = issue.get("description", "")
        truncated = desc[:50] + "..." if len(desc) > 50 else desc
        issue_id = issue.get("id", 0)
        
        # Card with drag support
        # Read issue ID from data attribute at drag time to avoid stale values
        return div(
            class_="rounded-lg border bg-card text-card-foreground shadow-sm p-3 cursor-grab active:cursor-grabbing",
            draggable="true",
            data_issue_id=str(issue_id),
            data_pynext_on_dragstart="var el = event.target.closest('[data-issue-id]'); event.dataTransfer.setData('text/plain', el ? el.getAttribute('data-issue-id') : ''); event.dataTransfer.effectAllowed = 'move';",
        )[
            Column(gap="xs")[
                Row(align="center", gap="xs")[
                    # Priority dot - static color since priority doesn't change on drag
                    span(
                        style=f"display:inline-block;width:12px;height:12px;border-radius:50%;background:{color};",
                    )[""],
                    Text(issue["title"], weight="medium", size="sm", data_pynext_field="title"),
                ],
                Text(truncated, size="xs", color="muted", data_pynext_field="description"),
            ],
        ]
    
    # Generate a safe ID from the title
    column_id = f"kanban-{title.lower().replace(' ', '_')}"
    
    # Drop handler - calls global function to avoid HTML attribute escaping issues
    drop_handler = f"handleKanbanDrop(event, '{status}')"
    
    dragover_handler = "event.preventDefault(); event.currentTarget.classList.add('ring-2', 'ring-primary');"
    dragleave_handler = "event.currentTarget.classList.remove('ring-2', 'ring-primary');"
    
    return Column(
        gap="sm",
        class_="min-w-64 bg-gray-50 rounded-lg p-3 transition-all",
        id=column_id,
        data_pynext_on_drop=drop_handler,
        data_pynext_on_dragover=dragover_handler,
        data_pynext_on_dragleave=dragleave_handler,
    )[
        Text(title, weight="semibold", size="sm", class_="mb-2"),
        For(each=lambda: issues_memo(), key_fn=lambda x: x["id"])[render_kanban_card],
    ]


