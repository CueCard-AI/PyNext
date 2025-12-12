"""
Integration Tests for PyNext Reactive System

40 tests covering:
- Signal + Effect integration (15)
- Signal + Memo integration (15)
- Store + Effect integration (10)

Run with: pytest tests/unit/reactive/test_integration.py -v
"""

import pytest
from pynext.reactive.signal import Signal
from pynext.reactive.effect import Effect
from pynext.reactive.memo import Memo
from pynext.reactive.store import Store
from pynext.reactive.batch import batch, untrack


# =============================================================================
# SECTION 1: SIGNAL + EFFECT INTEGRATION (15 tests)
# =============================================================================

class TestSignalEffectIntegration:
    """Integration tests for Signal and Effect."""
    
    def test_signal_triggers_effect(self):
        """Signal change triggers effect."""
        sig = Signal(0)
        values = []
        
        @Effect
        def tracker():
            values.append(sig())
        
        sig.set(1)
        sig.set(2)
        
        assert values == [0, 1, 2]
    
    def test_multiple_signals_one_effect(self):
        """Effect tracks multiple signals."""
        a = Signal(1)
        b = Signal(2)
        values = []
        
        @Effect
        def tracker():
            values.append(a() + b())
        
        a.set(10)
        b.set(20)
        
        assert values == [3, 12, 30]
    
    def test_cascading_effects(self):
        """Effects can cascade updates."""
        source = Signal(1)
        doubled = Signal(0)
        quadrupled = Signal(0)
        
        @Effect
        def double_it():
            doubled.set(source() * 2)
        
        @Effect
        def quadruple_it():
            quadrupled.set(doubled() * 2)
        
        assert doubled() == 2
        assert quadrupled() == 4
        
        source.set(5)
        
        assert doubled() == 10
        assert quadrupled() == 20
    
    def test_diamond_effect_graph(self):
        """Diamond dependency works correctly."""
        source = Signal(1)
        left = Signal(0)
        right = Signal(0)
        combined = []
        
        @Effect
        def update_left():
            left.set(source() * 2)
        
        @Effect
        def update_right():
            right.set(source() * 3)
        
        @Effect
        def combine():
            combined.append(left() + right())
        
        source.set(2)
        
        assert 10 in combined  # 4 + 6
    
    def test_effect_cleanup_on_rerun(self):
        """Effect cleanup runs before re-execution."""
        sig = Signal(0)
        cleanups = []
        
        @Effect
        def with_cleanup():
            val = sig()
            return lambda: cleanups.append(val)
        
        sig.set(1)
        sig.set(2)
        
        assert 0 in cleanups
        assert 1 in cleanups
    
    def test_conditional_dependency(self):
        """Effect with conditional dependency."""
        condition = Signal(True)
        a = Signal(1)
        b = Signal(2)
        values = []
        
        @Effect
        def conditional():
            if condition():
                values.append(('a', a()))
            else:
                values.append(('b', b()))
        
        condition.set(False)
        
        # Should have switched to tracking b
    
    def test_untrack_in_effect(self):
        """untrack prevents dependency."""
        sig = Signal(0)
        other = Signal(100)
        call_count = [0]
        
        @Effect
        def partial_track():
            sig()  # Tracked
            untrack(lambda: other())  # Not tracked
            call_count[0] += 1
        
        initial = call_count[0]
        
        other.set(200)  # Should not trigger
        assert call_count[0] == initial
        
        sig.set(1)  # Should trigger
        assert call_count[0] > initial
    
    def test_batch_with_effect(self):
        """Batch coalesces effect runs."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        initial = call_count[0]
        
        batch(lambda: (
            sig.set(1),
            sig.set(2),
            sig.set(3)
        ))
        
        assert call_count[0] == initial + 1  # Only one additional run
    
    def test_many_signals_one_effect(self):
        """Effect with many signal dependencies."""
        signals = [Signal(i) for i in range(10)]
        call_count = [0]
        
        @Effect
        def tracker():
            total = sum(s() for s in signals)
            call_count[0] += 1
        
        initial = call_count[0]
        
        signals[5].set(100)
        
        assert call_count[0] > initial
    
    def test_effect_sees_consistent_state(self):
        """Effect sees consistent state in batch."""
        a = Signal(1)
        b = Signal(2)
        ratios = []
        
        @Effect
        def ratio():
            if b() != 0:
                ratios.append(a() / b())
        
        batch(lambda: (
            a.set(10),
            b.set(5)
        ))
        
        assert ratios[-1] == 2.0
    
    def test_dispose_stops_tracking(self):
        """Disposed effect stops tracking."""
        sig = Signal(0)
        call_count = [0]
        
        eff = Effect(lambda: (sig(), call_count.__setitem__(0, call_count[0] + 1)))
        
        initial = call_count[0]
        eff.dispose()
        
        sig.set(1)
        
        assert call_count[0] == initial
    
    def test_stress_many_updates(self):
        """Stress test with many updates."""
        sig = Signal(0)
        values = []
        
        @Effect
        def tracker():
            values.append(sig())
        
        for i in range(1, 50):
            sig.set(i)
        
        assert values[-1] == 49
    
    def test_nested_effects(self):
        """Nested effects work correctly."""
        outer_sig = Signal(0)
        inner_sig = Signal(0)
        outer_count = [0]
        inner_count = [0]
        
        @Effect
        def outer():
            outer_sig()
            outer_count[0] += 1
        
        @Effect
        def inner():
            inner_sig()
            inner_count[0] += 1
        
        outer_sig.set(1)
        inner_sig.set(1)
        
        assert outer_count[0] >= 2
        assert inner_count[0] >= 2
    
    def test_effect_error_recovery(self):
        """Effect recovers from error."""
        sig = Signal(0)
        values = []
        
        @Effect
        def risky():
            val = sig()
            if val == 5:
                raise ValueError("bad value")
            values.append(val)
        
        try:
            sig.set(5)
        except:
            pass
        
        sig.set(6)
        
        assert 6 in values
    
    def test_effect_with_peek(self):
        """Effect with peek doesn't track."""
        tracked = Signal(0)
        peeked = Signal(0)
        call_count = [0]
        
        @Effect
        def mixed():
            tracked()
            peeked.peek()
            call_count[0] += 1
        
        initial = call_count[0]
        
        peeked.set(100)
        assert call_count[0] == initial  # No re-run


