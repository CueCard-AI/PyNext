"""
Tests for PyNext event modifiers.

Tests cover:
- EventHandler wrapper class
- stop(), prevent(), self_only(), once(), capture() functions
- Modifier composition
- HTML serialization with modifiers
- Context registration with modifiers
"""

import pytest
from unittest.mock import MagicMock, patch

from pynext.events import (
    EventHandler,
    stop,
    prevent,
    self_only,
    once,
    capture,
    stop_propagation,
    prevent_default,
)


# ==============================================================================
# EventHandler Class Tests
# ==============================================================================

class TestEventHandler:
    """Tests for the EventHandler dataclass."""
    
    def test_create_with_function(self):
        """EventHandler wraps a function."""
        fn = lambda: None
        handler = EventHandler(fn=fn)
        assert handler.fn is fn
        assert handler.stop is False
        assert handler.prevent is False
        assert handler.self_only is False
        assert handler.once is False
        assert handler.capture is False
    
    def test_create_with_modifiers(self):
        """EventHandler accepts all modifier flags."""
        fn = lambda: None
        handler = EventHandler(
            fn=fn,
            stop=True,
            prevent=True,
            self_only=True,
            once=True,
            capture=True,
        )
        assert handler.stop is True
        assert handler.prevent is True
        assert handler.self_only is True
        assert handler.once is True
        assert handler.capture is True
    
    def test_callable(self):
        """EventHandler is callable and delegates to fn."""
        result = []
        fn = lambda x: result.append(x)
        handler = EventHandler(fn=fn)
        handler("test")
        assert result == ["test"]
    
    def test_with_modifiers(self):
        """with_modifiers returns new EventHandler with updated flags."""
        fn = lambda: None
        handler = EventHandler(fn=fn)
        new_handler = handler.with_modifiers(stop=True, prevent=True)
        
        # Original unchanged
        assert handler.stop is False
        assert handler.prevent is False
        
        # New has updates
        assert new_handler.stop is True
        assert new_handler.prevent is True
        assert new_handler.fn is fn
    
    def test_get_modifiers_empty(self):
        """get_modifiers returns empty dict when no modifiers set."""
        handler = EventHandler(fn=lambda: None)
        assert handler.get_modifiers() == {}
    
    def test_get_modifiers_with_flags(self):
        """get_modifiers returns dict of active modifiers."""
        handler = EventHandler(
            fn=lambda: None,
            stop=True,
            self_only=True,
        )
        mods = handler.get_modifiers()
        assert mods == {"stop": True, "self_only": True}
    
    def test_get_modifiers_all(self):
        """get_modifiers includes all active flags."""
        handler = EventHandler(
            fn=lambda: None,
            stop=True,
            prevent=True,
            self_only=True,
            once=True,
            capture=True,
        )
        mods = handler.get_modifiers()
        assert mods == {
            "stop": True,
            "prevent": True,
            "self_only": True,
            "once": True,
            "capture": True,
        }


# ==============================================================================
# Modifier Function Tests
# ==============================================================================

class TestStopModifier:
    """Tests for stop() modifier."""
    
    def test_wraps_function(self):
        """stop() wraps plain function in EventHandler."""
        fn = lambda: None
        handler = stop(fn)
        assert isinstance(handler, EventHandler)
        assert handler.fn is fn
        assert handler.stop is True
    
    def test_updates_existing_handler(self):
        """stop() updates existing EventHandler."""
        fn = lambda: None
        existing = EventHandler(fn=fn, prevent=True)
        handler = stop(existing)
        assert handler.stop is True
        assert handler.prevent is True  # Preserved
        assert handler.fn is fn
    
    def test_alias_stop_propagation(self):
        """stop_propagation is alias for stop."""
        fn = lambda: None
        handler = stop_propagation(fn)
        assert handler.stop is True


class TestPreventModifier:
    """Tests for prevent() modifier."""
    
    def test_wraps_function(self):
        """prevent() wraps plain function in EventHandler."""
        fn = lambda: None
        handler = prevent(fn)
        assert isinstance(handler, EventHandler)
        assert handler.fn is fn
        assert handler.prevent is True
    
    def test_updates_existing_handler(self):
        """prevent() updates existing EventHandler."""
        fn = lambda: None
        existing = EventHandler(fn=fn, stop=True)
        handler = prevent(existing)
        assert handler.prevent is True
        assert handler.stop is True  # Preserved
    
    def test_alias_prevent_default(self):
        """prevent_default is alias for prevent."""
        fn = lambda: None
        handler = prevent_default(fn)
        assert handler.prevent is True


