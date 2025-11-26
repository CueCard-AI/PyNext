# Mentions Extension

> Turning @ into a superpower.

## What are Mentions?

You've used them everywhere — Twitter, Slack, GitHub. Type `@` and a list appears. Select a person (or issue, or emoji) and it gets inserted as a special, clickable chip.

Mentions transform plain text into connected, interactive content. They're how text becomes *smart*.

**The key insight**: Mentions aren't just autocomplete. They're a bridge between unstructured text and structured data — linking your prose to users, issues, documents, or any entity in your system.

## Why Do We Need It?

| Without Mentions | With Mentions |
|-----------------|---------------|
| "John should review this" | "@John should review this" (John gets notified) |
| "See issue 1234" | "See #1234" (clickable link to issue) |
| ":smile:" shows as text | Shows as emoji |
| Manual linking | Automatic entity linking |

## How Does It Work?

### The Mention Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Mention Detection Flow                         │
│                                                                       │
│  1. User types: "Hey @"                                              │
│                    │                                                  │
│                    ▼                                                  │
│  2. Trigger Detection                                                │
│     - Cursor after "@"                                               │
│     - No space after trigger                                         │
│                    │                                                  │
│                    ▼                                                  │
│  3. Show Suggestion List                                             │
│     ┌─────────────────────┐                                          │
│     │ Search: joh_        │                                          │
│     ├─────────────────────┤                                          │
│     │ > John Doe          │  ← highlighted                           │
│     │   John Smith        │                                          │
│     │   Johnny Appleseed  │                                          │
│     └─────────────────────┘                                          │
│                    │                                                  │
│                    ▼ (Enter/Tab/Click)                               │
│  4. Insert Mention                                                   │
│     "Hey @John Doe " → rendered as chip                              │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Architecture

```
USER TYPES "@joh"
       │
       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Editor detects │────►│  Dispatch event │────►│  Server Action  │
│  trigger + query│     │  pynext:mention │     │  search_users() │
│  "@joh"         │     │  -query         │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
       ┌────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Update UI with │◄────│  Render         │◄────│  Return results │
│  floating list  │     │  MentionList    │     │  [John, ...]    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼ (user selects)
                        ┌─────────────────┐
                        │  Insert chip    │
                        │  @John Doe      │
                        └─────────────────┘
```

## Step-by-Step Walkthrough

### Step 1: Configure Mentions

```python
from pynext.editor import Editor, TiptapLoader
from pynext.editor.mentions import MentionConfig, MentionExtensionLoader

def MentionableEditor():
    return div()[
        # Include both loaders
        TiptapLoader(),
        MentionExtensionLoader(),
        
        # Create editor with mentions
        Editor(
            id="comment-editor",
            content="",
            mentions=MentionConfig(
                trigger="@",
                min_chars=1,
                max_suggestions=5,
            ),
        ),
    ]
```

**What's happening:**
- `MentionConfig` defines how mentions behave
- `trigger="@"` sets the character that activates suggestions
- `min_chars=1` means show suggestions after just one character

### Step 2: Connect to Data Source

The real power comes from connecting to your data:

```python
from pynext.editor.mentions import MentionConfig

@server_action
async def search_users(query: str) -> list:
    """Search users matching the query."""
    users = await db.query(
        "SELECT id, name, avatar FROM users WHERE name ILIKE %s LIMIT 10",
        f"%{query}%"
    )
    return [
        {"id": u.id, "label": u.name, "avatar": u.avatar}
        for u in users
    ]

# In your component
Editor(
    id="comment-editor",
    mentions=MentionConfig(
        trigger="@",
        suggestions=search_users,  # Server action handles the search
    ),
)
```

**What's happening:**
- When user types `@joh`, the `search_users` action is called with `"joh"`
- Results are displayed in the suggestion list
- This happens server-side, so you can query your database

### Step 3: Customize the Suggestion List

```python
from pynext.editor.mentions import MentionConfig

def custom_render(user):
    """Custom rendering for each suggestion."""
    return f'''
        <div class="flex items-center gap-2">
            <img src="{user['avatar']}" class="w-6 h-6 rounded-full" />
            <div>
                <div class="font-medium">{user['label']}</div>
                <div class="text-xs text-muted-foreground">{user.get('email', '')}</div>
            </div>
        </div>
    '''

Editor(
    id="comment-editor",
    mentions=MentionConfig(
        trigger="@",
        suggestions=search_users,
        item_render=custom_render,
    ),
)
```

**What's happening:**
- `item_render` function receives each suggestion item
- You can return custom HTML for rich display
- Show avatars, emails, status indicators, etc.

### Step 4: Handle Mention Selection

```python
@server_action
async def on_mention_selected(mention):
    """Called when a mention is inserted."""
    # Track for notifications
    await create_notification(
        type="mention",
        user_id=mention["id"],
        content=f"You were mentioned"
    )

Editor(
    id="comment-editor",
    mentions=MentionConfig(
        trigger="@",
        suggestions=search_users,
        on_mention_select=on_mention_selected,
    ),
)
```

## Complete Example: Comment System

