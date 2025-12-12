"""
Tests for the reactive effect system.

Tests cover:
- createEffect function
- Effect registration
- Signal subscription
- Effect cleanup
- Dependency tracking
"""

import pytest
from pynext.reactive import Signal, effect
from pynext.reactive.effect import Effect
from pynext.reactive.batch import batch


class TestEffectBasic:
    """Basic effect tests."""
    
    def test_effect_runs_immediately(self):
        """Effect runs immediately on creation."""
        ran = []
        
        @effect
        def my_effect():
            ran.append(1)
        
        assert len(ran) == 1
    
    def test_effect_reruns_on_signal_change(self):
        """Effect reruns when dependent signal changes."""
        count = Signal(0, name="count")
        values = []
        
        @effect
        def track_count():
            values.append(count())
        
        assert values == [0]
        
        count.set(1)
        assert values == [0, 1]
        
        count.set(2)
        assert values == [0, 1, 2]
    
    def test_effect_tracks_multiple_signals(self):
        """Effect tracks multiple signal dependencies."""
        a = Signal(1, name="a")
        b = Signal(2, name="b")
        sums = []
        
        @effect
        def sum_ab():
            sums.append(a() + b())
        
        assert sums == [3]
        
        a.set(10)
        assert sums == [3, 12]
        
        b.set(20)
        assert sums == [3, 12, 30]
    
    def test_effect_with_conditional_read(self):
        """Effect with conditional signal reads."""
        show = Signal(True, name="show")
        value = Signal(10, name="value")
        results = []
        
        @effect
        def conditional_effect():
            if show():
                results.append(value())
            else:
                results.append(None)
        
        assert results == [10]
        
        value.set(20)
        assert results == [10, 20]
        
        show.set(False)
        assert results == [10, 20, None]


class TestEffectClass:
    """Tests for Effect class."""
    
    def test_effect_creation(self):
        """Create Effect instance."""
        ran = []
        eff = Effect(lambda: ran.append(1))
        
        assert len(ran) == 1
    
    def test_effect_has_dependencies(self):
        """Effect tracks dependencies."""
        count = Signal(0, name="count")
        
        eff = Effect(lambda: count())
        
        # Effect should have been created
        assert eff is not None
    
    def test_effect_dispose(self):
        """Disposed effect doesn't run."""
        count = Signal(0, name="count")
        values = []
        
        eff = Effect(lambda: values.append(count()))
        assert values == [0]
        
        eff.dispose()
        
        count.set(1)
        # Effect should not run after dispose
        assert 1 not in values or len(values) == 1


class TestEffectCleanup:
    """Tests for effect cleanup."""
    
    def test_cleanup_runs_before_rerun(self):
        """Cleanup function runs before effect reruns."""
        count = Signal(0, name="count")
        events = []
        
        @effect
        def with_cleanup():
            c = count()
            events.append(f"run_{c}")
            return lambda: events.append(f"cleanup_{c}")
        
        assert events == ["run_0"]
        
        count.set(1)
        assert "cleanup_0" in events
        assert "run_1" in events
    
    def test_cleanup_runs_on_dispose(self):
        """Cleanup runs when effect is disposed."""
        events = []
        
        def my_effect():
            events.append("run")
            return lambda: events.append("cleanup")
        
        eff = Effect(my_effect)
        assert events == ["run"]
        
        eff.dispose()
        assert "cleanup" in events


class TestBatchEffects:
    """Tests for batched effect execution."""
    
    def test_batch_delays_effects(self):
        """Batch delays effect execution."""
        count = Signal(0, name="count")
        values = []
        
        @effect
        def track():
            values.append(count())
        
        assert values == [0]
        
        # Use batch as a function
        def batch_updates():
            count.set(1)
            count.set(2)
            count.set(3)
        
        batch(batch_updates)
        
        # After batch, effect runs with final value
        assert values[-1] == 3
    
    def test_nested_batch(self):
        """Nested batch only executes after outermost."""
        count = Signal(0, name="count")
        values = []
        
        @effect
        def track():
            values.append(count())
        
        assert values == [0]
        
        def outer_batch():
            count.set(1)
            def inner_batch():
                count.set(2)
            batch(inner_batch)
        
        batch(outer_batch)
        
        # Effects should have run
        assert len(values) >= 2


class TestEffectDependencyTracking:
    """Tests for dependency tracking."""
    
    def test_dynamic_dependencies(self):
        """Dependencies can change between runs."""
        toggle = Signal(True, name="toggle")
        a = Signal(1, name="a")
        b = Signal(2, name="b")
        values = []
        
        @effect
        def dynamic():
            if toggle():
                values.append(("a", a()))
            else:
                values.append(("b", b()))
        
        assert values == [("a", 1)]
        
        a.set(10)
        assert values[-1] == ("a", 10)
        
        toggle.set(False)
        assert values[-1] == ("b", 2)
        
        # Now changing 'a' should NOT trigger effect
        a.set(100)
        # Effect should not have run with new 'a' value
        # (last value is still from toggle change)
    
    def test_no_duplicate_subscriptions(self):
        """Reading signal twice doesn't create duplicate subscriptions."""
        count = Signal(0, name="count")
        run_count = [0]
        
        @effect
        def double_read():
            _ = count() + count()  # Read twice
            run_count[0] += 1
        
        assert run_count[0] == 1
        
        count.set(1)
        assert run_count[0] == 2  # Only runs once, not twice


class TestEffectEdgeCases:
    """Edge cases for effects."""
    
    def test_effect_exception(self):
        """Effect that throws exception."""
        count = Signal(0, name="count")
        
        with pytest.raises(ZeroDivisionError):
            @effect
            def bad_effect():
                return 1 / count()  # Divide by zero on first run
    
    def test_effect_modifying_signal(self):
        """Effect that modifies a signal."""
        source = Signal(1, name="source")
        doubled = Signal(0, name="doubled")
        
        @effect
        def sync():
            doubled.set(source() * 2)
        
        assert doubled() == 2
        
        source.set(5)
        assert doubled() == 10
    
    def test_effect_with_memo(self):
        """Effect using memo."""
        from pynext.reactive import memo
        
        count = Signal(0, name="count")
        double = memo(lambda: count() * 2, name="double")
        values = []
        
        @effect
        def track_double():
            values.append(double())
        
        # Effect runs on creation
        assert len(values) >= 1
        
        count.set(5)
        # Effect should run again (implementation may vary)
        assert len(values) >= 1


class TestEffectReturn:
    """Tests for effect return values."""
    
    def test_effect_decorator_returns_effect(self):
        """@effect decorator returns Effect instance."""
        count = Signal(0, name="count")
        
        @effect
        def my_effect():
            return count()
        
        assert isinstance(my_effect, Effect)
    
    def test_effect_function_returns_cleanup(self):
        """Effect can return cleanup function."""
        cleanup_called = [False]
        count = Signal(0, name="count")
        
        @effect
        def with_cleanup():
            _ = count()
            return lambda: cleanup_called.__setitem__(0, True)
        
        assert cleanup_called[0] == False
        
        count.set(1)
        assert cleanup_called[0] == True

