# PyNext Promise & Scheduling APIs

## Overview

PyNext provides Promise utilities and browser scheduling APIs with polyfills for consistent behavior across all environments.

## Who Should Use This

- **Developers using async/await** in client code
- **Anyone needing Promise utilities** (Promise.any, Promise.withResolvers, etc.)
- **Developers using scheduling APIs** (requestAnimationFrame, etc.)

## What It Provides

### Promise Utilities

- `Promise.all` - Wait for all promises
- `Promise.allSettled` - Wait for all to settle
- `Promise.race` - First to resolve/reject
- `Promise.any` - First to resolve (with AggregateError)
- `Promise.withResolvers` - Create promise with resolve/reject

### Scheduling APIs

- `queueMicrotask` - Schedule microtask
- `requestIdleCallback` - Schedule during idle time
- `requestAnimationFrame` - Schedule before repaint
- `cancelIdleCallback` - Cancel idle callback
- `cancelAnimationFrame` - Cancel animation frame

## When to Use

- **Async operations**: Use Promise utilities
- **Animations**: Use requestAnimationFrame
- **Background work**: Use requestIdleCallback
- **Microtasks**: Use queueMicrotask

## How It Works

### Promise Example

```python
from pynext.client import Promise

async def fetch_data():
    results = await Promise.all([
        fetch("/api/users"),
        fetch("/api/posts")
    ])
    return results
```

### Scheduling Example

```python
from pynext.client import request_animation_frame, queue_microtask

def animate():
    # Animation code
    request_animation_frame(animate)

queue_microtask(lambda: print("Microtask"))
request_animation_frame(animate)
```

## Where to Find More

- `pynext/runtime/promise.js` - Promise utilities
- `pynext/runtime/scheduling.js` - Scheduling APIs

