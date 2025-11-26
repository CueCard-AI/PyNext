"""
Unit tests for Advanced Editor Features

Tests for:
- EditorHandle and use_editor()
- Markdown extension
- Mentions extension  
- Slash commands extension
"""

import pytest
from datetime import date


class TestEditorHandle:
    """Tests for the EditorHandle programmatic API."""
    
    def test_use_editor_returns_handle(self):
        from pynext.editor import use_editor, EditorHandle
        
        handle = use_editor("my-editor")
        
        assert isinstance(handle, EditorHandle)
        assert handle.editor_id == "my-editor"
    
    def test_get_content_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        js = handle.get_content()
        
        assert js == 'window.PyNextEditor.getContent("test-editor")'
    
    def test_set_content_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        js = handle.set_content("<p>Hello</p>")
        
        assert 'window.PyNextEditor.setContent("test-editor"' in js
        assert "<p>Hello</p>" in js
    
    def test_toggle_bold_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        js = handle.toggle_bold()
        
        assert 'executeCommand("test-editor", "bold")' in js
    
    def test_toggle_italic_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        js = handle.toggle_italic()
        
        assert 'executeCommand("test-editor", "italic")' in js
    
    def test_focus_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        js = handle.focus()
        
        assert 'window.PyNextEditor.focus("test-editor")' in js
    
    def test_clear_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        js = handle.clear()
        
        assert 'window.PyNextEditor.clear("test-editor")' in js
    
    def test_get_markdown_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("md-editor")
        js = handle.get_markdown()
        
        assert 'window.PyNextEditor.getMarkdown("md-editor")' in js
    
    def test_set_markdown_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("md-editor")
        js = handle.set_markdown("# Hello\n\nWorld")
        
        assert 'window.PyNextEditor.setMarkdown("md-editor"' in js
        assert "# Hello" in js
    
    def test_insert_text_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        js = handle.insert_text("Hello World")
        
        assert 'window.PyNextEditor.insertText("test-editor"' in js
        assert "Hello World" in js
    
    def test_set_heading_generates_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        js = handle.toggle_heading(level=1)
        
        assert 'setHeading("test-editor", 1)' in js
    
    def test_undo_redo_generate_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        
        assert 'undo("test-editor")' in handle.undo()
        assert 'redo("test-editor")' in handle.redo()
    
    def test_link_methods_generate_js(self):
        from pynext.editor import use_editor
        
        handle = use_editor("test-editor")
        
        js = handle.set_link("https://example.com")
        assert 'setLink("test-editor"' in js
        assert "https://example.com" in js
        
        js = handle.unset_link()
        assert 'unsetLink("test-editor")' in js


class TestMarkdownExtension:
    """Tests for markdown mode in Editor."""
    
    def test_editor_markdown_mode(self):
        from pynext.editor import Editor
        
        ed = Editor(
            id="md-editor",
            content="# Hello",
            markdown=True,
        )
        html = ed.render()
        
        assert '"markdown": true' in html or '"markdown":true' in html
    
    def test_markdown_editor_convenience(self):
        from pynext.editor import MarkdownEditor
        
        ed = MarkdownEditor(
            id="md-editor",
            content="# Hello",
        )
        html = ed.render()
        
        # Should have markdown enabled
        assert '"markdown": true' in html or '"markdown":true' in html
    
    def test_tiptap_loader_without_markdown(self):
        from pynext.editor import TiptapLoader
        
        html = TiptapLoader(markdown=False)
        
        # Should not include markdown library CDN scripts
        assert "unpkg.com/turndown" not in html
        assert "unpkg.com/marked" not in html
    
    def test_tiptap_loader_with_markdown(self):
        from pynext.editor import TiptapLoader
        
        html = TiptapLoader(markdown=True)
        
        # Should include markdown libraries
        assert "turndown" in html
        assert "marked" in html


