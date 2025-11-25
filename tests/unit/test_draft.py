"""
Unit tests for Draft Mode.

Tests:
- Draft signal
- Draft decorators
- Draft components
- Token management
"""

import pytest
from pynext.core.draft import (
    DraftSignal,
    DraftContext,
    use_draft,
    is_draft_mode,
    enable_draft,
    disable_draft,
    draft_content,
    draft_only,
    published_only,
    DraftSwitch,
    DraftBanner,
    DraftOverlay,
    get_draft_context,
    create_draft_context,
    get_draft_runtime_js,
    get_draft_css,
)
from pynext.server.draft import (
    generate_draft_token,
    verify_draft_token,
    DraftConfig,
)
from pynext.core.html import div, p


class TestDraftSignal:
    """Tests for DraftSignal."""
    
    def test_signal_creation(self):
        """Should create draft signal."""
        signal = DraftSignal(False)
        
        assert signal() is False
    
    def test_signal_enable(self):
        """Signal should enable with token."""
        signal = DraftSignal(False)
        signal.enable("test-token")
        
        assert signal() is True
        assert signal.is_authenticated()
    
    def test_signal_disable(self):
        """Signal should disable."""
        signal = DraftSignal(True)
        signal._draft_token = "token"
        signal.disable()
        
        assert signal() is False
        assert not signal.is_authenticated()
    
    def test_signal_toggle(self):
        """Signal should toggle."""
        signal = DraftSignal(False)
        
        signal.toggle()
        assert signal() is True
        
        signal.toggle()
        assert signal() is False


class TestDraftFunctions:
    """Tests for draft helper functions."""
    
    def test_use_draft_returns_signal(self):
        """use_draft should return the draft signal."""
        signal = use_draft()
        
        assert isinstance(signal, DraftSignal)
    
    def test_enable_disable_draft(self):
        """enable_draft and disable_draft should work."""
        disable_draft()  # Reset
        
        assert is_draft_mode() is False
        
        enable_draft("test-token")
        assert is_draft_mode() is True
        
        disable_draft()
        assert is_draft_mode() is False


class TestDraftContext:
    """Tests for draft context."""
    
    def test_create_context(self):
        """Should create draft context."""
        ctx = create_draft_context(is_draft=True, token="token123")
        
        assert ctx.is_draft is True
        assert ctx.draft_token == "token123"
    
    def test_context_defaults(self):
        """Context should have sensible defaults."""
        ctx = DraftContext()
        
        assert ctx.is_draft is False
        assert ctx.draft_token is None


class TestDraftDecorators:
    """Tests for draft decorators."""
    
    def setup_method(self):
        """Reset draft mode before each test."""
        disable_draft()
    
    def test_draft_content_decorator(self):
        """@draft_content should mark function."""
        @draft_content()
        def my_content():
            return div()["Draft"]
        
        assert hasattr(my_content, '_is_draft_content')
    
    def test_draft_only_decorator(self):
        """@draft_only should hide content in published mode."""
        @draft_only
        def draft_warning():
            return div()["Draft warning"]
        
        # In published mode
        result = draft_warning()
        assert result == ""
        
        # In draft mode
        enable_draft("token")
        result = draft_warning()
        assert "Draft warning" in result
        disable_draft()
    
    def test_published_only_decorator(self):
        """@published_only should hide content in draft mode."""
        @published_only
        def published_content():
            return div()["Published"]
        
        # In published mode
        result = published_content()
        assert "Published" in result
        
        # In draft mode
        enable_draft("token")
        result = published_content()
        assert result == ""
        disable_draft()


