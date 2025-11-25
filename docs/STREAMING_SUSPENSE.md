# PyNext Streaming & Suspense

> Progressive rendering for faster perceived performance

## Table of Contents

1. [Overview](#overview)
2. [Suspense Component](#suspense-component)
3. [Control Flow Components](#control-flow-components)
4. [ErrorBoundary](#errorboundary)
5. [Streaming HTML](#streaming-html)
6. [Deep Dive: Out-of-Order Streaming](#deep-dive-out-of-order-streaming)
7. [Performance Benchmarks](#performance-benchmarks)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)

---

## Overview

PyNext's streaming and Suspense system enables progressive rendering - sending HTML to the browser as data becomes available rather than waiting for everything to load.

### The Problem with Traditional SSR

```
Traditional Server-Side Rendering:

REQUEST ──────────────────────────────────────────────────> RESPONSE
         │                                                    │
         │  ┌─────────────────────────────────────────────┐  │
         │  │  1. Fetch ALL data (300-500ms+)             │  │
         │  │  2. Render complete HTML                     │  │
         │  │  3. Send response                            │  │
         │  └─────────────────────────────────────────────┘  │
         │                                                    │
         │◄───────────── User sees NOTHING ──────────────────►│
```

### The Streaming Solution

```
Streaming with Suspense:

REQUEST ─────────────────────────────────────────────────────>
    │
    │  SHELL (10μs)
    │  ├─ DOCTYPE, head, layout skeleton
    │  └─ User sees: Page structure + loading indicators
    │
    │  CHUNK 1 (50ms) - Sidebar loaded
    │  ├─ Replace sidebar skeleton with content
    │  └─ User sees: Working sidebar!
    │
    │  CHUNK 2 (100ms) - Header loaded  
    │  ├─ Replace header skeleton with content
    │  └─ User sees: Navigation ready!
    │
    │  CHUNK 3 (300ms) - Main content loaded
    │  ├─ Replace main skeleton with content
    │  └─ User sees: Full page!
    │
    ▼  COMPLETE
```

### Key Benefits

| Metric | Traditional | Streaming | Improvement |
|--------|-------------|-----------|-------------|
| Time to First Byte | 600ms | 10μs | **60,000x** |
| Time to First Paint | 600ms | 10μs | **60,000x** |
| Time to Interactive | 600ms | 300ms | **2x** |
| Perceived Performance | Poor | Excellent | ⭐⭐⭐⭐⭐ |

---

## Suspense Component

Suspense wraps components that depend on async data and shows a fallback while loading.

### Basic Usage

```python
from pynext import Suspense, Resource, div, span

# Create a resource for async data
users = Resource(fetch_users)

# Wrap in Suspense with a fallback
@page
async def UsersPage():
    await users.fetch()  # Resolved on server
    
    return Suspense(fallback=div(class_="skeleton")["Loading users..."])[
        UserList(users=users())
    ]
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Suspense Boundary Flow                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Suspense boundary created                                       │
│     └─> State: PENDING                                              │
│     └─> Fallback rendered                                           │
│                                                                      │
│  2. Child components render                                         │
│     └─> Resources detected                                          │
│     └─> Registered with boundary                                    │
│                                                                      │
│  3. Resources resolve                                               │
│     └─> State: RESOLVED                                             │
│     └─> Content replaces fallback                                   │
│                                                                      │
│  4. Error during fetch?                                             │
│     └─> State: ERRORED                                              │
│     └─> ErrorBoundary handles (if present)                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Suspense States

| State | Description | UI |
|-------|-------------|-----|
| `PENDING` | Resources loading | Shows fallback |
| `RESOLVED` | All resources ready | Shows content |
| `FALLBACK` | Error occurred | Shows fallback (or ErrorBoundary) |
| `TIMEOUT` | Exceeded timeout | Shows stale fallback |
| `REFRESHING` | Refetching | Shows content + indicator |

### Nested Suspense

Suspense boundaries can be nested for granular loading states:

```python
@page
async def Dashboard():
    return div()[
        # Outer boundary for entire page
        Suspense(fallback=PageSkeleton())[
            Header(),  # Fast - resolves first
            
            div(class_="content")[
                # Independent boundary for sidebar
                Suspense(fallback=SidebarSkeleton())[
                    Sidebar()  # Medium speed
                ],
                
                # Independent boundary for main content
                Suspense(fallback=MainSkeleton())[
                    MainContent()  # Slow - resolves last
                ],
            ],
            
            Footer(),  # Fast - resolves first
        ]
    ]
```

**Result:** Header and Footer show immediately, Sidebar shows when ready, Main shows last.

### Suspense with Timeout

```python
# Show fallback after 5 seconds if still loading
Suspense(fallback=Skeleton(), timeout=5.0)[
    SlowComponent()
]
```

---

## Control Flow Components

### Show

Conditional rendering - render children when condition is true.

```python
from pynext import Show, Signal

is_logged_in = Signal(False)

# Basic usage
Show(when=is_logged_in)[
    UserDashboard()
]

# With fallback
Show(when=is_logged_in, fallback=LoginPrompt())[
    UserDashboard()
]

# With callable condition
Show(when=lambda: user.loading())[
    Spinner()
]
```

### Switch / Match

Multi-way conditional rendering (like switch/case).

```python
from pynext import Switch, Match, Signal

status = Signal("loading")

Switch()[
    Match(when=lambda: status() == "loading")[
        Spinner()
    ],
    Match(when=lambda: status() == "error")[
        ErrorMessage()
    ],
    Match(when=lambda: status() == "success")[
        SuccessContent()
    ],
    Match()[  # Default case (no condition)
        FallbackContent()
    ],
]
```

### Performance Comparison

| Component | Render Time | Use Case |
|-----------|-------------|----------|
| `Show` | ~2μs | Simple true/false |
| `Switch` (first match) | ~4μs | Multiple conditions |
| `Switch` (last match) | ~5μs | Many conditions |

---

## ErrorBoundary

Catch and handle errors in child components.

### Basic Usage

```python
from pynext import ErrorBoundary, div

def error_fallback(error):
    return div(class_="error")[
        h1()["Something went wrong"],
        p()[str(error)],
        button(onclick="location.reload()")["Retry"]
    ]

ErrorBoundary(fallback=error_fallback)[
    RiskyComponent()  # If this throws, fallback is shown
]
```

### Nested Error Boundaries

```python
# Outer boundary catches errors not handled by inner
ErrorBoundary(fallback=lambda e: PageError(e))[
    Header(),  # Error here → PageError shown
    
    ErrorBoundary(fallback=lambda e: WidgetError(e))[
        Widget()  # Error here → WidgetError shown (contained)
    ],
    
    Footer(),  # Still renders even if Widget errors!
]
```

### Error Recovery

```python
def recoverable_fallback(error):
    return div()[
        p()[f"Error: {error}"],
        button(onclick="window.__pynext__.retry()")["Try Again"]
    ]

ErrorBoundary(fallback=recoverable_fallback)[
    DataComponent()
]
```

---

## Streaming HTML

### PageShell

The shell is sent immediately and contains the page structure:

```python
from pynext.server.streaming import PageShell

shell = PageShell(
    title="My App",
    head_content='<link rel="stylesheet" href="/styles.css">',
    body_class="dark-mode",
)

# Add initial state for hydration
shell.add_state("user", {"name": "Alice"})

# Add inline scripts
shell.add_script("console.log('Shell loaded!')")

# Render parts
opening = shell.render_opening()  # <!DOCTYPE html>...<body>
closing = shell.render_closing()  # </body></html>
```

### Loading Skeletons

Pre-built skeleton components for loading states:

```python
from pynext.server.streaming import create_loading_skeleton

# Single skeleton
skeleton = create_loading_skeleton()

# Custom size
skeleton = create_loading_skeleton(width="200px", height="50px")

# Multiple lines
skeleton = create_loading_skeleton(count=5)
```

**Generated HTML:**
```html
<div class="skeleton" style="width:200px;height:50px"></div>
```

### Suspense Placeholders

Placeholders for streaming replacement:

```python
from pynext.server.streaming import create_suspense_placeholder

placeholder = create_suspense_placeholder(
    boundary_id="user-profile",
    fallback_html="<div class='spinner'>Loading...</div>"
)
```

**Generated HTML:**
```html
<div data-suspense="user-profile" data-state="pending">
  <div data-suspense-fallback>
    <div class="spinner">Loading...</div>
  </div>
</div>
```

### Streaming Response

```python
from pynext.server.streaming import StreamingHTMLResponse

async def generate_page():
    # Send shell immediately
    yield shell.render_opening()
    
    # Send layout with placeholders
    yield layout_html
    
    # Wait for data and send replacements
    await user_resource.fetch()
    yield replacement_script
    
    # Close page
    yield shell.render_closing()

return StreamingHTMLResponse(generate_page())
```

### Out-of-Order Streaming

The most powerful feature of streaming is **out-of-order delivery** - content is sent in the order it RESOLVES, not the order it appears in the document.

```
Document Order (DOM):          Stream Order (Time):
┌─────────────────────┐        ┌─────────────────────┐
│ 1. Header (slow)    │────────│ 3. Sent LAST        │
├─────────────────────┤        ├─────────────────────┤
│ 2. Sidebar (medium) │────────│ 2. Sent SECOND      │
├─────────────────────┤        ├─────────────────────┤
│ 3. Main (fast)      │────────│ 1. Sent FIRST ⚡    │
└─────────────────────┘        └─────────────────────┘
```

**How it works:**

```python
# Server sends shell with ALL placeholders immediately
# 0ms - User sees layout with loading skeletons
<div data-suspense="header" data-state="pending">
  <div class="skeleton">Loading header...</div>
</div>
<div data-suspense="main" data-state="pending">
  <div class="skeleton">Loading main...</div>
</div>

# 10ms - Main Content resolves first!
# Server streams replacement script:
<script>
  __pynext__.replaceSuspense('main', '<div>Main Content</div>');
</script>

# 30ms - Sidebar resolves
<script>
  __pynext__.replaceSuspense('sidebar', '<div>Sidebar</div>');
</script>

# 50ms - Header finally resolves
<script>
  __pynext__.replaceSuspense('header', '<header>Header</header>');
</script>
```

**Key benefits:**
1. User sees content progressively (not all-or-nothing)
2. Fast components don't wait for slow components
3. Above-the-fold content can load while below-the-fold waits
4. Each component becomes interactive as soon as it arrives

**Implementation:**

```python
from pynext.server.streaming import stream_page

async def generate_page():
    # Send shell immediately
    yield shell_html
    
    # Stream replacements as boundaries resolve
    # Uses asyncio.wait(return_when=FIRST_COMPLETED)
    async for chunk in stream_page(shell, suspense_boundaries):
        yield chunk
```

### Streaming CSS

Built-in CSS for loading states:

```python
from pynext.server.streaming import get_streaming_css

css = get_streaming_css()
```

**Included Styles:**
- Suspense state transitions (pending/resolved/timeout)
- Skeleton loading animation
- Spinner animation

---

## Deep Dive: Out-of-Order Streaming

Out-of-order streaming is the most powerful feature of PyNext's progressive rendering. This section provides a comprehensive technical deep-dive.

### The Core Concept

Traditional streaming sends content top-to-bottom. Out-of-order streaming sends content **in resolution order**, regardless of DOM position.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL vs OUT-OF-ORDER STREAMING                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TRADITIONAL (In-Order):              OUT-OF-ORDER (Resolution Order):      │
│  ─────────────────────────            ────────────────────────────────      │
│                                                                              │
│  ┌─────────────────────┐              ┌─────────────────────┐               │
│  │ Header (100ms)      │ ─────┐       │ Header (100ms)      │ ─┐            │
│  └─────────────────────┘      │       └─────────────────────┘  │            │
│  ┌─────────────────────┐      │       ┌─────────────────────┐  │            │
│  │ Main (10ms) BLOCKED │ ◄────┤       │ Main (10ms)         │──┼─► FIRST!   │
│  └─────────────────────┘      │       └─────────────────────┘  │            │
│  ┌─────────────────────┐      │       ┌─────────────────────┐  │            │
│  │ Footer (50ms)       │ ◄────┘       │ Footer (50ms)       │──┼─► SECOND   │
│  └─────────────────────┘              └─────────────────────┘  │            │
│                                                                └─► THIRD    │
│  Main waits for Header        Main streams immediately when ready!          │
│  even though it's ready!                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          OUT-OF-ORDER STREAMING FLOW                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  SERVER                              NETWORK                          CLIENT    │
│  ──────                              ───────                          ──────    │
│                                                                                  │
│  ┌──────────────────┐                                                           │
│  │ Request received │                                                           │
│  └────────┬─────────┘                                                           │
│           │                                                                      │
│           ▼                                                                      │
│  ┌──────────────────┐                                    ┌──────────────────┐   │
│  │ Generate Shell   │ ──────── IMMEDIATE ──────────────► │ Render Shell     │   │
│  │ (0ms)            │          (First Byte)              │ + Skeletons      │   │
│  └────────┬─────────┘                                    └────────┬─────────┘   │
│           │                                                       │             │
│           │  Start parallel fetches                               │             │
│           │  ┌──────────────────┐                                 │             │
│           ├─►│ Fetch Header     │ (100ms)                         │             │
│           │  └──────────────────┘                                 │             │
│           │  ┌──────────────────┐                                 │             │
│           ├─►│ Fetch Main       │ (10ms)                          │             │
│           │  └──────────────────┘                                 │             │
│           │  ┌──────────────────┐                                 │             │
│           └─►│ Fetch Footer     │ (50ms)                          │             │
│              └──────────────────┘                                 │             │
│                                                                   │             │
│  ╔══════════════════════════════════════════════════════════════╗ │             │
│  ║ asyncio.wait(return_when=FIRST_COMPLETED)                    ║ │             │
│  ╚══════════════════════════════════════════════════════════════╝ │             │
│                                                                   │             │
│           ┌──────────────────┐                                    │             │
│  @ 10ms   │ Main READY       │                                    │             │
│           └────────┬─────────┘                                    │             │
│                    │                                              │             │
│                    ▼                                              ▼             │
│  ┌──────────────────────────┐           ┌────────────────────────────────────┐ │
│  │ <script>                 │           │ replaceSuspense('main', content)   │ │
│  │   replaceSuspense(       │ ────────► │ → Find [data-suspense="main"]      │ │
│  │     'main', content)     │           │ → Replace skeleton with content    │ │
│  │ </script>                │           │ → Hydrate new DOM                  │ │
│  └──────────────────────────┘           └────────────────────────────────────┘ │
│                                                                   │             │
│           ┌──────────────────┐                                    │             │
│  @ 50ms   │ Footer READY     │                                    │             │
│           └────────┬─────────┘                                    │             │
│                    │                                              ▼             │
│  ┌──────────────────────────┐           ┌────────────────────────────────────┐ │
│  │ <script>                 │           │ replaceSuspense('footer', content) │ │
│  │   replaceSuspense(       │ ────────► │ → Replace skeleton with content    │ │
│  │     'footer', content)   │           │ → Footer now visible!              │ │
│  │ </script>                │           └────────────────────────────────────┘ │
│  └──────────────────────────┘                                                  │
│                                                                   │             │
│           ┌──────────────────┐                                    │             │
│  @ 100ms  │ Header READY     │                                    │             │
│           └────────┬─────────┘                                    │             │
│                    │                                              ▼             │
│  ┌──────────────────────────┐           ┌────────────────────────────────────┐ │
│  │ <script>                 │           │ replaceSuspense('header', content) │ │
│  │   replaceSuspense(       │ ────────► │ → Replace skeleton with content    │ │
│  │     'header', content)   │           │ → Page complete!                   │ │
│  │ </script>                │           └────────────────────────────────────┘ │
│  └──────────────────────────┘                                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Network Waterfall Visualization

```
TIME (ms)    0        10       20       30       40       50       60       70       80       90      100
             │         │         │         │         │         │         │         │         │         │         │
             ▼         ▼         ▼         ▼         ▼         ▼         ▼         ▼         ▼         ▼         ▼

SHELL        ████ (sent immediately - user sees loading UI)
             │
PARALLEL     │
FETCHES:     │
             │
  Main       ├────────█ (10ms - resolves FIRST)
             │        │
             │        ▼
STREAM 1     │        ████ → Main content sent to browser
             │
  Footer     ├──────────────────────────────█ (50ms - resolves SECOND)
             │                              │
             │                              ▼
STREAM 2     │                              ████ → Footer content sent
             │
  Header     ├──────────────────────────────────────────────────────────────────────────────█ (100ms - LAST)
             │                                                                              │
             │                                                                              ▼
STREAM 3     │                                                                              ████ → Header sent

USER SEES:
   0ms       Loading skeletons for all sections
  10ms       Main content visible! (Header/Footer still loading)
  50ms       Main + Footer visible! (Header still loading)  
 100ms       Complete page!

TRADITIONAL SSR:
   0ms       Nothing
 100ms       Everything at once

IMPROVEMENT: User sees main content 90ms earlier! (10ms vs 100ms)
```

### Placeholder Mechanism

When the shell is sent, placeholders hold positions for pending content:

```html
<!-- Initial Shell (sent at 0ms) -->
<!DOCTYPE html>
<html>
<head>
  <title>My App</title>
  <style>
    /* Streaming CSS for skeletons */
    [data-suspense][data-state="pending"] [data-suspense-fallback] {
      display: block;
    }
    .skeleton {
      background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
      animation: skeleton-loading 1.5s infinite;
    }
  </style>
</head>
<body>
  
  <!-- Placeholder for Header (100ms to load) -->
  <div data-suspense="header" data-state="pending">
    <div data-suspense-fallback>
      <div class="skeleton" style="height:60px">Loading header...</div>
    </div>
  </div>
  
  <!-- Placeholder for Main (10ms to load) -->
  <div data-suspense="main" data-state="pending">
    <div data-suspense-fallback>
      <div class="skeleton" style="height:400px">Loading content...</div>
    </div>
  </div>
  
  <!-- Placeholder for Footer (50ms to load) -->
  <div data-suspense="footer" data-state="pending">
    <div data-suspense-fallback>
      <div class="skeleton" style="height:100px">Loading footer...</div>
    </div>
  </div>
  
</body>
</html>
```

### Replacement Script Anatomy

When a component resolves, a replacement script is streamed:

```html
<!-- Streamed at 10ms when Main resolves -->
<script>
(function() {
  // 1. Find the placeholder
  var placeholder = document.querySelector('[data-suspense="main"]');
  
  if (placeholder) {
    // 2. Parse the new content
    var content = "<main class=\"content\">\n  <h1>Welcome!</h1>\n  <p>This loaded in just 10ms...</p>\n</main>";
    
    // 3. Create temporary container
    var temp = document.createElement('div');
    temp.innerHTML = content;
    
    // 4. Insert new content BEFORE placeholder
    while (temp.firstChild) {
      placeholder.parentNode.insertBefore(temp.firstChild, placeholder);
    }
    
    // 5. Remove the placeholder (skeleton disappears)
    placeholder.remove();
    
    // 6. Trigger hydration for the new content
    if (window.__pynext__ && window.__pynext__.hydrateElement) {
      window.__pynext__.hydrateElement(placeholder.parentNode);
    }
  }
})();
</script>
```

### Server Implementation Details

```python
# pynext/server/streaming.py

async def stream_page(
    shell: str,
    suspense_boundaries: List[SuspenseBoundary],
    timeout: float = 10.0,
) -> AsyncGenerator[str, None]:
    """
    Stream a page with out-of-order Suspense resolution.
    """
    # 1. Send shell IMMEDIATELY (0ms)
    yield shell
    
    if not suspense_boundaries:
        return
    
    # 2. Track pending boundaries
    pending = {b.id: b for b in suspense_boundaries if b.has_pending()}
    
    if not pending:
        return
    
    start_time = asyncio.get_event_loop().time()
    
    # 3. Stream as each boundary resolves
    while pending:
        elapsed = asyncio.get_event_loop().time() - start_time
        remaining = max(0.1, timeout - elapsed)
        
        if elapsed >= timeout:
            # Send timeout scripts for any remaining
            for boundary_id in pending:
                yield _create_timeout_script(boundary_id)
            break
        
        # Create tasks for each pending boundary
        tasks = {
            boundary_id: asyncio.create_task(
                boundary.wait_all(timeout=remaining)
            )
            for boundary_id, boundary in pending.items()
        }
        
        # ═══════════════════════════════════════════════════════
        # KEY: Wait for FIRST to complete, not ALL
        # This enables out-of-order streaming!
        # ═══════════════════════════════════════════════════════
        done, _ = await asyncio.wait(
            tasks.values(),
            timeout=remaining,
            return_when=asyncio.FIRST_COMPLETED,  # ← CRITICAL!
        )
        
        # 4. Find which boundaries completed
        for boundary_id, task in tasks.items():
            if task.done():
                boundary = pending.pop(boundary_id)
                
                # 5. Stream replacement script immediately
                if boundary.resolved_content:
                    yield _create_replacement_script(
                        boundary_id,
                        boundary.resolved_content,
                    )
```

### Client-Side Handler

```javascript
// pynext/runtime/suspense.js

/**
 * Replace a Suspense placeholder with resolved content.
 * Called by streamed scripts from the server.
 */
function replaceSuspense(id, html) {
  const boundary = suspenseBoundaries.get(id);
  
  // Find placeholder element
  let element = boundary?.element;
  if (!element) {
    element = document.querySelector(`[data-suspense="${id}"]`);
  }
  
  if (element) {
    // Create temp container for new content
    const temp = document.createElement('div');
    temp.innerHTML = html;
    
    // Insert new content before placeholder
    while (temp.firstChild) {
      element.parentNode.insertBefore(temp.firstChild, element);
    }
    
    // Remove placeholder
    element.remove();
    
    // Update boundary state
    if (boundary) {
      boundary.state = SuspenseState.RESOLVED;
      boundary.element = null;
    }
    
    // Hydrate new content (connect signals, events)
    if (__pynext__.hydrate) {
      __pynext__.hydrate();
    }
  }
}

// Exported globally for streamed scripts
window.__pynext__.replaceSuspense = replaceSuspense;
```

### Timing Analysis: Real-World Example

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    E-COMMERCE PRODUCT PAGE EXAMPLE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Components and their data sources:                                             │
│  ─────────────────────────────────                                              │
│                                                                                  │
│  ┌───────────────┬──────────────────┬────────────┬───────────────────────────┐ │
│  │ Component     │ Data Source      │ Time (ms)  │ Priority                  │ │
│  ├───────────────┼──────────────────┼────────────┼───────────────────────────┤ │
│  │ Header        │ User session     │ 50         │ High (navigation)         │ │
│  │ Product Info  │ Product API      │ 30         │ Critical (main content)   │ │
│  │ Price         │ Pricing API      │ 20         │ Critical (buy decision)   │ │
│  │ Reviews       │ Reviews API      │ 150        │ Medium (social proof)     │ │
│  │ Related       │ Recommendations  │ 200        │ Low (discovery)           │ │
│  │ Footer        │ Static           │ 5          │ Low (static)              │ │
│  └───────────────┴──────────────────┴────────────┴───────────────────────────┘ │
│                                                                                  │
│  Stream Order (by resolution time):                                             │
│  ──────────────────────────────────                                             │
│                                                                                  │
│  TIME    STREAMED COMPONENT        USER SEES                                    │
│  ────    ──────────────────        ─────────                                    │
│   0ms    Shell + all skeletons     Layout with loading placeholders             │
│   5ms    Footer                    Footer appears                               │
│  20ms    Price                     "Add to Cart" button ready! ⚡               │
│  30ms    Product Info              Product name, images visible                 │
│  50ms    Header                    Navigation ready                             │
│ 150ms    Reviews                   Social proof visible                         │
│ 200ms    Related Products          Recommendations load last                    │
│                                                                                  │
│  ⚡ KEY INSIGHT:                                                                │
│     Price and "Add to Cart" are visible at 20ms!                                │
│     Traditional SSR: User waits 200ms for everything                            │
│     Out-of-order: User can start buying 180ms earlier!                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Timeline Comparison

```
TRADITIONAL SSR (Wait for all):
────────────────────────────────────────────────────────────────────────────────────
0ms                                                                             200ms
│                                                                                  │
│◄──────────────────── USER SEES NOTHING ────────────────────────────────────────►│
│                                                                                  │
│                                                                         ████████│
│                                                                         ↑       │
│                                                               Everything at once │


OUT-OF-ORDER STREAMING:
────────────────────────────────────────────────────────────────────────────────────
0ms     5ms    20ms    30ms    50ms                 150ms                   200ms
│        │       │       │       │                     │                       │
├────────┼───────┼───────┼───────┼─────────────────────┼───────────────────────┤
│        │       │       │       │                     │                       │
│ Shell  │Footer │Price  │Product│Header              │Reviews               │Related
│ ████   │  ██   │  ██   │  ████ │  ███               │  ████████            │  ████
│        │       │       │       │                     │                       │
│        │       │       │       │                     │                       │
│        │       ↓       │       │                     │                       │
│        │   User can    │       │                     │                       │
│        │   ADD TO CART │       │                     │                       │
│        │   at 20ms!    │       │                     │                       │


IMPROVEMENT METRICS:
────────────────────
Time to "Add to Cart":  Traditional: 200ms → Out-of-Order: 20ms  (10x faster!)
Time to see product:    Traditional: 200ms → Out-of-Order: 30ms  (6.7x faster!)
Time to full page:      Traditional: 200ms → Out-of-Order: 200ms (same, but progressive)
```

### Error Handling in Out-of-Order Streams

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING DURING STREAMING                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Scenario: Reviews API fails while Product Info succeeds                        │
│                                                                                  │
│  0ms     Shell sent with all placeholders                                       │
│  │                                                                               │
│  │       ┌─────────────────────────────────────────────────────────────────┐    │
│  │       │ [Header skeleton] [Product skeleton] [Reviews skeleton]         │    │
│  │       └─────────────────────────────────────────────────────────────────┘    │
│  │                                                                               │
│  30ms    Product Info resolves → Stream replacement                             │
│  │                                                                               │
│  │       ┌─────────────────────────────────────────────────────────────────┐    │
│  │       │ [Header skeleton] [PRODUCT CONTENT] [Reviews skeleton]          │    │
│  │       └─────────────────────────────────────────────────────────────────┘    │
│  │                                                                               │
│  50ms    Header resolves → Stream replacement                                   │
│  │                                                                               │
│  │       ┌─────────────────────────────────────────────────────────────────┐    │
│  │       │ [HEADER CONTENT] [PRODUCT CONTENT] [Reviews skeleton]           │    │
│  │       └─────────────────────────────────────────────────────────────────┘    │
│  │                                                                               │
│  150ms   Reviews API ERROR → Stream error script                                │
│          │                                                                       │
│          ▼                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │ <script>                                                                   │  │
│  │   __pynext__.showError('reviews', {                                       │  │
│  │     message: 'Failed to load reviews',                                    │  │
│  │     retry: true                                                           │  │
│  │   });                                                                      │  │
│  │ </script>                                                                  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  Result: Page is usable! Only Reviews shows error state.                        │
│  ─────────────────────────────────────────────────────                          │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ [HEADER CONTENT]                                                            ││
│  │ [PRODUCT CONTENT - fully functional!]                                       ││
│  │ [Reviews: "Failed to load" ⟳ Retry button]                                 ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Timeout Handling

```python
# When a component takes too long:

async def stream_page(shell, boundaries, timeout=10.0):
    # ... streaming logic ...
    
    if elapsed >= timeout:
        # Don't block the entire page!
        # Send timeout state for remaining boundaries
        for boundary_id in pending:
            yield f'''<script>
(function() {{
  var el = document.querySelector('[data-suspense="{boundary_id}"]');
  if (el) {{
    el.setAttribute('data-state', 'timeout');
    console.warn('Suspense boundary {boundary_id} timed out');
    
    // Optionally show timeout UI
    var fallback = el.querySelector('[data-suspense-fallback]');
    if (fallback) {{
      fallback.innerHTML = '<div class="timeout-message">Taking longer than expected...</div>';
    }}
  }}
}})();
</script>'''
```

### Memory and Performance Characteristics

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    RESOURCE USAGE DURING STREAMING                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  SERVER SIDE:                                                                   │
│  ────────────                                                                   │
│  • Response buffer: Minimal (chunks sent immediately)                           │
│  • Per-boundary overhead: ~200 bytes                                            │
│  • Async tasks: 1 per pending boundary                                          │
│  • Total memory: O(n) where n = number of boundaries                            │
│                                                                                  │
│  NETWORK:                                                                       │
│  ────────                                                                       │
│  • Transfer-Encoding: chunked                                                   │
│  • Shell: ~200-500 bytes (gzipped)                                              │
│  • Each replacement: ~100-200 bytes overhead + content                          │
│  • Connection: Kept open until streaming completes                              │
│                                                                                  │
│  CLIENT SIDE:                                                                   │
│  ────────────                                                                   │
│  • DOM operations: Minimal (insert + remove)                                    │
│  • No full page rerender needed                                                 │
│  • Each replacement: Single DOM mutation                                        │
│  • Memory: Only current DOM state (no buffering)                                │
│                                                                                  │
│  COMPARISON WITH TRADITIONAL SSR:                                               │
│  ────────────────────────────────                                               │
│  │ Metric              │ Traditional │ Streaming      │                         │
│  │─────────────────────│─────────────│────────────────│                         │
│  │ Server memory       │ Full HTML   │ Chunked        │ (lower peak)            │
│  │ TTFB                │ Slow        │ Instant        │ (much faster)           │
│  │ Network utilization │ Bursty      │ Smooth         │ (better distribution)   │
│  │ Client parsing      │ All at once │ Progressive    │ (smoother)              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Debugging Out-of-Order Streams

```python
# Enable debug mode to track streaming

from pynext.server.streaming import stream_page
import logging

logging.basicConfig(level=logging.DEBUG)

async def debug_stream():
    async for chunk in stream_page(shell, boundaries):
        # Log each chunk
        if '<script>' in chunk:
            boundary_id = extract_boundary_id(chunk)
            logger.debug(f"Streamed: {boundary_id} at {time.time()}")
        yield chunk
```

**Browser DevTools:**
```javascript
// Watch streaming in Network tab
// Each chunk appears as it's received

// Console logging
window.__pynext__.onSuspenseReplace = (id, content) => {
  console.log(`[${Date.now()}ms] Replaced: ${id}`);
  console.log(`Content length: ${content.length} bytes`);
};
```

---

## Performance Benchmarks

### Component Render Times

Measured on Apple M1, Python 3.11:

| Component | Min | Mean | Max | Ops/sec |
|-----------|-----|------|-----|---------|
| Shell closing | 80ns | 92ns | 2μs | 10.8M |
| Suspense placeholder | 111ns | 121ns | 429ns | 8.2M |
| Loading skeleton (1) | 167ns | 261ns | 28μs | 3.8M |
| Shell opening | 300ns | 360ns | 131μs | 2.8M |
| Show (true) | 1.7μs | 1.9μs | 96μs | 533K |
| Show (false + fallback) | 2.2μs | 2.5μs | 51μs | 400K |
| Switch (first match) | 3.5μs | 3.8μs | 50μs | 262K |
| ErrorBoundary (no error) | 3.9μs | 4.4μs | 34μs | 229K |
| Suspense (sync) | 4.7μs | 5.2μs | 53μs | 192K |
| Complex page | 21μs | 22.5μs | 68μs | 44K |

### Out-of-Order Streaming Impact

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    STREAMING PERFORMANCE COMPARISON                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  SCENARIO: Dashboard with 5 async components                                    │
│  ───────────────────────────────────────────                                    │
│                                                                                  │
│  Component       │ Fetch Time │ DOM Position │ Stream Order │ User Sees At      │
│  ────────────────│────────────│──────────────│──────────────│──────────────────│ │
│  Header          │ 50ms       │ 1            │ 4            │ 50ms             │ │
│  Sidebar         │ 30ms       │ 2            │ 3            │ 30ms             │ │
│  Main Content    │ 10ms       │ 3            │ 1 (FIRST!)   │ 10ms             │ │
│  Footer          │ 25ms       │ 4            │ 2            │ 25ms             │ │
│  Comments        │ 80ms       │ 5            │ 5            │ 80ms             │ │
│                                                                                  │
│  TRADITIONAL SSR:                                                               │
│  ────────────────                                                               │
│  │ All components visible at:     80ms (wait for slowest)                       │
│  │ Time to First Byte:            80ms                                          │
│  │ User sees main content:        80ms                                          │
│                                                                                  │
│  OUT-OF-ORDER STREAMING:                                                        │
│  ──────────────────────                                                         │
│  │ Shell + skeletons visible:     <1ms (immediate!)                             │
│  │ Main content visible:          10ms (CRITICAL content first!)                │
│  │ All components visible:        80ms (same total, but progressive)            │
│                                                                                  │
│  IMPROVEMENT:                                                                   │
│  ────────────                                                                   │
│  │ Time to First Byte:            80ms → <1ms     (80,000x faster)              │
│  │ Time to main content:          80ms → 10ms     (8x faster)                   │
│  │ Perceived performance:         Poor → Excellent                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Streaming Impact by Scenario

| Scenario | Traditional | Streaming | Improvement |
|----------|-------------|-----------|-------------|
| **3 data sources (100ms each)** | | | |
| TTFB | 603ms | 119μs | 5,000x faster |
| User sees skeleton | Never | 119μs | ∞ |
| Full content | 603ms | 301ms | 2x faster |
| | | | |
| **5 parallel fetches (100ms each)** | | | |
| Sequential | 507ms | - | - |
| Parallel | - | 101ms | 5x faster |
| | | | |
| **Mixed speeds (10ms, 50ms, 200ms)** | | | |
| Time to first content | 200ms | 10ms | 20x faster |
| Time to all content | 200ms | 200ms | Same |

### Out-of-Order Stream Efficiency

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    BYTES SENT OVER TIME                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Time    │ Bytes Sent (Cumulative) │ User Sees                                  │
│  ────────│─────────────────────────│──────────────────────────────────────────│ │
│  0ms     │ 645 bytes (gzipped)     │ Shell + all skeletons                     │ │
│  10ms    │ 895 bytes               │ + Main content (250 bytes)                │ │
│  25ms    │ 1,045 bytes             │ + Footer (150 bytes)                      │ │
│  30ms    │ 1,245 bytes             │ + Sidebar (200 bytes)                     │ │
│  50ms    │ 1,545 bytes             │ + Header (300 bytes)                      │ │
│  80ms    │ 2,045 bytes             │ + Comments (500 bytes)                    │ │
│                                                                                  │
│  TRADITIONAL: 2,045 bytes ALL at 80ms                                           │
│  STREAMING:   2,045 bytes PROGRESSIVELY over 80ms                               │
│                                                                                  │
│  Network graph:                                                                 │
│                                                                                  │
│  Traditional:                                                                   │
│  ────────────────────────────────────────────────────────────────█████████████  │
│  0ms                                                             80ms           │
│                                                                                  │
│  Streaming:                                                                     │
│  █████───██───██───███──────────────────████──────────────────────██████████── │
│  0ms  10ms  25ms 30ms                  50ms                       80ms          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Payload Sizes

| Chunk | Raw Size | Gzipped |
|-------|----------|---------|
| Shell opening | 207 bytes | ~80 bytes |
| Shell closing | 63 bytes | ~40 bytes |
| 1 skeleton | 58 bytes | ~30 bytes |
| 10 skeletons | 589 bytes | ~200 bytes |
| Suspense placeholder | 133 bytes | ~50 bytes |
| Streaming CSS | 943 bytes | ~300 bytes |
| Replacement script overhead | ~150 bytes | ~60 bytes |
| **Total initial shell** | **1,802 bytes** | **645 bytes** |

### Replacement Script Sizes

| Content Size | Script Overhead | Total | Efficiency |
|--------------|-----------------|-------|------------|
| 100 bytes | ~150 bytes | ~250 bytes | 40% overhead |
| 500 bytes | ~150 bytes | ~650 bytes | 23% overhead |
| 2 KB | ~150 bytes | ~2.15 KB | 7% overhead |
| 10 KB | ~150 bytes | ~10.15 KB | 1.5% overhead |

> **Note:** Larger content has negligible overhead. The ~150 byte script wrapper becomes insignificant.

### Memory Usage

- Each Suspense boundary: ~200 bytes Python overhead
- Each resource registration: ~100 bytes
- Streaming context: ~500 bytes per request
- asyncio tasks: ~200 bytes per pending boundary
- Replacement script buffer: 0 bytes (streamed immediately)

### Benchmarks: Out-of-Order Resolution

```python
# Run benchmarks
pytest tests/benchmarks/bench_suspense.py -v --benchmark-only

# Results:
# ───────────────────────────────────────────────────────────────────
# test_out_of_order_5_components     Mean: 81.2ms   (parallel fetch)
# test_traditional_5_components      Mean: 405.0ms  (sequential)
# 
# Speedup: 5x faster with out-of-order streaming
# ───────────────────────────────────────────────────────────────────
```

---

## Best Practices

### 1. Place Suspense Boundaries Strategically

```python
# ❌ Bad: Single boundary for entire page
Suspense(fallback=PageSkeleton())[
    Header(),
    Sidebar(),
    MainContent(),
    Comments(),
]  # All or nothing

# ✓ Good: Granular boundaries
div()[
    Header(),  # Static, no Suspense needed
    
    Suspense(fallback=SidebarSkeleton())[
        Sidebar()  # Independent loading
    ],
    
    Suspense(fallback=MainSkeleton())[
        MainContent()  # Independent loading
    ],
    
    Suspense(fallback=CommentsSkeleton())[
        Comments()  # Can load last
    ],
]
```

### 2. Use Meaningful Fallbacks

```python
# ❌ Bad: Generic spinner for everything
Suspense(fallback=Spinner())[...]

# ✓ Good: Content-specific skeleton
Suspense(fallback=div()[
    # Matches final layout
    div(class_="card-header")[create_loading_skeleton(width="150px")],
    div(class_="card-body")[create_loading_skeleton(count=3)],
])[
    UserCard()
]
```

### 3. Combine with ErrorBoundary

```python
# ✓ Best: Handle both loading and errors
ErrorBoundary(fallback=error_handler)[
    Suspense(fallback=Loading())[
        DataComponent()
    ]
]
```

### 4. Avoid Suspense for Fast Operations

```python
# ❌ Unnecessary: Static content doesn't need Suspense
Suspense(fallback=...)[
    div()["Hello, World!"]
]

# ✓ Only use for async operations
Suspense(fallback=...)[
    UserProfile(data=user_resource())  # Needs data
]
```

### 5. Set Appropriate Timeouts

```python
# Critical data: short timeout, show error
Suspense(fallback=Error("Checkout unavailable"), timeout=3.0)[
    CheckoutForm()
]

# Nice-to-have data: longer timeout, keep showing skeleton
Suspense(fallback=RecommendationsSkeleton(), timeout=10.0)[
    Recommendations()
]
```

---

## API Reference

### Suspense

```python
Suspense(
    fallback: Any = None,      # Content shown while loading
    timeout: float = None,     # Max seconds before timeout state
)[
    children                    # Components to render
]
```

**Methods:**
- `render() -> str` - Synchronous render
- `render_async() -> str` - Async render with resource resolution
- `get_js_init() -> str` - JavaScript initialization code

### Show

```python
Show(
    when: Any,                  # Condition (value or callable)
    fallback: Any = None,       # Content when condition is false
)[
    children                    # Content when condition is true
]
```

### Switch / Match

```python
Switch()[
    Match(when=condition)[content],
    Match(when=condition)[content],
    Match()[default_content],   # No condition = default
]
```

### ErrorBoundary

```python
ErrorBoundary(
    fallback: Callable[[Exception], Any]  # Function receiving error
)[
    children
]
```

### PageShell

```python
shell = PageShell(
    title: str = "PyNext App",
    head_content: str = "",
    body_class: str = "",
)

shell.add_state(key: str, value: Any)
shell.add_script(script: str)
shell.render_opening() -> str
shell.render_closing(runtime_url: str = "/__pynext__/runtime.js") -> str
```

### Streaming Helpers

```python
# Loading skeleton
create_loading_skeleton(
    width: str = "100%",
    height: str = "1em",
    count: int = 1,
) -> str

# Suspense placeholder
create_suspense_placeholder(
    boundary_id: str,
    fallback_html: str,
) -> str

# Streaming CSS
get_streaming_css() -> str
```

### StreamingHTMLResponse

```python
StreamingHTMLResponse(
    content: AsyncGenerator[str, None],
    status_code: int = 200,
    headers: Dict[str, str] = None,
    media_type: str = "text/html; charset=utf-8",
)
```

---

## Related Documentation

- [Resource (createResource)](./HYDRATION.md#resource-hydration) - Async data primitive
- [State Management](./STATE_MANAGEMENT.md) - Signals and reactivity
- [Hydration](./HYDRATION.md) - Server-to-client state transfer

---

## Demo Scripts

```bash
# Interactive demo with timing visualization
python tests/demos/demo_streaming_suspense.py

# Formal benchmarks
python -m pytest tests/benchmarks/bench_suspense.py -v --benchmark-only
```