class TestMentionsExtension:
    """Tests for @mention support."""
    
    def test_mention_config_creation(self):
        from pynext.editor.mentions import MentionConfig
        
        config = MentionConfig(
            trigger="@",
            min_chars=2,
            max_suggestions=10,
        )
        
        assert config.trigger == "@"
        assert config.min_chars == 2
        assert config.max_suggestions == 10
    
    def test_mention_config_to_dict(self):
        from pynext.editor.mentions import MentionConfig
        
        config = MentionConfig(
            trigger="#",
            debounce_ms=200,
        )
        d = config.to_dict()
        
        assert d["trigger"] == "#"
        assert d["debounceMs"] == 200
    
    def test_mention_list_render_empty(self):
        from pynext.editor.mentions import MentionList
        
        ml = MentionList(items=[], empty_message="No users found")
        html = ml.render()
        
        assert "data-pynext-mention-list" in html
        assert "No users found" in html
    
    def test_mention_list_render_with_items(self):
        from pynext.editor.mentions import MentionList
        
        items = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
        ]
        ml = MentionList(items=items, highlighted_index=0)
        html = ml.render()
        
        assert "data-pynext-mention-item" in html
        assert "Alice" in html
        assert "Bob" in html
        assert 'data-highlighted="true"' in html
    
    def test_mention_chip_render(self):
        from pynext.editor.mentions import MentionChip
        
        chip = MentionChip(id="user-123", label="John Doe")
        html = chip.render()
        
        assert 'data-pynext-mention="user-123"' in html
        assert "@John Doe" in html
    
    def test_mention_chip_with_link(self):
        from pynext.editor.mentions import MentionChip
        
        chip = MentionChip(
            id="user-123",
            label="John Doe",
            href="/users/123"
        )
        html = chip.render()
        
        assert "<a href=" in html
        assert "/users/123" in html
    
    def test_editor_with_mentions(self):
        from pynext.editor import Editor
        from pynext.editor.mentions import MentionConfig
        
        config = MentionConfig(trigger="@", min_chars=1)
        ed = Editor(
            id="mention-editor",
            content="Hello",
            mentions=config,
        )
        html = ed.render()
        
        assert '"mentions"' in html or "'mentions'" in html


class TestSlashCommands:
    """Tests for slash command support."""
    
    def test_slash_command_creation(self):
        from pynext.editor.slash import SlashCommand
        
        cmd = SlashCommand(
            id="h1",
            label="Heading 1",
            action="heading",
            icon="H1",
            description="Large heading",
        )
        
        assert cmd.id == "h1"
        assert cmd.label == "Heading 1"
        assert cmd.action == "heading"
    
    def test_slash_command_to_dict(self):
        from pynext.editor.slash import SlashCommand
        
        cmd = SlashCommand(
            id="bullet",
            label="Bullet List",
            action="bulletList",
            keywords=["list", "unordered"],
        )
        d = cmd.to_dict()
        
        assert d["id"] == "bullet"
        assert d["action"] == "bulletList"
        assert "list" in d["keywords"]
    
    def test_slash_config_creation(self):
        from pynext.editor.slash import SlashConfig, SlashCommand
        
        config = SlashConfig(
            commands=[
                SlashCommand("h1", "Heading 1", "heading"),
                SlashCommand("bullet", "Bullet List", "bulletList"),
            ],
            trigger="/",
        )
        
        assert config.trigger == "/"
        assert len(config.commands) == 2
    
    def test_slash_config_to_dict(self):
        from pynext.editor.slash import SlashConfig, SlashCommand
        
        config = SlashConfig(
            commands=[SlashCommand("h1", "Heading 1", "heading")],
            filter_on_type=True,
        )
        d = config.to_dict()
        
        assert d["trigger"] == "/"
        assert d["filterOnType"] == True
        assert len(d["commands"]) == 1
    
    def test_slash_menu_render_empty(self):
        from pynext.editor.slash import SlashMenu
        
        menu = SlashMenu(commands=[], empty_message="No commands")
        html = menu.render()
        
        assert "data-pynext-slash-menu" in html
        assert "No commands" in html
    
    def test_slash_menu_render_with_commands(self):
        from pynext.editor.slash import SlashMenu, SlashCommand
        
        commands = [
            SlashCommand("h1", "Heading 1", "heading", "H1", "Large heading"),
            SlashCommand("bullet", "Bullet List", "bulletList", "•"),
        ]
        menu = SlashMenu(commands=commands, highlighted_index=0)
        html = menu.render()
        
        assert "data-pynext-slash-item" in html
        assert "Heading 1" in html
        assert "Bullet List" in html
        assert 'data-highlighted="true"' in html
    
    def test_slash_menu_with_groups(self):
        from pynext.editor.slash import SlashMenu, SlashCommand
        
        commands = [
            SlashCommand("h1", "Heading 1", "heading", group="Text"),
            SlashCommand("bullet", "Bullet", "bulletList", group="Lists"),
        ]
        menu = SlashMenu(commands=commands, show_groups=True)
        html = menu.render()
        
        assert "data-pynext-slash-group" in html
        assert "Text" in html
        assert "Lists" in html
    
    def test_default_slash_commands_exist(self):
        from pynext.editor.slash import DEFAULT_SLASH_COMMANDS
        
        assert len(DEFAULT_SLASH_COMMANDS) > 0
        
        ids = [cmd.id for cmd in DEFAULT_SLASH_COMMANDS]
        assert "h1" in ids
        assert "bullet" in ids
        assert "code" in ids
    
    def test_editor_with_slash_commands(self):
        from pynext.editor import Editor
        from pynext.editor.slash import SlashConfig, SlashCommand
        
        config = SlashConfig(
            commands=[SlashCommand("h1", "Heading", "heading")]
        )
        ed = Editor(
            id="slash-editor",
            content="Hello",
            slash_commands=config,
        )
        html = ed.render()
        
        assert '"slashCommands"' in html or "'slashCommands'" in html


