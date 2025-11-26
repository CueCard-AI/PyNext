# PyNext Editor

A rich text editor built on Tiptap for content editing. Supports markdown, mentions, slash commands, and programmatic control.

## Quick Navigation

| Guide | Description |
|-------|-------------|
| [useEditor()](./USE_EDITOR.md) | Programmatic control from Python |
| [Markdown](./MARKDOWN.md) | Write and export Markdown |
| [Mentions](./MENTIONS.md) | @mention support |
| [Slash Commands](./SLASH_COMMANDS.md) | / command palette |
| [Collaborative Editing](./COLLABORATIVE.md) | Future: real-time collaboration |

## Installation

Add Tiptap to your layout:

```python
from pynext.editor import TiptapLoader

@layout
def root_layout(children):
    return html()[
        head()[
            TiptapLoader(),  # Basic editor
            # Or with markdown support:
            # TiptapLoader(markdown=True),
        ],
        body()[children]
    ]
```

## Components

```python
from pynext.editor import (
    # Core
    Editor,
    MarkdownEditor,
    EditorToolbar,
    EditorContent,
    
    # Programmatic control
    use_editor,
    EditorHandle,
    
    # Extensions
    MentionConfig,
    SlashConfig,
    SlashCommand,
    
    # Loaders
    TiptapLoader,
    MentionExtensionLoader,
    SlashExtensionLoader,
)
```

## Basic Usage

```python
Editor(
    content="<p>Start writing...</p>",
    on_change=handle_update,
    toolbar=True
)
```

## Feature Examples

### Programmatic Control

```python
from pynext.editor import Editor, use_editor
from pynext.shadcn import Button

def ControlledEditor():
    editor = use_editor("my-editor")
    
    return div()[
        div(class_="flex gap-2 mb-2")[
            Button(onclick=lambda: editor.toggle_bold())["B"],
            Button(onclick=lambda: editor.toggle_italic())["I"],
            Button(onclick=lambda: editor.clear())["Clear"],
        ],
        Editor(
            id="my-editor",  # Must match use_editor()
            content="Hello world",
            toolbar=False,
        ),
    ]
```

See [useEditor() Guide](./USE_EDITOR.md) for complete API.

### Markdown Mode

```python
from pynext.editor import MarkdownEditor, TiptapLoader, use_editor

def BlogEditor():
    editor = use_editor("blog-editor")
    
    return div()[
        # Include markdown support
        TiptapLoader(markdown=True),
        
        MarkdownEditor(
            id="blog-editor",
            content="# Hello\n\nThis is **markdown**!",
        ),
        
        Button(onclick=lambda: save(editor.get_markdown()))[
            "Save as Markdown"
        ],
    ]
```

See [Markdown Guide](./MARKDOWN.md) for details.

### Mentions

```python
from pynext.editor import Editor, MentionConfig, MentionExtensionLoader

@server_action
async def search_users(query: str):
    return await db.search_users(query)

def CommentEditor():
    return div()[
        TiptapLoader(),
        MentionExtensionLoader(),
        
        Editor(
            id="comment",
            content="",
            mentions=MentionConfig(
                trigger="@",
                suggestions=search_users,
            ),
        ),
    ]
```

See [Mentions Guide](./MENTIONS.md) for complete setup.

### Slash Commands

```python
from pynext.editor import Editor, SlashConfig, SlashCommand, SlashExtensionLoader

commands = [
    SlashCommand("h1", "Heading 1", "heading", "H1"),
    SlashCommand("bullet", "Bullet List", "bulletList", "*"),
    SlashCommand("code", "Code Block", "codeBlock", "</>"),
]

def DocumentEditor():
    return div()[
        TiptapLoader(),
        SlashExtensionLoader(),
        
        Editor(
            id="doc-editor",
            content="",
            placeholder="Type / for commands...",
            slash_commands=SlashConfig(commands=commands),
        ),
    ]
```

See [Slash Commands Guide](./SLASH_COMMANDS.md) for custom commands.

## API Reference

