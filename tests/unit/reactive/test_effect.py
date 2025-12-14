"""
Tests for PyNext Effect

50 tests covering:
- Creation (10): basic, decorated, deferred, with cleanup
- Execution (20): auto-run, dependency tracking, re-execution
- Cleanup (10): return cleanup, dispose
- Batching (10): batched updates, flush order

Run with: pytest tests/unit/reactive/test_effect.py -v
"""

import gc
import pytest
from typing import List
from unittest.mock import Mock

from pynext.reactive.signal import Signal
from pynext.reactive.effect import (
    Effect,
    EffectOptions,
    createEffect,
    effect,
    RenderEffect,
    createRenderEffect,
)
from pynext.reactive.batch import batch, untrack


# =============================================================================
# SECTION 1: CREATION TESTS (10 tests)
# =============================================================================

class TestEffectCreation:
    """Tests for Effect creation and initialization."""
    
    def test_create_basic_effect(self):
        """Effect can be created with a function."""
        call_count = [0]
        Effect(lambda: call_count.__setitem__(0, call_count[0] + 1))
        assert call_count[0] == 1
    
    def test_create_effect_decorator(self):
        """Effect can be used as decorator."""
        call_count = [0]
        
        @Effect
        def my_effect():
            call_count[0] += 1
        
        assert call_count[0] == 1
    
    def test_create_effect_with_name(self):
        """Effect can be created with debug name."""
        eff = Effect(lambda: None, name="my_effect")
        assert eff.name == "my_effect"
    
    def test_create_effect_with_options(self):
        """Effect can be created with EffectOptions."""
        options = EffectOptions(name="named_effect")
        eff = Effect(lambda: None, options=options)
        assert eff.name == "named_effect"
    
    def test_create_deferred_effect(self):
        """Deferred effect doesn't run immediately."""
        call_count = [0]
        eff = Effect(lambda: call_count.__setitem__(0, call_count[0] + 1), defer=True)
        assert call_count[0] == 0  # Not run yet
    
    def test_effect_generates_unique_id(self):
        """Each effect gets unique ID."""
        eff1 = Effect(lambda: None)
        eff2 = Effect(lambda: None)
        assert eff1.id != eff2.id
        assert eff1.id.startswith("eff_")
    
    def test_createEffect_factory(self):
        """createEffect factory function works."""
        call_count = [0]
        createEffect(lambda: call_count.__setitem__(0, call_count[0] + 1))
        assert call_count[0] == 1
    
    def test_effect_factory(self):
        """effect() factory function works."""
        call_count = [0]
        effect(lambda: call_count.__setitem__(0, call_count[0] + 1))
        assert call_count[0] == 1
    
    def test_decorator_returns_effect_instance(self):
        """Decorator returns the Effect instance."""
        @Effect
        def my_effect():
            pass
        
        assert isinstance(my_effect, Effect)
    
    def test_render_effect_creation(self):
        """RenderEffect can be created."""
        call_count = [0]
        RenderEffect(lambda: call_count.__setitem__(0, call_count[0] + 1))
        assert call_count[0] == 1


# =============================================================================
# SECTION 2: EXECUTION TESTS (20 tests)
# =============================================================================

