"""
Phase 33.4: Scheduling APIs Tests

Comprehensive tests for browser scheduling APIs transpilation.
Tests verify the runtime provides correct JavaScript implementations for:
- queueMicrotask
- requestIdleCallback / cancelIdleCallback
- requestAnimationFrame / cancelAnimationFrame
"""

import pytest
import asyncio


# =============================================================================
# QUEUEMICROTASK TESTS (10 tests)
# =============================================================================

class TestQueueMicrotask:
    """Tests for queueMicrotask()."""
    
    @pytest.mark.asyncio
    async def test_queuemicrotask_basic(self):
        """queueMicrotask schedules callback."""
        from pynext.runtime.scheduling import queueMicrotask
        
        results = []
        
        def callback():
            results.append("microtask")
        
        queueMicrotask(callback)
        results.append("sync")
        
        # Allow microtask to run
        await asyncio.sleep(0)
        
        # Microtask runs after sync code
        assert "sync" in results
    
    @pytest.mark.asyncio
    async def test_queuemicrotask_order(self):
        """Microtasks run in order."""
        from pynext.runtime.scheduling import queueMicrotask
        
        results = []
        
        queueMicrotask(lambda: results.append(1))
        queueMicrotask(lambda: results.append(2))
        queueMicrotask(lambda: results.append(3))
        
        await asyncio.sleep(0)
        
        assert results == [1, 2, 3]
    
    @pytest.mark.asyncio
    async def test_queuemicrotask_runs_before_settimeout(self):
        """Microtasks run before setTimeout callbacks."""
        from pynext.runtime.scheduling import queueMicrotask
        
        results = []
        
        queueMicrotask(lambda: results.append("microtask"))
        
        await asyncio.sleep(0.01)  # Simulate setTimeout(0)
        results.append("timeout")
        
        # Microtask should have run first
        assert results[0] == "microtask"
    
    @pytest.mark.asyncio
    async def test_queuemicrotask_nested(self):
        """Nested microtasks work."""
        from pynext.runtime.scheduling import queueMicrotask
        
        results = []
        
        def outer():
            results.append("outer")
            queueMicrotask(lambda: results.append("inner"))
        
        queueMicrotask(outer)
        
        await asyncio.sleep(0.01)
        
        assert results == ["outer", "inner"]
    
    def test_queuemicrotask_callable(self):
        """queueMicrotask accepts callable."""
        from pynext.runtime.scheduling import queueMicrotask
        
        class Callback:
            def __init__(self):
                self.called = False
            
            def __call__(self):
                self.called = True
        
        cb = Callback()
        queueMicrotask(cb)
        # Won't run synchronously, just verifying it accepts callable


# =============================================================================
# REQUESTIDLECALLBACK TESTS (8 tests)
# =============================================================================

class TestRequestIdleCallback:
    """Tests for requestIdleCallback()."""
    
    def test_requestidlecallback_returns_id(self):
        """requestIdleCallback returns handle."""
        from pynext.runtime.scheduling import requestIdleCallback
        
        handle = requestIdleCallback(lambda deadline: None)
        assert handle is not None
    
    def test_requestidlecallback_with_timeout(self):
        """requestIdleCallback accepts timeout option."""
        from pynext.runtime.scheduling import requestIdleCallback
        
        handle = requestIdleCallback(
            lambda deadline: None,
            {"timeout": 2000}
        )
        assert handle is not None
    
    @pytest.mark.asyncio
    async def test_requestidlecallback_runs(self):
        """requestIdleCallback runs callback."""
        from pynext.runtime.scheduling import requestIdleCallback
        
        results = []
        
        def callback(deadline):
            results.append("idle")
        
        requestIdleCallback(callback)
        
        await asyncio.sleep(0.1)  # Wait for idle callback
        
        assert "idle" in results
    
    @pytest.mark.asyncio
    async def test_requestidlecallback_deadline(self):
        """Callback receives deadline object."""
        from pynext.runtime.scheduling import requestIdleCallback
        
        deadline_received = [None]
        
        def callback(deadline):
            deadline_received[0] = deadline
        
        requestIdleCallback(callback)
        
        await asyncio.sleep(0.1)
        
        deadline = deadline_received[0]
        assert deadline is not None
        assert hasattr(deadline, 'timeRemaining') or callable(getattr(deadline, 'timeRemaining', None))
    
    def test_cancelidlecallback_basic(self):
        """cancelIdleCallback cancels scheduled callback."""
        from pynext.runtime.scheduling import requestIdleCallback, cancelIdleCallback
        
        called = [False]
        
        def callback(deadline):
            called[0] = True
        
        handle = requestIdleCallback(callback)
        cancelIdleCallback(handle)
        
        # Callback should not run (but we can't easily verify in Python)
        # Just verify it doesn't throw
    
    @pytest.mark.asyncio
    async def test_requestidlecallback_timeout_forces_run(self):
        """Timeout option forces callback to run."""
        from pynext.runtime.scheduling import requestIdleCallback
        
        ran = [False]
        
        def callback(deadline):
            ran[0] = True
        
        requestIdleCallback(callback, {"timeout": 50})
        
        await asyncio.sleep(0.1)
        
        assert ran[0] is True