```python
from pynext.editor import Editor, TiptapLoader, use_editor
from pynext.editor.mentions import MentionConfig, MentionExtensionLoader
from pynext.shadcn import Button, Avatar, AvatarImage, AvatarFallback

@server_action
async def search_team_members(query: str):
    """Search team members for mentions."""
    members = await get_team_members(query)
    return [
        {
            "id": m.id,
            "label": m.name,
            "avatar": m.avatar_url,
            "role": m.role,
        }
        for m in members
    ]

@server_action
async def post_comment(task_id: str, content: str, mentions: list):
    """Post a comment and notify mentioned users."""
    comment = await create_comment(task_id, content)
    
    # Notify mentioned users
    for mention_id in mentions:
        await notify_user(mention_id, f"You were mentioned in a comment")
    
    return comment

def CommentEditor(task_id: str):
    editor = use_editor("comment-editor")
    
    def member_render(member):
        return f'''
            <div class="flex items-center gap-2 py-1">
                <img src="{member['avatar']}" 
                     class="w-8 h-8 rounded-full" 
                     alt="{member['label']}" />
                <div>
                    <div class="font-medium">{member['label']}</div>
                    <div class="text-xs text-muted-foreground">
                        {member['role']}
                    </div>
                </div>
            </div>
        '''
    
    return div(class_="border rounded-lg")[
        # Loaders
        TiptapLoader(),
        MentionExtensionLoader(),
        
        # Editor
        Editor(
            id="comment-editor",
            content="",
            placeholder="Add a comment... Use @ to mention someone",
            toolbar=False,
            min_height="100px",
            mentions=MentionConfig(
                trigger="@",
                suggestions=search_team_members,
                item_render=member_render,
                min_chars=1,
                placeholder="Search team members...",
            ),
        ),
        
        # Actions
        div(class_="flex justify-end p-2 border-t")[
            Button(
                size="sm",
                onclick=lambda: post_comment(
                    task_id,
                    editor.get_content(),
                    get_mentions_from_content()  # Extract @mentions
                )
            )["Post Comment"],
        ],
    ]
```

## API Reference

### MentionConfig

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `trigger` | `str` | `"@"` | Character that triggers mentions |
| `suggestions` | `Callable` | `None` | Function to fetch suggestions |
| `render` | `str` | `"inline"` | UI style: "inline" or "command" |
| `item_render` | `Callable` | `None` | Custom render for each item |
| `allow_spaces` | `bool` | `False` | Allow spaces in search query |
| `highlight_matches` | `bool` | `True` | Highlight matching text |
| `debounce_ms` | `int` | `150` | Debounce delay for fetching |
| `min_chars` | `int` | `1` | Min chars before showing suggestions |
| `max_suggestions` | `int` | `10` | Max suggestions to display |
| `placeholder` | `str` | `"Search..."` | Placeholder in search input |
| `empty_message` | `str` | `"No results"` | Message when no results |
| `on_mention_select` | `Callable` | `None` | Callback when mention selected |

### MentionList Component

```python
MentionList(
    items=[{"id": "1", "name": "John"}],
    query="joh",
    highlighted_index=0,
    on_select=handle_select,
    empty_message="No users found",
)
```

### MentionChip Component

```python
MentionChip(
    id="user-123",
    label="John Doe",
    href="/users/123",  # Optional: makes it a link
)
```

## Common Patterns

### Pattern 1: Multiple Triggers

```python
# User mentions with @
user_mentions = MentionConfig(
    trigger="@",
    suggestions=search_users,
)

# Issue references with #
issue_mentions = MentionConfig(
    trigger="#",
    suggestions=search_issues,
)

# You'd need to combine these or use multiple editors
```

### Pattern 2: Emoji Picker

```python
@server_action
async def search_emoji(query: str):
    """Search emoji by name."""
    return [
        {"id": "smile", "label": "smile", "emoji": "emoji_smile"},
        {"id": "thumbsup", "label": "thumbsup", "emoji": "emoji_thumbsup"},
        # ...
    ]

Editor(
    mentions=MentionConfig(
        trigger=":",
        suggestions=search_emoji,
        item_render=lambda e: f'{e["emoji"]} :{e["label"]}:',
    ),
)
```

### Pattern 3: Command Palette Style

```python
# Use the Command component for suggestions
Editor(
    mentions=MentionConfig(
        trigger="@",
        suggestions=search_users,
        render="command",  # Uses Command component instead of inline list
    ),
)
```

## Events

The mention system dispatches several events:

| Event | Detail | Description |
|-------|--------|-------------|
| `pynext:mention-query` | `{editorId, query}` | When user types after trigger |
| `pynext:mention-update` | `{items, query, ...}` | When suggestions update |
| `pynext:mention-select` | `{editorId, item}` | When mention is selected |
| `pynext:mention-close` | `{editorId}` | When suggestion list closes |

## Troubleshooting

### Suggestions not appearing

**Problem**: Typing @ doesn't show anything

**Solutions**:
1. Include `MentionExtensionLoader()` in your page
2. Check that `MentionConfig.suggestions` is provided
3. Verify the server action returns data

### Wrong results

**Problem**: Suggestions don't match what was typed

**Solutions**:
1. Check `min_chars` setting (default is 1)
2. Verify your search function receives the query
3. Check `debounce_ms` (might be too slow)

### Mention not inserted

**Problem**: Selecting a suggestion doesn't insert

**Solutions**:
1. Ensure items have `id` and `label` fields
2. Check browser console for errors
3. Verify editor has focus

---

Previous: [Markdown](./MARKDOWN.md) | Next: [Slash Commands](./SLASH_COMMANDS.md)

