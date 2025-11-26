# useEditor() - Programmatic Editor Control

> Control your editor like a puppet master — from Python.

## What is useEditor()?

Imagine you have a remote control for your TV. Instead of walking to the TV to change channels, you press buttons from your couch. `useEditor()` is that remote control for your rich text editor.

With `useEditor()`, you can:
- Get or set content programmatically
- Apply formatting (bold, italic, etc.) from buttons or shortcuts
- Insert text or templates at the cursor
- Undo/redo actions
- Track character and word counts

**The key insight**: Your editor is just a component on the page, but sometimes you need to *do things* to it from other parts of your code — a save button, a keyboard shortcut, a template selector. `useEditor()` gives you that power.

## Why Do We Need It?

Without programmatic control, you're limited to what the user clicks in the toolbar. But real applications need more:

| Use Case | What You Need |
|----------|---------------|
| Auto-save | Get content every 30 seconds |
| Templates | Insert predefined content |
| Keyboard shortcuts | ⌘B to toggle bold |
| Character limits | Check length before submit |
| Clear on submit | Reset editor after posting |
| External toolbar | Custom floating toolbar |

## How Does It Work?

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Your Python Code                             │
│                                                                      │
│  editor = use_editor("my-editor")                                    │
│  Button(onclick=lambda: editor.toggle_bold())["Bold"]               │
│                              │                                       │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Lambda Transpilation                        │  │
│  │  Python: editor.toggle_bold()                                  │  │
│  │  JavaScript: window.PyNextEditor.executeCommand("my-editor",   │  │
│  │              "bold")                                           │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Browser (Client)                            │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    PyNextEditor Runtime                      │    │
│  │                                                              │    │
│  │  instances: { "my-editor": TiptapEditorInstance }           │    │
│  │                                                              │    │
│  │  executeCommand("my-editor", "bold"):                       │    │
│  │    → instances["my-editor"].chain().focus().toggleBold()   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      Tiptap Editor                           │    │
│  │                                                              │    │
│  │  Selection: "Hello |World|"                                 │    │
│  │  → toggleBold() → "Hello **World**"                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Python**: You call `editor.toggle_bold()` in an event handler
2. **Transpilation**: PyNext converts this to JavaScript code
3. **Runtime**: Browser executes `window.PyNextEditor.executeCommand(...)`
4. **Tiptap**: The underlying editor applies the formatting
5. **DOM**: User sees their text become bold

## Step-by-Step Walkthrough

### Step 1: Create an Editor with an ID

The ID is crucial — it's how `useEditor()` knows which editor to control.

```python
from pynext.editor import Editor, TiptapLoader

def MyPage():
    return div()[
        # Include the runtime (once, in your layout)
        TiptapLoader(),
        
        # Create editor with a unique ID
        Editor(
            id="post-editor",  # This ID is important!
            content="<p>Start writing...</p>",
            placeholder="What's on your mind?",
        ),
    ]
```

**What's happening:**
- `id="post-editor"` assigns a unique identifier
- This ID gets rendered as `data-pynext-editor="post-editor"` in HTML
- The runtime stores the editor instance in `PyNextEditor.instances["post-editor"]`

### Step 2: Get the Editor Handle

```python
from pynext.editor import use_editor

# Get a handle to control the editor
editor = use_editor("post-editor")
```

**What's happening:**
- `use_editor("post-editor")` returns an `EditorHandle` object
- The handle doesn't connect to the editor immediately
- It generates JavaScript code that will run when triggered

### Step 3: Use the Handle in Event Handlers

```python
from pynext.shadcn import Button

def FormatToolbar():
    editor = use_editor("post-editor")
    
    return div(class_="flex gap-2")[
        Button(onclick=lambda: editor.toggle_bold())["B"],
        Button(onclick=lambda: editor.toggle_italic())["I"],
        Button(onclick=lambda: editor.toggle_underline())["U"],
        Button(onclick=lambda: editor.clear())["Clear"],
    ]
```

**What's happening:**
- Each button's `onclick` contains a lambda calling an editor method
- When clicked, PyNext transpiles this to JavaScript
- The JavaScript calls `window.PyNextEditor.executeCommand(...)`

### Step 4: Complete Example

```python
from pynext.editor import Editor, TiptapLoader, use_editor
from pynext.shadcn import Button, Card, CardContent, CardFooter

def PostComposer():
    editor = use_editor("post-editor")
    
    return Card()[
        CardContent()[
            # Formatting toolbar
            div(class_="flex gap-1 mb-2 border-b pb-2")[
                Button(
                    variant="ghost", 
                    size="sm",
                    onclick=lambda: editor.toggle_bold()
                )["B"],
                Button(
                    variant="ghost",
                    size="sm", 
                    onclick=lambda: editor.toggle_italic()
                )["I"],
                Button(
                    variant="ghost",
                    size="sm",
                    onclick=lambda: editor.toggle_code()
                )["</>"],
            ],
            
            # The editor
            Editor(
                id="post-editor",
                content="",
                placeholder="Write your post...",
                toolbar=False,  # We're using custom toolbar above
                min_height="150px",
            ),
        ],
        CardFooter(class_="flex justify-between")[
            # Character count (would need client-side updates)
            span(class_="text-sm text-muted-foreground")[
                "Tip: Keep it under 280 characters"
            ],
            
            div(class_="flex gap-2")[
                Button(
                    variant="ghost",
                    onclick=lambda: editor.clear()
                )["Clear"],
                Button(onclick=lambda: submit_post(editor.get_content()))[
                    "Post"
                ],
            ],
        ],
    ]
```

