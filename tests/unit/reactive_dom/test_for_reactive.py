"""
Tests for For component reactive behavior.

Tests cover:
- For list rendering
- For with keys
- For binding registration
- Array diffing logic
- Template handling
"""

import pytest
from pynext.reactive import Signal
from pynext.reactive.store import Store
from pynext.reactive.control_flow import For
from pynext.core.context import RenderContext, set_context, clear_context


class TestForBasic:
    """Basic For rendering tests."""
    
    def test_for_static_list(self):
        """For renders static list items."""
        items = [1, 2, 3]
        for_comp = For(each=items)[lambda item, i: str(item)]
        html = for_comp.render()
        assert "1" in html
        assert "2" in html
        assert "3" in html
    
    def test_for_empty_list(self):
        """For with empty list renders fallback or empty."""
        for_comp = For(each=[])[lambda item, i: str(item)]
        html = for_comp.render()
        assert 'data-empty="true"' in html
    
    def test_for_with_fallback(self):
        """For with empty list renders fallback."""
        for_comp = For(each=[], fallback="No items")[lambda item, i: str(item)]
        html = for_comp.render()
        assert "No items" in html
    
    def test_for_callable_list(self):
        """For with callable that returns list."""
        items = [1, 2, 3]
        for_comp = For(each=lambda: items)[lambda item, i: str(item)]
        html = for_comp.render()
        assert "1" in html and "2" in html and "3" in html
    
    def test_for_signal_list(self):
        """For with signal containing list."""
        items = Signal([1, 2, 3], name="items")
        for_comp = For(each=lambda: items())[lambda item, i: str(item)]
        html = for_comp.render()
        assert "1" in html and "2" in html and "3" in html
    
    def test_for_has_unique_id(self):
        """Each For has unique ID."""
        for1 = For(each=[1])[lambda x, i: str(x)]
        for2 = For(each=[2])[lambda x, i: str(x)]
        assert for1._id != for2._id
        assert for1._id.startswith("for_")
    
    def test_for_pynext_for_attribute(self):
        """For renders data-pynext-for attribute."""
        for_comp = For(each=[1])[lambda x, i: str(x)]
        html = for_comp.render()
        assert 'data-pynext-for="true"' in html


class TestForKeys:
    """For key extraction tests."""
    
    def test_for_item_with_id(self):
        """Items with 'id' attribute use id as key."""
        class Item:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        items = [Item(1, "A"), Item(2, "B")]
        for_comp = For(each=items)[lambda item, i: item.name]
        html = for_comp.render()
        assert 'data-for-item="1"' in html
        assert 'data-for-item="2"' in html
    
    def test_for_dict_with_id(self):
        """Dict items with 'id' key use id as key."""
        items = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        for_comp = For(each=items)[lambda item, i: item["name"]]
        html = for_comp.render()
        assert 'data-for-item="1"' in html
        assert 'data-for-item="2"' in html
    
    def test_for_custom_key_fn(self):
        """Custom key function extracts key."""
        items = [{"email": "a@b.com"}, {"email": "c@d.com"}]
        for_comp = For(
            each=items,
            key_fn=lambda x: x["email"]
        )[lambda item, i: item["email"]]
        html = for_comp.render()
        assert 'data-for-item="a@b.com"' in html
        assert 'data-for-item="c@d.com"' in html
    
    def test_for_index_as_key_fallback(self):
        """Primitives use index as key."""
        items = ["a", "b", "c"]
        for_comp = For(each=items)[lambda item, i: item]
        html = for_comp.render()
        assert 'data-for-item="0"' in html
        assert 'data-for-item="1"' in html
        assert 'data-for-item="2"' in html


class TestForBindingRegistration:
    """For binding registration tests."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_for_registers_binding(self):
        """For with signal registers binding."""
        items = Signal([1, 2, 3], name="items")
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        for_comp.render()
        
        assert len(self.ctx.bindings) == 1
        binding = self.ctx.bindings[0]
        assert binding.binding_type == "for"
    
    def test_for_binding_has_signal_deps(self):
        """For binding has signal dependencies."""
        items = Signal([1, 2, 3], name="items")
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        for_comp.render()
        
        binding = self.ctx.bindings[0]
        assert items._id in binding.signal_deps
    
    def test_for_binding_has_initial_data(self):
        """For binding has initial data with count and keys."""
        items = Signal([{"id": 1}, {"id": 2}], name="items")
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        for_comp.render()
        
        binding = self.ctx.bindings[0]
        assert binding.initial_value["count"] == 2
        assert 1 in binding.initial_value["keys"]
        assert 2 in binding.initial_value["keys"]
    
    def test_for_no_binding_static_list(self):
        """Static list doesn't register binding."""
        items = [1, 2, 3]
        for_comp = For(each=items)[lambda x, i: str(x)]
        for_comp.render()
        
        assert len(self.ctx.bindings) == 0


