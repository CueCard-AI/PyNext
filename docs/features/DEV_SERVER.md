# Development Server

> Sub-50ms hot reload - see your changes instantly.

## The Problem

Slow dev feedback kills productivity:

```
Save file → Wait → Wait → Wait... → Page updates
            ↑
            This kills flow state
```

**Next.js**: ~200-500ms reload time (Webpack/Turbopack)
**PyNext**: <50ms target (Rust-based watching)

---

## Quick Start

```bash
# Start dev server
pynext dev

# Custom port
pynext dev --port 3000
```

That's it! Save a file and watch it reload instantly.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     File System                              │
│  pages/blog/post.py  ─────────────────────────────────────┐  │
│  components/card.py  ────────────────────────────────────┐│  │
│  public/styles.css   ───────────────────────────────────┐││  │
└─────────────────────────────────────────────────────────┼┼┼──┘
                                                          │││
┌─────────────────────────────────────────────────────────┼┼┼──┐
│                  watchfiles (Rust)                      │││  │
│  • Kernel-level file system events                      │││  │
│  • ~1ms detection latency                               ↓↓↓  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  PyNext Dev Server                           │
│                                                              │
│  1. Receive file change event                                │
│  2. Classify change type:                                    │
│     • page.py → hot reload                                   │
│     • component.py → hot reload                              │
│     • layout.py → full reload                                │
│     • styles.css → CSS hot swap                              │
│  3. Broadcast via WebSocket                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓ WebSocket
┌─────────────────────────────────────────────────────────────┐
│                  Browser Client                              │
│                                                              │
│  On "hot" → Fetch new HTML, swap content                     │
│  On "css" → Swap stylesheet (instant, no flash)              │
│  On "full" → window.location.reload()                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Reload Types

PyNext intelligently chooses the best reload strategy:

| File Changed | Reload Type | What Happens |
|--------------|-------------|--------------|
| `pages/*.py` | Hot | Swap content without refresh |
| `components/*.py` | Hot | Swap content without refresh |
| `public/*.css` | CSS | Instant stylesheet swap |
| `layout.py` | Full | Full page refresh |
| `template.py` | Full | Full page refresh |
| `pynext.config.py` | Full | Full page refresh |
| `public/*.js` | Full | Full page refresh |
| `pages/api/*.py` | None | No visual change needed |

### Hot Reload

Content is swapped without a full page refresh:

- Preserves scroll position
- Preserves form input values
- Preserves JavaScript state
- No white flash

### CSS Hot Swap

Stylesheets are swapped instantly:

- No page refresh
- No flash
- Instant visual update

### Full Reload

Full page refresh when necessary:

- Layout changes affect all pages
- Config changes need restart
- Script changes need re-execution

---

## Performance

| Metric | Next.js | PyNext |
|--------|---------|--------|
| File detection | ~50ms | <5ms |
| Server processing | ~100ms | <10ms |
| WebSocket push | ~20ms | <5ms |
| Browser update | ~200ms | <30ms |
| **Total** | **~370ms** | **<50ms** |

### Why So Fast?

1. **Rust-based file watching** (watchfiles)
   - Uses kernel events (inotify/FSEvents)
   - ~1ms detection latency

2. **Intelligent classification**
   - Determines optimal reload strategy
   - Avoids unnecessary full reloads

3. **WebSocket push**
   - No polling
   - Instant notification

4. **Surgical DOM updates**
   - Only changed content updates
   - Preserves state

---

## CLI Options

```bash
pynext dev [options]

Options:
  --port PORT      Server port (default: 8000)
  --host HOST      Server host (default: 0.0.0.0)
  --pages DIR      Pages directory (default: pages)
  --static DIR     Static files directory (default: public)
  --no-install     Skip dependency installation
  --skip-deps      Skip dependency check
```

### Examples

```bash
# Default
pynext dev

# Custom port
pynext dev --port 3000

# Skip dependency check (faster startup)
pynext dev --skip-deps
```

---

## Configuration

### Ignore Patterns

By default, these patterns are ignored:

- `__pycache__`
- `*.pyc`, `*.pyo`
- `.git`
- `.pynext`
- `node_modules`
- `.env*`
- `*.log`
- `.DS_Store`

### Custom Ignore Patterns

Create a `.pynextignore` file (coming soon):

```
# Ignore test files
tests/
*.test.py

# Ignore docs
docs/
```

---

## Browser Console

The dev client logs helpful messages:

```
[PyNext] Dev mode active
[PyNext] hot reload: pages/index.py
[PyNext] Reload completed in 23.4ms
[PyNext] css reload: public/styles.css
[PyNext] Reload completed in 5.2ms
```

### Debugging

Access dev utilities in browser console:

