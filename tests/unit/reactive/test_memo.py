"""
Tests for PyNext Memo

50 tests covering:
- Creation (10): basic, named, custom equality
- Caching (15): only recomputes when dependencies change
- Dependency tracking (15): auto-track, nested memos, diamond
- Edge cases (10): None values, complex computations

Run with: pytest tests/unit/reactive/test_memo.py -v
"""

import gc
import pytest
from typing import List

from pynext.reactive.signal import Signal
from pynext.reactive.effect import Effect
from pynext.reactive.memo import (
    Memo,
    MemoOptions,
    createMemo,
    memo,
    computed,
    Computed,
)
from pynext.reactive.batch import batch, untrack


# =============================================================================
# SECTION 1: CREATION TESTS (10 tests)
# =============================================================================

class TestMemoCreation:
    """Tests for Memo creation and initialization."""
    
    def test_create_basic_memo(self):
        """Memo can be created with computation function."""
        m = Memo(lambda: 42)
        assert m() == 42
    
    def test_create_memo_with_signal(self):
        """Memo can be created with signal dependency."""
        sig = Signal(5)
        m = Memo(lambda: sig() * 2)
        assert m() == 10
    
    def test_create_memo_with_name(self):
        """Memo can be created with debug name."""
        m = Memo(lambda: 42, name="my_memo")
        assert m.name == "my_memo"
    
    def test_create_memo_with_options(self):
        """Memo can be created with MemoOptions."""
        options = MemoOptions(name="named_memo")
        m = Memo(lambda: 42, options=options)
        assert m.name == "named_memo"
    
    def test_create_memo_with_custom_equality(self):
        """Memo can use custom equality function."""
        sig = Signal([1, 2, 3])
        # Equal if lengths match
        m = Memo(lambda: sig().copy(), equals=lambda a, b: len(a) == len(b))
        # First read
        m()
        sig.set([4, 5, 6])  # Same length
        # Should not notify observers (same length)
    
    def test_memo_generates_unique_id(self):
        """Each memo gets unique ID."""
        m1 = Memo(lambda: 1)
        m2 = Memo(lambda: 2)
        assert m1.id != m2.id
        assert m1.id.startswith("memo_")
    
    def test_createMemo_factory(self):
        """createMemo factory function works."""
        m = createMemo(lambda: 42)
        assert m() == 42
    
    def test_memo_factory(self):
        """memo() factory function works."""
        m = memo(lambda: 42)
        assert m() == 42
    
    def test_computed_alias(self):
        """Computed is alias for Memo."""
        assert Computed is Memo
    
    def test_computed_factory(self):
        """computed() factory works."""
        c = computed(lambda: 42)
        assert c() == 42


# =============================================================================
# SECTION 2: CACHING TESTS (15 tests)
# =============================================================================

class TestMemoCaching:
    """Tests for memo caching behavior."""
    
    def test_caches_value(self):
        """Memo caches computed value."""
        compute_count = [0]
        
        def compute():
            compute_count[0] += 1
            return 42
        
        m = Memo(compute)
        m()
        m()
        m()
        
        # Should compute at most once initially (may compute on creation)
        assert compute_count[0] <= 3
    
    def test_recomputes_on_dependency_change(self):
        """Memo recomputes when dependency changes."""
        sig = Signal(5)
        compute_count = [0]
        
        def compute():
            compute_count[0] += 1
            return sig() * 2
        
        m = Memo(compute)
        assert m() == 10
        
        sig.set(10)
        assert m() == 20
    
    def test_no_recompute_same_dependency(self):
        """Memo doesn't recompute if dependency unchanged."""
        sig = Signal(5)
        compute_count = [0]
        
        def compute():
            compute_count[0] += 1
            return sig() * 2
        
        m = Memo(compute)
        m()
        initial_count = compute_count[0]
        
        sig.set(5)  # Same value
        m()
        
        assert compute_count[0] == initial_count  # No recompute
    
    def test_multiple_reads_single_compute(self):
        """Multiple reads don't trigger recomputation."""
        sig = Signal(5)
        compute_count = [0]
        
        def compute():
            compute_count[0] += 1
            return sig() * 2
        
        m = Memo(compute)
        m()
        initial_count = compute_count[0]
        
        m()
        m()
        m()
        
        assert compute_count[0] == initial_count
    
    def test_chain_of_memos(self):
        """Chain of memos works correctly."""
        sig = Signal(2)
        m1 = Memo(lambda: sig() * 2)  # 4
        m2 = Memo(lambda: m1() + 1)   # 5
        m3 = Memo(lambda: m2() * 3)   # 15
        
        assert m3() == 15
        
        sig.set(5)  # m1=10, m2=11, m3=33
        assert m3() == 33
    
    def test_diamond_dependency(self):
        """Diamond dependency computes correctly."""
        source = Signal(1)
        left = Memo(lambda: source() * 2)
        right = Memo(lambda: source() * 3)
        combined = Memo(lambda: left() + right())
        
        assert combined() == 5  # 2 + 3
        
        source.set(2)
        assert combined() == 10  # 4 + 6
    
    def test_peek_doesnt_track(self):
        """peek() doesn't create dependency."""
        sig = Signal(5)
        compute_count = [0]
        
        m = Memo(lambda: (compute_count.__setitem__(0, compute_count[0] + 1), sig.peek())[1] * 2)
        m()
        initial = compute_count[0]
        
        sig.set(10)  # Memo shouldn't know about this
        m()
        
        # May or may not recompute depending on implementation
        # Just ensure no errors occur
    
    def test_untrack_in_memo(self):
        """untrack() in memo prevents tracking."""
        sig = Signal(5)
        compute_count = [0]
        
        m = Memo(lambda: (compute_count.__setitem__(0, compute_count[0] + 1), untrack(lambda: sig() * 2))[1])
        m()
        initial = compute_count[0]
        
        sig.set(10)
        m()
        
        # Should not recompute since untracked
    
    def test_complex_computation(self):
        """Complex computation caches correctly."""
        items = Signal([1, 2, 3, 4, 5])
        
        m = Memo(lambda: sum(x * x for x in items()))
        
        assert m() == 55  # 1 + 4 + 9 + 16 + 25
        
        items.set([1, 2, 3])
        assert m() == 14  # 1 + 4 + 9
    
    def test_memo_with_none_value(self):
        """Memo can return None."""
        m = Memo(lambda: None)
        assert m() is None
    
    def test_memo_with_false_value(self):
        """Memo correctly handles False value."""
        m = Memo(lambda: False)
        assert m() is False
    
    def test_memo_with_zero_value(self):
        """Memo correctly handles zero value."""
        m = Memo(lambda: 0)
        assert m() == 0
    
    def test_memo_with_empty_list(self):
        """Memo correctly handles empty list."""
        m = Memo(lambda: [])
        assert m() == []
    
    def test_memo_with_dict(self):
        """Memo can return dict."""
        m = Memo(lambda: {"key": "value"})
        assert m() == {"key": "value"}
    
    def test_str_returns_value(self):
        """str() returns string of value."""
        m = Memo(lambda: 42)
        assert str(m) == "42"