### Editor Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `id` | `str` | auto | Unique ID for use_editor() |
| `content` | `str` | `""` | Initial content (HTML or Markdown) |
| `on_change` | `Callable` | `None` | Change callback |
| `placeholder` | `str` | `""` | Placeholder text |
| `toolbar` | `bool \| list` | `True` | Show toolbar |
| `extensions` | `list[str]` | All | Enabled extensions |
| `markdown` | `bool` | `False` | Enable markdown mode |
| `mentions` | `MentionConfig` | `None` | Mention configuration |
| `slash_commands` | `SlashConfig` | `None` | Slash command configuration |
| `editable` | `bool` | `True` | Allow editing |
| `autofocus` | `bool` | `False` | Focus on mount |
| `min_height` | `str` | `"200px"` | Minimum height |
| `max_height` | `str` | `None` | Maximum height |

### EditorHandle Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_content()` | `str` | Get HTML content |
| `get_text()` | `str` | Get plain text |
| `get_markdown()` | `str` | Get as Markdown |
| `set_content(html)` | void | Set HTML content |
| `set_markdown(md)` | void | Set from Markdown |
| `insert_text(text)` | void | Insert at cursor |
| `clear()` | void | Clear all content |
| `focus()` | void | Focus editor |
| `blur()` | void | Remove focus |
| `toggle_bold()` | void | Toggle bold |
| `toggle_italic()` | void | Toggle italic |
| `toggle_heading(level)` | void | Toggle heading |
| `undo()` | void | Undo last action |
| `redo()` | void | Redo action |
| `is_empty()` | `bool` | Check if empty |
| `get_word_count()` | `int` | Get word count |

## Available Extensions

### Formatting
- `bold` - Bold text
- `italic` - Italic text
- `strike` - Strikethrough
- `underline` - Underlined text
- `code` - Inline code

### Structure
- `heading` - Headings (H1-H6)
- `bulletList` - Unordered lists
- `orderedList` - Ordered lists
- `blockquote` - Block quotes
- `codeBlock` - Code blocks
- `horizontalRule` - Horizontal line

### Inline
- `link` - Hyperlinks

## Events

```python
# Listen for content changes
@on("pynext:editor-change")
def handle_change(event):
    html = event.detail.html
    text = event.detail.text
    markdown = event.detail.markdown  # If markdown mode
    save_content(html)
```

## Styling

The editor uses Tailwind's typography plugin:

```python
Editor(
    content=content,
    class_="prose-lg prose-headings:text-primary"
)
```

## Full Example

```python
from pynext.editor import (
    Editor, TiptapLoader, use_editor,
    MentionConfig, MentionExtensionLoader,
    SlashConfig, SlashExtensionLoader,
    DEFAULT_SLASH_COMMANDS,
)
from pynext.shadcn import Button, Card, CardContent

@server_action
async def search_team(query: str):
    return await db.search_team_members(query)

@server_action
async def save_document(doc_id: str, content: str):
    await db.save_document(doc_id, content)

def FullEditor(doc_id: str, initial_content: str):
    editor = use_editor("full-editor")
    
    return Card()[
        # Loaders
        TiptapLoader(markdown=True),
        MentionExtensionLoader(),
        SlashExtensionLoader(),
        
        CardContent()[
            Editor(
                id="full-editor",
                content=initial_content,
                markdown=True,
                placeholder="Start writing... Use / for commands, @ for mentions",
                min_height="400px",
                mentions=MentionConfig(
                    trigger="@",
                    suggestions=search_team,
                ),
                slash_commands=SlashConfig(
                    commands=DEFAULT_SLASH_COMMANDS,
                ),
            ),
            
            div(class_="flex justify-end mt-4")[
                Button(
                    onclick=lambda: save_document(
                        doc_id, 
                        editor.get_markdown()
                    )
                )["Save"],
            ],
        ],
    ]
```

## Performance Notes

- Tiptap is lazily loaded (~150KB)
- Only loaded when `Editor` component is rendered
- Use `editable=False` for display-only to reduce overhead
- Markdown libraries add ~50KB when enabled