class TestDraftSwitch:
    """Tests for DraftSwitch component."""
    
    def setup_method(self):
        """Reset draft mode before each test."""
        disable_draft()
    
    def test_switch_shows_published(self):
        """DraftSwitch should show published content by default."""
        switch = DraftSwitch(
            draft=lambda: div()["Draft"],
            published=lambda: div()["Published"],
        )
        
        html = switch.render()
        
        assert "Published" in html
        assert 'data-mode="published"' in html
    
    def test_switch_shows_draft(self):
        """DraftSwitch should show draft content when enabled."""
        enable_draft("token")
        
        switch = DraftSwitch(
            draft=lambda: div()["Draft"],
            published=lambda: div()["Published"],
        )
        
        html = switch.render()
        
        assert "Draft" in html
        assert 'data-mode="draft"' in html
        
        disable_draft()


class TestDraftBanner:
    """Tests for DraftBanner component."""
    
    def setup_method(self):
        """Reset draft mode before each test."""
        disable_draft()
    
    def test_banner_hidden_in_published(self):
        """Banner should be hidden in published mode."""
        banner = DraftBanner()
        html = banner.render()
        
        assert html == ""
    
    def test_banner_shown_in_draft(self):
        """Banner should be shown in draft mode."""
        enable_draft("token")
        
        banner = DraftBanner(exit_url="/api/exit")
        html = banner.render()
        
        assert "draft-banner" in html
        assert "/api/exit" in html
        assert "Draft Mode" in html
        
        disable_draft()
    
    def test_banner_edit_button(self):
        """Banner should show edit button if configured."""
        enable_draft("token")
        
        banner = DraftBanner(edit_url="/cms/edit")
        html = banner.render()
        
        assert "/cms/edit" in html
        
        disable_draft()


class TestDraftOverlay:
    """Tests for DraftOverlay component."""
    
    def setup_method(self):
        """Reset draft mode before each test."""
        disable_draft()
    
    def test_overlay_hidden_in_published(self):
        """Overlay should be hidden in published mode."""
        overlay = DraftOverlay()
        html = overlay.render()
        
        assert html == ""
    
    def test_overlay_shown_in_draft(self):
        """Overlay should be shown in draft mode."""
        enable_draft("token")
        
        overlay = DraftOverlay()
        html = overlay.render()
        
        assert "draft-overlay" in html
        
        disable_draft()


class TestDraftToken:
    """Tests for draft token management."""
    
    def test_generate_token(self):
        """Should generate valid token."""
        token = generate_draft_token("secret", ttl=3600)
        
        assert token
        assert "." in token  # Has signature
    
    def test_verify_valid_token(self):
        """Should verify valid token."""
        token = generate_draft_token("secret", ttl=3600)
        payload = verify_draft_token(token, "secret")
        
        assert payload is not None
        assert "exp" in payload
    
    def test_verify_invalid_token(self):
        """Should reject invalid token."""
        payload = verify_draft_token("invalid.token", "secret")
        
        assert payload is None
    
    def test_verify_wrong_secret(self):
        """Should reject token with wrong secret."""
        token = generate_draft_token("secret1", ttl=3600)
        payload = verify_draft_token(token, "secret2")
        
        assert payload is None


class TestDraftRuntime:
    """Tests for draft JavaScript runtime."""
    
    def test_runtime_content(self):
        """Draft runtime should have essential functions."""
        js = get_draft_runtime_js()
        
        assert "__pynext__.draft" in js
        assert "enable" in js
        assert "disable" in js
        assert "toggle" in js
        assert "update" in js
    
    def test_css_content(self):
        """Draft CSS should have essential styles."""
        css = get_draft_css()
        
        assert ".draft-banner" in css
        assert ".draft-banner-top" in css


class TestSignalBasedUpdates:
    """Tests for signal-based draft updates."""
    
    def setup_method(self):
        """Reset draft mode before each test."""
        disable_draft()
    
    def test_draft_content_has_marker(self):
        """Draft content should have data attribute for updates."""
        @draft_content()
        def content():
            return div()["Content"]
        
        result = content()
        
        assert "data-draft-aware" in result
    
    def test_draft_only_has_marker(self):
        """Draft-only content should have marker."""
        enable_draft("token")
        
        @draft_only
        def banner():
            return div()["Banner"]
        
        result = banner()
        
        assert "data-draft-only" in result
        
        disable_draft()

