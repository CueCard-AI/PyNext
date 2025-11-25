"""
Unit tests for Intercepting Routes.

Tests:
- Interception rule parsing
- Modal component
- URL-driven state
- Background preservation
"""

import pytest
from pynext.router.intercept import (
    InterceptionType,
    InterceptionRule,
    InterceptionMatch,
    CompiledInterceptionMap,
    InterceptionScanner,
    get_interception_scanner,
    check_interception,
)
from pynext.core.modal import (
    Modal,
    ModalPortal,
    ModalContext,
    get_modal_context,
    create_modal_context,
    modal,
    photo_modal,
    form_modal,
    get_modal_runtime_js,
    get_modal_css,
)
from pynext.core.html import div, p


class TestInterceptionTypes:
    """Tests for interception types."""
    
    def test_soft_interception(self):
        """(..) should be soft interception."""
        assert InterceptionType.SOFT.value == "soft"
    
    def test_hard_interception(self):
        """(...) should be hard interception."""
        assert InterceptionType.HARD.value == "hard"
    
    def test_sibling_interception(self):
        """(.) should be sibling interception."""
        assert InterceptionType.SIBLING.value == "sibling"


class TestInterceptionRule:
    """Tests for interception rules."""
    
    def test_rule_creation(self):
        """Should create interception rule."""
        rule = InterceptionRule(
            source_pattern="/gallery",
            target_pattern="/photos/:id",
            interception_type=InterceptionType.SOFT,
            interceptor_path="/pages/@modal/(..)photos/[id]/page.py",
            original_path="/photos/:id",
        )
        
        assert rule.target_pattern == "/photos/:id"
        assert rule.interception_type == InterceptionType.SOFT
    
    def test_rule_default_slot(self):
        """Rule should default to 'modal' slot."""
        rule = InterceptionRule(
            source_pattern="",
            target_pattern="/photos/:id",
            interception_type=InterceptionType.SOFT,
            interceptor_path="",
            original_path="",
        )
        
        assert rule.slot_name == "modal"


class TestCompiledInterceptionMap:
    """Tests for compiled interception map."""
    
    def test_map_creation(self):
        """Should create compiled map."""
        rules = [
            InterceptionRule(
                source_pattern="",
                target_pattern="/photos/:id",
                interception_type=InterceptionType.SOFT,
                interceptor_path="/pages/@modal/(..)photos/[id]/page.py",
                original_path="/photos",
            ),
        ]
        
        map_ = CompiledInterceptionMap(rules=rules)
        
        assert "/photos/:id" in map_.target_index
    
    def test_should_intercept_with_referrer(self):
        """Map should intercept with valid referrer."""
        rules = [
            InterceptionRule(
                source_pattern="",
                target_pattern="/photos/:id",
                interception_type=InterceptionType.HARD,
                interceptor_path="/pages/@modal/(...)photos/[id]/page.py",
                original_path="/photos",
            ),
        ]
        
        map_ = CompiledInterceptionMap(rules=rules)
        
        match = map_.should_intercept("/photos/123", referrer="/gallery")
        
        assert match is not None
        assert match.is_intercepted
        assert match.target_params.get("id") == "123"
    
    def test_no_intercept_on_direct_navigation(self):
        """Should not intercept on direct navigation (no referrer)."""
        rules = [
            InterceptionRule(
                source_pattern="",
                target_pattern="/photos/:id",
                interception_type=InterceptionType.SOFT,
                interceptor_path="",
                original_path="/photos",
            ),
        ]
        
        map_ = CompiledInterceptionMap(rules=rules)
        
        match = map_.should_intercept("/photos/123", referrer=None)
        
        # Soft interception requires referrer
        assert match is None


class TestInterceptionScanner:
    """Tests for interception scanner."""
    
    def test_scanner_creation(self):
        """Should create scanner."""
        scanner = InterceptionScanner()
        
        assert scanner._rules == []
    
    def test_scanner_singleton(self):
        """get_interception_scanner should return singleton."""
        scanner1 = get_interception_scanner()
        scanner2 = get_interception_scanner()
        
        assert scanner1 is scanner2