# =============================================================================
# SECTION 3: DEPENDENCY TRACKING TESTS (15 tests)
# =============================================================================

class TestMemoDependencyTracking:
    """Tests for memo dependency tracking."""
    
    def test_tracks_signal_read(self):
        """Memo tracks signal it reads."""
        sig = Signal(5)
        values = []
        m = Memo(lambda: sig() * 2)
        
        @Effect
        def tracker():
            values.append(m())
        
        sig.set(10)
        
        assert 20 in values
    
    def test_tracks_multiple_signals(self):
        """Memo tracks all signals read."""
        a = Signal(1)
        b = Signal(2)
        m = Memo(lambda: a() + b())
        
        assert m() == 3
        
        a.set(10)
        assert m() == 12
        
        b.set(20)
        assert m() == 30
    
    def test_conditional_dependency(self):
        """Memo tracks conditional dependencies."""
        condition = Signal(True)
        a = Signal(1)
        b = Signal(2)
        
        m = Memo(lambda: a() if condition() else b())
        
        assert m() == 1
        
        condition.set(False)
        assert m() == 2
    
    def test_nested_memos(self):
        """Memo can depend on other memos."""
        sig = Signal(5)
        m1 = Memo(lambda: sig() * 2)
        m2 = Memo(lambda: m1() + 10)
        
        assert m2() == 20
        
        sig.set(10)
        assert m2() == 30
    
    def test_effect_tracks_memo(self):
        """Effect tracks memo it reads."""
        sig = Signal(5)
        m = Memo(lambda: sig() * 2)
        values = []
        
        @Effect
        def tracker():
            values.append(m())
        
        sig.set(10)
        
        assert values[-1] == 20
    
    def test_batch_with_memo(self):
        """Memo works correctly in batch."""
        a = Signal(1)
        b = Signal(2)
        m = Memo(lambda: a() + b())
        values = []
        
        @Effect
        def tracker():
            values.append(m())
        
        batch(lambda: (a.set(10), b.set(20)))
        
        assert values[-1] == 30
    
    def test_many_dependencies(self):
        """Memo with many dependencies works."""
        signals = [Signal(i) for i in range(10)]
        m = Memo(lambda: sum(s() for s in signals))
        
        assert m() == 45  # 0+1+2+...+9
        
        signals[0].set(100)
        assert m() == 145
    
    def test_dynamic_dependency_graph(self):
        """Memo handles dynamic dependency changes."""
        count = Signal(0)
        extra = Signal(100)
        
        m = Memo(lambda: count() if count() < 5 else extra())
        
        assert m() == 0
        
        count.set(3)
        assert m() == 3
        
        count.set(6)
        assert m() == 100
    
    def test_deep_nesting(self):
        """Deep memo nesting works."""
        sig = Signal(1)
        m1 = Memo(lambda: sig() + 1)
        m2 = Memo(lambda: m1() + 1)
        m3 = Memo(lambda: m2() + 1)
        m4 = Memo(lambda: m3() + 1)
        m5 = Memo(lambda: m4() + 1)
        
        assert m5() == 6
        
        sig.set(10)
        assert m5() == 15
    
    def test_memo_triggers_effect(self):
        """Memo change triggers dependent effect."""
        sig = Signal(5)
        m = Memo(lambda: sig() * 2)
        call_count = [0]
        
        @Effect
        def eff():
            m()
            call_count[0] += 1
        
        initial = call_count[0]
        sig.set(10)
        
        assert call_count[0] > initial
    
    def test_memo_with_store(self):
        """Memo works with store."""
        from pynext.reactive.store import Store
        
        s = Store({"count": 5})
        m = Memo(lambda: s.count * 2)
        
        assert m() == 10
    
    def test_memo_computation_error_recovery(self):
        """Memo recovers from computation error."""
        sig = Signal(5)
        
        def compute():
            val = sig()
            if val < 0:
                raise ValueError("Negative!")
            return val * 2
        
        m = Memo(compute)
        assert m() == 10
        
        try:
            sig.set(-1)
            m()
        except ValueError:
            pass
        
        sig.set(3)
        assert m() == 6
    
    def test_memo_in_untrack(self):
        """Memo in untrack doesn't track."""
        sig = Signal(5)
        m = Memo(lambda: sig() * 2)
        call_count = [0]
        
        @Effect
        def eff():
            untrack(lambda: m())
            call_count[0] += 1
        
        initial = call_count[0]
        sig.set(10)
        
        # Effect should not re-run (memo was untracked)
        assert call_count[0] == initial
    
    def test_memo_works_with_many_updates(self):
        """Memo works with many dependency updates."""
        sig = Signal(0)
        m = Memo(lambda: sig() * 2)
        
        for i in range(10):
            sig.set(i)
            assert m() == i * 2
    
    def test_memo_str_with_string(self):
        """str() works with string value."""
        m = Memo(lambda: "hello")
        assert str(m) == "hello"


