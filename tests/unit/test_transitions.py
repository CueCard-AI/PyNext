"""
Unit tests for PyNext Transitions & Navigation.

Tests cover:
- TransitionType enum
- TransitionConfig dataclass
- transition decorator
- Link component
- Navigation scripts
- Transition CSS
"""

import pytest
from pynext.core.transitions import (
    TransitionType,
    TransitionConfig,
    TransitionManager,
    NavigationState,
    NavigationEvent,
    PageTransition,
    transition,
    Link,
    navigate_script,
    back_script,
    forward_script,
    get_transition_manager,
    get_transition_css,
    get_transition_style_tag,
    generate_navigation_data,
    get_navigation_script,
)
from pynext.core.html import div, img, h2


# =============================================================================
# TransitionType Tests
# =============================================================================

class TestTransitionType:
    """Tests for TransitionType enum."""
    
    def test_all_types_defined(self):
        """All transition types are defined."""
        assert TransitionType.NONE.value == "none"
        assert TransitionType.FADE.value == "fade"
        assert TransitionType.SLIDE_LEFT.value == "slide-left"
        assert TransitionType.SLIDE_RIGHT.value == "slide-right"
        assert TransitionType.SLIDE_UP.value == "slide-up"
        assert TransitionType.SLIDE_DOWN.value == "slide-down"
        assert TransitionType.SCALE.value == "scale"
        assert TransitionType.MORPH.value == "morph"
    
    def test_type_count(self):
        """Correct number of transition types."""
        assert len(TransitionType) == 8


# =============================================================================
# TransitionConfig Tests
# =============================================================================

class TestTransitionConfig:
    """Tests for TransitionConfig dataclass."""
    
    def test_default_config(self):
        """Default config values."""
        config = TransitionConfig()
        
        assert config.type == TransitionType.FADE
        assert config.duration == 300
        assert config.easing == "ease-in-out"
        assert config.delay == 0
        assert config.use_view_transitions is True
    
    def test_custom_config(self):
        """Custom config values."""
        config = TransitionConfig(
            type=TransitionType.SLIDE_LEFT,
            duration=500,
            easing="linear",
            delay=100,
            custom_css="opacity: 0.5;"
        )
        
        assert config.type == TransitionType.SLIDE_LEFT
        assert config.duration == 500
        assert config.easing == "linear"
        assert config.delay == 100
        assert config.custom_css == "opacity: 0.5;"
    
    def test_string_type(self):
        """Config with string type."""
        config = TransitionConfig(type="custom-animation")
        
        assert config.type == "custom-animation"


# =============================================================================
# TransitionManager Tests
# =============================================================================

class TestTransitionManager:
    """Tests for TransitionManager class."""
    
    def test_manager_creation(self):
        """Create transition manager."""
        manager = TransitionManager()
        
        assert manager._active_navigation is None
        assert "before" in manager._transition_hooks
    
    def test_register_transition(self):
        """Register custom transition."""
        manager = TransitionManager()
        config = TransitionConfig(
            type="custom",
            duration=400
        )
        
        manager.register_transition("my-transition", config)
        
        assert "my-transition" in manager._custom_transitions
    
    def test_get_transition_custom(self):
        """Get registered custom transition."""
        manager = TransitionManager()
        config = TransitionConfig(type="custom", duration=400)
        manager.register_transition("my-transition", config)
        
        result = manager.get_transition("my-transition")
        
        assert result.duration == 400
    
    def test_get_transition_builtin(self):
        """Get built-in transition."""
        manager = TransitionManager()
        
        result = manager.get_transition("fade")
        
        assert result.type == TransitionType.FADE
    
    def test_get_transition_unknown(self):
        """Unknown transition falls back to fade."""
        manager = TransitionManager()
        
        result = manager.get_transition("unknown-type")
        
        assert result.type == TransitionType.FADE
    
    def test_on_before_hook(self):
        """Register before hook."""
        manager = TransitionManager()
        called = []
        
        @manager.on_before
        def my_hook():
            called.append("before")
        
        assert my_hook in manager._transition_hooks["before"]
    
    def test_on_after_hook(self):
        """Register after hook."""
        manager = TransitionManager()
        called = []
        
        @manager.on_after
        def my_hook():
            called.append("after")
        
        assert my_hook in manager._transition_hooks["after"]
    
    def test_global_manager(self):
        """Get global transition manager."""
        manager = get_transition_manager()
        
        assert isinstance(manager, TransitionManager)


