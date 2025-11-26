# Slash Commands Extension

> A command palette inside your text.

## What are Slash Commands?

You've seen them in Notion, Slack, and Discord. Type `/` at the start of a line, and a menu appears with actions: insert a heading, add a code block, create a table.

Slash commands transform your editor from a passive text box into a powerful command center.

**The key insight**: Instead of hunting through toolbars and menus, users stay in their typing flow. The command comes to them, right where their cursor is.

## Why Do We Need It?

| Traditional Toolbar | Slash Commands |
|--------------------|--------------| 
| Eyes leave content | Stay in writing flow |
| Mouse movement required | Pure keyboard |
| Fixed menu location | Contextual, at cursor |
| Discoverable but slow | Fast once learned |
| Limited customization | Fully programmable |

## How Does It Work?

### The Slash Command Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Slash Command Detection                          │
│                                                                       │
│  1. User starts new line and types: "/"                              │
│                                        │                              │
│                                        ▼                              │
│  2. Show Command Menu                                                │
│     ┌─────────────────────────────────┐                              │
│     │ Type to filter...               │                              │
│     ├─────────────────────────────────┤                              │
│     │ H1  Heading 1                   │ ← highlighted                │
│     │     Large section heading       │                              │
│     │ H2  Heading 2                   │                              │
│     │     Medium section heading      │                              │
│     │ *   Bullet List                 │                              │
│     │ 1.  Numbered List               │                              │
│     └─────────────────────────────────┘                              │
│                    │                                                  │
│                    ▼ (type "bul" to filter)                          │
│  3. Filtered to matching                                             │
│     ┌─────────────────────────────────┐                              │
│     │ *   Bullet List                 │ ← only match                 │
│     │     Create a bullet list        │                              │
│     └─────────────────────────────────┘                              │
│                    │                                                  │
│                    ▼ (Enter/Tab/Click)                               │
│  4. Execute Command                                                  │
│     - Delete "/bul"                                                  │
│     - Apply bullet list formatting                                   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Architecture

```
USER TYPES "/" AT LINE START
           │
           ▼
┌─────────────────────┐
│ Trigger Detection   │
│ - At start of line  │
│ - After trigger "/" │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐      ┌─────────────────────┐
│ Filter Commands     │◄────►│ Command Registry    │
│ query: "hea"        │      │ [h1, h2, h3, ...]  │
└─────────────────────┘      └─────────────────────┘
           │
           ▼
┌─────────────────────┐
│ Render SlashMenu    │
│ - Show matches      │
│ - Keyboard nav      │
└─────────────────────┘
           │
           ▼ (selection)
┌─────────────────────┐      ┌─────────────────────┐
│ Execute Action      │─────►│ Built-in: toggle    │
│                     │      │ heading, list, etc  │
│                     │      ├─────────────────────┤
│                     │─────►│ Custom: insert      │
│                     │      │ template, call API  │
└─────────────────────┘      └─────────────────────┘
```

## Step-by-Step Walkthrough

### Step 1: Use Default Commands

The easiest way to get started:

```python
from pynext.editor import Editor, TiptapLoader
from pynext.editor.slash import SlashConfig, SlashExtensionLoader, DEFAULT_SLASH_COMMANDS

def EditorWithSlash():
    return div()[
        # Include loaders
        TiptapLoader(),
        SlashExtensionLoader(),
        
        # Create editor with default slash commands
        Editor(
            id="doc-editor",
            content="",
            placeholder="Type / for commands...",
            slash_commands=SlashConfig(
                commands=DEFAULT_SLASH_COMMANDS,
            ),
        ),
    ]
```

**What's happening:**
- `DEFAULT_SLASH_COMMANDS` includes common formatting commands
- Typing `/` shows the command palette
- Selecting a command applies the formatting

### Step 2: Define Custom Commands

```python
from pynext.editor.slash import SlashConfig, SlashCommand

my_commands = [
    # Built-in actions (use action name)
    SlashCommand(
        id="h1",
        label="Heading 1",
        action="heading",  # Built-in Tiptap command
        icon="H1",
        description="Large section heading",
        keywords=["title", "header"],
        group="Text",
    ),
    
    SlashCommand(
        id="bullet",
        label="Bullet List",
        action="bulletList",  # Built-in
        icon="*",
        description="Create a bullet list",
        group="Lists",
    ),
    
    SlashCommand(
        id="code",
        label="Code Block",
        action="codeBlock",  # Built-in
        icon="</>",
        description="Add syntax-highlighted code",
        group="Blocks",
    ),
]

Editor(
    id="doc-editor",
    slash_commands=SlashConfig(commands=my_commands),
)
```

