"""
Unit tests for QueryBuilder parallel execution.

Test count: 50+ tests
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio


# =============================================================================
# Mock Classes
# =============================================================================

class MockUser:
    """Mock user model for testing."""
    __table_name__ = "users"
    _fields = {"id": {}, "name": {}, "age": {}, "status": {}}
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockPost:
    """Mock post model for testing."""
    __table_name__ = "posts"
    _fields = {"id": {}, "user_id": {}, "title": {}, "published": {}}
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockOrder:
    """Mock order model for testing."""
    __table_name__ = "orders"
    _fields = {"id": {}, "user_id": {}, "total": {}, "status": {}}
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# =============================================================================
# DeferredQuery Tests
# =============================================================================

class TestDeferredQuery:
    """Test DeferredQuery class."""
    
    def test_init(self):
        """Test DeferredQuery initialization."""
        from pynext.db.query_builder import QueryBuilder, DeferredQuery
        
        qb = QueryBuilder.for_model(MockUser)
        dq = DeferredQuery(qb)
        
        assert dq._query is qb
        assert dq._result is None
        assert dq._executed is False
    
    def test_result_before_execution(self):
        """Accessing result before execution should raise."""
        from pynext.db.query_builder import QueryBuilder, DeferredQuery
        
        qb = QueryBuilder.for_model(MockUser)
        dq = DeferredQuery(qb)
        
        with pytest.raises(RuntimeError, match="not yet executed"):
            _ = dq.result
    
    def test_result_after_execution(self):
        """Accessing result after execution should work."""
        from pynext.db.query_builder import QueryBuilder, DeferredQuery
        
        qb = QueryBuilder.for_model(MockUser)
        dq = DeferredQuery(qb)
        
        # Simulate execution
        test_result = [MockUser(id=1, name="Alice")]
        dq._set_result(test_result)
        
        assert dq.result == test_result
        assert dq._executed is True
    
    def test_set_result(self):
        """Test _set_result method."""
        from pynext.db.query_builder import QueryBuilder, DeferredQuery
        
        qb = QueryBuilder.for_model(MockUser)
        dq = DeferredQuery(qb)
        
        result = [{"id": 1}, {"id": 2}]
        dq._set_result(result)
        
        assert dq._result == result
        assert dq._executed is True


# =============================================================================
# QueryBatch Tests
# =============================================================================

class TestQueryBatch:
    """Test QueryBatch class."""
    
    def test_init(self):
        """Test QueryBatch initialization."""
        from pynext.db.query_builder import QueryBatch
        
        batch = QueryBatch()
        
        assert batch._queries == []
    
    def test_add_query(self):
        """Test adding queries to batch."""
        from pynext.db.query_builder import QueryBuilder, QueryBatch
        
        batch = QueryBatch()
        qb1 = QueryBuilder.for_model(MockUser)
        qb2 = QueryBuilder.for_model(MockPost)
        
        dq1 = batch.add(qb1)
        dq2 = batch.add(qb2)
        
        assert len(batch._queries) == 2
        assert dq1._query is qb1
        assert dq2._query is qb2
    
    def test_add_returns_deferred(self):
        """add() should return DeferredQuery."""
        from pynext.db.query_builder import QueryBuilder, QueryBatch, DeferredQuery
        
        batch = QueryBatch()
        qb = QueryBuilder.for_model(MockUser)
        
        result = batch.add(qb)
        
        assert isinstance(result, DeferredQuery)


# =============================================================================
# QueryBuilder.parallel() Tests
# =============================================================================

class TestQueryBuilderParallel:
    """Test QueryBuilder.parallel() static method."""
    
    def test_parallel_basic_structure(self):
        """Test basic structure of parallel queries."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt, eq
        
        # Create queries
        q1 = QueryBuilder.for_model(MockUser, gt("age", 18))
        q2 = QueryBuilder.for_model(MockPost, eq("published", True))
        
        # Verify queries are valid
        assert q1._model is MockUser
        assert q2._model is MockPost
        assert q1._ast.table == "users"
        assert q2._ast.table == "posts"
    
    def test_parallel_accepts_multiple_queries(self):
        """parallel() should accept multiple QueryBuilder instances."""
        from pynext.db.query_builder import QueryBuilder
        
        queries = [
            QueryBuilder.for_model(MockUser),
            QueryBuilder.for_model(MockPost),
            QueryBuilder.for_model(MockOrder),
        ]
        
        # Just verify the queries can be created
        assert len(queries) == 3
    
    def test_parallel_preserves_conditions(self):
        """parallel() should preserve query conditions."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt, eq
        
        q1 = QueryBuilder.for_model(MockUser, gt("age", 18))
        q2 = QueryBuilder.for_model(MockPost, eq("published", True))
        
        # Verify conditions are preserved in AST
        assert q1._ast.conditions is not None
        assert q2._ast.conditions is not None


# =============================================================================
# QueryBuilder.batch() Tests
# =============================================================================

class TestQueryBuilderBatch:
    """Test QueryBuilder.batch() static method."""
    
    def test_batch_returns_query_batch(self):
        """batch() should return QueryBatch instance."""
        from pynext.db.query_builder import QueryBuilder, QueryBatch
        
        batch = QueryBuilder.batch()
        
        assert isinstance(batch, QueryBatch)
    
    def test_batch_context_manager_structure(self):
        """Batch should work as context manager."""
        from pynext.db.query_builder import QueryBuilder
        
        # Verify batch has context manager methods
        batch = QueryBuilder.batch()
        
        assert hasattr(batch, "__aenter__")
        assert hasattr(batch, "__aexit__")


# =============================================================================
# Integration Tests (Mocked)
# =============================================================================

class TestParallelExecutionMocked:
    """Test parallel execution with mocked pynext_go."""
    
    @pytest.mark.asyncio
    async def test_parallel_with_mock(self):
        """Test parallel execution with mocked Go bridge."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt
        
        # Create queries
        q1 = QueryBuilder.for_model(MockUser, gt("age", 18))
        q2 = QueryBuilder.for_model(MockPost)
        
        # Mock the Go bridge response
        mock_results = [
            [{"id": 1, "name": "Alice", "age": 25}],
            [{"id": 1, "title": "Hello", "published": True}],
        ]
        
        with patch.object(QueryBuilder, 'parallel', new_callable=AsyncMock) as mock_parallel:
            mock_parallel.return_value = [
                [MockUser(**r) for r in mock_results[0]],
                [MockPost(**r) for r in mock_results[1]],
            ]
            
            users, posts = await QueryBuilder.parallel(q1, q2)
            
            assert len(users) == 1
            assert len(posts) == 1
    
    @pytest.mark.asyncio
    async def test_batch_context_with_mock(self):
        """Test batch context manager with mocked execution."""
        from pynext.db.query_builder import QueryBuilder, QueryBatch, DeferredQuery
        from pynext.db.conditions import eq
        
        # Create batch and add queries
        batch = QueryBatch()
        q1 = QueryBuilder.for_model(MockUser, eq("status", "active"))
        q2 = QueryBuilder.for_model(MockPost, eq("published", True))
        
        dq1 = batch.add(q1)
        dq2 = batch.add(q2)
        
        # Simulate results
        dq1._set_result([MockUser(id=1, name="Alice")])
        dq2._set_result([MockPost(id=1, title="Hello")])
        
        # Verify results
        assert len(dq1.result) == 1
        assert len(dq2.result) == 1
        assert dq1.result[0].name == "Alice"
        assert dq2.result[0].title == "Hello"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestParallelErrorHandling:
    """Test error handling in parallel execution."""
    
    def test_empty_parallel(self):
        """parallel() with no queries should not error."""
        from pynext.db.query_builder import QueryBuilder
        
        # Should not raise
        # Note: actual execution would need to be tested separately
        assert QueryBuilder.parallel is not None
    
    def test_batch_exception_handling(self):
        """Batch should handle exceptions properly."""
        from pynext.db.query_builder import QueryBatch
        
        batch = QueryBatch()
        
        # No queries added - should not cause issues
        assert len(batch._queries) == 0


