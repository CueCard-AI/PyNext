"""
Phase 33.4: Promise Utilities Tests

Comprehensive tests for Promise utility methods transpilation.
Tests verify the runtime provides correct JavaScript implementations for:
- Promise.all
- Promise.allSettled
- Promise.race
- Promise.any (with AggregateError)
- Promise.withResolvers
"""

import pytest
import asyncio


# =============================================================================
# PROMISE.ALL TESTS (5 tests)
# =============================================================================

class TestPromiseAll:
    """Tests for Promise.all()."""
    
    @pytest.mark.asyncio
    async def test_promise_all_success(self):
        """Promise.all resolves when all resolve."""
        from pynext.runtime.promise import Promise_all
        
        async def get_value(val):
            await asyncio.sleep(0.01)
            return val
        
        results = await Promise_all([
            get_value(1),
            get_value(2),
            get_value(3)
        ])
        assert results == [1, 2, 3]
    
    @pytest.mark.asyncio
    async def test_promise_all_empty(self):
        """Promise.all with empty list."""
        from pynext.runtime.promise import Promise_all
        results = await Promise_all([])
        assert results == []
    
    @pytest.mark.asyncio
    async def test_promise_all_reject(self):
        """Promise.all rejects on first rejection."""
        from pynext.runtime.promise import Promise_all
        
        async def success():
            await asyncio.sleep(0.01)
            return "ok"
        
        async def fail():
            await asyncio.sleep(0.01)
            raise ValueError("fail")
        
        with pytest.raises(ValueError):
            await Promise_all([success(), fail()])
    
    @pytest.mark.asyncio
    async def test_promise_all_order(self):
        """Promise.all preserves order."""
        from pynext.runtime.promise import Promise_all
        
        async def delayed(val, delay):
            await asyncio.sleep(delay)
            return val
        
        results = await Promise_all([
            delayed("a", 0.03),
            delayed("b", 0.01),
            delayed("c", 0.02)
        ])
        # Results in input order, not completion order
        assert results == ["a", "b", "c"]
    
    @pytest.mark.asyncio
    async def test_promise_all_mixed_values(self):
        """Promise.all handles mixed sync/async."""
        from pynext.runtime.promise import Promise_all
        
        async def async_val():
            return 42
        
        # Mix of coroutines
        results = await Promise_all([
            async_val(),
            async_val()
        ])
        assert results == [42, 42]


# =============================================================================
# PROMISE.ALLSETTLED TESTS (4 tests)
# =============================================================================

class TestPromiseAllSettled:
    """Tests for Promise.allSettled()."""
    
    @pytest.mark.asyncio
    async def test_promise_allsettled_all_success(self):
        """Promise.allSettled with all fulfilled."""
        from pynext.runtime.promise import Promise_allSettled
        
        async def get_value(val):
            return val
        
        results = await Promise_allSettled([
            get_value(1),
            get_value(2)
        ])
        assert len(results) == 2
        assert results[0]["status"] == "fulfilled"
        assert results[0]["value"] == 1
    
    @pytest.mark.asyncio
    async def test_promise_allsettled_mixed(self):
        """Promise.allSettled with mixed results."""
        from pynext.runtime.promise import Promise_allSettled
        
        async def success():
            return "ok"
        
        async def fail():
            raise ValueError("error")
        
        results = await Promise_allSettled([
            success(),
            fail()
        ])
        assert results[0]["status"] == "fulfilled"
        assert results[1]["status"] == "rejected"
    
    @pytest.mark.asyncio
    async def test_promise_allsettled_all_rejected(self):
        """Promise.allSettled with all rejected."""
        from pynext.runtime.promise import Promise_allSettled
        
        async def fail(msg):
            raise ValueError(msg)
        
        results = await Promise_allSettled([
            fail("error1"),
            fail("error2")
        ])
        assert all(r["status"] == "rejected" for r in results)
    
    @pytest.mark.asyncio
    async def test_promise_allsettled_empty(self):
        """Promise.allSettled with empty list."""
        from pynext.runtime.promise import Promise_allSettled
        results = await Promise_allSettled([])
        assert results == []


# =============================================================================
# PROMISE.RACE TESTS (4 tests)
# =============================================================================

