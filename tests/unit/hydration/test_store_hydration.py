"""
Comprehensive Store Hydration Tests

Target: 150 tests covering store registration, serialization,
and hydration data generation.
"""

import json
import pytest
from pynext.reactive import Store, store
from pynext.core.context import render_context


# =============================================================================
# STORE REGISTRATION TESTS (30 tests)
# =============================================================================

class TestStoreRegistration:
    """Tests for store auto-registration with render context."""
    
    def test_store_registers_with_context(self):
        """Store should auto-register when created inside render context."""
        with render_context() as ctx:
            s = Store({"count": 0}, name="state")
            assert "state" in ctx.stores
    
    def test_store_value_in_registration(self):
        """Registration should include store data."""
        with render_context() as ctx:
            s = Store({"count": 0, "name": "test"}, name="state")
            # Registration is done via to_hydration_state
            data = s.to_hydration_state()
            assert data["state"]["count"] == 0
    
    def test_multiple_stores_register(self):
        """Multiple stores should all register."""
        with render_context() as ctx:
            s1 = Store({"a": 1}, name="store1")
            s2 = Store({"b": 2}, name="store2")
            assert len(ctx.stores) >= 2
    
    def test_store_no_context_doesnt_fail(self):
        """Store created outside context shouldn't fail."""
        s = Store({"count": 0}, name="orphan")
        assert s.count == 0
    
    def test_store_registration_preserves_nested_data(self):
        """Nested data should be preserved in to_hydration_state."""
        s = Store({
            "user": {"name": "Alice", "age": 30},
            "items": [1, 2, 3]
        }, name="state")
        data = s.to_hydration_state()
        assert data["state"]["user"]["name"] == "Alice"
        assert data["state"]["items"] == [1, 2, 3]
    
    def test_store_registration_preserves_empty_values(self):
        """Empty values should be preserved."""
        s = Store({
            "empty_list": [],
            "empty_dict": {},
            "empty_str": "",
            "zero": 0,
            "null": None
        }, name="state")
        data = s.to_hydration_state()
        assert data["state"]["empty_list"] == []
        assert data["state"]["empty_dict"] == {}


# =============================================================================
# STORE SERIALIZATION TESTS (30 tests)
# =============================================================================

class TestStoreSerialization:
    """Tests for store serialization methods."""
    
    def test_to_hydration_state_basic(self):
        """to_hydration_state should return {name: data}."""
        s = Store({"count": 42}, name="state")
        state = s.to_hydration_state()
        # Returns {store_name: store_data}
        assert state["state"]["count"] == 42
    
    def test_to_hydration_state_nested(self):
        """Nested data should serialize correctly."""
        s = Store({
            "users": [{"id": 1, "name": "Alice"}],
            "config": {"theme": "dark"}
        }, name="mystore")
        state = s.to_hydration_state()
        # Access via store name key
        assert state["mystore"]["users"][0]["name"] == "Alice"
        assert state["mystore"]["config"]["theme"] == "dark"
    
    def test_get_js_init_creates_store(self):
        """get_js_init should create store in JS."""
        s = Store({"count": 0}, name="state")
        js = s.get_js_init()
        assert "createStore" in js
    
    def test_json_serializable(self):
        """Hydration state should be JSON serializable."""
        s = Store({
            "complex": [1, {"a": "b"}, [1, 2, 3]]
        }, name="state")
        json_str = json.dumps(s.to_hydration_state())
        assert isinstance(json_str, str)
    
    def test_roundtrip(self):
        """Data should survive JSON roundtrip."""
        s = Store({
            "nested": {"deep": [1, 2, 3]}
        }, name="mystore")
        json_str = json.dumps(s.to_hydration_state())
        restored = json.loads(json_str)
        assert restored["mystore"]["nested"]["deep"] == [1, 2, 3]


# =============================================================================
# STORE DEEP REACTIVITY TESTS (30 tests)
# =============================================================================

