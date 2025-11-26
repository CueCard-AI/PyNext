"""
Slash Commands Extension for PyNext Editor

Add / command palette with customizable commands.

Usage:
    from pynext.editor import Editor
    from pynext.editor.slash import SlashConfig, SlashCommand
    
    # Basic slash commands
    Editor(
        content=content,
        slash_commands=SlashConfig(
            commands=[
                SlashCommand("h1", "Heading 1", "heading", icon="H1"),
                SlashCommand("h2", "Heading 2", "heading", icon="H2"),
                SlashCommand("bullet", "Bullet List", "bulletList", icon="•"),
                SlashCommand("code", "Code Block", "codeBlock", icon="</>"),
            ]
        )
    )
    
    # With custom commands
    Editor(
        content=content,
        slash_commands=SlashConfig(
            commands=[
                SlashCommand(
                    id="template",
                    label="Insert Template",
                    action=lambda: insert_template(),
                    icon="📋",
                    description="Insert a predefined template"
                ),
            ]
        )
    )
"""

from typing import Any, Optional, List, Union, Callable, Literal
from dataclasses import dataclass, field
from pynext.tw import cn
import json


# Slash menu styles
SLASH_MENU_BASE = (
    "absolute z-50 min-w-[220px] max-h-[300px] overflow-y-auto "
    "rounded-md border bg-popover p-1 shadow-lg "
    "data-[state=open]:animate-in data-[state=closed]:animate-out "
    "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
)

SLASH_ITEM_BASE = (
    "relative flex cursor-pointer select-none items-center gap-2 rounded-sm px-2 py-1.5 "
    "text-sm outline-none hover:bg-accent hover:text-accent-foreground "
    "data-[highlighted=true]:bg-accent data-[highlighted=true]:text-accent-foreground"
)

SLASH_ITEM_ICON_BASE = (
    "flex h-8 w-8 items-center justify-center rounded border bg-background text-sm"
)

SLASH_ITEM_CONTENT_BASE = "flex flex-col"
SLASH_ITEM_LABEL_BASE = "font-medium"
SLASH_ITEM_DESC_BASE = "text-xs text-muted-foreground"

SLASH_GROUP_BASE = "py-1"
SLASH_GROUP_LABEL_BASE = "px-2 py-1.5 text-xs font-medium text-muted-foreground"


@dataclass
class SlashCommand:
    """
    A single slash command.
    
    Attributes:
        id: Unique identifier for the command
        label: Display label in the menu
        action: Built-in action name (e.g., "bold") or custom callback
        icon: Icon to display (emoji, text, or SVG)
        description: Optional description shown below label
        keywords: Additional search keywords
        group: Group name for organizing commands
    
    Example:
        SlashCommand(
            id="h1",
            label="Heading 1",
            action="heading",
            icon="H1",
            description="Large section heading",
            group="Headings",
        )
    """
    id: str
    label: str
    action: Union[str, Callable] = ""
    icon: str = ""
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    group: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "label": self.label,
            "action": self.action if isinstance(self.action, str) else f"custom:{self.id}",
            "icon": self.icon,
            "description": self.description,
            "keywords": self.keywords,
            "group": self.group,
        }


@dataclass
class SlashConfig:
    """
    Configuration for the slash commands extension.
    
    Attributes:
        commands: List of available slash commands
        trigger: Character that triggers the menu (default "/")
        render: UI style - "inline" for floating list, "command" for Command component
        filter_on_type: Filter commands as user types
        debounce_ms: Debounce delay for filtering
        placeholder: Placeholder text in search input
        empty_message: Message when no commands match
    
    Example:
        SlashConfig(
            commands=[
                SlashCommand("h1", "Heading 1", "heading"),
                SlashCommand("bullet", "Bullet List", "bulletList"),
            ],
            trigger="/",
            filter_on_type=True,
        )
    """
    commands: List[SlashCommand] = field(default_factory=list)
    trigger: str = "/"
    render: Literal["inline", "command"] = "inline"
    filter_on_type: bool = True
    debounce_ms: int = 50
    placeholder: str = "Type to filter..."
    empty_message: str = "No commands found"
    
    def to_dict(self) -> dict:
        """Convert config to dictionary for JSON serialization."""
        return {
            "commands": [cmd.to_dict() for cmd in self.commands],
            "trigger": self.trigger,
            "render": self.render,
            "filterOnType": self.filter_on_type,
            "debounceMs": self.debounce_ms,
            "placeholder": self.placeholder,
            "emptyMessage": self.empty_message,
        }


# Default commands for common formatting
DEFAULT_SLASH_COMMANDS = [
    SlashCommand("h1", "Heading 1", "heading", "H1", "Large section heading", ["title"], "Text"),
    SlashCommand("h2", "Heading 2", "heading", "H2", "Medium section heading", [], "Text"),
    SlashCommand("h3", "Heading 3", "heading", "H3", "Small section heading", [], "Text"),
    SlashCommand("bullet", "Bullet List", "bulletList", "•", "Create a bullet list", ["unordered"], "Lists"),
    SlashCommand("numbered", "Numbered List", "orderedList", "1.", "Create a numbered list", ["ordered"], "Lists"),
    SlashCommand("quote", "Quote", "blockquote", "❝", "Add a quote block", ["blockquote"], "Blocks"),
    SlashCommand("code", "Code Block", "codeBlock", "</>", "Add a code block", ["pre", "syntax"], "Blocks"),
    SlashCommand("divider", "Divider", "horizontalRule", "—", "Add a horizontal line", ["hr", "separator"], "Blocks"),
]


