"""
Comprehensive tests for Template functionality.

Tests:
- @template decorator basic usage
- Template configuration options
- Template rendering
- Transition types
- CSS generation
- Hydration data
- Convenience decorators
"""

import pytest
from pynext.core.template import (
    template,
    Template,
    TemplateConfig,
    TransitionType,
    fade_template,
    slide_template,
    scale_template,
    static_template,
)


# =============================================================================
# @template Decorator Tests
# =============================================================================

class TestTemplateDecorator:
    """Tests for @template decorator."""
    
    def test_basic_decorator(self):
        """Basic decorator without options."""
        @template
        def my_template(children):
            return f"<div>{children}</div>"
        
        assert isinstance(my_template, Template)
        assert my_template.config.name == "my_template"
        assert my_template.config.animate is True
        assert my_template.config.duration == 200
    
    def test_decorator_with_options(self):
        """Decorator with custom options."""
        @template(animate=False, duration=500, reset_scroll=False)
        def custom_template(children):
            return f"<div>{children}</div>"
        
        assert custom_template.config.animate is False
        assert custom_template.config.duration == 500
        assert custom_template.config.reset_scroll is False
    
    def test_decorator_with_transition_enum(self):
        """Decorator with TransitionType enum."""
        @template(transition=TransitionType.SLIDE_LEFT)
        def slide_left_template(children):
            return f"<div>{children}</div>"
        
        assert slide_left_template.config.transition == TransitionType.SLIDE_LEFT
    
    def test_decorator_with_transition_string(self):
        """Decorator with transition as string."""
        @template(transition="slide-right")
        def slide_right_template(children):
            return f"<div>{children}</div>"
        
        assert slide_right_template.config.transition == TransitionType.SLIDE_RIGHT
    
    def test_decorator_invalid_transition_string(self):
        """Invalid transition string defaults to FADE."""
        @template(transition="invalid-type")
        def invalid_template(children):
            return f"<div>{children}</div>"
        
        assert invalid_template.config.transition == TransitionType.FADE
    
    def test_decorator_custom_easing(self):
        """Custom easing function."""
        @template(easing="cubic-bezier(0.4, 0, 0.2, 1)")
        def easing_template(children):
            return f"<div>{children}</div>"
        
        assert "cubic-bezier" in easing_template.config.easing
    
    def test_preserves_function_name(self):
        """Preserves original function name."""
        @template
        def named_template(children):
            """Template docstring."""
            return f"<div>{children}</div>"
        
        assert named_template.__name__ == "named_template"
        assert named_template.__doc__ == "Template docstring."


# =============================================================================
# TemplateConfig Tests
# =============================================================================

class TestTemplateConfig:
    """Tests for TemplateConfig dataclass."""
    
    def test_default_values(self):
        """Default values are correct."""
        config = TemplateConfig(name="test")
        
        assert config.name == "test"
        assert config.animate is True
        assert config.duration == 200
        assert config.reset_scroll is True
        assert config.transition == TransitionType.FADE
        assert config.easing == "ease-out"
    
    def test_all_transition_types(self):
        """All transition types are valid."""
        for trans_type in TransitionType:
            config = TemplateConfig(name="test", transition=trans_type)
            assert config.transition == trans_type


# =============================================================================
# Template Rendering Tests
# =============================================================================

