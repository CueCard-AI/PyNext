# Supabase Full Integration

> **PyNext's Supabase integration provides a Pythonic, type-safe interface to all Supabase services - from authentication to realtime subscriptions, designed to be stupid-easy for Python developers.**

## Table of Contents

1. [Why Supabase + PyNext?](#why-supabase--pynext)
2. [First Principles: Understanding Supabase](#first-principles-understanding-supabase)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Configuration](#configuration)
6. [Authentication](#authentication)
7. [Storage](#storage)
8. [Realtime](#realtime)
9. [Edge Functions](#edge-functions)
10. [Row Level Security (RLS)](#row-level-security-rls)
11. [Integration Patterns](#integration-patterns)
12. [Error Handling](#error-handling)
13. [Testing](#testing)
14. [Performance](#performance)
15. [AI-Friendly Patterns](#ai-friendly-patterns)

---

## Why Supabase + PyNext?

### The Problem

When building full-stack Python applications, you typically need:
- User authentication (sign up, login, OAuth, sessions)
- File storage (upload, download, CDN)
- Real-time data sync (live updates, notifications)
- Database with security (row-level access control)
- Serverless functions (custom backend logic)

Setting all this up manually requires:
- Multiple libraries and configurations
- Complex security implementations
- Significant infrastructure knowledge
- Weeks of development time

### The PyNext Solution

```python
from pynext.db.supabase import Supabase

# One line to get everything
db = Supabase()

# Authentication - just works
user = await db.auth.sign_up("user@example.com", "password123")

# Storage - simple file operations
url = await db.storage.upload("avatars", "profile.jpg", file_data)

# Realtime - reactive updates
@db.realtime.on_insert("messages")
async def handle_new_message(record):
    print(f"New message: {record['content']}")

# RLS - security as code
@db.rls.policy("users", "select")
def users_can_read_own(user_id: str) -> str:
    return f"auth.uid() = id"
```

### Comparison: Traditional vs PyNext

| Task | Traditional | PyNext |
|------|-------------|--------|
| OAuth setup | 50+ lines config | `await db.auth.sign_in_oauth("google")` |
| File upload | Handle streams, errors | `await db.storage.upload(bucket, path, data)` |
| Realtime | WebSocket management | `@db.realtime.on_insert("table")` |
| RLS policies | Raw SQL migrations | `@db.rls.policy("table", "select")` |

---

## First Principles: Understanding Supabase

### What is Supabase?

Think of Supabase as "Firebase for SQL lovers". It provides:

```
┌─────────────────────────────────────────────────────────────┐
│                      YOUR APPLICATION                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE PLATFORM                         │
├─────────────┬─────────────┬─────────────┬─────────────┬─────┤
│  PostgreSQL │   GoTrue    │   Storage   │  Realtime   │Edge │
│  (Database) │   (Auth)    │   (Files)   │ (WebSocket) │Func │
└─────────────┴─────────────┴─────────────┴─────────────┴─────┘
```

### The Architecture

1. **PostgreSQL Database**: Full SQL database with all PostgreSQL features
2. **GoTrue Auth**: User authentication, OAuth, magic links, sessions
3. **Storage**: S3-compatible file storage with policies
4. **Realtime**: WebSocket server for live database changes
5. **Edge Functions**: Deno-based serverless functions

### Why Python Developers Love It

1. **SQL Database**: Unlike document stores, it's real SQL - familiar and powerful
2. **Self-hostable**: Not locked into any platform
3. **Open Source**: Full transparency and community
4. **Row Level Security**: Security directly in the database

---

## Quick Start

### Installation

```bash
# From GitHub (PyPI coming soon)
pip install "git+https://github.com/CueCard-AI/PyNext.git#egg=pynext[supabase]"
```

This installs:
- `supabase>=2.0.0` - Official Supabase client
- `realtime>=2.0.0` - Realtime subscriptions
- `storage3>=0.7.0` - Storage client
- `gotrue>=2.0.0` - Authentication

### Environment Setup

Create a `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  # Optional, for admin ops
```

### First Application

```python
# app.py
from pynext.db.supabase import Supabase

async def main():
    # Initialize
    db = Supabase()
    
    # Create a user
    user = await db.auth.sign_up(
        email="hello@example.com",
        password="secure123"
    )
    print(f"Created user: {user.id}")
    
    # Upload a file
    with open("avatar.png", "rb") as f:
        url = await db.storage.upload(
            bucket="avatars",
            path=f"users/{user.id}/avatar.png",
            file_data=f.read()
        )
    print(f"Avatar URL: {url}")
    
    # Subscribe to changes
    @db.realtime.on_insert("profiles")
    async def on_new_profile(record):
        print(f"New profile created: {record}")
    
    await db.realtime.connect()
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Core Concepts

### The Supabase Class

The `Supabase` class is your gateway to all services:

```python
from pynext.db.supabase import Supabase

# Initialize with environment variables
db = Supabase()

# Or with explicit config
from pynext.db.supabase import SupabaseConfig

config = SupabaseConfig(
    url="https://your-project.supabase.co",
    anon_key="your-anon-key",
    service_role_key="your-service-role-key"  # Optional
)
db = Supabase(config)
```

### Service Accessors

```python
# Authentication
db.auth        # SupabaseAuth instance

# File storage
db.storage     # SupabaseStorage instance

# Real-time subscriptions
db.realtime    # SupabaseRealtime instance

# Edge functions
db.functions   # SupabaseFunctions instance

# Row Level Security
db.rls         # SupabaseRLS instance

# Raw client (for advanced use)
db.client      # supabase.Client instance
```

### Sync vs Async

PyNext's Supabase integration is **async-first**:

```python
# All operations are async
user = await db.auth.sign_in(email, password)
files = await db.storage.list("bucket")
result = await db.functions.invoke("my-function")
```

For sync code, use `asyncio.run()` or integrate with your existing async runtime.

---

## Configuration

### SupabaseConfig

The configuration dataclass:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SupabaseConfig:
    """Configuration for Supabase connection."""
    
    url: str
    """Supabase project URL (e.g., https://abc123.supabase.co)"""
    
    anon_key: str
    """Anonymous/public API key - safe to expose in frontend"""
    
    service_role_key: Optional[str] = None
    """Service role key - NEVER expose, bypasses RLS"""
    
    auto_refresh_token: bool = True
    """Automatically refresh expired tokens"""
    
    persist_session: bool = True
    """Persist session to local storage"""
    
    realtime_enabled: bool = True
    """Enable realtime subscriptions"""
    
    storage_timeout: int = 60
    """Timeout for storage operations in seconds"""
    
    functions_timeout: int = 30
    """Timeout for edge function calls in seconds"""
    
    functions_region: Optional[str] = None
    """Region for edge functions (e.g., 'us-east-1')"""
```

### Environment Variables

The following environment variables are automatically detected:

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Project URL | Yes |
| `SUPABASE_KEY` or `SUPABASE_ANON_KEY` | Anonymous key | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key | No |
| `SUPABASE_REALTIME_ENABLED` | Enable realtime | No (default: true) |

### Configuration Examples

**Minimal configuration:**
```python
# Uses environment variables
db = Supabase()
```

**Explicit configuration:**
```python
db = Supabase(SupabaseConfig(
    url="https://abc123.supabase.co",
    anon_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
))
```

**Production configuration:**
```python
db = Supabase(SupabaseConfig(
    url=os.getenv("SUPABASE_URL"),
    anon_key=os.getenv("SUPABASE_ANON_KEY"),
    service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    auto_refresh_token=True,
    persist_session=True,
    storage_timeout=120,  # Larger files
    functions_timeout=60,  # Complex functions
    functions_region="us-east-1"
))
```

---

## Authentication

### Overview

PyNext wraps Supabase's GoTrue authentication with a Pythonic interface:

```
┌──────────────────────────────────────────────────────────────┐
│                     AUTHENTICATION FLOW                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐   │
│  │Sign Up  │───▶│Confirm  │───▶│Sign In  │───▶│Session  │   │
│  │(email)  │    │(email)  │    │(email)  │    │(JWT)    │   │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘   │
│       │                             │                         │
│       ▼                             ▼                         │
│  ┌─────────┐                  ┌─────────┐                    │
│  │OAuth    │                  │Magic    │                    │
│  │(Google) │                  │Link     │                    │
│  └─────────┘                  └─────────┘                    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Sign Up

Create new users:

```python
# Basic sign up
user = await db.auth.sign_up(
    email="user@example.com",
    password="secure123"
)
print(f"User ID: {user.id}")
print(f"Email: {user.email}")
print(f"Confirmed: {user.email_confirmed_at is not None}")

# Sign up with metadata
user = await db.auth.sign_up(
    email="user@example.com",
    password="secure123",
    user_metadata={
        "name": "John Doe",
        "avatar_url": "https://example.com/avatar.jpg",
        "preferences": {"theme": "dark"}
    }
)

# Sign up with phone
user = await db.auth.sign_up(
    phone="+1234567890",
    password="secure123"
)
```

### Sign In

Authenticate existing users:

```python
# Email/password sign in
session = await db.auth.sign_in(
    email="user@example.com",
    password="secure123"
)
print(f"Access Token: {session.access_token}")
print(f"User: {session.user.email}")

# Sign in with phone
session = await db.auth.sign_in(
    phone="+1234567890",
    password="secure123"
)
```

### OAuth (Social Login)

Support for 20+ OAuth providers:

```python
# Get OAuth URL for redirect
oauth_url = await db.auth.sign_in_oauth(
    provider="google",
    redirect_url="https://myapp.com/auth/callback",
    scopes=["email", "profile"]
)
print(f"Redirect user to: {oauth_url}")

# Available providers:
# - google, github, gitlab, bitbucket
# - facebook, twitter, discord, slack
# - apple, azure, spotify, twitch
# - and more...
```

### Magic Links

Passwordless authentication:

```python
# Send magic link
await db.auth.send_magic_link(
    email="user@example.com",
    redirect_url="https://myapp.com/welcome"
)

# User clicks link, then verify
session = await db.auth.verify_otp(
    email="user@example.com",
    token="123456",  # From URL or email
    type="magiclink"
)
```

### Sessions

Manage user sessions:

```python
# Get current session
session = await db.auth.get_session()
if session:
    print(f"Logged in as: {session.user.email}")
else:
    print("Not logged in")

# Get current user
user = await db.auth.get_user()

# Refresh session
new_session = await db.auth.refresh_session()

# Sign out
await db.auth.sign_out()

# Sign out from all devices
await db.auth.sign_out(scope="global")
```

### Password Management

```python
# Reset password (sends email)
await db.auth.reset_password(
    email="user@example.com",
    redirect_url="https://myapp.com/update-password"
)

# Update password (when logged in)
await db.auth.update_password("new-secure-password")
```

### User Management

```python
# Update user metadata
await db.auth.update_user(
    user_metadata={
        "name": "Jane Doe",
        "bio": "Software developer"
    }
)

# Update email
await db.auth.update_email("newemail@example.com")

# Verify email change
await db.auth.verify_otp(
    email="newemail@example.com",
    token="123456",
    type="email_change"
)
```

### Token Management

```python
# Get access token for API calls
access_token = await db.auth.get_access_token()

# Decode and inspect token
token_payload = await db.auth.decode_token(access_token)
print(f"User ID: {token_payload['sub']}")
print(f"Expires: {token_payload['exp']}")

# Check if token is expired
is_expired = await db.auth.is_token_expired()
```

---

## Storage

### Overview

Supabase Storage is S3-compatible file storage with policies:

```
┌──────────────────────────────────────────────────────────────┐
│                      STORAGE STRUCTURE                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                       BUCKET                             │ │
│  │  name: "avatars"                                         │ │
│  │  public: false                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐│ │
│  │  │                     FILES                           ││ │
│  │  │  ├── users/                                         ││ │
│  │  │  │   ├── user-123/                                  ││ │
│  │  │  │   │   ├── profile.jpg                            ││ │
│  │  │  │   │   └── banner.png                             ││ │
│  │  │  │   └── user-456/                                  ││ │
│  │  │  │       └── profile.jpg                            ││ │
│  │  │  └── defaults/                                      ││ │
│  │  │      └── avatar.png                                 ││ │
│  │  └─────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Upload Files

```python
# Upload from bytes
with open("photo.jpg", "rb") as f:
    url = await db.storage.upload(
        bucket="photos",
        path="vacation/beach.jpg",
        file_data=f.read(),
        content_type="image/jpeg"
    )
print(f"Uploaded to: {url}")

# Upload with upsert (overwrite existing)
url = await db.storage.upload(
    bucket="photos",
    path="profile.jpg",
    file_data=image_bytes,
    upsert=True
)

# Upload with cache control
url = await db.storage.upload(
    bucket="assets",
    path="logo.svg",
    file_data=svg_content,
    content_type="image/svg+xml",
    cache_control="max-age=31536000"  # 1 year
)
```

### Download Files

```python
# Download as bytes
file_data = await db.storage.download(
    bucket="photos",
    path="vacation/beach.jpg"
)
with open("local-beach.jpg", "wb") as f:
    f.write(file_data)

# Download with transform (images only)
thumbnail = await db.storage.download(
    bucket="photos",
    path="vacation/beach.jpg",
    transform={
        "width": 200,
        "height": 200,
        "resize": "cover"
    }
)
```

### Generate URLs

```python
# Public URL (for public buckets)
public_url = db.storage.get_public_url(
    bucket="public-assets",
    path="logo.png"
)
# Returns: https://project.supabase.co/storage/v1/object/public/public-assets/logo.png

# Signed URL (for private buckets)
signed_url = await db.storage.create_signed_url(
    bucket="private-docs",
    path="contract.pdf",
    expires_in=3600  # 1 hour
)

# Signed URLs for multiple files
urls = await db.storage.create_signed_urls(
    bucket="photos",
    paths=["photo1.jpg", "photo2.jpg", "photo3.jpg"],
    expires_in=3600
)

# Signed upload URL (for client-side uploads)
upload_url = await db.storage.create_signed_upload_url(
    bucket="uploads",
    path="user-content/file.pdf"
)
# Use this URL directly from browser for direct upload
```

### List Files

```python
# List all files in bucket
files = await db.storage.list(bucket="photos")
for file in files:
    print(f"{file['name']} - {file['metadata']['size']} bytes")

# List files in folder
files = await db.storage.list(
    bucket="photos",
    path="vacation"
)

# List with pagination
files = await db.storage.list(
    bucket="photos",
    path="",
    limit=100,
    offset=0,
    sort_by={"column": "created_at", "order": "desc"}
)
```

### Move and Copy

```python
# Move/rename file
await db.storage.move(
    bucket="photos",
    from_path="old/location/photo.jpg",
    to_path="new/location/photo.jpg"
)

# Copy file
await db.storage.copy(
    bucket="photos",
    from_path="templates/default.png",
    to_path="users/user-123/avatar.png"
)
```

### Delete Files

```python
# Delete single file
await db.storage.delete(
    bucket="photos",
    path="old-photo.jpg"
)

# Delete multiple files
await db.storage.delete_many(
    bucket="photos",
    paths=["photo1.jpg", "photo2.jpg", "photo3.jpg"]
)
```

### Bucket Management

```python
# List all buckets
buckets = await db.storage.list_buckets()
for bucket in buckets:
    print(f"{bucket['name']} - public: {bucket['public']}")

# Create bucket
await db.storage.create_bucket(
    name="user-uploads",
    public=False,
    allowed_mime_types=["image/jpeg", "image/png", "application/pdf"],
    file_size_limit=10 * 1024 * 1024  # 10MB
)

# Get bucket details
bucket = await db.storage.get_bucket("photos")

# Update bucket
await db.storage.update_bucket(
    name="photos",
    public=True
)

# Delete bucket (must be empty)
await db.storage.delete_bucket("old-bucket")

# Empty and delete bucket
await db.storage.empty_bucket("old-bucket")
await db.storage.delete_bucket("old-bucket")
```

---

## Realtime

### Overview

Supabase Realtime enables live updates via WebSockets:

```
┌──────────────────────────────────────────────────────────────┐
│                      REALTIME FLOW                           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────┐                           ┌─────────────────┐  │
│   │Database │                           │  Your App       │  │
│   │ Change  │                           │                 │  │
│   └────┬────┘                           │  ┌───────────┐  │  │
│        │                                │  │  Handler  │  │  │
│        ▼                                │  │           │  │  │
│   ┌─────────┐    WebSocket             │  │@on_insert │  │  │
│   │Realtime │◄──────────────────────────┤  │async def  │  │  │
│   │ Server  │          Message          │  │           │  │  │
│   └─────────┘                           │  └───────────┘  │  │
│                                         │                 │  │
│                                         │  ┌───────────┐  │  │
│                                         │  │  Signal   │  │  │
│                                         │  │           │  │  │
│                                         │  │messages() │  │  │
│                                         │  └───────────┘  │  │
│                                         │                 │  │
│                                         └─────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Decorator-Based Subscriptions

The simplest way to handle realtime events:

```python
# Handle new records
@db.realtime.on_insert("messages")
async def handle_new_message(record: dict):
    """Called when a new message is inserted."""
    print(f"New message from {record['user_id']}: {record['content']}")

# Handle updates
@db.realtime.on_update("messages")
async def handle_updated_message(record: dict, old_record: dict):
    """Called when a message is updated."""
    print(f"Message {record['id']} updated")
    print(f"Old: {old_record['content']}")
    print(f"New: {record['content']}")

# Handle deletions
@db.realtime.on_delete("messages")
async def handle_deleted_message(old_record: dict):
    """Called when a message is deleted."""
    print(f"Message {old_record['id']} was deleted")

# Handle any change
@db.realtime.on_change("messages")
async def handle_any_change(event_type: str, record: dict, old_record: dict = None):
    """Called on any change."""
    print(f"Event: {event_type}")
```

### Filtered Subscriptions

Filter which records trigger handlers:

```python
# Only messages in a specific channel
@db.realtime.on_insert("messages", filter="channel_id=eq.123")
async def handle_channel_message(record):
    print(f"New message in channel 123")

# Only high-priority notifications
@db.realtime.on_insert("notifications", filter="priority=eq.high")
async def handle_urgent_notification(record):
    print(f"URGENT: {record['title']}")

# Multiple filters
@db.realtime.on_insert(
    "orders",
    filter="status=eq.pending,total=gte.1000"
)
async def handle_large_pending_order(record):
    print(f"Large order needs attention: ${record['total']}")
```

### Schema-Specific Subscriptions

Subscribe to specific schemas (not just public):

```python
# Listen to auth schema changes
@db.realtime.on_insert("users", schema="auth")
async def handle_new_user(record):
    print(f"New user signed up!")

# Listen to custom schema
@db.realtime.on_update("settings", schema="app_config")
async def handle_settings_change(record, old_record):
    print(f"Settings updated")
```

### Signal-Based Subscriptions (Reactive Frontend)

For reactive UIs that auto-update:

```python
from pynext.core import Signal

# Create a reactive signal for messages
messages_signal = db.realtime.signal("messages")

# Use in a component
def ChatRoom():
    messages = messages_signal()  # Reactive access
    
    return div(
        *[Message(msg) for msg in messages]
    )

# With filters
channel_messages = db.realtime.signal(
    "messages",
    filter="channel_id=eq.123",
    initial_data=[]  # Initial value before first update
)

# Computed values from signals
def unread_count():
    return len([m for m in messages_signal() if not m.get("read")])
```

### Connection Management

```python
# Connect to realtime
await db.realtime.connect()

# Check connection status
if db.realtime.is_connected:
    print("Connected to realtime!")

# Disconnect
await db.realtime.disconnect()

# Reconnect on error
@db.realtime.on_error
async def handle_realtime_error(error):
    print(f"Realtime error: {error}")
    await asyncio.sleep(5)
    await db.realtime.reconnect()

# Connection lifecycle
@db.realtime.on_connect
async def handle_connect():
    print("Connected!")

@db.realtime.on_disconnect
async def handle_disconnect():
    print("Disconnected!")
```

### Multiple Table Subscriptions

```python
# Subscribe to multiple tables
@db.realtime.on_insert("users")
@db.realtime.on_insert("profiles")
async def handle_new_user_or_profile(record, table_name: str):
    print(f"New record in {table_name}")

# Or use a single handler for all
@db.realtime.on_change("*")  # All tables
async def handle_any_database_change(event_type, table_name, record):
    print(f"{event_type} on {table_name}")
```

### Broadcast (Custom Events)

Send custom events between clients:

```python
# Send a broadcast
await db.realtime.broadcast(
    channel="room:123",
    event="typing",
    payload={"user_id": "abc", "typing": True}
)

# Receive broadcasts
@db.realtime.on_broadcast("room:123", event="typing")
async def handle_typing(payload):
    print(f"User {payload['user_id']} is typing...")
```

### Presence (Track Online Users)

```python
# Track presence
await db.realtime.track_presence(
    channel="room:123",
    user_id="abc",
    data={"name": "John", "color": "blue"}
)

# Get current presence
presence = await db.realtime.get_presence("room:123")
for user_id, data in presence.items():
    print(f"{data['name']} is online")

# Listen for presence changes
@db.realtime.on_presence_join("room:123")
async def handle_user_join(user_id, data):
    print(f"{data['name']} joined!")

@db.realtime.on_presence_leave("room:123")
async def handle_user_leave(user_id, data):
    print(f"{data['name']} left!")
```

---

## Edge Functions

### Overview

Supabase Edge Functions are Deno-based serverless functions:

```
┌──────────────────────────────────────────────────────────────┐
│                   EDGE FUNCTION FLOW                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────┐              ┌───────────────────┐             │
│   │ PyNext  │    HTTPS     │   Edge Function   │             │
│   │  App    │─────────────▶│   (Deno Runtime)  │             │
│   └─────────┘              └─────────┬─────────┘             │
│                                      │                        │
│                            ┌─────────┴─────────┐             │
│                            │   Can Access:     │             │
│                            │   - Supabase DB   │             │
│                            │   - External APIs │             │
│                            │   - Secrets       │             │
│                            └───────────────────┘             │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Invoking Functions

```python
# Basic invocation
result = await db.functions.invoke("hello-world")
print(result)  # {"message": "Hello, World!"}

# With body
result = await db.functions.invoke(
    "process-data",
    body={"items": [1, 2, 3]}
)

# With custom headers
result = await db.functions.invoke(
    "api-proxy",
    body={"endpoint": "/users"},
    headers={"X-Custom-Header": "value"}
)

# Specify region
result = await db.functions.invoke(
    "compute-heavy",
    body={"data": large_data},
    region="us-east-1"
)
```

### Error Handling

```python
from pynext.db.supabase import FunctionInvokeError

try:
    result = await db.functions.invoke(
        "risky-function",
        body={"param": "value"}
    )
except FunctionInvokeError as e:
    print(f"Function failed: {e.status_code}")
    print(f"Error message: {e.message}")
    print(f"Error details: {e.details}")
```

### Timeout and Retry

```python
# Set timeout
result = await db.functions.invoke(
    "slow-function",
    body={"data": "large"},
    timeout=120  # 2 minutes
)

# With retry
from pynext.db.supabase import FunctionOptions

result = await db.functions.invoke(
    "flaky-function",
    body={"data": "value"},
    options=FunctionOptions(
        timeout=30,
        retry_count=3,
        retry_delay=1.0
    )
)
```

### Streaming Responses

```python
# Stream response (for large outputs)
async for chunk in db.functions.invoke_stream(
    "generate-report",
    body={"report_type": "full"}
):
    print(chunk, end="", flush=True)
```

---

## Row Level Security (RLS)

### Overview

RLS ensures users can only access their own data:

```
┌──────────────────────────────────────────────────────────────┐
│                      RLS CONCEPT                              │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────────────────────────────────────────────────┐│
│   │                    PostgreSQL Table                      ││
│   │  ┌─────────────────────────────────────────────────────┐││
│   │  │ id │ user_id │ content              │ created_at    │││
│   │  ├────┼─────────┼──────────────────────┼───────────────┤││
│   │  │ 1  │ user-a  │ Alice's private note │ 2024-01-01    │││
│   │  │ 2  │ user-b  │ Bob's secret data    │ 2024-01-02    │││
│   │  │ 3  │ user-a  │ Alice's diary        │ 2024-01-03    │││
│   │  └────┴─────────┴──────────────────────┴───────────────┘││
│   └─────────────────────────────────────────────────────────┘│
│                             │                                 │
│                             ▼                                 │
│   ┌─────────────────────────────────────────────────────────┐│
│   │              RLS Policy: "users own rows"                ││
│   │              auth.uid() = user_id                        ││
│   └─────────────────────────────────────────────────────────┘│
│                             │                                 │
│           ┌─────────────────┴─────────────────┐              │
│           │                                   │               │
│           ▼                                   ▼               │
│   ┌───────────────┐                   ┌───────────────┐      │
│   │   User A      │                   │   User B      │      │
│   │   Sees:       │                   │   Sees:       │      │
│   │   - Row 1     │                   │   - Row 2     │      │
│   │   - Row 3     │                   │               │      │
│   └───────────────┘                   └───────────────┘      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Policy Decorator

Define RLS policies as Python code:

```python
from pynext.db.supabase import policy

# Users can only see their own rows
@db.rls.policy("notes", "select")
def users_read_own_notes(user_id: str) -> str:
    return "auth.uid() = user_id"

# Users can only insert their own data
@db.rls.policy("notes", "insert")
def users_insert_own_notes(user_id: str) -> str:
    return "auth.uid() = user_id"

# Users can only update their own rows
@db.rls.policy("notes", "update")
def users_update_own_notes(user_id: str) -> str:
    return "auth.uid() = user_id"

# Users can only delete their own rows
@db.rls.policy("notes", "delete")
def users_delete_own_notes(user_id: str) -> str:
    return "auth.uid() = user_id"
```

### Complex Policies

```python
# Role-based access
@db.rls.policy("admin_logs", "select")
def admins_only() -> str:
    return """
    EXISTS (
        SELECT 1 FROM profiles
        WHERE profiles.id = auth.uid()
        AND profiles.role = 'admin'
    )
    """

# Time-based access
@db.rls.policy("events", "select")
def future_events_for_subscribers() -> str:
    return """
    (event_date > now() AND (
        is_public = true
        OR EXISTS (
            SELECT 1 FROM subscriptions
            WHERE subscriptions.user_id = auth.uid()
            AND subscriptions.event_id = events.id
        )
    ))
    """

# Organization membership
@db.rls.policy("org_documents", "select")
def org_members_only() -> str:
    return """
    EXISTS (
        SELECT 1 FROM org_members
        WHERE org_members.org_id = org_documents.org_id
        AND org_members.user_id = auth.uid()
    )
    """
```

### Multiple Operations

```python
# All CRUD operations with same policy
@db.rls.policy("profiles", ["select", "insert", "update", "delete"])
def profile_owner_only() -> str:
    return "auth.uid() = id"

# Different policies per operation
@db.rls.policy("posts", "select")
def anyone_can_read_published() -> str:
    return "published = true OR author_id = auth.uid()"

@db.rls.policy("posts", "insert")
def authenticated_can_create() -> str:
    return "auth.uid() IS NOT NULL AND author_id = auth.uid()"

@db.rls.policy("posts", "update")
def authors_can_update() -> str:
    return "author_id = auth.uid()"

@db.rls.policy("posts", "delete")
def authors_can_delete() -> str:
    return "author_id = auth.uid()"
```

### Generate Migrations

Convert policies to SQL migrations:

```python
# Generate migration file
migration_sql = db.rls.generate_migration()
print(migration_sql)

# Output:
# -- Enable RLS on tables
# ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
# ALTER TABLE admin_logs ENABLE ROW LEVEL SECURITY;
# ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
#
# -- Policy: users_read_own_notes on notes (SELECT)
# CREATE POLICY users_read_own_notes ON notes
#     FOR SELECT
#     USING (auth.uid() = user_id);
# ...

# Save to file
db.rls.save_migration("migrations/001_rls_policies.sql")
```

### Sync with Supabase

Apply policies directly to database:

```python
# Dry run (show what would change)
changes = await db.rls.sync(dry_run=True)
for change in changes:
    print(f"{change['action']}: {change['policy_name']} on {change['table']}")

# Apply changes
await db.rls.sync()

# Force recreate all policies
await db.rls.sync(force=True)
```

### Policy Diffing

Compare local policies with database:

```python
# Get differences
diff = await db.rls.diff()

for item in diff['added']:
    print(f"NEW: {item['policy_name']}")
    
for item in diff['removed']:
    print(f"REMOVED: {item['policy_name']}")
    
for item in diff['changed']:
    print(f"CHANGED: {item['policy_name']}")
    print(f"  Old: {item['old_expression']}")
    print(f"  New: {item['new_expression']}")
```

---

## Integration Patterns

### With PyNext Server Actions

```python
from pynext import action

@action
async def create_post(title: str, content: str):
    """Server action to create a post."""
    db = Supabase()
    
    # Get current user
    user = await db.auth.get_user()
    if not user:
        raise ValueError("Not authenticated")
    
    # Insert post (RLS will enforce ownership)
    result = await db.client.table("posts").insert({
        "title": title,
        "content": content,
        "author_id": user.id
    }).execute()
    
    return result.data[0]
```

### With PyNext Components

```python
from pynext import component, div, img

@component
def UserAvatar(user_id: str):
    """Display user avatar with realtime updates."""
    db = Supabase()
    
    # Reactive avatar URL signal
    avatar_signal = db.realtime.signal(
        "profiles",
        filter=f"id=eq.{user_id}",
        select="avatar_url"
    )
    
    avatar = avatar_signal()
    
    if avatar and avatar[0]:
        src = db.storage.get_public_url("avatars", avatar[0]["avatar_url"])
    else:
        src = "/default-avatar.png"
    
    return img(src=src, alt="User avatar", class_="avatar")
```

### With PyNext Tables

```python
from pynext.db import Table

class User(Table):
    name: str
    email: str
    avatar_url: str | None = None

# Use with Supabase
db = Supabase()

# Fetch users
users = await db.client.table("users").select("*").execute()

# Transform to Table instances
user_list = [User(**u) for u in users.data]
```

### Full-Stack Chat Example

```python
from pynext import component, action, div, input, button
from pynext.db.supabase import Supabase

db = Supabase()

# Server action to send message
@action
async def send_message(channel_id: str, content: str):
    user = await db.auth.get_user()
    if not user:
        raise ValueError("Not authenticated")
    
    await db.client.table("messages").insert({
        "channel_id": channel_id,
        "content": content,
        "user_id": user.id
    }).execute()

# Realtime handler
@db.realtime.on_insert("messages")
async def broadcast_message(record):
    # Additional processing (e.g., notifications)
    print(f"New message: {record['content']}")

# Component
@component
def ChatRoom(channel_id: str):
    # Reactive message list
    messages = db.realtime.signal(
        "messages",
        filter=f"channel_id=eq.{channel_id}",
        order={"column": "created_at", "ascending": True}
    )
    
    return div(
        div(
            *[Message(m) for m in messages()],
            class_="message-list"
        ),
        MessageInput(channel_id=channel_id)
    )

@component
def Message(msg: dict):
    return div(
        div(msg["user_id"], class_="author"),
        div(msg["content"], class_="content"),
        class_="message"
    )

@component
def MessageInput(channel_id: str):
    return div(
        input(type="text", id="message-input"),
        button(
            "Send",
            on_click=lambda e: send_message(
                channel_id,
                e.target.value
            )
        ),
        class_="message-input"
    )
```

---

## Error Handling

### Exception Hierarchy

```python
from pynext.db.supabase import (
    SupabaseError,           # Base exception
    AuthError,               # Authentication errors
    StorageError,            # Storage operation errors
    RealtimeError,           # Realtime connection errors
    FunctionInvokeError,     # Edge function errors
    RLSError,                # RLS policy errors
    ConfigurationError,      # Configuration errors
)
```

### Error Handling Patterns

```python
from pynext.db.supabase import (
    SupabaseError,
    AuthError,
    StorageError,
    FunctionInvokeError
)

async def safe_operation():
    db = Supabase()
    
    try:
        # Authentication
        user = await db.auth.sign_in(email, password)
        
    except AuthError as e:
        if e.code == "invalid_credentials":
            return {"error": "Invalid email or password"}
        elif e.code == "email_not_confirmed":
            return {"error": "Please confirm your email"}
        else:
            return {"error": "Authentication failed"}
    
    try:
        # Storage
        url = await db.storage.upload("bucket", "path", data)
        
    except StorageError as e:
        if e.code == "payload_too_large":
            return {"error": "File too large (max 50MB)"}
        elif e.code == "invalid_mime_type":
            return {"error": "Invalid file type"}
        else:
            return {"error": "Upload failed"}
    
    try:
        # Edge function
        result = await db.functions.invoke("my-function")
        
    except FunctionInvokeError as e:
        return {
            "error": f"Function error: {e.message}",
            "status": e.status_code
        }
```

### Retry Patterns

```python
import asyncio
from pynext.db.supabase import RealtimeError

async def connect_with_retry():
    db = Supabase()
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            await db.realtime.connect()
            print("Connected!")
            return
            
        except RealtimeError as e:
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Connection failed, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    raise RealtimeError("Failed to connect after multiple attempts")
```

---

## Testing

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pynext.db.supabase import Supabase, SupabaseConfig

@pytest.fixture
def mock_supabase():
    """Create a mocked Supabase instance."""
    with patch("pynext.db.supabase.adapter.create_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        
        db = Supabase(SupabaseConfig(
            url="https://test.supabase.co",
            anon_key="test-key"
        ))
        
        yield db, mock_client

@pytest.mark.asyncio
async def test_sign_up(mock_supabase):
    db, mock_client = mock_supabase
    
    # Setup mock response
    mock_client.auth.sign_up = AsyncMock(return_value=MagicMock(
        user=MagicMock(id="user-123", email="test@example.com")
    ))
    
    # Test
    user = await db.auth.sign_up("test@example.com", "password")
    
    # Assert
    assert user.id == "user-123"
    assert user.email == "test@example.com"
```

### Integration Testing

```python
import pytest
import os
from pynext.db.supabase import Supabase

@pytest.fixture
def supabase():
    """Create real Supabase instance for integration tests."""
    # Use test project credentials
    return Supabase()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_auth_flow(supabase):
    # Generate unique email
    email = f"test-{uuid.uuid4()}@example.com"
    
    # Sign up
    user = await supabase.auth.sign_up(email, "password123")
    assert user.id is not None
    
    # Sign in
    session = await supabase.auth.sign_in(email, "password123")
    assert session.access_token is not None
    
    # Sign out
    await supabase.auth.sign_out()
    
    # Cleanup: delete test user (requires service role)
    # await supabase.admin.delete_user(user.id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_storage_operations(supabase):
    test_bucket = "test-bucket"
    test_file = f"test-{uuid.uuid4()}.txt"
    
    # Upload
    url = await supabase.storage.upload(
        test_bucket,
        test_file,
        b"Hello, World!",
        content_type="text/plain"
    )
    assert test_file in url
    
    # Download
    data = await supabase.storage.download(test_bucket, test_file)
    assert data == b"Hello, World!"
    
    # Delete
    await supabase.storage.delete(test_bucket, test_file)
```

### Testing Realtime

```python
import asyncio
import pytest
from pynext.db.supabase import Supabase

@pytest.mark.integration
@pytest.mark.asyncio
async def test_realtime_subscription():
    db = Supabase()
    received_events = []
    
    @db.realtime.on_insert("test_table")
    async def capture_event(record):
        received_events.append(record)
    
    await db.realtime.connect()
    
    # Insert a record (from another client or service role)
    await db.client.table("test_table").insert({
        "name": "Test Record"
    }).execute()
    
    # Wait for event
    await asyncio.sleep(2)
    
    assert len(received_events) == 1
    assert received_events[0]["name"] == "Test Record"
    
    await db.realtime.disconnect()
```

### Testing RLS

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rls_enforced():
    # Create two users
    user_a = await create_test_user("a@test.com")
    user_b = await create_test_user("b@test.com")
    
    # User A creates a note
    db_a = Supabase()
    await db_a.auth.sign_in("a@test.com", "password")
    await db_a.client.table("notes").insert({
        "content": "Private note",
        "user_id": user_a.id
    }).execute()
    
    # User B tries to read
    db_b = Supabase()
    await db_b.auth.sign_in("b@test.com", "password")
    result = await db_b.client.table("notes").select("*").execute()
    
    # Should not see User A's notes
    assert len(result.data) == 0
```

---

## Performance

### Connection Pooling

Supabase handles connection pooling automatically, but you can optimize:

```python
# Reuse client instance
db = Supabase()

# Don't create new instances per request
# BAD:
async def handler():
    db = Supabase()  # New instance each time
    
# GOOD:
db = Supabase()
async def handler():
    await db.client.table("...").select("*").execute()
```

### Batch Operations

```python
# BAD: Multiple round trips
for item in items:
    await db.client.table("items").insert(item).execute()

# GOOD: Single batch insert
await db.client.table("items").insert(items).execute()
```

### Caching

```python
from functools import lru_cache
from cachetools import TTLCache

# Cache expensive queries
query_cache = TTLCache(maxsize=100, ttl=60)

async def get_user_profile(user_id: str):
    cache_key = f"profile:{user_id}"
    
    if cache_key in query_cache:
        return query_cache[cache_key]
    
    result = await db.client.table("profiles").select("*").eq("id", user_id).single().execute()
    query_cache[cache_key] = result.data
    
    return result.data
```

### Optimizing Realtime

```python
# Use specific filters to reduce message volume
@db.realtime.on_insert("messages", filter="channel_id=eq.123")
async def handle_specific_channel(record):
    pass  # Only receives messages for channel 123

# Select only needed columns
@db.realtime.on_insert("users", select="id,name,avatar")
async def handle_user(record):
    pass  # Only receives id, name, avatar
```

### Storage Optimization

```python
# Use transforms for images
url = db.storage.get_public_url(
    "avatars",
    "profile.jpg",
    transform={
        "width": 100,
        "height": 100,
        "resize": "cover",
        "quality": 80
    }
)

# Set proper cache headers
await db.storage.upload(
    "static",
    "logo.svg",
    svg_data,
    cache_control="max-age=31536000,immutable"
)
```

---

## AI-Friendly Patterns

### Clear Type Hints

```python
from typing import Optional, List, Dict, Any
from pynext.db.supabase import Supabase, SupabaseConfig, Session, User

async def get_authenticated_user() -> Optional[User]:
    """
    Get the currently authenticated user.
    
    Returns:
        User object if authenticated, None otherwise.
        
    Example:
        user = await get_authenticated_user()
        if user:
            print(f"Hello, {user.email}!")
    """
    db = Supabase()
    return await db.auth.get_user()
```

### Explicit Error Messages

```python
class AuthError(SupabaseError):
    """
    Authentication error with specific code.
    
    Common error codes:
        - invalid_credentials: Email or password is incorrect
        - email_not_confirmed: User hasn't confirmed their email
        - user_not_found: No user with this email exists
        - weak_password: Password doesn't meet requirements
        
    Example:
        try:
            await db.auth.sign_in(email, password)
        except AuthError as e:
            if e.code == "invalid_credentials":
                show_error("Wrong password")
    """
    pass
```

### Self-Documenting Code

```python
# Each function clearly states what it does
async def upload_user_avatar(
    user_id: str,
    image_data: bytes,
    content_type: str = "image/jpeg"
) -> str:
    """
    Upload a user's avatar image to storage.
    
    This function:
    1. Validates the image size (max 5MB)
    2. Uploads to the 'avatars' bucket
    3. Returns the public URL
    
    Args:
        user_id: The ID of the user (used as folder name)
        image_data: The raw image bytes
        content_type: MIME type (image/jpeg, image/png, etc.)
        
    Returns:
        Public URL of the uploaded avatar
        
    Raises:
        StorageError: If upload fails (size limit, permissions, etc.)
        
    Example:
        with open("avatar.jpg", "rb") as f:
            url = await upload_user_avatar("user-123", f.read())
            print(f"Avatar URL: {url}")
    """
    if len(image_data) > 5 * 1024 * 1024:
        raise StorageError("Image exceeds 5MB limit")
    
    db = Supabase()
    path = f"users/{user_id}/avatar"
    
    return await db.storage.upload(
        bucket="avatars",
        path=path,
        file_data=image_data,
        content_type=content_type,
        upsert=True  # Overwrite existing
    )
```

### Pattern Templates

```python
# TEMPLATE: Protected Server Action
@action
async def protected_action(data: dict):
    """
    Template for a server action that requires authentication.
    
    Pattern:
    1. Check authentication
    2. Validate input
    3. Perform operation
    4. Return result
    """
    db = Supabase()
    
    # 1. Check authentication
    user = await db.auth.get_user()
    if not user:
        raise ValueError("Authentication required")
    
    # 2. Validate input
    if not data.get("required_field"):
        raise ValueError("required_field is missing")
    
    # 3. Perform operation
    result = await db.client.table("table_name").insert({
        **data,
        "user_id": user.id
    }).execute()
    
    # 4. Return result
    return result.data[0]
```

---

## Reference

### SupabaseConfig

```python
@dataclass
class SupabaseConfig:
    url: str                              # Project URL
    anon_key: str                         # Anonymous key
    service_role_key: str | None = None   # Service role key
    auto_refresh_token: bool = True       # Auto-refresh tokens
    persist_session: bool = True          # Persist session
    realtime_enabled: bool = True         # Enable realtime
    storage_timeout: int = 60             # Storage timeout (seconds)
    functions_timeout: int = 30           # Functions timeout
    functions_region: str | None = None   # Edge functions region
```

### SupabaseAuth Methods

| Method | Description |
|--------|-------------|
| `sign_up(email, password, **kwargs)` | Create new user |
| `sign_in(email, password)` | Sign in with credentials |
| `sign_in_oauth(provider, **kwargs)` | Get OAuth URL |
| `send_magic_link(email, **kwargs)` | Send passwordless link |
| `verify_otp(email, token, type)` | Verify OTP/magic link |
| `get_session()` | Get current session |
| `get_user()` | Get current user |
| `refresh_session()` | Refresh tokens |
| `sign_out(scope)` | Sign out |
| `reset_password(email, **kwargs)` | Send password reset |
| `update_password(password)` | Update password |
| `update_user(**kwargs)` | Update user data |

### SupabaseStorage Methods

| Method | Description |
|--------|-------------|
| `upload(bucket, path, file_data, **kwargs)` | Upload file |
| `download(bucket, path, **kwargs)` | Download file |
| `delete(bucket, path)` | Delete file |
| `delete_many(bucket, paths)` | Delete multiple files |
| `list(bucket, **kwargs)` | List files |
| `move(bucket, from_path, to_path)` | Move/rename file |
| `copy(bucket, from_path, to_path)` | Copy file |
| `get_public_url(bucket, path, **kwargs)` | Get public URL |
| `create_signed_url(bucket, path, **kwargs)` | Get signed URL |
| `create_signed_urls(bucket, paths, **kwargs)` | Get signed URLs |
| `create_signed_upload_url(bucket, path)` | Get upload URL |
| `list_buckets()` | List all buckets |
| `create_bucket(name, **kwargs)` | Create bucket |
| `get_bucket(name)` | Get bucket info |
| `update_bucket(name, **kwargs)` | Update bucket |
| `delete_bucket(name)` | Delete bucket |
| `empty_bucket(name)` | Empty bucket |

### SupabaseRealtime Methods

| Method | Description |
|--------|-------------|
| `on_insert(table, **kwargs)` | Decorator for INSERT events |
| `on_update(table, **kwargs)` | Decorator for UPDATE events |
| `on_delete(table, **kwargs)` | Decorator for DELETE events |
| `on_change(table, **kwargs)` | Decorator for any event |
| `signal(table, **kwargs)` | Create reactive signal |
| `connect()` | Connect to realtime |
| `disconnect()` | Disconnect |
| `reconnect()` | Reconnect |
| `broadcast(channel, event, payload)` | Send broadcast |
| `track_presence(channel, user_id, data)` | Track presence |
| `get_presence(channel)` | Get presence state |

### SupabaseFunctions Methods

| Method | Description |
|--------|-------------|
| `invoke(name, **kwargs)` | Invoke edge function |
| `invoke_stream(name, **kwargs)` | Invoke with streaming |

### SupabaseRLS Methods

| Method | Description |
|--------|-------------|
| `policy(table, operation)` | Define RLS policy |
| `generate_migration()` | Generate SQL migration |
| `save_migration(path)` | Save migration to file |
| `sync(**kwargs)` | Sync policies to database |
| `diff()` | Get policy differences |

---

## Troubleshooting

### Common Issues

**"Invalid API key"**
```python
# Check your environment variables
import os
print(os.getenv("SUPABASE_URL"))
print(os.getenv("SUPABASE_KEY"))

# Ensure keys are for correct project
```

**"RLS policy violation"**
```python
# Check if RLS is enabled
# Verify user is authenticated
# Check policy expressions
```

**"Realtime not connecting"**
```python
# Check if realtime is enabled in project
# Verify network connectivity
# Check for WebSocket restrictions
```

**"Storage upload fails"**
```python
# Check bucket exists
# Verify file size limits
# Check MIME type restrictions
# Ensure storage policies allow upload
```

---

## Summary

PyNext's Supabase integration provides:

1. **Simple Authentication**: Sign up, sign in, OAuth, magic links
2. **Easy Storage**: Upload, download, manage files and buckets
3. **Reactive Realtime**: Decorators and signals for live updates
4. **Edge Functions**: Invoke serverless functions
5. **Security as Code**: Define RLS policies in Python

All designed to be:
- **Pythonic**: Native Python patterns and idioms
- **Type-Safe**: Full type hints for IDE support
- **AI-Friendly**: Clear documentation for LLM assistance
- **Performant**: Optimal connection and query patterns

Get started:
```python
from pynext.db.supabase import Supabase

db = Supabase()
user = await db.auth.sign_up("user@example.com", "password")
```