class TestSelfOnlyModifier:
    """Tests for self_only() modifier."""
    
    def test_wraps_function(self):
        """self_only() wraps plain function in EventHandler."""
        fn = lambda: None
        handler = self_only(fn)
        assert isinstance(handler, EventHandler)
        assert handler.fn is fn
        assert handler.self_only is True
    
    def test_updates_existing_handler(self):
        """self_only() updates existing EventHandler."""
        fn = lambda: None
        existing = EventHandler(fn=fn, stop=True)
        handler = self_only(existing)
        assert handler.self_only is True
        assert handler.stop is True  # Preserved


class TestOnceModifier:
    """Tests for once() modifier."""
    
    def test_wraps_function(self):
        """once() wraps plain function in EventHandler."""
        fn = lambda: None
        handler = once(fn)
        assert isinstance(handler, EventHandler)
        assert handler.fn is fn
        assert handler.once is True
    
    def test_updates_existing_handler(self):
        """once() updates existing EventHandler."""
        fn = lambda: None
        existing = EventHandler(fn=fn, prevent=True)
        handler = once(existing)
        assert handler.once is True
        assert handler.prevent is True  # Preserved


class TestCaptureModifier:
    """Tests for capture() modifier."""
    
    def test_wraps_function(self):
        """capture() wraps plain function in EventHandler."""
        fn = lambda: None
        handler = capture(fn)
        assert isinstance(handler, EventHandler)
        assert handler.fn is fn
        assert handler.capture is True
    
    def test_updates_existing_handler(self):
        """capture() updates existing EventHandler."""
        fn = lambda: None
        existing = EventHandler(fn=fn, stop=True)
        handler = capture(existing)
        assert handler.capture is True
        assert handler.stop is True  # Preserved


# ==============================================================================
# Modifier Composition Tests
# ==============================================================================

class TestModifierComposition:
    """Tests for composing multiple modifiers."""
    
    def test_stop_prevent(self):
        """Compose stop and prevent."""
        fn = lambda: None
        handler = stop(prevent(fn))
        assert handler.stop is True
        assert handler.prevent is True
    
    def test_prevent_stop(self):
        """Order doesn't matter for composition."""
        fn = lambda: None
        handler = prevent(stop(fn))
        assert handler.stop is True
        assert handler.prevent is True
    
    def test_three_modifiers(self):
        """Compose three modifiers."""
        fn = lambda: None
        handler = stop(prevent(self_only(fn)))
        assert handler.stop is True
        assert handler.prevent is True
        assert handler.self_only is True
    
    def test_all_modifiers(self):
        """Compose all modifiers."""
        fn = lambda: None
        handler = capture(once(stop(prevent(self_only(fn)))))
        assert handler.stop is True
        assert handler.prevent is True
        assert handler.self_only is True
        assert handler.once is True
        assert handler.capture is True
    
    def test_composition_preserves_function(self):
        """Composed modifiers still reference original function."""
        original = lambda: "result"
        handler = stop(prevent(original))
        assert handler.fn is original
        assert handler() == "result"


# ==============================================================================
# HTML Serialization Tests
# ==============================================================================

class TestHTMLSerialization:
    """Tests for event handler serialization in HTML."""
    
    def test_unwrap_plain_function(self):
        """Plain function returns function and empty mods."""
        from pynext.core.html import _unwrap_event_handler
        
        fn = lambda: None
        func, mods = _unwrap_event_handler(fn)
        assert func is fn
        assert mods == {}
    
    def test_unwrap_event_handler(self):
        """EventHandler returns function and modifiers."""
        from pynext.core.html import _unwrap_event_handler
        
        fn = lambda: None
        handler = EventHandler(fn=fn, stop=True, prevent=True)
        func, mods = _unwrap_event_handler(handler)
        assert func is fn
        assert mods == {"stop": True, "prevent": True}
    
    def test_is_event_handler_false(self):
        """_is_event_handler returns False for plain function."""
        from pynext.core.html import _is_event_handler
        
        assert _is_event_handler(lambda: None) is False
        assert _is_event_handler("string") is False
        assert _is_event_handler(123) is False
    
    def test_is_event_handler_true(self):
        """_is_event_handler returns True for EventHandler."""
        from pynext.core.html import _is_event_handler
        
        handler = EventHandler(fn=lambda: None)
        assert _is_event_handler(handler) is True


# ==============================================================================
# Context Registration Tests
# ==============================================================================

