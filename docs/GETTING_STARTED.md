# Getting Started with PyNext

Welcome to PyNext! This guide will walk you through creating your first PyNext application from scratch.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Create Your First Project](#create-your-first-project)
- [Project Structure](#project-structure)
- [Your First Component](#your-first-component)
- [Adding Reactivity](#adding-reactivity)
- [Creating Pages](#creating-pages)
- [Server Actions](#server-actions)
- [Running the Dev Server](#running-the-dev-server)
- [Next Steps](#next-steps)

---

## Prerequisites

Before starting, ensure you have:

- **Python 3.10+** installed
- **Node.js 16+** (for npm package bundling)
- A code editor (VS Code recommended)

```bash
# Check versions
python --version  # Python 3.10+
node --version    # v16.0.0+
```

---

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install pynext
```

### Option 2: Install from Source

```bash
git clone https://github.com/yourusername/pynext.git
cd pynext
pip install -e .
```

### Verify Installation

```bash
pynext --version
# PyNext 0.1.0
```

---

## Create Your First Project

Use the CLI to scaffold a new project:

```bash
# Create a new project
pynext init my-app

# Navigate to project
cd my-app

# Install dependencies
pip install -r requirements.txt
```

This creates:

```
my-app/
├── pages/
│   └── index.py          # Home page
├── components/
│   └── __init__.py       # Shared components
├── static/
│   └── styles.css        # Static assets
├── pynext.config.py      # Configuration
└── requirements.txt      # Python dependencies
```

---

## Project Structure

Let's understand each part:

```
my-app/
│
├── pages/                    # File-based routing
│   ├── index.py             # → /
│   ├── about.py             # → /about
│   └── users/
│       ├── index.py         # → /users
│       └── [id].py          # → /users/:id (dynamic)
│
├── components/               # Reusable components
│   ├── __init__.py
│   ├── header.py
│   └── footer.py
│
├── static/                   # Static files (CSS, images)
│   ├── styles.css
│   └── logo.png
│
├── pynext.config.py         # Framework configuration
│   # - npm_packages
│   # - server settings
│   # - build options
│
└── requirements.txt         # Python dependencies
```

### Key Concepts

| Folder | Purpose |
|--------|---------|
| `pages/` | Each `.py` file becomes a route automatically |
| `components/` | Shared, reusable UI components |
| `static/` | Static assets served at `/static/` |
| `pynext.config.py` | Configuration file |

---

## Your First Component

Open `pages/index.py` and let's build a simple component:

```python
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
# 1. Import elements and decorators
from pynext import page, div, h1, p

# 2. Use @page to define a page component
@page(title="Page Title")
def index():
    
    # 3. Return HTML elements
    return div(class_="container")[  # Attributes in ()
        h1()["Hello"],                # Children in []
        p()["World"]
    ]
```

### Element Syntax

```python
# Element with attributes
div(class_="box", id="main")

# Element with children
div()["Hello World"]

# Element with both
div(class_="box")[
    "Text content",
    span()["Nested element"]
]

# Multiple children
ul()[
    li()["Item 1"],
    li()["Item 2"],
    li()["Item 3"]
]
```

---

## Adding Reactivity

PyNext uses **Signals** for fine-grained reactivity. Let's create a counter:

```python
from pynext import page, component, Signal, div, h1, button, span

@component
def Counter():
    # Create a reactive signal
    count = Signal(0)
    
    return div(class_="counter")[
        h1()["Counter"],
        
        # Display the count - updates automatically!
        span(class_="count")[count],
        
        # Button with onclick handler
        button(onclick=lambda: count.update(lambda x: x + 1))[
            "Increment"
        ],
        
        button(onclick=lambda: count.set(0))[
            "Reset"
        ]
    ]

@page(title="Counter Demo")
def index():
    return div()[
        Counter()
    ]
```

### How Signals Work

```python
# Create a signal with initial value
count = Signal(0)

# Read the value (call it like a function)
current = count()  # 0

# Set a new value
count.set(5)

# Update based on previous value
count.update(lambda x: x + 1)

# When used in HTML, updates are automatic:
span()[count]  # Re-renders when count changes
```

### Computed Values

```python
from pynext import Signal, Computed

count = Signal(5)

# Computed values auto-update when dependencies change
doubled = Computed(lambda: count() * 2)
is_even = Computed(lambda: count() % 2 == 0)

div()[
    p()[f"Count: ", count],
    p()[f"Doubled: ", doubled],
    p()[f"Is Even: ", is_even]
]
```

---

## Creating Pages

### Basic Page

Create `pages/about.py`:

```python
from pynext import page, div, h1, p, a

@page(title="About Us")
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

Visit `http://localhost:3000/about` to see it.

### Dynamic Routes

Create `pages/users/[id].py`:

```python
from pynext import page, div, h1, p, get_params

@page(title="User Profile")
def user_profile():
    # Get route parameters
    params = get_params()
    user_id = params.get("id", "unknown")
    
    return div()[
        h1()[f"User Profile"],
        p()[f"Viewing user: {user_id}"]
    ]
```

Visit `http://localhost:3000/users/123` → Shows "Viewing user: 123"

### Nested Routes

```
pages/
├── blog/
│   ├── index.py          # /blog
│   ├── [slug].py         # /blog/:slug
│   └── [slug]/
│       └── comments.py   # /blog/:slug/comments
```

---

## Server Actions

Server actions let you call Python functions from the browser:

```python
from pynext import page, server_action, Signal, div, button, p

# This runs on the SERVER
@server_action
async def get_server_time() -> dict:
    from datetime import datetime
    return {
        "time": datetime.now().isoformat(),
        "message": "Hello from the server!"
    }

@server_action
async def calculate_factorial(n: int) -> dict:
    import math
    return {
        "input": n,
        "result": math.factorial(n)
    }

# This runs in the BROWSER
result = Signal(None)

@page(title="Server Actions Demo")
def index():
    async def fetch_time():
        data = await get_server_time()
        result.set(data)
    
    return div()[
        button(onclick=fetch_time)["Get Server Time"],
        
        result() and div()[
            p()[f"Time: {result()['time']}"],
            p()[result()["message"]]
        ]
    ]
```

### Using Python Packages

Server actions have access to the full Python ecosystem:

```python
from pynext import server_action

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
async def generate_chart_data() -> dict:
    import numpy as np
    
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    
    return {
        "x": x.tolist(),
        "y": y.tolist()
    }
```

---

## Running the Dev Server

Start the development server:

```bash
pynext dev
```

Output:
```
🚀 PyNext dev server starting...
   
   ➜  Local:   http://localhost:3000
   ➜  Network: http://192.168.1.100:3000
   
   Ready in 150ms
```

### Dev Server Features

- **Hot Reload**: Changes to files automatically refresh
- **Error Overlay**: Clear error messages in browser
- **API Docs**: Visit `/_pynext/docs` for FastAPI documentation

### Options

```bash
# Custom port
pynext dev --port 8080

# Custom host
pynext dev --host 0.0.0.0

# Debug mode
pynext dev --debug
```

---

## Complete Example

Here's a complete mini-application:

### `pages/index.py`

```python
from pynext import (
    page, component, Signal, Computed,
    div, h1, h2, p, button, input_, ul, li, span
)
from pynext import server_action

# Server action for data
@server_action
async def save_todo(text: str) -> dict:
    # In real app, save to database
    print(f"Saving todo: {text}")
    return {"saved": True, "id": hash(text)}

# Reactive state
todos = Signal([])
new_todo = Signal("")

@component
def TodoInput():
    async def add_todo():
        text = new_todo()
        if text.strip():
            # Call server action
            result = await save_todo(text)
            
            # Update local state
            todos.update(lambda t: t + [{"id": result["id"], "text": text}])
            new_todo.set("")
    
    return div(class_="todo-input")[
        input_(
            type="text",
            placeholder="What needs to be done?",
            value=new_todo,
            onchange=lambda e: new_todo.set(e.target.value)
        ),
        button(onclick=add_todo)["Add"]
    ]

@component
def TodoList():
    # Computed value
    count = Computed(lambda: len(todos()))
    
    return div(class_="todo-list")[
        h2()[f"Tasks (", count, ")"],
        
        ul()[
            [li(key=todo["id"])[todo["text"]] for todo in todos()]
        ] if todos() else p()["No tasks yet!"]
    ]

@page(title="PyNext Todo App")
def index():
    return div(class_="app")[
        h1()["PyNext Todo"],
        TodoInput(),
        TodoList()
    ]
```

### `static/styles.css`

```css
.app {
    max-width: 600px;
    margin: 2rem auto;
    padding: 1rem;
    font-family: system-ui, sans-serif;
}

.todo-input {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.todo-input input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.todo-input button {
    padding: 0.5rem 1rem;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.todo-list ul {
    list-style: none;
    padding: 0;
}

.todo-list li {
    padding: 0.5rem;
    border-bottom: 1px solid #eee;
}
```

---

## Next Steps

Now that you have the basics, explore:

### Documentation

- **[Routing Guide](ROUTING.md)** - Dynamic routes, params, navigation
- **[HTML API](HTML_API.md)** - All elements and attributes
- **[State Management](STATE_MANAGEMENT.md)** - Signals, Stores, Effects
- **[Server Actions](SERVER_ACTIONS.md)** - Full Python access from client
- **[Configuration](CONFIGURATION.md)** - All config options

### Tutorials

1. Build a blog with markdown support
2. Create a dashboard with charts
3. Add authentication
4. Deploy to production

### Example Projects

Check the `example/` directory for complete applications:

```bash
# Run the example app
cd example
pynext dev
```

---

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
pynext dev --port 3001
```

**Module not found:**
```bash
pip install -e .  # Reinstall in dev mode
```

**Hot reload not working:**
- Check file is in `pages/` or `components/`
- Ensure no syntax errors

### Getting Help

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share ideas
- **Discord**: Real-time community chat

---

## Summary

You've learned:

1. ✅ Installing PyNext
2. ✅ Creating a project with `pynext init`
3. ✅ Understanding project structure
4. ✅ Building components with HTML elements
5. ✅ Adding reactivity with Signals
6. ✅ Creating pages with file-based routing
7. ✅ Calling server actions with Python packages
8. ✅ Running the dev server

Welcome to PyNext! 🐍⚡