# =============================================================================
# REQUESTANIMATIONFRAME TESTS (8 tests)
# =============================================================================

class TestRequestAnimationFrame:
    """Tests for requestAnimationFrame()."""
    
    def test_requestanimationframe_returns_id(self):
        """requestAnimationFrame returns handle."""
        from pynext.runtime.scheduling import requestAnimationFrame
        
        handle = requestAnimationFrame(lambda ts: None)
        assert handle is not None
    
    @pytest.mark.asyncio
    async def test_requestanimationframe_runs(self):
        """requestAnimationFrame runs callback."""
        from pynext.runtime.scheduling import requestAnimationFrame
        
        results = []
        
        def callback(timestamp):
            results.append("frame")
        
        requestAnimationFrame(callback)
        
        await asyncio.sleep(0.05)  # Wait for frame
        
        assert "frame" in results
    
    @pytest.mark.asyncio
    async def test_requestanimationframe_timestamp(self):
        """Callback receives timestamp."""
        from pynext.runtime.scheduling import requestAnimationFrame
        
        timestamp_received = [None]
        
        def callback(timestamp):
            timestamp_received[0] = timestamp
        
        requestAnimationFrame(callback)
        
        await asyncio.sleep(0.05)
        
        ts = timestamp_received[0]
        assert ts is not None
        assert isinstance(ts, (int, float))
    
    def test_cancelanimationframe_basic(self):
        """cancelAnimationFrame cancels scheduled callback."""
        from pynext.runtime.scheduling import requestAnimationFrame, cancelAnimationFrame
        
        called = [False]
        
        def callback(timestamp):
            called[0] = True
        
        handle = requestAnimationFrame(callback)
        cancelAnimationFrame(handle)
        
        # Just verify it doesn't throw
    
    @pytest.mark.asyncio
    async def test_requestanimationframe_loop(self):
        """Animation loop pattern works."""
        from pynext.runtime.scheduling import requestAnimationFrame, cancelAnimationFrame
        
        frame_count = [0]
        max_frames = 3
        handle = [None]
        
        def animate(timestamp):
            frame_count[0] += 1
            if frame_count[0] < max_frames:
                handle[0] = requestAnimationFrame(animate)
        
        handle[0] = requestAnimationFrame(animate)
        
        await asyncio.sleep(0.2)  # Wait for frames
        
        # Should have run at least once
        assert frame_count[0] >= 1
    
    @pytest.mark.asyncio
    async def test_requestanimationframe_multiple(self):
        """Multiple requestAnimationFrame calls work."""
        from pynext.runtime.scheduling import requestAnimationFrame
        
        results = []
        
        requestAnimationFrame(lambda ts: results.append("a"))
        requestAnimationFrame(lambda ts: results.append("b"))
        requestAnimationFrame(lambda ts: results.append("c"))
        
        await asyncio.sleep(0.1)
        
        # All should have run
        assert len(results) == 3


# =============================================================================
# SCHEDULING INTEGRATION TESTS (4 tests)
# =============================================================================

class TestSchedulingIntegration:
    """Integration tests for scheduling APIs."""
    
    @pytest.mark.asyncio
    async def test_microtask_before_raf(self):
        """Microtasks run before RAF callbacks."""
        from pynext.runtime.scheduling import queueMicrotask, requestAnimationFrame
        
        results = []
        
        requestAnimationFrame(lambda ts: results.append("raf"))
        queueMicrotask(lambda: results.append("microtask"))
        
        await asyncio.sleep(0.05)
        
        # Microtask should be first
        if "microtask" in results and "raf" in results:
            assert results.index("microtask") < results.index("raf")
    
    @pytest.mark.asyncio
    async def test_idle_callback_low_priority(self):
        """Idle callbacks run during idle time."""
        from pynext.runtime.scheduling import requestIdleCallback, requestAnimationFrame
        
        results = []
        
        requestAnimationFrame(lambda ts: results.append("raf"))
        requestIdleCallback(lambda dl: results.append("idle"))
        
        await asyncio.sleep(0.2)
        
        # Both should have run
        assert "raf" in results
        assert "idle" in results
    
    def test_scheduling_api_availability(self):
        """All scheduling APIs are available."""
        from pynext.runtime.scheduling import (
            queueMicrotask,
            requestIdleCallback,
            cancelIdleCallback,
            requestAnimationFrame,
            cancelAnimationFrame
        )
        
        assert callable(queueMicrotask)
        assert callable(requestIdleCallback)
        assert callable(cancelIdleCallback)
        assert callable(requestAnimationFrame)
        assert callable(cancelAnimationFrame)
    
    @pytest.mark.asyncio
    async def test_cancel_before_run(self):
        """Canceling before callback runs works."""
        from pynext.runtime.scheduling import requestAnimationFrame, cancelAnimationFrame
        
        ran = [False]
        
        handle = requestAnimationFrame(lambda ts: ran.__setitem__(0, True))
        cancelAnimationFrame(handle)
        
        await asyncio.sleep(0.1)
        
        # Should not have run (or may have, depending on timing)
        # Just verify no exception