class TestContextRegistration:
    """Tests for context event registration with modifiers."""
    
    def test_register_event_without_modifiers(self):
        """Register event without modifiers."""
        from pynext.core.context import RenderContext
        
        ctx = RenderContext()
        ctx.register_event("el_1", "click", "console.log('clicked')")
        
        assert "el_1" in ctx.event_handlers
        assert "click" in ctx.event_handlers["el_1"]
        assert ctx.event_handlers["el_1"]["click"]["code"] == "console.log('clicked')"
        assert ctx.event_handlers["el_1"]["click"]["mods"] == {}
    
    def test_register_event_with_modifiers(self):
        """Register event with modifiers."""
        from pynext.core.context import RenderContext
        
        ctx = RenderContext()
        mods = {"stop": True, "self_only": True}
        ctx.register_event("el_1", "click", "console.log('clicked')", mods)
        
        assert ctx.event_handlers["el_1"]["click"]["mods"] == mods
    
    def test_register_multiple_events(self):
        """Register multiple events on same element."""
        from pynext.core.context import RenderContext
        
        ctx = RenderContext()
        ctx.register_event("el_1", "click", "handleClick()", {"stop": True})
        ctx.register_event("el_1", "submit", "handleSubmit()", {"prevent": True})
        
        assert "click" in ctx.event_handlers["el_1"]
        assert "submit" in ctx.event_handlers["el_1"]
        assert ctx.event_handlers["el_1"]["click"]["mods"]["stop"] is True
        assert ctx.event_handlers["el_1"]["submit"]["mods"]["prevent"] is True


# ==============================================================================
# Import/Export Tests
# ==============================================================================

class TestImportExport:
    """Tests for import/export from pynext package."""
    
    def test_import_from_pynext(self):
        """Can import event modifiers from pynext."""
        from pynext import stop, prevent, self_only, once, capture, EventHandler
        
        assert callable(stop)
        assert callable(prevent)
        assert callable(self_only)
        assert callable(once)
        assert callable(capture)
    
    def test_import_aliases(self):
        """Can import aliases from pynext."""
        from pynext import stop_propagation, prevent_default
        
        assert callable(stop_propagation)
        assert callable(prevent_default)
    
    def test_import_from_events_module(self):
        """Can import from pynext.events module."""
        from pynext.events import stop, prevent, self_only, once, capture
        
        assert callable(stop)


