"""
PyNext Example - About Page

A simple static page demonstrating basic routing.
"""

from pynext import page, div, h1, h2, p, a, ul, li, code, pre


@page(title="About PyNext")
def about():
    """About page with framework information."""
    return div(class_="container")[
        # Navigation back
        div(class_="nav-back")[
            a(href="/")["← Back to Home"]
        ],
        
        h1()["About PyNext"],
        
        p()[
            "PyNext is a modern Python web framework that brings the best ideas from "
            "Next.js and SolidJS to the Python ecosystem."
        ],
        
        h2()["Core Concepts"],
        
        div(class_="concept")[
            h2()["🎯 Fine-grained Reactivity"],
            p()[
                "Unlike React's virtual DOM, PyNext uses SolidJS-style signals for "
                "precise, efficient updates. Only the specific DOM nodes that depend "
                "on changed data are updated."
            ],
            pre()[code()["""
from pynext import Signal

count = Signal(0)
count.set(5)        # Updates only elements using this signal
count.update(lambda x: x + 1)  # Increment
"""]],
        ],
        
        div(class_="concept")[
            h2()["📁 File-based Routing"],
            p()["Create files in the pages/ directory and routes are automatically generated:"],
            ul()[
                li()[code()["pages/index.py"], " → ", code()["/"]],
                li()[code()["pages/about.py"], " → ", code()["/about"]],
                li()[code()["pages/users/[id].py"], " → ", code()["/users/:id"]],
                li()[code()["pages/docs/[...slug].py"], " → ", code()["/docs/*"]],
            ],
        ],
        
        div(class_="concept")[
            h2()["🐍 Server Actions"],
            p()[
                "Call Python functions directly from the client. Server actions have "
                "full access to Python packages and the server environment."
            ],
            pre()[code()["""
from pynext import server_action
import pandas as pd

@server_action
async def process_data(file_path: str) -> dict:
    df = pd.read_csv(file_path)
    return {"rows": len(df), "columns": list(df.columns)}
"""]],
        ],
        
        div(class_="concept")[
            h2()["📦 NPM Integration"],
            p()[
                "Use npm packages in your PyNext apps. Packages are bundled automatically "
                "using esbuild for optimal performance."
            ],
            pre()[code()["""
# pynext.config.py
npm_packages = [
    "chart.js",
    "lodash",
]
"""]],
        ],
        
        h2()["Getting Started"],
        pre()[code()["""
# Create a new project
pynext init my-app

# Start development server
cd my-app
pynext dev

# Build for production
pynext build
"""]],
        
        p()[
            a(href="/")["← Back to Home"], " | ",
            a(href="/users/42")["View User Profile →"]
        ],
        
        ABOUT_STYLES
    ]


# Styles
from pynext.core.html import Element
style = Element("style")

ABOUT_STYLES = style()["""
.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 20px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.nav-back {
    margin-bottom: 32px;
}

.nav-back a {
    color: #6366f1;
    text-decoration: none;
    font-weight: 500;
}

.nav-back a:hover {
    text-decoration: underline;
}

h1 {
    font-size: 36px;
    margin-bottom: 24px;
    color: #1f2937;
}

h2 {
    font-size: 24px;
    color: #374151;
    margin-top: 32px;
    margin-bottom: 16px;
}

p {
    color: #4b5563;
    line-height: 1.7;
    margin-bottom: 16px;
}

.concept {
    background: #f9fafb;
    padding: 24px;
    border-radius: 12px;
    margin-bottom: 24px;
    border: 1px solid #e5e7eb;
}

.concept h2 {
    margin-top: 0;
    font-size: 20px;
}

ul {
    color: #4b5563;
}

li {
    margin-bottom: 8px;
}

code {
    background: #e5e7eb;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Fira Code', monospace;
    font-size: 14px;
}

pre {
    background: #1f2937;
    color: #e5e7eb;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
}

pre code {
    background: none;
    padding: 0;
    color: inherit;
}

a {
    color: #6366f1;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}
"""]