```javascript
// Force full reload
__pynext_dev__.reload()

// Force hot reload
__pynext_dev__.hotReload()

// Reload CSS only
__pynext_dev__.reloadCSS()

// Check connection
__pynext_dev__.isConnected()

// Reconnect
__pynext_dev__.reconnect()
```

---

## Connection Status

The dev server shows connection status:

```
┌─────────────────────────────────────────────────────┐
│ [PyNext] Reconnecting... (1/10)                      │
└─────────────────────────────────────────────────────┘
```

- Auto-reconnects on disconnect
- Shows reconnection attempts
- Fallback message after max attempts

---

## How Change Detection Works

### File Classification

```python
# pages/index.py → PAGE type → hot reload
# pages/layout.py → LAYOUT type → full reload
# pages/api/users.py → API type → no reload needed
# components/card.py → COMPONENT type → hot reload
# public/style.css → STATIC type → css reload
# pynext.config.py → CONFIG type → full reload
```

### src/ Folder Support

The watcher handles both:
- `pages/` (standard)
- `src/pages/` (src folder structure)

---

## Programmatic Usage

### Start Dev Server

```python
from pynext.server.dev import run_dev_server

# Sync version (blocks)
run_dev_server(port=8000)

# Async version
import asyncio
from pynext.server.dev import run_dev_server_async

asyncio.run(run_dev_server_async())
```

### Create File Watcher

```python
from pynext.server.watcher import FileWatcher

watcher = FileWatcher(Path("."))

async for change in watcher.watch():
    print(f"Changed: {change.relative_path}")
    print(f"Type: {change.change_type.value}")
    print(f"Reload: {change.reload_type}")
```

---

## Troubleshooting

### Server Not Starting

**Symptom**: Error about uvicorn

**Fix**: Install uvicorn
```bash
pip install uvicorn[standard]
```

### No Hot Reload

**Symptom**: Changes not detected

**Check**:
1. File is in watched directory
2. File isn't in ignore patterns
3. WebSocket connected (check console)

### Connection Lost

**Symptom**: Overlay shows "Connection lost"

**Fix**:
1. Check if server is running
2. Refresh the page
3. Restart dev server

### Slow Reload

**Symptom**: Reload takes > 100ms

**Check**:
1. Large files being watched
2. Many files changed at once
3. Network latency (if remote)

---

## Comparison with Next.js

| Feature | Next.js | PyNext |
|---------|---------|--------|
| Hot Module Replacement | ✅ Complex | ✅ Simple |
| CSS Hot Swap | ✅ | ✅ |
| File Watching | Webpack/Turbopack | watchfiles (Rust) |
| State Preservation | Partial | Full |
| Reload Time | ~200-500ms | <50ms |
| Configuration | Required | Zero-config |

---

## Under the Hood

### FileWatcher

```python
class FileWatcher:
    """
    Watch files using watchfiles (Rust-based).
    
    Uses kernel-level events:
    - Linux: inotify
    - macOS: FSEvents  
    - Windows: ReadDirectoryChangesW
    """
    
    async def watch(self):
        async for changes in watchfiles.awatch(self.root):
            for change_type, path in changes:
                yield FileChange(...)
```

### DevServer

```python
class DevServer:
    """
    Development server with WebSocket hot reload.
    
    1. Creates FastAPI app
    2. Adds WebSocket endpoint at /__pynext/ws
    3. Watches files in background
    4. Broadcasts changes to all clients
    """
    
    async def start(self):
        # Start watcher
        asyncio.create_task(self._watch_files())
        # Run server
        await uvicorn.Server(config).serve()
```

### Dev Client

```javascript
// Tiny client (~2KB)
// Connects to /__pynext/ws
// Handles reload messages
// Auto-reconnects on disconnect
```

---

## Best Practices

### 1. Keep Pages Simple

```python
# Good: Simple page
def HomePage():
    return Div(H1("Hello"))

# Bad: Heavy computation on every render
def HomePage():
    result = expensive_computation()  # Runs on every hot reload
    return Div(result)
```

### 2. Use Components

```python
# Good: Changes to Card only reload Card
# components/card.py
def Card(title):
    return Div(H2(title))

# pages/index.py
from components.card import Card
def HomePage():
    return Card("Hello")
```

### 3. Separate Styles

```css
/* public/styles.css */
/* Changes trigger CSS hot swap (instant) */
.card { ... }
```

---

## Summary

| Command | Description |
|---------|-------------|
| `pynext dev` | Start dev server |
| `pynext dev --port 3000` | Custom port |
| `pynext dev --skip-deps` | Fast startup |

**Save a file. See it update. Stay in flow.**

That's the PyNext dev experience.

