"""
Global loading component.

Shown while page content is loading.
"""

from pynext import loading, div, span

@loading
def global_loading():
    """Global loading indicator."""
    return div(class_="loading-container")[
        div(class_="loading-spinner"),
        span(class_="loading-text")["Loading..."]
    ]

