# Markdown Extension

> Write formatted text without touching a mouse.

## What is Markdown Mode?

Markdown is like shorthand for rich text. Instead of clicking buttons to make text bold, you type `**bold**`. Instead of using a menu for headings, you type `# Heading`.

The Markdown extension lets your editor:
- **Accept** Markdown input and render it as rich text
- **Export** rich text back to Markdown format
- Work as a Markdown-native editor while showing formatted preview

**The key insight**: Markdown is how developers and writers *think*. Rich text editors are how content *displays*. This extension bridges both worlds.

## Why Do We Need It?

| Scenario | Without Markdown | With Markdown |
|----------|-----------------|---------------|
| Documentation | Click bold, click italic, click... | Type `**bold**`, `*italic*` |
| Blog posts | Export as HTML, manually convert | Native Markdown output |
| Developer tools | Separate editor for Markdown | Same editor, native support |
| Storage | Store HTML (verbose) | Store Markdown (compact) |
| Version control | HTML diffs are unreadable | Markdown diffs are clean |

## How Does It Work?

### The Round-Trip

```
MARKDOWN INPUT          HTML (INTERNAL)         RENDERED DISPLAY
--------------          ---------------         ----------------
# Hello           -->   <h1>Hello</h1>    -->   Hello
**World**               <strong>World</strong>   World (bold)

      ^                                              |
      |                                              |
      +---------- Turndown (HTML to MD) <-----------+
```

### Libraries Involved

| Library | Purpose | Direction |
|---------|---------|-----------|
| **marked** | Parse Markdown to HTML | Input |
| **Turndown** | Convert HTML to Markdown | Output |
| **Tiptap** | Rich text editing | Display and Edit |

## Step-by-Step Walkthrough

### Step 1: Enable Markdown Mode

```python
from pynext.editor import Editor, TiptapLoader

def MarkdownPage():
    return div()[
        # Include runtime WITH markdown support
        TiptapLoader(markdown=True),  # This loads marked + turndown
        
        # Create editor in markdown mode
        Editor(
            id="md-editor",
            content="# Hello\n\nThis is **markdown**!",
            markdown=True,  # Enable markdown mode
            placeholder="Write markdown...",
        ),
    ]
```

**What's happening:**
- `TiptapLoader(markdown=True)` loads the Turndown and marked libraries
- `markdown=True` on Editor tells it to parse input as Markdown
- The `content` string is Markdown, rendered as formatted text

### Step 2: Use the MarkdownEditor Convenience Component

For simpler code, use the `MarkdownEditor` wrapper:

```python
from pynext.editor import MarkdownEditor, TiptapLoader

def BlogEditor():
    return div()[
        TiptapLoader(markdown=True),
        
        MarkdownEditor(
            id="blog-editor",
            content="# My Blog Post\n\nWrite content here...",
            placeholder="Start writing...",
        ),
    ]
```

**What's happening:**
- `MarkdownEditor` is just `Editor(markdown=True, ...)`
- Cleaner API for markdown-focused use cases

### Step 3: Get Markdown Output

```python
from pynext.editor import use_editor
from pynext.shadcn import Button

def EditorWithSave():
    editor = use_editor("blog-editor")
    
    return div()[
        MarkdownEditor(id="blog-editor", content=initial_content),
        
        Button(onclick=lambda: save_markdown(editor.get_markdown()))[
            "Save as Markdown"
        ],
    ]

@server_action
async def save_markdown(markdown: str):
    # Store the markdown string
    await save_to_database(markdown)
```

**What's happening:**
- `editor.get_markdown()` converts the rich text back to Markdown
- The server action receives clean Markdown text
- Store it, version control it, render it later

### Step 4: Set Markdown Programmatically

```python
def TemplateLoader():
    editor = use_editor("blog-editor")
    
    blog_template = """# Blog Post Title

## Introduction

Write your introduction here...

## Main Content

- Point one
- Point two
- Point three

## Conclusion

Wrap up your thoughts.
"""
    
    return Button(
        onclick=lambda: editor.set_markdown(blog_template)
    )["Load Template"]
```