**What's happening:**
- Each `SlashCommand` defines a menu item
- `action` can be a built-in Tiptap command name
- `group` organizes commands into sections
- `keywords` help with search/filtering

### Step 3: Add Custom Actions

For actions beyond formatting:

```python
from pynext.editor.slash import SlashCommand

# Template insertion
meeting_template = """
<h2>Meeting Notes</h2>
<p><strong>Date:</strong> Today</p>
<p><strong>Attendees:</strong></p>
<ul><li></li></ul>
<h3>Discussion</h3>
<p></p>
<h3>Action Items</h3>
<ul><li></li></ul>
"""

commands = [
    SlashCommand(
        id="meeting",
        label="Meeting Notes",
        action=lambda: insert_template(meeting_template),  # Custom action
        icon="calendar_icon",
        description="Insert meeting notes template",
        group="Templates",
    ),
    
    SlashCommand(
        id="table",
        label="Insert Table",
        action=lambda: open_table_dialog(),  # Opens a dialog
        icon="grid_icon",
        description="Create a data table",
        group="Blocks",
    ),
    
    SlashCommand(
        id="image",
        label="Insert Image",
        action=lambda: open_image_picker(),  # Custom flow
        icon="image_icon",
        description="Upload or link an image",
        group="Media",
    ),
]
```

**What's happening:**
- Custom actions use lambda functions
- These dispatch events that your code handles
- You can open dialogs, call APIs, insert complex content

### Step 4: Handle Custom Actions

```python
# Listen for custom command execution
@client_effect(deps=[])
def setup_slash_handlers():
    return """
    document.addEventListener('pynext:slash-execute', (e) => {
        const { command } = e.detail;
        
        if (command.id === 'meeting') {
            // Insert template
            window.PyNextEditor.insertHTML('doc-editor', meetingTemplate);
        }
        
        if (command.id === 'table') {
            // Open dialog
            openTableDialog();
        }
    });
    """
```

## Complete Example: Notion-Style Editor

```python
from pynext.editor import Editor, TiptapLoader, use_editor
from pynext.editor.slash import (
    SlashConfig, SlashCommand, SlashExtensionLoader
)
from pynext.shadcn import Card, CardContent

def NotionStyleEditor():
    # Define all commands
    commands = [
        # Text formatting
        SlashCommand("text", "Text", "paragraph", "Aa", "Plain text", group="Basic"),
        SlashCommand("h1", "Heading 1", "heading", "H1", "Large heading", group="Basic"),
        SlashCommand("h2", "Heading 2", "heading", "H2", "Medium heading", group="Basic"),
        SlashCommand("h3", "Heading 3", "heading", "H3", "Small heading", group="Basic"),
        
        # Lists
        SlashCommand("bullet", "Bullet List", "bulletList", "->", "Unordered list", group="Lists"),
        SlashCommand("numbered", "Numbered List", "orderedList", "1.", "Ordered list", group="Lists"),
        SlashCommand("todo", "To-do List", "taskList", "[]", "Checkbox list", group="Lists"),
        
        # Blocks
        SlashCommand("quote", "Quote", "blockquote", "quotation", "Block quote", group="Blocks"),
        SlashCommand("code", "Code", "codeBlock", "</>", "Code block", group="Blocks"),
        SlashCommand("divider", "Divider", "horizontalRule", "---", "Horizontal line", group="Blocks"),
        
        # Media (custom)
        SlashCommand("image", "Image", "custom:image", "img_icon", "Upload image", group="Media"),
        SlashCommand("video", "Video", "custom:video", "vid_icon", "Embed video", group="Media"),
        
        # Templates (custom)
        SlashCommand("meeting", "Meeting Notes", "custom:meeting", "cal_icon", "Meeting template", group="Templates"),
        SlashCommand("project", "Project Brief", "custom:project", "doc_icon", "Project template", group="Templates"),
    ]
    
    return Card()[
        CardContent(class_="p-0")[
            # Loaders
            TiptapLoader(),
            SlashExtensionLoader(),
            
            # Editor
            Editor(
                id="notion-editor",
                content="",
                toolbar=False,  # Rely on slash commands
                placeholder="Type '/' for commands, or just start writing...",
                min_height="500px",
                slash_commands=SlashConfig(
                    commands=commands,
                    trigger="/",
                    filter_on_type=True,
                ),
            ),
        ],
    ]
```

## API Reference

### SlashCommand

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `id` | `str` | required | Unique identifier |
| `label` | `str` | required | Display name |
| `action` | `str` or `Callable` | `""` | Built-in command or custom function |
| `icon` | `str` | `""` | Icon (emoji, text, or SVG) |
| `description` | `str` | `""` | Help text below label |
| `keywords` | `List[str]` | `[]` | Additional search terms |
| `group` | `str` | `""` | Group for organization |

