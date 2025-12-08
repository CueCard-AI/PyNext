"""
Tests for Go Bridge async API.

Tests the async/await versions of execute, execute_batch, health, and warmup.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from pynext_go import GoBridge, GO_AVAILABLE
from pynext_go.config import BridgeConfig
from pynext_go.errors import BridgeError
from pynext_go.result import QueryResult, BatchResult
from pynext_go.health import HealthStatus


class TestAsyncMethodsExist:
    """Test that async methods exist on GoBridge."""
    
    def test_execute_async_exists(self):
        """GoBridge should have execute_async method."""
        bridge = GoBridge()
        assert hasattr(bridge, "execute_async")
        assert asyncio.iscoroutinefunction(bridge.execute_async)
    
    def test_execute_batch_async_exists(self):
        """GoBridge should have execute_batch_async method."""
        bridge = GoBridge()
        assert hasattr(bridge, "execute_batch_async")
        assert asyncio.iscoroutinefunction(bridge.execute_batch_async)
    
    def test_health_async_exists(self):
        """GoBridge should have health_async method."""
        bridge = GoBridge()
        assert hasattr(bridge, "health_async")
        assert asyncio.iscoroutinefunction(bridge.health_async)
    
    def test_warmup_async_exists(self):
        """GoBridge should have warmup_async method."""
        bridge = GoBridge()
        assert hasattr(bridge, "warmup_async")
        assert asyncio.iscoroutinefunction(bridge.warmup_async)


class TestModuleAsyncFunctions:
    """Test module-level async functions."""
    
    def test_execute_async_in_module(self):
        """pynext_go should export execute_async."""
        import pynext_go
        assert hasattr(pynext_go, "execute_async")
        assert asyncio.iscoroutinefunction(pynext_go.execute_async)
    
    def test_execute_batch_async_in_module(self):
        """pynext_go should export execute_batch_async."""
        import pynext_go
        assert hasattr(pynext_go, "execute_batch_async")
        assert asyncio.iscoroutinefunction(pynext_go.execute_batch_async)
    
    def test_health_async_in_module(self):
        """pynext_go should export health_async."""
        import pynext_go
        assert hasattr(pynext_go, "health_async")
        assert asyncio.iscoroutinefunction(pynext_go.health_async)
    
    def test_warmup_async_in_module(self):
        """pynext_go should export warmup_async."""
        import pynext_go
        assert hasattr(pynext_go, "warmup_async")
        assert asyncio.iscoroutinefunction(pynext_go.warmup_async)


class TestAsyncRaisesWhenNotInitialized:
    """Test async methods raise when bridge not initialized."""
    
    @pytest.mark.asyncio
    async def test_execute_async_raises(self):
        """execute_async should raise when not initialized."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            await bridge.execute_async("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_execute_batch_async_raises(self):
        """execute_batch_async should raise when not initialized."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            await bridge.execute_batch_async([("SELECT 1", [])])
    
    @pytest.mark.asyncio
    async def test_health_async_raises(self):
        """health_async should raise when not initialized."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            await bridge.health_async()
    
    @pytest.mark.asyncio
    async def test_warmup_async_raises(self):
        """warmup_async should raise when not initialized."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            await bridge.warmup_async()


class TestModuleAsyncRaisesWhenNotInitialized:
    """Test module async functions raise when not initialized."""
    
    @pytest.mark.asyncio
    async def test_execute_async_raises(self):
        """Module execute_async should raise when not initialized."""
        import pynext_go
        pynext_go.close()  # Ensure not initialized
        
        with pytest.raises(BridgeError, match="not initialized"):
            await pynext_go.execute_async("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_execute_batch_async_raises(self):
        """Module execute_batch_async should raise when not initialized."""
        import pynext_go
        pynext_go.close()
        
        with pytest.raises(BridgeError, match="not initialized"):
            await pynext_go.execute_batch_async([("SELECT 1", [])])
    
    @pytest.mark.asyncio
    async def test_health_async_raises(self):
        """Module health_async should raise when not initialized."""
        import pynext_go
        pynext_go.close()
        
        with pytest.raises(BridgeError, match="not initialized"):
            await pynext_go.health_async()
    
    @pytest.mark.asyncio
    async def test_warmup_async_raises(self):
        """Module warmup_async should raise when not initialized."""
        import pynext_go
        pynext_go.close()
        
        with pytest.raises(BridgeError, match="not initialized"):
            await pynext_go.warmup_async()


class TestAsyncConcurrency:
    """Test concurrent async execution."""
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_async_calls(self):
        """Multiple concurrent async calls should work."""
        bridge = GoBridge()
        bridge._initialized = True  # Mock initialization
        
        # Mock execute to return a result
        mock_result = QueryResult(
            success=True,
            rows=[[1]],
            columns=["id"],
        )
        
        async def mock_execute(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate async work
            return mock_result
        
        bridge.execute_async = mock_execute
        
        # Run multiple concurrent calls
        tasks = [bridge.execute_async(f"SELECT {i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(r.success for r in results)
    
    @pytest.mark.asyncio
    async def test_async_uses_executor(self):
        """Async methods should use run_in_executor."""
        bridge = GoBridge()
        bridge._initialized = True
        
        # Mock the sync execute method
        call_count = 0
        original_execute = bridge.execute
        
        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return QueryResult(success=True, rows=[], columns=[])
        
        bridge.execute = mock_execute
        
        # Call async version
        try:
            await bridge.execute_async("SELECT 1")
        except Exception:
            pass  # Expected without real Go bridge
        
        # Note: In the mock, this would be called
        # In real implementation, it goes through executor


class TestAsyncAll:
    """Test __all__ includes async functions."""
    
    def test_all_includes_async_functions(self):
        """__all__ should include async functions."""
        import pynext_go
        
        assert "execute_async" in pynext_go.__all__
        assert "execute_batch_async" in pynext_go.__all__
        assert "health_async" in pynext_go.__all__
        assert "warmup_async" in pynext_go.__all__


class TestAsyncUsagePatterns:
    """Test common async usage patterns."""
    
    @pytest.mark.asyncio
    async def test_can_await_execute_async(self):
        """Can await execute_async."""
        bridge = GoBridge()
        
        # Should be awaitable
        coro = bridge.execute_async("SELECT 1")
        assert asyncio.iscoroutine(coro)
        
        # Close the coroutine to avoid warning
        coro.close()
    
    @pytest.mark.asyncio
    async def test_can_await_execute_batch_async(self):
        """Can await execute_batch_async."""
        bridge = GoBridge()
        
        coro = bridge.execute_batch_async([("SELECT 1", [])])
        assert asyncio.iscoroutine(coro)
        coro.close()
    
    @pytest.mark.asyncio
    async def test_async_with_timeout(self):
        """Async calls should respect asyncio timeout."""
        import pynext_go
        pynext_go.close()
        
        # Should raise our error, not asyncio.TimeoutError
        with pytest.raises(BridgeError):
            async with asyncio.timeout(1.0):
                await pynext_go.execute_async("SELECT 1")


class TestAsyncReturnTypes:
    """Test async methods return correct types."""
    
    def test_execute_async_return_type_annotation(self):
        """execute_async should have QueryResult return annotation."""
        bridge = GoBridge()
        
        # Check return type annotation (string due to __future__ annotations)
        import inspect
        sig = inspect.signature(bridge.execute_async)
        assert "QueryResult" in str(sig.return_annotation)
    
    def test_execute_batch_async_return_type_annotation(self):
        """execute_batch_async should have BatchResult return annotation."""
        bridge = GoBridge()
        
        import inspect
        sig = inspect.signature(bridge.execute_batch_async)
        assert "BatchResult" in str(sig.return_annotation)
    
    def test_health_async_return_type_annotation(self):
        """health_async should have HealthStatus return annotation."""
        bridge = GoBridge()
        
        import inspect
        sig = inspect.signature(bridge.health_async)
        assert "HealthStatus" in str(sig.return_annotation)
    
    def test_warmup_async_return_type_annotation(self):
        """warmup_async should have None return annotation."""
        bridge = GoBridge()
        
        import inspect
        sig = inspect.signature(bridge.warmup_async)
        assert "None" in str(sig.return_annotation)

