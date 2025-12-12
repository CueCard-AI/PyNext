"""
Linear Clone - Main App with Router

This demonstrates PyNext's client-side router for multi-page SPA navigation.
Routes:
- /           → Dashboard/Home
- /issues     → Issue list with filters
- /issues/:id → Issue detail view
- /projects   → Project list
- /projects/:id → Project board (Kanban)
- /settings   → Settings page
"""

from pynext import page, div, nav, main, header, span, h1
from pynext.reactive import (
    Router, 
    Route, 
    Link, 
    useParams, 
    useNavigate,
    signal,
)
from pynext.core.html import a, select, option, button


# =============================================================================
# LAYOUT COMPONENT
# =============================================================================

def AppLayout(content):
    """Main application layout with sidebar navigation."""
    return div(class_="app-layout")[
        # Sidebar
        nav(class_="sidebar")[
            div(class_="logo")[
                h1()["Linear Clone"],
            ],
            
            div(class_="nav-links")[
                Link(href="/", exact=True, active_class="active")[
                    span(class_="icon")["🏠"],
                    span()["Dashboard"],
                ],
                Link(href="/issues", active_class="active")[
                    span(class_="icon")["📋"],
                    span()["Issues"],
                ],
                Link(href="/projects", active_class="active")[
                    span(class_="icon")["📁"],
                    span()["Projects"],
                ],
                Link(href="/settings", active_class="active")[
                    span(class_="icon")["⚙️"],
                    span()["Settings"],
                ],
            ],
        ],
        
        # Main content
        main(class_="main-content")[
            content,
        ],
    ]


# =============================================================================
# PAGE COMPONENTS
# =============================================================================

def Dashboard():
    """Dashboard/Home page."""
    from pynext.core.html import h2, p, section
    
    return div(class_="dashboard")[
        h1()["Welcome to Linear Clone"],
        
        section(class_="stats")[
            div(class_="stat-card")[
                h2()["12"],
                p()["Open Issues"],
            ],
            div(class_="stat-card")[
                h2()["3"],
                p()["In Progress"],
            ],
            div(class_="stat-card")[
                h2()["8"],
                p()["Completed This Week"],
            ],
        ],
        
        section(class_="recent")[
            h2()["Recent Activity"],
            div(class_="activity-list")[
                div(class_="activity-item")["Issue #123 was updated"],
                div(class_="activity-item")["New issue created: Bug fix"],
                div(class_="activity-item")["Project 'Alpha' completed"],
            ],
        ],
    ]


def IssueListPage():
    """Issue list page - delegates to the full implementation in pages/issues.py."""
    # Import the actual issues page component
    from pages.issues import issues as full_issues_page
    return full_issues_page()


def IssueDetailPage():
    """Issue detail page."""
    from pynext.core.html import h2, p, article, button
    
    params = useParams()
    navigate = useNavigate()
    issue_id = params.get("id", "unknown")
    
    return article(class_="issue-detail")[
        div(class_="issue-header")[
            button(
                class_="back-btn",
                onclick=lambda: navigate("/issues"),
            )["← Back to Issues"],
            h1()[f"Issue #{issue_id}"],
        ],
        
        div(class_="issue-body")[
            h2()["Description"],
            p()["This is the detailed view for issue " + issue_id],
            
            div(class_="issue-meta")[
                div()["Status: In Progress"],
                div()["Priority: High"],
                div()["Assignee: John Doe"],
            ],
        ],
        
        div(class_="issue-actions")[
            button(class_="btn-primary")["Edit"],
            button(class_="btn-secondary")["Close Issue"],
            button(class_="btn-danger")["Delete"],
        ],
    ]


def ProjectListPage():
    """Project list page."""
    from pynext.core.html import h2, ul, li
    
    projects = [
        {"id": "proj-1", "name": "Alpha", "issues": 5},
        {"id": "proj-2", "name": "Beta", "issues": 12},
        {"id": "proj-3", "name": "Gamma", "issues": 3},
    ]
    
    return div(class_="projects-page")[
        h1()["Projects"],
        
        div(class_="project-grid")[
            *[
                Link(href=f"/projects/{p['id']}", class_="project-card")[
                    h2()[p["name"]],
                    span()[f"{p['issues']} issues"],
                ] for p in projects
            ],
        ],
    ]


def ProjectBoardPage():
    """Project Kanban board page."""
    from pynext.core.html import h2, section
    
    params = useParams()
    navigate = useNavigate()
    project_id = params.get("id", "unknown")
    
    return div(class_="project-board")[
        div(class_="board-header")[
            button(onclick=lambda: navigate("/projects"))["← Projects"],
            h1()[f"Project: {project_id}"],
        ],
        
        div(class_="kanban-board")[
            section(class_="kanban-column")[
                h2()["Backlog"],
                div(class_="issue-card")["Issue 1"],
                div(class_="issue-card")["Issue 2"],
            ],
            section(class_="kanban-column")[
                h2()["In Progress"],
                div(class_="issue-card")["Issue 3"],
            ],
            section(class_="kanban-column")[
                h2()["Done"],
                div(class_="issue-card")["Issue 4"],
                div(class_="issue-card")["Issue 5"],
            ],
        ],
    ]


def SettingsPage():
    """Settings page."""
    from pynext.core.html import h2, form, label, input_, button, section
    
    return div(class_="settings-page")[
        h1()["Settings"],
        
        section(class_="settings-section")[
            h2()["Profile"],
            form(class_="settings-form")[
                div(class_="form-group")[
                    label()["Display Name"],
                    input_(type="text", value="John Doe"),
                ],
                div(class_="form-group")[
                    label()["Email"],
                    input_(type="email", value="john@example.com"),
                ],
                button(type="submit")["Save Profile"],
            ],
        ],
        
        section(class_="settings-section")[
            h2()["Preferences"],
            form(class_="settings-form")[
                div(class_="form-group")[
                    label()["Theme"],
                    select()[
                        option(value="light")["Light"],
                        option(value="dark")["Dark"],
                        option(value="system")["System"],
                    ],
                ],
                button(type="submit")["Save Preferences"],
            ],
        ],
    ]


def NotFoundPage():
    """404 page."""
    from pynext.core.html import p
    
    navigate = useNavigate()
    
    return div(class_="not-found")[
        h1()["404 - Page Not Found"],
        p()["The page you're looking for doesn't exist."],
        button(onclick=lambda: navigate("/"))["Go Home"],
    ]


# =============================================================================
# MAIN APP WITH ROUTER
# =============================================================================

@page(title="Linear Clone", hydration="full")
def app():
    """
    Main app entry point with client-side router.
    
    This demonstrates PyNext's SPA routing capabilities:
    - Clean URLs without page reloads
    - Active link highlighting
    - Route parameters (:id)
    - Programmatic navigation
    - Fallback for 404
    """
    return AppLayout(
        Router(fallback=NotFoundPage)[
            Route(path="/", component=Dashboard),
            Route(path="/issues", component=IssueListPage),
            Route(path="/issues/:id", component=IssueDetailPage),
            Route(path="/projects", component=ProjectListPage),
            Route(path="/projects/:id", component=ProjectBoardPage),
            Route(path="/settings", component=SettingsPage),
        ]
    )


# For direct execution
if __name__ == "__main__":
    print(app())

