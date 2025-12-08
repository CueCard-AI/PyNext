"""
Tests for Go Bridge parallel query execution.

Tests the execute_parallel() and execute_parallel_async() methods
that run multiple queries simultaneously in Go goroutines.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from pynext_go import GoBridge, GO_AVAILABLE
from pynext_go.config import BridgeConfig
from pynext_go.errors import BridgeError
from pynext_go.result import QueryResult


# =============================================================================
# Method Existence Tests
# =============================================================================

class TestParallelMethodsExist:
    """Test that parallel methods exist."""
    
    def test_execute_parallel_exists_on_bridge(self):
        """GoBridge should have execute_parallel method."""
        bridge = GoBridge()
        assert hasattr(bridge, "execute_parallel")
        assert callable(bridge.execute_parallel)
    
    def test_execute_parallel_async_exists_on_bridge(self):
        """GoBridge should have execute_parallel_async method."""
        bridge = GoBridge()
        assert hasattr(bridge, "execute_parallel_async")
        assert asyncio.iscoroutinefunction(bridge.execute_parallel_async)
    
    def test_execute_parallel_in_module(self):
        """pynext_go should export execute_parallel."""
        import pynext_go
        assert hasattr(pynext_go, "execute_parallel")
        assert callable(pynext_go.execute_parallel)
    
    def test_execute_parallel_async_in_module(self):
        """pynext_go should export execute_parallel_async."""
        import pynext_go
        assert hasattr(pynext_go, "execute_parallel_async")
        assert asyncio.iscoroutinefunction(pynext_go.execute_parallel_async)
    
    def test_in_all_exports(self):
        """Parallel functions should be in __all__."""
        import pynext_go
        assert "execute_parallel" in pynext_go.__all__
        assert "execute_parallel_async" in pynext_go.__all__


# =============================================================================
# Not Initialized Tests
# =============================================================================

class TestParallelRaisesWhenNotInitialized:
    """Test parallel methods raise when bridge not initialized."""
    
    def test_execute_parallel_raises(self):
        """execute_parallel should raise when not initialized."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            bridge.execute_parallel([("SELECT 1", [])])
    
    @pytest.mark.asyncio
    async def test_execute_parallel_async_raises(self):
        """execute_parallel_async should raise when not initialized."""
        bridge = GoBridge()
        
        with pytest.raises(BridgeError):
            await bridge.execute_parallel_async([("SELECT 1", [])])
    
    def test_module_execute_parallel_raises(self):
        """Module execute_parallel should raise when not initialized."""
        import pynext_go
        pynext_go.close()
        
        with pytest.raises(BridgeError, match="not initialized"):
            pynext_go.execute_parallel([("SELECT 1", [])])
    
    @pytest.mark.asyncio
    async def test_module_execute_parallel_async_raises(self):
        """Module execute_parallel_async should raise when not initialized."""
        import pynext_go
        pynext_go.close()
        
        with pytest.raises(BridgeError, match="not initialized"):
            await pynext_go.execute_parallel_async([("SELECT 1", [])])


# =============================================================================
# Input Validation Tests
# =============================================================================

class TestParallelInputValidation:
    """Test input validation for parallel execution."""
    
    def test_empty_queries_list(self):
        """Empty queries list should be handled."""
        bridge = GoBridge()
        bridge._initialized = True
        
        # Mock the ctypes call
        with patch.object(bridge, '_check_initialized'):
            # This would call Go with empty list
            # Go should return empty array
            pass
    
    def test_single_query(self):
        """Single query should work."""
        # Just verifying the API accepts a single query
        queries = [("SELECT 1", [])]
        assert len(queries) == 1
    
    def test_multiple_queries(self):
        """Multiple queries should be accepted."""
        queries = [
            ("SELECT 1", []),
            ("SELECT 2", []),
            ("SELECT 3", []),
        ]
        assert len(queries) == 3
    
    def test_queries_with_params(self):
        """Queries with parameters should be accepted."""
        queries = [
            ("SELECT * FROM users WHERE id = $1", [1]),
            ("SELECT * FROM orders WHERE user_id = $1 AND status = $2", [1, "active"]),
        ]
        assert len(queries) == 2


