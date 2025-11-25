# Getting Started with PyNext

> **Build web applications in Python with the simplicity of Next.js and the performance of SolidJS.**

Welcome to PyNext! This guide will transform you from zero to building reactive web applications in Python. Whether you're coming from Next.js, Django, Flask, or starting fresh, you'll feel right at home.

---

## Table of Contents

1. [What is PyNext?](#what-is-pynext)
2. [The "Aha!" Moment](#the-aha-moment)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Create Your First Project](#create-your-first-project)
6. [Project Structure](#project-structure)
7. [Your First Component](#your-first-component)
8. [Adding Reactivity](#adding-reactivity)
9. [Creating Pages](#creating-pages)
10. [Server Actions](#server-actions)
11. [Running the Dev Server](#running-the-dev-server)
12. [Complete Example](#complete-example)
13. [Understanding the Architecture](#understanding-the-architecture)
14. [Common Patterns](#common-patterns)
15. [What's Next](#whats-next)
16. [Troubleshooting](#troubleshooting)

---

## What is PyNext?

### The Elevator Pitch

PyNext is a **full-stack Python web framework** that brings Next.js concepts to Python with SolidJS-inspired reactivity:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PYNEXT AT A GLANCE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   🐍 Write EVERYTHING in Python      │   ⚡ SolidJS-style reactivity        │
│      - Pages                          │      - Fine-grained updates          │
│      - Components                     │      - No virtual DOM                │
│      - API routes                     │      - 10x faster than React         │
│      - Server actions                 │                                      │
│                                       │                                      │
│   📁 File-based routing              │   🔄 Server Actions                  │
│      pages/about.py → /about          │      - Call Python from browser      │
│      pages/users/[id].py → /users/:id │      - Full ecosystem access         │
│                                       │      - pandas, numpy, ML models      │
│                                       │                                      │
│   🏝️ Islands Architecture            │   📦 Zero Config                     │
│      - Minimal JavaScript             │      - Works out of the box          │
│      - Only hydrate what's needed     │      - Hot reload built-in           │
│                                       │                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### First Principles: Why PyNext Exists

**The Problem:**
- Traditional Python web frameworks (Django, Flask) require JavaScript for interactivity
- JavaScript frameworks can't use Python's data science ecosystem
- React-style virtual DOM is slow and complex

**The Solution:**
- Write UI in Python with HTML-like syntax
- Use signals for surgical DOM updates (no virtual DOM)
- Call Python functions directly from the browser (Server Actions)

**Think of it like this:**

```
Traditional Approach:
┌────────────────────────────────────────────────────────────────────────────┐
│  Python (Backend)          │  JavaScript (Frontend)                        │
│  ─────────────────         │  ───────────────────────                     │
│  • Flask/Django routes     │  • React/Vue components                       │
│  • API endpoints           │  • State management                           │
│  • Database queries        │  • Fetch API calls                            │
│  • Business logic          │  • UI rendering                               │
│                            │                                               │
│        ↕ JSON API ↕        │                                               │
└────────────────────────────────────────────────────────────────────────────┘
   You need to know TWO ecosystems and keep them in sync!


PyNext Approach:
┌────────────────────────────────────────────────────────────────────────────┐
│                          Python EVERYWHERE                                  │
│  ─────────────────────────────────────────                                 │
│  • Pages and components (rendered to HTML)                                 │
│  • Signals for reactivity (generates minimal JS)                           │
│  • Server Actions (Python functions callable from browser)                  │
│  • Full access to pandas, numpy, scikit-learn, etc.                        │
│                                                                            │
│  PyNext handles: HTML generation, hydration, RPC, routing                  │
└────────────────────────────────────────────────────────────────────────────┘
   ONE language, ONE codebase, full Python ecosystem!
```

---

## The "Aha!" Moment

Here's a complete interactive counter in PyNext—no JavaScript file needed:

```python
from pynext import page, Signal, div, h1, button, span

@page(title="Counter Demo")
def counter_page():
    # This is reactive state - changes automatically update the UI
    count = Signal(0)
    
    return div(class_="counter-app")[
        h1()["PyNext Counter"],
        
        # When count changes, ONLY this span updates (not the whole page!)
        span(class_="count")[count],
        
        # These buttons update the signal
        button(onclick=lambda: count.update(lambda x: x + 1))["➕ Increment"],
        button(onclick=lambda: count.set(0))["🔄 Reset"],
    ]
```

**What's happening here?**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HOW PYNEXT WORKS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. SERVER RENDERS (Initial Request)                                       │
│   ───────────────────────────────────                                       │
│                                                                              │
│   @page                                                                      │
│   def counter_page():                                                        │
│       count = Signal(0)  ←─── Signal created with initial value             │
│       return div()[span()[count], ...]                                       │
│                    │                                                         │
│                    ▼                                                         │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │ <div class="counter-app">                                           │    │
│   │   <h1>PyNext Counter</h1>                                           │    │
│   │   <span data-signal="sig_abc" class="count">0</span>  ←── Value     │    │
│   │   <button id="btn_1">➕ Increment</button>                          │    │
│   │   <button id="btn_2">🔄 Reset</button>                              │    │
│   │ </div>                                                              │    │
│   │ <script>                                                            │    │
│   │   __pynext__.createSignal('sig_abc', 0);  ←── Hydration data       │    │
│   │   // Event handlers attached                                        │    │
│   │ </script>                                                           │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│   2. CLIENT HYDRATION (Page Load)                                           │
│   ────────────────────────────────                                          │
│                                                                              │
│   • JavaScript runtime (~5KB) loads                                         │
│   • Signals recreated from hydration data                                   │
│   • Event handlers connected to buttons                                     │
│   • Page is now INTERACTIVE!                                                │
│                                                                              │
│   3. USER CLICKS INCREMENT                                                  │
│   ─────────────────────────                                                 │
│                                                                              │
│   count.update(x => x + 1)                                                  │
│        │                                                                     │
│        ▼                                                                     │
│   Signal value: 0 → 1                                                        │
│        │                                                                     │
│        ▼                                                                     │
│   DOM Update: <span>0</span> → <span>1</span>                               │
│               ↑                                                              │
│   ONLY this element updates!  (No full re-render like React)               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**The Magic:** When you update a signal, PyNext updates **only the DOM nodes** that depend on it—not the entire page, not a component tree, just the exact elements that changed. This is why it's called *fine-grained reactivity*.

---

## Prerequisites

Before starting, ensure you have:

### Required

| Tool | Version | Check Command |
|------|---------|---------------|
| **Python** | 3.10+ | `python --version` |
| **pip** | Latest | `pip --version` |

### Optional (for npm packages)

| Tool | Version | Check Command |
|------|---------|---------------|
| **Node.js** | 16+ | `node --version` |

```bash
# Verify your setup
python --version  # Python 3.10.0 or higher
pip --version     # pip 21.0 or higher

# Optional: for bundling npm packages
node --version    # v16.0.0 or higher (optional)
```

### Recommended Tools

- **VS Code** with Python extension
- **Cursor** for AI-assisted coding

---

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install pynext
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/pynext.git
cd pynext

# Install in development mode
pip install -e .
```

### Verify Installation

```bash
pynext --version
# PyNext 0.1.0
```

### What Gets Installed

```
pynext package:
├── Core framework
│   ├── HTML elements (div, span, button, etc.)
│   ├── Signals & reactivity
│   ├── Component system
│   └── Router
├── Server (FastAPI-based)
├── CLI tools
└── Runtime (JavaScript ~5KB)
```

---

## Create Your First Project

### Quick Start

```bash
# Create a new project
pynext init my-app

# Navigate to project
cd my-app

# Install dependencies
pip install -r requirements.txt

# Start development server
pynext dev
```

**Output:**
```
🚀 Creating new PyNext project: my-app

   ✓ Created pages/
   ✓ Created components/
   ✓ Created static/
   ✓ Created pynext.config.py
   ✓ Created requirements.txt
   
   Done! To get started:
   
   cd my-app
   pip install -r requirements.txt
   pynext dev
```

### What Gets Created

```
my-app/
├── pages/                    # Your pages and routes
│   ├── index.py             # Home page (/)
│   └── about.py             # About page (/about)
├── components/              # Reusable components
│   └── __init__.py
├── static/                  # Static files (CSS, images)
│   └── styles.css
├── pynext.config.py         # Configuration
└── requirements.txt         # Python dependencies
```

---

## Project Structure

Understanding the structure is key to working with PyNext effectively.

### Complete Project Layout

```
my-app/
│
├── pages/                    # 📁 FILE-BASED ROUTING
│   │
│   ├── index.py             # → /                 (home page)
│   ├── about.py             # → /about
│   ├── contact.py           # → /contact
│   │
│   ├── blog/                # Nested routes
│   │   ├── index.py         # → /blog
│   │   └── [slug].py        # → /blog/:slug (dynamic)
│   │
│   ├── users/
│   │   ├── index.py         # → /users
│   │   └── [id].py          # → /users/:id
│   │
│   ├── api/                  # API routes
│   │   └── users/
│   │       └── route.py     # → GET/POST /api/users
│   │
│   ├── layout.py            # Wraps all pages
│   ├── loading.py           # Loading state
│   ├── error.py             # Error boundary
│   └── not-found.py         # 404 page
│
├── components/               # 🧩 REUSABLE COMPONENTS
│   ├── __init__.py
│   ├── header.py
│   ├── footer.py
│   └── card.py
│
├── static/                   # 📦 STATIC ASSETS
│   ├── styles.css           # → /static/styles.css
│   ├── logo.png             # → /static/logo.png
│   └── fonts/
│
├── pynext.config.py         # ⚙️ CONFIGURATION
└── requirements.txt         # 📋 DEPENDENCIES
```

### The Mental Model: Files = Routes

```
Think of it like a file cabinet:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   FILE                          ROUTE                    ANALOGY            │
│   ────                          ─────                    ──────             │
│                                                                              │
│   pages/index.py            →   /                        Front door         │
│   pages/about.py            →   /about                   About section      │
│   pages/blog/index.py       →   /blog                    Blog section       │
│   pages/blog/[slug].py      →   /blog/hello-world        Individual post    │
│                                      /blog/my-post                          │
│                                      /blog/anything                         │
│                                                                              │
│   The [brackets] create "slots" that match ANY value!                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Folder/File | Purpose |
|-------------|---------|
| `pages/` | Each `.py` file becomes a route automatically |
| `components/` | Shared, reusable UI components |
| `static/` | Static assets served at `/static/` |
| `pynext.config.py` | Configuration file |
| `layout.py` | Wraps pages (headers, footers) |
| `[param].py` | Dynamic route parameter |
| `[...slug].py` | Catch-all route |
| `route.py` | API endpoint (REST) |

---

## Your First Component

Let's build a simple component to understand the syntax.

### Basic Syntax

```python
# pages/index.py

from pynext import page, div, h1, p

@page(title="Welcome to PyNext")
def index():
    return div(class_="container")[
        h1()["Hello, PyNext!"],
        p()["Your first PyNext application is running."]
    ]
```

### Understanding the Syntax

```python
# Think of it like building with LEGO blocks:

div(class_="container")     # ← The block type with properties
    [                       # ← Open the block to put things inside
        h1()["Hello"],      # ← Child elements go here
        p()["World"],
    ]                       # ← Close the block

# This becomes:
# <div class="container">
#     <h1>Hello</h1>
#     <p>World</p>
# </div>
```

### The Pattern: `element(attributes)[children]`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ELEMENT SYNTAX                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PYTHON                                    HTML OUTPUT                      │
│   ──────                                    ───────────                      │
│                                                                              │
│   div()                                     <div></div>                      │
│                                                                              │
│   div()["Hello"]                            <div>Hello</div>                 │
│                                                                              │
│   div(class_="box")                         <div class="box"></div>          │
│                                                                              │
│   div(class_="box")["Hello"]                <div class="box">Hello</div>     │
│                                                                              │
│   div(class_="box", id="main")[             <div class="box" id="main">      │
│       h1()["Title"],                            <h1>Title</h1>               │
│       p()["Content"]                            <p>Content</p>               │
│   ]                                         </div>                           │
│                                                                              │
│   Note: We use class_ (with underscore) because 'class' is a Python keyword │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Available Elements

```python
from pynext import (
    # Layout
    div, span, section, article, aside, main, header, footer, nav,
    
    # Typography
    h1, h2, h3, h4, h5, h6, p, a, strong, em, code, pre,
    
    # Forms
    form, input_, button, textarea, select, option, label,
    
    # Lists
    ul, ol, li,
    
    # Media
    img, video, audio,
    
    # Tables
    table, thead, tbody, tr, th, td,
    
    # And more...
)

# Note: input_ has an underscore because 'input' is a Python builtin
```

### Real Example: A Card Component

```python
# components/card.py

from pynext import component, div, h3, p, a

@component
def Card(title: str, description: str, link: str = "#"):
    """A reusable card component."""
    return div(class_="card")[
        div(class_="card-body")[
            h3(class_="card-title")[title],
            p(class_="card-text")[description],
            a(href=link, class_="card-link")["Learn more →"],
        ]
    ]

# Usage in a page:
from components.card import Card

@page
def index():
    return div(class_="cards")[
        Card(
            title="Getting Started",
            description="Learn the basics of PyNext.",
            link="/docs/getting-started"
        ),
        Card(
            title="Components",
            description="Build reusable UI components.",
            link="/docs/components"
        ),
    ]
```

---

## Adding Reactivity

This is where PyNext shines! **Signals** make your UI reactive without writing JavaScript.

### What is a Signal?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SIGNALS EXPLAINED                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ANALOGY: Think of a Signal like a "smart variable"                        │
│                                                                              │
│   Regular Variable:                                                          │
│   ─────────────────                                                          │
│   count = 0                                                                  │
│   display(count)  # Shows: 0                                                │
│   count = 5       # Value changes...                                        │
│   # BUT the display still shows 0! You have to manually update it.         │
│                                                                              │
│                                                                              │
│   Signal (Smart Variable):                                                   │
│   ─────────────────────────                                                  │
│   count = Signal(0)                                                          │
│   display(count)  # Shows: 0                                                │
│   count.set(5)    # Value changes...                                        │
│   # Display AUTOMATICALLY updates to 5! ✨                                  │
│                                                                              │
│                                                                              │
│   HOW IT WORKS:                                                             │
│   ──────────────                                                            │
│                                                                              │
│   count = Signal(0)                                                          │
│        │                                                                     │
│        ├──────────────────────────────────────────┐                         │
│        │                                          │                         │
│        ▼                                          ▼                         │
│   span()[count]                           button()[count]                   │
│        │                                          │                         │
│        └──────────────────────────────────────────┘                         │
│                            │                                                 │
│                   Both SUBSCRIBE to count                                    │
│                            │                                                 │
│                            ▼                                                 │
│                    count.set(5)                                              │
│                            │                                                 │
│                   Signal NOTIFIES subscribers                                │
│                            │                                                 │
│                   ┌────────┴────────┐                                       │
│                   ▼                 ▼                                       │
│              <span>5</span>    <button>5</button>                           │
│              Both update!                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Creating and Using Signals

```python
from pynext import page, Signal, div, h1, button, span

@page(title="Counter Demo")
def counter():
    # 1. CREATE a signal with initial value
    count = Signal(0)
    
    return div()[
        h1()["Counter"],
        
        # 2. USE the signal in your UI
        # Just reference it - it will update automatically!
        span(class_="display")[count],
        
        # 3. UPDATE the signal with events
        button(onclick=lambda: count.set(count() + 1))["Add 1"],
        button(onclick=lambda: count.update(lambda x: x + 1))["Add 1 (alt)"],
        button(onclick=lambda: count.set(0))["Reset"],
    ]
```

### Signal Methods

```python
count = Signal(0)

# READ the current value (call it like a function)
current = count()  # Returns: 0

# SET a new value directly
count.set(5)

# UPDATE based on current value
count.update(lambda x: x + 1)  # 5 → 6
count.update(lambda x: x * 2)  # 6 → 12

# SUBSCRIBE to changes (advanced)
unsubscribe = count.subscribe(lambda val: print(f"Count is now: {val}"))
```

### Computed Values (Derived State)

When you need a value that depends on other signals:

```python
from pynext import Signal, Computed

price = Signal(100)
quantity = Signal(2)
tax_rate = Signal(0.1)  # 10%

# Computed values auto-update when dependencies change!
subtotal = Computed(lambda: price() * quantity())
tax = Computed(lambda: subtotal() * tax_rate())
total = Computed(lambda: subtotal() + tax())

# UI automatically updates when ANY of these change
div()[
    p()[f"Price: $", price],
    p()[f"Qty: ", quantity],
    p()[f"Subtotal: $", subtotal],
    p()[f"Tax: $", tax],
    p(class_="total")[f"Total: $", total],
]
```

### Real Example: Todo List

```python
from pynext import page, Signal, div, h1, input_, button, ul, li

@page(title="Todo App")
def todo_app():
    todos = Signal([])
    new_todo = Signal("")
    
    def add_todo():
        text = new_todo()
        if text.strip():
            todos.update(lambda t: t + [{"id": len(t), "text": text, "done": False}])
            new_todo.set("")
    
    def toggle_todo(todo_id):
        def toggler(todos_list):
            return [
                {**t, "done": not t["done"]} if t["id"] == todo_id else t
                for t in todos_list
            ]
        todos.update(toggler)
    
    return div(class_="todo-app")[
        h1()["My Todos"],
        
        div(class_="add-form")[
            input_(
                type="text",
                placeholder="What needs to be done?",
                value=new_todo,
                onchange=lambda e: new_todo.set(e.target.value)
            ),
            button(onclick=add_todo)["Add"],
        ],
        
        ul(class_="todo-list")[
            [
                li(
                    class_="done" if todo["done"] else "",
                    onclick=lambda t=todo: toggle_todo(t["id"])
                )[todo["text"]]
                for todo in todos()
            ] if todos() else li()["No todos yet!"]
        ],
    ]
```

---

## Creating Pages

### Basic Page

```python
# pages/about.py

from pynext import page, div, h1, p, a

@page(title="About Us", description="Learn about our company")
def about():
    return div(class_="about-page")[
        h1()["About PyNext"],
        p()[
            "PyNext is a Python web framework inspired by ",
            "Next.js and SolidJS."
        ],
        a(href="/")["← Back to Home"]
    ]
```

**Visit:** `http://localhost:3000/about`

### Dynamic Routes

Dynamic routes capture URL parameters:

```python
# pages/users/[id].py
# This matches: /users/123, /users/alice, /users/anything

from pynext import page, get_params, div, h1, p

@page(title="User Profile")
def user_profile():
    # Get the URL parameter
    params = get_params()
    user_id = params.get("id", "unknown")
    
    return div()[
        h1()["User Profile"],
        p()[f"Viewing user: {user_id}"]
    ]
```

```
URL: /users/123
     └────────┬──────┘
              │
              ▼
    params = {"id": "123"}
```

### Nested Dynamic Routes

```python
# pages/blog/[year]/[month]/[slug].py
# Matches: /blog/2024/03/hello-world

from pynext import page, get_params, div, h1, p

@page(title="Blog Post")
def blog_post():
    params = get_params()
    
    year = params.get("year")
    month = params.get("month")
    slug = params.get("slug")
    
    return div()[
        h1()[f"Post: {slug}"],
        p()[f"Published: {month}/{year}"]
    ]
```

### Catch-All Routes

```python
# pages/docs/[...path].py
# Matches: /docs/anything/here/really

from pynext import page, get_params, div, h1

@page(title="Documentation")
def docs():
    params = get_params()
    path = params.get("path", [])  # This is a LIST
    
    return div()[
        h1()["Documentation"],
        p()[f"Path: /{'/'.join(path)}"]
    ]
```

```
URL: /docs/api/v2/users
     └─────────────────┘
              │
              ▼
    params = {"path": ["api", "v2", "users"]}
```

---

## Server Actions

**The killer feature:** Call Python functions directly from the browser!

### What Are Server Actions?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SERVER ACTIONS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ANALOGY: It's like having a Python REPL in your browser                   │
│                                                                              │
│   Traditional Approach:                                                      │
│   ────────────────────                                                       │
│   1. Write Python API endpoint                                              │
│   2. Write JavaScript to call it                                            │
│   3. Parse JSON response                                                     │
│   4. Update UI                                                              │
│   5. Handle errors                                                          │
│   6. Add loading states                                                     │
│   ... 50+ lines of boilerplate                                              │
│                                                                              │
│   Server Actions:                                                            │
│   ──────────────                                                            │
│                                                                              │
│   @server_action                                                            │
│   async def analyze_data(file_path):                                        │
│       import pandas as pd  # Full Python ecosystem!                        │
│       df = pd.read_csv(file_path)                                          │
│       return {"mean": df.mean(), "std": df.std()}                          │
│                                                                              │
│   button(onclick=analyze_data)["Analyze"]                                   │
│                                                                              │
│   That's it. Done. 5 lines.                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Basic Server Action

```python
from pynext import page, server_action, Signal, div, button, p

# This function runs on the SERVER
@server_action
async def get_server_time() -> dict:
    from datetime import datetime
    return {
        "time": datetime.now().isoformat(),
        "message": "Hello from Python!"
    }

# This component runs in the BROWSER
@page(title="Server Action Demo")
def demo():
    result = Signal(None)
    loading = Signal(False)
    
    async def fetch_time():
        loading.set(True)
        try:
            data = await get_server_time()
            result.set(data)
        finally:
            loading.set(False)
    
    return div()[
        button(onclick=fetch_time, disabled=loading)[
            "Loading..." if loading() else "Get Server Time"
        ],
        
        result() and div(class_="result")[
            p()[f"Time: {result()['time']}"],
            p()[result()["message"]]
        ]
    ]
```

### Using Python Packages

```python
from pynext import server_action

# You can use ANY Python package!

@server_action
async def analyze_csv(file_path: str) -> dict:
    import pandas as pd
    
    df = pd.read_csv(file_path)
    
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "summary": df.describe().to_dict()
    }

@server_action
async def predict_sentiment(text: str) -> dict:
    from transformers import pipeline
    
    classifier = pipeline("sentiment-analysis")
    result = classifier(text)[0]
    
    return {
        "label": result["label"],
        "confidence": result["score"]
    }

@server_action
async def generate_chart(data: list) -> dict:
    import matplotlib.pyplot as plt
    import io
    import base64
    
    plt.figure()
    plt.plot(data)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    return {
        "image": base64.b64encode(buf.getvalue()).decode()
    }
```

### How It Works Under the Hood

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SERVER ACTION FLOW                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   BROWSER                                          SERVER                    │
│   ───────                                          ──────                    │
│                                                                              │
│   button(onclick=get_server_time)                                           │
│        │                                                                     │
│        ▼                                                                     │
│   User clicks button                                                         │
│        │                                                                     │
│        ▼                                                                     │
│   __pynext__.callAction(                                                    │
│       "action_abc123",    ←─── Unique ID assigned at registration           │
│       {}                  ←─── Arguments                                     │
│   )                                                                          │
│        │                                                                     │
│        │  POST /_pynext/action                                              │
│        │  {"actionId": "action_abc123", "args": {}}                         │
│        │                                                                     │
│        └──────────────────────────────────►┐                                │
│                                            │                                 │
│                                            ▼                                 │
│                                   Action Registry                            │
│                                   looks up function                          │
│                                            │                                 │
│                                            ▼                                 │
│                                   async def get_server_time():              │
│                                       return {"time": "2024-..."}           │
│                                            │                                 │
│                                            ▼                                 │
│                                   {"data": {...}, "error": null}            │
│                                            │                                 │
│        ┌───────────────────────────────────┘                                │
│        │                                                                     │
│        ▼                                                                     │
│   result.set(data)                                                          │
│   UI updates!                                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Running the Dev Server

### Start Development Server

```bash
pynext dev
```

**Output:**
```
🚀 PyNext dev server starting...
   
   ➜  Local:   http://localhost:3000
   ➜  Network: http://192.168.1.100:3000
   
   📁 Watching for file changes...
   
   Ready in 150ms
```

### Dev Server Features

| Feature | Description |
|---------|-------------|
| **Hot Reload** | Changes auto-refresh the browser |
| **Error Overlay** | Clear error messages in browser |
| **API Docs** | Visit `/_pynext/docs` for OpenAPI docs |
| **Fast Startup** | Ready in milliseconds |

### Options

```bash
# Custom port
pynext dev --port 8080

# Custom host (for network access)
pynext dev --host 0.0.0.0

# Debug mode (verbose logging)
pynext dev --debug

# Combined
pynext dev --port 8080 --host 0.0.0.0 --debug
```

### Production Build

```bash
# Build for production
pynext build

# Run production server
pynext start
```

---

## Complete Example

Let's build a complete mini-app: a Todo List with server persistence.

### `pages/index.py`

```python
from pynext import (
    page, component, Signal, Computed,
    div, h1, h2, p, button, input_, ul, li, span,
    server_action
)

# ============================================
# Server Actions (run on server)
# ============================================

# In-memory storage (use database in production)
todos_db = []

@server_action
async def save_todo(text: str) -> dict:
    """Save a new todo to the database."""
    todo = {
        "id": len(todos_db) + 1,
        "text": text,
        "done": False
    }
    todos_db.append(todo)
    return todo

@server_action
async def load_todos() -> list:
    """Load all todos from database."""
    return todos_db

@server_action
async def toggle_todo(todo_id: int) -> dict:
    """Toggle a todo's done status."""
    for todo in todos_db:
        if todo["id"] == todo_id:
            todo["done"] = not todo["done"]
            return todo
    return {"error": "Not found"}

# ============================================
# Components
# ============================================

@component
def TodoInput(on_add):
    """Input component for adding new todos."""
    new_todo = Signal("")
    
    async def add():
        text = new_todo()
        if text.strip():
            await on_add(text)
            new_todo.set("")
    
    return div(class_="todo-input")[
        input_(
            type="text",
            placeholder="What needs to be done?",
            value=new_todo,
            onchange=lambda e: new_todo.set(e.target.value),
        ),
        button(onclick=add, class_="add-btn")["➕ Add"]
    ]

@component
def TodoItem(todo, on_toggle):
    """Single todo item component."""
    return li(
        class_=f"todo-item {'done' if todo['done'] else ''}",
        onclick=lambda: on_toggle(todo["id"])
    )[
        span(class_="checkbox")[
            "✅" if todo["done"] else "⬜"
        ],
        span(class_="text")[todo["text"]]
    ]

@component
def TodoStats(todos):
    """Statistics about todos."""
    total = Computed(lambda: len(todos()))
    done = Computed(lambda: sum(1 for t in todos() if t["done"]))
    remaining = Computed(lambda: total() - done())
    
    return div(class_="todo-stats")[
        span()[f"📊 Total: {total()}"],
        span()[f"✅ Done: {done()}"],
        span()[f"📝 Remaining: {remaining()}"],
    ]

# ============================================
# Page
# ============================================

@page(title="PyNext Todo App")
async def index():
    todos = Signal([])
    loading = Signal(True)
    
    # Load todos on page load
    async def init():
        loaded = await load_todos()
        todos.set(loaded)
        loading.set(False)
    
    await init()
    
    async def add_todo(text):
        todo = await save_todo(text)
        todos.update(lambda t: t + [todo])
    
    async def handle_toggle(todo_id):
        result = await toggle_todo(todo_id)
        if "error" not in result:
            todos.update(lambda t: [
                result if todo["id"] == todo_id else todo
                for todo in t
            ])
    
    if loading():
        return div(class_="loading")["Loading..."]
    
    return div(class_="app")[
        h1()["📝 PyNext Todo"],
        
        TodoInput(on_add=add_todo),
        TodoStats(todos=todos),
        
        ul(class_="todo-list")[
            [TodoItem(todo=t, on_toggle=handle_toggle) for t in todos()]
            if todos() else p(class_="empty")["No todos yet! Add one above."]
        ],
    ]
```

### `static/styles.css`

```css
* {
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    margin: 0;
    padding: 2rem;
}

.app {
    max-width: 500px;
    margin: 0 auto;
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

h1 {
    margin: 0 0 1.5rem;
    color: #1a202c;
    text-align: center;
}

.todo-input {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.todo-input input {
    flex: 1;
    padding: 0.75rem 1rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.2s;
}

.todo-input input:focus {
    outline: none;
    border-color: #667eea;
}

.add-btn {
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

.add-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.todo-stats {
    display: flex;
    justify-content: space-around;
    padding: 1rem;
    background: #f7fafc;
    border-radius: 8px;
    margin-bottom: 1rem;
}

.todo-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.todo-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    border-bottom: 1px solid #e2e8f0;
    cursor: pointer;
    transition: background 0.2s;
}

.todo-item:hover {
    background: #f7fafc;
}

.todo-item.done .text {
    text-decoration: line-through;
    color: #a0aec0;
}

.checkbox {
    font-size: 1.25rem;
}

.empty {
    text-align: center;
    color: #a0aec0;
    padding: 2rem;
}

.loading {
    text-align: center;
    padding: 4rem;
    font-size: 1.25rem;
    color: #a0aec0;
}
```

---

## Understanding the Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PYNEXT ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  YOUR CODE                       PYNEXT                         OUTPUT       │
│  ─────────                       ──────                         ──────       │
│                                                                              │
│  ┌──────────────┐               ┌──────────────────────────────────────┐    │
│  │ pages/*.py   │──────────────►│ File Router                          │    │
│  │              │               │ Scans pages/, builds route tree      │    │
│  └──────────────┘               └──────────────────────────────────────┘    │
│                                              │                               │
│                                              ▼                               │
│  ┌──────────────┐               ┌──────────────────────────────────────┐    │
│  │ @page        │──────────────►│ Page Renderer                        │    │
│  │ def index(): │               │ Executes Python, generates HTML      │    │
│  │   ...        │               └──────────────────────────────────────┘    │
│  └──────────────┘                            │                               │
│                                              ▼                               │
│  ┌──────────────┐               ┌──────────────────────────────────────┐    │
│  │ Signal(0)    │──────────────►│ Hydration System                     │───►│ HTML + JS
│  │ Computed()   │               │ Embeds state for client-side pickup  │    │
│  └──────────────┘               └──────────────────────────────────────┘    │
│                                              │                               │
│                                              ▼                               │
│  ┌──────────────┐               ┌──────────────────────────────────────┐    │
│  │@server_action│──────────────►│ Action Registry                      │───►│ RPC API
│  │async def ... │               │ Registers functions for RPC calls    │    │
│  └──────────────┘               └──────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


                              CLIENT RUNTIME (~5KB)
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │ signals.js         │  │ resource.js        │  │ navigation.js     │    │
│  │ Reactive primitives│  │ Async data         │  │ Client routing    │    │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘    │
│                                                                              │
│  When page loads:                                                            │
│  1. Parse __PYNEXT_HYDRATION__ data                                         │
│  2. Recreate signals with server values                                      │
│  3. Attach event handlers                                                    │
│  4. Page is interactive!                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REQUEST LIFECYCLE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. BROWSER REQUEST                                                          │
│     GET /users/123                                                          │
│          │                                                                   │
│          ▼                                                                   │
│  2. ROUTER MATCHING                                                          │
│     pages/users/[id].py → params = {"id": "123"}                            │
│          │                                                                   │
│          ▼                                                                   │
│  3. MIDDLEWARE (optional)                                                    │
│     Check auth, rate limit, etc.                                            │
│          │                                                                   │
│          ▼                                                                   │
│  4. PAGE RENDERING                                                          │
│     • Execute @page function                                                │
│     • Signals collect values                                                │
│     • Components render to HTML                                              │
│          │                                                                   │
│          ▼                                                                   │
│  5. HYDRATION DATA                                                          │
│     • Serialize signal values                                                │
│     • Register event handlers                                                │
│     • Embed in <script> tag                                                 │
│          │                                                                   │
│          ▼                                                                   │
│  6. RESPONSE                                                                 │
│     HTML + embedded hydration data                                          │
│          │                                                                   │
│          ▼                                                                   │
│  7. BROWSER HYDRATION                                                        │
│     • Parse hydration data                                                   │
│     • Recreate signals                                                       │
│     • Attach event handlers                                                  │
│     • Interactive!                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Common Patterns

### Conditional Rendering

```python
# Show/hide based on condition
user = Signal(None)

div()[
    user() and div()[f"Welcome, {user()['name']}!"],
    not user() and a(href="/login")["Please log in"],
]

# Or using Show component
from pynext import Show

Show(when=user, fallback=a(href="/login")["Please log in"])[
    div()[f"Welcome, {user()['name']}!"]
]
```

### Lists and Iteration

```python
items = Signal(["Apple", "Banana", "Cherry"])

ul()[
    [li(key=i)[item] for i, item in enumerate(items())]
]
```

### Forms

```python
form_data = Signal({"name": "", "email": ""})

form(onsubmit=handle_submit)[
    input_(
        type="text",
        value=form_data()["name"],
        onchange=lambda e: form_data.update(
            lambda d: {**d, "name": e.target.value}
        )
    ),
    input_(
        type="email",
        value=form_data()["email"],
        onchange=lambda e: form_data.update(
            lambda d: {**d, "email": e.target.value}
        )
    ),
    button(type="submit")["Submit"]
]
```

### Loading States

```python
data = Signal(None)
loading = Signal(False)
error = Signal(None)

async def fetch_data():
    loading.set(True)
    error.set(None)
    try:
        result = await fetch_from_api()
        data.set(result)
    except Exception as e:
        error.set(str(e))
    finally:
        loading.set(False)

# In UI
div()[
    loading() and div(class_="spinner")["Loading..."],
    error() and div(class_="error")[f"Error: {error()}"],
    data() and div()[render_data(data())],
]
```

---

## What's Next

Now that you have the basics, explore these topics:

### Core Concepts

| Topic | Description | Link |
|-------|-------------|------|
| **Routing** | Dynamic routes, params, navigation | [ROUTING.md](ROUTING.md) |
| **Layouts** | Shared headers, footers, nesting | [LAYOUTS.md](LAYOUTS.md) |
| **State Management** | Signals, Stores, Effects | [STATE_MANAGEMENT.md](STATE_MANAGEMENT.md) |
| **HTML API** | All elements and attributes | [HTML_API.md](HTML_API.md) |

### Advanced Features

| Topic | Description | Link |
|-------|-------------|------|
| **Server Actions** | Full Python access from browser | [SERVER_ACTIONS.md](SERVER_ACTIONS.md) |
| **API Routes** | REST endpoints | [API_ROUTES.md](API_ROUTES.md) |
| **Middleware** | Auth, rate limiting, logging | [MIDDLEWARE.md](MIDDLEWARE.md) |
| **ISR** | Incremental Static Regeneration | [ISR.md](ISR.md) |

### Performance

| Topic | Description | Link |
|-------|-------------|------|
| **Islands** | Selective hydration | [ISLANDS.md](ISLANDS.md) |
| **Streaming** | Progressive rendering | [STREAMING_SUSPENSE.md](STREAMING_SUSPENSE.md) |
| **Hydration** | Server-to-client state | [HYDRATION.md](HYDRATION.md) |

### Example Projects

```bash
# Run the built-in example app
cd example
pynext dev
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Use a different port
pynext dev --port 3001
```

#### Module Not Found

```bash
# Reinstall in development mode
pip install -e .
```

#### Hot Reload Not Working

- Check that files are in `pages/` or `components/`
- Ensure no syntax errors in your Python files
- Restart the dev server

#### Signal Not Updating UI

```python
# Make sure you're calling the signal in the template
count = Signal(0)

# ❌ Wrong - just referencing, not calling
span()[count]  # This works for display

# ✅ Right - when you need the value in logic
if count() > 10:  # Call it to get the value
    ...
```

#### Server Action Not Working

```python
# Make sure it's async and decorated
@server_action
async def my_action():  # Must be async
    ...
```

### Getting Help

- **GitHub Issues:** Report bugs and feature requests
- **Discussions:** Ask questions and share ideas
- **Discord:** Real-time community chat

---

## Summary

You've learned:

1. ✅ What PyNext is and why it exists
2. ✅ Installing PyNext and creating a project
3. ✅ Understanding the project structure
4. ✅ Building components with HTML elements
5. ✅ Adding reactivity with Signals
6. ✅ Creating pages with file-based routing
7. ✅ Calling Python from the browser with Server Actions
8. ✅ Running the development server
9. ✅ Understanding the architecture

**Welcome to PyNext!** 🐍⚡

You're now ready to build reactive web applications entirely in Python. Start with the [Routing Guide](ROUTING.md) to learn more about navigation, or jump into [State Management](STATE_MANAGEMENT.md) for advanced reactivity patterns.
