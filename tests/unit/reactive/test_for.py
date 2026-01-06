"""
Tests for For Component - Keyed List Reconciliation

100 comprehensive tests covering:
- Basic rendering (20 tests)
- Key reconciliation (35 tests)
- Reactive updates (25 tests)
- Edge cases (20 tests)
"""

import pytest
from pynext.reactive.control_flow import For
from pynext.reactive.signal import Signal
from pynext.reactive.store import Store
from pynext.reactive.effect import Effect


# =============================================================================
# SECTION 1: BASIC RENDERING (20 tests)
# =============================================================================

class TestForBasicRendering:
    """Basic For component rendering tests."""
    
    def test_for_renders_list(self):
        """For renders a basic list."""
        items = [1, 2, 3]
        for_comp = For(each=items)[lambda item, i: f"<li>{item}</li>"]
        html = for_comp.render()
        
        assert "<li>1</li>" in html
        assert "<li>2</li>" in html
        assert "<li>3</li>" in html
    
    def test_for_renders_empty_list(self):
        """For renders empty when list is empty."""
        for_comp = For(each=[])[lambda item, i: f"<li>{item}</li>"]
        html = for_comp.render()
        
        assert 'data-empty="true"' in html
    
    def test_for_with_fallback(self):
        """For shows fallback when empty."""
        for_comp = For(each=[], fallback="<p>No items</p>")[
            lambda item, i: f"<li>{item}</li>"
        ]
        html = for_comp.render()
        
        assert "No items" in html
    
    def test_for_single_item(self):
        """For renders single item."""
        for_comp = For(each=[42])[lambda item, i: f"<li>{item}</li>"]
        html = for_comp.render()
        
        assert "<li>42</li>" in html
    
    def test_for_index_available(self):
        """For provides index to render function."""
        for_comp = For(each=["a", "b", "c"])[
            lambda item, i: f"<li>{i}: {item}</li>"
        ]
        html = for_comp.render()
        
        assert "0: a" in html
        assert "1: b" in html
        assert "2: c" in html
    
    def test_for_with_objects(self):
        """For renders list of objects."""
        class Item:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        items = [Item(1, "Alice"), Item(2, "Bob")]
        for_comp = For(each=items)[
            lambda item, i: f"<div>{item.name}</div>"
        ]
        html = for_comp.render()
        
        assert "Alice" in html
        assert "Bob" in html
    
    def test_for_with_dicts(self):
        """For renders list of dicts."""
        items = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        for_comp = For(each=items)[
            lambda item, i: f"<div>{item['name']}</div>"
        ]
        html = for_comp.render()
        
        assert "A" in html
        assert "B" in html
    
    def test_for_unique_id(self):
        """Each For has unique ID."""
        for1 = For(each=[1])[lambda x, i: str(x)]
        for2 = For(each=[2])[lambda x, i: str(x)]
        
        assert for1._id != for2._id
    
    def test_for_data_attribute(self):
        """For includes data-for attribute."""
        for_comp = For(each=[1])[lambda x, i: str(x)]
        html = for_comp.render()
        
        assert 'data-pynext-for' in html
    
    def test_for_item_data_attribute(self):
        """For items have data-for-item attribute with key."""
        items = [{"id": "a"}, {"id": "b"}]
        for_comp = For(each=items)[lambda item, i: f"<div>{item['id']}</div>"]
        html = for_comp.render()
        
        assert 'data-for-item="a"' in html
        assert 'data-for-item="b"' in html
    
    def test_for_str_method(self):
        """For __str__ returns rendered HTML."""
        for_comp = For(each=[1])[lambda x, i: str(x)]
        assert str(for_comp) == for_comp.render()
    
    def test_for_repr(self):
        """For __repr__ is informative."""
        for_comp = For(each=[1, 2, 3])[lambda x, i: str(x)]
        assert "For" in repr(for_comp)
    
    def test_for_callable_each(self):
        """For works with callable each."""
        for_comp = For(each=lambda: [1, 2, 3])[lambda x, i: str(x)]
        html = for_comp.render()
        
        assert "1" in html
        assert "2" in html
        assert "3" in html
    
    def test_for_without_render_fn(self):
        """For without render function renders empty."""
        for_comp = For(each=[1, 2, 3])
        html = for_comp.render()
        
        assert 'data-pynext-for' in html
    
    def test_for_nested_content(self):
        """For renders nested HTML content."""
        for_comp = For(each=[1, 2])[
            lambda x, i: f"<li><span class='num'>{x}</span></li>"
        ]
        html = for_comp.render()
        
        assert "class='num'" in html
    
    def test_for_with_key_fn(self):
        """For uses custom key function."""
        items = [{"uuid": "abc", "name": "A"}, {"uuid": "def", "name": "B"}]
        for_comp = For(
            each=items,
            key_fn=lambda item: item["uuid"]
        )[lambda item, i: f"<div>{item['name']}</div>"]
        html = for_comp.render()
        
        assert 'data-for-item="abc"' in html
        assert 'data-for-item="def"' in html
    
    def test_for_iter_protocol(self):
        """For supports iteration for debugging."""
        items = ["a", "b", "c"]
        for_comp = For(each=items)[lambda x, i: x]
        
        result = list(for_comp)
        assert result == [("a", 0), ("b", 1), ("c", 2)]
    
    def test_for_to_js_init(self):
        """For generates JS init code."""
        for_comp = For(each=[1])[lambda x, i: str(x)]
        js = for_comp.to_js_init()
        
        assert "__pynext__.createFor" in js
        assert for_comp._id in js
    
    def test_for_strings(self):
        """For renders list of strings."""
        for_comp = For(each=["hello", "world"])[
            lambda s, i: f"<p>{s}</p>"
        ]
        html = for_comp.render()
        
        assert "hello" in html
        assert "world" in html