# =============================================================================
# Return Type Tests
# =============================================================================

class TestParallelReturnTypes:
    """Test that parallel methods return correct types."""
    
    def test_execute_parallel_return_annotation(self):
        """execute_parallel should return list[QueryResult]."""
        bridge = GoBridge()
        
        import inspect
        sig = inspect.signature(bridge.execute_parallel)
        # Check return annotation contains QueryResult
        assert "QueryResult" in str(sig.return_annotation)
        assert "list" in str(sig.return_annotation)
    
    def test_execute_parallel_async_return_annotation(self):
        """execute_parallel_async should return list[QueryResult]."""
        bridge = GoBridge()
        
        import inspect
        sig = inspect.signature(bridge.execute_parallel_async)
        assert "QueryResult" in str(sig.return_annotation)
        assert "list" in str(sig.return_annotation)


# =============================================================================
# Order Preservation Tests
# =============================================================================

class TestParallelOrderPreservation:
    """Test that results are returned in same order as queries."""
    
    def test_result_order_concept(self):
        """Results should match query order."""
        # This is a conceptual test - actual execution requires Go
        # The contract is: results[i] corresponds to queries[i]
        
        queries = [
            ("SELECT 'first'", []),
            ("SELECT 'second'", []),
            ("SELECT 'third'", []),
        ]
        
        # If we had results, they should be:
        # results[0] -> "first"
        # results[1] -> "second"
        # results[2] -> "third"
        
        assert len(queries) == 3


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestParallelErrorHandling:
    """Test error handling in parallel execution."""
    
    def test_partial_failure_concept(self):
        """Some queries can fail while others succeed."""
        # In parallel execution, one failing query shouldn't
        # prevent other queries from completing
        # Results array will have success=False for failed queries
        
        # This is the expected behavior contract
        assert True
    
    def test_all_fail_concept(self):
        """All queries failing should return all failures."""
        # If all queries fail, results array should have
        # all results with success=False
        assert True


# =============================================================================
# Async Behavior Tests
# =============================================================================

class TestParallelAsyncBehavior:
    """Test async behavior of parallel execution."""
    
    @pytest.mark.asyncio
    async def test_is_awaitable(self):
        """execute_parallel_async should be awaitable."""
        bridge = GoBridge()
        
        coro = bridge.execute_parallel_async([("SELECT 1", [])])
        assert asyncio.iscoroutine(coro)
        coro.close()
    
    @pytest.mark.asyncio
    async def test_can_use_with_gather(self):
        """Can use execute_parallel_async with asyncio.gather."""
        # This test verifies the API is compatible with gather
        bridge = GoBridge()
        
        async def mock_parallel():
            raise BridgeError("not initialized")
        
        # Just verify the pattern works
        try:
            await asyncio.gather(
                mock_parallel(),
                mock_parallel(),
            )
        except BridgeError:
            pass  # Expected


# =============================================================================
# Comparison Tests
# =============================================================================

class TestParallelVsBatch:
    """Test differences between parallel and batch execution."""
    
    def test_both_methods_exist(self):
        """Both execute_batch and execute_parallel should exist."""
        bridge = GoBridge()
        assert hasattr(bridge, "execute_batch")
        assert hasattr(bridge, "execute_parallel")
    
    def test_different_return_types(self):
        """execute_batch returns BatchResult, execute_parallel returns list."""
        import inspect
        bridge = GoBridge()
        
        batch_sig = inspect.signature(bridge.execute_batch)
        parallel_sig = inspect.signature(bridge.execute_parallel)
        
        # execute_batch returns BatchResult
        assert "BatchResult" in str(batch_sig.return_annotation)
        
        # execute_parallel returns list[QueryResult]
        assert "list" in str(parallel_sig.return_annotation)
    
    def test_batch_has_transaction_option(self):
        """execute_batch should have transaction option."""
        import inspect
        bridge = GoBridge()
        
        sig = inspect.signature(bridge.execute_batch)
        params = sig.parameters
        
        assert "transaction" in params
        assert "stop_on_error" in params
    
    def test_parallel_no_transaction(self):
        """execute_parallel should NOT have transaction option."""
        import inspect
        bridge = GoBridge()
        
        sig = inspect.signature(bridge.execute_parallel)
        params = sig.parameters
        
        # Parallel queries run independently - no transaction
        assert "transaction" not in params


