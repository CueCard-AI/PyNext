"""
Custom 404 page.

Shown when a route is not found.
"""

from pynext import not_found, div, h1, p, a

@not_found
def custom_404():
    """Custom 404 not found page."""
    return div(class_="not-found-container")[
        div(class_="not-found-content")[
            h1(class_="not-found-title")["404"],
            p(class_="not-found-message")[
                "Oops! The page you're looking for doesn't exist."
            ],
            a(href="/", class_="not-found-link")[
                "← Go back home"
            ]
        ]
    ]