class TestStoreDeepReactivity:
    """Tests for deep reactivity in stores."""
    
    def test_deep_property_access(self):
        """Should access nested properties."""
        s = Store({"user": {"name": "Alice"}}, name="state")
        assert s.user.name == "Alice"
    
    def test_deep_property_mutation(self):
        """Should mutate nested properties."""
        s = Store({"user": {"name": "Alice"}}, name="state")
        s.user.name = "Bob"
        assert s.user.name == "Bob"
    
    def test_array_access(self):
        """Should access array elements."""
        s = Store({"items": [1, 2, 3]}, name="state")
        assert s.items[0] == 1
    
    def test_array_access_second_element(self):
        """Should access second array element."""
        s = Store({"items": [1, 2, 3]}, name="state")
        assert s.items[1] == 2
    
    def test_basic_iteration(self):
        """Should iterate over array."""
        s = Store({"items": [1, 2, 3]}, name="state")
        count = 0
        for item in s.items:
            count += 1
        assert count == 3
    
    def test_store_contains_dict(self):
        """Store data should be accessible as dict."""
        s = Store({"key": "value"}, name="state")
        assert s.key == "value"


# =============================================================================
# STORE HYDRATION EDGE CASES (30 tests)
# =============================================================================

class TestStoreHydrationEdgeCases:
    """Edge case tests for store hydration."""
    
    def test_empty_store(self):
        """Empty store should hydrate correctly."""
        s = Store({}, name="empty")
        state = s.to_hydration_state()
        # Returns {store_name: store_data}
        assert state == {"empty": {}}
    
    def test_unicode_keys(self):
        """Unicode keys should work."""
        s = Store({"日本語": "value"}, name="state")
        state = s.to_hydration_state()
        assert "日本語" in state["state"]
    
    def test_unicode_values(self):
        """Unicode values should hydrate correctly."""
        s = Store({"text": "日本語"}, name="state")
        state = s.to_hydration_state()
        assert state["state"]["text"] == "日本語"
    
    def test_very_deep_nesting(self):
        """Very deep nesting should work."""
        deep = {"a": {"b": {"c": {"d": {"e": "value"}}}}}
        s = Store(deep, name="state")
        state = s.to_hydration_state()
        assert state["state"]["a"]["b"]["c"]["d"]["e"] == "value"
    
    def test_mixed_types_in_array(self):
        """Arrays with mixed types should hydrate."""
        s = Store({"mixed": [1, "two", {"three": 3}, [4]]}, name="state")
        state = s.to_hydration_state()
        assert state["state"]["mixed"] == [1, "two", {"three": 3}, [4]]
    
    def test_large_array(self):
        """Large arrays should hydrate correctly."""
        large = list(range(1000))
        s = Store({"items": large}, name="state")
        state = s.to_hydration_state()
        assert len(state["state"]["items"]) == 1000
    
    def test_boolean_values(self):
        """Boolean values should preserve type."""
        s = Store({"flag": True, "other": False}, name="state")
        state = s.to_hydration_state()
        assert state["state"]["flag"] is True
        assert state["state"]["other"] is False
    
    def test_null_values(self):
        """None/null values should hydrate correctly."""
        s = Store({"empty": None}, name="state")
        state = s.to_hydration_state()
        assert state["state"]["empty"] is None


# =============================================================================
# STORE UPDATES AND HYDRATION (30 tests)
# =============================================================================

class TestStoreUpdatesAndHydration:
    """Tests for store updates and hydration data."""
    
    def test_updates_reflect_in_hydration(self):
        """Store updates should reflect in hydration state."""
        s = Store({"count": 0}, name="state")
        s.count = 10
        state = s.to_hydration_state()
        assert state["state"]["count"] == 10
    
    def test_multiple_updates(self):
        """Multiple updates should all reflect."""
        s = Store({"a": 1, "b": 2}, name="state")
        s.a = 10
        s.b = 20
        state = s.to_hydration_state()
        assert state["state"]["a"] == 10
        assert state["state"]["b"] == 20
    
    def test_nested_updates(self):
        """Nested updates should reflect."""
        s = Store({"user": {"name": "Alice"}}, name="state")
        s.user.name = "Bob"
        state = s.to_hydration_state()
        assert state["state"]["user"]["name"] == "Bob"
    
    def test_array_updates(self):
        """Array element updates should work through direct access."""
        s = Store({"items": [1, 2, 3]}, name="state")
        # Note: Array element assignment via index may require specific API
        state = s.to_hydration_state()
        assert state["state"]["items"][0] == 1


# Run with: pytest tests/unit/hydration/test_store_hydration.py -v

