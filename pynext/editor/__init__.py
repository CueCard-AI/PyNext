"""
PyNext Rich Text Editor

A rich text editor built on Tiptap for content editing.
Supports markdown, mentions, slash commands, and more.

Usage:
    from pynext.editor import Editor, EditorContent, EditorToolbar, use_editor
    
    # Basic editor
    Editor(
        content=initial_content,
        on_change=handle_change
    )
    
    # With toolbar
    Editor(
        content=content,
        on_change=set_content,
        toolbar=True
    )
    
    # Full configuration
    Editor(
        content=content,
        on_change=set_content,
        toolbar=True,
        extensions=["bold", "italic", "link", "heading"],
        placeholder="Start writing...",
        editable=True,
    )
    
    # Programmatic control
    editor = use_editor("my-editor")
    editor.set_content("<p>Hello</p>")
    editor.toggle_bold()
    content = editor.get_content()
    
    # Markdown mode
    Editor(
        content=content,
        markdown=True,  # Enable markdown
        on_change=handle_change,
    )
"""

from typing import Any, Optional, List, Union, Callable, Dict, Literal
from pynext.tw import cn
import json
import hashlib


# =============================================================================
# EditorHandle - Programmatic Editor Control
# =============================================================================

class EditorHandle:
    """
    A handle for programmatic control of an Editor instance.
    
    The handle generates JavaScript code that calls the PyNextEditor runtime.
    Use with event handlers or client-side effects.
    
    Example:
        editor = use_editor("my-editor")
        
        # In an event handler
        Button(onclick=lambda: editor.toggle_bold())["Bold"]
        
        # Get/set content
        Button(onclick=lambda: editor.set_content("<p>Reset</p>"))["Reset"]
    """
    
    def __init__(self, editor_id: str):
        self.editor_id = editor_id
    
    def get_content(self) -> str:
        """Get the current HTML content of the editor."""
        return f'window.PyNextEditor.getContent("{self.editor_id}")'
    
    def get_text(self) -> str:
        """Get the plain text content (no HTML tags)."""
        return f'window.PyNextEditor.getText("{self.editor_id}")'
    
    def get_markdown(self) -> str:
        """Get content as Markdown (requires markdown extension)."""
        return f'window.PyNextEditor.getMarkdown("{self.editor_id}")'
    
    def set_content(self, html: str) -> str:
        """Set the editor content from HTML."""
        escaped = json.dumps(html)
        return f'window.PyNextEditor.setContent("{self.editor_id}", {escaped})'
    
    def set_markdown(self, markdown: str) -> str:
        """Set content from Markdown (requires markdown extension)."""
        escaped = json.dumps(markdown)
        return f'window.PyNextEditor.setMarkdown("{self.editor_id}", {escaped})'
    
    def insert_text(self, text: str) -> str:
        """Insert text at the current cursor position."""
        escaped = json.dumps(text)
        return f'window.PyNextEditor.insertText("{self.editor_id}", {escaped})'
    
    def insert_html(self, html: str) -> str:
        """Insert HTML at the current cursor position."""
        escaped = json.dumps(html)
        return f'window.PyNextEditor.insertHTML("{self.editor_id}", {escaped})'
    
    def focus(self) -> str:
        """Focus the editor."""
        return f'window.PyNextEditor.focus("{self.editor_id}")'
    
    def blur(self) -> str:
        """Remove focus from the editor."""
        return f'window.PyNextEditor.blur("{self.editor_id}")'
    
    def clear(self) -> str:
        """Clear all content from the editor."""
        return f'window.PyNextEditor.clear("{self.editor_id}")'
    
    def toggle_bold(self) -> str:
        """Toggle bold formatting on selection."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "bold")'
    
    def toggle_italic(self) -> str:
        """Toggle italic formatting on selection."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "italic")'
    
    def toggle_underline(self) -> str:
        """Toggle underline formatting on selection."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "underline")'
    
    def toggle_strike(self) -> str:
        """Toggle strikethrough formatting on selection."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "strike")'
    
    def toggle_code(self) -> str:
        """Toggle inline code formatting on selection."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "code")'
    
    def toggle_heading(self, level: int = 2) -> str:
        """Toggle heading at specified level (1-6)."""
        return f'window.PyNextEditor.setHeading("{self.editor_id}", {level})'
    
    def toggle_bullet_list(self) -> str:
        """Toggle bullet list."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "bulletList")'
    
    def toggle_ordered_list(self) -> str:
        """Toggle numbered list."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "orderedList")'
    
    def toggle_blockquote(self) -> str:
        """Toggle blockquote."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "blockquote")'
    
    def toggle_code_block(self) -> str:
        """Toggle code block."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "codeBlock")'
    
    def insert_horizontal_rule(self) -> str:
        """Insert a horizontal rule."""
        return f'window.PyNextEditor.executeCommand("{self.editor_id}", "horizontalRule")'
    
    def set_link(self, url: str) -> str:
        """Set a link on the current selection."""
        escaped = json.dumps(url)
        return f'window.PyNextEditor.setLink("{self.editor_id}", {escaped})'
    
    def unset_link(self) -> str:
        """Remove link from current selection."""
        return f'window.PyNextEditor.unsetLink("{self.editor_id}")'
    
    def undo(self) -> str:
        """Undo the last action."""
        return f'window.PyNextEditor.undo("{self.editor_id}")'
    
    def redo(self) -> str:
        """Redo the last undone action."""
        return f'window.PyNextEditor.redo("{self.editor_id}")'
    
    def is_empty(self) -> str:
        """Check if the editor is empty."""
        return f'window.PyNextEditor.isEmpty("{self.editor_id}")'
    
    def get_character_count(self) -> str:
        """Get the character count."""
        return f'window.PyNextEditor.getCharacterCount("{self.editor_id}")'
    
    def get_word_count(self) -> str:
        """Get the word count."""
        return f'window.PyNextEditor.getWordCount("{self.editor_id}")'


def use_editor(editor_id: str) -> EditorHandle:
    """
    Get a handle to control an editor programmatically.
    
    The editor_id should match the id passed to the Editor component.
    
    Args:
        editor_id: The unique identifier of the editor
    
    Returns:
        EditorHandle instance for controlling the editor
    
    Example:
        # Create editor with specific ID
        Editor(id="my-editor", content="Hello")
        
        # Get handle
        editor = use_editor("my-editor")
        
        # Use in event handlers
        Button(onclick=lambda: editor.toggle_bold())["Bold"]
        Button(onclick=lambda: editor.clear())["Clear"]
    """
    return EditorHandle(editor_id)


# Editor container styles
EDITOR_CONTAINER_BASE = (
    "rounded-md border bg-background"
)

# Editor content styles
EDITOR_CONTENT_BASE = (
    "prose prose-sm dark:prose-invert max-w-none p-4 min-h-[200px] "
    "focus:outline-none"
)

# Toolbar styles
TOOLBAR_BASE = (
    "flex flex-wrap items-center gap-1 p-2 border-b bg-muted/50"
)

TOOLBAR_BUTTON_BASE = (
    "inline-flex items-center justify-center rounded-md px-2 py-1.5 text-sm "
    "font-medium transition-colors hover:bg-accent hover:text-accent-foreground "
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring "
    "disabled:pointer-events-none disabled:opacity-50 "
    "data-[active=true]:bg-accent data-[active=true]:text-accent-foreground"
)

TOOLBAR_SEPARATOR_BASE = "w-px h-6 bg-border mx-1"

# Default extensions
DEFAULT_EXTENSIONS = [
    "bold", "italic", "strike", "underline",
    "heading", "bulletList", "orderedList",
    "link", "blockquote", "code", "codeBlock",
    "horizontalRule"
]


class Editor:
    """
    Rich text editor component.
    
    Attributes:
        id: Unique identifier (required for use_editor())
        content: Initial HTML or Markdown content
        on_change: Callback when content changes
        placeholder: Placeholder text
        toolbar: Show toolbar (True for default, or list of extensions)
        extensions: List of enabled extensions
        markdown: Enable markdown mode (parse input as markdown, output markdown)
        mentions: MentionConfig for @mention support
        slash_commands: SlashConfig for / command palette
        editable: Whether editor is editable
        autofocus: Focus editor on mount
        min_height: Minimum height
        max_height: Maximum height (enables scrolling)
        class_: Additional CSS classes
    
    Example:
        # Basic editor
        Editor(
            content="<p>Hello world</p>",
            on_change=handle_update,
            toolbar=True,
            placeholder="Start writing..."
        )
        
        # With ID for programmatic control
        Editor(
            id="my-editor",
            content="Hello",
            on_change=handle_update,
        )
        editor = use_editor("my-editor")
        
        # Markdown mode
        Editor(
            id="md-editor",
            content="# Hello\\n\\nThis is **markdown**",
            markdown=True,
            on_change=handle_markdown,
        )
        
        # With mentions
        Editor(
            content=content,
            mentions=MentionConfig(
                trigger="@",
                suggestions=search_users,
            )
        )
        
        # With slash commands
        Editor(
            content=content,
            slash_commands=SlashConfig(
                commands=[
                    SlashCommand("h1", "Heading 1", "heading"),
                    SlashCommand("bullet", "Bullet List", "bulletList"),
                ]
            )
        )
    """
    
    def __init__(
        self,
        content: str = "",
        on_change: Optional[Callable[[str], None]] = None,
        placeholder: str = "",
        toolbar: Union[bool, List[str]] = True,
        extensions: Optional[List[str]] = None,
        markdown: bool = False,
        mentions: Optional[Any] = None,  # MentionConfig
        slash_commands: Optional[Any] = None,  # SlashConfig
        editable: bool = True,
        autofocus: bool = False,
        min_height: str = "200px",
        max_height: Optional[str] = None,
        id: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.id = id
        self.content = content
        self.on_change = on_change
        self.placeholder = placeholder
        self.toolbar = toolbar
        self.extensions = extensions or DEFAULT_EXTENSIONS
        self.markdown = markdown
        self.mentions = mentions
        self.slash_commands = slash_commands
        self.editable = editable
        self.autofocus = autofocus
        self.min_height = min_height
        self.max_height = max_height
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        # Use provided ID or generate one
        editor_id = self.id or hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        class_str = cn(EDITOR_CONTAINER_BASE, self.extra_class)
        
        # Toolbar
        toolbar_html = ""
        if self.toolbar:
            toolbar_extensions = self.toolbar if isinstance(self.toolbar, list) else self.extensions
            toolbar_html = self._render_toolbar(toolbar_extensions)
        
        # Content area styles
        content_styles = [f"min-height:{self.min_height}"]
        if self.max_height:
            content_styles.append(f"max-height:{self.max_height}")
            content_styles.append("overflow-y:auto")
        
        # Editor config
        config = {
            "extensions": self.extensions,
            "content": self.content,
            "placeholder": self.placeholder,
            "editable": self.editable,
            "autofocus": self.autofocus,
            "markdown": self.markdown,
        }
        
        # Add mentions config if provided
        if self.mentions and hasattr(self.mentions, 'to_dict'):
            config["mentions"] = self.mentions.to_dict()
        
        # Add slash commands config if provided
        if self.slash_commands and hasattr(self.slash_commands, 'to_dict'):
            config["slashCommands"] = self.slash_commands.to_dict()
        
        config_json = json.dumps(config)
        
        return f'''
<div data-pynext-editor="{editor_id}" class="{class_str}">
    {toolbar_html}
    <div data-pynext-editor-content 
         class="{cn(EDITOR_CONTENT_BASE)}"
         style="{';'.join(content_styles)}">
        {self.content}
    </div>
</div>
<script>
    (function() {{
        var config = {config_json};
        var container = document.querySelector('[data-pynext-editor="{editor_id}"]');
        
        // Wait for Tiptap to load
        function initEditor() {{
            if (typeof window.PyNextEditor === 'undefined') {{
                setTimeout(initEditor, 100);
                return;
            }}
            
            window.PyNextEditor.create(container, config);
        }}
        
        initEditor();
    }})();
</script>
'''
    
    def _render_toolbar(self, extensions: List[str]) -> str:
        """Render the editor toolbar."""
        groups = self._group_extensions(extensions)
        
        buttons = []
        for i, group in enumerate(groups):
            if i > 0:
                buttons.append(f'<div class="{cn(TOOLBAR_SEPARATOR_BASE)}"></div>')
            
            for ext in group:
                buttons.append(self._render_toolbar_button(ext))
        
        return f'''
<div data-pynext-editor-toolbar class="{cn(TOOLBAR_BASE)}">
    {"".join(buttons)}
</div>
'''
    
    def _group_extensions(self, extensions: List[str]) -> List[List[str]]:
        """Group extensions by type for toolbar layout."""
        groups = {
            "formatting": ["bold", "italic", "underline", "strike", "code"],
            "heading": ["heading"],
            "lists": ["bulletList", "orderedList"],
            "blocks": ["blockquote", "codeBlock", "horizontalRule"],
            "insert": ["link", "image"],
        }
        
        result = []
        current_group = []
        
        for ext in extensions:
            # Find which group this extension belongs to
            added = False
            for group_name, group_exts in groups.items():
                if ext in group_exts:
                    if current_group and current_group[0] not in group_exts:
                        result.append(current_group)
                        current_group = []
                    current_group.append(ext)
                    added = True
                    break
            
            if not added:
                current_group.append(ext)
        
        if current_group:
            result.append(current_group)
        
        return result
    
    def _render_toolbar_button(self, extension: str) -> str:
        """Render a single toolbar button."""
        icons = {
            "bold": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 4h8a4 4 0 014 4 4 4 0 01-4 4H6z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 12h9a4 4 0 014 4 4 4 0 01-4 4H6z"/></svg>',
            "italic": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 4h4m0 0l-4 16m4-16h4M6 20h4"/></svg>',
            "underline": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8v8a5 5 0 0010 0V8M5 21h14"/></svg>',
            "strike": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-3-9v18M4 12h16"/></svg>',
            "heading": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h8m-8 6h16"/></svg>',
            "bulletList": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>',
            "orderedList": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>',
            "link": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>',
            "blockquote": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>',
            "code": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>',
            "codeBlock": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>',
            "horizontalRule": '<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 12h16"/></svg>',
        }
        
        icon = icons.get(extension, f'<span class="text-xs">{extension[:2].upper()}</span>')
        
        return f'''
<button type="button"
        data-pynext-editor-action="{extension}"
        class="{cn(TOOLBAR_BUTTON_BASE)}"
        title="{extension.replace('_', ' ').title()}">
    {icon}
</button>
'''
    
    def __str__(self) -> str:
        return self.render()


class EditorContent:
    """
    Wrapper for custom editor content styling.
    
    Example:
        EditorContent(class_="prose-lg")[
            # Editor content rendered here
        ]
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "EditorContent":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        class_str = cn(EDITOR_CONTENT_BASE, self.extra_class)
        
        return f'''
<div class="{class_str}">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class EditorToolbar:
    """
    Custom toolbar for the editor.
    
    Example:
        EditorToolbar()[
            EditorButton(action="bold"),
            EditorButton(action="italic"),
        ]
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "EditorToolbar":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        class_str = cn(TOOLBAR_BASE, self.extra_class)
        
        return f'''