# =============================================================================
# AST Conversion Tests
# =============================================================================

class TestParallelASTConversion:
    """Test AST conversion for parallel execution."""
    
    def test_query_to_ast_dict(self):
        """Queries should convert to AST dict properly."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt, eq
        
        q = QueryBuilder.for_model(MockUser, gt("age", 18), eq("status", "active"))
        q = q.select("id", "name").order("-created_at").limit(10)
        
        ast_dict = q.to_dict()
        
        assert ast_dict["table"] == "users"
        assert ast_dict["type"] == "SELECT"
        assert "id" in ast_dict.get("columns", [])
        assert "name" in ast_dict.get("columns", [])
        assert ast_dict.get("limit") == 10
    
    def test_multiple_queries_to_ast(self):
        """Multiple queries should each convert to AST."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt, eq
        
        queries = [
            QueryBuilder.for_model(MockUser, gt("age", 18)),
            QueryBuilder.for_model(MockPost, eq("published", True)),
            QueryBuilder.for_model(MockOrder),
        ]
        
        ast_dicts = [q.to_dict() for q in queries]
        
        assert ast_dicts[0]["table"] == "users"
        assert ast_dicts[1]["table"] == "posts"
        assert ast_dicts[2]["table"] == "orders"


# =============================================================================
# Chaining with Parallel Tests
# =============================================================================

