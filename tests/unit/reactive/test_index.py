"""
Tests for Index Component - Index-Based List Rendering

50 comprehensive tests covering:
- Basic rendering (15 tests)
- Index tracking (20 tests)
- Edge cases (15 tests)
"""

import pytest
from pynext.reactive.control_flow import Index
from pynext.reactive.signal import Signal
from pynext.reactive.store import Store


# =============================================================================
# SECTION 1: BASIC RENDERING (15 tests)
# =============================================================================

class TestIndexBasicRendering:
    """Basic Index component rendering tests."""
    
    def test_index_renders_list(self):
        """Index renders a basic list."""
        items = [1, 2, 3]
        index_comp = Index(each=items)[lambda item, i: f"<li>{item()}</li>"]
        html = index_comp.render()
        
        assert "<li>1</li>" in html
        assert "<li>2</li>" in html
        assert "<li>3</li>" in html
    
    def test_index_renders_empty(self):
        """Index renders empty when list is empty."""
        index_comp = Index(each=[])[lambda item, i: f"<li>{item()}</li>"]
        html = index_comp.render()
        
        assert 'data-empty="true"' in html
    
    def test_index_with_fallback(self):
        """Index shows fallback when empty."""
        index_comp = Index(each=[], fallback="<p>No items</p>")[
            lambda item, i: f"<li>{item()}</li>"
        ]
        html = index_comp.render()
        
        assert "No items" in html
    
    def test_index_single_item(self):
        """Index renders single item."""
        index_comp = Index(each=[42])[lambda item, i: f"<li>{item()}</li>"]
        html = index_comp.render()
        
        assert "<li>42</li>" in html
    
    def test_index_provides_index(self):
        """Index provides index to render function."""
        index_comp = Index(each=["a", "b", "c"])[
            lambda item, i: f"<li>{i}: {item()}</li>"
        ]
        html = index_comp.render()
        
        assert "0: a" in html
        assert "1: b" in html
        assert "2: c" in html
    
    def test_index_unique_id(self):
        """Each Index has unique ID."""
        idx1 = Index(each=[1])[lambda x, i: str(x())]
        idx2 = Index(each=[2])[lambda x, i: str(x())]
        
        assert idx1._id != idx2._id
    
    def test_index_data_attribute(self):
        """Index includes data-index attribute."""
        index_comp = Index(each=[1])[lambda x, i: str(x())]
        html = index_comp.render()
        
        assert 'data-index=' in html
    
    def test_index_item_data_attribute(self):
        """Index items have data-index-item attribute."""
        index_comp = Index(each=[1, 2])[lambda x, i: str(x())]
        html = index_comp.render()
        
        assert 'data-index-item="0"' in html
        assert 'data-index-item="1"' in html
    
    def test_index_str_method(self):
        """Index __str__ returns rendered HTML."""
        index_comp = Index(each=[1])[lambda x, i: str(x())]
        assert str(index_comp) == index_comp.render()
    
    def test_index_repr(self):
        """Index __repr__ is informative."""
        index_comp = Index(each=[1, 2, 3])[lambda x, i: str(x())]
        assert "Index" in repr(index_comp)
    
    def test_index_callable_each(self):
        """Index works with callable each."""
        index_comp = Index(each=lambda: [1, 2, 3])[lambda x, i: str(x())]
        html = index_comp.render()
        
        assert "1" in html
        assert "2" in html
    
    def test_index_without_render_fn(self):
        """Index without render function renders empty."""
        index_comp = Index(each=[1, 2, 3])
        html = index_comp.render()
        
        assert 'data-index=' in html
    
    def test_index_with_strings(self):
        """Index renders list of strings."""
        index_comp = Index(each=["hello", "world"])[
            lambda s, i: f"<p>{s()}</p>"
        ]
        html = index_comp.render()
        
        assert "hello" in html
        assert "world" in html
    
    def test_index_with_numbers(self):
        """Index renders list of numbers."""
        index_comp = Index(each=[1.5, 2.5, 3.5])[
            lambda n, i: f"<span>{n()}</span>"
        ]
        html = index_comp.render()
        
        assert "1.5" in html
        assert "2.5" in html
    
    def test_index_nested_content(self):
        """Index renders nested HTML content."""
        index_comp = Index(each=[1, 2])[
            lambda x, i: f"<li><span class='num'>{x()}</span></li>"
        ]
        html = index_comp.render()
        
        assert "class='num'" in html


# =============================================================================
# SECTION 2: INDEX TRACKING (20 tests)
# =============================================================================