<div data-pynext-editor-toolbar class="{class_str}">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


# CDN loader for Tiptap
def TiptapLoader(markdown: bool = False) -> str:
    """
    Include Tiptap and dependencies from CDN.
    Add this to your layout's <head>.
    
    Args:
        markdown: Include markdown extension for markdown support
    
    Example:
        head()[
            TiptapLoader(),
            ...
        ]
        
        # With markdown support
        head()[
            TiptapLoader(markdown=True),
            ...
        ]
    """
    markdown_script = ""
    if markdown:
        markdown_script = '''
<script src="https://unpkg.com/turndown@7.1.2/dist/turndown.js"></script>
<script src="https://unpkg.com/marked@9.1.2/marked.min.js"></script>
'''
    
    return f'''
<!-- Tiptap Core and Extensions -->
<script src="https://unpkg.com/@tiptap/core@2.1.12/dist/index.umd.js"></script>
<script src="https://unpkg.com/@tiptap/starter-kit@2.1.12/dist/index.umd.js"></script>
<script src="https://unpkg.com/@tiptap/extension-placeholder@2.1.12/dist/index.umd.js"></script>
<script src="https://unpkg.com/@tiptap/extension-underline@2.1.12/dist/index.umd.js"></script>
<script src="https://unpkg.com/@tiptap/extension-link@2.1.12/dist/index.umd.js"></script>
{markdown_script}
<script>
    // PyNext Editor wrapper - Extended API
    window.PyNextEditor = {{
        instances: {{}},
        configs: {{}},
        
        // =====================================================================
        // Editor Lifecycle
        // =====================================================================
        
        create: function(container, config) {{
            const editorId = container.dataset.pynextEditor;
            const contentEl = container.querySelector('[data-pynext-editor-content]');
            
            if (!contentEl) return;
            
            // Store config for later use
            this.configs[editorId] = config;
            
            // Build extensions based on config
            const extensions = [
                window.TiptapStarterKit.StarterKit,
            ];
            
            // Add optional extensions
            if (window.TiptapUnderline) {{
                extensions.push(window.TiptapUnderline.Underline);
            }}
            
            if (window.TiptapLink) {{
                extensions.push(window.TiptapLink.Link.configure({{
                    openOnClick: false,
                }}));
            }}
            
            if (config.placeholder) {{
                extensions.push(window.TiptapPlaceholder.Placeholder.configure({{
                    placeholder: config.placeholder
                }}));
            }}
            
            // Parse markdown content if markdown mode
            let initialContent = config.content;
            if (config.markdown && config.content && window.marked) {{
                initialContent = window.marked.parse(config.content);
            }}
            
            // Create editor
            const editor = new window.TiptapCore.Editor({{
                element: contentEl,
                extensions: extensions,
                content: initialContent,
                editable: config.editable !== false,
                autofocus: config.autofocus,
                onUpdate: ({{ editor }}) => {{
                    const html = editor.getHTML();
                    const text = editor.getText();
                    
                    // Get markdown if in markdown mode
                    let markdown = null;
                    if (config.markdown) {{
                        markdown = this.getMarkdown(editorId);
                    }}
                    
                    container.dispatchEvent(new CustomEvent('pynext:editor-change', {{
                        bubbles: true,
                        detail: {{ html, text, markdown }}
                    }}));
                }}
            }});
            
            this.instances[editorId] = editor;
            
            // Wire up toolbar buttons
            container.querySelectorAll('[data-pynext-editor-action]').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    const action = btn.dataset.pynextEditorAction;
                    this.executeCommand(editorId, action);
                }});
            }});
            
            return editor;
        }},
        
        destroy: function(editorId) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.destroy();
                delete this.instances[editorId];
                delete this.configs[editorId];
            }}
        }},
        
        // =====================================================================
        // Commands
        // =====================================================================
        
        executeCommand: function(editorId, command) {{
            const editor = this.instances[editorId];
            if (!editor) return;
            
            const chain = editor.chain().focus();
            
            switch (command) {{
                case 'bold': chain.toggleBold().run(); break;
                case 'italic': chain.toggleItalic().run(); break;
                case 'strike': chain.toggleStrike().run(); break;
                case 'underline': chain.toggleUnderline().run(); break;
                case 'code': chain.toggleCode().run(); break;
                case 'heading': chain.toggleHeading({{ level: 2 }}).run(); break;
                case 'bulletList': chain.toggleBulletList().run(); break;
                case 'orderedList': chain.toggleOrderedList().run(); break;
                case 'blockquote': chain.toggleBlockquote().run(); break;
                case 'codeBlock': chain.toggleCodeBlock().run(); break;
                case 'horizontalRule': chain.setHorizontalRule().run(); break;
                default: console.warn('Unknown command:', command);
            }}
        }},
        
        setHeading: function(editorId, level) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.chain().focus().toggleHeading({{ level }}).run();
            }}
        }},
        
        setLink: function(editorId, url) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.chain().focus().setLink({{ href: url }}).run();
            }}
        }},
        
        unsetLink: function(editorId) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.chain().focus().unsetLink().run();
            }}
        }},
        
        // =====================================================================
        // Content Getters
        // =====================================================================
        
        getContent: function(editorId) {{
            const editor = this.instances[editorId];
            return editor ? editor.getHTML() : '';
        }},
        
        getText: function(editorId) {{
            const editor = this.instances[editorId];
            return editor ? editor.getText() : '';
        }},
        
        getMarkdown: function(editorId) {{
            const editor = this.instances[editorId];
            if (!editor) return '';
            
            // Use Turndown to convert HTML to Markdown
            if (window.TurndownService) {{
                const turndown = new window.TurndownService({{
                    headingStyle: 'atx',
                    codeBlockStyle: 'fenced',
                }});
                return turndown.turndown(editor.getHTML());
            }}
            
            // Fallback: return HTML if Turndown not available
            console.warn('Turndown not loaded. Include TiptapLoader(markdown=True)');
            return editor.getHTML();
        }},
        
        getJSON: function(editorId) {{
            const editor = this.instances[editorId];
            return editor ? editor.getJSON() : null;
        }},
        
        // =====================================================================
        // Content Setters
        // =====================================================================
        
        setContent: function(editorId, content) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.commands.setContent(content);
            }}
        }},
        
        setMarkdown: function(editorId, markdown) {{
            const editor = this.instances[editorId];
            if (!editor) return;
            
            // Use marked to convert Markdown to HTML
            if (window.marked) {{
                const html = window.marked.parse(markdown);
                editor.commands.setContent(html);
            }} else {{
                console.warn('marked not loaded. Include TiptapLoader(markdown=True)');
                editor.commands.setContent(markdown);
            }}
        }},
        
        insertText: function(editorId, text) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.chain().focus().insertContent(text).run();
            }}
        }},
        
        insertHTML: function(editorId, html) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.chain().focus().insertContent(html).run();
            }}
        }},
        
        clear: function(editorId) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.commands.clearContent();
            }}
        }},
        
        // =====================================================================
        // Focus & Selection
        // =====================================================================
        
        focus: function(editorId) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.commands.focus();
            }}
        }},
        
        blur: function(editorId) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.commands.blur();
            }}
        }},
        
        selectAll: function(editorId) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.commands.selectAll();
            }}
        }},
        
        // =====================================================================
        // History
        // =====================================================================
        
        undo: function(editorId) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.commands.undo();
            }}
        }},
        
        redo: function(editorId) {{
            const editor = this.instances[editorId];
            if (editor) {{
                editor.commands.redo();
            }}
        }},
        
        // =====================================================================
        // State Queries
        // =====================================================================
        
        isEmpty: function(editorId) {{
            const editor = this.instances[editorId];
            return editor ? editor.isEmpty : true;
        }},
        
        getCharacterCount: function(editorId) {{
            const editor = this.instances[editorId];
            return editor ? editor.getText().length : 0;
        }},
        
        getWordCount: function(editorId) {{
            const editor = this.instances[editorId];
            if (!editor) return 0;
            const text = editor.getText().trim();
            return text ? text.split(/\\s+/).length : 0;
        }},
        
        isActive: function(editorId, name, attrs) {{
            const editor = this.instances[editorId];
            return editor ? editor.isActive(name, attrs) : false;
        }},
        
        can: function(editorId, command) {{
            const editor = this.instances[editorId];
            return editor ? editor.can()[command]?.() : false;
        }}
    }};
</script>
'''


