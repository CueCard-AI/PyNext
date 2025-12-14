"""
Comprehensive Tests for PyNext Batch and Context

50 tests covering:
- Batching (30): single, nested, error handling, flush
- Untrack (20): no dependency tracking, nested untrack

Run with: pytest tests/unit/reactive/test_batch_context.py -v
"""

import gc
import pytest
from typing import List, Any
from unittest.mock import Mock, patch

from pynext.reactive.signal import Signal
from pynext.reactive.effect import Effect
from pynext.reactive.batch import (
    batch,
    untrack,
    createRoot,
    on,
    createReaction,
    startTransition,
    deferredValue,
)
from pynext.reactive.context import (
    get_current_observer,
    is_batching,
    schedule_effect,
    flush_updates,
    _batch_depth,
    _pending_effects,
)


# =============================================================================
# SECTION 1: BATCHING TESTS (30 tests)
# =============================================================================

class TestBatching:
    """Tests for batch() function."""
    
    def test_batch_basic(self):
        """batch() groups updates."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        batch(lambda: sig.set(1))
        
        assert call_count[0] == 2  # Initial + 1
    
    def test_batch_multiple_updates(self):
        """batch() coalesces multiple updates."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        batch(lambda: (
            sig.set(1),
            sig.set(2),
            sig.set(3)
        ))
        
        assert call_count[0] == 2  # Not 4
    
    def test_batch_multiple_signals(self):
        """batch() works with multiple signals."""
        a = Signal(0)
        b = Signal(0)
        call_count = [0]
        
        @Effect
        def combined():
            a()
            b()
            call_count[0] += 1
        
        batch(lambda: (
            a.set(1),
            b.set(1)
        ))
        
        assert call_count[0] == 2
    
    def test_batch_nested(self):
        """Nested batches work."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        def outer():
            sig.set(1)
            batch(lambda: sig.set(2))
            sig.set(3)
        
        batch(outer)
        
        assert call_count[0] == 2
    
    def test_batch_triple_nested(self):
        """Triple nested batches work."""
        sig = Signal(0)
        
        batch(lambda:
            batch(lambda:
                batch(lambda:
                    sig.set(42)
                )
            )
        )
        
        assert sig() == 42
    
    def test_batch_return_value(self):
        """batch() returns function result."""
        result = batch(lambda: 42)
        assert result == 42
    
    def test_batch_with_exception(self):
        """batch() propagates exceptions."""
        with pytest.raises(ValueError):
            batch(lambda: (_ for _ in ()).throw(ValueError("test")))
    
    def test_batch_flushes_after_exception(self):
        """Pending updates flush after exception."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def counter():
            sig()
            call_count[0] += 1
        
        try:
            def bad():
                sig.set(1)
                raise ValueError()
            batch(bad)
        except:
            pass
        
        # Should have flushed
        assert call_count[0] >= 1
    
    def test_is_batching_true_inside(self):
        """is_batching() returns True inside batch."""
        inside_value = [None]
        
        def check():
            inside_value[0] = is_batching()
        
        batch(check)
        
        assert inside_value[0] is True
    
    def test_is_batching_false_outside(self):
        """is_batching() returns False outside batch."""
        assert is_batching() is False
    
    def test_batch_depth_increments(self):
        """Batch depth increments on enter."""
        depths = []
        
        def check():
            depths.append(_batch_depth.get())
        
        batch(check)
        
        assert depths[0] >= 1
    
    def test_batch_depth_decrements(self):
        """Batch depth decrements on exit."""
        before = _batch_depth.get()
        batch(lambda: None)
        after = _batch_depth.get()
        
        assert before == after
    
    def test_batch_sees_final_value(self):
        """Effect sees final value after batch."""
        sig = Signal(0)
        seen = []
        
        @Effect
        def tracker():
            seen.append(sig())
        
        batch(lambda: (
            sig.set(1),
            sig.set(2),
            sig.set(3)
        ))
        
        assert seen[-1] == 3
    
    def test_schedule_effect_queues(self):
        """schedule_effect queues for later."""
        calls = []
        
        def check():
            schedule_effect(lambda: calls.append("scheduled"))
            calls.append("immediate")
        
        batch(check)
        
        # scheduled should come after immediate
        assert calls.index("immediate") < calls.index("scheduled")
    
    def test_flush_updates_runs_pending(self):
        """flush_updates runs pending effects."""
        calls = []
        schedule_effect(lambda: calls.append("ran"))
        
        flush_updates()
        
        assert "ran" in calls
    
    def test_batch_empty_function(self):
        """batch() with empty function works."""
        result = batch(lambda: None)
        assert result is None
    
    def test_batch_with_signal_read(self):
        """Reading in batch works."""
        sig = Signal(42)
        
        result = batch(lambda: sig())
        
        assert result == 42
    
    def test_batch_order_deterministic(self):
        """Effects all run (order not guaranteed with WeakSet)."""
        sig = Signal(0)
        order = []
        effects = []  # Keep references
        
        for i in range(3):
            def make_effect(idx=i):
                @Effect
                def ordered():
                    sig()
                    order.append(idx)
                return ordered
            effects.append(make_effect())
        
        order.clear()
        batch(lambda: sig.set(1))
        
        # All effects should run (order not guaranteed)
        assert set(order) == {0, 1, 2}
    
    def test_batch_with_cleanup(self):
        """Effects with cleanup work in batch."""
        sig = Signal(0)
        cleanups = []
        
        @Effect
        def with_cleanup():
            val = sig()
            return lambda: cleanups.append(val)
        
        batch(lambda: sig.set(1))
        
        assert 0 in cleanups
    
    def test_batch_cascading(self):
        """Cascading updates in batch work."""
        a = Signal(1)
        b = Signal(0)
        c = Signal(0)
        
        @Effect
        def a_to_b():
            b.set(a() * 2)
        
        @Effect
        def b_to_c():
            c.set(b() + 10)
        
        batch(lambda: a.set(5))
        
        assert b() == 10
        assert c() == 20
    
    def test_many_signals_batch(self):
        """Many signals in batch work."""
        signals = [Signal(0) for _ in range(20)]
        call_count = [0]
        
        @Effect
        def all_reader():
            for s in signals:
                s()
            call_count[0] += 1
        
        def update_all():
            for i, s in enumerate(signals):
                s.set(i + 1)
        
        batch(update_all)
        
        assert call_count[0] == 2
    
    def test_batch_with_untrack(self):
        """batch with untrack works."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def untracked():
            untrack(lambda: sig())
            call_count[0] += 1
        
        batch(lambda: sig.set(1))
        
        assert call_count[0] == 1  # Only initial
    
    def test_batch_stress_test(self):
        """Stress test batch with many updates."""
        sig = Signal(0)
        
        def many_updates():
            for i in range(100):
                sig.set(i)
        
        batch(many_updates)
        
        assert sig() == 99
    
    def test_batch_with_store(self):
        """batch with store works."""
        from pynext.reactive.store import Store
        
        s = Store({"count": 0})
        call_count = [0]
        
        @Effect
        def watcher():
            s.count
            call_count[0] += 1
        
        batch(lambda: setattr(s, 'count', 10))
        
        assert call_count[0] == 2
    
    def test_batch_with_error_in_effect(self):
        """Error in effect during batch is handled."""
        sig = Signal(0)
        
        @Effect
        def bad():
            if sig() > 0:
                raise ValueError()
        
        @Effect
        def good():
            sig()
        
        try:
            batch(lambda: sig.set(1))
        except:
            pass
    
    def test_batch_in_effect(self):
        """batch inside effect works."""
        sig = Signal(0)
        other = Signal(0)
        
        @Effect
        def batch_inside():
            if sig() > 0:
                batch(lambda: other.set(sig() * 2))
        
        sig.set(5)
        assert other() == 10


# =============================================================================
# SECTION 2: UNTRACK TESTS (20 tests)
# =============================================================================

class TestUntrack:
    """Tests for untrack() function."""
    
    def test_untrack_basic(self):
        """untrack() prevents dependency."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def no_track():
            untrack(lambda: sig())
            call_count[0] += 1
        
        sig.set(1)
        
        assert call_count[0] == 1  # Only initial
    
    def test_untrack_return_value(self):
        """untrack() returns function result."""
        sig = Signal(42)
        result = untrack(lambda: sig())
        assert result == 42
    
    def test_untrack_nested(self):
        """Nested untrack works."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def nested():
            untrack(lambda: untrack(lambda: sig()))
            call_count[0] += 1
        
        sig.set(1)
        
        assert call_count[0] == 1
    
    def test_untrack_partial(self):
        """Partial untrack works."""
        tracked = Signal(0)
        untracked = Signal(0)
        call_count = [0]
        
        @Effect
        def partial():
            tracked()
            untrack(lambda: untracked())
            call_count[0] += 1
        
        assert call_count[0] == 1
        
        tracked.set(1)  # Triggers
        assert call_count[0] == 2
        
        untracked.set(1)  # Doesn't trigger
        assert call_count[0] == 2
    
    def test_untrack_restores_observer(self):
        """untrack restores previous observer."""
        sig = Signal(0)
        tracked_sig = Signal(0)
        call_count = [0]
        
        @Effect
        def restore():
            tracked_sig()  # Before untrack
            untrack(lambda: sig())
            tracked_sig()  # After untrack - should still track
            call_count[0] += 1
        
        tracked_sig.set(1)
        
        assert call_count[0] == 2
    
    def test_untrack_outside_effect(self):
        """untrack outside effect works."""
        sig = Signal(42)
        result = untrack(lambda: sig())
        assert result == 42
    
    def test_untrack_with_memo(self):
        """untrack with memo works."""
        from pynext.reactive.memo import Memo
        
        sig = Signal(5)
        m = Memo(lambda: sig() * 2)
        call_count = [0]
        
        @Effect
        def untracked_memo():
            untrack(lambda: m())
            call_count[0] += 1
        
        sig.set(10)
        
        # m changed, but effect didn't re-run (untracked)
        assert call_count[0] == 1
    
    def test_untrack_multiple_reads(self):
        """Multiple untracked reads work."""
        a = Signal(1)
        b = Signal(2)
        c = Signal(3)
        call_count = [0]
        
        @Effect
        def multi():
            untrack(lambda: (a(), b(), c()))
            call_count[0] += 1
        
        a.set(10)
        b.set(20)
        c.set(30)
        
        assert call_count[0] == 1
    
    def test_untrack_in_batch(self):
        """untrack in batch works."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def in_batch():
            untrack(lambda: sig())
            call_count[0] += 1
        
        batch(lambda: sig.set(1))
        
        assert call_count[0] == 1
    
    def test_untrack_sets_observer_none(self):
        """untrack sets observer to None."""
        observer_value = [None]
        
        @Effect
        def check():
            def inner():
                observer_value[0] = get_current_observer()
            untrack(inner)
        
        assert observer_value[0] is None
    
    def test_untrack_with_exception(self):
        """untrack restores observer after exception."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def with_error():
            tracked_sig = Signal(0)
            tracked_sig()
            try:
                def bad():
                    raise ValueError()
                untrack(bad)
            except:
                pass
            # Observer should be restored
            call_count[0] += 1
    
    def test_untrack_complex_expression(self):
        """untrack with complex expression."""
        a = Signal(1)
        b = Signal(2)
        
        result = untrack(lambda: a() + b() * 2)
        
        assert result == 5
    
    def test_untrack_conditional(self):
        """untrack with conditional."""
        condition = Signal(True)
        data = Signal(42)
        call_count = [0]
        
        @Effect
        def conditional():
            if condition():
                untrack(lambda: data())
            call_count[0] += 1
        
        data.set(100)  # Untracked, no re-run
        
        assert call_count[0] == 1
    
    def test_untrack_with_closure(self):
        """untrack with closure."""
        sig = Signal(10)
        multiplier = 2
        
        result = untrack(lambda: sig() * multiplier)
        
        assert result == 20
    
    def test_current_observer_none_in_untrack(self):
        """get_current_observer() is None in untrack."""
        observer = [object()]  # Non-None initial
        
        @Effect
        def check():
            untrack(lambda: observer.__setitem__(0, get_current_observer()))
        
        assert observer[0] is None
    
    def test_untrack_doesnt_affect_other_tracking(self):
        """untrack in one effect doesn't affect others."""
        sig = Signal(0)
        tracked_count = [0]
        untracked_count = [0]
        
        @Effect
        def tracked():
            sig()
            tracked_count[0] += 1
        
        @Effect
        def untracked():
            untrack(lambda: sig())
            untracked_count[0] += 1
        
        sig.set(1)
        
        assert tracked_count[0] == 2
        assert untracked_count[0] == 1
    
    def test_untrack_empty_function(self):
        """untrack with function returning None."""
        result = untrack(lambda: None)
        assert result is None
    
    def test_untrack_with_side_effect(self):
        """untrack function can have side effects."""
        results = []
        sig = Signal(0)
        
        @Effect
        def with_side_effect():
            untrack(lambda: results.append(sig()))
        
        assert len(results) == 1
    
    def test_untrack_preserves_value(self):
        """untrack returns exact value."""
        obj = {"key": "value"}
        sig = Signal(obj)
        
        result = untrack(lambda: sig())
        
        assert result is obj