# =============================================================================
# NavigationState Tests
# =============================================================================

class TestNavigationState:
    """Tests for NavigationState dataclass."""
    
    def test_state_creation(self):
        """Create navigation state."""
        state = NavigationState(
            id="nav-123",
            from_url="/home",
            to_url="/about",
            transition=TransitionConfig()
        )
        
        assert state.id == "nav-123"
        assert state.from_url == "/home"
        assert state.to_url == "/about"
        assert state.state == "pending"
    
    def test_state_with_error(self):
        """Navigation state with error."""
        state = NavigationState(
            id="nav-456",
            from_url="/",
            to_url="/error",
            transition=TransitionConfig(),
            state="error",
            error="Network error"
        )
        
        assert state.state == "error"
        assert state.error == "Network error"


# =============================================================================
# Transition Decorator Tests
# =============================================================================

class TestTransitionDecorator:
    """Tests for @transition decorator."""
    
    def test_transition_decorator(self):
        """Apply transition decorator."""
        @transition("hero-image")
        def ProductImage():
            return img(src="/product.jpg")
        
        assert hasattr(ProductImage, '_transition_name')
        assert ProductImage._transition_name == "hero-image"
    
    def test_transition_with_duration(self):
        """Transition with custom duration."""
        @transition("card", duration=500)
        def Card():
            return div()["Card"]
        
        assert Card._transition_duration == 500
    
    def test_transition_with_easing(self):
        """Transition with custom easing."""
        @transition("modal", easing="ease-out")
        def Modal():
            return div()["Modal"]
        
        assert Modal._transition_easing == "ease-out"
    
    def test_transition_auto_name(self):
        """Transition with auto-generated name."""
        @transition()
        def MyComponent():
            return div()["Content"]
        
        assert MyComponent._transition_name == "MyComponent"


# =============================================================================
# Link Component Tests
# =============================================================================

class TestLinkComponent:
    """Tests for Link component."""
    
    def test_basic_link(self):
        """Create basic link."""
        link = Link(href="/about")
        html = link.render()
        
        assert 'href="/about"' in html
        assert 'data-pynext-link="true"' in html
    
    def test_link_with_transition(self):
        """Link with transition type."""
        link = Link(href="/dashboard", transition=TransitionType.SLIDE_LEFT)
        html = link.render()
        
        assert 'data-transition="slide-left"' in html
    
    def test_link_with_string_transition(self):
        """Link with string transition."""
        link = Link(href="/settings", transition="custom-fade")
        html = link.render()
        
        assert 'data-transition="custom-fade"' in html
    
    def test_link_with_prefetch(self):
        """Link with prefetch enabled."""
        link = Link(href="/products", prefetch=True)
        html = link.render()
        
        assert 'data-prefetch="hover"' in html
    
    def test_link_without_prefetch(self):
        """Link without prefetch."""
        link = Link(href="/admin", prefetch=False)
        html = link.render()
        
        assert 'data-prefetch' not in html
    
    def test_link_with_replace(self):
        """Link with history replace."""
        link = Link(href="/step2", replace=True)
        html = link.render()
        
        assert 'data-replace="true"' in html
    
    def test_link_with_content(self):
        """Link with content."""
        link = Link(href="/home")["Go Home"]
        html = link.render()
        
        assert "Go Home" in html


# =============================================================================
# Navigation Scripts Tests
# =============================================================================

