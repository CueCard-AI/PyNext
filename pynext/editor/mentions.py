"""
Mentions Extension for PyNext Editor

Add @mention support with customizable suggestions and dual UI options.

Usage:
    from pynext.editor import Editor
    from pynext.editor.mentions import MentionConfig
    
    # Basic mentions
    Editor(
        content=content,
        mentions=MentionConfig(
            trigger="@",
            suggestions=search_users,  # @server_action
        )
    )
    
    # With custom rendering
    Editor(
        content=content,
        mentions=MentionConfig(
            trigger="@",
            suggestions=search_users,
            render="inline",  # or "command" to use Command component
            item_render=lambda user: f"{user['name']} ({user['email']})"
        )
    )
"""

from typing import Any, Optional, List, Union, Callable, Dict, Literal
from dataclasses import dataclass, field
from pynext.tw import cn
import json


# Mention list styles
MENTION_LIST_BASE = (
    "absolute z-50 min-w-[200px] max-h-[300px] overflow-y-auto "
    "rounded-md border bg-popover p-1 shadow-md "
    "data-[state=open]:animate-in data-[state=closed]:animate-out "
    "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
)

MENTION_ITEM_BASE = (
    "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 "
    "text-sm outline-none hover:bg-accent hover:text-accent-foreground "
    "data-[highlighted=true]:bg-accent data-[highlighted=true]:text-accent-foreground"
)

MENTION_CHIP_BASE = (
    "inline-flex items-center rounded px-1.5 py-0.5 text-sm font-medium "
    "bg-primary/10 text-primary"
)


@dataclass
class MentionConfig:
    """
    Configuration for the mentions extension.
    
    Attributes:
        trigger: Character that triggers mention popup (default "@")
        suggestions: Callback to fetch suggestions (receives query string)
        render: UI style - "inline" for floating list, "command" for Command component
        item_render: Custom render function for suggestion items
        allow_spaces: Allow spaces in mention search query
        highlight_matches: Highlight matching text in suggestions
        debounce_ms: Debounce delay for suggestion fetching
        min_chars: Minimum characters before showing suggestions
        max_suggestions: Maximum suggestions to show
        placeholder: Placeholder text in search input
        empty_message: Message when no suggestions found
        on_mention_select: Callback when a mention is selected
    
    Example:
        MentionConfig(
            trigger="@",
            suggestions=search_users,
            render="inline",
            min_chars=2,
            max_suggestions=10,
        )
    """
    trigger: str = "@"
    suggestions: Optional[Callable[[str], List[dict]]] = None
    render: Literal["inline", "command"] = "inline"
    item_render: Optional[Callable[[dict], str]] = None
    allow_spaces: bool = False
    highlight_matches: bool = True
    debounce_ms: int = 150
    min_chars: int = 1
    max_suggestions: int = 10
    placeholder: str = "Search..."
    empty_message: str = "No results found"
    on_mention_select: Optional[Callable[[dict], None]] = None
    
    def to_dict(self) -> dict:
        """Convert config to dictionary for JSON serialization."""
        return {
            "trigger": self.trigger,
            "render": self.render,
            "allowSpaces": self.allow_spaces,
            "highlightMatches": self.highlight_matches,
            "debounceMs": self.debounce_ms,
            "minChars": self.min_chars,
            "maxSuggestions": self.max_suggestions,
            "placeholder": self.placeholder,
            "emptyMessage": self.empty_message,
        }