class TestModalComponent:
    """Tests for Modal component."""
    
    def test_modal_renders_dialog(self):
        """Modal should render native dialog element."""
        m = Modal(on_close="/")[
            p()["Modal content"]
        ]
        
        html = m.render()
        
        assert "<dialog" in html
        assert "Modal content" in html
        assert 'data-modal' in html
    
    def test_modal_close_url(self):
        """Modal should have close URL."""
        m = Modal(on_close="/gallery")[
            div()["Content"]
        ]
        
        html = m.render()
        
        assert 'data-close-url="/gallery"' in html
    
    def test_modal_animation(self):
        """Modal should support animation types."""
        m = Modal(animation="scale")[
            div()["Content"]
        ]
        
        html = m.render()
        
        assert 'data-animation="scale"' in html
    
    def test_modal_close_button(self):
        """Modal should have close button by default."""
        m = Modal()[
            div()["Content"]
        ]
        
        html = m.render()
        
        assert "modal-close" in html
        assert "data-close-modal" in html
    
    def test_modal_no_close_button(self):
        """Modal should optionally hide close button."""
        m = Modal(show_close_button=False)[
            div()["Content"]
        ]
        
        html = m.render()
        
        assert "modal-close" not in html


class TestModalHelpers:
    """Tests for modal helper functions."""
    
    def test_modal_helper(self):
        """modal() should create Modal."""
        m = modal(on_close="/")
        
        assert isinstance(m, Modal)
    
    def test_photo_modal(self):
        """photo_modal should have photo optimizations."""
        m = photo_modal(on_close="/")
        
        assert "photo-modal" in m.overlay_class
    
    def test_form_modal(self):
        """form_modal should prevent accidental close."""
        m = form_modal(on_close="/")
        
        assert m.close_on_overlay is False


class TestModalContext:
    """Tests for modal context."""
    
    def test_create_context(self):
        """Should create modal context."""
        ctx = create_modal_context()
        
        assert ctx.is_modal_open is False
    
    def test_context_state(self):
        """Context should track modal state."""
        ctx = ModalContext(
            is_modal_open=True,
            current_path="/photos/123",
        )
        
        assert ctx.is_modal_open
        assert ctx.current_path == "/photos/123"


class TestModalPortal:
    """Tests for ModalPortal."""
    
    def test_portal_renders_container(self):
        """ModalPortal should render container."""
        portal = ModalPortal()
        html = portal.render()
        
        assert 'id="modal-portal"' in html
        assert 'class="modal-portal"' in html


class TestModalRuntime:
    """Tests for modal JavaScript runtime."""
    
    def test_runtime_content(self):
        """Modal runtime should have essential functions."""
        js = get_modal_runtime_js()
        
        assert "__pynext__.modal" in js
        assert "init" in js
        assert "close" in js
        assert "trapFocus" in js
    
    def test_css_content(self):
        """Modal CSS should have essential styles."""
        css = get_modal_css()
        
        assert ".pynext-modal" in css
        assert ".modal-backdrop" in css
        assert ".modal-content" in css


class TestURLDrivenState:
    """Tests for URL-driven modal state."""
    
    def test_modal_state_from_url(self):
        """Modal state should be derived from URL."""
        # Create rule
        rule = InterceptionRule(
            source_pattern="",
            target_pattern="/photos/:id",
            interception_type=InterceptionType.HARD,
            interceptor_path="",
            original_path="/photos",
        )
        
        map_ = CompiledInterceptionMap(rules=[rule])
        
        # Should intercept based on URL alone
        match = map_.should_intercept("/photos/456", referrer="/")
        
        # Modal content ID comes from URL
        assert match is not None
        assert match.target_params["id"] == "456"

