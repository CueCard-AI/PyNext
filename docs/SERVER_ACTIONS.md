# Server Actions in PyNext

Server Actions provide a seamless way to execute Python code on the server from client-side events. Unlike traditional REST APIs, server actions feel like calling a local function while giving you full access to Python's ecosystem.

## Table of Contents

- [Introduction to Server Actions](#introduction-to-server-actions)
- [Architecture Overview](#architecture-overview)
- [Using Python Packages](#using-python-packages)
- [How PyNext Executes Actions](#how-pynext-executes-actions)
- [Request/Response Flow](#requestresponse-flow)
- [Code Generation Details](#code-generation-details)
- [Error Handling](#error-handling)
- [Security Considerations](#security-considerations)
- [Advanced Patterns](#advanced-patterns)
- [Performance](#performance)
- [Debugging](#debugging)
- [API Reference](#api-reference)

---

## Introduction to Server Actions

### What Are Server Actions?

Server actions are Python functions decorated with `@server_action` that can be called directly from client-side event handlers. They execute on the server with full access to:

- **Any Python package** (pandas, numpy, scikit-learn, etc.)
- **File system** (read/write files, process uploads)
- **Databases** (SQLAlchemy, MongoDB, Redis, etc.)
- **External APIs** (with your server's credentials)
- **System resources** (CPU-intensive computations)

```python
from pynext import server_action, page, div, button
import pandas as pd
import numpy as np

@server_action
async def analyze_sales_data(year: int) -> dict:
    """This runs on the server with full Python access."""
    # Use pandas - not available in browser!
    df = pd.read_csv(f"/data/sales_{year}.csv")
    
    # Complex analysis
    monthly_totals = df.groupby('month')['revenue'].sum()
    growth_rate = monthly_totals.pct_change().mean()
    
    # Use numpy
    forecast = np.polyfit(range(12), monthly_totals.values, 2)
    
    return {
        "total_revenue": float(df['revenue'].sum()),
        "growth_rate": float(growth_rate),
        "best_month": monthly_totals.idxmax(),
        "forecast_trend": forecast.tolist(),
    }

@page
def dashboard():
    return div()[
        button(onclick=lambda: analyze_sales_data(2024))[
            "Analyze 2024 Sales"
        ]
    ]
```

### Why Server Actions vs Traditional APIs?

| Aspect | Traditional REST API | Server Actions |
|--------|---------------------|----------------|
| **Setup** | Define routes, handlers, serializers | Single decorator |
| **Type safety** | Manual validation | Python type hints |
| **Calling** | fetch() with URL, headers, body | Direct function call |
| **Boilerplate** | ~20-50 lines per endpoint | ~5 lines |
| **Discovery** | Swagger/OpenAPI docs | IDE autocomplete |
| **Refactoring** | Update URL + client code | Rename function |

### Comparison with Next.js Server Actions

| Feature | Next.js | PyNext |
|---------|---------|--------|
| Language | JavaScript/TypeScript | Python |
| Syntax | `"use server"` directive | `@server_action` decorator |
| Ecosystem | Node.js packages | Python packages (pandas, ML, etc.) |
| Execution | Edge/Node runtime | Python interpreter |
| Streaming | Built-in | Manual (via SSE) |
| Validation | Zod/manual | Pydantic/type hints |

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PyNext Application                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CLIENT (Browser)                             │   │
│  │                                                                      │   │
│  │   ┌──────────────────┐    ┌──────────────────┐                     │   │
│  │   │   Button Click   │───▶│  __pynext__.     │                     │   │
│  │   │   onclick=action │    │  callAction()    │                     │   │
│  │   └──────────────────┘    └────────┬─────────┘                     │   │
│  │                                    │                                │   │
│  └────────────────────────────────────┼────────────────────────────────┘   │
│                                       │                                     │
│                                       │ HTTP POST                           │
│                                       │ /_pynext/action                     │
│                                       │ {actionId, args}                    │
│                                       │                                     │
│  ┌────────────────────────────────────┼────────────────────────────────┐   │
│  │                         SERVER (Python)                              │   │
│  │                                    │                                 │   │
│  │   ┌────────────────────────────────▼─────────────────────────────┐  │   │
│  │   │                    FastAPI Endpoint                           │  │   │
│  │   │                    /_pynext/action                            │  │   │
│  │   └────────────────────────────────┬─────────────────────────────┘  │   │
│  │                                    │                                 │   │
│  │   ┌────────────────────────────────▼─────────────────────────────┐  │   │
│  │   │                    Action Registry                            │  │   │
│  │   │                                                               │  │   │
│  │   │   actions = {                                                 │  │   │
│  │   │     "action_abc123": <ServerAction: analyze_sales_data>,     │  │   │
│  │   │     "action_def456": <ServerAction: save_user>,              │  │   │
│  │   │     ...                                                       │  │   │
│  │   │   }                                                           │  │   │
│  │   └────────────────────────────────┬─────────────────────────────┘  │   │
│  │                                    │                                 │   │
│  │   ┌────────────────────────────────▼─────────────────────────────┐  │   │
│  │   │                    Action Execution                           │  │   │
│  │   │                                                               │  │   │
│  │   │   @server_action                                              │  │   │
│  │   │   async def analyze_sales_data(year):                        │  │   │
│  │   │       import pandas as pd  ◄── Full Python access!           │  │   │
│  │   │       df = pd.read_csv(...)                                  │  │   │
│  │   │       return {"result": ...}                                 │  │   │
│  │   │                                                               │  │   │
│  │   └────────────────────────────────┬─────────────────────────────┘  │   │
│  │                                    │                                 │   │
│  └────────────────────────────────────┼────────────────────────────────┘   │
│                                       │                                     │
│                                       │ HTTP Response                       │
│                                       │ {data: {...}, error: null}          │
│                                       │                                     │
│  ┌────────────────────────────────────┼────────────────────────────────┐   │
│  │                         CLIENT (Browser)                             │   │
│  │                                    │                                 │   │
│  │   ┌────────────────────────────────▼─────────────────────────────┐  │   │
│  │   │              Handle Response                                  │  │   │
│  │   │              Update UI / Signals                              │  │   │
│  │   └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JSON-RPC Protocol

PyNext uses a simplified JSON-RPC-like protocol:

**Request:**
```json
{
    "actionId": "action_abc123",
    "args": {
        "year": 2024,
        "include_forecast": true
    }
}
```

**Response (Success):**
```json
{
    "data": {
        "total_revenue": 1500000,
        "growth_rate": 0.15,
        "best_month": "December"
    },
    "error": null
}
```

**Response (Error):**
```json
{
    "data": null,
    "error": "File not found: /data/sales_2024.csv"
}
```

### Action Registry System

```python
# pynext/server/actions.py - Simplified view

class ActionRegistry:
    """Global registry of all server actions."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._actions = {}
        return cls._instance
    
    def register(self, action: "ServerAction"):
        """Register an action when @server_action is applied."""
        self._actions[action._action_id] = action
    
    def get(self, action_id: str) -> Optional["ServerAction"]:
        """Look up action by ID."""
        return self._actions.get(action_id)
    
    async def call(self, action_id: str, args: dict) -> Any:
        """Execute an action with given arguments."""
        action = self.get(action_id)
        if not action:
            raise ValueError(f"Unknown action: {action_id}")
        return await action.call(**args)

# Global singleton
_registry = ActionRegistry()
```

### Action Discovery and Registration

Actions are registered **at import time** when Python loads the module:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Action Registration Timeline                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Application starts                                                       │
│     │                                                                        │
│     ▼                                                                        │
│  2. Python imports page modules (pages/*.py)                                │
│     │                                                                        │
│     ▼                                                                        │
│  3. @server_action decorator executes                                       │
│     │                                                                        │
│     │   @server_action                                                      │
│     │   async def my_action():      ◄── Decorator runs HERE                 │
│     │       ...                                                             │
│     │                                                                        │
│     ▼                                                                        │
│  4. ServerAction object created                                             │
│     │                                                                        │
│     │   ServerAction(                                                       │
│     │       fn=my_action,                                                   │
│     │       action_id="action_abc123",  ◄── Unique ID generated            │
│     │       action_name="my_action"                                         │
│     │   )                                                                    │
│     │                                                                        │
│     ▼                                                                        │
│  5. Action registered in global registry                                    │
│     │                                                                        │
│     │   _registry.register(action)                                          │
│     │   # Now: _registry._actions["action_abc123"] = action                 │
│     │                                                                        │
│     ▼                                                                        │
│  6. Server ready to handle action calls                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Using Python Packages

### Full Python Ecosystem Access

Server actions run in a regular Python environment with access to **any installed package**:

```python
from pynext import server_action

# Data Science
@server_action
async def analyze_data(csv_path: str) -> dict:
    import pandas as pd
    import numpy as np
    from scipy import stats
    
    df = pd.read_csv(csv_path)
    
    return {
        "mean": float(df['value'].mean()),
        "std": float(df['value'].std()),
        "correlation": float(df['x'].corr(df['y'])),
        "normality_p": float(stats.normaltest(df['value'])[1]),
    }

# Machine Learning
@server_action
async def predict(features: list[float]) -> dict:
    import joblib
    import numpy as np
    
    model = joblib.load('/models/classifier.pkl')
    prediction = model.predict([features])
    probability = model.predict_proba([features])
    
    return {
        "class": int(prediction[0]),
        "confidence": float(probability[0].max()),
    }

# Image Processing
@server_action
async def process_image(image_base64: str) -> dict:
    from PIL import Image
    import io
    import base64
    
    # Decode image
    image_data = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_data))
    
    # Process
    image = image.resize((800, 600))
    image = image.convert('RGB')
    
    # Re-encode
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    
    return {
        "processed_image": base64.b64encode(buffer.getvalue()).decode(),
        "dimensions": image.size,
    }

# Web Scraping
@server_action
async def scrape_page(url: str) -> dict:
    import httpx
    from bs4 import BeautifulSoup
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    return {
        "title": soup.title.string if soup.title else None,
        "links": [a['href'] for a in soup.find_all('a', href=True)][:10],
        "headings": [h.text for h in soup.find_all(['h1', 'h2', 'h3'])][:5],
    }
```

### Async vs Sync Actions

**Async actions** (recommended for I/O operations):
```python
@server_action
async def fetch_user(user_id: int) -> dict:
    """Non-blocking I/O - other requests can be handled."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
    return response.json()
```

**Sync actions** (for CPU-bound work):
```python
@server_action
def compute_heavy(data: list) -> dict:
    """CPU-intensive - runs in thread pool to not block."""
    import numpy as np
    
    # Heavy computation
    result = np.linalg.eig(np.array(data))
    
    return {"eigenvalues": result[0].tolist()}
```

**How sync actions work internally:**
```python
# Inside ServerAction.call()
if self._is_async:
    result = await self._fn(**kwargs)
else:
    # Run sync function in thread pool to prevent blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: self._fn(**kwargs))
```

### Long-Running Operations

For operations that take > 30 seconds:

```python
from pynext import server_action, Signal
import asyncio

# Progress tracking
progress = Signal(0)
status = Signal("idle")

@server_action
async def process_large_dataset(file_path: str) -> dict:
    import pandas as pd
    
    status.set("loading")
    progress.set(0)
    
    # Load in chunks
    chunks = []
    total_rows = sum(1 for _ in open(file_path)) - 1
    processed = 0
    
    for chunk in pd.read_csv(file_path, chunksize=10000):
        chunks.append(process_chunk(chunk))
        processed += len(chunk)
        progress.set(int(processed / total_rows * 100))
        
        # Allow other tasks to run
        await asyncio.sleep(0)
    
    status.set("complete")
    return {"processed_rows": processed}
```

### File System Access

```python
from pynext import server_action
from pathlib import Path
import shutil

@server_action
async def list_files(directory: str) -> dict:
    """List files in a directory."""
    path = Path(directory)
    
    if not path.exists():
        return {"error": "Directory not found", "files": []}
    
    files = []
    for item in path.iterdir():
        files.append({
            "name": item.name,
            "is_dir": item.is_dir(),
            "size": item.stat().st_size if item.is_file() else None,
            "modified": item.stat().st_mtime,
        })
    
    return {"files": files}

@server_action
async def save_file(filename: str, content: str) -> dict:
    """Save content to a file."""
    path = Path("/uploads") / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    
    return {"saved": True, "path": str(path)}
```

### Database Connections

```python
from pynext import server_action
import asyncpg  # PostgreSQL
from motor.motor_asyncio import AsyncIOMotorClient  # MongoDB

# PostgreSQL
@server_action
async def get_users(limit: int = 10) -> dict:
    conn = await asyncpg.connect('postgresql://localhost/mydb')
    try:
        rows = await conn.fetch(
            'SELECT id, name, email FROM users LIMIT $1', 
            limit
        )
        return {"users": [dict(r) for r in rows]}
    finally:
        await conn.close()

# MongoDB
@server_action
async def search_products(query: str) -> dict:
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.mystore
    
    cursor = db.products.find(
        {"$text": {"$search": query}},
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(20)
    
    products = await cursor.to_list(length=20)
    
    # Convert ObjectId to string
    for p in products:
        p['_id'] = str(p['_id'])
    
    return {"products": products}

# SQLAlchemy (async)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

engine = create_async_engine("postgresql+asyncpg://localhost/mydb")
async_session = sessionmaker(engine, class_=AsyncSession)

@server_action
async def create_order(user_id: int, items: list) -> dict:
    async with async_session() as session:
        order = Order(user_id=user_id, items=items)
        session.add(order)
        await session.commit()
        
        return {"order_id": order.id}
```

---

## How PyNext Executes Actions

### Action Decorator Internals

```python
# pynext/server/actions.py

def server_action(
    fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    validate: bool = True,
) -> Union[ServerAction, Callable[[Callable], ServerAction]]:
    """
    Decorator to define a server action.
    
    When applied to a function:
    1. Wraps function in ServerAction class
    2. Generates unique action ID
    3. Registers with global registry
    4. Returns ServerAction (callable wrapper)
    """
    def decorator(fn: Callable) -> ServerAction:
        return ServerAction(fn, name=name, validate=validate)
    
    if fn is not None:
        return decorator(fn)
    return decorator


class ServerAction:
    """Wrapper that makes a Python function callable from the client."""
    
    _is_server_action = True  # Marker for identification
    
    def __init__(
        self,
        fn: Callable,
        *,
        name: Optional[str] = None,
        validate: bool = True,
    ):
        self._fn = fn
        self._action_name = name or fn.__name__
        self._action_id = f"action_{uuid.uuid4().hex[:8]}"  # Unique ID
        self._validate = validate
        self._is_async = asyncio.iscoroutinefunction(fn)
        
        # Preserve function metadata
        functools.update_wrapper(self, fn)
        
        # REGISTER WITH GLOBAL REGISTRY
        _registry.register(self)
    
    async def call(self, **kwargs) -> Any:
        """Execute the action (called by RPC handler)."""
        # Validate arguments
        if self._validate:
            sig = inspect.signature(self._fn)
            try:
                sig.bind(**kwargs)
            except TypeError as e:
                raise ValueError(f"Invalid arguments: {e}")
        
        # Execute
        if self._is_async:
            result = await self._fn(**kwargs)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self._fn(**kwargs)
            )
        
        # Ensure JSON-serializable
        try:
            orjson.dumps(result)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Result not JSON-serializable: {e}")
        
        return result
    
    def get_client_code(self) -> str:
        """Generate JavaScript code for calling this action."""
        return f"__pynext__.callAction('{self._action_id}', event)"
```

### Unique Action ID Generation

```python
import uuid

# Each @server_action gets a unique ID
action_id = f"action_{uuid.uuid4().hex[:8]}"

# Examples:
# action_a1b2c3d4
# action_e5f6g7h8
# action_i9j0k1l2

# This ID is:
# 1. Embedded in the HTML for event handlers
# 2. Sent from client in RPC requests
# 3. Used to look up the action in registry
```

### Handler Code Generation

When an action is used in an `onclick`:

```python
@server_action
async def save_data(value: str):
    return {"saved": True}

# In component
button(onclick=save_data)["Save"]
```

The HTML builder generates:

```python
# Inside html.py _render_attrs()

if _is_server_action(value):
    action_id = value._action_id
    action_name = value._action_name
    
    # Register with render context
    if ctx:
        ctx.register_action(action_name, action_id, {})
    
    # Generate handler code
    handler_code = f"__pynext__.callAction('{action_id}', event)"
    
    # Register event
    ctx.register_event(element_id, event_type, handler_code)
```

Resulting HTML:

```html
<button id="el_xyz789">Save</button>

<script>
window.__PYNEXT_HYDRATION__ = {
    "events": {
        "el_xyz789": {
            "click": "__pynext__.callAction('action_a1b2c3d4', event)"
        }
    },
    "actions": {
        "action_a1b2c3d4": {
            "name": "save_data",
            "id": "action_a1b2c3d4"
        }
    }
};
</script>
```

### Client-Side Proxy Generation

The JavaScript runtime creates callable proxies:

```javascript
// signals.js

async function callAction(actionId, event, args = {}) {
    if (event) {
        event.preventDefault();
    }

    try {
        const response = await fetch('/_pynext/action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                actionId,
                args
            })
        });

        if (!response.ok) {
            throw new Error(`Action failed: ${response.statusText}`);
        }

        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }

        return result.data;
    } catch (error) {
        console.error('Server action error:', error);
        throw error;
    }
}
```

---

## Request/Response Flow

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Complete Action Flow                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. USER EVENT                                                              │
│     └── User clicks button                                                  │
│                                                                              │
│  2. EVENT HANDLER                                                           │
│     └── onclick fires, calls registered handler:                            │
│         __pynext__.callAction('action_abc123', event)                       │
│                                                                              │
│  3. JAVASCRIPT RUNTIME                                                      │
│     └── callAction() function:                                              │
│         a. Prevent default event behavior                                   │
│         b. Build request payload: {actionId, args}                          │
│         c. Send POST to /_pynext/action                                     │
│                                                                              │
│  4. NETWORK                                                                 │
│     └── HTTP POST request                                                   │
│         POST /_pynext/action HTTP/1.1                                       │
│         Content-Type: application/json                                      │
│         {"actionId": "action_abc123", "args": {"year": 2024}}              │
│                                                                              │
│  5. FASTAPI ENDPOINT                                                        │
│     └── @app.post("/_pynext/action")                                       │
│         a. Parse request body (Pydantic validation)                         │
│         b. Call handle_action_request()                                     │
│                                                                              │
│  6. ACTION HANDLER                                                          │
│     └── handle_action_request():                                            │
│         a. Extract actionId and args                                        │
│         b. Look up action in registry                                       │
│         c. Call action.call(**args)                                         │
│                                                                              │
│  7. ACTION EXECUTION                                                        │
│     └── ServerAction.call():                                                │
│         a. Validate arguments against function signature                    │
│         b. Execute function (async or in thread pool)                       │
│         c. Verify result is JSON-serializable                               │
│         d. Return result                                                    │
│                                                                              │
│  8. RESPONSE                                                                │
│     └── Build JSON response:                                                │
│         {"data": {...}, "error": null}                                      │
│         or                                                                  │
│         {"data": null, "error": "..."}                                      │
│                                                                              │
│  9. NETWORK                                                                 │
│     └── HTTP response back to client                                        │
│                                                                              │
│ 10. JAVASCRIPT RUNTIME                                                      │
│     └── callAction() receives response:                                     │
│         a. Parse JSON                                                       │
│         b. Check for errors                                                 │
│         c. Return data to caller                                            │
│                                                                              │
│ 11. UI UPDATE                                                               │
│     └── Caller handles result:                                              │
│         a. Update signals/state                                             │
│         b. Trigger re-renders                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FastAPI Endpoint

```python
# pynext/server/app.py

class ActionRequest(BaseModel):
    """Pydantic model for action requests."""
    actionId: str
    args: dict[str, Any] = {}

@app.post("/_pynext/action", tags=["Server Actions"])
async def handle_action(action: ActionRequest) -> JSONResponse:
    """Handle server action RPC calls."""
    try:
        result = await handle_action_request(action.model_dump())
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse(
            {"data": None, "error": f"Action failed: {e}"},
            status_code=500,
        )
```

### Request Handler

```python
# pynext/server/actions.py

async def handle_action_request(request_data: dict) -> dict:
    """
    Handle an incoming action request.
    
    Expected format:
        {"actionId": "action_xxx", "args": {...}}
    
    Returns:
        {"data": <result>, "error": null}
        or
        {"data": null, "error": "error message"}
    """
    try:
        action_id = request_data.get("actionId")
        args = request_data.get("args", {})
        
        if not action_id:
            return {"data": None, "error": "Missing actionId"}
        
        # Look up and execute action
        result = await _registry.call(action_id, args)
        
        return {"data": result, "error": None}
        
    except ValueError as e:
        return {"data": None, "error": str(e)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"data": None, "error": f"Server error: {type(e).__name__}"}
```

---

## Code Generation Details

### How onclick Handlers Are Transformed

**Python code:**
```python
@server_action
async def submit_form(data: dict):
    return await save_to_db(data)

@page
def my_page():
    return form()[
        input_(type="text", name="username"),
        button(onclick=submit_form, type="submit")["Submit"]
    ]
```

**Transformation pipeline:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Handler Transformation                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 1: Python Component Rendering                                         │
│  ─────────────────────────────────────                                      │
│                                                                              │
│  button(onclick=submit_form)["Submit"]                                      │
│                    │                                                         │
│                    └── submit_form is a ServerAction object                 │
│                                                                              │
│  STEP 2: HTML Builder Detects Server Action                                 │
│  ─────────────────────────────────────────────                              │
│                                                                              │
│  # In _render_attrs():                                                      │
│  if _is_server_action(value):                                               │
│      action_id = value._action_id    # "action_abc123"                      │
│      handler_code = f"__pynext__.callAction('{action_id}', event)"         │
│                                                                              │
│  STEP 3: Event Registration                                                 │
│  ─────────────────────────────                                              │
│                                                                              │
│  ctx.register_event(                                                        │
│      element_id="el_xyz789",                                                │
│      event_type="click",                                                    │
│      handler_code="__pynext__.callAction('action_abc123', event)"          │
│  )                                                                          │
│                                                                              │
│  STEP 4: HTML Output                                                        │
│  ─────────────────────                                                      │
│                                                                              │
│  <button id="el_xyz789" type="submit">Submit</button>                       │
│                                                                              │
│  STEP 5: Hydration Data                                                     │
│  ────────────────────────                                                   │
│                                                                              │
│  window.__PYNEXT_HYDRATION__ = {                                            │
│      events: {                                                              │
│          "el_xyz789": {                                                     │
│              "click": "__pynext__.callAction('action_abc123', event)"      │
│          }                                                                  │
│      },                                                                     │
│      actions: {                                                             │
│          "action_abc123": {                                                 │
│              "name": "submit_form",                                         │
│              "id": "action_abc123"                                          │
│          }                                                                  │
│      }                                                                      │
│  };                                                                         │
│                                                                              │
│  STEP 6: Client-Side Hydration                                              │
│  ───────────────────────────────                                            │
│                                                                              │
│  // signals.js hydrate()                                                    │
│  for (const [elementId, handlers] of Object.entries(data.events)) {        │
│      const element = document.getElementById(elementId);                    │
│      for (const [eventType, handlerCode] of Object.entries(handlers)) {    │
│          const handler = new Function('event', handlerCode);               │
│          element.addEventListener(eventType, handler);                      │
│      }                                                                      │
│  }                                                                          │
│                                                                              │
│  // Result: Button now has click handler that calls server action          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Actions with Arguments

```python
@server_action
async def update_item(item_id: int, quantity: int):
    return await db.update(item_id, quantity=quantity)

# With lambda to pass arguments
button(onclick=lambda: update_item(item["id"], 5))["Set to 5"]
```

This generates:
```javascript
// Handler code includes the bound arguments
"__pynext__.callAction('action_def456', event, {item_id: 123, quantity: 5})"
```

### Action Results Updating Signals

```python
@server_action
async def load_users() -> list:
    return await db.get_users()

users = Signal([])
loading = Signal(False)

@component
def UserList():
    async def fetch():
        loading.set(True)
        try:
            result = await load_users()
            users.set(result)
        finally:
            loading.set(False)
    
    return div()[
        button(onclick=fetch)["Load Users"],
        loading() and span()["Loading..."],
        ul()[
            [li()[u["name"]] for u in users()]
        ]
    ]
```

---

## Error Handling

### Server-Side Exceptions

```python
@server_action
async def risky_operation(data: dict) -> dict:
    try:
        # Operation that might fail
        result = await process(data)
        return {"success": True, "result": result}
    
    except ValidationError as e:
        # Return structured error
        return {"success": False, "error": "validation", "details": str(e)}
    
    except DatabaseError as e:
        # Log and return generic error
        logger.error(f"Database error: {e}")
        return {"success": False, "error": "database", "details": "Database unavailable"}
    
    except Exception as e:
        # Unexpected error
        logger.exception("Unexpected error in risky_operation")
        raise  # Let framework handle it
```

### Exception Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Error Handling Flow                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Exception in Action                                                         │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  handle_action_request()                             │   │
│  │                                                                      │   │
│  │  try:                                                                │   │
│  │      result = await _registry.call(action_id, args)                 │   │
│  │  except ValueError as e:                                            │   │
│  │      # Validation/argument errors                                   │   │
│  │      return {"data": None, "error": str(e)}                        │   │
│  │  except Exception as e:                                             │   │
│  │      # Unexpected errors                                            │   │
│  │      traceback.print_exc()  # Log full traceback                   │   │
│  │      return {"data": None, "error": f"Server error: {type(e)}"}    │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Response Types:                                                            │
│                                                                              │
│  SUCCESS:     {"data": {...}, "error": null}                               │
│  USER ERROR:  {"data": null, "error": "Invalid input: ..."}               │
│  SERVER ERROR: {"data": null, "error": "Server error: DatabaseError"}      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Client-Side Error Handling

```javascript
// In signals.js

async function callAction(actionId, event, args = {}) {
    try {
        const response = await fetch('/_pynext/action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({actionId, args})
        });

        // Network error or server error status
        if (!response.ok) {
            throw new Error(`Action failed: ${response.statusText}`);
        }

        const result = await response.json();
        
        // Application-level error from action
        if (result.error) {
            throw new Error(result.error);
        }

        return result.data;
        
    } catch (error) {
        console.error('Server action error:', error);
        
        // Re-throw for caller to handle
        throw error;
    }
}
```

### Handling Errors in Components

```python
from pynext import Signal, component, div, button, span

error = Signal(None)
loading = Signal(False)
data = Signal(None)

@server_action
async def fetch_data():
    return await api.get_data()

@component
def DataComponent():
    async def load():
        loading.set(True)
        error.set(None)
        
        try:
            result = await fetch_data()
            data.set(result)
        except Exception as e:
            error.set(str(e))
        finally:
            loading.set(False)
    
    return div()[
        button(onclick=load, disabled=loading())["Load Data"],
        
        loading() and span(class_="loading")["Loading..."],
        
        error() and div(class_="error")[
            span()[f"Error: {error()}"],
            button(onclick=load)["Retry"]
        ],
        
        data() and div(class_="data")[
            # Render data
        ]
    ]
```

---

## Security Considerations

### Input Validation

**Always validate inputs:**

```python
from pydantic import BaseModel, validator
from typing import Optional

class CreateUserInput(BaseModel):
    username: str
    email: str
    age: Optional[int] = None
    
    @validator('username')
    def username_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v
    
    @validator('email')
    def email_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v

@server_action
async def create_user(username: str, email: str, age: int = None) -> dict:
    # Validate with Pydantic
    validated = CreateUserInput(username=username, email=email, age=age)
    
    # Now safe to use
    user = await db.create_user(
        username=validated.username,
        email=validated.email,
        age=validated.age
    )
    
    return {"user_id": user.id}
```

### Authentication Patterns

```python
from pynext import server_action
from functools import wraps

def require_auth(fn):
    """Decorator to require authentication for an action."""
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        # Get current user from context (implementation depends on your auth)
        user = get_current_user()
        
        if not user:
            return {"error": "Authentication required", "code": "UNAUTHORIZED"}
        
        # Add user to kwargs
        kwargs['_current_user'] = user
        
        return await fn(*args, **kwargs)
    
    return wrapper

def require_role(role: str):
    """Decorator to require a specific role."""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                return {"error": "Authentication required", "code": "UNAUTHORIZED"}
            
            if user.role != role:
                return {"error": f"Role '{role}' required", "code": "FORBIDDEN"}
            
            kwargs['_current_user'] = user
            return await fn(*args, **kwargs)
        
        return wrapper
    return decorator

# Usage
@server_action
@require_auth
async def get_profile(_current_user) -> dict:
    return {"profile": _current_user.to_dict()}

@server_action
@require_role("admin")
async def delete_user(user_id: int, _current_user) -> dict:
    await db.delete_user(user_id)
    return {"deleted": True}
```

### Rate Limiting

```python
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps

# Simple in-memory rate limiter
rate_limit_store = defaultdict(list)

def rate_limit(max_calls: int, period_seconds: int):
    """Rate limit an action."""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # Get client identifier (IP, user ID, etc.)
            client_id = get_client_id()
            
            now = datetime.now()
            window_start = now - timedelta(seconds=period_seconds)
            
            # Clean old entries
            rate_limit_store[client_id] = [
                t for t in rate_limit_store[client_id]
                if t > window_start
            ]
            
            # Check rate limit
            if len(rate_limit_store[client_id]) >= max_calls:
                return {
                    "error": "Rate limit exceeded",
                    "code": "RATE_LIMITED",
                    "retry_after": period_seconds
                }
            
            # Record this call
            rate_limit_store[client_id].append(now)
            
            return await fn(*args, **kwargs)
        
        return wrapper
    return decorator

# Usage
@server_action
@rate_limit(max_calls=10, period_seconds=60)
async def send_email(to: str, subject: str, body: str) -> dict:
    await email_service.send(to, subject, body)
    return {"sent": True}
```

### Path Traversal Protection

```python
from pathlib import Path

ALLOWED_BASE = Path("/app/uploads")

@server_action
async def read_file(filename: str) -> dict:
    # Sanitize path
    safe_path = ALLOWED_BASE / Path(filename).name
    
    # Verify it's within allowed directory
    try:
        safe_path.resolve().relative_to(ALLOWED_BASE.resolve())
    except ValueError:
        return {"error": "Invalid file path"}
    
    if not safe_path.exists():
        return {"error": "File not found"}
    
    return {"content": safe_path.read_text()}
```

---

## Advanced Patterns

### Streaming Responses

For large data or real-time updates, use Server-Sent Events:

```python
from pynext import server_action
from starlette.responses import StreamingResponse
import asyncio
import json

# Note: This requires custom endpoint, not @server_action

async def stream_generator(query: str):
    """Generate streaming results."""
    for i in range(100):
        result = await process_chunk(query, i)
        
        yield f"data: {json.dumps(result)}\n\n"
        
        await asyncio.sleep(0.1)
    
    yield "data: {\"done\": true}\n\n"

# Custom endpoint for streaming
@app.get("/api/stream")
async def stream_results(query: str):
    return StreamingResponse(
        stream_generator(query),
        media_type="text/event-stream"
    )
```

### Progress Updates

```python
from pynext import Signal, server_action
import asyncio

# Progress signal (shared between actions)
progress_store = {}

@server_action
async def start_long_task(task_id: str, data: dict) -> dict:
    """Start a long-running task."""
    
    async def run_task():
        progress_store[task_id] = {"status": "running", "progress": 0}
        
        for i in range(100):
            await process_step(data, i)
            progress_store[task_id]["progress"] = i + 1
            await asyncio.sleep(0.1)
        
        progress_store[task_id]["status"] = "complete"
    
    asyncio.create_task(run_task())
    
    return {"task_id": task_id, "status": "started"}

@server_action
async def get_task_progress(task_id: str) -> dict:
    """Check task progress."""
    if task_id not in progress_store:
        return {"error": "Task not found"}
    
    return progress_store[task_id]
```

### File Uploads

```python
from pynext import server_action, page, div, form, input_, button
import base64
from pathlib import Path

@server_action
async def upload_file(filename: str, content_base64: str) -> dict:
    """Handle file upload (base64 encoded)."""
    
    # Decode content
    content = base64.b64decode(content_base64)
    
    # Validate
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        return {"error": "File too large"}
    
    # Save file
    upload_path = Path("/uploads") / filename
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    upload_path.write_bytes(content)
    
    return {
        "uploaded": True,
        "path": str(upload_path),
        "size": len(content)
    }

@page
def upload_page():
    return div()[
        form()[
            input_(type="file", id="file-input"),
            button(onclick=handle_upload)["Upload"]
        ]
    ]

# Client-side JavaScript would read file and call upload_file
# with base64-encoded content
```

### Background Tasks

```python
from pynext import server_action
import asyncio
from datetime import datetime

# Task queue (in production, use Celery/RQ/etc.)
task_queue = asyncio.Queue()
task_results = {}

async def task_worker():
    """Background worker processing tasks."""
    while True:
        task = await task_queue.get()
        
        try:
            result = await task["fn"](*task["args"], **task["kwargs"])
            task_results[task["id"]] = {"status": "complete", "result": result}
        except Exception as e:
            task_results[task["id"]] = {"status": "error", "error": str(e)}
        
        task_queue.task_done()

# Start worker on app startup
asyncio.create_task(task_worker())

@server_action
async def enqueue_task(task_type: str, **kwargs) -> dict:
    """Add task to background queue."""
    import uuid
    
    task_id = uuid.uuid4().hex
    
    task_fn = {
        "send_email": send_email_task,
        "process_data": process_data_task,
        "generate_report": generate_report_task,
    }.get(task_type)
    
    if not task_fn:
        return {"error": f"Unknown task type: {task_type}"}
    
    await task_queue.put({
        "id": task_id,
        "fn": task_fn,
        "args": [],
        "kwargs": kwargs,
    })
    
    task_results[task_id] = {"status": "pending"}
    
    return {"task_id": task_id}

@server_action
async def check_task(task_id: str) -> dict:
    """Check background task status."""
    if task_id not in task_results:
        return {"error": "Task not found"}
    
    return task_results[task_id]
```

---

## Performance

### Connection Pooling

```python
# Database connection pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

# Create engine with connection pool
engine = create_async_engine(
    "postgresql+asyncpg://localhost/mydb",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

@server_action
async def get_data():
    async with engine.connect() as conn:
        result = await conn.execute(query)
        return result.fetchall()
```

### HTTP Client Pooling

```python
import httpx

# Shared client with connection pooling
http_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)

@server_action
async def fetch_external_api(endpoint: str) -> dict:
    response = await http_client.get(f"https://api.example.com/{endpoint}")
    return response.json()
```

### Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache
cache = {}
cache_ttl = {}

def cached(ttl_seconds: int = 60):
    """Cache action results."""
    def decorator(fn):
        async def wrapper(*args, **kwargs):
            # Create cache key
            key = f"{fn.__name__}:{args}:{kwargs}"
            
            # Check cache
            if key in cache:
                if datetime.now() < cache_ttl[key]:
                    return cache[key]
            
            # Execute and cache
            result = await fn(*args, **kwargs)
            cache[key] = result
            cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)
            
            return result
        
        return wrapper
    return decorator

@server_action
@cached(ttl_seconds=300)  # Cache for 5 minutes
async def get_expensive_data() -> dict:
    # This result will be cached
    return await expensive_computation()
```

### Batching Multiple Actions

```python
from pynext import server_action

@server_action
async def batch_actions(actions: list[dict]) -> dict:
    """Execute multiple actions in one request."""
    results = {}
    
    for action_spec in actions:
        action_id = action_spec["action"]
        args = action_spec.get("args", {})
        
        try:
            result = await _registry.call(action_id, args)
            results[action_id] = {"data": result, "error": None}
        except Exception as e:
            results[action_id] = {"data": None, "error": str(e)}
    
    return results

# Client-side:
# await __pynext__.callAction('batch_actions', event, {
#     actions: [
#         {action: 'action_1', args: {...}},
#         {action: 'action_2', args: {...}},
#     ]
# })
```

---

## Debugging

### Action Logging

```python
import logging
from functools import wraps

logger = logging.getLogger("pynext.actions")

def logged_action(fn):
    """Add logging to an action."""
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        action_name = fn.__name__
        
        logger.info(f"Action started: {action_name}", extra={
            "action": action_name,
            "args": args,
            "kwargs": kwargs,
        })
        
        try:
            result = await fn(*args, **kwargs)
            
            logger.info(f"Action completed: {action_name}", extra={
                "action": action_name,
                "result_keys": list(result.keys()) if isinstance(result, dict) else None,
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Action failed: {action_name}", extra={
                "action": action_name,
                "error": str(e),
            }, exc_info=True)
            raise
    
    return wrapper

@server_action
@logged_action
async def my_action(data: dict) -> dict:
    return await process(data)
```

### DevTools Integration

```javascript
// Add to signals.js for browser DevTools

window.__PYNEXT_DEVTOOLS__ = {
    ...window.__PYNEXT_DEVTOOLS__,
    
    actions: {
        history: [],
        
        // Track all action calls
        track: (actionId, args, result, duration) => {
            window.__PYNEXT_DEVTOOLS__.actions.history.push({
                actionId,
                args,
                result,
                duration,
                timestamp: Date.now(),
            });
            
            // Keep last 100 calls
            if (window.__PYNEXT_DEVTOOLS__.actions.history.length > 100) {
                window.__PYNEXT_DEVTOOLS__.actions.history.shift();
            }
        },
        
        // Get action history
        getHistory: () => window.__PYNEXT_DEVTOOLS__.actions.history,
        
        // Clear history
        clear: () => {
            window.__PYNEXT_DEVTOOLS__.actions.history = [];
        }
    }
};

// Modify callAction to track calls
const originalCallAction = callAction;
callAction = async (actionId, event, args = {}) => {
    const start = performance.now();
    
    try {
        const result = await originalCallAction(actionId, event, args);
        
        const duration = performance.now() - start;
        window.__PYNEXT_DEVTOOLS__.actions.track(actionId, args, result, duration);
        
        return result;
    } catch (error) {
        const duration = performance.now() - start;
        window.__PYNEXT_DEVTOOLS__.actions.track(actionId, args, {error: error.message}, duration);
        throw error;
    }
};
```

### Debug Endpoint

```python
# In development only
@app.get("/_pynext/debug/actions")
async def debug_actions():
    """List all registered actions for debugging."""
    if not app.debug:
        raise HTTPException(status_code=404)
    
    return {
        "actions": [
            {
                "id": action._action_id,
                "name": action._action_name,
                "is_async": action._is_async,
                "params": [
                    {"name": p.name, "default": str(p.default) if p.default != p.empty else None}
                    for p in inspect.signature(action._fn).parameters.values()
                ]
            }
            for action in _registry._actions.values()
        ]
    }
```

---

## API Reference

### @server_action Decorator

```python
def server_action(
    fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    validate: bool = True,
) -> Union[ServerAction, Callable[[Callable], ServerAction]]:
    """
    Decorator to define a server action.
    
    Args:
        fn: The function to wrap (when used without parentheses)
        name: Custom name for the action (default: function name)
        validate: Whether to validate arguments against function signature
    
    Returns:
        ServerAction wrapper that can be used in onclick handlers
    
    Examples:
        @server_action
        async def my_action(data: dict) -> dict:
            return {"processed": True}
        
        @server_action(name="custom_name", validate=True)
        def sync_action(value: int) -> dict:
            return {"value": value * 2}
    """
```

### ServerAction Class

```python
class ServerAction:
    """
    Wrapper for server-executable functions.
    
    Attributes:
        _action_id: str - Unique identifier
        _action_name: str - Human-readable name
        _is_server_action: bool - Always True (marker)
        _is_async: bool - Whether the wrapped function is async
    
    Methods:
        call(**kwargs) -> Any: Execute the action
        get_client_code() -> str: Get JavaScript call code
    """
```

### ActionRegistry Class

```python
class ActionRegistry:
    """
    Global registry of server actions.
    
    Methods:
        register(action: ServerAction) -> None
        get(action_id: str) -> Optional[ServerAction]
        get_by_name(name: str) -> Optional[ServerAction]
        call(action_id: str, args: dict) -> Any
        list_actions() -> list[dict]
    """
```

### JavaScript API

```javascript
// Call a server action
__pynext__.callAction(actionId: string, event?: Event, args?: object) -> Promise<any>

// Example
const result = await __pynext__.callAction('action_abc123', event, {
    year: 2024,
    includeDetails: true
});
```

---

## Next Steps

- **[State + Data Integration](STATE_DATA_INTEGRATION.md)** - How Server Actions update Signals and UI
- See [State Management](STATE_MANAGEMENT.md) for managing action results
- See [API Routes](API_ROUTES.md) for REST endpoints comparison
- See [React Integration](REACT_INTEGRATION.md) for using actions with React components
- Check the [Example App](../example/pages/actions.py) for working examples

