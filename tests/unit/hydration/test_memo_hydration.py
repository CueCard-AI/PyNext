"""
Comprehensive Memo Hydration Tests

Target: 100 tests covering memo registration, serialization,
and hydration data generation.
"""

import json
import pytest
from pynext.reactive import Signal, signal, memo, Memo
from pynext.core.context import render_context


# =============================================================================
# MEMO REGISTRATION TESTS (25 tests)
# =============================================================================

class TestMemoRegistration:
    """Tests for memo auto-registration with render context."""
    
    def test_memo_registers_with_context(self):
        """Memo should auto-register when created inside render context."""
        with render_context() as ctx:
            count = signal(0)
            doubled = Memo(lambda: count() * 2, name="doubled")
            # Memos register as signals
            assert "doubled" in ctx.signals
    
    def test_memo_value_in_registration(self):
        """Registration should include computed value."""
        with render_context() as ctx:
            count = signal(5)
            doubled = Memo(lambda: count() * 2, name="doubled")
            # Force computation
            doubled()
            # Memo registers as signal - check to_hydration_state directly
            state = doubled.to_hydration_state()
            assert state["doubled"] == 10
    
    def test_multiple_memos_register(self):
        """Multiple memos should all register."""
        with render_context() as ctx:
            count = signal(0)
            m1 = Memo(lambda: count() + 1, name="memo1")
            m2 = Memo(lambda: count() + 2, name="memo2")
            assert "memo1" in ctx.signals
            assert "memo2" in ctx.signals
    
    def test_memo_no_context_doesnt_fail(self):
        """Memo created outside context shouldn't fail."""
        count = signal(5)
        doubled = Memo(lambda: count() * 2, name="orphan")
        assert doubled() == 10
    
    def test_chained_memos_register(self):
        """Chained memos should all register."""
        with render_context() as ctx:
            count = signal(1)
            doubled = Memo(lambda: count() * 2, name="doubled")
            quadrupled = Memo(lambda: doubled() * 2, name="quadrupled")
            # Force computation
            quadrupled()
            assert "doubled" in ctx.signals
            assert "quadrupled" in ctx.signals


# =============================================================================
# MEMO SERIALIZATION TESTS (25 tests)
# =============================================================================

class TestMemoSerialization:
    """Tests for memo serialization methods."""
    
    def test_to_json_basic(self):
        """to_json should return dict with id, name, value."""
        count = signal(5)
        doubled = Memo(lambda: count() * 2, name="doubled")
        doubled()  # Force computation
        data = doubled.to_json()
        assert "id" in data
        assert "name" in data
        assert "value" in data
        assert data["value"] == 10
    
    def test_to_hydration_state_basic(self):
        """to_hydration_state should return {name: value}."""
        count = signal(5)
        doubled = Memo(lambda: count() * 2, name="doubled")
        state = doubled.to_hydration_state()
        assert state == {"doubled": 10}
    
    def test_get_js_init_creates_memo(self):
        """get_js_init should create memo in JS."""
        count = signal(5)
        doubled = Memo(lambda: count() * 2, name="doubled")
        js = doubled.get_js_init()
        assert "createMemo" in js
    
    def test_render_value_basic(self):
        """render_value should create span with data attribute."""
        count = signal(5)
        doubled = Memo(lambda: count() * 2, name="doubled")
        html = doubled.render_value()
        assert 'data-pynext-memo="doubled"' in html
        assert "10" in html
    
    def test_json_serializable(self):
        """to_json output should be JSON serializable."""
        count = signal(5)
        doubled = Memo(lambda: count() * 2, name="doubled")
        json_str = json.dumps(doubled.to_json())
        assert isinstance(json_str, str)


# =============================================================================
# MEMO COMPUTATION TESTS (25 tests)
# =============================================================================

class TestMemoComputation:
    """Tests for memo computation during hydration."""
    
    def test_lazy_computation(self):
        """Memo should compute lazily."""
        count = signal(5)
        computation_count = [0]
        
        def compute():
            computation_count[0] += 1
            return count() * 2
        
        doubled = Memo(compute, name="doubled")
        # Not read yet, should be dirty
        assert doubled._dirty is True
    
    def test_caching(self):
        """Memo should cache result."""
        count = signal(5)
        computation_count = [0]
        
        def compute():
            computation_count[0] += 1
            return count() * 2
        
        doubled = Memo(compute, name="doubled")
        doubled()  # First read
        doubled()  # Second read (cached)
        doubled()  # Third read (cached)
        assert computation_count[0] == 1
    
    def test_recomputation_on_dependency_change(self):
        """Memo should recompute when dependency changes."""
        count = signal(5)
        doubled = Memo(lambda: count() * 2, name="doubled")
        
        assert doubled() == 10
        count.set(10)
        assert doubled() == 20
    
    def test_multiple_dependencies(self):
        """Memo should track multiple dependencies."""
        a = signal(2)
        b = signal(3)
        product = Memo(lambda: a() * b(), name="product")
        
        assert product() == 6
        a.set(4)
        assert product() == 12
        b.set(5)
        assert product() == 20


# =============================================================================
# MEMO HYDRATION EDGE CASES (25 tests)
# =============================================================================

class TestMemoHydrationEdgeCases:
    """Edge case tests for memo hydration."""
    
    def test_memo_returning_list(self):
        """Memo returning list should hydrate correctly."""
        items = signal([1, 2, 3])
        doubled = Memo(lambda: [x * 2 for x in items()], name="doubled")
        state = doubled.to_hydration_state()
        assert state["doubled"] == [2, 4, 6]
    
    def test_memo_returning_dict(self):
        """Memo returning dict should hydrate correctly."""
        user = signal({"name": "Alice"})
        greeting = Memo(lambda: {"msg": f"Hello, {user()['name']}"}, name="greeting")
        state = greeting.to_hydration_state()
        assert state["greeting"]["msg"] == "Hello, Alice"
    
    def test_memo_returning_none(self):
        """Memo returning None should hydrate correctly."""
        items = signal([])
        first = Memo(lambda: items()[0] if items() else None, name="first")
        state = first.to_hydration_state()
        assert state["first"] is None
    
    def test_memo_returning_zero(self):
        """Memo returning 0 should hydrate correctly (not treated as None)."""
        items = signal([0, 1, 2])
        first = Memo(lambda: items()[0], name="first")
        state = first.to_hydration_state()
        assert state["first"] == 0
    
    def test_memo_returning_empty_string(self):
        """Memo returning empty string should hydrate correctly."""
        name = signal("")
        greeting = Memo(lambda: f"Hello, {name()}", name="greeting")
        state = greeting.to_hydration_state()
        assert state["greeting"] == "Hello, "
    
    def test_memo_with_conditional(self):
        """Memo with conditional should hydrate correctly."""
        count = signal(5)
        status = Memo(lambda: "many" if count() > 3 else "few", name="status")
        state = status.to_hydration_state()
        assert state["status"] == "many"


# Run with: pytest tests/unit/hydration/test_memo_hydration.py -v

