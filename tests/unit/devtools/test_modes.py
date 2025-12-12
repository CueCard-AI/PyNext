"""
Tests for debug mode functionality.

These tests cover:
- DebugMode enum
- Mode-specific configuration
- Mode parsing
"""

import pytest
from pynext.devtools.debugger import DebugMode, DebugConfig


class TestDebugMode:
    """Test DebugMode enum."""
    
    def test_mode_values(self):
        """DebugMode has expected values."""
        assert DebugMode.APP.value == "app"
        assert DebugMode.CORE.value == "core"
        assert DebugMode.EVERYTHING.value == "everything"
    
    def test_from_string_app(self):
        """Parses 'app' string correctly."""
        mode = DebugMode.from_string("app")
        assert mode == DebugMode.APP
    
    def test_from_string_core(self):
        """Parses 'core' string correctly."""
        mode = DebugMode.from_string("core")
        assert mode == DebugMode.CORE
    
    def test_from_string_everything(self):
        """Parses 'everything' string correctly."""
        mode = DebugMode.from_string("everything")
        assert mode == DebugMode.EVERYTHING
    
    def test_from_string_case_insensitive(self):
        """Mode parsing is case-insensitive."""
        assert DebugMode.from_string("APP") == DebugMode.APP
        assert DebugMode.from_string("Core") == DebugMode.CORE
        assert DebugMode.from_string("EVERYTHING") == DebugMode.EVERYTHING
    
    def test_from_string_with_whitespace(self):
        """Mode parsing trims whitespace."""
        assert DebugMode.from_string("  app  ") == DebugMode.APP
    
    def test_from_string_invalid_defaults_to_app(self):
        """Invalid mode defaults to APP."""
        assert DebugMode.from_string("invalid") == DebugMode.APP
        assert DebugMode.from_string("") == DebugMode.APP
        assert DebugMode.from_string(None) == DebugMode.APP


class TestModeCapture:
    """Test mode-specific capture flags."""
    
    def test_app_mode_captures_app_context(self):
        """APP mode captures app context."""
        assert DebugMode.APP.capture_app_context is True
    
    def test_app_mode_not_captures_framework(self):
        """APP mode doesn't capture framework internals."""
        assert DebugMode.APP.capture_framework_internals is False
    
    def test_core_mode_captures_framework(self):
        """CORE mode captures framework internals."""
        assert DebugMode.CORE.capture_framework_internals is True
    
    def test_core_mode_not_captures_app(self):
        """CORE mode doesn't capture app context."""
        assert DebugMode.CORE.capture_app_context is False
    
    def test_everything_mode_captures_all(self):
        """EVERYTHING mode captures everything."""
        mode = DebugMode.EVERYTHING
        assert mode.capture_app_context is True
        assert mode.capture_framework_internals is True
        assert mode.capture_browser_internals is True
    
    def test_browser_internals_only_everything(self):
        """Only EVERYTHING captures browser internals."""
        assert DebugMode.APP.capture_browser_internals is False
        assert DebugMode.CORE.capture_browser_internals is False
        assert DebugMode.EVERYTHING.capture_browser_internals is True


class TestDebugConfig:
    """Test DebugConfig with modes."""
    
    def test_default_mode_is_app(self):
        """Default mode is APP."""
        config = DebugConfig()
        assert config.mode == DebugMode.APP
    
    def test_config_with_mode_enum(self):
        """Config accepts DebugMode enum."""
        config = DebugConfig(mode=DebugMode.CORE)
        assert config.mode == DebugMode.CORE
    
    def test_config_with_mode_string(self):
        """Config accepts mode as string."""
        config = DebugConfig(mode="everything")
        assert config.mode == DebugMode.EVERYTHING
    
    def test_get_mode_description_app(self):
        """Mode description for APP."""
        config = DebugConfig(mode=DebugMode.APP)
        desc = config.get_mode_description()
        assert "App" in desc
        assert "application" in desc.lower()
    
    def test_get_mode_description_core(self):
        """Mode description for CORE."""
        config = DebugConfig(mode=DebugMode.CORE)
        desc = config.get_mode_description()
        assert "Core" in desc
        assert "framework" in desc.lower()
    
    def test_get_mode_description_everything(self):
        """Mode description for EVERYTHING."""
        config = DebugConfig(mode=DebugMode.EVERYTHING)
        desc = config.get_mode_description()
        assert "Everything" in desc
        assert "diagnostic" in desc.lower()
    
    def test_sessions_dir(self):
        """Sessions directory is derived from output_dir."""
        from pathlib import Path
        config = DebugConfig(output_dir=Path("/tmp/debug"))
        assert config.sessions_dir == Path("/tmp/debug/sessions")
    
    def test_api_key_config(self):
        """API key can be configured."""
        config = DebugConfig(api_key="sk-test")
        assert config.api_key == "sk-test"
    
    def test_enable_ai_analysis_default(self):
        """AI analysis is enabled by default."""
        config = DebugConfig()
        assert config.enable_ai_analysis is True
    
    def test_screenshot_interval_default(self):
        """Screenshot interval has sensible default."""
        config = DebugConfig()
        assert config.screenshot_interval_ms == 150


class TestSourceTracking:
    """Test source location tracking in Element."""
    
    def test_source_tracking_disabled_by_default(self):
        """Source tracking is disabled by default."""
        from pynext.core.html import Element
        assert Element._track_source is False
    
    def test_enable_source_tracking(self):
        """Source tracking can be enabled."""
        from pynext.core.html import Element
        
        original = Element._track_source
        try:
            Element.enable_source_tracking(True)
            assert Element._track_source is True
            
            Element.enable_source_tracking(False)
            assert Element._track_source is False
        finally:
            Element._track_source = original
    
    def test_element_source_attribute(self):
        """Elements can have source attribute."""
        from pynext.core.html import Element
        
        # Create element with explicit source (passed to __init__, not attrs)
        el = Element("div", _source="test.py:42")
        assert el._source == "test.py:42"
    
    def test_source_propagates_through_call(self):
        """Source propagates through __call__."""
        from pynext.core.html import Element
        
        el1 = Element("div", _source="test.py:10")
        el2 = el1(id="test")
        
        assert el2._source == "test.py:10"
    
    def test_source_propagates_through_getitem(self):
        """Source propagates through __getitem__."""
        from pynext.core.html import Element
        
        el1 = Element("div", _source="test.py:20")
        el2 = el1["child text"]
        
        assert el2._source == "test.py:20"
    
    def test_source_in_rendered_html(self):
        """Source appears in rendered HTML when tracking enabled."""
        from pynext.core.html import Element
        
        original = Element._track_source
        try:
            Element._track_source = True
            
            el = Element("div", _source="forms.py:100")
            html = el.render()
            
            assert 'data-pynext-source="forms.py:100"' in html
        finally:
            Element._track_source = original
    
    def test_source_not_in_html_when_disabled(self):
        """Source not in HTML when tracking disabled."""
        from pynext.core.html import Element
        
        original = Element._track_source
        try:
            Element._track_source = False
            
            el = Element("div", _source="forms.py:100")
            html = el.render()
            
            assert "data-pynext-source" not in html
        finally:
            Element._track_source = original