class MarkdownEditor(Editor):
    """
    A convenience wrapper for Editor with markdown mode enabled.
    
    Equivalent to Editor(markdown=True, ...).
    
    Example:
        MarkdownEditor(
            id="md-editor",
            content="# Hello\\n\\nThis is **markdown**",
            on_change=handle_markdown,
            toolbar=True,
        )
    """
    
    def __init__(
        self,
        content: str = "",
        on_change: Optional[Callable[[str], None]] = None,
        placeholder: str = "Write markdown...",
        toolbar: Union[bool, List[str]] = True,
        extensions: Optional[List[str]] = None,
        editable: bool = True,
        autofocus: bool = False,
        min_height: str = "200px",
        max_height: Optional[str] = None,
        id: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        super().__init__(
            content=content,
            on_change=on_change,
            placeholder=placeholder,
            toolbar=toolbar,
            extensions=extensions,
            markdown=True,  # Always enabled for MarkdownEditor
            editable=editable,
            autofocus=autofocus,
            min_height=min_height,
            max_height=max_height,
            id=id,
            class_=class_,
            **attrs
        )


# Import extension modules
from .mentions import MentionConfig, MentionList, MentionChip, MentionExtensionLoader
from .slash import SlashCommand, SlashConfig, SlashMenu, SlashExtensionLoader, DEFAULT_SLASH_COMMANDS


__all__ = [
    # Components
    "Editor",
    "MarkdownEditor",
    "EditorContent",
    "EditorToolbar",
    # Programmatic control
    "EditorHandle",
    "use_editor",
    # Loaders
    "TiptapLoader",
    # Mentions extension
    "MentionConfig",
    "MentionList",
    "MentionChip",
    "MentionExtensionLoader",
    # Slash commands extension
    "SlashCommand",
    "SlashConfig",
    "SlashMenu",
    "SlashExtensionLoader",
    "DEFAULT_SLASH_COMMANDS",
]