class TestNavigationScripts:
    """Tests for navigation script generation."""
    
    def test_navigate_script(self):
        """Generate navigate script."""
        script = navigate_script("/dashboard")
        
        assert '__pynext__.navigate' in script
        assert '"/dashboard"' in script
        assert 'transition:' in script
    
    def test_navigate_with_transition(self):
        """Navigate script with transition."""
        script = navigate_script("/page", transition=TransitionType.SLIDE_LEFT)
        
        assert '"slide-left"' in script
    
    def test_navigate_with_replace(self):
        """Navigate script with replace."""
        script = navigate_script("/page", replace=True)
        
        assert 'replace: true' in script
    
    def test_back_script(self):
        """Generate back script."""
        script = back_script()
        
        assert '__pynext__.back' in script
        assert '"slide-right"' in script
    
    def test_forward_script(self):
        """Generate forward script."""
        script = forward_script()
        
        assert '__pynext__.forward' in script
        assert '"slide-left"' in script


# =============================================================================
# Transition CSS Tests
# =============================================================================

class TestTransitionCSS:
    """Tests for transition CSS generation."""
    
    def test_get_transition_css(self):
        """Get transition CSS."""
        css = get_transition_css()
        
        assert "@view-transition" in css
        assert "pynext-fade-in" in css
        assert "pynext-fade-out" in css
    
    def test_css_contains_all_transitions(self):
        """CSS contains all transition types."""
        css = get_transition_css()
        
        assert "slide-left" in css
        assert "slide-right" in css
        assert "slide-up" in css
        assert "slide-down" in css
        assert "scale" in css
    
    def test_css_contains_loading(self):
        """CSS contains loading indicator."""
        css = get_transition_css()
        
        assert "pynext-nav-loading" in css
        assert "pynext-loading" in css
    
    def test_get_transition_style_tag(self):
        """Get style tag with CSS."""
        tag = get_transition_style_tag()
        
        assert tag.startswith("<style>")
        assert tag.endswith("</style>")
        assert "@view-transition" in tag


# =============================================================================
# PageTransition Tests
# =============================================================================

class TestPageTransition:
    """Tests for PageTransition wrapper."""
    
    def test_page_transition_render(self):
        """Render page with transition."""
        content = div()["Page content"]
        page = PageTransition(content=content, name="main-page")
        
        html = page.render()
        
        assert 'data-page-transition="main-page"' in html
        assert 'view-transition-name: main-page' in html
        assert "Page content" in html
    
    def test_page_transition_default_name(self):
        """Default transition name."""
        page = PageTransition(content=div()["Test"])
        
        html = page.render()
        
        assert 'data-page-transition="root"' in html


# =============================================================================
# NavigationEvent Tests
# =============================================================================

class TestNavigationEvent:
    """Tests for NavigationEvent dataclass."""
    
    def test_event_creation(self):
        """Create navigation event."""
        event = NavigationEvent(
            type="start",
            from_url="/home",
            to_url="/about",
            transition="fade"
        )
        
        assert event.type == "start"
        assert event.from_url == "/home"
        assert event.to_url == "/about"
    
    def test_event_with_error(self):
        """Event with error."""
        event = NavigationEvent(
            type="error",
            from_url="/",
            to_url="/broken",
            transition="fade",
            error="404 Not Found"
        )
        
        assert event.error == "404 Not Found"


# =============================================================================
# Navigation Data Tests
# =============================================================================

class TestNavigationData:
    """Tests for navigation data generation."""
    
    def test_generate_navigation_data(self):
        """Generate navigation JSON data."""
        data = generate_navigation_data(
            routes=["/", "/about", "/contact"],
            current_route="/about",
            prefetch_routes=["/contact"]
        )
        
        import json
        parsed = json.loads(data)
        
        assert parsed["current"] == "/about"
        assert "/" in parsed["routes"]
        assert "/contact" in parsed["prefetch"]
    
    def test_get_navigation_script(self):
        """Generate navigation script tag."""
        script = get_navigation_script(
            routes=["/", "/home"],
            current_route="/home"
        )
        
        assert "<script>" in script
        assert "__PYNEXT_NAV__" in script
        assert '"/home"' in script

