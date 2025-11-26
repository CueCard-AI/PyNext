# Collaborative Editing Architecture

> **Status**: Architecture Reference - Not Yet Implemented
> 
> This document describes the planned architecture for real-time collaborative editing in PyNext. Implementation is planned for a future release.

## What is Collaborative Editing?

Think of it like Google Docs - multiple people can edit the same document simultaneously, seeing each other's changes in real-time. When User A types "Hello" at the same time User B types "World", both changes merge seamlessly without conflicts.

### The Problem It Solves

Without collaboration support:
- Users have to take turns editing
- Changes can overwrite each other
- "Save conflicts" require manual resolution
- No visibility into who's editing what

With collaboration:
- Multiple users edit simultaneously
- Changes merge automatically
- See other users' cursors and selections
- Presence awareness (who's online)

## How It Works (First Principles)

### The Challenge: Concurrent Edits

Imagine two users start with "Hello":

```
Document: "Hello"

User A types "!" at end    →  "Hello!"
User B types "World " at position 5  →  "HelloWorld "

What should the final result be?
```

Naive approach (last write wins) loses data. We need something smarter.

### The Solution: CRDTs

**CRDT** = Conflict-free Replicated Data Type

CRDTs are special data structures where:
1. All operations can happen concurrently
2. Results are mathematically guaranteed to converge
3. No central authority needed to resolve conflicts

For text, **Yjs** implements a CRDT called YATA (Yet Another Transformation Approach).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           PyNext App                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Client A   │    │   Client B   │    │   Client C   │          │
│  │              │    │              │    │              │          │
│  │  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │          │
│  │  │ Editor │  │    │  │ Editor │  │    │  │ Editor │  │          │
│  │  └───┬────┘  │    │  └───┬────┘  │    │  └───┬────┘  │          │
│  │      │       │    │      │       │    │      │       │          │
│  │  ┌───┴────┐  │    │  ┌───┴────┐  │    │  ┌───┴────┐  │          │
│  │  │Y.Doc   │  │    │  │Y.Doc   │  │    │  │Y.Doc   │  │          │
│  │  │(local) │  │    │  │(local) │  │    │  │(local) │  │          │
│  │  └───┬────┘  │    │  └───┬────┘  │    │  └───┬────┘  │          │
│  └──────┼───────┘    └──────┼───────┘    └──────┼───────┘          │
│         │                   │                   │                   │
│         └───────────────────┼───────────────────┘                   │
│                             │                                        │
│                     ┌───────┴───────┐                                │
│                     │   Provider    │                                │
│                     │  (WebSocket)  │                                │
│                     └───────┬───────┘                                │
│                             │                                        │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
                      ┌───────┴───────┐
                      │    Server     │
                      │  (y-websocket)│
                      │               │
                      │  ┌─────────┐  │
                      │  │ Y.Doc   │  │
                      │  │(master) │  │
                      │  └─────────┘  │
                      └───────────────┘
```

## Key Components

### 1. Yjs Document (Y.Doc)

The CRDT document that syncs across clients:

```javascript
// Each client has a local Y.Doc
const ydoc = new Y.Doc();

// Text content is stored as Y.XmlFragment (for Tiptap)
const yXmlFragment = ydoc.getXmlFragment('prosemirror');

// Changes automatically sync via provider
```

### 2. Provider (Transport Layer)

Connects Y.Docs across clients:

| Provider | Use Case | Pros | Cons |
|----------|----------|------|------|
| **y-websocket** | Server-based sync | Simple, reliable | Requires server |
| **y-webrtc** | Peer-to-peer | No server needed | Complex NAT traversal |
| **y-indexeddb** | Offline persistence | Works offline | Local only |

### 3. Awareness Protocol

Tracks user presence and cursor positions:

```javascript
// Set local user state
awareness.setLocalState({
  user: {
    name: "Alice",
    color: "#ff0000"
  },
  cursor: { anchor: 10, head: 15 }
});

// Listen for other users
awareness.on('change', () => {
  const states = awareness.getStates();
  // Render cursors for other users
});
```

## Planned PyNext Integration

### Python API (Proposed)

```python
from pynext.editor import Editor, CollaborativeConfig

# Create collaborative editor
Editor(
    id="shared-doc",
    content=content,
    collaborative=CollaborativeConfig(
        room="document-123",          # Unique room ID
        provider="websocket",         # or "webrtc"
        websocket_url="wss://sync.example.com",
        user={"name": "Alice", "color": "#ff0000"},
        awareness=True,               # Show other cursors
        persist=True,                 # Save to IndexedDB
    )
)
```

### Server Setup (Proposed)

```python
# FastAPI integration
from pynext.collab import create_yjs_server

app = FastAPI()

# Add Yjs WebSocket endpoint
yjs_server = create_yjs_server(
    persistence="redis",  # or "postgres", "memory"
    auth=verify_user,     # Custom auth function
)

app.mount("/yjs", yjs_server)
```

### Events

```python
# Listen for collaboration events
@on("pynext:collab-connect")
def on_connect(event):
    print(f"User {event.detail.user} joined")

@on("pynext:collab-disconnect")
def on_disconnect(event):
    print(f"User {event.detail.user} left")

@on("pynext:collab-awareness")
def on_awareness(event):
    users = event.detail.users  # List of connected users
```

## Required Dependencies

### Client-Side (npm)
```
yjs                     # Core CRDT library
y-websocket             # WebSocket provider
y-webrtc                # WebRTC provider (optional)
y-indexeddb             # Offline persistence (optional)
@tiptap/extension-collaboration
@tiptap/extension-collaboration-cursor
```

### Server-Side (Python)
```
y-py                    # Python Yjs bindings
websockets              # WebSocket server
```

## Data Flow

### Edit Operation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User types "Hello"                                        │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Tiptap captures change                                    │
│    → Creates ProseMirror transaction                         │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. y-prosemirror converts to Yjs operation                   │
│    → Encoded as binary diff                                  │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Provider broadcasts to other clients                      │
│    → WebSocket sends binary message                          │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Other clients receive and apply                           │
│    → Yjs merges automatically (CRDT magic)                   │
│    → Tiptap re-renders                                       │
└─────────────────────────────────────────────────────────────┘
```

### Conflict Resolution Example

```
Initial: "Hello"

User A (offline): types " World" → "Hello World"
User B (offline): types "!" → "Hello!"

When both reconnect, Yjs merges:
→ "Hello World!"  (both edits preserved, order by timestamp)
```

## Considerations

### Scalability

| Users per Doc | Recommended Provider | Notes |
|---------------|---------------------|-------|
| 2-10 | y-websocket | Simple setup |
| 10-50 | y-websocket + Redis | Horizontal scaling |
| 50+ | Custom sharding | Advanced setup |

### Offline Support

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Online    │ ──► │   Offline   │ ──► │   Reconnect │
│             │     │             │     │             │
│ Edit & sync │     │ Edit locally│     │ Sync & merge│
│             │     │ (IndexedDB) │     │ all changes │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Security

- **Room authorization**: Verify user can access document
- **Operation validation**: Server can reject invalid operations
- **Rate limiting**: Prevent spam/abuse
- **Encryption**: Use WSS and consider E2E encryption

## Timeline

This feature is planned for a future release. The implementation will be phased:

1. **Phase 1**: Basic WebSocket sync (2 users, same document)
2. **Phase 2**: Cursor awareness and presence
3. **Phase 3**: Multiple provider support
4. **Phase 4**: Offline-first with IndexedDB
5. **Phase 5**: Advanced features (comments, suggestions, history)

## Resources

- [Yjs Documentation](https://docs.yjs.dev/)
- [Tiptap Collaboration Guide](https://tiptap.dev/docs/editor/guide/collaborative-editing)
- [CRDT Papers](https://crdt.tech/papers.html)
- [y-websocket Server](https://github.com/yjs/y-websocket)

---

*This architecture document will be updated as implementation progresses.*

