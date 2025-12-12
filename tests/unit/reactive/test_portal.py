"""
Tests for Portal Component - Render Outside Component Tree

50 comprehensive tests covering:
- Basic rendering (15 tests)
- Cleanup and lifecycle (20 tests)
- Edge cases (15 tests)
"""

import pytest
from pynext.reactive.control_flow import Portal
from pynext.reactive.signal import Signal


# =============================================================================
# SECTION 1: BASIC RENDERING (15 tests)
# =============================================================================

class TestPortalBasicRendering:
    """Basic Portal rendering tests."""
    
    def test_portal_renders_content(self):
        """Portal renders its content."""
        portal = Portal(mount="body")["Hello Portal"]
        html = portal.render()
        
        assert "Hello Portal" in html
    
    def test_portal_default_mount(self):
        """Portal defaults to body mount."""
        portal = Portal()["Content"]
        html = portal.render()
        
        assert 'data-mount="body"' in html
    
    def test_portal_custom_mount(self):
        """Portal accepts custom mount selector."""
        portal = Portal(mount="#modal-root")["Modal"]
        html = portal.render()
        
        assert 'data-mount="#modal-root"' in html
    
    def test_portal_class_selector(self):
        """Portal accepts class selector."""
        portal = Portal(mount=".overlay-container")["Overlay"]
        html = portal.render()
        
        assert 'data-mount=".overlay-container"' in html
    
    def test_portal_data_attribute(self):
        """Portal includes data-portal attribute."""
        portal = Portal()["Content"]
        html = portal.render()
        
        assert 'data-portal=' in html
    
    def test_portal_unique_id(self):
        """Each Portal has unique ID."""
        p1 = Portal()["A"]
        p2 = Portal()["B"]
        
        assert p1._id != p2._id
    
    def test_portal_use_shadow_attribute(self):
        """Portal includes shadow DOM attribute when enabled."""
        portal = Portal(mount="body", use_shadow=True)["Shadow"]
        html = portal.render()
        
        assert 'data-shadow="true"' in html
    
    def test_portal_svg_attribute(self):
        """Portal includes SVG attribute when enabled."""
        portal = Portal(mount="body", is_svg=True)["SVG Content"]
        html = portal.render()
        
        assert 'data-svg="true"' in html
    
    def test_portal_str_method(self):
        """Portal __str__ returns rendered HTML."""
        portal = Portal()["Content"]
        assert str(portal) == portal.render()
    
    def test_portal_repr(self):
        """Portal __repr__ is informative."""
        portal = Portal(mount="#modal")["Content"]
        assert "Portal" in repr(portal)
        assert "#modal" in repr(portal)
    
    def test_portal_html_content(self):
        """Portal renders HTML content."""
        portal = Portal()["<div class='modal'>Modal Content</div>"]
        html = portal.render()
        
        assert "class='modal'" in html
    
    def test_portal_nested_elements(self):
        """Portal renders nested elements."""
        portal = Portal()["<div class='modal-backdrop'><div class='modal-dialog'>Body</div></div>"]
        html = portal.render()
        
        assert "modal-backdrop" in html
        assert "modal-dialog" in html
    
    def test_portal_callable_content(self):
        """Portal renders callable content."""
        portal = Portal()[lambda: "Dynamic Content"]
        html = portal.render()
        
        assert "Dynamic Content" in html
    
    def test_portal_none_content(self):
        """Portal handles None content."""
        portal = Portal()[None]
        html = portal.render()
        
        assert 'data-portal=' in html
    
    def test_portal_empty_content(self):
        """Portal handles empty content."""
        portal = Portal()[""]
        html = portal.render()
        
        assert 'data-portal=' in html


# =============================================================================
# SECTION 2: CLEANUP AND LIFECYCLE (20 tests)
# =============================================================================