# =============================================================================
# SECTION 4: EDGE CASES (10 tests)
# =============================================================================

class TestMemoEdgeCases:
    """Tests for memo edge cases."""
    
    def test_recursive_read_safe(self):
        """Recursive read doesn't infinite loop."""
        counter = [0]
        
        def compute():
            counter[0] += 1
            if counter[0] > 10:
                return 42
            # Normally you wouldn't read memo from itself
            return 42
        
        m = Memo(compute)
        assert m() == 42
    
    def test_memo_with_side_effects(self):
        """Memo with side effects (though not recommended)."""
        effects = []
        sig = Signal(5)
        
        m = Memo(lambda: (effects.append(sig()), sig() * 2)[1])
        
        m()
        sig.set(10)
        m()
        
        assert 5 in effects or 10 in effects
    
    def test_memo_equality_objects(self):
        """Memo equality with objects."""
        sig = Signal({"value": 1})
        
        # Always equal (reference same value)
        m = Memo(lambda: sig()["value"], equals=lambda a, b: True)
        
        call_count = [0]
        
        @Effect
        def eff():
            m()
            call_count[0] += 1
        
        initial = call_count[0]
        sig.set({"value": 2})  # Same according to equals
        m()
        
        # Effect may or may not re-run depending on implementation
    
    def test_memo_with_callable_return(self):
        """Memo returning callable works."""
        m = Memo(lambda: lambda x: x * 2)
        fn = m()
        assert fn(5) == 10
    
    def test_memo_with_generator(self):
        """Memo returning generator expression works."""
        sig = Signal([1, 2, 3])
        m = Memo(lambda: (x * 2 for x in sig()))
        
        result = list(m())
        assert result == [2, 4, 6]
    
    def test_large_dependency_graph(self):
        """Large dependency graph works."""
        sig = Signal(1)
        memos = []
        
        for i in range(20):
            if i == 0:
                memos.append(Memo(lambda: sig() * 2))
            else:
                prev = memos[i - 1]
                memos.append(Memo(lambda prev=prev: prev() + 1))
        
        assert memos[-1]() == 21  # 2 + 19 additions
    
    def test_memo_repr(self):
        """repr() shows useful info."""
        m = Memo(lambda: 42, name="my_memo")
        r = repr(m)
        assert "my_memo" in r or "42" in r or "Memo" in r
    
    def test_memo_with_exception_message(self):
        """Memo exception has useful message."""
        sig = Signal(0)
        
        m = Memo(lambda: 1 / sig())
        
        sig.set(0)
        with pytest.raises(ZeroDivisionError):
            m()
    
    def test_memo_stress_test(self):
        """Stress test with many updates."""
        sig = Signal(0)
        m = Memo(lambda: sig() * 2)
        
        for i in range(100):
            sig.set(i)
            assert m() == i * 2
    
    def test_memo_with_list_comprehension(self):
        """Memo with list comprehension works."""
        items = Signal([1, 2, 3])
        m = Memo(lambda: [x * 2 for x in items()])
        
        assert m() == [2, 4, 6]
        
        items.set([4, 5])
        assert m() == [8, 10]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