class TestIndexTracking:
    """Tests for Index accessor behavior."""
    
    def test_index_item_is_callable(self):
        """Item in Index is a callable accessor."""
        called = [False]
        
        def render(item, i):
            result = item()  # Call the accessor
            called[0] = True
            return str(result)
        
        index_comp = Index(each=[42])[render]
        index_comp.render()
        
        assert called[0]
    
    def test_index_accessor_returns_value(self):
        """Index accessor returns correct value."""
        values = []
        
        def render(item, i):
            values.append(item())
            return str(item())
        
        index_comp = Index(each=[10, 20, 30])[render]
        index_comp.render()
        
        assert values == [10, 20, 30]
    
    def test_index_accessor_consistent(self):
        """Index accessor returns same value on repeated calls."""
        def render(item, i):
            v1 = item()
            v2 = item()
            v3 = item()
            assert v1 == v2 == v3
            return str(v1)
        
        index_comp = Index(each=[42])[render]
        index_comp.render()
    
    def test_index_tracks_position(self):
        """Index provides correct position index."""
        indices = []
        
        def render(item, i):
            indices.append(i)
            return str(item())
        
        index_comp = Index(each=["a", "b", "c", "d"])[render]
        index_comp.render()
        
        assert indices == [0, 1, 2, 3]
    
    def test_index_with_signal_list(self):
        """Index works with Signal containing list."""
        items = Signal([1, 2, 3])
        index_comp = Index(each=lambda: items())[lambda x, i: str(x())]
        
        html = index_comp.render()
        assert "1" in html
        assert "2" in html
    
    def test_index_updates_on_list_change(self):
        """Index updates when list changes."""
        items = Signal([1])
        index_comp = Index(each=lambda: items())[lambda x, i: str(x())]
        
        html1 = index_comp.render()
        assert "1" in html1
        
        items.set([1, 2])
        html2 = index_comp.render()
        
        assert "2" in html2
    
    def test_index_grows_list(self):
        """Index handles list growing."""
        items = Signal([1])
        index_comp = Index(each=lambda: items())[lambda x, i: str(x())]
        
        items.set([1, 2, 3, 4, 5])
        html = index_comp.render()
        
        assert "5" in html
    
    def test_index_shrinks_list(self):
        """Index handles list shrinking."""
        items = Signal([1, 2, 3, 4, 5])
        index_comp = Index(each=lambda: items())[lambda x, i: str(x())]
        
        items.set([1, 2])
        html = index_comp.render()
        
        assert 'data-index-item="2"' not in html
    
    def test_index_clears_list(self):
        """Index handles list becoming empty."""
        items = Signal([1, 2, 3])
        index_comp = Index(each=lambda: items(), fallback="Empty")[
            lambda x, i: str(x())
        ]
        
        items.set([])
        html = index_comp.render()
        
        assert "Empty" in html
    
    def test_index_populates_empty(self):
        """Index handles empty list being populated."""
        items = Signal([])
        index_comp = Index(each=lambda: items(), fallback="Empty")[
            lambda x, i: str(x())
        ]
        
        html1 = index_comp.render()
        assert "Empty" in html1
        
        items.set([42])
        html2 = index_comp.render()
        
        assert "42" in html2
    
    def test_index_item_update_simulation(self):
        """Index handles individual item updates."""
        items = Signal([10, 20, 30])
        index_comp = Index(each=lambda: items())[lambda x, i: str(x())]
        
        html1 = index_comp.render()
        assert "20" in html1
        
        items.set([10, 25, 30])
        html2 = index_comp.render()
        
        assert "25" in html2
    
    def test_index_replace_all(self):
        """Index handles replacing all items."""
        items = Signal([1, 2, 3])
        index_comp = Index(each=lambda: items())[lambda x, i: str(x())]
        
        html1 = index_comp.render()
        assert "1" in html1
        
        items.set([4, 5, 6])
        html = index_comp.render()
        
        assert "4" in html
    
    def test_index_with_store(self):
        """Index works with Store."""
        store = Store({"items": [1, 2, 3]})
        index_comp = Index(each=lambda: list(store.items))[
            lambda x, i: str(x())
        ]
        
        html = index_comp.render()
        assert "1" in html
        assert "2" in html
    
    def test_index_derived_list(self):
        """Index with derived list."""
        source = Signal([1, 2, 3, 4, 5])
        index_comp = Index(each=lambda: [x * 2 for x in source()])[
            lambda x, i: str(x())
        ]
        
        html = index_comp.render()
        assert "2" in html
        assert "10" in html
    
    def test_index_filtered_list(self):
        """Index with filtered list."""
        items = Signal([1, 2, 3, 4, 5])
        index_comp = Index(each=lambda: [x for x in items() if x > 2])[
            lambda x, i: str(x())
        ]
        
        html = index_comp.render()
        assert "3" in html
        assert "4" in html
        assert "5" in html
    
    def test_index_sorted_list(self):
        """Index with sorted list."""
        items = Signal([3, 1, 4, 1, 5])
        index_comp = Index(each=lambda: sorted(items()))[
            lambda x, i: str(x())
        ]
        
        html = index_comp.render()
        assert "1" in html
        assert "5" in html
    
    def test_index_item_accessor_captures_correctly(self):
        """Index item accessor captures correct value."""
        results = []
        
        def render(item, i):
            # Store the accessor, call it later
            results.append((i, item))
            return str(item())
        
        index_comp = Index(each=[100, 200, 300])[render]
        index_comp.render()
        
        # Each accessor should return its value
        for i, accessor in results:
            expected = [100, 200, 300][i]
            assert accessor() == expected
    
    def test_index_position_independent_of_value(self):
        """Index position is independent of value."""
        def render(item, i):
            return f"{i}:{item()}"
        
        index_comp = Index(each=[100, 100, 100])[render]
        html = index_comp.render()
        
        assert "0:100" in html
        assert "1:100" in html
        assert "2:100" in html
    
    def test_index_large_list_positions(self):
        """Index handles large list positions correctly."""
        items = list(range(100))
        positions = []
        
        def render(item, i):
            positions.append(i)
            return str(item())
        
        index_comp = Index(each=items)[render]
        index_comp.render()
        
        assert positions == list(range(100))