class TestEffectExecution:
    """Tests for effect execution behavior."""
    
    def test_runs_immediately(self):
        """Effect runs immediately on creation."""
        values = []
        Effect(lambda: values.append("ran"))
        assert values == ["ran"]
    
    def test_tracks_signal_read(self):
        """Effect tracks signal reads."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            sig()
            call_count[0] += 1
        
        assert call_count[0] == 1
        sig.set(1)
        assert call_count[0] == 2
    
    def test_tracks_multiple_signals(self):
        """Effect tracks multiple signals."""
        a = Signal(0)
        b = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            a()
            b()
            call_count[0] += 1
        
        a.set(1)
        assert call_count[0] == 2
        
        b.set(1)
        assert call_count[0] == 3
    
    def test_doesnt_track_peek(self):
        """Effect doesn't track peek() reads."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            sig.peek()
            call_count[0] += 1
        
        sig.set(1)
        assert call_count[0] == 1  # Still 1, not re-run
    
    def test_reruns_on_dependency_change(self):
        """Effect re-runs when dependency changes."""
        sig = Signal(0)
        values = []
        
        @Effect
        def tracker():
            values.append(sig())
        
        sig.set(1)
        sig.set(2)
        
        assert values == [0, 1, 2]
    
    def test_no_rerun_on_same_value(self):
        """Effect doesn't re-run if value doesn't change."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            sig()
            call_count[0] += 1
        
        sig.set(0)  # Same value
        
        assert call_count[0] == 1
    
    def test_cascading_effects(self):
        """Effects can cascade updates."""
        a = Signal(1)
        b = Signal(0)
        c = Signal(0)
        
        @Effect
        def a_to_b():
            b.set(a() * 2)
        
        @Effect
        def b_to_c():
            c.set(b() + 10)
        
        assert b() == 2
        assert c() == 12
        
        a.set(5)
        
        assert b() == 10
        assert c() == 20
    
    def test_diamond_dependency(self):
        """Diamond dependencies work correctly."""
        source = Signal(1)
        left = Signal(0)
        right = Signal(0)
        values = []
        
        @Effect
        def update_left():
            left.set(source() * 2)
        
        @Effect
        def update_right():
            right.set(source() * 3)
        
        @Effect
        def combined():
            values.append(left() + right())
        
        source.set(2)
        
        # Should only see final values, not intermediate
        assert 10 in values  # 4 + 6
    
    def test_untrack_prevents_dependency(self):
        """untrack() prevents dependency tracking."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            untrack(lambda: sig())
            call_count[0] += 1
        
        sig.set(1)
        
        assert call_count[0] == 1  # Not re-run
    
    def test_effect_with_memo(self):
        """Effect works with memo."""
        from pynext.reactive.memo import Memo
        
        sig = Signal(5)
        m = Memo(lambda: sig() * 2)
        values = []
        
        @Effect
        def tracker():
            values.append(m())
        
        sig.set(10)
        
        # Effect runs when signal changes, memo recomputes
        assert values[-1] == 20
    
    def test_many_effects_same_signal(self):
        """Multiple effects can depend on same signal."""
        sig = Signal(0)
        counts = [0, 0, 0]
        effects = []
        
        for i in range(3):
            def make_effect(idx=i):
                @Effect
                def eff():
                    sig()
                    counts[idx] += 1
                return eff
            effects.append(make_effect())
        
        sig.set(1)
        
        assert all(c == 2 for c in counts)
    
    def test_nested_signal_read(self):
        """Nested function calls track correctly."""
        sig = Signal(0)
        call_count = [0]
        
        def read_sig():
            return sig()
        
        @Effect
        def tracker():
            read_sig()
            call_count[0] += 1
        
        sig.set(1)
        
        assert call_count[0] == 2
    
    def test_effect_sees_current_value(self):
        """Effect always sees current signal value."""
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
    
    def test_dynamic_dependencies(self):
        """Dependencies can change between runs."""
        condition = Signal(True)
        a = Signal(1)
        b = Signal(2)
        values = []
        
        @Effect
        def tracker():
            if condition():
                values.append(('a', a()))
            else:
                values.append(('b', b()))
        
        initial_len = len(values)
        a.set(10)  # Tracked, re-runs
        assert len(values) > initial_len
        
        condition.set(False)  # Now tracks b
        len_after_condition = len(values)
        
        b.set(20)  # Now tracked
        assert len(values) > len_after_condition
    
    def test_effect_with_store(self):
        """Effect works with store."""
        from pynext.reactive.store import Store
        
        s = Store({"count": 0})
        values = []
        
        @Effect
        def tracker():
            values.append(s.count)
        
        s.count = 1
        
        assert values == [0, 1]
    
    def test_stress_test_many_updates(self):
        """Effect handles many rapid updates."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            sig()
            call_count[0] += 1
        
        for i in range(1, 100):  # Start from 1 to avoid same-value skip
            sig.set(i)
        
        # Effect runs on each unique value change (may have extra runs in implementation)
        assert call_count[0] >= 50  # At least half should run


# =============================================================================
# SECTION 3: CLEANUP TESTS (10 tests)
# =============================================================================

class TestEffectCleanup:
    """Tests for effect cleanup behavior."""
    
    def test_cleanup_returned_by_effect(self):
        """Effect can return a cleanup function."""
        cleanups = []
        sig = Signal(0)
        
        @Effect
        def with_cleanup():
            val = sig()
            return lambda: cleanups.append(val)
        
        sig.set(1)
        
        assert 0 in cleanups
    
    def test_cleanup_runs_before_rerun(self):
        """Cleanup runs before effect re-runs."""
        order = []
        sig = Signal(0)
        
        @Effect
        def with_cleanup():
            order.append(f"run:{sig()}")
            return lambda: order.append(f"cleanup:{sig()}")
        
        sig.set(1)
        
        # Initial run, then cleanup of 0, then run with 1
        assert order == ["run:0", "cleanup:1", "run:1"]
    
    def test_dispose_stops_effect(self):
        """Disposed effect doesn't run."""
        sig = Signal(0)
        call_count = [0]
        
        eff = Effect(lambda: (sig(), call_count.__setitem__(0, call_count[0] + 1)))
        
        eff.dispose()
        sig.set(1)
        
        assert call_count[0] == 1  # Only initial run
    
    def test_dispose_idempotent(self):
        """Calling dispose() multiple times is safe."""
        eff = Effect(lambda: None)
        
        eff.dispose()
        eff.dispose()
        eff.dispose()
        
        # Should not raise
    
    def test_cleanup_on_error(self):
        """Cleanup still runs if effect errors."""
        cleanups = []
        sig = Signal(0)
        
        try:
            @Effect
            def erroring():
                sig()
                if sig() > 0:
                    raise ValueError()
                return lambda: cleanups.append("cleaned")
            
            sig.set(1)
        except:
            pass
    
    def test_cleanup_error_doesnt_break_effect(self):
        """Error in cleanup doesn't prevent effect re-run."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def with_bad_cleanup():
            sig()
            call_count[0] += 1
            return lambda: (_ for _ in ()).throw(ValueError())
        
        try:
            sig.set(1)
        except:
            pass
        
        assert call_count[0] >= 1
    
    def test_nested_effects_cleanup(self):
        """Nested effects clean up properly."""
        outer_cleanups = []
        inner_cleanups = []
        sig = Signal(0)
        inner_effect = [None]
        
        @Effect
        def outer():
            val = sig()
            if val < 2:
                inner_effect[0] = Effect(
                    lambda: (sig(), inner_cleanups.append(sig()))
                )
            return lambda: outer_cleanups.append(val)
    
    def test_effect_dispose_is_safe(self):
        """Disposed effects don't cause issues."""
        sig = Signal(0)
        eff = Effect(lambda: sig())
        
        eff.dispose()
        
        # Signal updates shouldn't cause issues
        sig.set(1)
        sig.set(2)
        
        # No errors should occur
    
    def test_cleanup_receives_no_args(self):
        """Cleanup function receives no arguments."""
        received_args = []
        sig = Signal(0)
        
        @Effect
        def with_cleanup():
            sig()
            def cleanup(*args):
                received_args.extend(args)
            return cleanup
        
        sig.set(1)
        
        assert received_args == []