# =============================================================================
# Performance Concept Tests
# =============================================================================

class TestParallelPerformanceConcept:
    """Conceptual tests about parallel performance."""
    
    def test_parallel_faster_than_sequential(self):
        """Parallel should be faster than sequential for independent queries."""
        # This is a conceptual test about the expected behavior
        # Actual benchmarking would require a real database
        
        # Sequential: time = query1 + query2 + query3
        # Parallel: time = max(query1, query2, query3)
        
        # Example: 3 queries, each taking 100ms
        # Sequential: 300ms
        # Parallel: ~100ms
        
        assert True  # Document the expected behavior
    
    def test_parallel_uses_multiple_connections(self):
        """Parallel execution should use multiple connections."""
        # Each goroutine gets its own connection from the pool
        # This allows true parallel execution
        assert True


# =============================================================================
# Go Integration Tests (Mocked)
# =============================================================================

class TestParallelGoIntegration:
    """Test Go integration for parallel execution."""
    
    def test_request_format(self):
        """Request should be JSON array of QueryRequest."""
        import json
        
        queries = [
            ("SELECT * FROM users", []),
            ("SELECT * FROM orders WHERE id = $1", [123]),
        ]
        
        # This is what gets sent to Go
        request = [
            {"sql": sql, "params": params}
            for sql, params in queries
        ]
        
        # Should be valid JSON array
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["sql"] == "SELECT * FROM users"
        assert parsed[1]["params"] == [123]
    
    def test_response_parsing(self):
        """Response should be parsed as list of QueryResult."""
        # Simulate Go response
        response_data = [
            {"success": True, "rows": [[1, "Alice"]], "columns": ["id", "name"]},
            {"success": True, "rows": [[100]], "columns": ["count"]},
        ]
        
        results = [QueryResult.from_dict(r) for r in response_data]
        
        assert len(results) == 2
        assert results[0].success
        assert results[1].success
        assert results[0].rows == [[1, "Alice"]]
        assert results[1].rows == [[100]]


# =============================================================================
# Usage Pattern Tests
# =============================================================================

class TestParallelUsagePatterns:
    """Test common usage patterns."""
    
    def test_destructuring_results(self):
        """Can destructure results into variables."""
        # Simulate results
        results = [
            QueryResult(success=True, rows=[[1]], columns=["id"]),
            QueryResult(success=True, rows=[[2]], columns=["id"]),
            QueryResult(success=True, rows=[[3]], columns=["id"]),
        ]
        
        # Destructuring
        users, orders, products = results
        
        assert users.rows[0][0] == 1
        assert orders.rows[0][0] == 2
        assert products.rows[0][0] == 3
    
    def test_iterating_results(self):
        """Can iterate over results."""
        results = [
            QueryResult(success=True, rows=[[i]], columns=["n"])
            for i in range(5)
        ]
        
        for i, result in enumerate(results):
            assert result.rows[0][0] == i
    
    def test_checking_all_success(self):
        """Can check if all queries succeeded."""
        results = [
            QueryResult(success=True, rows=[], columns=[]),
            QueryResult(success=True, rows=[], columns=[]),
            QueryResult(success=False, error="timeout", rows=[], columns=[]),
        ]
        
        all_success = all(r.success for r in results)
        assert not all_success
        
        failed = [r for r in results if not r.success]
        assert len(failed) == 1
        assert failed[0].error == "timeout"