## API Reference

### EditorHandle Methods

#### Content Operations

| Method | Returns | Description |
|--------|---------|-------------|
| `get_content()` | `str` (JS) | Get HTML content |
| `get_text()` | `str` (JS) | Get plain text (no HTML) |
| `get_markdown()` | `str` (JS) | Get as Markdown (needs markdown mode) |
| `set_content(html)` | `void` (JS) | Replace content with HTML |
| `set_markdown(md)` | `void` (JS) | Replace content with Markdown |
| `insert_text(text)` | `void` (JS) | Insert text at cursor |
| `insert_html(html)` | `void` (JS) | Insert HTML at cursor |
| `clear()` | `void` (JS) | Remove all content |

#### Formatting Commands

| Method | Description |
|--------|-------------|
| `toggle_bold()` | Toggle **bold** on selection |
| `toggle_italic()` | Toggle *italic* on selection |
| `toggle_underline()` | Toggle <u>underline</u> on selection |
| `toggle_strike()` | Toggle ~~strikethrough~~ on selection |
| `toggle_code()` | Toggle `inline code` on selection |
| `toggle_heading(level)` | Toggle heading (1-6) |
| `toggle_bullet_list()` | Toggle bullet list |
| `toggle_ordered_list()` | Toggle numbered list |
| `toggle_blockquote()` | Toggle block quote |
| `toggle_code_block()` | Toggle code block |
| `insert_horizontal_rule()` | Insert `<hr>` |

#### Link Operations

| Method | Description |
|--------|-------------|
| `set_link(url)` | Add link to selection |
| `unset_link()` | Remove link from selection |

#### Focus & Selection

| Method | Description |
|--------|-------------|
| `focus()` | Focus the editor |
| `blur()` | Remove focus |

#### History

| Method | Description |
|--------|-------------|
| `undo()` | Undo last action |
| `redo()` | Redo last undone action |

#### State Queries

| Method | Returns | Description |
|--------|---------|-------------|
| `is_empty()` | `bool` (JS) | Check if editor is empty |
| `get_character_count()` | `int` (JS) | Get character count |
| `get_word_count()` | `int` (JS) | Get word count |

## Common Patterns

### Pattern 1: Auto-Save

```python
# Using client_effect for periodic saves
from pynext import client_effect

@client_effect(deps=[])  # Run once on mount
def setup_autosave():
    editor = use_editor("doc-editor")
    
    # This would need to be JS-based for setInterval
    # PyNext provides use_interval for this
    pass

# Alternative: Save on blur
Editor(
    id="doc-editor",
    content=content,
    # Add onblur event to save
)
```

### Pattern 2: Template Insertion

```python
templates = {
    "meeting": "<h2>Meeting Notes</h2><p><strong>Date:</strong></p><p><strong>Attendees:</strong></p><ul><li></li></ul>",
    "bug": "<h2>Bug Report</h2><p><strong>Steps:</strong></p><ol><li></li></ol><p><strong>Expected:</strong></p><p><strong>Actual:</strong></p>",
}

def TemplateSelector():
    editor = use_editor("doc-editor")
    
    return DropdownMenu()[
        DropdownMenuTrigger()[Button()["Insert Template"]],
        DropdownMenuContent()[
            DropdownMenuItem(
                onclick=lambda: editor.set_content(templates["meeting"])
            )["Meeting Notes"],
            DropdownMenuItem(
                onclick=lambda: editor.set_content(templates["bug"])
            )["Bug Report"],
        ],
    ]
```

### Pattern 3: Keyboard Shortcuts

```python
from pynext import on_keydown

@on_keydown("cmd+b")
def bold_shortcut():
    editor = use_editor("post-editor")
    return editor.toggle_bold()

@on_keydown("cmd+i")
def italic_shortcut():
    editor = use_editor("post-editor")
    return editor.toggle_italic()

@on_keydown("cmd+k")
def link_shortcut():
    editor = use_editor("post-editor")
    # Would open a dialog, then call editor.set_link(url)
    return "openLinkDialog()"
```

### Pattern 4: Character Limit Validation

```python
def PostComposer():
    editor = use_editor("post-editor")
    MAX_CHARS = 280
    
    return div()[
        Editor(id="post-editor", content=""),
        
        # Submit button that checks length
        Button(
            onclick=lambda: (
                f"const count = {editor.get_character_count()}; "
                f"if (count > {MAX_CHARS}) {{ alert('Too long!'); return; }} "
                f"submitPost({editor.get_content()});"
            )
        )["Post"],
    ]
```

## Troubleshooting

### "Editor not found" errors

**Problem**: `window.PyNextEditor.instances["my-editor"]` is undefined

**Causes & Solutions**:

1. **ID mismatch**: Ensure the ID in `use_editor("X")` matches `Editor(id="X")`
2. **Timing**: Editor hasn't mounted yet. Wait for DOMContentLoaded
3. **Missing TiptapLoader**: Include `TiptapLoader()` in your layout

### Methods not working

**Problem**: Calling `editor.toggle_bold()` does nothing

**Causes & Solutions**:

1. **Editor not focused**: Some commands require focus. Call `editor.focus()` first
2. **No selection**: For toggle commands, some text must be selected
3. **Extension not loaded**: Ensure the extension is in the editor's `extensions` list

### Markdown methods failing

**Problem**: `get_markdown()` returns HTML instead of Markdown

**Solution**: Include `TiptapLoader(markdown=True)` to load Turndown library

---

Next: [Markdown Extension →](./MARKDOWN.md)

