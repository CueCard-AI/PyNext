"""
Dashboard layout.

Nested layout for the dashboard section with sidebar navigation.
"""

from pynext import layout, div, nav, a, aside

@layout
def dashboard_layout(children):
    """Dashboard layout with sidebar."""
    return div(class_="dashboard-layout")[
        # Sidebar
        aside(class_="dashboard-sidebar")[
            nav(class_="sidebar-nav")[
                a(href="/dashboard", class_="sidebar-link")["Overview"],
                a(href="/dashboard/analytics", class_="sidebar-link")["Analytics"],
                a(href="/dashboard/settings", class_="sidebar-link")["Settings"],
            ]
        ],
        
        # Main dashboard content
        div(class_="dashboard-content")[
            children
        ]
    ]