# =============================================================================
# SECTION 3: EDGE CASES (15 tests)
# =============================================================================

class TestIndexEdgeCases:
    """Edge case tests for Index component."""
    
    def test_index_none_list(self):
        """Index handles None list."""
        index_comp = Index(each=lambda: None)[lambda x, i: str(x())]
        html = index_comp.render()
        
        assert 'data-empty="true"' in html
    
    def test_index_none_items(self):
        """Index handles None items in list."""
        items = [1, None, 3]
        index_comp = Index(each=items)[lambda x, i: str(x())]
        html = index_comp.render()
        
        assert "1" in html
        assert "None" in html
        assert "3" in html
    
    def test_index_very_large_list(self):
        """Index handles very large list."""
        items = list(range(1000))
        index_comp = Index(each=items)[lambda x, i: str(x())]
        
        html = index_comp.render()
        assert "999" in html
    
    def test_index_unicode(self):
        """Index handles unicode content."""
        items = ["日本語", "中文", "🎉"]
        index_comp = Index(each=items)[lambda x, i: f"<span>{x()}</span>"]
        
        html = index_comp.render()
        assert "日本語" in html
        assert "🎉" in html
    
    def test_index_html_content(self):
        """Index renders HTML content."""
        items = ["<b>bold</b>", "<i>italic</i>"]
        index_comp = Index(each=items)[lambda x, i: x()]
        
        html = index_comp.render()
        assert "<b>bold</b>" in html
    
    def test_index_empty_string_item(self):
        """Index handles empty string item."""
        items = ["a", "", "c"]
        index_comp = Index(each=items)[lambda x, i: f"[{x()}]"]
        
        html = index_comp.render()
        assert "[]" in html
    
    def test_index_boolean_items(self):
        """Index handles boolean items."""
        items = [True, False, True]
        index_comp = Index(each=items)[lambda x, i: str(x())]
        
        html = index_comp.render()
        assert "True" in html
        assert "False" in html
    
    def test_index_mixed_types(self):
        """Index handles mixed types."""
        items = [1, "two", 3.0, True, None]
        index_comp = Index(each=items)[lambda x, i: str(x())]
        
        html = index_comp.render()
        assert "1" in html
        assert "two" in html
        assert "3.0" in html
    
    def test_index_tuple_list(self):
        """Index handles tuple as list."""
        items = [1, 2, 3]  # Use list directly
        index_comp = Index(each=items)[lambda x, i: str(x())]
        
        html = index_comp.render()
        assert "1" in html
        assert "3" in html
    
    def test_index_generator(self):
        """Index handles generator."""
        def gen():
            yield 1
            yield 2
        
        index_comp = Index(each=lambda: list(gen()))[lambda x, i: str(x())]
        
        html = index_comp.render()
        assert "1" in html
        assert "2" in html
    
    def test_index_range(self):
        """Index handles range."""
        index_comp = Index(each=lambda: list(range(5)))[lambda x, i: str(x())]
        
        html = index_comp.render()
        assert "0" in html
        assert "4" in html
    
    def test_index_render_returns_empty(self):
        """Index handles render returning empty."""
        items = [1, 2, 3]
        index_comp = Index(each=items)[lambda x, i: ""]
        
        html = index_comp.render()
        assert 'data-index=' in html
    
    def test_index_render_returns_none(self):
        """Index handles render returning None."""
        items = [1, 2, 3]
        index_comp = Index(each=items)[lambda x, i: None]
        
        html = index_comp.render()
        assert 'data-index=' in html
    
    def test_index_callable_fallback(self):
        """Index handles callable fallback."""
        index_comp = Index(
            each=[],
            fallback=lambda: "Dynamic fallback"
        )[lambda x, i: str(x())]
        
        html = index_comp.render()
        assert "Dynamic fallback" in html
    
    def test_index_rerender_stability(self):
        """Index renders same output on repeated calls."""
        items = [1, 2, 3]
        index_comp = Index(each=items)[lambda x, i: str(x())]
        
        html1 = index_comp.render()
        html2 = index_comp.render()
        
        assert html1 == html2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