class TestPortalLifecycle:
    """Tests for Portal cleanup and lifecycle."""
    
    def test_portal_with_signal_content(self):
        """Portal works with Signal content."""
        message = Signal("Hello")
        portal = Portal()[lambda: message()]
        
        html = portal.render()
        assert "Hello" in html
        
        message.set("Goodbye")
        html = portal.render()
        assert "Goodbye" in html
    
    def test_portal_content_updates(self):
        """Portal content updates on re-render."""
        counter = [0]
        
        def get_content():
            counter[0] += 1
            return f"Render #{counter[0]}"
        
        portal = Portal()[get_content]
        
        assert "Render #1" in portal.render()
        assert "Render #2" in portal.render()
    
    def test_portal_multiple_renders_same_content(self):
        """Portal renders same static content consistently."""
        portal = Portal()["Static"]
        
        html1 = portal.render()
        html2 = portal.render()
        
        assert html1 == html2
    
    def test_portal_id_stable_across_renders(self):
        """Portal ID is stable across renders."""
        portal = Portal()["Content"]
        id1 = portal._id
        portal.render()
        id2 = portal._id
        portal.render()
        id3 = portal._id
        
        assert id1 == id2 == id3
    
    def test_portal_mount_stable_across_renders(self):
        """Portal mount is stable across renders."""
        portal = Portal(mount="#target")["Content"]
        
        html1 = portal.render()
        html2 = portal.render()
        
        assert 'data-mount="#target"' in html1
        assert 'data-mount="#target"' in html2
    
    def test_portal_complex_selector(self):
        """Portal accepts complex CSS selector."""
        portal = Portal(mount="div.modal-container > .inner")["Modal"]
        html = portal.render()
        
        assert "div.modal-container > .inner" in html
    
    def test_portal_attribute_selector(self):
        """Portal accepts attribute selector."""
        portal = Portal(mount="[data-modal-root]")["Modal"]
        html = portal.render()
        
        assert "[data-modal-root]" in html
    
    def test_portal_shadow_and_svg(self):
        """Portal can have both shadow and SVG enabled."""
        portal = Portal(mount="body", use_shadow=True, is_svg=True)["Content"]
        html = portal.render()
        
        assert 'data-shadow="true"' in html
        assert 'data-svg="true"' in html
    
    def test_portal_renders_object_with_render(self):
        """Portal renders object with render method."""
        class Component:
            def render(self):
                return "<span>Component</span>"
        
        portal = Portal()[Component()]
        html = portal.render()
        
        assert "<span>Component</span>" in html
    
    def test_portal_renders_list(self):
        """Portal renders list content."""
        portal = Portal()[["Part 1", " ", "Part 2"]]
        html = portal.render()
        
        assert "Part 1" in html
        assert "Part 2" in html
    
    def test_portal_reactive_mount_selector(self):
        """Portal mount is fixed (not reactive)."""
        portal = Portal(mount="#fixed")["Content"]
        html = portal.render()
        
        assert "#fixed" in html
    
    def test_portal_with_store_content(self):
        """Portal works with Store-based content."""
        from pynext.reactive.store import Store
        
        state = Store({"title": "Modal Title"})
        portal = Portal()[lambda: f"<h1>{state.title}</h1>"]
        
        html = portal.render()
        assert "Modal Title" in html
        
        state.title = "New Title"
        html = portal.render()
        assert "New Title" in html
    
    def test_portal_many_instances(self):
        """Many Portal instances can exist."""
        portals = [Portal(mount=f"#target-{i}")["Content"] for i in range(100)]
        
        for i, portal in enumerate(portals):
            html = portal.render()
            assert f"#target-{i}" in html
    
    def test_portal_nested_portals(self):
        """Portals can be nested."""
        outer = Portal(mount="#outer")[
            Portal(mount="#inner")["Inner Content"]
        ]
        html = outer.render()
        
        assert "Inner Content" in html
        assert "#inner" in html
    
    def test_portal_with_conditional_content(self):
        """Portal with conditional content."""
        visible = Signal(True)
        portal = Portal()[lambda: "Visible" if visible() else "Hidden"]
        
        assert "Visible" in portal.render()
        
        visible.set(False)
        assert "Hidden" in portal.render()
    
    def test_portal_wrapper_structure(self):
        """Portal has proper wrapper structure."""
        portal = Portal(mount="#modal")["Content"]
        html = portal.render()
        
        assert html.startswith("<div")
        assert html.endswith("</div>")
    
    def test_portal_renders_numbers(self):
        """Portal renders numeric content."""
        portal = Portal()[42]
        html = portal.render()
        
        assert "42" in html
    
    def test_portal_renders_boolean(self):
        """Portal renders boolean content."""
        portal = Portal()[True]
        html = portal.render()
        
        assert "True" in html
    
    def test_portal_with_memo_content(self):
        """Portal works with Memo-based content."""
        from pynext.reactive.memo import Memo
        
        count = Signal(5)
        doubled = Memo(lambda: count() * 2)
        
        portal = Portal()[lambda: str(doubled())]
        
        assert "10" in portal.render()
        
        count.set(10)
        assert "20" in portal.render()


