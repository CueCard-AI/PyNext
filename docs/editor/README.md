# PyNext Editor

A rich text editor built on Tiptap for content editing.

## Installation

Add Tiptap to your layout:

```python
from pynext.editor import TiptapLoader

@layout
def root_layout(children):
    return html()[
        head()[
            TiptapLoader(),  # Include Tiptap
        ],
        body()[children]
    ]
```

## Components

```python
from pynext.editor import Editor, EditorToolbar, EditorContent
```

## Basic Usage

```python
Editor(
    content="<p>Start writing...</p>",
    on_change=handle_update,
    toolbar=True
)
```

## Examples

### With Placeholder

```python
Editor(
    content="",
    placeholder="Write your story...",
    toolbar=True
)
```

### Custom Toolbar

```python
Editor(
    content=content,
    on_change=set_content,
    toolbar=["bold", "italic", "link", "heading"]
)
```

### Full Featured

```python
Editor(
    content=article_content,
    on_change=save_draft,
    toolbar=True,
    extensions=[
        "bold", "italic", "strike", "underline",
        "heading", "bulletList", "orderedList",
        "link", "blockquote", "code", "codeBlock",
        "horizontalRule"
    ],
    min_height="400px",
    max_height="800px"
)
```

### Read-Only Mode

```python
Editor(
    content=published_content,
    editable=False,
    toolbar=False
)
```

### Auto-Focus

```python
Editor(
    content="",
    autofocus=True,
    placeholder="Start typing..."
)
```

## API Reference

### Editor

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `content` | `str` | `""` | Initial HTML content |
| `on_change` | `Callable` | `None` | Change callback |
| `placeholder` | `str` | `""` | Placeholder text |
| `toolbar` | `bool \| list` | `True` | Show toolbar |
| `extensions` | `list[str]` | All | Enabled extensions |
| `editable` | `bool` | `True` | Allow editing |
| `autofocus` | `bool` | `False` | Focus on mount |
| `min_height` | `str` | `"200px"` | Minimum height |
| `max_height` | `str` | `None` | Maximum height |

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
    save_content(html)
```

## JavaScript API

For advanced control:

```javascript
// Get content
const html = window.PyNextEditor.getContent("editor-id");

// Set content
window.PyNextEditor.setContent("editor-id", "<p>New content</p>");

// Execute command
window.PyNextEditor.executeCommand("editor-id", "bold");
```

## Styling

The editor uses Tailwind's typography plugin:

```css
.prose {
    /* Default prose styles apply */
}

.prose-invert {
    /* Dark mode styles */
}
```

Customize with `class_`:

```python
Editor(
    content=content,
    class_="prose-lg prose-headings:text-primary"
)
```

## Integration with Forms

```python
@server_action
async def save_article(form_data):
    content = form_data.get("content")
    await db.save_article(content)

form()[
    Editor(
        name="content",
        content=existing_content,
        placeholder="Write your article..."
    ),
    Button(type="submit")["Save Article"]
]
```

## Markdown Support

Convert to/from markdown using the `markdown` extension:

```python
# Coming soon - Tiptap markdown extension support
```

## Performance Notes

- Tiptap is lazily loaded (~150KB)
- Only loaded when `Editor` component is rendered
- Use `editable=False` for display-only to reduce overhead