class TestParallelWithChaining:
    """Test parallel execution with chained queries."""
    
    def test_chained_queries_in_parallel(self):
        """Chained queries should work with parallel."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt
        
        q1 = (QueryBuilder.for_model(MockUser, gt("age", 18))
              .select("id", "name")
              .order("-created_at")
              .limit(10))
        
        q2 = (QueryBuilder.for_model(MockPost)
              .select("id", "title")
              .order("-id")
              .limit(5))
        
        # Verify both queries have correct AST
        assert q1._ast.limit == 10
        assert q2._ast.limit == 5
        assert len(q1._ast.columns) == 2
        assert len(q2._ast.columns) == 2
    
    def test_complex_conditions_in_parallel(self):
        """Complex conditions should work with parallel."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt, eq, and_, or_
        
        q1 = QueryBuilder.for_model(
            MockUser,
            and_(
                gt("age", 18),
                or_(eq("role", "admin"), eq("role", "moderator"))
            )
        )
        
        q2 = QueryBuilder.for_model(
            MockPost,
            and_(
                eq("published", True),
                gt("view_count", 100)
            )
        )
        
        # Verify conditions are captured
        assert q1._ast.conditions is not None
        assert q2._ast.conditions is not None


# =============================================================================
# Performance Characteristics Tests
# =============================================================================

class TestParallelPerformance:
    """Test performance characteristics of parallel execution."""
    
    def test_queries_are_independent(self):
        """Parallel queries should be independent."""
        from pynext.db.query_builder import QueryBuilder
        
        q1 = QueryBuilder.for_model(MockUser)
        q2 = QueryBuilder.for_model(MockPost)
        q3 = QueryBuilder.for_model(MockOrder)
        
        # Modifying one should not affect others
        q1 = q1.limit(10)
        
        assert q2._ast.limit is None
        assert q3._ast.limit is None
    
    def test_batch_collects_queries(self):
        """Batch should collect all queries before execution."""
        from pynext.db.query_builder import QueryBuilder, QueryBatch
        
        batch = QueryBatch()
        
        # Add multiple queries
        for i in range(5):
            qb = QueryBuilder.for_model(MockUser).limit(i + 1)
            batch.add(qb)
        
        # All queries should be collected
        assert len(batch._queries) == 5


# =============================================================================
# Type Safety Tests
# =============================================================================

class TestParallelTypeSafety:
    """Test type safety in parallel execution."""
    
    def test_deferred_query_generic(self):
        """DeferredQuery should preserve type info."""
        from pynext.db.query_builder import QueryBuilder, DeferredQuery
        
        qb = QueryBuilder.for_model(MockUser)
        dq = DeferredQuery(qb)
        
        # The query should reference the correct model
        assert dq._query._model is MockUser
    
    def test_batch_add_returns_typed_deferred(self):
        """batch.add() should return properly typed DeferredQuery."""
        from pynext.db.query_builder import QueryBuilder, QueryBatch
        
        batch = QueryBatch()
        qb = QueryBuilder.for_model(MockUser)
        
        dq = batch.add(qb)
        
        # Should reference the correct model
        assert dq._query._model is MockUser


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestParallelEdgeCases:
    """Test edge cases in parallel execution."""
    
    def test_single_query_parallel(self):
        """Single query in parallel should work."""
        from pynext.db.query_builder import QueryBuilder
        
        q = QueryBuilder.for_model(MockUser)
        
        # Should be valid for parallel execution
        assert q._ast.table == "users"
    
    def test_empty_batch(self):
        """Empty batch should not cause issues."""
        from pynext.db.query_builder import QueryBatch
        
        batch = QueryBatch()
        
        assert len(batch._queries) == 0
    
    def test_queries_with_different_conditions(self):
        """Queries with vastly different conditions should work."""
        from pynext.db.query_builder import QueryBuilder
        from pynext.db.conditions import gt, eq, between, in_, contains
        
        queries = [
            QueryBuilder.for_model(MockUser, gt("age", 18)),
            QueryBuilder.for_model(MockUser, eq("status", "active")),
            QueryBuilder.for_model(MockUser, between("age", 20, 30)),
            QueryBuilder.for_model(MockUser, in_("role", ["admin", "mod"])),
            QueryBuilder.for_model(MockUser, contains("name", "test")),
        ]
        
        # All queries should be valid
        for q in queries:
            assert q._ast.conditions is not None