**What's happening:**
- `editor.set_markdown(markdown)` parses and renders the Markdown
- User sees formatted rich text
- They can edit visually, then export as Markdown

## API Reference

### Editor Props (Markdown-related)

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `markdown` | `bool` | `False` | Enable markdown mode |
| `content` | `str` | `""` | Initial content (Markdown if mode enabled) |

### EditorHandle Methods (Markdown)

| Method | Description |
|--------|-------------|
| `get_markdown()` | Get content as Markdown string |
| `set_markdown(md)` | Set content from Markdown string |

### TiptapLoader

```python
TiptapLoader(markdown: bool = False) -> str
```

When `markdown=True`, includes:
- Turndown (HTML to Markdown converter)
- marked (Markdown to HTML parser)

## Markdown Syntax Support

The editor supports standard Markdown syntax:

| Syntax | Output |
|--------|--------|
| `# Heading 1` | Heading level 1 |
| `## Heading 2` | Heading level 2 |
| `**bold**` | bold text |
| `*italic*` | italic text |
| `~~strike~~` | strikethrough |
| backtick code backtick | inline code |
| `[link](url)` | hyperlink |
| `- item` | bullet list |
| `1. item` | numbered list |
| `> quote` | blockquote |
| `---` | horizontal rule |
| triple backticks | code block |

## Common Patterns

### Pattern 1: Markdown Preview

```python
def MarkdownWithPreview():
    editor = use_editor("preview-editor")
    
    return div(class_="grid grid-cols-2 gap-4")[
        # Editor side
        div()[
            h3()["Edit"],
            MarkdownEditor(id="preview-editor", content="# Hello"),
        ],
        
        # Preview side (would need client-side reactivity)
        div()[
            h3()["Preview"],
            div(id="preview-output", class_="prose")[
                # Updated via JS when editor changes
            ],
        ],
    ]
```

### Pattern 2: Import/Export

```python
def ImportExportEditor():
    editor = use_editor("import-editor")
    
    return div()[
        div(class_="flex gap-2 mb-4")[
            # Import from file
            input(
                type_="file",
                accept=".md,.markdown,.txt",
                onchange="handleFileImport(event)"
            ),
            
            # Export as file
            Button(
                onclick=lambda: download_file(
                    "document.md", 
                    editor.get_markdown()
                )
            )["Export .md"],
        ],
        
        MarkdownEditor(id="import-editor", content=""),
    ]
```

### Pattern 3: Documentation Editor

```python
def DocEditor(doc_path: str):
    editor = use_editor("doc-editor")
    content = load_doc_file(doc_path)
    
    return div()[
        # Breadcrumb
        nav(class_="text-sm text-muted-foreground mb-4")[
            f"Editing: {doc_path}"
        ],
        
        MarkdownEditor(
            id="doc-editor",
            content=content,
            min_height="600px",
        ),
        
        div(class_="flex justify-between mt-4")[
            span(class_="text-sm text-muted-foreground")[
                "Auto-saved every 30 seconds"
            ],
            Button(onclick=lambda: save_doc(doc_path, editor.get_markdown()))[
                "Save Now"
            ],
        ],
    ]
```

## Troubleshooting

### Markdown not rendering

**Problem**: Editor shows raw markdown instead of formatted text

**Solutions**:
1. Ensure `TiptapLoader(markdown=True)` is included
2. Check that `Editor(markdown=True)` is set
3. Verify the marked library loaded (check console)

### get_markdown() returns HTML

**Problem**: `editor.get_markdown()` returns HTML tags

**Solutions**:
1. Ensure `TiptapLoader(markdown=True)` is included
2. Check console for "Turndown not loaded" warning
3. Wait for libraries to load before calling

### Some syntax not working

**Problem**: Certain Markdown features don't parse

**Notes**:
- Some extended Markdown (tables, footnotes) may need additional extensions
- Tiptap's StarterKit covers most common syntax
- Check which extensions are enabled on the Editor

---

Previous: [useEditor()](./USE_EDITOR.md) | Next: [Mentions](./MENTIONS.md)