class TestTemplateRendering:
    """Tests for Template.render() method."""
    
    def test_render_with_children(self):
        """Renders with children content."""
        @template
        def wrapper(children):
            return f"<main>{children}</main>"
        
        html = wrapper.render("Hello World")
        
        assert "Hello World" in html
        assert "<main>" in html
        assert 'data-pynext-template="wrapper"' in html
    
    def test_render_includes_data_attributes(self):
        """Rendered HTML includes all data attributes."""
        @template(animate=True, duration=300, reset_scroll=False)
        def attr_template(children):
            return f"<div>{children}</div>"
        
        html = attr_template.render("content")
        
        assert 'data-pynext-template="attr_template"' in html
        assert 'data-animate="true"' in html
        assert 'data-duration="300"' in html
        assert 'data-reset-scroll="false"' in html
        assert 'data-transition="fade"' in html
        assert 'data-easing="ease-out"' in html
    
    def test_render_with_none_children(self):
        """Handles None children."""
        @template
        def none_template(children):
            return f"<div>{children or 'default'}</div>"
        
        html = none_template.render(None)
        assert "default" in html or "<div>None</div>" in html or "<div></div>" in html
    
    def test_render_callable_as_function(self):
        """Template can be called as function."""
        @template
        def callable_template(children):
            return f"<div>{children}</div>"
        
        # Call directly
        html = callable_template("test")
        assert "test" in html
    
    def test_render_component_with_render_method(self):
        """Handles components with .render() method."""
        class MockComponent:
            def render(self):
                return "<span>Component</span>"
        
        @template
        def component_template(children):
            return children
        
        # When children is a component with render()
        mock = MockComponent()
        html = component_template.render(mock)
        assert "Component" in html


# =============================================================================
# Transition CSS Generation Tests
# =============================================================================

class TestTransitionCSS:
    """Tests for Template.get_css() method."""
    
    def test_css_fade_transition(self):
        """Generates CSS for fade transition."""
        @template(transition=TransitionType.FADE)
        def fade(children):
            return children
        
        css = fade.get_css()
        
        assert "template-exit" in css
        assert "template-enter" in css
        assert "template-enter-active" in css
        assert "opacity" in css
    
    def test_css_slide_left_transition(self):
        """Generates CSS for slide-left transition."""
        @template(transition=TransitionType.SLIDE_LEFT)
        def slide(children):
            return children
        
        css = slide.get_css()
        
        assert "translateX" in css
    
    def test_css_slide_right_transition(self):
        """Generates CSS for slide-right transition."""
        @template(transition=TransitionType.SLIDE_RIGHT)
        def slide(children):
            return children
        
        css = slide.get_css()
        assert "translateX" in css
    
    def test_css_slide_up_transition(self):
        """Generates CSS for slide-up transition."""
        @template(transition=TransitionType.SLIDE_UP)
        def slide(children):
            return children
        
        css = slide.get_css()
        assert "translateY" in css
    
    def test_css_slide_down_transition(self):
        """Generates CSS for slide-down transition."""
        @template(transition=TransitionType.SLIDE_DOWN)
        def slide(children):
            return children
        
        css = slide.get_css()
        assert "translateY" in css
    
    def test_css_scale_transition(self):
        """Generates CSS for scale transition."""
        @template(transition=TransitionType.SCALE)
        def scale(children):
            return children
        
        css = scale.get_css()
        assert "scale" in css
    
    def test_css_none_transition(self):
        """No CSS for none transition."""
        @template(transition=TransitionType.NONE)
        def no_transition(children):
            return children
        
        css = no_transition.get_css()
        assert css == ""
    
    def test_css_no_animation(self):
        """No CSS when animate=False."""
        @template(animate=False)
        def no_animate(children):
            return children
        
        css = no_animate.get_css()
        assert css == ""
    
    def test_css_includes_duration(self):
        """CSS includes custom duration."""
        @template(duration=500)
        def custom_duration(children):
            return children
        
        css = custom_duration.get_css()
        assert "500ms" in css
    
    def test_css_includes_easing(self):
        """CSS includes custom easing."""
        @template(easing="ease-in-out")
        def custom_easing(children):
            return children
        
        css = custom_easing.get_css()
        assert "ease-in-out" in css


# =============================================================================
# Hydration Data Tests
# =============================================================================

