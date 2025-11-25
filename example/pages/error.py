"""
Global error boundary.

Shown when an unhandled error occurs.
"""

from pynext import error, div, h1, p, pre, button

@error
def global_error(error, reset):
    """Global error handler."""
    return div(class_="error-container")[
        div(class_="error-content")[
            h1(class_="error-title")["Something went wrong!"],
            p(class_="error-message")[
                "An unexpected error occurred. Please try again."
            ],
            pre(class_="error-details")[
                str(error)
            ],
            button(
                class_="error-retry",
                onclick=reset
            )["Try Again"]
        ]
    ]