### SlashConfig

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `commands` | `List[SlashCommand]` | `[]` | Available commands |
| `trigger` | `str` | `"/"` | Trigger character |
| `render` | `str` | `"inline"` | UI style: "inline" or "command" |
| `filter_on_type` | `bool` | `True` | Filter as user types |
| `debounce_ms` | `int` | `50` | Debounce for filtering |
| `placeholder` | `str` | `"Type..."` | Search placeholder |
| `empty_message` | `str` | `"No commands"` | Empty state message |

### SlashMenu Component

```python
SlashMenu(
    commands=[SlashCommand(...)],
    query="hea",
    highlighted_index=0,
    on_select=handle_select,
    show_groups=True,
)
```

### DEFAULT_SLASH_COMMANDS

Pre-defined commands for common formatting:

| ID | Label | Action |
|----|-------|--------|
| `h1` | Heading 1 | heading |
| `h2` | Heading 2 | heading |
| `h3` | Heading 3 | heading |
| `bullet` | Bullet List | bulletList |
| `numbered` | Numbered List | orderedList |
| `quote` | Quote | blockquote |
| `code` | Code Block | codeBlock |
| `divider` | Divider | horizontalRule |

## Common Patterns

### Pattern 1: Grouped Commands

```python
commands = [
    # Group: Formatting
    SlashCommand("h1", "Heading 1", "heading", group="Formatting"),
    SlashCommand("h2", "Heading 2", "heading", group="Formatting"),
    SlashCommand("bold", "Bold", "bold", group="Formatting"),
    
    # Group: Structure
    SlashCommand("bullet", "Bullet List", "bulletList", group="Structure"),
    SlashCommand("numbered", "Numbered List", "orderedList", group="Structure"),
    
    # Group: Embed
    SlashCommand("image", "Image", "custom:image", group="Embed"),
    SlashCommand("video", "Video", "custom:video", group="Embed"),
]

# Menu shows grouped:
# Formatting
#   H1  Heading 1
#   H2  Heading 2
# Structure
#   *   Bullet List
#   1.  Numbered List
```

### Pattern 2: Dynamic Commands

```python
@server_action
async def get_available_templates():
    """Fetch templates based on user/context."""
    templates = await get_user_templates(current_user)
    
    return [
        SlashCommand(
            id=f"template:{t.id}",
            label=t.name,
            action=f"custom:template:{t.id}",
            icon=t.icon,
            description=t.description,
            group="Templates",
        )
        for t in templates
    ]

# Build commands dynamically
base_commands = DEFAULT_SLASH_COMMANDS
template_commands = await get_available_templates()
all_commands = base_commands + template_commands
```

### Pattern 3: Context-Aware Commands

```python
def get_commands_for_context(context: str):
    """Return different commands based on context."""
    base = [
        SlashCommand("h1", "Heading 1", "heading"),
        SlashCommand("bullet", "Bullet List", "bulletList"),
    ]
    
    if context == "code":
        base.append(SlashCommand("run", "Run Code", "custom:run"))
    
    if context == "document":
        base.append(SlashCommand("toc", "Table of Contents", "custom:toc"))
    
    return base
```

## Events

The slash command system dispatches:

| Event | Detail | Description |
|-------|--------|-------------|
| `pynext:slash-update` | `{commands, query, ...}` | When menu updates |
| `pynext:slash-execute` | `{editorId, command}` | When command selected |
| `pynext:slash-close` | `{editorId}` | When menu closes |

## Keyboard Navigation

| Key | Action |
|-----|--------|
| `/` | Open menu (at line start) |
| `arrow_up` / `arrow_down` | Navigate items |
| `Enter` / `Tab` | Select highlighted |
| `Escape` | Close menu |
| Type | Filter commands |

## Troubleshooting

### Menu not appearing

**Problem**: Typing `/` does nothing

**Solutions**:
1. Include `SlashExtensionLoader()` in your page
2. Ensure `/` is typed at the start of a line or block
3. Check that `SlashConfig.commands` has items

### Commands not executing

**Problem**: Selecting a command does nothing

**Solutions**:
1. For built-in commands, check the action name is correct
2. For custom commands, verify your event handler
3. Check browser console for errors

### Custom actions not working

**Problem**: Custom command `action` isn't called

**Solution**: Custom actions dispatch the `pynext:slash-execute` event. You need to listen for it:

```javascript
document.addEventListener('pynext:slash-execute', (e) => {
    if (e.detail.command.action.startsWith('custom:')) {
        handleCustomCommand(e.detail.command);
    }
});
```

---

Previous: [Mentions](./MENTIONS.md) | Next: [Collaborative Editing](./COLLABORATIVE.md)