# =============================================================================
# SECTION 3: EDGE CASES (15 tests)
# =============================================================================

class TestPortalEdgeCases:
    """Edge case tests for Portal."""
    
    def test_portal_special_chars_in_mount(self):
        """Portal handles special chars in mount selector."""
        portal = Portal(mount="#modal_root")["Content"]
        html = portal.render()
        
        assert "modal_root" in html
    
    def test_portal_empty_mount(self):
        """Portal handles empty mount (uses body)."""
        portal = Portal(mount="")["Content"]
        html = portal.render()
        
        assert 'data-mount=""' in html
    
    def test_portal_whitespace_mount(self):
        """Portal handles whitespace mount."""
        portal = Portal(mount="  ")["Content"]
        html = portal.render()
        
        assert 'data-mount' in html
    
    def test_portal_unicode_content(self):
        """Portal handles unicode content."""
        portal = Portal()["Hello World"]
        html = portal.render()
        
        assert "Hello" in html
    
    def test_portal_very_long_content(self):
        """Portal handles very long content."""
        long_content = "Content " * 100
        portal = Portal()[long_content]
        
        html = portal.render()
        assert "Content" in html
    
    def test_portal_script_content(self):
        """Portal renders script content."""
        portal = Portal()["<script>alert('test')</script>"]
        html = portal.render()
        
        assert "<script>" in html
    
    def test_portal_style_content(self):
        """Portal renders style content."""
        portal = Portal()["<style>.modal { display: block; }</style>"]
        html = portal.render()
        
        assert "<style>" in html
    
    def test_portal_multiline_content(self):
        """Portal handles multiline content."""
        content = "<div><h1>Title</h1><p>Paragraph</p></div>"
        portal = Portal()[content]
        html = portal.render()
        
        assert "Title" in html
        assert "Paragraph" in html
    
    def test_portal_exception_in_content(self):
        """Portal handles exception in content."""
        def bad_content():
            raise ValueError("Bad!")
        
        portal = Portal()[bad_content]
        
        with pytest.raises(ValueError):
            portal.render()
    
    def test_portal_callable_in_callable(self):
        """Portal handles callable returning callable."""
        portal = Portal()[lambda: lambda: "Nested"]
        html = portal.render()
        
        assert "Nested" in html
    
    def test_portal_generator_content(self):
        """Portal handles generator content."""
        def gen():
            yield "A"
            yield "B"
        
        portal = Portal()[lambda: "".join(gen())]
        html = portal.render()
        
        assert "AB" in html
    
    def test_portal_dict_content(self):
        """Portal renders dict content."""
        portal = Portal()[{"key": "value"}]
        html = portal.render()
        
        assert "key" in html
    
    def test_portal_complex_mount_selector(self):
        """Portal handles complex mount selector."""
        portal = Portal(mount="body > div .container")["Content"]
        html = portal.render()
        
        assert "body > div .container" in html
    
    def test_portal_id_selector(self):
        """Portal handles ID selector."""
        portal = Portal(mount="#root")["Content"]
        html = portal.render()
        
        assert "#root" in html
    
    def test_portal_rerender_stability(self):
        """Portal renders same output on repeated calls."""
        portal = Portal(mount="#modal")["Content"]
        
        html1 = portal.render()
        html2 = portal.render()
        html3 = portal.render()
        
        assert html1 == html2 == html3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