class TestEditorRenderWithId:
    """Tests for Editor ID handling."""
    
    def test_editor_uses_provided_id(self):
        from pynext.editor import Editor
        
        ed = Editor(id="custom-id", content="Hello")
        html = ed.render()
        
        assert 'data-pynext-editor="custom-id"' in html
    
    def test_editor_generates_id_when_not_provided(self):
        from pynext.editor import Editor
        
        ed = Editor(content="Hello")
        html = ed.render()
        
        # Should have a generated ID (8 hex chars)
        assert 'data-pynext-editor="' in html
        
        # Extract the ID
        import re
        match = re.search(r'data-pynext-editor="([a-f0-9]+)"', html)
        assert match
        assert len(match.group(1)) == 8


class TestTiptapLoaderRuntime:
    """Tests for the TiptapLoader JavaScript runtime."""
    
    def test_loader_includes_editor_wrapper(self):
        from pynext.editor import TiptapLoader
        
        html = TiptapLoader()
        
        assert "window.PyNextEditor" in html
        assert "instances" in html
    
    def test_loader_includes_create_method(self):
        from pynext.editor import TiptapLoader
        
        html = TiptapLoader()
        
        assert "create: function" in html
    
    def test_loader_includes_content_methods(self):
        from pynext.editor import TiptapLoader
        
        html = TiptapLoader()
        
        assert "getContent:" in html
        assert "setContent:" in html
        assert "getText:" in html
    
    def test_loader_includes_markdown_methods(self):
        from pynext.editor import TiptapLoader
        
        html = TiptapLoader()
        
        assert "getMarkdown:" in html
        assert "setMarkdown:" in html
    
    def test_loader_includes_formatting_methods(self):
        from pynext.editor import TiptapLoader
        
        html = TiptapLoader()
        
        assert "executeCommand:" in html
        assert "setHeading:" in html
        assert "setLink:" in html
    
    def test_loader_includes_utility_methods(self):
        from pynext.editor import TiptapLoader
        
        html = TiptapLoader()
        
        assert "focus:" in html
        assert "blur:" in html
        assert "clear:" in html
        assert "undo:" in html
        assert "redo:" in html
    
    def test_loader_includes_state_queries(self):
        from pynext.editor import TiptapLoader
        
        html = TiptapLoader()
        
        assert "isEmpty:" in html
        assert "getCharacterCount:" in html
        assert "getWordCount:" in html


class TestExtensionLoaders:
    """Tests for extension loader scripts."""
    
    def test_mention_extension_loader(self):
        from pynext.editor.mentions import MentionExtensionLoader
        
        html = MentionExtensionLoader()
        
        assert "PyNextEditor.mentionState" in html
        assert "initMentions" in html
        assert "checkMentionTrigger" in html
        assert "selectMention" in html
    
    def test_slash_extension_loader(self):
        from pynext.editor.slash import SlashExtensionLoader
        
        html = SlashExtensionLoader()
        
        assert "PyNextEditor.slashState" in html
        assert "initSlashCommands" in html
        assert "checkSlashTrigger" in html
        assert "executeSlashCommand" in html


class TestEditorExports:
    """Tests that all components are properly exported."""
    
    def test_main_exports(self):
        from pynext.editor import (
            Editor,
            MarkdownEditor,
            EditorContent,
            EditorToolbar,
            EditorHandle,
            use_editor,
            TiptapLoader,
        )
        
        assert Editor is not None
        assert MarkdownEditor is not None
        assert EditorHandle is not None
        assert use_editor is not None
    
    def test_mention_exports(self):
        from pynext.editor import (
            MentionConfig,
            MentionList,
            MentionChip,
            MentionExtensionLoader,
        )
        
        assert MentionConfig is not None
        assert MentionList is not None
    
    def test_slash_exports(self):
        from pynext.editor import (
            SlashCommand,
            SlashConfig,
            SlashMenu,
            SlashExtensionLoader,
            DEFAULT_SLASH_COMMANDS,
        )
        
        assert SlashCommand is not None
        assert SlashConfig is not None
        assert len(DEFAULT_SLASH_COMMANDS) > 0

