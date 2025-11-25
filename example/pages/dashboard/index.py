"""
Dashboard overview page.

Demonstrates:
- Nested layouts
- Metadata API
"""

from pynext import page, Metadata, div, h1, h2, p

@page(
    metadata=Metadata(
        title="Dashboard | PyNext",
        description="Your personal dashboard",
        openGraph={
            "title": "Dashboard",
            "description": "Your personal dashboard"
        }
    )
)
def dashboard():
    """Dashboard overview page."""
    return div(class_="dashboard-overview")[
        h1()["Dashboard Overview"],
        
        div(class_="stats-grid")[
            div(class_="stat-card")[
                h2()["Total Users"],
                p(class_="stat-value")["1,234"]
            ],
            div(class_="stat-card")[
                h2()["Revenue"],
                p(class_="stat-value")["$12,345"]
            ],
            div(class_="stat-card")[
                h2()["Active Sessions"],
                p(class_="stat-value")["456"]
            ]
        ]
    ]