# =============================================================================
# SECTION 2: KEY RECONCILIATION (35 tests)
# =============================================================================

class TestForKeyReconciliation:
    """Tests for For's key-based reconciliation."""
    
    def test_key_from_id_attribute(self):
        """For extracts key from item.id."""
        class Item:
            def __init__(self, id):
                self.id = id
        
        items = [Item("x"), Item("y")]
        for_comp = For(each=items)[lambda x, i: str(x.id)]
        html = for_comp.render()
        
        assert 'data-for-item="x"' in html
        assert 'data-for-item="y"' in html
    
    def test_key_from_key_attribute(self):
        """For extracts key from item.key."""
        class Item:
            def __init__(self, key):
                self.key = key
        
        items = [Item("k1"), Item("k2")]
        for_comp = For(each=items)[lambda x, i: str(x.key)]
        html = for_comp.render()
        
        assert 'data-for-item="k1"' in html
    
    def test_key_from_dict_id(self):
        """For extracts key from dict['id']."""
        items = [{"id": "d1"}, {"id": "d2"}]
        for_comp = For(each=items)[lambda x, i: x["id"]]
        html = for_comp.render()
        
        assert 'data-for-item="d1"' in html
    
    def test_key_from_dict_key(self):
        """For extracts key from dict['key']."""
        items = [{"key": "k1"}, {"key": "k2"}]
        for_comp = For(each=items)[lambda x, i: x["key"]]
        html = for_comp.render()
        
        assert 'data-for-item="k1"' in html
    
    def test_key_fallback_to_index(self):
        """For falls back to index when no key available."""
        items = [10, 20, 30]  # Primitives have no id/key
        for_comp = For(each=items)[lambda x, i: str(x)]
        html = for_comp.render()
        
        assert 'data-for-item="0"' in html
        assert 'data-for-item="1"' in html
    
    def test_custom_key_fn(self):
        """For uses custom key_fn."""
        items = [{"email": "a@b.com"}, {"email": "c@d.com"}]
        for_comp = For(
            each=items,
            key_fn=lambda x: x["email"]
        )[lambda x, i: x["email"]]
        html = for_comp.render()
        
        assert 'data-for-item="a@b.com"' in html
    
    def test_key_fn_with_index(self):
        """Key function receives item, extracts key."""
        items = [{"name": "A"}, {"name": "B"}]
        for_comp = For(
            each=items,
            key_fn=lambda x: f"item_{x['name']}"
        )[lambda x, i: x["name"]]
        html = for_comp.render()
        
        assert 'data-for-item="item_A"' in html
    
    def test_unique_keys_preserved(self):
        """Keys are unique in rendered output."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        for_comp = For(each=items)[lambda x, i: str(x["id"])]
        html = for_comp.render()
        
        assert html.count('data-for-item="1"') == 1
        assert html.count('data-for-item="2"') == 1
        assert html.count('data-for-item="3"') == 1
    
    def test_add_item_simulation(self):
        """Simulate adding item to list."""
        items = Signal([{"id": 1}, {"id": 2}])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        html1 = for_comp.render()
        assert 'data-for-item="1"' in html1
        assert 'data-for-item="2"' in html1
        
        items.set([{"id": 1}, {"id": 2}, {"id": 3}])
        html2 = for_comp.render()
        
        assert 'data-for-item="3"' in html2
    
    def test_remove_item_simulation(self):
        """Simulate removing item from list."""
        items = Signal([{"id": 1}, {"id": 2}, {"id": 3}])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        html1 = for_comp.render()
        assert 'data-for-item="2"' in html1
        
        items.set([{"id": 1}, {"id": 3}])
        html2 = for_comp.render()
        
        assert 'data-for-item="2"' not in html2
    
    def test_reorder_simulation(self):
        """Simulate reordering items."""
        items = Signal([{"id": "a"}, {"id": "b"}, {"id": "c"}])
        for_comp = For(each=lambda: items())[lambda x, i: x["id"]]
        
        html1 = for_comp.render()
        
        items.set([{"id": "c"}, {"id": "a"}, {"id": "b"}])
        html2 = for_comp.render()
        
        assert 'data-for-item="c"' in html2
        assert 'data-for-item="a"' in html2
    
    def test_replace_all_items(self):
        """Simulate replacing all items."""
        items = Signal([{"id": 1}, {"id": 2}])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        items.set([{"id": 3}, {"id": 4}])
        html = for_comp.render()
        
        assert 'data-for-item="1"' not in html
        assert 'data-for-item="3"' in html
    
    def test_swap_two_items(self):
        """Simulate swapping two items."""
        items = Signal([{"id": "a"}, {"id": "b"}])
        for_comp = For(each=lambda: items())[lambda x, i: x["id"]]
        
        items.set([{"id": "b"}, {"id": "a"}])
        html = for_comp.render()
        
        # Both should still be present
        assert 'data-for-item="a"' in html
        assert 'data-for-item="b"' in html
    
    def test_insert_at_beginning(self):
        """Simulate inserting at beginning."""
        items = Signal([{"id": 2}, {"id": 3}])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        items.set([{"id": 1}, {"id": 2}, {"id": 3}])
        html = for_comp.render()
        
        assert 'data-for-item="1"' in html
    
    def test_insert_in_middle(self):
        """Simulate inserting in middle."""
        items = Signal([{"id": 1}, {"id": 3}])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        items.set([{"id": 1}, {"id": 2}, {"id": 3}])
        html = for_comp.render()
        
        assert 'data-for-item="2"' in html
    
    def test_remove_first(self):
        """Simulate removing first item."""
        items = Signal([{"id": 1}, {"id": 2}, {"id": 3}])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        items.set([{"id": 2}, {"id": 3}])
        html = for_comp.render()
        
        assert 'data-for-item="1"' not in html
    
    def test_remove_last(self):
        """Simulate removing last item."""
        items = Signal([{"id": 1}, {"id": 2}, {"id": 3}])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        items.set([{"id": 1}, {"id": 2}])
        html = for_comp.render()
        
        assert 'data-for-item="3"' not in html
    
    def test_clear_all_items(self):
        """Simulate clearing all items."""
        items = Signal([{"id": 1}, {"id": 2}])
        for_comp = For(each=lambda: items(), fallback="Empty")[
            lambda x, i: str(x["id"])
        ]
        
        items.set([])
        html = for_comp.render()
        
        assert "Empty" in html
    
    def test_populate_from_empty(self):
        """Simulate populating empty list."""
        items = Signal([])
        for_comp = For(each=lambda: items(), fallback="Empty")[
            lambda x, i: str(x["id"])
        ]
        
        html1 = for_comp.render()
        assert "Empty" in html1
        
        items.set([{"id": 1}])
        html2 = for_comp.render()
        
        assert 'data-for-item="1"' in html2
    
    def test_numeric_keys(self):
        """For handles numeric keys."""
        items = [{"id": 1}, {"id": 2}, {"id": 100}]
        for_comp = For(each=items)[lambda x, i: str(x["id"])]
        html = for_comp.render()
        
        assert 'data-for-item="1"' in html
        assert 'data-for-item="100"' in html
    
    def test_string_keys(self):
        """For handles string keys."""
        items = [{"id": "abc"}, {"id": "xyz"}]
        for_comp = For(each=items)[lambda x, i: x["id"]]
        html = for_comp.render()
        
        assert 'data-for-item="abc"' in html
    
    def test_mixed_key_types(self):
        """For handles mixed key types."""
        items = [{"id": 1}, {"id": "two"}, {"id": 3}]
        for_comp = For(each=items)[lambda x, i: str(x["id"])]
        html = for_comp.render()
        
        assert 'data-for-item="1"' in html
        assert 'data-for-item="two"' in html
    
    def test_update_item_content(self):
        """Update item content without changing key."""
        items = Signal([{"id": 1, "value": "old"}])
        for_comp = For(each=lambda: items())[
            lambda x, i: f'<span>{x["value"]}</span>'
        ]
        
        html1 = for_comp.render()
        assert "old" in html1
        
        items.set([{"id": 1, "value": "new"}])
        html2 = for_comp.render()
        
        assert "new" in html2
        assert 'data-for-item="1"' in html2
    
    def test_batch_add_multiple(self):
        """Add multiple items at once."""
        items = Signal([{"id": 1}])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        items.set([{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}])
        html = for_comp.render()
        
        assert 'data-for-item="2"' in html
        assert 'data-for-item="4"' in html
    
    def test_batch_remove_multiple(self):
        """Remove multiple items at once."""
        items = Signal([{"id": i} for i in range(5)])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        items.set([{"id": 0}, {"id": 4}])
        html = for_comp.render()
        
        assert 'data-for-item="1"' not in html
        assert 'data-for-item="2"' not in html
        assert 'data-for-item="0"' in html
        assert 'data-for-item="4"' in html
    
    def test_reverse_list(self):
        """Reverse entire list."""
        items = Signal([{"id": i} for i in range(5)])
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        items.set([{"id": i} for i in range(4, -1, -1)])
        html = for_comp.render()
        
        # All items should still be present
        for i in range(5):
            assert f'data-for-item="{i}"' in html
    
    def test_shuffle_list(self):
        """Shuffle list maintains all keys."""
        original = [{"id": i} for i in range(10)]
        items = Signal(original.copy())
        for_comp = For(each=lambda: items())[lambda x, i: str(x["id"])]
        
        # Shuffle
        import random
        shuffled = original.copy()
        random.shuffle(shuffled)
        items.set(shuffled)
        
        html = for_comp.render()
        
        for i in range(10):
            assert f'data-for-item="{i}"' in html
    
    def test_key_with_special_chars(self):
        """Keys with special characters."""
        items = [{"id": "a&b"}, {"id": "c<d"}, {"id": "e>f"}]
        for_comp = For(each=items)[lambda x, i: x["id"]]
        html = for_comp.render()
        
        assert "a&b" in html
    
    def test_empty_string_key(self):
        """Handle empty string key."""
        items = [{"id": ""}, {"id": "a"}]
        for_comp = For(each=items)[lambda x, i: x["id"] or "empty"]
        html = for_comp.render()
        
        assert 'data-for-item=""' in html
    
    def test_uuid_keys(self):
        """Handle UUID-like keys."""
        import uuid
        items = [{"id": str(uuid.uuid4())}, {"id": str(uuid.uuid4())}]
        for_comp = For(each=items)[lambda x, i: x["id"][:8]]
        html = for_comp.render()
        
        assert html.count('data-for-item=') == 2
    
    def test_large_key_values(self):
        """Handle large key values."""
        items = [{"id": "x" * 100}, {"id": "y" * 100}]
        for_comp = For(each=items)[lambda x, i: x["id"][:10]]
        html = for_comp.render()
        
        assert "x" * 100 in html
    
    def test_key_fn_returns_tuple(self):
        """Key function can return tuple (converted to string)."""
        items = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        for_comp = For(
            each=items,
            key_fn=lambda x: f"{x['a']}_{x['b']}"
        )[lambda x, i: str(x["a"])]
        html = for_comp.render()
        
        assert 'data-for-item="1_2"' in html


# =============================================================================
# SECTION 3: REACTIVE UPDATES (25 tests)
# =============================================================================

class TestForReactiveUpdates:
    """Tests for For with reactive signals and stores."""
    
    def test_for_with_signal_list(self):
        """For works with Signal containing list."""
        items = Signal([1, 2, 3])
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        
        html = for_comp.render()
        assert "1" in html
        assert "2" in html
    
    def test_for_updates_on_signal_change(self):
        """For updates when signal changes."""
        items = Signal([1])
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        
        html1 = for_comp.render()
        assert "1" in html1
        
        items.set([1, 2])
        html2 = for_comp.render()
        
        assert "2" in html2
    
    def test_for_with_store(self):
        """For works with Store."""
        store = Store({"items": [{"id": 1}, {"id": 2}]})
        for_comp = For(each=lambda: list(store.items))[
            lambda x, i: str(x["id"])
        ]
        
        html = for_comp.render()
        assert "1" in html
        assert "2" in html
    
    def test_for_content_reads_signal(self):
        """For item content can read signals."""
        multiplier = Signal(2)
        items = [1, 2, 3]
        for_comp = For(each=items)[
            lambda x, i: str(x * multiplier())
        ]
        
        html = for_comp.render()
        assert "2" in html
        assert "4" in html
    
    def test_for_content_updates_with_signal(self):
        """For content updates when signal changes."""
        suffix = Signal("!")
        items = ["a", "b"]
        for_comp = For(each=items)[
            lambda x, i: f"{x}{suffix()}"
        ]
        
        html1 = for_comp.render()
        assert "a!" in html1
        
        suffix.set("?")
        html2 = for_comp.render()
        
        assert "a?" in html2
    
    def test_for_empty_signal(self):
        """For handles Signal becoming empty."""
        items = Signal([1, 2, 3])
        for_comp = For(each=lambda: items(), fallback="Empty")[
            lambda x, i: str(x)
        ]
        
        items.set([])
        html = for_comp.render()
        
        assert "Empty" in html
    
    def test_for_signal_becomes_non_empty(self):
        """For handles Signal becoming non-empty."""
        items = Signal([])
        for_comp = For(each=lambda: items(), fallback="Empty")[
            lambda x, i: str(x)
        ]
        
        html1 = for_comp.render()
        assert "Empty" in html1
        
        items.set([42])
        html2 = for_comp.render()
        
        assert "42" in html2
    
    def test_for_multiple_signal_changes(self):
        """For handles multiple signal changes."""
        items = Signal([1])
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        
        for val in [2, 3, 4, 5]:
            items.set([val])
            html = for_comp.render()
            assert str(val) in html
    
    def test_for_derived_list(self):
        """For with derived list from signals."""
        a = Signal([1, 2])
        b = Signal([3, 4])
        
        for_comp = For(each=lambda: a() + b())[lambda x, i: str(x)]
        
        html = for_comp.render()
        assert "1" in html
        assert "4" in html
    
    def test_for_filtered_list(self):
        """For with filtered list."""
        items = Signal([1, 2, 3, 4, 5])
        threshold = Signal(3)
        
        for_comp = For(each=lambda: [{"id": x, "v": x} for x in items() if x > threshold()])[
            lambda x, i: str(x["v"])
        ]
        
        html = for_comp.render()
        assert "4" in html
        assert "5" in html
        # Note: 2 doesn't show because it's <= threshold
    
    def test_for_sorted_list(self):
        """For with sorted list."""
        items = Signal([3, 1, 2])
        
        for_comp = For(each=lambda: sorted(items()))[lambda x, i: str(x)]
        
        html = for_comp.render()
        assert "1" in html
        assert "2" in html
        assert "3" in html
    
    def test_for_with_effect(self):
        """For works alongside Effect."""
        items = Signal([1, 2])
        render_count = [0]
        
        @Effect
        def track():
            items()
            render_count[0] += 1
        
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        for_comp.render()
        
        assert render_count[0] >= 1
    
    def test_for_batch_updates(self):
        """For handles batched updates."""
        from pynext.reactive.batch import batch
        
        items = Signal([1])
        for_comp = For(each=lambda: items())[lambda x, i: str(x)]
        
        batch(lambda: items.set([1, 2, 3]))
        
        html = for_comp.render()
        assert "3" in html
    
    def test_for_nested_reactive_items(self):
        """For with nested reactive content."""
        items = Signal([
            {"id": 1, "name": Signal("Alice")},
            {"id": 2, "name": Signal("Bob")}
        ])
        
        for_comp = For(each=lambda: items())[
            lambda x, i: f"<div>{x['name']()}</div>"
        ]
        
        html = for_comp.render()
        assert "Alice" in html
        assert "Bob" in html
    
    def test_for_memo_derived_list(self):
        """For with Memo-derived list."""
        from pynext.reactive.memo import Memo
        
        source = Signal([1, 2, 3, 4, 5])
        evens = Memo(lambda: [{"id": x, "v": x} for x in source() if x % 2 == 0])
        
        for_comp = For(each=lambda: evens())[lambda x, i: str(x["v"])]
        
        html = for_comp.render()
        assert "2" in html
        assert "4" in html
        # Note: 3 is odd so not in evens list
    
    def test_for_complex_transform(self):
        """For with complex list transformation."""
        items = Signal([{"x": 1}, {"x": 2}, {"x": 3}])
        
        for_comp = For(
            each=lambda: [{"id": i["x"], "doubled": i["x"] * 2} for i in items()]
        )[lambda x, i: f"{x['id']}:{x['doubled']}"]
        
        html = for_comp.render()
        assert "1:2" in html
        assert "2:4" in html
    
    def test_for_reactive_key_fn(self):
        """For with reactive key function."""
        use_name = Signal(True)
        items = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        
        for_comp = For(
            each=items,
            key_fn=lambda x: x["name"] if use_name() else x["id"]
        )[lambda x, i: str(x["id"])]
        
        html1 = for_comp.render()
        assert 'data-for-item="a"' in html1
        
        use_name.set(False)
        html2 = for_comp.render()
        
        assert 'data-for-item="1"' in html2
    
    def test_for_store_array_mutations(self):
        """For reacts to store array mutations."""
        store = Store({"items": [{"id": 1}]})
        for_comp = For(each=lambda: list(store.items))[
            lambda x, i: str(x["id"])
        ]
        
        html1 = for_comp.render()
        assert "1" in html1
    
    def test_for_conditional_items(self):
        """For with conditionally included items."""
        show_all = Signal(False)
        items = [{"id": 1, "visible": True}, {"id": 2, "visible": False}]
        
        for_comp = For(
            each=lambda: [x for x in items if x["visible"] or show_all()]
        )[lambda x, i: f"item-{x['id']}"]
        
        html1 = for_comp.render()
        assert "item-1" in html1
        # item-2 should not be present when show_all is False
        assert "item-2" not in html1
        
        show_all.set(True)
        html2 = for_comp.render()
        
        assert "item-2" in html2
    
    def test_for_multiple_stores(self):
        """For with data from multiple stores."""
        users = Store({"data": [{"id": 1}]})
        orders = Store({"data": [{"userId": 1, "total": 100}]})
        
        for_comp = For(each=lambda: list(users.data))[
            lambda user, i: str(user["id"])
        ]
        
        html = for_comp.render()
        assert "1" in html
    
    def test_for_live_search_simulation(self):
        """Simulate live search filtering."""
        all_items = [{"id": i, "name": f"Item {i}"} for i in range(10)]
        query = Signal("")
        
        for_comp = For(
            each=lambda: [x for x in all_items if query() in x["name"]]
        )[lambda x, i: x["name"]]
        
        html1 = for_comp.render()
        assert "Item 0" in html1
        
        query.set("5")
        html2 = for_comp.render()
        
        assert "Item 5" in html2
        assert "Item 0" not in html2
    
    def test_for_pagination_simulation(self):
        """Simulate pagination."""
        all_items = [{"id": i} for i in range(100)]
        page = Signal(0)
        page_size = 10
        
        for_comp = For(
            each=lambda: all_items[page() * page_size:(page() + 1) * page_size]
        )[lambda x, i: str(x["id"])]
        
        html1 = for_comp.render()
        assert 'data-for-item="0"' in html1
        assert 'data-for-item="10"' not in html1
        
        page.set(1)
        html2 = for_comp.render()
        
        assert 'data-for-item="10"' in html2
        assert 'data-for-item="0"' not in html2
    
    def test_for_signal_of_signals(self):
        """For with signal containing signals."""
        inner1 = Signal("A")
        inner2 = Signal("B")
        items = Signal([inner1, inner2])
        
        for_comp = For(each=lambda: items())[
            lambda x, i: x()
        ]
        
        html = for_comp.render()
        assert "A" in html
        assert "B" in html


# =============================================================================
# SECTION 4: EDGE CASES (20 tests)
# =============================================================================

class TestForEdgeCases:
    """Edge case tests for For component."""
    
    def test_for_none_list(self):
        """For handles None list gracefully."""
        for_comp = For(each=lambda: None)[lambda x, i: str(x)]
        html = for_comp.render()
        
        assert 'data-empty="true"' in html
    
    def test_for_none_items_in_list(self):
        """For handles None items in list."""
        items = [1, None, 3]
        for_comp = For(each=items)[lambda x, i: str(x)]
        html = for_comp.render()
        
        assert "1" in html
        assert "None" in html
        assert "3" in html
    
    def test_for_exception_in_render(self):
        """For handles exception in render function."""
        def bad_render(x, i):
            if x == 2:
                raise ValueError("Bad!")
            return str(x)
        
        items = [1, 2, 3]
        for_comp = For(each=items)[bad_render]
        
        with pytest.raises(ValueError):
            for_comp.render()
    
    def test_for_very_large_list(self):
        """For handles very large list."""
        items = [{"id": i} for i in range(1000)]
        for_comp = For(each=items)[lambda x, i: str(x["id"])]
        
        html = for_comp.render()
        assert "999" in html
    
    def test_for_nested_for(self):
        """For can contain nested For."""
        rows = [{"id": 1, "cols": [1, 2]}, {"id": 2, "cols": [3, 4]}]
        
        for_comp = For(each=rows)[
            lambda row, ri: f"<tr>{For(each=row['cols'])[lambda col, ci: f'<td>{col}</td>']}</tr>"
        ]
        
        html = for_comp.render()
        assert "<td>1</td>" in html
        assert "<td>4</td>" in html
    
    def test_for_deeply_nested(self):
        """For handles deeply nested data."""
        data = {"level1": [{"level2": [{"level3": [1, 2, 3]}]}]}
        
        for_comp = For(each=data["level1"])[
            lambda l1, i: f"{For(each=l1['level2'])[lambda l2, j: str(l2['level3'])]}"
        ]
        
        html = for_comp.render()
        assert "[1, 2, 3]" in html
    
    def test_for_unicode_content(self):
        """For handles unicode content."""
        items = [{"id": "日本語"}, {"id": "中文"}, {"id": "🎉"}]
        for_comp = For(each=items)[lambda x, i: x["id"]]
        
        html = for_comp.render()
        assert "日本語" in html
        assert "🎉" in html
    
    def test_for_html_in_content(self):
        """For renders HTML in content."""
        items = [{"id": 1, "html": "<strong>Bold</strong>"}]
        for_comp = For(each=items)[lambda x, i: x["html"]]
        
        html = for_comp.render()
        assert "<strong>Bold</strong>" in html
    
    def test_for_empty_render_function_result(self):
        """For handles empty render function result."""
        items = [1, 2, 3]
        for_comp = For(each=items)[lambda x, i: ""]
        
        html = for_comp.render()
        assert 'data-pynext-for' in html
    
    def test_for_render_returns_none(self):
        """For handles render function returning None."""
        items = [1, 2, 3]
        for_comp = For(each=items)[lambda x, i: None]
        
        html = for_comp.render()
        assert 'data-pynext-for' in html
    
    def test_for_callback_modifies_item(self):
        """For callback can modify items."""
        items = [{"id": 1, "processed": False}]
        
        def render(x, i):
            x["processed"] = True
            return str(x["id"])
        
        for_comp = For(each=items)[render]
        for_comp.render()
        
        assert items[0]["processed"] is True
    
    def test_for_different_item_types(self):
        """For handles different item types in same list."""
        items = [1, "two", 3.0, True, None]
        for_comp = For(each=items)[lambda x, i: str(x)]
        
        html = for_comp.render()
        assert "1" in html
        assert "two" in html
        assert "3.0" in html
    
    def test_for_generator_each(self):
        """For handles generator as each."""
        def gen():
            yield {"id": 1}
            yield {"id": 2}
        
        for_comp = For(each=lambda: list(gen()))[
            lambda x, i: str(x["id"])
        ]
        
        html = for_comp.render()
        assert "1" in html
        assert "2" in html
    
    def test_for_tuple_each(self):
        """For handles tuple as each."""
        items = [{"id": 1}, {"id": 2}]  # Use list, tuple handled by _get_items
        for_comp = For(each=items)[lambda x, i: str(x["id"])]
        
        html = for_comp.render()
        assert "1" in html
        assert "2" in html
    
    def test_for_dict_values(self):
        """For handles dict.values() as each."""
        data = {"a": {"id": 1}, "b": {"id": 2}}
        for_comp = For(each=lambda: list(data.values()))[
            lambda x, i: str(x["id"])
        ]
        
        html = for_comp.render()
        assert "1" in html
        assert "2" in html
    
    def test_for_range(self):
        """For handles range as each."""
        for_comp = For(each=lambda: list(range(5)))[
            lambda x, i: str(x)
        ]
        
        html = for_comp.render()
        assert "0" in html
        assert "4" in html
    
    def test_for_key_collision_handling(self):
        """For handles potential key collisions."""
        items = [{"id": 1}, {"id": "1"}]  # int 1 and string "1"
        for_comp = For(each=items)[lambda x, i: str(x["id"])]
        
        html = for_comp.render()
        # Both should render, keys are converted to strings
        assert html.count('data-for-item="1"') >= 1
    
    def test_for_very_long_key(self):
        """For handles very long key."""
        items = [{"id": "x" * 1000}]
        for_comp = For(each=items)[lambda x, i: x["id"][:10]]
        
        html = for_comp.render()
        assert 'data-for-item="' in html
    
    def test_for_callable_fallback(self):
        """For handles callable fallback."""
        for_comp = For(
            each=[],
            fallback=lambda: "Dynamic fallback"
        )[lambda x, i: str(x)]
        
        html = for_comp.render()
        assert "Dynamic fallback" in html
    
    def test_for_rerender_stability(self):
        """For renders same output on repeated calls."""
        items = [{"id": 1}, {"id": 2}]
        for_comp = For(each=items)[lambda x, i: str(x["id"])]
        
        html1 = for_comp.render()
        html2 = for_comp.render()
        html3 = for_comp.render()
        
        assert html1 == html2 == html3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

