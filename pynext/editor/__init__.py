"""
PyNext Rich Text Editor

A rich text editor built on Tiptap for content editing.
Supports markdown, mentions, slash commands, and more.

Usage:
    from pynext.editor import Editor, EditorContent, EditorToolbar
    
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
"""

from typing import Any, Optional, List, Union, Callable, Dict, Literal
from pynext.tw import cn
import json
import hashlib


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
        content: Initial HTML content
        on_change: Callback when content changes
        placeholder: Placeholder text
        toolbar: Show toolbar (True for default, or list of extensions)
        extensions: List of enabled extensions
        editable: Whether editor is editable
        autofocus: Focus editor on mount
        min_height: Minimum height
        max_height: Maximum height (enables scrolling)
        class_: Additional CSS classes
    
    Example:
        Editor(
            content="<p>Hello world</p>",
            on_change=handle_update,
            toolbar=True,
            placeholder="Start writing..."
        )
    """
    
    def __init__(
        self,
        content: str = "",
        on_change: Optional[Callable[[str], None]] = None,
        placeholder: str = "",
        toolbar: Union[bool, List[str]] = True,
        extensions: Optional[List[str]] = None,
        editable: bool = True,
        autofocus: bool = False,
        min_height: str = "200px",
        max_height: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.content = content
        self.on_change = on_change
        self.placeholder = placeholder
        self.toolbar = toolbar
        self.extensions = extensions or DEFAULT_EXTENSIONS
        self.editable = editable
        self.autofocus = autofocus
        self.min_height = min_height
        self.max_height = max_height
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        editor_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
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
        }
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
def TiptapLoader() -> str:
    """
    Include Tiptap and dependencies from CDN.
    Add this to your layout's <head>.
    
    Example:
        head()[
            TiptapLoader(),
            ...
        ]
    """
    return '''
<!-- Tiptap Core and Extensions -->
<script src="https://unpkg.com/@tiptap/core@2.1.12/dist/index.umd.js"></script>
<script src="https://unpkg.com/@tiptap/starter-kit@2.1.12/dist/index.umd.js"></script>
<script src="https://unpkg.com/@tiptap/extension-placeholder@2.1.12/dist/index.umd.js"></script>
<script>
    // PyNext Editor wrapper
    window.PyNextEditor = {
        instances: {},
        
        create: function(container, config) {
            const editorId = container.dataset.pynextEditor;
            const contentEl = container.querySelector('[data-pynext-editor-content]');
            
            if (!contentEl) return;
            
            // Build extensions based on config
            const extensions = [
                window.TiptapStarterKit.StarterKit,
            ];
            
            if (config.placeholder) {
                extensions.push(window.TiptapPlaceholder.Placeholder.configure({
                    placeholder: config.placeholder
                }));
            }
            
            // Create editor
            const editor = new window.TiptapCore.Editor({
                element: contentEl,
                extensions: extensions,
                content: config.content,
                editable: config.editable !== false,
                autofocus: config.autofocus,
                onUpdate: ({ editor }) => {
                    const html = editor.getHTML();
                    container.dispatchEvent(new CustomEvent('pynext:editor-change', {
                        bubbles: true,
                        detail: { html }
                    }));
                }
            });
            
            this.instances[editorId] = editor;
            
            // Wire up toolbar buttons
            container.querySelectorAll('[data-pynext-editor-action]').forEach(btn => {
                btn.addEventListener('click', () => {
                    const action = btn.dataset.pynextEditorAction;
                    this.executeCommand(editorId, action);
                });
            });
            
            return editor;
        },
        
        executeCommand: function(editorId, command) {
            const editor = this.instances[editorId];
            if (!editor) return;
            
            const chain = editor.chain().focus();
            
            switch (command) {
                case 'bold': chain.toggleBold().run(); break;
                case 'italic': chain.toggleItalic().run(); break;
                case 'strike': chain.toggleStrike().run(); break;
                case 'underline': chain.toggleUnderline().run(); break;
                case 'code': chain.toggleCode().run(); break;
                case 'heading': chain.toggleHeading({ level: 2 }).run(); break;
                case 'bulletList': chain.toggleBulletList().run(); break;
                case 'orderedList': chain.toggleOrderedList().run(); break;
                case 'blockquote': chain.toggleBlockquote().run(); break;
                case 'codeBlock': chain.toggleCodeBlock().run(); break;
                case 'horizontalRule': chain.setHorizontalRule().run(); break;
                default: console.warn('Unknown command:', command);
            }
        },
        
        getContent: function(editorId) {
            const editor = this.instances[editorId];
            return editor ? editor.getHTML() : '';
        },
        
        setContent: function(editorId, content) {
            const editor = this.instances[editorId];
            if (editor) editor.commands.setContent(content);
        }
    };
</script>
'''


__all__ = [
    "Editor",
    "EditorContent",
    "EditorToolbar",
    "TiptapLoader",
]