class MentionList:
    """
    Floating suggestion list for mentions.
    
    This is the inline UI option for mentions. It appears as a
    floating dropdown near the cursor when the trigger character is typed.
    
    Example:
        MentionList(
            items=users,
            query="joh",
            highlighted_index=0,
            on_select=select_user,
        )
    """
    
    def __init__(
        self,
        items: List[dict] = None,
        query: str = "",
        highlighted_index: int = 0,
        on_select: Optional[Callable[[dict], None]] = None,
        item_render: Optional[Callable[[dict], str]] = None,
        empty_message: str = "No results found",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.items = items or []
        self.query = query
        self.highlighted_index = highlighted_index
        self.on_select = on_select
        self.item_render = item_render
        self.empty_message = empty_message
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn(MENTION_LIST_BASE, self.extra_class)
        
        if not self.items:
            return f'''
<div data-pynext-mention-list class="{class_str}" data-state="open">
    <div class="px-2 py-4 text-sm text-muted-foreground text-center">
        {self.empty_message}
    </div>
</div>
'''
        
        items_html = []
        for i, item in enumerate(self.items):
            is_highlighted = i == self.highlighted_index
            item_class = cn(MENTION_ITEM_BASE)
            
            # Render item content
            if self.item_render:
                content = self.item_render(item)
            else:
                # Default: show 'label' or 'name' field
                content = item.get('label', item.get('name', str(item)))
            
            items_html.append(f'''
<div data-pynext-mention-item="{i}"
     data-value="{item.get('id', item.get('value', i))}"
     data-highlighted="{str(is_highlighted).lower()}"
     class="{item_class}"
     role="option"
     aria-selected="{str(is_highlighted).lower()}">
    {content}
</div>
''')
        
        return f'''
<div data-pynext-mention-list 
     class="{class_str}" 
     data-state="open"
     role="listbox">
    {"".join(items_html)}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class MentionChip:
    """
    Display a mention chip (the rendered @mention in content).
    
    Example:
        MentionChip(
            id="user-123",
            label="John Doe",
            href="/users/123",
        )
    """
    
    def __init__(
        self,
        id: str,
        label: str,
        href: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.id = id
        self.label = label
        self.href = href
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn(MENTION_CHIP_BASE, self.extra_class)
        
        if self.href:
            return f'''
<a href="{self.href}" 
   data-pynext-mention="{self.id}"
   class="{class_str}">
    @{self.label}
</a>
'''
        
        return f'''
<span data-pynext-mention="{self.id}" class="{class_str}">
    @{self.label}
</span>
'''
    
    def __str__(self) -> str:
        return self.render()


def MentionExtensionLoader() -> str:
    """
    JavaScript runtime for the mentions extension.
    Include this after TiptapLoader.
    
    Example:
        head()[
            TiptapLoader(),
            MentionExtensionLoader(),
        ]
    """
    return '''
<script>
(function() {
    // Extend PyNextEditor with mention support
    if (!window.PyNextEditor) {
        console.error('PyNextEditor not found. Include TiptapLoader first.');
        return;
    }
    
    // Add mention handling to PyNextEditor
    window.PyNextEditor.mentionState = {};
    
    window.PyNextEditor.initMentions = function(editorId, config) {
        const editor = this.instances[editorId];
        if (!editor) return;
        
        this.mentionState[editorId] = {
            active: false,
            query: '',
            items: [],
            highlightedIndex: 0,
            position: null,
            config: config,
        };
        
        // Listen for text changes to detect trigger
        editor.on('update', ({ editor }) => {
            this.checkMentionTrigger(editorId, editor);
        });
        
        // Handle keyboard navigation in mention list
        editor.view.dom.addEventListener('keydown', (e) => {
            const state = this.mentionState[editorId];
            if (!state?.active) return;
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    state.highlightedIndex = Math.min(
                        state.highlightedIndex + 1, 
                        state.items.length - 1
                    );
                    this.updateMentionList(editorId);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    state.highlightedIndex = Math.max(state.highlightedIndex - 1, 0);
                    this.updateMentionList(editorId);
                    break;
                case 'Enter':
                case 'Tab':
                    if (state.items.length > 0) {
                        e.preventDefault();
                        this.selectMention(editorId, state.items[state.highlightedIndex]);
                    }
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.closeMentionList(editorId);
                    break;
            }
        });
    };
    
    window.PyNextEditor.checkMentionTrigger = function(editorId, editor) {
        const state = this.mentionState[editorId];
        if (!state) return;
        
        const { trigger } = state.config;
        const { selection } = editor.state;
        const { $from } = selection;
        
        // Get text before cursor
        const textBefore = $from.parent.textContent.slice(0, $from.parentOffset);
        
        // Find trigger character
        const triggerIndex = textBefore.lastIndexOf(trigger);
        
        if (triggerIndex === -1) {
            this.closeMentionList(editorId);
            return;
        }
        
        // Check if there's a space between trigger and cursor (unless allowSpaces)
        const query = textBefore.slice(triggerIndex + trigger.length);
        if (!state.config.allowSpaces && query.includes(' ')) {
            this.closeMentionList(editorId);
            return;
        }
        
        // Check minimum characters
        if (query.length < state.config.minChars) {
            this.closeMentionList(editorId);
            return;
        }
        
        // Update query and fetch suggestions
        state.query = query;
        state.active = true;
        state.highlightedIndex = 0;
        
        // Get cursor position for popup placement
        const coords = editor.view.coordsAtPos($from.pos);
        state.position = { x: coords.left, y: coords.bottom };
        
        // Fetch suggestions (dispatch event for server action)
        this.fetchMentionSuggestions(editorId, query);
    };
    
    window.PyNextEditor.fetchMentionSuggestions = function(editorId, query) {
        const editor = this.instances[editorId];
        const container = editor?.view?.dom?.closest('[data-pynext-editor]');
        
        if (container) {
            container.dispatchEvent(new CustomEvent('pynext:mention-query', {
                bubbles: true,
                detail: { editorId, query }
            }));
        }
    };
    
    window.PyNextEditor.setMentionSuggestions = function(editorId, items) {
        const state = this.mentionState[editorId];
        if (!state) return;
        
        state.items = items.slice(0, state.config.maxSuggestions);
        state.highlightedIndex = 0;
        this.updateMentionList(editorId);
    };
    
    window.PyNextEditor.updateMentionList = function(editorId) {
        const state = this.mentionState[editorId];
        if (!state?.active) return;
        
        const editor = this.instances[editorId];
        const container = editor?.view?.dom?.closest('[data-pynext-editor]');
        
        if (container) {
            container.dispatchEvent(new CustomEvent('pynext:mention-update', {
                bubbles: true,
                detail: {
                    editorId,
                    items: state.items,
                    query: state.query,
                    highlightedIndex: state.highlightedIndex,
                    position: state.position,
                }
            }));
        }
    };
    
    window.PyNextEditor.selectMention = function(editorId, item) {
        const state = this.mentionState[editorId];
        const editor = this.instances[editorId];
        if (!state || !editor) return;
        
        const { trigger } = state.config;
        const { selection } = editor.state;
        const { $from } = selection;
        
        // Find and replace the trigger + query
        const textBefore = $from.parent.textContent.slice(0, $from.parentOffset);
        const triggerIndex = textBefore.lastIndexOf(trigger);
        
        if (triggerIndex !== -1) {
            const from = $from.pos - (textBefore.length - triggerIndex);
            const to = $from.pos;
            
            // Insert mention node
            const label = item.label || item.name || item.id;
            const mentionHtml = `<span data-pynext-mention="${item.id}" class="mention">@${label}</span>&nbsp;`;
            
            editor.chain()
                .focus()
                .deleteRange({ from, to })
                .insertContent(mentionHtml)
                .run();
        }
        
        // Dispatch selection event
        const container = editor.view.dom.closest('[data-pynext-editor]');
        if (container) {
            container.dispatchEvent(new CustomEvent('pynext:mention-select', {
                bubbles: true,
                detail: { editorId, item }
            }));
        }
        
        this.closeMentionList(editorId);
    };
    
    window.PyNextEditor.closeMentionList = function(editorId) {
        const state = this.mentionState[editorId];
        if (state) {
            state.active = false;
            state.items = [];
            state.query = '';
        }
        
        const editor = this.instances[editorId];
        const container = editor?.view?.dom?.closest('[data-pynext-editor]');
        
        if (container) {
            container.dispatchEvent(new CustomEvent('pynext:mention-close', {
                bubbles: true,
                detail: { editorId }
            }));
        }
    };
})();
</script>
'''


__all__ = [
    "MentionConfig",
    "MentionList",
    "MentionChip",
    "MentionExtensionLoader",
]