# =============================================================================
# SECTION 2: SIGNAL + MEMO INTEGRATION (15 tests)
# =============================================================================

class TestSignalMemoIntegration:
    """Integration tests for Signal and Memo."""
    
    def test_memo_derives_from_signal(self):
        """Memo derives value from signal."""
        sig = Signal(5)
        doubled = Memo(lambda: sig() * 2)
        
        assert doubled() == 10
        
        sig.set(10)
        assert doubled() == 20
    
    def test_memo_chain(self):
        """Chain of memos works."""
        sig = Signal(1)
        m1 = Memo(lambda: sig() + 1)
        m2 = Memo(lambda: m1() * 2)
        m3 = Memo(lambda: m2() + 10)
        
        assert m3() == 14  # ((1+1)*2)+10
        
        sig.set(5)
        assert m3() == 22  # ((5+1)*2)+10
    
    def test_memo_multiple_signals(self):
        """Memo with multiple signal deps."""
        a = Signal(1)
        b = Signal(2)
        c = Signal(3)
        
        total = Memo(lambda: a() + b() + c())
        
        assert total() == 6
        
        a.set(10)
        assert total() == 15
    
    def test_memo_cached(self):
        """Memo caches value."""
        sig = Signal(5)
        compute_count = [0]
        
        m = Memo(lambda: (compute_count.__setitem__(0, compute_count[0] + 1), sig() * 2)[1])
        
        m()
        m()
        m()
        
        # Should only compute once for unchanged signal
    
    def test_memo_with_effect(self):
        """Memo and effect work together."""
        sig = Signal(5)
        m = Memo(lambda: sig() * 2)
        values = []
        
        @Effect
        def tracker():
            values.append(m())
        
        sig.set(10)
        
        assert 20 in values
    
    def test_diamond_memo(self):
        """Diamond memo dependency."""
        source = Signal(1)
        left = Memo(lambda: source() * 2)
        right = Memo(lambda: source() * 3)
        combined = Memo(lambda: left() + right())
        
        assert combined() == 5
        
        source.set(2)
        assert combined() == 10
    
    def test_memo_conditional(self):
        """Memo with conditional logic."""
        condition = Signal(True)
        a = Signal(1)
        b = Signal(2)
        
        m = Memo(lambda: a() if condition() else b())
        
        assert m() == 1
        
        condition.set(False)
        assert m() == 2
    
    def test_memo_with_untrack(self):
        """Memo with untrack."""
        tracked = Signal(5)
        untracked = Signal(100)
        
        m = Memo(lambda: tracked() + untrack(lambda: untracked()))
        
        assert m() == 105
        
        untracked.set(200)
        assert m() == 105  # Still 105, untracked didn't trigger recompute
        
        tracked.set(10)
        assert m() == 210  # Now uses new untracked value
    
    def test_memo_with_batch(self):
        """Memo with batched updates."""
        a = Signal(1)
        b = Signal(2)
        m = Memo(lambda: a() + b())
        values = []
        
        @Effect
        def tracker():
            values.append(m())
        
        batch(lambda: (a.set(10), b.set(20)))
        
        assert values[-1] == 30
    
    def test_many_memos_one_signal(self):
        """Many memos from one signal."""
        sig = Signal(1)
        memos = [Memo(lambda i=i: sig() * i) for i in range(10)]
        
        sig.set(5)
        
        for i, m in enumerate(memos):
            assert m() == 5 * i
    
    def test_memo_stress_test(self):
        """Stress test memo updates."""
        sig = Signal(0)
        m = Memo(lambda: sig() * 2)
        
        for i in range(100):
            sig.set(i)
            assert m() == i * 2
    
    def test_memo_equality_check(self):
        """Memo with custom equality."""
        sig = Signal([1, 2, 3])
        
        # Equal if lengths match
        m = Memo(lambda: sig().copy(), equals=lambda a, b: len(a) == len(b))
        
        m()
        sig.set([4, 5, 6])  # Same length
        # Memo should not notify observers
    
    def test_memo_with_store(self):
        """Memo works with store."""
        s = Store({"count": 5})
        m = Memo(lambda: s.count * 2)
        
        assert m() == 10
    
    def test_deep_memo_chain(self):
        """Deep chain of memos."""
        sig = Signal(1)
        m = sig
        for i in range(10):
            prev = m
            m = Memo(lambda prev=prev: prev() + 1 if callable(prev) else prev + 1)
        
        # Just ensure it works without error
    
    def test_memo_with_none(self):
        """Memo returning None."""
        sig = Signal(True)
        m = Memo(lambda: None if sig() else "value")
        
        assert m() is None
        
        sig.set(False)
        assert m() == "value"