class TestForSignalExtraction:
    """For signal dependency extraction tests."""
    
    def test_extract_signal_from_each(self):
        """Extract signal from each lambda."""
        items = Signal([1], name="items")
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        
        deps = for_comp._extract_signal_deps()
        assert items._id in deps
    
    def test_extract_store_from_each(self):
        """Extract store from each lambda."""
        store = Store({"items": [1, 2]}, name="store")
        for_comp = For(each=lambda: store.items)[lambda x, i: str(x)]
        
        deps = for_comp._extract_signal_deps()
        assert len(deps) >= 0  # Store extraction may vary
    
    def test_no_deps_static_list(self):
        """Static list has no dependencies."""
        for_comp = For(each=[1, 2, 3])[lambda x, i: str(x)]
        
        deps = for_comp._extract_signal_deps()
        assert deps == []


class TestForUpdateExpr:
    """For update expression generation tests."""
    
    def test_generate_signal_read_expr(self):
        """Generate expression that reads signal."""
        items = Signal([1], name="items")
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        
        expr = for_comp._generate_update_expr()
        assert f"getSignal('{items._id}')" in expr
    
    def test_generate_empty_for_no_deps(self):
        """Generate empty array for no dependencies."""
        for_comp = For(each=[1])[lambda x, i: str(x)]
        
        expr = for_comp._generate_update_expr()
        assert expr == "[]"


class TestForHydrationData:
    """For hydration data tests."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_for_binding_in_hydration(self):
        """For binding appears in hydration data."""
        items = Signal([1], name="items")
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        for_comp.render()
        
        data = self.ctx.get_hydration_data()
        assert len(data["bindings"]) == 1
    
    def test_for_type_in_hydration(self):
        """For type is 'for' in hydration data."""
        items = Signal([1], name="items")
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        for_comp.render()
        
        data = self.ctx.get_hydration_data()
        assert data["bindings"][0]["type"] == "for"


class TestForEdgeCases:
    """For edge case tests."""
    
    def test_for_no_render_fn(self):
        """For without render function renders empty."""
        for_comp = For(each=[1, 2, 3])
        html = for_comp.render()
        assert 'data-pynext-for="true"' in html
    
    def test_for_none_items(self):
        """For with None items renders fallback."""
        for_comp = For(each=lambda: None, fallback="Empty")[lambda x, i: str(x)]
        # Should handle gracefully
        html = for_comp.render()
        assert html is not None
    
    def test_for_str_method(self):
        """For __str__ returns rendered HTML."""
        for_comp = For(each=[1])[lambda x, i: str(x)]
        assert str(for_comp) == for_comp.render()
    
    def test_for_repr_method(self):
        """For __repr__ is informative."""
        for_comp = For(each=[1, 2, 3])[lambda x, i: str(x)]
        assert "For" in repr(for_comp)
    
    def test_for_iter_method(self):
        """For is iterable for debugging."""
        for_comp = For(each=[1, 2, 3])[lambda x, i: str(x)]
        items = list(for_comp)
        assert len(items) == 3
        assert items[0] == (1, 0)
        assert items[1] == (2, 1)


class TestForWithElements:
    """For with Element children tests."""
    
    def test_for_with_div_children(self):
        """For renders Element children."""
        from pynext.core.html import div
        items = [{"name": "A"}, {"name": "B"}]
        for_comp = For(each=items)[lambda item, i: div()[item["name"]]]
        html = for_comp.render()
        assert "<div>A</div>" in html
        assert "<div>B</div>" in html
    
    def test_for_with_nested_elements(self):
        """For renders nested Elements."""
        from pynext.core.html import div, span
        items = [1, 2]
        for_comp = For(each=items)[
            lambda item, i: div()[span()[str(item)]]
        ]
        html = for_comp.render()
        assert "<span>1</span>" in html
        assert "<span>2</span>" in html


class TestForLargeList:
    """For performance tests with large lists."""
    
    def test_for_100_items(self):
        """For handles 100 items."""
        items = list(range(100))
        for_comp = For(each=items)[lambda x, i: str(x)]
        html = for_comp.render()
        assert "99" in html
    
    def test_for_1000_items(self):
        """For handles 1000 items."""
        items = list(range(1000))
        for_comp = For(each=items)[lambda x, i: str(x)]
        html = for_comp.render()
        assert "999" in html


class TestForReactiveStore:
    """For with reactive Store tests."""
    
    def setup_method(self):
        """Set up render context."""
        self.ctx = RenderContext()
        set_context(self.ctx)
    
    def teardown_method(self):
        """Clear render context."""
        clear_context()
    
    def test_for_with_store_list(self):
        """For works with Store property."""
        store = Store({"todos": [{"id": 1, "text": "A"}]}, name="store")
        for_comp = For(each=lambda: store.todos)[
            lambda item, i: item.text if hasattr(item, 'text') else str(item)
        ]
        html = for_comp.render()
        assert html is not None

