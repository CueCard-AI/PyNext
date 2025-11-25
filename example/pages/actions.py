"""
PyNext Example - Server Actions

Demonstrates server actions with Python package access.
"""

from pynext import (
    page, component, server_action, Signal,
    div, h1, h2, p, button, pre, code, a, span, input_
)
import os
import sys
import json
from datetime import datetime


@server_action
async def get_system_info() -> dict:
    """Get system information from the server."""
    return {
        "python_version": sys.version,
        "platform": sys.platform,
        "cwd": os.getcwd(),
        "timestamp": datetime.now().isoformat(),
        "env_vars": len(os.environ),
    }


@server_action
async def calculate_fibonacci(n: int) -> dict:
    """Calculate Fibonacci numbers on the server."""
    def fib(n):
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    start = datetime.now()
    result = fib(min(n, 100))  # Cap at 100 for safety
    end = datetime.now()
    
    return {
        "n": n,
        "result": result,
        "computation_time_ms": (end - start).total_seconds() * 1000,
    }


@server_action
async def process_text(text: str) -> dict:
    """Process text on the server with Python string methods."""
    return {
        "original": text,
        "uppercase": text.upper(),
        "lowercase": text.lower(),
        "word_count": len(text.split()),
        "char_count": len(text),
        "reversed": text[::-1],
    }


@component
def ActionDemo(title: str, description: str, action, button_text: str = "Run"):
    """Reusable component for demonstrating an action."""
    result = Signal(None)
    loading = Signal(False)
    
    async def run_action():
        loading.set(True)
        try:
            data = await action()
            result.set(data)
        except Exception as e:
            result.set({"error": str(e)})
        finally:
            loading.set(False)
    
    return div(class_="action-card")[
        h2()[title],
        p()[description],
        button(
            class_="btn btn-primary",
            onclick=run_action,
            disabled=loading
        )[
            span()[loading() and "Loading..." or button_text]
        ],
        div(class_="result")[
            result() and pre()[code()[json.dumps(result(), indent=2)]]
        ]
    ]


@page(title="Server Actions - PyNext")
def actions():
    """Page demonstrating server actions."""
    
    # State for interactive demos
    fib_n = Signal(20)
    fib_result = Signal(None)
    
    text_input = Signal("Hello, PyNext!")
    text_result = Signal(None)
    
    sys_info = Signal(None)
    
    return div(class_="container")[
        div(class_="nav-back")[
            a(href="/")["← Back to Home"]
        ],
        
        h1()["Server Actions"],
        p(class_="intro")[
            "Server actions let you call Python functions from the client. "
            "These functions run on the server with full Python package access."
        ],
        
        # System Info Demo
        div(class_="action-card")[
            h2()["📊 System Information"],
            p()["Fetch system info from the server."],
            button(
                class_="btn btn-primary",
                onclick=get_system_info
            )["Get System Info"],
            div(id="sysinfo-result", class_="result")[""]
        ],
        
        # Fibonacci Demo
        div(class_="action-card")[
            h2()["🔢 Fibonacci Calculator"],
            p()["Calculate Fibonacci numbers server-side."],
            div(class_="input-group")[
                input_(
                    type="number",
                    value=fib_n,
                    min="1",
                    max="100",
                    class_="input",
                    placeholder="Enter n"
                ),
                button(
                    class_="btn btn-primary",
                    onclick=lambda: calculate_fibonacci(int(fib_n()))
                )["Calculate"]
            ],
            div(id="fib-result", class_="result")[""]
        ],
        
        # Text Processing Demo
        div(class_="action-card")[
            h2()["📝 Text Processing"],
            p()["Process text using Python string methods."],
            div(class_="input-group")[
                input_(
                    type="text",
                    value=text_input,
                    class_="input input-wide",
                    placeholder="Enter text to process"
                ),
                button(
                    class_="btn btn-primary",
                    onclick=lambda: process_text(text_input())
                )["Process"]
            ],
            div(id="text-result", class_="result")[""]
        ],
        
        # Code example
        div(class_="code-example")[
            h2()["How it works"],
            pre()[code()['''
from pynext import server_action
import pandas as pd  # Use any Python package!

@server_action
async def analyze_data(file_path: str) -> dict:
    """This runs on the server with full Python access."""
    df = pd.read_csv(file_path)
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "summary": df.describe().to_dict()
    }

# In your component, just call it:
button(onclick=lambda: analyze_data("/data/sales.csv"))["Analyze"]
''']]
        ],
        
        ACTIONS_STYLES
    ]


from pynext.core.html import Element
style = Element("style")

ACTIONS_STYLES = style()["""
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

h1 {
    font-size: 36px;
    margin-bottom: 16px;
    color: #1f2937;
}

.intro {
    font-size: 18px;
    color: #6b7280;
    margin-bottom: 32px;
}

.action-card {
    background: white;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 24px;
}

.action-card h2 {
    margin: 0 0 8px 0;
    font-size: 20px;
    color: #1f2937;
}

.action-card p {
    color: #6b7280;
    margin: 0 0 16px 0;
}

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
    background: #6366f1;
    color: white;
}

.btn-primary:hover {
    background: #4f46e5;
}

.btn-primary:disabled {
    background: #a5b4fc;
    cursor: not-allowed;
}

.input-group {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}

.input {
    padding: 10px 16px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    font-size: 14px;
    width: 120px;
}

.input-wide {
    flex: 1;
}

.input:focus {
    outline: none;
    border-color: #6366f1;
}

.result {
    margin-top: 16px;
    min-height: 20px;
}

.result pre {
    background: #1f2937;
    color: #e5e7eb;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 0;
    font-size: 13px;
}

.code-example {
    background: #f9fafb;
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

.code-example h2 {
    margin: 0 0 16px 0;
    font-size: 18px;
    color: #1f2937;
}

.code-example pre {
    background: #1f2937;
    color: #e5e7eb;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 0;
    font-size: 13px;
}

.code-example code {
    font-family: 'Fira Code', monospace;
}
"""]