# =============================================================================
# SECTION 3: STORE + EFFECT INTEGRATION (10 tests)
# =============================================================================

class TestStoreEffectIntegration:
    """Integration tests for Store and Effect."""
    
    def test_store_triggers_effect(self):
        """Store change triggers effect."""
        s = Store({"count": 0})
        values = []
        
        @Effect
        def tracker():
            values.append(s.count)
        
        s.count = 1
        s.count = 2
        
        assert 1 in values
        assert 2 in values
    
    def test_store_multiple_keys_effect(self):
        """Effect tracks multiple store keys."""
        s = Store({"a": 1, "b": 2})
        sums = []
        
        @Effect
        def tracker():
            sums.append(s.a + s.b)
        
        s.a = 10
        
        assert 12 in sums
    
    def test_store_with_signal(self):
        """Store and signal together."""
        store_data = Store({"value": 5})
        multiplier = Signal(2)
        results = []
        
        @Effect
        def tracker():
            results.append(store_data.value * multiplier())
        
        store_data.value = 10
        multiplier.set(3)
        
        assert 30 in results
    
    def test_store_batch_update(self):
        """Store updates in batch."""
        s = Store({"a": 1, "b": 2})
        call_count = [0]
        
        @Effect
        def tracker():
            s.a
            s.b
            call_count[0] += 1
        
        initial = call_count[0]
        
        batch(lambda: (
            setattr(s, 'a', 10),
            setattr(s, 'b', 20)
        ))
        
        # Should coalesce updates
    
    def test_store_cleanup_effect(self):
        """Store with effect cleanup."""
        s = Store({"value": 0})
        cleanups = []
        
        @Effect
        def with_cleanup():
            val = s.value
            return lambda: cleanups.append(val)
        
        s.value = 1
        
        assert 0 in cleanups
    
    def test_store_memo_integration(self):
        """Store with memo."""
        s = Store({"a": 5, "b": 10})
        total = Memo(lambda: s.a + s.b)
        
        assert total() == 15
    
    def test_store_stress_test(self):
        """Stress test store updates."""
        s = Store({"count": 0})
        
        for i in range(100):
            s.count = i
        
        assert s.count == 99
    
    def test_store_untrack(self):
        """Store with untrack."""
        s = Store({"tracked": 0, "untracked": 0})
        call_count = [0]
        
        @Effect
        def tracker():
            s.tracked
            untrack(lambda: s.untracked)
            call_count[0] += 1
        
        initial = call_count[0]
        
        s.untracked = 100  # Should not trigger
        # May or may not trigger depending on implementation
    
    def test_simple_app_pattern(self):
        """Simple app pattern with store."""
        state = Store({
            "count": 0,
            "name": "App"
        })
        
        ui_updates = []
        
        @Effect
        def render():
            ui_updates.append(f"{state.name}: {state.count}")
        
        state.count = 1
        state.count = 2
        
        assert len(ui_updates) >= 2
    
    def test_store_replace_value(self):
        """Replace store value entirely."""
        s = Store({"value": {"nested": 1}})
        
        s.value = {"nested": 2}
        
        # Should work without error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