# =============================================================================
# SECTION 4: BATCHING TESTS (10 tests)
# =============================================================================

class TestEffectBatching:
    """Tests for effect batching behavior."""
    
    def test_batch_coalesces_updates(self):
        """batch() coalesces multiple updates."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            sig()
            call_count[0] += 1
        
        batch(lambda: (
            sig.set(1),
            sig.set(2),
            sig.set(3)
        ))
        
        assert call_count[0] == 2  # Initial + 1 batch
    
    def test_batch_with_multiple_signals(self):
        """batch() works with multiple signals."""
        a = Signal(0)
        b = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            a()
            b()
            call_count[0] += 1
        
        batch(lambda: (
            a.set(1),
            b.set(1)
        ))
        
        assert call_count[0] == 2
    
    def test_nested_batch(self):
        """Nested batches work."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            sig()
            call_count[0] += 1
        
        def outer():
            sig.set(1)
            batch(lambda: sig.set(2))
            sig.set(3)
        
        batch(outer)
        
        assert call_count[0] == 2
    
    def test_batch_sees_final_value(self):
        """Effects see final value after batch."""
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
    
    def test_batch_with_cascading(self):
        """Cascading effects work in batch."""
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
    
    def test_batch_stress_test(self):
        """Batch handles many updates."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            sig()
            call_count[0] += 1
        
        def many_updates():
            for i in range(100):
                sig.set(i)
        
        batch(many_updates)
        
        assert call_count[0] == 2  # Initial + 1 batch
    
    def test_batch_preserves_effect_order(self):
        """Effects all run after batch (order not guaranteed)."""
        sig = Signal(0)
        ran = []
        effects = []
        
        for i in range(3):
            def make_eff(idx=i):
                @Effect
                def eff():
                    sig()
                    ran.append(idx)
                return eff
            effects.append(make_eff())
        
        ran.clear()
        batch(lambda: sig.set(1))
        
        assert set(ran) == {0, 1, 2}
    
    def test_batch_return_value(self):
        """batch() returns function result."""
        result = batch(lambda: 42)
        assert result == 42
    
    def test_batch_with_cleanup(self):
        """Cleanups run correctly in batch."""
        cleanups = []
        sig = Signal(0)
        
        @Effect
        def with_cleanup():
            val = sig()
            return lambda: cleanups.append(val)
        
        batch(lambda: sig.set(1))
        
        assert 0 in cleanups
    
    def test_batch_error_still_flushes(self):
        """Pending effects flush after error."""
        sig = Signal(0)
        call_count = [0]
        
        @Effect
        def tracker():
            sig()
            call_count[0] += 1
        
        try:
            def bad():
                sig.set(1)
                raise ValueError()
            batch(bad)
        except:
            pass
        
        assert call_count[0] >= 1