class SlashMenu:
    """
    Floating command menu for slash commands.
    
    This is the inline UI option for slash commands. It appears as a
    floating dropdown when the trigger character is typed.
    
    Example:
        SlashMenu(
            commands=filtered_commands,
            query="hea",
            highlighted_index=0,
            on_select=execute_command,
        )
    """
    
    def __init__(
        self,
        commands: List[SlashCommand] = None,
        query: str = "",
        highlighted_index: int = 0,
        on_select: Optional[Callable[[SlashCommand], None]] = None,
        show_groups: bool = True,
        empty_message: str = "No commands found",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.commands = commands or []
        self.query = query
        self.highlighted_index = highlighted_index
        self.on_select = on_select
        self.show_groups = show_groups
        self.empty_message = empty_message
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn(SLASH_MENU_BASE, self.extra_class)
        
        if not self.commands:
            return f'''
<div data-pynext-slash-menu class="{class_str}" data-state="open">
    <div class="px-2 py-4 text-sm text-muted-foreground text-center">
        {self.empty_message}
    </div>
</div>
'''
        
        # Group commands if needed
        if self.show_groups:
            groups = self._group_commands()
            items_html = self._render_groups(groups)
        else:
            items_html = self._render_items(self.commands, 0)
        
        return f'''
<div data-pynext-slash-menu 
     class="{class_str}" 
     data-state="open"
     role="listbox">
    {items_html}
</div>
'''
    
    def _group_commands(self) -> dict:
        """Group commands by their group property."""
        groups = {}
        for cmd in self.commands:
            group_name = cmd.group or "Other"
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(cmd)
        return groups
    
    def _render_groups(self, groups: dict) -> str:
        html_parts = []
        idx = 0
        
        for group_name, commands in groups.items():
            group_html = f'''
<div data-pynext-slash-group class="{cn(SLASH_GROUP_BASE)}">
    <div class="{cn(SLASH_GROUP_LABEL_BASE)}">{group_name}</div>
    {self._render_items(commands, idx)}
</div>
'''
            html_parts.append(group_html)
            idx += len(commands)
        
        return "".join(html_parts)
    
    def _render_items(self, commands: List[SlashCommand], start_idx: int) -> str:
        items_html = []
        
        for i, cmd in enumerate(commands):
            idx = start_idx + i
            is_highlighted = idx == self.highlighted_index
            item_class = cn(SLASH_ITEM_BASE)
            
            # Icon
            icon_html = f'''
<div class="{cn(SLASH_ITEM_ICON_BASE)}">
    {cmd.icon or cmd.id[:2].upper()}
</div>
'''
            
            # Label and description
            desc_html = ""
            if cmd.description:
                desc_html = f'<span class="{cn(SLASH_ITEM_DESC_BASE)}">{cmd.description}</span>'
            
            content_html = f'''
<div class="{cn(SLASH_ITEM_CONTENT_BASE)}">
    <span class="{cn(SLASH_ITEM_LABEL_BASE)}">{cmd.label}</span>
    {desc_html}
</div>
'''
            
            items_html.append(f'''
<div data-pynext-slash-item="{idx}"
     data-command="{cmd.id}"
     data-highlighted="{str(is_highlighted).lower()}"
     class="{item_class}"
     role="option"
     aria-selected="{str(is_highlighted).lower()}">
    {icon_html}
    {content_html}
</div>
''')
        
        return "".join(items_html)
    
    def __str__(self) -> str:
        return self.render()


def SlashExtensionLoader() -> str:
    """
    JavaScript runtime for the slash commands extension.
    Include this after TiptapLoader.
    
    Example:
        head()[
            TiptapLoader(),
            SlashExtensionLoader(),
        ]
    """
    return '''
<script>
(function() {
    // Extend PyNextEditor with slash command support
    if (!window.PyNextEditor) {
        console.error('PyNextEditor not found. Include TiptapLoader first.');
        return;
    }
    
    // Add slash command handling to PyNextEditor
    window.PyNextEditor.slashState = {};
    
    window.PyNextEditor.initSlashCommands = function(editorId, config) {
        const editor = this.instances[editorId];
        if (!editor) return;
        
        this.slashState[editorId] = {
            active: false,
            query: '',
            commands: config.commands || [],
            filteredCommands: config.commands || [],
            highlightedIndex: 0,
            position: null,
            config: config,
        };
        
        // Listen for text changes to detect trigger
        editor.on('update', ({ editor }) => {
            this.checkSlashTrigger(editorId, editor);
        });
        
        // Handle keyboard navigation in slash menu
        editor.view.dom.addEventListener('keydown', (e) => {
            const state = this.slashState[editorId];
            if (!state?.active) return;
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    state.highlightedIndex = Math.min(
                        state.highlightedIndex + 1, 
                        state.filteredCommands.length - 1
                    );
                    this.updateSlashMenu(editorId);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    state.highlightedIndex = Math.max(state.highlightedIndex - 1, 0);
                    this.updateSlashMenu(editorId);
                    break;
                case 'Enter':
                case 'Tab':
                    if (state.filteredCommands.length > 0) {
                        e.preventDefault();
                        this.executeSlashCommand(editorId, state.filteredCommands[state.highlightedIndex]);
                    }
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.closeSlashMenu(editorId);
                    break;
            }
        });
    };
    
    window.PyNextEditor.checkSlashTrigger = function(editorId, editor) {
        const state = this.slashState[editorId];
        if (!state) return;
        
        const { trigger } = state.config;
        const { selection } = editor.state;
        const { $from } = selection;
        
        // Get text before cursor in current block
        const textBefore = $from.parent.textContent.slice(0, $from.parentOffset);
        
        // Check if line starts with trigger (slash commands typically at start of block)
        const lastNewline = textBefore.lastIndexOf('\\n');
        const lineStart = lastNewline === -1 ? 0 : lastNewline + 1;
        const lineText = textBefore.slice(lineStart);
        
        if (!lineText.startsWith(trigger)) {
            this.closeSlashMenu(editorId);
            return;
        }
        
        // Get query (text after trigger)
        const query = lineText.slice(trigger.length);
        
        // Don't show if there's a space in query (command selected)
        if (query.includes(' ')) {
            this.closeSlashMenu(editorId);
            return;
        }
        
        // Update state
        state.query = query;
        state.active = true;
        state.highlightedIndex = 0;
        
        // Filter commands
        if (state.config.filterOnType && query) {
            const lowerQuery = query.toLowerCase();
            state.filteredCommands = state.commands.filter(cmd => 
                cmd.label.toLowerCase().includes(lowerQuery) ||
                cmd.id.toLowerCase().includes(lowerQuery) ||
                (cmd.keywords || []).some(kw => kw.toLowerCase().includes(lowerQuery))
            );
        } else {
            state.filteredCommands = state.commands;
        }
        
        // Get cursor position for popup placement
        const coords = editor.view.coordsAtPos($from.pos);
        state.position = { x: coords.left, y: coords.bottom };
        
        this.updateSlashMenu(editorId);
    };
    
    window.PyNextEditor.updateSlashMenu = function(editorId) {
        const state = this.slashState[editorId];
        if (!state?.active) return;
        
        const editor = this.instances[editorId];
        const container = editor?.view?.dom?.closest('[data-pynext-editor]');
        
        if (container) {
            container.dispatchEvent(new CustomEvent('pynext:slash-update', {
                bubbles: true,
                detail: {
                    editorId,
                    commands: state.filteredCommands,
                    query: state.query,
                    highlightedIndex: state.highlightedIndex,
                    position: state.position,
                }
            }));
        }
    };
    
    window.PyNextEditor.executeSlashCommand = function(editorId, command) {
        const state = this.slashState[editorId];
        const editor = this.instances[editorId];
        if (!state || !editor) return;
        
        const { trigger } = state.config;
        const { selection } = editor.state;
        const { $from } = selection;
        
        // Find and delete the trigger + query
        const textBefore = $from.parent.textContent.slice(0, $from.parentOffset);
        const lastNewline = textBefore.lastIndexOf('\\n');
        const lineStart = lastNewline === -1 ? 0 : lastNewline + 1;
        
        const from = $from.pos - (textBefore.length - lineStart);
        const to = $from.pos;
        
        // Delete the slash command text
        editor.chain().focus().deleteRange({ from, to }).run();
        
        // Execute the command action
        if (typeof command.action === 'string') {
            this.executeCommand(editorId, command.action);
        } else {
            // Custom command - dispatch event
            const container = editor.view.dom.closest('[data-pynext-editor]');
            if (container) {
                container.dispatchEvent(new CustomEvent('pynext:slash-execute', {
                    bubbles: true,
                    detail: { editorId, command }
                }));
            }
        }
        
        this.closeSlashMenu(editorId);
    };
    
    window.PyNextEditor.closeSlashMenu = function(editorId) {
        const state = this.slashState[editorId];
        if (state) {
            state.active = false;
            state.filteredCommands = state.commands;
            state.query = '';
        }
        
        const editor = this.instances[editorId];
        const container = editor?.view?.dom?.closest('[data-pynext-editor]');
        
        if (container) {
            container.dispatchEvent(new CustomEvent('pynext:slash-close', {
                bubbles: true,
                detail: { editorId }
            }));
        }
    };
})();
</script>
'''


__all__ = [
    "SlashCommand",
    "SlashConfig",
    "SlashMenu",
    "SlashExtensionLoader",
    "DEFAULT_SLASH_COMMANDS",
]

