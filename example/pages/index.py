"""
PyNext Example - Home Page

Demonstrates basic reactivity with signals and component structure.
"""

from pynext import (
    page, component, Signal, Store, Computed,
    div, h1, h2, p, button, span, input_, a, ul, li, header, main, footer, nav
)


@component
def Counter():
    """A simple counter component demonstrating signals."""
    count = Signal(0)
    
    return div(class_="counter-card")[
        h2()["Counter"],
        p(class_="count-display")[
            "Count: ",
            span(class_="count-value")[count]
        ],
        div(class_="button-group")[
            button(
                class_="btn btn-primary",
                onclick=lambda: count.update(lambda x: x + 1)
            )["+ Increment"],
            button(
                class_="btn btn-secondary",
                onclick=lambda: count.update(lambda x: x - 1)
            )["- Decrement"],
            button(
                class_="btn btn-outline",
                onclick=lambda: count.set(0)
            )["Reset"]
        ]
    ]


@component
def TodoList():
    """A todo list demonstrating stores and list rendering."""
    todos = Store({
        "items": [
            {"id": 1, "text": "Learn PyNext", "done": False},
            {"id": 2, "text": "Build something awesome", "done": False},
            {"id": 3, "text": "Share with friends", "done": False},
        ],
        "nextId": 4
    })
    
    new_todo = Signal("")
    
    def add_todo():
        text = new_todo()
        if text.strip():
            items = todos.items
            items.append({
                "id": todos.nextId,
                "text": text,
                "done": False
            })
            todos.nextId = todos.nextId + 1
            new_todo.set("")
    
    def toggle_todo(todo_id):
        for item in todos.items:
            if item["id"] == todo_id:
                item["done"] = not item["done"]
                break
    
    return div(class_="todo-card")[
        h2()["Todo List"],
        div(class_="todo-input")[
            input_(
                type="text",
                placeholder="What needs to be done?",
                value=new_todo,
                class_="input"
            ),
            button(class_="btn btn-primary", onclick=add_todo)["Add"]
        ],
        ul(class_="todo-list")[
            [
                li(
                    class_=f"todo-item {'done' if item['done'] else ''}",
                    key=str(item["id"])
                )[
                    span(
                        class_="todo-text",
                        onclick=lambda i=item: toggle_todo(i["id"])
                    )[item["text"]]
                ]
                for item in todos.items
            ]
        ]
    ]


@component
def Navigation():
    """Navigation component."""
    return nav(class_="main-nav")[
        div(class_="nav-brand")[
            a(href="/")["🐍 PyNext"]
        ],
        ul(class_="nav-links")[
            li()[a(href="/")["Home"]],
            li()[a(href="/about")["About"]],
            li()[a(href="/users/123")["User Profile"]],
            li()[a(href="/actions")["Server Actions"]],
        ]
    ]