# ==============================================================================
# Edge Cases
# ==============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_handler_with_args(self):
        """Handler function with arguments."""
        result = []
        fn = lambda x, y: result.append(x + y)
        handler = stop(fn)
        handler(1, 2)
        assert result == [3]
    
    def test_handler_with_kwargs(self):
        """Handler function with keyword arguments."""
        result = []
        fn = lambda x, y=10: result.append(x + y)
        handler = stop(fn)
        handler(5, y=20)
        assert result == [25]
    
    def test_handler_returns_value(self):
        """Handler can return a value."""
        fn = lambda: "returned"
        handler = stop(fn)
        assert handler() == "returned"
    
    def test_none_function(self):
        """EventHandler with None function (invalid but shouldn't crash)."""
        handler = EventHandler(fn=None)  # type: ignore
        assert handler.fn is None
    
    def test_double_wrap_same_modifier(self):
        """Wrapping with same modifier twice is idempotent."""
        fn = lambda: None
        handler = stop(stop(fn))
        assert handler.stop is True
        # Should still work, just redundant
    
    def test_get_modifiers_false_values_excluded(self):
        """get_modifiers only includes True values."""
        handler = EventHandler(
            fn=lambda: None,
            stop=True,
            prevent=False,  # Explicitly False
        )
        mods = handler.get_modifiers()
        assert "stop" in mods
        assert "prevent" not in mods


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """Integration tests with HTML elements."""
    
    def test_element_with_stop_handler(self):
        """Element can use stop() modifier."""
        from pynext import div, stop
        from pynext.core.context import RenderContext, set_context, clear_context
        
        try:
            ctx = RenderContext()
            set_context(ctx)
            
            element = div(onclick=stop(lambda: None))
            html = element.render()
            
            # Should have an ID for event attachment
            assert "id=" in html
        finally:
            clear_context()
    
    def test_element_with_self_only_handler(self):
        """Element can use self_only() modifier."""
        from pynext import div, self_only
        from pynext.core.context import RenderContext, set_context, clear_context
        
        try:
            ctx = RenderContext()
            set_context(ctx)
            
            element = div(onclick=self_only(lambda: None))
            html = element.render()
            
            # Check event was registered with modifier
            assert len(ctx.event_handlers) > 0
            for el_id, handlers in ctx.event_handlers.items():
                if "click" in handlers:
                    assert handlers["click"]["mods"].get("self_only") is True
        finally:
            clear_context()
    
    def test_element_with_composed_handlers(self):
        """Element can use composed modifiers."""
        from pynext import button, stop, prevent
        from pynext.core.context import RenderContext, set_context, clear_context
        
        try:
            ctx = RenderContext()
            set_context(ctx)
            
            element = button(onclick=stop(prevent(lambda: None)))
            html = element.render()
            
            # Check both modifiers registered
            for el_id, handlers in ctx.event_handlers.items():
                if "click" in handlers:
                    mods = handlers["click"]["mods"]
                    assert mods.get("stop") is True
                    assert mods.get("prevent") is True
        finally:
            clear_context()
    
    def test_hydration_data_includes_modifiers(self):
        """Hydration data includes event modifiers."""
        from pynext import div, self_only
        from pynext.core.context import RenderContext, set_context, clear_context
        
        try:
            ctx = RenderContext()
            set_context(ctx)
            
            element = div(onclick=self_only(lambda: None))
            element.render()
            
            hydration_data = ctx.get_hydration_data()
            
            # Events should be in hydration data
            assert "events" in hydration_data
            events = hydration_data["events"]
            
            # At least one event with self_only
            found_self_only = False
            for el_id, handlers in events.items():
                for event_type, handler_data in handlers.items():
                    if handler_data.get("mods", {}).get("self_only"):
                        found_self_only = True
            
            assert found_self_only, "self_only modifier not found in hydration data"
        finally:
            clear_context()
    
    def test_nested_handlers(self):
        """Nested elements with different handlers."""
        from pynext import div, button, self_only, stop
        from pynext.core.context import RenderContext, set_context, clear_context
        
        try:
            ctx = RenderContext()
            set_context(ctx)
            
            # Outer with self_only, inner with stop
            outer = div(onclick=self_only(lambda: None))[
                button(onclick=stop(lambda: None))["Click"]
            ]
            outer.render()
            
            # Should have two events registered
            assert len(ctx.event_handlers) == 2
        finally:
            clear_context()
    
    def test_form_with_prevent(self):
        """Form element with prevent() for submission."""
        from pynext.core.html import form
        from pynext import prevent
        from pynext.core.context import RenderContext, set_context, clear_context
        
        try:
            ctx = RenderContext()
            set_context(ctx)
            
            element = form(onsubmit=prevent(lambda: None))
            element.render()
            
            # Check prevent modifier
            for el_id, handlers in ctx.event_handlers.items():
                if "submit" in handlers:
                    assert handlers["submit"]["mods"].get("prevent") is True
        finally:
            clear_context()
    
    def test_once_modifier_in_context(self):
        """once() modifier appears in context."""
        from pynext import div, once
        from pynext.core.context import RenderContext, set_context, clear_context
        
        try:
            ctx = RenderContext()
            set_context(ctx)
            
            element = div(onclick=once(lambda: None))
            element.render()
            
            for el_id, handlers in ctx.event_handlers.items():
                if "click" in handlers:
                    assert handlers["click"]["mods"].get("once") is True
        finally:
            clear_context()
    
    def test_capture_modifier_in_context(self):
        """capture() modifier appears in context."""
        from pynext import div, capture
        from pynext.core.context import RenderContext, set_context, clear_context
        
        try:
            ctx = RenderContext()
            set_context(ctx)
            
            element = div(onclick=capture(lambda: None))
            element.render()
            
            for el_id, handlers in ctx.event_handlers.items():
                if "click" in handlers:
                    assert handlers["click"]["mods"].get("capture") is True
        finally:
            clear_context()
    
    def test_all_modifiers_in_context(self):
        """All modifiers appear in context when composed."""
        from pynext import div, stop, prevent, self_only, once, capture
        from pynext.core.context import RenderContext, set_context, clear_context
        
        try:
            ctx = RenderContext()
            set_context(ctx)
            
            element = div(onclick=capture(once(stop(prevent(self_only(lambda: None))))))
            element.render()
            
            for el_id, handlers in ctx.event_handlers.items():
                if "click" in handlers:
                    mods = handlers["click"]["mods"]
                    assert mods.get("stop") is True
                    assert mods.get("prevent") is True
                    assert mods.get("self_only") is True
                    assert mods.get("once") is True
                    assert mods.get("capture") is True
        finally:
            clear_context()