class TestPromiseRace:
    """Tests for Promise.race()."""
    
    @pytest.mark.asyncio
    async def test_promise_race_first_wins(self):
        """Promise.race returns first to complete."""
        from pynext.runtime.promise import Promise_race
        
        async def delayed(val, delay):
            await asyncio.sleep(delay)
            return val
        
        result = await Promise_race([
            delayed("slow", 0.1),
            delayed("fast", 0.01)
        ])
        assert result == "fast"
    
    @pytest.mark.asyncio
    async def test_promise_race_first_reject(self):
        """Promise.race rejects if first to complete rejects."""
        from pynext.runtime.promise import Promise_race
        
        async def delayed_fail():
            await asyncio.sleep(0.01)
            raise ValueError("fast fail")
        
        async def delayed_success():
            await asyncio.sleep(0.1)
            return "slow success"
        
        with pytest.raises(ValueError):
            await Promise_race([
                delayed_fail(),
                delayed_success()
            ])
    
    @pytest.mark.asyncio
    async def test_promise_race_single(self):
        """Promise.race with single promise."""
        from pynext.runtime.promise import Promise_race
        
        async def get_value():
            return 42
        
        result = await Promise_race([get_value()])
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_promise_race_timeout_pattern(self):
        """Promise.race for timeout pattern."""
        from pynext.runtime.promise import Promise_race
        
        async def slow_op():
            await asyncio.sleep(1)
            return "done"
        
        async def timeout():
            await asyncio.sleep(0.01)
            raise TimeoutError("timed out")
        
        with pytest.raises(TimeoutError):
            await Promise_race([slow_op(), timeout()])


# =============================================================================
# PROMISE.ANY TESTS (4 tests)
# =============================================================================

class TestPromiseAny:
    """Tests for Promise.any()."""
    
    @pytest.mark.asyncio
    async def test_promise_any_first_success(self):
        """Promise.any returns first success."""
        from pynext.runtime.promise import Promise_any
        
        async def fail():
            await asyncio.sleep(0.01)
            raise ValueError("fail")
        
        async def success():
            await asyncio.sleep(0.02)
            return "success"
        
        result = await Promise_any([fail(), success()])
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_promise_any_all_reject(self):
        """Promise.any raises AggregateError if all reject."""
        from pynext.runtime.promise import Promise_any, AggregateError
        
        async def fail(msg):
            raise ValueError(msg)
        
        with pytest.raises(AggregateError) as exc_info:
            await Promise_any([fail("e1"), fail("e2")])
        
        assert len(exc_info.value.errors) == 2
    
    @pytest.mark.asyncio
    async def test_promise_any_first_success_wins(self):
        """Promise.any returns fastest success."""
        from pynext.runtime.promise import Promise_any
        
        async def fast_fail():
            await asyncio.sleep(0.01)
            raise ValueError("fail")
        
        async def slow_success():
            await asyncio.sleep(0.03)
            return "slow"
        
        async def fast_success():
            await asyncio.sleep(0.02)
            return "fast"
        
        result = await Promise_any([
            fast_fail(),
            slow_success(),
            fast_success()
        ])
        assert result == "fast"
    
    @pytest.mark.asyncio
    async def test_promise_any_single_success(self):
        """Promise.any with single successful promise."""
        from pynext.runtime.promise import Promise_any
        
        async def success():
            return 42
        
        result = await Promise_any([success()])
        assert result == 42


# =============================================================================
# PROMISE.WITHRESOLVERS TESTS (3 tests)
# =============================================================================

class TestPromiseWithResolvers:
    """Tests for Promise.withResolvers()."""
    
    @pytest.mark.asyncio
    async def test_withresolvers_resolve(self):
        """withResolvers can resolve later."""
        from pynext.runtime.promise import Promise_withResolvers
        
        promise, resolve, reject = Promise_withResolvers()
        
        async def resolve_later():
            await asyncio.sleep(0.01)
            resolve(42)
        
        asyncio.create_task(resolve_later())
        result = await promise
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_withresolvers_reject(self):
        """withResolvers can reject later."""
        from pynext.runtime.promise import Promise_withResolvers
        
        promise, resolve, reject = Promise_withResolvers()
        
        async def reject_later():
            await asyncio.sleep(0.01)
            reject(ValueError("failed"))
        
        asyncio.create_task(reject_later())
        
        with pytest.raises(ValueError):
            await promise
    
    @pytest.mark.asyncio
    async def test_withresolvers_external_control(self):
        """withResolvers enables external control."""
        from pynext.runtime.promise import Promise_withResolvers
        
        promise, resolve, reject = Promise_withResolvers()
        
        # Resolve immediately
        resolve("immediate")
        result = await promise
        assert result == "immediate"