@page(
    title="PyNext - Python + SolidJS Reactivity",
    meta=[
        {"name": "description", "content": "PyNext: A Python web framework with SolidJS-inspired reactivity"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
    ]
)
def index():
    """Home page showcasing PyNext features."""
    return div(class_="app")[
        Navigation(),
        
        main(class_="main-content")[
            # Hero section
            div(class_="hero")[
                h1(class_="hero-title")["Welcome to PyNext 🚀"],
                p(class_="hero-subtitle")[
                    "A Python framework that brings SolidJS-inspired fine-grained "
                    "reactivity to the server, with seamless client hydration."
                ],
            ],
            
            # Features grid
            div(class_="features")[
                div(class_="feature")[
                    span(class_="feature-icon")["📁"],
                    h2()["File-based Routing"],
                    p()["Create pages in the pages/ directory and routes are automatically generated."],
                ],
                div(class_="feature")[
                    span(class_="feature-icon")["⚡"],
                    h2()["Fine-grained Reactivity"],
                    p()["Signals, Effects, and Stores for precise, efficient updates."],
                ],
                div(class_="feature")[
                    span(class_="feature-icon")["🐍"],
                    h2()["Server Actions"],
                    p()["Call Python functions from the client with full package access."],
                ],
                div(class_="feature")[
                    span(class_="feature-icon")["📦"],
                    h2()["NPM Integration"],
                    p()["Use npm packages with automatic bundling via esbuild."],
                ],
            ],
            
            # Interactive demos
            div(class_="demos")[
                h2(class_="section-title")["Interactive Demos"],
                div(class_="demo-grid")[
                    Counter(),
                    TodoList(),
                ]
            ]
        ],
        
        footer(class_="main-footer")[
            p()["Built with PyNext • ", a(href="https://github.com/pynext/pynext")["GitHub"]]
        ],
        
        # Inline styles for the demo
        style()[CSS_STYLES]
    ]


# CSS styles embedded in the page
CSS_STYLES = """
:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --secondary: #10b981;
    --text: #1f2937;
    --text-light: #6b7280;
    --bg: #f9fafb;
    --card-bg: #ffffff;
    --border: #e5e7eb;
    --radius: 12px;
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    margin: 0;
}

.app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Navigation */
.main-nav {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand a {
    font-size: 24px;
    font-weight: 700;
    color: var(--text);
    text-decoration: none;
}

.nav-links {
    display: flex;
    gap: 24px;
    list-style: none;
    margin: 0;
    padding: 0;
}

.nav-links a {
    color: var(--text-light);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
}

.nav-links a:hover {
    color: var(--primary);
}

/* Main content */
.main-content {
    flex: 1;
    max-width: 1200px;
    margin: 0 auto;
    padding: 48px 24px;
    width: 100%;
}

/* Hero */
.hero {
    text-align: center;
    margin-bottom: 64px;
}

.hero-title {
    font-size: 48px;
    font-weight: 800;
    margin: 0 0 16px 0;
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 20px;
    color: var(--text-light);
    max-width: 600px;
    margin: 0 auto;
}

/* Features */
.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 24px;
    margin-bottom: 64px;
}

.feature {
    background: var(--card-bg);
    padding: 24px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
}

.feature-icon {
    font-size: 32px;
    margin-bottom: 12px;
    display: block;
}

.feature h2 {
    font-size: 18px;
    margin: 0 0 8px 0;
}

.feature p {
    color: var(--text-light);
    margin: 0;
    font-size: 14px;
}

/* Demos */
.section-title {
    text-align: center;
    margin-bottom: 32px;
}

.demo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 24px;
}

/* Counter card */
.counter-card, .todo-card {
    background: var(--card-bg);
    padding: 24px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
}

.counter-card h2, .todo-card h2 {
    margin: 0 0 16px 0;
    font-size: 20px;
}

.count-display {
    font-size: 24px;
    margin: 16px 0;
}

.count-value {
    font-weight: 700;
    color: var(--primary);
}

.button-group {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

/* Buttons */
.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 14px;
}

.btn-primary {
    background: var(--primary);
    color: white;
}

.btn-primary:hover {
    background: var(--primary-dark);
}

.btn-secondary {
    background: var(--secondary);
    color: white;
}

.btn-secondary:hover {
    background: #059669;
}

.btn-outline {
    background: transparent;
    border: 2px solid var(--border);
    color: var(--text);
}

.btn-outline:hover {
    border-color: var(--primary);
    color: var(--primary);
}

/* Todo */
.todo-input {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}

.input {
    flex: 1;
    padding: 10px 16px;
    border: 2px solid var(--border);
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.2s;
}

.input:focus {
    outline: none;
    border-color: var(--primary);
}

.todo-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.todo-item {
    padding: 12px;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    transition: background 0.2s;
}

.todo-item:hover {
    background: var(--bg);
}

.todo-item.done .todo-text {
    text-decoration: line-through;
    color: var(--text-light);
}

/* Footer */
.main-footer {
    background: var(--card-bg);
    border-top: 1px solid var(--border);
    padding: 24px;
    text-align: center;
    color: var(--text-light);
}

.main-footer a {
    color: var(--primary);
    text-decoration: none;
}

.main-footer a:hover {
    text-decoration: underline;
}
"""


# Import style element
from pynext.core.html import Element
style = Element("style")