class TestHydrationData:
    """Tests for Template.get_hydration_data() method."""
    
    def test_hydration_data_basic(self):
        """Returns correct hydration data."""
        @template
        def basic(children):
            return children
        
        data = basic.get_hydration_data()
        
        assert data["name"] == "basic"
        assert data["animate"] is True
        assert data["duration"] == 200
        assert data["resetScroll"] is True
        assert data["transition"] == "fade"
        assert data["easing"] == "ease-out"
    
    def test_hydration_data_custom(self):
        """Returns correct custom hydration data."""
        @template(
            animate=False,
            duration=1000,
            reset_scroll=False,
            transition=TransitionType.SCALE,
            easing="linear",
        )
        def custom(children):
            return children
        
        data = custom.get_hydration_data()
        
        assert data["animate"] is False
        assert data["duration"] == 1000
        assert data["resetScroll"] is False
        assert data["transition"] == "scale"
        assert data["easing"] == "linear"


# =============================================================================
# Convenience Decorator Tests
# =============================================================================

class TestConvenienceDecorators:
    """Tests for convenience decorator functions."""
    
    def test_fade_template_decorator(self):
        """fade_template() creates fade transition."""
        @fade_template()
        def my_fade(children):
            return children
        
        assert my_fade.config.transition == TransitionType.FADE
    
    def test_fade_template_custom_duration(self):
        """fade_template() accepts custom duration."""
        @fade_template(duration=500)
        def my_fade(children):
            return children
        
        assert my_fade.config.duration == 500
    
    def test_slide_template_left(self):
        """slide_template() defaults to left."""
        @slide_template()
        def my_slide(children):
            return children
        
        assert my_slide.config.transition == TransitionType.SLIDE_LEFT
    
    def test_slide_template_directions(self):
        """slide_template() accepts all directions."""
        for direction in ["left", "right", "up", "down"]:
            @slide_template(direction=direction)
            def my_slide(children):
                return children
            
            expected = getattr(TransitionType, f"SLIDE_{direction.upper()}")
            assert my_slide.config.transition == expected
    
    def test_scale_template_decorator(self):
        """scale_template() creates scale transition."""
        @scale_template()
        def my_scale(children):
            return children
        
        assert my_scale.config.transition == TransitionType.SCALE
    
    def test_static_template_decorator(self):
        """static_template() creates no-animation template."""
        @static_template()
        def my_static(children):
            return children
        
        assert my_static.config.animate is False


# =============================================================================
# TransitionType Enum Tests
# =============================================================================

class TestTransitionType:
    """Tests for TransitionType enum."""
    
    def test_all_types_have_string_values(self):
        """All transition types have kebab-case string values."""
        expected = {
            TransitionType.FADE: "fade",
            TransitionType.SLIDE_LEFT: "slide-left",
            TransitionType.SLIDE_RIGHT: "slide-right",
            TransitionType.SLIDE_UP: "slide-up",
            TransitionType.SLIDE_DOWN: "slide-down",
            TransitionType.SCALE: "scale",
            TransitionType.NONE: "none",
        }
        
        for trans_type, value in expected.items():
            assert trans_type.value == value
    
    def test_types_can_be_created_from_string(self):
        """Can create enum from string value."""
        assert TransitionType("fade") == TransitionType.FADE
        assert TransitionType("slide-left") == TransitionType.SLIDE_LEFT


# =============================================================================
# Edge Cases
# =============================================================================

class TestTemplateEdgeCases:
    """Tests for edge cases."""
    
    def test_template_with_no_children_param(self):
        """Template function can omit children."""
        @template
        def no_children():
            return "<div>Static</div>"
        
        html = no_children.render()
        assert "Static" in html
    
    def test_template_with_positional_children(self):
        """Template function can use positional children."""
        @template
        def positional(content):
            return f"<div>{content}</div>"
        
        html = positional.render("test")
        assert "test" in html
    
    def test_very_long_duration(self):
        """Handles very long duration values."""
        @template(duration=60000)  # 1 minute
        def long_duration(children):
            return children
        
        assert long_duration.config.duration == 60000
    
    def test_zero_duration(self):
        """Handles zero duration (instant transition)."""
        @template(duration=0)
        def instant(children):
            return children
        
        assert instant.config.duration == 0

